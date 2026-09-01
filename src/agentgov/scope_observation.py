"""Persist one path-level scope observation and bind it to an existing event."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping

from agentgov.change_scope import (
    SCOPE_REPORT_CONTRACT,
    SCOPE_REPORT_SCHEMA_VERSION,
    DevelopmentScopeReport,
    ScopeFindingStatus,
    check_development_scope,
)
from agentgov.event_store import LocalStateError, append_governance_event, write_local_record


_REPORT_FIELDS = {
    "contract",
    "schema_version",
    "task_id",
    "task_path",
    "task_digest",
    "head_sha",
    "changes",
    "findings",
    "known_limits",
    "authority_boundary",
}
_CHANGE_FIELDS = {"layer", "status", "path", "old_path", "endpoints"}
_ENDPOINT_FIELDS = {
    "role",
    "path",
    "admitted",
    "matched_include",
    "matched_exclude",
    "reason",
}
_FINDING_FIELDS = {"status", "check_id", "message"}
_LAYERS = {"staged", "unstaged", "untracked"}
_CHANGE_STATUSES = {
    "added",
    "copied",
    "deleted",
    "modified",
    "renamed",
    "type_changed",
    "unmerged",
    "unknown",
    "untracked",
}
_ROLES = {"current", "old", "new"}
_FINDING_STATUSES = {"PASS", "FAIL", "ADVISORY"}
_AUTHORITY_BOUNDARY = {
    "writes_repository": False,
    "modifies_worktree": False,
    "modifies_index": False,
    "modifies_branch": False,
    "modifies_history": False,
    "authorizes_exception": False,
    "authorizes_commit": False,
    "authorizes_merge": False,
}
_ARTIFACT_RE = re.compile(r"\.agentgov/evidence/(scp-[0-9a-f]{32})\.json")
_DIGEST_RE = re.compile(r"sha256:[0-9a-f]{64}")
_HEAD_RE = re.compile(r"[0-9a-f]{40,64}")


class ScopeObservationError(RuntimeError):
    """A scope observation cannot be recorded or trusted safely."""


@dataclass(frozen=True)
class ScopeObservation:
    report: DevelopmentScopeReport
    evidence_ref: str
    event_ref: str


def _safe_path(value: Any, *, nullable: bool = False) -> bool:
    if value is None:
        return nullable
    return (
        isinstance(value, str)
        and bool(value)
        and not value.startswith(("/", "\\"))
        and "\\" not in value
        and ".." not in Path(value).parts
    )


def scope_report_payload(report: DevelopmentScopeReport) -> Mapping[str, Any]:
    payload = asdict(report)
    for finding in payload["findings"]:
        finding["status"] = finding["status"].value
    return payload


def _canonical_payload(payload: Mapping[str, Any]) -> bytes:
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _artifact_id(payload: Mapping[str, Any]) -> str:
    return "scp-" + hashlib.sha256(_canonical_payload(payload)).hexdigest()[:32]


def _validate_scope_report_payload(
    payload: Any,
    *,
    expected_task_id: str,
    expected_task_digest: str,
) -> Mapping[str, Any]:
    if not isinstance(payload, dict) or set(payload) != _REPORT_FIELDS:
        raise ScopeObservationError("scope observation has unexpected fields")
    if (
        payload.get("contract") != SCOPE_REPORT_CONTRACT
        or payload.get("schema_version") != SCOPE_REPORT_SCHEMA_VERSION
    ):
        raise ScopeObservationError("scope observation uses an unsupported contract")
    if payload.get("task_id") != expected_task_id:
        raise ScopeObservationError("scope observation task_id does not match the event")
    if payload.get("task_digest") != expected_task_digest or not _DIGEST_RE.fullmatch(
        str(payload.get("task_digest", ""))
    ):
        raise ScopeObservationError("scope observation task digest does not match the event")
    if not _safe_path(payload.get("task_path")):
        raise ScopeObservationError("scope observation task path is unsafe")
    if not isinstance(payload.get("head_sha"), str) or not _HEAD_RE.fullmatch(
        payload["head_sha"]
    ):
        raise ScopeObservationError("scope observation HEAD identity is invalid")

    changes = payload.get("changes")
    if not isinstance(changes, list):
        raise ScopeObservationError("scope observation changes must be an array")
    for change in changes:
        if not isinstance(change, dict) or set(change) != _CHANGE_FIELDS:
            raise ScopeObservationError("scope observation change has unexpected fields")
        if change.get("layer") not in _LAYERS or change.get("status") not in _CHANGE_STATUSES:
            raise ScopeObservationError("scope observation change classification is invalid")
        if not _safe_path(change.get("path")) or not _safe_path(
            change.get("old_path"), nullable=True
        ):
            raise ScopeObservationError("scope observation change path is unsafe")
        endpoints = change.get("endpoints")
        if not isinstance(endpoints, list) or not 1 <= len(endpoints) <= 2:
            raise ScopeObservationError("scope observation endpoints are invalid")
        for endpoint in endpoints:
            if not isinstance(endpoint, dict) or set(endpoint) != _ENDPOINT_FIELDS:
                raise ScopeObservationError("scope observation endpoint has unexpected fields")
            if endpoint.get("role") not in _ROLES or not isinstance(
                endpoint.get("admitted"), bool
            ):
                raise ScopeObservationError("scope observation endpoint classification is invalid")
            if not _safe_path(endpoint.get("path")):
                raise ScopeObservationError("scope observation endpoint path is unsafe")
            for field in ("matched_include", "matched_exclude"):
                if not _safe_path(endpoint.get(field), nullable=True):
                    raise ScopeObservationError("scope observation scope match is unsafe")
            if not isinstance(endpoint.get("reason"), str) or not endpoint["reason"]:
                raise ScopeObservationError("scope observation endpoint reason is invalid")

    findings = payload.get("findings")
    if not isinstance(findings, list) or not findings:
        raise ScopeObservationError("scope observation findings must be a non-empty array")
    for finding in findings:
        if not isinstance(finding, dict) or set(finding) != _FINDING_FIELDS:
            raise ScopeObservationError("scope observation finding has unexpected fields")
        if finding.get("status") not in _FINDING_STATUSES or any(
            not isinstance(finding.get(field), str) or not finding[field]
            for field in ("check_id", "message")
        ):
            raise ScopeObservationError("scope observation finding is invalid")

    known_limits = payload.get("known_limits")
    if (
        not isinstance(known_limits, list)
        or not known_limits
        or len(known_limits) != len(set(known_limits))
        or any(not isinstance(item, str) or not item for item in known_limits)
    ):
        raise ScopeObservationError("scope observation known limits are invalid")
    if payload.get("authority_boundary") != _AUTHORITY_BOUNDARY:
        raise ScopeObservationError("scope observation authority boundary is invalid")
    return payload


def load_scope_observation(
    repository: Path,
    evidence_ref: str,
    *,
    expected_task_id: str,
    expected_task_digest: str,
) -> Mapping[str, Any]:
    """Load one event-referenced scope report with exact identity binding."""

    match = _ARTIFACT_RE.fullmatch(evidence_ref)
    if match is None:
        raise ScopeObservationError("scope observation reference is unsupported or unsafe")
    root = repository.resolve()
    path = root / evidence_ref
    if path.is_symlink() or not path.is_file():
        raise ScopeObservationError("scope observation artifact is unavailable")
    try:
        if path.resolve().parent != (root / ".agentgov" / "evidence").resolve():
            raise ScopeObservationError("scope observation artifact escaped local evidence")
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ScopeObservationError(f"cannot read scope observation artifact: {exc}") from exc
    validated = _validate_scope_report_payload(
        payload,
        expected_task_id=expected_task_id,
        expected_task_digest=expected_task_digest,
    )
    if _artifact_id(validated) != match.group(1):
        raise ScopeObservationError("scope observation artifact identity does not match its content")
    return validated


def record_scope_observation(
    repository: Path,
    task_path: Path,
    *,
    actor_class: str,
    actor_label: str | None,
    reason_codes: tuple[str, ...],
    expected_changed_paths: tuple[str, ...] | None = None,
) -> ScopeObservation:
    """Check scope, persist its report, and append one evidence-bound event."""

    report = check_development_scope(task_path, repository=repository)
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
    if expected_changed_paths is not None and observed_paths != expected_changed_paths:
        raise ScopeObservationError(
            "working-copy paths changed after the adapter trigger; start a fresh cycle"
        )

    payload = scope_report_payload(report)
    record_id = _artifact_id(payload)
    expected_ref = f".agentgov/evidence/{record_id}.json"
    try:
        evidence_ref = write_local_record(
            repository,
            area="evidence",
            record_id=record_id,
            payload=payload,
        )
    except LocalStateError:
        existing = load_scope_observation(
            repository,
            expected_ref,
            expected_task_id=report.task_id,
            expected_task_digest=report.task_digest,
        )
        if _canonical_payload(existing) != _canonical_payload(payload):
            raise ScopeObservationError("existing scope observation artifact conflicts")
        evidence_ref = expected_ref

    event_reasons = reason_codes + (("scope_failure",) if report.has_failures else ())
    _, event_ref = append_governance_event(
        repository,
        event_type="scope.checked",
        actor_class=actor_class,
        actor_label=actor_label,
        task_id=report.task_id,
        task_digest=report.task_digest,
        outcome="failed" if report.has_failures else "passed",
        evidence_ref=evidence_ref,
        reason_codes=event_reasons,
        metrics={
            "changes": len(report.changes),
            "failures": report.count(ScopeFindingStatus.FAIL),
            "advisories": report.count(ScopeFindingStatus.ADVISORY),
        },
    )
    return ScopeObservation(report=report, evidence_ref=evidence_ref, event_ref=event_ref)
