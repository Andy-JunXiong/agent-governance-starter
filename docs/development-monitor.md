# Development governance Monitor

## Status

The Phase 4 static Monitor MVP is implemented in development source for the
future 0.3 line. It consumes the privacy-bounded events created by
`agentgov govern start/check/finish` and produces a self-contained local file with:

- Overview;
- Active Task;
- Live Sessions;
- Protection Events;
- Activity Timeline;
- Task Detail;
- Benefit;
- Learning.

Monitor contract 1.10 adds a local-session-only Active Task projection. It
binds one admitted task and digest to its canonical development state, admitted
context, existing activity-event identities, and event-referenced evidence.
Path-level scope facts appear only when the latest `scope.checked` event points
to a valid immutable event-referenced scope artifact stored locally for the
same task and digest;
otherwise affected paths remain explicitly unavailable. The projection offers
read-only human-boundary guidance and denies commit, merge, publish, release,
and deploy authority.

Monitor contract 1.9 added exact candidate-bound human Learning reviews to the
strict current-observation Learning projection introduced in 1.8 and to the
single-observation Benefit projection introduced in 1.7, the read-only guidance
introduced for Protection Events in 1.6, and the shared drift-review
reminder state introduced in 1.5. It keeps semantic drift, supported-benefit
inference, and every repeated-signal Learning candidate advisory. A recorded
human disposition remains a judgment, not handling, resolution, or benefit.

It is not part of stable 0.2.1. The explicit redacted-export slice lets it read
one reviewed development export or combine that export with a CI-only replay
store. The future 0.3 managed workflow template now includes a default-off,
manual-dispatch artifact path. It still does not include central telemetry,
GitHub Pages, automatic local-state transfer, approval controls, or
governance-file edits.

## Accepted product direction

ADR-0013 makes the Monitor and Dashboard a core automatically refreshed product
surface rather than a command the ordinary user must remember to run. The
current static Monitor is the validated read-model foundation. Development
source now derives Overview, local Active Task, Live Sessions, Protection
Events, Activity Timeline, Task Detail, Benefit, Learning, and the
non-authoritative drift-review reminder.
Protection Events now provide enum-bounded read-only links to Task Detail; an
explicit future handling or resolution contract is still required before
actual handling or resolution can be linked across events. The first single-
observation Benefit slice, current-observation Learning candidates, and exact
candidate-bound human Learning review records are implemented in development
source. Multi-observation trends and cross-window Benefit evidence remain
future work. `agentgov dev` refreshes this
Dashboard after each processed adapter event, and its strict `--stream` JSONL
mode can process several events in one foreground coding-agent connection. The
first packaged Codex lifecycle-hook Adapter is implemented in development
source; Claude Code and IDE adapters remain optional future portability work.

Vendor-neutral host-interaction requests are foreground response artifacts,
not Dashboard resolution evidence. A displayed option has
`decision_applied=false`; until a later explicit decision/resolution link is
recorded, Protection Events must continue to report resolution as unknown. A
Monitor guidance link is navigation to visible task context, not that
missing resolution record.

The target Dashboard explains how AgentGov protected both the user and the
coding agent: bounded scope and authority, relevant context, stale evidence,
repeated attempts, failures attributable to environment or unclear intent,
human decisions, and remaining unknowns. This target is not yet implemented in
stable 0.2.1 or as the primary `v0.3.0rc1` user experience.

Generate the default local dashboard:

```powershell
$env:PYTHONPATH = "src"
python -m agentgov monitor development .
```

The command refreshes `.agentgov/dashboard.html`. JSON and Markdown use the
same derived model:

```powershell
python -m agentgov monitor development . --format json
python -m agentgov monitor development . --format markdown
```

An explicit `--output` may select another repository-local generated file.
AgentGov refuses to overwrite a Git-tracked target, a symbolic link, or an
existing file without the matching AgentGov Monitor ownership marker. The
default untracked `.agentgov/` output does not enter the fresh-evidence digest.

Preview one fixed human judgment for a current repeated signal:

```powershell
$env:PYTHONPATH = "src"
python -m agentgov review learning . `
  --signal-class scope_boundary `
  --disposition false_positive
```

The preview is read-only. Adding `--apply` still writes nothing unless an
interactive human types exact `RECORD`. Immediately before exclusive creation,
AgentGov reloads current local events and rechecks the signal class, sorted
source identities, two-event rule, and candidate digest. The strict record
lives under `.agentgov/learning-reviews`; it contains no free text, personal
name, task identity, resolution, or downstream authority.

## Observation scope

Every Monitor prominently declares its scope, event interval, validated event
count, duplicate count, missing sources, and `partial` history completeness.

Supported sources are:

- `local_session`: validated events currently present in this working copy;
- `exported_development`: one explicitly created and validated metadata-only
  development export;
- `ci_only`: events from the current CI observation, all of which must declare
  actor class `ci`;
- `combined`: one explicit development export plus one CI-only replay event
  directory.

To render the CI-only form directly from development source:

```powershell
python -m agentgov monitor development . `
  --scope ci_only --output .agentgov/dashboard.html
```

The future 0.3 managed governance workflow exposes
`publish_development_monitor`, a boolean manual-dispatch input whose default is
`false`. When an owner explicitly enables it, the workflow uploads only
`agentgov-development-monitor.html`. An optional repository-relative
`development_export` input selects a validated metadata-only export. With no
export the scope is `ci_only`; with an export it is `exported_development`, or
`combined` only when actor-validated CI event files are also present.

The template never uploads the development export, raw events, or the
`.agentgov/` directory. AgentGov revalidates the export contract and rejects
human or coding-agent actors from the CI event input. The feature exists only
in the future 0.3 source template until a separate release and consumer
migration are approved.

Create and inspect a development export as documented in
[Redacted development-event export](development-event-export.md), then pass its
repository-local path with `--export`. A `combined` Monitor also accepts
`--events` for the CI replay directory. Every Timeline entry is labeled
`local_session`, `exported_development`, or `ci_only`, and observation metadata
reports a separate count for each source.

All four scopes set cross-stage discovery comparison to unavailable. Even a
combined view lacks a stable finding identity and resolution link, so it must
not infer where an issue was first found across pre-code, local development,
PR, and CI.

## What the views answer

Within the displayed observation scope:

- Active Task answers five first-review questions for one exact local session:
  what requirement is admitted, which path boundary applies, what AgentGov has
  directly observed, what the canonical state means, and which human boundary
  comes next. Its activity list references the same canonical event identities
  used by Timeline. Exported, CI-only, combined, missing-session, or invalid
  bindings show the detail as unavailable rather than inferring a current task.
- Timeline answers when governance ran, which command family triggered it,
  which actor class invoked it, which governance paths start selected, recorded
  reason codes, observed counts, and outcome. Selection does not prove agent
  consumption.
- Overview counts tasks, starts, checks, validations, completions, handoffs,
  fresh/stale results, Protection Events, sessions needing attention, and
  event-reported findings without computing a score or percentage.
- Live Sessions classifies the latest visible task event as `active`,
  `needs_attention`, `review_ready`, or `handed_off`.
- Protection Events deterministically classify recorded scope failures,
  validation failures, stale validation evidence, and completion that needs
  evidence. Each class carries one deterministic read-only action label and a
  schema-bounded `task_detail` target. HTML and Markdown render internal links
  to the matching deterministic task-card anchor; JSON contains no URL. Their
  identity is derived from the source event, and resolution remains explicitly unknown
  without a future cross-event link.
- Task Detail groups the visible sequence and shows the latest recorded event
  and completion outcome. A task with a Protection Event is prominent and open
  by default, with the latest protection class, observed outcome and reasons,
  recorded counters, a deterministic next human review action, and the explicit
  statement that resolution is unknown. Affected paths appear only when that
  protection event is the latest scope event referenced by the Active Task's
  validated path-level artifact; otherwise they are shown as unavailable
  instead of inferred. Tasks without Protection Events remain compact.
- Benefit uses one strict five-card projection over the current observation:
  `observed_fact` contains only validated direct counts;
  `reproduced_comparison` is explicitly unavailable without a selected
  baseline, denominator, applicability rules, and comparable window;
  `supported_inference` is advisory and only connects recorded protection
  context to review prioritization; `human_feedback` is unavailable because
  current events do not record attributed feedback; and `unknown` preserves
  counterfactual outcomes, semantic correctness, causal benefit, time savings,
  governance completeness, and return on investment.
- Learning uses one strict four-card projection over the same current
  observation. `observed_signal` reports direct zero-inclusive counts for the
  four existing Protection Event classes. `repeated_signal_candidate` is
  advisory and includes only a class appearing in at least two unique validated
  Protection Events, together with occurrence and distinct-task counts but no
  task identity. Two events may belong to the same task; the rule is a visible
  display threshold, not statistical significance or permission to generalize.
  `human_judgment` remains unavailable without an exact matching local review;
  when present, it reports the canonical human-product-owner role, a fixed
  disposition, zero-inclusive disposition counts, and resolution `unknown`.
  It exposes no task or source-event identity. `unknown` preserves causal improvement,
  outside-scope applicability, transferability, future recurrence, time
  savings, governance completeness, and ROI.

The self-contained HTML keeps the embedded machine-readable JSON collapsed
under `Technical audit data (optional)`. It is subordinate tool/debugging data;
ordinary task review does not require opening it.

Passing or verified outcomes are observations, not approval or causal benefit.
A Learning review records one bounded human disposition, not an explicit
continue/narrow/pause action and not handling or resolution. Those states
remain `unknown`. A later passing event is not labeled as proof that AgentGov
caused or resolved an earlier problem.
Guidance availability means only that the current report can navigate to Task
Detail; it does not mean the suggested review occurred.

Development source implements ADR-0012's separate `session.handed_off` event.
Monitor schema 1.4 counts and displays handoff as routing state while retaining
`verified` as the distinct latest completion state. Monitor generation itself
does not create the event or claim that a human read the output. For the exact
fresh verified local session, the CLI may print a `govern handoff --dry-run`
command only as guidance; that message grants no write or approval authority.

## Observed, inferred, and unknown

The Monitor keeps three claim layers visible:

- **Observed:** validated event fields and direct counts.
- **Inferred:** chronological grouping that may help review but does not prove
  causality.
- **Unknown:** missing history, semantic correctness, validation sufficiency,
  human handling, causal benefit, and ROI.

Monitor 1.7's Benefit view refines these layers into `observed_fact`,
`reproduced_comparison`, `supported_inference`, `human_feedback`, and `unknown`.
This first slice is `single_observation_only`, so reproduced comparison and human feedback are unavailable
rather than inferred. The separate two-snapshot Benefit Monitor is not imported or relabeled.
A future reproduced comparison
requires a documented denominator, applicability rules, and comparable
observation windows. Protection-event counts do not by themselves prove a
prevented production outcome, causal improvement, or ROI.

Monitor 1.9 keeps direct class counts observed and repeated-signal candidates
advisory. Local immutable reviews may make one exact current candidate's human
judgment available; stale reviews and export-backed inputs do not. Human
judgment remains distinct from resolution, while transferability and impact
remain unknown. Repetition inside one partial observation
does not prove a shared root cause, false-positive status, systemic weakness,
confirmed improvement, portability, or future recurrence. Task identities are
used only to derive a distinct-task count and are not emitted in the Learning
projection.

Monitor 1.10 keeps Active Task context artifact-owned and state derived from
the existing session and lifecycle events. Its immutable scope artifact records
only repository-relative Git path metadata, matched boundaries, deterministic
findings, and known limits—never source contents or raw validation output.
`verified` means only that the declared checks passed on the unchanged admitted
snapshot; human acceptance, architectural correctness, resolution, and every
downstream authority remain separate or unknown.

The static HTML escapes event metadata, embeds no source code or raw validation
output, performs no external requests, and contains no approval, exception,
commit, merge, deployment, or governance mutation controls. Exported actor
labels and local evidence pointers are always absent. Protection guidance uses
only deterministic internal task-card fragments; the strict machine contract
accepts no external or absolute target.

## Event integrity

Generation fails closed on malformed events, unsafe paths, sensitive text,
invalid authority, unsupported actor/outcome/type, mismatched event filename,
conflicting duplicate event IDs, or an unsafe, malformed, content-mismatched,
or task-mismatched scope artifact. Byte-equivalent duplicate event records
are removed deterministically and disclosed in the observation metadata.

The generated Monitor is a read model. Governance declarations continue to
live in their owning task, ADR, Skill, capability, control, dependency, and
evaluation artifacts; the Dashboard does not become a second source of truth.
