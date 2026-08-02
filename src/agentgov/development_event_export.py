"""Explicit, metadata-only export of local development governance events."""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Mapping

from agentgov.event_store import (
    EVENT_CONTRACT,
    EVENT_SCHEMA_VERSION,
    GovernanceEvent,
    LocalStateError,
    governance_event_from_payload,
    load_governance_events,
    utc_now,
)


EXPORT_CONTRACT = "agentgov.development-event-export"
EXPORT_SCHEMA_VERSION = "1.0"
EXPORT_CONFIRMATION = "EXPORT"
MAX_EXPORT_EVENTS = 10_000
REDACTION_PROFILE = "metadata_only_v1"

CLAIM_LIMITS = (
    "The bundle contains only events present in the explicitly selected local event store at export time.",
    "Actor labels and local evidence references were removed; retained fields are bounded governance metadata.",
    "The bundle does not prove complete history, coding-agent consumption, semantic correctness, causality, or return on investment.",
)

AUTHORITY_BOUNDARY = {
    "approves_governance": False,
    "writes_governance_files": False,
    "authorizes_exception": False,
    "authorizes_commit": False,
    "authorizes_merge": False,
    "authorizes_deployment": False,
}


class DevelopmentExportPolicyError(RuntimeError):
    """A development event export cannot be created or trusted safely."""


@dataclass(frozen=True)
class DevelopmentEventExport:
    contract: str
    schema_version: str
    export_id: str
    created_at: str
    source: Mapping[str, Any]
    redaction: Mapping[str, Any]
    events: tuple[Mapping[str, Any], ...]
    claim_limits: tuple[str, ...]
    authority_boundary: Mapping[str, bool]


def _safe_root(repository: Path) -> Path:
    if repository.is_symlink() or not repository.exists() or not repository.is_dir():
        raise DevelopmentExportPolicyError(
            "repository root must be an existing non-symbolic-link directory"
        )
    return repository.resolve()


def _repository_path(
    root: Path,
    candidate: Path,
    *,
    purpose: str,
    allow_missing_leaf: bool,
) -> tuple[Path, Path]:
    target = candidate if candidate.is_absolute() else root / candidate
    try:
        relative = target.absolute().relative_to(root)
    except ValueError as exc:
        raise DevelopmentExportPolicyError(f"{purpose} must remain inside the repository") from exc
    current = root
    for index, part in enumerate(relative.parts):
        current = current / part
        is_leaf = index == len(relative.parts) - 1
        if current.is_symlink():
            raise DevelopmentExportPolicyError(f"{purpose} must not cross a symbolic link")
        if not current.exists() and (not is_leaf or not allow_missing_leaf):
            if not allow_missing_leaf:
                raise DevelopmentExportPolicyError(f"{purpose} does not exist")
            break
    resolved = target.resolve(strict=False)
    try:
        resolved_relative = resolved.relative_to(root)
    except ValueError as exc:
        raise DevelopmentExportPolicyError(f"{purpose} must remain inside the repository") from exc
    return resolved, resolved_relative


def _validate_timestamp(value: Any, *, field: str) -> str:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise DevelopmentExportPolicyError(f"{field} must be a UTC Z timestamp")
    try:
        datetime.fromisoformat(value.removesuffix("Z") + "+00:00")
    except ValueError as exc:
        raise DevelopmentExportPolicyError(f"{field} is invalid") from exc
    return value


def _canonical_events_digest(events: list[Mapping[str, Any]] | tuple[Mapping[str, Any], ...]) -> str:
    encoded = json.dumps(
        list(events),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _redacted_payload(event: GovernanceEvent) -> dict[str, Any]:
    return {
        "contract": EVENT_CONTRACT,
        "schema_version": EVENT_SCHEMA_VERSION,
        "event_id": event.event_id,
        "occurred_at": event.occurred_at,
        "event_type": event.event_type,
        "actor": {"class": event.actor["class"]},
        "task_id": event.task_id,
        "task_digest": event.task_digest,
        "observation_scope": event.observation_scope,
        "outcome": event.outcome,
        "evidence_ref": None,
        "governance_refs": list(event.governance_refs),
        "reason_codes": list(event.reason_codes),
        "metrics": dict(sorted(event.metrics.items())),
        "authority_boundary": dict(event.authority_boundary),
    }


def _validate_exportable_event(event: GovernanceEvent) -> None:
    if event.actor.get("class") == "ci":
        raise DevelopmentExportPolicyError(
            "development export cannot include CI events; use ci_only Monitor input for replay events"
        )
    if len(event.task_id) > 128:
        raise DevelopmentExportPolicyError(f"event {event.event_id} task_id exceeds 128 characters")
    if len(event.governance_refs) > 128 or any(len(item) > 512 for item in event.governance_refs):
        raise DevelopmentExportPolicyError(
            f"event {event.event_id} governance_refs exceed the metadata export bounds"
        )
    if len(event.reason_codes) > 64 or len(event.metrics) > 64:
        raise DevelopmentExportPolicyError(
            f"event {event.event_id} reason_codes or metrics exceed the metadata export bounds"
        )
    if any(len(key) > 64 for key in event.metrics):
        raise DevelopmentExportPolicyError(f"event {event.event_id} metric name is too long")


def build_development_event_export(
    repository: Path,
    *,
    event_directory: Path | None = None,
    created_at: str | None = None,
) -> DevelopmentEventExport:
    """Build a redacted export in memory without writing any file."""

    root = _safe_root(repository)
    source_candidate = event_directory or Path(".agentgov/events")
    source, _ = _repository_path(
        root,
        source_candidate,
        purpose="event source",
        allow_missing_leaf=False,
    )
    loaded = load_governance_events(source)
    if not loaded.events:
        raise DevelopmentExportPolicyError("development export requires at least one local event")
    if len(loaded.events) > MAX_EXPORT_EVENTS:
        raise DevelopmentExportPolicyError(
            f"development export exceeds the {MAX_EXPORT_EVENTS}-event safety bound"
        )
    for event in loaded.events:
        _validate_exportable_event(event)
    redacted_events = tuple(_redacted_payload(event) for event in loaded.events)
    for payload in redacted_events:
        governance_event_from_payload(payload, source_name="redacted-export-event.json")
    digest = _canonical_events_digest(redacted_events)
    timestamp = _validate_timestamp(created_at or utc_now(), field="created_at")
    return DevelopmentEventExport(
        contract=EXPORT_CONTRACT,
        schema_version=EXPORT_SCHEMA_VERSION,
        export_id="exp-" + digest.removeprefix("sha256:")[:32],
        created_at=timestamp,
        source={
            "observation_scope": "local_session",
            "event_files_read": loaded.files_read,
            "duplicates_removed": loaded.duplicates_removed,
            "event_count": len(redacted_events),
            "started_at": loaded.events[0].occurred_at,
            "ended_at": loaded.events[-1].occurred_at,
            "events_digest": digest,
        },
        redaction={
            "profile": REDACTION_PROFILE,
            "actor_labels_removed": sum("label" in event.actor for event in loaded.events),
            "evidence_refs_removed": sum(event.evidence_ref is not None for event in loaded.events),
            "source_content_included": False,
            "validation_output_included": False,
            "absolute_paths_included": False,
            "credentials_included": False,
        },
        events=redacted_events,
        claim_limits=CLAIM_LIMITS,
        authority_boundary=AUTHORITY_BOUNDARY,
    )


def development_export_default_output(bundle: DevelopmentEventExport) -> Path:
    return Path(".agentgov/exports") / f"{bundle.export_id}.json"


def render_development_event_export_preview(
    bundle: DevelopmentEventExport,
    *,
    output: Path,
) -> str:
    source = bundle.source
    redaction = bundle.redaction
    return "\n".join(
        (
            "DEVELOPMENT EVENT EXPORT PREVIEW",
            f"EXPORT_ID {bundle.export_id}",
            f"OUTPUT {output.as_posix()}",
            f"SOURCE events={source['event_count']} files={source['event_files_read']} duplicates_removed={source['duplicates_removed']}",
            f"INTERVAL {source['started_at']} to {source['ended_at']}",
            f"REDACTION profile={redaction['profile']} actor_labels_removed={redaction['actor_labels_removed']} evidence_refs_removed={redaction['evidence_refs_removed']}",
            "RETAINED event/task identities, timestamps, actor classes, governance refs, reason codes, outcomes, and bounded counters",
            "EXCLUDED actor labels, local evidence refs, code, prompts, validation output, absolute paths, and credentials",
            "SCOPE exported_development remains partial; cross-stage discovery is unavailable",
            "AUTHORITY approval=false governance_write=false exception=false commit=false merge=false deployment=false",
        )
    ) + "\n"


def request_development_export_confirmation(
    *,
    decision_reader: Callable[[str], str],
    is_interactive_terminal: bool,
) -> bool:
    if not is_interactive_terminal:
        return False
    return decision_reader(
        f"Type {EXPORT_CONFIRMATION} to create the reviewed redacted development-event bundle: "
    ).strip() == EXPORT_CONFIRMATION


def _is_tracked(root: Path, relative: Path) -> bool:
    completed = subprocess.run(
        ("git", "-C", str(root), "ls-files", "--error-unmatch", "--", relative.as_posix()),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
        timeout=30,
    )
    if completed.returncode not in {0, 1}:
        raise DevelopmentExportPolicyError("could not verify that export output is untracked")
    return completed.returncode == 0


def _validate_bundle_payload(payload: Any) -> DevelopmentEventExport:
    top_fields = {
        "contract", "schema_version", "export_id", "created_at", "source",
        "redaction", "events", "claim_limits", "authority_boundary",
    }
    if not isinstance(payload, dict) or set(payload) != top_fields:
        raise DevelopmentExportPolicyError("development event export has unexpected fields")
    if payload.get("contract") != EXPORT_CONTRACT or payload.get("schema_version") != EXPORT_SCHEMA_VERSION:
        raise DevelopmentExportPolicyError("development event export uses an unsupported contract")
    export_id = payload.get("export_id")
    if not isinstance(export_id, str) or not re.fullmatch(r"exp-[0-9a-f]{32}", export_id):
        raise DevelopmentExportPolicyError("development event export has an invalid export_id")
    created_at = _validate_timestamp(payload.get("created_at"), field="created_at")
    source = payload.get("source")
    expected_source = {
        "observation_scope", "event_files_read", "duplicates_removed", "event_count",
        "started_at", "ended_at", "events_digest",
    }
    if not isinstance(source, dict) or set(source) != expected_source:
        raise DevelopmentExportPolicyError("development event export source summary is invalid")
    if source.get("observation_scope") != "local_session":
        raise DevelopmentExportPolicyError("development event export source scope must be local_session")
    for field in ("event_files_read", "duplicates_removed", "event_count"):
        value = source.get(field)
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise DevelopmentExportPolicyError(f"development event export {field} is invalid")
    events_payload = payload.get("events")
    if not isinstance(events_payload, (list, tuple)) or not events_payload or len(events_payload) > MAX_EXPORT_EVENTS:
        raise DevelopmentExportPolicyError("development event export events are outside the safety bounds")
    if source["event_count"] != len(events_payload):
        raise DevelopmentExportPolicyError("development event export event_count does not match events")
    events: list[GovernanceEvent] = []
    for index, event_payload in enumerate(events_payload):
        try:
            event = governance_event_from_payload(
                event_payload,
                source_name=f"export-event-{index}.json",
            )
        except LocalStateError as exc:
            raise DevelopmentExportPolicyError(str(exc)) from exc
        _validate_exportable_event(event)
        if "label" in event.actor or event.evidence_ref is not None:
            raise DevelopmentExportPolicyError(
                f"event {event.event_id} contains a field required to be removed by redaction"
            )
        events.append(event)
    expected_order = sorted(events, key=lambda item: (item.occurred_at, item.event_id))
    if events != expected_order or len({item.event_id for item in events}) != len(events):
        raise DevelopmentExportPolicyError("development event export events must be unique and ordered")
    started_at = _validate_timestamp(source.get("started_at"), field="source.started_at")
    ended_at = _validate_timestamp(source.get("ended_at"), field="source.ended_at")
    if started_at != events[0].occurred_at or ended_at != events[-1].occurred_at:
        raise DevelopmentExportPolicyError("development event export interval does not match events")
    digest = _canonical_events_digest(events_payload)
    if source.get("events_digest") != digest:
        raise DevelopmentExportPolicyError("development event export events_digest does not match events")
    if export_id != "exp-" + digest.removeprefix("sha256:")[:32]:
        raise DevelopmentExportPolicyError("development event export export_id does not match events")
    redaction = payload.get("redaction")
    expected_redaction = {
        "profile", "actor_labels_removed", "evidence_refs_removed",
        "source_content_included", "validation_output_included",
        "absolute_paths_included", "credentials_included",
    }
    if not isinstance(redaction, dict) or set(redaction) != expected_redaction:
        raise DevelopmentExportPolicyError("development event export redaction summary is invalid")
    if redaction.get("profile") != REDACTION_PROFILE:
        raise DevelopmentExportPolicyError("development event export redaction profile is unsupported")
    for field in ("actor_labels_removed", "evidence_refs_removed"):
        value = redaction.get(field)
        if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= len(events):
            raise DevelopmentExportPolicyError(f"development event export {field} is invalid")
    for field in (
        "source_content_included", "validation_output_included",
        "absolute_paths_included", "credentials_included",
    ):
        if redaction.get(field) is not False:
            raise DevelopmentExportPolicyError(f"development event export {field} must be false")
    claim_limits = payload.get("claim_limits")
    if not isinstance(claim_limits, (list, tuple)) or tuple(claim_limits) != CLAIM_LIMITS:
        raise DevelopmentExportPolicyError("development event export claim limits are invalid")
    if payload.get("authority_boundary") != AUTHORITY_BOUNDARY:
        raise DevelopmentExportPolicyError("development event export authority boundary is invalid")
    return DevelopmentEventExport(
        contract=EXPORT_CONTRACT,
        schema_version=EXPORT_SCHEMA_VERSION,
        export_id=export_id,
        created_at=created_at,
        source=dict(source),
        redaction=dict(redaction),
        events=tuple(dict(item) for item in events_payload),
        claim_limits=CLAIM_LIMITS,
        authority_boundary=AUTHORITY_BOUNDARY,
    )


def validate_development_event_export(bundle: DevelopmentEventExport) -> DevelopmentEventExport:
    return _validate_bundle_payload(asdict(bundle))


def load_development_event_export(
    repository: Path,
    path: Path,
) -> DevelopmentEventExport:
    root = _safe_root(repository)
    source, _ = _repository_path(
        root,
        path,
        purpose="development export input",
        allow_missing_leaf=False,
    )
    if not source.is_file():
        raise DevelopmentExportPolicyError("development export input must be a file")
    try:
        payload = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise DevelopmentExportPolicyError(f"cannot read development event export: {exc}") from exc
    return _validate_bundle_payload(payload)


def write_development_event_export(
    repository: Path,
    *,
    bundle: DevelopmentEventExport,
    output: Path,
) -> Path:
    """Create one immutable, repository-local export without overwrite behavior."""

    root = _safe_root(repository)
    checked = validate_development_event_export(bundle)
    target, relative = _repository_path(
        root,
        output,
        purpose="development export output",
        allow_missing_leaf=True,
    )
    if target.suffix.lower() != ".json":
        raise DevelopmentExportPolicyError("development export output must use a .json suffix")
    if target.exists():
        raise DevelopmentExportPolicyError("development export output already exists; exports are immutable")
    if _is_tracked(root, relative):
        raise DevelopmentExportPolicyError("refusing to write a tracked development export output")
    parent = root
    for part in relative.parts[:-1]:
        parent = parent / part
        if parent.is_symlink():
            raise DevelopmentExportPolicyError("development export output must not cross a symbolic link")
        if parent.exists() and not parent.is_dir():
            raise DevelopmentExportPolicyError("development export output parent must be a directory")
    target.parent.mkdir(parents=True, exist_ok=True)
    encoded = (json.dumps(asdict(checked), ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    try:
        descriptor = os.open(target, flags, 0o600)
    except FileExistsError as exc:
        raise DevelopmentExportPolicyError(
            "development export output already exists; exports are immutable"
        ) from exc
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
    except BaseException:
        try:
            target.unlink(missing_ok=True)
        except OSError:
            pass
        raise
    return target
