"""Deterministic mapping from repository state to one smallest next action."""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from agentgov.adoption import AdoptionState, inspect_adoption
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

    return select_report_next_action(root, check_repository(root))


def render_next_action_json(
    action: NextAction,
    *,
    non_interactive: bool,
) -> str:
    payload = {
        "contract_version": NEXT_ACTION_VERSION,
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
