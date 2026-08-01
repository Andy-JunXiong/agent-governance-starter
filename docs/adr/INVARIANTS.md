# Repository Governance Invariants

## Deterministic and advisory findings remain distinct

- Authority: `AGENTS.md`

### Enforcement points

- Repository findings use `PASS`, `WARN`, `FAIL`, or `ADVISORY`.
- Deterministic contract violations may fail automation.
- Advisory judgment is not presented as an objective failure.

### Verification

- Run the complete unit-test suite.
- Run `python -m agentgov check repository .`.
- Review every non-PASS finding.

### Failure response

Correct deterministic contract violations. Route semantic sufficiency and
human-authority questions to accountable review.

## Successful checks do not authorize external transitions

- Authority: `AGENTS.md`

### Enforcement points

Merge, publication, release, and deployment require separate explicit human
approval.

### Verification

Review CLI and report language and inspect workflow permissions.

### Failure response

Stop the transition and obtain explicit authority.

## Automated upgrade proposals never authorize merge

- Authority: `docs/adr/0007-separate-upgrade-proposal-from-merge-authority.md`

### Enforcement points

- Upgrade planning is read-only and declares exact before/after hashes.
- Only the managed consumer workflow may be proposed for automatic change.
- Customized workflows, incompatible layouts, and declared migrations block.
- Pull-request creation and merge are separate authorities.
- Proposal writes accept only scheduled or explicitly opted-in dispatch events.
- Pull-request governance remains read-only; FAIL blocks, WARN and ADVISORY are
  visible but non-blocking, and owner trend/upgrade information is excluded
  from the PR-author surface.
- Regression delivery may fail a trusted default-branch notification job but
  cannot comment, open issues, modify contents, merge, release, or deploy.
- Authority: `docs/adr/0008-deliver-findings-by-persona-without-pr-write-authority.md`
- Existing branches and PRs are reused only when their diff is exactly the
  managed workflow change.

### Verification

- Validate the upgrade PR plan schema and fixture states.
- Confirm every authority flag is false in a dry-run plan.
- Confirm result contracts deny merge, release, deploy, and production authority.
- Inspect the proposal job's two write permissions before enabling it.

### Failure response

Stop automatic proposal creation and route the conflict or migration to the
consumer repository owner.
