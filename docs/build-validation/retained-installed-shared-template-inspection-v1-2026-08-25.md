# Retained installed shared-template inspection v1

Date: 2026-08-25

## Outcome

`STOPPED_AFTER_VERIFIED_SHARED_TEMPLATE_GATES_AT_SOURCE_STAGE_BREADTH_REVIEW`

All four retained-artifact technical gates passed, but the task is not
presented as fully accepted. The one build driver archived all 747 committed
regular files from `HEAD` instead of the 199 exact committed distribution
inputs used by the prior protocol. The seven exact current distribution
overlays still matched, and setuptools emitted the same 188-member inventory,
but staging extra committed repository files violated the admitted narrow
source-staging constraint.

There was no repair, second build, second install, alternate artifact, or
rehearsal-v2 continuation. The successful technical gate evidence is retained
because it answers the installed shared-template question; the staging-breadth
deviation is retained because it limits task acceptance.

## Governed boundary

- Alignment journey: `mcpj-3993a26f8dc44cafbb99607d55fc37d0`.
- Selected direction: retained artifact inspection.
- Native proposal: `prp-4e715fe7fcac47549a79c3eef3e1f51e`.
- Admitted task: `p0-retained-installed-shared-template-inspection-v1`.
- Task-start baseline:
  `sha256:83ef50d825da41ff7f0b31e968667c119ef79200e87cacfb62fcbe266e9197b5`.

The already retained `setuptools 84.0.0` wheel was the sole candidate and
matched expected SHA-256
`51a52592b3b99e102b609654876bd65f19f999935166d1352678931132b0c670`
before the one task root was created.

## Observed run

| Observation | Result |
| --- | --- |
| Repository `HEAD` preflight | matched task-start head |
| Retained backend candidates / digest matches | 1 / 1 |
| Current distribution overlays | exact expected set of 7 |
| Overlay source/stage digest matches | 7 |
| Task roots created | 1 |
| Longest projected target / limit | 207 / 240 characters |
| Committed regular files archived | 747 |
| Exact committed distribution inputs | 199 |
| Build-backend install attempts | 1 |
| Wheel-build attempts / retries | 1 / 0 |
| Wheels produced | 1 |
| Wheel SHA-256 | `145c785d35e077438b383f6cc20a92a7b4c92b9cc95a8b232301f93b68584d87` |
| Wheel members | 188 |
| Wheel member-inventory SHA-256 | `6ca19e08b0658442eab2616ec25f260265ddfcc8fed734e50a0e47f54fbd05da` |
| Runtime creations / install attempts | 1 / 1 |
| Install and installed-version gate | passed |
| Repairs / substitutions | 0 / 0 |
| Network calls / model calls | 0 / 0 |
| Rehearsal v2 started | no |

The wheel member count and canonical inventory digest exactly match the prior
successful short-root build. That observation shows package output inventory
stability for this run; it does not excuse the broader input staging.

## Separated shared-template gates

| Gate | Result | Evidence meaning |
| --- | --- | --- |
| Exact wheel member | **PASS**: exactly one `.data/data/share/.../example-capability.input.schema.template.json` member | The wheel carries the intended member under the `data` key. |
| Wheel member versus source | **PASS** | The wheel member SHA-256 matches the staged exact-current source template. |
| Actual runtime data scheme | **PASS**: `scheme.data` equals the fresh runtime root | The normalized installed target is `scheme.data/share/agent-governance-starter/templates/example-capability.input.schema.template.json`. |
| Installed-file presence | **PASS** | The exact regular, non-link installed template exists at the scheme-derived target. |
| Source versus installed bytes | **PASS** | Source and installed template SHA-256 both equal `e596a428f37f914c6652d650c36df7a47261d6d75118858b6a6ebf99abd91fd6`. |

The earlier combined gate can now be interpreted as a driver-observability
problem rather than current evidence of a missing or byte-different installed
template. This remains a local Python 3.11 / pip 24.0 / setuptools 84.0.0
result, not a cross-version or released-artifact guarantee.

## First retained deviation

The driver used `git archive HEAD` without the exact distribution pathspec.
Read-only post-result classification confirmed that `HEAD` contains 747
tracked files while the declared package inputs comprise 199 committed files.
The prior protocol's 199 count is therefore reproducible, and the 747 count is
an actual staging-breadth deviation rather than a changed repository size
interpretation.

No second build may correct this within the task. A later review may decide
whether the identical wheel inventory and fully passing installed gates are
sufficient product evidence or whether one separately admitted exact-pathspec
replay is necessary before rehearsal v2.

## Cleanup and authority

The foreground driver paused with the verified short-root object until this
evidence became durable, accepted the one exact cleanup continuation, and
removed the exact root. Cleanup result: **1 created / 1 removed**. The wheel,
build environment, installed runtime, staged source, caches, and temporary
files were removed with that root.

Persisted evidence excludes absolute paths, root token, process identifiers,
raw command output, archive contents, source contents, prompts, responses,
credentials, and host session identities. No product source or packaging
declaration changed. No network, credential, consumer, model, Git mutation,
commit, push, publication, release, deployment, or external write was used or
authorized.

## Validation

- all 7 focused short-root tests passed with 1 platform-limited symbolic-link
  skip;
- the complete supported Python 3.11 suite passed all 1102 tests with 5
  platform-limited skips in 161.963 seconds;
- task governance returned `PASS=3 WARN=1 FAIL=0 ADVISORY=3`;
- repository governance returned `PASS=26 WARN=2 FAIL=0 ADVISORY=4`;
- task JSON parsing and `git diff --check` passed;
- the final task-start scope comparison returned
  `PASS=21 PRESERVED=22 FAIL=0 TOTAL=43`;
- post-cleanup operating-system temporary-root inspection found zero current
  direct children matching the short-root ownership pattern.

Distinct native current-Agent advisory review
`srv-77008f76376b004de694dcdd7be14d9b` found the positive installed-template
evidence, single-attempt boundary, evidence-before-cleanup sequence, exact-root
cleanup, repository scope, privacy, and denied authority consistent. It also
classified the 747-versus-199 staging breadth as an unsatisfied task constraint
and did not recommend automatic rehearsal-v2 continuation. This is a separate
self-review pass, not independent assurance. No completion record is claimed
because the admitted source-staging constraint was not satisfied.
