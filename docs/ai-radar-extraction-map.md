# AI Radar extraction map

## Purpose

This document records the narrow, read-only inventory used to extract reusable
governance patterns from AI Radar. It distinguishes portable contracts from
AI Radar implementation details and prevents the starter kit from becoming a
copy of the reference product.

Inventory date: 2026-07-13

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
| `AGENTS.md` | Constitution, operating modes, security and approval boundaries | `rewrite-required` | Extract a neutral constitution template; remove AWS, S3, product workflow, and repository-specific paths. |
| `docs/adr/TEMPLATE.md` | ADR authoring contract | `generic-reusable` | Adapt the decision and tradeoff structure into a portable template. |
| `docs/adr/INVARIANTS.md` | Cross-ADR invariant register | `rewrite-required` | Define a generic invariant-record format without importing AI Radar invariants. |
| `agent-skills/README.md` | Separates product runtime skills from coding-agent protocols | `generic-reusable` | Preserve the layer distinction and vendor-neutral source-of-truth principle. |
| `agent-skills/development-slice/SKILL.md` | Small-slice planning, validation, and handoff protocol | `rewrite-required` | Remove AI Radar status files and product gates; keep the slice contract and closed-loop validation pattern. |
| `agent-skills/incident-response/SKILL.md` | Operational incident procedure | `rewrite-required` | Replace AWS-specific commands and deployment rules with configurable stop and escalation contracts. |
| `agent-skills/context-first-review/SKILL.md` | Repo-grounded proposal review | `generic-reusable` | Adapted path, boundary, conflict, and decision discovery into a vendor-neutral protocol; excluded AI Radar admission gates and product invariants. |
| `agent-skills/incident-attribution/SKILL.md` | Reviewable process-learning protocol | `rewrite-required` | Adapted factual capture, stage attribution, pattern review, and explicit outcomes; removed named participants, fixed record paths, infrastructure language, and core-file lists. |
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

## NYC Taxi consumer-integration pilot

Pilot inventory date: 2026-08-01

The local NYC Taxi repository at
`C:\Users\maki8\OneDrive\桌面\Find a job\NY Taxi\NYC-Taxi-Demand-And-Fare-Intelligence-Platform`
is a read-only research input for the consumer CI and status-visibility slice.
No NYC source code, data, credentials, production workflow behavior, or
project-specific policy is starter-kit source.

| NYC Taxi source | Observed role | Classification | Starter-kit treatment |
|---|---|---|---|
| `.github/workflows/ci.yml` | Runs the project test suite but does not invoke AgentGov | `reference-only` | Use only as evidence that adopted governance can remain manual and invisible; create an independent portable consumer workflow. |
| `AGENTS.md` | Names manual AgentGov validation and human authority boundaries | `reference-only` | Preserve the general need for explicit authority in the starter's existing contracts; do not copy NYC operating rules. |
| `governance/capabilities/nyc-hourly-zone-demand-forecast.json` | Connects one capability to callers, contracts, ownership, risk, and evaluation | `reference-only` | Use sanitized field presence to test status rendering; do not copy the capability or its business semantics. |
| `governance/contract.json` | Marks repository layout `1.0` after an explicit refresh | `generic-reusable` | Detect the existing portable contract through AgentGov's own schema; do not add NYC-specific fields. |

Reuse decision: implement a generic create-missing-only GitHub Actions
integration and a read-only status surface. Validate them against synthetic
fixtures first, then use NYC only as an adoption pilot. The integration must
not install adopting-project dependencies, run production workflows, overwrite
an existing workflow, or authorize Git, merge, release, or deployment actions.
