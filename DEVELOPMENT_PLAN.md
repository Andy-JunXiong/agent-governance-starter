# Agent Governance Starter Kit Development Plan

Last updated: 2026-08-21

## Purpose

This is the strategic development plan for the repository. It owns product
direction, priority sequencing, and strategic acceptance and stop conditions;
it is not the current execution dashboard or the historical evidence ledger.

Use it to answer:

1. What is the project building?
2. Which top-level product priorities and capability tracks come first?
3. What strategic acceptance and stop conditions constrain those tracks?
4. What evidence is required before a version is considered stable?

Current capability facts, the active slice, validation state, incomplete work,
blockers, and the next product review belong in [`STATUS.md`](STATUS.md).
Append-only session evidence lives under `docs/development-log/`. Exact task
scope and admission live in `governance/tasks/`; durable architecture decisions
belong in `docs/adr/`. None of these planning statements grants execution or
external authority.

Documentation State Separation v1 establishes these ownership rules going
forward. Historical Documentation Migration v1 relocates only clearly
section-bounded checkpoint and implementation-history passages into the dated,
source-labeled migration record while preserving their factual wording and
evidence paths. Do not add new session-level history to this plan.

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

ADR-0016 now constrains this direction to a minimum sufficient Kernel. The
Kernel owns governance meaning and state semantics; Policy, Application,
Adapter, Consumer Context, and Experiment remain separate responsibilities.
Enforcement is proved per transition. The minimum journey is `Propose -> Admit
-> Implement -> Scope/Evidence Check -> Completion Verified -> Bounded
Handoff`, and new Kernel promotion is paused until a structured real-consumer
counterexample demonstrates a lost distinction or governed outcome.

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

## Current-state reference

Current release, capability, validation, blocker, and active-slice reality is
owned by [`STATUS.md`](STATUS.md). The superseded snapshot and foundation
implementation-history passages previously stored here are preserved verbatim,
with source labels, in the
[2026-08-14 historical migration record](docs/development-log/2026-08-14-historical-migration.md).
The product direction and priority sequence below remain authoritative for
strategy only.

The current bounded relationship among Harness Contract v1, First Deviation,
and the sanitized AIRBNB fixture remains documented in `STATUS.md` and the
linked contract and dated evidence. This strategic plan does not restate that
completed-session evidence.
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

### README product entry and documentation responsibility split

Implemented as bounded v1 on 2026-08-21 through human-admitted task
`p1-readme-product-entry-refactor-v1`. Before migration, all 27 prior README
sections were inventoried and classified by their owning responsibility:

- **Product**: concise purpose, audience, value, boundaries, release channels,
  one governed workflow, and the shortest verified path to first use;
- **Reference**: command, purpose, expected result, and authority boundary;
- **Architecture**: durable design meaning owned by architecture guides and
  ADRs, with only one overview diagram retained in README;
- **Evidence**: version chronology, experiments, consumer replays, failures,
  recoveries, and validation owned by `STATUS.md` and dated development logs.

The resulting README is a concise product entry with 12 second-level sections,
one first-screen portfolio showcase, and one overview architecture diagram.
The showcase follows the shared GLAP and NYC pattern with CI and Live Demo
badges, a linked hero, one centered product-story caption, four focused product
links, and an evidence-boundary note. Detailed command, architecture, reviewer,
and chronological evidence content now routes to existing topical documents,
`STATUS.md`, and dated evidence. No new catch-all reference was created.
Documentation tests protect release identity, authority, links, and unique
claims at their owning surfaces instead of requiring those claims to be
duplicated in README.

Reader-centered acceptance signals:

- within two to three minutes, a new reader can explain what AgentGov is, the
  problem it solves, what stable can do, what current development source adds,
  how to run the shortest relevant journey, and where to read deeper material;
- the first screen presents four focused product routes: the interactive
  product, the governed walkthrough, the evidence portfolio, and Quickstart;
- `Interview snapshot` becomes a neutral product overview, while interview and
  portfolio material remains available under reviewer documentation;
- stable, published prerelease, and current development-source states appear
  early and remain distinct, including development-only doctor behavior;
- README retains one architecture diagram and routes detailed design to its
  existing architecture owner;
- documentation tests, link integrity, release identity, unique-claim
  preservation, and source-of-truth ownership pass after the refactor.

The static structure and ownership signals are implemented. The two-to-three-
minute comprehension outcome remains pending until a genuinely unbriefed human
reviews the result; no automated test may claim that outcome.

A result around 400–650 lines or 3,000–4,500 words is a useful review signal,
not a hard acceptance threshold. Clarity and preservation of required release,
authority, and evidence boundaries take precedence over a size target.

Stop conditions:

- stop if a section has no confirmed destination or contains a unique claim
  whose owner is unclear;
- stop if stable, prerelease, and development-source behavior cannot be stated
  without ambiguity;
- do not create a new catch-all reference, rewrite historical evidence, or use
  this backlog entry as implementation, Git, publication, or release authority.

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

Implemented in development source as the optional standalone
`agentgov.evidence-freshness` 1.0 contract and
`agentgov check evidence-freshness` command. The first bounded slice records
review dates, explicit expiry, policy validity, declared invalidating events,
observed events, and explicit applicability.

The deterministic semantics are:

- `WARN` when a declared review date is due;
- `FAIL` for malformed records, future review facts, explicit expiry,
  superseded policy, or an exact invalidation-event match;
- `ADVISORY` when policy validity is unknown;
- `NOT_APPLICABLE` only when the record explicitly declares it;
- `PASS` when no declared invalidating condition is active.

Elapsed time beyond a review date never becomes expiry by inference. The
checker reads one record and does not discover change events, refresh evidence,
or automatically join freshness into repository, release, upgrade, or report
flows. Any such integration requires real use evidence and a separately
admitted contract.

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

## Next product review reference

The current product review, active slice, incomplete work, blockers, and
pending validation are owned by [`STATUS.md`](STATUS.md). Strategic ordering
continues in the priority sections above and in
[`docs/development-plan.md`](docs/development-plan.md). The superseded
checkpoint narrative formerly under `Next Recommended Starting Point` is
preserved in the
[2026-08-14 historical migration record](docs/development-log/2026-08-14-historical-migration.md).
This pointer authorizes no follow-on task or external action.
## Validation Baseline

Required baseline command:

```powershell
$env:PYTHONPATH = "src"
python -m unittest discover -s tests -v
```

The project requires Python 3.11 or newer. Validation executed with an older
interpreter is not a release baseline.

## Documentation Rule

- `AGENTS.md` owns operating rules, authority boundaries, and development
  protocol; update it only when those rules change.
- `governance/tasks/*.json` owns exact task scope, admission, and recorded task
  decisions; it grants no broader authority.
- `docs/adr/` and durable contracts own architecture decisions and invariants.
- `DEVELOPMENT_PLAN.md` owns strategic direction, priority sequencing, and
  strategic acceptance or stop conditions; update it only when those change.
- `STATUS.md` owns concise current repository reality and is updated at each
  formal development closeout.
- dated files under `docs/development-log/` preserve append-only session
  evidence at stable paths.
- Other `docs/` files own detailed guidance, pilots, migrations, and reports.

Plans, status entries, logs, and roadmap items do not authorize tasks, Git,
publication, release, deployment, or external actions. Historical migration
and archive automation remain outside Documentation State Separation v1.
