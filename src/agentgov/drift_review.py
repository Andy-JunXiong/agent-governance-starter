"""Deterministic cadence and immutable records for advisory drift reviews."""

from __future__ import annotations

import json
import os
import re
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

from agentgov.event_store import GovernanceEvent, load_governance_events, utc_now


POLICY_CONTRACT = "agentgov.drift-review-policy"
POLICY_SCHEMA_VERSION = "1.0"
RECORD_CONTRACT = "agentgov.drift-review-record"
RECORD_SCHEMA_VERSION = "1.0"
STATUS_CONTRACT = "agentgov.drift-review-status"
STATUS_SCHEMA_VERSION = "1.0"
DEFAULT_POLICY_PATH = Path("governance/drift-review-policy.json")
DEFAULT_RECORD_DIRECTORY = Path("governance/drift-reviews")
DEFAULT_MAX_AGE_DAYS = 7
DEFAULT_MAX_COMPLETED_TASKS = 3
DEFAULT_SNOOZE_DAYS = 7
DRIFT_DIMENSIONS = ("requirement", "architecture", "functionality")
REVIEW_OUTCOMES = {
    "no_drift_evidence",
    "candidate_drift",
    "insufficient_evidence",
}

_RECORD_ID_RE = re.compile(r"^drr-[0-9a-f]{32}$")


class DriftReviewPolicyError(RuntimeError):
    """A cadence policy or review record is unsafe or ambiguous."""


@dataclass(frozen=True)
class DriftReviewPolicy:
    contract: str
    schema_version: str
    max_age_days: int
    max_completed_tasks: int
    snooze_days: int
    dimensions: tuple[str, ...]
    semantic_classification: str
    authority_boundary: Mapping[str, bool]


@dataclass(frozen=True)
class DriftReviewRecord:
    contract: str
    schema_version: str
    record_id: str
    recorded_at: str
    action: str
    outcome: str | None
    snoozed_until: str | None
    completed_task_baseline: int
    dimensions: tuple[str, ...]
    semantics: str
    actor_class: str
    authority_boundary: Mapping[str, bool]


@dataclass(frozen=True)
class DriftReviewStatus:
    contract: str
    schema_version: str
    generated_at: str
    state: str
    reason_codes: tuple[str, ...]
    cadence: Mapping[str, int]
    observations: Mapping[str, Any]
    review_request: Mapping[str, Any]
    authority_boundary: Mapping[str, bool]


def _authority_boundary() -> Mapping[str, bool]:
    return {
        "decides_semantic_drift": False,
        "authorizes_governance_mutation": False,
        "authorizes_scope_expansion": False,
        "authorizes_exception": False,
        "authorizes_commit": False,
        "authorizes_merge": False,
        "authorizes_deployment": False,
    }


def _parse_utc(value: Any, *, label: str) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise DriftReviewPolicyError(f"{label} must be a UTC Z timestamp")
    try:
        parsed = datetime.fromisoformat(value.removesuffix("Z") + "+00:00")
    except ValueError as exc:
        raise DriftReviewPolicyError(f"{label} must be a valid UTC Z timestamp") from exc
    return parsed.astimezone(timezone.utc)


def _utc_text(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _safe_root(repository: Path) -> Path:
    if repository.is_symlink() or not repository.exists() or not repository.is_dir():
        raise DriftReviewPolicyError(
            "repository root must be an existing non-symbolic-link directory"
        )
    return repository.resolve()


def default_drift_review_policy() -> DriftReviewPolicy:
    return DriftReviewPolicy(
        contract=POLICY_CONTRACT,
        schema_version=POLICY_SCHEMA_VERSION,
        max_age_days=DEFAULT_MAX_AGE_DAYS,
        max_completed_tasks=DEFAULT_MAX_COMPLETED_TASKS,
        snooze_days=DEFAULT_SNOOZE_DAYS,
        dimensions=DRIFT_DIMENSIONS,
        semantic_classification="advisory",
        authority_boundary=_authority_boundary(),
    )


def drift_review_policy_from_payload(payload: Any) -> DriftReviewPolicy:
    fields = {
        "contract",
        "schema_version",
        "cadence",
        "dimensions",
        "semantic_classification",
        "authority_boundary",
    }
    if not isinstance(payload, Mapping) or set(payload) != fields:
        raise DriftReviewPolicyError("drift review policy has unexpected fields")
    if (
        payload.get("contract") != POLICY_CONTRACT
        or payload.get("schema_version") != POLICY_SCHEMA_VERSION
    ):
        raise DriftReviewPolicyError("drift review policy uses an unsupported contract")
    cadence = payload.get("cadence")
    if not isinstance(cadence, Mapping) or set(cadence) != {
        "max_age_days",
        "max_completed_tasks",
        "snooze_days",
    }:
        raise DriftReviewPolicyError("drift review cadence has unexpected fields")
    for key in ("max_age_days", "max_completed_tasks", "snooze_days"):
        value = cadence.get(key)
        if not isinstance(value, int) or isinstance(value, bool) or not 1 <= value <= 365:
            raise DriftReviewPolicyError(f"drift review {key} must be between 1 and 365")
    dimensions = payload.get("dimensions")
    if dimensions != list(DRIFT_DIMENSIONS):
        raise DriftReviewPolicyError(
            "drift review dimensions must be requirement, architecture, and functionality"
        )
    if payload.get("semantic_classification") != "advisory":
        raise DriftReviewPolicyError("semantic drift classification must remain advisory")
    if payload.get("authority_boundary") != _authority_boundary():
        raise DriftReviewPolicyError("drift review policy grants unsupported authority")
    return DriftReviewPolicy(
        contract=POLICY_CONTRACT,
        schema_version=POLICY_SCHEMA_VERSION,
        max_age_days=cadence["max_age_days"],
        max_completed_tasks=cadence["max_completed_tasks"],
        snooze_days=cadence["snooze_days"],
        dimensions=DRIFT_DIMENSIONS,
        semantic_classification="advisory",
        authority_boundary=_authority_boundary(),
    )


def load_drift_review_policy(repository: Path) -> tuple[DriftReviewPolicy, str]:
    root = _safe_root(repository)
    path = root / DEFAULT_POLICY_PATH
    if not path.exists():
        return default_drift_review_policy(), "built_in_default"
    if path.is_symlink() or not path.is_file():
        raise DriftReviewPolicyError("drift review policy must be a regular file")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise DriftReviewPolicyError(f"cannot read drift review policy: {exc}") from exc
    return drift_review_policy_from_payload(payload), DEFAULT_POLICY_PATH.as_posix()


def drift_review_record_from_payload(payload: Any, *, source_name: str) -> DriftReviewRecord:
    fields = {
        "contract",
        "schema_version",
        "record_id",
        "recorded_at",
        "action",
        "outcome",
        "snoozed_until",
        "completed_task_baseline",
        "dimensions",
        "semantics",
        "actor_class",
        "authority_boundary",
    }
    if not isinstance(payload, Mapping) or set(payload) != fields:
        raise DriftReviewPolicyError(f"drift review record {source_name!r} has unexpected fields")
    if (
        payload.get("contract") != RECORD_CONTRACT
        or payload.get("schema_version") != RECORD_SCHEMA_VERSION
    ):
        raise DriftReviewPolicyError(f"drift review record {source_name!r} uses an unsupported contract")
    record_id = payload.get("record_id")
    if not isinstance(record_id, str) or not _RECORD_ID_RE.fullmatch(record_id):
        raise DriftReviewPolicyError(f"drift review record {source_name!r} has an invalid id")
    recorded_at = payload.get("recorded_at")
    recorded_time = _parse_utc(recorded_at, label="recorded_at")
    action = payload.get("action")
    outcome = payload.get("outcome")
    snoozed_until = payload.get("snoozed_until")
    if action == "review_completed":
        if outcome not in REVIEW_OUTCOMES or snoozed_until is not None:
            raise DriftReviewPolicyError("completed drift review record is inconsistent")
    elif action == "snoozed":
        if outcome is not None or snoozed_until is None:
            raise DriftReviewPolicyError("snoozed drift review record is inconsistent")
        if _parse_utc(snoozed_until, label="snoozed_until") <= recorded_time:
            raise DriftReviewPolicyError("snoozed_until must be later than recorded_at")
    else:
        raise DriftReviewPolicyError("drift review record action is unsupported")
    baseline = payload.get("completed_task_baseline")
    if not isinstance(baseline, int) or isinstance(baseline, bool) or baseline < 0:
        raise DriftReviewPolicyError("completed_task_baseline must be a non-negative integer")
    if payload.get("dimensions") != list(DRIFT_DIMENSIONS):
        raise DriftReviewPolicyError("drift review record dimensions are invalid")
    if payload.get("semantics") != "advisory" or payload.get("actor_class") != "human":
        raise DriftReviewPolicyError("drift review completion remains advisory and human-recorded")
    if payload.get("authority_boundary") != _authority_boundary():
        raise DriftReviewPolicyError("drift review record grants unsupported authority")
    return DriftReviewRecord(
        contract=RECORD_CONTRACT,
        schema_version=RECORD_SCHEMA_VERSION,
        record_id=record_id,
        recorded_at=recorded_at,
        action=action,
        outcome=outcome,
        snoozed_until=snoozed_until,
        completed_task_baseline=baseline,
        dimensions=DRIFT_DIMENSIONS,
        semantics="advisory",
        actor_class="human",
        authority_boundary=_authority_boundary(),
    )


def load_drift_review_records(repository: Path) -> tuple[DriftReviewRecord, ...]:
    root = _safe_root(repository)
    directory = root / DEFAULT_RECORD_DIRECTORY
    if not directory.exists():
        return ()
    if directory.is_symlink() or not directory.is_dir():
        raise DriftReviewPolicyError("drift review record path must be a directory")
    records: list[DriftReviewRecord] = []
    seen: set[str] = set()
    for path in sorted(directory.glob("drr-*.json")):
        if path.is_symlink() or not path.is_file():
            raise DriftReviewPolicyError("drift review records must be regular files")
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise DriftReviewPolicyError(f"cannot read drift review record {path.name!r}: {exc}") from exc
        record = drift_review_record_from_payload(payload, source_name=path.name)
        if path.stem != record.record_id or record.record_id in seen:
            raise DriftReviewPolicyError("drift review record identity is duplicated or mismatched")
        seen.add(record.record_id)
        records.append(record)
    return tuple(
        sorted(
            records,
            key=lambda item: (
                _parse_utc(item.recorded_at, label="recorded_at"),
                item.record_id,
            ),
        )
    )


def _verified_task_ids(events: Iterable[GovernanceEvent]) -> set[str]:
    return {
        event.task_id
        for event in events
        if event.event_type == "completion.reconciled" and event.outcome == "verified"
    }


def build_drift_review_status(
    repository: Path,
    *,
    as_of: str | None = None,
    events: Iterable[GovernanceEvent] | None = None,
) -> DriftReviewStatus:
    root = _safe_root(repository)
    now_text = as_of or utc_now()
    now = _parse_utc(now_text, label="as_of")
    policy, policy_source = load_drift_review_policy(root)
    records = load_drift_review_records(root)
    visible_events = tuple(events) if events is not None else load_governance_events(root / ".agentgov/events").events
    completed_total = len(_verified_task_ids(visible_events))
    completed_reviews = tuple(item for item in records if item.action == "review_completed")
    last_review = completed_reviews[-1] if completed_reviews else None
    later_snoozes = tuple(
        item
        for item in records
        if item.action == "snoozed"
        and (
            last_review is None
            or _parse_utc(item.recorded_at, label="recorded_at")
            > _parse_utc(last_review.recorded_at, label="recorded_at")
        )
    )
    latest_snooze = later_snoozes[-1] if later_snoozes else None
    since_review = (
        max(0, completed_total - last_review.completed_task_baseline)
        if last_review is not None
        else completed_total
    )
    reasons: list[str] = []
    next_due_at: str | None = None
    if latest_snooze is not None and _parse_utc(latest_snooze.snoozed_until, label="snoozed_until") > now:
        state = "not_due"
        reasons.append("snoozed")
        next_due_at = latest_snooze.snoozed_until
    elif last_review is None:
        state = "due"
        reasons.append("initial_review_required")
    else:
        time_due = _parse_utc(last_review.recorded_at, label="recorded_at") + timedelta(
            days=policy.max_age_days
        )
        next_due_at = _utc_text(time_due)
        if since_review >= policy.max_completed_tasks:
            reasons.append("completed_task_threshold_reached")
        if now >= time_due:
            reasons.append("age_threshold_reached")
        state = "due" if reasons else "not_due"
        if not reasons:
            reasons.append("within_cadence")
    return DriftReviewStatus(
        contract=STATUS_CONTRACT,
        schema_version=STATUS_SCHEMA_VERSION,
        generated_at=now_text,
        state=state,
        reason_codes=tuple(reasons),
        cadence={
            "max_age_days": policy.max_age_days,
            "max_completed_tasks": policy.max_completed_tasks,
            "snooze_days": policy.snooze_days,
        },
        observations={
            "policy_source": policy_source,
            "history_scope": "visible_governance_events",
            "completed_tasks_total": completed_total,
            "completed_tasks_since_review": since_review,
            "last_reviewed_at": last_review.recorded_at if last_review else None,
            "last_review_outcome": last_review.outcome if last_review else None,
            "snoozed_until": latest_snooze.snoozed_until if latest_snooze else None,
            "next_due_at": next_due_at,
        },
        review_request={
            "dimensions": list(DRIFT_DIMENSIONS),
            "semantics": "advisory",
            "options": ["review_now", "snooze_configured_interval"],
            "claim_limit": "No drift conclusion exists until an evidence-bounded advisory review is completed and confirmed by a human.",
        },
        authority_boundary=_authority_boundary(),
    )


def build_drift_review_record(
    repository: Path,
    *,
    action: str,
    outcome: str | None = None,
    recorded_at: str | None = None,
    record_id: str | None = None,
) -> DriftReviewRecord:
    root = _safe_root(repository)
    timestamp = recorded_at or utc_now()
    recorded_time = _parse_utc(timestamp, label="recorded_at")
    policy, _ = load_drift_review_policy(root)
    completed_total = len(
        _verified_task_ids(load_governance_events(root / ".agentgov/events").events)
    )
    snoozed_until = (
        _utc_text(recorded_time + timedelta(days=policy.snooze_days))
        if action == "snoozed"
        else None
    )
    payload = {
        "contract": RECORD_CONTRACT,
        "schema_version": RECORD_SCHEMA_VERSION,
        "record_id": record_id or f"drr-{uuid.uuid4().hex}",
        "recorded_at": timestamp,
        "action": action,
        "outcome": outcome,
        "snoozed_until": snoozed_until,
        "completed_task_baseline": completed_total,
        "dimensions": list(DRIFT_DIMENSIONS),
        "semantics": "advisory",
        "actor_class": "human",
        "authority_boundary": _authority_boundary(),
    }
    return drift_review_record_from_payload(payload, source_name="planned-record.json")


def write_drift_review_record(repository: Path, record: DriftReviewRecord) -> Path:
    root = _safe_root(repository)
    directory = root / DEFAULT_RECORD_DIRECTORY
    if directory.is_symlink():
        raise DriftReviewPolicyError("drift review record directory must not be a symbolic link")
    directory.mkdir(parents=True, exist_ok=True)
    if directory.resolve().parent != (root / "governance").resolve():
        raise DriftReviewPolicyError("drift review record directory escaped governance")
    target = directory / f"{record.record_id}.json"
    encoded = (json.dumps(asdict(record), ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    try:
        descriptor = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError as exc:
        raise DriftReviewPolicyError("drift review record already exists") from exc
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


def render_drift_review_status_json(status: DriftReviewStatus) -> str:
    return json.dumps(asdict(status), ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def render_drift_review_status_terminal(status: DriftReviewStatus) -> str:
    reasons = ",".join(status.reason_codes)
    lines = [
        f"DRIFT_REVIEW {status.state} reasons={reasons}",
        (
            "CADENCE "
            f"tasks={status.cadence['max_completed_tasks']} days={status.cadence['max_age_days']} "
            f"snooze_days={status.cadence['snooze_days']}"
        ),
        "DIMENSIONS requirement, architecture, functionality",
        "SEMANTICS advisory; due status is deterministic but semantic drift remains human-owned",
        "AUTHORITY scope_expansion=false exception=false commit=false merge=false deployment=false",
    ]
    if status.state == "due":
        lines.append("NEXT run an evidence-bounded advisory drift review or record a seven-day snooze")
    return "\n".join(lines) + "\n"


def render_drift_review_status_github(status: DriftReviewStatus) -> str:
    heading = "## AgentGov drift review reminder"
    body = [
        heading,
        "",
        f"- State: `{status.state}`",
        f"- Reasons: `{', '.join(status.reason_codes)}`",
        "- Dimensions: `requirement`, `architecture`, `functionality`",
        "- Semantics: `ADVISORY` — this reminder is not a failing check or a drift verdict.",
        "- Authority: no scope, exception, Git, release, or deployment authority.",
    ]
    if status.state == "due":
        body.insert(0, "::warning title=AgentGov drift review due::Review requirement, architecture, and functionality alignment; this advisory does not fail the workflow.")
    return "\n".join(body) + "\n"
