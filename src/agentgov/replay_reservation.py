"""Human-controlled, create-only replay correlation reservation."""

from __future__ import annotations

import hashlib
import json
import os
import re
from collections.abc import Callable, Mapping
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from agentgov.replay_preflight import (
    AUTHORITY_BOUNDARY,
    ReplayPreflightPlanError,
    ReplayPreflightReport,
    ReplayPreflightStatus,
    evaluate_replay_preflight,
    validate_replay_preflight_plan,
)


REPLAY_RESERVATION_MARKER_CONTRACT = "agentgov.replay-correlation-reservation"
REPLAY_RESERVATION_PREVIEW_CONTRACT = (
    "agentgov.replay-correlation-reservation-preview"
)
REPLAY_RESERVATION_RESULT_CONTRACT = "agentgov.replay-correlation-reservation-result"
REPLAY_RESERVATION_SCHEMA_VERSION = "1.0"

_RESERVATION_ID_RE = re.compile(r"^rrv-[0-9a-f]{16}$")
_CORRELATION_ID_RE = re.compile(r"^rpf-[0-9a-f]{16}$")
_SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_GIT_SHA_RE = re.compile(r"^[0-9a-f]{40,64}$")
_ADAPTER_ID_RE = re.compile(r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$")
_VERSION_RE = re.compile(r"^[0-9]+(?:\.[0-9]+){1,3}(?:(?:a|b|rc)[0-9]+)?$")
_PROTOCOL_RE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")


class ReplayReservationError(ValueError):
    """Reservation input or local state cannot be used safely."""


class ReplayReservationConflictError(ReplayReservationError):
    """The exact create-only marker already exists or won a race."""


class ReplayReservationStaleError(ReplayReservationError):
    """The reviewed preview no longer matches fresh preflight facts."""


class ReplayReservationPreviewStatus(str, Enum):
    READY = "READY_TO_RESERVE"
    BLOCKED = "BLOCKED"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class ReplayReservationPreview:
    contract: str
    schema_version: str
    status: ReplayReservationPreviewStatus
    correlation_id: str
    marker_path: str
    marker: Mapping[str, Any] | None
    preflight: ReplayPreflightReport
    reason_codes: tuple[str, ...]
    known_limits: tuple[str, ...]
    authority_boundary: Mapping[str, bool]


@dataclass(frozen=True)
class ReplayReservationResult:
    contract: str
    schema_version: str
    status: str
    correlation_id: str
    marker_path: str
    marker_digest: str
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


def _marker_bytes(marker: Mapping[str, Any]) -> bytes:
    return (json.dumps(marker, indent=2, sort_keys=True) + "\n").encode("utf-8")


def validate_replay_reservation_marker(document: Any) -> list[str]:
    """Return strict marker-contract errors without inspecting a repository."""

    errors: list[str] = []
    required = {
        "contract",
        "schema_version",
        "reservation_id",
        "correlation_id",
        "marker_path",
        "preflight",
        "adapter",
        "status",
        "authority_boundary",
    }
    if not isinstance(document, Mapping):
        return ["$ must be an object"]
    if set(document) != required:
        for field in sorted(required - set(document)):
            errors.append(f"$.{field} is required")
        for field in sorted(set(document) - required):
            errors.append(f"$.{field} is not allowed")
        return errors
    if document["contract"] != REPLAY_RESERVATION_MARKER_CONTRACT:
        errors.append(
            f"$.contract must equal {REPLAY_RESERVATION_MARKER_CONTRACT!r}"
        )
    if document["schema_version"] != REPLAY_RESERVATION_SCHEMA_VERSION:
        errors.append("$.schema_version must equal '1.0'")
    reservation_id = document["reservation_id"]
    if not isinstance(reservation_id, str) or not _RESERVATION_ID_RE.fullmatch(
        reservation_id
    ):
        errors.append("$.reservation_id must match ^rrv-[0-9a-f]{16}$")
    correlation_id = document["correlation_id"]
    if not isinstance(correlation_id, str) or not _CORRELATION_ID_RE.fullmatch(
        correlation_id
    ):
        errors.append("$.correlation_id must match ^rpf-[0-9a-f]{16}$")
    marker_path = document["marker_path"]
    expected_suffix = f"/{correlation_id}.json" if isinstance(correlation_id, str) else ""
    if (
        not isinstance(marker_path, str)
        or "\\" in marker_path
        or marker_path.startswith("/")
        or ".." in marker_path.split("/")
        or not marker_path.endswith(expected_suffix)
    ):
        errors.append("$.marker_path must be the repository-relative correlation marker")
    preflight = document["preflight"]
    if not isinstance(preflight, Mapping) or set(preflight) != {
        "plan_digest",
        "expected_head_sha",
        "observed_head_sha",
    }:
        errors.append("$.preflight must contain exact digest and revision fields")
    else:
        digest = preflight["plan_digest"]
        if not isinstance(digest, str) or not _SHA256_RE.fullmatch(digest):
            errors.append("$.preflight.plan_digest must be a SHA-256 digest")
        for field in ("expected_head_sha", "observed_head_sha"):
            value = preflight[field]
            if not isinstance(value, str) or not _GIT_SHA_RE.fullmatch(value):
                errors.append(f"$.preflight.{field} must be a lowercase Git SHA")
    adapter = document["adapter"]
    if not isinstance(adapter, Mapping) or set(adapter) != {
        "adapter_id",
        "adapter_version",
        "protocol_version",
    }:
        errors.append("$.adapter must contain exact non-empty identity fields")
    elif (
        not isinstance(adapter["adapter_id"], str)
        or not _ADAPTER_ID_RE.fullmatch(adapter["adapter_id"])
        or not isinstance(adapter["adapter_version"], str)
        or not _VERSION_RE.fullmatch(adapter["adapter_version"])
        or not isinstance(adapter["protocol_version"], str)
        or not _PROTOCOL_RE.fullmatch(adapter["protocol_version"])
    ):
        errors.append("$.adapter contains an invalid identity or protocol field")
    if document["status"] != "reserved":
        errors.append("$.status must equal 'reserved'")
    if not isinstance(document["authority_boundary"], Mapping) or dict(
        document["authority_boundary"]
    ) != AUTHORITY_BOUNDARY:
        errors.append("$.authority_boundary must deny every replay and action authority")
    return errors


def _root(repository: Path) -> Path:
    if repository.is_symlink():
        raise ReplayReservationError("repository root must not be a symbolic link")
    if not repository.exists() or not repository.is_dir():
        raise ReplayReservationError("repository root must be an existing directory")
    return repository.resolve()


def _registry_state(root: Path, relative: str) -> tuple[str, str | None]:
    candidate = root
    for segment in relative.split("/"):
        candidate = candidate / segment
        if candidate.is_symlink():
            return "UNKNOWN", "reservation_registry_unsafe"
    if not candidate.exists():
        return "BLOCKED", "reservation_registry_missing"
    if not candidate.is_dir():
        return "UNKNOWN", "reservation_registry_unsafe"
    return "READY", None


def _build_marker(
    document: Mapping[str, Any],
    report: ReplayPreflightReport,
    *,
    marker_path: str,
) -> Mapping[str, Any]:
    plan_digest = _canonical_digest(document)
    marker = {
        "contract": REPLAY_RESERVATION_MARKER_CONTRACT,
        "schema_version": REPLAY_RESERVATION_SCHEMA_VERSION,
        "reservation_id": "rrv-" + plan_digest.removeprefix("sha256:")[:16],
        "correlation_id": report.correlation_id,
        "marker_path": marker_path,
        "preflight": {
            "plan_digest": plan_digest,
            "expected_head_sha": document["repository"]["expected_head_sha"],
            "observed_head_sha": report.observed_head_sha,
        },
        "adapter": {
            "adapter_id": document["adapter"]["expected_adapter_id"],
            "adapter_version": document["adapter"]["expected_adapter_version"],
            "protocol_version": document["adapter"]["expected_protocol_version"],
        },
        "status": "reserved",
        "authority_boundary": dict(AUTHORITY_BOUNDARY),
    }
    errors = validate_replay_reservation_marker(marker)
    if errors:
        raise ReplayReservationError("invalid derived reservation marker: " + "; ".join(errors))
    return marker


def prepare_replay_reservation(
    document: Mapping[str, Any], *, repository: Path
) -> ReplayReservationPreview:
    """Prepare one exact marker without changing repository state."""

    errors = validate_replay_preflight_plan(document)
    if errors:
        raise ReplayPreflightPlanError("; ".join(errors))
    report = evaluate_replay_preflight(document, repository=repository)
    correlation_id = report.correlation_id
    registry_relative = str(document["correlation"]["registry_directory"])
    marker_path = f"{registry_relative}/{correlation_id}.json"
    reason_codes = list(report.reason_codes)
    marker: Mapping[str, Any] | None = None
    if report.status is ReplayPreflightStatus.UNKNOWN:
        status = ReplayReservationPreviewStatus.UNKNOWN
    elif report.status is ReplayPreflightStatus.BLOCKED:
        status = ReplayReservationPreviewStatus.BLOCKED
    else:
        root = _root(repository)
        registry_status, registry_reason = _registry_state(root, registry_relative)
        if registry_status == "UNKNOWN":
            status = ReplayReservationPreviewStatus.UNKNOWN
        elif registry_status == "BLOCKED":
            status = ReplayReservationPreviewStatus.BLOCKED
        else:
            status = ReplayReservationPreviewStatus.READY
            marker = _build_marker(document, report, marker_path=marker_path)
        if registry_reason is not None:
            reason_codes.append(registry_reason)
    return ReplayReservationPreview(
        contract=REPLAY_RESERVATION_PREVIEW_CONTRACT,
        schema_version=REPLAY_RESERVATION_SCHEMA_VERSION,
        status=status,
        correlation_id=correlation_id,
        marker_path=marker_path,
        marker=marker,
        preflight=report,
        reason_codes=tuple(dict.fromkeys(reason_codes)),
        known_limits=(
            "Reservation records one local correlation identity; it does not launch or authorize a replay.",
            "Repository state can change after reservation and must be governed separately before replay.",
            "The low-level terminal confirmation is a development and recovery surface, not the final native product interaction.",
        ),
        authority_boundary=dict(AUTHORITY_BOUNDARY),
    )


def request_replay_reservation_confirmation(
    preview: ReplayReservationPreview,
    *,
    decision_reader: Callable[[str], str],
    is_interactive_terminal: bool,
) -> bool:
    """Require an exact low-level fallback confirmation from a real terminal."""

    if (
        preview.status is not ReplayReservationPreviewStatus.READY
        or preview.marker is None
        or not is_interactive_terminal
    ):
        return False
    answer = decision_reader(
        f"Create only {preview.marker_path}? Type RESERVE to confirm: "
    )
    return answer == "RESERVE"


def _preview_digest(preview: ReplayReservationPreview) -> str:
    return _canonical_digest(asdict(preview))


def apply_replay_reservation(
    preview: ReplayReservationPreview,
    document: Mapping[str, Any],
    *,
    repository: Path,
) -> ReplayReservationResult:
    """Revalidate one reviewed preview and exclusively create its marker."""

    if preview.status is not ReplayReservationPreviewStatus.READY or preview.marker is None:
        raise ReplayReservationError("reservation preview is not ready to apply")
    root = _root(repository)
    marker = root.joinpath(*preview.marker_path.split("/"))
    if marker.exists() or marker.is_symlink():
        raise ReplayReservationConflictError("correlation marker already exists")
    fresh = prepare_replay_reservation(document, repository=root)
    if fresh.status is not ReplayReservationPreviewStatus.READY:
        if "duplicate_correlation" in fresh.reason_codes:
            raise ReplayReservationConflictError("correlation marker already exists")
        raise ReplayReservationStaleError(
            "replay preflight is no longer ready for the reviewed reservation"
        )
    if _preview_digest(fresh) != _preview_digest(preview):
        raise ReplayReservationStaleError("reservation preview changed before apply")
    payload = _marker_bytes(preview.marker)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    descriptor: int | None = None
    created = False
    try:
        descriptor = os.open(marker, flags, 0o600)
        created = True
        written = 0
        while written < len(payload):
            count = os.write(descriptor, payload[written:])
            if count <= 0:
                raise OSError("reservation marker write made no progress")
            written += count
        os.fsync(descriptor)
    except FileExistsError as exc:
        raise ReplayReservationConflictError(
            "correlation marker appeared before exclusive creation"
        ) from exc
    except OSError:
        if created:
            try:
                marker.unlink()
            except OSError:
                pass
        raise
    finally:
        if descriptor is not None:
            os.close(descriptor)
    marker_digest = "sha256:" + hashlib.sha256(payload).hexdigest()
    return ReplayReservationResult(
        contract=REPLAY_RESERVATION_RESULT_CONTRACT,
        schema_version=REPLAY_RESERVATION_SCHEMA_VERSION,
        status="RESERVED",
        correlation_id=preview.correlation_id,
        marker_path=preview.marker_path,
        marker_digest=marker_digest,
        effect={"repository_modified": True, "reservation_created": True},
        authority_boundary=dict(AUTHORITY_BOUNDARY),
    )


def render_replay_reservation_preview_json(preview: ReplayReservationPreview) -> str:
    return json.dumps(asdict(preview), indent=2, sort_keys=True) + "\n"


def render_replay_reservation_preview_terminal(
    preview: ReplayReservationPreview,
) -> str:
    lines = [
        f"RESERVATION PREVIEW correlation={preview.correlation_id} status={preview.status.value}",
        f"MARKER {preview.marker_path}",
    ]
    if preview.marker is not None:
        lines.append(json.dumps(preview.marker, indent=2, sort_keys=True))
        lines.append("NEXT exact interactive human confirmation is required before create-only apply")
    else:
        lines.append(
            "BLOCK reservation is not ready: "
            + (", ".join(preview.reason_codes) or "required facts are unavailable")
        )
    lines.append(
        "NOTE reservation does not admit a task, authorize or launch a replay, or grant Git, release, deployment, or publication authority"
    )
    return "\n".join(lines) + "\n"


def render_replay_reservation_result_json(result: ReplayReservationResult) -> str:
    return json.dumps(asdict(result), indent=2, sort_keys=True) + "\n"


def render_replay_reservation_result_terminal(result: ReplayReservationResult) -> str:
    return (
        f"RESERVED correlation={result.correlation_id} marker={result.marker_path}\n"
        "PASS one create-only local reservation marker was written\n"
        "NOTE reservation does not admit a task, authorize or launch a replay, or grant Git, release, deployment, or publication authority\n"
    )
