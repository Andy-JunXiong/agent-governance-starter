"""In-memory alignment dialogue transport for the foreground Coding Agent stream."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from typing import Any, Mapping

from agentgov.clarification_dialogue import (
    ALIGNMENT_CONTEXT_CONTRACT,
    CLARIFICATION_UPDATE_CONTRACT,
    AlignmentContext,
    ClarificationDialogue,
    ClarificationPrompt,
    alignment_context_from_payload,
    apply_clarification_update,
    build_alignment_resolution_prompt,
    build_next_clarification_prompt,
    clarification_dialogue_from_payload,
    clarification_prompt_from_payload,
    clarification_update_from_payload,
    denied_authority,
    resolve_clarification_dialogue,
    start_clarification_dialogue,
)
from agentgov.human_decision import (
    DECISION_RESULT_CONTRACT,
    HumanDecisionPrompt,
    human_decision_prompt_from_payload,
    human_decision_result_from_payload,
)
from agentgov.host_interaction import (
    REFERENCE_HOST_CAPABILITIES,
    HostInteractionCapabilities,
)


ALIGNMENT_RESPONSE_CONTRACT = "agentgov.coding-agent-alignment-response"
ALIGNMENT_RESPONSE_SCHEMA_VERSION = "1.0"
SUPPORTED_INPUT_CONTRACTS = {
    ALIGNMENT_CONTEXT_CONTRACT,
    CLARIFICATION_UPDATE_CONTRACT,
    DECISION_RESULT_CONTRACT,
}

_CONTEXT_ID_RE = re.compile(r"^acx-[0-9a-f]{32}$")
_UPDATE_ID_RE = re.compile(r"^cup-[0-9a-f]{32}$")
_RESULT_ID_RE = re.compile(r"^drs-[0-9a-f]{32}$")
_ADAPTER_ID_RE = re.compile(r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$")


class AlignmentTransportError(ValueError):
    """An alignment stream record is invalid, stale, or out of order."""


@dataclass(frozen=True)
class AlignmentStreamResponse:
    contract: str
    schema_version: str
    sequence: int
    input: Mapping[str, str]
    status: str
    persistence: Mapping[str, Any]
    dialogue: ClarificationDialogue
    clarification_prompt: ClarificationPrompt | None
    decision_prompt: HumanDecisionPrompt | None
    authority_boundary: Mapping[str, bool]


def alignment_stream_record_from_json(line: str) -> Mapping[str, Any]:
    """Parse one non-blank JSON object without accepting an unknown contract."""

    if not line.strip():
        raise AlignmentTransportError("coding-agent stream records cannot be blank")
    try:
        payload = json.loads(line)
    except json.JSONDecodeError as exc:
        raise AlignmentTransportError("coding-agent stream record is not valid JSON") from exc
    if not isinstance(payload, Mapping):
        raise AlignmentTransportError("coding-agent stream record must be a JSON object")
    return payload


def _input_identity(
    *, contract: str, input_id: str, actor_class: str, adapter_id: str
) -> Mapping[str, str]:
    patterns = {
        ALIGNMENT_CONTEXT_CONTRACT: (_CONTEXT_ID_RE, "coding_agent"),
        CLARIFICATION_UPDATE_CONTRACT: (_UPDATE_ID_RE, "human"),
        DECISION_RESULT_CONTRACT: (_RESULT_ID_RE, "human"),
    }
    if contract not in patterns:
        raise AlignmentTransportError("alignment input contract is unsupported")
    pattern, expected_actor = patterns[contract]
    if not isinstance(input_id, str) or not pattern.fullmatch(input_id):
        raise AlignmentTransportError("alignment input identity is invalid")
    if actor_class != expected_actor:
        raise AlignmentTransportError("alignment input actor is invalid")
    if not isinstance(adapter_id, str) or not _ADAPTER_ID_RE.fullmatch(adapter_id):
        raise AlignmentTransportError("alignment input adapter is invalid")
    return {
        "contract": contract,
        "id": input_id,
        "actor_class": actor_class,
        "adapter_id": adapter_id,
    }


def alignment_stream_response_from_payload(payload: Any) -> AlignmentStreamResponse:
    fields = {
        "contract",
        "schema_version",
        "sequence",
        "input",
        "status",
        "persistence",
        "dialogue",
        "clarification_prompt",
        "decision_prompt",
        "authority_boundary",
    }
    if not isinstance(payload, Mapping) or set(payload) != fields:
        raise AlignmentTransportError("alignment response has unexpected fields")
    if (
        payload.get("contract") != ALIGNMENT_RESPONSE_CONTRACT
        or payload.get("schema_version") != ALIGNMENT_RESPONSE_SCHEMA_VERSION
    ):
        raise AlignmentTransportError("alignment response contract is unsupported")
    sequence = payload.get("sequence")
    if not isinstance(sequence, int) or isinstance(sequence, bool) or sequence < 1:
        raise AlignmentTransportError("alignment response sequence is invalid")
    input_value = payload.get("input")
    if not isinstance(input_value, Mapping) or set(input_value) != {
        "contract", "id", "actor_class", "adapter_id"
    }:
        raise AlignmentTransportError("alignment response input binding is invalid")
    input_identity = _input_identity(
        contract=input_value.get("contract"),
        input_id=input_value.get("id"),
        actor_class=input_value.get("actor_class"),
        adapter_id=input_value.get("adapter_id"),
    )
    persistence = payload.get("persistence")
    if persistence != {"mode": "foreground_memory", "survives_restart": False}:
        raise AlignmentTransportError("alignment response persistence claim is invalid")
    dialogue = clarification_dialogue_from_payload(payload.get("dialogue"))
    if payload.get("status") != dialogue.status:
        raise AlignmentTransportError("alignment response status does not match dialogue")
    clarification_value = payload.get("clarification_prompt")
    decision_value = payload.get("decision_prompt")
    clarification = (
        None
        if clarification_value is None
        else clarification_prompt_from_payload(clarification_value)
    )
    decision = (
        None
        if decision_value is None
        else human_decision_prompt_from_payload(decision_value)
    )
    if dialogue.status == "exploring":
        expected = build_next_clarification_prompt(dialogue)
        if clarification is None or asdict(clarification) != asdict(expected) or decision is not None:
            raise AlignmentTransportError("exploring response requires the exact next question")
    elif dialogue.status == "ready_for_decision":
        expected = build_alignment_resolution_prompt(dialogue, binding=decision.binding)
        if decision is None or asdict(decision) != asdict(expected) or clarification is not None:
            raise AlignmentTransportError("ready response requires the exact final decision")
    elif clarification is not None or decision is not None:
        raise AlignmentTransportError("terminal alignment response cannot carry another prompt")
    authority = payload.get("authority_boundary")
    if authority != denied_authority():
        raise AlignmentTransportError("alignment response cannot grant project authority")
    return AlignmentStreamResponse(
        contract=ALIGNMENT_RESPONSE_CONTRACT,
        schema_version=ALIGNMENT_RESPONSE_SCHEMA_VERSION,
        sequence=sequence,
        input=input_identity,
        status=dialogue.status,
        persistence=dict(persistence),
        dialogue=dialogue,
        clarification_prompt=clarification,
        decision_prompt=decision,
        authority_boundary=dict(authority),
    )


def _build_response(
    *,
    sequence: int,
    input_identity: Mapping[str, str],
    dialogue: ClarificationDialogue,
    decision_binding: Mapping[str, str],
) -> AlignmentStreamResponse:
    clarification = (
        build_next_clarification_prompt(dialogue)
        if dialogue.status == "exploring"
        else None
    )
    decision = (
        build_alignment_resolution_prompt(dialogue, binding=decision_binding)
        if dialogue.status == "ready_for_decision"
        else None
    )
    return alignment_stream_response_from_payload(
        {
            "contract": ALIGNMENT_RESPONSE_CONTRACT,
            "schema_version": ALIGNMENT_RESPONSE_SCHEMA_VERSION,
            "sequence": sequence,
            "input": dict(input_identity),
            "status": dialogue.status,
            "persistence": {"mode": "foreground_memory", "survives_restart": False},
            "dialogue": asdict(dialogue),
            "clarification_prompt": None if clarification is None else asdict(clarification),
            "decision_prompt": None if decision is None else asdict(decision),
            "authority_boundary": denied_authority(),
        }
    )


class AlignmentStreamSession:
    """Advance one alignment dialogue atomically for one foreground connection."""

    def __init__(
        self,
        *,
        host_capabilities: HostInteractionCapabilities = REFERENCE_HOST_CAPABILITIES,
    ) -> None:
        self._dialogue: ClarificationDialogue | None = None
        self._clarification_prompt: ClarificationPrompt | None = None
        self._decision_prompt: HumanDecisionPrompt | None = None
        self._seen_input_ids: set[str] = set()
        self._coding_adapter_id: str | None = None
        capability = host_capabilities.interactions["task_admission"]
        self._decision_binding = {
            "adapter_id": host_capabilities.adapter_id,
            "delivery_mode": capability["delivery_mode"],
            "decision_recording": capability["decision_recording"],
            "reason_code": capability["reason_code"],
        }

    @property
    def coding_adapter_id(self) -> str | None:
        return self._coding_adapter_id

    def process_payload(self, payload: Any, *, sequence: int) -> AlignmentStreamResponse:
        if not isinstance(payload, Mapping):
            raise AlignmentTransportError("alignment stream record must be an object")
        contract = payload.get("contract")
        if contract not in SUPPORTED_INPUT_CONTRACTS:
            raise AlignmentTransportError("alignment input contract is unsupported")
        if sequence < 1:
            raise AlignmentTransportError("alignment sequence must be positive")

        if contract == ALIGNMENT_CONTEXT_CONTRACT:
            context = alignment_context_from_payload(payload)
            identity = _input_identity(
                contract=contract,
                input_id=context.context_id,
                actor_class=context.source["actor_class"],
                adapter_id=context.source["adapter_id"],
            )
            if context.context_id in self._seen_input_ids:
                raise AlignmentTransportError("duplicate alignment context_id in stream")
            if self._coding_adapter_id is not None and (
                context.source["adapter_id"] != self._coding_adapter_id
            ):
                raise AlignmentTransportError("alignment Coding Agent adapter drifted")
            if self._dialogue is not None and self._dialogue.status in {
                "exploring", "ready_for_decision"
            }:
                raise AlignmentTransportError("an unresolved alignment dialogue is already active")
            next_dialogue = start_clarification_dialogue(context)
            response = _build_response(
                sequence=sequence,
                input_identity=identity,
                dialogue=next_dialogue,
                decision_binding=self._decision_binding,
            )
            self._dialogue = next_dialogue
            self._clarification_prompt = response.clarification_prompt
            self._decision_prompt = response.decision_prompt
            self._coding_adapter_id = context.source["adapter_id"]
            self._seen_input_ids.add(context.context_id)
            return response

        if self._dialogue is None:
            raise AlignmentTransportError("alignment update requires an active dialogue")

        if contract == CLARIFICATION_UPDATE_CONTRACT:
            update = clarification_update_from_payload(payload)
            identity = _input_identity(
                contract=contract,
                input_id=update.update_id,
                actor_class=update.actor["actor_class"],
                adapter_id=update.actor["adapter_id"],
            )
            if update.update_id in self._seen_input_ids:
                raise AlignmentTransportError("duplicate clarification update_id in stream")
            if self._clarification_prompt is None:
                raise AlignmentTransportError("active dialogue is not waiting for clarification")
            try:
                next_dialogue = apply_clarification_update(
                    self._dialogue,
                    self._clarification_prompt,
                    update,
                )
            except ValueError as exc:
                raise AlignmentTransportError(str(exc)) from exc
            response = _build_response(
                sequence=sequence,
                input_identity=identity,
                dialogue=next_dialogue,
                decision_binding=self._decision_binding,
            )
            self._dialogue = next_dialogue
            self._clarification_prompt = response.clarification_prompt
            self._decision_prompt = response.decision_prompt
            self._seen_input_ids.add(update.update_id)
            return response

        result = human_decision_result_from_payload(payload)
        identity = _input_identity(
            contract=contract,
            input_id=result.result_id,
            actor_class=result.actor["actor_class"],
            adapter_id=result.actor["adapter_id"],
        )
        if result.result_id in self._seen_input_ids:
            raise AlignmentTransportError("duplicate human decision result_id in stream")
        if self._decision_prompt is None:
            raise AlignmentTransportError("active dialogue is not waiting for a final decision")
        try:
            next_dialogue = resolve_clarification_dialogue(
                self._dialogue,
                self._decision_prompt,
                result,
            )
        except ValueError as exc:
            raise AlignmentTransportError(str(exc)) from exc
        response = _build_response(
            sequence=sequence,
            input_identity=identity,
            dialogue=next_dialogue,
            decision_binding=self._decision_binding,
        )
        self._dialogue = next_dialogue
        self._clarification_prompt = response.clarification_prompt
        self._decision_prompt = response.decision_prompt
        self._seen_input_ids.add(result.result_id)
        return response


def render_alignment_stream_response_json(response: AlignmentStreamResponse) -> str:
    response = alignment_stream_response_from_payload(asdict(response))
    return json.dumps(asdict(response), ensure_ascii=False, sort_keys=True) + "\n"


def render_alignment_stream_response_terminal(response: AlignmentStreamResponse) -> str:
    response = alignment_stream_response_from_payload(asdict(response))
    lines = [
        f"AGENTGOV ALIGNMENT {response.sequence} {response.status}",
        f"INPUT {response.input['contract']} ({response.input['id']})",
        f"DIALOGUE {response.dialogue.dialogue_id} revision={response.dialogue.revision}",
        "PERSISTENCE foreground_memory survives_restart=false",
    ]
    if response.clarification_prompt is not None:
        lines.extend(
            (
                f"CENTER {response.clarification_prompt.center_summary}",
                f"OBSERVED_DRIFT {response.clarification_prompt.drift_summary}",
                f"QUESTION {response.clarification_prompt.question['text']}",
                "ANSWER natural language through the host; Core receives only a normalized update",
            )
        )
    elif response.decision_prompt is not None:
        prompt = response.decision_prompt
        lines.append(
            f"DECISION_PROMPT {prompt.kind} single_select recommended={prompt.recommended_option_id}"
        )
        for option in prompt.options:
            lines.append(f"OPTION {option['index']} {option['id']}: {option['label']}")
    else:
        lines.append("PROMPT none")
    lines.append(
        "AUTHORITY center=false task=false session=false code=false scope=false exception=false git=false deployment=false release=false"
    )
    return "\n".join(lines) + "\n"
