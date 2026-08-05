# AgentGov remaining development plan

Updated 2026-08-05. This page separates implemented development-source behavior
from published and consumer-adopted behavior.

## Current checkpoint

- Published stable: AgentGov 0.2.1; published Pre-release: v0.3.0rc1.
- NYC consumer: managed 0.2.1 workflow.
- Implemented locally for the future 0.3 line: persona-aware PR and owner UI,
  trusted-main benefit monitor, scheduled baseline refresh, redacted portable
  evidence, separate bounded Draft PR workflow, and pre-write current/target
  dry-run evidence. The managed governance template also has a default-off,
  manual-dispatch Development Monitor artifact path that uploads only the
  derived HTML.
- The generated two-workflow contract and fixture review is complete.
- ADR-0009 now makes requirement, architecture, and coding-agent governance
  during development the primary product direction. PR/CI remains a backstop.
- Implemented in development source: compact/standard task-contract 1.1,
  read-only `agentgov check task`, artifact-owned Skill routing metadata, an
  in-memory Registry, and task-specific `agentgov context task` output in
  terminal, JSON, and Markdown with selection reasons and source hashes. The
  working-tree scope core now also inventories staged, unstaged, deleted,
  renamed, and non-ignored untracked paths and applies the deterministic
  segment-aware include/exclude policy through `agentgov check scope`.
  `agentgov govern check/finish` now adds local observations, canonical
  committed/dirty snapshot evidence, declared-command validation, and honest
  `verified`/`needs_evidence` reconciliation. `agentgov monitor development`
  now renders the validated local event stream as a static Overview, Activity
  Timeline, and Task Detail with explicit observation and claim limits. Guided
  `govern start` now previews and explicitly confirms one existing or compact
  task, derives selected governance, records one active task/base per working
  copy, and lets check/finish resume it without repeated arguments. Explicit
  `export development` now creates an immutable metadata-only bundle after
  preview and exact confirmation; Monitor ingestion supports honest
  `exported_development` and `combined` views with per-source event labels and
  counts. Read-only `agentgov next` now preserves onboarding and repository
  `FAIL` precedence, then derives exactly one start/check/finish/Monitor action
  from the strict active-session pointer and current-session events.
- Implemented in development source: ADR-0012's `govern handoff` re-establishes
  fresh verified evidence, previews one stable append-only event, requires
  exact interactive `HANDOFF`, preserves the pointer and prior artifacts, and
  makes repeated matching handoff idempotent. Monitor 1.4 retains the 1.3
  separation of verified completion from handed-off routing, and `next` filters the same digest before
  offering a separate `--replace-active` rollover.
- Not yet implemented: explicit exception records or action-loop
  self-reporting. Local-state transfer remains explicit; the workflow does not
  upload raw events or an export bundle.
- Completed independent installed-build pilot: the exact source wheel was
  installed with no runtime dependencies in a fresh environment and governed
  a real Coding Agent change in a repository with no AI Radar dependency. The
  corrected run reached `verified` and generated four Monitor events. The
  initial invalid Skill and unignored Python cache attempts remained visible as
  fail-closed product evidence.
- Completed exact-wheel guided-next rehearsal: an isolated `0.3.0.dev0` wheel
  preserved onboarding and explicit-choice boundaries, then selected check,
  finish, and Monitor in order for one verified task. All observed `next`
  calls were Git-non-mutating; the local Monitor contained four source-labeled
  events. This is internal deterministic plumbing evidence, not uncoached
  usability evidence.
- ADR-0011 completes the bootstrap/update boundary decision. Public fixed-wheel
  installation must precede the CLI; installed update inspection remains
  `agentgov update --check`; and update availability does not enter `next`
  while development metadata has no artifact or verified sessions lack a
  terminal handoff/rollover state.
- ADR-0012 completes the verified-session terminal contract. Exact `HANDOFF`
  now appends one `session.handed_off` event only after re-establishing
  fresh verified evidence; it retains the pointer and all prior artifacts, and
  leaves the next task to a separate reviewed `--replace-active` start. This is
  a routing transition, not approval or semantic completion.
- The source and bundled compatibility metadata identify as 0.3.0rc1,
  distinct from published stable 0.2.1. The GitHub candidate is published;
  its immutable manifest conservatively underclaims compatibility because the
  tag workflow omitted the reviewed metadata input. The source workflow is
  corrected for later candidates. Not yet completed: NYC 0.3 migration or
  evidence from real NYC runs. Those are supporting delivery tasks rather
  than the next product-defining slice.
- Public entry points now distinguish stable 0.2.1 from candidate source
  0.3.0rc1, use one isolated pipx user path, keep the AgentGov product page
  primary, and present AI Radar only as a bounded origin reference after the
  AgentGov evidence story.
- Portfolio raw-Markdown and out-of-root schema links now target project-local
  HTML. A live build exposed that same-name HTML proxies collide with Jekyll's
  Markdown output, so commit `743f3b3` applies the shared AgentGov layout
  directly to authoritative Markdown and removes those proxies. The follow-up
  Pages build and public URL replay passed for all reference and schema
  surfaces; published JSON schema copies remain byte-checked.

## Next-session starting point

The exact isolated `0.3.0rc1` wheel has completed the ADR-0012 rehearsal in
three independent repositories: verified completion, Monitor guidance,
handoff, zero/one/many rollover selection, and exact `REPLACE`. Seventeen
delivered historical tasks are paused for routing hygiene, leaving one admitted
RC closeout task.

ADR-0013 now records the next product boundary: the implemented manual
`next/start/check/finish/Monitor/handoff` sequence is a set of internal and
fallback primitives, not the intended daily user experience. The next product
slice is a general, vendor-neutral, foreground automatic coordinator plus an
automatically refreshed protection and benefit Dashboard. It must pass an
independent non-NYC rehearsal before NYC is used as the first real consumer
feedback pilot.

The first two internal automation slices are now implemented in development source:
`agentgov.development-state` 1.0 projects validated active-session events into
one lifecycle stage and recommended operation, and
`agentgov.development-trigger` 1.0 defines privacy-bounded vendor-neutral
adapter events. Existing `next` active-session routing consumes the projection.
`agentgov.foreground-cycle` 1.0, `agentgov dev`, and the minimal reference
adapter now perform one explicit event cycle: implementation changes trigger
scope observation; completion requests trigger scope, admitted validation,
reconciliation, and Dashboard refresh; human review can hand off verified work.
Monitor 1.4 derives Live Sessions and Protection Events while keeping
resolution unknown without an explicit link. Live coding-agent transport,
natural-language task admission, visual cards, and Benefit/Learning remain; see
`docs/development-automation-contracts.md`.

Do not rewrite `v0.3.0rc1`, publish another candidate, promote stable 0.3.0,
modify NYC, add automatic local-state upload, hidden daemon authority,
mechanical runtime interruption, merge authority, or deployment without a
separate decision.

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
   state-machine service while preserving current CLI bytes, exit codes,
   authority flags, and fixture behavior. The active-session projection is
   implemented; no-task admission remains a human gate.
2. Extend the implemented strict, versioned, vendor-neutral trigger and
   minimal reference-adapter contract for
   at least task requested, repository activated, implementation changed,
   scope decision requested, completion requested, validation completed, and
   session reviewed events. The trigger vocabulary and authority boundary are
   implemented; live vendor transport remains.
3. Extend the implemented explicit one-cycle foreground coordinator
   `agentgov dev`, that consumes adapter events, invokes existing deterministic
   cores, records disclosed local metadata events, refreshes the Dashboard, and
   returns findings without a hidden daemon. Connect it to a real coding-agent
   surface and evaluate whether a longer-lived foreground process is needed.
4. Extend the implemented repository-state reference adapter with one live
   coding-agent transport. Adapter configuration remains replaceable input and
   never governance authority.
5. Add a concise task and approval surface. Normal product interaction uses a
   card, button, or adapter approval event; exact `START`, `REPLACE`, and
   `HANDOFF` text remains only a headless fallback.
6. Preserve the implemented per-cycle automatic Monitor refresh and Overview,
   Live Sessions, Protection Events, and Task Detail views; add explicit
   resolution links. The Dashboard remains a read model and contains no policy,
   merge, release, or deployment controls.
7. Add Benefit and Learning views with explicit `observed_fact`,
   `reproduced_comparison`, `supported_inference`, `human_feedback`, and
   `unknown` semantics. Every comparison states its denominator,
   applicability, and observation window; no combined governance score is
   introduced.
8. Run one exact-artifact automatic user-journey rehearsal in an independent
   non-NYC repository. One ordinary low-risk task must reach a reviewable
   completion without hand-authored internal JSON, repeated `next` queries,
   manual lifecycle command composition, or special confirmation words in the
   primary UI.
9. Only after the general rehearsal passes, run one real low-risk NYC shadow
   pilot. Keep its task, policy, paths, and business semantics in NYC; record
   feedback as consumer-local, general Core, adapter, usability,
   insufficient-evidence, or rejected.
10. Implement only admitted general gaps in AgentGov and replay them in both
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

- add notification deduplication or acknowledgement only if NYC evidence shows
  the read-only channel is insufficient;
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
