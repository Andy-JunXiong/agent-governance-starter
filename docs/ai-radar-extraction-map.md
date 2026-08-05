---
layout: reference
title: AI Radar extraction map
source_path: docs/ai-radar-extraction-map.md
---

# AI Radar extraction map

## Purpose

This document records the narrow, read-only inventory used to extract reusable
governance patterns from AI Radar. It distinguishes portable contracts from
AI Radar implementation details and prevents the starter kit from becoming a
copy of the reference product.

Initial inventory date: 2026-07-13

Development-loop revalidation date: 2026-08-02

Automatic-governance management revalidation date: 2026-08-05

Current read-only reference: the `ai-radar-aws` repository at commit
`dcc27bd8e1166bc3380d3ad75d2d2c76395106d8`. Machine-specific absolute paths
are intentionally omitted. The 2026-08-05 management revalidation read only
committed `HEAD` content with `git show`; it did not inspect or reuse the wider
AI Radar worktree's unrelated user and generated-data changes. The earlier
development-loop implementation comparison used commit
`3a9323cb2a9ef575da42d29fb17d330ef872afd3`.

## Classification rules

| Classification | Meaning |
|---|---|
| `generic-reusable` | Portable with minimal normalization. |
| `rewrite-required` | Valuable pattern, but coupled to AI Radar wording, paths, or behavior. |
| `reference-only` | Demonstrates real use; do not copy it into the starter kit. |
| `ai-radar-specific` | Product logic that is excluded from the starter kit. |

## Current inventory

| AI Radar source | Current role | Classification | Starter-kit treatment |
|---|---|---|---|
| `AGENTS.md` | Constitution, task modes, narrow-scope rules, context routing, security, core-file, Git, and approval boundaries | `rewrite-required` | Preserve always-loaded hard boundaries, explicit task scope and context routing; remove AWS, S3, dual-repository sync, product workflows, and repository-specific paths. |
| `AI_CONTEXT.md` | Selective architecture memory for ambiguous or architectural work | `rewrite-required` | Preserve the distinction between always-loaded constitution and task-selected architecture context; do not copy AI Radar services, topology, or business objects. |
| `docs/adr/TEMPLATE.md` | ADR authoring contract | `generic-reusable` | Adapt the decision and tradeoff structure into a portable template. |
| `docs/adr/INVARIANTS.md` | Cross-ADR invariant register and slice-to-required-reading router | `rewrite-required` | Preserve scoped invariant discovery and owning-decision references without importing AI Radar evidence, Reflection, Watch, or Project Takeaway rules. |
| `agent-skills/README.md` | Separates product runtime skills from Layer A' coding-agent protocols and provides canonical trigger discovery | `generic-reusable` | Preserve the layer distinction, canonical registry, explicit consumers, and trigger routing without importing the complete AI Radar skill set. |
| `agent-skills/development-slice/SKILL.md` | Requirement framing, architecture/core-doc preflight, bounded implementation, validation, and handoff | `rewrite-required` | Remove AI Radar status files and product gates; keep the slice contract, goal/non-goal fields, closed-loop ownership, validation, stop, and handoff pattern. |
| `agent-skills/development-slice/references/closed-loop-contract.md` | Keeps the coding agent inside an approved implementation loop while the human retains purpose, boundary, and approval | `rewrite-required` | Generalize the task contract and fresh-evidence completion rule; do not treat a closed loop as broader autonomy or automatic Git authority. |
| `agent-skills/grill-before-sprint/SKILL.md` | Project-axis requirement gate before meaningful implementation | `rewrite-required` | Generalize concrete-gap, why-now, smallest-slice, tradeoff, and validation questions into task admission; replace AI Radar-specific outcomes and records with portable task states. |
| `agent-skills/grill-before-absorb/SKILL.md` | Human cognitive-ownership gate for durable agent-shaped decisions | `rewrite-required` | Preserve human ownership as an advisory decision boundary; remove named-person and cognitive-log coupling, and do not make it a deterministic code gate. |
| `agent-skills/incident-response/SKILL.md` | Operational incident procedure | `rewrite-required` | Replace AWS-specific commands and deployment rules with configurable stop and escalation contracts. |
| `agent-skills/context-first-review/SKILL.md` | Repo-grounded architecture and cross-module proposal review | `generic-reusable` | Preserve path, boundary, conflict, and decision discovery before implementation; exclude AI Radar admission outcomes and product invariants. |
| `agent-skills/action-loop-stagnation/SKILL.md` | Detects repeated action hypotheses, false completion, and handoff-before-evidence during implementation | `rewrite-required` | Generalize failure packets, structurally different hypotheses, verification oracles, and human handoff; retain the explicit boundary that a protocol request is not a mechanical runtime halt. |
| `agent-skills/reconcile-invariants/SKILL.md` | Scoped completion-time alignment across constitution, ADRs, invariants, and protocol registry | `rewrite-required` | Generalize scoped drift review and proposed-diff output; do not scan the whole repository or automatically rewrite core governance files. |
| `docs/adr/0004-agents-constitution-skill-registry.md` | Rationale for constitution-plus-routing rather than one always-loaded SOP | `reference-only` | Use as design evidence for separating hard rules from conditional protocols; do not copy AI Radar phases or proposed-status claims. |
| `docs/adr/0005-dual-gate-pre-sprint-protocol.md` | Separates project value from human cognitive ownership before agent execution | `reference-only` | Preserve the decision-axis separation as product rationale; portable implementation remains subject to AgentGov task-contract design and user validation. |
| `docs/adr/0016-action-loop-stagnation-protocol.md` | Separates action-loop governance from claim verification and runtime enforcement | `reference-only` | Preserve the protocol-versus-mechanical-enforcement boundary; do not import external-skill taxonomy, hooks, telemetry, or AI Radar runtime gates. |
| `agent-skills/incident-attribution/SKILL.md` | Reviewable process-learning protocol | `rewrite-required` | Adapted factual capture, stage attribution, pattern review, and explicit outcomes; removed named participants, fixed record paths, infrastructure language, and core-file lists. |
| `docs/metrics-monitoring-mvp.md` | Event-first local monitoring, operational summaries, privacy limits, and read-only admin views | `rewrite-required` | Preserve append-only local metadata events, observation gaps, period narratives, and read-only views; replace pipeline, collector, LLM, verification, cost, and AI Radar business metrics with AgentGov session, protection, evidence, benefit, and learning semantics. |
| `backend/app/prompts/skill_meta.py` | Minimal metadata decorator for prompt capabilities | `reference-only` | Use it as evidence for the capability-schema design; do not import the class. |
| `backend/app/prompts/registry.py` | AI Radar runtime prompt implementations | `ai-radar-specific` | Do not copy prompts or runtime behavior. Use only anonymized metadata examples later. |
| `backend/app/prompts/export_skills.py` | Generates reviewable skill artifacts and source hashes | `rewrite-required` | Reimplemented as manifest-driven repository-local capability artifacts; removed runtime discovery, timestamps, Pydantic, scoring, and vendor-directory writes. |
| `backend/tests/test_skill_meta.py` | Metadata contract tests | `reference-only` | Derive generic schema fixtures rather than copying runtime tests. |
| `backend/tests/test_export_skills.py` | Export and hash-drift tests | `generic-reusable` | Recreated independent tests for deterministic export, explicit replacement, manual-file preservation, source and manifest drift, and path containment. |
| `scripts/run_skill_export_check.py` | Repository import-path wrapper | `ai-radar-specific` | Exclude; the starter package must not need AI Radar path bootstrapping. |
| `scripts/validate_skill_baselines.py` | Baseline readiness validation | `rewrite-required` | Generalize only after readiness states and baseline schemas are defined. |
| `tests/test_skill_baseline_validation.py` | Tests current baseline policies | `reference-only` | Use as validation evidence; build independent generic fixtures. |

## Explicit exclusions

The starter kit must not extract or generalize these AI Radar product concepts
in v0.1:

- Project Takeaway candidates, review outcomes, overrides, or action gates;
- `blocked_downstream_actions` and AI Radar evidence categories;
- Signal, Insight, Trend, Review Inbox, Agent Watch, Reflection, or Trajectory
  workflows;
- AI Radar model routing behavior;
- AWS accounts, services, buckets, deployment paths, or credentials;
- generated signals, prompts containing private context, uploaded files, or
  runtime data.

## Coupling findings

1. The root `app/prompts/*` modules proxy the backend prompt implementation, so
   the current export path is repository-layout-aware rather than portable.
2. `SkillMeta` is a useful starting point but does not yet contain the full
   owner, risk, model-route, evaluation-readiness, and provenance contract
   proposed for this project.
3. Exported skills target a vendor-specific user directory by default. The
   reusable core should first produce repository-local artifacts; vendor
   adapters can be optional targets.
4. Current evaluation validation covers selected capabilities and should be
   described as scaffolding, not a general benchmark system.
5. Human approval has both repository-change and AI Radar product meanings.
   Only the repository-change pattern belongs in this starter kit.

## Extraction closeout

No additional AI Radar extraction is scheduled for v0.1. The independent
clean-repository adoption rehearsal is complete and covers package
installation, initialization, placeholder visibility, capability and reference
checks, artifact export, evaluation readiness, agent-protocol validation, and
repository reporting. See `docs/v0.1-adoption-rehearsal.md` for the recorded
result.

New reference-project patterns must be admitted as separate scoped proposals
rather than extending this map by default.

## Development-loop consistency decision

The 2026-08-02 revalidation admits one new portable product direction: AgentGov
should govern coding-agent work during development, from requirement admission
through architecture grounding, bounded implementation, fresh verification,
and scoped closeout reconciliation. Pull-request and CI checks remain an
independent replay and evidence backstop, not the first or primary governance
interaction.

The portable correspondence is:

| AI Radar governance moment | AgentGov portable responsibility |
|---|---|
| concrete sprint proposal | requirement/task admission with goal, non-goals, smallest scope, risks, and acceptance signals |
| selective context and ADR/invariant preflight | architecture context assembled from repository-owned decisions, dependencies, controls, and approval boundaries |
| development slice and closed loop | coding-agent execution constrained to the admitted task with explicit stop conditions and fresh verification |
| action-loop stagnation | advisory detection of repeated approaches, missing verification, or premature handoff |
| invariant reconciliation | completion-time check for drift between the task, architecture decisions, implementation, evidence, and governance memory |
| PR and CI | independent deterministic replay, bypass prevention, and durable evidence |

This does not admit AI Radar runtime code, its named business gates, cognitive
logs, product schemas, project-specific core-file list, deployment model, or a
mechanical agent-control hook. AgentGov must also preserve AI Radar's current
Layer A' boundary: repository protocols can instruct, check, and request a
stop, but they do not become runtime enforcement or new authority merely by
being machine-readable.

Phase 1 implementation reuse decision: derive an in-memory Registry from
AgentGov artifacts, always select the consumer's root `AGENTS.md`, select
explicit task references, route Skills from their own structured metadata, and
connect capability governance through artifact-declared repository paths. This
is a `rewrite-required` adaptation of the already recorded AI Radar
`AGENTS.md`, `AI_CONTEXT.md`, Invariants, and Skill routing responsibilities.
No AI Radar content, paths, runtime code, business taxonomy, or persisted
Registry is copied.

## Automatic-governance management revalidation

The 2026-08-05 pass found that the useful AI Radar management primitives were
already represented in AgentGov's task, context, development-slice,
action-loop, reconciliation, incident-attribution, event, and Monitor
contracts. A second skill tree or AI Radar-style management subsystem would be
duplicate framework weight. The admitted next reuse is therefore narrower:

1. project the existing development event stream into one versioned internal
   lifecycle state that a foreground coordinator can consume;
2. define a strict vendor-neutral trigger contract for coding-agent adapters;
3. expose protection and benefit observations through the existing local
   Monitor/Dashboard path rather than a second source of truth;
4. keep high-risk project-value and human-ownership questions risk-triggered,
   not mandatory interactions for every ordinary task.

AI Radar's documentation architecture is also cautionary evidence. Its
committed management surfaces are intentionally detailed and useful within
that product, but AgentGov must not reproduce their accumulated always-loaded
or current-status volume. AgentGov should keep canonical contracts small,
derive read models from structured state, archive history, and use
deterministic freshness checks instead of requiring humans to synchronize the
same fact across many documents.

Implementation decision for the first automatic slice: `rewrite-required`.
AgentGov may reuse only the management responsibilities above. It must not copy
AI Radar files, named people, product gates, cognitive logs, claim-verification
objects, AWS/runtime metrics, business workflows, or host-specific paths.

The following foreground slice remains the same `rewrite-required` decision:
AgentGov implemented its own vendor-neutral trigger, state, one-cycle
coordinator, reference adapter, and Dashboard contracts. No AI Radar runtime
module, event schema, metric name, command surface, product gate, or business
object was copied.

## NYC Taxi development-loop pilot boundary

Pilot inventory date: 2026-08-01

The local `NYC-Taxi-Demand-And-Fare-Intelligence-Platform` repository is a
read-only research input for AgentGov portability; its machine-specific
absolute path is intentionally omitted. The completed
consumer-CI and status-visibility pilot is historical backstop evidence; it did
not validate governance while a coding agent was developing the change. No NYC
source code, data, credentials, production workflow behavior, or
project-specific policy is starter-kit source.

| NYC Taxi source | Observed role | Classification | Starter-kit treatment |
|---|---|---|---|
| `.github/workflows/ci.yml` | Runs the project test suite but does not invoke AgentGov | `reference-only` | Use only as evidence that adopted governance can remain manual and invisible; create an independent portable consumer workflow. |
| `AGENTS.md` | Names manual AgentGov validation and human authority boundaries | `reference-only` | Preserve the general need for explicit authority in the starter's existing contracts; do not copy NYC operating rules. |
| `governance/capabilities/nyc-hourly-zone-demand-forecast.json` | Connects one capability to callers, contracts, ownership, risk, and evaluation | `reference-only` | Use sanitized field presence to test status rendering; do not copy the capability or its business semantics. |
| `governance/contract.json` | Marks repository layout `1.0` after an explicit refresh | `generic-reusable` | Detect the existing portable contract through AgentGov's own schema; do not add NYC-specific fields. |

Current reuse decision: use NYC first as a development-loop shadow pilot for a
real low-risk task. Begin with human requirement admission and selected
repository context before editing, observe bounded work and stagnation during
implementation, and require fresh evidence plus scoped invariant
reconciliation before handoff. Only afterward may the existing generic GitHub
Actions integration independently replay deterministic facts as a backstop.
The pilot must not copy or modify NYC business policy as starter-kit source,
install project dependencies, run production workflows, overwrite an existing
workflow, or authorize Git, merge, release, or deployment actions.
