"""Privacy-bounded, append-only local governance event storage."""

from __future__ import annotations

import json
import os
import re
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping


EVENT_CONTRACT = "agentgov.governance-event"
EVENT_SCHEMA_VERSION = "1.2"
ACTOR_CLASSES = {"human", "coding_agent", "ci"}
EVENT_TYPES = {
    "task.started",
    "scope.checked",
    "validation.completed",
    "completion.reconciled",
    "session.handed_off",
}
EVENT_OUTCOMES = {
    "started",
    "passed",
    "failed",
    "stale",
    "needs_evidence",
    "verified",
    "handed_off",
}

_ABSOLUTE_WINDOWS_RE = re.compile(r"(?i)(?:^|[\s\"'])?[a-z]:[\\/]")
_CREDENTIAL_ASSIGNMENT_RE = re.compile(
    r"(?i)(?:api[_-]?key|access[_-]?token|auth[_-]?token|password|passwd|secret)\s*[:=]\s*\S+"
)
_SECRET_TOKEN_RE = re.compile(
    r"(?i)(?:"
    r"gh[pousr]_[a-z0-9]{20,}"
    r"|sk-[a-z0-9_-]{20,}"
    r"|AKIA[0-9A-Z]{16}"
    r"|bearer\s+[a-z0-9._~-]{20,}"
    r"|eyJ[a-z0-9_-]{8,}\.[a-z0-9_-]{8,}\.[a-z0-9_-]{8,}"
    r"|-----BEGIN(?: [A-Z]+)* PRIVATE KEY-----"
    r")"
)


class LocalStateError(RuntimeError):
    """Local AgentGov state cannot be written or trusted safely."""


@dataclass(frozen=True)
class GovernanceEvent:
    contract: str
    schema_version: str
    event_id: str
    occurred_at: str
    event_type: str
    actor: Mapping[str, str]
    task_id: str
    task_digest: str
    observation_scope: str
    outcome: str
    evidence_ref: str | None
    governance_refs: tuple[str, ...]
    reason_codes: tuple[str, ...]
    metrics: Mapping[str, int]
    authority_boundary: Mapping[str, bool]


@dataclass(frozen=True)
class EventLoadResult:
    events: tuple[GovernanceEvent, ...]
    files_read: int
    duplicates_removed: int


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _contains_disallowed_text(value: Any) -> bool:
    if isinstance(value, str):
        return bool(
            value.startswith(("/", "\\\\"))
            or _ABSOLUTE_WINDOWS_RE.search(value)
            or _CREDENTIAL_ASSIGNMENT_RE.search(value)
            or _SECRET_TOKEN_RE.search(value)
        )
    if isinstance(value, Mapping):
        return any(_contains_disallowed_text(key) or _contains_disallowed_text(item) for key, item in value.items())
    if isinstance(value, (list, tuple)):
        return any(_contains_disallowed_text(item) for item in value)
    return False


def _event_from_payload(
    payload: Any,
    *,
    source: Path,
    require_filename_match: bool = True,
) -> GovernanceEvent:
    base_fields = {
        "contract", "schema_version", "event_id", "occurred_at", "event_type",
        "actor", "task_id", "task_digest", "observation_scope", "outcome",
        "evidence_ref", "reason_codes", "metrics", "authority_boundary",
    }
    if not isinstance(payload, dict):
        raise LocalStateError(f"event {source.name!r} has unexpected fields")
    schema_version = payload.get("schema_version")
    expected_fields = base_fields if schema_version == "1.0" else base_fields | {"governance_refs"}
    if set(payload) != expected_fields:
        raise LocalStateError(f"event {source.name!r} has unexpected fields")
    if payload.get("contract") != EVENT_CONTRACT or schema_version not in {"1.0", "1.1", EVENT_SCHEMA_VERSION}:
        raise LocalStateError(f"event {source.name!r} uses an unsupported contract")
    event_id = payload.get("event_id")
    if not isinstance(event_id, str) or not re.fullmatch(r"evt-[0-9a-f]{32}", event_id):
        raise LocalStateError(f"event {source.name!r} has an invalid event_id")
    if require_filename_match and source.stem != event_id:
        raise LocalStateError(f"event filename {source.name!r} does not match event_id")
    occurred_at = payload.get("occurred_at")
    if not isinstance(occurred_at, str) or not occurred_at.endswith("Z"):
        raise LocalStateError(f"event {event_id} must use a UTC Z timestamp")
    try:
        datetime.fromisoformat(occurred_at.removesuffix("Z") + "+00:00")
    except ValueError as exc:
        raise LocalStateError(f"event {event_id} timestamp is invalid") from exc
    event_type = payload.get("event_type")
    if event_type not in EVENT_TYPES:
        raise LocalStateError(f"event {event_id} has an unsupported event_type")
    if schema_version == "1.0" and event_type == "task.started":
        raise LocalStateError(f"event {event_id} uses task.started with an older schema")
    if schema_version != EVENT_SCHEMA_VERSION and event_type == "session.handed_off":
        raise LocalStateError(f"event {event_id} uses session.handed_off with an older schema")
    actor = payload.get("actor")
    if not isinstance(actor, dict) or set(actor) - {"class", "label"} or "class" not in actor:
        raise LocalStateError(f"event {event_id} actor is invalid")
    if actor.get("class") not in ACTOR_CLASSES:
        raise LocalStateError(f"event {event_id} actor class is invalid")
    if "label" in actor and (not isinstance(actor["label"], str) or not actor["label"]):
        raise LocalStateError(f"event {event_id} actor label is invalid")
    task_id = payload.get("task_id")
    task_digest = payload.get("task_digest")
    if not isinstance(task_id, str) or not task_id:
        raise LocalStateError(f"event {event_id} task_id is invalid")
    if not isinstance(task_digest, str) or not re.fullmatch(r"sha256:[0-9a-f]{64}", task_digest):
        raise LocalStateError(f"event {event_id} task_digest is invalid")
    if payload.get("observation_scope") != "local_development":
        raise LocalStateError(f"event {event_id} observation_scope is unsupported")
    outcome = payload.get("outcome")
    if outcome not in EVENT_OUTCOMES:
        raise LocalStateError(f"event {event_id} outcome is invalid")
    if schema_version == "1.0" and outcome == "started":
        raise LocalStateError(f"event {event_id} uses started with an older schema")
    if schema_version != EVENT_SCHEMA_VERSION and outcome == "handed_off":
        raise LocalStateError(f"event {event_id} uses handed_off with an older schema")
    if (event_type == "session.handed_off") != (outcome == "handed_off"):
        raise LocalStateError(f"event {event_id} has an invalid handoff type/outcome pair")
    if event_type == "session.handed_off" and actor.get("class") != "human":
        raise LocalStateError(f"event {event_id} handoff actor must be human")
    evidence_ref = payload.get("evidence_ref")
    if evidence_ref is not None and (
        not isinstance(evidence_ref, str)
        or evidence_ref.startswith(("/", "\\"))
        or "\\" in evidence_ref
        or ".." in Path(evidence_ref).parts
    ):
        raise LocalStateError(f"event {event_id} evidence_ref is unsafe")
    governance_refs = payload.get("governance_refs", [])
    if not isinstance(governance_refs, list) or len(governance_refs) != len(set(governance_refs)) or any(
        not isinstance(reference, str)
        or not reference
        or reference.startswith(("/", "\\"))
        or "\\" in reference
        or ".." in Path(reference).parts
        for reference in governance_refs
    ):
        raise LocalStateError(f"event {event_id} governance_refs are invalid")
    reason_codes = payload.get("reason_codes")
    if not isinstance(reason_codes, list) or len(reason_codes) != len(set(reason_codes)) or any(
        not isinstance(code, str) or not re.fullmatch(r"[a-z][a-z0-9_]*", code)
        for code in reason_codes
    ):
        raise LocalStateError(f"event {event_id} reason_codes are invalid")
    metrics = payload.get("metrics")
    if not isinstance(metrics, dict) or any(
        not isinstance(key, str)
        or not isinstance(value, int)
        or isinstance(value, bool)
        or value < 0
        for key, value in metrics.items()
    ):
        raise LocalStateError(f"event {event_id} metrics are invalid")
    authority = payload.get("authority_boundary")
    expected_authority = {
        "authorizes_code_change": False,
        "authorizes_exception": False,
        "authorizes_commit": False,
        "authorizes_merge": False,
        "authorizes_deployment": False,
    }
    if authority != expected_authority:
        raise LocalStateError(f"event {event_id} authority boundary is invalid")
    if _contains_disallowed_text(payload):
        raise LocalStateError(f"event {event_id} contains disallowed sensitive text")
    return GovernanceEvent(
        contract=payload["contract"],
        schema_version=schema_version,
        event_id=event_id,
        occurred_at=occurred_at,
        event_type=event_type,
        actor=dict(actor),
        task_id=task_id,
        task_digest=task_digest,
        observation_scope=payload["observation_scope"],
        outcome=payload["outcome"],
        evidence_ref=evidence_ref,
        governance_refs=tuple(governance_refs),
        reason_codes=tuple(reason_codes),
        metrics=dict(metrics),
        authority_boundary=dict(authority),
    )


def governance_event_from_payload(
    payload: Any,
    *,
    source_name: str = "embedded-event.json",
) -> GovernanceEvent:
    """Validate an embedded event without applying the file-name identity rule."""

    return _event_from_payload(
        payload,
        source=Path(source_name),
        require_filename_match=False,
    )


def load_governance_event(path: Path) -> GovernanceEvent:
    if path.is_symlink():
        raise LocalStateError(f"event file {path.name!r} must not be a symbolic link")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeError) as exc:
        raise LocalStateError(f"cannot read event {path.name!r}: {exc}") from exc
    return _event_from_payload(payload, source=path)


def load_governance_events(directory: Path) -> EventLoadResult:
    """Load, validate, sort, and deterministically deduplicate event files."""

    if directory.is_symlink():
        raise LocalStateError("event directory must not be a symbolic link")
    if not directory.exists():
        return EventLoadResult(events=(), files_read=0, duplicates_removed=0)
    if not directory.is_dir():
        raise LocalStateError("event source must be a directory")
    paths = sorted(directory.rglob("evt-*.json"), key=lambda item: item.as_posix())
    by_id: dict[str, GovernanceEvent] = {}
    duplicates = 0
    for path in paths:
        event = load_governance_event(path)
        existing = by_id.get(event.event_id)
        if existing is None:
            by_id[event.event_id] = event
        elif existing == event:
            duplicates += 1
        else:
            raise LocalStateError(f"conflicting duplicate event_id {event.event_id!r}")
    events = tuple(sorted(by_id.values(), key=lambda item: (item.occurred_at, item.event_id)))
    return EventLoadResult(events=events, files_read=len(paths), duplicates_removed=duplicates)


def _safe_state_directory(repository: Path, area: str) -> Path:
    if area not in {"events", "evidence"}:
        raise ValueError("unsupported AgentGov local-state area")
    if repository.is_symlink():
        raise LocalStateError("repository root must not be a symbolic link")
    root = repository.resolve()
    if not root.exists() or not root.is_dir():
        raise LocalStateError("repository root must be an existing directory")
    state_root = root / ".agentgov"
    target = state_root / area
    for candidate in (state_root, target):
        if candidate.is_symlink():
            raise LocalStateError(f"refusing symbolic-link local state path {candidate.name!r}")
    state_root.mkdir(mode=0o700, exist_ok=True)
    target.mkdir(mode=0o700, exist_ok=True)
    if target.resolve().parent != state_root.resolve():
        raise LocalStateError("local state area escaped .agentgov")
    return target


def write_local_record(
    repository: Path,
    *,
    area: str,
    record_id: str,
    payload: Mapping[str, Any],
) -> str:
    """Write one immutable JSON record and return its repository-relative path."""

    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{7,127}", record_id):
        raise LocalStateError("local record id is not a portable identifier")
    if _contains_disallowed_text(payload):
        raise LocalStateError("local record contains an absolute path or credential-like assignment")
    directory = _safe_state_directory(repository, area)
    path = directory / f"{record_id}.json"
    encoded = (json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    try:
        descriptor = os.open(path, flags, 0o600)
    except FileExistsError as exc:
        raise LocalStateError(f"local record already exists: {record_id}") from exc
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
    except BaseException:
        try:
            path.unlink(missing_ok=True)
        except OSError:
            pass
        raise
    return path.relative_to(repository.resolve()).as_posix()


def append_governance_event(
    repository: Path,
    *,
    event_type: str,
    actor_class: str,
    actor_label: str | None,
    task_id: str,
    task_digest: str,
    outcome: str,
    evidence_ref: str | None,
    governance_refs: tuple[str, ...] = (),
    reason_codes: tuple[str, ...] = (),
    metrics: Mapping[str, int] | None = None,
    occurred_at: str | None = None,
    event_id: str | None = None,
) -> tuple[GovernanceEvent, str]:
    if event_type not in EVENT_TYPES:
        raise ValueError(f"event_type must be one of {sorted(EVENT_TYPES)}")
    if actor_class not in ACTOR_CLASSES:
        raise ValueError(f"actor_class must be one of {sorted(ACTOR_CLASSES)}")
    if actor_label is not None and (not isinstance(actor_label, str) or not actor_label):
        raise ValueError("actor_label must be a non-empty string when provided")
    if not isinstance(task_id, str) or not task_id:
        raise ValueError("task_id must be a non-empty string")
    if outcome not in EVENT_OUTCOMES:
        raise ValueError(f"outcome must be one of {sorted(EVENT_OUTCOMES)}")
    if (event_type == "session.handed_off") != (outcome == "handed_off"):
        raise ValueError("session.handed_off and handed_off must be used together")
    if event_type == "session.handed_off" and actor_class != "human":
        raise ValueError("session.handed_off requires a human actor")
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", task_digest):
        raise ValueError("task_digest must be a SHA-256 identity")
    if evidence_ref is not None and (
        evidence_ref.startswith(("/", "\\"))
        or "\\" in evidence_ref
        or ".." in Path(evidence_ref).parts
    ):
        raise ValueError("evidence_ref must be a safe repository-relative path")
    if not isinstance(governance_refs, (list, tuple)) or any(
        not isinstance(reference, str)
        or not reference
        or reference.startswith(("/", "\\"))
        or "\\" in reference
        or ".." in Path(reference).parts
        for reference in governance_refs
    ):
        raise ValueError("governance_refs must be unique safe repository-relative paths")
    if len(governance_refs) != len(set(governance_refs)):
        raise ValueError("governance_refs must be unique safe repository-relative paths")
    if not isinstance(reason_codes, (list, tuple)) or any(
        not isinstance(code, str) or not re.fullmatch(r"[a-z][a-z0-9_]*", code)
        for code in reason_codes
    ):
        raise ValueError("reason_codes must use portable snake_case")
    if len(reason_codes) != len(set(reason_codes)):
        raise ValueError("reason_codes must use unique portable snake_case values")
    if metrics is not None and not isinstance(metrics, Mapping):
        raise ValueError("event metrics must be an object")
    if metrics is not None and any(
        not isinstance(key, str)
        or not isinstance(value, int)
        or isinstance(value, bool)
        or value < 0
        for key, value in metrics.items()
    ):
        raise ValueError("event metrics must be non-negative integers")
    actor = {"class": actor_class}
    if actor_label:
        actor["label"] = actor_label
    timestamp = occurred_at or utc_now()
    if not isinstance(timestamp, str) or not timestamp.endswith("Z"):
        raise ValueError("occurred_at must be a UTC Z timestamp")
    try:
        datetime.fromisoformat(timestamp.removesuffix("Z") + "+00:00")
    except ValueError as exc:
        raise ValueError("occurred_at must be a valid UTC Z timestamp") from exc
    event_id = event_id or f"evt-{uuid.uuid4().hex}"
    if not re.fullmatch(r"evt-[0-9a-f]{32}", event_id):
        raise ValueError("event_id must be an AgentGov event identifier")
    event = GovernanceEvent(
        contract=EVENT_CONTRACT,
        schema_version=EVENT_SCHEMA_VERSION,
        event_id=event_id,
        occurred_at=timestamp,
        event_type=event_type,
        actor=actor,
        task_id=task_id,
        task_digest=task_digest,
        observation_scope="local_development",
        outcome=outcome,
        evidence_ref=evidence_ref,
        governance_refs=tuple(governance_refs),
        reason_codes=tuple(reason_codes),
        metrics=dict(metrics or {}),
        authority_boundary={
            "authorizes_code_change": False,
            "authorizes_exception": False,
            "authorizes_commit": False,
            "authorizes_merge": False,
            "authorizes_deployment": False,
        },
    )
    relative = write_local_record(
        repository,
        area="events",
        record_id=event_id,
        payload=asdict(event),
    )
    return event, relative
