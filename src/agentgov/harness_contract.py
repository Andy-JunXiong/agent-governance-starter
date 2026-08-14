"""Dependency-free validation and evaluation for Harness Contract v1."""

from __future__ import annotations

import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from agentgov.path_policy import scope_path_error


HARNESS_CONTRACT = "agentgov.harness-run"
HARNESS_SCHEMA_VERSION = "1.0"
EVIDENCE_STRENGTHS = {
    "observed",
    "paired_counterfactual",
    "repeated_intervention",
    "cross_context_replication",
}
HARNESS_STAGES = (
    "session_start",
    "work_request",
    "agent_selection",
    "proposal_materialization",
    "governance_decision",
    "human_decision_mediation",
    "before_action",
    "after_action",
    "scope_observation",
    "validation",
    "intervention_outcome",
    "completion_request",
    "handoff",
    "terminal",
)
ACTOR_CLASSES = {"host", "agent", "agentgov", "human", "ci_scm"}
GOVERNANCE_EFFECTS = {"OBSERVE", "ADVISE", "MEDIATE", "BLOCK"}
DISPOSITIONS = {"continue", "pause", "abort", "no_op"}
RESULT_STATUSES = {
    "accepted",
    "denied",
    "unavailable",
    "invalid",
    "stale",
    "duplicate",
    "error",
}
TERMINAL_STATUSES = {"completed", "failed", "interrupted", "unknown"}
CHANNEL_STATUSES = {"conforming", "deviating", "not_reached", "unknown"}
CHANNEL_NAMES = (
    "agent_selection",
    "governance_decision",
    "intervention_outcome",
)
OBSERVATION_MODES = {
    "event_stream",
    "lifecycle_hook",
    "mcp",
    "mixed",
    "unknown",
}
MEDIATION_MODES = {"none", "human_form", "host_permission", "custom", "unknown"}
BLOCK_MODES = {"supported", "unsupported", "unknown"}
EXECUTION_MODES = {"synchronous", "asynchronous", "mixed", "unknown"}
DECISION_DELIVERY_MODES = {"native", "structured", "context_only", "unsupported"}
DECISION_RECORDING_MODES = {"adapter_event", "host_managed", "unavailable"}
HUMAN_ORIGIN_ASSURANCE = {
    "bound_native_form",
    "host_asserted",
    "unavailable",
    "unknown",
}
FAILURE_BEHAVIORS = {"fail_open", "fail_closed", "host_default", "unknown"}
TIMEOUT_BEHAVIORS = {"fail_open", "fail_closed", "host_default", "unknown"}
CONFIDENCE_LEVELS = {
    "documented",
    "locally_demonstrated",
    "externally_demonstrated",
    "unknown",
}

_RUN_ID_RE = re.compile(r"^hrn-[0-9a-f]{16}$")
_TRANSITION_ID_RE = re.compile(r"^trn-[a-z0-9]+(?:-[a-z0-9]+)*$")
_NORMALIZED_ID_RE = re.compile(r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$")
_STAGE_RANK = {stage: index for index, stage in enumerate(HARNESS_STAGES)}
_COMPARE_FIELDS = (
    "actor_class",
    "outcome",
    "effect",
    "disposition",
    "side_effect_completed",
)


@dataclass(frozen=True)
class HarnessEvaluation:
    """One deterministic validation and First Deviation result."""

    run_id: str | None
    errors: tuple[str, ...]
    first_deviation: Mapping[str, Any] | None
    channel_statuses: Mapping[str, str]

    @property
    def valid(self) -> bool:
        return not self.errors


def _mapping(value: Any, path: str, errors: list[str]) -> Mapping[str, Any] | None:
    if not isinstance(value, Mapping):
        errors.append(f"{path} must be an object")
        return None
    return value


def _fields(
    value: Mapping[str, Any],
    *,
    path: str,
    required: set[str],
    errors: list[str],
) -> None:
    actual = set(value)
    for field in sorted(required - actual):
        errors.append(f"{path}.{field} is required")
    for field in sorted(actual - required):
        errors.append(f"{path}.{field} is not allowed")


def _string(
    value: Any,
    path: str,
    errors: list[str],
    *,
    minimum: int = 1,
    maximum: int = 400,
) -> str | None:
    if not isinstance(value, str) or not minimum <= len(value.strip()) <= maximum:
        errors.append(
            f"{path} must be a string between {minimum} and {maximum} characters"
        )
        return None
    return value


def _enum(value: Any, path: str, allowed: set[str], errors: list[str]) -> str | None:
    if not isinstance(value, str) or value not in allowed:
        errors.append(f"{path} must be one of {sorted(allowed)}")
        return None
    return value


def _normalized_id(value: Any, path: str, errors: list[str]) -> str | None:
    result = _string(value, path, errors, maximum=120)
    if result is not None and _NORMALIZED_ID_RE.fullmatch(result) is None:
        errors.append(f"{path} must be a normalized identifier")
        return None
    return result


def _boolean(value: Any, path: str, errors: list[str]) -> bool | None:
    if not isinstance(value, bool):
        errors.append(f"{path} must be a boolean")
        return None
    return value


def _string_list(
    value: Any,
    path: str,
    errors: list[str],
    *,
    minimum: int = 0,
    maximum: int = 20,
    normalized: bool = False,
) -> list[str] | None:
    if not isinstance(value, list):
        errors.append(f"{path} must be an array")
        return None
    if not minimum <= len(value) <= maximum:
        errors.append(f"{path} must contain between {minimum} and {maximum} items")
    if any(not isinstance(item, str) or not item.strip() for item in value):
        errors.append(f"{path} must contain only non-empty strings")
        return None
    for index, item in enumerate(value):
        maximum_length = 120 if normalized else 400
        if len(item) > maximum_length:
            errors.append(
                f"{path}[{index}] must contain at most {maximum_length} characters"
            )
    if len(set(value)) != len(value):
        errors.append(f"{path} must contain unique items")
    if normalized:
        for index, item in enumerate(value):
            if _NORMALIZED_ID_RE.fullmatch(item) is None:
                errors.append(f"{path}[{index}] must be a normalized identifier")
    return value


def _evidence_refs(
    value: Any, path: str, errors: list[str], *, minimum: int = 0
) -> list[str] | None:
    items = _string_list(value, path, errors, minimum=minimum)
    if items is not None:
        for index, item in enumerate(items):
            problem = scope_path_error(item)
            if problem:
                errors.append(f"{path}[{index}] {problem}")
    return items


def _nullable_normalized_id(value: Any, path: str, errors: list[str]) -> str | None:
    if value is None:
        return None
    return _normalized_id(value, path, errors)


def _validate_scenario(value: Any, errors: list[str]) -> None:
    scenario = _mapping(value, "$.scenario", errors)
    if scenario is None:
        return
    fields = {"scenario_id", "title", "evidence_strength", "source_refs"}
    _fields(scenario, path="$.scenario", required=fields, errors=errors)
    _normalized_id(scenario.get("scenario_id"), "$.scenario.scenario_id", errors)
    _string(scenario.get("title"), "$.scenario.title", errors, minimum=5, maximum=200)
    _enum(
        scenario.get("evidence_strength"),
        "$.scenario.evidence_strength",
        EVIDENCE_STRENGTHS,
        errors,
    )
    _evidence_refs(scenario.get("source_refs"), "$.scenario.source_refs", errors, minimum=1)


def _validate_capabilities(value: Any, errors: list[str]) -> Mapping[str, Any] | None:
    path = "$.host.capabilities"
    capabilities = _mapping(value, path, errors)
    if capabilities is None:
        return None
    fields = {
        "observation_mode",
        "mediation_mode",
        "block_mode",
        "observe_action",
        "pre_action_hook",
        "human_decision_ui",
        "mediate_action",
        "block_action",
        "post_action_evidence",
        "semantic_materializer",
        "coverage",
        "execution_mode",
        "decision_delivery",
        "decision_recording",
        "human_origin_assurance",
        "failure_behavior",
        "timeout_behavior",
        "bypass_conditions",
        "configuration_requirements",
        "confidence",
        "evidence_refs",
    }
    _fields(capabilities, path=path, required=fields, errors=errors)
    _enum(capabilities.get("observation_mode"), f"{path}.observation_mode", OBSERVATION_MODES, errors)
    _enum(capabilities.get("mediation_mode"), f"{path}.mediation_mode", MEDIATION_MODES, errors)
    _enum(capabilities.get("block_mode"), f"{path}.block_mode", BLOCK_MODES, errors)
    for field in (
        "observe_action",
        "pre_action_hook",
        "human_decision_ui",
        "mediate_action",
        "block_action",
        "post_action_evidence",
        "semantic_materializer",
    ):
        _boolean(capabilities.get(field), f"{path}.{field}", errors)
    _string_list(capabilities.get("coverage"), f"{path}.coverage", errors, minimum=1, normalized=True)
    _enum(capabilities.get("execution_mode"), f"{path}.execution_mode", EXECUTION_MODES, errors)
    _enum(capabilities.get("decision_delivery"), f"{path}.decision_delivery", DECISION_DELIVERY_MODES, errors)
    _enum(capabilities.get("decision_recording"), f"{path}.decision_recording", DECISION_RECORDING_MODES, errors)
    _enum(
        capabilities.get("human_origin_assurance"),
        f"{path}.human_origin_assurance",
        HUMAN_ORIGIN_ASSURANCE,
        errors,
    )
    _enum(capabilities.get("failure_behavior"), f"{path}.failure_behavior", FAILURE_BEHAVIORS, errors)
    _enum(capabilities.get("timeout_behavior"), f"{path}.timeout_behavior", TIMEOUT_BEHAVIORS, errors)
    _string_list(capabilities.get("bypass_conditions"), f"{path}.bypass_conditions", errors)
    _string_list(
        capabilities.get("configuration_requirements"),
        f"{path}.configuration_requirements",
        errors,
    )
    _enum(capabilities.get("confidence"), f"{path}.confidence", CONFIDENCE_LEVELS, errors)
    _evidence_refs(capabilities.get("evidence_refs"), f"{path}.evidence_refs", errors, minimum=1)
    return capabilities


def _validate_host(value: Any, errors: list[str]) -> Mapping[str, Any] | None:
    host = _mapping(value, "$.host", errors)
    if host is None:
        return None
    fields = {
        "adapter_id",
        "adapter_version",
        "host_family",
        "host_surface",
        "host_version",
        "provider_family",
        "repository_correlation",
        "capabilities",
    }
    _fields(host, path="$.host", required=fields, errors=errors)
    for field in ("adapter_id", "host_family", "host_surface", "provider_family", "repository_correlation"):
        _normalized_id(host.get(field), f"$.host.{field}", errors)
    _string(host.get("adapter_version"), "$.host.adapter_version", errors, maximum=80)
    _string(host.get("host_version"), "$.host.host_version", errors, maximum=80)
    _validate_capabilities(host.get("capabilities"), errors)
    return host


def _validate_transition(
    value: Any, path: str, errors: list[str]
) -> Mapping[str, Any] | None:
    transition = _mapping(value, path, errors)
    if transition is None:
        return None
    fields = {
        "sequence",
        "transition_id",
        "stage",
        "actor_class",
        "outcome",
        "effect",
        "disposition",
        "side_effect_completed",
        "reason_code",
        "evidence_refs",
    }
    _fields(transition, path=path, required=fields, errors=errors)
    sequence = transition.get("sequence")
    if not isinstance(sequence, int) or isinstance(sequence, bool) or not 1 <= sequence <= 64:
        errors.append(f"{path}.sequence must be an integer between 1 and 64")
    transition_id = _string(transition.get("transition_id"), f"{path}.transition_id", errors, maximum=120)
    if transition_id is not None and _TRANSITION_ID_RE.fullmatch(transition_id) is None:
        errors.append(f"{path}.transition_id must be a normalized transition identifier")
    _enum(transition.get("stage"), f"{path}.stage", set(HARNESS_STAGES), errors)
    _enum(transition.get("actor_class"), f"{path}.actor_class", ACTOR_CLASSES, errors)
    _normalized_id(transition.get("outcome"), f"{path}.outcome", errors)
    _enum(transition.get("effect"), f"{path}.effect", GOVERNANCE_EFFECTS, errors)
    _enum(transition.get("disposition"), f"{path}.disposition", DISPOSITIONS, errors)
    _boolean(transition.get("side_effect_completed"), f"{path}.side_effect_completed", errors)
    _nullable_normalized_id(transition.get("reason_code"), f"{path}.reason_code", errors)
    _evidence_refs(transition.get("evidence_refs"), f"{path}.evidence_refs", errors, minimum=1)
    return transition


def _validate_trace(value: Any, path: str, errors: list[str]) -> list[Mapping[str, Any]] | None:
    if not isinstance(value, list):
        errors.append(f"{path} must be an array")
        return None
    if not 1 <= len(value) <= 64:
        errors.append(f"{path} must contain between 1 and 64 transitions")
    transitions: list[Mapping[str, Any]] = []
    for index, item in enumerate(value):
        transition = _validate_transition(item, f"{path}[{index}]", errors)
        if transition is not None:
            transitions.append(transition)
    if len(transitions) != len(value):
        return None
    sequences = [item.get("sequence") for item in transitions]
    if sequences != list(range(1, len(transitions) + 1)):
        errors.append(f"{path} sequence values must be contiguous and ordered from 1")
    identifiers = [item.get("transition_id") for item in transitions]
    if all(isinstance(item, str) for item in identifiers) and len(
        set(identifiers)
    ) != len(identifiers):
        errors.append(f"{path} transition_id values must be unique")
    stages = [item.get("stage") for item in transitions]
    if all(isinstance(item, str) for item in stages) and len(set(stages)) != len(stages):
        errors.append(f"{path} stages must be unique")
    if all(isinstance(stage, str) and stage in _STAGE_RANK for stage in stages):
        ranks = [_STAGE_RANK[stage] for stage in stages]
        if ranks != sorted(ranks):
            errors.append(f"{path} stages must follow Harness lifecycle order")
    return transitions


def _validate_channels(value: Any, errors: list[str]) -> Mapping[str, Any] | None:
    channels = _mapping(value, "$.channels", errors)
    if channels is None:
        return None
    _fields(channels, path="$.channels", required=set(CHANNEL_NAMES), errors=errors)
    fields = {"status", "reason_code", "summary", "evidence_refs"}
    for name in CHANNEL_NAMES:
        path = f"$.channels.{name}"
        channel = _mapping(channels.get(name), path, errors)
        if channel is None:
            continue
        _fields(channel, path=path, required=fields, errors=errors)
        _enum(channel.get("status"), f"{path}.status", CHANNEL_STATUSES, errors)
        _normalized_id(channel.get("reason_code"), f"{path}.reason_code", errors)
        _string(channel.get("summary"), f"{path}.summary", errors, maximum=400)
        _evidence_refs(channel.get("evidence_refs"), f"{path}.evidence_refs", errors, minimum=1)
    return channels


def _empty_first_deviation() -> dict[str, Any]:
    return {
        "present": False,
        "sequence": None,
        "stage": None,
        "code": None,
        "expected_outcome": None,
        "observed_outcome": None,
    }


def derive_first_deviation(document: Mapping[str, Any]) -> dict[str, Any]:
    """Return the earliest exact transition mismatch in one normalized run."""

    expected = document.get("expected_transitions")
    observed = document.get("observed_transitions")
    if not isinstance(expected, Sequence) or isinstance(expected, (str, bytes)):
        raise ValueError("expected_transitions must be an array")
    if not isinstance(observed, Sequence) or isinstance(observed, (str, bytes)):
        raise ValueError("observed_transitions must be an array")
    if len(expected) != len(observed):
        raise ValueError("expected and observed traces must contain the same stages")

    for index, (expected_item, observed_item) in enumerate(zip(expected, observed)):
        if not isinstance(expected_item, Mapping) or not isinstance(observed_item, Mapping):
            raise ValueError("transition entries must be objects")
        if expected_item.get("transition_id") != observed_item.get("transition_id"):
            raise ValueError("expected and observed transition identities must match")
        if expected_item.get("stage") != observed_item.get("stage"):
            raise ValueError("expected and observed transition stages must match")
        mismatched = next(
            (field for field in _COMPARE_FIELDS if expected_item.get(field) != observed_item.get(field)),
            None,
        )
        if mismatched is None:
            continue
        code = observed_item.get("reason_code")
        if not isinstance(code, str) or _NORMALIZED_ID_RE.fullmatch(code) is None:
            code = f"{mismatched}_mismatch"
        return {
            "present": True,
            "sequence": index + 1,
            "stage": observed_item.get("stage"),
            "code": code,
            "expected_outcome": expected_item.get("outcome"),
            "observed_outcome": observed_item.get("outcome"),
        }
    return _empty_first_deviation()


def _validate_first_deviation(value: Any, errors: list[str]) -> Mapping[str, Any] | None:
    path = "$.first_deviation"
    deviation = _mapping(value, path, errors)
    if deviation is None:
        return None
    fields = {"present", "sequence", "stage", "code", "expected_outcome", "observed_outcome"}
    _fields(deviation, path=path, required=fields, errors=errors)
    present = _boolean(deviation.get("present"), f"{path}.present", errors)
    nullable_fields = ("sequence", "stage", "code", "expected_outcome", "observed_outcome")
    if present is False:
        for field in nullable_fields:
            if deviation.get(field) is not None:
                errors.append(f"{path}.{field} must be null when no deviation is present")
    elif present is True:
        sequence = deviation.get("sequence")
        if not isinstance(sequence, int) or isinstance(sequence, bool) or not 1 <= sequence <= 64:
            errors.append(f"{path}.sequence must be an integer between 1 and 64")
        _enum(deviation.get("stage"), f"{path}.stage", set(HARNESS_STAGES), errors)
        for field in ("code", "expected_outcome", "observed_outcome"):
            _normalized_id(deviation.get(field), f"{path}.{field}", errors)
    return deviation


def _validate_harness_result(value: Any, errors: list[str]) -> Mapping[str, Any] | None:
    path = "$.harness_result"
    result = _mapping(value, path, errors)
    if result is None:
        return None
    fields = {
        "disposition",
        "effect",
        "status",
        "reason_code",
        "affected_transition",
        "prevented_transition",
        "already_completed_effect",
    }
    _fields(result, path=path, required=fields, errors=errors)
    _enum(result.get("disposition"), f"{path}.disposition", DISPOSITIONS, errors)
    _enum(result.get("effect"), f"{path}.effect", GOVERNANCE_EFFECTS, errors)
    _enum(result.get("status"), f"{path}.status", RESULT_STATUSES, errors)
    _normalized_id(result.get("reason_code"), f"{path}.reason_code", errors)
    _enum(result.get("affected_transition"), f"{path}.affected_transition", set(HARNESS_STAGES), errors)
    prevented = result.get("prevented_transition")
    if prevented is not None:
        _enum(prevented, f"{path}.prevented_transition", set(HARNESS_STAGES), errors)
    _boolean(result.get("already_completed_effect"), f"{path}.already_completed_effect", errors)
    return result


def _validate_terminal(value: Any, errors: list[str]) -> Mapping[str, Any] | None:
    path = "$.terminal"
    terminal = _mapping(value, path, errors)
    if terminal is None:
        return None
    fields = {"status", "repository_modified", "external_side_effect_completed"}
    _fields(terminal, path=path, required=fields, errors=errors)
    _enum(terminal.get("status"), f"{path}.status", TERMINAL_STATUSES, errors)
    _boolean(terminal.get("repository_modified"), f"{path}.repository_modified", errors)
    _boolean(
        terminal.get("external_side_effect_completed"),
        f"{path}.external_side_effect_completed",
        errors,
    )
    return terminal


def _validate_false_boundary(
    value: Any, path: str, fields: set[str], errors: list[str]
) -> None:
    boundary = _mapping(value, path, errors)
    if boundary is None:
        return
    _fields(boundary, path=path, required=fields, errors=errors)
    for field in sorted(fields):
        current = boundary.get(field)
        _boolean(current, f"{path}.{field}", errors)
        if current is not False:
            errors.append(f"{path}.{field} must be false")


def validate_harness_run_document(document: Mapping[str, Any]) -> list[str]:
    """Return deterministic structural and semantic violations for one run."""

    errors: list[str] = []
    top_fields = {
        "contract",
        "schema_version",
        "run_id",
        "scenario",
        "host",
        "expected_transitions",
        "observed_transitions",
        "channels",
        "first_deviation",
        "harness_result",
        "terminal",
        "privacy_boundary",
        "claim_limits",
        "authority_boundary",
    }
    _fields(document, path="$", required=top_fields, errors=errors)
    if document.get("contract") != HARNESS_CONTRACT:
        errors.append(f"$.contract must equal {HARNESS_CONTRACT!r}")
    if document.get("schema_version") != HARNESS_SCHEMA_VERSION:
        errors.append(f"$.schema_version must equal {HARNESS_SCHEMA_VERSION!r}")
    run_id = _string(document.get("run_id"), "$.run_id", errors, maximum=20)
    if run_id is not None and _RUN_ID_RE.fullmatch(run_id) is None:
        errors.append("$.run_id must match hrn- followed by 16 lowercase hex characters")

    _validate_scenario(document.get("scenario"), errors)
    host = _validate_host(document.get("host"), errors)
    expected = _validate_trace(document.get("expected_transitions"), "$.expected_transitions", errors)
    observed = _validate_trace(document.get("observed_transitions"), "$.observed_transitions", errors)
    _validate_channels(document.get("channels"), errors)
    declared = _validate_first_deviation(document.get("first_deviation"), errors)
    result = _validate_harness_result(document.get("harness_result"), errors)
    terminal = _validate_terminal(document.get("terminal"), errors)
    _validate_false_boundary(
        document.get("privacy_boundary"),
        "$.privacy_boundary",
        {
            "contains_raw_prompt",
            "contains_transcript",
            "contains_model_output",
            "contains_tool_input_output",
            "contains_source_content",
            "contains_credentials",
            "contains_absolute_paths",
            "contains_unbounded_payloads",
        },
        errors,
    )
    _validate_false_boundary(
        document.get("claim_limits"),
        "$.claim_limits",
        {
            "claims_causality",
            "publishes_effectiveness_percentage",
            "claims_cross_context_replication",
            "publishes_coverage_percentage",
        },
        errors,
    )
    _validate_false_boundary(
        document.get("authority_boundary"),
        "$.authority_boundary",
        {
            "admits_task",
            "authorizes_code_change",
            "authorizes_exception",
            "authorizes_git_operations",
            "authorizes_publication",
            "authorizes_release",
            "authorizes_deployment",
            "authorizes_external_write",
            "starts_session",
        },
        errors,
    )

    if expected is not None and observed is not None:
        expected_identity = [(item.get("transition_id"), item.get("stage")) for item in expected]
        observed_identity = [(item.get("transition_id"), item.get("stage")) for item in observed]
        if expected_identity != observed_identity:
            errors.append(
                "$.observed_transitions must use the same ordered transition identities and stages as $.expected_transitions"
            )
        else:
            derived = derive_first_deviation(document)
            if declared is not None and dict(declared) != derived:
                errors.append("$.first_deviation must equal the deterministic earliest transition mismatch")

    if result is not None and host is not None:
        capabilities = host.get("capabilities")
        block_mode = capabilities.get("block_mode") if isinstance(capabilities, Mapping) else None
        pre_action_hook = capabilities.get("pre_action_hook") if isinstance(capabilities, Mapping) else None
        block_action = capabilities.get("block_action") if isinstance(capabilities, Mapping) else None
        mediate_action = capabilities.get("mediate_action") if isinstance(capabilities, Mapping) else None
        if result.get("effect") == "BLOCK" and (
            block_mode != "supported"
            or pre_action_hook is not True
            or block_action is not True
        ):
            errors.append(
                "$.harness_result.effect cannot be BLOCK unless host block_mode is supported and pre_action_hook/block_action are true"
            )
        if result.get("effect") == "MEDIATE" and mediate_action is not True:
            errors.append(
                "$.harness_result.effect cannot be MEDIATE unless host mediate_action is true"
            )

    if host is not None:
        capabilities = host.get("capabilities")
        if isinstance(capabilities, Mapping):
            block_mode = capabilities.get("block_mode")
            pre_action_hook = capabilities.get("pre_action_hook")
            block_action = capabilities.get("block_action")
            mediation_mode = capabilities.get("mediation_mode")
            mediate_action = capabilities.get("mediate_action")
            human_decision_ui = capabilities.get("human_decision_ui")
            if block_mode == "supported" and (
                pre_action_hook is not True or block_action is not True
            ):
                errors.append(
                    "$.host.capabilities supported block_mode requires pre_action_hook and block_action"
                )
            if block_mode in {"unsupported", "unknown"} and block_action is True:
                errors.append(
                    "$.host.capabilities block_action cannot be true when block_mode is unsupported or unknown"
                )
            if mediation_mode == "none" and (
                mediate_action is True or human_decision_ui is True
            ):
                errors.append(
                    "$.host.capabilities mediation_mode none cannot claim mediation or human decision UI"
                )
        if result.get("effect") == "BLOCK" and result.get("prevented_transition") is None:
            errors.append("$.harness_result.prevented_transition is required for BLOCK")
        if result.get("effect") != "BLOCK" and result.get("prevented_transition") is not None:
            errors.append("$.harness_result.prevented_transition is allowed only for BLOCK")
        if result.get("already_completed_effect") is True:
            if result.get("effect") == "BLOCK":
                errors.append("$.harness_result cannot claim BLOCK after an effect completed")
            if result.get("prevented_transition") is not None:
                errors.append("$.harness_result cannot claim a prevented transition after an effect completed")

    if terminal is not None and observed is not None:
        observed_side_effect = any(item.get("side_effect_completed") is True for item in observed)
        if terminal.get("external_side_effect_completed") != observed_side_effect:
            errors.append(
                "$.terminal.external_side_effect_completed must match the observed transition facts"
            )
        repository_write = any(item.get("outcome") == "repository_write_completed" for item in observed)
        if terminal.get("repository_modified") != repository_write:
            errors.append("$.terminal.repository_modified must match repository_write_completed evidence")

    return errors


def evaluate_harness_run(document: Mapping[str, Any]) -> HarnessEvaluation:
    """Validate one run and expose its bounded deterministic result."""

    errors = tuple(validate_harness_run_document(document))
    deviation: Mapping[str, Any] | None = None
    if not errors:
        deviation = derive_first_deviation(document)
    channels = document.get("channels")
    channel_statuses: dict[str, str] = {}
    if isinstance(channels, Mapping):
        for name in CHANNEL_NAMES:
            value = channels.get(name)
            if isinstance(value, Mapping) and isinstance(value.get("status"), str):
                channel_statuses[name] = value["status"]
    run_id = document.get("run_id") if isinstance(document.get("run_id"), str) else None
    return HarnessEvaluation(
        run_id=run_id,
        errors=errors,
        first_deviation=deviation,
        channel_statuses=channel_statuses,
    )


def load_harness_run(path: Path) -> Mapping[str, Any]:
    """Load one UTF-8 Harness Contract v1 document with an object root."""

    document = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(document, Mapping):
        raise ValueError("Harness run root must be an object")
    return document
