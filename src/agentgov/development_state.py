"""Pure projection of validated development events into one lifecycle state."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any, Mapping, Sequence

from agentgov.development_handoff import is_session_handoff_event
from agentgov.development_session import DevelopmentSession
from agentgov.event_store import GovernanceEvent


STATE_CONTRACT = "agentgov.development-state"
STATE_SCHEMA_VERSION = "1.0"


class DevelopmentStage(str, Enum):
    ACTIVE_UNCHECKED = "active_unchecked"
    SCOPE_PASSED = "scope_passed"
    SCOPE_BLOCKED = "scope_blocked"
    VALIDATION_RECORDED = "validation_recorded"
    NEEDS_EVIDENCE = "needs_evidence"
    REVIEW_READY = "review_ready"
    HANDED_OFF = "handed_off"
    INVALID = "invalid"


class DevelopmentOperation(str, Enum):
    CHECK_SCOPE = "check_scope"
    VALIDATE_AND_RECONCILE = "validate_and_reconcile"
    RECONCILE_COMPLETION = "reconcile_completion"
    REFRESH_DASHBOARD = "refresh_dashboard"
    ROLLOVER = "rollover"
    REQUIRE_HUMAN = "require_human"


@dataclass(frozen=True)
class DevelopmentState:
    contract: str
    schema_version: str
    task_id: str
    task_digest: str
    stage: str
    recommended_operation: str
    blocking: bool
    reason_code: str
    event_count: int
    latest_event_type: str | None
    latest_outcome: str | None
    authority_boundary: Mapping[str, bool]


def _state(
    session: DevelopmentSession,
    events: Sequence[GovernanceEvent],
    *,
    stage: DevelopmentStage,
    operation: DevelopmentOperation,
    blocking: bool,
    reason_code: str,
) -> DevelopmentState:
    latest = events[-1] if events else None
    return DevelopmentState(
        contract=STATE_CONTRACT,
        schema_version=STATE_SCHEMA_VERSION,
        task_id=session.task_id,
        task_digest=session.task_digest,
        stage=stage.value,
        recommended_operation=operation.value,
        blocking=blocking,
        reason_code=reason_code,
        event_count=len(events),
        latest_event_type=latest.event_type if latest else None,
        latest_outcome=latest.outcome if latest else None,
        authority_boundary={
            "executes_operation": False,
            "authorizes_code_change": False,
            "authorizes_exception": False,
            "authorizes_commit": False,
            "authorizes_merge": False,
            "authorizes_deployment": False,
        },
    )


def project_development_state(
    session: DevelopmentSession,
    events: Sequence[GovernanceEvent],
) -> DevelopmentState:
    """Project an exact session event stream without executing its next operation."""

    ordered = tuple(events)
    if any(
        event.task_id != session.task_id
        or event.task_digest != session.task_digest
        or event.occurred_at < session.started_at
        for event in ordered
    ):
        return _state(
            session,
            ordered,
            stage=DevelopmentStage.INVALID,
            operation=DevelopmentOperation.REQUIRE_HUMAN,
            blocking=True,
            reason_code="event_outside_session",
        )
    if any(
        earlier.occurred_at > later.occurred_at
        for earlier, later in zip(ordered, ordered[1:])
    ):
        return _state(
            session,
            ordered,
            stage=DevelopmentStage.INVALID,
            operation=DevelopmentOperation.REQUIRE_HUMAN,
            blocking=True,
            reason_code="events_not_chronological",
        )
    if not ordered or not (
        ordered[0].event_type == "task.started"
        and ordered[0].occurred_at == session.started_at
    ):
        return _state(
            session,
            ordered,
            stage=DevelopmentStage.INVALID,
            operation=DevelopmentOperation.REQUIRE_HUMAN,
            blocking=True,
            reason_code="missing_start_event",
        )

    latest = ordered[-1]
    if latest.event_type == "task.started":
        return _state(
            session,
            ordered,
            stage=DevelopmentStage.ACTIVE_UNCHECKED,
            operation=DevelopmentOperation.CHECK_SCOPE,
            blocking=False,
            reason_code="task_started",
        )
    if latest.event_type == "scope.checked":
        if latest.outcome == "passed":
            return _state(
                session,
                ordered,
                stage=DevelopmentStage.SCOPE_PASSED,
                operation=DevelopmentOperation.VALIDATE_AND_RECONCILE,
                blocking=False,
                reason_code="scope_passed",
            )
        return _state(
            session,
            ordered,
            stage=DevelopmentStage.SCOPE_BLOCKED,
            operation=DevelopmentOperation.CHECK_SCOPE,
            blocking=True,
            reason_code="scope_blocked",
        )
    if latest.event_type == "validation.completed":
        return _state(
            session,
            ordered,
            stage=DevelopmentStage.VALIDATION_RECORDED,
            operation=DevelopmentOperation.RECONCILE_COMPLETION,
            blocking=False,
            reason_code="validation_recorded",
        )
    if latest.event_type == "completion.reconciled":
        if latest.outcome == "verified":
            return _state(
                session,
                ordered,
                stage=DevelopmentStage.REVIEW_READY,
                operation=DevelopmentOperation.REFRESH_DASHBOARD,
                blocking=False,
                reason_code="completion_verified",
            )
        return _state(
            session,
            ordered,
            stage=DevelopmentStage.NEEDS_EVIDENCE,
            operation=DevelopmentOperation.VALIDATE_AND_RECONCILE,
            blocking=False,
            reason_code="completion_needs_evidence",
        )
    if latest.event_type == "session.handed_off":
        prior = ordered[-2] if len(ordered) >= 2 else None
        if not (
            is_session_handoff_event(latest, session)
            and prior is not None
            and prior.event_type == "completion.reconciled"
            and prior.outcome == "verified"
            and prior.evidence_ref == latest.evidence_ref
        ):
            return _state(
                session,
                ordered,
                stage=DevelopmentStage.INVALID,
                operation=DevelopmentOperation.REQUIRE_HUMAN,
                blocking=True,
                reason_code="invalid_handoff",
            )
        return _state(
            session,
            ordered,
            stage=DevelopmentStage.HANDED_OFF,
            operation=DevelopmentOperation.ROLLOVER,
            blocking=False,
            reason_code="session_handed_off",
        )
    return _state(
        session,
        ordered,
        stage=DevelopmentStage.INVALID,
        operation=DevelopmentOperation.REQUIRE_HUMAN,
        blocking=True,
        reason_code="unsupported_progress",
    )


def development_state_payload(state: DevelopmentState) -> Mapping[str, Any]:
    """Return the stable machine-readable representation used by adapters."""

    return asdict(state)
