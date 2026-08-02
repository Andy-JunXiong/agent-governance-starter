# Development changed-file scope check

## Status

The read-only changed-file scope check is implemented in development source
for the future 0.3 line. It is not included in stable 0.2.1 and is not yet
published. Guided `govern check` now wraps it and can resolve the task from the
confirmed working-copy session.

Run it against an admitted task from a Git worktree root:

```powershell
$env:PYTHONPATH = "src"
python -m agentgov check scope governance/tasks/my-task.json `
  --repository . --format terminal
```

`--format json` emits the strict
[`agentgov.development-scope-report`](../schemas/development-scope-report.schema.json)
contract. `--format markdown` presents the same findings for human review.

Exit code `1` means at least one deterministic changed-path boundary failed.
WARN is not used by this contract: architecture relevance is an `ADVISORY`,
and operational Git or filesystem errors use exit code `2`.

## Git facts inspected

The checker invokes read-only Git commands for:

- staged changes relative to `HEAD`;
- unstaged tracked changes relative to the index;
- non-ignored untracked paths from `git ls-files --others --exclude-standard`;
- Git-reported additions, modifications, deletions, type changes, conflicts,
  copies, and renames.

Ignored caches and build outputs do not appear. Untracked `.agentgov/` local
tool state is also canonically excluded so start/check/finish events cannot
fail their own scope check. If `.agentgov/` is tracked, its changes remain
visible like any other repository path. A file that is both staged and
then modified again appears in both layers because those are different facts.
The report records snapshot `HEAD`, task digest, layer, status, endpoints,
selection reason, and denied authority.

## Deterministic path policy

Paths use repository-relative POSIX segments:

- `src/route` matches itself and `src/route/handler.py`;
- `src/route` does not match `src/router/handler.py`;
- at least one include prefix must match;
- any matching exclude prefix overrides inclusion;
- a deletion checks its old path;
- a rename checks both old and new paths, and both must be admitted;
- a copy checks the changed destination path.

These rules implement
[Development Trigger and Routing Semantics v1](specs/development-trigger-routing-v1.md).
Natural-language task meaning does not participate in the deterministic
decision.

When a task explicitly declares architecture references and Git reports a
change, the report emits `architecture:candidate` as `ADVISORY`. This asks the
human or coding agent to review the already selected context; it does not claim
that architecture is violated.

## Authority and limits

The checker does not modify files, index, branch, history, task declarations,
or exception state. It does not authorize a scope exception, commit, or merge.

This phase covers the working tree only. A WIP commit removes those paths from
the staged/unstaged inventory. Committed-since-base scope requires the explicit
`comparison_base_sha` and canonical snapshot contract defined for the later
fresh-evidence phase. Until that exists, the report must not imply that a clean
working tree proves the whole task change set is in scope.

Explicit human exception records and action-loop self-reporting remain later
Phase 2 slices. Users can currently narrow or update the admitted task through
the human-controlled task decision process; AgentGov does not silently widen
scope.
