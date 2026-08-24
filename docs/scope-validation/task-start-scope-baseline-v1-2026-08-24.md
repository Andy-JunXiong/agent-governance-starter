# Task-start scope baseline v1 — 2026-08-24

## Outcome

Task `p0-task-start-scope-baseline-v1` implements a repository-internal,
deterministic comparison boundary under `scripts/task_start_scope_baseline`.
It is a bridge for a later separately admitted task, not public product surface
and not retroactive completion evidence.

## What was built

The internal module:

- validates and binds one exact admitted task path, task ID, canonical task
  digest, captured scope, comparison base, and HEAD;
- captures stable before/after canonical Git snapshots and aborts if state
  changes during capture;
- derives a separate identity for every committed-since-base, staged,
  unstaged, and untracked record, retaining both rename/copy endpoints;
- stores only normalized relative paths, status categories, identity kinds,
  and SHA-256 digests, never raw content or patches;
- creates one explicitly selected local record below
  `.agentgov/scope-baselines` with exclusive no-overwrite semantics;
- reports an exact unchanged pre-existing exclusion as `PRESERVED`, admits a
  post-start change only when every endpoint is included, and fails closed on
  excluded or unclassified drift, disappearance, task drift, HEAD drift,
  malformed state, unsafe paths, symlinks, or capture races.

The internal command shape is:

```powershell
$env:PYTHONPATH = "src"
py -3.11 -m scripts.task_start_scope_baseline capture --repository . --task governance/tasks/<task>.json --output .agentgov/scope-baselines/<task>.json
py -3.11 -m scripts.task_start_scope_baseline check --repository . --task governance/tasks/<task>.json --baseline .agentgov/scope-baselines/<task>.json
```

These commands do not grant task, exception, Git, model, release, deployment,
publication, or external-write authority.

## Privacy and mutation boundary

Persisted records exclude source text, raw diffs, absolute paths, environment
values, credentials, process identifiers, and human or host identity. Capture
and comparison use read-only Git commands. Only `capture` can create a file,
and only at the caller-selected safe local baseline path. It refuses overwrite.
The task performed no dependency download, network call, model call, Codex or
MCP execution, consumer change, Git transition, commit, push, publication,
release, or deployment.

## Bootstrap limit

This tool did not exist before its own implementation began. Its real-worktree
smoke capture was deliberately non-persisted and occurred after implementation;
therefore it proves only that capture and immediate comparison work on the
current repository. It does not prove this task's start state, waive the
existing cumulative scope failures, or retroactively complete the foreground
STDIO controller task.

The first meaningful use must be a later separately admitted task that invokes
`capture` before any repository write.

## Validation

- 17 focused tests pass; one symlink test is skipped because this Windows host
  does not permit the fixture link.
- Python compilation passes for the internal module.
- A non-persisted real-worktree capture observed 67 Git-layer identities.
- An immediate non-persisted comparison returned `FAIL=0`, `PRESERVED=42`, and
  `PASS=25`. This is mechanics evidence only, not start-boundary evidence.
- The complete supported Python 3.11 suite passes all 1083 tests with 4
  platform-limited skips in 159.851 seconds.
- All 54 documentation tests pass.
- Task governance reports `PASS=3 WARN=1 FAIL=0 ADVISORY=3`.
- Repository governance reports `PASS=26 WARN=2 FAIL=0 ADVISORY=4`.
- `git diff --check` passes, and the bounded task-path secret-pattern scan has
  no matches.

The existing cumulative worktree scope report contains 68 layer records:
`PASS=26 FAIL=42`. The 26 admitted paths comprise 11 task-owned files plus
preserved predecessor paths; all 42 failures are pre-existing paths that the
task explicitly excludes. This is the expected bootstrap boundary, not a pass,
exception, or claim that older work was authorized.

Native task-completion recording was unavailable in the current tool surface,
so no completion record is claimed. Native current-Agent self-review
`srv-22bc7be44bc9c41bef679609d8ea8db8` completed as a separate advisory pass.
It confirmed the bounded requirement, internal architecture, exact scope,
deterministic implementation, and privacy boundary while retaining the
bootstrap limit, performance, cross-platform symlink behavior, causal benefit,
and later controller closeout as unknown. It is not independent assurance or
an exception.
