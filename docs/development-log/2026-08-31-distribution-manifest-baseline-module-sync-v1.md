# Distribution manifest baseline-module synchronization v1 - 2026-08-31

## Goal and boundaries

Restore the exact current distribution-input contract after independent
automatic-journey rehearsal v3 found that the newly packaged task-start
baseline module was absent from the persisted manifest. Keep the existing
derivation architecture and controller request contract. Do not build an
artifact, retry v3, start v4, rewrite historical 186-path evidence, or perform
network, Git, publication, release, deployment, or external actions.

## Human direction and admission

Resolved alignment journey `mcpj-c65f17a515b04eaba7080c8682e09df4`
recorded the product owner's selection of the coherent minimal repair. Native
proposal `prp-e24721b244fe4c648b5180f2c84c0e93` admitted task
`p0-distribution-manifest-baseline-module-sync-v1`; the product owner then
supplied exact `REPLACE`. Current-source session start captured baseline
`sha256:ac4fbb4b3ebab05cc8ce283081c8ea3a37580ca32fe5023e5a479a72ece8af6e`
before implementation writes.

## Implemented vertical slice

- Added `src/agentgov/task_start_scope_baseline.py` once at its sorted location
  in the durable manifest.
- Refreshed the manifest to 187 paths with canonical path identity
  `sha256:79839fec9be5dfb8bb30c41e74a0d8a9a6a11b3587001af6395f7f1b7c506e9a`
  and content identity
  `sha256:a695fb5afcaadcc2f3382a7a878d4e182070539d61b5e39a0ea663b00874a96c`.
- Updated the fixed artifact replay controller to require the same count and
  identities.
- Updated the focused controller source-transport expectation from 186 to 187.

No manifest derivation rule, schema, controller request shape, authority flag,
retry behavior, build action, cleanup behavior, privacy boundary, package
source, or historical evidence changed.

## Validation

Fresh manifest comparison passes with 187 committed inputs, zero differences,
zero tracked deltas, and zero untracked overlays. The focused manifest and
controller suites pass all 19 tests with one Windows privilege-limited
symbolic-link skip. The full suite passes all 1,134 tests with six
platform-conditioned skips. Task governance reports `PASS=3`, `WARN=1`,
`FAIL=0`, `ADVISORY=3`; repository governance reports `PASS=26`, `WARN=2`,
`FAIL=0`, `ADVISORY=4`. The task-start scope check preserves every declared
pre-existing exclusion and limits the new delta to admitted paths. Task JSON
parsing and the diff-whitespace check pass.

Distinct native current-Agent self-review
`srv-45a0e365efa6b83b40b05743175e747b` found the static repair consistent with
the selected direction and preserved the historical-evidence and authority
boundaries. It keeps artifact-build success, automatic consumer-journey
success, and observed user benefit unknown. This is advisory self-review, not
independent assurance or human acceptance. Governed completion reconciliation
used the current-source CLI fallback because the native MCP completion-record
tool was not exposed. Evidence `evd-3384ac3b5e2d49e095948986c0ea8069`
ran all eight task-declared commands with exit code zero and reconciled the
unchanged governed snapshot as `verified`. This deterministic result does not
grant requirement acceptance, Git authority, or downstream authority.

## Product interpretation and next review

This repair restores the deterministic gate that blocked v3; it does not prove
that a 187-path wheel builds or that the automatic consumer journey succeeds.
Historical 186-path records remain accurate observations of earlier runs.

The next product review may decide whether one newly admitted v4 rehearsal is
warranted. This suggestion grants no replay, task, model, Git, publication,
release, deployment, or external authority.
