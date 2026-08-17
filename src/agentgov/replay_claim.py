"""Atomic, create-only pre-run claim for one replay reservation."""

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
from agentgov.replay_correlation_bridge import (
    replay_reservation_marker_digest,
    validate_replay_correlation_bridge,
)
from agentgov.replay_preflight import (
    AUTHORITY_BOUNDARY,
    REPLAY_ADAPTER_METADATA_CONTRACT,
    REPLAY_PREFLIGHT_SCHEMA_VERSION,
)
from agentgov.replay_reservation import validate_replay_reservation_marker


REPLAY_CLAIM_PLAN_CONTRACT = "agentgov.replay-correlation-claim-plan"
REPLAY_CLAIM_MARKER_CONTRACT = "agentgov.replay-correlation-claim"
REPLAY_CLAIM_PREVIEW_CONTRACT = "agentgov.replay-correlation-claim-preview"
REPLAY_CLAIM_RESULT_CONTRACT = "agentgov.replay-correlation-claim-result"
REPLAY_CLAIM_SCHEMA_VERSION = "1.0"

_CLAIM_ID_RE = re.compile(r"^rcl-[0-9a-f]{16}$")
_RESERVATION_ID_RE = re.compile(r"^rrv-[0-9a-f]{16}$")
_CORRELATION_ID_RE = re.compile(r"^rpf-[0-9a-f]{16}$")
_SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_GIT_SHA_RE = re.compile(r"^[0-9a-f]{40,64}$")
_NORMALIZED_ID_RE = re.compile(r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$")
_VERSION_RE = re.compile(r"^[0-9]+(?:\.[0-9]+){1,3}(?:(?:a|b|rc)[0-9]+)?$")
_PROTOCOL_RE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")


class ReplayClaimError(ValueError):
    """Claim input or local state cannot be used safely."""


class ReplayClaimPlanError(ReplayClaimError):
    """The claim plan is malformed or unsafe."""


class ReplayClaimConflictError(ReplayClaimError):
    """The create-only claim exists or won an exclusive-create race."""


class ReplayClaimStaleError(ReplayClaimError):
    """The reviewed claim preview no longer matches fresh local facts."""


class ReplayClaimPreviewStatus(str, Enum):
    READY = "READY_TO_CLAIM"
    BLOCKED = "BLOCKED"
    UNKNOWN = "UNKNOWN"


class ReplayClaimFindingStatus(str, Enum):
    PASS = "PASS"
    BLOCKED = "BLOCKED"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class ReplayClaimFinding:
    status: ReplayClaimFindingStatus
    check_id: str
    reason_code: str | None
    message: str


@dataclass(frozen=True)
class ReplayClaimPreview:
    contract: str
    schema_version: str
    status: ReplayClaimPreviewStatus
    correlation_id: str | None
    claim_path: str | None
    claim: Mapping[str, Any] | None
    reservation_marker_digest: str
    findings: tuple[ReplayClaimFinding, ...]
    reason_codes: tuple[str, ...]
    known_limits: tuple[str, ...]
    authority_boundary: Mapping[str, bool]


@dataclass(frozen=True)
class ReplayClaimResult:
    contract: str
    schema_version: str
    status: str
    correlation_id: str
    claim_path: str
    claim_digest: str
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


def _claim_bytes(claim: Mapping[str, Any]) -> bytes:
    return (json.dumps(claim, indent=2, sort_keys=True) + "\n").encode("utf-8")


def replay_claim_digest(claim: Mapping[str, Any]) -> str:
    """Return the digest of one canonical claim marker payload."""

    return "sha256:" + hashlib.sha256(_claim_bytes(claim)).hexdigest()


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


def _relative_path(value: Any, *, path: str, errors: list[str]) -> str | None:
    if not isinstance(value, str) or not value or len(value) > 400:
        errors.append(f"{path} must be a non-empty repository-relative path")
        return None
    problem = scope_path_error(value)
    if problem:
        errors.append(f"{path} {problem}")
        return None
    return value


def validate_replay_claim_plan(document: Any) -> list[str]:
    """Validate a strict claim plan without inspecting a repository."""

    errors: list[str] = []
    root = _exact_mapping(
        document,
        path="$",
        fields={
            "contract",
            "schema_version",
            "reservation",
            "claim",
            "adapter",
            "authority_boundary",
        },
        errors=errors,
    )
    if root is None:
        return errors
    if root["contract"] != REPLAY_CLAIM_PLAN_CONTRACT:
        errors.append(f"$.contract must equal {REPLAY_CLAIM_PLAN_CONTRACT!r}")
    if root["schema_version"] != REPLAY_CLAIM_SCHEMA_VERSION:
        errors.append("$.schema_version must equal '1.0'")

    reservation = _exact_mapping(
        root["reservation"],
        path="$.reservation",
        fields={"marker_path", "marker_digest"},
        errors=errors,
    )
    if reservation is not None:
        _relative_path(
            reservation["marker_path"],
            path="$.reservation.marker_path",
            errors=errors,
        )
        marker_digest = reservation["marker_digest"]
        if not isinstance(marker_digest, str) or not _SHA256_RE.fullmatch(
            marker_digest
        ):
            errors.append("$.reservation.marker_digest must be a SHA-256 digest")

    claim = _exact_mapping(
        root["claim"],
        path="$.claim",
        fields={"registry_directory", "claimant_id"},
        errors=errors,
    )
    if claim is not None:
        _relative_path(
            claim["registry_directory"],
            path="$.claim.registry_directory",
            errors=errors,
        )
        claimant_id = claim["claimant_id"]
        if not isinstance(claimant_id, str) or not _NORMALIZED_ID_RE.fullmatch(
            claimant_id
        ):
            errors.append("$.claim.claimant_id must be a normalized identifier")

    adapter = _exact_mapping(
        root["adapter"],
        path="$.adapter",
        fields={"metadata_path"},
        errors=errors,
    )
    if adapter is not None:
        _relative_path(
            adapter["metadata_path"],
            path="$.adapter.metadata_path",
            errors=errors,
        )
    if not isinstance(root["authority_boundary"], Mapping) or dict(
        root["authority_boundary"]
    ) != AUTHORITY_BOUNDARY:
        errors.append("$.authority_boundary must deny every replay and action authority")
    return errors


def validate_replay_claim_marker(document: Any) -> list[str]:
    """Validate one strict claim marker without consulting external evidence."""

    errors: list[str] = []
    root = _exact_mapping(
        document,
        path="$",
        fields={
            "contract",
            "schema_version",
            "claim_id",
            "correlation_id",
            "claim_path",
            "reservation",
            "repository_head",
            "adapter",
            "claimant_id",
            "status",
            "authority_boundary",
        },
        errors=errors,
    )
    if root is None:
        return errors
    if root["contract"] != REPLAY_CLAIM_MARKER_CONTRACT:
        errors.append(f"$.contract must equal {REPLAY_CLAIM_MARKER_CONTRACT!r}")
    if root["schema_version"] != REPLAY_CLAIM_SCHEMA_VERSION:
        errors.append("$.schema_version must equal '1.0'")
    claim_id = root["claim_id"]
    if not isinstance(claim_id, str) or not _CLAIM_ID_RE.fullmatch(claim_id):
        errors.append("$.claim_id must match ^rcl-[0-9a-f]{16}$")
    correlation_id = root["correlation_id"]
    if not isinstance(correlation_id, str) or not _CORRELATION_ID_RE.fullmatch(
        correlation_id
    ):
        errors.append("$.correlation_id must match ^rpf-[0-9a-f]{16}$")
    claim_path = _relative_path(root["claim_path"], path="$.claim_path", errors=errors)
    suffix = f"/{correlation_id}.json" if isinstance(correlation_id, str) else ""
    if claim_path is not None and not claim_path.endswith(suffix):
        errors.append("$.claim_path must end with the claimed correlation marker")

    reservation = _exact_mapping(
        root["reservation"],
        path="$.reservation",
        fields={"reservation_id", "marker_path", "marker_digest"},
        errors=errors,
    )
    if reservation is not None:
        reservation_id = reservation["reservation_id"]
        if not isinstance(reservation_id, str) or not _RESERVATION_ID_RE.fullmatch(
            reservation_id
        ):
            errors.append("$.reservation.reservation_id must match ^rrv-[0-9a-f]{16}$")
        marker_path = _relative_path(
            reservation["marker_path"],
            path="$.reservation.marker_path",
            errors=errors,
        )
        if marker_path is not None and not marker_path.endswith(suffix):
            errors.append(
                "$.reservation.marker_path must end with the reserved correlation marker"
            )
        marker_digest = reservation["marker_digest"]
        if not isinstance(marker_digest, str) or not _SHA256_RE.fullmatch(
            marker_digest
        ):
            errors.append("$.reservation.marker_digest must be a SHA-256 digest")

    repository_head = root["repository_head"]
    if not isinstance(repository_head, str) or not _GIT_SHA_RE.fullmatch(
        repository_head
    ):
        errors.append("$.repository_head must be a lowercase Git SHA")
    adapter = _exact_mapping(
        root["adapter"],
        path="$.adapter",
        fields={"adapter_id", "adapter_version", "protocol_version"},
        errors=errors,
    )
    if adapter is not None and (
        not isinstance(adapter["adapter_id"], str)
        or not _NORMALIZED_ID_RE.fullmatch(adapter["adapter_id"])
        or not isinstance(adapter["adapter_version"], str)
        or not _VERSION_RE.fullmatch(adapter["adapter_version"])
        or not isinstance(adapter["protocol_version"], str)
        or not _PROTOCOL_RE.fullmatch(adapter["protocol_version"])
    ):
        errors.append("$.adapter contains an invalid identity or protocol field")
    claimant_id = root["claimant_id"]
    if not isinstance(claimant_id, str) or not _NORMALIZED_ID_RE.fullmatch(
        claimant_id
    ):
        errors.append("$.claimant_id must be a normalized identifier")
    if root["status"] != "claimed":
        errors.append("$.status must equal 'claimed'")
    if not isinstance(root["authority_boundary"], Mapping) or dict(
        root["authority_boundary"]
    ) != AUTHORITY_BOUNDARY:
        errors.append("$.authority_boundary must deny every replay and action authority")
    return errors


def validate_replay_claim(
    document: Any,
    *,
    reservation_marker: Mapping[str, Any] | None = None,
    reserved_bridge: Mapping[str, Any] | None = None,
) -> list[str]:
    """Bind one claim to its immutable reservation and optional reserved bridge."""

    errors = validate_replay_claim_marker(document)
    if errors or not isinstance(document, Mapping):
        return errors
    if reservation_marker is None:
        errors.append("$ reservation_marker evidence is required")
        return errors
    marker_errors = validate_replay_reservation_marker(reservation_marker)
    errors.extend(f"$reservation_marker {item}" for item in marker_errors)
    if marker_errors:
        return errors
    comparisons = (
        ("$.correlation_id", document["correlation_id"], "correlation_id"),
        (
            "$.reservation.reservation_id",
            document["reservation"]["reservation_id"],
            "reservation_id",
        ),
        (
            "$.reservation.marker_path",
            document["reservation"]["marker_path"],
            "marker_path",
        ),
        ("$.repository_head", document["repository_head"], "preflight"),
        ("$.adapter", document["adapter"], "adapter"),
    )
    for path, claim_value, marker_field in comparisons:
        if marker_field == "preflight":
            marker_value = reservation_marker["preflight"]["observed_head_sha"]
        else:
            marker_value = reservation_marker[marker_field]
        if claim_value != marker_value:
            errors.append(f"{path} must match reservation marker evidence")
    if document["reservation"]["marker_digest"] != replay_reservation_marker_digest(
        reservation_marker
    ):
        errors.append(
            "$.reservation.marker_digest must match reservation marker evidence"
        )
    if reserved_bridge is not None:
        bridge_errors = validate_replay_correlation_bridge(
            reserved_bridge,
            reservation_marker=reservation_marker,
            harness_run=None,
        )
        errors.extend(f"$reserved_bridge {item}" for item in bridge_errors)
        if not bridge_errors:
            if reserved_bridge["state"] != "reserved":
                errors.append("$reserved_bridge state must equal 'reserved'")
            if reserved_bridge["correlation_id"] != document["correlation_id"]:
                errors.append("$reserved_bridge correlation must match the claim")
            if (
                reserved_bridge["reservation"]["reservation_id"]
                != document["reservation"]["reservation_id"]
            ):
                errors.append("$reserved_bridge reservation must match the claim")
    return errors


def _load_json(path: Path, *, label: str) -> Mapping[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ReplayClaimPlanError(f"{label} is not readable JSON") from exc
    if not isinstance(value, Mapping):
        raise ReplayClaimPlanError(f"{label} must be a JSON object")
    return value


def load_replay_claim_plan(path: Path) -> Mapping[str, Any]:
    document = _load_json(path, label="replay claim plan")
    errors = validate_replay_claim_plan(document)
    if errors:
        raise ReplayClaimPlanError("; ".join(errors))
    return document


def _root(repository: Path) -> Path:
    if repository.is_symlink():
        raise ReplayClaimError("repository root must not be a symbolic link")
    if not repository.exists() or not repository.is_dir():
        raise ReplayClaimError("repository root must be an existing directory")
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
        ("git", "-c", "core.quotepath=false", "-C", str(root), "rev-parse", "--show-toplevel", "HEAD"),
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
    status: ReplayClaimFindingStatus,
    check_id: str,
    message: str,
    reason_code: str | None = None,
) -> ReplayClaimFinding:
    return ReplayClaimFinding(status, check_id, reason_code, message)


def _adapter_finding(
    root: Path,
    relative: str,
    marker: Mapping[str, Any],
) -> ReplayClaimFinding:
    path = _inside(root, relative)
    if _has_symlink_component(root, relative) or not path.is_file():
        return _finding(
            ReplayClaimFindingStatus.UNKNOWN,
            "adapter:metadata",
            "local Adapter metadata is unavailable",
            "adapter_metadata_unavailable",
        )
    try:
        metadata = _load_json(path, label="Adapter metadata")
    except ReplayClaimPlanError:
        return _finding(
            ReplayClaimFindingStatus.UNKNOWN,
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
    if set(metadata) != required or (
        metadata.get("contract") != REPLAY_ADAPTER_METADATA_CONTRACT
        or metadata.get("schema_version") != REPLAY_PREFLIGHT_SCHEMA_VERSION
        or not isinstance(metadata.get("adapter_id"), str)
        or not _NORMALIZED_ID_RE.fullmatch(metadata["adapter_id"])
        or not isinstance(metadata.get("adapter_version"), str)
        or not _VERSION_RE.fullmatch(metadata["adapter_version"])
        or not isinstance(metadata.get("protocol_version"), str)
        or not _PROTOCOL_RE.fullmatch(metadata["protocol_version"])
    ):
        return _finding(
            ReplayClaimFindingStatus.UNKNOWN,
            "adapter:metadata",
            "local Adapter metadata does not satisfy the strict contract",
            "adapter_metadata_invalid",
        )
    observed = {
        "adapter_id": metadata["adapter_id"],
        "adapter_version": metadata["adapter_version"],
        "protocol_version": metadata["protocol_version"],
    }
    if observed != marker["adapter"]:
        return _finding(
            ReplayClaimFindingStatus.BLOCKED,
            "adapter:identity",
            "local Adapter identity does not match the reservation",
            "adapter_mismatch",
        )
    return _finding(
        ReplayClaimFindingStatus.PASS,
        "adapter:identity",
        "local Adapter identity matches the reservation",
    )


def _build_claim(
    plan: Mapping[str, Any],
    marker: Mapping[str, Any],
    *,
    claim_path: str,
    repository_head: str,
) -> Mapping[str, Any]:
    claim = {
        "contract": REPLAY_CLAIM_MARKER_CONTRACT,
        "schema_version": REPLAY_CLAIM_SCHEMA_VERSION,
        "claim_id": "rcl-" + _canonical_digest(plan).removeprefix("sha256:")[:16],
        "correlation_id": marker["correlation_id"],
        "claim_path": claim_path,
        "reservation": {
            "reservation_id": marker["reservation_id"],
            "marker_path": marker["marker_path"],
            "marker_digest": replay_reservation_marker_digest(marker),
        },
        "repository_head": repository_head,
        "adapter": dict(marker["adapter"]),
        "claimant_id": plan["claim"]["claimant_id"],
        "status": "claimed",
        "authority_boundary": dict(AUTHORITY_BOUNDARY),
    }
    errors = validate_replay_claim(claim, reservation_marker=marker)
    if errors:
        raise ReplayClaimError("invalid derived claim marker: " + "; ".join(errors))
    return claim


def prepare_replay_claim(
    document: Mapping[str, Any],
    *,
    repository: Path,
    reserved_bridge: Mapping[str, Any] | None = None,
) -> ReplayClaimPreview:
    """Prepare an exact create-only claim without changing repository state."""

    errors = validate_replay_claim_plan(document)
    if errors:
        raise ReplayClaimPlanError("; ".join(errors))
    root = _root(repository)
    marker_relative = str(document["reservation"]["marker_path"])
    expected_digest = str(document["reservation"]["marker_digest"])
    registry_relative = str(document["claim"]["registry_directory"])
    adapter_relative = str(document["adapter"]["metadata_path"])
    findings: list[ReplayClaimFinding] = []
    marker: Mapping[str, Any] | None = None

    marker_path = _inside(root, marker_relative)
    if _has_symlink_component(root, marker_relative) or not marker_path.is_file():
        findings.append(
            _finding(
                ReplayClaimFindingStatus.UNKNOWN,
                "reservation:marker",
                "reservation marker is unavailable",
                "reservation_marker_unavailable",
            )
        )
    else:
        try:
            marker = _load_json(marker_path, label="reservation marker")
        except ReplayClaimPlanError:
            findings.append(
                _finding(
                    ReplayClaimFindingStatus.UNKNOWN,
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
                        ReplayClaimFindingStatus.UNKNOWN,
                        "reservation:marker",
                        "reservation marker does not satisfy its strict contract",
                        "reservation_marker_invalid",
                    )
                )
                marker = None
            elif replay_reservation_marker_digest(marker) != expected_digest:
                findings.append(
                    _finding(
                        ReplayClaimFindingStatus.BLOCKED,
                        "reservation:digest",
                        "reservation marker digest does not match the claim plan",
                        "reservation_marker_mismatch",
                    )
                )
            else:
                findings.append(
                    _finding(
                        ReplayClaimFindingStatus.PASS,
                        "reservation:marker",
                        "reservation marker is valid and unchanged",
                    )
                )

    repository_head: str | None = None
    try:
        repository_head = _git_head(root)
    except (OSError, subprocess.SubprocessError):
        findings.append(
            _finding(
                ReplayClaimFindingStatus.UNKNOWN,
                "repository:head",
                "repository HEAD is unavailable",
                "repository_head_unavailable",
            )
        )
    if marker is not None and repository_head is not None:
        expected_head = marker["preflight"]["observed_head_sha"]
        if (
            marker["preflight"]["expected_head_sha"] != expected_head
            or repository_head != expected_head
        ):
            findings.append(
                _finding(
                    ReplayClaimFindingStatus.BLOCKED,
                    "repository:head",
                    "repository HEAD no longer matches the reservation",
                    "repository_head_mismatch",
                )
            )
        else:
            findings.append(
                _finding(
                    ReplayClaimFindingStatus.PASS,
                    "repository:head",
                    "repository HEAD matches the reservation",
                )
            )
        findings.append(_adapter_finding(root, adapter_relative, marker))

    registry = _inside(root, registry_relative)
    registry_safe = not _has_symlink_component(root, registry_relative)
    if not registry_safe or (registry.exists() and not registry.is_dir()):
        findings.append(
            _finding(
                ReplayClaimFindingStatus.UNKNOWN,
                "claim:registry",
                "claim registry is unsafe",
                "claim_registry_unsafe",
            )
        )
    elif not registry.is_dir():
        findings.append(
            _finding(
                ReplayClaimFindingStatus.BLOCKED,
                "claim:registry",
                "claim registry does not exist",
                "claim_registry_missing",
            )
        )
    else:
        findings.append(
            _finding(
                ReplayClaimFindingStatus.PASS,
                "claim:registry",
                "claim registry exists",
            )
        )

    correlation_id = marker["correlation_id"] if marker is not None else None
    claim_relative = (
        f"{registry_relative}/{correlation_id}.json"
        if correlation_id is not None
        else None
    )
    if claim_relative is not None and registry_safe and registry.is_dir():
        claim_path = _inside(root, claim_relative)
        if claim_path.exists() or claim_path.is_symlink():
            findings.append(
                _finding(
                    ReplayClaimFindingStatus.BLOCKED,
                    "claim:unique",
                    "a claim already exists for the reservation correlation",
                    "duplicate_claim",
                )
            )
        else:
            findings.append(
                _finding(
                    ReplayClaimFindingStatus.PASS,
                    "claim:unique",
                    "the reservation correlation has no local claim",
                )
            )

    if marker is not None and reserved_bridge is not None:
        bridge_errors = validate_replay_correlation_bridge(
            reserved_bridge,
            reservation_marker=marker,
            harness_run=None,
        )
        if bridge_errors or reserved_bridge.get("state") != "reserved":
            findings.append(
                _finding(
                    ReplayClaimFindingStatus.BLOCKED,
                    "bridge:reserved",
                    "reserved bridge evidence does not match the reservation",
                    "reserved_bridge_mismatch",
                )
            )
        else:
            findings.append(
                _finding(
                    ReplayClaimFindingStatus.PASS,
                    "bridge:reserved",
                    "reserved bridge evidence matches the reservation",
                )
            )

    statuses = {finding.status for finding in findings}
    if ReplayClaimFindingStatus.UNKNOWN in statuses:
        status = ReplayClaimPreviewStatus.UNKNOWN
    elif ReplayClaimFindingStatus.BLOCKED in statuses:
        status = ReplayClaimPreviewStatus.BLOCKED
    else:
        status = ReplayClaimPreviewStatus.READY
    claim: Mapping[str, Any] | None = None
    if (
        status is ReplayClaimPreviewStatus.READY
        and marker is not None
        and claim_relative is not None
        and repository_head is not None
    ):
        claim = _build_claim(
            document,
            marker,
            claim_path=claim_relative,
            repository_head=repository_head,
        )
        if reserved_bridge is not None:
            binding_errors = validate_replay_claim(
                claim,
                reservation_marker=marker,
                reserved_bridge=reserved_bridge,
            )
            if binding_errors:
                raise ReplayClaimError(
                    "invalid derived claim binding: " + "; ".join(binding_errors)
                )
    reason_codes = tuple(
        dict.fromkeys(
            finding.reason_code
            for finding in findings
            if finding.reason_code is not None
        )
    )
    return ReplayClaimPreview(
        contract=REPLAY_CLAIM_PREVIEW_CONTRACT,
        schema_version=REPLAY_CLAIM_SCHEMA_VERSION,
        status=status,
        correlation_id=correlation_id,
        claim_path=claim_relative,
        claim=claim,
        reservation_marker_digest=expected_digest,
        findings=tuple(findings),
        reason_codes=reason_codes,
        known_limits=(
            "A claim records durable pre-run ownership; it does not authorize or launch a replay.",
            "A created or partially created claim is never automatically deleted, expired, recovered, or taken over.",
            "Local exclusive creation does not establish network-filesystem behavior.",
        ),
        authority_boundary=dict(AUTHORITY_BOUNDARY),
    )


def request_replay_claim_confirmation(
    preview: ReplayClaimPreview,
    *,
    decision_reader: Callable[[str], str],
    is_interactive_terminal: bool,
) -> bool:
    """Require exact low-level human confirmation from a real terminal."""

    if (
        preview.status is not ReplayClaimPreviewStatus.READY
        or preview.claim is None
        or not is_interactive_terminal
    ):
        return False
    answer = decision_reader(
        f"Create only {preview.claim_path}? Type CLAIM to confirm: "
    )
    return answer == "CLAIM"


def _preview_digest(preview: ReplayClaimPreview) -> str:
    return _canonical_digest(asdict(preview))


def apply_replay_claim(
    preview: ReplayClaimPreview,
    document: Mapping[str, Any],
    *,
    repository: Path,
    reserved_bridge: Mapping[str, Any] | None = None,
) -> ReplayClaimResult:
    """Revalidate one reviewed preview and exclusively create its claim."""

    if preview.status is not ReplayClaimPreviewStatus.READY or preview.claim is None:
        raise ReplayClaimError("claim preview is not ready to apply")
    root = _root(repository)
    if preview.claim_path is None:
        raise ReplayClaimError("claim preview has no claim path")
    claim_path = _inside(root, preview.claim_path)
    if claim_path.exists() or claim_path.is_symlink():
        raise ReplayClaimConflictError("replay claim already exists")
    fresh = prepare_replay_claim(
        document,
        repository=root,
        reserved_bridge=reserved_bridge,
    )
    if fresh.status is not ReplayClaimPreviewStatus.READY:
        if "duplicate_claim" in fresh.reason_codes:
            raise ReplayClaimConflictError("replay claim already exists")
        raise ReplayClaimStaleError("replay claim facts are no longer ready")
    if _preview_digest(fresh) != _preview_digest(preview):
        raise ReplayClaimStaleError("claim preview changed before apply")

    payload = _claim_bytes(preview.claim)
    descriptor: int | None = None
    try:
        descriptor = os.open(claim_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        written = 0
        while written < len(payload):
            count = os.write(descriptor, payload[written:])
            if count <= 0:
                raise OSError("claim marker write made no progress")
            written += count
        os.fsync(descriptor)
    except FileExistsError as exc:
        raise ReplayClaimConflictError(
            "replay claim appeared before exclusive creation"
        ) from exc
    finally:
        if descriptor is not None:
            os.close(descriptor)
    return ReplayClaimResult(
        contract=REPLAY_CLAIM_RESULT_CONTRACT,
        schema_version=REPLAY_CLAIM_SCHEMA_VERSION,
        status="CLAIMED",
        correlation_id=str(preview.correlation_id),
        claim_path=preview.claim_path,
        claim_digest="sha256:" + hashlib.sha256(payload).hexdigest(),
        effect={"repository_modified": True, "claim_created": True},
        authority_boundary=dict(AUTHORITY_BOUNDARY),
    )


def render_replay_claim_preview_json(preview: ReplayClaimPreview) -> str:
    return json.dumps(asdict(preview), indent=2, sort_keys=True) + "\n"


def render_replay_claim_preview_terminal(preview: ReplayClaimPreview) -> str:
    correlation = preview.correlation_id or "unavailable"
    claim_path = preview.claim_path or "unavailable"
    lines = [
        f"CLAIM PREVIEW correlation={correlation} status={preview.status.value}",
        f"CLAIM {claim_path}",
    ]
    if preview.claim is not None:
        lines.append(json.dumps(preview.claim, indent=2, sort_keys=True))
        lines.append(
            "NEXT exact interactive human confirmation is required before create-only apply"
        )
    else:
        lines.append(
            "BLOCK claim is not ready: "
            + (", ".join(preview.reason_codes) or "required facts are unavailable")
        )
    lines.append(
        "NOTE claim does not authorize, launch, consume, expire, recover, or prove a replay"
    )
    return "\n".join(lines) + "\n"


def render_replay_claim_result_terminal(result: ReplayClaimResult) -> str:
    return (
        f"CLAIMED correlation={result.correlation_id} claim={result.claim_path}\n"
        "PASS one create-only local replay claim was written\n"
        "NOTE claim does not authorize, launch, consume, expire, recover, or prove a replay\n"
    )
