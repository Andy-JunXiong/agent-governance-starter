# ADR-0010: Route next through the guided development lifecycle

Status: Accepted

Date: 2026-08-05

## Decision gate

Extend the read-only `agentgov next` interaction contract from onboarding and
repository findings into the already implemented ADR-0009 development session
without creating another state source or moving write authority into `next`.

## Context

ADR-0005 established that `doctor` and `next` are always read-only and that
`next` selects one smallest useful action. Its first implementation stopped at
adoption state and repository `FAIL`, `WARN`, and `ADVISORY` findings. ADR-0009
later added a strict working-copy session, immutable development events, fresh
evidence, completion reconciliation, and a static Monitor.

Users therefore still had to reconstruct `govern start` → `govern check` →
`govern finish` → `monitor development` themselves. Adding a second progress
file or silently executing those commands would duplicate source of truth and
violate the existing authority boundary.

## Decision

`agentgov next` keeps this deterministic precedence:

1. adoption path conflict;
2. missing required governance scaffold;
3. first deterministic repository `FAIL`;
4. strict development-session and event state.

Repository `WARN` and `ADVISORY` findings remain visible through `check`,
`report`, and `status`, but do not displace the active daily development route.
This is the only precedence change to ADR-0005; its read-only, non-interactive,
and human-authority decisions remain in force.

Development routing derives only from the existing untracked
`.agentgov/current-task.json` pointer, its exact task digest and comparison
base, and validated immutable events at or after the session start:

| Current state | One selected action |
|---|---|
| No active session | Preview `govern start`; choose explicitly when several tasks exist |
| `task.started` | Run `govern check` |
| Latest `scope.checked` passed | Run `govern finish` |
| Latest scope failed | Resolve scope and rerun `govern check` as a blocking action |
| Validation recorded without later reconciliation | Run `govern finish` |
| Completion needs evidence | Run `govern finish` |
| Completion verified | Generate/review `monitor development` |

Malformed or tracked session state, missing matching start events, invalid or
conflicting events, task drift, and unavailable comparison-base identity fail
closed as exactly one blocking action. Older events with the same task identity
do not establish progress for a newer session.

`next` may return a command string, but never executes it, prompts, writes,
repairs state, chooses task meaning, runs validation, or grants implementation,
Git, release, merge, or deployment authority.

## Consequences

- The daily journey has one read-only router without adding a Registry or
  lifecycle state file.
- Existing onboarding conflicts, missing scaffold, and deterministic
  repository failures remain higher-priority safety gates.
- WARN and ADVISORY work remains reviewable but no longer prevents the user
  from seeing the active development step.
- A verified completion continues to recommend the Monitor because Monitor
  generation is a derived read action and does not append a progress event.
- Invalid local state may intentionally return no repair command when no safe,
  deterministic repair exists.

## Rejected alternatives

- Automatically execute the selected command: rejected because selection is
  not write or validation authority.
- Add a separate workflow-stage pointer: rejected as a duplicate source of
  truth that can drift from immutable events.
- Choose among multiple admitted tasks by filename or semantic inference:
  rejected because task choice belongs to human intent.
- Keep WARN and ADVISORY ahead of development routing: rejected because common
  non-blocking gaps would permanently hide the ADR-0009 daily loop.

## Validation

Fixture tests cover adoption and repository-failure precedence, zero/one/many
task discovery, current-session start/check/validation/completion routing,
older-event isolation, scope failure, task drift, missing start events,
malformed session state, JSON purity, exact single-action output, and no-write
authority.

## Relationship to prior decisions

This ADR refines only the `next` action-selection portion of ADR-0005. ADR-0005
continues to own onboarding write confirmation and the rule that `doctor` and
`next` are always read-only. ADR-0009 continues to own development governance,
event evidence, completion semantics, and the Monitor.

ADR-0011 keeps pre-install bootstrap outside the CLI and leaves installed
update inspection on `agentgov update --check`. Update availability does not
enter this precedence model until a reviewed stable artifact and a non-looping
terminal-session handoff contract exist.
