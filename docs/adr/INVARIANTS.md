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
