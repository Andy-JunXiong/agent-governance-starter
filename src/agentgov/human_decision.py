"""Vendor-neutral proactive prompts and bounded human decision results."""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from dataclasses import asdict, dataclass
from typing import Any, Callable, Mapping

from agentgov.admission_routing import (
    AdmissionRoute,
    AdmissionRoutingError,
    admission_route_document,
    build_admission_route,
)
from agentgov.event_store import utc_now
from agentgov.host_interaction import (
    REFERENCE_HOST_CAPABILITIES,
    HostInteractionCapabilities,
    HostInteractionRequest,
    host_interaction_request_from_payload,
)
from agentgov.path_policy import scope_path_error
from agentgov.task_proposal import (
    TaskAdmissionResult,
    TaskProposalPolicyError,
    apply_task_admission_plan,
)


DECISION_PROMPT_CONTRACT = "agentgov.human-decision-prompt"
DECISION_PROMPT_SCHEMA_VERSION = "1.0"
DECISION_RESULT_CONTRACT = "agentgov.human-decision-result"
DECISION_RESULT_SCHEMA_VERSION = "1.0"

_PROMPT_ID_RE = re.compile(r"^dpr-[0-9a-f]{32}$")
_RESULT_ID_RE = re.compile(r"^drs-[0-9a-f]{32}$")
_SOURCE_ID_RE = re.compile(r"^(?:req|wrq|dlg)-[0-9a-f]{32}$")
_OPTION_ID_RE = re.compile(r"^[a-z][a-z0-9_]*$")
_ADAPTER_ID_RE = re.compile(r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$")
_TASK_ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_TIME_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$")
_SENSITIVE_RE = re.compile(
    r"(?i)(?:api[_-]?key|access[_-]?token|auth[_-]?token|password|passwd|secret)\s*[:=]"
)
_ABSOLUTE_PATH_RE = re.compile(r"(?i)(?:^|\s)(?:[a-z]:[\\/]|/(?:users|home|var|etc|tmp)/)")

_PROMPT_AUTHORITY_FIELDS = {
    "decision_recorded",
    "decision_applied",
    "authorizes_code_change",
    "authorizes_scope_expansion",
    "authorizes_exception",
    "authorizes_git_operations",
    "authorizes_deployment",
    "authorizes_release",
}
_RESULT_AUTHORITY_FIELDS = _PROMPT_AUTHORITY_FIELDS | {
    "selected_transition_authorized"
}


class HumanDecisionError(ValueError):
    """A human decision prompt, selection, or application is invalid or unsafe."""


@dataclass(frozen=True)
class HumanDecisionPrompt:
    contract: str
    schema_version: str
    prompt_id: str
    source: Mapping[str, str]
    kind: str
    title: str
    summary: str
    why_now: str
    recommended_option_id: str
    options: tuple[Mapping[str, Any], ...]
    input: Mapping[str, Any]
    binding: Mapping[str, str]
    authority_boundary: Mapping[str, bool]


@dataclass(frozen=True)
class HumanDecisionResult:
    contract: str
    schema_version: str
    result_id: str
    prompt: Mapping[str, str]
    source: Mapping[str, str]
    selection: Mapping[str, Any]
    actor: Mapping[str, str]
    recorded_at: str
    authority_boundary: Mapping[str, bool]


def canonical_document_digest(document: Mapping[str, Any]) -> str:
    encoded = json.dumps(
        document,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _prompt_digest(prompt: HumanDecisionPrompt) -> str:
    return canonical_document_digest(asdict(prompt))


def _prompt_authority() -> Mapping[str, bool]:
    return {field: False for field in sorted(_PROMPT_AUTHORITY_FIELDS)}


def _bounded_text(value: Any, *, label: str, maximum: int = 500) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        raise HumanDecisionError(f"{label} must be non-empty and at most {maximum} characters")
    if any(unicodedata.category(character).startswith("C") for character in value):
        raise HumanDecisionError(f"{label} contains unsupported control characters")
    if _SENSITIVE_RE.search(value) or _ABSOLUTE_PATH_RE.search(value):
        raise HumanDecisionError(f"{label} contains sensitive or host-local content")
    return value


def _validate_transition(value: Any) -> Mapping[str, str]:
    if not isinstance(value, Mapping) or "action" not in value:
        raise HumanDecisionError("decision option transition is invalid")
    action = value.get("action")
    if action == "none":
        if set(value) != {"action"}:
            raise HumanDecisionError("none transition has unexpected fields")
    elif action == "emit_core_event":
        if set(value) != {"action", "event_type", "fact_name", "fact_value"}:
            raise HumanDecisionError("Core event transition has unexpected fields")
        triple = (value.get("event_type"), value.get("fact_name"), value.get("fact_value"))
        allowed = {
            ("scope.decision_recorded", "scope_decision", "approved"),
            ("scope.decision_recorded", "scope_decision", "declined"),
            ("scope.decision_recorded", "scope_decision", "needs_human"),
            ("session.reviewed", "review_outcome", "accepted"),
            ("session.reviewed", "review_outcome", "changes_requested"),
        }
        if triple not in allowed:
            raise HumanDecisionError("Core event transition is unsupported")
    elif action == "admit_exact_task":
        if set(value) != {"action", "target", "task_id", "task_digest"}:
            raise HumanDecisionError("task admission transition has unexpected fields")
        target = value.get("target")
        task_id = value.get("task_id")
        digest = value.get("task_digest")
        if (
            not isinstance(target, str)
            or scope_path_error(target)
            or not isinstance(task_id, str)
            or not _TASK_ID_RE.fullmatch(task_id)
            or target != f"governance/tasks/{task_id}.json"
            or not isinstance(digest, str)
            or not _DIGEST_RE.fullmatch(digest)
        ):
            raise HumanDecisionError("task admission transition identity is invalid")
    elif action == "record_alignment_resolution":
        if set(value) != {"action", "resolution_id"}:
            raise HumanDecisionError("alignment resolution transition has unexpected fields")
        if value.get("resolution_id") not in {
            "return_to_center",
            "adopt_new_center",
            "split_new_requirement",
            "continue_exploration",
            "stop",
        }:
            raise HumanDecisionError("alignment resolution is unsupported")
    else:
        raise HumanDecisionError("decision option transition action is unsupported")
    return dict(value)


def human_decision_prompt_from_payload(payload: Any) -> HumanDecisionPrompt:
    fields = {
        "contract", "schema_version", "prompt_id", "source", "kind", "title",
        "summary", "why_now", "recommended_option_id", "options", "input",
        "binding", "authority_boundary",
    }
    if not isinstance(payload, Mapping) or set(payload) != fields:
        raise HumanDecisionError("human decision prompt has unexpected fields")
    if (
        payload.get("contract") != DECISION_PROMPT_CONTRACT
        or payload.get("schema_version") != DECISION_PROMPT_SCHEMA_VERSION
    ):
        raise HumanDecisionError("human decision prompt uses an unsupported contract")
    prompt_id = payload.get("prompt_id")
    if not isinstance(prompt_id, str) or not _PROMPT_ID_RE.fullmatch(prompt_id):
        raise HumanDecisionError("human decision prompt_id is invalid")
    source = payload.get("source")
    if not isinstance(source, Mapping) or set(source) != {"contract", "id", "digest"}:
        raise HumanDecisionError("human decision prompt source is invalid")
    if source.get("contract") not in {
        "agentgov.host-interaction-request", "agentgov.admission-route",
        "agentgov.clarification-dialogue",
    }:
        raise HumanDecisionError("human decision prompt source contract is unsupported")
    if not isinstance(source.get("id"), str) or not _SOURCE_ID_RE.fullmatch(source["id"]):
        raise HumanDecisionError("human decision prompt source id is invalid")
    if not isinstance(source.get("digest"), str) or not _DIGEST_RE.fullmatch(source["digest"]):
        raise HumanDecisionError("human decision prompt source digest is invalid")
    kind = payload.get("kind")
    if kind not in {
        "task_routing", "task_admission", "scope_resolution",
        "completion_review", "alignment_resolution",
    }:
        raise HumanDecisionError("human decision prompt kind is unsupported")
    title = _bounded_text(payload.get("title"), label="title", maximum=160)
    summary = _bounded_text(payload.get("summary"), label="summary")
    why_now = _bounded_text(payload.get("why_now"), label="why_now")
    options = payload.get("options")
    if not isinstance(options, (list, tuple)) or not 2 <= len(options) <= 5:
        raise HumanDecisionError("human decision prompt requires two through five options")
    normalized_options: list[Mapping[str, Any]] = []
    option_ids: set[str] = set()
    for index, option in enumerate(options, start=1):
        if not isinstance(option, Mapping) or set(option) != {
            "id", "index", "label", "effect", "transition"
        }:
            raise HumanDecisionError("human decision option has unexpected fields")
        option_id = option.get("id")
        if (
            not isinstance(option_id, str)
            or not _OPTION_ID_RE.fullmatch(option_id)
            or option_id in option_ids
            or option.get("index") != index
        ):
            raise HumanDecisionError("human decision option identity is invalid")
        option_ids.add(option_id)
        normalized_options.append(
            {
                "id": option_id,
                "index": index,
                "label": _bounded_text(option.get("label"), label="option label", maximum=160),
                "effect": _bounded_text(option.get("effect"), label="option effect"),
                "transition": _validate_transition(option.get("transition")),
            }
        )
    recommended = payload.get("recommended_option_id")
    if recommended not in option_ids:
        raise HumanDecisionError("recommended option must identify one displayed option")
    input_contract = payload.get("input")
    if input_contract != {
        "mode": "single_select",
        "minimum_selections": 1,
        "maximum_selections": 1,
        "free_text_required": False,
    }:
        raise HumanDecisionError("human decision input must require one selection and no free text")
    binding = payload.get("binding")
    if not isinstance(binding, Mapping) or set(binding) != {
        "adapter_id", "delivery_mode", "decision_recording", "reason_code"
    }:
        raise HumanDecisionError("human decision prompt binding is invalid")
    if not isinstance(binding.get("adapter_id"), str) or not _ADAPTER_ID_RE.fullmatch(binding["adapter_id"]):
        raise HumanDecisionError("human decision prompt adapter_id is invalid")
    if binding.get("delivery_mode") not in {"native", "structured", "context_only", "unsupported"}:
        raise HumanDecisionError("human decision prompt delivery mode is unsupported")
    if binding.get("decision_recording") not in {"adapter_event", "host_managed", "unavailable"}:
        raise HumanDecisionError("human decision prompt recording mode is unsupported")
    _bounded_text(binding.get("reason_code"), label="binding reason_code", maximum=120)
    authority = payload.get("authority_boundary")
    if (
        not isinstance(authority, Mapping)
        or set(authority) != _PROMPT_AUTHORITY_FIELDS
        or any(value is not False for value in authority.values())
    ):
        raise HumanDecisionError("displaying a prompt cannot record or apply a decision")
    return HumanDecisionPrompt(
        contract=DECISION_PROMPT_CONTRACT,
        schema_version=DECISION_PROMPT_SCHEMA_VERSION,
        prompt_id=prompt_id,
        source=dict(source),
        kind=kind,
        title=title,
        summary=summary,
        why_now=why_now,
        recommended_option_id=recommended,
        options=tuple(normalized_options),
        input=dict(input_contract),
        binding=dict(binding),
        authority_boundary=dict(authority),
    )


def build_human_decision_prompt(
    *,
    source: Mapping[str, str],
    kind: str,
    title: str,
    summary: str,
    why_now: str,
    recommended_option_id: str,
    options: tuple[Mapping[str, Any], ...],
    binding: Mapping[str, str],
) -> HumanDecisionPrompt:
    identity = f"{source['contract']}\x00{source['id']}\x00{source['digest']}\x00{kind}"
    payload = {
        "contract": DECISION_PROMPT_CONTRACT,
        "schema_version": DECISION_PROMPT_SCHEMA_VERSION,
        "prompt_id": "dpr-" + hashlib.sha256(identity.encode("utf-8")).hexdigest()[:32],
        "source": dict(source),
        "kind": kind,
        "title": title,
        "summary": summary,
        "why_now": why_now,
        "recommended_option_id": recommended_option_id,
        "options": list(options),
        "input": {
            "mode": "single_select",
            "minimum_selections": 1,
            "maximum_selections": 1,
            "free_text_required": False,
        },
        "binding": dict(binding),
        "authority_boundary": _prompt_authority(),
    }
    return human_decision_prompt_from_payload(payload)


def build_host_decision_prompt(request: HostInteractionRequest) -> HumanDecisionPrompt:
    """Turn an existing real human gate into a proactive bounded choice."""

    request = host_interaction_request_from_payload(asdict(request))
    source = {
        "contract": request.contract,
        "id": request.request_id,
        "digest": canonical_document_digest(asdict(request)),
    }
    recommendations = {
        "task_admission": "route_work_request",
        "scope_resolution": "narrow_changes",
        "completion_review": "request_changes",
    }
    kinds = {
        "task_admission": "task_routing",
        "scope_resolution": "scope_resolution",
        "completion_review": "completion_review",
    }
    options: list[Mapping[str, Any]] = []
    for index, option in enumerate(request.options, start=1):
        next_event = option["next_event"]
        transition: Mapping[str, str]
        if next_event is None:
            transition = {"action": "none"}
            effect = "Return this routing choice to the host; no repository transition is applied."
        else:
            transition = {"action": "emit_core_event", **next_event}
            effect = (
                f"Authorize only {next_event['event_type']} with "
                f"{next_event['fact_name']}={next_event['fact_value']}."
            )
        options.append(
            {
                "id": option["id"],
                "index": index,
                "label": option["label"],
                "effect": effect,
                "transition": transition,
            }
        )
    return build_human_decision_prompt(
        source=source,
        kind=kinds[request.kind],
        title=request.title,
        summary=request.summary,
        why_now="AgentGov reached a real human decision boundary and cannot choose on the user's behalf.",
        recommended_option_id=recommendations[request.kind],
        options=tuple(options),
        binding=request.binding,
    )


def build_route_decision_prompt(
    route: AdmissionRoute,
    *,
    capabilities: HostInteractionCapabilities = REFERENCE_HOST_CAPABILITIES,
) -> HumanDecisionPrompt:
    """Build a one-selection prompt for one exact low-risk human-review route."""

    if route.route != "human_review" or route.admission_plan is None:
        raise HumanDecisionError("only a planned low-risk human_review route can be prompted for admission")
    plan = route.admission_plan
    source_document = admission_route_document(route)
    source = {
        "contract": "agentgov.admission-route",
        "id": route.request["request_id"],
        "digest": canonical_document_digest(source_document),
    }
    binding = capabilities.interactions["task_admission"]
    options = (
        {
            "id": "approve_exact_task",
            "index": 1,
            "label": "Approve this exact low-risk task",
            "effect": f"Create only {plan.target}; do not start a session or execute code.",
            "transition": {
                "action": "admit_exact_task",
                "target": plan.target,
                "task_id": plan.task_document["task_id"],
                "task_digest": plan.task_digest,
            },
        },
        {
            "id": "request_changes",
            "index": 2,
            "label": "Request changes",
            "effect": "Return the proposal for revision and make no repository change.",
            "transition": {"action": "none"},
        },
        {
            "id": "reject",
            "index": 3,
            "label": "Reject this task",
            "effect": "Reject the proposal and make no repository change.",
            "transition": {"action": "none"},
        },
    )
    return build_human_decision_prompt(
        source=source,
        kind="task_admission",
        title=f"Decide whether to admit {plan.task_document['task_id']}",
        summary="The low-risk task is valid but falls outside the current standing fast-track delegation.",
        why_now="A human decision is required because the standing policy does not authorize this exact task.",
        recommended_option_id="request_changes",
        options=options,
        binding={
            "adapter_id": capabilities.adapter_id,
            "delivery_mode": binding["delivery_mode"],
            "decision_recording": binding["decision_recording"],
            "reason_code": binding["reason_code"],
        },
    )


def render_human_decision_prompt_terminal(prompt: HumanDecisionPrompt) -> str:
    prompt = human_decision_prompt_from_payload(asdict(prompt))
    lines = [
        "HUMAN DECISION REQUIRED",
        prompt.title,
        f"SUMMARY {prompt.summary}",
        f"WHY_NOW {prompt.why_now}",
    ]
    for option in prompt.options:
        recommended = " [recommended safe default]" if option["id"] == prompt.recommended_option_id else ""
        lines.append(f"[{option['index']}] {option['label']}{recommended}")
        lines.append(f"    {option['effect']}")
    lines.extend(
        (
            "INPUT select one number; no confirmation word or free-text rationale is required",
            "AUTHORITY displaying this prompt records nothing and applies nothing",
        )
    )
    return "\n".join(lines) + "\n"


def render_human_decision_prompt_json(prompt: HumanDecisionPrompt) -> str:
    return json.dumps(asdict(prompt), ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def human_decision_result_from_payload(payload: Any) -> HumanDecisionResult:
    fields = {
        "contract", "schema_version", "result_id", "prompt", "source",
        "selection", "actor", "recorded_at", "authority_boundary",
    }
    if not isinstance(payload, Mapping) or set(payload) != fields:
        raise HumanDecisionError("human decision result has unexpected fields")
    if (
        payload.get("contract") != DECISION_RESULT_CONTRACT
        or payload.get("schema_version") != DECISION_RESULT_SCHEMA_VERSION
    ):
        raise HumanDecisionError("human decision result uses an unsupported contract")
    result_id = payload.get("result_id")
    if not isinstance(result_id, str) or not _RESULT_ID_RE.fullmatch(result_id):
        raise HumanDecisionError("human decision result_id is invalid")
    prompt = payload.get("prompt")
    if not isinstance(prompt, Mapping) or set(prompt) != {"prompt_id", "prompt_digest"}:
        raise HumanDecisionError("human decision result prompt binding is invalid")
    if not isinstance(prompt.get("prompt_id"), str) or not _PROMPT_ID_RE.fullmatch(prompt["prompt_id"]):
        raise HumanDecisionError("human decision result prompt_id is invalid")
    if not isinstance(prompt.get("prompt_digest"), str) or not _DIGEST_RE.fullmatch(prompt["prompt_digest"]):
        raise HumanDecisionError("human decision result prompt digest is invalid")
    source = payload.get("source")
    if not isinstance(source, Mapping) or set(source) != {"contract", "id", "digest"}:
        raise HumanDecisionError("human decision result source is invalid")
    if source.get("contract") not in {
        "agentgov.host-interaction-request", "agentgov.admission-route",
        "agentgov.clarification-dialogue",
    }:
        raise HumanDecisionError("human decision result source contract is unsupported")
    if not isinstance(source.get("id"), str) or not _SOURCE_ID_RE.fullmatch(source["id"]):
        raise HumanDecisionError("human decision result source id is invalid")
    if not isinstance(source.get("digest"), str) or not _DIGEST_RE.fullmatch(source["digest"]):
        raise HumanDecisionError("human decision result source digest is invalid")
    selection = payload.get("selection")
    if not isinstance(selection, Mapping) or set(selection) != {"option_id", "transition"}:
        raise HumanDecisionError("human decision result selection is invalid")
    option_id = selection.get("option_id")
    if not isinstance(option_id, str) or not _OPTION_ID_RE.fullmatch(option_id):
        raise HumanDecisionError("human decision result option_id is invalid")
    transition = _validate_transition(selection.get("transition"))
    actor = payload.get("actor")
    if not isinstance(actor, Mapping) or set(actor) != {"adapter_id", "actor_class", "recording_method"}:
        raise HumanDecisionError("human decision result actor is invalid")
    if not isinstance(actor.get("adapter_id"), str) or not _ADAPTER_ID_RE.fullmatch(actor["adapter_id"]):
        raise HumanDecisionError("human decision result adapter_id is invalid")
    if actor.get("actor_class") != "human":
        raise HumanDecisionError("human decision result actor_class must equal human")
    if actor.get("recording_method") not in {"host_single_select", "reference_terminal_single_select"}:
        raise HumanDecisionError("human decision result recording method is unsupported")
    recorded_at = payload.get("recorded_at")
    if not isinstance(recorded_at, str) or not _TIME_RE.fullmatch(recorded_at):
        raise HumanDecisionError("human decision result recorded_at is invalid")
    authority = payload.get("authority_boundary")
    expected_authorized = transition["action"] != "none"
    if (
        not isinstance(authority, Mapping)
        or set(authority) != _RESULT_AUTHORITY_FIELDS
        or authority.get("decision_recorded") is not True
        or authority.get("selected_transition_authorized") is not expected_authorized
        or authority.get("decision_applied") is not False
        or any(
            authority.get(field) is not False
            for field in _RESULT_AUTHORITY_FIELDS
            - {"decision_recorded", "selected_transition_authorized", "decision_applied"}
        )
    ):
        raise HumanDecisionError("human decision result authority boundary is invalid")
    return HumanDecisionResult(
        contract=DECISION_RESULT_CONTRACT,
        schema_version=DECISION_RESULT_SCHEMA_VERSION,
        result_id=result_id,
        prompt=dict(prompt),
        source=dict(source),
        selection={"option_id": option_id, "transition": transition},
        actor=dict(actor),
        recorded_at=recorded_at,
        authority_boundary=dict(authority),
    )


def record_human_decision(
    prompt: HumanDecisionPrompt,
    *,
    selected_option_id: str,
    adapter_id: str,
    recording_method: str,
    recorded_at: str | None = None,
) -> HumanDecisionResult:
    """Record one explicit host selection without retaining the user's raw input."""

    prompt = human_decision_prompt_from_payload(asdict(prompt))
    if prompt.binding["decision_recording"] == "unavailable":
        raise HumanDecisionError("this host can display the prompt but cannot record its decision")
    if prompt.binding["delivery_mode"] in {"context_only", "unsupported"}:
        raise HumanDecisionError("this host has no trusted structured decision surface")
    if adapter_id != prompt.binding["adapter_id"]:
        raise HumanDecisionError("decision adapter does not match the displayed prompt")
    option = next((item for item in prompt.options if item["id"] == selected_option_id), None)
    if option is None:
        raise HumanDecisionError("selected option was not presented to the human")
    timestamp = recorded_at or utc_now()
    prompt_digest = _prompt_digest(prompt)
    identity = f"{prompt_digest}\x00{selected_option_id}\x00{timestamp}\x00{adapter_id}"
    authority = {field: False for field in sorted(_RESULT_AUTHORITY_FIELDS)}
    authority["decision_recorded"] = True
    authority["selected_transition_authorized"] = option["transition"]["action"] != "none"
    payload = {
        "contract": DECISION_RESULT_CONTRACT,
        "schema_version": DECISION_RESULT_SCHEMA_VERSION,
        "result_id": "drs-" + hashlib.sha256(identity.encode("utf-8")).hexdigest()[:32],
        "prompt": {"prompt_id": prompt.prompt_id, "prompt_digest": prompt_digest},
        "source": dict(prompt.source),
        "selection": {
            "option_id": selected_option_id,
            "transition": dict(option["transition"]),
        },
        "actor": {
            "adapter_id": adapter_id,
            "actor_class": "human",
            "recording_method": recording_method,
        },
        "recorded_at": timestamp,
        "authority_boundary": authority,
    }
    return human_decision_result_from_payload(payload)


def validate_result_for_prompt(
    prompt: HumanDecisionPrompt,
    result: HumanDecisionResult,
) -> None:
    prompt = human_decision_prompt_from_payload(asdict(prompt))
    result = human_decision_result_from_payload(asdict(result))
    if result.prompt != {"prompt_id": prompt.prompt_id, "prompt_digest": _prompt_digest(prompt)}:
        raise HumanDecisionError("decision result does not match the exact displayed prompt")
    if result.source != prompt.source:
        raise HumanDecisionError("decision result source does not match the displayed prompt")
    option = next((item for item in prompt.options if item["id"] == result.selection["option_id"]), None)
    if option is None or result.selection["transition"] != option["transition"]:
        raise HumanDecisionError("decision result does not match a displayed option and transition")
    if result.actor["adapter_id"] != prompt.binding["adapter_id"]:
        raise HumanDecisionError("decision result adapter does not match the displayed prompt")


def request_reference_terminal_selection(
    prompt: HumanDecisionPrompt,
    *,
    decision_reader: Callable[[str], str],
    is_interactive_terminal: bool,
) -> HumanDecisionResult:
    """Collect one numeric selection from the reference terminal surface."""

    prompt = human_decision_prompt_from_payload(asdict(prompt))
    if not is_interactive_terminal:
        raise HumanDecisionError("reference decision selection requires an interactive terminal")
    if prompt.binding["adapter_id"] != REFERENCE_HOST_CAPABILITIES.adapter_id:
        raise HumanDecisionError("reference terminal cannot record another adapter's prompt")
    raw_selection = decision_reader(f"Select one option [1-{len(prompt.options)}]: ")
    if not isinstance(raw_selection, str) or not re.fullmatch(r"[1-9]", raw_selection.strip()):
        raise HumanDecisionError("selection must be one displayed option number")
    index = int(raw_selection.strip())
    if not 1 <= index <= len(prompt.options):
        raise HumanDecisionError("selection must be one displayed option number")
    return record_human_decision(
        prompt,
        selected_option_id=prompt.options[index - 1]["id"],
        adapter_id=REFERENCE_HOST_CAPABILITIES.adapter_id,
        recording_method="reference_terminal_single_select",
    )


def apply_route_human_decision(
    route: AdmissionRoute,
    prompt: HumanDecisionPrompt,
    result: HumanDecisionResult,
) -> TaskAdmissionResult | None:
    """Apply only an exact approved low-risk task; other selections are read-only."""

    validate_result_for_prompt(prompt, result)
    if prompt.source["contract"] != "agentgov.admission-route":
        raise HumanDecisionError("only an admission-route prompt can apply a task")
    action = result.selection["transition"]["action"]
    if action == "none":
        return None
    if action != "admit_exact_task" or result.selection["option_id"] != "approve_exact_task":
        raise HumanDecisionError("selected transition cannot apply a task")
    rebuilt = build_admission_route(
        route.root,
        policy_path=route.policy_path,
        request=route.request,
    )
    if rebuilt.route != "human_review" or rebuilt.admission_plan is None:
        raise HumanDecisionError("review route changed after the human prompt")
    if canonical_document_digest(admission_route_document(rebuilt)) != prompt.source["digest"]:
        raise HumanDecisionError("review route drifted after the human prompt")
    transition = result.selection["transition"]
    plan = rebuilt.admission_plan
    if (
        transition["target"] != plan.target
        or transition["task_id"] != plan.task_document["task_id"]
        or transition["task_digest"] != plan.task_digest
    ):
        raise HumanDecisionError("approved task does not match the exact reviewed plan")
    try:
        return apply_task_admission_plan(plan)
    except (TaskProposalPolicyError, AdmissionRoutingError) as exc:
        raise HumanDecisionError(str(exc)) from exc
