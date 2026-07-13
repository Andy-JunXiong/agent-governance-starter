"""Deterministic serialization for repository governance findings."""

from __future__ import annotations

import json
from pathlib import Path

from agentgov.repository import Finding, FindingStatus, RepositoryReport


REPORT_SCHEMA_VERSION = "1.0"
REPORT_STATUSES = (
    FindingStatus.PASS,
    FindingStatus.WARN,
    FindingStatus.FAIL,
    FindingStatus.ADVISORY,
)
SCOPE_LIMITATIONS = (
    "No governance coverage percentage or weighted score is calculated.",
    (
        "Reference checks establish existence and structural readability, not "
        "semantic compatibility or runtime reachability."
    ),
    "Architecture quality and human-approval correctness remain review judgments.",
)


class ReportConflictError(Exception):
    """Raised when report output would overwrite or cross an unsafe boundary."""


def _escape_table_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\r\n", "<br>").replace("\n", "<br>")


def _known_gaps(report: RepositoryReport) -> tuple[Finding, ...]:
    return tuple(
        finding
        for finding in report.findings
        if finding.status is not FindingStatus.PASS
    )


def _recommended_action(finding: Finding) -> str:
    if finding.status is FindingStatus.FAIL:
        return "Resolve this deterministic failure before treating governance as passing."
    if finding.status is FindingStatus.WARN:
        return "Complete or explicitly defer this non-blocking configuration gap."
    return "Have an accountable human review and record this judgment."


def _finding_document(finding: Finding) -> dict[str, str]:
    return {
        "check_id": finding.check_id,
        "status": finding.status.value,
        "message": finding.message,
    }


def repository_report_document(report: RepositoryReport) -> dict[str, object]:
    """Build the versioned machine-readable contract from one check result."""

    gaps = _known_gaps(report)
    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "repository": str(report.root),
        "summary": {
            status.value.lower(): report.count(status) for status in REPORT_STATUSES
        },
        "findings": [_finding_document(finding) for finding in report.findings],
        "known_gaps": [_finding_document(finding) for finding in gaps],
        "recommended_actions": [
            {
                "check_id": finding.check_id,
                "status": finding.status.value,
                "action": _recommended_action(finding),
            }
            for finding in gaps
        ],
        "scope_limitations": list(SCOPE_LIMITATIONS),
    }


def render_repository_report_json(report: RepositoryReport) -> str:
    """Serialize a repository report as deterministic JSON with a trailing newline."""

    return json.dumps(
        repository_report_document(report),
        ensure_ascii=False,
        indent=2,
    ) + "\n"


def render_repository_report(report: RepositoryReport) -> str:
    """Render one repository report without timestamps or score inflation."""

    lines = [
        "# Agent Governance Report",
        "",
        f"Repository: `{report.root}`",
        "",
        "This report contains deterministic findings and explicit human-review",
        "advisories. It does not calculate a governance coverage percentage.",
        "",
        "## Summary",
        "",
        "| Status | Count |",
        "|---|---:|",
    ]
    lines.extend(
        f"| {status.value} | {report.count(status)} |" for status in REPORT_STATUSES
    )
    lines.extend(
        [
            "",
            "## How to interpret this report",
            "",
            "- `PASS` means a deterministic contract was satisfied. It is not an",
            "  approval to merge, publish, release, or deploy.",
            "- `WARN` marks a non-blocking configuration or evidence gap. An",
            "  accountable human must complete it or explicitly record a deferral.",
            "- `FAIL` marks a deterministic requirement that must be resolved before",
            "  governance is treated as passing.",
            "- `ADVISORY` marks a judgment that static checks cannot make. An",
            "  accountable human must review and record it.",
            "",
            (
                "Successful report generation means the checks ran; it does not "
                "mean governance is complete."
            ),
            "This report does not authorize merge, publish, release, or deploy.",
            "Those actions require separate explicit human approval.",
            "",
            "## Human decisions still required",
            "",
        ]
    )

    warnings = [
        finding for finding in report.findings if finding.status is FindingStatus.WARN
    ]
    failures = [
        finding for finding in report.findings if finding.status is FindingStatus.FAIL
    ]
    advisories = [
        finding
        for finding in report.findings
        if finding.status is FindingStatus.ADVISORY
    ]
    if warnings:
        warning_ids = ", ".join(f"`{finding.check_id}`" for finding in warnings)
        lines.append(
            "- Complete or explicitly defer each WARN finding: " f"{warning_ids}."
        )
    if failures:
        failure_ids = ", ".join(f"`{finding.check_id}`" for finding in failures)
        lines.append(
            f"- Resolve each FAIL finding before claiming a pass: {failure_ids}."
        )
    if advisories:
        advisory_ids = ", ".join(f"`{finding.check_id}`" for finding in advisories)
        lines.append(
            "- Have an accountable human review and record each ADVISORY judgment: "
            f"{advisory_ids}."
        )
    if not (warnings or failures or advisories):
        lines.append(
            "- No non-passing findings remain; still confirm that approval and "
            "escalation boundaries match the repository's real risks."
        )

    lines.extend(
        [
            "- Treat merge, publish, release, and deploy as separate human-controlled",
            "  actions regardless of this report's counts.",
            "",
            "## Findings",
            "",
            "| Status | Check | Finding |",
            "|---|---|---|",
        ]
    )
    lines.extend(
        "| "
        f"{finding.status.value} | "
        f"`{_escape_table_cell(finding.check_id)}` | "
        f"{_escape_table_cell(finding.message)} |"
        for finding in report.findings
    )

    gaps = _known_gaps(report)
    lines.extend(["", "## Known gaps", ""])
    if gaps:
        lines.extend(
            f"- **{finding.status.value}** `{finding.check_id}`: {finding.message}"
            for finding in gaps
        )
    else:
        lines.append("No non-passing findings were reported.")

    lines.extend(["", "## Recommended actions", ""])
    if gaps:
        for finding in gaps:
            lines.append(f"- `{finding.check_id}`: {_recommended_action(finding)}")
    else:
        lines.append("- Continue normal review and rerun checks after governance changes.")

    lines.extend(
        [
            "",
            "## Scope limitations",
            "",
            *(f"- {limitation}" for limitation in SCOPE_LIMITATIONS),
            "",
        ]
    )
    return "\n".join(lines)


def write_report(path: Path, content: str) -> None:
    """Write a new report file without creating parents or overwriting output."""

    if path.is_symlink() or path.exists():
        raise ReportConflictError(f"output already exists or is a symbolic link: {path}")
    parent = path.parent
    if parent.is_symlink():
        raise ReportConflictError(f"output parent must not be a symbolic link: {parent}")
    if not parent.exists():
        raise FileNotFoundError(parent)
    if not parent.is_dir():
        raise NotADirectoryError(parent)

    try:
        with path.open("x", encoding="utf-8", newline="\n") as output_file:
            output_file.write(content)
    except FileExistsError as exc:
        raise ReportConflictError(f"output already exists: {path}") from exc


def write_markdown_report(path: Path, content: str) -> None:
    """Backward-compatible wrapper for the original Markdown file writer."""

    write_report(path, content)
