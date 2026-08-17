"""Read-only replay-claim inspection and immutable recovery evidence."""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
from collections.abc import Callable, Mapping
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from agentgov.path_policy import scope_path_error
from agentgov.replay_claim import validate_replay_claim
from agentgov.replay_correlation_bridge import replay_reservation_marker_digest
from agentgov.replay_preflight import (
    AUTHORITY_BOUNDARY,
    REPLAY_ADAPTER_METADATA_CONTRACT,
    REPLAY_PREFLIGHT_SCHEMA_VERSION,
)
from agentgov.replay_reservation import validate_replay_reservation_marker


REPLAY_CLAIM_RECOVERY_PLAN_CONTRACT = "agentgov.replay-claim-recovery-plan"
REPLAY_CLAIM_RECOVERY_INSPECTION_CONTRACT = (
    "agentgov.replay-claim-recovery-inspection"
)
REPLAY_CLAIM_RECOVERY_MARKER_CONTRACT = "agentgov.replay-claim-recovery"
REPLAY_CLAIM_RECOVERY_PREVIEW_CONTRACT = "agentgov.replay-claim-recovery-preview"
REPLAY_CLAIM_RECOVERY_RESULT_CONTRACT = "agentgov.replay-claim-recovery-result"
REPLAY_CLAIM_RECOVERY_SCHEMA_VERSION = "1.0"
MAX_CLAIM_EVIDENCE_BYTES = 1_048_576

_RECOVERY_ID_RE = re.compile(r"^rcr-[0-9a-f]{16}$")
_RESERVATION_ID_RE = re.compile(r"^rrv-[0-9a-f]{16}$")
_CORRELATION_ID_RE = re.compile(r"^rpf-[0-9a-f]{16}$")
_SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_GIT_SHA_RE = re.compile(r"^[0-9a-f]{40,64}$")
_NORMALIZED_ID_RE = re.compile(r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$")
_VERSION_RE = re.compile(r"^[0-9]+(?:\.[0-9]+){1,3}(?:(?:a|b|rc)[0-9]+)?$")
_PROTOCOL_RE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")


class ReplayClaimRecoveryError(ValueError):
    """Recovery input or local state cannot be used safely."""


class ReplayClaimRecoveryPlanError(ReplayClaimRecoveryError):
    """The recovery plan is malformed or unsafe."""


class ReplayClaimRecoveryConflictError(ReplayClaimRecoveryError):
    """A recovery marker already exists or won the create race."""


class ReplayClaimRecoveryStaleError(ReplayClaimRecoveryError):
    """The reviewed recovery preview no longer matches local facts."""


class _DuplicateJsonKeyError(ValueError):
    """A strict JSON object contains a repeated member name."""


class ClaimEvidenceClassification(str, Enum):
    VALID = "VALID"
    PARTIAL = "PARTIAL"
    MALFORMED = "MALFORMED"
    MISSING = "MISSING"
    INCONSISTENT = "INCONSISTENT"
    UNKNOWN = "UNKNOWN"
    RECOVERED = "RECOVERED"


class RecoveryPreviewStatus(str, Enum):
    READY = "READY_TO_RECOVER"
    BLOCKED = "BLOCKED"
    UNKNOWN = "UNKNOWN"
    ALREADY_RECOVERED = "ALREADY_RECOVERED"


class RecoveryFindingStatus(str, Enum):
    PASS = "PASS"
    BLOCKED = "BLOCKED"
    UNKNOWN = "UNKNOWN"


class ReplayClaimOwnership(str, Enum):
    ACTIVE = "ACTIVE"
    RECOVERED = "RECOVERED"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class RecoveryFinding:
    status: RecoveryFindingStatus
    check_id: str
    reason_code: str | None
    message: str


@dataclass(frozen=True)
class ReplayClaimRecoveryInspection:
    contract: str
    schema_version: str
    classification: ClaimEvidenceClassification
    correlation_id: str
    claim_path: str
    observed_claim_digest: str | None
    observed_byte_length: int | None
    recovery_path: str
    findings: tuple[RecoveryFinding, ...]
    reason_codes: tuple[str, ...]
    known_limits: tuple[str, ...]
    authority_boundary: Mapping[str, bool]


@dataclass(frozen=True)
class ReplayClaimRecoveryPreview:
    contract: str
    schema_version: str
    status: RecoveryPreviewStatus
    inspection: ReplayClaimRecoveryInspection
    recovery: Mapping[str, Any] | None
    authority_boundary: Mapping[str, bool]


@dataclass(frozen=True)
class ReplayClaimRecoveryResult:
    contract: str
    schema_version: str
    status: str
    correlation_id: str
    recovery_path: str
    recovery_digest: str
    effect: Mapping[str, bool]
    authority_boundary: Mapping[str, bool]


def _canonical_digest(document: Mapping[str, Any]) -> str:
    encoded = json.dumps(
        document,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _raw_digest(content: bytes) -> str:
    return "sha256:" + hashlib.sha256(content).hexdigest()


def _recovery_bytes(recovery: Mapping[str, Any]) -> bytes:
    return (json.dumps(recovery, indent=2, sort_keys=True) + "\n").encode("utf-8")


def replay_claim_recovery_digest(recovery: Mapping[str, Any]) -> str:
    """Return the digest of one canonical recovery marker payload."""

    return _raw_digest(_recovery_bytes(recovery))


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
    return None if missing or extra else value


def _relative_path(value: Any, *, path: str, errors: list[str]) -> str | None:
    if not isinstance(value, str) or not value or len(value) > 400:
        errors.append(f"{path} must be a non-empty repository-relative path")
        return None
    problem = scope_path_error(value)
    if problem:
        errors.append(f"{path} {problem}")
        return None
    return value


def _adapter_errors(value: Any, *, path: str) -> list[str]:
    errors: list[str] = []
    adapter = _exact_mapping(
        value,
        path=path,
        fields={"adapter_id", "adapter_version", "protocol_version"},
        errors=errors,
    )
    if adapter is None:
        return errors
    if (
        not isinstance(adapter["adapter_id"], str)
        or not _NORMALIZED_ID_RE.fullmatch(adapter["adapter_id"])
        or not isinstance(adapter["adapter_version"], str)
        or not _VERSION_RE.fullmatch(adapter["adapter_version"])
        or not isinstance(adapter["protocol_version"], str)
        or not _PROTOCOL_RE.fullmatch(adapter["protocol_version"])
    ):
        errors.append(f"{path} contains an invalid identity or protocol field")
    return errors


def validate_replay_claim_recovery_plan(document: Any) -> list[str]:
    """Validate one strict recovery plan without repository access."""

    errors: list[str] = []
    root = _exact_mapping(
        document,
        path="$",
        fields={
            "contract",
            "schema_version",
            "correlation_id",
            "reservation",
            "claim",
            "recovery",
            "adapter",
            "authority_boundary",
        },
        errors=errors,
    )
    if root is None:
        return errors
    if root["contract"] != REPLAY_CLAIM_RECOVERY_PLAN_CONTRACT:
        errors.append(
            f"$.contract must equal {REPLAY_CLAIM_RECOVERY_PLAN_CONTRACT!r}"
        )
    if root["schema_version"] != REPLAY_CLAIM_RECOVERY_SCHEMA_VERSION:
        errors.append("$.schema_version must equal '1.0'")
    correlation = root["correlation_id"]
    if not isinstance(correlation, str) or not _CORRELATION_ID_RE.fullmatch(
        correlation
    ):
        errors.append("$.correlation_id must match ^rpf-[0-9a-f]{16}$")
    suffix = f"/{correlation}.json" if isinstance(correlation, str) else ""

    reservation = _exact_mapping(
        root["reservation"],
        path="$.reservation",
        fields={"marker_path", "marker_digest"},
        errors=errors,
    )
    if reservation is not None:
        path = _relative_path(
            reservation["marker_path"],
            path="$.reservation.marker_path",
            errors=errors,
        )
        if path is not None and not path.endswith(suffix):
            errors.append("$.reservation.marker_path must end with the correlation marker")
        if not isinstance(reservation["marker_digest"], str) or not _SHA256_RE.fullmatch(
            reservation["marker_digest"]
        ):
            errors.append("$.reservation.marker_digest must be a SHA-256 digest")

    claim = _exact_mapping(
        root["claim"], path="$.claim", fields={"marker_path"}, errors=errors
    )
    if claim is not None:
        path = _relative_path(
            claim["marker_path"], path="$.claim.marker_path", errors=errors
        )
        if path is not None and not path.endswith(suffix):
            errors.append("$.claim.marker_path must end with the correlation marker")

    recovery = _exact_mapping(
        root["recovery"],
        path="$.recovery",
        fields={"registry_directory", "recovered_by", "reason_code"},
        errors=errors,
    )
    if recovery is not None:
        _relative_path(
            recovery["registry_directory"],
            path="$.recovery.registry_directory",
            errors=errors,
        )
        for field in ("recovered_by", "reason_code"):
            value = recovery[field]
            if not isinstance(value, str) or not _NORMALIZED_ID_RE.fullmatch(value):
                errors.append(f"$.recovery.{field} must be a normalized identifier")

    adapter = _exact_mapping(
        root["adapter"], path="$.adapter", fields={"metadata_path"}, errors=errors
    )
    if adapter is not None:
        _relative_path(
            adapter["metadata_path"], path="$.adapter.metadata_path", errors=errors
        )
    if not isinstance(root["authority_boundary"], Mapping) or dict(
        root["authority_boundary"]
    ) != AUTHORITY_BOUNDARY:
        errors.append("$.authority_boundary must deny every replay and action authority")
    if (
        isinstance(correlation, str)
        and reservation is not None
        and claim is not None
        and recovery is not None
        and all(
            isinstance(item, str)
            for item in (
                reservation["marker_path"],
                claim["marker_path"],
                recovery["registry_directory"],
            )
        )
    ):
        recovery_path = f"{recovery['registry_directory']}/{correlation}.json"
        evidence_paths = {
            reservation["marker_path"],
            claim["marker_path"],
            recovery_path,
        }
        if len(evidence_paths) != 3:
            errors.append("reservation, claim, and recovery marker paths must be distinct")
    return errors


def validate_replay_claim_recovery_marker(document: Any) -> list[str]:
    """Validate one strict recovery marker without external evidence."""

    errors: list[str] = []
    root = _exact_mapping(
        document,
        path="$",
        fields={
            "contract",
            "schema_version",
            "recovery_id",
            "correlation_id",
            "recovery_path",
            "reservation",
            "abandoned_claim",
            "repository_head",
            "adapter",
            "recovered_by",
            "reason_code",
            "status",
            "authority_boundary",
        },
        errors=errors,
    )
    if root is None:
        return errors
    if root["contract"] != REPLAY_CLAIM_RECOVERY_MARKER_CONTRACT:
        errors.append(
            f"$.contract must equal {REPLAY_CLAIM_RECOVERY_MARKER_CONTRACT!r}"
        )
    if root["schema_version"] != REPLAY_CLAIM_RECOVERY_SCHEMA_VERSION:
        errors.append("$.schema_version must equal '1.0'")
    if not isinstance(root["recovery_id"], str) or not _RECOVERY_ID_RE.fullmatch(
        root["recovery_id"]
    ):
        errors.append("$.recovery_id must match ^rcr-[0-9a-f]{16}$")
    correlation = root["correlation_id"]
    if not isinstance(correlation, str) or not _CORRELATION_ID_RE.fullmatch(
        correlation
    ):
        errors.append("$.correlation_id must match ^rpf-[0-9a-f]{16}$")
    suffix = f"/{correlation}.json" if isinstance(correlation, str) else ""
    recovery_path = _relative_path(
        root["recovery_path"], path="$.recovery_path", errors=errors
    )
    if recovery_path is not None and not recovery_path.endswith(suffix):
        errors.append("$.recovery_path must end with the recovered correlation marker")

    reservation = _exact_mapping(
        root["reservation"],
        path="$.reservation",
        fields={"reservation_id", "marker_path", "marker_digest"},
        errors=errors,
    )
    if reservation is not None:
        if not isinstance(reservation["reservation_id"], str) or not _RESERVATION_ID_RE.fullmatch(
            reservation["reservation_id"]
        ):
            errors.append("$.reservation.reservation_id must match ^rrv-[0-9a-f]{16}$")
        marker_path = _relative_path(
            reservation["marker_path"],
            path="$.reservation.marker_path",
            errors=errors,
        )
        if marker_path is not None and not marker_path.endswith(suffix):
            errors.append("$.reservation.marker_path must end with the correlation marker")
        if not isinstance(reservation["marker_digest"], str) or not _SHA256_RE.fullmatch(
            reservation["marker_digest"]
        ):
            errors.append("$.reservation.marker_digest must be a SHA-256 digest")

    abandoned = _exact_mapping(
        root["abandoned_claim"],
        path="$.abandoned_claim",
        fields={"marker_path", "marker_digest", "byte_length", "classification"},
        errors=errors,
    )
    if abandoned is not None:
        marker_path = _relative_path(
            abandoned["marker_path"],
            path="$.abandoned_claim.marker_path",
            errors=errors,
        )
        if marker_path is not None and not marker_path.endswith(suffix):
            errors.append("$.abandoned_claim.marker_path must end with the correlation marker")
        if not isinstance(abandoned["marker_digest"], str) or not _SHA256_RE.fullmatch(
            abandoned["marker_digest"]
        ):
            errors.append("$.abandoned_claim.marker_digest must be a SHA-256 digest")
        byte_length = abandoned["byte_length"]
        if (
            not isinstance(byte_length, int)
            or isinstance(byte_length, bool)
            or not 0 <= byte_length <= MAX_CLAIM_EVIDENCE_BYTES
        ):
            errors.append("$.abandoned_claim.byte_length must be a bounded integer")
        if abandoned["classification"] not in (
            ClaimEvidenceClassification.VALID.value,
            ClaimEvidenceClassification.PARTIAL.value,
            ClaimEvidenceClassification.MALFORMED.value,
        ):
            errors.append(
                "$.abandoned_claim.classification must be VALID, PARTIAL, or MALFORMED"
            )

    if not isinstance(root["repository_head"], str) or not _GIT_SHA_RE.fullmatch(
        root["repository_head"]
    ):
        errors.append("$.repository_head must be a lowercase Git SHA")
    errors.extend(_adapter_errors(root["adapter"], path="$.adapter"))
    for field in ("recovered_by", "reason_code"):
        value = root[field]
        if not isinstance(value, str) or not _NORMALIZED_ID_RE.fullmatch(value):
            errors.append(f"$.{field} must be a normalized identifier")
    if root["status"] != "recovered":
        errors.append("$.status must equal 'recovered'")
    if not isinstance(root["authority_boundary"], Mapping) or dict(
        root["authority_boundary"]
    ) != AUTHORITY_BOUNDARY:
        errors.append("$.authority_boundary must deny every replay and action authority")
    if (
        reservation is not None
        and abandoned is not None
        and all(
            isinstance(item, str)
            for item in (
                reservation["marker_path"],
                abandoned["marker_path"],
                root["recovery_path"],
            )
        )
    ):
        evidence_paths = {
            reservation["marker_path"],
            abandoned["marker_path"],
            root["recovery_path"],
        }
        if len(evidence_paths) != 3:
            errors.append("reservation, claim, and recovery marker paths must be distinct")
    return errors


def _json_classification(content: bytes) -> tuple[ClaimEvidenceClassification, Any]:
    if not content.strip():
        return ClaimEvidenceClassification.PARTIAL, None
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        return ClaimEvidenceClassification.MALFORMED, None
    try:
        return ClaimEvidenceClassification.VALID, json.loads(
            text, object_pairs_hook=_unique_object
        )
    except json.JSONDecodeError as exc:
        partial = exc.pos >= max(len(text) - 1, 0) or "Unterminated" in exc.msg
        return (
            ClaimEvidenceClassification.PARTIAL
            if partial
            else ClaimEvidenceClassification.MALFORMED,
            None,
        )
    except _DuplicateJsonKeyError:
        return ClaimEvidenceClassification.MALFORMED, None


def classify_replay_claim_bytes(
    content: bytes,
    *,
    claim_path: str,
    correlation_id: str,
    reservation_marker: Mapping[str, Any],
) -> ClaimEvidenceClassification:
    """Classify bounded claim bytes using immutable reservation evidence."""

    if len(content) > MAX_CLAIM_EVIDENCE_BYTES:
        return ClaimEvidenceClassification.UNKNOWN
    syntax, document = _json_classification(content)
    if syntax is not ClaimEvidenceClassification.VALID:
        return syntax
    if not isinstance(document, Mapping):
        return ClaimEvidenceClassification.MALFORMED
    errors = validate_replay_claim(document, reservation_marker=reservation_marker)
    if (
        errors
        or document.get("correlation_id") != correlation_id
        or document.get("claim_path") != claim_path
    ):
        return ClaimEvidenceClassification.INCONSISTENT
    return ClaimEvidenceClassification.VALID


def validate_replay_claim_recovery(
    document: Any,
    *,
    reservation_marker: Mapping[str, Any] | None = None,
    claim_bytes: bytes | None = None,
) -> list[str]:
    """Bind one recovery marker to its reservation and exact raw claim bytes."""

    errors = validate_replay_claim_recovery_marker(document)
    if errors or not isinstance(document, Mapping):
        return errors
    if reservation_marker is None:
        errors.append("$ reservation_marker evidence is required")
        return errors
    marker_errors = validate_replay_reservation_marker(reservation_marker)
    errors.extend(f"$reservation_marker {item}" for item in marker_errors)
    if marker_errors:
        return errors
    if claim_bytes is None:
        errors.append("$ claim_bytes evidence is required")
        return errors
    if len(claim_bytes) > MAX_CLAIM_EVIDENCE_BYTES:
        errors.append("$ claim_bytes exceeds the bounded evidence limit")
        return errors
    if document["correlation_id"] != reservation_marker["correlation_id"]:
        errors.append("$.correlation_id must match reservation marker evidence")
    if document["reservation"]["reservation_id"] != reservation_marker["reservation_id"]:
        errors.append("$.reservation.reservation_id must match reservation marker evidence")
    if document["reservation"]["marker_path"] != reservation_marker["marker_path"]:
        errors.append("$.reservation.marker_path must match reservation marker evidence")
    if document["reservation"]["marker_digest"] != replay_reservation_marker_digest(
        reservation_marker
    ):
        errors.append("$.reservation.marker_digest must match reservation marker evidence")
    abandoned = document["abandoned_claim"]
    if abandoned["marker_digest"] != _raw_digest(claim_bytes):
        errors.append("$.abandoned_claim.marker_digest must match exact claim bytes")
    if abandoned["byte_length"] != len(claim_bytes):
        errors.append("$.abandoned_claim.byte_length must match exact claim bytes")
    classification = classify_replay_claim_bytes(
        claim_bytes,
        claim_path=abandoned["marker_path"],
        correlation_id=document["correlation_id"],
        reservation_marker=reservation_marker,
    )
    if abandoned["classification"] != classification.value:
        errors.append("$.abandoned_claim.classification must match exact claim bytes")
    if document["repository_head"] != reservation_marker["preflight"]["observed_head_sha"]:
        errors.append("$.repository_head must match reservation marker evidence")
    if document["adapter"] != reservation_marker["adapter"]:
        errors.append("$.adapter must match reservation marker evidence")
    return errors


def evaluate_replay_claim_ownership(
    claim_bytes: bytes,
    *,
    recovery_marker: Mapping[str, Any] | None,
    reservation_marker: Mapping[str, Any] | None,
) -> ReplayClaimOwnership:
    """Return RECOVERED only for exact, strictly bound recovery evidence."""

    if recovery_marker is not None:
        if not validate_replay_claim_recovery(
            recovery_marker,
            reservation_marker=reservation_marker,
            claim_bytes=claim_bytes,
        ):
            return ReplayClaimOwnership.RECOVERED
        return ReplayClaimOwnership.UNKNOWN
    if reservation_marker is None or validate_replay_reservation_marker(
        reservation_marker
    ):
        return ReplayClaimOwnership.UNKNOWN
    syntax, claim = _json_classification(claim_bytes)
    if (
        syntax is ClaimEvidenceClassification.VALID
        and isinstance(claim, Mapping)
        and not validate_replay_claim(claim, reservation_marker=reservation_marker)
    ):
        return ReplayClaimOwnership.ACTIVE
    return ReplayClaimOwnership.UNKNOWN


def _load_json(path: Path, *, label: str) -> Mapping[str, Any]:
    try:
        value = json.loads(
            path.read_text(encoding="utf-8"), object_pairs_hook=_unique_object
        )
    except (OSError, UnicodeError, json.JSONDecodeError, _DuplicateJsonKeyError) as exc:
        raise ReplayClaimRecoveryPlanError(f"{label} is not readable JSON") from exc
    if not isinstance(value, Mapping):
        raise ReplayClaimRecoveryPlanError(f"{label} must be a JSON object")
    return value


def _unique_object(pairs: list[tuple[str, Any]]) -> Mapping[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateJsonKeyError(key)
        result[key] = value
    return result


def load_replay_claim_recovery_plan(path: Path) -> Mapping[str, Any]:
    document = _load_json(path, label="replay claim recovery plan")
    errors = validate_replay_claim_recovery_plan(document)
    if errors:
        raise ReplayClaimRecoveryPlanError("; ".join(errors))
    return document


def _root(repository: Path) -> Path:
    if repository.is_symlink():
        raise ReplayClaimRecoveryError("repository root must not be a symbolic link")
    if not repository.exists() or not repository.is_dir():
        raise ReplayClaimRecoveryError("repository root must be an existing directory")
    return repository.resolve()


def _inside(root: Path, relative: str) -> Path:
    return root.joinpath(*relative.split("/"))


def _has_symlink_component(root: Path, relative: str) -> bool:
    candidate = root
    for segment in relative.split("/"):
        candidate = candidate / segment
        if candidate.is_symlink():
            return True
    return False


def _git_head(root: Path) -> str:
    completed = subprocess.run(
        (
            "git",
            "-c",
            "core.quotepath=false",
            "-C",
            str(root),
            "rev-parse",
            "--show-toplevel",
            "HEAD",
        ),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=30,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if completed.returncode != 0:
        raise OSError(completed.stderr.strip() or "Git HEAD is unavailable")
    lines = completed.stdout.splitlines()
    if len(lines) != 2 or Path(lines[0]).resolve() != root:
        raise OSError("repository must be the Git worktree root")
    head = lines[1].strip()
    if not _GIT_SHA_RE.fullmatch(head):
        raise OSError("Git reported an invalid HEAD revision")
    return head


def _finding(
    status: RecoveryFindingStatus,
    check_id: str,
    message: str,
    reason_code: str | None = None,
) -> RecoveryFinding:
    return RecoveryFinding(status, check_id, reason_code, message)


def _adapter_finding(
    root: Path, relative: str, marker: Mapping[str, Any]
) -> RecoveryFinding:
    path = _inside(root, relative)
    if _has_symlink_component(root, relative) or not path.is_file():
        return _finding(
            RecoveryFindingStatus.UNKNOWN,
            "adapter:metadata",
            "local Adapter metadata is unavailable",
            "adapter_metadata_unavailable",
        )
    try:
        metadata = _load_json(path, label="Adapter metadata")
    except ReplayClaimRecoveryPlanError:
        return _finding(
            RecoveryFindingStatus.UNKNOWN,
            "adapter:metadata",
            "local Adapter metadata is invalid or unreadable",
            "adapter_metadata_invalid",
        )
    required = {
        "contract",
        "schema_version",
        "adapter_id",
        "adapter_version",
        "protocol_version",
    }
    observed = {
        "adapter_id": metadata.get("adapter_id"),
        "adapter_version": metadata.get("adapter_version"),
        "protocol_version": metadata.get("protocol_version"),
    }
    if (
        set(metadata) != required
        or metadata.get("contract") != REPLAY_ADAPTER_METADATA_CONTRACT
        or metadata.get("schema_version") != REPLAY_PREFLIGHT_SCHEMA_VERSION
        or _adapter_errors(observed, path="$.adapter")
    ):
        return _finding(
            RecoveryFindingStatus.UNKNOWN,
            "adapter:metadata",
            "local Adapter metadata does not satisfy the strict contract",
            "adapter_metadata_invalid",
        )
    if observed != marker["adapter"]:
        return _finding(
            RecoveryFindingStatus.BLOCKED,
            "adapter:identity",
            "local Adapter identity does not match the reservation",
            "adapter_mismatch",
        )
    return _finding(
        RecoveryFindingStatus.PASS,
        "adapter:identity",
        "local Adapter identity matches the reservation",
    )


def _build_recovery(
    plan: Mapping[str, Any],
    marker: Mapping[str, Any],
    claim_bytes: bytes,
    classification: ClaimEvidenceClassification,
    *,
    recovery_path: str,
    repository_head: str,
) -> Mapping[str, Any]:
    recovery = {
        "contract": REPLAY_CLAIM_RECOVERY_MARKER_CONTRACT,
        "schema_version": REPLAY_CLAIM_RECOVERY_SCHEMA_VERSION,
        "recovery_id": "rcr-" + _canonical_digest(plan).removeprefix("sha256:")[:16],
        "correlation_id": plan["correlation_id"],
        "recovery_path": recovery_path,
        "reservation": {
            "reservation_id": marker["reservation_id"],
            "marker_path": marker["marker_path"],
            "marker_digest": replay_reservation_marker_digest(marker),
        },
        "abandoned_claim": {
            "marker_path": plan["claim"]["marker_path"],
            "marker_digest": _raw_digest(claim_bytes),
            "byte_length": len(claim_bytes),
            "classification": classification.value,
        },
        "repository_head": repository_head,
        "adapter": dict(marker["adapter"]),
        "recovered_by": plan["recovery"]["recovered_by"],
        "reason_code": plan["recovery"]["reason_code"],
        "status": "recovered",
        "authority_boundary": dict(AUTHORITY_BOUNDARY),
    }
    errors = validate_replay_claim_recovery(
        recovery, reservation_marker=marker, claim_bytes=claim_bytes
    )
    if errors:
        raise ReplayClaimRecoveryError(
            "invalid derived recovery marker: " + "; ".join(errors)
        )
    return recovery


def prepare_replay_claim_recovery(
    document: Mapping[str, Any], *, repository: Path
) -> ReplayClaimRecoveryPreview:
    """Inspect exact claim evidence and prepare a recovery without writing."""

    errors = validate_replay_claim_recovery_plan(document)
    if errors:
        raise ReplayClaimRecoveryPlanError("; ".join(errors))
    root = _root(repository)
    correlation = str(document["correlation_id"])
    reservation_relative = str(document["reservation"]["marker_path"])
    claim_relative = str(document["claim"]["marker_path"])
    registry_relative = str(document["recovery"]["registry_directory"])
    adapter_relative = str(document["adapter"]["metadata_path"])
    recovery_relative = f"{registry_relative}/{correlation}.json"
    findings: list[RecoveryFinding] = []
    marker: Mapping[str, Any] | None = None
    reservation_bound = False

    reservation_path = _inside(root, reservation_relative)
    if _has_symlink_component(root, reservation_relative) or not reservation_path.is_file():
        findings.append(
            _finding(
                RecoveryFindingStatus.UNKNOWN,
                "reservation:marker",
                "reservation marker is unavailable",
                "reservation_marker_unavailable",
            )
        )
    else:
        try:
            marker = _load_json(reservation_path, label="reservation marker")
        except ReplayClaimRecoveryPlanError:
            findings.append(
                _finding(
                    RecoveryFindingStatus.UNKNOWN,
                    "reservation:marker",
                    "reservation marker is invalid or unreadable",
                    "reservation_marker_invalid",
                )
            )
        if marker is not None:
            marker_errors = validate_replay_reservation_marker(marker)
            if marker_errors:
                findings.append(
                    _finding(
                        RecoveryFindingStatus.UNKNOWN,
                        "reservation:marker",
                        "reservation marker does not satisfy its strict contract",
                        "reservation_marker_invalid",
                    )
                )
                marker = None
            elif (
                marker["correlation_id"] != correlation
                or marker["marker_path"] != reservation_relative
                or replay_reservation_marker_digest(marker)
                != document["reservation"]["marker_digest"]
            ):
                findings.append(
                    _finding(
                        RecoveryFindingStatus.BLOCKED,
                        "reservation:binding",
                        "reservation marker does not match the recovery plan",
                        "reservation_marker_mismatch",
                    )
                )
            else:
                reservation_bound = True
                findings.append(
                    _finding(
                        RecoveryFindingStatus.PASS,
                        "reservation:binding",
                        "reservation marker is valid and unchanged",
                    )
                )

    repository_head: str | None = None
    try:
        repository_head = _git_head(root)
    except (OSError, subprocess.SubprocessError):
        findings.append(
            _finding(
                RecoveryFindingStatus.UNKNOWN,
                "repository:head",
                "repository HEAD is unavailable",
                "repository_head_unavailable",
            )
        )
    if marker is not None and repository_head is not None:
        expected_head = marker["preflight"]["observed_head_sha"]
        if marker["preflight"]["expected_head_sha"] != expected_head or repository_head != expected_head:
            findings.append(
                _finding(
                    RecoveryFindingStatus.BLOCKED,
                    "repository:head",
                    "repository HEAD no longer matches the reservation",
                    "repository_head_mismatch",
                )
            )
        else:
            findings.append(
                _finding(
                    RecoveryFindingStatus.PASS,
                    "repository:head",
                    "repository HEAD matches the reservation",
                )
            )
        findings.append(_adapter_finding(root, adapter_relative, marker))

    claim_bytes: bytes | None = None
    classification = ClaimEvidenceClassification.UNKNOWN
    claim_path = _inside(root, claim_relative)
    if _has_symlink_component(root, claim_relative):
        findings.append(
            _finding(
                RecoveryFindingStatus.UNKNOWN,
                "claim:evidence",
                "claim path is unsafe",
                "claim_path_unsafe",
            )
        )
    elif not claim_path.exists():
        classification = ClaimEvidenceClassification.MISSING
        findings.append(
            _finding(
                RecoveryFindingStatus.BLOCKED,
                "claim:evidence",
                "the declared claim is missing and needs no recovery marker",
                "claim_missing",
            )
        )
    elif not claim_path.is_file():
        findings.append(
            _finding(
                RecoveryFindingStatus.UNKNOWN,
                "claim:evidence",
                "claim path is not a regular file",
                "claim_path_unsafe",
            )
        )
    else:
        try:
            size = claim_path.stat().st_size
            if size > MAX_CLAIM_EVIDENCE_BYTES:
                findings.append(
                    _finding(
                        RecoveryFindingStatus.UNKNOWN,
                        "claim:evidence",
                        "claim evidence exceeds the bounded read limit",
                        "claim_evidence_unbounded",
                    )
                )
            else:
                with claim_path.open("rb") as stream:
                    bounded = stream.read(MAX_CLAIM_EVIDENCE_BYTES + 1)
                if len(bounded) > MAX_CLAIM_EVIDENCE_BYTES:
                    findings.append(
                        _finding(
                            RecoveryFindingStatus.UNKNOWN,
                            "claim:evidence",
                            "claim evidence changed beyond the bounded read limit",
                            "claim_evidence_unbounded",
                        )
                    )
                else:
                    claim_bytes = bounded
        except OSError:
            findings.append(
                _finding(
                    RecoveryFindingStatus.UNKNOWN,
                    "claim:evidence",
                    "claim evidence is unreadable",
                    "claim_evidence_unreadable",
                )
            )
        if claim_bytes is not None and marker is not None:
            classification = classify_replay_claim_bytes(
                claim_bytes,
                claim_path=claim_relative,
                correlation_id=correlation,
                reservation_marker=marker,
            )
            if classification is ClaimEvidenceClassification.INCONSISTENT:
                findings.append(
                    _finding(
                        RecoveryFindingStatus.BLOCKED,
                        "claim:classification",
                        "claim JSON is inconsistent with the reservation or plan",
                        "claim_inconsistent",
                    )
                )
            elif classification is ClaimEvidenceClassification.UNKNOWN:
                findings.append(
                    _finding(
                        RecoveryFindingStatus.UNKNOWN,
                        "claim:classification",
                        "claim evidence cannot be classified safely",
                        "claim_classification_unknown",
                    )
                )
            else:
                findings.append(
                    _finding(
                        RecoveryFindingStatus.PASS,
                        "claim:classification",
                        f"claim evidence is classified as {classification.value}",
                    )
                )

    registry = _inside(root, registry_relative)
    registry_safe = not _has_symlink_component(root, registry_relative)
    if not registry_safe or (registry.exists() and not registry.is_dir()):
        findings.append(
            _finding(
                RecoveryFindingStatus.UNKNOWN,
                "recovery:registry",
                "recovery registry is unsafe",
                "recovery_registry_unsafe",
            )
        )
    elif not registry.is_dir():
        findings.append(
            _finding(
                RecoveryFindingStatus.BLOCKED,
                "recovery:registry",
                "recovery registry does not exist",
                "recovery_registry_missing",
            )
        )
    else:
        findings.append(
            _finding(
                RecoveryFindingStatus.PASS,
                "recovery:registry",
                "recovery registry exists",
            )
        )

    recovered = False
    recovery_path = _inside(root, recovery_relative)
    if registry_safe and registry.is_dir() and (
        recovery_path.exists() or recovery_path.is_symlink()
    ):
        if recovery_path.is_symlink() or not recovery_path.is_file():
            findings.append(
                _finding(
                    RecoveryFindingStatus.UNKNOWN,
                    "recovery:existing",
                    "existing recovery marker is unsafe",
                    "recovery_marker_unsafe",
                )
            )
        else:
            try:
                existing = _load_json(recovery_path, label="recovery marker")
            except ReplayClaimRecoveryPlanError:
                findings.append(
                    _finding(
                        RecoveryFindingStatus.UNKNOWN,
                        "recovery:existing",
                        "existing recovery marker is invalid or unreadable",
                        "recovery_marker_invalid",
                    )
                )
            else:
                if reservation_bound and marker is not None and claim_bytes is not None and not validate_replay_claim_recovery(
                    existing,
                    reservation_marker=marker,
                    claim_bytes=claim_bytes,
                ):
                    recovered = True
                    classification = ClaimEvidenceClassification.RECOVERED
                    findings.append(
                        _finding(
                            RecoveryFindingStatus.PASS,
                            "recovery:existing",
                            "exact immutable recovery evidence already exists",
                        )
                    )
                else:
                    findings.append(
                        _finding(
                            RecoveryFindingStatus.UNKNOWN,
                            "recovery:existing",
                            "existing recovery marker does not bind exact evidence",
                            "recovery_marker_invalid",
                        )
                    )
    elif registry_safe and registry.is_dir():
        findings.append(
            _finding(
                RecoveryFindingStatus.PASS,
                "recovery:unique",
                "no recovery marker exists for the correlation",
            )
        )

    statuses = {item.status for item in findings}
    if recovered:
        status = RecoveryPreviewStatus.ALREADY_RECOVERED
    elif RecoveryFindingStatus.UNKNOWN in statuses:
        status = RecoveryPreviewStatus.UNKNOWN
    elif RecoveryFindingStatus.BLOCKED in statuses:
        status = RecoveryPreviewStatus.BLOCKED
    else:
        status = RecoveryPreviewStatus.READY
    recovery: Mapping[str, Any] | None = None
    if (
        status is RecoveryPreviewStatus.READY
        and marker is not None
        and reservation_bound
        and claim_bytes is not None
        and repository_head is not None
        and classification
        in {
            ClaimEvidenceClassification.VALID,
            ClaimEvidenceClassification.PARTIAL,
            ClaimEvidenceClassification.MALFORMED,
        }
    ):
        recovery = _build_recovery(
            document,
            marker,
            claim_bytes,
            classification,
            recovery_path=recovery_relative,
            repository_head=repository_head,
        )
    reason_codes = tuple(
        dict.fromkeys(
            item.reason_code for item in findings if item.reason_code is not None
        )
    )
    inspection = ReplayClaimRecoveryInspection(
        contract=REPLAY_CLAIM_RECOVERY_INSPECTION_CONTRACT,
        schema_version=REPLAY_CLAIM_RECOVERY_SCHEMA_VERSION,
        classification=classification,
        correlation_id=correlation,
        claim_path=claim_relative,
        observed_claim_digest=_raw_digest(claim_bytes) if claim_bytes is not None else None,
        observed_byte_length=len(claim_bytes) if claim_bytes is not None else None,
        recovery_path=recovery_relative,
        findings=tuple(findings),
        reason_codes=reason_codes,
        known_limits=(
            "Abandonment is a human-owned fact; inspection does not infer whether a valid claim owner is still active.",
            "Recovery evidence preserves and supersedes exact bytes; it does not delete, repair, replace, or transfer the claim.",
            "Local exclusive creation does not establish network-filesystem or power-loss behavior.",
        ),
        authority_boundary=dict(AUTHORITY_BOUNDARY),
    )
    return ReplayClaimRecoveryPreview(
        contract=REPLAY_CLAIM_RECOVERY_PREVIEW_CONTRACT,
        schema_version=REPLAY_CLAIM_RECOVERY_SCHEMA_VERSION,
        status=status,
        inspection=inspection,
        recovery=recovery,
        authority_boundary=dict(AUTHORITY_BOUNDARY),
    )


def request_replay_claim_recovery_confirmation(
    preview: ReplayClaimRecoveryPreview,
    *,
    decision_reader: Callable[[str], str],
    is_interactive_terminal: bool,
) -> bool:
    """Require exact human recovery confirmation from a real terminal."""

    if (
        preview.status is not RecoveryPreviewStatus.READY
        or preview.recovery is None
        or not is_interactive_terminal
    ):
        return False
    answer = decision_reader(
        f"Create only {preview.inspection.recovery_path}? Type RECOVER to confirm: "
    )
    return answer == "RECOVER"


def _preview_digest(preview: ReplayClaimRecoveryPreview) -> str:
    return _canonical_digest(asdict(preview))


def apply_replay_claim_recovery(
    preview: ReplayClaimRecoveryPreview,
    document: Mapping[str, Any],
    *,
    repository: Path,
) -> ReplayClaimRecoveryResult:
    """Revalidate one reviewed preview and create its recovery marker once."""

    if preview.status is not RecoveryPreviewStatus.READY or preview.recovery is None:
        raise ReplayClaimRecoveryError("recovery preview is not ready to apply")
    root = _root(repository)
    recovery_path = _inside(root, preview.inspection.recovery_path)
    if recovery_path.exists() or recovery_path.is_symlink():
        raise ReplayClaimRecoveryConflictError("replay claim recovery already exists")
    fresh = prepare_replay_claim_recovery(document, repository=root)
    if fresh.status is RecoveryPreviewStatus.ALREADY_RECOVERED:
        raise ReplayClaimRecoveryConflictError("replay claim recovery already exists")
    if fresh.status is not RecoveryPreviewStatus.READY:
        raise ReplayClaimRecoveryStaleError("recovery facts are no longer ready")
    if _preview_digest(fresh) != _preview_digest(preview):
        raise ReplayClaimRecoveryStaleError("recovery preview changed before apply")

    payload = _recovery_bytes(preview.recovery)
    descriptor: int | None = None
    try:
        descriptor = os.open(
            recovery_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600
        )
        written = 0
        while written < len(payload):
            count = os.write(descriptor, payload[written:])
            if count <= 0:
                raise OSError("recovery marker write made no progress")
            written += count
        os.fsync(descriptor)
    except FileExistsError as exc:
        raise ReplayClaimRecoveryConflictError(
            "replay claim recovery appeared before exclusive creation"
        ) from exc
    finally:
        if descriptor is not None:
            os.close(descriptor)
    return ReplayClaimRecoveryResult(
        contract=REPLAY_CLAIM_RECOVERY_RESULT_CONTRACT,
        schema_version=REPLAY_CLAIM_RECOVERY_SCHEMA_VERSION,
        status="RECOVERED",
        correlation_id=preview.inspection.correlation_id,
        recovery_path=preview.inspection.recovery_path,
        recovery_digest=_raw_digest(payload),
        effect={"repository_modified": True, "recovery_created": True},
        authority_boundary=dict(AUTHORITY_BOUNDARY),
    )


def render_replay_claim_recovery_preview_json(
    preview: ReplayClaimRecoveryPreview,
) -> str:
    return json.dumps(asdict(preview), indent=2, sort_keys=True) + "\n"


def render_replay_claim_recovery_preview_terminal(
    preview: ReplayClaimRecoveryPreview,
) -> str:
    inspection = preview.inspection
    lines = [
        f"RECOVERY PREVIEW correlation={inspection.correlation_id} status={preview.status.value}",
        f"CLAIM classification={inspection.classification.value} path={inspection.claim_path}",
        f"RECOVERY {inspection.recovery_path}",
    ]
    if preview.recovery is not None:
        lines.append(json.dumps(preview.recovery, indent=2, sort_keys=True))
        lines.append(
            "NEXT exact interactive human confirmation is required before create-only recovery apply"
        )
    elif preview.status is RecoveryPreviewStatus.ALREADY_RECOVERED:
        lines.append("PASS exact immutable recovery evidence already exists")
    else:
        lines.append(
            "BLOCK recovery is not ready: "
            + (", ".join(inspection.reason_codes) or "required facts are unavailable")
        )
    lines.append(
        "NOTE recovery preserves the claim and grants no replacement claim or replay authority"
    )
    return "\n".join(lines) + "\n"


def render_replay_claim_recovery_result_terminal(
    result: ReplayClaimRecoveryResult,
) -> str:
    return (
        f"RECOVERED correlation={result.correlation_id} recovery={result.recovery_path}\n"
        "PASS one immutable recovery marker was written; the original claim was preserved\n"
        "NOTE recovery grants no replacement claim or replay authority\n"
    )
