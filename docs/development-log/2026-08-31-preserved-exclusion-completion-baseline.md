# Preserved-exclusion completion baseline — 2026-08-31

## Goal and stop conditions

Close the observed admission-to-completion dead end without weakening scope:
an explicitly excluded pre-existing change may stop blocking completion only
when its exact task-start Git-layer identity remains unchanged and visible.
Stop on missing task admission, baseline collision, unclassified state,
identity mismatch, validation failure, scope expansion, or any need for Git,
release, deployment, publication, or external authority.

## Human-owned direction and admission

Alignment journey `mcpj-dd891f58ebbb4b54bc330f7010d8ed4a` offered strict
blocking, isolated-worktree-first, and frozen-exclusion-baseline directions.
The product owner selected the frozen baseline option. Native proposal
`prp-d1d3bd5ccbe748e8a1c5d6c2862e98e3` admitted exact task
`p0-preserved-exclusion-completion-baseline-v1`; a separate exact `REPLACE`
started it.

Because automatic start capture was the feature being built, the existing
internal tool captured this task's local pre-write baseline immediately after
session take-up and before implementation edits. Its digest is
`sha256:9286077ae464adbf336664869d5ffdc61b232ea2757df13e52b264277df72d50`.
Immediate comparison reported zero failures; seven current task paths passed
and seven explicitly excluded predecessor identities were preserved.

## Implemented vertical slice

- Promoted the deterministic baseline implementation into installed module
  `agentgov.task_start_scope_baseline`; the former script module now aliases the
  installed implementation.
- Added exclusive baseline capture to confirmed `govern start` before the
  pointer and start event, including exact-record rollback on later failure.
- Added baseline-aware completion findings. Byte-identical excluded identities
  render as visible non-owned `scope.preserved` passes; every material mismatch
  remains a failure.
- Kept missing-baseline behavior strict so historical and already-active
  sessions cannot acquire a retroactive boundary.
- Replaced native MCP's contradictory raw-scope precheck with the same
  baseline-aware, zero-write preflight used by completion semantics.
- Updated durable contracts and user guidance without changing task schema,
  completion states, release identity, or authority boundaries.

## Tests and validation

Focused coverage now includes start capture, collision, rollback, included
post-start deltas, unchanged predecessor exclusions, changed and malformed
baselines, strict missing-baseline fallback, MCP parity, and zero-write MCP
scope blocking. The focused set passes 97 tests with two platform-limited
skips. The complete suite passes 1,135 tests with six platform-limited skips.

Task governance is `PASS=3 WARN=1 FAIL=0 ADVISORY=3`; repository governance is
`PASS=26 WARN=2 FAIL=0 ADVISORY=4`; `git diff --check` passes. First formal
evidence `evd-735121e5ffa54da9b35aaa25a829a237` ran all five declared commands,
recorded no validation mutation, kept all seven predecessor exclusions visible
as `scope.preserved`, and reached `verified`. A final no-edit rerun after this
closeout record re-establishes freshness for the completed tracked snapshot.

## Advisory review and remaining limits

Native current-Agent self-review `srv-6cbb0eb1f8803996b9d90681f1457880`
found the selected requirement, single-policy architecture, exact scope,
fixture behavior, and hash-only privacy boundary consistent. It retained large
dirty-worktree performance, external installed-consumer replay, POSIX real-host
execution, Windows symlink behavior, and hostile-local-writer protection as
unknown. This is self-review, not independent assurance.

## Authority and next review

No commit, push, merge, publication, release, deployment, consumer mutation,
or external write was performed. The baseline is local evidence, not task
ownership, an exception, semantic acceptance, or downstream authority. Product
review may next return to the independent automatic journey; that proposal does
not itself authorize a new task or action.
