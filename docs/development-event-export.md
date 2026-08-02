# Redacted development-event export

## Status and purpose

The future-0.3 development source implements an explicit portable event bundle.
It closes one narrow visibility gap: `.agentgov/events/` is local and normally
Git-ignored, so CI cannot see development-time observations unless a user
deliberately exports them.

The export is not telemetry, an automatic upload, or an approval artifact. It
is a create-once JSON file that can be supplied to the static Monitor.

## User flow

First preview the exact source counts, retained fields, redaction, output, and
authority boundary without writing:

```powershell
python -m agentgov export development --repository . --dry-run
```

Then run the same command without `--dry-run` and type exact `EXPORT` in an
interactive terminal:

```powershell
python -m agentgov export development --repository .
```

The default file is immutable and content-addressed:

```text
.agentgov/exports/exp-<events-digest-prefix>.json
```

AgentGov refuses non-interactive confirmation, existing output, tracked output,
symbolic links, paths outside the repository, an empty source, CI events, or a
source with more than 10,000 events. It never silently replaces an export.

Use the printed path to build an exported-development Monitor:

```powershell
python -m agentgov monitor development . `
  --scope exported_development `
  --export .agentgov/exports/exp-<id>.json
```

To build a combined view in CI, place the reviewed export inside the checkout,
record CI replay events with actor class `ci`, and select both inputs:

```powershell
python -m agentgov monitor development . `
  --scope combined `
  --export .agentgov/exports/exp-<id>.json `
  --events .agentgov/events
```

AgentGov does not add the artifact download, upload, retention, or workflow
steps. Those remain repository-owned delivery decisions.

## Metadata retained and removed

The `metadata_only_v1` profile retains only bounded governance metadata:

- event and task identities, UTC timestamp, event type, and outcome;
- actor class (`human` or `coding_agent`), never a vendor/person label;
- selected repository-relative governance references and trigger reason codes;
- non-negative small counters and denied authority fields.

It always removes:

- optional actor labels;
- local evidence references;
- source or prompt content;
- validation commands and stdout/stderr;
- absolute user or runner paths;
- credential assignments and recognized token/private-key shapes.

Actor labels and local evidence references were removed by design; the bundle
cannot reconstruct them later.

The export contract validates every embedded event, canonical ordering,
uniqueness, event count, interval, SHA-256 event digest, content-derived export
ID, fixed redaction profile, claim limits, and denied authority. This detects
accidental corruption; it is not a signature or protection against a hostile
local author.

## Monitor truth boundary

`exported_development` means only the events explicitly present when the bundle
was created. `combined` means that export plus the selected CI replay store.
Both remain `partial`:

- unexported, deleted, other-working-copy, and other-machine development events
  remain absent;
- other CI runs and deleted CI artifacts remain absent;
- redacted labels and evidence pointers cannot be reconstructed;
- there is no cross-stage finding identity or resolution link.

Therefore even `combined` cannot report where a problem was first discovered,
causal benefit, ROI, requirement correctness, architecture correctness, or
coding-agent consumption. It only shows which bounded records were visible
from each declared source.

## Authority boundary

Preview is read-only. Export writes only the explicitly confirmed new bundle.
Neither export nor Monitor approves governance, changes governance files,
authorizes an exception, commits, merges, releases, or deploys. Automatic
GitHub Actions wiring and publication remain separate human-controlled work.
