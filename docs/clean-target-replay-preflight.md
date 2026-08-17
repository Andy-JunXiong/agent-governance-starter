# Clean-target replay preflight

Status: implemented in development source as a deterministic, dependency-free,
read-only contract, evaluator, and CLI check. It does not clean a repository,
reserve a replay identifier, launch a model session, admit a task, or authorize
a replay. A separate development-source reservation command can create one
human-confirmed marker after repeating the same preflight; it does not change
this read-only check.

## Purpose

A governed replay is useful only when its starting state can exercise the
intended behavior. The clean-target preflight checks those prerequisites before
a scarce replay is consumed. It was added after the 2026-08-16 AIRBNB attempt
started with an earlier target change and related task already present, making
the intended Adapter behavior unmeasurable.

The preflight answers one narrow question:

> Do the explicit local prerequisites in this replay plan hold now?

It does not authorize a replay, decide whether a replay should be authorized,
or decide whether the requested product experiment is valuable.

## Plan contract

`agentgov.replay-preflight-plan` version `1.0` binds:

- one `rpf-` correlation identifier and a repository-relative marker directory;
- the exact expected Git `HEAD` revision;
- one or more exact target paths and explicit machine-checkable preconditions;
- exact related task identifiers that must be absent;
- a repository-relative Adapter metadata document and the expected Adapter id,
  version, and MCP protocol;
- a denied authority boundary.

Supported target preconditions are deliberately small:

- `path_absent`;
- `text_absent`;
- `text_present`;
- `sha256_equals`.

The evaluator does not infer that different text is semantically equivalent.
Use `sha256_equals` when exact bytes are the required baseline.

Example plan:

```json
{
  "contract": "agentgov.replay-preflight-plan",
  "schema_version": "1.0",
  "correlation": {
    "correlation_id": "rpf-0123456789abcdef",
    "registry_directory": ".agentgov/replay-correlations"
  },
  "repository": {
    "expected_head_sha": "0123456789abcdef0123456789abcdef01234567"
  },
  "targets": [
    {
      "path": "README.md",
      "precondition": {
        "kind": "text_absent",
        "value": "### Two-terminal local demo"
      }
    }
  ],
  "related_tasks": {
    "directory": "governance/tasks",
    "absent_task_ids": ["rename-readme-demo-heading"]
  },
  "adapter": {
    "metadata_path": ".agentgov/adapter.json",
    "expected_adapter_id": "openai.codex-mcp",
    "expected_adapter_version": "1.5.0",
    "expected_protocol_version": "2026-07-28"
  },
  "authority_boundary": {
    "authorizes_cleanup": false,
    "authorizes_deployment": false,
    "authorizes_git_operations": false,
    "authorizes_publication": false,
    "authorizes_release": false,
    "authorizes_replay": false,
    "authorizes_repository_write": false,
    "authorizes_task_admission": false
  }
}
```

The local Adapter metadata file is also strict and intentionally small:

```json
{
  "contract": "agentgov.replay-adapter-metadata",
  "schema_version": "1.0",
  "adapter_id": "openai.codex-mcp",
  "adapter_version": "1.5.0",
  "protocol_version": "2026-07-28"
}
```

If no trustworthy local metadata file exists, the result is `UNKNOWN`; an
operator-supplied guess is not promoted to observed Adapter identity.

## Run the check

From development source:

```powershell
$env:PYTHONPATH = "src"
python -m agentgov check replay-preflight path/to/plan.json `
  --repository path/to/consumer --format terminal
```

Use `--format json` for the versioned machine-readable report. Exit code `0`
means `READY`; `1` means `BLOCKED` or `UNKNOWN`; malformed plans and operational
input errors use the CLI error exit code.

## Result semantics

- `READY`: every named prerequisite is established. This is not replay
  authorization.
- `BLOCKED`: at least one deterministic prerequisite is false and no required
  fact is unknown.
- `UNKNOWN`: at least one required fact cannot be established. `UNKNOWN` takes
  precedence over `BLOCKED` so incomplete inspection is never hidden.

Every non-`READY` result says not to consume the replay. Stable reason codes
identify stale revisions, dirty or mismatched targets, missing targets,
related-task collisions, Adapter mismatch or unavailable metadata, duplicate
correlation markers, and unavailable Git or registry facts.

The Git inspection reads `HEAD`, tracked changes including both rename
endpoints, and non-ignored untracked paths. It does not write the index,
working tree, branch, or history.

## Correlation boundary

The check looks for
`<registry_directory>/<correlation_id>.json`. An existing marker is a
deterministic collision. A missing marker means only that no local collision
was recorded; the preflight does not create or reserve a marker and cannot
eliminate a time-of-check/time-of-use race. Marker creation, replay admission,
and lifecycle evidence remain separate human-controlled work.

## Human-controlled reservation

Development source now implements three strict version `1.0` contracts in
`schemas/replay-correlation-reservation-v1.schema.json`:

- `agentgov.replay-correlation-reservation-preview` shows the exact proposed
  marker and fresh preflight facts;
- `agentgov.replay-correlation-reservation` is the create-only local marker;
- `agentgov.replay-correlation-reservation-result` records the bounded write
  effect while retaining the denied authority boundary.

The low-level CLI defaults to a read-only preview:

```powershell
$env:PYTHONPATH = "src"
python -m agentgov reserve replay-correlation path/to/plan.json `
  --repository path/to/consumer --format terminal
```

The plan's `registry_directory` must already exist as a real local directory.
Preview refuses a missing, non-directory, or symbolic-link registry instead of
creating scaffolding. A non-`READY` preflight cannot produce a marker preview.

Applying the preview is a separate terminal-only fallback:

```powershell
python -m agentgov reserve replay-correlation path/to/plan.json `
  --repository path/to/consumer --apply
```

The CLI prints the exact marker, requires exact interactive `RESERVE`, then
re-evaluates the same plan against the same repository immediately before an
exclusive file create. Redirected input, cancellation, stale target or Git
state, Adapter mismatch, existing markers, and exclusive-create races do not
overwrite or create the requested marker. Successful apply writes exactly one
marker beneath the declared registry.

Reservation closes the local correlation-name race at marker creation time.
It does not freeze later repository state, admit a task, authorize or launch a
replay, or grant cleanup, Git, publication, release, or deployment authority.
The exact-word terminal interaction is a development and recovery surface; a
future host-native decision surface may carry the same contract separately.

## Create-only pre-run claim

Development source also implements strict version `1.0` plan, marker, preview,
and result contracts in `schemas/replay-correlation-claim-v1.schema.json`. A
claim plan names one immutable reservation marker and digest, one pre-existing
claim registry, one normalized claimant, and the local Adapter metadata path.

The default command is a read-only preview:

```powershell
$env:PYTHONPATH = "src"
python -m agentgov claim replay-correlation path/to/claim-plan.json `
  --repository path/to/consumer --format terminal
```

Preview reports `READY_TO_CLAIM`, `BLOCKED`, or `UNKNOWN`. It requires the
reservation marker to remain valid and byte-digest-equivalent, the consumer's
current `HEAD` to match the reservation, the local Adapter identity to match,
the declared claim registry to exist as a real directory, and the derived
claim path to be absent. It creates no directory or marker.

Create-only apply is a separate terminal action:

```powershell
python -m agentgov claim replay-correlation path/to/claim-plan.json `
  --repository path/to/consumer --apply
```

The CLI displays the exact claim, accepts only interactive exact `CLAIM`,
revalidates the reviewed facts, and uses an exclusive local file create. A
collision, stale input, malformed evidence, or uncertain state fails closed
without overwriting the reservation or any existing claim. If creation begins
but writing becomes uncertain, the path is retained to block automatic reuse;
there is no automatic deletion, expiry, recovery, or takeover.

`agentgov.replay-correlation-claim` is durable pre-run ownership evidence. It
does not authorize, launch, consume, expire, recover, take over, or prove a
replay, and it grants no task, cleanup, Git, publication, release, or
deployment authority. The optional pure bridge binding accepts only the exact
matching `reserved` bridge; neither contract is mutated.

## Immutable abandoned-claim recovery

An interrupted claim write is deliberately retained, so recovery is a
separate side path rather than mutation of the claim. Development source
defines strict `1.0` plan, inspection, recovery marker, preview, and result
contracts in `schemas/replay-claim-recovery-v1.schema.json`.

The default CLI is read-only:

```powershell
$env:PYTHONPATH = "src"
python -m agentgov recover replay-claim path/to/recovery-plan.json `
  --repository path/to/consumer --format terminal
```

Inspection reads at most 1 MiB of claim evidence and records only its digest,
byte length, and classification. It reports `VALID`, `PARTIAL`, `MALFORMED`,
`MISSING`, `INCONSISTENT`, `UNKNOWN`, or `RECOVERED`; raw claim content is not
copied into the report or recovery marker. Missing and inconsistent evidence
is blocked, while unsafe, unreadable, oversized, or invalid recovery evidence
is unknown. A valid claim is not automatically considered abandoned:
abandonment remains a human-owned fact.

Create-only recovery requires a pre-existing safe recovery registry:

```powershell
python -m agentgov recover replay-claim path/to/recovery-plan.json `
  --repository path/to/consumer --apply
```

Only exact bounded `VALID`, `PARTIAL`, or `MALFORMED` bytes can reach
`READY_TO_RECOVER`. The CLI displays the exact marker, accepts only interactive
exact `RECOVER`, repeats reservation, raw claim digest, consumer `HEAD`,
Adapter, registry, and collision checks, then uses exclusive local file
creation. Cancellation and stale, conflicting, or uncertain evidence write
nothing. If recovery-marker creation begins but its write becomes uncertain,
the path remains to block automatic reuse.

The recovery marker preserves the original reservation and claim bytes and
can classify only that exact digest as `RECOVERED` in the pure ownership
evaluator. It does not delete, repair, expire, replace, or transfer a claim; it
does not create replacement ownership, authorize or prove replay, or grant cleanup, Git,
publication, release, deployment, or task authority. `recovered_by` and
`reason_code` are human-declared labels, not identity authentication. Network-
filesystem exclusive-create and power-loss behavior remain unvalidated.

## Product connection

The bounded sequence is now:

```text
read-only preflight -> human-controlled reservation -> create-only claim -> separately authorized replay -> correlation bridge -> Harness Contract v1
```

Abandoned-claim inspection and immutable recovery form a side branch from the
claim. Recovery is not a substitute step that advances into replay.

Harness Contract v1 remains the offline post-replay evidence contract that
derives First Deviation from normalized expected and observed transitions.
The additive `agentgov.replay-correlation-bridge` `1.0` contract now makes the
mapping explicit without changing or automatically populating the Harness
schema. It represents exactly `reserved`, `consumed`, `invalidated`, or
`unavailable`, preserves the reservation identity, marker path, and marker
digest, and fixes the downstream mapping to the existing Harness v1 field
`host.repository_correlation`.

The dependency-free bridge validator accepts already-loaded normalized JSON
only. `reserved` and `consumed` require the exact matching reservation marker;
`consumed` additionally requires a valid Harness run whose `run_id` and
`host.repository_correlation` match the bridge. Invalidated or unavailable
records retain an explicit reason and cannot name Harness evidence. Strict
fixtures for all four states live under
`governance/fixtures/replay-correlation-bridge-v1/`.

The bridge records and verifies correlation lifecycle evidence. It does not
reserve, consume, invalidate, authorize, launch, or complete a replay; write a
marker or Harness record; prove product effectiveness; or grant task, cleanup,
Git, publication, release, or deployment authority. The separate pre-run claim
closes only the local ownership race, while recovery preserves exact abandoned
evidence without creating replacement ownership. A future launcher still needs a
separately designed claim-to-Harness consume transition. `doctor` still checks
repository and installation readiness, while `check scope` still compares
existing changes with one admitted development task. Their meanings are
unchanged.

No AIRBNB cleanup or replay is part of this implementation. Reservation itself
does not authorize a real-consumer rehearsal. Restart-safe native journey
persistence remains a separate future product-review candidate.
