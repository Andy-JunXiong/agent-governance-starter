---
layout: reference
title: "Drift review reminders"
source_path: docs/drift-review-reminders.md
---

# Drift review reminders

## Status

Development source implements the shared cadence and foreground reminder for a
future AgentGov release. A future-version managed GitHub Actions renderer also
contains the scheduled read-only reminder step. Published stable `0.2.1` and
Pre-release `v0.3.0rc1` workflow output are intentionally unchanged.

This feature is a reminder and evidence-routing surface. It is not an automatic
semantic judge and it is not a hidden background service.

## Shared cadence

AgentGov checks the same repository policy in foreground and CI contexts:

- review after three distinct verified task completions; or
- review seven days after the last confirmed review;
- a confirmed snooze defers the reminder for seven days.

The first review is due when no confirmed baseline exists. New scaffolds place
the strict policy at `governance/drift-review-policy.json`; repositories created
before this feature receive the same built-in defaults without an automatic
repository write.

Only the due calculation is deterministic. The requested review covers
`requirement`, `architecture`, and `functionality`, and every conclusion remains
`ADVISORY`. “No drift evidence observed” never means that AgentGov proved the
absence of drift.

## User journey

Inspect the current status without writing:

```powershell
agentgov review drift .
agentgov review drift . --format json
```

When due, an active foreground cycle adds a non-blocking drift card only when a
higher-priority task, scope, or completion card is not already occupying the
interaction surface. The user can ask the current coding agent to perform an
evidence-bounded advisory review, or snooze the reminder. The Monitor keeps the
due state visible even when another decision card takes priority.

Development Adapter `1.4.0` now connects that card to the capability-gated
`agentgov_drift_review_record` MCP tool. The current Agent supplies one
normalized advisory candidate, exactly one observation for each of
`requirement`, `architecture`, and `functionality`, and repository-relative
evidence references. It cannot supply the human decision. A form-capable host
then displays the exact candidate and offers only: record it, snooze for the
configured interval, or create no record. The Adapter revalidates that the
same cadence state is still due before any create-only write. Clients that do
not negotiate native form elicitation never discover this write-capable tool.

After a successful record or snooze, the tool returns the refreshed shared
status and refreshes the AgentGov-owned local Monitor. A Monitor refresh failure
is reported separately after preserving the successful immutable record, so a
host does not invite a duplicate retry. This native form is implemented in
development source and installed only in the existing local AgentGov pipx
runtime. It remains unpublished and consumer-inactive. One bounded direct App
Server replay reached its form request and stopped without a human decision or
record; live Agent selection and end-user UI presentation remain unproven.

The headless fallback previews an immutable record before writing it:

```powershell
agentgov review drift . --record-outcome no_drift_evidence
agentgov review drift . --record-outcome candidate_drift
agentgov review drift . --record-outcome insufficient_evidence
agentgov review drift . --snooze
```

Add `--apply` to preview the exact JSON and then confirm `RECORD` in a real
interactive terminal. Redirected and non-interactive input cannot authorize the
write. Apply creates one new file under `governance/drift-reviews/`; it does not
overwrite an earlier record, commit it, change scope, or approve any transition.
A rich host may map the same human selection to this create-only operation
without asking users to compose a fallback command. The record's
`actor_class: human` is a declared provenance field, not cryptographic identity
proof; host authentication remains outside this contract.

## Scheduled CI reminder

The future-version managed workflow runs this read-only command on its existing
schedule:

```bash
agentgov review drift . --format github
```

When review is due, the command emits a GitHub warning annotation and Markdown
job summary but exits successfully. The job stays green because an advisory
reminder is not a deterministic failure. It does not open an issue, send email
or chat messages, comment on a pull request, or request write permission.

CI sees tracked policy and review records plus only the governance events
available in that checkout. Therefore the seven-day threshold is portable;
the three-task threshold may have more complete evidence in the local
foreground session. The status declares its history scope rather than treating
missing local events as proof that no task occurred.

## Monitor and authority boundary

Development Monitor contract 1.5 displays the due state, reason codes,
dimensions, evidence limits, and the advisory boundary. It does not claim that
the user read, acknowledged, or resolved the reminder.

Neither status calculation nor a recorded review authorizes requirement or ADR
edits, scope expansion, exceptions, commits, merges, publication, release, or
deployment. A true out-of-session push notification would require a separately
approved external channel. A hidden daemon remains outside ADR-0013.
