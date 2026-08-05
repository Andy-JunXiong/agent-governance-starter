"""Explicit foreground coordinator for automatic development governance."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping

from agentgov.change_scope import ScopeFindingStatus, check_development_scope
from agentgov.development_evidence import reconcile_task_completion, run_task_validation
from agentgov.development_handoff import apply_handoff_plan, build_handoff_plan
from agentgov.development_monitor import build_development_monitor, write_development_monitor
from agentgov.development_session import (
    current_session_events,
    load_active_session,
    resolve_active_task,
)
from agentgov.development_state import development_state_payload, project_development_state
from agentgov.development_trigger import DevelopmentTrigger, working_copy_digest
from agentgov.event_store import append_governance_event


COORDINATOR_CONTRACT = "agentgov.foreground-cycle"
COORDINATOR_SCHEMA_VERSION = "1.0"
DEFAULT_DASHBOARD = Path(".agentgov/dashboard.html")


class CoordinatorPolicyError(RuntimeError):
    """A trigger cannot be safely bound to the selected working copy."""


@dataclass(frozen=True)
class ForegroundCycle:
    contract: str
    schema_version: str
    trigger: Mapping[str, str]
    status: str
    task_ref: Mapping[str, str] | None
    state_before: Mapping[str, Any] | None
    state_after: Mapping[str, Any] | None
    actions: tuple[Mapping[str, Any], ...]
    findings: tuple[Mapping[str, Any], ...]
    human_gate: Mapping[str, Any] | None
    dashboard_ref: str
    authority_boundary: Mapping[str, bool]


def _action(
    name: str,
    outcome: str,
    *,
    event_ref: str | None = None,
    artifact_ref: str | None = None,
) -> Mapping[str, Any]:
    return {
        "name": name,
        "outcome": outcome,
        "event_ref": event_ref,
        "artifact_ref": artifact_ref,
    }


def _finding(
    code: str,
    message: str,
    *,
    blocking: bool,
    semantics: str = "deterministic",
) -> Mapping[str, Any]:
    return {
        "semantics": semantics,
        "code": code,
        "message": message,
        "blocking": blocking,
    }


def _gate(kind: str, reason_code: str, options: tuple[str, ...]) -> Mapping[str, Any]:
    return {
        "kind": kind,
        "reason_code": reason_code,
        "options": list(options),
    }


def _append_scope_observation(
    repository: Path,
    task_path: Path,
    trigger: DevelopmentTrigger,
) -> tuple[Any, str]:
    report = check_development_scope(task_path, repository=repository)
    if trigger.trigger_type == "implementation.changed":
        observed_paths = tuple(
            sorted(
                {
                    path
                    for change in report.changes
                    for path in (change.old_path, change.path)
                    if path is not None
                }
            )
        )
        if observed_paths != tuple(trigger.facts["changed_paths"]):
            raise CoordinatorPolicyError(
                "working-copy paths changed after the adapter trigger; start a fresh cycle"
            )
    _, event_ref = append_governance_event(
        repository,
        event_type="scope.checked",
        actor_class=trigger.source["actor_class"],
        actor_label=trigger.source["adapter_id"],
        task_id=report.task_id,
        task_digest=report.task_digest,
        outcome="failed" if report.has_failures else "passed",
        evidence_ref=None,
        reason_codes=(
            "foreground_coordinator",
            "implementation_changed"
            if trigger.trigger_type == "implementation.changed"
            else "completion_requested",
        ) + (("scope_failure",) if report.has_failures else ()),
        metrics={
            "changes": len(report.changes),
            "failures": report.count(ScopeFindingStatus.FAIL),
            "advisories": report.count(ScopeFindingStatus.ADVISORY),
        },
    )
    return report, event_ref


def _refresh_dashboard(repository: Path, output: Path) -> str:
    monitor = build_development_monitor(repository)
    written = write_development_monitor(
        repository,
        monitor=monitor,
        output=output,
        output_format="html",
    )
    return written.relative_to(repository.resolve()).as_posix()


def run_foreground_cycle(
    repository: Path,
    *,
    trigger: DevelopmentTrigger,
    dashboard_output: Path = DEFAULT_DASHBOARD,
) -> ForegroundCycle:
    """Run one disclosed foreground cycle using only already-approved authority."""

    root = repository.resolve(strict=True)
    if working_copy_digest(root) != trigger.working_copy_digest:
        raise CoordinatorPolicyError("trigger working copy does not match the selected repository")

    actions: list[Mapping[str, Any]] = []
    findings: list[Mapping[str, Any]] = []
    human_gate: Mapping[str, Any] | None = None
    session = load_active_session(root)
    task_ref: Mapping[str, str] | None = None
    state_before: Mapping[str, Any] | None = None
    state_after: Mapping[str, Any] | None = None
    task_path: Path | None = None

    if session is None:
        human_gate = _gate(
            "task_admission",
            "no_active_admitted_task",
            ("review_task_card", "decline"),
        )
        findings.append(
            _finding(
                "task_admission_required",
                "No active admitted task exists; the coordinator will not infer scope from the user prompt.",
                blocking=True,
            )
        )
    else:
        task_path, session = resolve_active_task(root)
        task_ref = {"task_id": session.task_id, "task_digest": session.task_digest}
        if trigger.task_ref is not None and dict(trigger.task_ref) != task_ref:
            raise CoordinatorPolicyError("trigger task identity does not match the active admitted task")
        events_before = current_session_events(root, session)
        state_before = development_state_payload(
            project_development_state(session, events_before)
        )

        if trigger.trigger_type == "implementation.changed":
            report, event_ref = _append_scope_observation(root, task_path, trigger)
            actions.append(
                _action(
                    "check_scope",
                    "blocked" if report.has_failures else "passed",
                    event_ref=event_ref,
                )
            )
            if report.has_failures:
                findings.append(
                    _finding(
                        "scope_boundary_blocked",
                        "Observed working-copy changes exceed or violate the admitted task scope.",
                        blocking=True,
                    )
                )
        elif trigger.trigger_type == "completion.requested":
            report, event_ref = _append_scope_observation(root, task_path, trigger)
            actions.append(
                _action(
                    "check_scope",
                    "blocked" if report.has_failures else "passed",
                    event_ref=event_ref,
                )
            )
            if report.has_failures:
                findings.append(
                    _finding(
                        "completion_blocked_by_scope",
                        "Completion validation was not run because the current change set is outside admitted scope.",
                        blocking=True,
                    )
                )
            else:
                validation = run_task_validation(
                    task_path,
                    repository=root,
                    comparison_base=session.comparison_base_sha,
                    actor_class=trigger.source["actor_class"],
                    actor_label=trigger.source["adapter_id"],
                )
                actions.append(
                    _action(
                        "run_preapproved_validation",
                        validation.evidence.outcome,
                        event_ref=validation.event_ref,
                        artifact_ref=validation.evidence_ref,
                    )
                )
                completion = reconcile_task_completion(
                    task_path,
                    repository=root,
                    evidence_path=Path(validation.evidence_ref),
                    actor_class=trigger.source["actor_class"],
                    actor_label=trigger.source["adapter_id"],
                )
                actions.append(
                    _action(
                        "reconcile_completion",
                        completion.state,
                        event_ref=completion.event_ref,
                        artifact_ref=completion.evidence_ref,
                    )
                )
                if completion.state != "verified":
                    findings.append(
                        _finding(
                            "completion_needs_evidence",
                            "Completion remains unverified within the admitted evidence contract.",
                            blocking=False,
                        )
                    )
        elif trigger.trigger_type == "scope.decision_requested":
            human_gate = _gate(
                "scope_decision",
                "material_scope_decision_requested",
                ("approve_task_revision", "narrow", "decline"),
            )
        elif trigger.trigger_type == "scope.decision_recorded":
            human_gate = _gate(
                "task_readmission",
                "scope_decision_requires_task_contract_revision",
                ("review_revised_task", "stop"),
            )
            findings.append(
                _finding(
                    "scope_decision_not_self_applying",
                    "The recorded decision does not rewrite scope or bypass task admission.",
                    blocking=True,
                )
            )
        elif trigger.trigger_type == "validation.completed":
            findings.append(
                _finding(
                    "adapter_validation_is_context_only",
                    "Adapter-reported validation is not AgentGov completion evidence; request completion to run the admitted validation contract.",
                    blocking=False,
                    semantics="advisory",
                )
            )
        elif trigger.trigger_type == "session.reviewed":
            if trigger.facts["review_outcome"] == "accepted":
                if state_before["stage"] != "review_ready":
                    findings.append(
                        _finding(
                            "review_not_ready",
                            "The session cannot be handed off until fresh completion is verified.",
                            blocking=True,
                        )
                    )
                else:
                    plan = build_handoff_plan(
                        root,
                        actor_label=trigger.source["adapter_id"],
                    )
                    result = apply_handoff_plan(plan)
                    actions.append(
                        _action(
                            "handoff_session",
                            "already_handed_off" if result.already_handed_off else "handed_off",
                            event_ref=result.event_ref,
                            artifact_ref=plan.evidence_ref,
                        )
                    )
            else:
                findings.append(
                    _finding(
                        "review_changes_requested",
                        "The human review requested changes; routing responsibility remains active.",
                        blocking=False,
                        semantics="advisory",
                    )
                )

        events_after = current_session_events(root, session)
        state_after = development_state_payload(
            project_development_state(session, events_after)
        )

    dashboard_ref = _refresh_dashboard(root, dashboard_output)
    actions.append(_action("refresh_dashboard", "refreshed", artifact_ref=dashboard_ref))

    blocking = any(item["blocking"] for item in findings)
    if human_gate is not None:
        status = "needs_human"
    elif blocking:
        status = "blocked"
    elif state_after is not None and state_after["stage"] == "handed_off":
        status = "handed_off"
    elif state_after is not None and state_after["stage"] == "review_ready":
        status = "review_ready"
    elif len(actions) > 1:
        status = "advanced"
    else:
        status = "observed"

    return ForegroundCycle(
        contract=COORDINATOR_CONTRACT,
        schema_version=COORDINATOR_SCHEMA_VERSION,
        trigger={
            "trigger_id": trigger.trigger_id,
            "trigger_type": trigger.trigger_type,
            "adapter_id": trigger.source["adapter_id"],
            "actor_class": trigger.source["actor_class"],
            "correlation_id": trigger.correlation_id,
        },
        status=status,
        task_ref=task_ref,
        state_before=state_before,
        state_after=state_after,
        actions=tuple(actions),
        findings=tuple(findings),
        human_gate=human_gate,
        dashboard_ref=dashboard_ref,
        authority_boundary={
            "uses_only_admitted_validation": True,
            "authorizes_scope_expansion": False,
            "authorizes_exception": False,
            "authorizes_commit": False,
            "authorizes_merge": False,
            "authorizes_deployment": False,
        },
    )


def render_foreground_cycle_json(cycle: ForegroundCycle) -> str:
    return json.dumps(asdict(cycle), ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def render_foreground_cycle_terminal(cycle: ForegroundCycle) -> str:
    lines = [
        f"AGENTGOV DEV {cycle.status}",
        f"TRIGGER {cycle.trigger['trigger_type']} ({cycle.trigger['trigger_id']})",
        f"DASHBOARD {cycle.dashboard_ref}",
    ]
    if cycle.task_ref is not None:
        lines.append(f"TASK {cycle.task_ref['task_id']} ({cycle.task_ref['task_digest']})")
    for action in cycle.actions:
        lines.append(f"ACTION {action['name']} {action['outcome']}")
    for finding in cycle.findings:
        lines.append(
            f"FINDING {finding['semantics']} {finding['code']} blocking={str(finding['blocking']).lower()}"
        )
    if cycle.human_gate is not None:
        lines.append(
            f"HUMAN_GATE {cycle.human_gate['kind']} {cycle.human_gate['reason_code']}"
        )
        lines.append("OPTIONS " + ", ".join(cycle.human_gate["options"]))
    lines.append(
        "AUTHORITY scope_expansion=false exception=false commit=false merge=false deployment=false"
    )
    return "\n".join(lines) + "\n"
