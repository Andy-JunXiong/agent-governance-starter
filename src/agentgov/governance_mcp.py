"""Foreground MCP Adapter for governed alignment and active-Agent self-review."""

from __future__ import annotations

import json
import re
import subprocess
import unicodedata
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from pathlib import PurePosixPath
from typing import Any, Callable, Mapping, Sequence, TextIO

from agentgov.clarification_dialogue import denied_authority
from agentgov.alignment_transport import AlignmentStreamSession
from agentgov.change_scope import (
    GitInspectionError,
    ScopePolicyError,
    check_development_scope,
)
from agentgov.development_evidence import (
    EvidenceError,
    reconcile_task_completion,
    run_task_validation,
)
from agentgov.development_monitor import (
    build_development_monitor,
    write_development_monitor,
)
from agentgov.development_session import (
    SessionPolicyError,
    load_active_session,
    resolve_active_task,
)
from agentgov.drift_review import (
    DRIFT_DIMENSIONS,
    REVIEW_OUTCOMES,
    DriftReviewPolicyError,
    build_drift_review_record,
    build_drift_review_status,
    write_drift_review_record,
)
from agentgov.event_store import LocalStateError
from agentgov.git_snapshot import GitSnapshotError, capture_git_snapshot, snapshot_paths
from agentgov.host_interaction import build_host_interaction_capabilities
from agentgov.human_decision import canonical_document_digest
from agentgov.path_policy import evaluate_path_scope, scope_path_error
from agentgov.reference_alignment_adapter import (
    AlignmentContextDraft,
    ClarificationUpdateDraft,
    ReferenceAlignmentAdapter,
    ReferenceAlignmentAdapterError,
)
from agentgov.reference_task_proposal_adapter import (
    ReferenceTaskProposalAdapter,
    ReferenceTaskProposalAdapterError,
    TaskProposalDraft,
    TaskProposalPreparation,
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
from agentgov.task_proposal import (
    TaskProposalPolicyError,
    apply_task_admission_plan,
    render_task_admission_plan_json,
)
from agentgov.task_contract import load_development_task


MCP_PROTOCOL_VERSION = "2026-07-28"
MCP_LEGACY_PROTOCOL_VERSIONS = ("2025-11-25", "2025-06-18")
MCP_SERVER_NAME = "agentgov-governance"
MCP_SERVER_VERSION = "1.6.0"
MCP_NATIVE_ACCOUNTABLE_OWNER = "Human product owner"
MCP_BASE_TOOL_NAMES = (
    "agentgov_alignment_start",
    "agentgov_alignment_update",
    "agentgov_alignment_resolve",
    "agentgov_self_review_start",
    "agentgov_self_review_complete",
    "agentgov_task_completion_record",
)
MCP_TASK_COMPLETION_TOOL_NAME = MCP_BASE_TOOL_NAMES[-1]
MCP_TASK_PROPOSAL_TOOL_NAME = "agentgov_task_proposal_review"
MCP_DRIFT_REVIEW_TOOL_NAME = "agentgov_drift_review_record"
MCP_FORM_TOOL_NAMES = (
    MCP_TASK_PROPOSAL_TOOL_NAME,
    MCP_DRIFT_REVIEW_TOOL_NAME,
)
MCP_TOOL_NAMES = (*MCP_BASE_TOOL_NAMES, *MCP_FORM_TOOL_NAMES)
MAX_PROPOSAL_ELICITATION_MESSAGE_CHARACTERS = 24_000
MAX_DRIFT_REVIEW_ELICITATION_MESSAGE_CHARACTERS = 12_000
MCP_SERVER_INSTRUCTIONS = (
    "Use these tools without waiting for the user to name them. Before meaningful development "
    "with multiple reasonable product, requirement, architecture, scope, or implementation "
    "directions, or when asked to choose what to build, start alignment from normalized meaning. "
    "Do not use alignment merely for read-only explanation, diagnosis, status, or a fully specified "
    "low-risk change with no material direction choice. Answer only the exact pending question and "
    "let the human select the final offered direction; never select it for them. After implementing "
    "and validating any repository-changing task, run a distinct advisory review before completion. "
    "For a resolved alignment journey use the native active-Agent self-review tools; for a fully "
    "specified task without alignment, do not fabricate a journey handle and disclose a bounded "
    "current-Agent review without claiming native completion. If a required call fails, report "
    "the bounded failure and do not silently continue. Never send raw prompts, raw answers, "
    "transcripts, assistant messages, credentials, absolute paths, or source content. "
    "Before any repository write, require a readable, validated governance/tasks/*.json record "
    "that matches and explicitly authorizes that exact change with a human admitted or approved "
    "decision. A direct chat request, approval, authorization, tool permission, or unrelated, "
    "measurement-only, or differently scoped task is not that record. When no matching record "
    "exists, use the native proposal-review tool with normalized low-risk task meaning. Do not "
    "use proposal review for read-only work. Do not modify the repository if the required tool is "
    "unavailable or fails. That tool may create only the exact "
    "human-admitted task after a capability-negotiated form; ordinary tool permission is not task admission. "
    "After bounded implementation, use the task-completion-record tool for the exact admitted task. "
    "It may run only task-declared validation and append privacy-bounded local evidence; it never "
    "changes the human decision, proves semantic acceptance, starts or hands off a session, or grants authority. "
    "When the periodic drift reminder is due, perform an evidence-bounded advisory review, then "
    "use the native drift-review tool with only normalized candidate observations. The human alone "
    "chooses whether to record that exact candidate, snooze, or write nothing. "
    "No tool grants code, scope, exception, Git, release, deployment, or external authority."
)

_HANDLE_RE = re.compile(r"^mcpj-[0-9a-f]{32}$")
_PROMPT_ID_RE = re.compile(r"^cqp-[0-9a-f]{32}$")
_DECISION_ID_RE = re.compile(r"^dpr-[0-9a-f]{32}$")
_REQUEST_ID_RE = re.compile(r"^asq-[0-9a-f]{32}$")
_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_ID_RE = re.compile(r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$")
_SENSITIVE_INPUT_RE = re.compile(
    r"(?i)(?:api[_-]?key|access[_-]?token|auth[_-]?token|password|passwd|secret)\s*[:=]"
)
_ABSOLUTE_INPUT_PATH_RE = re.compile(
    r"(?i)(?:^|\s)(?:[a-z]:[\\/]|/(?:users|home|var|etc|tmp)/)"
)
_TASK_COMPLETION_PATH_RE = re.compile(
    r"^governance/tasks/(?:[a-z0-9][a-z0-9._-]*/)*[a-z0-9][a-z0-9._-]*\.json$"
)


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

    def materialize_task_proposal(self, request_text: str) -> None:
        raise GovernanceMcpError("MCP Adapter accepts only normalized task-proposal drafts")


def _alignment_input_error(*, stage: str, field_path: str, rule: str) -> None:
    raise GovernanceMcpError(
        "Normalized alignment input violates the indicated rule; correct it and retry",
        code="alignment_invalid_field",
        stage=stage,
        field_path=field_path,
        rule=rule,
        retryable=True,
    )


def _post_selection_input_error(*, stage: str, field_path: str, rule: str) -> None:
    raise GovernanceMcpError(
        "Normalized post-selection input violates the indicated rule; correct it and retry",
        code="post_selection_invalid_field",
        stage=stage,
        field_path=field_path,
        rule=rule,
        retryable=True,
    )


def _task_proposal_input_error(*, field_path: str, rule: str) -> None:
    raise GovernanceMcpError(
        "Normalized task-proposal input violates the indicated rule; correct it and retry",
        code="task_proposal_invalid_field",
        stage=MCP_TASK_PROPOSAL_TOOL_NAME,
        field_path=field_path,
        rule=rule,
        retryable=True,
    )


def _task_completion_input_error(*, field_path: str, rule: str) -> None:
    raise GovernanceMcpError(
        "Normalized task-completion input violates the indicated rule; correct it and retry",
        code="task_completion_invalid_field",
        stage=MCP_TASK_COMPLETION_TOOL_NAME,
        field_path=field_path,
        rule=rule,
        retryable=True,
    )


def _task_proposal_text(
    value: Any,
    *,
    field_path: str,
    minimum: int = 1,
    maximum: int = 1_000,
    repository_path: bool = False,
) -> str:
    if (
        not isinstance(value, str)
        or len(value.strip()) < minimum
        or len(value) > maximum
        or any(unicodedata.category(character).startswith("C") for character in value)
    ):
        _task_proposal_input_error(field_path=field_path, rule="normalized_text")
    if repository_path:
        if scope_path_error(value):
            _task_proposal_input_error(field_path=field_path, rule="repository_relative")
    elif _SENSITIVE_INPUT_RE.search(value) or _ABSOLUTE_INPUT_PATH_RE.search(value):
        _task_proposal_input_error(field_path=field_path, rule="privacy_boundary")
    return value


def _task_proposal_text_list(
    value: Any,
    *,
    field_path: str,
    minimum_items: int = 0,
    maximum_items: int = 25,
    item_maximum: int = 1_000,
    repository_paths: bool = False,
) -> tuple[str, ...]:
    if not isinstance(value, list):
        _task_proposal_input_error(field_path=field_path, rule="array_required")
    if len(value) < minimum_items:
        _task_proposal_input_error(field_path=field_path, rule="min_items")
    if len(value) > maximum_items:
        _task_proposal_input_error(field_path=field_path, rule="max_items")
    result = tuple(
        _task_proposal_text(
            item,
            field_path=f"{field_path}[{index}]",
            maximum=item_maximum,
            repository_path=repository_paths,
        )
        for index, item in enumerate(value)
    )
    if len(result) != len(set(result)):
        _task_proposal_input_error(field_path=field_path, rule="unique_items")
    return result


def _drift_review_input_error(*, field_path: str | None, rule: str) -> None:
    raise GovernanceMcpError(
        "Normalized drift-review input violates the indicated rule; correct it and retry",
        code="drift_review_invalid_field",
        stage=MCP_DRIFT_REVIEW_TOOL_NAME,
        field_path=field_path,
        rule=rule,
        retryable=True,
    )


def _drift_review_text(
    value: Any,
    *,
    field_path: str,
    maximum: int = 800,
) -> str:
    if (
        not isinstance(value, str)
        or not value.strip()
        or len(value) > maximum
        or any(unicodedata.category(character).startswith("C") for character in value)
        or _SENSITIVE_INPUT_RE.search(value)
        or _ABSOLUTE_INPUT_PATH_RE.search(value)
    ):
        _drift_review_input_error(field_path=field_path, rule="normalized_text")
    return value


def _drift_review_status_binding(status: Any) -> Mapping[str, Any]:
    observations = status.observations
    return {
        "state": status.state,
        "reason_codes": list(status.reason_codes),
        "cadence": dict(status.cadence),
        "completed_tasks_total": observations["completed_tasks_total"],
        "completed_tasks_since_review": observations["completed_tasks_since_review"],
        "last_reviewed_at": observations["last_reviewed_at"],
        "snoozed_until": observations["snoozed_until"],
        "policy_source": observations["policy_source"],
    }


def _normalized_input_text(
    value: Any,
    *,
    stage: str,
    field_path: str,
    maximum: int,
) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        _alignment_input_error(
            stage=stage, field_path=field_path, rule="normalized_text"
        )
    if any(unicodedata.category(character).startswith("C") for character in value):
        _alignment_input_error(
            stage=stage, field_path=field_path, rule="normalized_text"
        )
    if _SENSITIVE_INPUT_RE.search(value) or _ABSOLUTE_INPUT_PATH_RE.search(value):
        _alignment_input_error(
            stage=stage, field_path=field_path, rule="privacy_boundary"
        )
    return value


def _normalized_input_text_list(
    value: Any,
    *,
    stage: str,
    field_path: str,
    maximum_items: int = 50,
    minimum_items: int = 0,
    item_maximum: int = 400,
) -> tuple[str, ...]:
    if not isinstance(value, list):
        _alignment_input_error(stage=stage, field_path=field_path, rule="array_required")
    if len(value) > maximum_items:
        _alignment_input_error(stage=stage, field_path=field_path, rule="max_items")
    if len(value) < minimum_items:
        _alignment_input_error(stage=stage, field_path=field_path, rule="min_items")
    result = tuple(
        _normalized_input_text(
            item,
            stage=stage,
            field_path=f"{field_path}[{index}]",
            maximum=item_maximum,
        )
        for index, item in enumerate(value)
    )
    if len(result) != len(set(result)):
        _alignment_input_error(stage=stage, field_path=field_path, rule="unique_items")
    return result


def _validate_center_input(
    value: Any,
    *,
    stage: str,
    field_path: str,
    patch: bool = False,
) -> Mapping[str, Any]:
    fields = {"outcome", "why_now", "success_signals", "constraints", "non_goals"}
    if not isinstance(value, Mapping) or set(value) != fields:
        _alignment_input_error(stage=stage, field_path=field_path, rule="exact_fields")
    for key in ("outcome", "why_now"):
        item = value[key]
        if patch and item is None:
            continue
        _normalized_input_text(
            item, stage=stage, field_path=f"{field_path}.{key}", maximum=800
        )
    for key in ("success_signals", "constraints", "non_goals"):
        item = value[key]
        if patch and item is None:
            continue
        _normalized_input_text_list(
            item,
            stage=stage,
            field_path=f"{field_path}.{key}",
            minimum_items=0 if patch or key != "success_signals" else 1,
        )
    return value


def _validate_drift_input(
    value: Any, *, stage: str, field_path: str
) -> Mapping[str, Any]:
    fields = {"kind", "semantics", "observation", "evidence_refs", "impact"}
    if not isinstance(value, Mapping) or set(value) != fields:
        _alignment_input_error(stage=stage, field_path=field_path, rule="exact_fields")
    kind = value["kind"]
    semantics = value["semantics"]
    if kind not in {"business", "requirement", "architecture", "scope", "implementation"}:
        _alignment_input_error(stage=stage, field_path=f"{field_path}.kind", rule="enum")
    if semantics not in {"advisory", "deterministic"}:
        _alignment_input_error(
            stage=stage, field_path=f"{field_path}.semantics", rule="enum"
        )
    if kind in {"business", "requirement", "architecture"} and semantics != "advisory":
        _alignment_input_error(
            stage=stage,
            field_path=f"{field_path}.semantics",
            rule="advisory_required",
        )
    _normalized_input_text(
        value["observation"],
        stage=stage,
        field_path=f"{field_path}.observation",
        maximum=800,
    )
    evidence = _normalized_input_text_list(
        value["evidence_refs"],
        stage=stage,
        field_path=f"{field_path}.evidence_refs",
        maximum_items=20,
        item_maximum=240,
    )
    if any(scope_path_error(item) for item in evidence):
        _alignment_input_error(
            stage=stage,
            field_path=f"{field_path}.evidence_refs",
            rule="repository_relative",
        )
    _normalized_input_text(
        value["impact"],
        stage=stage,
        field_path=f"{field_path}.impact",
        maximum=800,
    )
    return value


@dataclass
class _Journey:
    adapter: ReferenceAlignmentAdapter
    self_review: ActiveAgentSelfReviewStreamSession
    self_review_sequence: int = 0
    review_requested: bool = False
    review_completed: bool = False
    pending_review_request: Mapping[str, str] | None = None
    allowed_review_evidence_refs: tuple[str, ...] = ()


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
    if len(value) > 100:
        _alignment_input_error(stage=stage, field_path=field_path, rule="max_items")
    expected = {"question", "why_matters", "material", "priority"}
    questions = []
    for index, item in enumerate(value):
        item_path = f"{field_path}[{index}]"
        if not isinstance(item, Mapping) or set(item) != expected:
            raise GovernanceMcpError(
                f"{field_path} item has unexpected fields",
                code="alignment_invalid_field",
                stage=stage,
                field_path=item_path,
                rule="exact_fields",
                retryable=True,
            )
        _normalized_input_text(
            item["question"],
            stage=stage,
            field_path=f"{item_path}.question",
            maximum=800,
        )
        _normalized_input_text(
            item["why_matters"],
            stage=stage,
            field_path=f"{item_path}.why_matters",
            maximum=800,
        )
        if not isinstance(item["material"], bool):
            _alignment_input_error(
                stage=stage,
                field_path=f"{item_path}.material",
                rule="boolean_required",
            )
        priority = item["priority"]
        if (
            not isinstance(priority, int)
            or isinstance(priority, bool)
            or not 1 <= priority <= 5
        ):
            _alignment_input_error(
                stage=stage,
                field_path=f"{item_path}.priority",
                rule="range",
            )
        questions.append({"question_id": f"qst-{uuid.uuid4().hex[:16]}", **item})
    return tuple(questions)


def _validate_candidate_resolutions(
    value: Any, *, stage: str, field_path: str
) -> tuple[Mapping[str, Any], ...]:
    if not isinstance(value, list):
        _alignment_input_error(stage=stage, field_path=field_path, rule="array_required")
    if len(value) > 5:
        _alignment_input_error(stage=stage, field_path=field_path, rule="max_items")
    allowed_ids = {
        "return_to_center",
        "adopt_new_center",
        "split_new_requirement",
        "continue_exploration",
        "stop",
    }
    result: list[Mapping[str, Any]] = []
    seen_ids: set[str] = set()
    for index, item in enumerate(value):
        item_path = f"{field_path}[{index}]"
        if not isinstance(item, Mapping) or set(item) != {
            "id", "label", "effect", "center_patch"
        }:
            _alignment_input_error(
                stage=stage, field_path=item_path, rule="exact_fields"
            )
        option_id = item["id"]
        if option_id not in allowed_ids:
            _alignment_input_error(
                stage=stage, field_path=f"{item_path}.id", rule="enum"
            )
        if option_id in seen_ids:
            _alignment_input_error(
                stage=stage, field_path=f"{item_path}.id", rule="unique_items"
            )
        _normalized_input_text(
            item["label"],
            stage=stage,
            field_path=f"{item_path}.label",
            maximum=120,
        )
        _normalized_input_text(
            item["effect"],
            stage=stage,
            field_path=f"{item_path}.effect",
            maximum=800,
        )
        patch = _validate_center_input(
            item["center_patch"],
            stage=stage,
            field_path=f"{item_path}.center_patch",
            patch=True,
        )
        has_patch = any(patch_value is not None for patch_value in patch.values())
        if option_id == "adopt_new_center" and not has_patch:
            _alignment_input_error(
                stage=stage,
                field_path=f"{item_path}.center_patch",
                rule="adopt_patch_required",
            )
        if option_id != "adopt_new_center" and has_patch:
            _alignment_input_error(
                stage=stage,
                field_path=f"{item_path}.center_patch",
                rule="patch_forbidden",
            )
        seen_ids.add(option_id)
        result.append(dict(item))
    return tuple(result)


def _alignment_rejection(exc: BaseException, *, stage: str) -> GovernanceMcpError:
    if stage == MCP_TOOL_NAMES[0]:
        return GovernanceMcpError(
            "Core rejected a schema-aligned start after Adapter input validation",
            code="alignment_rejected_internal",
            stage=stage,
            field_path=None,
            rule="unclassified",
            retryable=False,
        )
    cause = exc.__cause__
    message = str(cause) if isinstance(cause, ValueError) else ""
    mappings = (
        ("alignment center has unexpected fields", "center", "exact_fields"),
        ("alignment center requires at least one success signal", "center.success_signals", "min_items"),
        ("drift observation has unexpected fields", "drift", "exact_fields"),
        ("drift kind or semantics is unsupported", "drift", "enum"),
        ("drift must remain advisory", "drift.semantics", "advisory_required"),
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


def _binding(
    value: Any,
    *,
    fields: set[str],
    identifier: re.Pattern[str],
    label: str,
    stage: str | None = None,
    field_path: str | None = None,
) -> Mapping[str, Any]:
    if not isinstance(value, Mapping) or set(value) != fields:
        if stage is not None and field_path is not None:
            _post_selection_input_error(
                stage=stage, field_path=field_path, rule="exact_fields"
            )
        raise GovernanceMcpError(f"{label} binding is invalid")
    identity = value.get(next(iter(fields - {"digest"})))
    digest = value.get("digest")
    if (
        not isinstance(identity, str)
        or not identifier.fullmatch(identity)
        or not isinstance(digest, str)
        or not _DIGEST_RE.fullmatch(digest)
    ):
        if stage is not None and field_path is not None:
            _post_selection_input_error(
                stage=stage, field_path=field_path, rule="digest_binding"
            )
        raise GovernanceMcpError(f"{label} binding is invalid")
    return dict(value)


def _post_selection_text_list(
    value: Any,
    *,
    stage: str,
    field_path: str,
    maximum_items: int = 50,
    minimum_items: int = 1,
    item_maximum: int = 400,
) -> tuple[str, ...]:
    try:
        return _normalized_input_text_list(
            value,
            stage=stage,
            field_path=field_path,
            maximum_items=maximum_items,
            minimum_items=minimum_items,
            item_maximum=item_maximum,
        )
    except GovernanceMcpError as exc:
        raise GovernanceMcpError(
            str(exc),
            code="post_selection_invalid_field",
            stage=stage,
            field_path=exc.field_path,
            rule=exc.rule,
            retryable=True,
        ) from exc


def _post_selection_identifiers(
    value: Any, *, stage: str, field_path: str, maximum_items: int = 50
) -> tuple[str, ...]:
    identifiers = _post_selection_text_list(
        value,
        stage=stage,
        field_path=field_path,
        maximum_items=maximum_items,
    )
    for index, identifier in enumerate(identifiers):
        if len(identifier) > 120 or not _ID_RE.fullmatch(identifier):
            _post_selection_input_error(
                stage=stage,
                field_path=f"{field_path}[{index}]",
                rule="normalized_identifier",
            )
    return identifiers


def _post_selection_text(value: Any, *, stage: str, field_path: str, maximum: int) -> str:
    try:
        return _normalized_input_text(
            value, stage=stage, field_path=field_path, maximum=maximum
        )
    except GovernanceMcpError as exc:
        raise GovernanceMcpError(
            str(exc), code="post_selection_invalid_field", stage=stage,
            field_path=exc.field_path, rule=exc.rule, retryable=True,
        ) from exc


def _validate_evidence_refs(value: Any, *, stage: str, field_path: str) -> tuple[str, ...]:
    refs = _post_selection_text_list(
        value,
        stage=stage,
        field_path=field_path,
        maximum_items=20,
        item_maximum=240,
    )
    if any(scope_path_error(item) for item in refs):
        _post_selection_input_error(
            stage=stage, field_path=field_path, rule="repository_relative"
        )
    return refs


def _validate_review_observations(
    value: Any,
    *,
    stage: str,
    allowed_evidence_refs: Sequence[str],
) -> tuple[Mapping[str, Any], ...]:
    if not isinstance(value, list):
        _post_selection_input_error(
            stage=stage, field_path="observations", rule="array_required"
        )
    if not 1 <= len(value) <= 20:
        _post_selection_input_error(
            stage=stage, field_path="observations", rule="item_count"
        )
    fields = {
        "kind", "summary", "evidence_refs", "assumptions", "unknowns",
        "recommended_question",
    }
    allowed_kinds = {
        "business", "requirement", "architecture", "scope", "implementation",
        "security", "data",
    }
    result: list[Mapping[str, Any]] = []
    for index, item in enumerate(value):
        path = f"observations[{index}]"
        if not isinstance(item, Mapping) or set(item) != fields:
            _post_selection_input_error(
                stage=stage, field_path=path, rule="exact_fields"
            )
        if not isinstance(item["kind"], str) or item["kind"] not in allowed_kinds:
            _post_selection_input_error(
                stage=stage, field_path=f"{path}.kind", rule="enum"
            )
        _post_selection_text(
            item["summary"], stage=stage, field_path=f"{path}.summary", maximum=800
        )
        evidence_refs = _validate_evidence_refs(
            item["evidence_refs"], stage=stage, field_path=f"{path}.evidence_refs"
        )
        if not set(evidence_refs) <= set(allowed_evidence_refs):
            _post_selection_input_error(
                stage=stage,
                field_path=f"{path}.evidence_refs",
                rule="allowed_evidence",
            )
        for field in ("assumptions", "unknowns"):
            _post_selection_text_list(
                item[field],
                stage=stage,
                field_path=f"{path}.{field}",
                maximum_items=20,
                minimum_items=0,
            )
        question = item["recommended_question"]
        if question is not None:
            _post_selection_text(
                question,
                stage=stage,
                field_path=f"{path}.recommended_question",
                maximum=800,
            )
        result.append(dict(item))
    if len({canonical_document_digest(item) for item in result}) != len(result):
        _post_selection_input_error(
            stage=stage, field_path="observations", rule="unique_items"
        )
    return tuple(result)


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


def _text_list_schema(*, maximum_items: int = 50) -> Mapping[str, Any]:
    return {"type": "array", "maxItems": maximum_items, "uniqueItems": True, "items": {"type": "string", "minLength": 1, "maxLength": 400}}


def _center_schema(*, patch: bool = False) -> Mapping[str, Any]:
    text = {"type": "string", "minLength": 1, "maxLength": 800}
    items = _text_list_schema()
    if patch:
        text = {"anyOf": [text, {"type": "null"}]}
        items = {"anyOf": [items, {"type": "null"}]}
    success_items = dict(items)
    if not patch:
        success_items["minItems"] = 1
    return {
        "type": "object", "additionalProperties": False,
        "required": ["outcome", "why_now", "success_signals", "constraints", "non_goals"],
        "properties": {"outcome": text, "why_now": text, "success_signals": success_items, "constraints": items, "non_goals": items},
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
        "allOf": [
            {
                "if": {
                    "properties": {
                        "kind": {
                            "enum": ["business", "requirement", "architecture"]
                        }
                    },
                    "required": ["kind"],
                },
                "then": {"properties": {"semantics": {"const": "advisory"}}},
            }
        ],
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
    schema = {
        "type": "object", "additionalProperties": False,
        "required": ["id", "label", "effect", "center_patch"],
        "properties": {
            "id": {"enum": ["return_to_center", "adopt_new_center", "split_new_requirement", "continue_exploration", "stop"]},
            "label": {"type": "string", "minLength": 1, "maxLength": 120},
            "effect": {"type": "string", "minLength": 1, "maxLength": 800},
            "center_patch": _center_schema(patch=True),
        },
    }
    non_null_patch_properties = []
    for key in ("outcome", "why_now"):
        non_null_patch_properties.append(
            {"properties": {"center_patch": {"properties": {key: {"type": "string"}}}}}
        )
    for key in ("success_signals", "constraints", "non_goals"):
        non_null_patch_properties.append(
            {"properties": {"center_patch": {"properties": {key: {"type": "array"}}}}}
        )
    null_patch = {
        "properties": {
            "center_patch": {
                "properties": {
                    key: {"const": None}
                    for key in ("outcome", "why_now", "success_signals", "constraints", "non_goals")
                }
            }
        }
    }
    schema["allOf"] = [
        {
            "if": {
                "properties": {"id": {"const": "adopt_new_center"}},
                "required": ["id"],
            },
            "then": {"anyOf": non_null_patch_properties},
            "else": null_patch,
        }
    ]
    return schema


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
            "assumptions": _text_list_schema(maximum_items=20),
            "unknowns": _text_list_schema(maximum_items=20),
            "recommended_question": {"anyOf": [{"type": "null"}, {"type": "string", "minLength": 1, "maxLength": 800}]},
        },
    }


def _task_proposal_scope_schema() -> Mapping[str, Any]:
    path_items = {"type": "string", "minLength": 1, "maxLength": 400}
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["include_paths", "exclude_paths"],
        "properties": {
            "include_paths": {
                "type": "array",
                "minItems": 1,
                "maxItems": 25,
                "uniqueItems": True,
                "items": path_items,
            },
            "exclude_paths": {
                "type": "array",
                "maxItems": 25,
                "uniqueItems": True,
                "items": path_items,
            },
        },
    }


def _task_proposal_input_schema() -> Mapping[str, Any]:
    text_list = {
        "type": "array",
        "maxItems": 25,
        "uniqueItems": True,
        "items": {"type": "string", "minLength": 1, "maxLength": 1_000},
    }
    required_text_list = dict(text_list, minItems=1)
    fields = {
        "task_id": {
            "type": "string",
            "minLength": 1,
            "maxLength": 100,
            "pattern": "^[a-z0-9]+(?:-[a-z0-9]+)*$",
        },
        "title": {"type": "string", "minLength": 5, "maxLength": 200},
        "requirement_summary": {
            "type": "string",
            "minLength": 10,
            "maxLength": 1_000,
        },
        "scope": _task_proposal_scope_schema(),
        "acceptance_signals": required_text_list,
        "validation_commands": required_text_list,
        "risk_items": text_list,
        "assumptions": text_list,
        "unknowns": text_list,
    }
    return _tool_schema(fields, tuple(fields))


def _drift_review_input_schema() -> Mapping[str, Any]:
    fields = {
        "candidate_outcome": {"enum": sorted(REVIEW_OUTCOMES)},
        "observations": {
            "type": "array",
            "minItems": len(DRIFT_DIMENSIONS),
            "maxItems": len(DRIFT_DIMENSIONS),
            "uniqueItems": True,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["dimension", "finding"],
                "properties": {
                    "dimension": {"enum": list(DRIFT_DIMENSIONS)},
                    "finding": {"type": "string", "minLength": 1, "maxLength": 800},
                },
            },
        },
        "evidence_refs": {
            "type": "array",
            "minItems": 1,
            "maxItems": 12,
            "uniqueItems": True,
            "items": {"type": "string", "minLength": 1, "maxLength": 240},
        },
    }
    return _tool_schema(fields, tuple(fields))


def governance_mcp_tools() -> tuple[Mapping[str, Any], ...]:
    """Return a deterministic tool catalog with strict top-level input schemas."""

    common_annotations = {
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": False,
    }
    start_input_schema = _tool_schema(
        {
            "subject_type": {"enum": ["work_request", "active_task", "architecture"]},
            "subject_id": {"type": "string", "pattern": "^[a-z0-9]+(?:[._-][a-z0-9]+)*$"},
            "center": _center_schema(),
            "drift": _drift_schema(),
            "assumptions": _text_list_schema(),
            "unknowns": {"type": "array", "maxItems": 100, "items": _question_schema()},
            "candidate_resolutions": {"type": "array", "maxItems": 5, "items": _resolution_schema()},
            "recommended_resolution_id": {"anyOf": [{"type": "string"}, {"type": "null"}]},
        },
        ("subject_type", "subject_id", "center", "drift", "assumptions", "unknowns", "candidate_resolutions", "recommended_resolution_id"),
    )
    start_input_schema["allOf"] = [
        {
            "if": {
                "properties": {"unknowns": {"maxItems": 0}},
                "required": ["unknowns"],
            },
            "then": {
                "properties": {
                    "candidate_resolutions": {"minItems": 2},
                    "recommended_resolution_id": {"type": "string"},
                }
            },
        }
    ]
    tools = (
        {
            "name": MCP_TOOL_NAMES[0],
            "title": "Start governed alignment",
            "description": "Use before meaningful development when multiple reasonable directions exist or the Agent is asked to choose what to build. Start one foreground alignment journey from normalized meaning; the human must select the final direction. Do not use for read-only or fully specified low-risk work.",
            "inputSchema": start_input_schema,
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
                {
                    "journey_handle": _handle_schema(),
                    "reason_codes": {
                        "type": "array", "minItems": 1, "maxItems": 50,
                        "uniqueItems": True,
                        "items": {
                            "type": "string", "maxLength": 120,
                            "pattern": "^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$",
                        },
                    },
                    "allowed_evidence_refs": {
                        "type": "array", "minItems": 1, "maxItems": 20,
                        "uniqueItems": True,
                        "items": {"type": "string", "minLength": 1, "maxLength": 240},
                    },
                },
                ("journey_handle", "reason_codes", "allowed_evidence_refs"),
            ),
            "annotations": common_annotations,
        },
        {
            "name": MCP_TOOL_NAMES[4],
            "title": "Complete active-Agent self-review",
            "description": "Submit normalized observations for the exact pending self-review request.",
            "inputSchema": _tool_schema(
                {"journey_handle": _handle_schema(), "request": _digest_binding_schema("request_id", "^asq-[0-9a-f]{32}$"), "observations": {"type": "array", "minItems": 1, "maxItems": 20, "uniqueItems": True, "items": _observation_schema()}},
                ("journey_handle", "request", "observations"),
            ),
            "annotations": common_annotations,
        },
        {
            "name": MCP_TASK_COMPLETION_TOOL_NAME,
            "title": "Record deterministic task completion evidence",
            "description": (
                "Use after bounded implementation for one exact human-admitted task. "
                "Revalidate its complete Git scope, run only its declared validation commands, "
                "and append privacy-bounded local validation and completion evidence. This tool "
                "does not edit the task decision, prove human acceptance, start or hand off a "
                "session, or authorize source changes, Git operations, release, or deployment."
            ),
            "inputSchema": _tool_schema(
                {
                    "task_path": {
                        "type": "string",
                        "minLength": 1,
                        "maxLength": 400,
                        "pattern": _TASK_COMPLETION_PATH_RE.pattern,
                    }
                },
                ("task_path",),
            ),
            "annotations": {
                "readOnlyHint": False,
                "destructiveHint": False,
                "idempotentHint": False,
                "openWorldHint": False,
            },
        },
        {
            "name": MCP_TASK_PROPOSAL_TOOL_NAME,
            "title": "Prepare and review a low-risk task proposal",
            "description": (
                "Use before any repository write when no readable, validated governance/tasks/*.json "
                "record matches and authorizes that exact change with a human admitted or approved "
                "decision. A direct chat request, approval, authorization, tool permission, or an "
                "unrelated, measurement-only, or differently scoped task does not count; read-only "
                "work does not need proposal review. Materialize only normalized low-risk task meaning from the "
                "current conversation. AgentGov "
                "creates the strict proposal and opens one native human review form; never "
                "supply raw chat, proposal identity, authority, repository identity, an "
                "accountable-owner identity, or a human decision. The Adapter binds the "
                "canonical human owner role, and the task is created only after exact "
                "native admission."
            ),
            "inputSchema": _task_proposal_input_schema(),
            "annotations": {
                "readOnlyHint": False,
                "destructiveHint": False,
                "idempotentHint": False,
                "openWorldHint": False,
            },
        },
        {
            "name": MCP_DRIFT_REVIEW_TOOL_NAME,
            "title": "Review and record a due drift reminder",
            "description": (
                "Use only after the shared periodic drift reminder is due and the current "
                "Agent has completed a distinct evidence-bounded advisory review. Supply one "
                "normalized candidate outcome, exactly one observation for requirement, "
                "architecture, and functionality, and only repository-relative evidence "
                "references. Never supply or infer the human decision. AgentGov opens one "
                "native form; only the human may record the exact candidate, snooze the "
                "configured interval, or create no record."
            ),
            "inputSchema": _drift_review_input_schema(),
            "annotations": {
                "readOnlyHint": False,
                "destructiveHint": False,
                "idempotentHint": False,
                "openWorldHint": False,
            },
        },
    )
    return tools


class GovernanceMcpAdapter:
    """Host-neutral tools with foreground journeys and bounded local records."""

    def __init__(
        self,
        *,
        adapter_id: str,
        provider: SemanticReviewProviderCapabilities,
        repository: Path | None = None,
    ) -> None:
        if not isinstance(adapter_id, str) or not _ID_RE.fullmatch(adapter_id):
            raise GovernanceMcpError("MCP adapter_id is invalid")
        normalized_provider = semantic_review_provider_capabilities_from_payload(asdict(provider))
        if normalized_provider.adapter_id != adapter_id:
            raise GovernanceMcpError("MCP Provider adapter_id does not match the host Adapter")
        self.adapter_id = adapter_id
        self.provider = normalized_provider
        self.repository = repository
        self._journeys: dict[str, _Journey] = {}

    def call_tool(self, name: str, arguments: Any) -> Mapping[str, Any]:
        dispatch = {
            MCP_TOOL_NAMES[0]: self._alignment_start,
            MCP_TOOL_NAMES[1]: self._alignment_update,
            MCP_TOOL_NAMES[2]: self._alignment_resolve,
            MCP_TOOL_NAMES[3]: self._self_review_start,
            MCP_TOOL_NAMES[4]: self._self_review_complete,
            MCP_TASK_COMPLETION_TOOL_NAME: self._task_completion_record,
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

    def prepare_task_proposal(self, value: Any) -> TaskProposalPreparation:
        """Build an exact read-only plan from one Codex-materialized draft."""

        fields = {
            "task_id",
            "title",
            "requirement_summary",
            "scope",
            "acceptance_signals",
            "validation_commands",
            "risk_items",
            "assumptions",
            "unknowns",
        }
        args = _exact_arguments(value, fields, tool=MCP_TASK_PROPOSAL_TOOL_NAME)
        task_id = _task_proposal_text(
            args["task_id"], field_path="task_id", maximum=100
        )
        if not re.fullmatch(r"^[a-z0-9]+(?:-[a-z0-9]+)*$", task_id):
            _task_proposal_input_error(field_path="task_id", rule="kebab_case")
        title = _task_proposal_text(
            args["title"], field_path="title", minimum=5, maximum=200
        )
        summary = _task_proposal_text(
            args["requirement_summary"],
            field_path="requirement_summary",
            minimum=10,
            maximum=1_000,
        )
        scope = args["scope"]
        if not isinstance(scope, Mapping) or set(scope) != {
            "include_paths",
            "exclude_paths",
        }:
            _task_proposal_input_error(field_path="scope", rule="exact_fields")
        include_paths = _task_proposal_text_list(
            scope["include_paths"],
            field_path="scope.include_paths",
            minimum_items=1,
            item_maximum=400,
            repository_paths=True,
        )
        exclude_paths = _task_proposal_text_list(
            scope["exclude_paths"],
            field_path="scope.exclude_paths",
            item_maximum=400,
            repository_paths=True,
        )
        if set(include_paths) & set(exclude_paths):
            _task_proposal_input_error(field_path="scope", rule="disjoint_paths")
        draft = TaskProposalDraft(
            task_id=task_id,
            title=title,
            requirement_summary=summary,
            include_paths=include_paths,
            exclude_paths=exclude_paths,
            acceptance_signals=_task_proposal_text_list(
                args["acceptance_signals"],
                field_path="acceptance_signals",
                minimum_items=1,
            ),
            validation_commands=_task_proposal_text_list(
                args["validation_commands"],
                field_path="validation_commands",
                minimum_items=1,
            ),
            owner=MCP_NATIVE_ACCOUNTABLE_OWNER,
            risk_items=_task_proposal_text_list(
                args["risk_items"], field_path="risk_items"
            ),
            assumptions=_task_proposal_text_list(
                args["assumptions"], field_path="assumptions"
            ),
            unknowns=_task_proposal_text_list(
                args["unknowns"], field_path="unknowns"
            ),
        )
        if self.repository is None:
            raise GovernanceMcpError(
                "MCP task-proposal review has no locally bound repository",
                code="task_proposal_repository_unavailable",
                stage=MCP_TASK_PROPOSAL_TOOL_NAME,
                field_path=None,
                rule="local_repository_binding",
                retryable=False,
            )
        try:
            return ReferenceTaskProposalAdapter(
                _NormalizedOnlyMaterializer(),
                adapter_id=self.adapter_id,
            ).prepare_from_draft(self.repository, draft)
        except ReferenceTaskProposalAdapterError as exc:
            raise GovernanceMcpError(
                str(exc),
                code="task_proposal_rejected",
                stage=MCP_TASK_PROPOSAL_TOOL_NAME,
                field_path=None,
                rule="strict_proposal_contract",
                retryable=True,
            ) from exc
        except OSError as exc:
            raise GovernanceMcpError(
                "Local repository state prevented safe task-proposal preparation",
                code="task_proposal_repository_unavailable",
                stage=MCP_TASK_PROPOSAL_TOOL_NAME,
                field_path=None,
                rule="local_repository_binding",
                retryable=False,
            ) from exc

    def complete_task_proposal_review(
        self,
        preparation: TaskProposalPreparation,
        response: Any,
    ) -> Mapping[str, Any]:
        """Apply only one exact native admit response to the reviewed plan."""

        if not isinstance(response, Mapping):
            raise GovernanceMcpError(
                "Native proposal review response is malformed",
                code="task_proposal_review_invalid",
                stage=MCP_TASK_PROPOSAL_TOOL_NAME,
                field_path="elicitation_response",
                rule="object",
                retryable=False,
            )
        action = response.get("action")
        if action not in {"accept", "decline", "cancel"}:
            raise GovernanceMcpError(
                "Native proposal review action is invalid",
                code="task_proposal_review_invalid",
                stage=MCP_TASK_PROPOSAL_TOOL_NAME,
                field_path="elicitation_response.action",
                rule="enum",
                retryable=False,
            )
        content = response.get("content")
        decision: str | None = None
        if action == "accept":
            if not isinstance(content, Mapping) or set(content) != {"decision"}:
                raise GovernanceMcpError(
                    "Accepted native proposal review content is invalid",
                    code="task_proposal_review_invalid",
                    stage=MCP_TASK_PROPOSAL_TOOL_NAME,
                    field_path="elicitation_response.content",
                    rule="exact_decision",
                    retryable=False,
                )
            decision = content.get("decision")
            if not isinstance(decision, str) or decision not in {
                "admit", "request_changes", "reject"
            }:
                raise GovernanceMcpError(
                    "Native proposal review decision is invalid",
                    code="task_proposal_review_invalid",
                    stage=MCP_TASK_PROPOSAL_TOOL_NAME,
                    field_path="elicitation_response.content.decision",
                    rule="enum",
                    retryable=False,
                )
        elif content is not None:
            raise GovernanceMcpError(
                "Declined or cancelled native proposal review must not include content",
                code="task_proposal_review_invalid",
                stage=MCP_TASK_PROPOSAL_TOOL_NAME,
                field_path="elicitation_response.content",
                rule="absent",
                retryable=False,
            )

        status = {
            "decline": "declined",
            "cancel": "cancelled",
        }.get(
            action,
            {"admit": "admitted", "request_changes": "changes_requested", "reject": "rejected"}.get(decision),
        )
        modified = False
        if action == "accept" and decision == "admit":
            try:
                apply_task_admission_plan(preparation.plan)
            except TaskProposalPolicyError as exc:
                raise GovernanceMcpError(
                    str(exc),
                    code="task_proposal_plan_stale",
                    stage=MCP_TASK_PROPOSAL_TOOL_NAME,
                    field_path="admission_plan",
                    rule="revalidation",
                    retryable=False,
                ) from exc
            except OSError as exc:
                raise GovernanceMcpError(
                    "Local repository state prevented safe task admission",
                    code="task_proposal_plan_stale",
                    stage=MCP_TASK_PROPOSAL_TOOL_NAME,
                    field_path="admission_plan",
                    rule="revalidation",
                    retryable=False,
                ) from exc
            status = "admitted"
            modified = True

        return {
            "contract": "agentgov.task-proposal-review-result",
            "schema_version": "1.0",
            "status": status,
            "proposal": {
                "proposal_id": preparation.plan.proposal["proposal_id"],
                "proposal_digest": preparation.plan.proposal_digest,
                "target": preparation.plan.target,
                "task_digest": preparation.plan.task_digest,
            },
            "review": {
                "surface": "mcp_form_elicitation",
                "action": action,
                "decision": decision,
            },
            "execution": {
                "semantic_materialization_owner": "current_coding_agent_host",
                "user_authored_structured_records": 0,
                "agentgov_model_calls": 0,
                "agentgov_network_calls": 0,
                "core_received_raw_conversation": False,
            },
            "authority_boundary": {
                "repository_modified": modified,
                "task_admitted": modified,
                "starts_session": False,
                "authorizes_code_change": False,
                "authorizes_scope_expansion": False,
                "authorizes_exception": False,
                "authorizes_git_operations": False,
                "authorizes_publication": False,
                "authorizes_deployment": False,
                "authorizes_release": False,
            },
        }

    def prepare_drift_review(self, value: Any) -> Mapping[str, Any]:
        """Bind one advisory candidate to the current due state before elicitation."""

        args = _exact_arguments(
            value,
            {"candidate_outcome", "observations", "evidence_refs"},
            tool=MCP_DRIFT_REVIEW_TOOL_NAME,
        )
        candidate = args["candidate_outcome"]
        if candidate not in REVIEW_OUTCOMES:
            _drift_review_input_error(field_path="candidate_outcome", rule="enum")
        raw_observations = args["observations"]
        if not isinstance(raw_observations, list) or len(raw_observations) != len(
            DRIFT_DIMENSIONS
        ):
            _drift_review_input_error(field_path="observations", rule="item_count")
        observations: list[Mapping[str, str]] = []
        seen_dimensions: set[str] = set()
        for index, item in enumerate(raw_observations):
            path = f"observations[{index}]"
            if not isinstance(item, Mapping) or set(item) != {"dimension", "finding"}:
                _drift_review_input_error(field_path=path, rule="exact_fields")
            dimension = item.get("dimension")
            if dimension not in DRIFT_DIMENSIONS or dimension in seen_dimensions:
                _drift_review_input_error(
                    field_path=f"{path}.dimension", rule="dimension_set"
                )
            seen_dimensions.add(dimension)
            observations.append(
                {
                    "dimension": dimension,
                    "finding": _drift_review_text(
                        item.get("finding"), field_path=f"{path}.finding"
                    ),
                }
            )
        if seen_dimensions != set(DRIFT_DIMENSIONS):
            _drift_review_input_error(field_path="observations", rule="dimension_set")

        raw_refs = args["evidence_refs"]
        if not isinstance(raw_refs, list) or not 1 <= len(raw_refs) <= 12:
            _drift_review_input_error(field_path="evidence_refs", rule="item_count")
        if len(raw_refs) != len(set(raw_refs)):
            _drift_review_input_error(field_path="evidence_refs", rule="unique_items")
        if self.repository is None:
            raise GovernanceMcpError(
                "MCP drift review has no locally bound repository",
                code="drift_review_repository_unavailable",
                stage=MCP_DRIFT_REVIEW_TOOL_NAME,
                field_path=None,
                rule="local_repository_binding",
                retryable=False,
            )
        try:
            root = self.repository.resolve(strict=True)
        except OSError as exc:
            raise GovernanceMcpError(
                "MCP drift review cannot resolve its locally bound repository",
                code="drift_review_repository_unavailable",
                stage=MCP_DRIFT_REVIEW_TOOL_NAME,
                field_path=None,
                rule="local_repository_binding",
                retryable=False,
            ) from exc
        evidence_refs: list[str] = []
        for index, raw_ref in enumerate(raw_refs):
            field_path = f"evidence_refs[{index}]"
            if (
                not isinstance(raw_ref, str)
                or len(raw_ref) > 240
                or scope_path_error(raw_ref)
            ):
                _drift_review_input_error(
                    field_path=field_path, rule="repository_relative"
                )
            try:
                target = (root / raw_ref).resolve()
            except OSError:
                _drift_review_input_error(field_path=field_path, rule="readable_evidence")
            try:
                target.relative_to(root)
            except ValueError:
                _drift_review_input_error(
                    field_path=field_path, rule="repository_relative"
                )
            if not target.is_file():
                _drift_review_input_error(field_path=field_path, rule="readable_evidence")
            evidence_refs.append(raw_ref)

        try:
            status = build_drift_review_status(root)
        except (DriftReviewPolicyError, LocalStateError, OSError, UnicodeError) as exc:
            raise GovernanceMcpError(
                "Local repository state prevented safe drift-review preparation",
                code="drift_review_repository_unavailable",
                stage=MCP_DRIFT_REVIEW_TOOL_NAME,
                field_path=None,
                rule="local_repository_binding",
                retryable=False,
            ) from exc
        if status.state != "due":
            raise GovernanceMcpError(
                "The shared drift-review cadence is not currently due",
                code="drift_review_not_due",
                stage=MCP_DRIFT_REVIEW_TOOL_NAME,
                field_path=None,
                rule="due_state_required",
                retryable=False,
            )
        binding = _drift_review_status_binding(status)
        return {
            "candidate_outcome": candidate,
            "observations": observations,
            "evidence_refs": evidence_refs,
            "due_state": binding,
            "due_state_digest": canonical_document_digest(binding),
        }

    def complete_drift_review(
        self,
        preparation: Mapping[str, Any],
        response: Any,
    ) -> Mapping[str, Any]:
        """Apply only the exact native human choice to one still-due review."""

        if not isinstance(response, Mapping):
            raise GovernanceMcpError(
                "Native drift review response is malformed",
                code="drift_review_response_invalid",
                stage=MCP_DRIFT_REVIEW_TOOL_NAME,
                field_path="elicitation_response",
                rule="object",
                retryable=False,
            )
        action = response.get("action")
        if action not in {"accept", "decline", "cancel"}:
            raise GovernanceMcpError(
                "Native drift review action is invalid",
                code="drift_review_response_invalid",
                stage=MCP_DRIFT_REVIEW_TOOL_NAME,
                field_path="elicitation_response.action",
                rule="enum",
                retryable=False,
            )
        content = response.get("content")
        decision: str | None = None
        if action == "accept":
            if not isinstance(content, Mapping) or set(content) != {"decision"}:
                raise GovernanceMcpError(
                    "Accepted native drift review content is invalid",
                    code="drift_review_response_invalid",
                    stage=MCP_DRIFT_REVIEW_TOOL_NAME,
                    field_path="elicitation_response.content",
                    rule="exact_decision",
                    retryable=False,
                )
            decision = content.get("decision")
            if decision not in {"record_candidate", "snooze", "no_record"}:
                raise GovernanceMcpError(
                    "Native drift review decision is invalid",
                    code="drift_review_response_invalid",
                    stage=MCP_DRIFT_REVIEW_TOOL_NAME,
                    field_path="elicitation_response.content.decision",
                    rule="enum",
                    retryable=False,
                )
        elif content is not None:
            raise GovernanceMcpError(
                "Declined or cancelled native drift review must not include content",
                code="drift_review_response_invalid",
                stage=MCP_DRIFT_REVIEW_TOOL_NAME,
                field_path="elicitation_response.content",
                rule="absent",
                retryable=False,
            )

        status_name = {"decline": "declined", "cancel": "cancelled"}.get(
            action, "not_recorded" if decision == "no_record" else decision
        )
        record_ref: str | None = None
        refreshed_status: Mapping[str, Any] | None = None
        monitor = {"status": "not_refreshed", "artifact_ref": None, "reason_code": None}
        modified = False
        if action == "accept" and decision in {"record_candidate", "snooze"}:
            if self.repository is None:
                raise GovernanceMcpError(
                    "MCP drift review has no locally bound repository",
                    code="drift_review_repository_unavailable",
                    stage=MCP_DRIFT_REVIEW_TOOL_NAME,
                    field_path=None,
                    rule="local_repository_binding",
                    retryable=False,
                )
            try:
                root = self.repository.resolve(strict=True)
            except OSError as exc:
                raise GovernanceMcpError(
                    "MCP drift review cannot resolve its locally bound repository",
                    code="drift_review_repository_unavailable",
                    stage=MCP_DRIFT_REVIEW_TOOL_NAME,
                    field_path=None,
                    rule="local_repository_binding",
                    retryable=False,
                ) from exc
            try:
                current = build_drift_review_status(root)
            except (DriftReviewPolicyError, LocalStateError, OSError, UnicodeError) as exc:
                raise GovernanceMcpError(
                    "Local repository state prevented drift-review revalidation",
                    code="drift_review_state_stale",
                    stage=MCP_DRIFT_REVIEW_TOOL_NAME,
                    field_path=None,
                    rule="revalidation",
                    retryable=False,
                ) from exc
            current_binding = _drift_review_status_binding(current)
            if (
                current.state != "due"
                or canonical_document_digest(current_binding)
                != preparation["due_state_digest"]
            ):
                raise GovernanceMcpError(
                    "The drift-review due state changed after the native form was prepared",
                    code="drift_review_state_stale",
                    stage=MCP_DRIFT_REVIEW_TOOL_NAME,
                    field_path=None,
                    rule="revalidation",
                    retryable=False,
                )
            try:
                record = build_drift_review_record(
                    root,
                    action=(
                        "review_completed" if decision == "record_candidate" else "snoozed"
                    ),
                    outcome=(
                        preparation["candidate_outcome"]
                        if decision == "record_candidate"
                        else None
                    ),
                )
                written = write_drift_review_record(root, record)
            except (DriftReviewPolicyError, LocalStateError, OSError, UnicodeError) as exc:
                raise GovernanceMcpError(
                    "Local repository state prevented the create-only drift-review write",
                    code="drift_review_state_stale",
                    stage=MCP_DRIFT_REVIEW_TOOL_NAME,
                    field_path=None,
                    rule="create_only_write",
                    retryable=False,
                ) from exc
            record_ref = written.relative_to(root).as_posix()
            modified = True
            status_name = "recorded" if decision == "record_candidate" else "snoozed"
            try:
                refreshed = build_drift_review_status(root, as_of=record.recorded_at)
                refreshed_status = asdict(refreshed)
                monitor_value = build_development_monitor(root, generated_at=record.recorded_at)
                monitor_path = write_development_monitor(
                    root,
                    monitor=monitor_value,
                    output=Path(".agentgov/dashboard.html"),
                    output_format="html",
                )
                monitor = {
                    "status": "refreshed",
                    "artifact_ref": monitor_path.relative_to(root).as_posix(),
                    "reason_code": None,
                }
            except Exception:
                monitor = {
                    "status": "refresh_failed",
                    "artifact_ref": None,
                    "reason_code": "local_monitor_refresh_failed",
                }

        return {
            "contract": "agentgov.drift-review-form-result",
            "schema_version": "1.0",
            "status": status_name,
            "candidate": {
                "outcome": preparation["candidate_outcome"],
                "semantics": "advisory",
                "dimensions": list(DRIFT_DIMENSIONS),
            },
            "review": {
                "surface": "mcp_form_elicitation",
                "action": action,
                "decision": decision,
            },
            "record_ref": record_ref,
            "drift_review": refreshed_status,
            "monitor": monitor,
            "authority_boundary": {
                "repository_modified": modified,
                "review_record_created": record_ref is not None,
                "monitor_refreshed": monitor["status"] == "refreshed",
                "decides_semantic_drift": False,
                "authorizes_code_change": False,
                "authorizes_scope_expansion": False,
                "authorizes_exception": False,
                "authorizes_git_operations": False,
                "authorizes_publication": False,
                "authorizes_deployment": False,
                "authorizes_release": False,
            },
        }

    def _lookup(self, value: Any) -> tuple[str, _Journey]:
        handle = _journey_handle(value)
        journey = self._journeys.get(handle)
        if journey is None:
            raise GovernanceMcpError("journey_handle is unknown or belonged to a restarted Adapter")
        return handle, journey

    def _alignment_start(self, value: Any) -> Mapping[str, Any]:
        fields = {"subject_type", "subject_id", "center", "drift", "assumptions", "unknowns", "candidate_resolutions", "recommended_resolution_id"}
        args = _exact_arguments(value, fields, tool=MCP_TOOL_NAMES[0])
        if args["subject_type"] not in {"work_request", "active_task", "architecture"}:
            _alignment_input_error(
                stage=MCP_TOOL_NAMES[0], field_path="subject_type", rule="enum"
            )
        if (
            not isinstance(args["subject_id"], str)
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
        center = _validate_center_input(
            args["center"], stage=MCP_TOOL_NAMES[0], field_path="center"
        )
        drift = _validate_drift_input(
            args["drift"], stage=MCP_TOOL_NAMES[0], field_path="drift"
        )
        assumptions = _normalized_input_text_list(
            args["assumptions"],
            stage=MCP_TOOL_NAMES[0],
            field_path="assumptions",
        )
        questions = _questions_with_adapter_ids(
            args["unknowns"], stage=MCP_TOOL_NAMES[0], field_path="unknowns"
        )
        candidates = _validate_candidate_resolutions(
            args["candidate_resolutions"],
            stage=MCP_TOOL_NAMES[0],
            field_path="candidate_resolutions",
        )
        recommendation = args["recommended_resolution_id"]
        candidate_ids = {item["id"] for item in candidates}
        if recommendation is not None and (
            not isinstance(recommendation, str) or recommendation not in candidate_ids
        ):
            _alignment_input_error(
                stage=MCP_TOOL_NAMES[0],
                field_path="recommended_resolution_id",
                rule="candidate_binding",
            )
        if not questions:
            if len(candidates) < 2:
                raise GovernanceMcpError(
                    "A context without open questions requires at least two stable options",
                    code="alignment_invalid_field",
                    stage=MCP_TOOL_NAMES[0],
                    field_path="candidate_resolutions",
                    rule="stable_options_required",
                    retryable=True,
                )
            if recommendation is None:
                raise GovernanceMcpError(
                    "A context without open questions requires one recommended option",
                    code="alignment_invalid_field",
                    stage=MCP_TOOL_NAMES[0],
                    field_path="recommended_resolution_id",
                    rule="recommendation_required",
                    retryable=True,
                )
        draft = AlignmentContextDraft(
            subject_type=args["subject_type"], subject_id=args["subject_id"],
            center=center, drift=drift, assumptions=assumptions,
            unknowns=questions, candidate_resolutions=candidates,
            recommended_resolution_id=recommendation,
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
        binding = _binding(
            args["decision_prompt"], fields={"prompt_id", "digest"},
            identifier=_DECISION_ID_RE, label="decision prompt",
            stage=MCP_TOOL_NAMES[2], field_path="decision_prompt",
        )
        expected = {"prompt_id": prompt.prompt_id, "digest": canonical_document_digest(asdict(prompt))}
        if binding != expected:
            _post_selection_input_error(
                stage=MCP_TOOL_NAMES[2], field_path="decision_prompt", rule="stale_binding"
            )
        offered = {item["id"] for item in asdict(prompt)["options"]}
        if (
            not isinstance(args["selected_option_id"], str)
            or args["selected_option_id"] not in offered
        ):
            _post_selection_input_error(
                stage=MCP_TOOL_NAMES[2], field_path="selected_option_id", rule="offered_option"
            )
        response = journey.adapter.select(args["selected_option_id"])
        return self._alignment_result(handle, response)

    def _self_review_start(self, value: Any) -> Mapping[str, Any]:
        fields = {"journey_handle", "reason_codes", "allowed_evidence_refs"}
        args = _exact_arguments(value, fields, tool=MCP_TOOL_NAMES[3])
        handle, journey = self._lookup(args["journey_handle"])
        if journey.review_requested or journey.review_completed:
            raise GovernanceMcpError("self-review has already started for this journey")
        active = journey.adapter.journey().responses[-1]
        if active.status != "resolved":
            raise GovernanceMcpError(
                "self-review requires resolved human alignment",
                code="post_selection_state_invalid", stage=MCP_TOOL_NAMES[3],
                field_path="journey_handle", rule="alignment_resolved_required",
                retryable=False,
            )
        reason_codes = _post_selection_identifiers(
            args["reason_codes"], stage=MCP_TOOL_NAMES[3], field_path="reason_codes"
        )
        evidence_refs = _validate_evidence_refs(
            args["allowed_evidence_refs"],
            stage=MCP_TOOL_NAMES[3],
            field_path="allowed_evidence_refs",
        )
        start = {
            "contract": SELF_REVIEW_START_CONTRACT,
            "schema_version": "1.0",
            "start_id": "asx-" + uuid.uuid4().hex,
            "source": {"adapter_id": self.adapter_id, "actor_class": "coding_agent"},
            "alignment": {"dialogue_id": active.dialogue.dialogue_id, "revision": active.dialogue.revision, "digest": canonical_document_digest(asdict(active.dialogue))},
            "risk": {"level": "medium", "reason_codes": list(reason_codes)},
            "provider": asdict(self.provider),
            "allowed_evidence_refs": list(evidence_refs),
            "content_boundary": semantic_content_boundary(),
            "authority_boundary": semantic_authority_boundary(),
        }
        response = journey.self_review.process_payload(
            start, sequence=1, alignment_response=active, expected_adapter_id=self.adapter_id
        )
        materialization_request = response.materialization_request
        journey.pending_review_request = {
            "request_id": materialization_request["request_id"],
            "digest": materialization_request["request_digest"],
        }
        journey.allowed_review_evidence_refs = evidence_refs
        journey.self_review_sequence = 1
        journey.review_requested = True
        return {"journey_handle": handle, "stage": "self_review", "response": asdict(response), "authority_boundary": semantic_authority_boundary()}

    def _self_review_complete(self, value: Any) -> Mapping[str, Any]:
        fields = {"journey_handle", "request", "observations"}
        args = _exact_arguments(value, fields, tool=MCP_TOOL_NAMES[4])
        handle, journey = self._lookup(args["journey_handle"])
        if not journey.review_requested or journey.review_completed:
            raise GovernanceMcpError("self-review completion requires one pending request")
        request = _binding(
            args["request"], fields={"request_id", "digest"},
            identifier=_REQUEST_ID_RE, label="self-review request",
            stage=MCP_TOOL_NAMES[4], field_path="request",
        )
        if request != journey.pending_review_request:
            _post_selection_input_error(
                stage=MCP_TOOL_NAMES[4], field_path="request", rule="stale_binding"
            )
        observations = _validate_review_observations(
            args["observations"],
            stage=MCP_TOOL_NAMES[4],
            allowed_evidence_refs=journey.allowed_review_evidence_refs,
        )
        draft = {
            "contract": SELF_REVIEW_DRAFT_CONTRACT,
            "schema_version": "1.0",
            "draft_id": "asd-" + uuid.uuid4().hex,
            "source": {"adapter_id": self.adapter_id, "actor_class": "coding_agent"},
            "request": {"request_id": request["request_id"], "request_digest": request["digest"]},
            "observations": list(observations),
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

    def _task_completion_record(self, value: Any) -> Mapping[str, Any]:
        fields = {"task_path"}
        args = _exact_arguments(
            value, fields, tool=MCP_TASK_COMPLETION_TOOL_NAME
        )
        task_ref = args["task_path"]
        if (
            not isinstance(task_ref, str)
            or not task_ref.strip()
            or len(task_ref) > 400
            or any(
                unicodedata.category(character).startswith("C")
                for character in task_ref
            )
        ):
            _task_completion_input_error(
                field_path="task_path", rule="normalized_text"
            )
        if (
            scope_path_error(task_ref)
            or not _TASK_COMPLETION_PATH_RE.fullmatch(task_ref)
        ):
            _task_completion_input_error(
                field_path="task_path", rule="repository_task_path"
            )
        if self.repository is None:
            raise GovernanceMcpError(
                "MCP task completion has no locally bound repository",
                code="task_completion_repository_unavailable",
                stage=MCP_TASK_COMPLETION_TOOL_NAME,
                field_path=None,
                rule="local_repository_binding",
                retryable=False,
            )

        root = self.repository.resolve()
        task_path = root.joinpath(*PurePosixPath(task_ref).parts)
        try:
            scope_report = check_development_scope(task_path, repository=root)
            if scope_report.has_failures:
                raise GovernanceMcpError(
                    "Current repository changes exceed the exact admitted task scope",
                    code="task_completion_scope_blocked",
                    stage=MCP_TASK_COMPLETION_TOOL_NAME,
                    field_path="task_path",
                    rule="admitted_scope",
                    retryable=True,
                )

            comparison_base = scope_report.head_sha
            execution_mode = "head_snapshot"
            active_session = load_active_session(root)
            if active_session is not None:
                active_task, resolved_session = resolve_active_task(root)
                if active_task != task_path.resolve():
                    raise GovernanceMcpError(
                        "The active AgentGov session belongs to a different task",
                        code="task_completion_active_task_mismatch",
                        stage=MCP_TASK_COMPLETION_TOOL_NAME,
                        field_path="task_path",
                        rule="active_task_binding",
                        retryable=False,
                    )
                comparison_base = resolved_session.comparison_base_sha
                execution_mode = "active_session"

            task = load_development_task(task_path)
            task_scope = task["scope"]
            snapshot = capture_git_snapshot(
                root, comparison_base=comparison_base
            )
            blocked_paths = tuple(
                path
                for path in snapshot_paths(snapshot)
                if not evaluate_path_scope(
                    path,
                    includes=task_scope["include_paths"],
                    excludes=task_scope["exclude_paths"],
                ).admitted
            )
            if blocked_paths:
                raise GovernanceMcpError(
                    "The complete Git snapshot exceeds the exact admitted task scope",
                    code="task_completion_scope_blocked",
                    stage=MCP_TASK_COMPLETION_TOOL_NAME,
                    field_path="task_path",
                    rule="complete_snapshot_scope",
                    retryable=True,
                )

            validation = run_task_validation(
                task_path,
                repository=root,
                comparison_base=comparison_base,
            )
            completion = reconcile_task_completion(
                task_path,
                repository=root,
                evidence_path=Path(validation.evidence_ref),
            )
        except GovernanceMcpError:
            raise
        except (
            EvidenceError,
            GitInspectionError,
            GitSnapshotError,
            LocalStateError,
            ScopePolicyError,
            SessionPolicyError,
            OSError,
            subprocess.SubprocessError,
            TypeError,
            ValueError,
        ) as exc:
            raise GovernanceMcpError(
                "Repository state prevented safe task-completion recording",
                code="task_completion_failed_closed",
                stage=MCP_TASK_COMPLETION_TOOL_NAME,
                field_path=None,
                rule="validated_local_completion",
                retryable=True,
            ) from exc

        return {
            "contract": "agentgov.task-completion-record-result",
            "schema_version": "1.0",
            "status": completion.state,
            "task": {
                "task_id": completion.task_id,
                "task_path": completion.task_path,
                "task_digest": completion.task_digest,
            },
            "execution": {
                "mode": execution_mode,
                "comparison_base_sha": comparison_base,
                "validation_outcome": validation.evidence.outcome,
                "evidence_ref": validation.evidence_ref,
                "validation_event_ref": validation.event_ref,
                "completion_event_ref": completion.event_ref,
            },
            "findings": {
                "passes": sum(
                    item.status == "PASS" for item in completion.findings
                ),
                "failures": sum(
                    item.status == "FAIL" for item in completion.findings
                ),
                "advisories": sum(
                    item.status == "ADVISORY" for item in completion.findings
                ),
            },
            "known_limits": list(completion.known_limits),
            "authority_boundary": {
                "local_governance_modified": True,
                "task_modified": False,
                "starts_session": False,
                "hands_off_session": False,
                "authorizes_requirement_completion": False,
                "authorizes_architecture_correctness": False,
                "authorizes_code_change": False,
                "authorizes_scope_expansion": False,
                "authorizes_exception": False,
                "authorizes_git_operations": False,
                "authorizes_publication": False,
                "authorizes_release": False,
                "authorizes_deployment": False,
            },
        }

    @staticmethod
    def _alignment_result(handle: str, response: Any) -> Mapping[str, Any]:
        return {"journey_handle": handle, "stage": "alignment", "response": asdict(response), "authority_boundary": denied_authority()}


class GovernanceMcpServer:
    """Dependency-free JSON-RPC surface for current and legacy STDIO MCP clients."""

    def __init__(
        self,
        adapter: GovernanceMcpAdapter,
        *,
        request_id_factory: Callable[[], str] | None = None,
    ) -> None:
        self.adapter = adapter
        self._client_supports_form_elicitation = False
        self._request_id_factory = request_id_factory or (
            lambda: f"elc-{uuid.uuid4().hex}"
        )

    @staticmethod
    def _supports_form_elicitation(capabilities: Any) -> bool:
        if not isinstance(capabilities, Mapping):
            return False
        elicitation = capabilities.get("elicitation")
        if not isinstance(elicitation, Mapping):
            return False
        return not elicitation or isinstance(elicitation.get("form"), Mapping)

    def _available_tools(self) -> tuple[Mapping[str, Any], ...]:
        tools = governance_mcp_tools()
        if self._client_supports_form_elicitation:
            return tools
        return tuple(
            tool for tool in tools if tool["name"] not in MCP_FORM_TOOL_NAMES
        )

    @staticmethod
    def _tool_success(structured: Mapping[str, Any]) -> Mapping[str, Any]:
        text = json.dumps(structured, ensure_ascii=False, sort_keys=True)
        return {
            "resultType": "complete",
            "content": [{"type": "text", "text": text}],
            "structuredContent": structured,
            "isError": False,
        }

    @staticmethod
    def _tool_failure(exc: GovernanceMcpError) -> Mapping[str, Any]:
        return {
            "resultType": "complete",
            "content": [{"type": "text", "text": str(exc)}],
            "structuredContent": {"error": exc.diagnostic()},
            "isError": True,
        }

    @staticmethod
    def _proposal_review_schema() -> Mapping[str, Any]:
        return {
            "type": "object",
            "properties": {
                "decision": {
                    "type": "string",
                    "title": "Task proposal decision",
                    "description": (
                        "Admit only this exact reviewed task, request changes without "
                        "writing, or reject it without writing."
                    ),
                    "oneOf": [
                        {"const": "admit", "title": "Admit this exact task"},
                        {"const": "request_changes", "title": "Request changes"},
                        {"const": "reject", "title": "Reject proposal"},
                    ],
                }
            },
            "required": ["decision"],
        }

    @staticmethod
    def _drift_review_schema() -> Mapping[str, Any]:
        return {
            "type": "object",
            "properties": {
                "decision": {
                    "type": "string",
                    "title": "Periodic drift-review decision",
                    "description": (
                        "Record only the exact displayed advisory candidate, snooze "
                        "for the configured interval, or create no repository record."
                    ),
                    "oneOf": [
                        {
                            "const": "record_candidate",
                            "title": "Record this exact advisory outcome",
                        },
                        {
                            "const": "snooze",
                            "title": "Snooze for the configured interval",
                        },
                        {"const": "no_record", "title": "Create no record"},
                    ],
                }
            },
            "required": ["decision"],
        }

    @staticmethod
    def _write_payload(output_stream: TextIO, payload: Mapping[str, Any]) -> None:
        output_stream.write(
            json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n"
        )
        output_stream.flush()

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
            self._client_supports_form_elicitation = self._supports_form_elicitation(
                params.get("capabilities")
            )
            requested = params["protocolVersion"]
            selected = requested if requested in {MCP_PROTOCOL_VERSION, *MCP_LEGACY_PROTOCOL_VERSIONS} else MCP_LEGACY_PROTOCOL_VERSIONS[0]
            return self._result(request_id, {"protocolVersion": selected, "capabilities": {"tools": {"listChanged": False}}, "serverInfo": {"name": MCP_SERVER_NAME, "version": MCP_SERVER_VERSION}, "instructions": MCP_SERVER_INSTRUCTIONS})
        if method == "ping":
            return self._result(request_id, {})
        if method == "tools/list":
            return self._result(request_id, {"resultType": "complete", "tools": list(self._available_tools()), "ttlMs": 300000, "cacheScope": "public"})
        if method == "tools/call":
            if not isinstance(params, Mapping) or set(params) - {"name", "arguments", "_meta", "inputResponses", "requestState"}:
                return self._error(request_id, -32602, "Invalid tools/call params")
            name = params.get("name")
            if name not in MCP_TOOL_NAMES:
                return self._error(request_id, -32602, "Unknown AgentGov tool")
            if name in MCP_FORM_TOOL_NAMES:
                is_proposal = name == MCP_TASK_PROPOSAL_TOOL_NAME
                if not self._client_supports_form_elicitation:
                    return self._result(
                        request_id,
                        self._tool_failure(
                            GovernanceMcpError(
                                "Codex did not negotiate native form elicitation",
                                code=(
                                    "task_proposal_elicitation_unsupported"
                                    if is_proposal
                                    else "drift_review_elicitation_unsupported"
                                ),
                                stage=name,
                                field_path=None,
                                rule="client_capability",
                                retryable=False,
                            )
                        ),
                    )
                return self._result(
                    request_id,
                    self._tool_failure(
                        GovernanceMcpError(
                            "Native form review requires the interactive STDIO transport",
                            code=(
                                "task_proposal_elicitation_transport_required"
                                if is_proposal
                                else "drift_review_elicitation_transport_required"
                            ),
                            stage=name,
                            field_path=None,
                            rule="interactive_transport",
                            retryable=False,
                        )
                    ),
                )
            try:
                structured = self.adapter.call_tool(name, params.get("arguments", {}))
            except GovernanceMcpError as exc:
                return self._result(request_id, self._tool_failure(exc))
            return self._result(request_id, self._tool_success(structured))
        return self._error(request_id, -32601, "Method not found")

    @staticmethod
    def _result(request_id: Any, result: Mapping[str, Any]) -> Mapping[str, Any]:
        return {"jsonrpc": "2.0", "id": request_id, "result": result}

    @staticmethod
    def _error(request_id: Any, code: int, message: str) -> Mapping[str, Any]:
        return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}

    def _serve_task_proposal_call(
        self,
        payload: Mapping[str, Any],
        input_stream: TextIO,
        output_stream: TextIO,
    ) -> Mapping[str, Any]:
        request_id = payload.get("id")
        params = payload.get("params", {})
        if (
            not isinstance(params, Mapping)
            or set(params)
            - {"name", "arguments", "_meta", "inputResponses", "requestState"}
        ):
            return self._error(request_id, -32602, "Invalid tools/call params")
        if not self._client_supports_form_elicitation:
            exc = GovernanceMcpError(
                "Codex did not negotiate native form elicitation",
                code="task_proposal_elicitation_unsupported",
                stage=MCP_TASK_PROPOSAL_TOOL_NAME,
                field_path=None,
                rule="client_capability",
                retryable=False,
            )
            return self._result(request_id, self._tool_failure(exc))
        try:
            preparation = self.adapter.prepare_task_proposal(
                params.get("arguments", {})
            )
            message = (
                "Review this exact bounded AgentGov task-admission plan. "
                "Only 'Admit this exact task' may create the listed target; all "
                "other outcomes perform no repository write.\n\n"
                + render_task_admission_plan_json(preparation.plan)
            )
            if len(message) > MAX_PROPOSAL_ELICITATION_MESSAGE_CHARACTERS:
                raise GovernanceMcpError(
                    "Task proposal is too large for bounded native review",
                    code="task_proposal_elicitation_too_large",
                    stage=MCP_TASK_PROPOSAL_TOOL_NAME,
                    field_path="admission_plan",
                    rule="max_characters",
                    retryable=True,
                )
        except GovernanceMcpError as exc:
            return self._result(request_id, self._tool_failure(exc))

        elicitation_id = self._request_id_factory()
        self._write_payload(
            output_stream,
            {
                "jsonrpc": "2.0",
                "id": elicitation_id,
                "method": "elicitation/create",
                "params": {
                    "mode": "form",
                    "message": message,
                    "requestedSchema": self._proposal_review_schema(),
                },
            },
        )

        while True:
            line = input_stream.readline()
            if line == "":
                exc = GovernanceMcpError(
                    "Native proposal review was interrupted before a bound decision",
                    code="task_proposal_elicitation_interrupted",
                    stage=MCP_TASK_PROPOSAL_TOOL_NAME,
                    field_path=None,
                    rule="response_required",
                    retryable=True,
                )
                return self._result(request_id, self._tool_failure(exc))
            try:
                incoming = json.loads(line)
            except json.JSONDecodeError:
                self._write_payload(output_stream, self._error(None, -32700, "Parse error"))
                continue
            if not isinstance(incoming, Mapping):
                self._write_payload(output_stream, self._error(None, -32600, "Invalid Request"))
                continue
            if incoming.get("id") == elicitation_id and "method" not in incoming:
                if (
                    incoming.get("jsonrpc") != "2.0"
                    or set(incoming) - {"jsonrpc", "id", "result", "error"}
                    or "result" not in incoming
                    or "error" in incoming
                ):
                    exc = GovernanceMcpError(
                        "Native proposal review returned no admissible result",
                        code="task_proposal_elicitation_failed",
                        stage=MCP_TASK_PROPOSAL_TOOL_NAME,
                        field_path="elicitation_response",
                        rule="result_required",
                        retryable=True,
                    )
                    return self._result(request_id, self._tool_failure(exc))
                try:
                    structured = self.adapter.complete_task_proposal_review(
                        preparation, incoming["result"]
                    )
                except GovernanceMcpError as exc:
                    return self._result(request_id, self._tool_failure(exc))
                return self._result(request_id, self._tool_success(structured))
            if incoming.get("method") == "notifications/cancelled":
                cancelled = incoming.get("params")
                if isinstance(cancelled, Mapping) and cancelled.get("requestId") in {
                    elicitation_id,
                    request_id,
                }:
                    exc = GovernanceMcpError(
                        "Native proposal review was cancelled before admission",
                        code="task_proposal_elicitation_interrupted",
                        stage=MCP_TASK_PROPOSAL_TOOL_NAME,
                        field_path=None,
                        rule="cancelled",
                        retryable=True,
                    )
                    return self._result(request_id, self._tool_failure(exc))
                continue
            if "method" in incoming:
                nested_response = self.dispatch(incoming)
                if nested_response is not None:
                    self._write_payload(output_stream, nested_response)

    def _serve_drift_review_call(
        self,
        payload: Mapping[str, Any],
        input_stream: TextIO,
        output_stream: TextIO,
    ) -> Mapping[str, Any]:
        request_id = payload.get("id")
        params = payload.get("params", {})
        if (
            not isinstance(params, Mapping)
            or set(params)
            - {"name", "arguments", "_meta", "inputResponses", "requestState"}
        ):
            return self._error(request_id, -32602, "Invalid tools/call params")
        if not self._client_supports_form_elicitation:
            exc = GovernanceMcpError(
                "Codex did not negotiate native form elicitation",
                code="drift_review_elicitation_unsupported",
                stage=MCP_DRIFT_REVIEW_TOOL_NAME,
                field_path=None,
                rule="client_capability",
                retryable=False,
            )
            return self._result(request_id, self._tool_failure(exc))
        try:
            preparation = self.adapter.prepare_drift_review(
                params.get("arguments", {})
            )
            observation_lines = "\n".join(
                f"- {item['dimension']}: {item['finding']}"
                for item in preparation["observations"]
            )
            evidence_lines = "\n".join(
                f"- {item}" for item in preparation["evidence_refs"]
            )
            message = (
                "Review this evidence-bounded AgentGov drift candidate. The candidate is "
                "ADVISORY and does not prove correctness. Only 'Record this exact advisory "
                "outcome' creates a completed-review record; snooze creates only a configured "
                "snooze record; all other outcomes write nothing.\n\n"
                f"Candidate outcome: {preparation['candidate_outcome']}\n"
                f"Due reasons: {', '.join(preparation['due_state']['reason_codes'])}\n\n"
                f"Snooze interval: {preparation['due_state']['cadence']['snooze_days']} days\n\n"
                f"Dimension observations:\n{observation_lines}\n\n"
                f"Repository evidence references:\n{evidence_lines}"
            )
            if len(message) > MAX_DRIFT_REVIEW_ELICITATION_MESSAGE_CHARACTERS:
                raise GovernanceMcpError(
                    "Drift review is too large for bounded native review",
                    code="drift_review_elicitation_too_large",
                    stage=MCP_DRIFT_REVIEW_TOOL_NAME,
                    field_path="observations",
                    rule="max_characters",
                    retryable=True,
                )
        except GovernanceMcpError as exc:
            return self._result(request_id, self._tool_failure(exc))

        elicitation_id = self._request_id_factory()
        self._write_payload(
            output_stream,
            {
                "jsonrpc": "2.0",
                "id": elicitation_id,
                "method": "elicitation/create",
                "params": {
                    "mode": "form",
                    "message": message,
                    "requestedSchema": self._drift_review_schema(),
                },
            },
        )

        while True:
            line = input_stream.readline()
            if line == "":
                exc = GovernanceMcpError(
                    "Native drift review was interrupted before a bound decision",
                    code="drift_review_elicitation_interrupted",
                    stage=MCP_DRIFT_REVIEW_TOOL_NAME,
                    field_path=None,
                    rule="response_required",
                    retryable=True,
                )
                return self._result(request_id, self._tool_failure(exc))
            try:
                incoming = json.loads(line)
            except json.JSONDecodeError:
                self._write_payload(output_stream, self._error(None, -32700, "Parse error"))
                continue
            if not isinstance(incoming, Mapping):
                self._write_payload(output_stream, self._error(None, -32600, "Invalid Request"))
                continue
            if incoming.get("id") == elicitation_id and "method" not in incoming:
                if (
                    incoming.get("jsonrpc") != "2.0"
                    or set(incoming) - {"jsonrpc", "id", "result", "error"}
                    or "result" not in incoming
                    or "error" in incoming
                ):
                    exc = GovernanceMcpError(
                        "Native drift review returned no admissible result",
                        code="drift_review_elicitation_failed",
                        stage=MCP_DRIFT_REVIEW_TOOL_NAME,
                        field_path="elicitation_response",
                        rule="result_required",
                        retryable=True,
                    )
                    return self._result(request_id, self._tool_failure(exc))
                try:
                    structured = self.adapter.complete_drift_review(
                        preparation, incoming["result"]
                    )
                except GovernanceMcpError as exc:
                    return self._result(request_id, self._tool_failure(exc))
                return self._result(request_id, self._tool_success(structured))
            if incoming.get("method") == "notifications/cancelled":
                cancelled = incoming.get("params")
                if isinstance(cancelled, Mapping) and cancelled.get("requestId") in {
                    elicitation_id,
                    request_id,
                }:
                    exc = GovernanceMcpError(
                        "Native drift review was cancelled before recording",
                        code="drift_review_elicitation_interrupted",
                        stage=MCP_DRIFT_REVIEW_TOOL_NAME,
                        field_path=None,
                        rule="cancelled",
                        retryable=True,
                    )
                    return self._result(request_id, self._tool_failure(exc))
                continue
            if "method" in incoming:
                nested_response = self.dispatch(incoming)
                if nested_response is not None:
                    self._write_payload(output_stream, nested_response)

    def serve(self, input_stream: TextIO, output_stream: TextIO) -> int:
        for line in input_stream:
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                response = self._error(None, -32700, "Parse error")
            else:
                if (
                    isinstance(payload, Mapping)
                    and payload.get("method") == "tools/call"
                    and isinstance(payload.get("params"), Mapping)
                    and payload["params"].get("name") in MCP_FORM_TOOL_NAMES
                ):
                    if payload["params"].get("name") == MCP_TASK_PROPOSAL_TOOL_NAME:
                        response = self._serve_task_proposal_call(
                            payload, input_stream, output_stream
                        )
                    else:
                        response = self._serve_drift_review_call(
                            payload, input_stream, output_stream
                        )
                else:
                    response = self.dispatch(payload)
            if response is not None:
                self._write_payload(output_stream, response)
        return 0
