"""Pure attribution and reconciliation for normalized process snapshots.

This internal module does not inspect or control operating-system processes.
Callers provide already-normalized, in-memory facts and retain any transient
process identifiers themselves.  Results contain only bounded process classes,
counts, statuses, and stable reason codes.
"""

from __future__ import annotations

import re
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any


GATE_STATUSES = frozenset({"ready", "blocked", "indeterminate"})
ATTRIBUTION_STATUSES = frozenset({"ambient", "task_owned", "indeterminate"})
TASK_LINEAGES = frozenset(
    {"not_task_tree", "task_root_or_descendant", "unknown"}
)

_PROCESS_CLASS_RE = re.compile(r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$")
_OBSERVATION_FIELDS = frozenset(
    {
        "process_class",
        "present_at_preflight",
        "present_at_postflight",
        "task_lineage",
        "identity_complete",
    }
)
_MAX_OBSERVATIONS = 10_000
_MAX_PROCESS_COUNT = 10_000


@dataclass(frozen=True, order=True)
class ProcessAttributionFinding:
    """One privacy-bounded finding about a normalized process class."""

    code: str
    process_class: str | None = None


@dataclass(frozen=True)
class ProcessAttribution:
    """Ownership classification for one normalized process observation."""

    status: str
    process_class: str | None
    findings: tuple[ProcessAttributionFinding, ...]

    def __post_init__(self) -> None:
        if self.status not in ATTRIBUTION_STATUSES:
            raise ValueError("unsupported process attribution status")

    @property
    def reason_codes(self) -> tuple[str, ...]:
        return tuple(finding.code for finding in self.findings)


@dataclass(frozen=True)
class ProcessAttributionGateResult:
    """Fail-closed result for one normalized before/after process boundary."""

    status: str
    findings: tuple[ProcessAttributionFinding, ...]
    preflight_counts: tuple[tuple[str, int], ...]
    postflight_counts: tuple[tuple[str, int], ...]
    ambient_counts: tuple[tuple[str, int], ...]
    task_owned_counts: tuple[tuple[str, int], ...]
    remaining_task_owned_counts: tuple[tuple[str, int], ...]
    new_remaining_counts: tuple[tuple[str, int], ...]

    def __post_init__(self) -> None:
        if self.status not in GATE_STATUSES:
            raise ValueError("unsupported process attribution gate status")

    @property
    def reason_codes(self) -> tuple[str, ...]:
        return tuple(finding.code for finding in self.findings)


@dataclass(frozen=True)
class _NormalizedObservation:
    process_class: str
    present_at_preflight: bool
    present_at_postflight: bool
    task_lineage: str
    identity_complete: bool


def _finding(
    code: str, process_class: str | None = None
) -> ProcessAttributionFinding:
    return ProcessAttributionFinding(code=code, process_class=process_class)


def _ordered_findings(
    findings: Sequence[ProcessAttributionFinding],
) -> tuple[ProcessAttributionFinding, ...]:
    return tuple(
        sorted(set(findings), key=lambda item: (item.code, item.process_class or ""))
    )


def _safe_process_class(value: Any) -> str | None:
    if (
        isinstance(value, str)
        and len(value) <= 120
        and _PROCESS_CLASS_RE.fullmatch(value)
    ):
        return value
    return None


def _normalized_counts(counter: Mapping[str, int]) -> tuple[tuple[str, int], ...]:
    return tuple(sorted((key, value) for key, value in counter.items() if value))


def _normalize_snapshot(
    value: Any,
    *,
    phase: str,
) -> tuple[dict[str, int] | None, tuple[ProcessAttributionFinding, ...]]:
    if not isinstance(value, Mapping):
        return None, (_finding(f"{phase}_snapshot_not_mapping"),)

    counts: dict[str, int] = {}
    findings: list[ProcessAttributionFinding] = []
    total = 0
    for raw_class, raw_count in value.items():
        process_class = _safe_process_class(raw_class)
        if process_class is None:
            findings.append(_finding(f"{phase}_process_class_invalid"))
            continue
        if (
            not isinstance(raw_count, int)
            or isinstance(raw_count, bool)
            or raw_count < 0
            or raw_count > _MAX_PROCESS_COUNT
        ):
            findings.append(
                _finding(f"{phase}_process_count_invalid", process_class)
            )
            continue
        counts[process_class] = raw_count
        total += raw_count

    if total > _MAX_OBSERVATIONS:
        findings.append(_finding(f"{phase}_snapshot_limit_exceeded"))
    if findings:
        return None, _ordered_findings(findings)
    return counts, ()


def _normalize_observation(
    value: Any,
) -> tuple[_NormalizedObservation | None, tuple[ProcessAttributionFinding, ...]]:
    if not isinstance(value, Mapping):
        return None, (_finding("observation_not_mapping"),)

    process_class = _safe_process_class(value.get("process_class"))
    if set(value) != _OBSERVATION_FIELDS:
        return None, (_finding("observation_fields_invalid", process_class),)

    findings: list[ProcessAttributionFinding] = []
    if process_class is None:
        findings.append(_finding("process_class_invalid"))

    for field in ("present_at_preflight", "present_at_postflight"):
        if not isinstance(value[field], bool):
            findings.append(_finding(f"{field}_invalid", process_class))

    task_lineage = value["task_lineage"]
    if not isinstance(task_lineage, str) or task_lineage not in TASK_LINEAGES:
        findings.append(_finding("task_lineage_invalid", process_class))

    if not isinstance(value["identity_complete"], bool):
        findings.append(_finding("identity_complete_invalid", process_class))

    if findings:
        return None, _ordered_findings(findings)

    assert process_class is not None
    return (
        _NormalizedObservation(
            process_class=process_class,
            present_at_preflight=value["present_at_preflight"],
            present_at_postflight=value["present_at_postflight"],
            task_lineage=task_lineage,
            identity_complete=value["identity_complete"],
        ),
        (),
    )


def _classify_normalized(observation: _NormalizedObservation) -> ProcessAttribution:
    process_class = observation.process_class
    findings: list[ProcessAttributionFinding] = []
    if not observation.identity_complete:
        findings.append(_finding("identity_incomplete", process_class))
    if observation.task_lineage == "unknown":
        findings.append(_finding("task_lineage_unknown", process_class))
    if (
        observation.present_at_preflight
        and observation.task_lineage == "task_root_or_descendant"
    ):
        findings.append(
            _finding("preflight_task_lineage_conflict", process_class)
        )
    if (
        not observation.present_at_preflight
        and observation.task_lineage == "not_task_tree"
    ):
        findings.append(_finding("new_process_unattributed", process_class))

    if findings:
        return ProcessAttribution(
            status="indeterminate",
            process_class=process_class,
            findings=_ordered_findings(findings),
        )
    if observation.present_at_preflight:
        return ProcessAttribution("ambient", process_class, ())
    return ProcessAttribution("task_owned", process_class, ())


def classify_process_observation(value: Any) -> ProcessAttribution:
    """Classify one normalized observation without retaining raw input fields."""

    normalized, findings = _normalize_observation(value)
    if normalized is None:
        return ProcessAttribution(
            status="indeterminate",
            process_class=None,
            findings=findings,
        )
    return _classify_normalized(normalized)


def assess_process_attribution_gate(
    preflight_snapshot: Any,
    postflight_snapshot: Any,
    observations: Any,
) -> ProcessAttributionGateResult:
    """Reconcile normalized observations with snapshots and fail closed.

    A nonzero ambient baseline is allowed.  ``ready`` requires complete
    per-instance attribution, exact reconciliation with both snapshots, and no
    task-owned process remaining after the attempt.
    """

    preflight, preflight_findings = _normalize_snapshot(
        preflight_snapshot, phase="preflight"
    )
    postflight, postflight_findings = _normalize_snapshot(
        postflight_snapshot, phase="postflight"
    )
    findings = [*preflight_findings, *postflight_findings]

    if not isinstance(observations, Sequence) or isinstance(
        observations, (str, bytes, bytearray)
    ):
        findings.append(_finding("observations_not_sequence"))
        observations = ()
    elif len(observations) > _MAX_OBSERVATIONS:
        findings.append(_finding("observation_limit_exceeded"))
        observations = ()

    normalized_observations: list[_NormalizedObservation] = []
    for value in observations:
        normalized, observation_findings = _normalize_observation(value)
        findings.extend(observation_findings)
        if normalized is not None:
            normalized_observations.append(normalized)

    attributions = [
        _classify_normalized(observation)
        for observation in normalized_observations
    ]
    for attribution in attributions:
        findings.extend(attribution.findings)

    preflight_counts: Counter[str] = Counter()
    postflight_counts: Counter[str] = Counter()
    ambient_counts: Counter[str] = Counter()
    task_owned_counts: Counter[str] = Counter()
    remaining_task_owned_counts: Counter[str] = Counter()

    for observation, attribution in zip(normalized_observations, attributions):
        if observation.present_at_preflight:
            preflight_counts[observation.process_class] += 1
        if observation.present_at_postflight:
            postflight_counts[observation.process_class] += 1
        if attribution.status == "ambient":
            ambient_counts[observation.process_class] += 1
        elif attribution.status == "task_owned":
            task_owned_counts[observation.process_class] += 1
            if observation.present_at_postflight:
                remaining_task_owned_counts[observation.process_class] += 1

    if preflight is not None and dict(preflight_counts) != {
        key: count for key, count in preflight.items() if count
    }:
        findings.append(_finding("preflight_snapshot_unreconciled"))
    if postflight is not None and dict(postflight_counts) != {
        key: count for key, count in postflight.items() if count
    }:
        findings.append(_finding("postflight_snapshot_unreconciled"))

    new_remaining_counts: Counter[str] = Counter()
    if preflight is not None and postflight is not None:
        for process_class in set(preflight) | set(postflight):
            increase = postflight.get(process_class, 0) - preflight.get(
                process_class, 0
            )
            if increase > 0:
                new_remaining_counts[process_class] = increase

    if findings:
        status = "indeterminate"
    elif remaining_task_owned_counts:
        status = "blocked"
        findings.extend(
            _finding("task_owned_process_remaining", process_class)
            for process_class in remaining_task_owned_counts
        )
    else:
        status = "ready"

    return ProcessAttributionGateResult(
        status=status,
        findings=_ordered_findings(findings),
        preflight_counts=_normalized_counts(preflight or {}),
        postflight_counts=_normalized_counts(postflight or {}),
        ambient_counts=_normalized_counts(ambient_counts),
        task_owned_counts=_normalized_counts(task_owned_counts),
        remaining_task_owned_counts=_normalized_counts(
            remaining_task_owned_counts
        ),
        new_remaining_counts=_normalized_counts(new_remaining_counts),
    )
