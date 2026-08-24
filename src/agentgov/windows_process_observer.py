"""Privacy-bounded Windows process observation for controlled diagnostics.

The host boundary transiently reads process metadata, immediately reduces it
to normalized process classes and ancestry facts, and never exposes raw names,
command lines, executable paths, or process identifiers in public results.
It observes processes only; it never controls or terminates them.
"""

from __future__ import annotations

import json
import os
import subprocess
from collections import Counter
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from agentgov.process_attribution_gate import (
    ProcessAttributionGateResult,
    assess_process_attribution_gate,
)


OBSERVER_STATUSES = frozenset({"ready", "indeterminate"})
BOUNDARY_STATUSES = frozenset({"ready", "blocked", "indeterminate"})

_PROCESS_FIELDS = frozenset(
    {
        "ProcessId",
        "ParentProcessId",
        "Name",
        "CommandLine",
        "CreationDate",
    }
)
_MAX_QUERY_BYTES = 8 * 1024 * 1024
_MAX_PROCESS_RECORDS = 10_000
_QUERY_TIMEOUT_SECONDS = 20
_ROOT_PROCESS_IDS = frozenset({0, 4})

_POWERSHELL_QUERY = (
    "$ErrorActionPreference='Stop'; "
    "@(Get-CimInstance Win32_Process | "
    "Select-Object ProcessId,ParentProcessId,Name,CommandLine,CreationDate) "
    "| ConvertTo-Json -Compress -Depth 3"
)


@dataclass(frozen=True, order=True)
class ProcessObserverFinding:
    """One stable observer finding containing no host-local value."""

    code: str
    process_class: str | None = None


@dataclass(frozen=True)
class _RelevantInstance:
    identity: tuple[int, str]
    process_id: int
    parent_process_id: int
    process_class: str


@dataclass(frozen=True)
class WindowsProcessSnapshot:
    """Normalized snapshot with private transient identity and ancestry data."""

    status: str
    counts: tuple[tuple[str, int], ...]
    findings: tuple[ProcessObserverFinding, ...]
    _instances: tuple[_RelevantInstance, ...] = field(
        default=(), repr=False, compare=False
    )
    _parents: tuple[tuple[int, int], ...] = field(
        default=(), repr=False, compare=False
    )

    def __post_init__(self) -> None:
        if self.status not in OBSERVER_STATUSES:
            raise ValueError("unsupported observer status")

    @property
    def reason_codes(self) -> tuple[str, ...]:
        return tuple(finding.code for finding in self.findings)


@dataclass(frozen=True)
class ObservedProcessBoundary:
    """Privacy-safe assessment over one before/after observation boundary."""

    status: str
    findings: tuple[ProcessObserverFinding, ...]
    preflight_counts: tuple[tuple[str, int], ...]
    postflight_counts: tuple[tuple[str, int], ...]
    ambient_counts: tuple[tuple[str, int], ...]
    task_owned_counts: tuple[tuple[str, int], ...]
    remaining_task_owned_counts: tuple[tuple[str, int], ...]
    _gate_result: ProcessAttributionGateResult | None = field(
        default=None, repr=False, compare=False
    )

    def __post_init__(self) -> None:
        if self.status not in BOUNDARY_STATUSES:
            raise ValueError("unsupported observed boundary status")

    @property
    def reason_codes(self) -> tuple[str, ...]:
        return tuple(finding.code for finding in self.findings)


ProcessQuery = Callable[[], Any]


def _finding(
    code: str, process_class: str | None = None
) -> ProcessObserverFinding:
    return ProcessObserverFinding(code=code, process_class=process_class)


def _ordered_findings(
    findings: Sequence[ProcessObserverFinding],
) -> tuple[ProcessObserverFinding, ...]:
    return tuple(
        sorted(set(findings), key=lambda item: (item.code, item.process_class or ""))
    )


def _normalized_counts(
    instances: Sequence[_RelevantInstance],
) -> tuple[tuple[str, int], ...]:
    return tuple(sorted(Counter(item.process_class for item in instances).items()))


def _text(value: Any) -> str | None:
    return value if isinstance(value, str) else None


def _process_class(name: str, command_line: str | None) -> tuple[str | None, bool]:
    """Return a normalized class and whether classification was complete."""

    normalized_name = name.strip().lower()
    stem = normalized_name.rsplit(".", 1)[0]
    command = command_line.lower() if command_line is not None else None

    if stem == "codex":
        return "codex_host", True
    if stem.startswith("agentgov"):
        return "agentgov_service", True

    if stem in {"node", "nodejs"}:
        if command is None:
            return None, False
        if "@openai/codex" in command or "codex.js" in command:
            return "codex_host", True
        return None, True

    if stem in {"python", "pythonw", "py"}:
        if command is None:
            return None, False
        if "agentgov.installed_schema_validation" in command:
            return None, True
        service_markers = (
            "agentgov.governance_mcp",
            "agentgov governance-mcp",
            "agentgov-mcp",
            "governance_mcp.py",
        )
        if any(marker in command for marker in service_markers):
            return "python_service", True
        return None, True

    return None, True


def _normalize_records(value: Any) -> WindowsProcessSnapshot:
    if isinstance(value, Mapping):
        records: Sequence[Any] = (value,)
    elif isinstance(value, Sequence) and not isinstance(
        value, (str, bytes, bytearray)
    ):
        records = value
    else:
        return WindowsProcessSnapshot(
            "indeterminate", (), (_finding("query_result_not_records"),)
        )

    if len(records) > _MAX_PROCESS_RECORDS:
        return WindowsProcessSnapshot(
            "indeterminate", (), (_finding("process_record_limit_exceeded"),)
        )

    findings: list[ProcessObserverFinding] = []
    instances: list[_RelevantInstance] = []
    parents: dict[int, int] = {}
    seen_identities: set[tuple[int, str]] = set()

    for raw in records:
        if not isinstance(raw, Mapping) or not _PROCESS_FIELDS <= set(raw):
            findings.append(_finding("process_record_invalid"))
            continue
        process_id = raw.get("ProcessId")
        parent_process_id = raw.get("ParentProcessId")
        name = _text(raw.get("Name"))
        command_line = _text(raw.get("CommandLine"))
        creation_date = _text(raw.get("CreationDate"))
        if (
            not isinstance(process_id, int)
            or isinstance(process_id, bool)
            or process_id < 0
            or not isinstance(parent_process_id, int)
            or isinstance(parent_process_id, bool)
            or parent_process_id < 0
            or not name
        ):
            findings.append(_finding("process_record_invalid"))
            continue

        parents[process_id] = parent_process_id
        process_class, classification_complete = _process_class(name, command_line)
        if not classification_complete:
            findings.append(_finding("relevant_classification_incomplete"))
            continue
        if process_class is None:
            continue
        if process_id == 0 or not creation_date:
            findings.append(_finding("relevant_identity_incomplete", process_class))
            continue
        identity = (process_id, creation_date)
        if identity in seen_identities:
            findings.append(_finding("relevant_identity_duplicate", process_class))
            continue
        seen_identities.add(identity)
        instances.append(
            _RelevantInstance(
                identity=identity,
                process_id=process_id,
                parent_process_id=parent_process_id,
                process_class=process_class,
            )
        )

    status = "indeterminate" if findings else "ready"
    ordered_instances = tuple(
        sorted(instances, key=lambda item: (item.process_class, item.identity))
    )
    return WindowsProcessSnapshot(
        status=status,
        counts=_normalized_counts(ordered_instances),
        findings=_ordered_findings(findings),
        _instances=ordered_instances,
        _parents=tuple(sorted(parents.items())),
    )


def _default_query() -> Any:
    if os.name != "nt":
        raise OSError("unsupported platform")
    completed = subprocess.run(
        (
            "powershell.exe",
            "-NoLogo",
            "-NoProfile",
            "-NonInteractive",
            "-Command",
            _POWERSHELL_QUERY,
        ),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
        timeout=_QUERY_TIMEOUT_SECONDS,
    )
    if completed.returncode != 0 or len(completed.stdout) > _MAX_QUERY_BYTES:
        raise OSError("bounded process query failed")
    try:
        return json.loads(completed.stdout.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise OSError("bounded process query returned invalid data") from exc


def observe_windows_processes(
    query: ProcessQuery | None = None,
) -> WindowsProcessSnapshot:
    """Capture one read-only snapshot and return only normalized public facts."""

    try:
        raw = (query or _default_query)()
    except (OSError, subprocess.SubprocessError, ValueError, TypeError):
        return WindowsProcessSnapshot(
            "indeterminate", (), (_finding("process_query_failed"),)
        )
    return _normalize_records(raw)


def _counts_mapping(value: tuple[tuple[str, int], ...]) -> dict[str, int]:
    return dict(value)


def assess_ambient_process_baseline(
    snapshot: WindowsProcessSnapshot,
) -> ObservedProcessBoundary:
    """Require a complete snapshot while allowing a nonzero ambient baseline."""

    if snapshot.status != "ready":
        return ObservedProcessBoundary(
            "indeterminate",
            snapshot.findings,
            snapshot.counts,
            snapshot.counts,
            (),
            (),
            (),
        )
    observations = [
        {
            "process_class": item.process_class,
            "present_at_preflight": True,
            "present_at_postflight": True,
            "task_lineage": "not_task_tree",
            "identity_complete": True,
        }
        for item in snapshot._instances
    ]
    counts = _counts_mapping(snapshot.counts)
    gate = assess_process_attribution_gate(counts, counts, observations)
    findings = tuple(_finding(code) for code in gate.reason_codes)
    return ObservedProcessBoundary(
        gate.status,
        findings,
        gate.preflight_counts,
        gate.postflight_counts,
        gate.ambient_counts,
        gate.task_owned_counts,
        gate.remaining_task_owned_counts,
        gate,
    )


def _task_lineage(
    instance: _RelevantInstance,
    *,
    task_root_process_id: int,
    parents: Mapping[int, int],
) -> str:
    current = instance.process_id
    visited: set[int] = set()
    for _ in range(_MAX_PROCESS_RECORDS):
        if current == task_root_process_id:
            return "task_root_or_descendant"
        if current in visited:
            return "unknown"
        visited.add(current)
        parent = parents.get(current)
        if parent is None:
            return "unknown"
        if parent == task_root_process_id:
            return "task_root_or_descendant"
        if parent in _ROOT_PROCESS_IDS:
            return "not_task_tree"
        current = parent
    return "unknown"


def reconcile_windows_processes(
    preflight: WindowsProcessSnapshot,
    postflight: WindowsProcessSnapshot,
    *,
    task_root_process_id: int,
) -> ObservedProcessBoundary:
    """Reduce transient instance identity into the existing deterministic gate."""

    observer_findings = [*preflight.findings, *postflight.findings]
    if (
        preflight.status != "ready"
        or postflight.status != "ready"
        or not isinstance(task_root_process_id, int)
        or isinstance(task_root_process_id, bool)
        or task_root_process_id <= 0
    ):
        if not isinstance(task_root_process_id, int) or isinstance(
            task_root_process_id, bool
        ) or task_root_process_id <= 0:
            observer_findings.append(_finding("task_root_identity_invalid"))
        return ObservedProcessBoundary(
            "indeterminate",
            _ordered_findings(observer_findings),
            preflight.counts,
            postflight.counts,
            (),
            (),
            (),
        )

    pre_by_identity = {item.identity: item for item in preflight._instances}
    post_by_identity = {item.identity: item for item in postflight._instances}
    parents = dict(postflight._parents)
    observations: list[dict[str, Any]] = []

    for identity, item in pre_by_identity.items():
        observations.append(
            {
                "process_class": item.process_class,
                "present_at_preflight": True,
                "present_at_postflight": identity in post_by_identity,
                "task_lineage": "not_task_tree",
                "identity_complete": True,
            }
        )
    for identity, item in post_by_identity.items():
        if identity in pre_by_identity:
            continue
        observations.append(
            {
                "process_class": item.process_class,
                "present_at_preflight": False,
                "present_at_postflight": True,
                "task_lineage": _task_lineage(
                    item,
                    task_root_process_id=task_root_process_id,
                    parents=parents,
                ),
                "identity_complete": True,
            }
        )

    gate = assess_process_attribution_gate(
        _counts_mapping(preflight.counts),
        _counts_mapping(postflight.counts),
        observations,
    )
    findings = _ordered_findings(
        [*observer_findings, *(_finding(code) for code in gate.reason_codes)]
    )
    return ObservedProcessBoundary(
        gate.status,
        findings,
        gate.preflight_counts,
        gate.postflight_counts,
        gate.ambient_counts,
        gate.task_owned_counts,
        gate.remaining_task_owned_counts,
        gate,
    )
