# Minimal noninteractive artifact driver v1

Date: 2026-08-26

## Outcome

Human-admitted task `p0-minimal-noninteractive-artifact-driver-v1` implements
one lightweight repository-internal driver that composes the existing
manifest preflight, verified short-root allocation, explicit evidence receipt,
and evidence-gated cleanup contracts. It invokes one injected fixture action
at most once and has no public CLI or installed-package surface.

Resolved alignment journey `mcpj-3db912cb51964c5782430d651c223a41`
records the product owner's selection of the minimal-driver direction. Native
proposal `prp-dcfd28255d964c43b7773589bdb650ba` admitted the exact task, and
the product owner separately instructed take-up. Task-start baseline
`sha256:6d4b19f18acf5144013cc3412783047f7aa04bf6a04756da1150cbcfae46ca47`
was captured before implementation; it does not prove earlier state.

## Deterministic contract

- `run_artifact_replay` validates the repository, manifest reference,
  evidence target, injected action, and existing manifest-check result before
  or at their fail-closed boundary.
- The existing manifest checker must pass before one verified short root can
  be allocated.
- The injected action receives only the `ShortBuildRoot` and is invoked at
  most once. The driver performs no build itself.
- `ArtifactEvidence` hides its text from representations and accepts only
  bounded, non-empty, LF-normalized UTF-8 text without unsupported control
  characters. Semantic sanitization remains caller-owned.
- The evidence target must be normalized and repository-relative beneath an
  existing real parent. Unsafe, linked, escaping, or existing targets fail
  before allocation.
- Evidence uses exclusive create, then flush and `fsync`, before an exact
  canonical SHA-256 is supplied to `create_evidence_receipt`.
- Gated cleanup runs only after receipt creation. Success requires evidence
  revalidation, exact-root removal, and observed root absence.
- The driver has no prompt, stdin read, TTY branch, retry, repair, scheduler,
  backend selection, network path, public CLI, or external authority.

## Failure and privacy boundary

Manifest, allocation, action, evidence, receipt, and cleanup failures map to
bounded reason codes without raw exceptions. A failure report contains only
counts, booleans, the reason code, contract identity, and denied authority.
Host paths, evidence contents, and callback exception text are excluded.

Before validated evidence authorizes removal, failures preserve the exact root
and record no cleanup success. The private recovery handle exists only for a
separately controlled cleanup step; the driver does not bypass the evidence
gate during failure handling.

## Validation

Initial implementation validation passes all 12 driver fixture tests with one
Windows privilege-limited directory-link skip. Covered behavior includes one
action attempt, closed, redirected, and TTY-reported input, pre-allocation
manifest and evidence gates, exclusive-create race handling, exact digest
binding, `fsync` before receipt and cleanup, changed evidence, write, receipt,
and cleanup failures, root preservation, privacy-bounded reports, and absence
of a public CLI.

Formal validation passes. All 24 focused driver and short-root tests pass with
3 Windows privilege-limited symbolic-link skips. All 55 user-documentation
tests pass. The complete supported Python 3.11 suite passes all 1102 tests with
5 platform-limited skips in 167.903 seconds.

Task governance is `PASS=3 WARN=1 FAIL=0 ADVISORY=3`; repository governance is
`PASS=26 WARN=2 FAIL=0 ADVISORY=4`. Task JSON, privacy, zero-short-root,
`git diff --check`, and trailing-whitespace checks pass. Final task-start scope
is `PASS=10 PRESERVED=3 FAIL=0 TOTAL=13`; all seven post-capture paths are the
admitted implementation and closeout paths. The prior replay evidence, prior
task record, and local MCP configuration remain byte-identical.

Distinct native current-Agent advisory review
`srv-d5527863960da8481216eeb9820e332d` found the selected requirement,
internal composition architecture, one-action and evidence-before-cleanup
sequencing, scope preservation, privacy boundary, and denied authority
consistent. It retained future real-caller observation fields,
recovery/concurrency needs, cross-platform adversarial replacement, and
semantic evidence completeness as unknowns. This is a separate self-review
pass, not independent assurance. The native task-completion-record tool is not
exposed in this session, so no completion record is claimed or fabricated.

## Authority and unknowns

No real artifact or wheel build, retained backend, dependency installation,
network request, public CLI, installed package, external Agent, model,
consumer form, credential, Git mutation, publication, release, deployment,
scheduling, retry, repair, or full journey was used or authorized.

Future real-action metadata, repeated reliability, concurrent recovery,
cross-platform filesystem behavior, adoption, time savings, causal benefit,
return on investment, and whether a public surface is ever warranted remain
unknown.
