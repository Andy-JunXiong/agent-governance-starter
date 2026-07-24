# Agent Governance Starter Kit Development Plan

Last updated: 2026-07-23

## Purpose

This is the top-level development plan for the repository.

Use it to answer:

1. What is the project building?
2. What has already been completed?
3. What should be implemented next?
4. What evidence is required before a version is considered stable?

Daily execution details belong in
[`STATUS.md`](STATUS.md). Historical daily records live under
`docs/development-log/`. Durable
architecture decisions belong in `docs/adr/`.

## Product Direction

The target product is a lightweight, repository-native AI governance kernel:

```text
Repository Governance Kernel
        +
Project Evidence Bridge
        +
Domain-informed adoption profiles
```

It should connect:

- declared AI capabilities;
- implementation and contract references;
- control implementation and verification evidence;
- evaluation readiness and evaluation decisions;
- accountable owners and human approval boundaries;
- deterministic repository findings and advisory human judgments.

Project-specific runtime controls, model runners, business thresholds, and
deployment systems remain in adopting repositories.

## Non-goals

Do not turn this repository into:

- an LLM gateway or runtime firewall;
- a universal model-evaluation platform;
- a deployment or release-authorization system;
- a compliance certification product;
- a general-purpose repository linter;
- a source of unsupported governance coverage percentages.

The project must not calculate a governance coverage percentage until the
denominator, applicability rules, exclusions, and weighting model are
documented and tested.

## Development Rules

For each meaningful slice:

- state the goal, non-goals, acceptance signals, and stop conditions;
- implement a small vertical slice;
- mark findings as deterministic or advisory;
- add fixture-based tests for supported states;
- keep legacy compatibility explicit and bounded;
- preserve the ten-minute adoption path;
- run relevant tests and record unresolved validation gaps;
- keep commit, push, tag, release, and deployment as separate human-approved
  actions.

No check result authorizes merge, publish, release, or deploy.

## Current State

Status: `0.1.0.dev0`, experimental.

Implemented foundations:

- safe initialization of new or empty repositories;
- create-missing-only adoption for existing repositories;
- read-only repository inspection and checks;
- strict capability, evaluation, case, adoption-report, and repository-report
  contracts;
- repository-local reference validation;
- deterministic capability artifact export and artifact drift checks;
- Markdown, JSON, and self-contained HTML reports from one findings model;
- stable CLI exit semantics;
- agent-skill contracts;
- explicit human authority boundaries;
- cross-platform CI definition.

Completed on 2026-07-23:

- evaluation readiness was separated from evaluation decision outcome;
- relative baseline regression thresholds were added;
- review dates and accepted/rejected decision evidence were added;
- Prompt Capability was generalized into canonical AI Capability fields;
- new scaffolds moved to the `governance/` layout;
- read-only legacy support for `prompt-governance/` was retained;
- simultaneous canonical and legacy layouts became a deterministic conflict;
- ADR-0001 and ADR-0002 recorded the durable decisions.

## Current P0 Track

### Pre-pilot credibility hardening

Goal:

Make the starter's own contracts, status, reports, and CI internally
consistent before adding repository inventory or beginning an external pilot.

In scope:

- explicit canonical capability contract identity;
- bounded read-only legacy compatibility and lifecycle documentation;
- truthful current status separated from historical development logs;
- AI Capability terminology on current product surfaces;
- report schema version separated from tool producer version;
- one truthful repository capability manifest;
- repository self-check and report artifact in CI.

Acceptance signals:

- canonical manifests cannot omit or contradict their contract identity;
- legacy manifests without identity remain readable with the existing
  layout-level migration warning;
- the repository's status does not describe committed work as uncommitted;
- JSON reports identify the producing agentgov version;
- the repository runs its own governance check in CI;
- the complete unit-test suite and `git diff --check` pass.

Stop conditions:

- do not add Taxi-specific contracts or policy;
- do not implement inventory, controls, dependency propagation, or profiles in
  this slice;
- do not weaken a deterministic failure to make self-check pass.

### Repository Inventory and Control Evidence

Goal:

Create an explicit, reviewable chain from governed capability inventory to
implementation controls and verification evidence.

This track must not claim automatic AI-capability discovery. It validates the
completeness and consistency of declarations made by accountable repository
owners.

### Slice 1 — Governance Inventory

Completed on 2026-07-24.

Planned canonical file:

```text
governance/inventory.json
```

Minimum contract:

- schema version;
- capability name;
- manifest reference;
- owner;
- governance status;
- explicit exclusions with path and reason.

Deterministic checks:

- every inventory capability references an existing manifest;
- every canonical manifest appears in the inventory;
- capability names are unique;
- capability and manifest identities agree;
- every capability has an owner;
- exclusions contain a non-empty reason;
- paths remain repository-relative and cannot escape through traversal or
  symbolic links.

Advisory boundary:

- the checker cannot prove that every real AI capability was declared;
- exclusions may be structurally valid while still requiring human judgment.

Acceptance signals:

- passing, warning, failing, and not-configured fixtures exist;
- initialized repositories receive an honest starter inventory;
- legacy repositories remain readable;
- no percentage or weighted score is emitted.

### Slice 2 — Orphan Evidence Checks

Completed on 2026-07-24.

Goal:

Detect declared evaluation and artifact directories that cannot be connected
to the governed inventory.

Implemented checks:

- manifest not listed in inventory;
- inventory item without manifest;
- evaluation bundle with unknown capability;
- artifact directory with unknown capability;
- declared capability without expected evidence, where policy requires it.

Acceptance signals:

- orphan evaluation and orphan artifact fixtures fail deterministically;
- optional evidence remains WARN or not applicable according to explicit
  policy;
- no repository content is inferred from matching filenames alone.

### Slice 3 — Control Mapping

Completed on 2026-07-24.

Canonical path:

```text
governance/controls/<capability-name>.json
```

Minimum control contract:

- capability name;
- control ID;
- objective;
- applicability;
- enforcement mode for applicable controls;
- implementation references;
- verification references;
- owner;
- exception authority;
- rationale for not-applicable controls.

Supported enforcement modes:

- `deterministic`;
- `platform_enforced`;
- `human_procedural`;
- `advisory_only`.

Deterministic checks:

- control IDs are unique;
- referenced capability exists;
- implementation and verification references are safe and readable;
- owner and exception authority are present;
- applicable enforcement mode is supported;
- not-applicable controls have a rationale and no enforcement evidence fields.

Advisory boundary:

- file existence does not prove that a control is effective;
- semantic sufficiency and exception quality remain human judgments.

### Slice 4 — Capability Dependencies

Completed on 2026-07-24.

Goal:

Represent explicit capability-to-capability dependencies without assuming that
all pipelines share one readiness model.

Canonical path:

```text
governance/dependencies/<capability-name>.json
```

Implemented design:

```json
{
  "depends_on": [
    {
      "capability": "prepare-features",
      "minimum_readiness": "baseline_ready"
    }
  ]
}
```

Deterministic checks:

- referenced capabilities exist;
- declaration owners and endpoints close to Governance Inventory;
- self-dependencies fail;
- cycles fail;
- explicitly declared minimum readiness is satisfied.

Do not automatically fail merely because downstream and upstream readiness
labels differ when no minimum was declared.

Advisory boundary:

- an empty dependency array is a valid explicit declaration;
- static checks cannot prove that every runtime or organizational dependency
  was discovered;
- dependency declarations do not enable automatic risk propagation or runtime
  orchestration.

## P1 — Pilot and Adoption Experience

Begin as a separate workstream after pre-pilot credibility hardening is
complete. The pilot may use a thin spike before inventory/control contracts
are frozen so real expression gaps can inform their design.

### Cross-domain pilot

Use one real repository, preferably NYC Taxi or Bitcoin, as an evaluation of
agentgov rather than a demonstration.

Before adoption:

- preregister fields expected to be insufficient;
- record which evidence is already present;
- record which claims should remain advisory;
- do not optimize for an all-green report.

Pilot outputs:

- gap report;
- schema corrections supported by real evidence;
- ten-minute adoption friction record;
- explicit decision on whether profiles are justified.

### Profile-based adoption

Candidate profiles:

- `agentic-runtime`;
- `ml-system`;
- `decision-support`;
- `research-evaluation`.

Profiles may select templates and recommendations. They must not embed
project-specific business thresholds or runtime logic.

### Consumer CI workflow

Provide an adopting-repository workflow that:

- pins an agentgov version;
- runs repository checks;
- always writes a JSON report;
- uploads the report as an artifact;
- optionally adds a step summary;
- blocks only configured deterministic statuses;
- does not authorize release.

### Evidence freshness

Define before implementing:

- review dates;
- explicit expiry or policy-based validity periods;
- change events that invalidate evidence;
- WARN versus FAIL semantics.

Do not infer expiry solely from elapsed time.

## P2 — Report Evolution

Begin after at least one real cross-domain pilot.

Planned additions:

- tool version;
- policy version;
- repository commit when explicitly available;
- profile;
- finding category;
- capability;
- owner;
- evidence references;
- blocking semantics derived from policy.

Planned command:

```text
agentgov diff old-report.json new-report.json
```

Expected comparisons:

- new and resolved FAIL findings;
- new WARN findings;
- readiness downgrade;
- expired evidence;
- source, artifact, or control drift;
- newly declared but incomplete capabilities.

Keep `artifact_drift` separate from future `behavioral_drift`.

## P3 — Multi-project Learning

Only begin after NYC Taxi, GLAP, and Bitcoin-style use cases have supplied
real adoption evidence.

Possible work:

- domain adapter interface;
- cross-project compatibility report;
- portfolio-level summary;
- validated risk dimensions;
- `v0.2.0`.

Do not build these from hypothetical taxonomies alone.

## Version Plan

### `0.1.0-rc1`

- Evaluation Evidence Bridge;
- canonical AI Capability schema;
- `governance/` layout;
- bounded legacy compatibility;
- migration documentation.

### `0.1.0-rc2`

- inventory contract;
- orphan checks;
- control mapping;
- relevant fixture coverage.

### `0.1.0`

- one real cross-domain pilot completed;
- adoption and migration documentation corrected from pilot evidence;
- consumer CI workflow;
- complete Python 3.11+ validation;
- no unresolved deterministic failures;
- explicit human approval for version change, tag, and release.

## Next Recommended Starting Point

Begin the cross-domain pilot as a separate workstream. The pre-pilot
repository-governance upgrade was integrated on 2026-07-24 after Capability
Dependencies PR #8 and the complete supported CI matrix passed.

Use Taxi or another real repository as an adversarial adopter:

1. select two or three real capabilities;
2. attempt to express only facts and evidence that actually exist;
3. record contract-expression failures and temporary workarounds;
4. defer contract changes until the pilot has supplied enough evidence to
   review them together.

Do not begin dependency risk propagation, repository profiles, governance
scoring, or taxonomy expansion before pilot evidence justifies the change.

## Validation Baseline

Required baseline command:

```powershell
$env:PYTHONPATH = "src"
python -m unittest discover -s tests -v
```

The project requires Python 3.11 or newer. Validation executed with an older
interpreter is not a release baseline.

## Documentation Rule

- `DEVELOPMENT_PLAN.md` owns top-level direction and sequencing.
- `STATUS.md` owns concise current state; dated files under
  `docs/development-log/` preserve historical execution records.
- `docs/adr/` owns durable architecture decisions.
- Other `docs/` files own detailed guidance, pilots, migrations, and reports.
- Update this plan only when priorities, scope, or acceptance criteria change.
