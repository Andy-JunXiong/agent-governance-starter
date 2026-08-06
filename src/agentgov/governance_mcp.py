"""Foreground MCP Adapter for governed alignment and active-Agent self-review."""

from __future__ import annotations

import json
import re
import uuid
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence, TextIO

from agentgov.clarification_dialogue import denied_authority
from agentgov.alignment_transport import AlignmentStreamSession
from agentgov.host_interaction import build_host_interaction_capabilities
from agentgov.human_decision import canonical_document_digest
from agentgov.reference_alignment_adapter import (
    AlignmentContextDraft,
    ClarificationUpdateDraft,
    ReferenceAlignmentAdapter,
    ReferenceAlignmentAdapterError,
)
from agentgov.semantic_review import (
    SemanticReviewProviderCapabilities,
    semantic_authority_boundary,
    semantic_content_boundary,
    semantic_review_provider_capabilities_from_payload,
)
from agentgov.self_review_transport import (
    SELF_REVIEW_DRAFT_CONTRACT,
    SELF_REVIEW_START_CONTRACT,
    ActiveAgentSelfReviewStreamSession,
    SelfReviewTransportError,
)


MCP_PROTOCOL_VERSION = "2026-07-28"
MCP_LEGACY_PROTOCOL_VERSIONS = ("2025-11-25", "2025-06-18")
MCP_SERVER_NAME = "agentgov-governance"
MCP_SERVER_VERSION = "1.2.0"
MCP_TOOL_NAMES = (
    "agentgov_alignment_start",
    "agentgov_alignment_update",
    "agentgov_alignment_resolve",
    "agentgov_self_review_start",
    "agentgov_self_review_complete",
)
MCP_SERVER_INSTRUCTIONS = (
    "Use these tools without waiting for the user to name them. Before meaningful development "
    "with multiple reasonable product, requirement, architecture, scope, or implementation "
    "directions, or when asked to choose what to build, start alignment from normalized meaning. "
    "Do not use alignment merely for read-only explanation, diagnosis, status, or a fully specified "
    "low-risk change with no material direction choice. Answer only the exact pending question and "
    "let the human select the final offered direction; never select it for them. After implementing "
    "and validating that resolved direction, run medium-risk active-Agent self-review as a distinct "
    "advisory pass and return its observations before completion. If a required call fails, report "
    "the bounded failure and do not silently continue. Never send raw prompts, raw answers, "
    "transcripts, assistant messages, credentials, absolute paths, or source content. The tools "
    "grant no task, code, scope, Git, release, deployment, or external authority."
)

_HANDLE_RE = re.compile(r"^mcpj-[0-9a-f]{32}$")
_PROMPT_ID_RE = re.compile(r"^cqp-[0-9a-f]{32}$")
_DECISION_ID_RE = re.compile(r"^dpr-[0-9a-f]{32}$")
_REQUEST_ID_RE = re.compile(r"^asq-[0-9a-f]{32}$")
_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_ID_RE = re.compile(r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$")


class GovernanceMcpError(ValueError):
    """An MCP request or governed tool call is malformed, stale, or unsafe."""

    def __init__(
        self,
        message: str,
        *,
        code: str = "mcp_invalid_request",
        stage: str = "tool_call",
        field_path: str | None = None,
        rule: str = "invalid",
        retryable: bool = False,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.stage = stage
        self.field_path = field_path
        self.rule = rule
        self.retryable = retryable

    def diagnostic(self) -> Mapping[str, Any]:
        return {
            "contract": "agentgov.mcp-tool-error",
            "schema_version": "1.0",
            "error_code": self.code,
            "stage": self.stage,
            "field_path": self.field_path,
            "rule": self.rule,
            "retryable": self.retryable,
        }


class _NormalizedOnlyMaterializer:
    def materialize_request(self, request_text: str) -> None:
        raise GovernanceMcpError("MCP Adapter accepts only normalized request drafts")

    def materialize_answer(self, answer_text: str, **_: Any) -> None:
        raise GovernanceMcpError("MCP Adapter accepts only normalized answer drafts")


@dataclass
class _Journey:
    adapter: ReferenceAlignmentAdapter
    self_review: ActiveAgentSelfReviewStreamSession
    self_review_sequence: int = 0
    review_requested: bool = False
    review_completed: bool = False


def build_active_host_self_review_provider(
    *,
    adapter_id: str,
    provider_id: str,
) -> SemanticReviewProviderCapabilities:
    """Build a host-owned current-entitlement Provider outside model-free Core."""

    payload = {
        "contract": "agentgov.semantic-review-provider-capabilities",
        "schema_version": "1.0",
        "provider_id": provider_id,
        "adapter_id": adapter_id,
        "source": {"owner": "active_host", "access_mode": "current_agent_entitlement"},
        "availability": {"status": "available", "reason_code": "active_mcp_session"},
        "review_mode": "self_review",
        "independence_level": "separate_pass",
        "cost_owner": "existing_user_entitlement",
        "data_policy": {"retention": "host_policy", "external_transfer": False},
        "content_boundary": semantic_content_boundary(),
        "authority_boundary": semantic_authority_boundary(),
    }
    return semantic_review_provider_capabilities_from_payload(payload)


def _exact_arguments(value: Any, fields: set[str], *, tool: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping) or set(value) != fields:
        raise GovernanceMcpError(
            f"{tool} arguments have unexpected fields",
            code="tool_arguments_invalid",
            stage=tool,
            field_path="$",
            rule="exact_fields",
            retryable=True,
        )
    return value


def _questions_with_adapter_ids(value: Any, *, stage: str, field_path: str) -> tuple[Mapping[str, Any], ...]:
    if not isinstance(value, list):
        raise GovernanceMcpError(
            f"{field_path} must be an array",
            code="alignment_invalid_field",
            stage=stage,
            field_path=field_path,
            rule="array_required",
            retryable=True,
        )
    expected = {"question", "why_matters", "material", "priority"}
    questions = []
    for index, item in enumerate(value):
        if not isinstance(item, Mapping) or set(item) != expected:
            raise GovernanceMcpError(
                f"{field_path} item has unexpected fields",
                code="alignment_invalid_field",
                stage=stage,
                field_path=f"{field_path}[{index}]",
                rule="exact_fields",
                retryable=True,
            )
        questions.append({"question_id": f"qst-{uuid.uuid4().hex[:16]}", **item})
    return tuple(questions)


def _alignment_rejection(exc: BaseException, *, stage: str) -> GovernanceMcpError:
    cause = exc.__cause__
    message = str(cause) if isinstance(cause, ValueError) else ""
    mappings = (
        ("alignment center has unexpected fields", "center", "exact_fields"),
        ("alignment center requires at least one success signal", "center.success_signals", "min_items"),
        ("drift observation has unexpected fields", "drift", "exact_fields"),
        ("drift kind or semantics is unsupported", "drift", "enum"),
        ("drift evidence must be repository-relative", "drift.evidence_refs", "repository_relative"),
        ("assumptions", "assumptions", "normalized_text"),
        ("unknowns", "unknowns", "normalized_question"),
        ("candidate resolution", "candidate_resolutions", "normalized_resolution"),
        ("recommended resolution", "recommended_resolution_id", "candidate_binding"),
        ("sensitive or host-local content", "$", "privacy_boundary"),
        ("control characters", "$", "normalized_text"),
    )
    for marker, field_path, rule in mappings:
        if marker in message:
            return GovernanceMcpError(
                "Core rejected a normalized alignment field; correct the indicated field and retry",
                code="alignment_invalid_field",
                stage=stage,
                field_path=field_path,
                rule=rule,
                retryable=True,
            )
    return GovernanceMcpError(
        "Core rejected the normalized alignment draft without a safe retry classification",
        code="alignment_rejected_internal",
        stage=stage,
        field_path=None,
        rule="unclassified",
        retryable=False,
    )


def _binding(value: Any, *, fields: set[str], identifier: re.Pattern[str], label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping) or set(value) != fields:
        raise GovernanceMcpError(f"{label} binding is invalid")
    identity = value.get(next(iter(fields - {"digest"})))
    digest = value.get("digest")
    if (
        not isinstance(identity, str)
        or not identifier.fullmatch(identity)
        or not isinstance(digest, str)
        or not _DIGEST_RE.fullmatch(digest)
    ):
        raise GovernanceMcpError(f"{label} binding is invalid")
    return dict(value)


def _journey_handle(value: Any) -> str:
    if not isinstance(value, str) or not _HANDLE_RE.fullmatch(value):
        raise GovernanceMcpError("journey_handle is invalid")
    return value


def _tool_schema(properties: Mapping[str, Any], required: Sequence[str]) -> Mapping[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "additionalProperties": False,
        "required": list(required),
        "properties": dict(properties),
    }


def _handle_schema() -> Mapping[str, Any]:
    return {"type": "string", "pattern": "^mcpj-[0-9a-f]{32}$"}


def _text_list_schema() -> Mapping[str, Any]:
    return {"type": "array", "maxItems": 50, "uniqueItems": True, "items": {"type": "string", "minLength": 1, "maxLength": 400}}


def _center_schema(*, patch: bool = False) -> Mapping[str, Any]:
    text = {"type": "string", "minLength": 1, "maxLength": 800}
    items = _text_list_schema()
    if patch:
        text = {"anyOf": [text, {"type": "null"}]}
        items = {"anyOf": [items, {"type": "null"}]}
    return {
        "type": "object", "additionalProperties": False,
        "required": ["outcome", "why_now", "success_signals", "constraints", "non_goals"],
        "properties": {"outcome": text, "why_now": text, "success_signals": items, "constraints": items, "non_goals": items},
    }


def _drift_schema() -> Mapping[str, Any]:
    return {
        "type": "object", "additionalProperties": False,
        "required": ["kind", "semantics", "observation", "evidence_refs", "impact"],
        "properties": {
            "kind": {"enum": ["business", "requirement", "architecture", "scope", "implementation"]},
            "semantics": {"enum": ["advisory", "deterministic"]},
            "observation": {"type": "string", "minLength": 1, "maxLength": 800},
            "evidence_refs": {"type": "array", "maxItems": 20, "uniqueItems": True, "items": {"type": "string", "minLength": 1, "maxLength": 240}},
            "impact": {"type": "string", "minLength": 1, "maxLength": 800},
        },
    }


def _question_schema() -> Mapping[str, Any]:
    return {
        "type": "object", "additionalProperties": False,
        "required": ["question", "why_matters", "material", "priority"],
        "properties": {
            "question": {"type": "string", "minLength": 1, "maxLength": 800},
            "why_matters": {"type": "string", "minLength": 1, "maxLength": 800},
            "material": {"type": "boolean"}, "priority": {"type": "integer", "minimum": 1, "maximum": 5},
        },
    }


def _resolution_schema() -> Mapping[str, Any]:
    return {
        "type": "object", "additionalProperties": False,
        "required": ["id", "label", "effect", "center_patch"],
        "properties": {
            "id": {"enum": ["return_to_center", "adopt_new_center", "split_new_requirement", "continue_exploration", "stop"]},
            "label": {"type": "string", "minLength": 1, "maxLength": 120},
            "effect": {"type": "string", "minLength": 1, "maxLength": 800},
            "center_patch": _center_schema(patch=True),
        },
    }


def _digest_binding_schema(identity: str, pattern: str) -> Mapping[str, Any]:
    return {
        "type": "object", "additionalProperties": False,
        "required": [identity, "digest"],
        "properties": {identity: {"type": "string", "pattern": pattern}, "digest": {"type": "string", "pattern": "^sha256:[0-9a-f]{64}$"}},
    }


def _observation_schema() -> Mapping[str, Any]:
    return {
        "type": "object", "additionalProperties": False,
        "required": ["kind", "summary", "evidence_refs", "assumptions", "unknowns", "recommended_question"],
        "properties": {
            "kind": {"enum": ["business", "requirement", "architecture", "scope", "implementation", "security", "data"]},
            "summary": {"type": "string", "minLength": 1, "maxLength": 800},
            "evidence_refs": {"type": "array", "minItems": 1, "maxItems": 20, "uniqueItems": True, "items": {"type": "string", "minLength": 1, "maxLength": 240}},
            "assumptions": _text_list_schema(), "unknowns": _text_list_schema(),
            "recommended_question": {"anyOf": [{"type": "null"}, {"type": "string", "minLength": 1, "maxLength": 800}]},
        },
    }


def governance_mcp_tools() -> tuple[Mapping[str, Any], ...]:
    """Return a deterministic tool catalog with strict top-level input schemas."""

    common_annotations = {
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": False,
    }
    tools = (
        {
            "name": MCP_TOOL_NAMES[0],
            "title": "Start governed alignment",
            "description": "Use before meaningful development when multiple reasonable directions exist or the Agent is asked to choose what to build. Start one foreground alignment journey from normalized meaning; the human must select the final direction. Do not use for read-only or fully specified low-risk work.",
            "inputSchema": _tool_schema(
                {
                    "subject_type": {"enum": ["work_request", "active_task", "architecture"]},
                    "subject_id": {"type": "string", "pattern": "^[a-z0-9]+(?:[._-][a-z0-9]+)*$"},
                    "center": _center_schema(),
                    "drift": _drift_schema(),
                    "assumptions": {"type": "array", "items": {"type": "string"}},
                    "unknowns": {"type": "array", "maxItems": 100, "items": _question_schema()},
                    "candidate_resolutions": {"type": "array", "maxItems": 5, "items": _resolution_schema()},
                    "recommended_resolution_id": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                },
                ("subject_type", "subject_id", "center", "drift", "assumptions", "unknowns", "candidate_resolutions", "recommended_resolution_id"),
            ),
            "annotations": common_annotations,
        },
        {
            "name": MCP_TOOL_NAMES[1],
            "title": "Apply normalized clarification",
            "description": "Apply one normalized human answer to the exact pending alignment question.",
            "inputSchema": _tool_schema(
                {
                    "journey_handle": _handle_schema(),
                    "prompt": _digest_binding_schema("prompt_id", "^cqp-[0-9a-f]{32}$"),
                    "answer_summary": {"type": "string", "minLength": 1, "maxLength": 800},
                    "center_patch": _center_schema(patch=True),
                    "new_questions": {"type": "array", "maxItems": 100, "items": _question_schema()},
                    "candidate_resolutions": {"type": "array", "maxItems": 5, "items": _resolution_schema()},
                    "recommended_resolution_id": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                    "ready_requested": {"type": "boolean"},
                },
                ("journey_handle", "prompt", "answer_summary", "center_patch", "new_questions", "candidate_resolutions", "recommended_resolution_id", "ready_requested"),
            ),
            "annotations": common_annotations,
        },
        {
            "name": MCP_TOOL_NAMES[2],
            "title": "Record human alignment choice",
            "description": "Record the human-selected option from the exact pending decision prompt.",
            "inputSchema": _tool_schema(
                {"journey_handle": _handle_schema(), "decision_prompt": _digest_binding_schema("prompt_id", "^dpr-[0-9a-f]{32}$"), "selected_option_id": {"enum": ["return_to_center", "adopt_new_center", "split_new_requirement", "continue_exploration", "stop"]}},
                ("journey_handle", "decision_prompt", "selected_option_id"),
            ),
            "annotations": common_annotations,
        },
        {
            "name": MCP_TOOL_NAMES[3],
            "title": "Start active-Agent self-review",
            "description": "Use after implementing and validating a human-resolved aligned direction, before completion handoff. Prepare one distinct advisory current-Agent self-review request from allowed evidence.",
            "inputSchema": _tool_schema(
                {"journey_handle": _handle_schema(), "reason_codes": {"type": "array", "minItems": 1, "uniqueItems": True, "items": {"type": "string"}}, "allowed_evidence_refs": {"type": "array", "minItems": 1, "uniqueItems": True, "items": {"type": "string"}}},
                ("journey_handle", "reason_codes", "allowed_evidence_refs"),
            ),
            "annotations": common_annotations,
        },
        {
            "name": MCP_TOOL_NAMES[4],
            "title": "Complete active-Agent self-review",
            "description": "Submit normalized observations for the exact pending self-review request.",
            "inputSchema": _tool_schema(
                {"journey_handle": _handle_schema(), "request": _digest_binding_schema("request_id", "^asq-[0-9a-f]{32}$"), "observations": {"type": "array", "minItems": 1, "maxItems": 20, "items": _observation_schema()}},
                ("journey_handle", "request", "observations"),
            ),
            "annotations": common_annotations,
        },
    )
    return tools


class GovernanceMcpAdapter:
    """Host-neutral tool layer backed only by foreground in-memory state."""

    def __init__(
        self,
        *,
        adapter_id: str,
        provider: SemanticReviewProviderCapabilities,
    ) -> None:
        if not isinstance(adapter_id, str) or not _ID_RE.fullmatch(adapter_id):
            raise GovernanceMcpError("MCP adapter_id is invalid")
        normalized_provider = semantic_review_provider_capabilities_from_payload(asdict(provider))
        if normalized_provider.adapter_id != adapter_id:
            raise GovernanceMcpError("MCP Provider adapter_id does not match the host Adapter")
        self.adapter_id = adapter_id
        self.provider = normalized_provider
        self._journeys: dict[str, _Journey] = {}

    def call_tool(self, name: str, arguments: Any) -> Mapping[str, Any]:
        dispatch = {
            MCP_TOOL_NAMES[0]: self._alignment_start,
            MCP_TOOL_NAMES[1]: self._alignment_update,
            MCP_TOOL_NAMES[2]: self._alignment_resolve,
            MCP_TOOL_NAMES[3]: self._self_review_start,
            MCP_TOOL_NAMES[4]: self._self_review_complete,
        }
        handler = dispatch.get(name)
        if handler is None:
            raise GovernanceMcpError("MCP tool name is unsupported")
        try:
            return handler(arguments)
        except ReferenceAlignmentAdapterError as exc:
            raise _alignment_rejection(exc, stage=name) from exc
        except (SelfReviewTransportError, ValueError, TypeError) as exc:
            if isinstance(exc, GovernanceMcpError):
                raise
            raise GovernanceMcpError(str(exc)) from exc

    def _lookup(self, value: Any) -> tuple[str, _Journey]:
        handle = _journey_handle(value)
        journey = self._journeys.get(handle)
        if journey is None:
            raise GovernanceMcpError("journey_handle is unknown or belonged to a restarted Adapter")
        return handle, journey

    def _alignment_start(self, value: Any) -> Mapping[str, Any]:
        fields = {"subject_type", "subject_id", "center", "drift", "assumptions", "unknowns", "candidate_resolutions", "recommended_resolution_id"}
        args = _exact_arguments(value, fields, tool=MCP_TOOL_NAMES[0])
        if (
            args["subject_type"] not in {"work_request", "active_task", "architecture"}
            or not isinstance(args["subject_id"], str)
            or not re.fullmatch(r"^[a-z0-9]+(?:[._-][a-z0-9]+)*$", args["subject_id"])
        ):
            raise GovernanceMcpError(
                "alignment subject identity is invalid",
                code="alignment_invalid_field",
                stage=MCP_TOOL_NAMES[0],
                field_path="subject_id",
                rule="normalized_identifier",
                retryable=True,
            )
        draft = AlignmentContextDraft(
            subject_type=args["subject_type"], subject_id=args["subject_id"],
            center=args["center"], drift=args["drift"], assumptions=tuple(args["assumptions"]),
            unknowns=_questions_with_adapter_ids(
                args["unknowns"], stage=MCP_TOOL_NAMES[0], field_path="unknowns"
            ), candidate_resolutions=tuple(args["candidate_resolutions"]),
            recommended_resolution_id=args["recommended_resolution_id"],
        )
        host_capabilities = build_host_interaction_capabilities(
            adapter_id=self.adapter_id,
            surface_family="mcp_tools",
            interactions={
                "task_admission": {"delivery_mode": "structured", "decision_recording": "adapter_event", "reason_code": "mcp_single_selection_available"},
                "scope_resolution": {"delivery_mode": "context_only", "decision_recording": "unavailable", "reason_code": "outside_alignment_tool_scope"},
                "completion_review": {"delivery_mode": "context_only", "decision_recording": "unavailable", "reason_code": "outside_alignment_tool_scope"},
                "tool_permission": {"delivery_mode": "native", "decision_recording": "host_managed", "reason_code": "mcp_client_policy"},
            },
        )
        adapter = ReferenceAlignmentAdapter(
            _NormalizedOnlyMaterializer(),
            adapter_id=self.adapter_id,
            session=AlignmentStreamSession(host_capabilities=host_capabilities),
        )
        response = adapter.start_from_draft(draft)
        handle = "mcpj-" + uuid.uuid4().hex
        self._journeys[handle] = _Journey(adapter=adapter, self_review=ActiveAgentSelfReviewStreamSession())
        return self._alignment_result(handle, response)

    def _alignment_update(self, value: Any) -> Mapping[str, Any]:
        fields = {"journey_handle", "prompt", "answer_summary", "center_patch", "new_questions", "candidate_resolutions", "recommended_resolution_id", "ready_requested"}
        args = _exact_arguments(value, fields, tool=MCP_TOOL_NAMES[1])
        handle, journey = self._lookup(args["journey_handle"])
        active = journey.adapter.journey().responses[-1]
        prompt = active.clarification_prompt
        if prompt is None:
            raise GovernanceMcpError("alignment journey is not waiting for clarification")
        binding = _binding(args["prompt"], fields={"prompt_id", "digest"}, identifier=_PROMPT_ID_RE, label="clarification prompt")
        expected = {"prompt_id": prompt.prompt_id, "digest": canonical_document_digest(asdict(prompt))}
        if binding != expected:
            raise GovernanceMcpError("clarification prompt binding is stale")
        draft = ClarificationUpdateDraft(
            answer_summary=args["answer_summary"], center_patch=args["center_patch"],
            new_questions=_questions_with_adapter_ids(
                args["new_questions"], stage=MCP_TOOL_NAMES[1], field_path="new_questions"
            ), candidate_resolutions=tuple(args["candidate_resolutions"]),
            recommended_resolution_id=args["recommended_resolution_id"], ready_requested=args["ready_requested"],
        )
        response = journey.adapter.answer_from_draft(draft)
        return self._alignment_result(handle, response)

    def _alignment_resolve(self, value: Any) -> Mapping[str, Any]:
        fields = {"journey_handle", "decision_prompt", "selected_option_id"}
        args = _exact_arguments(value, fields, tool=MCP_TOOL_NAMES[2])
        handle, journey = self._lookup(args["journey_handle"])
        active = journey.adapter.journey().responses[-1]
        prompt = active.decision_prompt
        if prompt is None:
            raise GovernanceMcpError("alignment journey is not waiting for a human direction choice")
        binding = _binding(args["decision_prompt"], fields={"prompt_id", "digest"}, identifier=_DECISION_ID_RE, label="decision prompt")
        expected = {"prompt_id": prompt.prompt_id, "digest": canonical_document_digest(asdict(prompt))}
        if binding != expected:
            raise GovernanceMcpError("decision prompt binding is stale")
        response = journey.adapter.select(args["selected_option_id"])
        return self._alignment_result(handle, response)

    def _self_review_start(self, value: Any) -> Mapping[str, Any]:
        fields = {"journey_handle", "reason_codes", "allowed_evidence_refs"}
        args = _exact_arguments(value, fields, tool=MCP_TOOL_NAMES[3])
        handle, journey = self._lookup(args["journey_handle"])
        if journey.review_requested or journey.review_completed:
            raise GovernanceMcpError("self-review has already started for this journey")
        active = journey.adapter.journey().responses[-1]
        start = {
            "contract": SELF_REVIEW_START_CONTRACT,
            "schema_version": "1.0",
            "start_id": "asx-" + uuid.uuid4().hex,
            "source": {"adapter_id": self.adapter_id, "actor_class": "coding_agent"},
            "alignment": {"dialogue_id": active.dialogue.dialogue_id, "revision": active.dialogue.revision, "digest": canonical_document_digest(asdict(active.dialogue))},
            "risk": {"level": "medium", "reason_codes": list(args["reason_codes"])},
            "provider": asdict(self.provider),
            "allowed_evidence_refs": list(args["allowed_evidence_refs"]),
            "content_boundary": semantic_content_boundary(),
            "authority_boundary": semantic_authority_boundary(),
        }
        response = journey.self_review.process_payload(
            start, sequence=1, alignment_response=active, expected_adapter_id=self.adapter_id
        )
        journey.self_review_sequence = 1
        journey.review_requested = True
        return {"journey_handle": handle, "stage": "self_review", "response": asdict(response), "authority_boundary": semantic_authority_boundary()}

    def _self_review_complete(self, value: Any) -> Mapping[str, Any]:
        fields = {"journey_handle", "request", "observations"}
        args = _exact_arguments(value, fields, tool=MCP_TOOL_NAMES[4])
        handle, journey = self._lookup(args["journey_handle"])
        if not journey.review_requested or journey.review_completed:
            raise GovernanceMcpError("self-review completion requires one pending request")
        request = _binding(args["request"], fields={"request_id", "digest"}, identifier=_REQUEST_ID_RE, label="self-review request")
        draft = {
            "contract": SELF_REVIEW_DRAFT_CONTRACT,
            "schema_version": "1.0",
            "draft_id": "asd-" + uuid.uuid4().hex,
            "source": {"adapter_id": self.adapter_id, "actor_class": "coding_agent"},
            "request": {"request_id": request["request_id"], "request_digest": request["digest"]},
            "observations": list(args["observations"]),
            "content_boundary": semantic_content_boundary(),
            "authority_boundary": semantic_authority_boundary(),
        }
        active = journey.adapter.journey().responses[-1]
        response = journey.self_review.process_payload(
            draft, sequence=2, alignment_response=active, expected_adapter_id=self.adapter_id
        )
        journey.self_review_sequence = 2
        journey.review_completed = True
        return {"journey_handle": handle, "stage": "self_review", "response": asdict(response), "authority_boundary": semantic_authority_boundary()}

    @staticmethod
    def _alignment_result(handle: str, response: Any) -> Mapping[str, Any]:
        return {"journey_handle": handle, "stage": "alignment", "response": asdict(response), "authority_boundary": denied_authority()}


class GovernanceMcpServer:
    """Dependency-free JSON-RPC surface for current and legacy STDIO MCP clients."""

    def __init__(self, adapter: GovernanceMcpAdapter) -> None:
        self.adapter = adapter

    def dispatch(self, payload: Any) -> Mapping[str, Any] | None:
        if not isinstance(payload, Mapping):
            return self._error(None, -32600, "Invalid Request")
        request_id = payload.get("id")
        if payload.get("jsonrpc") != "2.0" or not isinstance(payload.get("method"), str):
            return self._error(request_id, -32600, "Invalid Request")
        method = payload["method"]
        params = payload.get("params", {})
        if method == "notifications/initialized":
            return None
        if method == "server/discover":
            return self._result(request_id, {
                "resultType": "complete", "supportedVersions": [MCP_PROTOCOL_VERSION, *MCP_LEGACY_PROTOCOL_VERSIONS],
                "capabilities": {"tools": {}},
                "_meta": {"io.modelcontextprotocol/serverInfo": {"name": MCP_SERVER_NAME, "version": MCP_SERVER_VERSION}},
                "instructions": MCP_SERVER_INSTRUCTIONS, "ttlMs": 300000, "cacheScope": "public",
            })
        if method == "initialize":
            if not isinstance(params, Mapping) or not isinstance(params.get("protocolVersion"), str):
                return self._error(request_id, -32602, "Invalid initialize params")
            requested = params["protocolVersion"]
            selected = requested if requested in {MCP_PROTOCOL_VERSION, *MCP_LEGACY_PROTOCOL_VERSIONS} else MCP_LEGACY_PROTOCOL_VERSIONS[0]
            return self._result(request_id, {"protocolVersion": selected, "capabilities": {"tools": {"listChanged": False}}, "serverInfo": {"name": MCP_SERVER_NAME, "version": MCP_SERVER_VERSION}, "instructions": MCP_SERVER_INSTRUCTIONS})
        if method == "ping":
            return self._result(request_id, {})
        if method == "tools/list":
            return self._result(request_id, {"resultType": "complete", "tools": list(governance_mcp_tools()), "ttlMs": 300000, "cacheScope": "public"})
        if method == "tools/call":
            if not isinstance(params, Mapping) or set(params) - {"name", "arguments", "_meta", "inputResponses", "requestState"}:
                return self._error(request_id, -32602, "Invalid tools/call params")
            name = params.get("name")
            if name not in MCP_TOOL_NAMES:
                return self._error(request_id, -32602, "Unknown AgentGov tool")
            try:
                structured = self.adapter.call_tool(name, params.get("arguments", {}))
            except GovernanceMcpError as exc:
                diagnostic = exc.diagnostic()
                return self._result(request_id, {
                    "resultType": "complete",
                    "content": [{"type": "text", "text": str(exc)}],
                    "structuredContent": {"error": diagnostic},
                    "isError": True,
                })
            text = json.dumps(structured, ensure_ascii=False, sort_keys=True)
            return self._result(request_id, {"resultType": "complete", "content": [{"type": "text", "text": text}], "structuredContent": structured, "isError": False})
        return self._error(request_id, -32601, "Method not found")

    @staticmethod
    def _result(request_id: Any, result: Mapping[str, Any]) -> Mapping[str, Any]:
        return {"jsonrpc": "2.0", "id": request_id, "result": result}

    @staticmethod
    def _error(request_id: Any, code: int, message: str) -> Mapping[str, Any]:
        return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}

    def serve(self, input_stream: TextIO, output_stream: TextIO) -> int:
        for line in input_stream:
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                response = self._error(None, -32700, "Parse error")
            else:
                response = self.dispatch(payload)
            if response is not None:
                output_stream.write(json.dumps(response, ensure_ascii=False, sort_keys=True) + "\n")
                output_stream.flush()
        return 0
