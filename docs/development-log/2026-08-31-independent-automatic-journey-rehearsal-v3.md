# Independent automatic-governance journey rehearsal v3 - 2026-08-31

## Goal, non-goals, and stop condition

Run one independently governed exact-current-source automatic user journey
using the available supported Python 3.12 runtime. Do not modify product code,
the distribution manifest, existing consumer state, configuration, or any
pre-existing untracked path. Stop at the first reproducibility, scope, privacy,
host, protocol, or state-preservation deviation without retry or repair.

## Human direction and admission

The product owner selected the automatic-journey direction through resolved
alignment journey `mcpj-e3a056c978254d30a602c2885f5c5edc`. Native proposal
`prp-d8a070579b444e4cae5d17bf674b57f5` admitted task
`p0-independent-automatic-journey-rehearsal-v3`. After a stale installed CLI
preview requested the wrong transition for the actual state and was cancelled
without writes, the product owner supplied exact `START`. Current source then
created baseline
`sha256:9ce1affec3832e9af4810d51d19b96c3a0d65c13fadbd5f7c1db296c2963f305`
before the activity pointer and start event.

## Actions and first deviation

Read-only preflight confirmed the task-start baseline and preserved the three
pre-existing untracked exclusions. The next mandatory gate checked the durable
distribution manifest against independent derivation from exact current
source. It failed deterministically:

- manifest path count: 186;
- derived path count: 187;
- extra derived path: `src/agentgov/task_start_scope_baseline.py`;
- declared versus derived path identity: mismatch;
- declared versus derived content identity: mismatch; and
- tracked deltas and untracked overlays in the derived distribution set: zero.

The task therefore stopped as
`STOPPED_AT_DISTRIBUTION_MANIFEST_PREFLIGHT`. No build, wheel, isolated
installation, temporary root, fixture repository, fixture commit, external
Codex session, model request, consumer form, consumer tool call, retry, repair,
or substitution occurred.

Durable normalized evidence is in
`docs/experiments/independent-automatic-journey-rehearsal-v3-2026-08-31.md`.

## Validation and review

The current-source scope comparison passes with three preserved exclusions,
one unchanged included task record, and all three post-start documentation
deltas in scope. The focused documentation suite passes all 63 tests. The
complete suite passes all 1,134 tests with six platform-limited skips. Task
governance is `PASS=3 WARN=1 FAIL=0 ADVISORY=3`; repository governance is
`PASS=26 WARN=2 FAIL=0 ADVISORY=4`. Task JSON and `git diff --check` pass.
Final freshness is re-established after this result update. Distinct
current-Agent advisory review `srv-88c41660caae11d2bf57ded4ddbd33d7`
found the first-deviation attribution, contract ownership, scope, privacy, and
authority boundaries consistent. It retained all downstream journey behavior
and product benefit as unknown and is not independent assurance or human
acceptance.

## Authority and remaining gap

The distribution manifest and product source are excluded from this task and
remain unchanged. No Git, network, publication, release, deployment, or other
external authority was exercised. The first deviation leaves artifact build
and every downstream automatic-journey stage untested.

The next product review may consider one narrow manifest synchronization task.
That suggestion does not authorize the repair, a retry, a new rehearsal, or
any downstream action.
