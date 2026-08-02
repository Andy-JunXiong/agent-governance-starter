# Fresh validation evidence and completion reconciliation

## Status

The Phase 3 core is implemented in development source for the future 0.3
line. It is not part of stable 0.2.1. Guided `govern start` now records the
active task and comparison base; GitHub event export, automatic artifact wiring,
and cross-machine history are still pending.

The shortest current development-source workflow is:

```powershell
$env:PYTHONPATH = "src"
python -m agentgov govern check governance/tasks/my-task.json --repository .
python -m agentgov govern finish governance/tasks/my-task.json `
  --repository . --base <comparison-base-revision>
```

`govern finish --base` resolves the comparison base, captures `S0`, runs every
validation command declared by the admitted task, captures `S1`, writes local
evidence, captures `S2`, and immediately reconciles completion. Omitting
`--base` reuses the latest evidence for that task; `--evidence` selects one
specific record beneath `.agentgov/evidence/`.

After one confirmed `govern start`, ordinary use is now `govern check` followed
by `govern finish`; both resolve the active task and finish also runs validation
from the recorded base. Explicit task/base/evidence arguments remain low-level
composition interfaces.

## What `verified` means

`verified` has a deliberately narrow meaning:

- every validation command currently declared by the admitted task ran and
  exited successfully;
- the task digest, comparison base, snapshot `HEAD`, committed-since-base,
  staged, unstaged, rename, and non-ignored untracked identities remained
  unchanged from validation completion to finish;
- all canonical changed paths remain inside the task's structured scope.

It does not prove that the validation commands were sufficient, the
requirement was satisfied, or the architecture is correct. Architecture and
requirement review remain advisory and accountable to humans. The report and
events grant no commit, merge, deployment, exception, or semantic-completion
authority.

Without matching evidence, finish reports `needs_evidence`; it never upgrades a
self-reported completion claim to `verified`.

## Canonical snapshot and exclusions

The `agentgov.git-change-set.v1` digest binds four ordered Git layers:

1. committed changes from `comparison_base_sha` to `snapshot_head_sha`;
2. staged changes relative to snapshot `HEAD`;
3. unstaged tracked changes relative to the index;
4. non-ignored untracked file and symlink identities.

Evidence stores repository-relative paths and SHA-256 identities, not source
content. It also stores command, stdout, and stderr digests rather than command
text or output text. Absolute user paths and credential-like assignments are
rejected from persisted local records.

Ignored untracked files do not enter the snapshot. Untracked `.agentgov/`
local state is also excluded, so recording evidence or an event cannot make
itself stale. Tracked `.agentgov/` changes and tracked `.gitignore` changes are
never hidden.

If validation creates a tracked or non-ignored artifact, evidence becomes
`stale`. The finding identifies repository-relative affected paths and asks the
user or coding agent to inspect and retain intentional task work, remove a
disposable artifact, or intentionally add an appropriate ignore rule before
rerunning validation. AgentGov does not edit `.gitignore` automatically.

Both orders remain valid when nothing changes between validation and finish:

```text
edit -> validate/finish -> commit
edit -> commit -> validate/finish
```

Editing, staging, unstaging, renaming, committing, checking out, or rebasing
after validation makes prior evidence stale.

## Local events and observation limits

Each observation is written once to a new file beneath
`.agentgov/events/`; evidence is written once beneath
`.agentgov/evidence/`. Unique create-only files avoid overwriting prior facts
and make concurrent writers independent. Symlinked local-state paths and
existing record identifiers are rejected.

Current event types are:

- `task.started`;
- `scope.checked`;
- `validation.completed`;
- `completion.reconciled`.

Events contain actor class (`human`, `coding_agent`, or `ci`), optional
vendor-neutral label, task digest, outcome, selected governance references,
reason codes, small observed counts, and denied authority. Version 1.1 adds
`task.started` and governance references; the loader remains compatible with
version 1.0 events, treating their absent reference list as empty. Events do
not contain source, validation output, absolute paths, or causal/ROI claims.

These events have observation scope `local_development`. CI and other machines
cannot see them unless a user creates the explicit metadata-only bundle defined
in [Redacted development-event export](development-event-export.md). An export
removes actor labels and local evidence pointers and still represents partial,
not complete, development history.

## Execution and trust boundary

`govern finish --base` executes the commands declared in the admitted task.
That is an explicit local execution boundary: users should admit tasks and
commands only from a repository they trust. AgentGov records command identity
and outcome but does not sandbox project commands.

Evidence has strict structural and internal-integrity checks, but v1 does not
cryptographically attest a hostile local actor. Signed evidence, runtime
enforcement, hooks, and daemon behavior require a separate threat model and
authorization decision.
