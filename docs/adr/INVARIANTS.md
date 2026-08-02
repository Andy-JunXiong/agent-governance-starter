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

## Development-time governance is the primary product boundary

- Authority: `docs/adr/0009-govern-coding-agents-during-development.md`

### Enforcement points

- Meaningful coding-agent work starts from an admitted requirement and bounded
  task contract before implementation.
- Task context selects relevant architecture, invariants, capabilities,
  controls, evidence, and approval boundaries without presenting unrelated
  repository detail as task-specific guidance.
- Implementation and completion checks compare actual changes and fresh
  evidence with the admitted task while preserving deterministic versus
  advisory semantics.
- PR and CI replay the deterministic facts independently; they are a backstop,
  not the first governance interaction.
- Agent protocols may request a stop but do not gain mechanical runtime, Git,
  merge, release, or deployment authority.

### Verification

- Validate task contracts and changed-file fixtures across passing, incomplete,
  conflicting, advisory, and not-applicable states where supported.
- Confirm local development commands do not modify repository or Git state.
- Confirm CI consumes the same versioned deterministic contract.
- Pilot context relevance and workflow friction with humans; do not infer them
  from structural checks.

### Failure response

Stop implementation on deterministic task-boundary failures. Route requirement
meaning, architecture sufficiency, exceptions, and approval quality to the
accountable human instead of manufacturing a deterministic answer.

## Automated upgrade proposals never authorize merge

- Authority: `docs/adr/0007-separate-upgrade-proposal-from-merge-authority.md`

### Enforcement points

- Upgrade planning is read-only and declares exact before/after hashes.
- Only the two fixed managed consumer workflow paths may be proposed for
  automatic change.
- Customized workflows, incompatible layouts, and unsupported migrations
  block. The named two-workflow bootstrap is review-only because it creates a
  file; automatic writers accept updates only.
- Pull-request creation and merge are separate authorities.
- Proposal writes accept only scheduled or explicitly opted-in dispatch events.
- Pull-request governance remains read-only; FAIL blocks, WARN and ADVISORY are
  visible but non-blocking, and owner trend/upgrade information is excluded
  from the PR-author surface.
- Regression delivery may fail a trusted default-branch notification job but
  cannot comment, open issues, modify contents, merge, release, or deploy.
- Authority: `docs/adr/0008-deliver-findings-by-persona-without-pr-write-authority.md`
- Existing branches and PRs are reused only when their diff is exactly the
  planned managed workflow set.

### Verification

- Validate the upgrade PR plan schema and fixture states.
- Confirm every authority flag is false in a dry-run plan.
- Confirm result contracts deny merge, release, deploy, and production authority.
- Inspect the proposal job's two write permissions before enabling it.

### Failure response

Stop automatic proposal creation and route the conflict or migration to the
consumer repository owner.
