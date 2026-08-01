"""Honest before/after evidence from two AgentGov repository reports."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from agentgov import __version__


BENEFIT_COMPARISON_CONTRACT_VERSION = "1.0"
_STATUSES = {"PASS", "WARN", "FAIL", "ADVISORY"}
_REPORT_FIELDS = {
    "schema_version",
    "tool",
    "repository",
    "summary",
    "findings",
    "known_gaps",
    "recommended_actions",
    "scope_limitations",
}


@dataclass(frozen=True)
class FindingTransition:
    check_id: str
    before: str
    after: str


@dataclass(frozen=True)
class BenefitComparison:
    before_path: Path
    after_path: Path
    repository: str
    before_tool_version: str
    after_tool_version: str
    before_finding_count: int
    after_finding_count: int
    matched_check_count: int
    added_checks: tuple[str, ...]
    removed_checks: tuple[str, ...]
    transitions: tuple[FindingTransition, ...]

    @property
    def deterministic_failures_resolved(self) -> tuple[str, ...]:
        return tuple(
            item.check_id
            for item in self.transitions
            if item.before == "FAIL" and item.after == "PASS"
        )

    @property
    def deterministic_failures_introduced(self) -> tuple[str, ...]:
        return tuple(
            item.check_id
            for item in self.transitions
            if item.before == "PASS" and item.after == "FAIL"
        )

    @property
    def non_passing_findings_cleared(self) -> tuple[str, ...]:
        return tuple(
            item.check_id
            for item in self.transitions
            if item.before != "PASS" and item.after == "PASS"
        )


def _mapping(value: Any, *, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{field} must be an object")
    return value


def _load_report(path: Path) -> tuple[str, str, dict[str, str]]:
    if path.is_symlink() or not path.is_file():
        raise FileNotFoundError(path)
    document = json.loads(path.read_text(encoding="utf-8"))
    report = _mapping(document, field="report root")
    if set(report) != _REPORT_FIELDS:
        raise ValueError("report must use the exact repository report v1.0 fields")
    if report.get("schema_version") != "1.0":
        raise ValueError("report schema_version must equal '1.0'")
    repository = report.get("repository")
    if not isinstance(repository, str):
        raise ValueError("report repository must be a string")
    tool = _mapping(report.get("tool"), field="report tool")
    if set(tool) != {"name", "version"}:
        raise ValueError("report tool must contain exactly name and version")
    version = tool.get("version")
    if tool.get("name") != "agentgov" or not isinstance(version, str):
        raise ValueError("report tool must identify an AgentGov version")
    raw_findings = report.get("findings")
    if not isinstance(raw_findings, list):
        raise ValueError("report findings must be an array")
    findings: dict[str, str] = {}
    for index, raw_finding in enumerate(raw_findings):
        finding = _mapping(raw_finding, field=f"report findings[{index}]")
        if set(finding) != {"check_id", "status", "message"}:
            raise ValueError(f"report findings[{index}] has unsupported fields")
        check_id = finding.get("check_id")
        status = finding.get("status")
        message = finding.get("message")
        if not isinstance(check_id, str) or not check_id:
            raise ValueError(f"report findings[{index}].check_id must be non-empty")
        if status not in _STATUSES:
            raise ValueError(f"report findings[{index}].status is unsupported")
        if not isinstance(message, str):
            raise ValueError(f"report findings[{index}].message must be a string")
        if check_id in findings:
            raise ValueError(f"report contains duplicate check_id: {check_id}")
        findings[check_id] = str(status)

    summary = _mapping(report.get("summary"), field="report summary")
    expected_summary_fields = {status.lower() for status in _STATUSES}
    if set(summary) != expected_summary_fields:
        raise ValueError("report summary must contain exactly pass, warn, fail, advisory")
    calculated = {
        status.lower(): sum(1 for value in findings.values() if value == status)
        for status in _STATUSES
    }
    for field, expected in calculated.items():
        value = summary.get(field)
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ValueError(f"report summary.{field} must be a non-negative integer")
        if value != expected:
            raise ValueError(
                f"report summary.{field} does not match findings: "
                f"declared {value}, calculated {expected}"
            )
    return repository, version, findings


def compare_repository_reports(before: Path, after: Path) -> BenefitComparison:
    before_repository, before_version, before_findings = _load_report(before)
    after_repository, after_version, after_findings = _load_report(after)
    if before_repository != after_repository:
        raise ValueError("before and after reports must identify the same repository")

    before_ids = set(before_findings)
    after_ids = set(after_findings)
    matched = sorted(before_ids & after_ids)
    transitions = tuple(
        FindingTransition(
            check_id=check_id,
            before=before_findings[check_id],
            after=after_findings[check_id],
        )
        for check_id in matched
        if before_findings[check_id] != after_findings[check_id]
    )
    return BenefitComparison(
        before_path=before.resolve(),
        after_path=after.resolve(),
        repository=before_repository,
        before_tool_version=before_version,
        after_tool_version=after_version,
        before_finding_count=len(before_findings),
        after_finding_count=len(after_findings),
        matched_check_count=len(matched),
        added_checks=tuple(sorted(after_ids - before_ids)),
        removed_checks=tuple(sorted(before_ids - after_ids)),
        transitions=transitions,
    )


def benefit_comparison_document(comparison: BenefitComparison) -> dict[str, Any]:
    return {
        "contract_version": BENEFIT_COMPARISON_CONTRACT_VERSION,
        "tool": {"name": "agentgov", "version": __version__},
        "mode": "read_only",
        "repository": comparison.repository,
        "inputs": {
            "before": str(comparison.before_path),
            "after": str(comparison.after_path),
            "before_tool_version": comparison.before_tool_version,
            "after_tool_version": comparison.after_tool_version,
        },
        "denominators": {
            "before_finding_count": comparison.before_finding_count,
            "after_finding_count": comparison.after_finding_count,
            "matched_check_count": comparison.matched_check_count,
        },
        "evidence": {
            "deterministic_failures_resolved": list(
                comparison.deterministic_failures_resolved
            ),
            "deterministic_failures_introduced": list(
                comparison.deterministic_failures_introduced
            ),
            "non_passing_findings_cleared": list(
                comparison.non_passing_findings_cleared
            ),
            "added_checks": list(comparison.added_checks),
            "removed_checks": list(comparison.removed_checks),
            "transitions": [
                {
                    "check_id": item.check_id,
                    "before": item.before,
                    "after": item.after,
                }
                for item in comparison.transitions
            ],
        },
        "scope_limitations": [
            "This comparison describes two report snapshots; it does not prove causality.",
            "Added or removed checks are not classified as improvements or regressions.",
            "No prevented incident, time saving, coverage percentage, or ROI is inferred.",
            "Project-test results and post-merge runtime outcomes are not observed.",
        ],
        "authority_boundary": {
            "repository_modified": False,
            "git_or_pull_request_action_run": False,
            "merge_release_or_deploy_authorized": False,
        },
    }


def render_benefit_comparison_json(comparison: BenefitComparison) -> str:
    return json.dumps(
        benefit_comparison_document(comparison),
        indent=2,
        ensure_ascii=False,
    ) + "\n"
