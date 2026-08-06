"""Two-stage foreground transport for active Coding Agent self-review."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from typing import Any, Mapping

from agentgov.active_agent_self_review import (
    ActiveAgentSelfReviewError,
    ActiveAgentSelfReviewRun,
    PreparedActiveAgentSelfReview,
    SelfReviewObservationDraft,
    complete_active_agent_self_review,
    prepare_active_agent_self_review,
)
from agentgov.alignment_transport import AlignmentStreamResponse
from agentgov.human_decision import canonical_document_digest
from agentgov.semantic_review import (
    SemanticReviewContractError,
    semantic_authority_boundary,
    semantic_content_boundary,
    semantic_review_provider_capabilities_from_payload,
    semantic_review_provider_digest,
    semantic_review_result_from_payload,
    semantic_review_route_from_payload,
)


SELF_REVIEW_START_CONTRACT = "agentgov.active-agent-self-review-start"
SELF_REVIEW_DRAFT_CONTRACT = "agentgov.active-agent-self-review-draft"
SELF_REVIEW_RESPONSE_CONTRACT = "agentgov.active-agent-self-review-stream-response"
SELF_REVIEW_SCHEMA_VERSION = "1.0"
SELF_REVIEW_INPUT_CONTRACTS = {
    SELF_REVIEW_START_CONTRACT,
    SELF_REVIEW_DRAFT_CONTRACT,
}

_START_ID_RE = re.compile(r"^asx-[0-9a-f]{32}$")
_DRAFT_ID_RE = re.compile(r"^asd-[0-9a-f]{32}$")
_REQUEST_ID_RE = re.compile(r"^asq-[0-9a-f]{32}$")
_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_ADAPTER_ID_RE = re.compile(r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$")


class SelfReviewTransportError(ValueError):
    """A live self-review record is invalid, stale, or out of order."""


@dataclass(frozen=True)
class ActiveAgentSelfReviewStart:
    contract: str
    schema_version: str
    start_id: str
    source: Mapping[str, str]
    alignment: Mapping[str, Any]
    risk: Mapping[str, Any]
    provider: Any
    allowed_evidence_refs: tuple[str, ...]
    content_boundary: Mapping[str, bool]
    authority_boundary: Mapping[str, bool]


@dataclass(frozen=True)
class ActiveAgentSelfReviewDraft:
    contract: str
    schema_version: str
    draft_id: str
    source: Mapping[str, str]
    request: Mapping[str, str]
    observations: tuple[SelfReviewObservationDraft, ...]
    content_boundary: Mapping[str, bool]
    authority_boundary: Mapping[str, bool]


@dataclass(frozen=True)
class ActiveAgentSelfReviewStreamResponse:
    contract: str
    schema_version: str
    sequence: int
    input: Mapping[str, str]
    status: str
    persistence: Mapping[str, Any]
    materialization_request: Mapping[str, Any] | None
    run: ActiveAgentSelfReviewRun | None
    authority_boundary: Mapping[str, bool]


def active_agent_self_review_stream_response_from_payload(
    value: Any,
) -> ActiveAgentSelfReviewStreamResponse:
    """Parse a response and reject status, binding, privacy, or authority drift."""

    fields = {
        "contract", "schema_version", "sequence", "input", "status", "persistence",
        "materialization_request", "run", "authority_boundary",
    }
    if not isinstance(value, Mapping) or set(value) != fields:
        raise SelfReviewTransportError("self-review response has unexpected fields")
    if value.get("contract") != SELF_REVIEW_RESPONSE_CONTRACT or value.get(
        "schema_version"
    ) != SELF_REVIEW_SCHEMA_VERSION:
        raise SelfReviewTransportError("self-review response contract is unsupported")
    sequence = value.get("sequence")
    if not isinstance(sequence, int) or isinstance(sequence, bool) or sequence < 1:
        raise SelfReviewTransportError("self-review response sequence is invalid")
    input_value = value.get("input")
    if not isinstance(input_value, Mapping) or set(input_value) != {"contract", "id", "adapter_id"}:
        raise SelfReviewTransportError("self-review response input binding is invalid")
    contract = input_value.get("contract")
    input_id = input_value.get("id")
    pattern = {
        SELF_REVIEW_START_CONTRACT: _START_ID_RE,
        SELF_REVIEW_DRAFT_CONTRACT: _DRAFT_ID_RE,
    }.get(contract)
    adapter_id = input_value.get("adapter_id")
    if (
        pattern is None
        or not isinstance(input_id, str)
        or not pattern.fullmatch(input_id)
        or not isinstance(adapter_id, str)
        or not _ADAPTER_ID_RE.fullmatch(adapter_id)
    ):
        raise SelfReviewTransportError("self-review response input binding is invalid")
    if value.get("persistence") != {"mode": "foreground_memory", "survives_restart": False}:
        raise SelfReviewTransportError("self-review response persistence claim is invalid")
    authority = _exact_false_boundary(
        value.get("authority_boundary"), semantic_authority_boundary(), "response authority boundary"
    )
    status = value.get("status")
    request_value = value.get("materialization_request")
    run_value = value.get("run")
    request: Mapping[str, Any] | None = None
    run: ActiveAgentSelfReviewRun | None = None
    if status == "materialization_required":
        if contract != SELF_REVIEW_START_CONTRACT or run_value is not None:
            raise SelfReviewTransportError("materialization response has an impossible status combination")
        request = _validated_materialization_request(request_value)
    elif status == "completed":
        if contract != SELF_REVIEW_DRAFT_CONTRACT or request_value is not None:
            raise SelfReviewTransportError("completed response has an impossible status combination")
        run = _run_from_payload(run_value)
    else:
        raise SelfReviewTransportError("self-review response status is unsupported")
    return ActiveAgentSelfReviewStreamResponse(
        contract=SELF_REVIEW_RESPONSE_CONTRACT,
        schema_version=SELF_REVIEW_SCHEMA_VERSION,
        sequence=sequence,
        input=dict(input_value),
        status=status,
        persistence={"mode": "foreground_memory", "survives_restart": False},
        materialization_request=request,
        run=run,
        authority_boundary=authority,
    )


def _validated_materialization_request(value: Any) -> Mapping[str, Any]:
    fields = {"request_id", "request_digest", "start", "context", "context_binding", "instruction"}
    if not isinstance(value, Mapping) or set(value) != fields:
        raise SelfReviewTransportError("materialization request has unexpected fields")
    request_id = value.get("request_id")
    digest = value.get("request_digest")
    body = {key: value[key] for key in ("start", "context", "context_binding", "instruction")}
    if (
        not isinstance(request_id, str)
        or not _REQUEST_ID_RE.fullmatch(request_id)
        or not isinstance(digest, str)
        or not _DIGEST_RE.fullmatch(digest)
        or canonical_document_digest(body) != digest
        or request_id != "asq-" + digest.removeprefix("sha256:")[:32]
    ):
        raise SelfReviewTransportError("materialization request identity is invalid")
    start = value.get("start")
    if not isinstance(start, Mapping) or set(start) != {"start_id", "start_digest"}:
        raise SelfReviewTransportError("materialization request start binding is invalid")
    if not _START_ID_RE.fullmatch(str(start.get("start_id"))) or not _DIGEST_RE.fullmatch(str(start.get("start_digest"))):
        raise SelfReviewTransportError("materialization request start binding is invalid")
    instruction = value.get("instruction")
    if instruction != {
        "response_contract": SELF_REVIEW_DRAFT_CONTRACT,
        "review_mode": "self_review",
        "semantics": "advisory",
        "return_observation_ids": False,
    }:
        raise SelfReviewTransportError("materialization instruction is invalid")
    context = value.get("context")
    binding = value.get("context_binding")
    if not isinstance(context, Mapping) or set(context) != {
        "subject", "dialogue", "route", "provider", "center", "drift", "assumptions",
        "allowed_evidence_refs", "content_boundary", "authority_boundary",
    }:
        raise SelfReviewTransportError("materialization context is invalid")
    if not isinstance(binding, Mapping) or set(binding) != {
        "dialogue_id", "dialogue_revision", "dialogue_digest", "resolution_option_id",
        "route_id", "provider_id", "provider_capability_digest", "allowed_evidence_digest",
        "materializer_context_digest",
    }:
        raise SelfReviewTransportError("materialization context binding is invalid")
    try:
        route = semantic_review_route_from_payload(context.get("route"))
        provider = semantic_review_provider_capabilities_from_payload(context.get("provider"))
    except SemanticReviewContractError as exc:
        raise SelfReviewTransportError("materialization context contract is invalid") from exc
    if (
        route.route != "self_review"
        or route.provider is None
        or route.provider["provider_id"] != provider.provider_id
        or route.provider["capability_digest"] != semantic_review_provider_digest(provider)
        or binding.get("route_id") != route.route_id
        or binding.get("provider_id") != provider.provider_id
        or binding.get("provider_capability_digest") != route.provider["capability_digest"]
        or not isinstance(context.get("subject"), Mapping)
        or context["subject"] != {
            "type": "alignment_dialogue", "id": binding.get("dialogue_id")
        }
        or not isinstance(context.get("dialogue"), Mapping)
        or context["dialogue"] != {
            "dialogue_id": binding.get("dialogue_id"),
            "revision": binding.get("dialogue_revision"),
            "digest": binding.get("dialogue_digest"),
            "resolution_option_id": binding.get("resolution_option_id"),
        }
        or canonical_document_digest(context.get("allowed_evidence_refs"))
        != binding.get("allowed_evidence_digest")
        or canonical_document_digest(context) != binding.get("materializer_context_digest")
    ):
        raise SelfReviewTransportError("materialization context binding is stale")
    _exact_false_boundary(context.get("content_boundary"), semantic_content_boundary(), "context content boundary")
    _exact_false_boundary(context.get("authority_boundary"), semantic_authority_boundary(), "context authority boundary")
    return dict(value)


def _run_from_payload(value: Any) -> ActiveAgentSelfReviewRun:
    fields = {"route", "result", "context_binding", "execution", "privacy_boundary", "authority_boundary"}
    if not isinstance(value, Mapping) or set(value) != fields:
        raise SelfReviewTransportError("self-review run has unexpected fields")
    try:
        route = semantic_review_route_from_payload(value.get("route"))
        result = semantic_review_result_from_payload(value.get("result"))
        provider_payload = value.get("result", {}).get("provider") if isinstance(value.get("result"), Mapping) else None
        if route.provider != provider_payload:
            raise SelfReviewTransportError("self-review run Provider binding is stale")
    except SemanticReviewContractError as exc:
        raise SelfReviewTransportError("self-review run contract is invalid") from exc
    execution = value.get("execution")
    if execution != {
        "source": "active_host", "review_mode": "self_review", "materializer_invocations": 1,
        "agentgov_model_calls": 0, "agentgov_network_calls": 0, "context_retained_by_adapter": False,
    }:
        raise SelfReviewTransportError("self-review execution disclosure is invalid")
    privacy = value.get("privacy_boundary")
    expected_privacy = {
        "contains_raw_request": False, "contains_raw_answer": False, "contains_transcript": False,
        "contains_assistant_response": False, "contains_source_content": False,
        "contains_credentials": False, "contains_model_prompt": False, "contains_absolute_paths": False,
    }
    _exact_false_boundary(privacy, expected_privacy, "self-review privacy boundary")
    authority = _exact_false_boundary(value.get("authority_boundary"), semantic_authority_boundary(), "run authority boundary")
    binding = value.get("context_binding")
    expected_binding_fields = {
        "dialogue_id", "dialogue_revision", "dialogue_digest", "resolution_option_id",
        "route_id", "provider_id", "provider_capability_digest", "allowed_evidence_digest",
        "materializer_context_digest",
    }
    if (
        not isinstance(binding, Mapping)
        or set(binding) != expected_binding_fields
        or binding.get("route_id") != route.route_id
        or binding.get("provider_id") != result.provider["provider_id"]
        or binding.get("provider_capability_digest") != result.provider["capability_digest"]
    ):
        raise SelfReviewTransportError("self-review run context binding is invalid")
    return ActiveAgentSelfReviewRun(
        route=route,
        result=result,
        context_binding=dict(binding),
        execution=dict(execution),
        privacy_boundary=dict(privacy),
        authority_boundary=authority,
    )


def _exact_false_boundary(value: Any, expected: Mapping[str, bool], label: str) -> Mapping[str, bool]:
    if not isinstance(value, Mapping) or set(value) != set(expected) or any(
        item is not False for item in value.values()
    ):
        raise SelfReviewTransportError(f"{label} must deny every field")
    return dict(value)


def _source(value: Any) -> Mapping[str, str]:
    if not isinstance(value, Mapping) or set(value) != {"adapter_id", "actor_class"}:
        raise SelfReviewTransportError("self-review source is invalid")
    adapter_id = value.get("adapter_id")
    if not isinstance(adapter_id, str) or not _ADAPTER_ID_RE.fullmatch(adapter_id):
        raise SelfReviewTransportError("self-review source adapter_id is invalid")
    if value.get("actor_class") != "coding_agent":
        raise SelfReviewTransportError("self-review must be supplied by a Coding Agent")
    return {"adapter_id": adapter_id, "actor_class": "coding_agent"}


def active_agent_self_review_start_from_payload(value: Any) -> ActiveAgentSelfReviewStart:
    fields = {
        "contract", "schema_version", "start_id", "source", "alignment", "risk",
        "provider", "allowed_evidence_refs", "content_boundary", "authority_boundary",
    }
    if not isinstance(value, Mapping) or set(value) != fields:
        raise SelfReviewTransportError("self-review start has unexpected fields")
    if value.get("contract") != SELF_REVIEW_START_CONTRACT or value.get(
        "schema_version"
    ) != SELF_REVIEW_SCHEMA_VERSION:
        raise SelfReviewTransportError("self-review start contract is unsupported")
    start_id = value.get("start_id")
    if not isinstance(start_id, str) or not _START_ID_RE.fullmatch(start_id):
        raise SelfReviewTransportError("self-review start_id is invalid")
    alignment = value.get("alignment")
    if not isinstance(alignment, Mapping) or set(alignment) != {
        "dialogue_id", "revision", "digest"
    }:
        raise SelfReviewTransportError("self-review alignment binding is invalid")
    if (
        not isinstance(alignment.get("dialogue_id"), str)
        or not isinstance(alignment.get("revision"), int)
        or isinstance(alignment.get("revision"), bool)
        or alignment.get("revision") < 1
        or not isinstance(alignment.get("digest"), str)
        or not _DIGEST_RE.fullmatch(alignment.get("digest"))
    ):
        raise SelfReviewTransportError("self-review alignment binding is invalid")
    risk = value.get("risk")
    if not isinstance(risk, Mapping) or set(risk) != {"level", "reason_codes"}:
        raise SelfReviewTransportError("self-review risk binding is invalid")
    reasons = risk.get("reason_codes")
    if risk.get("level") != "medium" or not isinstance(reasons, list) or not reasons:
        raise SelfReviewTransportError("live active-Agent self-review requires medium risk")
    if any(not isinstance(item, str) for item in reasons) or len(reasons) != len(set(reasons)):
        raise SelfReviewTransportError("self-review reason_codes are invalid")
    refs = value.get("allowed_evidence_refs")
    if not isinstance(refs, list):
        raise SelfReviewTransportError("allowed_evidence_refs must be a list")
    try:
        provider = semantic_review_provider_capabilities_from_payload(value.get("provider"))
    except SemanticReviewContractError as exc:
        raise SelfReviewTransportError("self-review Provider contract is invalid") from exc
    return ActiveAgentSelfReviewStart(
        contract=SELF_REVIEW_START_CONTRACT,
        schema_version=SELF_REVIEW_SCHEMA_VERSION,
        start_id=start_id,
        source=_source(value.get("source")),
        alignment=dict(alignment),
        risk={"level": "medium", "reason_codes": tuple(reasons)},
        provider=provider,
        allowed_evidence_refs=tuple(refs),
        content_boundary=_exact_false_boundary(
            value.get("content_boundary"), semantic_content_boundary(), "start content boundary"
        ),
        authority_boundary=_exact_false_boundary(
            value.get("authority_boundary"), semantic_authority_boundary(), "start authority boundary"
        ),
    )


def _draft_observation(value: Any) -> SelfReviewObservationDraft:
    fields = {"kind", "summary", "evidence_refs", "assumptions", "unknowns", "recommended_question"}
    if not isinstance(value, Mapping) or set(value) != fields:
        raise SelfReviewTransportError("self-review draft observation has unexpected fields")
    sequences: dict[str, tuple[Any, ...]] = {}
    for field in ("evidence_refs", "assumptions", "unknowns"):
        item = value.get(field)
        if not isinstance(item, list):
            raise SelfReviewTransportError(f"self-review observation {field} must be a list")
        sequences[field] = tuple(item)
    return SelfReviewObservationDraft(
        kind=value.get("kind"),
        summary=value.get("summary"),
        evidence_refs=sequences["evidence_refs"],
        assumptions=sequences["assumptions"],
        unknowns=sequences["unknowns"],
        recommended_question=value.get("recommended_question"),
    )


def active_agent_self_review_draft_from_payload(value: Any) -> ActiveAgentSelfReviewDraft:
    fields = {
        "contract", "schema_version", "draft_id", "source", "request", "observations",
        "content_boundary", "authority_boundary",
    }
    if not isinstance(value, Mapping) or set(value) != fields:
        raise SelfReviewTransportError("self-review draft has unexpected fields")
    if value.get("contract") != SELF_REVIEW_DRAFT_CONTRACT or value.get(
        "schema_version"
    ) != SELF_REVIEW_SCHEMA_VERSION:
        raise SelfReviewTransportError("self-review draft contract is unsupported")
    draft_id = value.get("draft_id")
    if not isinstance(draft_id, str) or not _DRAFT_ID_RE.fullmatch(draft_id):
        raise SelfReviewTransportError("self-review draft_id is invalid")
    request = value.get("request")
    if not isinstance(request, Mapping) or set(request) != {"request_id", "request_digest"}:
        raise SelfReviewTransportError("self-review draft request binding is invalid")
    if not isinstance(request.get("request_id"), str) or not _REQUEST_ID_RE.fullmatch(request.get("request_id")):
        raise SelfReviewTransportError("self-review draft request_id is invalid")
    if not isinstance(request.get("request_digest"), str) or not _DIGEST_RE.fullmatch(request.get("request_digest")):
        raise SelfReviewTransportError("self-review draft request_digest is invalid")
    observations = value.get("observations")
    if not isinstance(observations, list):
        raise SelfReviewTransportError("self-review observations must be a list")
    return ActiveAgentSelfReviewDraft(
        contract=SELF_REVIEW_DRAFT_CONTRACT,
        schema_version=SELF_REVIEW_SCHEMA_VERSION,
        draft_id=draft_id,
        source=_source(value.get("source")),
        request=dict(request),
        observations=tuple(_draft_observation(item) for item in observations),
        content_boundary=_exact_false_boundary(
            value.get("content_boundary"), semantic_content_boundary(), "draft content boundary"
        ),
        authority_boundary=_exact_false_boundary(
            value.get("authority_boundary"), semantic_authority_boundary(), "draft authority boundary"
        ),
    )


def _request_payload(start: ActiveAgentSelfReviewStart, prepared: PreparedActiveAgentSelfReview) -> Mapping[str, Any]:
    body = {
        "start": {
            "start_id": start.start_id,
            "start_digest": canonical_document_digest(asdict(start)),
        },
        "context": asdict(prepared.context),
        "context_binding": dict(prepared.context_binding),
        "instruction": {
            "response_contract": SELF_REVIEW_DRAFT_CONTRACT,
            "review_mode": "self_review",
            "semantics": "advisory",
            "return_observation_ids": False,
        },
    }
    digest = canonical_document_digest(body)
    return {
        "request_id": "asq-" + digest.removeprefix("sha256:")[:32],
        "request_digest": digest,
        **body,
    }


class ActiveAgentSelfReviewStreamSession:
    """One foreground-only start/draft exchange bound to a resolved alignment."""

    def __init__(self) -> None:
        self._prepared: PreparedActiveAgentSelfReview | None = None
        self._request: Mapping[str, Any] | None = None
        self._adapter_id: str | None = None
        self._completed = False
        self._seen_ids: set[str] = set()

    def process_payload(
        self,
        payload: Mapping[str, Any],
        *,
        sequence: int,
        alignment_response: AlignmentStreamResponse | None,
        expected_adapter_id: str | None,
    ) -> ActiveAgentSelfReviewStreamResponse:
        if not isinstance(sequence, int) or isinstance(sequence, bool) or sequence < 1:
            raise SelfReviewTransportError("self-review stream sequence is invalid")
        contract = payload.get("contract") if isinstance(payload, Mapping) else None
        if contract == SELF_REVIEW_START_CONTRACT:
            return self._start(payload, sequence, alignment_response, expected_adapter_id)
        if contract == SELF_REVIEW_DRAFT_CONTRACT:
            return self._complete(payload, sequence, expected_adapter_id)
        raise SelfReviewTransportError("self-review input contract is unsupported")

    def _start(self, payload: Mapping[str, Any], sequence: int, alignment_response: AlignmentStreamResponse | None, expected_adapter_id: str | None) -> ActiveAgentSelfReviewStreamResponse:
        start = active_agent_self_review_start_from_payload(payload)
        if start.start_id in self._seen_ids or self._prepared is not None or self._completed:
            raise SelfReviewTransportError("self-review start is duplicate or out of order")
        if alignment_response is None or alignment_response.status != "resolved":
            raise SelfReviewTransportError("self-review start requires the current resolved alignment")
        if expected_adapter_id is None or start.source["adapter_id"] != expected_adapter_id:
            raise SelfReviewTransportError("self-review start adapter does not match the alignment session")
        expected_alignment = {
            "dialogue_id": alignment_response.dialogue.dialogue_id,
            "revision": alignment_response.dialogue.revision,
            "digest": canonical_document_digest(asdict(alignment_response.dialogue)),
        }
        if start.alignment != expected_alignment:
            raise SelfReviewTransportError("self-review start alignment binding is stale")
        try:
            prepared = prepare_active_agent_self_review(
                alignment_response=alignment_response,
                provider=start.provider,
                risk_level=start.risk["level"],
                reason_codes=start.risk["reason_codes"],
                allowed_evidence_refs=start.allowed_evidence_refs,
            )
        except ActiveAgentSelfReviewError as exc:
            raise SelfReviewTransportError(str(exc)) from exc
        request = _request_payload(start, prepared)
        self._prepared = prepared
        self._request = request
        self._adapter_id = start.source["adapter_id"]
        self._seen_ids.add(start.start_id)
        return self._response(sequence, start.contract, start.start_id, "materialization_required", request, None)

    def _complete(self, payload: Mapping[str, Any], sequence: int, expected_adapter_id: str | None) -> ActiveAgentSelfReviewStreamResponse:
        draft = active_agent_self_review_draft_from_payload(payload)
        if draft.draft_id in self._seen_ids or self._completed:
            raise SelfReviewTransportError("self-review draft is duplicate or out of order")
        if self._prepared is None or self._request is None or self._adapter_id is None:
            raise SelfReviewTransportError("self-review draft requires a pending materialization request")
        if draft.source["adapter_id"] != self._adapter_id or draft.source["adapter_id"] != expected_adapter_id:
            raise SelfReviewTransportError("self-review draft adapter does not match the pending request")
        expected_request = {
            "request_id": self._request["request_id"],
            "request_digest": self._request["request_digest"],
        }
        if draft.request != expected_request:
            raise SelfReviewTransportError("self-review draft request binding is stale")
        try:
            run = complete_active_agent_self_review(self._prepared, draft.observations)
        except ActiveAgentSelfReviewError as exc:
            raise SelfReviewTransportError(str(exc)) from exc
        self._seen_ids.add(draft.draft_id)
        self._completed = True
        self._prepared = None
        self._request = None
        return self._response(sequence, draft.contract, draft.draft_id, "completed", None, run)

    def _response(self, sequence: int, contract: str, input_id: str, status: str, request: Mapping[str, Any] | None, run: ActiveAgentSelfReviewRun | None) -> ActiveAgentSelfReviewStreamResponse:
        return ActiveAgentSelfReviewStreamResponse(
            contract=SELF_REVIEW_RESPONSE_CONTRACT,
            schema_version=SELF_REVIEW_SCHEMA_VERSION,
            sequence=sequence,
            input={"contract": contract, "id": input_id, "adapter_id": self._adapter_id or ""},
            status=status,
            persistence={"mode": "foreground_memory", "survives_restart": False},
            materialization_request=request,
            run=run,
            authority_boundary=semantic_authority_boundary(),
        )


def render_self_review_stream_response_json(response: ActiveAgentSelfReviewStreamResponse) -> str:
    parsed = active_agent_self_review_stream_response_from_payload(asdict(response))
    return json.dumps(asdict(parsed), ensure_ascii=False, sort_keys=True) + "\n"


def render_self_review_stream_response_terminal(response: ActiveAgentSelfReviewStreamResponse) -> str:
    response = active_agent_self_review_stream_response_from_payload(asdict(response))
    if response.status == "materialization_required":
        request_id = response.materialization_request["request_id"]
        detail = f"REQUEST {request_id}: active Coding Agent should return advisory observations"
    else:
        detail = f"RESULT {response.run.result.result_id}: advisory self-review accepted"
    return f"SELF-REVIEW {response.status} sequence={response.sequence}\n{detail}\n"
