"""Strict foreground JSONL transport for coding-agent lifecycle events."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping

from agentgov.development_trigger import TRIGGER_ACTORS, TRIGGER_TYPES
from agentgov.foreground_coordinator import ForegroundCycle, run_foreground_cycle
from agentgov.host_interaction import (
    REFERENCE_HOST_CAPABILITIES,
    HostInteractionCapabilities,
    HostInteractionRequest,
    build_host_interaction_request,
)
from agentgov.human_decision import (
    HumanDecisionPrompt,
    HumanDecisionResult,
    build_host_decision_prompt,
    validate_result_for_prompt,
)
from agentgov.reference_adapter import build_reference_trigger


EVENT_CONTRACT = "agentgov.coding-agent-event"
EVENT_SCHEMA_VERSION = "1.0"
CARD_CONTRACT = "agentgov.interaction-card"
CARD_SCHEMA_VERSION = "1.1"
RESPONSE_CONTRACT = "agentgov.coding-agent-response"
RESPONSE_SCHEMA_VERSION = "1.3"

_EVENT_ID_RE = re.compile(r"^evt-[0-9a-f]{32}$")
_ID_RE = re.compile(r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$")


class CodingAgentTransportError(ValueError):
    """A host event is unsafe, ambiguous, or outside the stream contract."""


@dataclass(frozen=True)
class CodingAgentEvent:
    contract: str
    schema_version: str
    event_id: str
    occurred_at: str
    event_type: str
    source: Mapping[str, str]
    correlation_id: str
    facts: Mapping[str, str | None]


@dataclass(frozen=True)
class InteractionCard:
    contract: str
    schema_version: str
    kind: str
    status: str
    title: str
    summary: str
    facts: tuple[Mapping[str, str], ...]
    actions: tuple[str, ...]
    authority_boundary: Mapping[str, bool]


@dataclass(frozen=True)
class CodingAgentResponse:
    contract: str
    schema_version: str
    sequence: int
    event: Mapping[str, str]
    status: str
    cycle: ForegroundCycle
    card: InteractionCard | None
    interaction: HostInteractionRequest | None
    decision_prompt: HumanDecisionPrompt | None


def _timestamp(value: Any) -> str:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise CodingAgentTransportError("occurred_at must be a UTC Z timestamp")
    try:
        datetime.fromisoformat(value.removesuffix("Z") + "+00:00")
    except ValueError as exc:
        raise CodingAgentTransportError("occurred_at must be a UTC Z timestamp") from exc
    return value


def _identifier(value: Any, *, label: str, maximum: int) -> str:
    if not isinstance(value, str) or len(value) > maximum or not _ID_RE.fullmatch(value):
        raise CodingAgentTransportError(f"{label} is invalid")
    return value


def _safe_reference(value: Any) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value or "\\" in value:
        raise CodingAgentTransportError("evidence_ref must be a repository-relative POSIX path")
    path = Path(value)
    if path.is_absolute() or value == "." or ".." in path.parts or ":" in path.parts[0]:
        raise CodingAgentTransportError("evidence_ref must be a repository-relative POSIX path")
    return value


def coding_agent_event_from_payload(payload: Any) -> CodingAgentEvent:
    """Validate a privacy-bounded host event and reject every unknown field."""

    fields = {
        "contract",
        "schema_version",
        "event_id",
        "occurred_at",
        "event_type",
        "source",
        "correlation_id",
        "facts",
    }
    if not isinstance(payload, Mapping) or set(payload) != fields:
        raise CodingAgentTransportError("coding-agent event has unexpected fields")
    if payload.get("contract") != EVENT_CONTRACT or payload.get("schema_version") != EVENT_SCHEMA_VERSION:
        raise CodingAgentTransportError("coding-agent event uses an unsupported contract")

    event_id = payload.get("event_id")
    if not isinstance(event_id, str) or not _EVENT_ID_RE.fullmatch(event_id):
        raise CodingAgentTransportError("event_id is invalid")
    occurred_at = _timestamp(payload.get("occurred_at"))
    event_type = payload.get("event_type")
    if event_type not in TRIGGER_TYPES:
        raise CodingAgentTransportError("event_type is unsupported")

    source = payload.get("source")
    if not isinstance(source, Mapping) or set(source) != {"adapter_id", "actor_class"}:
        raise CodingAgentTransportError("source has unexpected fields")
    adapter_id = _identifier(source.get("adapter_id"), label="source adapter_id", maximum=80)
    actor_class = source.get("actor_class")
    if actor_class not in TRIGGER_ACTORS:
        raise CodingAgentTransportError("source actor_class is unsupported")
    correlation_id = _identifier(
        payload.get("correlation_id"), label="correlation_id", maximum=120
    )

    facts = payload.get("facts")
    fact_fields = {
        "validation_outcome",
        "evidence_ref",
        "scope_decision",
        "review_outcome",
    }
    if not isinstance(facts, Mapping) or set(facts) != fact_fields:
        raise CodingAgentTransportError("facts has unexpected fields")
    validation_outcome = facts.get("validation_outcome")
    evidence_ref = _safe_reference(facts.get("evidence_ref"))
    scope_decision = facts.get("scope_decision")
    review_outcome = facts.get("review_outcome")

    if event_type == "validation.completed":
        if validation_outcome not in {"passed", "failed"}:
            raise CodingAgentTransportError("validation.completed requires validation_outcome")
    elif validation_outcome is not None or evidence_ref is not None:
        raise CodingAgentTransportError(
            "validation_outcome and evidence_ref are only valid for validation.completed"
        )

    if event_type == "scope.decision_recorded":
        if actor_class != "human" or scope_decision not in {
            "approved",
            "declined",
            "needs_human",
        }:
            raise CodingAgentTransportError(
                "scope.decision_recorded requires a human scope_decision"
            )
    elif scope_decision is not None:
        raise CodingAgentTransportError(
            "scope_decision is only valid for scope.decision_recorded"
        )

    if event_type == "session.reviewed":
        if actor_class != "human" or review_outcome not in {
            "accepted",
            "changes_requested",
        }:
            raise CodingAgentTransportError(
                "session.reviewed requires a human review_outcome"
            )
    elif review_outcome is not None:
        raise CodingAgentTransportError(
            "review_outcome is only valid for session.reviewed"
        )

    return CodingAgentEvent(
        contract=EVENT_CONTRACT,
        schema_version=EVENT_SCHEMA_VERSION,
        event_id=event_id,
        occurred_at=occurred_at,
        event_type=event_type,
        source={"adapter_id": adapter_id, "actor_class": actor_class},
        correlation_id=correlation_id,
        facts={
            "validation_outcome": validation_outcome,
            "evidence_ref": evidence_ref,
            "scope_decision": scope_decision,
            "review_outcome": review_outcome,
        },
    )


def coding_agent_event_from_json(line: str) -> CodingAgentEvent:
    """Parse one JSONL record without accepting blank or non-object records."""

    if not line.strip():
        raise CodingAgentTransportError("coding-agent stream records cannot be blank")
    try:
        payload = json.loads(line)
    except json.JSONDecodeError as exc:
        raise CodingAgentTransportError("coding-agent stream record is not valid JSON") from exc
    return coding_agent_event_from_payload(payload)


def coding_agent_event_from_human_decision(
    response: CodingAgentResponse,
    result: HumanDecisionResult,
    *,
    event_id: str,
    occurred_at: str,
) -> CodingAgentEvent:
    """Carry one recorded scope/completion selection into its predeclared Core event."""

    if response.decision_prompt is None:
        raise CodingAgentTransportError("response has no human decision prompt")
    try:
        validate_result_for_prompt(response.decision_prompt, result)
    except ValueError as exc:
        raise CodingAgentTransportError(str(exc)) from exc
    transition = result.selection["transition"]
    if transition["action"] != "emit_core_event":
        raise CodingAgentTransportError(
            "selected decision has no Core event transition"
        )
    facts: dict[str, str | None] = {
        "validation_outcome": None,
        "evidence_ref": None,
        "scope_decision": None,
        "review_outcome": None,
    }
    facts[transition["fact_name"]] = transition["fact_value"]
    return coding_agent_event_from_payload(
        {
            "contract": EVENT_CONTRACT,
            "schema_version": EVENT_SCHEMA_VERSION,
            "event_id": event_id,
            "occurred_at": occurred_at,
            "event_type": transition["event_type"],
            "source": {
                "adapter_id": result.actor["adapter_id"],
                "actor_class": "human",
            },
            "correlation_id": response.event["correlation_id"],
            "facts": facts,
        }
    )


def _authority_boundary() -> Mapping[str, bool]:
    return {
        "authorizes_scope_expansion": False,
        "authorizes_exception": False,
        "authorizes_commit": False,
        "authorizes_merge": False,
        "authorizes_deployment": False,
    }


def _task_card(repository: Path, cycle: ForegroundCycle) -> InteractionCard:
    if cycle.task_ref is None:
        return InteractionCard(
            contract=CARD_CONTRACT,
            schema_version=CARD_SCHEMA_VERSION,
            kind="task",
            status="review_required",
            title="Work request routing available",
            summary=(
                "No active admitted task exists. No-write work needs no task; route any "
                "repository change before implementation begins."
            ),
            facts=(
                {"label": "governance", "value": "scope not inferred from prompts"},
                {
                    "label": "routing_contract",
                    "value": "agentgov.work-request 1.0; no-write routes require zero interruptions",
                },
                {
                    "label": "proposal_contract",
                    "value": "agentgov.task-proposal 1.0; proposing does not admit the task",
                },
                {"label": "dashboard", "value": cycle.dashboard_ref},
            ),
            actions=("route_work_request", "prepare_task_proposal", "review_task", "decline"),
            authority_boundary=_authority_boundary(),
        )

    from agentgov.development_session import resolve_active_task

    task_path, _ = resolve_active_task(repository)
    document = json.loads(task_path.read_text(encoding="utf-8"))
    scope = document["scope"]
    validations = document["validation_commands"]
    summary = document.get("goal") or document["requirement"]["summary"]
    return InteractionCard(
        contract=CARD_CONTRACT,
        schema_version=CARD_SCHEMA_VERSION,
        kind="task",
        status="active",
        title=document["title"],
        summary=summary,
        facts=(
            {"label": "task", "value": cycle.task_ref["task_id"]},
            {
                "label": "scope",
                "value": f"{len(scope['include_paths'])} included / {len(scope['exclude_paths'])} excluded",
            },
            {"label": "validation", "value": f"{len(validations)} pre-approved commands"},
            {"label": "dashboard", "value": cycle.dashboard_ref},
        ),
        actions=("continue", "request_scope_decision"),
        authority_boundary=_authority_boundary(),
    )


def _completion_card(cycle: ForegroundCycle) -> InteractionCard:
    outcomes = {action["name"]: action["outcome"] for action in cycle.actions}
    if cycle.status == "review_ready":
        summary = "Admitted scope and validation evidence are fresh. Human completion review is required."
        actions = ("accept", "request_changes")
    elif cycle.status == "blocked":
        summary = "Completion is blocked. Review the deterministic findings before continuing."
        actions = ("review_findings", "request_changes")
    else:
        summary = "Completion is not yet review-ready. Review the recorded evidence limits."
        actions = ("review_evidence", "continue")
    return InteractionCard(
        contract=CARD_CONTRACT,
        schema_version=CARD_SCHEMA_VERSION,
        kind="completion",
        status=cycle.status,
        title="Completion review",
        summary=summary,
        facts=(
            {"label": "scope", "value": outcomes.get("check_scope", "not_run")},
            {
                "label": "validation",
                "value": outcomes.get("run_preapproved_validation", "not_run"),
            },
            {
                "label": "evidence",
                "value": outcomes.get("reconcile_completion", "not_run"),
            },
            {"label": "dashboard", "value": cycle.dashboard_ref},
        ),
        actions=actions,
        authority_boundary=_authority_boundary(),
    )


def _scope_card(cycle: ForegroundCycle) -> InteractionCard:
    reason = (
        cycle.human_gate["reason_code"]
        if cycle.human_gate is not None
        else "observed_changes_outside_admitted_scope"
    )
    return InteractionCard(
        contract=CARD_CONTRACT,
        schema_version=CARD_SCHEMA_VERSION,
        kind="scope",
        status=cycle.status,
        title="Scope resolution required",
        summary=(
            "A human must choose whether to narrow the changes or review a revised "
            "task. This card does not change the admitted scope."
        ),
        facts=(
            {"label": "reason", "value": reason},
            {"label": "dashboard", "value": cycle.dashboard_ref},
        ),
        actions=("review_task_revision", "narrow_changes", "needs_human"),
        authority_boundary=_authority_boundary(),
    )


def _drift_review_card(cycle: ForegroundCycle) -> InteractionCard:
    return InteractionCard(
        contract=CARD_CONTRACT,
        schema_version=CARD_SCHEMA_VERSION,
        kind="drift",
        status="review_required",
        title="Periodic drift review due",
        summary=(
            "Review requirement, architecture, and functionality alignment using bounded "
            "repository evidence. The reminder is non-blocking and does not decide drift."
        ),
        facts=(
            {"label": "dimensions", "value": "requirement, architecture, functionality"},
            {"label": "semantics", "value": "advisory; due status is deterministic"},
            {"label": "native_form_tool", "value": "agentgov_drift_review_record"},
            {"label": "dashboard", "value": cycle.dashboard_ref},
        ),
        actions=("run_advisory_review", "snooze_configured_interval"),
        authority_boundary=_authority_boundary(),
    )


def build_interaction_card(
    repository: Path,
    *,
    event: CodingAgentEvent,
    cycle: ForegroundCycle,
) -> InteractionCard | None:
    """Build only the bounded card implied by this lifecycle event."""

    if event.event_type in {"task.requested", "repository.activated"}:
        return _task_card(repository, cycle)
    if event.event_type in {"implementation.changed", "scope.decision_requested"} and (
        cycle.status in {"blocked", "needs_human"}
    ):
        return _scope_card(cycle)
    if event.event_type == "completion.requested":
        if any(
            finding["code"] == "completion_blocked_by_scope"
            for finding in cycle.findings
        ):
            return _scope_card(cycle)
        return _completion_card(cycle)
    if (
        cycle.human_gate is None
        and cycle.status in {"observed", "advanced", "handed_off"}
        and any(finding["code"] == "drift_review_due" for finding in cycle.findings)
    ):
        return _drift_review_card(cycle)
    return None


def run_coding_agent_event(
    repository: Path,
    *,
    event: CodingAgentEvent,
    sequence: int,
    dashboard_output: Path,
    host_capabilities: HostInteractionCapabilities = REFERENCE_HOST_CAPABILITIES,
) -> CodingAgentResponse:
    """Bind one host event to trusted local facts and run one foreground cycle."""

    if sequence < 1:
        raise CodingAgentTransportError("sequence must be positive")
    trigger = build_reference_trigger(
        repository,
        trigger_type=event.event_type,
        actor_class=event.source["actor_class"],
        adapter_id=event.source["adapter_id"],
        correlation_id=event.correlation_id,
        validation_outcome=event.facts["validation_outcome"],
        evidence_ref=event.facts["evidence_ref"],
        scope_decision=event.facts["scope_decision"],
        review_outcome=event.facts["review_outcome"],
    )
    cycle = run_foreground_cycle(
        repository,
        trigger=trigger,
        dashboard_output=dashboard_output,
    )
    card = build_interaction_card(repository, event=event, cycle=cycle)
    interaction = build_host_interaction_request(
        event_id=event.event_id,
        card=card,
        capabilities=host_capabilities,
    )
    return CodingAgentResponse(
        contract=RESPONSE_CONTRACT,
        schema_version=RESPONSE_SCHEMA_VERSION,
        sequence=sequence,
        event={
            "event_id": event.event_id,
            "event_type": event.event_type,
            "adapter_id": event.source["adapter_id"],
            "actor_class": event.source["actor_class"],
            "correlation_id": event.correlation_id,
        },
        status="processed",
        cycle=cycle,
        card=card,
        interaction=interaction,
        decision_prompt=(
            build_host_decision_prompt(interaction)
            if interaction is not None
            else None
        ),
    )


def render_coding_agent_response_json(response: CodingAgentResponse) -> str:
    """Render one compact JSON object suitable for JSONL framing."""

    return json.dumps(asdict(response), ensure_ascii=False, sort_keys=True) + "\n"


def render_coding_agent_response_terminal(response: CodingAgentResponse) -> str:
    lines = [
        f"AGENTGOV LIVE {response.sequence} {response.cycle.status}",
        f"EVENT {response.event['event_type']} ({response.event['event_id']})",
        f"DASHBOARD {response.cycle.dashboard_ref}",
    ]
    if response.card is not None:
        card = response.card
        lines.extend(
            (
                f"CARD {card.kind.upper()} {card.status}",
                f"TITLE {card.title}",
                f"SUMMARY {card.summary}",
            )
        )
        for fact in card.facts:
            lines.append(f"{fact['label'].upper()} {fact['value']}")
        lines.append("ACTIONS " + ", ".join(card.actions))
    else:
        lines.append("CARD none")
    if response.interaction is not None:
        interaction = response.interaction
        lines.extend(
            (
                f"INTERACTION {interaction.kind} {interaction.status} ({interaction.request_id})",
                (
                    "DELIVERY "
                    f"{interaction.binding['delivery_mode']} "
                    f"recording={interaction.binding['decision_recording']} "
                    f"reason={interaction.binding['reason_code']}"
                ),
            )
        )
    else:
        lines.append("INTERACTION none")
    if response.decision_prompt is not None:
        prompt = response.decision_prompt
        lines.append(
            f"DECISION_PROMPT {prompt.kind} single_select recommended={prompt.recommended_option_id}"
        )
        for option in prompt.options:
            lines.append(f"OPTION {option['index']} {option['id']}: {option['label']}")
    else:
        lines.append("DECISION_PROMPT none")
    lines.append(
        "AUTHORITY scope_expansion=false exception=false commit=false merge=false deployment=false"
    )
    return "\n".join(lines) + "\n"
