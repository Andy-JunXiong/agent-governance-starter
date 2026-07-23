"""Zero-dependency validation for legacy prompt and canonical AI capabilities."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Mapping


SCHEMA_VERSION = "1.0"
CAPABILITY_KINDS = {
    "product_runtime",
    "operator_guidance",
    "evaluation_judge",
}
CAPABILITY_TYPES = {
    "decision_support",
    "evaluation_judge",
    "ml_inference",
    "operator_guidance",
    "content_generation",
    "data_transformation",
}
IMPLEMENTATION_MODES = {"deterministic", "model", "prompt", "hybrid"}
DECISION_AUTHORITIES = {
    "inform",
    "recommend",
    "assess_claim",
    "publish_bounded_output",
    "execute_bounded_action",
}
AUTONOMY_LEVELS = {
    "advisory_only",
    "human_approval_required",
    "deterministic_gate",
    "bounded_autonomous",
}
RISK_LEVELS = {"low", "medium", "high", "critical"}
MODEL_ROUTE_MODES = {"fixed", "dynamic", "not_applicable"}
EVALUATION_READINESS = {
    "not_configured",
    "schema_only",
    "needs_seed_cases",
    "baseline_ready",
    "regression_ready",
}
PROVENANCE_ORIGINS = {"authored", "extracted", "generated"}

_TOP_LEVEL_FIELDS = {
    "schema_version",
    "name",
    "version",
    "purpose",
    "capability_kind",
    "task_type",
    "triggers",
    "not_for",
    "contracts",
    "called_by",
    "owner",
    "risk_level",
    "human_review",
    "model_route",
    "evaluation",
    "provenance",
    "capability_type",
    "implementation_mode",
    "decision_authority",
    "autonomy_level",
}
_COMMON_REQUIRED_FIELDS = _TOP_LEVEL_FIELDS - {
    "capability_kind",
    "model_route",
    "capability_type",
    "implementation_mode",
    "decision_authority",
    "autonomy_level",
}
_LEGACY_FIELDS = {"capability_kind", "model_route"}
_CANONICAL_FIELDS = {
    "capability_type",
    "implementation_mode",
    "decision_authority",
    "autonomy_level",
}
_NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_VERSION_RE = re.compile(r"^v?[0-9]+(?:\.[0-9]+){0,2}(?:[-+][0-9A-Za-z.-]+)?$")
_TASK_TYPE_RE = re.compile(r"^[a-z0-9]+(?:[_-][a-z0-9]+)*$")
_SCHEMA_REF_RE = re.compile(r"^[^\s]+\.json(?:#.*)?$")
_SOURCE_HASH_RE = re.compile(r"^sha256:[0-9a-f]{64}$")


def _object(value: Any, path: str, errors: list[str]) -> Mapping[str, Any] | None:
    if not isinstance(value, Mapping):
        errors.append(f"{path} must be an object")
        return None
    return value


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


def _string(value: Any, path: str, errors: list[str], *, minimum: int = 1) -> str | None:
    if not isinstance(value, str) or len(value) < minimum:
        errors.append(f"{path} must be a string with at least {minimum} characters")
        return None
    return value


def _string_list(
    value: Any,
    path: str,
    errors: list[str],
    *,
    minimum: int = 0,
) -> list[str] | None:
    if not isinstance(value, list):
        errors.append(f"{path} must be an array")
        return None
    if len(value) < minimum:
        errors.append(f"{path} must contain at least {minimum} item(s)")
    if any(not isinstance(item, str) or not item for item in value):
        errors.append(f"{path} must contain only non-empty strings")
        return None
    if len(set(value)) != len(value):
        errors.append(f"{path} must contain unique items")
    return value


def _enum(value: Any, path: str, allowed: set[str], errors: list[str]) -> str | None:
    if not isinstance(value, str) or value not in allowed:
        errors.append(f"{path} must be one of {sorted(allowed)}")
        return None
    return value


def validate_capability_manifest(manifest: Mapping[str, Any]) -> list[str]:
    """Return deterministic contract violations for one capability manifest."""

    errors: list[str] = []
    uses_legacy = bool(set(manifest) & _LEGACY_FIELDS)
    uses_canonical = bool(set(manifest) & _CANONICAL_FIELDS)
    if uses_legacy and uses_canonical:
        errors.append(
            "$ must use either legacy capability_kind/model_route fields or "
            "canonical AI capability fields, not both"
        )
    required = _COMMON_REQUIRED_FIELDS | (
        _LEGACY_FIELDS if uses_legacy and not uses_canonical else _CANONICAL_FIELDS
    )
    if not uses_legacy and not uses_canonical:
        required |= _CANONICAL_FIELDS
    _check_fields(
        manifest,
        path="$",
        required=required,
        allowed=_TOP_LEVEL_FIELDS,
        errors=errors,
    )

    if manifest.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"$.schema_version must equal {SCHEMA_VERSION!r}")

    name = _string(manifest.get("name"), "$.name", errors)
    if name and not _NAME_RE.fullmatch(name):
        errors.append("$.name must use kebab-case")

    version = _string(manifest.get("version"), "$.version", errors)
    if version and not _VERSION_RE.fullmatch(version):
        errors.append("$.version must be a supported numeric version")

    _string(manifest.get("purpose"), "$.purpose", errors, minimum=10)
    if uses_legacy and not uses_canonical:
        _enum(manifest.get("capability_kind"), "$.capability_kind", CAPABILITY_KINDS, errors)
    else:
        _enum(
            manifest.get("capability_type"),
            "$.capability_type",
            CAPABILITY_TYPES,
            errors,
        )
        implementation_mode = _enum(
            manifest.get("implementation_mode"),
            "$.implementation_mode",
            IMPLEMENTATION_MODES,
            errors,
        )
        _enum(
            manifest.get("decision_authority"),
            "$.decision_authority",
            DECISION_AUTHORITIES,
            errors,
        )
        _enum(
            manifest.get("autonomy_level"),
            "$.autonomy_level",
            AUTONOMY_LEVELS,
            errors,
        )

    task_type = _string(manifest.get("task_type"), "$.task_type", errors)
    if task_type and not _TASK_TYPE_RE.fullmatch(task_type):
        errors.append("$.task_type must use lowercase words separated by '_' or '-'")

    _string_list(manifest.get("triggers"), "$.triggers", errors, minimum=1)
    _string_list(manifest.get("not_for"), "$.not_for", errors)
    _string_list(manifest.get("called_by"), "$.called_by", errors)
    _string(manifest.get("owner"), "$.owner", errors)
    risk_level = _enum(manifest.get("risk_level"), "$.risk_level", RISK_LEVELS, errors)

    contracts = _object(manifest.get("contracts"), "$.contracts", errors)
    if contracts is not None:
        fields = {"input_schema", "output_schema"}
        _check_fields(contracts, path="$.contracts", required=fields, allowed=fields, errors=errors)
        for field in sorted(fields):
            ref = _string(contracts.get(field), f"$.contracts.{field}", errors)
            if ref and not _SCHEMA_REF_RE.fullmatch(ref):
                errors.append(f"$.contracts.{field} must reference a JSON schema")

    human_review = _object(manifest.get("human_review"), "$.human_review", errors)
    if human_review is not None:
        required = {"required", "stages"}
        allowed = required | {"reason"}
        _check_fields(human_review, path="$.human_review", required=required, allowed=allowed, errors=errors)
        review_required = human_review.get("required")
        if not isinstance(review_required, bool):
            errors.append("$.human_review.required must be a boolean")
            review_required = None
        stages = _string_list(human_review.get("stages"), "$.human_review.stages", errors)
        if review_required is True:
            if stages is not None and not stages:
                errors.append("$.human_review.stages must not be empty when review is required")
            _string(human_review.get("reason"), "$.human_review.reason", errors, minimum=10)
        elif review_required is False and stages:
            errors.append("$.human_review.stages must be empty when review is not required")
        if risk_level in {"high", "critical"} and review_required is not True:
            errors.append("$.human_review.required must be true for high or critical risk")

    model_route = None
    if uses_legacy and not uses_canonical:
        model_route = _object(manifest.get("model_route"), "$.model_route", errors)
    if model_route is not None:
        required = {"mode"}
        allowed = required | {"route_ref"}
        _check_fields(model_route, path="$.model_route", required=required, allowed=allowed, errors=errors)
        mode = _enum(model_route.get("mode"), "$.model_route.mode", MODEL_ROUTE_MODES, errors)
        route_ref = model_route.get("route_ref")
        if mode in {"fixed", "dynamic"}:
            _string(route_ref, "$.model_route.route_ref", errors)
        elif mode == "not_applicable" and route_ref is not None:
            errors.append("$.model_route.route_ref is not allowed when mode is not_applicable")

    if (
        not uses_legacy
        and manifest.get("autonomy_level") == "bounded_autonomous"
        and manifest.get("decision_authority") == "execute_bounded_action"
        and risk_level in {"high", "critical"}
    ):
        errors.append(
            "$.autonomy_level bounded_autonomous execution is not allowed for "
            "high or critical risk"
        )

    evaluation = _object(manifest.get("evaluation"), "$.evaluation", errors)
    if evaluation is not None:
        fields = {"readiness", "evidence_refs"}
        _check_fields(evaluation, path="$.evaluation", required=fields, allowed=fields, errors=errors)
        readiness = _enum(
            evaluation.get("readiness"),
            "$.evaluation.readiness",
            EVALUATION_READINESS,
            errors,
        )
        evidence_refs = _string_list(
            evaluation.get("evidence_refs"),
            "$.evaluation.evidence_refs",
            errors,
        )
        if readiness in {"baseline_ready", "regression_ready"} and evidence_refs == []:
            errors.append(f"$.evaluation.evidence_refs must not be empty for {readiness}")

    provenance = _object(manifest.get("provenance"), "$.provenance", errors)
    if provenance is not None:
        required = {"origin", "source_refs"}
        allowed = required | {"source_hash"}
        _check_fields(provenance, path="$.provenance", required=required, allowed=allowed, errors=errors)
        _enum(provenance.get("origin"), "$.provenance.origin", PROVENANCE_ORIGINS, errors)
        _string_list(provenance.get("source_refs"), "$.provenance.source_refs", errors, minimum=1)
        source_hash = provenance.get("source_hash")
        if source_hash is not None:
            source_hash = _string(source_hash, "$.provenance.source_hash", errors)
            if source_hash and not _SOURCE_HASH_RE.fullmatch(source_hash):
                errors.append("$.provenance.source_hash must be a lowercase sha256 digest")

    return errors


def load_capability_manifest(path: Path) -> Mapping[str, Any]:
    """Load a capability manifest and require a JSON object at the root."""

    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError("capability manifest root must be an object")
    return payload
