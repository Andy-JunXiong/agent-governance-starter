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
from agentgov.event_store import (
    GovernanceEvent,
    governance_event_from_payload,
    load_governance_events,
    utc_now,
)


MONITOR_CONTRACT = "agentgov.development-monitor"
MONITOR_SCHEMA_VERSION = "1.3"
MONITOR_SCOPES = {"local_session", "exported_development", "ci_only", "combined"}


class MonitorPolicyError(RuntimeError):
    """A Monitor claim cannot be supported by the available event source."""


@dataclass(frozen=True)
class DevelopmentMonitor:
    contract: str
    schema_version: str
    generated_at: str
    observation: Mapping[str, Any]
    overview: Mapping[str, int]
    timeline: tuple[Mapping[str, Any], ...]
    tasks: tuple[Mapping[str, Any], ...]
    claim_layers: Mapping[str, tuple[str, ...]]
    authority_boundary: Mapping[str, bool]


@dataclass(frozen=True)
class _ObservedEvent:
    event: GovernanceEvent
    source_scope: str


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
    claim_layers = {
        "observed": (
            "Event timestamps, actor classes, task identities, trigger reason codes, outcomes, and small counters come from validated event records.",
            "Selected governance paths come from confirmed task-start routing; they show selection, not coding-agent consumption.",
            "Each timeline source label comes from the explicitly selected local, export, or CI input boundary rather than a semantic inference.",
            "Latest recorded outcome means the chronologically latest event visible in this observation scope.",
            "Verified completion and handed-off routing are counted separately; handoff records routing responsibility, not semantic approval.",
        ),
        "inferred": (
            "Chronological grouping suggests a task activity sequence but does not prove that one event caused another.",
        ),
        "unknown": (
            "Events do not prove requirement satisfaction, architecture correctness, validation sufficiency, causal benefit, or return on investment.",
            "Which routed governance artifacts or Skills the coding agent actually consumed is unknown until context-consumption events exist.",
            "Human handling and resolution are unknown unless a future explicit human-decision event records them.",
            "History outside the displayed observation scope is unknown.",
        ),
    }
    return DevelopmentMonitor(
        contract=MONITOR_CONTRACT,
        schema_version=MONITOR_SCHEMA_VERSION,
        generated_at=generated_at or utc_now(),
        observation=observation,
        overview=overview,
        timeline=timeline,
        tasks=tasks,
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
        lines.extend(
            [
                f"### {task['task_id']}",
                "",
                f"- Events: `{task['event_count']}`",
                f"- Latest recorded outcome: `{task['latest_recorded_outcome']}`",
                f"- Latest completion state: `{_display(task['latest_completion_state'])}`",
                f"- Latest routing state: `{task['latest_routing_state']}`",
                "",
            ]
        )
    if not monitor.tasks:
        lines.append("No task events are visible.\n")
    lines.extend(["## Claim limits", ""])
    for layer in ("observed", "inferred", "unknown"):
        lines.append(f"### {layer.title()}\n")
        lines.extend(f"- {item}" for item in monitor.claim_layers[layer])
        lines.append("")
    return "\n".join(lines)


def render_development_monitor_html(monitor: DevelopmentMonitor) -> str:
    esc = lambda value: html.escape(_display(value), quote=True)
    observation = monitor.observation
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
        task_cards = "".join(
            '<details class="task">'
            f'<summary><span>{esc(task["task_id"])}</span><b>{esc(task["latest_recorded_outcome"])}</b></summary>'
            '<div class="task-grid">'
            f'<div><small>First observed</small><strong>{esc(task["first_observed_at"])}</strong></div>'
            f'<div><small>Last observed</small><strong>{esc(task["last_observed_at"])}</strong></div>'
            f'<div><small>Starts / checks / validations / completions / handoffs</small><strong>{task["task_starts"]} / {task["scope_checks"]} / {task["validations"]} / {task["completions"]} / {task["handoffs"]}</strong></div>'
            f'<div><small>Completion / routing</small><strong>{esc(task["latest_completion_state"])} / {esc(task["latest_routing_state"])}</strong></div>'
            "</div>"
            '<p class="task-note">Handling remains unknown unless an explicit human-decision event records it. A later outcome is not presented as proof that an earlier issue was caused or resolved by AgentGov.</p>'
            "</details>"
            for task in monitor.tasks
        )
    else:
        task_cards = '<div class="empty">No task details are available.</div>'
    machine = html.escape(render_development_monitor_json(monitor), quote=False)
    return f'''<!doctype html>
<!-- {MONITOR_CONTRACT} -->
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; img-src data:">
<title>AgentGov Development Monitor</title><style>
:root{{--ink:#12222b;--muted:#617078;--paper:#fffdf7;--wash:#f1eee4;--line:#ddd8ca;--teal:#0d6f69;--amber:#a85e12;--red:#a33d3d;--blue:#315c8a}}*{{box-sizing:border-box}}body{{margin:0;background:var(--wash);color:var(--ink);font:15px/1.55 ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif}}.shell{{width:min(1120px,calc(100% - 32px));margin:auto}}header{{background:var(--ink);color:white;padding:18px 0}}header .shell{{display:flex;justify-content:space-between;align-items:center;gap:18px}}.brand{{font-weight:850;letter-spacing:.02em}}.scope{{border:1px solid #ffffff55;border-radius:999px;padding:6px 11px;font-size:12px}}main{{padding:42px 0 56px}}.hero{{display:grid;grid-template-columns:1.45fr .75fr;gap:24px;align-items:end;margin-bottom:30px}}.eyebrow{{color:var(--teal);font-size:12px;font-weight:850;letter-spacing:.14em;text-transform:uppercase}}h1{{font-size:clamp(38px,6vw,68px);line-height:.98;letter-spacing:-.045em;margin:10px 0 16px;max-width:780px}}h2{{font-size:27px;letter-spacing:-.02em;margin:0 0 6px}}h3{{margin:0}}.lede,.sub,.event p,.task-note{{color:var(--muted)}}.boundary{{background:#e5f3ed;border-left:4px solid var(--teal);padding:18px;border-radius:12px}}.boundary strong{{display:block;font-size:21px}}.metrics{{display:grid;grid-template-columns:repeat(6,1fr);gap:10px;margin:26px 0}}.metric,.panel,.claim,.task{{background:var(--paper);border:1px solid var(--line);border-radius:16px}}.metric{{padding:17px}}.metric span{{display:block;color:var(--muted);font-size:11px;text-transform:uppercase;letter-spacing:.07em}}.metric strong{{display:block;font-size:28px;margin-top:8px}}.panel{{padding:25px;margin-top:18px}}.limits{{display:grid;grid-template-columns:.8fr 1.2fr;gap:22px}}.missing{{background:#fff3dd;border-radius:12px;padding:16px}}.missing h3{{color:var(--amber)}}.claims{{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-top:16px}}.claim{{padding:18px}}.claim h3{{text-transform:uppercase;font-size:12px;letter-spacing:.1em}}.claim.observed h3{{color:var(--teal)}}.claim.inferred h3{{color:var(--blue)}}.claim.unknown h3{{color:var(--amber)}}.claim ul,.missing ul{{padding-left:20px;margin-bottom:0}}.timeline{{list-style:none;margin:24px 0 0;padding:0}}.event{{display:grid;grid-template-columns:190px 1fr;gap:24px;padding:0 0 25px 24px;border-left:2px solid var(--line);position:relative}}.event:before{{content:"";position:absolute;width:12px;height:12px;border-radius:50%;background:var(--teal);left:-7px;top:5px}}time{{color:var(--muted);font-size:12px}}.event-head{{display:flex;gap:8px;align-items:center;margin-bottom:6px}}.kind,.outcome{{font-size:11px;font-weight:800;padding:4px 8px;border-radius:999px;background:#e8ecea}}.outcome.verified,.outcome.passed{{background:#dcefe6;color:var(--teal)}}.outcome.failed,.outcome.stale,.outcome.needs_evidence{{background:#f8dfd8;color:var(--red)}}.event p{{margin:4px 0}}.task{{margin-top:11px;overflow:hidden}}summary{{cursor:pointer;display:flex;justify-content:space-between;padding:17px 19px;font-weight:800}}summary b{{color:var(--teal)}}.task-grid{{border-top:1px solid var(--line);display:grid;grid-template-columns:repeat(4,1fr);gap:12px;padding:18px}}.task-grid small{{display:block;color:var(--muted)}}.task-grid strong{{font-size:13px}}.task-note{{padding:0 18px 18px;margin:0}}.empty{{color:var(--muted);padding:20px;border:1px dashed var(--line);border-radius:12px}}details.machine{{margin-top:18px}}pre{{white-space:pre-wrap;word-break:break-word;background:#17272f;color:#e8f3f0;padding:18px;border-radius:12px;font-size:12px}}footer{{padding:25px 0;color:var(--muted)}}@media(max-width:880px){{.metrics{{grid-template-columns:repeat(3,1fr)}}.hero,.limits{{grid-template-columns:1fr}}.claims{{grid-template-columns:1fr}}.task-grid{{grid-template-columns:1fr 1fr}}}}@media(max-width:560px){{header .shell{{align-items:flex-start;flex-direction:column}}.metrics{{grid-template-columns:1fr 1fr}}.event{{grid-template-columns:1fr;gap:5px}}.task-grid{{grid-template-columns:1fr}}}}
</style></head><body><header><div class="shell"><div class="brand">AGENTGOV · DEVELOPMENT MONITOR</div><div class="scope">Observation scope · {esc(observation['scope'])}</div></div></header><main class="shell">
<section class="hero"><div><div class="eyebrow">Govern → Observe → Monitor</div><h1>See governance while development is happening.</h1><p class="lede">A local, static view of when AgentGov ran, why it ran, who invoked it, and what its event records observed—without turning evidence into approval.</p></div><aside class="boundary"><span>History completeness</span><strong>{esc(observation['history_completeness'])}</strong><small>{observation['event_count']} validated events · {observation['duplicates_removed']} duplicate records removed</small></aside></section>
<section aria-labelledby="overview"><h2 id="overview">Overview</h2><p class="sub">Observed counts within this dashboard's declared scope. They are not a governance score.</p><div class="metrics">{cards}</div></section>
<section class="panel limits"><div><h2>Observation boundary</h2><p><b>{esc(observation['scope'])}</b> from {esc(observation['started_at'])} to {esc(observation['ended_at'])}.</p><p class="sub">Source events: {esc(", ".join(f"{key}={value}" for key, value in observation['source_event_counts'].items()))}.</p><p class="sub">Cross-stage discovery comparison is unavailable because the event contract has no cross-stage finding identity or resolution link.</p></div><div class="missing"><h3>Missing sources</h3><ul>{missing}</ul></div></section>
<section class="panel"><h2>Claim layers</h2><p class="sub">Facts, cautious interpretation, and unknowns stay visibly separate.</p><div class="claims">{layers}</div></section>
<section class="panel" aria-labelledby="timeline"><h2 id="timeline">Activity Timeline</h2><p class="sub">When governance triggered, why it triggered, who used it, and what was recorded.</p><ol class="timeline">{timeline}</ol></section>
<section class="panel" aria-labelledby="tasks"><h2 id="tasks">Task Detail</h2><p class="sub">Latest recorded outcomes and visible task activity. Requirement and architecture correctness remain human judgments.</p>{task_cards}</section>
<details class="machine"><summary>Embedded machine-readable Monitor</summary><pre>{machine}</pre></details>
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
