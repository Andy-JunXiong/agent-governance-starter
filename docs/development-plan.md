# AgentGov remaining development plan

Updated 2026-08-02. This page separates implemented development-source behavior
from published and consumer-adopted behavior.

## Current checkpoint

- Published stable: AgentGov 0.2.1.
- NYC consumer: managed 0.2.1 workflow.
- Implemented locally for the future 0.3 line: persona-aware PR and owner UI,
  trusted-main benefit monitor, scheduled baseline refresh, redacted portable
  evidence, separate bounded Draft PR workflow, and pre-write current/target
  dry-run evidence.
- Not yet completed: 0.3 versioning, release-candidate review and publication,
  NYC 0.3 migration, or evidence from real NYC runs.

## Ordered work

### P0 — close the 0.3 delivery slice

1. Finish contract and fixture review for the generated two-workflow layout.
2. Add a migration-declared 0.3 release manifest and release notes.
3. Build the 0.3 candidate and run the portable AgentGov/NYC release review.
4. Generate the consumer-local NYC migration review with the exact workflow and
   permission diff.
5. Replay selected historical NYC changes as the pre-release case-study gate.
6. Obtain human RC approval before tag, publication, or NYC migration.

Acceptance signals:

- complete source tests and repository check pass with no deterministic failure;
- legacy 0.1/0.2 managed workflows retain their declared compatibility;
- current/target dry-run reports and digests are present before any Draft PR;
- generated evidence contains no runner home, credential, or token value;
- NYC review stays inside NYC and requests only the declared workflow changes.

Stop conditions:

- undeclared repository migration, permission expansion, remote drift, report
  identity mismatch, deterministic regression, or missing human approval.

### P1 — shift governance into the development loop

1. Specify a minimal task-context and changed-files contract.
2. Implement a read-only local development check with stable JSON and concise
   Markdown output.
3. Map relevant capabilities, controls, dependencies, evaluation evidence, and
   approval boundaries to the proposed change.
4. Distinguish deterministic blockers from advisory review prompts.
5. Expose the contract for coding agents without coupling it to one IDE or AI
   provider.
6. Validate it against NYC changes before adding pre-commit or watch mode.

Acceptance signals:

- a developer receives relevant constraints before opening a PR;
- no repository file or Git state is changed by the read-only command;
- the same deterministic facts can be reproduced in CI;
- irrelevant repository-wide detail is not presented as task-specific advice.

### P2 — prove delivery and benefit in NYC

1. Human-review and merge the one-time 0.3 migration in NYC after stable release.
2. Confirm the first trusted-main run establishes `baseline_missing` without a
   trend claim.
3. Confirm a later scheduled or main run restores the exact baseline.
4. Exercise one real NYC change, or the approved historical replay, through both
   local development and PR surfaces.
5. Record findings, user actions, false positives, and evidence limitations in
   the NYC case study.
6. Decide whether owner push notifications need additional write authority.

Acceptance signals:

- PR authors and project owners receive different, action-relevant summaries;
- WARN remains visible and non-blocking while deterministic FAIL blocks;
- a trusted-main regression reaches the owner through the documented channel;
- `unchanged` is reported honestly and no business-code benefit is inferred
  from a workflow-only upgrade.

### P3 — harden only from observed use

- add notification deduplication or acknowledgement only if NYC evidence shows
  the read-only channel is insufficient;
- consider a GitHub App only with a documented authority and threat model;
- extend retention or export only when a real low-activity history need is
  demonstrated;
- add integrations only when they preserve the repo-native CLI and evidence
  contracts.

## Authority boundaries

Development and CI checks may inspect and report. Draft upgrade automation may
propose one bounded change. Commit, merge, release, deployment, production
execution, and any new notification write authority remain separately
human-controlled.

See [open product decisions](open-decisions-2026-08-02.md) for questions that
must be resolved through implementation evidence rather than assumptions.
