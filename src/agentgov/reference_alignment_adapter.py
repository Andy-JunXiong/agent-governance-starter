"""Host-side natural-language Adapter for the governed alignment flow.

The semantic materializer belongs to the Coding Agent host.  This module binds
its normalized drafts to strict Core contracts without retaining the raw user
request or answer.
"""

from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Protocol, Sequence

from agentgov.active_agent_self_review import (
    ActiveAgentSelfReviewError,
    ActiveAgentSelfReviewMaterializer,
    ActiveAgentSelfReviewRun,
    run_active_agent_self_review,
)
from agentgov.alignment_transport import AlignmentStreamResponse, AlignmentStreamSession
from agentgov.clarification_dialogue import (
    ALIGNMENT_CONTEXT_CONTRACT,
    CLARIFICATION_UPDATE_CONTRACT,
    ClarificationDialogue,
    ClarificationPrompt,
    denied_authority,
)
from agentgov.event_store import utc_now
from agentgov.human_decision import canonical_document_digest, record_human_decision
from agentgov.reference_adapter import REFERENCE_ADAPTER_ID
from agentgov.semantic_review import SemanticReviewProviderCapabilities


@dataclass(frozen=True)
class AlignmentContextDraft:
    """Semantic fields a host Coding Agent derives from the current conversation."""

    subject_type: str
    subject_id: str
    center: Mapping[str, Any]
    drift: Mapping[str, Any]
    assumptions: tuple[str, ...]
    unknowns: tuple[Mapping[str, Any], ...]
    candidate_resolutions: tuple[Mapping[str, Any], ...] = ()
    recommended_resolution_id: str | None = None


@dataclass(frozen=True)
class ClarificationUpdateDraft:
    """Normalized meaning a host derives from one natural-language answer."""

    answer_summary: str
    center_patch: Mapping[str, Any]
    new_questions: tuple[Mapping[str, Any], ...] = ()
    candidate_resolutions: tuple[Mapping[str, Any], ...] = ()
    recommended_resolution_id: str | None = None
    ready_requested: bool = False


class HostSemanticMaterializer(Protocol):
    """Replaceable host capability; AgentGov Core does not implement this step."""

    def materialize_request(self, request_text: str) -> AlignmentContextDraft:
        """Interpret one natural-language request without returning raw text."""

    def materialize_answer(
        self,
        answer_text: str,
        *,
        dialogue: ClarificationDialogue,
        prompt: ClarificationPrompt,
    ) -> ClarificationUpdateDraft:
        """Normalize one human answer against the exact active Core question."""


@dataclass(frozen=True)
class AlignmentJourney:
    """Privacy-safe observable state for one foreground Adapter journey."""

    status: str
    sequence: int
    responses: tuple[AlignmentStreamResponse, ...]
    interaction_burden: Mapping[str, int]
    privacy_boundary: Mapping[str, bool]


class ReferenceAlignmentAdapterError(ValueError):
    """The host-side journey was invoked out of order or materialization failed."""


def _require_natural_language(value: Any, *, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ReferenceAlignmentAdapterError(f"{label} must be non-empty natural language")
    return value


class ReferenceAlignmentAdapter:
    """Drive strict Core alignment using only natural-language host inputs.

    The Adapter never stores ``request_text`` or ``answer_text``.  A real host
    supplies a semantic materializer backed by its current Coding Agent context;
    tests and offline rehearsals may supply a deterministic fixture materializer.
    """

    def __init__(
        self,
        materializer: HostSemanticMaterializer,
        *,
        adapter_id: str = REFERENCE_ADAPTER_ID,
        session: AlignmentStreamSession | None = None,
    ) -> None:
        self._materializer = materializer
        self._adapter_id = adapter_id
        self._session = session or AlignmentStreamSession()
        self._responses: list[AlignmentStreamResponse] = []
        self._natural_language_requests = 0
        self._natural_language_answers = 0
        self._single_select_decisions = 0

    def start(self, request_text: str) -> AlignmentStreamResponse:
        """Start once from ordinary user language and return the first Core prompt."""

        request_text = _require_natural_language(request_text, label="request_text")
        if self._responses:
            raise ReferenceAlignmentAdapterError("alignment journey has already started")
        try:
            draft = self._materializer.materialize_request(request_text)
        except Exception as exc:
            raise ReferenceAlignmentAdapterError(
                "host semantic materializer could not normalize the request"
            ) from exc
        if not isinstance(draft, AlignmentContextDraft):
            raise ReferenceAlignmentAdapterError(
                "host semantic materializer must return AlignmentContextDraft"
            )
        response = self.start_from_draft(draft)
        self._natural_language_requests += 1
        return response

    def start_from_draft(
        self,
        draft: AlignmentContextDraft,
    ) -> AlignmentStreamResponse:
        """Start from a normalized host draft without treating it as user-authored JSON."""

        if self._responses:
            raise ReferenceAlignmentAdapterError("alignment journey has already started")
        if not isinstance(draft, AlignmentContextDraft):
            raise ReferenceAlignmentAdapterError(
                "host Adapter must supply AlignmentContextDraft"
            )
        payload = {
            "contract": ALIGNMENT_CONTEXT_CONTRACT,
            "schema_version": "1.0",
            "context_id": f"acx-{uuid.uuid4().hex}",
            "source": {
                "adapter_id": self._adapter_id,
                "actor_class": "coding_agent",
                "subject_type": draft.subject_type,
                "subject_id": draft.subject_id,
            },
            "center": dict(draft.center),
            "drift": dict(draft.drift),
            "assumptions": list(draft.assumptions),
            "unknowns": [dict(item) for item in draft.unknowns],
            "candidate_resolutions": [
                dict(item) for item in draft.candidate_resolutions
            ],
            "recommended_resolution_id": draft.recommended_resolution_id,
            "content_boundary": {
                "contains_raw_prompt": False,
                "contains_raw_answer": False,
                "contains_transcript": False,
                "contains_assistant_response": False,
                "contains_source_content": False,
                "contains_credentials": False,
                "contains_absolute_paths": False,
            },
            "authority_boundary": denied_authority(),
        }
        return self._process(payload)

    def answer(self, answer_text: str) -> AlignmentStreamResponse:
        """Normalize one natural answer and return the next exact Core prompt."""

        answer_text = _require_natural_language(answer_text, label="answer_text")
        active = self._active_response()
        prompt = active.clarification_prompt
        if prompt is None:
            raise ReferenceAlignmentAdapterError(
                "alignment journey is not waiting for a clarification answer"
            )
        try:
            draft = self._materializer.materialize_answer(
                answer_text,
                dialogue=active.dialogue,
                prompt=prompt,
            )
        except Exception as exc:
            raise ReferenceAlignmentAdapterError(
                "host semantic materializer could not normalize the answer"
            ) from exc
        if not isinstance(draft, ClarificationUpdateDraft):
            raise ReferenceAlignmentAdapterError(
                "host semantic materializer must return ClarificationUpdateDraft"
            )
        response = self.answer_from_draft(draft)
        self._natural_language_answers += 1
        return response

    def answer_from_draft(
        self,
        draft: ClarificationUpdateDraft,
    ) -> AlignmentStreamResponse:
        """Apply one normalized host answer draft to the exact pending question."""

        if not isinstance(draft, ClarificationUpdateDraft):
            raise ReferenceAlignmentAdapterError(
                "host Adapter must supply ClarificationUpdateDraft"
            )
        active = self._active_response()
        prompt = active.clarification_prompt
        if prompt is None:
            raise ReferenceAlignmentAdapterError(
                "alignment journey is not waiting for a clarification answer"
            )
        payload = {
            "contract": CLARIFICATION_UPDATE_CONTRACT,
            "schema_version": "1.0",
            "update_id": f"cup-{uuid.uuid4().hex}",
            "dialogue": {
                "dialogue_id": active.dialogue.dialogue_id,
                "revision": active.dialogue.revision,
                "digest": canonical_document_digest(asdict(active.dialogue)),
            },
            "prompt": {
                "prompt_id": prompt.prompt_id,
                "prompt_digest": canonical_document_digest(asdict(prompt)),
            },
            "question_id": prompt.question["question_id"],
            "actor": {
                "adapter_id": self._adapter_id,
                "actor_class": "human",
                "recording_method": "host_conversation",
            },
            "recorded_at": utc_now(),
            "answer_summary": draft.answer_summary,
            "center_patch": dict(draft.center_patch),
            "new_questions": [dict(item) for item in draft.new_questions],
            "candidate_resolutions": [
                dict(item) for item in draft.candidate_resolutions
            ],
            "recommended_resolution_id": draft.recommended_resolution_id,
            "ready_requested": draft.ready_requested,
            "content_boundary": {
                "contains_raw_prompt": False,
                "contains_raw_answer": False,
                "contains_transcript": False,
                "contains_assistant_response": False,
                "contains_source_content": False,
                "contains_credentials": False,
                "contains_absolute_paths": False,
            },
            "authority_boundary": denied_authority(),
        }
        return self._process(payload)

    def select(self, option_id: str) -> AlignmentStreamResponse:
        """Record one host UI selection; the human never constructs a result record."""

        active = self._active_response()
        prompt = active.decision_prompt
        if prompt is None:
            raise ReferenceAlignmentAdapterError(
                "alignment journey is not waiting for a final single-select decision"
            )
        offered = {item["id"] for item in prompt.options}
        if option_id not in offered:
            raise ReferenceAlignmentAdapterError("selected option was not offered")
        result = record_human_decision(
            prompt,
            selected_option_id=option_id,
            adapter_id=self._adapter_id,
            recording_method="host_single_select",
        )
        response = self._process(asdict(result))
        self._single_select_decisions += 1
        return response

    def self_review(
        self,
        materializer: ActiveAgentSelfReviewMaterializer,
        *,
        provider: SemanticReviewProviderCapabilities,
        reason_codes: Sequence[str],
        allowed_evidence_refs: Sequence[str],
        risk_level: str = "medium",
    ) -> ActiveAgentSelfReviewRun:
        """Run one disclosed active-Agent review after the human resolves alignment."""

        active = self._active_response()
        try:
            return run_active_agent_self_review(
                alignment_response=active,
                provider=provider,
                materializer=materializer,
                risk_level=risk_level,
                reason_codes=reason_codes,
                allowed_evidence_refs=allowed_evidence_refs,
            )
        except ActiveAgentSelfReviewError as exc:
            raise ReferenceAlignmentAdapterError(
                "active-Agent self-review did not produce an accepted advisory result"
            ) from exc

    def journey(self) -> AlignmentJourney:
        """Return normalized evidence and friction metrics without raw conversation."""

        active = self._responses[-1] if self._responses else None
        clarification_turns = (
            active.dialogue.metrics["clarification_turns"] if active is not None else 0
        )
        decision_episodes = (
            active.dialogue.metrics["governance_decision_episodes"]
            if active is not None
            else 0
        )
        return AlignmentJourney(
            status=active.status if active is not None else "not_started",
            sequence=len(self._responses),
            responses=tuple(self._responses),
            interaction_burden={
                "natural_language_requests": self._natural_language_requests,
                "natural_language_answers": self._natural_language_answers,
                "clarification_turns": clarification_turns,
                "single_select_decisions": self._single_select_decisions,
                "governance_decision_episodes": decision_episodes,
                "user_authored_structured_records": 0,
                "user_authored_internal_commands": 0,
                "manual_confirmation_words": 0,
            },
            privacy_boundary={
                "adapter_retains_raw_request": False,
                "adapter_retains_raw_answers": False,
                "adapter_retains_transcript": False,
                "core_receives_raw_conversation": False,
                "survives_restart": False,
            },
        )

    def _active_response(self) -> AlignmentStreamResponse:
        if not self._responses:
            raise ReferenceAlignmentAdapterError("alignment journey has not started")
        return self._responses[-1]

    def _process(self, payload: Mapping[str, Any]) -> AlignmentStreamResponse:
        try:
            response = self._session.process_payload(
                payload,
                sequence=len(self._responses) + 1,
            )
        except ValueError as exc:
            raise ReferenceAlignmentAdapterError(
                "Core rejected the host's normalized alignment draft"
            ) from exc
        self._responses.append(response)
        return response
