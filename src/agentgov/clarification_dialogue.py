"""Governed multi-turn clarification and advisory drift re-centering."""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from dataclasses import asdict, dataclass
from typing import Any, Mapping

from agentgov.host_interaction import REFERENCE_HOST_CAPABILITIES
from agentgov.human_decision import (
    HumanDecisionPrompt,
    HumanDecisionResult,
    build_human_decision_prompt,
    canonical_document_digest,
    validate_result_for_prompt,
)
from agentgov.path_policy import scope_path_error


ALIGNMENT_CONTEXT_CONTRACT = "agentgov.alignment-context"
ALIGNMENT_CONTEXT_SCHEMA_VERSION = "1.0"
CLARIFICATION_DIALOGUE_CONTRACT = "agentgov.clarification-dialogue"
CLARIFICATION_DIALOGUE_SCHEMA_VERSION = "1.0"
CLARIFICATION_PROMPT_CONTRACT = "agentgov.clarification-prompt"
CLARIFICATION_PROMPT_SCHEMA_VERSION = "1.0"
CLARIFICATION_UPDATE_CONTRACT = "agentgov.clarification-update"
CLARIFICATION_UPDATE_SCHEMA_VERSION = "1.0"

DRIFT_KINDS = {"business", "requirement", "architecture", "scope", "implementation"}
RESOLUTION_IDS = {
    "return_to_center",
    "adopt_new_center",
    "split_new_requirement",
    "continue_exploration",
    "stop",
}
_CONTEXT_ID_RE = re.compile(r"^acx-[0-9a-f]{32}$")
_DIALOGUE_ID_RE = re.compile(r"^dlg-[0-9a-f]{32}$")
_QUESTION_ID_RE = re.compile(r"^qst-[0-9a-f]{16}$")
_PROMPT_ID_RE = re.compile(r"^cqp-[0-9a-f]{32}$")
_UPDATE_ID_RE = re.compile(r"^cup-[0-9a-f]{32}$")
_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_ADAPTER_ID_RE = re.compile(r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$")
_SUBJECT_ID_RE = re.compile(r"^[a-z0-9]+(?:[._-][a-z0-9]+)*$")
_TIME_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$")
_SENSITIVE_RE = re.compile(
    r"(?i)(?:api[_-]?key|access[_-]?token|auth[_-]?token|password|passwd|secret)\s*[:=]"
)
_ABSOLUTE_PATH_RE = re.compile(r"(?i)(?:^|\s)(?:[a-z]:[\\/]|/(?:users|home|var|etc|tmp)/)")
_CONTENT_FIELDS = {
    "contains_raw_prompt",
    "contains_raw_answer",
    "contains_transcript",
    "contains_assistant_response",
    "contains_source_content",
    "contains_credentials",
    "contains_absolute_paths",
}
_AUTHORITY_FIELDS = {
    "changes_center",
    "resolves_drift",
    "admits_task",
    "starts_session",
    "authorizes_code_change",
    "authorizes_scope_expansion",
    "authorizes_exception",
    "authorizes_git_operations",
    "authorizes_deployment",
    "authorizes_release",
}
_CENTER_FIELDS = {"outcome", "why_now", "success_signals", "constraints", "non_goals"}


class ClarificationDialogueError(ValueError):
    """A clarification snapshot, update, or resolution is ambiguous or unsafe."""


@dataclass(frozen=True)
class AlignmentContext:
    contract: str
    schema_version: str
    context_id: str
    source: Mapping[str, str]
    center: Mapping[str, Any]
    drift: Mapping[str, Any]
    assumptions: tuple[str, ...]
    unknowns: tuple[Mapping[str, Any], ...]
    candidate_resolutions: tuple[Mapping[str, Any], ...]
    recommended_resolution_id: str | None
    content_boundary: Mapping[str, bool]
    authority_boundary: Mapping[str, bool]


@dataclass(frozen=True)
class ClarificationDialogue:
    contract: str
    schema_version: str
    dialogue_id: str
    source: Mapping[str, str]
    revision: int
    status: str
    center: Mapping[str, Any]
    drift: Mapping[str, Any]
    assumptions: tuple[str, ...]
    open_questions: tuple[Mapping[str, Any], ...]
    discussion_records: tuple[Mapping[str, str], ...]
    candidate_resolutions: tuple[Mapping[str, Any], ...]
    recommended_resolution_id: str | None
    metrics: Mapping[str, int]
    resolution: Mapping[str, str] | None
    authority_boundary: Mapping[str, bool]


@dataclass(frozen=True)
class ClarificationPrompt:
    contract: str
    schema_version: str
    prompt_id: str
    dialogue: Mapping[str, Any]
    status: str
    center_summary: str
    drift_summary: str
    why_question_matters: str
    question: Mapping[str, str]
    guidance: Mapping[str, Any]
    authority_boundary: Mapping[str, bool]


@dataclass(frozen=True)
class ClarificationUpdate:
    contract: str
    schema_version: str
    update_id: str
    dialogue: Mapping[str, Any]
    prompt: Mapping[str, str]
    question_id: str
    actor: Mapping[str, str]
    recorded_at: str
    answer_summary: str
    center_patch: Mapping[str, Any]
    new_questions: tuple[Mapping[str, Any], ...]
    candidate_resolutions: tuple[Mapping[str, Any], ...]
    recommended_resolution_id: str | None
    ready_requested: bool
    content_boundary: Mapping[str, bool]
    authority_boundary: Mapping[str, bool]


def _text(value: Any, *, label: str, maximum: int = 800) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        raise ClarificationDialogueError(
            f"{label} must be non-empty and at most {maximum} characters"
        )
    if any(unicodedata.category(character).startswith("C") for character in value):
        raise ClarificationDialogueError(f"{label} contains control characters")
    if _SENSITIVE_RE.search(value) or _ABSOLUTE_PATH_RE.search(value):
        raise ClarificationDialogueError(f"{label} contains sensitive or host-local content")
    return value


def _text_list(value: Any, *, label: str, maximum: int = 50) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)) or len(value) > maximum:
        raise ClarificationDialogueError(f"{label} must contain at most {maximum} items")
    result = tuple(_text(item, label=f"{label} item", maximum=400) for item in value)
    if len(result) != len(set(result)):
        raise ClarificationDialogueError(f"{label} must not contain duplicates")
    return result


def _authority(value: Any, *, display_only: bool = False) -> Mapping[str, bool]:
    if (
        not isinstance(value, Mapping)
        or set(value) != _AUTHORITY_FIELDS
        or any(item is not False for item in value.values())
    ):
        subject = "display" if display_only else "dialogue"
        raise ClarificationDialogueError(f"{subject} cannot grant authority")
    return dict(value)


def denied_authority() -> Mapping[str, bool]:
    return {field: False for field in sorted(_AUTHORITY_FIELDS)}


def _content_boundary(value: Any) -> Mapping[str, bool]:
    if (
        not isinstance(value, Mapping)
        or set(value) != _CONTENT_FIELDS
        or any(item is not False for item in value.values())
    ):
        raise ClarificationDialogueError("clarification content boundary must deny raw or sensitive content")
    return dict(value)


def _center(value: Any, *, patch: bool = False) -> Mapping[str, Any]:
    if not isinstance(value, Mapping) or set(value) != _CENTER_FIELDS:
        raise ClarificationDialogueError("alignment center has unexpected fields")
    normalized: dict[str, Any] = {}
    for key in ("outcome", "why_now"):
        item = value.get(key)
        normalized[key] = None if patch and item is None else _text(item, label=f"center {key}")
    for key in ("success_signals", "constraints", "non_goals"):
        item = value.get(key)
        normalized[key] = None if patch and item is None else _text_list(item, label=f"center {key}")
    if not patch and not normalized["success_signals"]:
        raise ClarificationDialogueError("alignment center requires at least one success signal")
    return normalized


def _drift(value: Any) -> Mapping[str, Any]:
    fields = {"kind", "semantics", "observation", "evidence_refs", "impact"}
    if not isinstance(value, Mapping) or set(value) != fields:
        raise ClarificationDialogueError("drift observation has unexpected fields")
    kind = value.get("kind")
    semantics = value.get("semantics")
    if kind not in DRIFT_KINDS or semantics not in {"advisory", "deterministic"}:
        raise ClarificationDialogueError("drift kind or semantics is unsupported")
    if kind in {"business", "requirement", "architecture"} and semantics != "advisory":
        raise ClarificationDialogueError(f"{kind} drift must remain advisory")
    evidence = _text_list(value.get("evidence_refs"), label="drift evidence", maximum=20)
    for item in evidence:
        if scope_path_error(item):
            raise ClarificationDialogueError("drift evidence must be repository-relative")
    return {
        "kind": kind,
        "semantics": semantics,
        "observation": _text(value.get("observation"), label="drift observation"),
        "evidence_refs": evidence,
        "impact": _text(value.get("impact"), label="drift impact"),
    }


def _questions(value: Any, *, label: str) -> tuple[Mapping[str, Any], ...]:
    if not isinstance(value, (list, tuple)) or len(value) > 100:
        raise ClarificationDialogueError(f"{label} must contain at most 100 operational records")
    normalized: list[Mapping[str, Any]] = []
    ids: set[str] = set()
    for item in value:
        fields = {"question_id", "question", "why_matters", "material", "priority"}
        if not isinstance(item, Mapping) or set(item) != fields:
            raise ClarificationDialogueError(f"{label} question has unexpected fields")
        question_id = item.get("question_id")
        if (
            not isinstance(question_id, str)
            or not _QUESTION_ID_RE.fullmatch(question_id)
            or question_id in ids
        ):
            raise ClarificationDialogueError(f"{label} question identity is invalid")
        if not isinstance(item.get("material"), bool):
            raise ClarificationDialogueError(f"{label} question material must be boolean")
        priority = item.get("priority")
        if not isinstance(priority, int) or isinstance(priority, bool) or not 1 <= priority <= 5:
            raise ClarificationDialogueError(f"{label} question priority must be 1 through 5")
        ids.add(question_id)
        normalized.append(
            {
                "question_id": question_id,
                "question": _text(item.get("question"), label="clarification question"),
                "why_matters": _text(item.get("why_matters"), label="question reason"),
                "material": item["material"],
                "priority": priority,
            }
        )
    return tuple(normalized)


def _resolutions(value: Any) -> tuple[Mapping[str, Any], ...]:
    if not isinstance(value, (list, tuple)) or len(value) > len(RESOLUTION_IDS):
        raise ClarificationDialogueError("candidate resolutions are invalid")
    result: list[Mapping[str, Any]] = []
    ids: set[str] = set()
    for item in value:
        fields = {"id", "label", "effect", "center_patch"}
        if not isinstance(item, Mapping) or set(item) != fields:
            raise ClarificationDialogueError("candidate resolution has unexpected fields")
        option_id = item.get("id")
        if option_id not in RESOLUTION_IDS or option_id in ids:
            raise ClarificationDialogueError("candidate resolution id is invalid")
        patch = _center(item.get("center_patch"), patch=True)
        has_patch = any(value is not None for value in patch.values())
        if option_id == "adopt_new_center" and not has_patch:
            raise ClarificationDialogueError("adopt_new_center requires an explicit center patch")
        if option_id != "adopt_new_center" and has_patch:
            raise ClarificationDialogueError("only adopt_new_center may carry a center patch")
        ids.add(option_id)
        result.append(
            {
                "id": option_id,
                "label": _text(item.get("label"), label="resolution label", maximum=160),
                "effect": _text(item.get("effect"), label="resolution effect"),
                "center_patch": patch,
            }
        )
    return tuple(result)


def _recommendation(value: Any, resolutions: tuple[Mapping[str, Any], ...]) -> str | None:
    ids = {item["id"] for item in resolutions}
    if value is not None and value not in ids:
        raise ClarificationDialogueError("recommended resolution must name one candidate")
    return value


def alignment_context_from_payload(payload: Any) -> AlignmentContext:
    fields = {
        "contract", "schema_version", "context_id", "source", "center", "drift",
        "assumptions", "unknowns", "candidate_resolutions",
        "recommended_resolution_id", "content_boundary", "authority_boundary",
    }
    if not isinstance(payload, Mapping) or set(payload) != fields:
        raise ClarificationDialogueError("alignment context has unexpected fields")
    if (
        payload.get("contract") != ALIGNMENT_CONTEXT_CONTRACT
        or payload.get("schema_version") != ALIGNMENT_CONTEXT_SCHEMA_VERSION
    ):
        raise ClarificationDialogueError("alignment context contract is unsupported")
    context_id = payload.get("context_id")
    if not isinstance(context_id, str) or not _CONTEXT_ID_RE.fullmatch(context_id):
        raise ClarificationDialogueError("alignment context_id is invalid")
    source = payload.get("source")
    if not isinstance(source, Mapping) or set(source) != {
        "adapter_id", "actor_class", "subject_type", "subject_id"
    }:
        raise ClarificationDialogueError("alignment context source is invalid")
    if (
        not isinstance(source.get("adapter_id"), str)
        or not _ADAPTER_ID_RE.fullmatch(source["adapter_id"])
        or source.get("actor_class") != "coding_agent"
        or source.get("subject_type") not in {"work_request", "active_task", "architecture"}
        or not isinstance(source.get("subject_id"), str)
        or not _SUBJECT_ID_RE.fullmatch(source["subject_id"])
    ):
        raise ClarificationDialogueError("alignment context source identity is invalid")
    center = _center(payload.get("center"))
    drift = _drift(payload.get("drift"))
    assumptions = _text_list(payload.get("assumptions"), label="assumptions")
    unknowns = _questions(payload.get("unknowns"), label="unknowns")
    resolutions = _resolutions(payload.get("candidate_resolutions"))
    recommendation = _recommendation(payload.get("recommended_resolution_id"), resolutions)
    if not unknowns and (len(resolutions) < 2 or recommendation is None):
        raise ClarificationDialogueError(
            "a context without unknowns requires stable recommended resolutions"
        )
    return AlignmentContext(
        contract=ALIGNMENT_CONTEXT_CONTRACT,
        schema_version=ALIGNMENT_CONTEXT_SCHEMA_VERSION,
        context_id=context_id,
        source=dict(source),
        center=center,
        drift=drift,
        assumptions=assumptions,
        unknowns=unknowns,
        candidate_resolutions=resolutions,
        recommended_resolution_id=recommendation,
        content_boundary=_content_boundary(payload.get("content_boundary")),
        authority_boundary=_authority(payload.get("authority_boundary")),
    )


def clarification_dialogue_from_payload(payload: Any) -> ClarificationDialogue:
    fields = {
        "contract", "schema_version", "dialogue_id", "source", "revision", "status",
        "center", "drift", "assumptions", "open_questions", "discussion_records",
        "candidate_resolutions", "recommended_resolution_id", "metrics", "resolution",
        "authority_boundary",
    }
    if not isinstance(payload, Mapping) or set(payload) != fields:
        raise ClarificationDialogueError("clarification dialogue has unexpected fields")
    if (
        payload.get("contract") != CLARIFICATION_DIALOGUE_CONTRACT
        or payload.get("schema_version") != CLARIFICATION_DIALOGUE_SCHEMA_VERSION
    ):
        raise ClarificationDialogueError("clarification dialogue contract is unsupported")
    dialogue_id = payload.get("dialogue_id")
    if not isinstance(dialogue_id, str) or not _DIALOGUE_ID_RE.fullmatch(dialogue_id):
        raise ClarificationDialogueError("clarification dialogue_id is invalid")
    source = payload.get("source")
    if not isinstance(source, Mapping) or set(source) != {"context_id", "context_digest"}:
        raise ClarificationDialogueError("clarification dialogue source is invalid")
    if (
        not isinstance(source.get("context_id"), str)
        or not _CONTEXT_ID_RE.fullmatch(source["context_id"])
        or not isinstance(source.get("context_digest"), str)
        or not _DIGEST_RE.fullmatch(source["context_digest"])
    ):
        raise ClarificationDialogueError("clarification dialogue source identity is invalid")
    revision = payload.get("revision")
    if not isinstance(revision, int) or isinstance(revision, bool) or revision < 1:
        raise ClarificationDialogueError("clarification dialogue revision is invalid")
    status = payload.get("status")
    if status not in {"exploring", "ready_for_decision", "resolved", "stopped"}:
        raise ClarificationDialogueError("clarification dialogue status is invalid")
    center = _center(payload.get("center"))
    drift = _drift(payload.get("drift"))
    assumptions = _text_list(payload.get("assumptions"), label="assumptions")
    questions = _questions(payload.get("open_questions"), label="open questions")
    records = payload.get("discussion_records")
    if not isinstance(records, (list, tuple)) or len(records) > 100:
        raise ClarificationDialogueError("discussion records exceed the operational snapshot limit")
    normalized_records: list[Mapping[str, str]] = []
    for record in records:
        if not isinstance(record, Mapping) or set(record) != {
            "question_id", "question_summary", "answer_summary", "recorded_at", "recorded_by"
        }:
            raise ClarificationDialogueError("discussion record has unexpected fields")
        if not isinstance(record.get("question_id"), str) or not _QUESTION_ID_RE.fullmatch(record["question_id"]):
            raise ClarificationDialogueError("discussion record question_id is invalid")
        if not isinstance(record.get("recorded_at"), str) or not _TIME_RE.fullmatch(record["recorded_at"]):
            raise ClarificationDialogueError("discussion record time is invalid")
        if record.get("recorded_by") != "human":
            raise ClarificationDialogueError("discussion record must be human-owned")
        normalized_records.append(
            {
                "question_id": record["question_id"],
                "question_summary": _text(record.get("question_summary"), label="question summary"),
                "answer_summary": _text(record.get("answer_summary"), label="answer summary"),
                "recorded_at": record["recorded_at"],
                "recorded_by": "human",
            }
        )
    resolutions = _resolutions(payload.get("candidate_resolutions"))
    recommendation = _recommendation(payload.get("recommended_resolution_id"), resolutions)
    metrics = payload.get("metrics")
    if not isinstance(metrics, Mapping) or set(metrics) != {
        "clarification_turns", "governance_decision_episodes"
    }:
        raise ClarificationDialogueError("clarification metrics are invalid")
    for key in metrics:
        if not isinstance(metrics[key], int) or isinstance(metrics[key], bool) or metrics[key] < 0:
            raise ClarificationDialogueError("clarification metric must be non-negative")
    if metrics["clarification_turns"] < len(normalized_records):
        raise ClarificationDialogueError(
            "clarification turn count cannot be smaller than the rolling records"
        )
    resolution = payload.get("resolution")
    if status in {"resolved", "stopped"}:
        if not isinstance(resolution, Mapping) or set(resolution) != {
            "option_id", "summary", "recorded_at"
        }:
            raise ClarificationDialogueError("resolved dialogue requires one resolution")
        if resolution.get("option_id") not in RESOLUTION_IDS:
            raise ClarificationDialogueError("dialogue resolution is unsupported")
        _text(resolution.get("summary"), label="resolution summary")
        if not isinstance(resolution.get("recorded_at"), str) or not _TIME_RE.fullmatch(resolution["recorded_at"]):
            raise ClarificationDialogueError("dialogue resolution time is invalid")
    elif resolution is not None:
        raise ClarificationDialogueError("unresolved dialogue cannot carry a resolution")
    material_open = any(item["material"] for item in questions)
    if status == "exploring" and not questions:
        raise ClarificationDialogueError("exploring dialogue requires an open question")
    if status == "ready_for_decision" and (material_open or len(resolutions) < 2 or recommendation is None):
        raise ClarificationDialogueError("ready dialogue requires resolved material unknowns and stable options")
    return ClarificationDialogue(
        contract=CLARIFICATION_DIALOGUE_CONTRACT,
        schema_version=CLARIFICATION_DIALOGUE_SCHEMA_VERSION,
        dialogue_id=dialogue_id,
        source=dict(source),
        revision=revision,
        status=status,
        center=center,
        drift=drift,
        assumptions=assumptions,
        open_questions=questions,
        discussion_records=tuple(normalized_records),
        candidate_resolutions=resolutions,
        recommended_resolution_id=recommendation,
        metrics=dict(metrics),
        resolution=None if resolution is None else dict(resolution),
        authority_boundary=_authority(payload.get("authority_boundary")),
    )


def start_clarification_dialogue(context: AlignmentContext) -> ClarificationDialogue:
    context = alignment_context_from_payload(asdict(context))
    context_digest = canonical_document_digest(asdict(context))
    dialogue_id = "dlg-" + hashlib.sha256(
        f"{context.context_id}\x00{context_digest}".encode("utf-8")
    ).hexdigest()[:32]
    status = (
        "ready_for_decision"
        if not any(item["material"] for item in context.unknowns)
        and len(context.candidate_resolutions) >= 2
        and context.recommended_resolution_id is not None
        else "exploring"
    )
    return clarification_dialogue_from_payload(
        {
            "contract": CLARIFICATION_DIALOGUE_CONTRACT,
            "schema_version": CLARIFICATION_DIALOGUE_SCHEMA_VERSION,
            "dialogue_id": dialogue_id,
            "source": {"context_id": context.context_id, "context_digest": context_digest},
            "revision": 1,
            "status": status,
            "center": dict(context.center),
            "drift": dict(context.drift),
            "assumptions": list(context.assumptions),
            "open_questions": list(context.unknowns),
            "discussion_records": [],
            "candidate_resolutions": list(context.candidate_resolutions),
            "recommended_resolution_id": context.recommended_resolution_id,
            "metrics": {"clarification_turns": 0, "governance_decision_episodes": 0},
            "resolution": None,
            "authority_boundary": denied_authority(),
        }
    )


def clarification_prompt_from_payload(payload: Any) -> ClarificationPrompt:
    fields = {
        "contract", "schema_version", "prompt_id", "dialogue", "status",
        "center_summary", "drift_summary", "why_question_matters", "question",
        "guidance", "authority_boundary",
    }
    if not isinstance(payload, Mapping) or set(payload) != fields:
        raise ClarificationDialogueError("clarification prompt has unexpected fields")
    if (
        payload.get("contract") != CLARIFICATION_PROMPT_CONTRACT
        or payload.get("schema_version") != CLARIFICATION_PROMPT_SCHEMA_VERSION
    ):
        raise ClarificationDialogueError("clarification prompt contract is unsupported")
    prompt_id = payload.get("prompt_id")
    if not isinstance(prompt_id, str) or not _PROMPT_ID_RE.fullmatch(prompt_id):
        raise ClarificationDialogueError("clarification prompt_id is invalid")
    dialogue = payload.get("dialogue")
    if not isinstance(dialogue, Mapping) or set(dialogue) != {"dialogue_id", "revision", "digest"}:
        raise ClarificationDialogueError("clarification prompt dialogue binding is invalid")
    if (
        not isinstance(dialogue.get("dialogue_id"), str)
        or not _DIALOGUE_ID_RE.fullmatch(dialogue["dialogue_id"])
        or not isinstance(dialogue.get("revision"), int)
        or dialogue["revision"] < 1
        or not isinstance(dialogue.get("digest"), str)
        or not _DIGEST_RE.fullmatch(dialogue["digest"])
    ):
        raise ClarificationDialogueError("clarification prompt dialogue identity is invalid")
    if payload.get("status") != "requires_clarification":
        raise ClarificationDialogueError("clarification prompt status is invalid")
    question = payload.get("question")
    if not isinstance(question, Mapping) or set(question) != {"question_id", "text", "response_mode"}:
        raise ClarificationDialogueError("clarification prompt question is invalid")
    if (
        not isinstance(question.get("question_id"), str)
        or not _QUESTION_ID_RE.fullmatch(question["question_id"])
        or question.get("response_mode") != "natural_language"
    ):
        raise ClarificationDialogueError("clarification prompt question identity is invalid")
    guidance = payload.get("guidance")
    if guidance != {
        "one_question": True,
        "answer_in_own_words": True,
        "raw_answer_persisted": False,
        "decision_episode": False,
    }:
        raise ClarificationDialogueError("clarification prompt guidance is invalid")
    return ClarificationPrompt(
        contract=CLARIFICATION_PROMPT_CONTRACT,
        schema_version=CLARIFICATION_PROMPT_SCHEMA_VERSION,
        prompt_id=prompt_id,
        dialogue=dict(dialogue),
        status="requires_clarification",
        center_summary=_text(payload.get("center_summary"), label="center summary"),
        drift_summary=_text(payload.get("drift_summary"), label="drift summary"),
        why_question_matters=_text(payload.get("why_question_matters"), label="question importance"),
        question={
            "question_id": question["question_id"],
            "text": _text(question.get("text"), label="clarification prompt question"),
            "response_mode": "natural_language",
        },
        guidance=dict(guidance),
        authority_boundary=_authority(payload.get("authority_boundary"), display_only=True),
    )


def build_next_clarification_prompt(dialogue: ClarificationDialogue) -> ClarificationPrompt:
    dialogue = clarification_dialogue_from_payload(asdict(dialogue))
    if dialogue.status != "exploring" or not dialogue.open_questions:
        raise ClarificationDialogueError("dialogue has no open clarification question")
    question = sorted(
        dialogue.open_questions,
        key=lambda item: (not item["material"], -item["priority"], item["question_id"]),
    )[0]
    digest = canonical_document_digest(asdict(dialogue))
    identity = f"{dialogue.dialogue_id}\x00{dialogue.revision}\x00{digest}\x00{question['question_id']}"
    return clarification_prompt_from_payload(
        {
            "contract": CLARIFICATION_PROMPT_CONTRACT,
            "schema_version": CLARIFICATION_PROMPT_SCHEMA_VERSION,
            "prompt_id": "cqp-" + hashlib.sha256(identity.encode("utf-8")).hexdigest()[:32],
            "dialogue": {
                "dialogue_id": dialogue.dialogue_id,
                "revision": dialogue.revision,
                "digest": digest,
            },
            "status": "requires_clarification",
            "center_summary": dialogue.center["outcome"],
            "drift_summary": dialogue.drift["observation"],
            "why_question_matters": question["why_matters"],
            "question": {
                "question_id": question["question_id"],
                "text": question["question"],
                "response_mode": "natural_language",
            },
            "guidance": {
                "one_question": True,
                "answer_in_own_words": True,
                "raw_answer_persisted": False,
                "decision_episode": False,
            },
            "authority_boundary": denied_authority(),
        }
    )


def render_clarification_prompt_terminal(prompt: ClarificationPrompt) -> str:
    prompt = clarification_prompt_from_payload(asdict(prompt))
    return "\n".join(
        (
            "CLARIFICATION NEEDED",
            f"CENTER {prompt.center_summary}",
            f"OBSERVED_DRIFT {prompt.drift_summary}",
            f"WHY_THIS_QUESTION {prompt.why_question_matters}",
            f"QUESTION {prompt.question['text']}",
            "ANSWER in your own words; AgentGov stores only a reviewed normalized summary",
            "METRIC this discussion turn is not a governance decision episode",
            "AUTHORITY display and discussion apply no task, architecture, scope, code, Git, deployment, or release change",
        )
    ) + "\n"


def clarification_update_from_payload(payload: Any) -> ClarificationUpdate:
    fields = {
        "contract", "schema_version", "update_id", "dialogue", "prompt",
        "question_id", "actor", "recorded_at", "answer_summary", "center_patch",
        "new_questions", "candidate_resolutions", "recommended_resolution_id",
        "ready_requested", "content_boundary", "authority_boundary",
    }
    if not isinstance(payload, Mapping) or set(payload) != fields:
        raise ClarificationDialogueError("clarification update has unexpected fields")
    if (
        payload.get("contract") != CLARIFICATION_UPDATE_CONTRACT
        or payload.get("schema_version") != CLARIFICATION_UPDATE_SCHEMA_VERSION
    ):
        raise ClarificationDialogueError("clarification update contract is unsupported")
    update_id = payload.get("update_id")
    if not isinstance(update_id, str) or not _UPDATE_ID_RE.fullmatch(update_id):
        raise ClarificationDialogueError("clarification update_id is invalid")
    dialogue = payload.get("dialogue")
    if not isinstance(dialogue, Mapping) or set(dialogue) != {"dialogue_id", "revision", "digest"}:
        raise ClarificationDialogueError("clarification update dialogue binding is invalid")
    if (
        not isinstance(dialogue.get("dialogue_id"), str)
        or not _DIALOGUE_ID_RE.fullmatch(dialogue["dialogue_id"])
        or not isinstance(dialogue.get("revision"), int)
        or dialogue["revision"] < 1
        or not isinstance(dialogue.get("digest"), str)
        or not _DIGEST_RE.fullmatch(dialogue["digest"])
    ):
        raise ClarificationDialogueError("clarification update dialogue identity is invalid")
    prompt = payload.get("prompt")
    if not isinstance(prompt, Mapping) or set(prompt) != {"prompt_id", "prompt_digest"}:
        raise ClarificationDialogueError("clarification update prompt binding is invalid")
    if (
        not isinstance(prompt.get("prompt_id"), str)
        or not _PROMPT_ID_RE.fullmatch(prompt["prompt_id"])
        or not isinstance(prompt.get("prompt_digest"), str)
        or not _DIGEST_RE.fullmatch(prompt["prompt_digest"])
    ):
        raise ClarificationDialogueError("clarification update prompt identity is invalid")
    question_id = payload.get("question_id")
    if not isinstance(question_id, str) or not _QUESTION_ID_RE.fullmatch(question_id):
        raise ClarificationDialogueError("clarification update question_id is invalid")
    actor = payload.get("actor")
    if not isinstance(actor, Mapping) or set(actor) != {"adapter_id", "actor_class", "recording_method"}:
        raise ClarificationDialogueError("clarification update actor is invalid")
    if (
        not isinstance(actor.get("adapter_id"), str)
        or not _ADAPTER_ID_RE.fullmatch(actor["adapter_id"])
        or actor.get("actor_class") != "human"
        or actor.get("recording_method") not in {
            "host_conversation", "reference_terminal_conversation"
        }
    ):
        raise ClarificationDialogueError("clarification update requires a human conversation record")
    recorded_at = payload.get("recorded_at")
    if not isinstance(recorded_at, str) or not _TIME_RE.fullmatch(recorded_at):
        raise ClarificationDialogueError("clarification update time is invalid")
    resolutions = _resolutions(payload.get("candidate_resolutions"))
    recommendation = _recommendation(payload.get("recommended_resolution_id"), resolutions)
    if not isinstance(payload.get("ready_requested"), bool):
        raise ClarificationDialogueError("ready_requested must be boolean")
    return ClarificationUpdate(
        contract=CLARIFICATION_UPDATE_CONTRACT,
        schema_version=CLARIFICATION_UPDATE_SCHEMA_VERSION,
        update_id=update_id,
        dialogue=dict(dialogue),
        prompt=dict(prompt),
        question_id=question_id,
        actor=dict(actor),
        recorded_at=recorded_at,
        answer_summary=_text(payload.get("answer_summary"), label="normalized answer summary"),
        center_patch=_center(payload.get("center_patch"), patch=True),
        new_questions=_questions(payload.get("new_questions"), label="new questions"),
        candidate_resolutions=resolutions,
        recommended_resolution_id=recommendation,
        ready_requested=payload["ready_requested"],
        content_boundary=_content_boundary(payload.get("content_boundary")),
        authority_boundary=_authority(payload.get("authority_boundary")),
    )


def apply_clarification_update(
    dialogue: ClarificationDialogue,
    prompt: ClarificationPrompt,
    update: ClarificationUpdate,
) -> ClarificationDialogue:
    dialogue = clarification_dialogue_from_payload(asdict(dialogue))
    prompt = clarification_prompt_from_payload(asdict(prompt))
    update = clarification_update_from_payload(asdict(update))
    dialogue_digest = canonical_document_digest(asdict(dialogue))
    prompt_digest = canonical_document_digest(asdict(prompt))
    expected_dialogue = {
        "dialogue_id": dialogue.dialogue_id,
        "revision": dialogue.revision,
        "digest": dialogue_digest,
    }
    if prompt.dialogue != expected_dialogue or update.dialogue != expected_dialogue:
        raise ClarificationDialogueError("clarification dialogue drifted after the question")
    if update.prompt != {"prompt_id": prompt.prompt_id, "prompt_digest": prompt_digest}:
        raise ClarificationDialogueError("clarification update does not match the exact prompt")
    if update.question_id != prompt.question["question_id"]:
        raise ClarificationDialogueError("clarification update answers a different question")
    current = next(
        (item for item in dialogue.open_questions if item["question_id"] == update.question_id),
        None,
    )
    if current is None:
        raise ClarificationDialogueError("clarification question is no longer open")
    remaining = tuple(
        item for item in dialogue.open_questions if item["question_id"] != update.question_id
    )
    remaining_ids = {item["question_id"] for item in remaining}
    if any(item["question_id"] in remaining_ids for item in update.new_questions):
        raise ClarificationDialogueError("clarification update duplicates an open question")
    open_questions = remaining + update.new_questions
    center = dict(dialogue.center)
    for key, value in update.center_patch.items():
        if value is not None:
            center[key] = value
    resolutions = update.candidate_resolutions or dialogue.candidate_resolutions
    recommendation = (
        update.recommended_resolution_id
        if update.candidate_resolutions
        else dialogue.recommended_resolution_id
    )
    material_open = any(item["material"] for item in open_questions)
    if update.ready_requested and (
        material_open or len(resolutions) < 2 or recommendation is None
    ):
        raise ClarificationDialogueError(
            "dialogue cannot become ready while material unknowns or unstable options remain"
        )
    status = "ready_for_decision" if update.ready_requested else "exploring"
    records = (dialogue.discussion_records + (
        {
            "question_id": current["question_id"],
            "question_summary": current["question"],
            "answer_summary": update.answer_summary,
            "recorded_at": update.recorded_at,
            "recorded_by": "human",
        },
    ))[-100:]
    return clarification_dialogue_from_payload(
        {
            **asdict(dialogue),
            "revision": dialogue.revision + 1,
            "status": status,
            "center": center,
            "open_questions": list(open_questions),
            "discussion_records": list(records),
            "candidate_resolutions": list(resolutions),
            "recommended_resolution_id": recommendation,
            "metrics": {
                "clarification_turns": dialogue.metrics["clarification_turns"] + 1,
                "governance_decision_episodes": dialogue.metrics["governance_decision_episodes"],
            },
        }
    )


def build_alignment_resolution_prompt(
    dialogue: ClarificationDialogue,
    *,
    binding: Mapping[str, str] | None = None,
) -> HumanDecisionPrompt:
    dialogue = clarification_dialogue_from_payload(asdict(dialogue))
    if dialogue.status != "ready_for_decision":
        raise ClarificationDialogueError("alignment resolution requires a ready dialogue")
    if binding is None:
        capability = REFERENCE_HOST_CAPABILITIES.interactions["task_admission"]
        binding = {
            "adapter_id": REFERENCE_HOST_CAPABILITIES.adapter_id,
            "delivery_mode": capability["delivery_mode"],
            "decision_recording": capability["decision_recording"],
            "reason_code": capability["reason_code"],
        }
    options = tuple(
        {
            "id": item["id"],
            "index": index,
            "label": item["label"],
            "effect": item["effect"],
            "transition": {
                "action": "record_alignment_resolution",
                "resolution_id": item["id"],
            },
        }
        for index, item in enumerate(dialogue.candidate_resolutions, start=1)
    )
    return build_human_decision_prompt(
        source={
            "contract": CLARIFICATION_DIALOGUE_CONTRACT,
            "id": dialogue.dialogue_id,
            "digest": canonical_document_digest(asdict(dialogue)),
        },
        kind="alignment_resolution",
        title="Choose how to re-center the work",
        summary=(
            f"The clarification dialogue resolved material unknowns around "
            f"{dialogue.drift['kind']} drift."
        ),
        why_now="The alternatives are stable enough for one durable human-owned direction decision.",
        recommended_option_id=dialogue.recommended_resolution_id,
        options=options,
        binding={
            "adapter_id": binding["adapter_id"],
            "delivery_mode": binding["delivery_mode"],
            "decision_recording": binding["decision_recording"],
            "reason_code": binding["reason_code"],
        },
    )


def resolve_clarification_dialogue(
    dialogue: ClarificationDialogue,
    prompt: HumanDecisionPrompt,
    result: HumanDecisionResult,
) -> ClarificationDialogue:
    dialogue = clarification_dialogue_from_payload(asdict(dialogue))
    if dialogue.status != "ready_for_decision":
        raise ClarificationDialogueError("dialogue is not ready for final resolution")
    validate_result_for_prompt(prompt, result)
    if prompt.source != {
        "contract": CLARIFICATION_DIALOGUE_CONTRACT,
        "id": dialogue.dialogue_id,
        "digest": canonical_document_digest(asdict(dialogue)),
    }:
        raise ClarificationDialogueError("alignment decision does not match the exact dialogue")
    transition = result.selection["transition"]
    if transition["action"] != "record_alignment_resolution":
        raise ClarificationDialogueError("human result is not an alignment resolution")
    option_id = transition["resolution_id"]
    candidate = next(
        (item for item in dialogue.candidate_resolutions if item["id"] == option_id),
        None,
    )
    if candidate is None:
        raise ClarificationDialogueError("selected alignment resolution is no longer available")
    center = dict(dialogue.center)
    if option_id == "adopt_new_center":
        for key, value in candidate["center_patch"].items():
            if value is not None:
                center[key] = value
    if option_id == "continue_exploration":
        if not dialogue.open_questions:
            raise ClarificationDialogueError(
                "continue_exploration requires at least one remaining non-material question"
            )
        status = "exploring"
        resolution = None
    else:
        status = "stopped" if option_id == "stop" else "resolved"
        resolution = {
            "option_id": option_id,
            "summary": candidate["effect"],
            "recorded_at": result.recorded_at,
        }
    return clarification_dialogue_from_payload(
        {
            **asdict(dialogue),
            "revision": dialogue.revision + 1,
            "status": status,
            "center": center,
            "metrics": {
                "clarification_turns": dialogue.metrics["clarification_turns"],
                "governance_decision_episodes": dialogue.metrics["governance_decision_episodes"] + 1,
            },
            "resolution": resolution,
        }
    )
