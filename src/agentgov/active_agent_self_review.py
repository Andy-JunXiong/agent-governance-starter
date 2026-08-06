"""Host-neutral active Coding Agent self-review materialization.

AgentGov prepares a normalized ephemeral context and validates the result.  The
active host supplies semantic inference through the protocol in this module;
Core does not select or call a model.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Protocol, Sequence

from agentgov.alignment_transport import (
    AlignmentStreamResponse,
    alignment_stream_response_from_payload,
)
from agentgov.human_decision import canonical_document_digest
from agentgov.path_policy import scope_path_error
from agentgov.semantic_review import (
    SemanticReviewContractError,
    SemanticReviewProviderCapabilities,
    SemanticReviewResult,
    SemanticReviewRoute,
    accept_semantic_review_result,
    build_semantic_review_result,
    route_semantic_review,
    semantic_authority_boundary,
    semantic_content_boundary,
    semantic_review_provider_capabilities_from_payload,
)


@dataclass(frozen=True)
class ActiveAgentSelfReviewContext:
    """Ephemeral normalized evidence supplied to the active host materializer."""

    subject: Mapping[str, str]
    dialogue: Mapping[str, Any]
    route: SemanticReviewRoute
    provider: SemanticReviewProviderCapabilities
    center: Mapping[str, Any]
    drift: Mapping[str, Any]
    assumptions: tuple[str, ...]
    allowed_evidence_refs: tuple[str, ...]
    content_boundary: Mapping[str, bool]
    authority_boundary: Mapping[str, bool]


@dataclass(frozen=True)
class SelfReviewObservationDraft:
    """Small normalized advisory observation returned by the active host."""

    kind: str
    summary: str
    evidence_refs: tuple[str, ...]
    assumptions: tuple[str, ...] = ()
    unknowns: tuple[str, ...] = ()
    recommended_question: str | None = None


class ActiveAgentSelfReviewMaterializer(Protocol):
    """Host capability that performs one disclosed same-Agent review pass."""

    def materialize_self_review(
        self,
        context: ActiveAgentSelfReviewContext,
    ) -> Sequence[SelfReviewObservationDraft | Mapping[str, Any]]:
        """Return normalized observations without mutating context or project state."""


@dataclass(frozen=True)
class ActiveAgentSelfReviewRun:
    """Accepted result and truthful execution disclosures for one host callback."""

    route: SemanticReviewRoute
    result: SemanticReviewResult
    context_binding: Mapping[str, Any]
    execution: Mapping[str, Any]
    privacy_boundary: Mapping[str, bool]
    authority_boundary: Mapping[str, bool]


@dataclass(frozen=True)
class PreparedActiveAgentSelfReview:
    """Validated context retained only while a foreground review is pending."""

    context: ActiveAgentSelfReviewContext
    context_binding: Mapping[str, Any]


class ActiveAgentSelfReviewError(ValueError):
    """The self-review request, host draft, or accepted result is unsafe."""


_DRAFT_FIELDS = {
    "kind",
    "summary",
    "evidence_refs",
    "assumptions",
    "unknowns",
    "recommended_question",
}
_SENSITIVE_PATH_RE = re.compile(
    r"(?i)(?:api[_-]?key|access[_-]?token|auth[_-]?token|password|passwd|secret)\s*[:=]"
)


def _safe_evidence_refs(value: Any, *, label: str) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)) or not 1 <= len(value) <= 50:
        raise ActiveAgentSelfReviewError(f"{label} must contain 1 to 50 paths")
    normalized: list[str] = []
    for item in value:
        if (
            not isinstance(item, str)
            or len(item) > 240
            or scope_path_error(item)
            or any(
                unicodedata.category(character).startswith("C") for character in item
            )
            or _SENSITIVE_PATH_RE.search(item)
        ):
            raise ActiveAgentSelfReviewError(
                f"{label} must contain only safe repository paths"
            )
        normalized.append(item)
    if len(normalized) != len(set(normalized)):
        raise ActiveAgentSelfReviewError(f"{label} must not contain duplicates")
    return tuple(normalized)


def _draft_from_value(value: Any) -> SelfReviewObservationDraft:
    if isinstance(value, SelfReviewObservationDraft):
        payload = asdict(value)
    elif isinstance(value, Mapping):
        payload = dict(value)
    else:
        raise ActiveAgentSelfReviewError(
            "self-review materializer must return observation draft objects"
        )
    if set(payload) != _DRAFT_FIELDS:
        raise ActiveAgentSelfReviewError(
            "self-review observation draft has unexpected fields"
        )
    kind = payload.get("kind")
    summary = payload.get("summary")
    assumptions = payload.get("assumptions")
    unknowns = payload.get("unknowns")
    question = payload.get("recommended_question")
    if not isinstance(kind, str) or not isinstance(summary, str):
        raise ActiveAgentSelfReviewError("self-review draft kind and summary are required")
    if not isinstance(assumptions, (list, tuple)) or not isinstance(
        unknowns, (list, tuple)
    ):
        raise ActiveAgentSelfReviewError(
            "self-review draft assumptions and unknowns must be lists"
        )
    if question is not None and not isinstance(question, str):
        raise ActiveAgentSelfReviewError(
            "self-review draft recommended_question must be text or null"
        )
    return SelfReviewObservationDraft(
        kind=kind,
        summary=summary,
        evidence_refs=_safe_evidence_refs(
            payload.get("evidence_refs"), label="draft evidence_refs"
        ),
        assumptions=tuple(assumptions),
        unknowns=tuple(unknowns),
        recommended_question=question,
    )


def _context_binding(context: ActiveAgentSelfReviewContext) -> Mapping[str, Any]:
    return {
        "dialogue_id": context.dialogue["dialogue_id"],
        "dialogue_revision": context.dialogue["revision"],
        "dialogue_digest": context.dialogue["digest"],
        "resolution_option_id": context.dialogue["resolution_option_id"],
        "route_id": context.route.route_id,
        "provider_id": context.provider.provider_id,
        "provider_capability_digest": context.route.provider["capability_digest"],
        "allowed_evidence_digest": canonical_document_digest(
            context.allowed_evidence_refs
        ),
    }


def _observation_payload(
    *,
    draft: SelfReviewObservationDraft,
    position: int,
    context_binding: Mapping[str, Any],
) -> Mapping[str, Any]:
    normalized = asdict(draft)
    identity = canonical_document_digest(
        {
            "context_binding": context_binding,
            "position": position,
            "draft": normalized,
        }
    )
    return {
        "observation_id": "obs-" + identity.removeprefix("sha256:")[:16],
        **normalized,
    }


def prepare_active_agent_self_review(
    *,
    alignment_response: AlignmentStreamResponse,
    provider: SemanticReviewProviderCapabilities,
    risk_level: str,
    reason_codes: Sequence[str],
    allowed_evidence_refs: Sequence[str],
) -> PreparedActiveAgentSelfReview:
    """Validate and bind the exact context before asking the host to reason."""

    try:
        response = alignment_stream_response_from_payload(asdict(alignment_response))
    except ValueError as exc:
        raise ActiveAgentSelfReviewError(
            "active-Agent self-review requires an exact alignment response"
        ) from exc
    if response.status != "resolved" or response.dialogue.resolution is None:
        raise ActiveAgentSelfReviewError(
            "active-Agent self-review requires a resolved human alignment decision"
        )
    if risk_level != "medium":
        raise ActiveAgentSelfReviewError(
            "active-Agent materialization supports only medium-risk self-review"
        )
    try:
        normalized_provider = semantic_review_provider_capabilities_from_payload(
            asdict(provider)
        )
        route = route_semantic_review(
            risk_level=risk_level,
            reason_codes=reason_codes,
            active_agent_provider=normalized_provider,
        )
    except SemanticReviewContractError as exc:
        raise ActiveAgentSelfReviewError(
            "active-Agent Provider cannot satisfy the self-review route"
        ) from exc
    allowed_refs = _safe_evidence_refs(
        allowed_evidence_refs, label="allowed_evidence_refs"
    )
    dialogue_digest = canonical_document_digest(asdict(response.dialogue))
    context = ActiveAgentSelfReviewContext(
        subject={
            "type": "alignment_dialogue",
            "id": response.dialogue.dialogue_id,
        },
        dialogue={
            "dialogue_id": response.dialogue.dialogue_id,
            "revision": response.dialogue.revision,
            "digest": dialogue_digest,
            "resolution_option_id": response.dialogue.resolution["option_id"],
        },
        route=route,
        provider=normalized_provider,
        center=dict(response.dialogue.center),
        drift=dict(response.dialogue.drift),
        assumptions=tuple(response.dialogue.assumptions),
        allowed_evidence_refs=allowed_refs,
        content_boundary=semantic_content_boundary(),
        authority_boundary=semantic_authority_boundary(),
    )
    materializer_context_digest = canonical_document_digest(asdict(context))
    binding = {
        **_context_binding(context),
        "materializer_context_digest": materializer_context_digest,
    }
    return PreparedActiveAgentSelfReview(context=context, context_binding=binding)


def complete_active_agent_self_review(
    prepared: PreparedActiveAgentSelfReview,
    draft_values: Sequence[SelfReviewObservationDraft | Mapping[str, Any]],
    *,
    materializer_invocations: int = 1,
) -> ActiveAgentSelfReviewRun:
    """Validate host drafts and build the advisory result without calling a model."""

    if not isinstance(prepared, PreparedActiveAgentSelfReview):
        raise ActiveAgentSelfReviewError("prepared self-review context is invalid")
    context = prepared.context
    binding = prepared.context_binding
    materializer_context_digest = binding.get("materializer_context_digest")
    if canonical_document_digest(asdict(context)) != materializer_context_digest:
        raise ActiveAgentSelfReviewError("bound self-review context changed before completion")
    allowed_refs = context.allowed_evidence_refs
    route = context.route
    normalized_provider = context.provider
    if not isinstance(materializer_invocations, int) or isinstance(
        materializer_invocations, bool
    ) or materializer_invocations != 1:
        raise ActiveAgentSelfReviewError("self-review requires exactly one host materialization")
    if (
        not isinstance(draft_values, (list, tuple))
        or not 1 <= len(draft_values) <= 20
    ):
        raise ActiveAgentSelfReviewError(
            "self-review materializer must return 1 to 20 observation drafts"
        )
    drafts = tuple(_draft_from_value(item) for item in draft_values)
    if len({canonical_document_digest(asdict(item)) for item in drafts}) != len(drafts):
        raise ActiveAgentSelfReviewError(
            "self-review materializer returned duplicate observations"
        )
    allowed_set = set(allowed_refs)
    if any(not set(item.evidence_refs) <= allowed_set for item in drafts):
        raise ActiveAgentSelfReviewError(
            "self-review observation cites evidence outside the allowed set"
        )
    observations = tuple(
        _observation_payload(draft=item, position=index, context_binding=binding)
        for index, item in enumerate(drafts, start=1)
    )
    try:
        result = build_semantic_review_result(
            route,
            normalized_provider,
            observations=observations,
        )
        accepted = accept_semantic_review_result(route, normalized_provider, result)
    except SemanticReviewContractError as exc:
        raise ActiveAgentSelfReviewError(
            "active host self-review result failed the Core contract"
        ) from exc
    return ActiveAgentSelfReviewRun(
        route=route,
        result=accepted,
        context_binding=binding,
        execution={
            "source": "active_host",
            "review_mode": "self_review",
            "materializer_invocations": materializer_invocations,
            "agentgov_model_calls": 0,
            "agentgov_network_calls": 0,
            "context_retained_by_adapter": False,
        },
        privacy_boundary={
            "contains_raw_request": False,
            "contains_raw_answer": False,
            "contains_transcript": False,
            "contains_assistant_response": False,
            "contains_source_content": False,
            "contains_credentials": False,
            "contains_model_prompt": False,
            "contains_absolute_paths": False,
        },
        authority_boundary=semantic_authority_boundary(),
    )


def run_active_agent_self_review(
    *,
    alignment_response: AlignmentStreamResponse,
    provider: SemanticReviewProviderCapabilities,
    materializer: ActiveAgentSelfReviewMaterializer,
    risk_level: str,
    reason_codes: Sequence[str],
    allowed_evidence_refs: Sequence[str],
) -> ActiveAgentSelfReviewRun:
    """Run one active-host callback and accept only its exactly bound result."""

    prepared = prepare_active_agent_self_review(
        alignment_response=alignment_response,
        provider=provider,
        risk_level=risk_level,
        reason_codes=reason_codes,
        allowed_evidence_refs=allowed_evidence_refs,
    )
    try:
        draft_values = materializer.materialize_self_review(prepared.context)
    except Exception as exc:
        raise ActiveAgentSelfReviewError(
            "active host could not materialize semantic self-review"
        ) from exc
    if canonical_document_digest(asdict(prepared.context)) != prepared.context_binding.get(
        "materializer_context_digest"
    ):
        raise ActiveAgentSelfReviewError(
            "active host mutated the bound self-review context"
        )
    return complete_active_agent_self_review(prepared, draft_values)
