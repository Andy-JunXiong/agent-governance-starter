"""Deterministic mapping from repository state to one smallest next action."""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from agentgov import __version__
from agentgov.adoption import AdoptionState, inspect_adoption
from agentgov.development_session import (
    DevelopmentSession,
    SessionPolicyError,
    discover_admitted_tasks,
    load_active_session,
    resolve_active_task,
)
from agentgov.development_handoff import is_session_handoff_event
from agentgov.event_store import GovernanceEvent, LocalStateError, load_governance_events
from agentgov.git_snapshot import GitSnapshotError
from agentgov.repository import FindingStatus, RepositoryReport, check_repository


class ActionKind(str, Enum):
    DETERMINISTIC_WORK = "deterministic_work"
    INCOMPLETE_EVIDENCE = "incomplete_evidence"
    HUMAN_JUDGMENT = "human_judgment"
    COMPLETE = "complete"


@dataclass(frozen=True)
class NextAction:
    root: Path
    kind: ActionKind
    title: str
    reason: str
    command: str | None
    source_check_id: str | None
    blocking: bool


NEXT_ACTION_VERSION = "1.0"
_SCAFFOLDABLE_AREAS = {
    "governance:constitution",
    "governance:adr-template",
    "governance:invariants",
    "governance:capabilities",
    "governance:evaluation",
    "governance:agent-skills",
}


def _first_finding(
    report: RepositoryReport,
    status: FindingStatus,
):
    return next(
        (finding for finding in report.findings if finding.status is status),
        None,
    )


def select_report_next_action(root: Path, report: RepositoryReport) -> NextAction:
    """Select one action from an already evaluated repository report."""

    resolved = root.resolve()
    failure = _first_finding(report, FindingStatus.FAIL)
    if failure is not None:
        return NextAction(
            resolved,
            ActionKind.DETERMINISTIC_WORK,
            "Resolve the first deterministic repository failure",
            failure.message,
            f'agentgov check repository "{resolved}"',
            failure.check_id,
            True,
        )

    warning = _first_finding(report, FindingStatus.WARN)
    if warning is not None:
        if warning.check_id.startswith("evaluation:evaluation/"):
            relative_bundle = warning.check_id.removeprefix("evaluation:")
            bundle = resolved / Path(relative_bundle)
            return NextAction(
                resolved,
                ActionKind.INCOMPLETE_EVIDENCE,
                "Review the first incomplete evaluation evidence item",
                warning.message,
                f'agentgov check evaluation "{bundle}"',
                warning.check_id,
                False,
            )
        return NextAction(
            resolved,
            ActionKind.INCOMPLETE_EVIDENCE,
            "Review the first incomplete configuration or evidence finding",
            warning.message,
            f'agentgov check repository "{resolved}"',
            warning.check_id,
            False,
        )

    advisory = _first_finding(report, FindingStatus.ADVISORY)
    if advisory is not None:
        return NextAction(
            resolved,
            ActionKind.HUMAN_JUDGMENT,
            "Record the first outstanding human judgment",
            advisory.message,
            None,
            advisory.check_id,
            False,
        )

    return NextAction(
        resolved,
        ActionKind.COMPLETE,
        "No repository governance action is currently identified",
        "the configured deterministic checks have no FAIL or WARN finding",
        None,
        None,
        False,
    )


def _invalid_development_state(
    root: Path,
    *,
    title: str,
    reason: str,
    source_check_id: str,
    command: str | None = None,
) -> NextAction:
    return NextAction(
        root,
        ActionKind.DETERMINISTIC_WORK,
        title,
        reason,
        command,
        source_check_id,
        True,
    )


def _start_action(
    root: Path,
    *,
    replace_active: bool = False,
    excluded_task_digests: tuple[str, ...] = (),
) -> NextAction:
    candidates = discover_admitted_tasks(
        root,
        excluded_task_digests=excluded_task_digests,
    )
    replace_option = " --replace-active" if replace_active else ""
    if len(candidates) == 1:
        command = (
            f'agentgov govern start "{candidates[0]}" '
            f'--repository "{root}"{replace_option} --dry-run'
        )
        reason = (
            "one other admitted task is available after the exact prior digest was handed off"
            if replace_active
            else "one admitted task is available and no task is active in this working copy"
        )
    elif len(candidates) > 1:
        command = (
            f'agentgov govern start "<TASK_JSON>" '
            f'--repository "{root}"{replace_option} --dry-run'
        )
        reason = (
            f"{len(candidates)} admitted tasks are available; choose one explicitly because "
            "AgentGov does not infer human intent"
        )
    else:
        command = (
            f'agentgov govern start --repository "{root}" --title "<TASK_TITLE>" '
            f'--include "<PATH>"{replace_option} --dry-run'
        )
        reason = (
            "no admitted task is active or discoverable; preview a low-risk compact task "
            "with an explicit machine-checkable scope"
        )
    return NextAction(
        root,
        ActionKind.DETERMINISTIC_WORK,
        "Preview the next governed development task rollover" if replace_active else "Preview the next governed development task",
        reason,
        command,
        "development-session:handed-off" if replace_active else "development-session:missing",
        False,
    )


def _session_events(
    root: Path,
    session: DevelopmentSession,
) -> tuple[GovernanceEvent, ...]:
    loaded = load_governance_events(root / ".agentgov" / "events")
    return tuple(
        event
        for event in loaded.events
        if event.task_id == session.task_id
        and event.task_digest == session.task_digest
        and event.occurred_at >= session.started_at
    )


def _active_development_action(root: Path, session: DevelopmentSession) -> NextAction:
    check_command = f'agentgov govern check --repository "{root}"'
    finish_command = f'agentgov govern finish --repository "{root}"'
    monitor_command = f'agentgov monitor development "{root}"'
    try:
        _task_path, verified_session = resolve_active_task(root)
    except (GitSnapshotError, OSError, UnicodeError, ValueError) as exc:
        task = root / session.task_path
        reason = str(exc)
        if isinstance(exc, GitSnapshotError):
            reason = f"active session comparison base is unavailable: {exc}"
        return _invalid_development_state(
            root,
            title="Review active task drift before continuing",
            reason=reason,
            command=(
                f'agentgov govern start "{task}" --repository "{root}" '
                "--replace-active --dry-run"
            ),
            source_check_id="development-session:task-drift",
        )
    try:
        events = _session_events(root, verified_session)
    except (LocalStateError, OSError, UnicodeError, ValueError) as exc:
        return _invalid_development_state(
            root,
            title="Resolve invalid local development events",
            reason=str(exc),
            source_check_id="development-events:invalid",
        )
    start = next(
        (
            event
            for event in events
            if event.event_type == "task.started"
            and event.occurred_at == verified_session.started_at
        ),
        None,
    )
    if start is None:
        return _invalid_development_state(
            root,
            title="Restore the reviewed development-session boundary",
            reason=(
                "the active session has no matching immutable task.started event; "
                "AgentGov will not infer progress from unrelated or older events"
            ),
            source_check_id="development-session:start-event",
        )

    latest = events[-1]
    if latest.event_type == "task.started":
        return NextAction(
            root,
            ActionKind.DETERMINISTIC_WORK,
            "Check the active task scope",
            "the task is active and no current-session scope observation has been recorded",
            check_command,
            "development-session:started",
            False,
        )
    if latest.event_type == "scope.checked":
        if latest.outcome == "passed":
            return NextAction(
                root,
                ActionKind.INCOMPLETE_EVIDENCE,
                "Run fresh validation and reconcile completion",
                "the latest current-session scope check passed but completion is not verified",
                finish_command,
                "development-session:scope-passed",
                False,
            )
        return _invalid_development_state(
            root,
            title="Resolve task-scope failures and check again",
            reason=(
                f"the latest current-session scope outcome is {latest.outcome!r}; "
                "review changed paths or the admitted task before continuing"
            ),
            command=check_command,
            source_check_id="development-session:scope-failed",
        )
    if latest.event_type == "validation.completed":
        return NextAction(
            root,
            ActionKind.INCOMPLETE_EVIDENCE,
            "Reconcile the active task completion",
            (
                f"validation outcome {latest.outcome!r} is recorded without a later "
                "current-session completion reconciliation"
            ),
            finish_command,
            "development-session:validation-recorded",
            False,
        )
    if latest.event_type == "completion.reconciled":
        if latest.outcome == "verified":
            return NextAction(
                root,
                ActionKind.COMPLETE,
                "Review the verified task in the Development Monitor",
                (
                    "the latest current-session completion is verified within its "
                    "declared evidence limits"
                ),
                monitor_command,
                "development-session:verified",
                False,
            )
        return NextAction(
            root,
            ActionKind.INCOMPLETE_EVIDENCE,
            "Refresh evidence and reconcile completion",
            f"the latest current-session completion outcome is {latest.outcome!r}",
            finish_command,
            "development-session:needs-evidence",
            False,
        )
    if latest.event_type == "session.handed_off":
        prior = events[-2] if len(events) >= 2 else None
        if (
            not is_session_handoff_event(latest, verified_session)
            or prior is None
            or prior.event_type != "completion.reconciled"
            or prior.outcome != "verified"
            or prior.evidence_ref != latest.evidence_ref
        ):
            return _invalid_development_state(
                root,
                title="Resolve the invalid verified-session handoff",
                reason="the terminal event is not linked to the exact latest verified completion",
                source_check_id="development-session:invalid-handoff",
            )
        return _start_action(
            root,
            replace_active=True,
            excluded_task_digests=(verified_session.task_digest,),
        )
    return _invalid_development_state(
        root,
        title="Resolve unsupported current-session progress",
        reason=f"the latest current-session event type is {latest.event_type!r}",
        source_check_id="development-events:unsupported-progress",
    )


def select_development_next_action(root: Path) -> NextAction:
    """Select one read-only action from strict working-copy development state."""

    resolved = root.resolve()
    try:
        session = load_active_session(resolved)
    except (SessionPolicyError, OSError, UnicodeError, ValueError) as exc:
        return _invalid_development_state(
            resolved,
            title="Resolve the invalid active development session",
            reason=str(exc),
            source_check_id="development-session:invalid",
        )
    if session is None:
        return _start_action(resolved)
    return _active_development_action(resolved, session)


def select_next_action(root: Path) -> NextAction:
    """Select one action from explicit repository state without writing."""

    inspection = inspect_adoption(root)
    conflict = next(
        (
            item
            for item in inspection.items
            if item.state is AdoptionState.CONFLICT
        ),
        None,
    )
    resolved = root.resolve()
    if conflict is not None:
        return NextAction(
            resolved,
            ActionKind.DETERMINISTIC_WORK,
            "Resolve the first governance path conflict",
            conflict.message,
            f'agentgov doctor "{resolved}"',
            conflict.check_id,
            True,
        )

    missing_scaffold = next(
        (
            item
            for item in inspection.items
            if item.state is AdoptionState.MISSING
            and item.check_id in _SCAFFOLDABLE_AREAS
        ),
        None,
    )
    if missing_scaffold is not None:
        return NextAction(
            resolved,
            ActionKind.DETERMINISTIC_WORK,
            "Preview create-missing-only governance adoption",
            missing_scaffold.message,
            (
                f'agentgov onboard "{resolved}" --project-name '
                '"<PROJECT_NAME>" --dry-run'
            ),
            missing_scaffold.check_id,
            False,
        )

    report = check_repository(root)
    failure = _first_finding(report, FindingStatus.FAIL)
    if failure is not None:
        return select_report_next_action(root, report)
    return select_development_next_action(resolved)


def render_next_action_json(
    action: NextAction,
    *,
    non_interactive: bool,
) -> str:
    payload = {
        "contract_version": NEXT_ACTION_VERSION,
        "tool": {"name": "agentgov", "version": __version__},
        "repository": str(action.root),
        "mode": "read_only",
        "interaction": "non_interactive" if non_interactive else "no_prompt",
        "action": {
            "kind": action.kind.value,
            "title": action.title,
            "reason": action.reason,
            "command": action.command,
            "source_check_id": action.source_check_id,
            "blocking": action.blocking,
        },
        "authority_boundary": {
            "action_executed": False,
            "modifies_repository": False,
            "authorizes_git_or_release_operations": False,
        },
    }
    return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
