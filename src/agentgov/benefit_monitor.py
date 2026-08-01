"""Portable continuous benefit evidence without causal or ROI claims."""

from __future__ import annotations

import hashlib
import html
import json
import re
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Mapping

from agentgov import __version__
from agentgov.benefits import (
    BenefitComparison,
    compare_repository_reports,
    load_repository_report_snapshot,
)
from agentgov.redaction import redact_evidence_text


BENEFIT_MONITOR_CONTRACT_VERSION = "1.0"
UPGRADE_OBSERVATION_CONTRACT_VERSION = "1.0"
MAX_HISTORY_POINTS = 20
_REPOSITORY_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
_COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
_EVENT_RE = re.compile(r"^[a-z][a-z0-9_]*$")


class BenefitMonitorState(str, Enum):
    BASELINE_MISSING = "baseline_missing"
    UNCHANGED = "unchanged"
    IMPROVEMENT_OBSERVED = "improvement_observed"
    REGRESSION_OBSERVED = "regression_observed"
    MIXED_CHANGE = "mixed_change"
    CHANGE_OBSERVED = "change_observed"


class BenefitUserState(str, Enum):
    MISSING = "missing"
    UNCHANGED = "unchanged"
    IMPROVED = "improved"
    NEEDS_REVIEW = "needs_review"


@dataclass(frozen=True)
class SnapshotIdentity:
    repository: str
    ref: str
    commit_sha: str
    run_id: int
    run_attempt: int
    event: str
    observed_at: str
    report_sha256: str
    tool_version: str
    summary: Mapping[str, int]


@dataclass(frozen=True)
class BenefitMonitor:
    state: BenefitMonitorState
    snapshot: SnapshotIdentity
    baseline: SnapshotIdentity | None
    comparison: BenefitComparison | None
    history: tuple[Mapping[str, Any], ...]


@dataclass(frozen=True)
class UpgradeObservation:
    repository: str
    commit_sha: str
    run_id: int
    state: str
    branch: str | None
    pull_request_url: str | None
    draft_pr_created_this_run: bool
    detection_to_draft_pr_seconds: int | None
    mechanical_bridge_actions_observed: int | None
    human_merge_decision_required: bool


class BenefitMonitorConflictError(Exception):
    """Raised when generated monitor output would overwrite existing evidence."""


def _validate_positive_int(value: int, *, field: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"{field} must be a positive integer")


def _validate_observed_at(value: str) -> None:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("observed_at must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise ValueError("observed_at must include a timezone")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def benefit_user_state(state: BenefitMonitorState) -> BenefitUserState:
    """Map diagnostic evidence states to four action-oriented UI states."""

    if state is BenefitMonitorState.BASELINE_MISSING:
        return BenefitUserState.MISSING
    if state is BenefitMonitorState.UNCHANGED:
        return BenefitUserState.UNCHANGED
    if state is BenefitMonitorState.IMPROVEMENT_OBSERVED:
        return BenefitUserState.IMPROVED
    return BenefitUserState.NEEDS_REVIEW


def _snapshot_document(snapshot: SnapshotIdentity) -> dict[str, Any]:
    return {
        "repository": snapshot.repository,
        "ref": snapshot.ref,
        "commit_sha": snapshot.commit_sha,
        "run_id": snapshot.run_id,
        "run_attempt": snapshot.run_attempt,
        "event": snapshot.event,
        "observed_at": snapshot.observed_at,
        "report_sha256": snapshot.report_sha256,
        "tool_version": snapshot.tool_version,
        "summary": dict(snapshot.summary),
    }


def _snapshot_from_document(value: Any, *, field: str) -> SnapshotIdentity:
    if not isinstance(value, Mapping):
        raise ValueError(f"{field} must be an object")
    expected = {
        "repository",
        "ref",
        "commit_sha",
        "run_id",
        "run_attempt",
        "event",
        "observed_at",
        "report_sha256",
        "tool_version",
        "summary",
    }
    if set(value) != expected:
        raise ValueError(f"{field} must use the exact snapshot fields")
    summary = value["summary"]
    if not isinstance(summary, Mapping) or set(summary) != {
        "pass",
        "warn",
        "fail",
        "advisory",
    }:
        raise ValueError(f"{field}.summary is invalid")
    for key, count in summary.items():
        if isinstance(count, bool) or not isinstance(count, int) or count < 0:
            raise ValueError(f"{field}.summary.{key} must be non-negative")
    repository = value["repository"]
    commit_sha = value["commit_sha"]
    run_id = value["run_id"]
    run_attempt = value["run_attempt"]
    event = value["event"]
    observed_at = value["observed_at"]
    report_sha256 = value["report_sha256"]
    if not isinstance(repository, str) or not _REPOSITORY_RE.fullmatch(repository):
        raise ValueError(f"{field}.repository must use owner/name form")
    if not isinstance(commit_sha, str) or not _COMMIT_RE.fullmatch(commit_sha):
        raise ValueError(f"{field}.commit_sha must be 40 lowercase hex characters")
    _validate_positive_int(run_id, field=f"{field}.run_id")
    _validate_positive_int(run_attempt, field=f"{field}.run_attempt")
    if not isinstance(event, str) or not _EVENT_RE.fullmatch(event):
        raise ValueError(f"{field}.event is invalid")
    if not isinstance(observed_at, str):
        raise ValueError(f"{field}.observed_at must be a string")
    _validate_observed_at(observed_at)
    if (
        not isinstance(report_sha256, str)
        or not re.fullmatch(r"[0-9a-f]{64}", report_sha256)
    ):
        raise ValueError(f"{field}.report_sha256 must be SHA-256")
    if not isinstance(value["ref"], str) or not value["ref"]:
        raise ValueError(f"{field}.ref must be non-empty")
    if not isinstance(value["tool_version"], str) or not value["tool_version"]:
        raise ValueError(f"{field}.tool_version must be non-empty")
    return SnapshotIdentity(
        repository=repository,
        ref=str(value["ref"]),
        commit_sha=commit_sha,
        run_id=run_id,
        run_attempt=run_attempt,
        event=event,
        observed_at=observed_at,
        report_sha256=report_sha256,
        tool_version=str(value["tool_version"]),
        summary={str(key): int(count) for key, count in summary.items()},
    )


def _history_point(snapshot: SnapshotIdentity, state: str) -> dict[str, Any]:
    return {
        "run_id": snapshot.run_id,
        "observed_at": snapshot.observed_at,
        "commit_sha": snapshot.commit_sha,
        "state": state,
        "summary": dict(snapshot.summary),
    }


def _validated_history_point(value: Any, *, index: int) -> dict[str, Any]:
    field = f"baseline monitor history[{index}]"
    if not isinstance(value, Mapping) or set(value) != {
        "run_id",
        "observed_at",
        "commit_sha",
        "state",
        "summary",
    }:
        raise ValueError(f"{field} must use the exact history fields")
    run_id = value["run_id"]
    observed_at = value["observed_at"]
    commit_sha = value["commit_sha"]
    state = value["state"]
    summary = value["summary"]
    _validate_positive_int(run_id, field=f"{field}.run_id")
    if not isinstance(observed_at, str):
        raise ValueError(f"{field}.observed_at must be a string")
    _validate_observed_at(observed_at)
    if not isinstance(commit_sha, str) or not _COMMIT_RE.fullmatch(commit_sha):
        raise ValueError(f"{field}.commit_sha is invalid")
    if state not in {item.value for item in BenefitMonitorState}:
        raise ValueError(f"{field}.state is invalid")
    if not isinstance(summary, Mapping) or set(summary) != {
        "pass",
        "warn",
        "fail",
        "advisory",
    }:
        raise ValueError(f"{field}.summary is invalid")
    clean_summary: dict[str, int] = {}
    for key, count in summary.items():
        if isinstance(count, bool) or not isinstance(count, int) or count < 0:
            raise ValueError(f"{field}.summary.{key} must be non-negative")
        clean_summary[str(key)] = count
    return {
        "run_id": run_id,
        "observed_at": observed_at,
        "commit_sha": commit_sha,
        "state": state,
        "summary": clean_summary,
    }


def _load_baseline_monitor(
    path: Path,
    *,
    report: Path,
    repository: str,
) -> tuple[SnapshotIdentity, tuple[Mapping[str, Any], ...]]:
    if path.is_symlink() or not path.is_file():
        raise FileNotFoundError(path)
    document = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(document, Mapping):
        raise ValueError("baseline monitor root must be an object")
    if set(document) != {
        "contract_version",
        "tool",
        "mode",
        "state",
        "user_state",
        "snapshot",
        "baseline",
        "comparison",
        "history",
        "scope_limitations",
        "authority_boundary",
    }:
        raise ValueError("baseline monitor must use the exact contract fields")
    if document.get("contract_version") != BENEFIT_MONITOR_CONTRACT_VERSION:
        raise ValueError("baseline monitor contract_version is unsupported")
    if document.get("mode") != "observational_read_only":
        raise ValueError("baseline monitor mode is unsupported")
    tool = document.get("tool")
    if (
        not isinstance(tool, Mapping)
        or set(tool) != {"name", "version"}
        or tool.get("name") != "agentgov"
        or not isinstance(tool.get("version"), str)
    ):
        raise ValueError("baseline monitor tool identity is invalid")
    if document.get("state") not in {item.value for item in BenefitMonitorState}:
        raise ValueError("baseline monitor state is invalid")
    diagnostic_state = BenefitMonitorState(str(document["state"]))
    if document.get("user_state") != benefit_user_state(diagnostic_state).value:
        raise ValueError("baseline monitor user_state is inconsistent")
    limitations = document.get("scope_limitations")
    if (
        not isinstance(limitations, list)
        or not limitations
        or any(not isinstance(item, str) or not item for item in limitations)
    ):
        raise ValueError("baseline monitor scope limitations are invalid")
    authority = document.get("authority_boundary")
    if authority != {
        "governed_repository_modified": False,
        "git_or_pull_request_action_run": False,
        "merge_release_or_deploy_authorized": False,
    }:
        raise ValueError("baseline monitor authority boundary is invalid")
    snapshot = _snapshot_from_document(document.get("snapshot"), field="baseline snapshot")
    if snapshot.repository != repository:
        raise ValueError("baseline monitor identifies a different repository")
    if snapshot.report_sha256 != _sha256(report):
        raise ValueError("baseline report digest does not match its monitor identity")
    history = document.get("history")
    if (
        not isinstance(history, list)
        or not history
        or len(history) > MAX_HISTORY_POINTS
    ):
        raise ValueError("baseline monitor history must contain 1 to 20 points")
    validated_history = tuple(
        _validated_history_point(point, index=index)
        for index, point in enumerate(history)
    )
    last = validated_history[-1]
    if (
        last["run_id"] != snapshot.run_id
        or last["commit_sha"] != snapshot.commit_sha
        or last["summary"] != dict(snapshot.summary)
    ):
        raise ValueError("baseline monitor history does not end at its snapshot")
    return snapshot, validated_history


def _classify(comparison: BenefitComparison) -> BenefitMonitorState:
    resolved = bool(comparison.non_passing_findings_cleared)
    introduced = bool(comparison.deterministic_failures_introduced)
    if resolved and introduced:
        return BenefitMonitorState.MIXED_CHANGE
    if introduced:
        return BenefitMonitorState.REGRESSION_OBSERVED
    if resolved:
        return BenefitMonitorState.IMPROVEMENT_OBSERVED
    if comparison.transitions or comparison.added_checks or comparison.removed_checks:
        return BenefitMonitorState.CHANGE_OBSERVED
    return BenefitMonitorState.UNCHANGED


def build_benefit_monitor(
    current_report: Path,
    *,
    repository: str,
    ref: str,
    commit_sha: str,
    run_id: int,
    run_attempt: int,
    event: str,
    observed_at: str,
    baseline_report: Path | None = None,
    baseline_monitor: Path | None = None,
) -> BenefitMonitor:
    if not _REPOSITORY_RE.fullmatch(repository):
        raise ValueError("repository must use owner/name form")
    if not ref:
        raise ValueError("ref must be non-empty")
    if not _COMMIT_RE.fullmatch(commit_sha):
        raise ValueError("commit_sha must be 40 lowercase hex characters")
    _validate_positive_int(run_id, field="run_id")
    _validate_positive_int(run_attempt, field="run_attempt")
    if not _EVENT_RE.fullmatch(event):
        raise ValueError("event is invalid")
    _validate_observed_at(observed_at)
    if (baseline_report is None) != (baseline_monitor is None):
        raise ValueError("baseline report and monitor must be supplied together")

    current = load_repository_report_snapshot(current_report)
    snapshot = SnapshotIdentity(
        repository=repository,
        ref=ref,
        commit_sha=commit_sha,
        run_id=run_id,
        run_attempt=run_attempt,
        event=event,
        observed_at=observed_at,
        report_sha256=_sha256(current_report),
        tool_version=current.tool_version,
        summary=current.summary,
    )
    if baseline_report is None or baseline_monitor is None:
        state = BenefitMonitorState.BASELINE_MISSING
        baseline = None
        comparison = None
        prior_history: tuple[Mapping[str, Any], ...] = ()
    else:
        baseline, prior_history = _load_baseline_monitor(
            baseline_monitor,
            report=baseline_report,
            repository=repository,
        )
        comparison = compare_repository_reports(baseline_report, current_report)
        state = _classify(comparison)
    history = (*prior_history, _history_point(snapshot, state.value))[-MAX_HISTORY_POINTS:]
    return BenefitMonitor(
        state=state,
        snapshot=snapshot,
        baseline=baseline,
        comparison=comparison,
        history=tuple(history),
    )


def _comparison_evidence(comparison: BenefitComparison | None) -> dict[str, Any] | None:
    if comparison is None:
        return None
    return {
        "denominators": {
            "before_finding_count": comparison.before_finding_count,
            "after_finding_count": comparison.after_finding_count,
            "matched_check_count": comparison.matched_check_count,
        },
        "deterministic_failures_resolved": [
            redact_evidence_text(item)
            for item in comparison.deterministic_failures_resolved
        ],
        "deterministic_failures_introduced": [
            redact_evidence_text(item)
            for item in comparison.deterministic_failures_introduced
        ],
        "non_passing_findings_cleared": [
            redact_evidence_text(item)
            for item in comparison.non_passing_findings_cleared
        ],
        "added_checks": [redact_evidence_text(item) for item in comparison.added_checks],
        "removed_checks": [redact_evidence_text(item) for item in comparison.removed_checks],
        "transitions": [
            {
                "check_id": redact_evidence_text(item.check_id),
                "before": item.before,
                "after": item.after,
            }
            for item in comparison.transitions
        ],
    }


def benefit_monitor_document(monitor: BenefitMonitor) -> dict[str, Any]:
    return {
        "contract_version": BENEFIT_MONITOR_CONTRACT_VERSION,
        "tool": {"name": "agentgov", "version": __version__},
        "mode": "observational_read_only",
        "state": monitor.state.value,
        "user_state": benefit_user_state(monitor.state).value,
        "snapshot": _snapshot_document(monitor.snapshot),
        "baseline": (
            {"available": False, "snapshot": None, "reason": "no prior trusted main baseline"}
            if monitor.baseline is None
            else {
                "available": True,
                "snapshot": _snapshot_document(monitor.baseline),
                "reason": "previous trusted default-branch AgentGov artifact",
            }
        ),
        "comparison": _comparison_evidence(monitor.comparison),
        "history": list(monitor.history),
        "scope_limitations": [
            "Observed report transitions do not prove that AgentGov caused the change.",
            "No prevented incident, labor saving, false-positive rate, coverage percentage, or ROI is inferred.",
            "Project tests, merge outcomes, runtime behavior, and production incidents are not observed here.",
            "A missing or expired baseline produces no trend claim.",
        ],
        "authority_boundary": {
            "governed_repository_modified": False,
            "git_or_pull_request_action_run": False,
            "merge_release_or_deploy_authorized": False,
        },
    }


def render_benefit_monitor_json(monitor: BenefitMonitor) -> str:
    return json.dumps(benefit_monitor_document(monitor), indent=2, ensure_ascii=False) + "\n"


def render_github_annotations(report: Path) -> str:
    """Render non-passing findings as escaped, non-secret GitHub annotations."""

    load_repository_report_snapshot(report)
    document = json.loads(report.read_text(encoding="utf-8"))
    commands: list[str] = []
    for finding in document["findings"]:
        status = finding["status"]
        if status == "PASS":
            continue
        level = "error" if status == "FAIL" else "warning"
        title = f"AgentGov {status}"
        message = redact_evidence_text(
            f"{finding['check_id']}: {finding['message']}"
        )
        escaped = (
            message.replace("%", "%25")
            .replace("\r", "%0D")
            .replace("\n", "%0A")
        )
        commands.append(f"::{level} title={title}::{escaped}")
    return "\n".join(commands) + ("\n" if commands else "")


def render_benefit_monitor_markdown(monitor: BenefitMonitor) -> str:
    current = monitor.snapshot
    evidence = _comparison_evidence(monitor.comparison)
    lines = [
        "# AgentGov Benefit Monitor",
        "",
        f"**Observed state:** `{monitor.state.value}`",
        f"**Action state:** `{benefit_user_state(monitor.state).value}`",
        "",
        f"Repository: `{current.repository}`  ",
        f"Commit: `{current.commit_sha[:12]}`  ",
        f"Run: `{current.run_id}` attempt `{current.run_attempt}`",
        "",
        "## Current governance findings",
        "",
        "| PASS | WARN | FAIL | ADVISORY |",
        "|---:|---:|---:|---:|",
        (
            f"| {current.summary['pass']} | {current.summary['warn']} | "
            f"{current.summary['fail']} | {current.summary['advisory']} |"
        ),
        "",
    ]
    if evidence is None:
        lines.extend(
            [
                "## Comparison",
                "",
                "No trusted prior `main` baseline is available yet. This run establishes",
                "a snapshot but makes no trend or benefit claim.",
                "",
            ]
        )
    else:
        denominators = evidence["denominators"]
        lines.extend(
            [
                "## Change from previous trusted main baseline",
                "",
                (
                    f"Matched `{denominators['matched_check_count']}` checks from "
                    f"`{denominators['before_finding_count']}` before and "
                    f"`{denominators['after_finding_count']}` after."
                ),
                "",
                f"- Deterministic failures resolved: `{len(evidence['deterministic_failures_resolved'])}`",
                f"- Deterministic failures introduced: `{len(evidence['deterministic_failures_introduced'])}`",
                f"- Non-passing findings cleared: `{len(evidence['non_passing_findings_cleared'])}`",
                f"- Added checks: `{len(evidence['added_checks'])}`",
                f"- Removed checks: `{len(evidence['removed_checks'])}`",
                "",
            ]
        )
        transitions = evidence["transitions"]
        if transitions:
            lines.extend(["| Check | Before | After |", "|---|---|---|"])
            lines.extend(
                f"| `{item['check_id']}` | {item['before']} | {item['after']} |"
                for item in transitions
            )
            lines.append("")
    lines.extend(
        [
            "## Recent observed trend",
            "",
            "| Run | Commit | PASS | WARN | FAIL | ADVISORY | State |",
            "|---:|---|---:|---:|---:|---:|---|",
        ]
    )
    for point in monitor.history:
        summary = point["summary"]
        lines.append(
            f"| {point['run_id']} | `{point['commit_sha'][:12]}` | "
            f"{summary['pass']} | {summary['warn']} | {summary['fail']} | "
            f"{summary['advisory']} | `{point['state']}` |"
        )
    lines.extend(
        [
            "",
            "## Evidence limits",
            "",
            "- These are observed governance-report transitions, not proof of causality.",
            "- No prevented incident, time saving, coverage percentage, or ROI is inferred.",
            "- Project tests and production outcomes are outside this monitor.",
            "",
        ]
    )
    return "\n".join(lines)


def render_pull_request_review_markdown(monitor: BenefitMonitor) -> str:
    """Render only PR-local delta and actions; omit trend and upgrade administration."""

    current = monitor.snapshot
    evidence = _comparison_evidence(monitor.comparison)
    blocking = current.summary["fail"]
    action = "changes requested" if blocking else "non-blocking review"
    lines = [
        "# AgentGov Pull Request Review",
        "",
        f"**Merge signal:** `{action}`",
        "",
        "This surface contains only the current PR governance delta and required action.",
        "Repository trend and administrative history are shown only",
        "on trusted default-branch runs.",
        "",
        "## Current action",
        "",
        f"- Blocking deterministic failures: `{blocking}`",
        f"- Non-blocking warnings: `{current.summary['warn']}`",
        f"- Human-judgment advisories: `{current.summary['advisory']}`",
    ]
    if evidence is None:
        lines.extend(
            [
                "- Delta: unavailable because no trusted default-branch baseline was restored.",
                "",
                "Review the current findings; no improvement or regression claim is made.",
            ]
        )
    else:
        resolved_failures = sum(
            1
            for item in evidence["transitions"]
            if item["before"] == "FAIL" and item["after"] != "FAIL"
        )
        baseline_failures = monitor.baseline.summary["fail"] if monitor.baseline else 0
        introduced_failures = max(
            0,
            current.summary["fail"] - baseline_failures + resolved_failures,
        )
        lines.extend(
            [
                f"- New deterministic failures: `{introduced_failures}`",
                f"- Cleared non-passing findings: `{len(evidence['non_passing_findings_cleared'])}`",
                "",
            ]
        )
        transitions = evidence["transitions"]
        if transitions:
            lines.extend(["| Changed check | Before | After |", "|---|---|---|"])
            lines.extend(
                f"| `{item['check_id']}` | {item['before']} | {item['after']} |"
                for item in transitions
            )
        else:
            lines.append("No matched governance check changed state in this PR.")
    lines.extend(
        [
            "",
            "FAIL is blocking. WARN and ADVISORY are visible but non-blocking and require",
            "the author or designated reviewer to decide whether follow-up evidence is needed.",
            "",
        ]
    )
    return "\n".join(lines)


def render_benefit_monitor_html(monitor: BenefitMonitor) -> str:
    markdown = render_benefit_monitor_markdown(monitor)
    rows = "".join(
        "<tr>"
        f"<td>{point['run_id']}</td>"
        f"<td><code>{html.escape(point['commit_sha'][:12])}</code></td>"
        f"<td>{point['summary']['pass']}</td>"
        f"<td>{point['summary']['warn']}</td>"
        f"<td>{point['summary']['fail']}</td>"
        f"<td>{point['summary']['advisory']}</td>"
        f"<td><code>{html.escape(point['state'])}</code></td>"
        "</tr>"
        for point in monitor.history
    )
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>AgentGov Benefit Monitor</title>
<style>body{{font:16px system-ui;max-width:1000px;margin:2rem auto;padding:0 1rem;color:#172033}}.card{{border:1px solid #ccd5e0;border-radius:12px;padding:1rem;margin:1rem 0}}table{{border-collapse:collapse;width:100%}}th,td{{border:1px solid #ccd5e0;padding:.55rem;text-align:left}}code{{background:#eef2f7;padding:.1rem .3rem;border-radius:4px}}.limit{{color:#5b6472}}</style></head>
<body><h1>AgentGov Benefit Monitor</h1><div class="card"><strong>Observed state:</strong> <code>{html.escape(monitor.state.value)}</code><br><strong>Action state:</strong> <code>{html.escape(benefit_user_state(monitor.state).value)}</code><br>Repository: <code>{html.escape(monitor.snapshot.repository)}</code><br>Commit: <code>{monitor.snapshot.commit_sha[:12]}</code></div>
<h2>Recent observed trend</h2><table><thead><tr><th>Run</th><th>Commit</th><th>PASS</th><th>WARN</th><th>FAIL</th><th>ADVISORY</th><th>State</th></tr></thead><tbody>{rows}</tbody></table>
<div class="card limit"><strong>Evidence limits:</strong> observed report transitions do not prove causality, prevented incidents, time savings, coverage, or ROI. Project tests and production outcomes are not observed.</div>
<details><summary>Portable Markdown source</summary><pre>{html.escape(markdown)}</pre></details></body></html>
"""


def write_benefit_monitor_bundle(output: Path, monitor: BenefitMonitor) -> Path:
    if output.is_symlink() or output.exists():
        raise BenefitMonitorConflictError(f"output already exists: {output}")
    if output.parent.is_symlink() or not output.parent.is_dir():
        raise BenefitMonitorConflictError("output parent must be a safe existing directory")
    output.mkdir()
    (output / "benefit-monitor.json").write_text(
        render_benefit_monitor_json(monitor), encoding="utf-8", newline="\n"
    )
    (output / "BENEFIT_MONITOR.md").write_text(
        render_benefit_monitor_markdown(monitor), encoding="utf-8", newline="\n"
    )
    (output / "PR_REVIEW.md").write_text(
        render_pull_request_review_markdown(monitor), encoding="utf-8", newline="\n"
    )
    (output / "benefit-monitor.html").write_text(
        render_benefit_monitor_html(monitor), encoding="utf-8", newline="\n"
    )
    return output


def build_upgrade_observation(
    result_path: Path,
    *,
    repository: str,
    commit_sha: str,
    run_id: int,
    started_epoch: int,
    completed_epoch: int,
) -> UpgradeObservation:
    if not _REPOSITORY_RE.fullmatch(repository):
        raise ValueError("repository must use owner/name form")
    if not _COMMIT_RE.fullmatch(commit_sha):
        raise ValueError("commit_sha must be 40 lowercase hex characters")
    _validate_positive_int(run_id, field="run_id")
    if started_epoch < 0 or completed_epoch < started_epoch:
        raise ValueError("upgrade observation epochs are invalid")
    document = json.loads(result_path.read_text(encoding="utf-8"))
    if not isinstance(document, Mapping):
        raise ValueError("upgrade result root must be an object")
    if document.get("contract_version") != "1.0" or document.get("mode") != "github_draft_pull_request":
        raise ValueError("upgrade result contract is unsupported")
    if document.get("repository") != repository:
        raise ValueError("upgrade result identifies a different repository")
    state = document.get("state")
    if state not in {"current", "created", "recovered", "existing"}:
        raise ValueError("upgrade result state is unsupported")
    actions = document.get("actions")
    if not isinstance(actions, Mapping):
        raise ValueError("upgrade result actions are missing")
    created = actions.get("draft_pull_request_created") is True
    pr = document.get("pull_request")
    pr_url = str(pr["url"]) if isinstance(pr, Mapping) and isinstance(pr.get("url"), str) else None
    branch = document.get("branch")
    if branch is not None and not isinstance(branch, str):
        raise ValueError("upgrade result branch is invalid")
    automated = created and state in {"created", "recovered"}
    return UpgradeObservation(
        repository=repository,
        commit_sha=commit_sha,
        run_id=run_id,
        state=str(state),
        branch=branch,
        pull_request_url=pr_url,
        draft_pr_created_this_run=created,
        detection_to_draft_pr_seconds=(completed_epoch - started_epoch if automated else None),
        mechanical_bridge_actions_observed=(0 if automated else None),
        human_merge_decision_required=pr_url is not None,
    )


def upgrade_observation_document(observation: UpgradeObservation) -> dict[str, Any]:
    return {
        "contract_version": UPGRADE_OBSERVATION_CONTRACT_VERSION,
        "tool": {"name": "agentgov", "version": __version__},
        "mode": "observational_read_only",
        "repository": observation.repository,
        "commit_sha": observation.commit_sha,
        "run_id": observation.run_id,
        "upgrade_state": observation.state,
        "branch": observation.branch,
        "pull_request_url": observation.pull_request_url,
        "metrics": {
            "draft_pr_created_this_run": observation.draft_pr_created_this_run,
            "detection_to_draft_pr_seconds": observation.detection_to_draft_pr_seconds,
            "mechanical_bridge_actions_observed": observation.mechanical_bridge_actions_observed,
            "human_merge_decision_required": observation.human_merge_decision_required,
        },
        "metric_definitions": {
            "detection_to_draft_pr_seconds": "Elapsed workflow seconds from starting the validated upgrade check to receiving a Draft PR result.",
            "mechanical_bridge_actions_observed": "Human release-copy actions requested by this automated proposal path during this run; zero is not a claim about actions avoided.",
        },
        "scope_limitations": [
            "Elapsed workflow time is not human labor saved.",
            "Zero observed bridge actions does not estimate counterfactual actions avoided.",
            "This observation does not prove causality, prevented incidents, or ROI.",
            "A human merge decision remains required.",
        ],
        "authority_boundary": {
            "merge_authorized": False,
            "release_or_deploy_authorized": False,
        },
    }


def render_upgrade_observation_json(observation: UpgradeObservation) -> str:
    return json.dumps(upgrade_observation_document(observation), indent=2, ensure_ascii=False) + "\n"


def render_upgrade_observation_markdown(observation: UpgradeObservation) -> str:
    duration = (
        "not observed"
        if observation.detection_to_draft_pr_seconds is None
        else f"{observation.detection_to_draft_pr_seconds} seconds"
    )
    bridge = (
        "not observed"
        if observation.mechanical_bridge_actions_observed is None
        else str(observation.mechanical_bridge_actions_observed)
    )
    return "\n".join(
        [
            "# AgentGov Upgrade Automation Observation",
            "",
            f"- Upgrade state: `{observation.state}`",
            f"- Draft PR created this run: `{str(observation.draft_pr_created_this_run).lower()}`",
            f"- Detection-to-Draft-PR workflow time: `{duration}`",
            f"- Mechanical bridge actions requested in this run: `{bridge}`",
            f"- Human merge decision required: `{str(observation.human_merge_decision_required).lower()}`",
            "",
            "These are workflow observations, not proof of labor saved, avoided incidents, causality, or ROI.",
            "",
        ]
    )


def write_upgrade_observation_bundle(output: Path, observation: UpgradeObservation) -> Path:
    if output.is_symlink() or output.exists():
        raise BenefitMonitorConflictError(f"output already exists: {output}")
    if output.parent.is_symlink() or not output.parent.is_dir():
        raise BenefitMonitorConflictError("output parent must be a safe existing directory")
    output.mkdir()
    (output / "upgrade-observation.json").write_text(
        render_upgrade_observation_json(observation), encoding="utf-8", newline="\n"
    )
    (output / "UPGRADE_OBSERVATION.md").write_text(
        render_upgrade_observation_markdown(observation), encoding="utf-8", newline="\n"
    )
    return output
