"""Versioned, vendor-neutral foreground adapter trigger contract."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any, Mapping


TRIGGER_CONTRACT = "agentgov.development-trigger"
TRIGGER_SCHEMA_VERSION = "1.0"
TRIGGER_TYPES = {
    "task.requested",
    "repository.activated",
    "implementation.changed",
    "scope.decision_requested",
    "scope.decision_recorded",
    "completion.requested",
    "validation.completed",
    "session.reviewed",
}
TRIGGER_ACTORS = {"human", "coding_agent", "ci"}

_ID_RE = re.compile(r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$")
_TRIGGER_ID_RE = re.compile(r"^trg-[0-9a-f]{32}$")
_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_TASK_ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class TriggerContractError(ValueError):
    """An adapter trigger is ambiguous, unsafe, or outside the contract."""


@dataclass(frozen=True)
class DevelopmentTrigger:
    contract: str
    schema_version: str
    trigger_id: str
    occurred_at: str
    trigger_type: str
    source: Mapping[str, str]
    working_copy_digest: str
    correlation_id: str
    task_ref: Mapping[str, str] | None
    facts: Mapping[str, Any]
    authority_boundary: Mapping[str, bool]


def working_copy_digest(repository: Path) -> str:
    """Create a local correlation value without exposing the absolute path."""

    resolved = repository.resolve(strict=True)
    if not resolved.is_dir():
        raise TriggerContractError("repository must be a directory")
    return "sha256:" + hashlib.sha256(str(resolved).encode("utf-8")).hexdigest()


def _safe_relative_path(value: Any, *, label: str) -> str:
    if not isinstance(value, str) or not value or "\\" in value:
        raise TriggerContractError(f"{label} must be a repository-relative POSIX path")
    pure = PurePosixPath(value)
    if pure.is_absolute() or value == "." or ".." in pure.parts:
        raise TriggerContractError(f"{label} must be a repository-relative POSIX path")
    return value


def _parse_timestamp(value: Any) -> str:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise TriggerContractError("occurred_at must be a UTC Z timestamp")
    try:
        datetime.fromisoformat(value.removesuffix("Z") + "+00:00")
    except ValueError as exc:
        raise TriggerContractError("occurred_at must be a UTC Z timestamp") from exc
    return value


def development_trigger_from_payload(payload: Any) -> DevelopmentTrigger:
    """Validate one adapter trigger and fail closed on unknown fields."""

    fields = {
        "contract",
        "schema_version",
        "trigger_id",
        "occurred_at",
        "trigger_type",
        "source",
        "working_copy_digest",
        "correlation_id",
        "task_ref",
        "facts",
        "authority_boundary",
    }
    if not isinstance(payload, Mapping) or set(payload) != fields:
        raise TriggerContractError("trigger has unexpected fields")
    if payload.get("contract") != TRIGGER_CONTRACT or payload.get("schema_version") != TRIGGER_SCHEMA_VERSION:
        raise TriggerContractError("trigger uses an unsupported contract")
    trigger_id = payload.get("trigger_id")
    if not isinstance(trigger_id, str) or not _TRIGGER_ID_RE.fullmatch(trigger_id):
        raise TriggerContractError("trigger_id is invalid")
    occurred_at = _parse_timestamp(payload.get("occurred_at"))
    trigger_type = payload.get("trigger_type")
    if trigger_type not in TRIGGER_TYPES:
        raise TriggerContractError("trigger_type is unsupported")

    source = payload.get("source")
    if not isinstance(source, Mapping) or set(source) != {"adapter_id", "actor_class"}:
        raise TriggerContractError("source has unexpected fields")
    adapter_id = source.get("adapter_id")
    actor_class = source.get("actor_class")
    if not isinstance(adapter_id, str) or not _ID_RE.fullmatch(adapter_id) or len(adapter_id) > 80:
        raise TriggerContractError("source adapter_id is invalid")
    if actor_class not in TRIGGER_ACTORS:
        raise TriggerContractError("source actor_class is unsupported")

    copy_digest = payload.get("working_copy_digest")
    if not isinstance(copy_digest, str) or not _DIGEST_RE.fullmatch(copy_digest):
        raise TriggerContractError("working_copy_digest is invalid")
    correlation_id = payload.get("correlation_id")
    if not isinstance(correlation_id, str) or not _ID_RE.fullmatch(correlation_id) or len(correlation_id) > 120:
        raise TriggerContractError("correlation_id is invalid")

    task_ref = payload.get("task_ref")
    if task_ref is not None:
        if not isinstance(task_ref, Mapping) or set(task_ref) != {"task_id", "task_digest"}:
            raise TriggerContractError("task_ref has unexpected fields")
        task_id = task_ref.get("task_id")
        task_digest = task_ref.get("task_digest")
        if not isinstance(task_id, str) or not _TASK_ID_RE.fullmatch(task_id):
            raise TriggerContractError("task_ref task_id is invalid")
        if not isinstance(task_digest, str) or not _DIGEST_RE.fullmatch(task_digest):
            raise TriggerContractError("task_ref task_digest is invalid")

    facts = payload.get("facts")
    fact_fields = {
        "changed_paths",
        "validation_outcome",
        "evidence_ref",
        "scope_decision",
        "review_outcome",
    }
    if not isinstance(facts, Mapping) or set(facts) != fact_fields:
        raise TriggerContractError("facts has unexpected fields")
    changed_paths = facts.get("changed_paths")
    if not isinstance(changed_paths, list) or len(changed_paths) != len(set(changed_paths)):
        raise TriggerContractError("changed_paths must be a unique array")
    normalized_paths = tuple(
        _safe_relative_path(value, label="changed path") for value in changed_paths
    )
    validation_outcome = facts.get("validation_outcome")
    if validation_outcome not in {None, "passed", "failed"}:
        raise TriggerContractError("validation_outcome is invalid")
    evidence_ref = facts.get("evidence_ref")
    if evidence_ref is not None:
        evidence_ref = _safe_relative_path(evidence_ref, label="evidence_ref")
    scope_decision = facts.get("scope_decision")
    if scope_decision not in {None, "approved", "declined", "needs_human"}:
        raise TriggerContractError("scope_decision is invalid")
    review_outcome = facts.get("review_outcome")
    if review_outcome not in {None, "accepted", "changes_requested"}:
        raise TriggerContractError("review_outcome is invalid")

    if trigger_type == "implementation.changed" and not normalized_paths:
        raise TriggerContractError("implementation.changed requires changed_paths")
    if trigger_type != "implementation.changed" and normalized_paths:
        raise TriggerContractError("changed_paths are only valid for implementation.changed")
    if trigger_type == "validation.completed" and validation_outcome is None:
        raise TriggerContractError("validation.completed requires validation_outcome")
    if trigger_type != "validation.completed" and validation_outcome is not None:
        raise TriggerContractError("validation_outcome is only valid for validation.completed")
    if trigger_type != "validation.completed" and evidence_ref is not None:
        raise TriggerContractError("evidence_ref is only valid for validation.completed")
    if trigger_type == "scope.decision_requested" and scope_decision is not None:
        raise TriggerContractError("scope.decision_requested cannot contain a decision")
    if trigger_type == "scope.decision_recorded":
        if scope_decision is None or actor_class != "human":
            raise TriggerContractError("scope.decision_recorded requires a human decision")
    elif scope_decision is not None:
        raise TriggerContractError("scope_decision is only valid for scope.decision_recorded")
    if trigger_type == "session.reviewed" and review_outcome is None:
        raise TriggerContractError("session.reviewed requires review_outcome")
    if trigger_type == "session.reviewed" and actor_class != "human":
        raise TriggerContractError("session.reviewed requires a human actor")
    if trigger_type != "session.reviewed" and review_outcome is not None:
        raise TriggerContractError("review_outcome is only valid for session.reviewed")

    authority = payload.get("authority_boundary")
    authority_fields = {
        "authorizes_scope_expansion",
        "authorizes_exception",
        "authorizes_commit",
        "authorizes_merge",
        "authorizes_deployment",
    }
    if (
        not isinstance(authority, Mapping)
        or set(authority) != authority_fields
        or any(value is not False for value in authority.values())
    ):
        raise TriggerContractError("trigger cannot grant consequential authority")

    return DevelopmentTrigger(
        contract=TRIGGER_CONTRACT,
        schema_version=TRIGGER_SCHEMA_VERSION,
        trigger_id=trigger_id,
        occurred_at=occurred_at,
        trigger_type=trigger_type,
        source={"adapter_id": adapter_id, "actor_class": actor_class},
        working_copy_digest=copy_digest,
        correlation_id=correlation_id,
        task_ref=dict(task_ref) if task_ref is not None else None,
        facts={
            "changed_paths": normalized_paths,
            "validation_outcome": validation_outcome,
            "evidence_ref": evidence_ref,
            "scope_decision": scope_decision,
            "review_outcome": review_outcome,
        },
        authority_boundary=dict(authority),
    )
