# AgentGov remaining development plan

Updated 2026-08-14. This page separates implemented development-source behavior
from published and consumer-adopted behavior.

## Documentation state contract

This page is a public strategic-plan surface. It owns top-level direction,
priority sequencing, and strategic acceptance or stop conditions; update it
when those change. Current execution facts and validation state belong in the
repository `STATUS.md`, exact task scope and admission belong in
`governance/tasks/`, durable architecture decisions belong in `docs/adr/`, and
append-only session evidence belongs in dated `docs/development-log/` files at
stable paths.

Planning and roadmap text does not authorize a task, implementation, Git
operation, publication, release, deployment, or external action. Documentation
State Separation v1 defines the ownership contract. Historical Documentation
Migration v1 relocates the clearly section-bounded checkpoint passages into a
dated, source-labeled record. Archive automation and any broader migration
remain separate, not-yet-authorized changes.

## Current checkpoint reference

Current release, capability, validation, blocker, and active-slice reality is
owned by the repository [`STATUS.md`](../STATUS.md). The superseded public
checkpoint and next-session narratives previously stored here are preserved,
with their original headings and facts, in the
[2026-08-14 historical migration record](development-log/2026-08-14-historical-migration.md).

The strategic direction remains constrained by ADR-0016's
minimum sufficient Kernel and its separation of Completion Verified from
Bounded Handoff. New
Kernel promotion remains paused until a structured real-consumer
counterexample shows that the current Kernel loses a necessary distinction or
governed outcome.

## Next product review reference

The repository `STATUS.md` owns the next product review. The ordered work below
remains strategic input only and grants no task, Git, publication, release, or
deployment authority.
## Ordered work

### Accepted productization constraint

Final users must not need to hand-author internal JSON, understand Registry
internals, poll workflow state, type special confirmation words, or manually
assemble a chain of low-level commands. GitHub installation, updates,
repository onboarding, task admission, context routing, scope observation,
checks, completion, Monitor, Dashboard, benefit evidence, and handoff must
converge on an event-driven automatic workflow. Human confirmation occurs only
at material scope, architecture, exception, unapproved-execution, semantic, or
consequential authority boundaries. The current low-level commands remain
development, headless, CI, diagnostic, testing, and recovery interfaces, not
the intended final UX. The canonical requirements are in
`docs/product-requirements-automatic-governance.md`.

### P0 — automate the primary product experience

1. Complete extraction of the implemented lifecycle routing behind `next`, `govern start`,
   `govern check`, `govern finish`, Monitor, and handoff into an internal
   state-machine service while preserving current CLI results, exit codes,
   authority flags, and fixture behavior. The active-session projection is
   implemented; no-write work is explicitly not a task-admission gate.
2. Extend the implemented strict, versioned, vendor-neutral trigger and
   minimal reference-adapter contract for
   at least task requested, repository activated, implementation changed,
   scope decision requested, completion requested, validation completed, and
   session reviewed events. The trigger vocabulary and authority boundary are
   implemented; the generic process transport is implemented while packaged
   vendor-specific adapters remain.
3. Extend the implemented explicit one-cycle foreground coordinator
   `agentgov dev`, that consumes adapter events, invokes existing deterministic
   cores, records disclosed local metadata events, refreshes the Dashboard, and
   returns findings without a hidden daemon. One JSONL foreground process can
   now consume several coding-agent events; the first Codex hook integration is
   implemented in development source.
4. Preserve the implemented Codex lifecycle-hook Adapter and add another host
   only when portability evidence requires it. Adapter configuration remains
   replaceable input and never governance authority.
5. Preserve the implemented vendor-neutral host capability, interaction
   request, proactive decision-prompt, and human-result contracts. Capable
   hosts present one recommended single-select choice and carry only its exact
   transition; the reference presenter uses one number without free text.
   Codex Hooks currently provide context-only custom gates; a native
   authenticated button callback remains host productization work. Exact
   `START`, `REPLACE`, and `HANDOFF` text remains only a headless fallback.
6. Preserve the implemented vendor-neutral structured task-proposal and
   human-admission fallback. A Coding Agent proposal grants no authority;
   one proactive numeric approval can create only the exact reviewed low-risk
   task; exact interactive `ADMIT` remains a fallback. The reference
   natural-language-to-proposal Adapter seam is implemented and excludes raw
   conversation data from Core. Codex development source now connects the
   current Agent and native MCP form; install/live proof and other hosts remain
   open.
7. Preserve the implemented risk-based router and friction budget. No-write,
   exact active-task continuation, and clean-policy fast-track each require
   zero interruptions; material work must never enter fast-track. Treat Git
   policy ownership as an auditable attestation, not cryptographic identity.
8. Preserve the implemented per-cycle automatic Monitor refresh and Overview,
   Live Sessions, Protection Events, and Task Detail views; add explicit
   resolution links. The Dashboard remains a read model and contains no policy,
   merge, release, or deployment controls.
9. Add Benefit and Learning views with explicit `observed_fact`,
   `reproduced_comparison`, `supported_inference`, `human_feedback`, and
   `unknown` semantics. Every comparison states its denominator,
   applicability, and observation window; no combined governance score is
   introduced.
10. Run one exact-artifact automatic user-journey rehearsal in an independent
   non-NYC repository. One ordinary low-risk task must reach a reviewable
   completion without hand-authored internal JSON, repeated `next` queries,
   manual lifecycle command composition, or special confirmation words in the
   primary UI.
11. Only after the general rehearsal passes, run one real low-risk NYC shadow
   pilot. Keep its task, policy, paths, and business semantics in NYC; record
   feedback as consumer-local, general Core, adapter, usability,
   insufficient-evidence, or rejected.
12. Implement only admitted general gaps in AgentGov and replay them in both
    the independent repository and NYC before any stable promotion.

Acceptance signals:

- the ordinary user requests work through a coding-agent surface, confirms at
  most one concise task card when required, and reviews one completion card;
- context selection, scope observation, approved validation, evidence
  reconciliation, Monitor refresh, and session routing occur automatically;
- deterministic failures and protection events reach the coding agent and
  Dashboard without requiring user polling;
- ambiguous scope, architecture changes, exceptions, unapproved commands, and
  consequential transitions remain explicitly human-gated;
- Core events, transitions, findings, benefit semantics, and Dashboard data
  contain no vendor or consumer-specific policy;
- the Dashboard explains observed protection and evidence limits without
  claiming unsupported causality, ROI, or coverage;
- existing CLI and CI fixtures remain compatible and available for headless
  recovery and independent replay.

Stop conditions:

- a design requires a hidden daemon, automatic local-state upload, raw prompt
  collection, source upload, or host configuration as governance authority;
- automation silently expands scope, invents semantic admission, approves an
  exception, or gains external write authority;
- the Dashboard becomes a second governance source of truth or publishes an
  undocumented score;
- an NYC-specific path, policy, workflow, business object, or threshold is
  proposed for AgentGov Core;
- the automatic path cannot preserve current deterministic/advisory and fresh
  evidence semantics.

### P0 foundation — govern the coding agent during development

1. [Implemented development preview] Specify a minimal task contract for
   requirement provenance, parent objective, goal, non-goals, smallest scope,
   architecture references, acceptance signals, risks, approvals, stop
   conditions, and human admission state.
2. [Implemented development preview] Implement read-only task-context selection across the repository
   constitution, ADRs, invariants, capabilities, dependencies, controls, and
   evidence declarations. The current slice uses artifact-owned metadata,
   emits stable JSON/Markdown/terminal context, and adds no Registry file.
3. [Canonical working-tree and committed-since-base core implemented in development preview] Implement a read-only changed-file check covering staged, unstaged,
   untracked, and renamed paths without modifying Git state. Before
   implementation, satisfy the segment-aware matching, exclude-precedence,
   rename-endpoint, and classification policy gate in
   `docs/specs/development-trigger-routing-v1.md`. Segment matching,
   exclude precedence, rename endpoints, terminal/JSON/Markdown reporting, and
   Git no-mutation fixtures now pass. Phase 3 canonical snapshots add
   committed-since-base identity. Explicit exception records remain pending.
4. [First protocol and control mapping implemented] Map deterministic
   task-boundary and evidence failures separately from advisory requirement,
   architecture, stagnation, exception, reconciliation, and human-ownership
   judgments. Runtime hook integration and observed false-positive tuning
   remain pending.
5. [Implemented development preview] Add completion reconciliation that requires fresh validation evidence and
   exposes durable governance drift before claiming completion. Before
   implementation, satisfy the canonical Git-layer, local-tool-state,
   gitignore, validation-artifact, snapshot-ordering, and actionable-error hard
   gate in `docs/specs/fresh-validation-evidence-v1.md`. The implementation
   now binds S0/S1/S2, task digest, comparison base, snapshot HEAD, four Git
   layers, declared command identities, local evidence, and append-only local
   events. It never presents passing validation as semantic correctness.
6. [Implemented for context, scope, evidence, and completion previews] Expose stable terminal, Markdown, and JSON contracts for humans and coding
   agents without coupling to one IDE or model provider.
7. Use `docs/case-studies/0001-pr-center-architecture-drift.md` as the first
   self-governance acceptance scenario: preserve requirement and architecture
   references, reproduce scope and evidence facts, and keep the conclusion
   that supporting work displaced the product core explicitly advisory.
8. [Implemented local, portable, and opt-in Actions MVP] Generate a
   self-contained development Monitor with Overview, Activity Timeline, and
   Task Detail. The current
   source supports honest `local_session`, `exported_development`,
   actor-validated `ci_only`, and explicit export-plus-CI `combined` views.
   All remain partial, identify each event source, keep cross-stage discovery
   unavailable, and never expose approval or governance-write controls. The
   future 0.3 managed workflow adds a default-off manual-dispatch artifact that
   uploads only the derived HTML; it does not transfer raw events, the export
   bundle, or local `.agentgov/` state.
9. [Implemented development preview] Add the guided `govern start` vertical
   slice: deterministic single-candidate discovery, compact low-risk task
   scaffolding, exact write preview and confirmation, one active task per
   working copy, task-drift rejection, selected-governance start events, and
   active-session defaults for check and finish. Installation/update and CI
   wiring remain later productization work.
10. [Completed internal installed pilot] Exercise the complete guided loop from
    an exact wheel in an independent repository and record actual context
    consumption. The result supports package and workflow feasibility for one
    small Python task; it does not establish uncoached adoption, general
    effectiveness, or causal benefit.
11. [Implemented development preview] Export local development observations
    through a strict `metadata_only_v1` contract. Preview and exact `EXPORT`
    confirmation precede the create-only write; actor labels, local evidence
    pointers, source content, validation output, absolute paths, credential
    assignments, and recognized secret-token shapes cannot enter the bundle.
12. [Deferred behind the automatic-experience gate] Exercise the complete
    development loop on one real, low-risk NYC task in shadow mode only after
    P0 automatic orchestration passes independently. Record assistance,
    interruption burden, protection events, false positives, missed
    constraints, overrides, benefit evidence, and time; do not copy NYC policy
    into AgentGov or treat the later CI replay as the product interaction.

Acceptance signals:

- a coding agent receives the relevant requirement and architecture constraints
  before editing or while the change is still in progress;
- task-specific output omits unrelated repository-wide detail;
- deterministic scope and evidence facts reproduce from the same checkout and
  base ref;
- no development check modifies repository files, index, branch, or working
  tree;
- advisory requirement and architecture judgments remain explicitly human;
- completion cannot be reported as verified without fresh evidence;
- both commit-before-validation and commit-after-finish workflows remain valid,
  while any governed snapshot mutation between validation and finish makes the
  evidence stale;
- v1 exposes one active task per working copy and never silently overwrites the
  local active-task pointer;
- the `AG-DRIFT-001` scenario can surface the PR-center drift before PR
  creation without treating the existence of PR/CI work as an objective
  failure.

Stop conditions:

- ambiguous human intent that would materially change scope;
- unavailable or shallow base history that prevents a truthful change claim;
- unsafe paths, identity mismatch, architecture conflict, missing approval, or
  any design that silently turns advisory relevance into a deterministic fact.

### P1 — retain PR/CI as an independent backstop

1. Keep the completed two-workflow generation, migration review, redaction,
   benefit-monitor, and Draft PR boundaries covered by regression tests.
2. Make CI consume the same deterministic task/change facts as local
   development rather than defining a second governance meaning.
3. Add the migration-declared 0.3 release manifest and release notes only after
   the P0 task-contract compatibility surface is known.
4. Build and review the candidate without granting merge, publication,
   migration, or deployment authority.
5. Keep legacy 0.1/0.2 consumers supported through their declared boundary.

Acceptance signals:

- CI independently reproduces deterministic local findings;
- a skipped local check remains visible at the backstop;
- existing PR checks, artifacts, and upgrade evidence remain compatible;
- generated evidence contains no runner home, credential, or token value;
- no PR result claims requirement correctness or architecture sufficiency.

### P2 — validate portability against AI Radar and an independent consumer

1. Run the complete automatic journey first in an independent non-NYC
   repository, using the exact candidate artifact and one ordinary low-risk
   task without manual lifecycle command composition.
2. Replay bounded AI Radar development scenarios for requirement admission,
   architecture preflight, scoped implementation, fresh verification, and
   invariant reconciliation without importing AI Radar rules.
3. Run the NYC development-loop shadow pilot through the same automatic,
   portable contracts before any PR or CI migration, without importing NYC
   rules.
4. Compare what was surfaced before coding, during coding, at completion, and
   in PR/CI; record interruption burden, protection events, false positives,
   missed constraints, human overrides, handling time, benefit evidence, and
   limitations.
5. Classify NYC feedback before admission; keep consumer-local configuration
   in NYC and implement only general Core, adapter, or usability gaps in
   AgentGov.
6. Replay admitted changes in the independent repository and NYC, then resume
   NYC 0.3 migration only as a retained CI backstop.

Acceptance signals:

- AI Radar responsibility boundaries are preserved without copied business
  gates, paths, runtime schemas, or individual-specific policy;
- the independent consumer can use the same contracts without AI Radar
  knowledge;
- the automatic journey succeeds before NYC supplies product feedback;
- NYC demonstrates the governance interaction during coding, not only after a
  pull request exists;
- users discover relevant constraints before PR creation;
- WARN and ADVISORY remain visible and non-blocking while configured
  deterministic FAIL can block;
- no workflow-only change is presented as a business-code benefit.

### P3 — harden only from observed use

- add an external push-notification channel only if observed use shows the
  foreground card and scheduled read-only summary are insufficient, and only
  after a separate write-authority decision;
- consider a GitHub App only with a documented authority and threat model;
- extend retention or export only when a real low-activity history need is
  demonstrated;
- add integrations only when they preserve the repo-native CLI and evidence
  contracts.
- consider runtime hooks or mechanical interruption only after a separate
  authority and threat-model decision.

## Authority boundaries

Development and CI checks may inspect, report, and request a stop. They do not
objectively determine requirement meaning or architecture quality. Draft
upgrade automation may propose one bounded change set. Repository writes outside an
explicit task action, commit, merge, release, deployment, production execution,
mechanical agent interruption, and any new notification write authority remain
separately human-controlled.

See [open product decisions](open-decisions-2026-08-02.md) for questions that
must be resolved through implementation evidence rather than assumptions.
