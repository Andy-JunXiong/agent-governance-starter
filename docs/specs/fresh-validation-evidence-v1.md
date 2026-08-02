# Fresh Validation Evidence Semantics v1

Status: design contract; hard gate before Phase 3 implementation
Owner: AgentGov development-governance architecture
Related decision: [ADR-0009](../adr/0009-govern-coding-agents-during-development.md)
Product context: [AgentGov product and architecture plan](../proposals/2026-08-02-agentgov-product-and-architecture-plan.zh-CN.md)

## Purpose

This specification defines when validation evidence is fresh for the exact
task and repository snapshot being reconciled. It prevents AgentGov's own
event files and normal ignored build outputs from invalidating evidence, while
still detecting relevant source, staging, commit, and non-ignored artifact
changes.

Fresh evidence proves only that a declared validation command completed
against an unchanged governed snapshot. It does not prove that the command was
sufficient, the architecture is correct, or the requirement was satisfied.

## Evidence identity

Each evidence record contains at least:

- validation command or stable command identity;
- start and completion timestamps, exit status, and optional sanitized output
  digest;
- canonical task-contract digest;
- `comparison_base_sha`: the commit against which the admitted task change set
  is defined;
- `snapshot_head_sha`: `HEAD` at the validation snapshot;
- canonical change-set digest and its algorithm version;
- AgentGov version and evidence-contract version.

`comparison_base_sha` and `snapshot_head_sha` are separate fields. Calling
either one only “base commit” is prohibited because task comparison and the
current validation snapshot serve different purposes.

## Canonical change-set scope

The digest represents ordered Git layers relative to the admitted comparison
base:

1. committed task changes from `comparison_base_sha` to `snapshot_head_sha`;
2. staged changes relative to `snapshot_head_sha`;
3. unstaged tracked changes relative to the index;
4. non-ignored untracked files reported by
   `git ls-files --others --exclude-standard`;
5. rename identity, including both old and new repository-relative paths, in
   the layer where Git reports it.

Each canonical entry identifies its layer, change type, repository-relative
POSIX path or rename endpoints, and content or patch identity. Entries are
sorted deterministically and hashed with SHA-256 under an explicit digest
format version. Evidence stores hashes and necessary repository-relative
identifiers, not source contents.

Canonical exclusions are narrow:

- ignored untracked files are absent because untracked discovery uses
  `--exclude-standard`;
- untracked files beneath the reserved `.agentgov/` local tool-state directory
  are excluded even when a consumer has not yet added the recommended ignore;
- tracked changes are never hidden by these exclusions, including tracked
  `.agentgov/` files;
- a changed tracked `.gitignore` is included like any other tracked change;
- exclusion reasons and the digest-format version are part of digest metadata
  so the scope remains explainable.

AgentGov must not write an event into a tracked repository file as a side
effect of a read-only governance check. Observe writes are limited to the
disclosed local tool-state area, and source/index/branch/history remain
unchanged.

## Validation snapshots

AgentGov computes three snapshots:

- `S0` immediately before running the validation command;
- `S1` immediately after the command completes;
- `S2` when `govern finish` reconciles the task.

Evidence is fresh only when all of the following remain equal across the
applicable snapshots:

- canonical task digest;
- `comparison_base_sha`;
- `snapshot_head_sha`;
- canonical change-set digest and digest-format version.

The validation result must also satisfy the task's declared acceptance rule.
File mtime is not a freshness oracle.

Ignored test caches, coverage files, and build outputs do not change the
digest. If validation creates or changes a tracked or non-ignored file, `S1`
differs from `S0` and the evidence is stale. The error must identify the
affected repository-relative paths and explain the recovery options: inspect
and retain the generated change as task work, remove the disposable artifact,
or intentionally add an appropriate ignore rule, then rerun validation.
AgentGov must not edit `.gitignore` automatically.

## Valid and invalid workflow order

Both of these are valid when no governed snapshot changes after validation:

```text
edit -> validate -> govern finish -> commit
edit -> commit -> validate -> govern finish
```

A WIP commit is therefore supported. These sequences are stale and require
validation to be rerun:

```text
validate -> edit/stage/unstage/rename -> govern finish
validate -> commit/checkout/rebase -> govern finish
```

The user-facing error must name the changed identity: task contract,
comparison base, snapshot `HEAD`, staged state, worktree content, rename, or
non-ignored untracked artifact. A raw “digest mismatch” is insufficient.

## Completion states and claim limits

Without fresh evidence for the current task and snapshot, completion may be
reported as `claimed` or `needs_evidence`, never `verified`. Even with fresh
evidence, unresolved advisory architecture or requirement questions remain
visible for human decision.

## Required Phase 3 policy tests

Phase 3 implementation is blocked until fixture-based tests cover at least:

- ignored `.agentgov/events/` writes not invalidating evidence;
- an unignored local `.agentgov/` event write being canonically excluded;
- a tracked `.agentgov/` change being included;
- ignored pytest, coverage, and build artifacts being excluded;
- a validation-generated non-ignored artifact making evidence stale with an
  actionable message;
- a changed tracked `.gitignore` invalidating prior evidence;
- edits, staging changes, commits, renames, and task-contract changes between
  validation and finish making evidence stale;
- both documented valid workflow orders succeeding;
- deterministic ordering producing the same digest for the same snapshot;
- evidence never storing source contents, credentials, or absolute user paths.
