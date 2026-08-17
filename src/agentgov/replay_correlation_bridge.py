"""Pure replay-reservation lifecycle and Harness correlation bridge validation."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from typing import Any

from agentgov.harness_contract import (
    HARNESS_CONTRACT,
    HARNESS_SCHEMA_VERSION,
    validate_harness_run_document,
)
from agentgov.path_policy import scope_path_error
from agentgov.replay_preflight import AUTHORITY_BOUNDARY
from agentgov.replay_reservation import (
    REPLAY_RESERVATION_MARKER_CONTRACT,
    REPLAY_RESERVATION_SCHEMA_VERSION,
    validate_replay_reservation_marker,
)


REPLAY_CORRELATION_BRIDGE_CONTRACT = "agentgov.replay-correlation-bridge"
REPLAY_CORRELATION_BRIDGE_SCHEMA_VERSION = "1.0"
REPLAY_CORRELATION_BRIDGE_STATES = {
    "reserved",
    "consumed",
    "invalidated",
    "unavailable",
}
HARNESS_CORRELATION_FIELD = "host.repository_correlation"

_BRIDGE_ID_RE = re.compile(r"^rcb-[0-9a-f]{16}$")
_RESERVATION_ID_RE = re.compile(r"^rrv-[0-9a-f]{16}$")
_CORRELATION_ID_RE = re.compile(r"^rpf-[0-9a-f]{16}$")
_HARNESS_RUN_ID_RE = re.compile(r"^hrn-[0-9a-f]{16}$")
_SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_REASON_CODE_RE = re.compile(r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$")

PRIVACY_BOUNDARY = {
    "contains_raw_prompt": False,
    "contains_transcript": False,
    "contains_model_output": False,
    "contains_tool_input_output": False,
    "contains_source_content": False,
    "contains_credentials": False,
    "contains_absolute_paths": False,
    "contains_unbounded_payloads": False,
}

CLAIM_LIMITS = {
    "proves_replay_authorized": False,
    "proves_replay_launched": False,
    "proves_replay_completed": False,
    "proves_product_effectiveness": False,
}


def replay_reservation_marker_digest(marker: Mapping[str, Any]) -> str:
    """Return the digest used by the create-only reservation result contract."""

    payload = (json.dumps(marker, indent=2, sort_keys=True) + "\n").encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _exact_mapping(
    value: Any,
    *,
    path: str,
    fields: set[str],
    errors: list[str],
) -> Mapping[str, Any] | None:
    if not isinstance(value, Mapping):
        errors.append(f"{path} must be an object")
        return None
    missing = fields - set(value)
    extra = set(value) - fields
    for field in sorted(missing):
        errors.append(f"{path}.{field} is required")
    for field in sorted(extra):
        errors.append(f"{path}.{field} is not allowed")
    if missing or extra:
        return None
    return value


def _safe_evidence_ref(value: Any, *, path: str, errors: list[str]) -> None:
    if not isinstance(value, str) or not value or len(value) > 400:
        errors.append(f"{path} must be a non-empty repository-relative path")
        return
    problem = scope_path_error(value)
    if problem:
        errors.append(f"{path} {problem}")


def validate_replay_correlation_bridge_document(document: Any) -> list[str]:
    """Validate the strict bridge document without consulting external evidence."""

    errors: list[str] = []
    fields = {
        "contract",
        "schema_version",
        "bridge_id",
        "correlation_id",
        "state",
        "reservation",
        "harness_mapping",
        "reason_code",
        "privacy_boundary",
        "claim_limits",
        "authority_boundary",
    }
    root = _exact_mapping(document, path="$", fields=fields, errors=errors)
    if root is None:
        return errors

    if root["contract"] != REPLAY_CORRELATION_BRIDGE_CONTRACT:
        errors.append(
            f"$.contract must equal {REPLAY_CORRELATION_BRIDGE_CONTRACT!r}"
        )
    if root["schema_version"] != REPLAY_CORRELATION_BRIDGE_SCHEMA_VERSION:
        errors.append("$.schema_version must equal '1.0'")
    bridge_id = root["bridge_id"]
    if not isinstance(bridge_id, str) or _BRIDGE_ID_RE.fullmatch(bridge_id) is None:
        errors.append("$.bridge_id must match ^rcb-[0-9a-f]{16}$")
    correlation_id = root["correlation_id"]
    if (
        not isinstance(correlation_id, str)
        or _CORRELATION_ID_RE.fullmatch(correlation_id) is None
    ):
        errors.append("$.correlation_id must match ^rpf-[0-9a-f]{16}$")
    state = root["state"]
    state_valid = (
        isinstance(state, str) and state in REPLAY_CORRELATION_BRIDGE_STATES
    )
    if not state_valid:
        errors.append(
            "$.state must be one of reserved, consumed, invalidated, unavailable"
        )

    reservation = _exact_mapping(
        root["reservation"],
        path="$.reservation",
        fields={
            "contract",
            "schema_version",
            "reservation_id",
            "marker_path",
            "marker_digest",
        },
        errors=errors,
    )
    if reservation is not None:
        if reservation["contract"] != REPLAY_RESERVATION_MARKER_CONTRACT:
            errors.append(
                "$.reservation.contract must name the reservation marker contract"
            )
        if reservation["schema_version"] != REPLAY_RESERVATION_SCHEMA_VERSION:
            errors.append("$.reservation.schema_version must equal '1.0'")
        reservation_id = reservation["reservation_id"]
        if (
            not isinstance(reservation_id, str)
            or _RESERVATION_ID_RE.fullmatch(reservation_id) is None
        ):
            errors.append(
                "$.reservation.reservation_id must match ^rrv-[0-9a-f]{16}$"
            )
        marker_path = reservation["marker_path"]
        _safe_evidence_ref(
            marker_path, path="$.reservation.marker_path", errors=errors
        )
        expected_suffix = (
            f"/{correlation_id}.json" if isinstance(correlation_id, str) else ""
        )
        if not isinstance(marker_path, str) or not marker_path.endswith(expected_suffix):
            errors.append(
                "$.reservation.marker_path must end with the bridge correlation marker"
            )
        marker_digest = reservation["marker_digest"]
        if (
            not isinstance(marker_digest, str)
            or _SHA256_RE.fullmatch(marker_digest) is None
        ):
            errors.append("$.reservation.marker_digest must be a SHA-256 digest")

    mapping = _exact_mapping(
        root["harness_mapping"],
        path="$.harness_mapping",
        fields={"contract", "schema_version", "field", "expected_value", "run_id", "evidence_ref"},
        errors=errors,
    )
    if mapping is not None:
        if mapping["contract"] != HARNESS_CONTRACT:
            errors.append("$.harness_mapping.contract must name Harness Contract v1")
        if mapping["schema_version"] != HARNESS_SCHEMA_VERSION:
            errors.append("$.harness_mapping.schema_version must equal '1.0'")
        if mapping["field"] != HARNESS_CORRELATION_FIELD:
            errors.append(
                "$.harness_mapping.field must equal 'host.repository_correlation'"
            )
        if mapping["expected_value"] != correlation_id:
            errors.append(
                "$.harness_mapping.expected_value must equal $.correlation_id"
            )
        run_id = mapping["run_id"]
        evidence_ref = mapping["evidence_ref"]
        if state == "consumed":
            if (
                not isinstance(run_id, str)
                or _HARNESS_RUN_ID_RE.fullmatch(run_id) is None
            ):
                errors.append(
                    "$.harness_mapping.run_id must name one Harness run when consumed"
                )
            _safe_evidence_ref(
                evidence_ref,
                path="$.harness_mapping.evidence_ref",
                errors=errors,
            )
        elif state_valid:
            if run_id is not None:
                errors.append(
                    "$.harness_mapping.run_id must be null unless state is consumed"
                )
            if evidence_ref is not None:
                errors.append(
                    "$.harness_mapping.evidence_ref must be null unless state is consumed"
                )

    reason_code = root["reason_code"]
    if state_valid and state in {"reserved", "consumed"}:
        if reason_code is not None:
            errors.append("$.reason_code must be null for reserved or consumed state")
    elif state_valid and (
        not isinstance(reason_code, str)
        or _REASON_CODE_RE.fullmatch(reason_code) is None
    ):
        errors.append(
            "$.reason_code must be a normalized identifier for invalidated or unavailable state"
        )

    if root["privacy_boundary"] != PRIVACY_BOUNDARY:
        errors.append("$.privacy_boundary must deny every sensitive-content field")
    if root["claim_limits"] != CLAIM_LIMITS:
        errors.append("$.claim_limits must deny every replay and effectiveness claim")
    if root["authority_boundary"] != AUTHORITY_BOUNDARY:
        errors.append("$.authority_boundary must deny every replay and action authority")
    return errors


def validate_replay_correlation_bridge(
    document: Any,
    *,
    reservation_marker: Mapping[str, Any] | None = None,
    harness_run: Mapping[str, Any] | None = None,
) -> list[str]:
    """Validate a bridge and any lifecycle-required external evidence mappings."""

    errors = validate_replay_correlation_bridge_document(document)
    if errors or not isinstance(document, Mapping):
        return errors
    state = document["state"]
    reservation = document["reservation"]
    mapping = document["harness_mapping"]

    if state in {"reserved", "consumed"} and reservation_marker is None:
        errors.append(
            "$ reservation_marker evidence is required for reserved or consumed state"
        )
    if reservation_marker is not None:
        marker_errors = validate_replay_reservation_marker(reservation_marker)
        errors.extend(f"$reservation_marker {item}" for item in marker_errors)
        if not marker_errors:
            comparisons = (
                ("$.reservation.reservation_id", reservation["reservation_id"], "reservation_id"),
                ("$.correlation_id", document["correlation_id"], "correlation_id"),
                ("$.reservation.marker_path", reservation["marker_path"], "marker_path"),
            )
            for path, bridge_value, marker_field in comparisons:
                if bridge_value != reservation_marker[marker_field]:
                    errors.append(
                        f"{path} must match reservation marker evidence"
                    )
            if reservation["marker_digest"] != replay_reservation_marker_digest(
                reservation_marker
            ):
                errors.append(
                    "$.reservation.marker_digest must match reservation marker evidence"
                )

    if state == "consumed" and harness_run is None:
        errors.append("$ harness_run evidence is required for consumed state")
    if state != "consumed" and harness_run is not None:
        errors.append("$ harness_run evidence is allowed only for consumed state")
    if harness_run is not None:
        harness_errors = validate_harness_run_document(harness_run)
        errors.extend(f"$harness_run {item}" for item in harness_errors)
        if not harness_errors:
            if mapping["run_id"] != harness_run["run_id"]:
                errors.append(
                    "$.harness_mapping.run_id must match Harness run evidence"
                )
            observed = harness_run["host"]["repository_correlation"]
            if mapping["expected_value"] != observed:
                errors.append(
                    "$.harness_mapping.expected_value must match Harness host.repository_correlation"
                )
    return errors
