"""Explicit, evidence-preserving terminal handoff for verified sessions."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Mapping

from agentgov.development_evidence import EvidenceError, inspect_task_completion
from agentgov.development_session import (
    SESSION_RELATIVE_PATH,
    DevelopmentSession,
    SessionPolicyError,
    current_session_events,
    resolve_active_task,
)
from agentgov.event_store import (
    GovernanceEvent,
    LocalStateError,
    append_governance_event,
    load_governance_event,
    utc_now,
)


class HandoffPolicyError(RuntimeError):
    """A session handoff cannot be previewed or recorded truthfully."""


@dataclass(frozen=True)
class HandoffPlan:
    root: Path
    session: DevelopmentSession
    evidence_ref: str
    completion_event_id: str
    event_id: str
    occurred_at: str
    actor_label: str | None
    already_handed_off: bool
    existing_event_ref: str | None

    @property
    def event_target(self) -> str:
        return f".agentgov/events/{self.event_id}.json"

    @property
    def targets(self) -> tuple[str, ...]:
        return () if self.already_handed_off else (self.event_target,)


@dataclass(frozen=True)
class HandoffResult:
    session: DevelopmentSession
    event_ref: str
    already_handed_off: bool


def _handoff_event_id(session: DevelopmentSession) -> str:
    identity = (
        f"{session.task_id}\0{session.task_digest}\0"
        f"{session.comparison_base_sha}\0{session.started_at}\0session.handed_off"
    ).encode("utf-8")
    return "evt-" + hashlib.sha256(identity).hexdigest()[:32]


def _timestamp_after(previous: str, candidate: str | None) -> str:
    selected = candidate or utc_now()
    if selected > previous:
        return selected
    prior = datetime.fromisoformat(previous.removesuffix("Z") + "+00:00")
    return (prior + timedelta(milliseconds=1)).astimezone(timezone.utc).isoformat(
        timespec="milliseconds"
    ).replace("+00:00", "Z")


def is_session_handoff_event(
    event: GovernanceEvent,
    session: DevelopmentSession,
) -> bool:
    """Return whether an event is the stable terminal marker for one session."""

    return all(
        (
            event.event_id == _handoff_event_id(session),
            event.event_type == "session.handed_off",
            event.actor.get("class") == "human",
            event.task_id == session.task_id,
            event.task_digest == session.task_digest,
            event.outcome == "handed_off",
            event.evidence_ref is not None,
        )
    )


def _matching_handoff(event: GovernanceEvent, plan: HandoffPlan) -> bool:
    return all(
        (
            is_session_handoff_event(event, plan.session),
            event.evidence_ref == plan.evidence_ref,
        )
    )


def build_handoff_plan(
    repository: Path,
    *,
    actor_label: str | None = None,
    occurred_at: str | None = None,
    event_id: str | None = None,
) -> HandoffPlan:
    """Build a read-only handoff preview after re-establishing fresh completion evidence."""

    try:
        task_path, session = resolve_active_task(repository)
        events = current_session_events(repository.resolve(), session)
    except (LocalStateError, SessionPolicyError) as exc:
        raise HandoffPolicyError(str(exc)) from exc
    starts = tuple(
        event
        for event in events
        if event.event_type == "task.started" and event.occurred_at == session.started_at
    )
    if len(starts) != 1:
        raise HandoffPolicyError("active session must have exactly one matching task.started event")
    if not events:
        raise HandoffPolicyError("active session has no immutable event history")

    latest = events[-1]
    already_handed_off = latest.event_type == "session.handed_off"
    if already_handed_off:
        completion = events[-2] if len(events) >= 2 else None
        if (
            completion is None
            or completion.event_type != "completion.reconciled"
            or completion.outcome != "verified"
            or latest.evidence_ref != completion.evidence_ref
        ):
            raise HandoffPolicyError("existing handoff is not linked to the latest verified completion")
        evidence_ref = latest.evidence_ref
        assert evidence_ref is not None
        if not is_session_handoff_event(latest, session):
            raise HandoffPolicyError("existing handoff does not use the stable session event identity")
        return HandoffPlan(
            root=repository.resolve(),
            session=session,
            evidence_ref=evidence_ref,
            completion_event_id=completion.event_id,
            event_id=latest.event_id,
            occurred_at=latest.occurred_at,
            actor_label=latest.actor.get("label"),
            already_handed_off=True,
            existing_event_ref=f".agentgov/events/{latest.event_id}.json",
        )

    if latest.event_type != "completion.reconciled" or latest.outcome != "verified":
        raise HandoffPolicyError(
            "latest current-session event must be completion.reconciled: verified; run govern finish"
        )
    if latest.evidence_ref is None:
        raise HandoffPolicyError("verified completion does not reference validation evidence")
    try:
        report = inspect_task_completion(
            task_path,
            repository=repository,
            evidence_path=Path(latest.evidence_ref),
        )
    except EvidenceError as exc:
        raise HandoffPolicyError(str(exc)) from exc
    if report.state != "verified":
        failures = "; ".join(
            finding.message for finding in report.findings if finding.status == "FAIL"
        )
        raise HandoffPolicyError(
            "verified completion evidence is no longer fresh; run govern finish"
            + (f": {failures}" if failures else "")
        )
    if report.task_digest != session.task_digest or report.evidence_ref != latest.evidence_ref:
        raise HandoffPolicyError("fresh evidence does not match the exact active completion")
    if report.comparison_base_sha != session.comparison_base_sha:
        raise HandoffPolicyError("fresh evidence comparison base does not match the active session")

    expected_id = _handoff_event_id(session)
    if event_id is not None and event_id != expected_id:
        raise HandoffPolicyError("handoff event identity changed after preview")
    return HandoffPlan(
        root=repository.resolve(),
        session=session,
        evidence_ref=latest.evidence_ref,
        completion_event_id=latest.event_id,
        event_id=expected_id,
        occurred_at=_timestamp_after(latest.occurred_at, occurred_at),
        actor_label=actor_label,
        already_handed_off=False,
        existing_event_ref=None,
    )


def _plan_payload(plan: HandoffPlan) -> Mapping[str, Any]:
    return {
        "action": "already_handed_off" if plan.already_handed_off else "handoff",
        "task": {
            "path": plan.session.task_path,
            "task_id": plan.session.task_id,
            "task_digest": plan.session.task_digest,
        },
        "comparison_base_sha": plan.session.comparison_base_sha,
        "verified_completion_event_id": plan.completion_event_id,
        "verified_evidence_ref": plan.evidence_ref,
        "retained": [SESSION_RELATIVE_PATH, plan.session.task_path, plan.evidence_ref],
        "targets": list(plan.targets),
        "meaning": "end automatic routing responsibility for this exact working-copy session",
        "authority_boundary": {
            "authorizes_code_change": False,
            "authorizes_exception": False,
            "authorizes_commit": False,
            "authorizes_merge": False,
            "authorizes_deployment": False,
        },
    }


def render_handoff_plan_json(plan: HandoffPlan) -> str:
    return json.dumps(_plan_payload(plan), ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def render_handoff_plan_terminal(plan: HandoffPlan) -> str:
    action = "already_handed_off" if plan.already_handed_off else "handoff"
    lines = [
        "GOVERN HANDOFF PREVIEW",
        f"ACTION {action}",
        f"TASK {plan.session.task_id} ({plan.session.task_path})",
        f"TASK_DIGEST {plan.session.task_digest}",
        f"COMPARISON_BASE {plan.session.comparison_base_sha}",
        f"VERIFIED_COMPLETION {plan.completion_event_id}",
        f"VERIFIED_EVIDENCE {plan.evidence_ref}",
        f"RETAINED {SESSION_RELATIVE_PATH}",
        f"WRITE_TARGETS {len(plan.targets)}",
    ]
    lines.extend(f"  - {target}" for target in plan.targets)
    lines.extend(
        (
            "MEANING end automatic routing responsibility for this exact working-copy session",
            "AUTHORITY code_change=false exception=false commit=false merge=false deployment=false",
            "NOTE handoff is not requirement, architecture, implementation, Monitor, commit, merge, release, or deployment approval",
        )
    )
    return "\n".join(lines) + "\n"


def request_handoff_confirmation(
    plan: HandoffPlan,
    *,
    decision_reader: Callable[[str], str],
    is_interactive_terminal: bool,
) -> bool:
    if plan.already_handed_off:
        return True
    if not is_interactive_terminal:
        return False
    try:
        decision = decision_reader(
            f'Type HANDOFF to append 1 reviewed event in "{plan.root}": '
        )
    except EOFError:
        return False
    return decision == "HANDOFF"


def apply_handoff_plan(plan: HandoffPlan) -> HandoffResult:
    """Revalidate a reviewed preview and append at most one stable handoff event."""

    if plan.already_handed_off:
        assert plan.existing_event_ref is not None
        return HandoffResult(plan.session, plan.existing_event_ref, True)
    current = build_handoff_plan(
        plan.root,
        actor_label=plan.actor_label,
        occurred_at=plan.occurred_at,
        event_id=plan.event_id,
    )
    if current.already_handed_off:
        assert current.existing_event_ref is not None
        if (
            current.session == plan.session
            and current.event_id == plan.event_id
            and current.evidence_ref == plan.evidence_ref
        ):
            return HandoffResult(plan.session, current.existing_event_ref, True)
        raise HandoffPolicyError("handoff state changed after preview; build and review a new plan")
    if current != plan:
        raise HandoffPolicyError("handoff state changed after preview; build and review a new plan")
    try:
        _, event_ref = append_governance_event(
            plan.root,
            event_type="session.handed_off",
            actor_class="human",
            actor_label=plan.actor_label,
            task_id=plan.session.task_id,
            task_digest=plan.session.task_digest,
            outcome="handed_off",
            evidence_ref=plan.evidence_ref,
            reason_codes=(
                "handoff_confirmed",
                "verified_evidence_fresh",
                "routing_responsibility_ended",
            ),
            metrics={"verified_evidence": 1},
            occurred_at=plan.occurred_at,
            event_id=plan.event_id,
        )
        return HandoffResult(plan.session, event_ref, False)
    except LocalStateError as exc:
        target = plan.root / plan.event_target
        try:
            existing = load_governance_event(target)
        except (LocalStateError, OSError) as load_exc:
            raise HandoffPolicyError(str(exc)) from load_exc
        if not _matching_handoff(existing, plan):
            raise HandoffPolicyError("handoff event target exists with conflicting content") from exc
        return HandoffResult(plan.session, plan.event_target, True)
