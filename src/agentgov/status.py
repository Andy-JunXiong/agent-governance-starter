"""Read-only visibility into how AgentGov is used by one repository."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from agentgov import __version__
from agentgov.adoption import AdoptionState, inspect_adoption
from agentgov.consumer_ci import (
    UPGRADE_WORKFLOW_PATH,
    WORKFLOW_PATH,
    ConsumerCIState,
    ConsumerCIStatus,
    inspect_consumer_ci,
    inspect_managed_workflow_content,
    inspect_managed_upgrade_workflow_content,
)
from agentgov.next_action import NextAction, select_report_next_action
from agentgov.repository import FindingStatus, RepositoryReport, check_repository
from agentgov.update_check import comparable_version_key, load_repository_layout


STATUS_CONTRACT_VERSION = "1.0"


@dataclass(frozen=True)
class CapabilityUsage:
    name: str
    purpose: str
    owner: str
    risk_level: str
    readiness: str
    called_by: tuple[str, ...]
    manifest: Path


@dataclass(frozen=True)
class StatusSurface:
    name: str
    state: str
    explanation: str


@dataclass(frozen=True)
class GovernanceStatus:
    root: Path
    adopted: bool
    layout_version: str | None
    layout_error: str | None
    ci: ConsumerCIStatus
    capabilities: tuple[CapabilityUsage, ...]
    surfaces: tuple[StatusSurface, ...]
    repository_report: RepositoryReport
    next_action: NextAction

    @property
    def has_failures(self) -> bool:
        return (
            self.repository_report.has_failures
            or self.layout_error is not None
            or self.ci.state is ConsumerCIState.CONFLICT
        )


def _mapping(value: Any) -> Mapping[str, Any] | None:
    return value if isinstance(value, Mapping) else None


def _capability_usages(root: Path) -> tuple[CapabilityUsage, ...]:
    canonical = root / "governance/capabilities"
    legacy = root / "prompt-governance/capabilities"
    capability_root = canonical if canonical.exists() else legacy
    if not capability_root.is_dir() or capability_root.is_symlink():
        return ()

    usages: list[CapabilityUsage] = []
    for path in sorted(capability_root.rglob("*.json")):
        if not path.is_file() or path.is_symlink():
            continue
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            continue
        manifest = _mapping(document)
        if manifest is None:
            continue
        evaluation = _mapping(manifest.get("evaluation")) or {}
        callers = manifest.get("called_by")
        if not isinstance(callers, list):
            callers = []
        usages.append(
            CapabilityUsage(
                name=str(manifest.get("name", path.stem)),
                purpose=str(manifest.get("purpose", "undeclared")),
                owner=str(manifest.get("owner", "undeclared")),
                risk_level=str(manifest.get("risk_level", "undeclared")),
                readiness=str(evaluation.get("readiness", "not_configured")),
                called_by=tuple(str(item) for item in callers if isinstance(item, str)),
                manifest=path.relative_to(root),
            )
        )
    return tuple(usages)


def _evaluation_surface(capabilities: tuple[CapabilityUsage, ...]) -> StatusSurface:
    readiness = {capability.readiness for capability in capabilities}
    if readiness & {"baseline_ready", "regression_ready"}:
        state = "active"
        explanation = "at least one capability declares a checked evaluation baseline"
    elif readiness:
        state = "incomplete"
        explanation = "evaluation state is declared but no checked baseline is ready"
    else:
        state = "not_configured"
        explanation = "no capability evaluation state was discovered"
    return StatusSurface("evaluation_evidence", state, explanation)


def inspect_governance_status(root: Path) -> GovernanceStatus:
    """Build one deterministic, read-only adoption and usage status."""

    adoption = inspect_adoption(root)
    resolved = root.resolve()
    adopted = (
        adoption.count(AdoptionState.PRESENT) == 6
        and adoption.count(AdoptionState.CONFLICT) == 0
    )
    layout: str | None = None
    layout_error: str | None = None
    try:
        layout = load_repository_layout(resolved)
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
        layout_error = str(exc)

    ci = inspect_consumer_ci(resolved)
    capabilities = _capability_usages(resolved)
    report = check_repository(resolved)
    next_action = select_report_next_action(resolved, report)
    artifact_active = any(
        path.is_file() and not path.is_symlink()
        for artifact_root in (
            resolved / "governance/artifacts",
            resolved / "prompt-governance/artifacts",
        )
        if artifact_root.is_dir() and not artifact_root.is_symlink()
        for path in artifact_root.rglob("artifact.json")
    )
    ci_active = ci.state in {ConsumerCIState.MANAGED, ConsumerCIState.CUSTOM}
    managed_release = None
    managed_workflow = resolved / WORKFLOW_PATH
    if ci.state is ConsumerCIState.MANAGED and managed_workflow.is_file():
        managed_release = inspect_managed_workflow_content(
            managed_workflow.read_text(encoding="utf-8")
        )
    monitor_enabled = (
        managed_release is not None
        and comparable_version_key(managed_release.version)
        >= comparable_version_key("0.3.0")
    )
    upgrade_workflow = resolved / UPGRADE_WORKFLOW_PATH
    proposal_release = None
    if upgrade_workflow.is_file() and not upgrade_workflow.is_symlink():
        proposal_release = inspect_managed_upgrade_workflow_content(
            upgrade_workflow.read_text(encoding="utf-8")
        )
    proposal_enabled = (
        monitor_enabled
        and proposal_release is not None
        and comparable_version_key(proposal_release.version)
        >= comparable_version_key("0.3.0")
    )
    surfaces = (
        StatusSurface(
            "repository_validation",
            "available" if adopted else "incomplete",
            (
                "contracts, references, evidence declarations, and agent skills can be checked"
                if adopted
                else "core governance adoption paths are not all configured"
            ),
        ),
        StatusSurface(
            "pull_request_visibility",
            "active" if ci_active else ci.state.value,
            ci.message,
        ),
        _evaluation_surface(capabilities),
        StatusSurface(
            "benefit_evidence",
            (
                "monitor_enabled"
                if monitor_enabled
                else "ready_to_collect" if ci_active else "not_configured"
            ),
            (
                "CI restores the previous trusted main baseline, publishes observed "
                "trend evidence, and retains a self-contained monitor page"
                if monitor_enabled
                else "CI preserves versioned report snapshots; compare two runs with "
                "agentgov benefits compare after the workflow has run"
                if ci_active
                else "no CI report snapshots are configured for later comparison"
            ),
        ),
        StatusSurface(
            "upgrade_automation",
            "proposal_enabled" if proposal_enabled else "review_ready",
            (
                "scheduled and explicitly dispatched checks may create one bounded "
                "AgentGov Draft PR; merge remains human-controlled"
                if proposal_enabled
                else "consumer-local stable upgrade review is available; no authenticated "
                "branch or pull-request writer is configured"
            ),
        ),
        StatusSurface(
            "artifact_drift",
            "active" if artifact_active else "not_configured",
            (
                "generated capability artifacts can detect declared source drift"
                if artifact_active
                else "source-hash drift is not checked because no capability artifact is configured"
            ),
        ),
        StatusSurface(
            "human_authority",
            "declared" if (resolved / "AGENTS.md").is_file() else "missing",
            "repository instructions declare authority boundaries; AgentGov does not grant approval",
        ),
    )
    return GovernanceStatus(
        root=resolved,
        adopted=adopted,
        layout_version=layout,
        layout_error=layout_error,
        ci=ci,
        capabilities=capabilities,
        surfaces=surfaces,
        repository_report=report,
        next_action=next_action,
    )


def render_status_json(status: GovernanceStatus, *, non_interactive: bool) -> str:
    payload = {
        "contract_version": STATUS_CONTRACT_VERSION,
        "tool": {"name": "agentgov", "version": __version__},
        "repository": str(status.root),
        "mode": "read_only",
        "interaction": "non_interactive" if non_interactive else "no_prompt",
        "adoption": {
            "configured": status.adopted,
            "layout_version": status.layout_version,
            "layout_error": status.layout_error,
        },
        "ci": {
            "state": status.ci.state.value,
            "managed_path": status.ci.managed_path.as_posix(),
            "workflow_paths": [path.as_posix() for path in status.ci.workflow_paths],
            "message": status.ci.message,
        },
        "capabilities": [
            {
                "name": capability.name,
                "purpose": capability.purpose,
                "owner": capability.owner,
                "risk_level": capability.risk_level,
                "readiness": capability.readiness,
                "manifest": capability.manifest.as_posix(),
                "called_by": list(capability.called_by),
            }
            for capability in status.capabilities
        ],
        "surfaces": [
            {
                "name": surface.name,
                "state": surface.state,
                "explanation": surface.explanation,
            }
            for surface in status.surfaces
        ],
        "summary": {
            finding_status.value: status.repository_report.count(finding_status)
            for finding_status in FindingStatus
        },
        "next_action": {
            "kind": status.next_action.kind.value,
            "title": status.next_action.title,
            "command": status.next_action.command,
            "blocking": status.next_action.blocking,
        },
        "authority_boundary": {
            "modifies_repository": False,
            "runs_project_or_production_workflows": False,
            "authorizes_git_or_release_operations": False,
        },
    }
    return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"


def _escape_markdown_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\r\n", "<br>").replace("\n", "<br>")


def render_status_markdown(status: GovernanceStatus) -> str:
    """Render a deterministic, job-summary-friendly governance status."""

    layout = status.layout_version or ("invalid" if status.layout_error else "unversioned")
    report = status.repository_report
    lines = [
        "# AgentGov Status",
        "",
        f"Repository: `{_escape_markdown_cell(status.root.name)}`",
        "",
        (
            "> Read-only visibility: this status does not run project workflows or "
            "authorize merge, release, or deployment."
        ),
        "",
        "## At a glance",
        "",
        "| Area | State | Detail |",
        "|---|---|---|",
        (
            "| Adoption | "
            f"{'configured' if status.adopted else 'incomplete'} | "
            f"Layout `{_escape_markdown_cell(layout)}` |"
        ),
        (
            f"| CI | {_escape_markdown_cell(status.ci.state.value)} | "
            f"{_escape_markdown_cell(status.ci.message)} |"
        ),
        "",
        "## Findings",
        "",
        "| PASS | WARN | FAIL | ADVISORY |",
        "|---:|---:|---:|---:|",
        "| "
        + " | ".join(str(report.count(finding_status)) for finding_status in FindingStatus)
        + " |",
        "",
        "## Governed capabilities",
        "",
        "| Capability | Owner | Risk | Readiness | Used by |",
        "|---|---|---|---|---|",
    ]
    if status.capabilities:
        lines.extend(
            "| "
            f"`{_escape_markdown_cell(capability.name)}` | "
            f"{_escape_markdown_cell(capability.owner)} | "
            f"{_escape_markdown_cell(capability.risk_level)} | "
            f"{_escape_markdown_cell(capability.readiness)} | "
            f"{_escape_markdown_cell(', '.join(capability.called_by) or 'not declared')} |"
            for capability in status.capabilities
        )
    else:
        lines.append("| none | not declared | not declared | not configured | not declared |")

    lines.extend(
        [
            "",
            "## Governance surfaces",
            "",
            "| Surface | State | What it means |",
            "|---|---|---|",
            *(
                "| "
                f"`{_escape_markdown_cell(surface.name)}` | "
                f"{_escape_markdown_cell(surface.state)} | "
                f"{_escape_markdown_cell(surface.explanation)} |"
                for surface in status.surfaces
            ),
            "",
            "## Next action",
            "",
            _escape_markdown_cell(status.next_action.title),
        ]
    )
    if status.next_action.command:
        portable_command = status.next_action.command.replace(
            f'"{status.root}"', "."
        ).replace(str(status.root), ".")
        lines.extend(["", f"    {portable_command}"])
    lines.extend(
        [
            "",
            "## Authority boundary",
            "",
            "- Repository files were not modified.",
            "- Project and production workflows were not run.",
            "- Git, merge, release, and deployment actions remain separately authorized.",
            "- Visible status does not prove governance sufficiency.",
            "",
        ]
    )
    return "\n".join(lines)
