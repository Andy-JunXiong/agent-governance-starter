# ADR-0013: Make automatic governance and the Dashboard the primary experience

Status: Accepted

Date: 2026-08-05

Implementation status: not yet implemented as the primary product experience.

## Decision gate

Should AgentGov expose its lifecycle primarily as a sequence of commands that
the user must query and execute, or should it automatically coordinate the
governed coding-agent session and reserve human interaction for real authority
and semantic decision boundaries?

## Context

ADR-0009 made development-time coding-agent governance the product core.
Development source subsequently implemented task admission, repository context,
changed-file scope, fresh evidence, completion reconciliation, immutable local
events, Monitor, handoff, and read-only `next` routing.

Those primitives prove the core semantics, but their current user journey
still exposes internal state transitions. A user must understand and compose
`next`, `govern start`, `govern check`, `govern finish`, Monitor, and handoff.
Exact terminal confirmation words protect headless writes but are not an
acceptable primary software experience. This contradicts the approved
productization constraint that ordinary users should not hand-author internal
JSON, understand Registry internals, poll workflow state, or assemble low-level
commands.

The static Monitor also proves that privacy-bounded events can create a
reviewable local read model. It does not yet provide an automatically refreshed
product Dashboard for live sessions, protection events, benefit evidence, and
learning.

## Decision

Make event-driven automatic orchestration and an automatically updated Monitor
and Dashboard the primary AgentGov product experience.

The target journey is:

```text
Human requests work through a coding agent
  -> adapter emits a vendor-neutral task event
  -> AgentGov drafts or resolves the governed task and relevant context
  -> one bounded confirmation occurs only when policy requires it
  -> AgentGov observes scope and evidence automatically during work
  -> completion triggers approved validation and reconciliation
  -> Dashboard explains protection, evidence, benefit, and unknowns
  -> a human retains semantic acceptance and consequential authority
```

The normal low-risk journey must not require hand-authored internal JSON,
special confirmation words, repeated `next` queries, or manual lifecycle
command composition.

Implement the first automatic coordinator as an explicit foreground process or
adapter-owned session, not a hidden system daemon. Its placeholder entry point
is `agentgov dev`; the final name and UI are not owned by this ADR.

Existing commands remain supported as internal primitives and as headless,
diagnostic, CI, testing, and recovery interfaces. ADR-0010's read-only `next`
router remains a safe fallback and state-machine oracle, but it is no longer
the intended primary daily user interaction.

Automatic behavior may inspect repository state, select declared context, run
deterministic checks, execute repository-declared pre-approved validation,
record disclosed privacy-bounded local events, update the Dashboard, and return
findings to the coding-agent adapter. It may not infer authority to expand
scope, approve exceptions, execute unapproved commands, write external systems,
commit, push, merge, publish, release, deploy, or perform production actions.

Human interruption is reserved for ambiguous or material scope, requirement or
architecture expansion, exceptions, unapproved execution, unresolved semantic
or high-risk judgment, and consequential external transitions. Normal product
confirmation should be a concise card, button, or adapter approval event;
exact terminal words remain a fallback where no richer approval surface exists.

The Dashboard is a core product surface with Overview, Live Sessions,
Protection Events, Task Detail, Benefit, and Learning views. It remains a read
model and must distinguish observed facts, reproduced comparisons, supported
inferences, human feedback, and unknowns. No single governance, protection, or
benefit score may be published without a documented denominator,
applicability, and comparison model.

Core events, state transitions, findings, benefit semantics, and Dashboard data
remain vendor-neutral. Codex, Claude Code, IDE, and other integrations are
optional adapters. Host state is not governance authority. NYC and other
consumer projects provide usage feedback but do not contribute project-specific
paths, policy, data, workflows, or business concepts to Core.

Semantic interpretation follows the same separation. AgentGov Core remains
model-free and routes semantic review through a vendor-neutral host
Provider. Medium-risk review defaults to the active Coding Agent performing a
structured separate pass or isolated-context self-review with the user's
existing entitlement and no new setup. High-risk review may use a user- or
organization-provided independent Reviewer with at least separate context;
different model or provider raises the disclosed independence level but does
not create objective truth.

If an independent Reviewer is required but unavailable, the product offers
human review, an explicitly labeled lower-assurance same-agent review, or
Provider setup. It never silently downgrades or makes a second model mandatory
for installation and ordinary work. Credentials, cost, retention, and external
transfer remain owned by the configured user/organization Provider or a future
separately approved hosted service. Every LLM finding remains advisory and
cannot select a direction or gain project or external-write authority.

ADR-0014 now owns the implemented Provider-capability, risk-route, and
advisory-result contracts. This ADR continues to own the broader automatic
product journey; it does not imply that a production model materializer exists.

The detailed approved requirements are owned by
`docs/product-requirements-automatic-governance.md`.

## Owns

- the automatic, interruption-minimal primary user journey;
- the foreground-or-adapter orchestration boundary;
- the role of low-level commands and `next` as internal or fallback surfaces;
- automatic versus human-gated action classes;
- the Monitor and Dashboard as a core product surface;
- benefit claim semantics and denominator requirements;
- vendor-neutral Core and consumer/adapter separation;
- the gate that general automatic rehearsal precedes NYC feedback use.

## Does not own

- the final CLI command, desktop, IDE, terminal, or web UI design;
- a hidden daemon, hostile-agent security sandbox, or mechanical process
  termination;
- automatic semantic interpretation of arbitrary requirements;
- automatic exception, merge, release, deployment, or production authority;
- central telemetry, SaaS hosting, or automatic local-state upload;
- a general claim-verification or token-cost subsystem;
- NYC, AI Radar, or another consumer's business policy or workflow.

## Consequences

- the current manual development commands are explicitly development and
  fallback interfaces rather than the final product journey;
- `next` becomes an internal routing oracle and safe recovery surface instead
  of the product center;
- trigger, adapter, foreground orchestration, approval, and Dashboard contracts
  require new bounded implementation slices;
- the NYC shadow pilot moves after an independent automatic-experience
  rehearsal;
- current stable 0.2.1 and published 0.3.0rc1 behavior remain unchanged;
- future public surfaces must distinguish implemented behavior from this
  accepted product direction.

## Alternatives considered

### Keep the command sequence as the primary experience

Rejected. It exposes internal state and makes the user repeatedly ask the tool
what to do instead of governing the coding agent automatically.

### Build a hidden background daemon first

Rejected. It adds lifecycle, installation, trust, and termination authority
before a foreground automatic session and adapter contract are proven.

### Make one coding-agent vendor the Core runtime

Rejected. It would make host configuration a product authority and weaken
portability. Vendor integration belongs in optional adapters.

### Show one governance or benefit score

Rejected. It would combine inapplicable controls, deterministic findings,
human judgment, and unsupported causal claims into false precision.

## Implementation order

1. Refactor the implemented lifecycle into an internal state-machine service
   without changing current CLI results.
2. Define versioned vendor-neutral trigger and adapter contracts.
3. Implement one explicit foreground orchestrator using the existing checks,
   event store, evidence, Monitor, and authority boundaries.
4. Add bounded approval events and keep exact terminal words as fallback.
5. Add automatically refreshed Live Sessions and Protection Events views.
6. Add denominator-aware Benefit and Learning views.
7. Run an exact-artifact, independent, non-NYC automatic user-journey rehearsal.
8. Run the first NYC low-risk shadow pilot only after that gate passes.
9. Admit only general feedback into AgentGov; replay every accepted change in
   both the independent fixture and consumer pilot before stable promotion.

## Implementation notes — 2026-08-05

- `agentgov.development-state` 1.0 now projects active-session events and backs
  the existing `next` lifecycle routing.
- `agentgov.development-trigger` 1.0 defines the vendor-neutral event envelope;
  scope decisions and session review require human-originated records.
- `agentgov.foreground-cycle` 1.0 and `agentgov dev` now implement one explicit
  foreground cycle through the minimal reference adapter.
- `implementation.changed` derives actual Git paths and records scope;
  `completion.requested` blocks on scope failure or runs only admitted
  validation before reconciliation; every completed cycle refreshes the local
  Dashboard.
- Monitor 1.4 exposes Live Sessions and Protection Events. Resolution remains
  unknown without explicit cross-event links.
- A live coding-agent transport, natural-language task drafting/admission,
  visual cards, persistent foreground session, Benefit/Learning views, and the
  independent automatic journey remain unimplemented. Therefore the accepted
  primary experience is still incomplete and no stable/RC behavior changes.

## Implementation notes — 2026-08-06

- `agentgov.coding-agent-event` 1.0 now provides a strict host-process JSONL
  envelope. It cannot carry raw prompts, source, host paths, changed-path or
  task-identity claims, or consequential authority.
- `agentgov dev --stream` keeps one disclosed foreground process open for
  several events and returns one structured response per accepted event. It is
  not a daemon and does not upload local state.
- The reference adapter derives working-copy identity, active task identity,
  and Git changes locally before invoking the existing trigger/coordinator
  path. Invalid records stop at their input line before coordinator action.
- `agentgov.interaction-card` 1.0 provides bounded task, scope, and completion cards.
  Card actions remain offers for human or host handling and apply no scope,
  exception, commit, merge, release, or deployment authority.
- The first packaged Codex lifecycle-hook Adapter maps `SessionStart`,
  `UserPromptSubmit`, `PostToolUse`, and `Stop` into those vendor-neutral
  events. Sensitive hook fields are discarded before event construction.
- Codex project-hook integration is create-missing-only, requires exact
  interactive confirmation, refuses overwrite/merge, and leaves trust review
  to the user. `PostToolUse` cannot undo completed effects and repeated `Stop`
  continuation is bounded by `stop_hook_active`.
- `agentgov.host-interaction-capabilities` 1.0 and
  `agentgov.host-interaction-request` 1.0 keep presentation and decision
  recording vendor-neutral. A request has no decision or consequential
  authority merely because a host displays it.
- `agentgov.human-decision-prompt` and `agentgov.human-decision-result` 1.0 now
  bind one proactive no-free-text choice to the exact source and predeclared
  transition. The reference review accepts one number; safe recommendations
  are never selected automatically.
- The Codex binding declares custom task, scope, and completion gates as
  context-only because current Hooks provide no arbitrary button or trusted
  custom-decision callback. `PermissionRequest` leaves the ordinary Codex
  human tool prompt undecided and is not treated as governance approval.
- Vendor-neutral alignment-context and clarification-dialogue contracts now
  keep substantive multi-turn discussion separate from final governance
  decisions. They preserve the current center, mark business, requirement, and
  architecture drift advisory, ask one natural-language question per turn,
  retain only normalized rolling summaries, and reuse the existing
  single-select result only after material unknowns and option instability are
  resolved. Discussion or resolution grants no project-change authority.
- The disclosed foreground Coding Agent stream now dispatches those strict
  normalized contexts, human clarification updates, and final results. It
  automatically returns exactly one next prompt through
  `agentgov.coding-agent-alignment-response` 1.0, keeps state in memory only,
  declares that it does not survive restart, and does not invoke a development
  coordinator cycle for alignment-only records.
- A host-side reference Alignment Adapter now accepts ordinary request and
  answer text, delegates interpretation through a replaceable semantic
  materializer, constructs the strict Core records, and records one final host
  selection. Its privacy-safe offline rehearsal reports zero user-authored
  JSON or internal commands; it does not add semantic inference to Core.
- Natural-language task drafting, production host semantic materializers, a
  native authenticated custom-decision surface,
  explicit protection resolution, Benefit/Learning views, additional host
  adapters, and the independent journey remain unimplemented. Stable 0.2.1 and
  immutable `v0.3.0rc1` are unchanged.

## Validation

Deterministic validation must cover event ordering, idempotence, adapter input,
state-machine transitions, allowed automatic actions, denied authority,
privacy and path safety, Dashboard serialization, no hidden external requests,
and unchanged behavior for existing CLI fixtures.

Scenario validation must prove that one ordinary low-risk task can reach a
reviewable completion with no hand-authored internal JSON, no repeated status
queries, no manual lifecycle command composition, and no special confirmation
words in the primary UI. Human review must assess task-card clarity, context
relevance, interruption burden, protection usefulness, and benefit honesty.

## Relationship to prior decisions

This ADR refines ADR-0009's product interface without changing its development
governance, deterministic/advisory, or human-authority boundaries. It repositions
ADR-0010's `next` router as a fallback and internal oracle. It preserves
ADR-0012's distinction between verified completion, handoff, and semantic
acceptance while replacing routine manual handoff interaction in richer product
surfaces with a bounded approval event.

## Rollback or replacement

A later decision may replace the foreground process or adapter UI after real
use, but it must preserve vendor-neutral Core contracts, repository-owned
authority, deterministic/advisory separation, evidence honesty, privacy,
fallback diagnostics, and explicit human control of consequential transitions.
