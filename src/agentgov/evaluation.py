"""Zero-dependency evaluation readiness checks."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path, PurePosixPath
from typing import Any, Mapping

from agentgov.capability import EVALUATION_READINESS


class EvaluationStatus(str, Enum):
    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"


@dataclass(frozen=True)
class EvaluationResult:
    status: EvaluationStatus
    readiness: str
    messages: tuple[str, ...]
    capability_name: str | None = None


_NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_CASE_TYPES = {
    "seed": "seed-cases",
    "golden": "golden-examples",
    "failure": "failure-cases",
}
_SOURCE_TYPES = {"hand_constructed", "production_derived", "external"}
_RISK_LEVELS = {"low", "medium", "high", "critical"}
_DECISION_OUTCOMES = {
    "pending",
    "accepted",
    "accepted_with_conditions",
    "rejected",
}
_METRIC_DIRECTIONS = {"higher_is_better", "lower_is_better"}
_DATE_RE = re.compile(r"^\d{4}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12]\d|3[01])$")


def _check_fields(
    value: Mapping[str, Any],
    *,
    path: str,
    required: set[str],
    allowed: set[str],
    errors: list[str],
) -> None:
    for field in sorted(required - set(value)):
        errors.append(f"{path}.{field} is required")
    for field in sorted(set(value) - allowed):
        errors.append(f"{path}.{field} is not allowed")


def _mapping(value: Any, path: str, errors: list[str]) -> Mapping[str, Any] | None:
    if not isinstance(value, Mapping):
        errors.append(f"{path} must be an object")
        return None
    return value


def _string(value: Any, path: str, errors: list[str], *, minimum: int = 1) -> str | None:
    if not isinstance(value, str) or len(value) < minimum:
        errors.append(f"{path} must be a string with at least {minimum} characters")
        return None
    return value


def _string_list(value: Any, path: str, errors: list[str]) -> list[str] | None:
    if not isinstance(value, list):
        errors.append(f"{path} must be an array")
        return None
    if any(not isinstance(item, str) or not item for item in value):
        errors.append(f"{path} must contain only non-empty strings")
        return None
    if len(set(value)) != len(value):
        errors.append(f"{path} must contain unique items")
    return value


def _validate_source(value: Any, path: str, errors: list[str]) -> None:
    source = _mapping(value, path, errors)
    if source is None:
        return
    fields = {"source_type", "reference", "sanitized"}
    _check_fields(source, path=path, required=fields, allowed=fields, errors=errors)
    source_type = source.get("source_type")
    if not isinstance(source_type, str) or source_type not in _SOURCE_TYPES:
        errors.append(f"{path}.source_type must be one of {sorted(_SOURCE_TYPES)}")
    _string(source.get("reference"), f"{path}.reference", errors)
    sanitized = source.get("sanitized")
    if not isinstance(sanitized, bool):
        errors.append(f"{path}.sanitized must be a boolean")
    if source_type == "production_derived" and sanitized is not True:
        errors.append(f"{path}.sanitized must be true for production-derived material")


def _validate_manifest(manifest: Mapping[str, Any]) -> tuple[str, dict[str, list[str]], list[str]]:
    errors: list[str] = []
    fields = {
        "schema_version",
        "capability_name",
        "declared_readiness",
        "cases",
        "baseline",
        "regression",
        "decision",
    }
    _check_fields(
        manifest,
        path="$",
        required=fields - {"decision"},
        allowed=fields,
        errors=errors,
    )
    if manifest.get("schema_version") != "1.0":
        errors.append("$.schema_version must equal '1.0'")
    capability_name = _string(manifest.get("capability_name"), "$.capability_name", errors) or ""
    if capability_name and not _NAME_RE.fullmatch(capability_name):
        errors.append("$.capability_name must use kebab-case")
    readiness = manifest.get("declared_readiness")
    if not isinstance(readiness, str) or readiness not in EVALUATION_READINESS:
        errors.append(f"$.declared_readiness must be one of {sorted(EVALUATION_READINESS)}")
        readiness = "unknown"

    case_refs: dict[str, list[str]] = {case_type: [] for case_type in _CASE_TYPES}
    cases = _mapping(manifest.get("cases"), "$.cases", errors)
    if cases is not None:
        case_fields = set(_CASE_TYPES)
        _check_fields(cases, path="$.cases", required=case_fields, allowed=case_fields, errors=errors)
        for case_type in _CASE_TYPES:
            refs = _string_list(cases.get(case_type), f"$.cases.{case_type}", errors)
            if refs is not None:
                case_refs[case_type] = refs

    baseline = _mapping(manifest.get("baseline"), "$.baseline", errors)
    if baseline is not None:
        required = {"human_approved", "evidence_refs"}
        allowed = required | {"reviewer", "reviewed_at"}
        _check_fields(baseline, path="$.baseline", required=required, allowed=allowed, errors=errors)
        approved = baseline.get("human_approved")
        if not isinstance(approved, bool):
            errors.append("$.baseline.human_approved must be a boolean")
        evidence_refs = _string_list(
            baseline.get("evidence_refs"), "$.baseline.evidence_refs", errors
        )
        if readiness in {"baseline_ready", "regression_ready"}:
            if approved is not True:
                errors.append("$.baseline.human_approved must be true for declared readiness")
            _string(baseline.get("reviewer"), "$.baseline.reviewer", errors)
            if evidence_refs == []:
                errors.append("$.baseline.evidence_refs must not be empty for declared readiness")
        reviewed_at = baseline.get("reviewed_at")
        if reviewed_at is not None:
            reviewed_at = _string(reviewed_at, "$.baseline.reviewed_at", errors)
            if reviewed_at and not _DATE_RE.fullmatch(reviewed_at):
                errors.append("$.baseline.reviewed_at must use YYYY-MM-DD")

    regression = _mapping(manifest.get("regression"), "$.regression", errors)
    if regression is not None:
        required = {"threshold_configured", "minimum_pass_rate"}
        allowed = required | {"baseline_comparison"}
        _check_fields(
            regression,
            path="$.regression",
            required=required,
            allowed=allowed,
            errors=errors,
        )
        configured = regression.get("threshold_configured")
        if not isinstance(configured, bool):
            errors.append("$.regression.threshold_configured must be a boolean")
        pass_rate = regression.get("minimum_pass_rate")
        if pass_rate is not None and (
            isinstance(pass_rate, bool)
            or not isinstance(pass_rate, (int, float))
            or not 0 <= pass_rate <= 1
        ):
            errors.append("$.regression.minimum_pass_rate must be null or a number from 0 to 1")
        comparison = regression.get("baseline_comparison")
        if comparison is not None:
            comparison = _mapping(
                comparison, "$.regression.baseline_comparison", errors
            )
        if comparison is not None:
            comparison_fields = {
                "baseline_ref",
                "metric",
                "direction",
                "minimum_improvement",
            }
            _check_fields(
                comparison,
                path="$.regression.baseline_comparison",
                required=comparison_fields,
                allowed=comparison_fields,
                errors=errors,
            )
            _string(
                comparison.get("baseline_ref"),
                "$.regression.baseline_comparison.baseline_ref",
                errors,
            )
            metric = _string(
                comparison.get("metric"),
                "$.regression.baseline_comparison.metric",
                errors,
            )
            if metric and not re.fullmatch(r"^[a-z0-9]+(?:[_-][a-z0-9]+)*$", metric):
                errors.append(
                    "$.regression.baseline_comparison.metric must use lowercase words"
                )
            direction = comparison.get("direction")
            if direction not in _METRIC_DIRECTIONS:
                errors.append(
                    "$.regression.baseline_comparison.direction must be one of "
                    f"{sorted(_METRIC_DIRECTIONS)}"
                )
            improvement = comparison.get("minimum_improvement")
            if (
                isinstance(improvement, bool)
                or not isinstance(improvement, (int, float))
                or improvement < 0
            ):
                errors.append(
                    "$.regression.baseline_comparison.minimum_improvement "
                    "must be a non-negative number"
                )
        if readiness == "regression_ready":
            if configured is not True:
                errors.append("$.regression.threshold_configured must be true for regression_ready")
            numeric_pass_rate = (
                not isinstance(pass_rate, bool) and isinstance(pass_rate, (int, float))
            )
            has_comparison = comparison is not None
            if numeric_pass_rate == has_comparison:
                errors.append(
                    "$.regression must configure exactly one of numeric "
                    "minimum_pass_rate or baseline_comparison for regression_ready"
                )

    decision = manifest.get("decision")
    if decision is not None:
        decision = _mapping(decision, "$.decision", errors)
    if decision is not None:
        decision_fields = {
            "outcome",
            "reason",
            "reviewer",
            "reviewed_at",
            "evidence_refs",
        }
        _check_fields(
            decision,
            path="$.decision",
            required=decision_fields,
            allowed=decision_fields,
            errors=errors,
        )
        outcome = decision.get("outcome")
        if outcome not in _DECISION_OUTCOMES:
            errors.append(f"$.decision.outcome must be one of {sorted(_DECISION_OUTCOMES)}")
        _string(decision.get("reason"), "$.decision.reason", errors, minimum=10)
        _string(decision.get("reviewer"), "$.decision.reviewer", errors)
        reviewed_at = _string(
            decision.get("reviewed_at"), "$.decision.reviewed_at", errors
        )
        if reviewed_at and not _DATE_RE.fullmatch(reviewed_at):
            errors.append("$.decision.reviewed_at must use YYYY-MM-DD")
        decision_evidence = _string_list(
            decision.get("evidence_refs"), "$.decision.evidence_refs", errors
        )
        if outcome != "pending" and decision_evidence == []:
            errors.append(
                "$.decision.evidence_refs must not be empty for a completed decision"
            )

    return str(readiness), case_refs, errors


def _safe_case_path(bundle: Path, reference: str, expected_directory: str) -> Path:
    if "\\" in reference:
        raise ValueError("case references must use forward slashes")
    relative = PurePosixPath(reference)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("case references must remain inside the evaluation bundle")
    if not relative.parts or relative.parts[0] != expected_directory or relative.suffix != ".json":
        raise ValueError(f"case reference must point to {expected_directory}/*.json")

    path = bundle.joinpath(*relative.parts)
    current = bundle
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise ValueError("case references must not use symbolic links")
    return path


def _validate_case(case_type: str, case: Mapping[str, Any]) -> tuple[str, str, bool, list[str]]:
    errors: list[str] = []
    common = {"schema_version", "case_id", "capability_name", "input", "source"}
    type_fields = {
        "seed": {"expected_properties", "review_status"},
        "golden": {"expected_output", "approval"},
        "failure": {
            "observed_failure",
            "expected_behavior",
            "regression_assertion",
            "risk_level",
            "review_status",
        },
    }[case_type]
    fields = common | type_fields
    _check_fields(case, path="$", required=fields, allowed=fields, errors=errors)
    if case.get("schema_version") != "1.0":
        errors.append("$.schema_version must equal '1.0'")
    case_id = _string(case.get("case_id"), "$.case_id", errors) or ""
    capability_name = _string(case.get("capability_name"), "$.capability_name", errors) or ""
    for value, path in ((case_id, "$.case_id"), (capability_name, "$.capability_name")):
        if value and not _NAME_RE.fullmatch(value):
            errors.append(f"{path} must use kebab-case")
    if not isinstance(case.get("input"), Mapping):
        errors.append("$.input must be an object")
    _validate_source(case.get("source"), "$.source", errors)

    reviewed = False
    if case_type == "seed":
        expected = case.get("expected_properties")
        if not isinstance(expected, Mapping) or not expected:
            errors.append("$.expected_properties must be a non-empty object")
        status = case.get("review_status")
        if status not in {"draft", "reviewed"}:
            errors.append("$.review_status must be draft or reviewed")
        reviewed = status == "reviewed"
    elif case_type == "golden":
        expected = case.get("expected_output")
        if not isinstance(expected, Mapping) or not expected:
            errors.append("$.expected_output must be a non-empty object")
        approval = _mapping(case.get("approval"), "$.approval", errors)
        if approval is not None:
            approval_fields = {"status", "reviewer", "rationale"}
            _check_fields(
                approval,
                path="$.approval",
                required=approval_fields,
                allowed=approval_fields,
                errors=errors,
            )
            if approval.get("status") != "approved":
                errors.append("$.approval.status must equal 'approved'")
            _string(approval.get("reviewer"), "$.approval.reviewer", errors)
            _string(approval.get("rationale"), "$.approval.rationale", errors, minimum=10)
            reviewed = not errors
    else:
        _string(case.get("observed_failure"), "$.observed_failure", errors, minimum=10)
        _string(case.get("expected_behavior"), "$.expected_behavior", errors, minimum=10)
        assertion = case.get("regression_assertion")
        if not isinstance(assertion, Mapping) or not assertion:
            errors.append("$.regression_assertion must be a non-empty object")
        risk_level = case.get("risk_level")
        if not isinstance(risk_level, str) or risk_level not in _RISK_LEVELS:
            errors.append(f"$.risk_level must be one of {sorted(_RISK_LEVELS)}")
        if case.get("review_status") != "reviewed":
            errors.append("$.review_status must equal 'reviewed'")
        reviewed = not errors

    return case_id, capability_name, reviewed, errors


def check_evaluation_bundle(bundle: Path) -> EvaluationResult:
    """Validate evidence and the honesty of one declared readiness label."""

    if bundle.is_symlink():
        raise ValueError(f"evaluation bundle must not be a symbolic link: {bundle}")
    if not bundle.exists():
        raise FileNotFoundError(bundle)
    if not bundle.is_dir():
        raise ValueError(f"evaluation bundle is not a directory: {bundle}")

    manifest_path = bundle / "evaluation-manifest.json"
    if not manifest_path.exists():
        return EvaluationResult(
            EvaluationStatus.WARN,
            "not_configured",
            ("evaluation-manifest.json is missing",),
        )
    if manifest_path.is_symlink():
        return EvaluationResult(
            EvaluationStatus.FAIL,
            "unknown",
            ("evaluation-manifest.json must not be a symbolic link",),
        )

    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return EvaluationResult(
            EvaluationStatus.FAIL,
            "unknown",
            (f"evaluation-manifest.json invalid JSON at {exc.lineno}:{exc.colno}: {exc.msg}",),
        )
    if not isinstance(payload, Mapping):
        return EvaluationResult(
            EvaluationStatus.FAIL,
            "unknown",
            ("evaluation manifest root must be an object",),
        )

    readiness, case_refs, errors = _validate_manifest(payload)
    capability_name = payload.get("capability_name")
    declared_capability = (
        capability_name
        if isinstance(capability_name, str) and _NAME_RE.fullmatch(capability_name)
        else None
    )
    counts = {case_type: 0 for case_type in _CASE_TYPES}
    seen_case_ids: set[str] = set()
    for case_type, references in case_refs.items():
        for reference in references:
            try:
                path = _safe_case_path(bundle, reference, _CASE_TYPES[case_type])
            except ValueError as exc:
                errors.append(f"{reference}: {exc}")
                continue
            if not path.is_file():
                errors.append(f"{reference}: referenced case file is missing")
                continue
            try:
                case_payload = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                errors.append(f"{reference}: invalid JSON at {exc.lineno}:{exc.colno}: {exc.msg}")
                continue
            if not isinstance(case_payload, Mapping):
                errors.append(f"{reference}: case root must be an object")
                continue
            case_id, case_capability, reviewed, case_errors = _validate_case(case_type, case_payload)
            errors.extend(f"{reference}: {error}" for error in case_errors)
            if case_id:
                if case_id in seen_case_ids:
                    errors.append(f"{reference}: duplicate case_id {case_id!r}")
                seen_case_ids.add(case_id)
            if case_capability and case_capability != capability_name:
                errors.append(
                    f"{reference}: capability_name must equal manifest capability_name"
                )
            if not case_errors and reviewed and case_capability == capability_name:
                counts[case_type] += 1

    if readiness in {"baseline_ready", "regression_ready"}:
        for case_type in _CASE_TYPES:
            if counts[case_type] < 1:
                errors.append(
                    f"declared {readiness} requires at least one reviewed {case_type} case"
                )

    if errors:
        return EvaluationResult(
            EvaluationStatus.FAIL,
            readiness,
            tuple(errors),
            declared_capability,
        )
    if readiness in {"not_configured", "schema_only", "needs_seed_cases"}:
        return EvaluationResult(
            EvaluationStatus.WARN,
            readiness,
            (f"declared readiness {readiness} is valid but incomplete",),
            declared_capability,
        )
    return EvaluationResult(
        EvaluationStatus.PASS,
        readiness,
        (f"evidence supports declared readiness {readiness}",),
        declared_capability,
    )
