"""Minimal vendor-neutral reference adapter for one foreground cycle."""

from __future__ import annotations

import uuid
from dataclasses import asdict
from pathlib import Path
from typing import Any, Mapping

from agentgov.change_scope import check_development_scope
from agentgov.development_session import load_active_session, resolve_active_task
from agentgov.development_trigger import (
    TRIGGER_CONTRACT,
    TRIGGER_SCHEMA_VERSION,
    DevelopmentTrigger,
    development_trigger_from_payload,
    working_copy_digest,
)
from agentgov.event_store import utc_now


REFERENCE_ADAPTER_ID = "agentgov.reference-adapter"


def build_reference_trigger(
    repository: Path,
    *,
    trigger_type: str,
    actor_class: str = "coding_agent",
    correlation_id: str | None = None,
    validation_outcome: str | None = None,
    evidence_ref: str | None = None,
    scope_decision: str | None = None,
    review_outcome: str | None = None,
) -> DevelopmentTrigger:
    """Observe bounded repository facts and build one strict adapter trigger."""

    root = repository.resolve(strict=True)
    session = load_active_session(root)
    changed_paths: list[str] = []
    if trigger_type == "implementation.changed":
        task_path, session = resolve_active_task(root)
        report = check_development_scope(task_path, repository=root)
        changed_paths = sorted(
            {
                path
                for change in report.changes
                for path in (change.old_path, change.path)
                if path is not None
            }
        )
    task_ref: Mapping[str, str] | None = None
    if session is not None:
        task_ref = {
            "task_id": session.task_id,
            "task_digest": session.task_digest,
        }
    payload: Mapping[str, Any] = {
        "contract": TRIGGER_CONTRACT,
        "schema_version": TRIGGER_SCHEMA_VERSION,
        "trigger_id": f"trg-{uuid.uuid4().hex}",
        "occurred_at": utc_now(),
        "trigger_type": trigger_type,
        "source": {
            "adapter_id": REFERENCE_ADAPTER_ID,
            "actor_class": actor_class,
        },
        "working_copy_digest": working_copy_digest(root),
        "correlation_id": correlation_id or f"cycle-{uuid.uuid4().hex}",
        "task_ref": task_ref,
        "facts": {
            "changed_paths": changed_paths,
            "validation_outcome": validation_outcome,
            "evidence_ref": evidence_ref,
            "scope_decision": scope_decision,
            "review_outcome": review_outcome,
        },
        "authority_boundary": {
            "authorizes_scope_expansion": False,
            "authorizes_exception": False,
            "authorizes_commit": False,
            "authorizes_merge": False,
            "authorizes_deployment": False,
        },
    }
    return development_trigger_from_payload(payload)


def reference_trigger_payload(trigger: DevelopmentTrigger) -> Mapping[str, Any]:
    return asdict(trigger)
