# ADR-0008: Deliver findings by persona without PR write authority

## Status

Accepted for the 0.3 release candidate.

## Context

Pull-request authors need the delta introduced by their change and a concrete
next action. Repository owners need default-branch trend, baseline, benefit,
and upgrade administration. Combining both audiences in one Actions Summary
hides actionable PR findings and makes the owner dashboard noisy.

GitHub also has no direct four-state mapping for AgentGov PASS, WARN, FAIL, and
ADVISORY findings. Granting comment or issue write permission to a workflow
that executes pull-request content would increase the trust surface, especially
for same-repository pull requests that can propose workflow changes.

## Decision

- Pull-request summaries contain only current findings, baseline-relative
  transitions, and author/reviewer actions. They exclude trend and upgrade
  administration.
- Default-branch and scheduled summaries contain repository health, benefit
  history, and upgrade state.
- FAIL emits an error annotation and fails the deterministic governance gate.
- WARN and ADVISORY emit warning annotations and remain non-blocking.
- The pull-request path receives no write permission and creates no PR comment.
- The Draft PR writer is rendered into a separate
  `.github/workflows/agentgov-upgrade.yml` workflow that has no `pull_request`
  or `push` trigger; the PR governance workflow contains no write-permission job.
- A trusted default-branch regression or mixed change makes a separate
  read-only job fail, allowing GitHub's normal Actions failure notification and
  workflow badge to push the state without repository or issue writes.
- Diagnostic monitor states remain precise, while the user surface maps them
  to `missing`, `unchanged`, `improved`, or `needs_review`.

## Consequences

The PR author sees fewer administrative details and can distinguish blocking
from non-blocking findings. Owners receive a visible red default-branch signal
for a new regression. Notification delivery still depends on GitHub account
notification settings; adding comments, issues, chat, or email adapters later
requires a separate trusted workflow and explicit authority review.

No result authorizes merge, release, deployment, or production execution.
