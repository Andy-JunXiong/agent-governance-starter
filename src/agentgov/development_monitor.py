"""Static development-governance Monitor derived from local events."""

from __future__ import annotations

import html
import json
import os
import subprocess
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping

from agentgov.development_event_export import (
    DevelopmentExportPolicyError,
    load_development_event_export,
)
from agentgov.development_session import SessionPolicyError, resolve_active_task
from agentgov.development_state import development_state_payload, project_development_state
from agentgov.event_store import (
    GovernanceEvent,
    governance_event_from_payload,
    load_governance_events,
    utc_now,
)
from agentgov.drift_review import build_drift_review_status
from agentgov.learning_review import (
    HUMAN_PRODUCT_OWNER_ROLE,
    LEARNING_DISPOSITIONS,
    LearningReview,
    LearningReviewPolicyError,
    learning_candidate_digest,
    load_learning_reviews,
    protection_signal_class,
)
from agentgov.scope_observation import ScopeObservationError, load_scope_observation
from agentgov.task_contract import load_development_task


MONITOR_CONTRACT = "agentgov.development-monitor"
MONITOR_SCHEMA_VERSION = "1.10"
MONITOR_SCOPES = {"local_session", "exported_development", "ci_only", "combined"}

_PROTECTION_GUIDANCE = {
    "scope_boundary": (
        "review_scope_boundary",
        "Review task scope and changed paths",
    ),
    "validation_failure": (
        "review_validation_failure",
        "Review failed validation evidence",
    ),
    "stale_evidence": (
        "refresh_stale_evidence",
        "Refresh stale validation evidence",
    ),
    "incomplete_completion": (
        "complete_missing_evidence",
        "Complete missing completion evidence",
    ),
}


class MonitorPolicyError(RuntimeError):
    """A Monitor claim cannot be supported by the available event source."""


@dataclass(frozen=True)
class DevelopmentMonitor:
    contract: str
    schema_version: str
    generated_at: str
    observation: Mapping[str, Any]
    active_task: Mapping[str, Any]
    overview: Mapping[str, int]
    live_sessions: tuple[Mapping[str, Any], ...]
    protection_events: tuple[Mapping[str, Any], ...]
    timeline: tuple[Mapping[str, Any], ...]
    tasks: tuple[Mapping[str, Any], ...]
    benefit: Mapping[str, Any]
    learning: Mapping[str, Any]
    drift_review: Mapping[str, Any]
    claim_layers: Mapping[str, tuple[str, ...]]
    authority_boundary: Mapping[str, bool]


@dataclass(frozen=True)
class _ObservedEvent:
    event: GovernanceEvent
    source_scope: str


_ACTIVE_TASK_AUTHORITY = {
    "authorizes_commit": False,
    "authorizes_merge": False,
    "authorizes_publish": False,
    "authorizes_release": False,
    "authorizes_deploy": False,
}
_ACTIVE_TASK_CLAIM_LIMITS = (
    "Observed Git paths do not identify who changed or restored a file.",
    "Selected governance context does not prove that a coding agent consumed it.",
    "Completion Verified does not prove requirement or architecture correctness, human acceptance, or validation sufficiency.",
    "No task, event, evidence record, Monitor view, or bounded handoff grants commit, merge, publish, release, or deploy authority.",
    "A later passing event does not prove that an earlier Protection Event was handled or resolved.",
)


def _unavailable_active_task(reason_code: str) -> Mapping[str, Any]:
    return {
        "availability": "unavailable",
        "reason_code": reason_code,
        "claim_limits": list(_ACTIVE_TASK_CLAIM_LIMITS),
        "authority": dict(_ACTIVE_TASK_AUTHORITY),
    }


def _state_meaning(stage: str) -> str:
    return {
        "active_unchecked": (
            "Work is associated with this admitted task, but the current scope has not yet been checked."
        ),
        "scope_passed": (
            "The latest scope check found the current changed paths within the admitted path boundary; fresh completion evidence is not yet established."
        ),
        "scope_blocked": (
            "The latest scope check found one or more current changes outside or inconsistent with the admitted path boundary."
        ),
        "validation_recorded": (
            "The task's declared validation was recorded; completion still requires reconciliation against the same unchanged evidence."
        ),
        "needs_evidence": (
            "Completion cannot be verified because the admitted evidence contract is missing, failed, or no longer fresh."
        ),
        "review_ready": (
            "The current change set is within the admitted path scope, and the task's declared checks passed on an unchanged snapshot."
        ),
        "handed_off": (
            "A human ended AgentGov's routing responsibility for this bounded session; downstream authority remains separate."
        ),
        "invalid": (
            "AgentGov cannot safely determine the current task state from the available session and event records."
        ),
    }.get(stage, "AgentGov cannot safely explain the current task state.")


def _human_boundary(stage: str) -> Mapping[str, Any]:
    title, guidance = {
        "active_unchecked": (
            "Scope evidence required",
            "Run the existing governed scope observation before treating the current work as in scope.",
        ),
        "scope_passed": (
            "Fresh completion evidence required",
            "Use only the task's already admitted validation contract and then reconcile completion.",
        ),
        "scope_blocked": (
            "Human scope review required",
            "Keep the admitted scope and narrow the changes, or prepare a separately reviewed task revision; this view applies neither choice.",
        ),
        "validation_recorded": (
            "Completion reconciliation required",
            "Re-establish that the recorded validation still belongs to the same unchanged task and snapshot.",
        ),
        "needs_evidence": (
            "Evidence refresh required",
            "Review the recorded evidence limits and rerun only the admitted validation after the blocking condition is corrected.",
        ),
        "review_ready": (
            "Human review remains required",
            "Review the bounded work and evidence before any separate handoff or downstream authority decision.",
        ),
        "handed_off": (
            "No downstream authority granted",
            "The bounded session has ended; commit, merge, publish, release, and deploy remain separate human-owned transitions.",
        ),
        "invalid": (
            "Human investigation required",
            "Repair or re-establish the exact admitted task, session, and event binding before continuing.",
        ),
    }.get(
        stage,
        ("Human investigation required", "No safe next guidance is available from the current records."),
    )
    return {
        "availability": "read_only_guidance",
        "title": title,
        "guidance": guidance,
        "decision_applied": False,
    }


def _event_evidence(
    events: tuple[GovernanceEvent, ...],
    event_type: str,
) -> Mapping[str, Any]:
    matching = tuple(item for item in events if item.event_type == event_type)
    if not matching:
        return {"availability": "unavailable", "reason_code": f"{event_type.replace('.', '_')}_not_recorded"}
    latest = matching[-1]
    return {
        "availability": "available",
        "event_id": latest.event_id,
        "outcome": latest.outcome,
        "evidence_ref": latest.evidence_ref,
        "metrics": dict(sorted(latest.metrics.items())),
    }


def _scope_evidence(
    root: Path,
    events: tuple[GovernanceEvent, ...],
) -> Mapping[str, Any]:
    matching = tuple(item for item in events if item.event_type == "scope.checked")
    if not matching:
        return {"availability": "unavailable", "reason_code": "scope_check_not_recorded"}
    latest = matching[-1]
    if latest.evidence_ref is None:
        return {
            "availability": "unavailable",
            "reason_code": "scope_artifact_not_recorded",
            "event_id": latest.event_id,
            "outcome": latest.outcome,
        }
    try:
        report = load_scope_observation(
            root,
            latest.evidence_ref,
            expected_task_id=latest.task_id,
            expected_task_digest=latest.task_digest,
        )
    except ScopeObservationError:
        return {
            "availability": "unavailable",
            "reason_code": "scope_artifact_invalid",
            "event_id": latest.event_id,
            "outcome": latest.outcome,
        }
    affected_paths = []
    for change in report["changes"]:
        for endpoint in change["endpoints"]:
            affected_paths.append(
                {
                    "path": endpoint["path"],
                    "role": endpoint["role"],
                    "layer": change["layer"],
                    "change_status": change["status"],
                    "status": "PASS" if endpoint["admitted"] else "FAIL",
                    "admitted": endpoint["admitted"],
                    "matched_include": endpoint["matched_include"],
                    "matched_exclude": endpoint["matched_exclude"],
                    "reason": endpoint["reason"],
                }
            )
    return {
        "availability": "available",
        "event_id": latest.event_id,
        "outcome": latest.outcome,
        "evidence_ref": latest.evidence_ref,
        "head_sha": report["head_sha"],
        "affected_paths": affected_paths,
        "findings": list(report["findings"]),
        "known_limits": list(report["known_limits"]),
    }


def _active_task_view(
    root: Path,
    observation_scope: str,
    observed_events: tuple[_ObservedEvent, ...],
) -> Mapping[str, Any]:
    if observation_scope != "local_session":
        return _unavailable_active_task("active_task_requires_local_session")
    try:
        task_path, session = resolve_active_task(root)
        document = load_development_task(task_path)
    except (SessionPolicyError, OSError, UnicodeError, ValueError, json.JSONDecodeError):
        return _unavailable_active_task("active_task_not_safely_resolved")
    events = tuple(
        item.event
        for item in observed_events
        if item.event.task_id == session.task_id
        and item.event.task_digest == session.task_digest
        and item.event.occurred_at >= session.started_at
    )
    state = development_state_payload(project_development_state(session, events))
    requirement = document["requirement"]
    scope = document["scope"]
    decision = document["decision"]
    return {
        "availability": "available",
        "reason_code": "active_task_bound",
        "identity": {
            "task_id": session.task_id,
            "task_digest": session.task_digest,
            "task_path": task_path.relative_to(root).as_posix(),
            "title": document["title"],
            "profile": document["profile"],
            "decision_state": decision["state"],
        },
        "context": {
            "requirement_summary": requirement["summary"],
            "goal": document.get("goal"),
            "non_goals": list(document.get("non_goals", [])),
            "include_paths": list(scope["include_paths"]),
            "exclude_paths": list(scope["exclude_paths"]),
            "architecture_refs": list(document.get("architecture_refs", [])),
            "acceptance_signals": list(document["acceptance_signals"]),
        },
        "governance_state": {
            **state,
            "human_meaning": _state_meaning(state["stage"]),
        },
        "evidence": {
            "scope": _scope_evidence(root, events),
            "validation": _event_evidence(events, "validation.completed"),
            "completion": _event_evidence(events, "completion.reconciled"),
        },
        "activity_event_ids": [item.event_id for item in events],
        "human_boundary": _human_boundary(state["stage"]),
        "claim_limits": list(_ACTIVE_TASK_CLAIM_LIMITS),
        "authority": dict(_ACTIVE_TASK_AUTHORITY),
    }


def _safe_root(repository: Path) -> Path:
    if repository.is_symlink() or not repository.exists() or not repository.is_dir():
        raise MonitorPolicyError("repository root must be an existing non-symbolic-link directory")
    return repository.resolve()


def _timeline_entry(observed: _ObservedEvent) -> dict[str, Any]:
    event = observed.event
    return {
        "event_id": event.event_id,
        "occurred_at": event.occurred_at,
        "event_type": event.event_type,
        "source_scope": observed.source_scope,
        "actor_class": event.actor["class"],
        "actor_label": event.actor.get("label"),
        "task_id": event.task_id,
        "task_digest": event.task_digest,
        "outcome": event.outcome,
        "governance_refs": list(event.governance_refs),
        "reason_codes": list(event.reason_codes),
        "evidence_ref": event.evidence_ref,
        "metrics": dict(sorted(event.metrics.items())),
    }


def _task_detail(task_id: str, observed_events: tuple[_ObservedEvent, ...]) -> dict[str, Any]:
    events = tuple(item.event for item in observed_events)
    completion_events = tuple(item for item in events if item.event_type == "completion.reconciled")
    latest_completion = completion_events[-1] if completion_events else None
    handoff_events = tuple(item for item in events if item.event_type == "session.handed_off")
    latest_handoff = handoff_events[-1] if handoff_events else None
    return {
        "task_id": task_id,
        "task_digests": sorted({item.task_digest for item in events}),
        "event_count": len(events),
        "first_observed_at": events[0].occurred_at,
        "last_observed_at": events[-1].occurred_at,
        "task_starts": sum(item.event_type == "task.started" for item in events),
        "scope_checks": sum(item.event_type == "scope.checked" for item in events),
        "validations": sum(item.event_type == "validation.completed" for item in events),
        "completions": len(completion_events),
        "handoffs": len(handoff_events),
        "latest_event_type": events[-1].event_type,
        "latest_recorded_outcome": events[-1].outcome,
        "latest_completion_state": latest_completion.outcome if latest_completion else None,
        "latest_completion_at": latest_completion.occurred_at if latest_completion else None,
        "latest_routing_state": "handed_off" if latest_handoff else "active",
        "latest_handoff_at": latest_handoff.occurred_at if latest_handoff else None,
        "observed_failure_count": sum(item.metrics.get("failures", 0) for item in events),
        "observed_advisory_count": sum(item.metrics.get("advisories", 0) for item in events),
        "events": [_timeline_entry(item) for item in observed_events],
    }


def _live_session(
    task_id: str,
    task_digest: str,
    observed_events: tuple[_ObservedEvent, ...],
) -> dict[str, Any]:
    latest = observed_events[-1].event
    if latest.event_type == "session.handed_off":
        state = "handed_off"
    elif latest.event_type == "completion.reconciled" and latest.outcome == "verified":
        state = "review_ready"
    elif latest.outcome in {"failed", "stale", "needs_evidence"}:
        state = "needs_attention"
    else:
        state = "active"
    return {
        "task_id": task_id,
        "task_digest": task_digest,
        "state": state,
        "attention_required": state == "needs_attention",
        "latest_event_type": latest.event_type,
        "latest_recorded_outcome": latest.outcome,
        "last_observed_at": latest.occurred_at,
    }


def _protection_event(observed: _ObservedEvent) -> dict[str, Any] | None:
    event = observed.event
    protection_type = protection_signal_class(event)
    if protection_type is None:
        return None
    action_id, label = _PROTECTION_GUIDANCE[protection_type]
    return {
        "protection_id": f"protection:{event.event_id}",
        "source_event_id": event.event_id,
        "source_scope": observed.source_scope,
        "occurred_at": event.occurred_at,
        "task_id": event.task_id,
        "protection_type": protection_type,
        "observed_outcome": event.outcome,
        "status": "observed_resolution_unknown",
        "guidance": {
            "availability": "available",
            "action_id": action_id,
            "label": label,
            "target": "task_detail",
            "semantics": "read_only_navigation",
        },
        "reason_codes": list(event.reason_codes),
        "evidence_ref": event.evidence_ref,
    }


def _benefit_view(
    observation: Mapping[str, Any],
    overview: Mapping[str, int],
) -> Mapping[str, Any]:
    protection_count = overview["protection_events"]
    if protection_count:
        inference_status = "supported"
        inference_summary = (
            "Recorded Protection Events can support prioritizing human review; "
            "they do not prove prevention or causal benefit."
        )
        inference_reasons = [
            "protection_context_observed",
            "causality_not_established",
        ]
        inference_metrics = {
            "protection_events": protection_count,
            "sessions_needing_attention": overview["sessions_needing_attention"],
        }
    else:
        inference_status = "unavailable"
        inference_summary = (
            "No Protection Event is visible in this observation scope, so no "
            "review-prioritization inference is presented."
        )
        inference_reasons = ["protection_context_unavailable"]
        inference_metrics = {}
    return {
        "comparison_mode": "single_observation_only",
        "scope": observation["scope"],
        "observation_window": {
            "started_at": observation["started_at"],
            "ended_at": observation["ended_at"],
        },
        "cards": (
            {
                "card_id": "current_scope_activity",
                "claim_class": "observed_fact",
                "status": "observed",
                "semantics": "observed",
                "title": "Current-scope activity",
                "summary": (
                    "Validated events and direct counts visible in this scope; "
                    "these counts are not a benefit score."
                ),
                "reason_codes": ["validated_current_scope_counts"],
                "metrics": {
                    "tasks": overview["tasks"],
                    "events": overview["events"],
                    "protection_events": protection_count,
                    "verified_completions": overview["verified_completions"],
                    "handoffs": overview["handoffs"],
                },
            },
            {
                "card_id": "cross_window_comparison",
                "claim_class": "reproduced_comparison",
                "status": "unavailable",
                "semantics": "observed",
                "title": "Cross-window comparison",
                "summary": (
                    "No baseline or cross-window input was selected for Benefit "
                    "View v1."
                ),
                "reason_codes": [
                    "baseline_not_selected",
                    "denominator_unavailable",
                    "applicability_rules_unavailable",
                    "comparable_window_unavailable",
                ],
                "metrics": {},
            },
            {
                "card_id": "review_prioritization",
                "claim_class": "supported_inference",
                "status": inference_status,
                "semantics": "advisory",
                "title": "Review prioritization",
                "summary": inference_summary,
                "reason_codes": inference_reasons,
                "metrics": inference_metrics,
            },
            {
                "card_id": "attributed_human_feedback",
                "claim_class": "human_feedback",
                "status": "unavailable",
                "semantics": "human_judgment",
                "title": "Attributed human feedback",
                "summary": (
                    "Current Monitor events and Learning reviews do not record "
                    "attributed benefit feedback."
                ),
                "reason_codes": ["attributed_feedback_not_recorded"],
                "metrics": {},
            },
            {
                "card_id": "causal_benefit_limits",
                "claim_class": "unknown",
                "status": "unknown",
                "semantics": "unknown",
                "title": "Causal benefit limits",
                "summary": (
                    "Counterfactual outcomes, semantic correctness, causal "
                    "benefit, time savings, governance completeness, and return "
                    "on investment are unknown."
                ),
                "reason_codes": ["benefit_not_established"],
                "metrics": {},
            },
        ),
        "claim_limit": (
            "Single-observation cards do not prove causal benefit, prevention, "
            "time savings, governance completeness, or return on investment."
        ),
    }


def _learning_view(
    observation: Mapping[str, Any],
    protection_events: tuple[Mapping[str, Any], ...],
    learning_reviews: tuple[LearningReview, ...],
    *,
    review_source_available: bool,
) -> Mapping[str, Any]:
    counts = {
        protection_type: sum(
            item["protection_type"] == protection_type
            for item in protection_events
        )
        for protection_type in _PROTECTION_GUIDANCE
    }
    candidate_event_ids = {
        protection_type: tuple(
            sorted(
                item["source_event_id"]
                for item in protection_events
                if item["protection_type"] == protection_type
            )
        )
        for protection_type, count in counts.items()
        if count >= 2
    }
    candidate_digests = {
        protection_type: learning_candidate_digest(protection_type, identities)
        for protection_type, identities in candidate_event_ids.items()
    }
    candidates = tuple(
        {
            "signal_id": protection_type,
            "candidate_digest": candidate_digests[protection_type],
            "occurrences": count,
            "distinct_tasks": len(
                {
                    item["task_id"]
                    for item in protection_events
                    if item["protection_type"] == protection_type
                }
            ),
            "cross_task": len(
                {
                    item["task_id"]
                    for item in protection_events
                    if item["protection_type"] == protection_type
                }
            ) > 1,
        }
        for protection_type, count in counts.items()
        if count >= 2
    )
    matching_reviews = tuple(
        review
        for review in learning_reviews
        if candidate_digests.get(review.signal_class) == review.candidate_digest
    )
    stale_review_count = len(learning_reviews) - len(matching_reviews)
    disposition_counts = {
        disposition: sum(review.disposition == disposition for review in matching_reviews)
        for disposition in LEARNING_DISPOSITIONS
    }
    judgment_items = tuple(
        {
            "signal_id": review.signal_class,
            "disposition": review.disposition,
            "recorded_at": review.recorded_at,
            "actor_role": HUMAN_PRODUCT_OWNER_ROLE,
            "semantics": "human_judgment",
            "resolution": "unknown",
            "reason_codes": tuple(review.reason_codes),
        }
        for review in matching_reviews
    )
    if candidates:
        repeated_status = "candidates_observed"
        repeated_summary = (
            "Protection classes repeated within this observation are advisory "
            "review candidates, not evidence of shared cause or future recurrence."
        )
        repeated_reasons = ["recurrence_rule_met", "generalization_not_allowed"]
    else:
        repeated_status = "none_observed"
        repeated_summary = (
            "No Protection Event class reaches the two-event display rule in "
            "this observation; absence is not proof that friction is absent."
        )
        repeated_reasons = ["recurrence_rule_not_met", "absence_not_established"]
    if matching_reviews:
        judgment_status = "recorded"
        judgment_summary = (
            "Human-product-owner judgments match exact current candidates; "
            "they do not prove handling, resolution, shared cause, or benefit."
        )
        judgment_reasons = [
            "exact_candidate_bound_human_judgment",
            "resolution_not_established",
        ]
        judgment_metrics = {
            "matched_reviews": len(matching_reviews),
            **disposition_counts,
        }
    elif review_source_available:
        judgment_status = "unavailable"
        judgment_summary = (
            "No immutable human Learning review matches an exact current "
            "repeated-signal candidate."
        )
        judgment_reasons = ["human_disposition_not_recorded"]
        judgment_metrics = {}
    else:
        judgment_status = "unavailable"
        judgment_summary = (
            "The selected event source contains no local Learning review "
            "records, so attributed human judgment is unavailable."
        )
        judgment_reasons = ["learning_review_source_unavailable"]
        judgment_metrics = {}
    return {
        "mode": "current_observation_candidates",
        "scope": observation["scope"],
        "observation_window": {
            "started_at": observation["started_at"],
            "ended_at": observation["ended_at"],
        },
        "recurrence_rule": {
            "signal_source": "protection_type",
            "minimum_occurrences": 2,
            "requires_distinct_tasks": False,
            "generalization_allowed": False,
        },
        "human_review_source": {
            "availability": "available" if review_source_available else "unavailable",
            "source_kind": (
                "repository_local_learning_reviews"
                if review_source_available
                else "absent_from_selected_event_source"
            ),
            "records_read": len(learning_reviews),
            "matched_records": len(matching_reviews),
            "stale_records": stale_review_count,
        },
        "cards": (
            {
                "card_id": "observed_protection_signals",
                "learning_class": "observed_signal",
                "status": "observed",
                "semantics": "observed",
                "title": "Observed protection signals",
                "summary": (
                    "Direct counts for the existing deterministic Protection "
                    "Event classes in this observation."
                ),
                "reason_codes": ["validated_protection_class_counts"],
                "metrics": counts,
                "candidates": (),
                "judgments": (),
                "topics": (),
            },
            {
                "card_id": "repeated_protection_signals",
                "learning_class": "repeated_signal_candidate",
                "status": repeated_status,
                "semantics": "advisory",
                "title": "Repeated signal candidates",
                "summary": repeated_summary,
                "reason_codes": repeated_reasons,
                "metrics": {},
                "candidates": candidates,
                "judgments": (),
                "topics": (),
            },
            {
                "card_id": "human_learning_judgments",
                "learning_class": "human_judgment",
                "status": judgment_status,
                "semantics": "human_judgment",
                "title": "Human learning judgments",
                "summary": judgment_summary,
                "reason_codes": judgment_reasons,
                "metrics": judgment_metrics,
                "candidates": (),
                "judgments": judgment_items,
                "topics": (
                    "false_positive_disposition",
                    "missed_constraint_confirmation",
                    "override_outcome",
                    "consumer_local_configuration_need",
                    "general_improvement_decision",
                ),
            },
            {
                "card_id": "learning_limits",
                "learning_class": "unknown",
                "status": "unknown",
                "semantics": "unknown",
                "title": "Learning limits",
                "summary": (
                    "Causal improvement, applicability outside this scope and "
                    "window, transferability, future recurrence, time savings, "
                    "governance completeness, and return on investment are unknown."
                ),
                "reason_codes": ["learning_not_established"],
                "metrics": {},
                "candidates": (),
                "judgments": (),
                "topics": (
                    "causal_improvement",
                    "outside_scope_applicability",
                    "transferability",
                    "future_recurrence",
                    "time_savings",
                    "governance_completeness",
                    "return_on_investment",
                ),
            },
        ),
        "claim_limit": (
            "Current-observation repetition does not prove shared root cause, "
            "false-positive status, systemic weakness, improvement, "
            "transferability, future recurrence, or causal benefit."
        ),
    }


def _event_source(root: Path, event_directory: Path | None) -> Path:
    source = event_directory or root / ".agentgov" / "events"
    source = source if source.is_absolute() else root / source
    if source.is_symlink():
        raise MonitorPolicyError("event source must not be a symbolic link")
    source = source.resolve()
    try:
        source.relative_to(root)
    except ValueError as exc:
        raise MonitorPolicyError("event source must remain inside the repository") from exc
    return source


def _export_events(repository: Path, export_path: Path) -> tuple[tuple[GovernanceEvent, ...], Mapping[str, Any]]:
    try:
        bundle = load_development_event_export(repository, export_path)
    except DevelopmentExportPolicyError as exc:
        raise MonitorPolicyError(str(exc)) from exc
    events = tuple(
        governance_event_from_payload(payload, source_name="redacted-export-event.json")
        for payload in bundle.events
    )
    return events, bundle.source


def build_development_monitor(
    repository: Path,
    *,
    observation_scope: str = "local_session",
    event_directory: Path | None = None,
    export_path: Path | None = None,
    generated_at: str | None = None,
) -> DevelopmentMonitor:
    """Build a read-only Monitor from an explicitly declared observation source."""

    root = _safe_root(repository)
    if observation_scope not in MONITOR_SCOPES:
        raise MonitorPolicyError(f"observation scope must be one of {sorted(MONITOR_SCOPES)}")
    if observation_scope in {"exported_development", "combined"} and export_path is None:
        raise MonitorPolicyError(f"{observation_scope} Monitor requires --export with a validated redacted bundle")
    if observation_scope in {"local_session", "ci_only"} and export_path is not None:
        raise MonitorPolicyError(f"{observation_scope} Monitor does not consume a development export")
    if observation_scope == "exported_development" and event_directory is not None:
        raise MonitorPolicyError("exported_development Monitor consumes only the explicit export bundle")

    source_counts = {"local_session": 0, "exported_development": 0, "ci_only": 0}
    event_files_read = 0
    duplicates_removed = 0
    observed_events: tuple[_ObservedEvent, ...]
    if observation_scope in {"local_session", "ci_only"}:
        loaded = load_governance_events(_event_source(root, event_directory))
        events = loaded.events
        if observation_scope == "ci_only" and any(item.actor.get("class") != "ci" for item in events):
            raise MonitorPolicyError("ci_only Monitor cannot include human or coding_agent events")
        source_counts[observation_scope] = len(events)
        event_files_read = loaded.files_read
        duplicates_removed = loaded.duplicates_removed
        observed_events = tuple(_ObservedEvent(item, observation_scope) for item in events)
    else:
        exported_events, exported_source = _export_events(root, export_path)  # type: ignore[arg-type]
        source_counts["exported_development"] = len(exported_events)
        event_files_read = 1
        duplicates_removed = int(exported_source["duplicates_removed"])
        exported_observed = tuple(
            _ObservedEvent(item, "exported_development") for item in exported_events
        )
        if observation_scope == "exported_development":
            observed_events = exported_observed
        else:
            ci_loaded = load_governance_events(_event_source(root, event_directory))
            if not ci_loaded.events:
                raise MonitorPolicyError("combined Monitor requires at least one CI replay event")
            if any(item.actor.get("class") != "ci" for item in ci_loaded.events):
                raise MonitorPolicyError("combined Monitor local event input must contain only CI replay events")
            exported_ids = {item.event_id for item in exported_events}
            overlap = exported_ids & {item.event_id for item in ci_loaded.events}
            if overlap:
                raise MonitorPolicyError(
                    f"combined Monitor has event_id present in both sources: {sorted(overlap)[0]}"
                )
            source_counts["ci_only"] = len(ci_loaded.events)
            event_files_read += ci_loaded.files_read
            duplicates_removed += ci_loaded.duplicates_removed
            observed_events = exported_observed + tuple(
                _ObservedEvent(item, "ci_only") for item in ci_loaded.events
            )
            observed_events = tuple(
                sorted(observed_events, key=lambda item: (item.event.occurred_at, item.event.event_id))
            )

    events = tuple(item.event for item in observed_events)
    timeline = tuple(_timeline_entry(item) for item in observed_events)
    by_task: dict[str, list[_ObservedEvent]] = {}
    for item in observed_events:
        by_task.setdefault(item.event.task_id, []).append(item)
    tasks = tuple(
        _task_detail(task_id, tuple(task_events))
        for task_id, task_events in sorted(by_task.items())
    )
    by_session: dict[tuple[str, str], list[_ObservedEvent]] = {}
    for item in observed_events:
        key = (item.event.task_id, item.event.task_digest)
        by_session.setdefault(key, []).append(item)
    live_sessions = tuple(
        _live_session(task_id, task_digest, tuple(session_events))
        for (task_id, task_digest), session_events in sorted(by_session.items())
    )
    protection_events = tuple(
        item
        for item in (_protection_event(observed) for observed in observed_events)
        if item is not None
    )
    overview = {
        "tasks": len(tasks),
        "events": len(events),
        "task_starts": sum(item.event_type == "task.started" for item in events),
        "scope_checks": sum(item.event_type == "scope.checked" for item in events),
        "validations": sum(item.event_type == "validation.completed" for item in events),
        "completions": sum(item.event_type == "completion.reconciled" for item in events),
        "handoffs": sum(item.event_type == "session.handed_off" for item in events),
        "passed_events": sum(item.outcome == "passed" for item in events),
        "failed_events": sum(item.outcome == "failed" for item in events),
        "stale_events": sum(item.outcome == "stale" for item in events),
        "verified_completions": sum(
            item.event_type == "completion.reconciled" and item.outcome == "verified"
            for item in events
        ),
        "needs_evidence_completions": sum(
            item.event_type == "completion.reconciled" and item.outcome == "needs_evidence"
            for item in events
        ),
        "event_reported_failures": sum(item.metrics.get("failures", 0) for item in events),
        "event_reported_advisories": sum(item.metrics.get("advisories", 0) for item in events),
        "protection_events": len(protection_events),
        "sessions_needing_attention": sum(
            item["attention_required"] for item in live_sessions
        ),
    }
    if observation_scope == "ci_only":
        missing_sources = (
            "pre-code and local development events were not exported to this CI observation",
            "other CI runs and deleted artifacts are not present",
        )
        source_kind = "ci_job_local_events"
    elif observation_scope == "local_session":
        missing_sources = (
            "events recorded before this local store existed are unavailable",
            "other working copies, machines, and CI runs are not present",
            "deleted local events cannot be reconstructed",
        )
        source_kind = "repository_local_event_store"
    elif observation_scope == "exported_development":
        missing_sources = (
            "development events absent from the explicit export, other working copies, and other machines are not present",
            "actor labels and local evidence references were intentionally removed",
            "CI replay events are not present",
        )
        source_kind = "redacted_development_export"
    else:
        missing_sources = (
            "development events absent from the explicit export, other working copies, and other machines are not present",
            "CI runs outside the provided replay event store and deleted artifacts are not present",
            "actor labels and local evidence references were intentionally removed from development events",
            "cross-stage finding identity and resolution links do not exist",
        )
        source_kind = "combined_sources"
    observation = {
        "scope": observation_scope,
        "source_kind": source_kind,
        "source_event_counts": source_counts,
        "event_files_read": event_files_read,
        "duplicates_removed": duplicates_removed,
        "event_count": len(events),
        "started_at": events[0].occurred_at if events else None,
        "ended_at": events[-1].occurred_at if events else None,
        "history_completeness": "partial",
        "missing_sources": list(missing_sources),
        "cross_stage_discovery_available": False,
    }
    active_task = _active_task_view(root, observation_scope, observed_events)
    benefit = _benefit_view(observation, overview)
    learning_reviews: tuple[LearningReview, ...] = ()
    review_source_available = observation_scope == "local_session"
    if review_source_available:
        try:
            learning_reviews = load_learning_reviews(root)
        except LearningReviewPolicyError as exc:
            raise MonitorPolicyError(str(exc)) from exc
    learning = _learning_view(
        observation,
        protection_events,
        learning_reviews,
        review_source_available=review_source_available,
    )
    monitor_generated_at = generated_at or utc_now()
    drift_review = asdict(
        build_drift_review_status(root, as_of=monitor_generated_at, events=events)
    )
    claim_layers = {
        "observed": (
            "Event timestamps, actor classes, task identities, trigger reason codes, outcomes, and small counters come from validated event records.",
            "Selected governance paths come from confirmed task-start routing; they show selection, not coding-agent consumption.",
            "Each timeline source label comes from the explicitly selected local, export, or CI input boundary rather than a semantic inference.",
            "Latest recorded outcome means the chronologically latest event visible in this observation scope.",
            "Verified completion and handed-off routing are counted separately; handoff records routing responsibility, not semantic approval.",
            "Protection Events are deterministic read-model classifications of failed, stale, or incomplete recorded outcomes.",
            "Protection Event guidance is deterministic read-only navigation to visible Task Detail; it is not remediation or resolution evidence.",
            "Attributed Learning judgments come only from immutable local records bound to the exact current repeated-signal candidate.",
        ),
        "inferred": (
            "Chronological grouping suggests a task activity sequence but does not prove that one event caused another.",
        ),
        "unknown": (
            "Events do not prove requirement satisfaction, architecture correctness, validation sufficiency, causal benefit, or return on investment.",
            "Which routed governance artifacts or Skills the coding agent actually consumed is unknown until context-consumption events exist.",
            "Human handling and resolution are unknown unless a future explicit handling or resolution record establishes them.",
            "A later passing event does not prove that a Protection Event was resolved because cross-event resolution links do not yet exist.",
            "History outside the displayed observation scope is unknown.",
        ),
    }
    return DevelopmentMonitor(
        contract=MONITOR_CONTRACT,
        schema_version=MONITOR_SCHEMA_VERSION,
        generated_at=monitor_generated_at,
        observation=observation,
        active_task=active_task,
        overview=overview,
        live_sessions=live_sessions,
        protection_events=protection_events,
        timeline=timeline,
        tasks=tasks,
        benefit=benefit,
        learning=learning,
        drift_review=drift_review,
        claim_layers=claim_layers,
        authority_boundary={
            "approves_governance": False,
            "writes_governance_files": False,
            "authorizes_exception": False,
            "authorizes_commit": False,
            "authorizes_merge": False,
            "authorizes_deployment": False,
        },
    )


def render_development_monitor_json(monitor: DevelopmentMonitor) -> str:
    return json.dumps(asdict(monitor), ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _display(value: Any) -> str:
    if value is None:
        return "Unknown"
    return str(value).replace("_", " ")


def _markdown_link_label(value: Any) -> str:
    return str(value).replace("\\", "\\\\").replace("[", "\\[").replace("]", "\\]")


def _task_anchor(task_id: Any) -> str:
    identity = uuid.uuid5(
        uuid.NAMESPACE_OID,
        f"{MONITOR_CONTRACT}:{task_id}",
    ).hex
    return f"task-detail-{identity}"


def _guidance_available(guidance: Any) -> bool:
    return (
        isinstance(guidance, Mapping)
        and guidance.get("availability") == "available"
        and isinstance(guidance.get("action_id"), str)
        and bool(guidance.get("action_id"))
        and isinstance(guidance.get("label"), str)
        and bool(guidance.get("label"))
        and guidance.get("target") == "task_detail"
        and guidance.get("semantics") == "read_only_navigation"
    )


def _guidance_markdown(guidance: Any, task_id: Any) -> str:
    if _guidance_available(guidance):
        label = _markdown_link_label(guidance.get("label", "Review task detail"))
        return f"[{label}](#{_task_anchor(task_id)})"
    return "unavailable"


def _guidance_html(guidance: Any, task_id: Any) -> str:
    if _guidance_available(guidance):
        label = html.escape(_display(guidance.get("label")), quote=True)
        return (
            f'<a class="resolution-link" href="#{_task_anchor(task_id)}">'
            f"{label}</a>"
        )
    return "Unavailable"


def _task_attention(
    task: Mapping[str, Any],
    protection_events: tuple[Mapping[str, Any], ...],
) -> Mapping[str, Any] | None:
    matching = tuple(
        item
        for item in protection_events
        if item.get("task_id") == task.get("task_id")
    )
    if not matching:
        return None
    protection = max(
        matching,
        key=lambda item: (
            str(item.get("occurred_at", "")),
            str(item.get("source_event_id", "")),
        ),
    )
    source_event = next(
        (
            item
            for item in task.get("events", ())
            if item.get("event_id") == protection.get("source_event_id")
        ),
        None,
    )
    guidance = protection.get("guidance")
    if not isinstance(guidance, Mapping):
        guidance = {}
    metrics = source_event.get("metrics", {}) if source_event else {}
    return {
        "source_event_id": protection.get("source_event_id"),
        "protection_type": protection.get("protection_type"),
        "observed_outcome": protection.get("observed_outcome"),
        "reason_codes": tuple(protection.get("reason_codes", ())),
        "metrics": dict(sorted(metrics.items())) if isinstance(metrics, Mapping) else {},
        "next_action": (
            guidance.get("label") if _guidance_available(guidance) else None
        ),
        "resolution": "unknown",
    }


def _activity_meaning(event_type: str, outcome: str) -> str:
    if event_type == "task.started":
        return "Work began under this admitted task record."
    if event_type == "scope.checked" and outcome == "passed":
        return "AgentGov checked the current working copy; the observed changed paths were within the admitted path boundary."
    if event_type == "scope.checked" and outcome == "failed":
        return "AgentGov observed one or more current changes outside or inconsistent with the admitted path boundary."
    if event_type == "validation.completed":
        return "The task's declared validation was run and recorded."
    if event_type == "completion.reconciled" and outcome == "verified":
        return "Fresh evidence matched the unchanged admitted task and snapshot."
    if event_type == "completion.reconciled":
        return "Completion remains unverified within the admitted evidence contract."
    if event_type == "session.handed_off":
        return "A human ended AgentGov's routing responsibility for this bounded session."
    return "AgentGov recorded a bounded governance observation."


def _active_task_events(monitor: DevelopmentMonitor) -> tuple[Mapping[str, Any], ...]:
    active = monitor.active_task
    if active.get("availability") != "available":
        return ()
    event_ids = set(active.get("activity_event_ids", ()))
    return tuple(item for item in monitor.timeline if item.get("event_id") in event_ids)


def _active_scope_paths_for_event(
    monitor: DevelopmentMonitor,
    event_id: Any,
) -> tuple[Mapping[str, Any], ...] | None:
    active = monitor.active_task
    if active.get("availability") != "available":
        return None
    evidence = active.get("evidence")
    if not isinstance(evidence, Mapping):
        return None
    scope = evidence.get("scope")
    if (
        not isinstance(scope, Mapping)
        or scope.get("availability") != "available"
        or scope.get("event_id") != event_id
    ):
        return None
    paths = scope.get("affected_paths")
    if not isinstance(paths, list):
        return None
    return tuple(item for item in paths if isinstance(item, Mapping))


def _render_active_task_markdown(monitor: DevelopmentMonitor) -> list[str]:
    active = monitor.active_task
    lines = ["", "## Active Task", ""]
    if active.get("availability") != "available":
        lines.extend(
            [
                "- Availability: `unavailable`",
                f"- Reason: `{active['reason_code']}`",
                "- This Monitor does not infer task context from aggregate, exported, or incomplete records.",
            ]
        )
    else:
        identity = active["identity"]
        context = active["context"]
        state = active["governance_state"]
        boundary = active["human_boundary"]
        scope = active["evidence"]["scope"]
        lines.extend(
            [
                f"### {identity['title']}",
                "",
                f"- Task: `{identity['task_id']}`",
                f"- Decision: `{identity['decision_state']}`",
                f"- Requirement: {context['requirement_summary']}",
                f"- Included paths: `{', '.join(context['include_paths'])}`",
                f"- Excluded paths: `{', '.join(context['exclude_paths']) or 'none declared'}`",
                "",
                "### Current governance state",
                "",
                state["human_meaning"],
                "",
                f"- Technical state: `{state['stage']}`",
                f"- Reason: `{state['reason_code']}`",
                f"- Blocking: `{str(state['blocking']).lower()}`",
                "",
                "### Scope evidence",
                "",
            ]
        )
        if scope["availability"] == "available":
            if scope["affected_paths"]:
                lines.extend(["| Status | Path | Change | Why |", "|---|---|---|---|"])
                for item in scope["affected_paths"]:
                    reason = str(item["reason"]).replace("|", "\\|").replace("\n", " ")
                    lines.append(
                        f"| {item['status']} | `{item['path']}` | `{item['layer']}:{item['change_status']}` | {reason} |"
                    )
            else:
                lines.append("- No staged, unstaged, or non-ignored untracked path was recorded.")
            lines.append(f"- Evidence: `{scope['evidence_ref']}`")
        else:
            lines.extend(
                [
                    "- Affected paths: `unavailable`",
                    f"- Reason: `{scope['reason_code']}`",
                    "- Paths are not inferred from current repository state or governance references.",
                ]
            )
        lines.extend(
            [
                "",
                "### Human boundary",
                "",
                f"- {boundary['title']}: {boundary['guidance']}",
                "- Decision applied by this view: `false`",
                "",
                "### Task activity",
                "",
            ]
        )
        for event in _active_task_events(monitor):
            lines.append(
                f"- `{event['occurred_at']}` - {_activity_meaning(event['event_type'], event['outcome'])} Technical event: `{event['event_type']}` / `{event['outcome']}`."
            )
        if not active["activity_event_ids"]:
            lines.append("- No exact session event is visible.")
    lines.extend(["", "### Authority not granted", ""])
    lines.extend(
        f"- `{key.removeprefix('authorizes_')}`: `NOT GRANTED`"
        for key in active["authority"]
    )
    lines.extend(["", "### Active Task claim limits", ""])
    lines.extend(f"- {item}" for item in active["claim_limits"])
    return lines


def render_development_monitor_markdown(monitor: DevelopmentMonitor) -> str:
    observation = monitor.observation
    lines = [
        "# AgentGov development Monitor",
        "",
        f"- Observation scope: `{observation['scope']}`",
        f"- History completeness: `{observation['history_completeness']}`",
        f"- Events: `{observation['event_count']}`",
        "- Source events: " + ", ".join(
            f"`{key}={value}`" for key, value in observation["source_event_counts"].items()
        ),
        f"- Interval: `{_display(observation['started_at'])}` to `{_display(observation['ended_at'])}`",
        f"- Cross-stage discovery comparison: `unavailable`",
        "",
        "## Overview",
        "",
        "| Measure | Observed value |",
        "|---|---:|",
    ]
    lines.extend(f"| {key.replace('_', ' ')} | {value} |" for key, value in monitor.overview.items())
    lines.extend(_render_active_task_markdown(monitor))
    lines.extend(
        [
            "",
            "## Drift Review Reminder",
            "",
            f"- State: `{monitor.drift_review['state']}`",
            f"- Reasons: `{', '.join(monitor.drift_review['reason_codes'])}`",
            "- Dimensions: `requirement`, `architecture`, `functionality`",
            "- Semantics: `ADVISORY`; the deterministic due state is not a drift verdict.",
            "- Available responses: run an evidence-bounded review or record a seven-day snooze.",
        ]
    )
    lines.extend(["", "## Live Sessions", ""])
    if monitor.live_sessions:
        lines.extend(
            f"- `{item['task_id']}` — `{item['state']}` — latest `{item['latest_event_type']}` / `{item['latest_recorded_outcome']}`"
            for item in monitor.live_sessions
        )
    else:
        lines.append("- No sessions are visible in this observation scope.")
    lines.extend(["", "## Protection Events", ""])
    if monitor.protection_events:
        lines.extend(
            f"- `{item['occurred_at']}` — `{item['task_id']}` — `{item['protection_type']}` — resolution `unknown`; guidance {_guidance_markdown(item.get('guidance'), item['task_id'])}"
            for item in monitor.protection_events
        )
    else:
        lines.append("- No protection event is visible in this observation scope.")
    lines.extend(["", "## Activity Timeline", ""])
    if monitor.timeline:
        lines.extend(
            f"- `{item['occurred_at']}` — source `{item['source_scope']}` — `{item['task_id']}` — `{item['event_type']}` — `{item['outcome']}` — reasons: `{', '.join(item['reason_codes']) or 'unknown'}`"
            for item in monitor.timeline
        )
    else:
        lines.append("- No events are visible in this observation scope.")
    lines.extend(["", "## Task Detail", ""])
    for task in monitor.tasks:
        attention = _task_attention(task, monitor.protection_events)
        lines.extend(
            [
                f'<a id="{_task_anchor(task["task_id"])}"></a>',
                f"### {task['task_id']}",
                "",
                f"- Events: `{task['event_count']}`",
                f"- Latest recorded outcome: `{task['latest_recorded_outcome']}`",
                f"- Latest completion state: `{_display(task['latest_completion_state'])}`",
                f"- Latest routing state: `{task['latest_routing_state']}`",
            ]
        )
        if attention:
            reasons = ", ".join(attention["reason_codes"]) or "none recorded"
            counts = ", ".join(
                f"{key}={value}" for key, value in attention["metrics"].items()
            ) or "none recorded"
            affected_paths = _active_scope_paths_for_event(
                monitor, attention["source_event_id"]
            )
            if affected_paths is None:
                path_lines = [
                    "- Affected paths: `unavailable` - no valid event-referenced path-level scope artifact is available."
                ]
            elif affected_paths:
                path_lines = [
                    "- Affected paths: "
                    + ", ".join(
                        f"`{item['path']}` ({item['status']})" for item in affected_paths
                    )
                ]
            else:
                path_lines = ["- Affected paths: `none recorded`"]
            lines.extend(
                [
                    f"- Needs attention: `{_display(attention['protection_type'])}` / `{_display(attention['observed_outcome'])}`",
                    f"- Observed reasons: `{reasons}`",
                    f"- Recorded counts: `{counts}`",
                    *path_lines,
                    f"- Next human action: `{_display(attention['next_action'])}`",
                    "- Resolution: `unknown`; navigation and review guidance do not prove handling or resolution.",
                ]
            )
        lines.append("")
    if not monitor.tasks:
        lines.append("No task events are visible.\n")
    benefit = monitor.benefit
    window = benefit["observation_window"]
    lines.extend(
        [
            "## Benefit",
            "",
            f"- Evidence mode: `{benefit['comparison_mode']}`",
            f"- Observation scope: `{benefit['scope']}`",
            f"- Observation window: `{_display(window['started_at'])}` to `{_display(window['ended_at'])}`",
            "",
        ]
    )
    for card in benefit["cards"]:
        counts = ", ".join(
            f"{key}={value}" for key, value in card["metrics"].items()
        ) or "none recorded"
        reasons = ", ".join(card["reason_codes"])
        lines.extend(
            [
                f"### {card['title']}",
                "",
                f"- Claim class: `{card['claim_class']}`",
                f"- Status: `{card['status']}`",
                f"- Semantics: `{card['semantics']}`",
                f"- Summary: {card['summary']}",
                f"- Recorded counts: `{counts}`",
                f"- Evidence reasons: `{reasons}`",
                "",
            ]
        )
    lines.extend([f"> Claim limit: {benefit['claim_limit']}", ""])
    learning = monitor.learning
    learning_window = learning["observation_window"]
    recurrence_rule = learning["recurrence_rule"]
    human_review_source = learning["human_review_source"]
    lines.extend(
        [
            "## Learning",
            "",
            f"- Evidence mode: `{learning['mode']}`",
            f"- Observation scope: `{learning['scope']}`",
            f"- Observation window: `{_display(learning_window['started_at'])}` to `{_display(learning_window['ended_at'])}`",
            f"- Recurrence rule: `{recurrence_rule['signal_source']}` appears at least `{recurrence_rule['minimum_occurrences']}` times; distinct tasks required `{str(recurrence_rule['requires_distinct_tasks']).lower()}`; generalization allowed `{str(recurrence_rule['generalization_allowed']).lower()}`",
            f"- Human review source: `{human_review_source['availability']}` / `{human_review_source['source_kind']}`; records read `{human_review_source['records_read']}`, matched `{human_review_source['matched_records']}`, stale `{human_review_source['stale_records']}`",
            "",
        ]
    )
    for card in learning["cards"]:
        counts = ", ".join(
            f"{key}={value}" for key, value in card["metrics"].items()
        ) or "none recorded"
        candidates = "; ".join(
            f"{item['signal_id']}: occurrences={item['occurrences']}, distinct_tasks={item['distinct_tasks']}, cross_task={str(item['cross_task']).lower()}"
            for item in card["candidates"]
        ) or "none observed"
        topics = ", ".join(card["topics"]) or "none"
        judgments = "; ".join(
            "{}: disposition={}, actor role={}, resolution={}".format(
                item["signal_id"],
                item["disposition"],
                item["actor_role"],
                item["resolution"],
            )
            for item in card["judgments"]
        ) or "none recorded"
        reasons = ", ".join(card["reason_codes"])
        lines.extend(
            [
                f"### {card['title']}",
                "",
                f"- Learning class: `{card['learning_class']}`",
                f"- Status: `{card['status']}`",
                f"- Semantics: `{card['semantics']}`",
                f"- Summary: {card['summary']}",
                f"- Recorded counts: `{counts}`",
                f"- Repeated candidates: `{candidates}`",
                f"- Attributed judgments: `{judgments}`",
                f"- Bounded topics: `{topics}`",
                f"- Evidence reasons: `{reasons}`",
                "",
            ]
        )
    lines.extend([f"> Claim limit: {learning['claim_limit']}", ""])
    lines.extend(["## Claim limits", ""])
    for layer in ("observed", "inferred", "unknown"):
        lines.append(f"### {layer.title()}\n")
        lines.extend(f"- {item}" for item in monitor.claim_layers[layer])
        lines.append("")
    return "\n".join(lines)


def _render_active_task_html(monitor: DevelopmentMonitor) -> str:
    esc = lambda value: html.escape(_display(value), quote=True)
    active = monitor.active_task
    authority = "".join(
        '<div class="authority-row"><span>'
        + esc(key.removeprefix("authorizes_"))
        + "</span><strong>NOT GRANTED</strong></div>"
        for key in active["authority"]
    )
    limits = "".join(f"<li>{esc(item)}</li>" for item in active["claim_limits"])
    if active.get("availability") != "available":
        body = (
            '<div class="active-unavailable"><strong>Active Task detail unavailable</strong>'
            f'<p>Reason: <code>{esc(active["reason_code"])}</code></p>'
            "<p>Task context is not inferred from aggregate, exported, or incomplete records.</p></div>"
        )
    else:
        identity = active["identity"]
        context = active["context"]
        state = active["governance_state"]
        boundary = active["human_boundary"]
        scope = active["evidence"]["scope"]
        if scope["availability"] == "available":
            if scope["affected_paths"]:
                path_rows = "".join(
                    '<tr><td><b class="path-status '
                    + esc(item["status"].lower())
                    + '">'
                    + esc(item["status"])
                    + "</b></td><td><code>"
                    + esc(item["path"])
                    + "</code></td><td>"
                    + esc(f"{item['layer']}:{item['change_status']}")
                    + "</td><td>"
                    + esc(item["reason"])
                    + "</td></tr>"
                    for item in scope["affected_paths"]
                )
                scope_html = (
                    '<div class="scope-table-wrap"><table class="scope-table"><thead><tr>'
                    "<th>Status</th><th>Path</th><th>Change</th><th>Why</th>"
                    f"</tr></thead><tbody>{path_rows}</tbody></table></div>"
                    f'<p class="evidence-ref">Evidence <code>{esc(scope["evidence_ref"])}</code></p>'
                )
            else:
                scope_html = (
                    '<p class="empty">No staged, unstaged, or non-ignored untracked path was recorded.</p>'
                    f'<p class="evidence-ref">Evidence <code>{esc(scope["evidence_ref"])}</code></p>'
                )
        else:
            scope_html = (
                '<div class="active-unavailable"><strong>Affected paths unavailable</strong>'
                f'<p>Reason: <code>{esc(scope["reason_code"])}</code></p>'
                "<p>Paths are not inferred from current repository state or governance references.</p></div>"
            )
        activity = "".join(
            '<li><time>'
            + esc(event["occurred_at"])
            + "</time><p>"
            + esc(_activity_meaning(event["event_type"], event["outcome"]))
            + "</p><code>"
            + esc(f"{event['event_type']} / {event['outcome']}")
            + "</code></li>"
            for event in _active_task_events(monitor)
        ) or "<li>No exact session event is visible.</li>"
        includes = "".join(f"<li><code>{esc(item)}</code></li>" for item in context["include_paths"])
        excludes = "".join(f"<li><code>{esc(item)}</code></li>" for item in context["exclude_paths"]) or "<li>None declared</li>"
        body = (
            '<div class="active-heading"><div><span class="eyebrow">Current governed work</span>'
            f'<h3>{esc(identity["title"])}</h3><p><code>{esc(identity["task_id"])}</code> &middot; decision <b>{esc(identity["decision_state"])}</b></p>'
            f'</div><b class="state-pill {esc(state["stage"])}">{esc(state["stage"])}</b></div>'
            f'<p class="active-requirement">{esc(context["requirement_summary"])}</p>'
            '<div class="active-grid"><section><h3>Admitted boundary</h3><div class="scope-columns">'
            f'<div><small>Included</small><ul>{includes}</ul></div><div><small>Excluded</small><ul>{excludes}</ul></div>'
            "</div></section><section class=\"state-card\"><h3>Current governance state</h3>"
            f'<p>{esc(state["human_meaning"])}</p><dl><dt>Technical state</dt><dd><code>{esc(state["stage"])}</code></dd>'
            f'<dt>Reason</dt><dd><code>{esc(state["reason_code"])}</code></dd><dt>Blocking</dt><dd>{esc(str(state["blocking"]).lower())}</dd></dl></section></div>'
            f'<section class="active-evidence"><h3>Scope evidence</h3>{scope_html}</section>'
            '<div class="active-grid"><section class="boundary-card"><h3>'
            + esc(boundary["title"])
            + "</h3><p>"
            + esc(boundary["guidance"])
            + "</p><small>Read-only guidance &middot; decision applied false</small></section>"
            f'<section><h3>Task activity</h3><ol class="active-activity">{activity}</ol></section></div>'
        )
    return (
        '<section class="panel active-task" id="active-task"><h2>Active Task</h2>'
        '<p class="sub">One exact local task: context, observed evidence, current state, human boundary, and denied downstream authority.</p>'
        + body
        + f'<div class="authority-panel"><h3>Authority not granted</h3>{authority}</div>'
        + f'<details class="active-limits"><summary>Active Task claim limits</summary><ul>{limits}</ul></details>'
        + "</section>"
    )


def render_development_monitor_html(monitor: DevelopmentMonitor) -> str:
    esc = lambda value: html.escape(_display(value), quote=True)
    observation = monitor.observation
    drift_review = monitor.drift_review
    active_task_html = _render_active_task_html(monitor)
    cards = "".join(
        f'<article class="metric"><span>{esc(key)}</span><strong>{value}</strong></article>'
        for key, value in (
            ("Tasks", monitor.overview["tasks"]),
            ("Governance events", monitor.overview["events"]),
            ("Task starts", monitor.overview["task_starts"]),
            ("Scope checks", monitor.overview["scope_checks"]),
            ("Validations", monitor.overview["validations"]),
            ("Verified completions", monitor.overview["verified_completions"]),
            ("Session handoffs", monitor.overview["handoffs"]),
            ("Protection events", monitor.overview["protection_events"]),
            ("Needs attention", monitor.overview["sessions_needing_attention"]),
        )
    )
    missing = "".join(f"<li>{esc(item)}</li>" for item in observation["missing_sources"])
    layers = "".join(
        f'<article class="claim {layer}"><h3>{esc(layer.title())}</h3><ul>'
        + "".join(f"<li>{esc(item)}</li>" for item in monitor.claim_layers[layer])
        + "</ul></article>"
        for layer in ("observed", "inferred", "unknown")
    )
    if monitor.timeline:
        timeline = "".join(
            '<li class="event">'
            f'<time>{esc(item["occurred_at"])}</time>'
            f'<div><div class="event-head"><span class="kind">{esc(item["event_type"])}</span>'
            f'<span class="outcome {esc(item["outcome"])}">{esc(item["outcome"])}</span></div>'
            f'<h3>{esc(item["task_id"])}</h3>'
            f'<p>Source: {esc(item["source_scope"])}</p>'
            f'<p>Actor: {esc(item["actor_class"])}{(" · " + esc(item["actor_label"])) if item["actor_label"] else ""}</p>'
            f'<p>Why: {esc(", ".join(item["reason_codes"]) or "unknown — no trigger reason was recorded")}</p>'
            f'<p>Selected governance: {esc(", ".join(item["governance_refs"]) or "none recorded")}</p>'
            f'<p>Observed counts: {esc(", ".join(f"{key}={value}" for key, value in item["metrics"].items()) or "none")}</p>'
            "</div></li>"
            for item in monitor.timeline
        )
    else:
        timeline = '<li class="empty">No governance events are visible in this observation scope.</li>'
    if monitor.tasks:
        rendered_tasks = []
        for task in monitor.tasks:
            attention = _task_attention(task, monitor.protection_events)
            task_class = "task task-attention" if attention else "task"
            open_state = " open" if attention else ""
            attention_html = ""
            if attention:
                reasons = ", ".join(attention["reason_codes"]) or "none recorded"
                counts = ", ".join(
                    f"{key}={value}" for key, value in attention["metrics"].items()
                ) or "none recorded"
                affected_paths = _active_scope_paths_for_event(
                    monitor, attention["source_event_id"]
                )
                if affected_paths is None:
                    affected_paths_html = (
                        "Unavailable - no valid event-referenced path-level scope artifact is available."
                    )
                elif affected_paths:
                    affected_paths_html = ", ".join(
                        f"{item['path']} ({item['status']})" for item in affected_paths
                    )
                else:
                    affected_paths_html = "None recorded"
                attention_html = (
                    '<section class="attention-context" aria-label="Protection context">'
                    '<div class="attention-heading"><span>Needs attention</span>'
                    f'<strong>{esc(_display(attention["protection_type"]))}</strong></div>'
                    '<div class="attention-grid">'
                    f'<div><small>Observed outcome</small><strong>{esc(attention["observed_outcome"])}</strong></div>'
                    f'<div><small>Observed reasons</small><strong>{esc(reasons)}</strong></div>'
                    f'<div><small>Recorded counts</small><strong>{esc(counts)}</strong></div>'
                    f'<div><small>Affected paths</small><strong>{esc(affected_paths_html)}</strong></div>'
                    "</div>"
                    '<p class="next-action"><span>Next human action</span>'
                    f'<strong>{esc(attention["next_action"])}</strong></p>'
                    '<p class="task-note">Resolution remains unknown. Navigation and review guidance do not prove handling or resolution.</p>'
                    "</section>"
                )
            rendered_tasks.append(
                f'<details class="{task_class}" id="{_task_anchor(task["task_id"])}"{open_state}>'
                f'<summary><span>{esc(task["task_id"])}</span><b>{esc(task["latest_recorded_outcome"])}</b></summary>'
                + attention_html
                + '<div class="task-grid">'
                + f'<div><small>First observed</small><strong>{esc(task["first_observed_at"])}</strong></div>'
                + f'<div><small>Last observed</small><strong>{esc(task["last_observed_at"])}</strong></div>'
                + f'<div><small>Starts / checks / validations / completions / handoffs</small><strong>{task["task_starts"]} / {task["scope_checks"]} / {task["validations"]} / {task["completions"]} / {task["handoffs"]}</strong></div>'
                + f'<div><small>Completion / routing</small><strong>{esc(task["latest_completion_state"])} / {esc(task["latest_routing_state"])}</strong></div>'
                + "</div>"
                + '<p class="task-note">Handling remains unknown unless an explicit handling or resolution record establishes it. A Learning judgment or later outcome is not presented as proof that an earlier issue was caused or resolved by AgentGov.</p>'
                + "</details>"
            )
        task_cards = "".join(rendered_tasks)
    else:
        task_cards = '<div class="empty">No task details are available.</div>'
    if monitor.live_sessions:
        live_sessions = "".join(
            '<article class="metric">'
            f'<span>{esc(item["task_id"])}</span><strong>{esc(item["state"])}</strong>'
            f'<small>Latest: {esc(item["latest_event_type"])} / {esc(item["latest_recorded_outcome"])}</small>'
            "</article>"
            for item in monitor.live_sessions
        )
    else:
        live_sessions = '<div class="empty">No sessions are visible in this observation scope.</div>'
    if monitor.protection_events:
        protections = "".join(
            '<article class="task">'
            f'<summary><span>{esc(item["protection_type"])}</span><b>{esc(item["task_id"])}</b></summary>'
            '<div class="task-grid">'
            f'<div><small>Observed</small><strong>{esc(item["occurred_at"])}</strong></div>'
            f'<div><small>Outcome</small><strong>{esc(item["observed_outcome"])}</strong></div>'
            f'<div><small>Source</small><strong>{esc(item["source_scope"])}</strong></div>'
            '<div><small>Resolution</small><strong>Unknown</strong></div>'
            f'<div><small>Guidance</small><strong>{_guidance_html(item.get("guidance"), item["task_id"])}</strong></div>'
            "</div></article>"
            for item in monitor.protection_events
        )
    else:
        protections = '<div class="empty">No protection event is visible in this observation scope.</div>'
    benefit = monitor.benefit
    benefit_cards = "".join(
        '<article class="benefit-card">'
        '<div class="benefit-head">'
        f'<span>{esc(item["claim_class"])}</span>'
        f'<b class="benefit-status {esc(item["status"])}">{esc(item["status"])}</b>'
        "</div>"
        f'<h3>{esc(item["title"])}</h3>'
        f'<p>{esc(item["summary"])}</p>'
        '<p class="benefit-meta"><small>Semantics</small>'
        f'<strong>{esc(item["semantics"])}</strong></p>'
        '<p class="benefit-meta"><small>Recorded counts</small>'
        f'<strong>{esc(", ".join(f"{key}={value}" for key, value in item["metrics"].items()) or "none recorded")}</strong></p>'
        '<p class="benefit-reasons"><small>Evidence reasons</small> '
        f'{esc(", ".join(item["reason_codes"]))}</p>'
        "</article>"
        for item in benefit["cards"]
    )
    benefit_window = benefit["observation_window"]
    learning = monitor.learning
    learning_cards = "".join(
        '<article class="benefit-card">'
        '<div class="benefit-head">'
        f'<span>{esc(item["learning_class"])}</span>'
        f'<b class="benefit-status {esc(item["status"])}">{esc(item["status"])}</b>'
        "</div>"
        f'<h3>{esc(item["title"])}</h3>'
        f'<p>{esc(item["summary"])}</p>'
        '<p class="benefit-meta"><small>Semantics</small>'
        f'<strong>{esc(item["semantics"])}</strong></p>'
        '<p class="benefit-meta"><small>Recorded counts</small>'
        f'<strong>{esc(", ".join(f"{key}={value}" for key, value in item["metrics"].items()) or "none recorded")}</strong></p>'
        '<p class="benefit-meta"><small>Repeated candidates</small>'
        f'<strong>{esc("; ".join("{}: occurrences={}, distinct tasks={}, cross task={}".format(candidate["signal_id"], candidate["occurrences"], candidate["distinct_tasks"], str(candidate["cross_task"]).lower()) for candidate in item["candidates"]) or "none observed")}</strong></p>'
        '<p class="benefit-meta"><small>Attributed judgments</small>'
        f'<strong>{esc("; ".join("{}: disposition={}, actor role={}, resolution={}".format(judgment["signal_id"], judgment["disposition"], judgment["actor_role"], judgment["resolution"]) for judgment in item["judgments"]) or "none recorded")}</strong></p>'
        '<p class="benefit-meta"><small>Bounded topics</small>'
        f'<strong>{esc(", ".join(item["topics"]) or "none")}</strong></p>'
        '<p class="benefit-reasons"><small>Evidence reasons</small> '
        f'{esc(", ".join(item["reason_codes"]))}</p>'
        "</article>"
        for item in learning["cards"]
    )
    learning_window = learning["observation_window"]
    learning_rule = learning["recurrence_rule"]
    learning_review_source = learning["human_review_source"]
    machine = html.escape(render_development_monitor_json(monitor), quote=False)
    return f'''<!doctype html>
<!-- {MONITOR_CONTRACT} -->
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; img-src data:">
<title>AgentGov Development Monitor</title><style>
:root{{--ink:#12222b;--muted:#617078;--paper:#fffdf7;--wash:#f1eee4;--line:#ddd8ca;--teal:#0d6f69;--amber:#a85e12;--red:#a33d3d;--blue:#315c8a}}*{{box-sizing:border-box}}body{{margin:0;background:var(--wash);color:var(--ink);font:15px/1.55 ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif}}.shell{{width:min(1120px,calc(100% - 32px));margin:auto}}header{{background:var(--ink);color:white;padding:18px 0}}header .shell{{display:flex;justify-content:space-between;align-items:center;gap:18px}}.brand{{font-weight:850;letter-spacing:.02em}}.scope{{border:1px solid #ffffff55;border-radius:999px;padding:6px 11px;font-size:12px}}main{{padding:42px 0 56px}}.hero{{display:grid;grid-template-columns:1.45fr .75fr;gap:24px;align-items:end;margin-bottom:30px}}.eyebrow{{color:var(--teal);font-size:12px;font-weight:850;letter-spacing:.14em;text-transform:uppercase}}h1{{font-size:clamp(38px,6vw,68px);line-height:.98;letter-spacing:-.045em;margin:10px 0 16px;max-width:780px}}h2{{font-size:27px;letter-spacing:-.02em;margin:0 0 6px}}h3{{margin:0}}a.resolution-link{{color:var(--teal);text-decoration-thickness:2px;text-underline-offset:3px}}a.resolution-link:focus-visible{{outline:3px solid var(--amber);outline-offset:3px}}.lede,.sub,.event p,.task-note{{color:var(--muted)}}.boundary{{background:#e5f3ed;border-left:4px solid var(--teal);padding:18px;border-radius:12px}}.boundary strong{{display:block;font-size:21px}}.metrics{{display:grid;grid-template-columns:repeat(6,1fr);gap:10px;margin:26px 0}}.metric,.panel,.claim,.task{{background:var(--paper);border:1px solid var(--line);border-radius:16px}}.metric{{padding:17px}}.metric span{{display:block;color:var(--muted);font-size:11px;text-transform:uppercase;letter-spacing:.07em}}.metric strong{{display:block;font-size:28px;margin-top:8px}}.panel{{padding:25px;margin-top:18px}}.limits{{display:grid;grid-template-columns:.8fr 1.2fr;gap:22px}}.missing{{background:#fff3dd;border-radius:12px;padding:16px}}.missing h3{{color:var(--amber)}}.claims{{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-top:16px}}.claim{{padding:18px}}.claim h3{{text-transform:uppercase;font-size:12px;letter-spacing:.1em}}.claim.observed h3{{color:var(--teal)}}.claim.inferred h3{{color:var(--blue)}}.claim.unknown h3{{color:var(--amber)}}.claim ul,.missing ul{{padding-left:20px;margin-bottom:0}}.timeline{{list-style:none;margin:24px 0 0;padding:0}}.event{{display:grid;grid-template-columns:190px 1fr;gap:24px;padding:0 0 25px 24px;border-left:2px solid var(--line);position:relative}}.event:before{{content:"";position:absolute;width:12px;height:12px;border-radius:50%;background:var(--teal);left:-7px;top:5px}}time{{color:var(--muted);font-size:12px}}.event-head{{display:flex;gap:8px;align-items:center;margin-bottom:6px}}.kind,.outcome{{font-size:11px;font-weight:800;padding:4px 8px;border-radius:999px;background:#e8ecea}}.outcome.verified,.outcome.passed{{background:#dcefe6;color:var(--teal)}}.outcome.failed,.outcome.stale,.outcome.needs_evidence{{background:#f8dfd8;color:var(--red)}}.event p{{margin:4px 0}}.task{{margin-top:11px;overflow:hidden}}summary{{cursor:pointer;display:flex;justify-content:space-between;padding:17px 19px;font-weight:800}}summary b{{color:var(--teal)}}.task-grid{{border-top:1px solid var(--line);display:grid;grid-template-columns:repeat(4,1fr);gap:12px;padding:18px}}.task-grid small{{display:block;color:var(--muted)}}.task-grid strong{{font-size:13px}}.task-note{{padding:0 18px 18px;margin:0}}.empty{{color:var(--muted);padding:20px;border:1px dashed var(--line);border-radius:12px}}details.machine{{margin-top:18px}}pre{{white-space:pre-wrap;word-break:break-word;background:#17272f;color:#e8f3f0;padding:18px;border-radius:12px;font-size:12px}}footer{{padding:25px 0;color:var(--muted)}}@media(max-width:880px){{.metrics{{grid-template-columns:repeat(3,1fr)}}.hero,.limits{{grid-template-columns:1fr}}.claims{{grid-template-columns:1fr}}.task-grid{{grid-template-columns:1fr 1fr}}}}@media(max-width:560px){{header .shell{{align-items:flex-start;flex-direction:column}}.metrics{{grid-template-columns:1fr 1fr}}.event{{grid-template-columns:1fr;gap:5px}}.task-grid{{grid-template-columns:1fr}}}}
.task[id]{{scroll-margin-top:24px}}.task-attention{{border:2px solid #d18a36;box-shadow:0 0 0 4px #fff3dd}}.task-attention>summary{{background:#fff3dd}}.attention-context{{margin:0 18px 18px;padding:18px;border:1px solid #e8c994;border-radius:12px;background:#fffaf0}}.attention-heading{{display:flex;justify-content:space-between;gap:12px;margin-bottom:14px}}.attention-heading span{{color:var(--amber);font-size:12px;font-weight:850;letter-spacing:.1em;text-transform:uppercase}}.attention-heading strong{{color:var(--red)}}.attention-grid{{display:grid;grid-template-columns:repeat(2,1fr);gap:14px}}.attention-grid small,.next-action span{{display:block;color:var(--muted);font-size:11px;text-transform:uppercase;letter-spacing:.06em}}.attention-grid strong{{display:block;font-size:13px}}.next-action{{margin:18px 0 10px;padding:14px;border-left:4px solid var(--teal);background:#e5f3ed}}.next-action strong{{display:block;margin-top:4px}}.benefit-grid{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px;margin-top:18px}}.benefit-card{{padding:18px;border:1px solid var(--line);border-radius:14px;background:#fff}}.benefit-card:last-child{{grid-column:1/-1}}.benefit-head{{display:flex;justify-content:space-between;gap:12px;margin-bottom:10px}}.benefit-head span,.benefit-meta small,.benefit-reasons small{{color:var(--muted);font-size:11px;text-transform:uppercase;letter-spacing:.06em}}.benefit-status{{padding:3px 8px;border-radius:999px;background:#e8ecea;font-size:11px}}.benefit-status.observed,.benefit-status.supported{{background:#dcefe6;color:var(--teal)}}.benefit-status.unavailable,.benefit-status.unknown{{background:#fff3dd;color:var(--amber)}}.benefit-card h3{{margin-bottom:8px}}.benefit-card p{{margin:8px 0;color:var(--muted)}}.benefit-meta strong{{display:block;color:var(--ink);font-size:13px}}.benefit-limit{{margin-top:16px;padding:14px;border-left:4px solid var(--amber);background:#fff3dd}}.active-heading{{display:flex;justify-content:space-between;gap:18px;align-items:flex-start;margin:22px 0 14px}}.active-heading h3{{font-size:25px;margin-top:5px}}.state-pill{{padding:7px 11px;border-radius:999px;background:#e8ecea;font-size:12px}}.state-pill.scope_blocked,.state-pill.invalid,.state-pill.needs_evidence{{background:#f8dfd8;color:var(--red)}}.state-pill.review_ready,.state-pill.scope_passed,.state-pill.handed_off{{background:#dcefe6;color:var(--teal)}}.active-requirement{{font-size:18px;max-width:850px}}.active-grid{{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin:18px 0}}.active-grid>section,.active-evidence,.authority-panel,.active-unavailable{{border:1px solid var(--line);border-radius:14px;padding:18px;background:#fff}}.scope-columns{{display:grid;grid-template-columns:1fr 1fr;gap:12px}}.scope-columns small{{color:var(--muted);text-transform:uppercase;font-size:11px}}.scope-columns ul{{padding-left:18px}}.state-card{{border-left:4px solid var(--teal)!important}}.state-card dl{{display:grid;grid-template-columns:max-content 1fr;gap:5px 12px}}.state-card dt{{color:var(--muted)}}.state-card dd{{margin:0}}.scope-table-wrap{{overflow-x:auto}}.scope-table{{width:100%;border-collapse:collapse;margin-top:12px}}.scope-table th,.scope-table td{{text-align:left;border-bottom:1px solid var(--line);padding:10px;vertical-align:top}}.path-status{{font-size:11px}}.path-status.pass{{color:var(--teal)}}.path-status.fail{{color:var(--red)}}.evidence-ref{{color:var(--muted);font-size:12px}}.boundary-card{{background:#e5f3ed!important;border-left:4px solid var(--teal)!important}}.active-activity{{padding-left:20px}}.active-activity li{{margin-bottom:12px}}.active-activity p{{margin:3px 0}}.authority-panel{{margin-top:18px;background:#17272f;color:white}}.authority-panel h3{{margin-bottom:10px}}.authority-row{{display:flex;justify-content:space-between;gap:12px;padding:8px 0;border-top:1px solid #ffffff22}}.authority-row strong{{color:#ffd59b;font-size:12px}}.active-limits{{margin-top:12px;border:1px solid var(--line);border-radius:12px}}.active-limits>summary{{justify-content:flex-start}}.active-limits ul{{padding:0 38px 18px}}details.machine{{margin-top:28px;border-top:1px solid var(--line);color:var(--muted)}}details.machine>summary{{justify-content:flex-start;padding:16px 0;font-size:13px;font-weight:700}}.machine-note{{margin:0;padding:0 0 14px}}@media(max-width:560px){{.attention-grid,.benefit-grid,.active-grid,.scope-columns{{grid-template-columns:1fr}}.active-heading{{display:block}}.state-pill{{display:inline-block}}.benefit-card:last-child{{grid-column:auto}}}}
.review-guide{{display:grid;grid-template-columns:.8fr 1.2fr;gap:22px;padding:24px;margin:0 0 18px;border:1px solid #b8d8ce;border-left:5px solid var(--teal);border-radius:16px;background:#e5f3ed}}.review-guide h2{{margin-top:5px}}.review-guide p{{margin-bottom:0}}.review-steps{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px;margin:0;padding:0;list-style:none;counter-reset:review-step}}.review-steps li{{counter-increment:review-step;padding:12px;border:1px solid #c8ddd6;border-radius:12px;background:#fff}}.review-steps li:before{{content:counter(review-step);display:inline-grid;place-items:center;width:24px;height:24px;margin-right:8px;border-radius:50%;background:var(--teal);color:white;font-weight:850;font-size:12px}}.review-steps strong{{display:inline}}.review-steps span{{display:block;margin:5px 0 0 32px;color:var(--muted);font-size:13px}}.review-note{{grid-column:1/-1;padding-top:12px;border-top:1px solid #b8d8ce;color:var(--muted);font-size:13px}}.monitor-history{{margin-top:24px;border:1px solid var(--line);border-radius:16px;background:var(--paper);overflow:hidden}}.monitor-history>summary{{align-items:center;padding:20px 24px;font-size:18px}}.monitor-history>summary span{{display:block}}.monitor-history>summary small{{display:block;color:var(--muted);font-weight:500;font-size:12px}}.history-content{{padding:0 24px 24px;border-top:1px solid var(--line)}}@media(max-width:880px){{.review-guide{{grid-template-columns:1fr}}}}@media(max-width:560px){{.review-steps{{grid-template-columns:1fr}}.history-content{{padding:0 14px 14px}}}}
</style></head><body><header><div class="shell"><div class="brand">AGENTGOV · DEVELOPMENT MONITOR</div><div class="scope">Observation scope · {esc(observation['scope'])}</div></div></header><main class="shell">
<section class="hero"><div><div class="eyebrow">Govern → Observe → Monitor</div><h1>See governance while development is happening.</h1><p class="lede">A local, static view of when AgentGov ran, why it ran, who invoked it, and what its event records observed—without turning evidence into approval.</p></div><aside class="boundary"><span>History completeness</span><strong>{esc(observation['history_completeness'])}</strong><small>{observation['event_count']} validated events · {observation['duplicates_removed']} duplicate records removed</small></aside></section>
<section class="review-guide" id="review-guide" aria-labelledby="review-guide-title"><div><span class="eyebrow">Guided review</span><h2 id="review-guide-title">Review one task, not the whole history.</h2><p>Start with Active Task below. Use it to answer six questions before opening the full Monitor history.</p></div><ol class="review-steps"><li><strong>Requirement</strong><span>What exact work was admitted?</span></li><li><strong>Path boundary</strong><span>What may change, and what is excluded?</span></li><li><strong>Direct evidence</strong><span>What did AgentGov actually observe?</span></li><li><strong>Current state</strong><span>What does the canonical governance state mean?</span></li><li><strong>Human boundary</strong><span>What decision or action belongs to a person next?</span></li><li><strong>Authority</strong><span>What downstream authority is still not granted?</span></li></ol><p class="review-note">This page provides guidance. Any comprehension observation made from it is guided or assisted, not uncoached.</p></section>
{active_task_html}
<details class="monitor-history"><summary><span>Full Monitor history<small>Open aggregate counts, protection events, timelines, task detail, Benefit, Learning, and technical audit data.</small></span><b>Optional detail</b></summary><div class="history-content">
<section aria-labelledby="overview"><h2 id="overview">Overview</h2><p class="sub">Observed counts within this dashboard's declared scope. They are not a governance score.</p><div class="metrics">{cards}</div></section>
<section class="panel"><h2>Drift Review Reminder</h2><p><b>{esc(drift_review['state'])}</b> · {esc(', '.join(drift_review['reason_codes']))}</p><p class="sub">Requirement, architecture, and functionality conclusions remain ADVISORY. This deterministic cadence reminder neither decides drift nor grants scope, Git, release, or deployment authority.</p></section>
<section class="panel limits"><div><h2>Observation boundary</h2><p><b>{esc(observation['scope'])}</b> from {esc(observation['started_at'])} to {esc(observation['ended_at'])}.</p><p class="sub">Source events: {esc(", ".join(f"{key}={value}" for key, value in observation['source_event_counts'].items()))}.</p><p class="sub">Cross-stage discovery comparison is unavailable because the event contract has no cross-stage finding identity or resolution link.</p></div><div class="missing"><h3>Missing sources</h3><ul>{missing}</ul></div></section>
<section class="panel"><h2>Claim layers</h2><p class="sub">Facts, cautious interpretation, and unknowns stay visibly separate.</p><div class="claims">{layers}</div></section>
<section class="panel"><h2>Live Sessions</h2><p class="sub">Current read-model state from each task's latest visible event.</p><div class="metrics">{live_sessions}</div></section>
<section class="panel"><h2>Protection Events</h2><p class="sub">Observed blocked, failed, stale, or incomplete outcomes. Guidance links are read-only navigation; resolution remains unknown without explicit resolution evidence.</p>{protections}</section>
<section class="panel" aria-labelledby="timeline"><h2 id="timeline">Activity Timeline</h2><p class="sub">When governance triggered, why it triggered, who used it, and what was recorded.</p><ol class="timeline">{timeline}</ol></section>
<section class="panel" aria-labelledby="tasks"><h2 id="tasks">Task Detail</h2><p class="sub">Latest recorded outcomes and visible task activity. Requirement and architecture correctness remain human judgments.</p>{task_cards}</section>
<section class="panel" aria-labelledby="benefit"><h2 id="benefit">Benefit</h2><p class="sub">Single-observation evidence cards, not a governance score or causal benefit claim.</p><p class="sub">Scope <b>{esc(benefit['scope'])}</b> · window {esc(benefit_window['started_at'])} to {esc(benefit_window['ended_at'])}</p><div class="benefit-grid">{benefit_cards}</div><p class="benefit-limit"><b>Claim limit:</b> {esc(benefit['claim_limit'])}</p></section>
<section class="panel" aria-labelledby="learning"><h2 id="learning">Learning</h2><p class="sub">Current-observation review candidates and exact candidate-bound human judgments, not confirmed root causes, trends, resolution, or general improvements.</p><p class="sub">Scope <b>{esc(learning['scope'])}</b> &middot; window {esc(learning_window['started_at'])} to {esc(learning_window['ended_at'])}</p><p class="sub">Rule: {esc(learning_rule['signal_source'])} appears at least <b>{learning_rule['minimum_occurrences']}</b> times; distinct tasks required <b>{esc(str(learning_rule['requires_distinct_tasks']).lower())}</b>; generalization allowed <b>{esc(str(learning_rule['generalization_allowed']).lower())}</b>.</p><p class="sub">Human review source <b>{esc(learning_review_source['availability'])}</b> &middot; records read {learning_review_source['records_read']} &middot; matched {learning_review_source['matched_records']} &middot; stale {learning_review_source['stale_records']}.</p><div class="benefit-grid">{learning_cards}</div><p class="benefit-limit"><b>Claim limit:</b> {esc(learning['claim_limit'])}</p></section>
<details class="machine"><summary>Technical audit data (optional)</summary><p class="sub machine-note">Machine-readable JSON for tools and debugging. Ordinary task review does not require this section.</p><pre>{machine}</pre></details>
</div></details>
</main><footer class="shell">Generated locally · No external requests · No approval, mutation, merge, or deployment authority</footer></body></html>'''


def write_development_monitor(
    repository: Path,
    *,
    monitor: DevelopmentMonitor,
    output: Path,
    output_format: str,
) -> Path:
    """Atomically refresh only an AgentGov-owned generated Monitor file."""

    root = _safe_root(repository)
    target = output if output.is_absolute() else root / output
    target = target.resolve()
    try:
        relative = target.relative_to(root)
    except ValueError as exc:
        raise MonitorPolicyError("Monitor output must remain inside the repository") from exc
    parent = root
    for part in relative.parts[:-1]:
        parent = parent / part
        if parent.is_symlink():
            raise MonitorPolicyError("Monitor output path must not cross a symbolic link")
    if target.is_symlink():
        raise MonitorPolicyError("Monitor output must not be a symbolic link")
    tracked = subprocess.run(
        ("git", "-C", str(root), "ls-files", "--error-unmatch", "--", relative.as_posix()),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
        timeout=30,
    )
    if tracked.returncode == 0:
        raise MonitorPolicyError("refusing to overwrite a tracked Monitor output")
    if tracked.returncode != 1:
        raise MonitorPolicyError("could not verify that Monitor output is untracked")
    renderers = {
        "html": render_development_monitor_html,
        "json": render_development_monitor_json,
        "markdown": render_development_monitor_markdown,
    }
    if output_format not in renderers:
        raise MonitorPolicyError("unsupported Monitor output format")
    content = renderers[output_format](monitor)
    marker = {
        "html": f"<!-- {MONITOR_CONTRACT} -->",
        "json": f'"contract": "{MONITOR_CONTRACT}"',
        "markdown": "# AgentGov development Monitor",
    }[output_format]
    if target.exists():
        try:
            existing = target.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            raise MonitorPolicyError(f"cannot inspect existing Monitor output: {exc}") from exc
        if marker not in existing[:2048]:
            raise MonitorPolicyError("refusing to replace a file not owned by the AgentGov Monitor")
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.parent / f".{target.name}.tmp-{uuid.uuid4().hex}"
    try:
        with temporary.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)
    return target
