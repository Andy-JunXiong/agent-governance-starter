"""Deterministic validity checks for longer-lived governance evidence."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import date, datetime, timezone
from enum import Enum
from pathlib import Path, PurePosixPath
from typing import Any, Mapping


CONTRACT = "agentgov.evidence-freshness"
SCHEMA_VERSION = "1.0"


class EvidenceFreshnessStatus(str, Enum):
    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"
    ADVISORY = "ADVISORY"
    NOT_APPLICABLE = "NOT_APPLICABLE"


@dataclass(frozen=True)
class EvidenceFreshnessResult:
    status: EvidenceFreshnessStatus
    evidence_id: str | None
    as_of: str
    reason_codes: tuple[str, ...]
    messages: tuple[str, ...]


_TOP_LEVEL_FIELDS = {
    "contract",
    "schema_version",
    "evidence_id",
    "applicability",
    "evidence_refs",
    "review",
    "validity",
    "invalidation",
}
_ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_EVENT_RE = re.compile(r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$")
_DATE_RE = re.compile(r"^\d{4}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12]\d|3[01])$")
_SENSITIVE_RE = re.compile(
    r"(?i)(?:api[_-]?key|access[_-]?token|auth[_-]?token|password|passwd|secret)[\"']?\s*[:=]"
)


def _parse_date(value: Any, *, path: str, errors: list[str]) -> date | None:
    if value is None:
        return None
    if not isinstance(value, str) or not _DATE_RE.fullmatch(value):
        errors.append(f"{path} must use YYYY-MM-DD or null")
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        errors.append(f"{path} must be a real calendar date")
        return None


def _parse_as_of(value: str | date | None) -> date:
    if value is None:
        return datetime.now(timezone.utc).date()
    if isinstance(value, date):
        return value
    if not isinstance(value, str) or not _DATE_RE.fullmatch(value):
        raise ValueError("as_of must use YYYY-MM-DD")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError("as_of must be a real calendar date") from exc


def _safe_reference(value: Any, *, path: str, errors: list[str]) -> str | None:
    if not isinstance(value, str) or not value or len(value) > 240:
        errors.append(f"{path} must be a non-empty repository-relative path")
        return None
    relative = PurePosixPath(value)
    if (
        "\\" in value
        or relative.is_absolute()
        or not relative.parts
        or ".." in relative.parts
        or value.startswith("./")
        or re.match(r"^[A-Za-z]:", value)
    ):
        errors.append(f"{path} must be a repository-relative POSIX path")
        return None
    return value


def _string_list(
    value: Any,
    *,
    path: str,
    errors: list[str],
    pattern: re.Pattern[str] | None = None,
) -> list[str] | None:
    if not isinstance(value, list):
        errors.append(f"{path} must be an array")
        return None
    if len(value) > 50:
        errors.append(f"{path} must contain at most 50 items")
    if len(value) != len(set(item for item in value if isinstance(item, str))):
        errors.append(f"{path} must contain unique items")
    result: list[str] = []
    for index, item in enumerate(value):
        item_path = f"{path}[{index}]"
        if pattern is None:
            checked = _safe_reference(item, path=item_path, errors=errors)
            if checked is not None:
                result.append(checked)
        elif (
            not isinstance(item, str)
            or len(item) > 120
            or not pattern.fullmatch(item)
        ):
            errors.append(f"{item_path} must use a normalized event identifier")
        else:
            result.append(item)
    return result


def _validate_document(document: Any) -> tuple[dict[str, Any] | None, list[str]]:
    errors: list[str] = []
    if not isinstance(document, Mapping):
        return None, ["$ must be an object"]
    if set(document) != _TOP_LEVEL_FIELDS:
        errors.append("$ must contain exactly the Evidence Freshness v1 fields")
    if document.get("contract") != CONTRACT:
        errors.append(f"$.contract must equal {CONTRACT!r}")
    if document.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"$.schema_version must equal {SCHEMA_VERSION!r}")

    evidence_id = document.get("evidence_id")
    if (
        not isinstance(evidence_id, str)
        or len(evidence_id) > 120
        or not _ID_RE.fullmatch(evidence_id)
    ):
        errors.append("$.evidence_id must use kebab-case")

    applicability = document.get("applicability")
    if not isinstance(applicability, Mapping) or set(applicability) != {"status", "reason"}:
        errors.append("$.applicability must contain exactly status and reason")
        applicability = {}
    applicability_status = applicability.get("status")
    applicability_reason = applicability.get("reason")
    if applicability_status not in {"applicable", "not_applicable"}:
        errors.append("$.applicability.status must be applicable or not_applicable")
    if applicability_reason is not None and (
        not isinstance(applicability_reason, str)
        or not applicability_reason.strip()
        or len(applicability_reason) > 400
    ):
        errors.append(
            "$.applicability.reason must be a non-empty string of at most 400 characters or null"
        )

    evidence_refs = _string_list(
        document.get("evidence_refs"), path="$.evidence_refs", errors=errors
    )

    review = document.get("review")
    if not isinstance(review, Mapping) or set(review) != {"reviewed_at", "review_due_on"}:
        errors.append("$.review must contain exactly reviewed_at and review_due_on")
        review = {}
    reviewed_at = _parse_date(review.get("reviewed_at"), path="$.review.reviewed_at", errors=errors)
    review_due_on = _parse_date(
        review.get("review_due_on"), path="$.review.review_due_on", errors=errors
    )

    validity = document.get("validity")
    if not isinstance(validity, Mapping) or set(validity) != {
        "expires_on",
        "policy_status",
        "policy_ref",
    }:
        errors.append(
            "$.validity must contain exactly expires_on, policy_status, and policy_ref"
        )
        validity = {}
    expires_on = _parse_date(
        validity.get("expires_on"), path="$.validity.expires_on", errors=errors
    )
    policy_status = validity.get("policy_status")
    if policy_status not in {"current", "superseded", "unknown", "not_applicable"}:
        errors.append(
            "$.validity.policy_status must be current, superseded, unknown, or not_applicable"
        )
    policy_ref_value = validity.get("policy_ref")
    policy_ref = None
    if policy_ref_value is not None:
        policy_ref = _safe_reference(
            policy_ref_value, path="$.validity.policy_ref", errors=errors
        )

    invalidation = document.get("invalidation")
    if not isinstance(invalidation, Mapping) or set(invalidation) != {
        "declared_events",
        "observed_events",
    }:
        errors.append(
            "$.invalidation must contain exactly declared_events and observed_events"
        )
        invalidation = {}
    declared_events = _string_list(
        invalidation.get("declared_events"),
        path="$.invalidation.declared_events",
        errors=errors,
        pattern=_EVENT_RE,
    )
    observed_events = _string_list(
        invalidation.get("observed_events"),
        path="$.invalidation.observed_events",
        errors=errors,
        pattern=_EVENT_RE,
    )

    if reviewed_at and review_due_on and review_due_on <= reviewed_at:
        errors.append("$.review.review_due_on must be later than reviewed_at")
    if reviewed_at and expires_on and expires_on <= reviewed_at:
        errors.append("$.validity.expires_on must be later than reviewed_at")

    if applicability_status == "applicable":
        if applicability_reason is not None:
            errors.append("$.applicability.reason must be null when evidence is applicable")
        if not evidence_refs:
            errors.append("$.evidence_refs must not be empty when evidence is applicable")
        if reviewed_at is None:
            errors.append("$.review.reviewed_at is required when evidence is applicable")
        if policy_status == "not_applicable":
            errors.append(
                "$.validity.policy_status cannot be not_applicable when evidence is applicable"
            )
        if policy_ref is None:
            errors.append("$.validity.policy_ref is required when evidence is applicable")
    elif applicability_status == "not_applicable":
        if not isinstance(applicability_reason, str) or not applicability_reason.strip():
            errors.append(
                "$.applicability.reason is required when evidence is not_applicable"
            )
        if evidence_refs:
            errors.append("$.evidence_refs must be empty when evidence is not_applicable")
        if any(item is not None for item in (reviewed_at, review_due_on, expires_on, policy_ref)):
            errors.append("not_applicable evidence cannot declare review or validity dates")
        if policy_status != "not_applicable":
            errors.append(
                "$.validity.policy_status must be not_applicable when evidence is not_applicable"
            )
        if declared_events or observed_events:
            errors.append("not_applicable evidence cannot declare invalidation events")

    encoded = json.dumps(document, ensure_ascii=False, sort_keys=True)
    if _SENSITIVE_RE.search(encoded):
        errors.append("$ contains secret-like material, which is not allowed")

    normalized = {
        "evidence_id": evidence_id if isinstance(evidence_id, str) else None,
        "applicability_status": applicability_status,
        "reviewed_at": reviewed_at,
        "review_due_on": review_due_on,
        "expires_on": expires_on,
        "policy_status": policy_status,
        "declared_events": tuple(declared_events or ()),
        "observed_events": tuple(observed_events or ()),
    }
    return normalized, errors


def check_evidence_freshness(
    record: Path,
    *,
    as_of: str | date | None = None,
) -> EvidenceFreshnessResult:
    """Check one Evidence Freshness v1 record without changing the repository."""

    effective_date = _parse_as_of(as_of)
    if record.is_symlink():
        raise ValueError("evidence freshness record must not be a symbolic link")
    document = json.loads(record.read_text(encoding="utf-8"))
    normalized, errors = _validate_document(document)
    evidence_id = normalized.get("evidence_id") if normalized else None
    if errors:
        return EvidenceFreshnessResult(
            status=EvidenceFreshnessStatus.FAIL,
            evidence_id=evidence_id,
            as_of=effective_date.isoformat(),
            reason_codes=("contract_invalid",),
            messages=tuple(errors),
        )
    assert normalized is not None

    if normalized["applicability_status"] == "not_applicable":
        return EvidenceFreshnessResult(
            status=EvidenceFreshnessStatus.NOT_APPLICABLE,
            evidence_id=evidence_id,
            as_of=effective_date.isoformat(),
            reason_codes=("declared_not_applicable",),
            messages=("Evidence freshness is explicitly not applicable to this record.",),
        )

    reasons: list[str] = []
    messages: list[str] = []
    failures = 0
    warnings = 0
    advisories = 0

    reviewed_at = normalized["reviewed_at"]
    if reviewed_at > effective_date:
        failures += 1
        reasons.append("reviewed_in_future")
        messages.append("The review date is later than the as-of date.")

    expires_on = normalized["expires_on"]
    if expires_on is not None and effective_date >= expires_on:
        failures += 1
        reasons.append("explicitly_expired")
        messages.append("The explicit expiry date has been reached.")

    policy_status = normalized["policy_status"]
    if policy_status == "superseded":
        failures += 1
        reasons.append("policy_superseded")
        messages.append("The governing policy is explicitly superseded.")
    elif policy_status == "unknown":
        advisories += 1
        reasons.append("policy_validity_unknown")
        messages.append("An accountable human must review the unknown policy validity.")

    matched_events = sorted(
        set(normalized["declared_events"]) & set(normalized["observed_events"])
    )
    if matched_events:
        failures += 1
        reasons.append("invalidation_event_observed")
        messages.append(
            "Declared invalidating change events were observed: " + ", ".join(matched_events)
        )

    review_due_on = normalized["review_due_on"]
    if review_due_on is not None and effective_date >= review_due_on:
        warnings += 1
        reasons.append("review_due")
        messages.append(
            "The declared review date is due; elapsed time alone does not invalidate the evidence."
        )

    if failures:
        status = EvidenceFreshnessStatus.FAIL
    elif warnings:
        status = EvidenceFreshnessStatus.WARN
    elif advisories:
        status = EvidenceFreshnessStatus.ADVISORY
    else:
        status = EvidenceFreshnessStatus.PASS
        reasons.append("current")
        messages.append("No explicit expiry or invalidating condition is active.")

    return EvidenceFreshnessResult(
        status=status,
        evidence_id=evidence_id,
        as_of=effective_date.isoformat(),
        reason_codes=tuple(reasons),
        messages=tuple(messages),
    )
