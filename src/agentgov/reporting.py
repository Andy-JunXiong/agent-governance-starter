"""Deterministic Markdown reporting for repository governance findings."""

from __future__ import annotations

from pathlib import Path

from agentgov.repository import FindingStatus, RepositoryReport


class ReportConflictError(Exception):
    """Raised when report output would overwrite or cross an unsafe boundary."""


def _escape_table_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\r\n", "<br>").replace("\n", "<br>")


def render_repository_report(report: RepositoryReport) -> str:
    """Render one repository report without timestamps or score inflation."""

    statuses = (
        FindingStatus.PASS,
        FindingStatus.WARN,
        FindingStatus.FAIL,
        FindingStatus.ADVISORY,
    )
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
    lines.extend(f"| {status.value} | {report.count(status)} |" for status in statuses)
    lines.extend(
        [
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

    gaps = [
        finding
        for finding in report.findings
        if finding.status is not FindingStatus.PASS
    ]
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
            if finding.status is FindingStatus.FAIL:
                action = "Resolve this deterministic failure before treating governance as passing."
            elif finding.status is FindingStatus.WARN:
                action = "Complete or explicitly defer this non-blocking configuration gap."
            else:
                action = "Have an accountable human review and record this judgment."
            lines.append(f"- `{finding.check_id}`: {action}")
    else:
        lines.append("- Continue normal review and rerun checks after governance changes.")

    lines.extend(
        [
            "",
            "## Scope limitations",
            "",
            "- No governance coverage percentage or weighted score is calculated.",
            "- Referenced schema and call-site paths are not yet checked for existence.",
            "- Architecture quality and human-approval correctness remain review judgments.",
            "",
        ]
    )
    return "\n".join(lines)


def write_markdown_report(path: Path, content: str) -> None:
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
