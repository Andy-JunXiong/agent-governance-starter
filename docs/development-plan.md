# AgentGov remaining development plan

Updated 2026-08-03. This page separates implemented development-source behavior
from published and consumer-adopted behavior.

## Current checkpoint

- Published stable: AgentGov 0.2.1; current source identity: 0.3.0.dev0.
- NYC consumer: managed 0.2.1 workflow.
- Implemented locally for the future 0.3 line: persona-aware PR and owner UI,
  trusted-main benefit monitor, scheduled baseline refresh, redacted portable
  evidence, separate bounded Draft PR workflow, and pre-write current/target
  dry-run evidence.
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
  counts.
- Not yet implemented: explicit exception records, action-loop self-reporting,
  or automatic GitHub Actions artifact wiring.
- Completed independent installed-build pilot: the exact source wheel was
  installed with no runtime dependencies in a fresh environment and governed
  a real Coding Agent change in a repository with no AI Radar dependency. The
  corrected run reached `verified` and generated four Monitor events. The
  initial invalid Skill and unignored Python cache attempts remained visible as
  fail-closed product evidence.
- The development source and bundled compatibility metadata now identify as
  0.3.0.dev0, distinct from published stable 0.2.1. Not yet completed:
  release-candidate review and publication, NYC 0.3 migration, or evidence from
  real NYC runs. Those are supporting delivery tasks rather than the next
  product-defining slice.
- Public entry points now distinguish stable 0.2.1 from development source
  0.3.0.dev0, use one isolated pipx user path, keep the AgentGov product page
  primary, and present AI Radar only as a bounded origin reference after the
  AgentGov evidence story.
- The working copy also replaces Portfolio raw-Markdown and out-of-root schema
  links with shared-layout HTML reference proxies. Markdown and source schemas
  remain authoritative; published JSON schema copies are byte-checked. A real
  GitHub Pages build and URL replay remain required before this repair can be
  called published.

## Ordered work

### Accepted productization constraint

Final users must not need to hand-author internal JSON, understand Registry
internals, or manually assemble a chain of low-level commands. GitHub
installation, updates, repository onboarding, task admission, context routing,
checks, finish, and Monitor generation must converge on a small guided workflow
with safe discovery, preview, sensible defaults, and explicit human confirmation
only at real authority boundaries. This productization work is intentionally
scheduled after the core Govern/Observe/Monitor semantics are proven; the
current low-level commands remain development interfaces, not the intended
final UX.

### P0 — govern the coding agent during development

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
4. Map deterministic task-boundary failures separately from advisory
   requirement, architecture, exception, and human-ownership judgments.
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
8. [Implemented local and portable MVP] Generate a self-contained development
   Monitor with Overview, Activity Timeline, and Task Detail. The current
   source supports honest `local_session`, `exported_development`,
   actor-validated `ci_only`, and explicit export-plus-CI `combined` views.
   All remain partial, identify each event source, keep cross-stage discovery
   unavailable, and never expose approval or governance-write controls.
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

1. Replay bounded AI Radar development scenarios for requirement admission,
   architecture preflight, scoped implementation, fresh verification, and
   invariant reconciliation without importing AI Radar rules.
2. Exercise an independent repository change through the same local contracts
   to detect hidden AI Radar coupling.
3. Compare what was surfaced before coding, during coding, at completion, and
   in PR/CI.
4. Record assistance, false positives, missed constraints, human overrides,
   handling time, and evidence limitations.
5. Resume the NYC 0.3 migration only when it tests the retained backstop or the
   independent-consumer role rather than standing in for core product value.

Acceptance signals:

- AI Radar responsibility boundaries are preserved without copied business
  gates, paths, runtime schemas, or individual-specific policy;
- the independent consumer can use the same contracts without AI Radar
  knowledge;
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
