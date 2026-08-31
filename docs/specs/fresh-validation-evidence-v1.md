---
layout: reference
title: Fresh validation evidence semantics v1
source_path: docs/specs/fresh-validation-evidence-v1.md
---

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

## Task-start exclusion baseline

A newly confirmed development session must exclusively create
`.agentgov/scope-baselines/<task-id>.json` before the session pointer, start
event, or implementation write. The record binds the exact admitted task path,
task digest, captured scope, comparison base, HEAD, snapshot exclusion rules,
and privacy-reduced identity of every Git-layer change visible at that boundary.
It contains repository-relative paths and SHA-256 identities only, never raw
source, patches, commands, output, credentials, environment values, host or
human identity.

At completion, an exact baseline identity outside the include scope may be
reported as `scope.preserved` only when its layer, status, path and any old
path, identity kind, and digest remain unchanged. It stays visible and
non-owned. A changed, removed, renamed, copied, re-layered, new, excluded, or
unclassified identity fails closed. Task, scope, comparison-base, HEAD,
snapshot-exclusion, malformed-record, symlink, capture-race, and overwrite
mismatches also fail closed.

A missing baseline never creates one retroactively. Completion instead applies
the prior strict rule in which every current changed path must be admitted.
Baseline preservation changes neither the `needs_evidence`/`verified` state
model nor any task, exception, Git, release, or semantic-acceptance authority.

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

## Platform shell execution

The admitted `validation_commands` contract remains an ordered array of
strings. Each string is interpreted by one explicit platform-native shell;
AgentGov does not pass it to Python's implicit `shell=True` selection:

- Windows uses `powershell.exe` with `-NoLogo`, `-NoProfile`,
  `-NonInteractive`, and a UTF-16LE `-EncodedCommand` payload. The encoded
  payload preserves PowerShell quoting and appends bounded exit handling so a
  successful command exits zero, a failed native command retains its nonzero
  exit code, and another PowerShell failure exits nonzero.
- POSIX uses `/bin/sh -c` with the original command string.

The stable command identity is always calculated from the admitted original
string, not the platform argv, encoding, or Windows exit-handling suffix. Raw
standard output and error remain transient; persisted evidence contains only
their digests. Commands still stop at the first nonzero result, retain the
declared timeout, and run between the same `S0` and `S1` snapshots.

For compatibility with existing admitted Windows strings whose first token is
a quoted executable path, the encoded execution payload inserts PowerShell's
call operator before that token. This bounded adaptation does not rewrite the
task or command identity and does not reintroduce `cmd.exe` interpretation.

If the platform is unsupported or its required shell cannot be started,
validation fails closed before an evidence or completion event is written.
The explicit shell is an execution adapter, not a sandbox or a trust upgrade:
the accountable human must still admit only project commands they trust.

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
