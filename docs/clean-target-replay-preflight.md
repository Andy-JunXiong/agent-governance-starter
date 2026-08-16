# Clean-target replay preflight

Status: implemented in development source as a deterministic, dependency-free,
read-only contract, evaluator, and CLI check. It does not clean a repository,
reserve a replay identifier, launch a model session, admit a task, or authorize
a replay.

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

## Product connection

This gate runs before a replay. Harness Contract v1 remains the offline
post-replay evidence contract that derives First Deviation from normalized
expected and observed transitions. `doctor` still checks repository and
installation readiness, while `check scope` still compares existing changes
with one admitted development task. Their meanings are unchanged.

No AIRBNB cleanup or replay is part of this implementation. A future product
review may consider a human-controlled correlation reservation or restart-safe
native journey persistence, but neither is authorized here.
