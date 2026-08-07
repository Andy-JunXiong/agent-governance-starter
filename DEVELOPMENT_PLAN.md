# Agent Governance Starter Kit Development Plan

Last updated: 2026-08-07

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

The target product is a lightweight, repository-native coding-agent governance
kernel:

```text
Requirement and Task Governance
        +
Architecture and Invariant Context
        +
Bounded Coding-Agent Execution Evidence
        +
Independent PR/CI Replay
```

It should connect:

- human-admitted goals, non-goals, scope, acceptance signals, and stop
  conditions;
- repository architecture decisions and invariants relevant to the task;
- declared AI capabilities;
- implementation and contract references;
- control implementation and verification evidence;
- evaluation readiness and evaluation decisions;
- accountable owners and human approval boundaries;
- actual code changes, fresh validation evidence, deterministic repository
  findings, and advisory human judgments.

ADR-0009 makes this development-time loop the product core. PR and CI remain
an independent backstop and evidence surface, not the first point at which a
coding agent should discover constraints.

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

Status: published stable `0.2.1`; published Pre-release `v0.3.0rc1`. The
accepted automatic primary experience is not yet implemented. Its first
internal contract slice now provides a read-only active-session state
projection, vendor-neutral adapter trigger envelope, and Monitor 1.4 Live
Sessions / Protection Events read models. The next slice now also implements
one explicit `agentgov dev` foreground cycle, a minimal repository-state
reference adapter, automatic scope/completion actions, Dashboard refresh, and
human-review handoff. A generic strict JSONL foreground transport, bounded
task/scope/completion cards, and the first packaged Codex lifecycle-hook Adapter are
now implemented in development source. A vendor-neutral host-interaction
request/capability contract is also implemented, with Codex custom governance
decisions honestly limited to context-only delivery. A reference host Adapter
now converts ordinary request text through a replaceable semantic materializer
into the existing strict proposal and read-only admission plan. Development
Codex Adapter `1.3.0` now connects the current Agent as the first production
materializer and MCP form elicitation as its native exact-plan review surface;
local installation and installed-runtime preflight now pass. The first approved
event-level attempt stopped in its host bridge during App Server initialization
without an observable thread or proposal form. The separately approved
null-stream retry passed local initialization and thread probes, then its real
turn ended at App Server EOF before a form or tool result. The standalone CLI
then reported `Not logged in` with no inheritable credential environment
variable. Live proposal review remains unproven; authentication repair and
another replay are not admitted. Proactive prompt/result
contracts and a reference
single-selection review path are implemented; a native authenticated decision
surface and the complete automatic
journey remain open. A vendor-neutral governed clarification protocol now
keeps business, requirement, and architecture drift discussion separate from
the final human direction decision. The live foreground Coding Agent stream
now automatically carries normalized alignment context, human clarification
updates, and the final direction result in memory. A host-side reference
Alignment Adapter now proves the smaller natural-language alignment journey:
the host materializer derives normalized drafts, the Adapter supplies strict
envelopes, the user answers naturally and finishes with one selection, and the
privacy-safe trace reports zero user-authored JSON or commands. This is an
offline integration rehearsal, not a production semantic materializer or the
complete automatic development journey. No NYC
development-loop pilot or 0.3 consumer migration has occurred.

The 2026-08-06 native Codex MCP work now proves five-tool discovery, automatic
alignment selection for a delegated product choice, human ownership of the
final direction, and fail-closed stopping. The latest uncoached replay still
failed because the MCP schema allowed deterministic semantics for business,
requirement, and architecture drift while Core requires those judgment-bearing
kinds to remain advisory. The admitted bounded correction aligns that schema,
adds privacy-safe retry classification, and precedes one new installed-runtime
replay. NYC, another host, stable promotion, release, and
deployment remain gated on completion of human direction selection and
current-Agent advisory self-review.
The corrected local runtime is installed and has passed Adapter `1.2.1`,
five-tool, conditional-schema, and same-process retry preflight. A newly created
uncoached Codex session then corrected its first drift error but stopped on a
second unclassified rejection. Normalized diagnosis found that a no-unknown
context could omit Core's required stable option set or recommendation.
Development Adapter `1.2.2` now exposes and precisely classifies that rule;
full validation precedes any separately reviewed reinstall and replay.
Adapter `1.2.2` is now installed and its exact conditional schema plus
same-process two-error correction path have passed preflight. The remaining
newly created uncoached replay still stopped on another unclassified start
rejection. Development Adapter `1.2.3` now applies a complete, documented
eleven-family Alignment Start parity audit rather than another single-symptom
patch. Full validation passed, and the exact source is now installed in the
Python 3.12.10 pipx runtime with protocol preflight complete. The product owner
approved one external fresh session, but its normalizer mixed actual events
with historical repository text; raw events were not retained, so the outcome
is invalid rather than successful evidence. A separately approved replay used
an event-scoped normalizer and passed the intended Start boundary: the fresh
session corrected one retryable Start input, reached `ready_for_decision`, and
stopped for human selection without an internal/unclassified error. The human
then selected a bounded deterministic post-selection slice. Development Adapter
`1.2.4` now validates Resolve and current-Agent self-review inputs before state
mutation and supports corrected same-process retry. At that checkpoint a live
post-selection implementation, validation, and self-review journey remained
separately gated; the current-session continuation below later closed that
current-host gate.
The independent installation-gate review found and corrected five remaining
downstream parity gaps covering reason identifiers, evidence length and allow-
list membership, observation list bounds, and duplicate observations.
Renewed focused, full-suite, governance, and atomic-retry validation now passes;
the exact current wheel is installed in the existing Python 3.12.10 pipx
environment and installed-runtime protocol/schema/atomic-retry preflight passes.
The human product owner designated the current ephemeral Codex session as the
sole approved replay, selected the recommended direction, and prohibited another
session or Agent. The current native journey bound that human selection through
Alignment Resolve, and focused plus complete 734-test Python 3.12 validation
passes. Current-Agent MCP self-review then completed with bounded advisory
observations and no AgentGov model/network calls or Adapter context retention.
This slice is complete; another host, NYC, release, and its then-undecided next
requirement remain outside it. The later human-selected reference proposal
generation seam is now implemented separately.

ADR-0014 and the strict Provider-capability, risk-route, and advisory-result
contracts now implement the model-free semantic-review boundary. Low risk does
not request semantic review; medium risk binds the active Coding Agent's
existing entitlement as disclosed self-review; high risk binds a qualifying
independent Reviewer or exposes exactly three unselected human choices without
silent downgrade. Cross-host fixtures exercise one vendor-neutral parser, but
perform no inference. The host-neutral active-Agent materializer seam is now
connected to the resolved `ReferenceAlignmentAdapter` journey: it invokes one
supplied host callback with normalized ephemeral context and accepts only the
exact advisory result. The next bounded dependency is installing that callback
in one real Coding Agent surface; an external independent Reviewer remains a
later optional integration.

Current product priority: turn the now-implemented installation, update,
onboarding, task admission, architecture context, changed-file, fresh-evidence,
completion, event, Monitor, handoff, and routing primitives into one automatic,
event-driven coding-agent governance experience. Ordinary users should request
work through their coding agent, confirm only real scope or authority
boundaries, and review an automatically updated protection and benefit
Dashboard. The existing command sequence remains a development and fallback
surface. ADR-0013 and
`docs/product-requirements-automatic-governance.md` own this direction; the
detailed ordering is in `docs/development-plan.md`.

Implemented foundations:

- one package-version source shared by build metadata, structured producer
  metadata, and `agentgov --version`;
- a strict local release-manifest contract and validator for future RC
  compatibility metadata;
- verified stable-release discovery, bounded download, SHA-256 validation,
  pipx upgrade, new-process continuation, and repository refresh through
  `agentgov update .`;
- separate tag-triggered stable and release-candidate publication of an
  immutable release manifest and universal wheel through GitHub Releases;
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

## Foundation implementation history

The sections below preserve the foundation and adoption sequencing that
produced stable 0.2.1 and the future 0.3 source work. They are not the current
priority order. `docs/development-plan.md` owns the active P0 coding-agent
development loop defined by ADR-0009.

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

Initial Taxi evidence on 2026-07-24:

- direct adoption exposed a Windows wheel build failure when the starter was
  cloned inside an already deeply nested target repository;
- direct installation from GitHub succeeded without vendoring the starter;
- `python -m agentgov` was more reliable than depending on a scripts directory
  being present on `PATH`;
- the correct repository check is
  `python -m agentgov check repository .`;
- a stale target-project virtual environment was unrelated to governance
  adoption and should not become a prerequisite for using AgentGov;
- the generated scaffold required real project adaptation after `adopt`;
  `FAIL=0` alone did not mean governance was complete.

The pilot is not complete until its timing, assistance, maintainer decisions,
and remaining release-boundary findings are recorded.

### Low-friction tool execution

Completed on 2026-07-25 for the v0.1 execution-model decision and Windows
rehearsal. ADR-0004 selects pipx-managed persistent isolation. The reviewed
`v0.1.0` GitHub Release now supplies the stable Quickstart pin and the
machine-readable update channel.

Goal:

Run AgentGov without coupling installation to the adopting repository's
virtual environment or requiring the starter source tree inside that
repository.

Acceptance signals:

- a Windows user can install or invoke the tool with one copyable command;
- the same interpreter runs all AgentGov subcommands;
- a broken project `.venv` does not block read-only inspection or adoption;
- the workflow does not install the adopting project's dependencies;
- update and uninstall behavior is documented;
- an isolated Windows pilot validates install, `inspect`, dry-run, `adopt`, and
  `check repository` from a realistically deep repository path.

Stop conditions:

- do not silently modify or replace the target project's environment;
- do not vendor the starter repository;
- do not require Docker, Node, or project-specific runtime dependencies;
- do not describe a workaround as the final supported experience until the
  full path is tested.

### Guided onboarding

Develop alongside low-friction tool execution. The primary onboarding
experience should guide a user from environment diagnosis through the first
honest repository check without requiring a governance expert beside them.
Static HTML remains reference material and a review surface; it should not be
the only source of state-dependent help.

Candidate commands:

```text
agentgov doctor .
agentgov onboard .
agentgov next .
```

Intended responsibilities:

- `doctor` performs read-only checks of the selected path, usable Python
  interpreter, Git repository context, Windows path risk, and existing
  governance state. It explains whether a detected project-environment problem
  actually blocks AgentGov.
- `onboard` sequences inspect, result explanation, adoption preview, explicit
  write confirmation, create-missing-only adoption, and the first repository
  check.
- `next` maps current findings to the smallest useful next action and explains
  whether it is deterministic work, incomplete evidence, a human judgment, or
  a completed development step. In future-0.3 source it preserves onboarding
  and repository-FAIL precedence, then routes strict session/event state to a
  dry-run `govern start`, `govern check`, `govern finish`, or
  `monitor development` without executing the command.

Interaction contract:

- default to read-only until the user explicitly confirms a planned write;
- show the exact target repository before confirmation;
- explain `MISSING`, `WARN`, `FAIL`, and `ADVISORY` in context;
- distinguish scaffold creation from completed project adaptation;
- never repair or replace the target project's virtual environment;
- never install target-project dependencies;
- never commit, push, merge, publish, release, deploy, or increase evaluation
  readiness automatically;
- provide `--non-interactive` behavior with stable exit codes for automation;
- make prompts and decisions injectable so fixture-based tests do not depend
  on a real terminal.

Acceptance signals:

- a first-time Windows user can complete install, diagnosis, inspect, preview,
  adopt, first check, and understand the next action without external
  assistance;
- cancellation at every confirmation leaves repository files unchanged;
- conflict, missing path, stale project environment, incomplete scaffold,
  deterministic failure, and advisory-only states have fixture-based tests;
- redirected input and non-interactive execution cannot accidentally authorize
  writes;
- a fresh Taxi rehearsal records timing, questions, wrong turns, assistance
  required, and final understanding;
- the primary Quickstart becomes shorter because it delegates adaptive guidance
  to the CLI rather than duplicating every branch in HTML.

Implementation order:

1. write a short ADR and interaction/result contracts (completed 2026-07-25);
2. implement the read-only `doctor` vertical slice (completed 2026-07-25);
3. implement `onboard --dry-run` without write authority (completed
   2026-07-25);
4. add explicit interactive confirmation and create-missing-only adoption
   (completed 2026-07-25);
5. implement finding-to-action mapping for `next` (completed 2026-07-25);
6. test a fresh Taxi adoption without live coaching;
7. update Quickstart only from verified pilot evidence.

Stop conditions:

- do not build an open-ended chatbot into the CLI;
- do not use an LLM to decide deterministic repository state;
- do not hide findings to make the workflow appear simpler;
- stop and request human judgment whenever ownership, authority, release, or
  deployment boundaries are unresolved.

### Profile-based adoption

Candidate profiles:

- `agentic-runtime`;
- `ml-system`;
- `decision-support`;
- `research-evaluation`.

Profiles may select templates and recommendations. They must not embed
project-specific business thresholds or runtime logic.

### Consumer CI workflow

Implemented as a bounded create-missing-only vertical slice on 2026-08-01.
`agentgov integrate github-actions` previews or explicitly creates a pinned,
read-only workflow, and `agentgov status` distinguishes managed, custom,
manual-only, and conflicting integration states while showing declared
capability usage. The workflow now verifies the fixed release wheel SHA-256.
Development version 0.2 also renders a deterministic Markdown status card for
GitHub job summaries. Version-aware workflow rendering leaves the stable 0.1
consumer workflow unchanged and adds the status card only to 0.2-or-newer
managed workflows.

The bounded upgrade slice now includes `agentgov plan upgrade-pr`, which
validates one stable release and produces a no-write `current`, `candidate`, or
`blocked` plan. It proposes only the exact one- or two-file managed-workflow
set. The
consumer-local `agentgov review upgrade` layer turns that plan into portable
JSON, Markdown UI, an exact patch, current status, gates, and a pending human
decision without applying the change. Managed 0.2+ consumer CI automatically
downloads the latest stable manifest, generates this bundle, appends the UI to
the job summary, and uploads the evidence artifact. Future 0.3 source contains
a separate schedule/dispatch-only Draft PR writer for compatible updates to
the two fixed workflow paths; the 0.2-to-0.3 file-creation migration remains a
human-reviewed bootstrap and no writer can merge.

Provide an adopting-repository workflow that:

- pins an agentgov version;
- runs repository checks;
- always writes a JSON report;
- uploads the report as an artifact;
- optionally adds a step summary;
- blocks only configured deterministic statuses;
- does not authorize release.

### Benefit evidence monitor

Implemented as a two-snapshot, read-only comparison in release candidate
`0.2.0rc1`. `agentgov benefits compare` reports explicit before, after, and
matched finding denominators plus status transitions. It does not infer
causality, prevented incidents, time savings, governance coverage, or ROI.

The next slice requires real NYC CI observations and a separate event contract
for project-test status, PR outcome, timestamps, human disposition, and
retention before trend reporting is admitted.

### Release review evidence

Implemented in local release candidate 0.2.0rc1. `agentgov review release`
accepts an exact wheel, immutable manifest, source repository, and consumer
pilot, then creates a new review bundle containing source tests, isolated-wheel
checks, consumer status, and upgrade-policy evidence. Artifact construction
remains a separate release stage, and the command never records a human
decision or authorizes Git, publication, release, or deployment.

### Consumer upgrade review evidence

Implemented in local release candidate 0.2.0rc1. `agentgov review upgrade`
runs against the adopting repository and a reviewed release manifest. It
creates a new local/CI bundle showing the current and proposed versions, exact
managed-workflow hashes and patch, consumer findings, deterministic gates, and
the pending consumer decision. Release-candidate manifests are visibly blocked.
Managed 0.2+ consumer CI publishes the review as a job summary and artifact.
The command does not apply the patch, run project tests, create a branch or
pull request, merge, release, or deploy.

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

Released on 2026-07-25.

Delivered:

- pipx-isolated installation and update lifecycle;
- guided diagnosis, onboarding, inspection, and next-action commands;
- immutable GitHub Release manifest with fixed-tag wheel URL and SHA-256;
- one-command verified software update followed by bounded repository refresh;
- explicit interruption, failure, partial-update, and recovery reporting;
- complete local suite with 302 tests passing and one platform-limited skip;
- successful human-authorized `v0.1.0` tag and GitHub Release.

Carried forward after the release:

- complete the fresh uncoached human adoption pilot;
- finish the Taxi cross-domain pilot record and maintainer decisions;
- pilot the reusable consumer CI workflow in NYC and record the result;
- verify the supported operating-system and Python matrix continuously in CI.

## Next Recommended Starting Point

Continue productizing the implemented ADR-0009 loop:

1. [Completed internal pilot] Preserve the installed-build independent
   repository evidence, including actual Coding Agent context consumption,
   fail-closed Skill and validation-artifact findings, and the explicit limit
   that this was not an uncoached human study;
2. [Completed development preview] Define the explicit redacted event-export
   contract so local history can be carried into CI without pretending the CI
   replay observed development. The metadata-only bundle is immutable,
   integrity-checked, explicitly confirmed, and now supports honest
   `exported_development` and `combined` Monitor views;
3. [Completed prerequisite] Give development source a distinct
   `0.3.0.dev0` runtime and bundled-metadata identity while retaining stable
   0.2.1 as the published consumer fact;
4. [Completed prerequisite] Synchronize README, status, plans, public HTML,
   localized guides, sample reports, release facts, and protecting tests; keep
   AgentGov's product page primary and AI Radar as a bounded origin reference;
   publish Portfolio evidence by applying the shared reference layout directly
   to authoritative Markdown, rather than raw Markdown, conflicting proxy
   outputs, or project-root-escaping schema links;
5. [Completed development preview] Wire the static Monitor as a default-off
   GitHub Actions artifact. The future 0.3 managed workflow now requires an
   explicit manual-dispatch boolean, accepts only an optional validated
   metadata-only development export plus actor-validated CI events, and uploads
   only the self-contained HTML read model. Stable workflow bytes, release
   identity, and consumer files remain unchanged;
6. [Low-level guided routing and installed rehearsal implemented] Converge installation, update,
   onboarding, task admission, and Monitor generation on the same small guided
   workflow without hidden hooks or daemon authority. `agentgov next` now
   bridges onboarding and deterministic repository failures into strict
   start/check/finish/Monitor session routing. An exact `0.3.0.dev0` wheel
   completed the independent zero-task, multiple-task, and full lifecycle
   rehearsal without `next` changing Git state. A truthful pre-install
   bootstrap boundary is now decided by ADR-0011: fixed stable installation
   precedes the CLI, while installed `update --check` remains separate from
   `next`. Runtime update routing remains blocked until a reviewed stable
   artifact and non-looping verified-session handoff exist. ADR-0012's
   event-only, pointer-preserving handoff and separate `--replace-active`
   rollover are now implemented in development source. The exact `0.3.0rc1`
   wheel completed verified finish, Monitor, handoff, zero/one/many rollover,
   and exact `REPLACE` in independent repositories without source-path leakage;
7. [Release candidate published] Preserve `v0.3.0rc1` as immutable evidence of
   the low-level lifecycle primitives; do not treat it as proof of the final
   user experience;
8. [Codex hooks Adapter implemented in development source] Preserve the strict
   `agentgov dev --stream` transport while mapping Codex `SessionStart`,
   `UserPromptSubmit`, `PermissionRequest`, `PostToolUse`, and `Stop` through a
   create-only, separately trusted project hook integration. Add another host
   only when portability evidence requires it;
9. [Proactive minimal-input decision contracts implemented; native authenticated
   UI remains] Preserve vendor-neutral capability, interaction-request,
   decision-prompt, and decision-result contracts. Capable hosts proactively
   present one recommended single-select choice and return only its exact
   transition; the reference terminal uses one number with no free text. Codex
   keeps its normal human tool permission prompt, but Hooks do not provide
   arbitrary trusted task/scope/completion button callbacks;
10. [Structured task admission and risk routing implemented] Preserve the strict
    vendor-neutral proposal and admission-plan contracts. A proactive numeric
    human-review selection may create the exact manually reviewed low-risk
    task; exact interactive `ADMIT` remains a fallback, while a
    clean human-owned standing policy may non-interactively fast-track only its
    narrow declared envelope. No-write and exact active-task continuation need
    no admission or interruption. The reference host-side natural-language
    proposal seam is implemented with an offline materializer fixture.
    Development Codex `1.3.0` connects the current Agent and native MCP form;
    local installation/preflight pass, while external live proof and other
    hosts remain separate work;
11. [Friction budget implemented] Preserve zero interruptions for no-write,
    active-task, and fast-track routes, at most one for ordinary bounded
    review, and full review for material characteristics;
12. [Governed clarification implemented] Preserve the current center while
    material meaning is unsettled, ask one natural-language question per turn,
    keep normalized discussion turns outside the governance-decision budget,
    and offer one digest-bound direction choice only after options stabilize.
    The foreground Adapter stream now returns those prompts automatically from
    strict normalized records, with no restart-persistence claim;
13. [Native MCP Adapter, proposal-review installation, and local preflight
    implemented; external replay remains] Preserve the five-tool normalized
    alignment/self-review journey and capability-gated sixth proposal tool,
    explicit foreground handle, exact pending bindings, and create-missing-only
    Codex config. Ordinary users add no protocol JSON, protocol question IDs,
    repeat confirmation, or second-model setup. Known invalid normalized input
    now receives privacy-safe structured field/rule/retry diagnostics without
    partial state. The exact `1.3.0` source is installed and locally preflighted;
    run a fresh external replay only after separate human approval. Another MCP
    host and the optional independent high-risk Reviewer path remain later
    choices;
14. [Per-cycle automation implemented; richer views remain] Extend the
   automatically refreshed Live Sessions, Protection Events, and Task Detail
   views with explicit resolution links, and add denominator-aware
   Benefit and Learning views without turning the Dashboard into a source of
   truth or a score;
15. [Gate before NYC] Prove one ordinary low-risk task in an independent
    non-NYC repository without hand-authored internal JSON, repeated state
    queries, manual lifecycle command composition, or special confirmation
    words in the primary UI;
16. [External feedback after the gate] Use NYC as the first real consumer,
    keep NYC-specific policy local, classify feedback before admission, and
    modify AgentGov only for general gaps;
17. Keep stable promotion, consumer migration, publication, and deployment as
    later, separate human-approved actions.

The automatic independent rehearsal, uncoached adoption evidence, NYC feedback
record, stable 0.3 promotion, NYC migration, and PyPI decision remain open.
NYC feedback cannot replace general product admission, and the low-level
command sequence cannot replace the automatic user experience as product core.

### Next session after the 2026-08-07 checkpoint

Development Adapter `1.3.0`, the current-Agent proposal materializer, native
MCP proposal-review form, strict admission boundary, and installed-runtime
preflight are complete. The first two authorized external attempts did not
measure that Adapter path: the corrected bridge reached `turn/start`, then the
standalone Codex App Server closed before returning a form or tool call. The
same binary subsequently reported `Not logged in`, with no inheritable Codex or
OpenAI credential environment variable. This is a host-authentication gate,
not Adapter success or failure.

Resume in this order:

1. review and separately authorize repair of the standalone Codex host's
   authentication; do not change AgentGov Core, repository scope, or product
   authority to work around the host failure;
2. verify login status and complete a local initialization/thread/MCP
   capability preflight without sending a task;
3. obtain separate approval for one fresh event-level proposal-review replay;
4. if the native form appears, let the human review the exact proposal and
   record only the selected transition; do not implement an admitted proposal
   without another explicit product-owner decision;
5. review the resulting evidence with the product owner before selecting the
   next requirement. Another host, the independent non-NYC rehearsal, NYC,
   stable promotion, release, and deployment remain later gates.

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
