"""Host-side natural-language Adapter for strict task-proposal preparation.

The semantic materializer belongs to the Coding Agent host. This module gives
it one narrow output type, adds Adapter-owned identity and policy boundaries,
and then hands only the normalized proposal to the existing read-only Core
admission planner. Raw request text is never stored on the Adapter or result.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from agentgov.reference_adapter import REFERENCE_ADAPTER_ID
from agentgov.task_proposal import (
    TaskAdmissionPlan,
    TaskProposalPolicyError,
    build_task_admission_plan,
)


MAX_NATURAL_LANGUAGE_REQUEST_CHARACTERS = 20_000


@dataclass(frozen=True)
class TaskProposalDraft:
    """Normalized proposal meaning returned by a host-owned materializer."""

    task_id: str
    title: str
    requirement_summary: str
    include_paths: tuple[str, ...]
    exclude_paths: tuple[str, ...]
    acceptance_signals: tuple[str, ...]
    validation_commands: tuple[str, ...]
    owner: str
    risk_items: tuple[str, ...] = ()
    assumptions: tuple[str, ...] = ()
    unknowns: tuple[str, ...] = ()


class HostTaskProposalMaterializer(Protocol):
    """Replaceable host capability; AgentGov Core does not infer semantics."""

    def materialize_task_proposal(self, request_text: str) -> TaskProposalDraft:
        """Return normalized low-risk task meaning without raw conversation."""


@dataclass(frozen=True)
class TaskProposalPreparation:
    """Privacy-safe evidence plus the existing human-review admission plan."""

    plan: TaskAdmissionPlan
    materializer_invocations: int
    agentgov_model_calls: int = 0
    agentgov_network_calls: int = 0
    result_contains_raw_request: bool = False
    core_received_raw_request: bool = False
    repository_modified: bool = False
    task_admitted: bool = False
    session_started: bool = False
    authorizes_code_change: bool = False
    authorizes_scope_expansion: bool = False
    authorizes_exception: bool = False
    authorizes_git_operations: bool = False
    authorizes_deployment: bool = False
    authorizes_release: bool = False


class ReferenceTaskProposalAdapterError(ValueError):
    """The host request or its normalized draft is invalid or unsafe."""


def _require_request(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ReferenceTaskProposalAdapterError(
            "request_text must be non-empty natural language"
        )
    if len(value) > MAX_NATURAL_LANGUAGE_REQUEST_CHARACTERS:
        raise ReferenceTaskProposalAdapterError(
            "request_text exceeds the host Adapter input limit"
        )
    return value


class ReferenceTaskProposalAdapter:
    """Prepare one strict proposal from ordinary host conversation.

    A real host supplies semantic inference through ``materializer``. AgentGov
    creates the proposal identity and all privacy/authority declarations, then
    reuses the established read-only admission planner. The returned plan still
    requires the separate exact human ``ADMIT`` flow before any file is created.
    """

    def __init__(
        self,
        materializer: HostTaskProposalMaterializer,
        *,
        adapter_id: str = REFERENCE_ADAPTER_ID,
    ) -> None:
        self._materializer = materializer
        self._adapter_id = adapter_id

    def prepare(
        self,
        repository: Path,
        request_text: str,
    ) -> TaskProposalPreparation:
        """Materialize once and return a non-authoritative admission preview."""

        request_text = _require_request(request_text)
        try:
            draft = self._materializer.materialize_task_proposal(request_text)
        except Exception:
            raise ReferenceTaskProposalAdapterError(
                "host task-proposal materializer could not normalize the request"
            ) from None
        if type(draft) is not TaskProposalDraft:
            raise ReferenceTaskProposalAdapterError(
                "host task-proposal materializer must return TaskProposalDraft"
            )
        return self._prepare_from_draft(
            repository,
            draft,
            materializer_invocations=1,
        )

    def prepare_from_draft(
        self,
        repository: Path,
        draft: TaskProposalDraft,
    ) -> TaskProposalPreparation:
        """Bind one normalized host draft to the existing Core preview path."""

        return self._prepare_from_draft(
            repository,
            draft,
            materializer_invocations=0,
        )

    def _prepare_from_draft(
        self,
        repository: Path,
        draft: TaskProposalDraft,
        *,
        materializer_invocations: int,
    ) -> TaskProposalPreparation:
        if type(draft) is not TaskProposalDraft:
            raise ReferenceTaskProposalAdapterError(
                "host Adapter must supply TaskProposalDraft"
            )
        proposal = {
            "contract": "agentgov.task-proposal",
            "schema_version": "1.0",
            "proposal_id": f"prp-{uuid.uuid4().hex}",
            "source": {
                "adapter_id": self._adapter_id,
                "actor_class": "coding_agent",
            },
            "task": {
                "task_id": draft.task_id,
                "title": draft.title,
                "requirement_summary": draft.requirement_summary,
                "scope": {
                    "include_paths": list(draft.include_paths),
                    "exclude_paths": list(draft.exclude_paths),
                },
                "acceptance_signals": list(draft.acceptance_signals),
                "validation_commands": list(draft.validation_commands),
                "owner": draft.owner,
                "risk": {"level": "low", "items": list(draft.risk_items)},
                "assumptions": list(draft.assumptions),
                "unknowns": list(draft.unknowns),
            },
            "content_boundary": {
                "contains_raw_prompt": False,
                "contains_transcript": False,
                "contains_source_content": False,
                "contains_credentials": False,
                "contains_absolute_paths": False,
            },
            "authority_boundary": {
                "admits_task": False,
                "starts_session": False,
                "authorizes_code_change": False,
                "authorizes_scope_expansion": False,
                "authorizes_exception": False,
                "authorizes_git_operations": False,
                "authorizes_deployment": False,
                "authorizes_release": False,
            },
        }
        try:
            plan = build_task_admission_plan(repository, proposal)
        except FileNotFoundError:
            raise ReferenceTaskProposalAdapterError(
                "repository is unavailable for task-proposal preparation"
            ) from None
        except TaskProposalPolicyError as exc:
            raise ReferenceTaskProposalAdapterError(
                f"normalized task-proposal draft was rejected: {exc}"
            ) from exc
        return TaskProposalPreparation(
            plan=plan,
            materializer_invocations=materializer_invocations,
        )
