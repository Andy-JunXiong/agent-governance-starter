# Development governance Monitor

## Status

The Phase 4 static Monitor MVP is implemented in development source for the
future 0.3 line. It consumes the privacy-bounded events created by
`agentgov govern start/check/finish` and produces a self-contained local file with:

- Overview;
- Activity Timeline;
- Task Detail.

It is not part of stable 0.2.1. The later explicit redacted-export slice now
lets it read one reviewed development export or combine that export with a
CI-only replay store. It still does not include central telemetry, GitHub
Pages, automatic Actions upload, approval controls, or governance-file edits.

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

For a CI artifact:

```powershell
python -m agentgov monitor development . `
  --scope ci_only --output .agentgov/dashboard.html
```

The resulting file can be uploaded with the repository's normal artifact
step. AgentGov does not add or change that workflow in this phase.

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
- Overview counts tasks, starts, checks, validations, completions, fresh/stale results,
  and event-reported findings without computing a score or percentage.
- Task Detail groups the visible sequence and shows the latest recorded event
  and completion outcome.

Passing or verified outcomes are observations, not approval or causal benefit.
The current events do not record explicit human continue/narrow/pause/override
decisions, so handling and resolution remain `unknown`. A later passing event
is not labeled as proof that AgentGov caused or resolved an earlier problem.

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
