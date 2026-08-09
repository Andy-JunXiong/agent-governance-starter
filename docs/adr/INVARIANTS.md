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

## Capability availability and transport permission do not grant authority

- Authority: `AGENTS.md`, `docs/adr/0009-govern-coding-agents-during-development.md`, and `docs/adr/0015-use-mcp-elicitation-for-codex-task-admission.md`

### Enforcement points

- Advertising a command, MCP tool, hook, API, or interaction does not admit a
  task or authorize its consequential effect.
- A governed transition binds the applicable state, required evidence,
  permission or decision, and responsible authority; stale or mismatched
  bindings fail closed.
- Deterministic structural validity, advisory reasoning, and human authority
  remain separate. None is silently promoted into another.
- When AgentGov does not mediate a host capability, it must not claim that the
  capability is mechanically governed or that AgentGov is a runtime security
  boundary.

### Verification

- Confirm write-capable adapters require their declared authority, decision
  when applicable, and revalidation sequence after ordinary transport or tool
  permission.
- Confirm missing, declined, stale, malformed, or mismatched decisions cannot
  apply the governed transition.
- Review product claims and diagrams for any implication that optional AgentGov
  tool selection intercepts unrelated host tools.

### Failure response

Stop the consequential transition or narrow the product claim. A new runtime
mediation or enforcement boundary requires a separate ADR, authority model,
threat model, and validation; it is not inferred from the current MCP Adapter.

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

## The primary user journey is automatic and interruption-minimal

- Authority: `docs/adr/0013-make-automatic-governance-and-dashboard-primary.md`

### Enforcement points

- Ordinary users interact through their coding agent and a concise approval
  and Dashboard surface rather than composing lifecycle commands or internal
  JSON.
- Repository observation, context routing, declared checks, evidence
  reconciliation, and Dashboard refresh are automatic after activation.
- Human interruption is reserved for material scope, architecture, exception,
  unapproved execution, semantic judgment, or consequential authority.
- Periodic drift-review cadence may be deterministic, but requirement,
  architecture, and functionality conclusions remain advisory. A reminder is
  non-blocking and cannot manufacture an external notification-write authority.
- `next`, `govern start/check/finish`, Monitor generation, and handoff remain
  supported internal, headless, diagnostic, CI, testing, and recovery
  interfaces rather than the intended primary daily journey.
- Benefit views distinguish observed facts, reproduced comparisons, supported
  inference, human feedback, and unknowns; they do not manufacture a score.

### Verification

- Exercise one complete low-risk task through the automatic product surface
  without hand-authored internal JSON, repeated state queries, manual lifecycle
  command composition, or special confirmation words.
- Confirm adapters cannot grant scope expansion, exceptions, external writes,
  commit, merge, release, or deployment authority.
- Confirm Dashboard data derives from validated events and does not become a
  second governance source of truth.
- Pilot interruption burden, context relevance, protection usefulness, and
  benefit claim honesty with humans.

### Failure response

Treat a return to command-driven daily use, hidden authority, consumer-specific
Core policy, or unsupported benefit claims as product architecture drift. Keep
the low-level interface available for recovery while correcting the primary
automatic journey.
