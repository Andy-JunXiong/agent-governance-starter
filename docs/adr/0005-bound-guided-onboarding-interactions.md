# ADR-0005: Bound guided onboarding interactions

Status: Accepted

Date: 2026-07-25

## Decision gate

Define the authority, interaction, and result contracts for guided onboarding
before implementing commands that may eventually write repository files.

## Context

Static guides require first-time users to interpret environment health,
adoption state, deterministic findings, and advisory human decisions without
state-dependent help. The first Taxi pilot also showed that an unrelated stale
project `.venv` can be mistaken for an AgentGov prerequisite.

Guidance must not blur read-only diagnosis, planned writes, completed scaffold
creation, and project-specific governance completion.

## Decision

Use three bounded commands:

- `agentgov doctor .` diagnoses the selected path, AgentGov interpreter, Git
  context, Windows path risk, project-environment signals, and adoption state.
- `agentgov onboard .` will sequence inspection, explanation, preview,
  explicit confirmation, create-missing-only adoption, and the first check.
- `agentgov next .` will map current findings to one smallest useful action.

`doctor` and `next` are always read-only. `onboard` defaults to read-only
preview and may write only after an interactive terminal receives explicit
confirmation for the exact target and planned files.

`--non-interactive` never grants write authority. A future non-interactive
write must require a separate explicit flag and a complete conflict-free plan;
this ADR does not authorize or define that flag.

All results distinguish deterministic findings from advisory interpretation.
No command repairs project environments, installs project dependencies, edits
existing governance files, or performs Git and release operations.

## Owns

- Read-only defaults and explicit write-confirmation boundaries.
- Stable `PASS`, `WARN`, `FAIL`, and `ADVISORY` onboarding semantics.
- Machine-readable result contracts for automation.
- Target-path disclosure before any future confirmation.

## Does not own

- Installer selection, which is governed by ADR-0004.
- Project-specific governance decisions.
- Automatic repair of a project `.venv`.
- Commit, push, merge, publication, release, or deployment.

## Consequences

- `doctor` can be implemented and tested without a terminal.
- Redirected input cannot accidentally authorize writes.
- A stale project environment is visible but is not a deterministic AgentGov
  failure when the isolated AgentGov interpreter is healthy.
- Future `onboard` work must inject prompt decisions in tests.

## 2026-08-05 development-routing refinement

[ADR-0010](0010-route-next-through-development-lifecycle.md) extends only the
`next` selection portion of this decision across the ADR-0009 development
session. Adoption conflicts, missing scaffold, and deterministic repository
`FAIL` remain first. Strict session/event state then selects `govern start`,
`govern check`, `govern finish`, or `monitor development`; repository `WARN`
and `ADVISORY` remain visible through checks and reports but no longer displace
the active daily route. `next` remains read-only and never executes the command.

## Implementation plan

1. Implement read-only `doctor` with text and strict JSON output.
2. Implement `onboard --dry-run` without write authority. Completed on
   2026-07-25.
3. Add injectable explicit confirmation for interactive adoption. Completed
   on 2026-07-25.
4. Implement deterministic finding-to-action mapping for `next`. Completed on
   2026-07-25.
5. Rehearse the complete flow without live coaching.

## Validation

Fixture-based tests cover a healthy repository, an unconfigured repository,
governance conflicts, stale project-environment signals, Windows path risk,
JSON purity, stable exit codes, and the no-write authority boundary.

Human review remains necessary to judge whether diagnostic recommendations
fit the repository and whether later adoption should proceed.

## Rollback or replacement

A later ADR may refine interaction details after pilot evidence. It must retain
read-only defaults, explicit target disclosure, injectable decisions, stable
non-interactive behavior, and separate human authority for high-risk actions.
