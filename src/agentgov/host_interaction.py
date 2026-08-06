"""Vendor-neutral host interaction requests and capability declarations."""

from __future__ import annotations

import hashlib
import re
from dataclasses import asdict, dataclass
from typing import Any, Mapping


CAPABILITIES_CONTRACT = "agentgov.host-interaction-capabilities"
CAPABILITIES_SCHEMA_VERSION = "1.0"
REQUEST_CONTRACT = "agentgov.host-interaction-request"
REQUEST_SCHEMA_VERSION = "1.0"

INTERACTION_KINDS = (
    "task_admission",
    "scope_resolution",
    "completion_review",
    "tool_permission",
)
REQUEST_KINDS = INTERACTION_KINDS[:3]
DELIVERY_MODES = {"native", "structured", "context_only", "unsupported"}
DECISION_RECORDING_MODES = {"adapter_event", "host_managed", "unavailable"}

_ID_RE = re.compile(r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$")
_REQUEST_ID_RE = re.compile(r"^req-[0-9a-f]{32}$")


class HostInteractionContractError(ValueError):
    """A host interaction declaration or request is ambiguous or unsafe."""


@dataclass(frozen=True)
class HostInteractionCapabilities:
    contract: str
    schema_version: str
    adapter_id: str
    surface_family: str
    interactions: Mapping[str, Mapping[str, str]]
    authority_boundary: Mapping[str, bool]


@dataclass(frozen=True)
class HostInteractionRequest:
    contract: str
    schema_version: str
    request_id: str
    kind: str
    status: str
    title: str
    summary: str
    options: tuple[Mapping[str, Any], ...]
    binding: Mapping[str, str]
    authority_boundary: Mapping[str, bool]


def _authority_boundary() -> Mapping[str, bool]:
    return {
        "decision_applied": False,
        "authorizes_scope_expansion": False,
        "authorizes_exception": False,
        "authorizes_commit": False,
        "authorizes_merge": False,
        "authorizes_deployment": False,
    }


def _required_identifier(value: Any, *, label: str) -> str:
    if not isinstance(value, str) or len(value) > 120 or not _ID_RE.fullmatch(value):
        raise HostInteractionContractError(f"{label} is invalid")
    return value


def host_interaction_capabilities_from_payload(
    payload: Any,
) -> HostInteractionCapabilities:
    fields = {
        "contract",
        "schema_version",
        "adapter_id",
        "surface_family",
        "interactions",
        "authority_boundary",
    }
    if not isinstance(payload, Mapping) or set(payload) != fields:
        raise HostInteractionContractError("host capabilities have unexpected fields")
    if (
        payload.get("contract") != CAPABILITIES_CONTRACT
        or payload.get("schema_version") != CAPABILITIES_SCHEMA_VERSION
    ):
        raise HostInteractionContractError("host capabilities use an unsupported contract")
    adapter_id = _required_identifier(payload.get("adapter_id"), label="adapter_id")
    surface_family = _required_identifier(
        payload.get("surface_family"), label="surface_family"
    )
    interactions = payload.get("interactions")
    if not isinstance(interactions, Mapping) or set(interactions) != set(INTERACTION_KINDS):
        raise HostInteractionContractError(
            "host capabilities must declare every interaction kind"
        )
    normalized: dict[str, Mapping[str, str]] = {}
    for kind in INTERACTION_KINDS:
        item = interactions[kind]
        if not isinstance(item, Mapping) or set(item) != {
            "delivery_mode",
            "decision_recording",
            "reason_code",
        }:
            raise HostInteractionContractError(f"{kind} capability has unexpected fields")
        delivery_mode = item.get("delivery_mode")
        decision_recording = item.get("decision_recording")
        if delivery_mode not in DELIVERY_MODES:
            raise HostInteractionContractError(f"{kind} delivery_mode is unsupported")
        if decision_recording not in DECISION_RECORDING_MODES:
            raise HostInteractionContractError(
                f"{kind} decision_recording is unsupported"
            )
        reason_code = _required_identifier(
            item.get("reason_code"), label=f"{kind} reason_code"
        )
        normalized[kind] = {
            "delivery_mode": delivery_mode,
            "decision_recording": decision_recording,
            "reason_code": reason_code,
        }
    authority = payload.get("authority_boundary")
    if (
        not isinstance(authority, Mapping)
        or set(authority) != set(_authority_boundary())
        or any(value is not False for value in authority.values())
    ):
        raise HostInteractionContractError(
            "host capabilities cannot grant governance or consequential authority"
        )
    return HostInteractionCapabilities(
        contract=CAPABILITIES_CONTRACT,
        schema_version=CAPABILITIES_SCHEMA_VERSION,
        adapter_id=adapter_id,
        surface_family=surface_family,
        interactions=normalized,
        authority_boundary=dict(authority),
    )


def build_host_interaction_capabilities(
    *,
    adapter_id: str,
    surface_family: str,
    interactions: Mapping[str, Mapping[str, str]],
) -> HostInteractionCapabilities:
    return host_interaction_capabilities_from_payload(
        {
            "contract": CAPABILITIES_CONTRACT,
            "schema_version": CAPABILITIES_SCHEMA_VERSION,
            "adapter_id": adapter_id,
            "surface_family": surface_family,
            "interactions": interactions,
            "authority_boundary": _authority_boundary(),
        }
    )


REFERENCE_HOST_CAPABILITIES = build_host_interaction_capabilities(
    adapter_id="agentgov.reference-adapter",
    surface_family="foreground_stream",
    interactions={
        "task_admission": {
            "delivery_mode": "structured",
            "decision_recording": "adapter_event",
            "reason_code": "structured_single_selection_available",
        },
        "scope_resolution": {
            "delivery_mode": "structured",
            "decision_recording": "adapter_event",
            "reason_code": "human_event_required",
        },
        "completion_review": {
            "delivery_mode": "structured",
            "decision_recording": "adapter_event",
            "reason_code": "human_event_required",
        },
        "tool_permission": {
            "delivery_mode": "unsupported",
            "decision_recording": "unavailable",
            "reason_code": "surface_has_no_permission_prompt",
        },
    },
)


def _request_id(event_id: str, kind: str) -> str:
    digest = hashlib.sha256(f"{event_id}\x00{kind}".encode("utf-8")).hexdigest()
    return "req-" + digest[:32]


def _next_event(
    event_type: str,
    fact_name: str,
    fact_value: str,
) -> Mapping[str, str]:
    return {
        "event_type": event_type,
        "fact_name": fact_name,
        "fact_value": fact_value,
    }


def _request_options(kind: str) -> tuple[Mapping[str, Any], ...]:
    if kind == "task_admission":
        return (
            {
                "id": "route_work_request",
                "label": "Route no-write, active, low-risk, or material work",
                "next_event": None,
            },
            {
                "id": "prepare_task_proposal",
                "label": "Prepare and review a structured task proposal",
                "next_event": None,
            },
            {"id": "review_task", "label": "Review a bounded task", "next_event": None},
            {"id": "decline", "label": "Decline the request", "next_event": None},
        )
    if kind == "scope_resolution":
        return (
            {
                "id": "review_task_revision",
                "label": "Review a revised task before readmission",
                "next_event": _next_event(
                    "scope.decision_recorded", "scope_decision", "approved"
                ),
            },
            {
                "id": "narrow_changes",
                "label": "Decline expansion and narrow the changes",
                "next_event": _next_event(
                    "scope.decision_recorded", "scope_decision", "declined"
                ),
            },
            {
                "id": "needs_human",
                "label": "Escalate for further human review",
                "next_event": _next_event(
                    "scope.decision_recorded", "scope_decision", "needs_human"
                ),
            },
        )
    if kind == "completion_review":
        return (
            {
                "id": "accept",
                "label": "Accept the verified completion",
                "next_event": _next_event(
                    "session.reviewed", "review_outcome", "accepted"
                ),
            },
            {
                "id": "request_changes",
                "label": "Request changes",
                "next_event": _next_event(
                    "session.reviewed", "review_outcome", "changes_requested"
                ),
            },
        )
    raise HostInteractionContractError("interaction request kind is unsupported")


def host_interaction_request_from_payload(payload: Any) -> HostInteractionRequest:
    fields = {
        "contract",
        "schema_version",
        "request_id",
        "kind",
        "status",
        "title",
        "summary",
        "options",
        "binding",
        "authority_boundary",
    }
    if not isinstance(payload, Mapping) or set(payload) != fields:
        raise HostInteractionContractError("host interaction request has unexpected fields")
    if (
        payload.get("contract") != REQUEST_CONTRACT
        or payload.get("schema_version") != REQUEST_SCHEMA_VERSION
    ):
        raise HostInteractionContractError(
            "host interaction request uses an unsupported contract"
        )
    request_id = payload.get("request_id")
    if not isinstance(request_id, str) or not _REQUEST_ID_RE.fullmatch(request_id):
        raise HostInteractionContractError("host interaction request_id is invalid")
    kind = payload.get("kind")
    if kind not in REQUEST_KINDS or payload.get("status") != "requires_human":
        raise HostInteractionContractError("host interaction request state is invalid")
    title = payload.get("title")
    summary = payload.get("summary")
    if not isinstance(title, str) or not title or not isinstance(summary, str) or not summary:
        raise HostInteractionContractError("host interaction request text is invalid")
    options = payload.get("options")
    if not isinstance(options, (list, tuple)) or len(options) < 2:
        raise HostInteractionContractError("host interaction request requires options")
    normalized_options: list[Mapping[str, Any]] = []
    option_ids: set[str] = set()
    for option in options:
        if not isinstance(option, Mapping) or set(option) != {"id", "label", "next_event"}:
            raise HostInteractionContractError("host interaction option has unexpected fields")
        option_id = option.get("id")
        label = option.get("label")
        if (
            not isinstance(option_id, str)
            or not re.fullmatch(r"^[a-z][a-z0-9_]*$", option_id)
            or option_id in option_ids
            or not isinstance(label, str)
            or not label
        ):
            raise HostInteractionContractError("host interaction option is invalid")
        option_ids.add(option_id)
        next_event = option.get("next_event")
        if kind == "task_admission":
            if next_event is not None:
                raise HostInteractionContractError(
                    "task admission has no implemented decision event"
                )
        else:
            expected = (
                ("scope.decision_recorded", "scope_decision")
                if kind == "scope_resolution"
                else ("session.reviewed", "review_outcome")
            )
            if (
                not isinstance(next_event, Mapping)
                or set(next_event) != {"event_type", "fact_name", "fact_value"}
                or (next_event.get("event_type"), next_event.get("fact_name"))
                != expected
            ):
                raise HostInteractionContractError(
                    "host interaction option does not map to the expected core event"
                )
            allowed_values = (
                {"approved", "declined", "needs_human"}
                if kind == "scope_resolution"
                else {"accepted", "changes_requested"}
            )
            if next_event.get("fact_value") not in allowed_values:
                raise HostInteractionContractError(
                    "host interaction option fact value is unsupported"
                )
        normalized_options.append(
            {"id": option_id, "label": label, "next_event": next_event}
        )
    binding = payload.get("binding")
    if not isinstance(binding, Mapping) or set(binding) != {
        "adapter_id",
        "delivery_mode",
        "decision_recording",
        "reason_code",
    }:
        raise HostInteractionContractError("host interaction binding has unexpected fields")
    adapter_id = _required_identifier(binding.get("adapter_id"), label="binding adapter_id")
    if binding.get("delivery_mode") not in DELIVERY_MODES:
        raise HostInteractionContractError("host interaction delivery_mode is unsupported")
    if binding.get("decision_recording") not in DECISION_RECORDING_MODES:
        raise HostInteractionContractError(
            "host interaction decision_recording is unsupported"
        )
    reason_code = _required_identifier(
        binding.get("reason_code"), label="binding reason_code"
    )
    authority = payload.get("authority_boundary")
    if (
        not isinstance(authority, Mapping)
        or set(authority) != set(_authority_boundary())
        or any(value is not False for value in authority.values())
    ):
        raise HostInteractionContractError(
            "host interaction request cannot apply a decision or grant authority"
        )
    return HostInteractionRequest(
        contract=REQUEST_CONTRACT,
        schema_version=REQUEST_SCHEMA_VERSION,
        request_id=request_id,
        kind=kind,
        status="requires_human",
        title=title,
        summary=summary,
        options=tuple(normalized_options),
        binding={
            "adapter_id": adapter_id,
            "delivery_mode": binding["delivery_mode"],
            "decision_recording": binding["decision_recording"],
            "reason_code": reason_code,
        },
        authority_boundary=dict(authority),
    )


def build_host_interaction_request(
    *,
    event_id: str,
    card: Any,
    capabilities: HostInteractionCapabilities = REFERENCE_HOST_CAPABILITIES,
) -> HostInteractionRequest | None:
    """Build a decision request only when the card represents a real human gate."""

    kind: str | None = None
    if card is None:
        return None
    if card.kind == "task" and card.status == "review_required":
        kind = "task_admission"
    elif card.kind == "scope" and card.status in {"blocked", "needs_human"}:
        kind = "scope_resolution"
    elif card.kind == "completion" and card.status == "review_ready":
        kind = "completion_review"
    if kind is None:
        return None
    binding = capabilities.interactions[kind]
    request = HostInteractionRequest(
        contract=REQUEST_CONTRACT,
        schema_version=REQUEST_SCHEMA_VERSION,
        request_id=_request_id(event_id, kind),
        kind=kind,
        status="requires_human",
        title=card.title,
        summary=card.summary,
        options=_request_options(kind),
        binding={
            "adapter_id": capabilities.adapter_id,
            "delivery_mode": binding["delivery_mode"],
            "decision_recording": binding["decision_recording"],
            "reason_code": binding["reason_code"],
        },
        authority_boundary=_authority_boundary(),
    )
    return host_interaction_request_from_payload(asdict(request))
