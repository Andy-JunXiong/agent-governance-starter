# Development governance Monitor

## Status

The Phase 4 static Monitor MVP is implemented in development source for the
future 0.3 line. It consumes the privacy-bounded events created by
`agentgov govern start/check/finish` and produces a self-contained local file with:

- Overview;
- Activity Timeline;
- Task Detail.

It is not part of stable 0.2.1. The explicit redacted-export slice lets it read
one reviewed development export or combine that export with a CI-only replay
store. The future 0.3 managed workflow template now includes a default-off,
manual-dispatch artifact path. It still does not include central telemetry,
GitHub Pages, automatic local-state transfer, approval controls, or
governance-file edits.

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

- Timeline answers when governance ran, which command family triggered it,
  which actor class invoked it, which governance paths start selected, recorded
  reason codes, observed counts, and outcome. Selection does not prove agent
  consumption.
- Overview counts tasks, starts, checks, validations, completions, handoffs,
  fresh/stale results, and event-reported findings without computing a score
  or percentage.
- Task Detail groups the visible sequence and shows the latest recorded event
  and completion outcome.

Passing or verified outcomes are observations, not approval or causal benefit.
The current events do not record explicit human continue/narrow/pause/override
decisions, so handling and resolution remain `unknown`. A later passing event
is not labeled as proof that AgentGov caused or resolved an earlier problem.

Development source implements ADR-0012's separate `session.handed_off` event.
Monitor schema 1.3 counts and displays handoff as routing state while retaining
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

The static HTML escapes event metadata, embeds no source code or raw validation
output, performs no external requests, and contains no approval, exception,
commit, merge, deployment, or governance mutation controls. Exported actor
labels and local evidence pointers are always absent.

## Event integrity

Generation fails closed on malformed events, unsafe paths, sensitive text,
invalid authority, unsupported actor/outcome/type, mismatched event filename,
or conflicting duplicate event IDs. Byte-equivalent duplicate event records
are removed deterministically and disclosed in the observation metadata.

The generated Monitor is a read model. Governance declarations continue to
live in their owning task, ADR, Skill, capability, control, dependency, and
evaluation artifacts; the Dashboard does not become a second source of truth.
