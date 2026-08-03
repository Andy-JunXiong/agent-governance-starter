# Agent Governance Starter Kit Status

Last verified: 2026-08-03

## Current state

- Version: published stable `0.2.1`; development source `0.3.0.dev0`.
- Maturity: experimental and suitable for repository-level evaluation.
- Canonical capability layout: `governance/`.
- Legacy `prompt-governance/` input remains a bounded, read-only compatibility
  surface.
- Portfolio links now target project-base-aware HTML outputs generated from
  authoritative repository Markdown. Commit `743f3b3` corrected a Jekyll
  same-destination collision by putting the AgentGov layout directly on those
  Markdown sources. The Pages build and all linked reference/schema surfaces
  are publicly verified; published schema copies remain byte-checked against
  their source contracts.
- Merge, publish, release, and deployment remain separate human-authorized
  actions.

## Product direction

- ADR-0009 makes development-time governance of coding-agent requirements,
  architecture context, implementation scope, verification evidence, and
  completion reconciliation the product core.
- PR and CI reporting, benefit evidence, and upgrade automation remain retained
  backstop and delivery capabilities rather than the primary user interaction.
- This direction was revalidated against clean scoped governance files from AI
  Radar commit `3a9323cb2a9ef575da42d29fb17d330ef872afd3`; reuse and exclusion
  decisions are recorded in `docs/ai-radar-extraction-map.md`.
- Task contract 1.1 and read-only `agentgov check task` are implemented in
  development source with low-risk compact and full standard profiles, safe
  references, validation commands, and objective-alignment advisory review.
- Read-only `agentgov context task` now derives an in-memory Registry and emits
  terminal, JSON, or Markdown task context with artifact-owned Skill routing,
  explicit references, path-linked capability governance, selection reasons,
  source hashes, known limits, and denied mutation authority.
- Guided `agentgov govern start` is implemented in development source. It can
  select exactly one admitted task or preview a low-risk compact task, requires
  exact interactive confirmation, derives the governance context, records the
  comparison base, and writes a strict untracked single-task working-copy
  pointer plus one immutable start event. Automatic GitHub Actions artifact
  wiring is not implemented.
- Read-only `agentgov check scope` now inventories staged, unstaged, deleted,
  renamed, and non-ignored untracked paths and applies segment-aware
  include/exclude rules. Explicit architecture references remain ADVISORY.
  The low-level scope-only report remains working-tree-specific; explicit
  exception records and action-loop self-reporting are not implemented yet.
- `agentgov govern check` now appends a privacy-bounded local scope event.
  `agentgov govern finish --base` captures canonical committed, staged,
  unstaged, renamed, and non-ignored untracked identities, runs every declared
  validation command, and reconciles `verified` versus `needs_evidence`.
  Evidence and one-file events live under untracked `.agentgov/` local state;
  tracked `.agentgov/` and `.gitignore` changes remain visible. These local
  records are not CI-visible unless a user explicitly creates and transfers a
  redacted development export.
- With an active session, `govern check` defaults to its task and `govern
  finish` defaults to its task and exact base. Changed task content fails
  closed until a reviewed replacement start. Untracked `.agentgov/` tool state
  is now consistently excluded by both scope and fresh-evidence inventories;
  tracked local state remains visible.
- `agentgov monitor development` now generates a self-contained static
  Overview, Activity Timeline, and Task Detail from validated local, exported,
  CI-only, or combined sources. Every output displays partial history, source
  counts, per-event source labels, missing inputs, unavailable cross-stage
  discovery, and separate observed, inferred, and unknown claims.
- `agentgov export development` now previews and, after exact interactive
  `EXPORT` confirmation, creates an immutable metadata-only bundle. It removes
  actor labels and local evidence references; rejects CI events, sensitive
  token/path shapes, tracked/existing/outside/symlink output, and integrity
  drift; and grants no upload, workflow, Git, approval, or deployment authority.
- The first exact-wheel independent development pilot is complete. A fresh
  isolated installation routed eight relevant governance artifacts; the Coding
  Agent read them, changed only the admitted Python source, passed scope and
  validation, reached `verified`, and produced a four-event Monitor. The pilot
  also preserved fail-closed evidence for an invalid Skill and unignored
  `__pycache__` output instead of weakening checks.
- The pilot is internal evidence, not uncoached human or general effectiveness
  evidence. Its source-identity blocker is resolved: development builds now
  report `0.3.0.dev0` instead of stable `0.2.1`. Actionable
  validation-artifact readiness guidance without editing `.gitignore` remains
  a pre-release action.

## Development-source P0 preview

- Runtime and bundled compatibility metadata now use `0.3.0.dev0` with the
  `development` channel. Published stable 0.2.1 documentation and consumer
  pins remain unchanged; no release artifact or digest is claimed.

- `schemas/development-task.schema.json` defines a strict, vendor-neutral task
  identity with compact/standard profiles, exact scope, acceptance and
  validation commands, owner, risk, and human decision. Standard adds parent
  objective, goal boundaries, architecture, approval, and stop conditions.
- `schemas/development-session.schema.json` defines the local task/base pointer;
  task, ADR, invariant, AGENTS.md, and Skill content remain artifact-owned.
- `agentgov check task <task.json> --repository .` validates the contract and
  readable repository-local references without modifying repository or Git
  state.
- Draft and incomplete tasks retain WARN and ADVISORY findings. Admission and
  approval inconsistencies, unsafe paths, and broken declared references fail
  deterministically.
- `governance/tasks/p0-minimal-task-contract.json` dogfoods the contract for
  this slice and links `AG-DRIFT-001`, ADR-0009, and the corrected P0 plan.
- `governance/tasks/p0-context-selection.json` admits the first Phase 1 slice;
  `schemas/development-context.schema.json` defines its derived output.
- This interface is not published in stable 0.2.1 and is not yet added to
  initialization, repository-wide checking, task Markdown/JSON reporting, or
  CI replay.

## Stable foundations

- Installable, zero-runtime-dependency Python CLI.
- Package metadata and `agentgov --version` derive from the single runtime
  version declared by `agentgov.__version__`.
- Strict release-manifest schema, fixtures, and
  `agentgov check release-manifest` validation.
- Verified one-command update flow: stable-release discovery, bounded temporary
  download, SHA-256 verification, pipx upgrade, new-process relaunch,
  repository refresh, explicit terminal states, and recovery guidance.
- Separate tag-triggered stable and release-candidate workflows publish the
  universal wheel and immutable machine-readable manifest. RC tags create a
  GitHub Pre-release and cannot enter the stable consumer update channel.
- Deterministic repository, capability, reference, evaluation, agent-skill,
  and artifact-drift checks.
- Explicit `PASS`, `WARN`, `FAIL`, and `ADVISORY` semantics.
- Markdown, JSON, and HTML report surfaces.
- Read-only `agentgov status` visibility for adoption, CI state, governed
  capabilities, active surfaces, repository findings, and the next action,
  including a portable Markdown view for GitHub job summaries.
- Create-missing-only `agentgov integrate github-actions` support for a pinned,
  read-only consumer CI workflow with exact interactive confirmation.
- Read-only `agentgov plan upgrade-pr` contract for current, candidate, and
  blocked managed-workflow upgrades with exact hashes and no Git authority.
- Read-only `agentgov benefits compare` evidence for two repository-report
  snapshots with explicit finding denominators and no causal or ROI claim.
- Create-new-only `agentgov review release` bundles exact wheel, manifest,
  source-test, consumer-check, status, and upgrade-policy evidence while leaving
  the approve/change/reject decision pending.
- Consumer-local `agentgov review upgrade` bundles a stable upgrade plan,
  current status, exact workflow patch, deterministic gates, and a pending
  project-owner decision without applying the proposed change.
- Managed 0.2+ consumer CI automatically publishes that upgrade review in the
  GitHub job summary and report artifact while retaining read-only permissions.
- Future 0.3 source separates read-only governance from its schedule/dispatch
  Draft PR writer and bounds upgrade plans to the two exact managed workflow
  paths. This behavior is not yet published or adopted by NYC.
- Windows and Ubuntu CI definitions for Python 3.11, 3.12, and 3.13.

## Current milestone

Future-0.3 development-governance integration and pre-release evidence:

- Governance Inventory contract and zero-dependency validator implemented;
- canonical manifest, owner, identity, exclusion, and safe-path closure;
- evaluation and artifact contract claims close to Inventory declarations
  without filename inference;
- deterministic orphan failures with legacy-compatible non-cascading behavior;
- strict capability control mappings with explicit applicability, enforcement
  mode, ownership, exception authority, and safe evidence references;
- deterministic control identity and reference checks paired with an explicit
  effectiveness advisory;
- strict capability dependency declarations with Inventory-linked endpoints,
  deterministic self-dependency and cycle rejection, and optional explicit
  readiness floors;
- readiness differences remain non-blocking when no minimum is declared;
- explicit completeness advisories without automatic discovery claims;
- implementation, review, supported CI, and human-controlled integration are
  complete on `main`.
- the NYC Taxi repository is the first consumer-CI pilot: AgentGov validation
  now runs on pull requests and pushes, publishes a GitHub job summary, and
  uploads machine-readable and Markdown evidence without authorizing merge,
  release, or deployment.
- ADR-0006 rejects a general semantic-model implementation until a verified
  cross-domain gap survives existing-contract-first review; no semantic
  schema, checker, report field, or migration has been added.

## Remaining TODOs

- [x] Design and test a low-friction installation path that keeps AgentGov
  independent from the adopting repository's Python environment. ADR-0004
  selects persistent isolated tool execution through pipx for v0.1; the
  Windows rehearsal covered Git install, inspect, dry-run, adopt, repository
  check, upgrade, and uninstall without using the target `.venv`.
- [ ] Complete guided onboarding so a first-time user can finish the safe path
  without an AgentGov expert beside them. ADR-0005 now defines the bounded
  `doctor`, `onboard`, and `next` interaction contracts, and the first
  read-only `agentgov doctor .` slice is implemented.
  `agentgov onboard . --dry-run` now combines diagnosis, exact target
  disclosure, create/preserve preview, and strict non-interactive write denial.
  Interactive onboarding now accepts only exact `ADOPT` from a real terminal,
  revalidates the complete reviewed plan before writing, and creates only the
  files shown in that plan. `agentgov next .` now selects one read-only action
  using fixed conflict, adoption, FAIL, WARN, ADVISORY, and complete
  precedence. An isolated automated deep-path Windows rehearsal now covers the
  complete installed sequence and corrected `onboard` to run the first
  repository check automatically. Remaining work is a fresh uncoached human
  pilot.
  The facilitator protocol, participant-only handout, and observation record
  now exercise the current `doctor` → `onboard` → `next` path; a fresh human
  session is still required.
- [ ] Convert the Taxi adoption notes into a completed cross-domain pilot
  record, including timing, assistance required, unresolved release-gate
  findings, and final maintainer decisions. A bounded semantic-relation gap
  analysis record is prepared under `docs/experiments/semantic-relations/`;
  it contains no invented Taxi observations.
- [x] Decide whether the supported one-command experience should use an
  isolated tool installer, an ephemeral runner, or a small bootstrap command.
  The isolated installer is selected and the primary Quickstart now pins the
  reviewed `v0.1.0` Release wheel instead of mutable Git `main`.
- [x] Publish the first stable software-update channel. `agentgov update .`
  discovers the latest stable manifest, verifies the fixed-tag wheel digest,
  upgrades the pipx environment, relaunches the updated executable, and
  continues the bounded repository refresh.

## Known gaps

- Taxi supplied initial cross-domain adoption evidence, but the pilot record
  and maintainer decisions are not complete.
- Published 0.2.1 consumer CI reports stable-release update state but cannot
  open or merge dependency-update pull requests. The future 0.3 source writer
  remains unavailable to consumers until a separately approved release and
  one-time workflow migration.
- Stable `v0.2.1` is published. Its consumer workflow preserves the canonical
  wheel filename found missing by the first NYC 0.2 run.
- The first NYC 0.2 run exposed that pip rejects a valid wheel renamed to
  `agentgov.whl`; stable 0.2.1 corrected the generated workflow. No NYC
  business or production workflow was involved.
- Benefit evidence currently compares two downloaded report snapshots. It does
  not yet observe project-test outcomes, PR disposition, runtime incidents,
  human handling time, or false-positive decisions.
- Installation still depends on Python 3.11 or newer and pipx. GitHub Release
  is the current stable distribution channel; PyPI publication is not yet
  configured.
- Static HTML remains reference material and cannot adapt to repository state.
  The bilingual Quickstarts now label guided onboarding as a development
  preview; the primary path remains unchanged until an uncoached human pilot.
- Dependency risk propagation and repository profiles are not implemented.
- Output-level identity and evidence mapping remain an unverified cross-domain
  question. Existing schema references must be evaluated before any new
  semantic relation contract.
- Legacy removal release remains undecided.
- A successful check does not prove semantic governance sufficiency.

## Validation

Published-reference-page validation on 2026-08-03:

- 511 unit tests passed with one platform-limited skip;
- 11 focused Portfolio and reference-page tests passed;
- the admitted reference-page task returned
  `PASS=6 WARN=0 FAIL=0 ADVISORY=1`, its working-copy scope returned
  `PASS=29 FAIL=0 ADVISORY=1`, and repository governance returned
  `PASS=16 WARN=2 FAIL=0 ADVISORY=4`;
- no Portfolio link ends in `.md` or starts with `../`, every local target
  exists, and both published schema JSON files are byte-identical to their
  authoritative source schemas;
- the first live Pages build exposed a same-destination layout collision for
  Markdown-backed HTML; follow-up commit `743f3b3` built successfully, all 13
  HTML reference pages returned 200 with the AgentGov layout, both schema JSON
  URLs returned valid JSON, and the Portfolio retained zero `.md` or `../`
  hrefs.

Documentation and development-source validation on 2026-08-03:

- 507 unit tests passed with one platform-limited skip;
- 46 focused product-site, portfolio, user-documentation, report, adoption, and
  documentation-freshness tests passed;
- all 12 public HTML files had resolvable repository-relative links;
- the public README and HTML surfaces no longer advertise the v0.1 wheel,
  mutable `main` installation, or the independent consumer project;
- `git diff --check` passed with only Git's existing line-ending notice for the
  Chinese HTML quickstart.
- the admitted documentation-sync task returned
  `PASS=6 WARN=0 FAIL=0 ADVISORY=1`, its combined working-copy scope returned
  `PASS=35 FAIL=0 ADVISORY=1`, and repository governance returned
  `PASS=16 WARN=2 FAIL=0 ADVISORY=4`.

Development-source identity validation on 2026-08-03:

- 497 unit tests passed with one platform-limited skip;
- focused package, release-metadata, and update validation passed 36 tests;
- an isolated wheel built as
  `agent_governance_starter-0.3.0.dev0-py3-none-any.whl`, installed with no
  runtime dependencies, and reported `agentgov 0.3.0.dev0`;
- bundled development release metadata passed its strict manifest contract;
- the admitted identity task returned `PASS=6 WARN=0 FAIL=0 ADVISORY=1`, and
  its working-copy scope returned `PASS=12 FAIL=0 ADVISORY=1`;
- repository self-check returned `PASS=16 WARN=2 FAIL=0 ADVISORY=4`;
- `git diff --check` passed;
- no workflow mutation, consumer migration, commit, push, tag, release,
  publication, or artifact upload was performed.

Development-source Phase 7 validation on 2026-08-03:

- 496 unit tests passed with one platform-limited skip;
- repository self-check returned `PASS=16 WARN=2 FAIL=0 ADVISORY=4`;
- the admitted redacted-export task returned
  `PASS=6 WARN=0 FAIL=0 ADVISORY=1`;
- export and four-scope Monitor CLI help rendered successfully;
- `git diff --check` passed;
- no commit, push, release, workflow mutation, artifact upload, or external
  telemetry action was performed.

Consumer CI pilot validation on 2026-08-01:

- 353 unit tests passed with the active supported interpreter; one
  platform-limited symbolic-link test was skipped;
- repository self-check completed with
  `PASS=16 WARN=2 FAIL=0 ADVISORY=4`;
- NYC dry-run revalidation returned `PRESERVE=1` and `CONFLICT=0` for the
  generated workflow;
- development-source status classified NYC CI as `managed` and pull-request
  visibility as active;
- the installed stable AgentGov 0.1.0 validated NYC with
  `PASS=17 WARN=1 FAIL=0 ADVISORY=4`;
- the broken pipx launcher was rebuilt against Python 3.11.9 from the original
  fixed v0.1.0 release URL and `agentgov --version` works again;
- `git diff --check` passed in both repositories; NYC emitted only line-ending
  warnings for unrelated pre-existing changes.

Release-candidate wheel validation on 2026-08-02:

- 370 unit tests passed with Python 3.11; one platform-limited symbolic-link
  test was skipped;
- built `agent_governance_starter-0.2.0rc1-py3-none-any.whl` in an isolated
  Python 3.11 environment;
- wheel SHA-256 was
  `504a80878ee3f13b0ab7162b194ab1ec1aa612b5a27f528ddebe93c40bf18bdd`;
- the wheel contains the status, consumer-CI, upgrade-PR, benefit, and release
  review modules plus their machine-readable schemas;
- an immutable rehearsal manifest passed validation, declared compatibility
  from stable 0.1.0, retained layout 1.0, declared no repository migrations,
  and matched the wheel digest;
- a fresh wheel-only environment reported `agentgov 0.2.0rc1`, validated NYC
  with `PASS=17 WARN=1 FAIL=0 ADVISORY=4`, and rendered its status as portable
  Markdown;
- NYC upgrade planning returned `blocked` because release-candidate manifests
  cannot authorize a consumer upgrade proposal; only a validated stable
  manifest may produce a candidate;
- `agentgov review release` produced an atomic NYC evidence bundle with all
  seven automated gates passing, state `ready_for_human_review`, and the human
  decision left `pending`;
- consumer-local NYC upgrade review correctly reported `blocked` for the RC
  manifest, preserved a passing NYC governance check, and applied no workflow
  or Git change;
- stable 0.1 workflow rendering remained byte-exact with NYC at SHA-256
  `9fa83b71b498b058afb2f5bdf777b23ed27933995faedc546faf4321f3974be8`,
  while the 0.2 preview retained `contents: read` and added one automatic
  consumer upgrade review.

Semantic-relation admission documentation validation on 2026-07-27:

- 302 unit tests passed with the active supported interpreter; one
  platform-limited symbolic-link test was skipped;
- repository self-check completed with
  `PASS=16 WARN=2 FAIL=0 ADVISORY=4`;
- `git diff --check` passed;
- no semantic schema, checker, CLI behavior, or report contract changed.

Isolated execution validation on 2026-07-25:

- Windows, Python 3.12.10, and pipx 1.11.1;
- public Git install into a pipx-managed environment;
- deep-path inspect, dry-run, create-missing-only adoption, and repository
  check completed with `PASS=14 WARN=4 FAIL=0 ADVISORY=4`;
- the unrelated target `.venv` was not used or modified;
- upgrade and uninstall behavior completed successfully.

Guided onboarding validation on 2026-07-25:

- ADR-0005 fixes read-only defaults, non-interactive write denial, target
  disclosure, and human authority boundaries;
- `agentgov doctor .` reports interpreter support, Git context, Windows path
  risk, project `.venv` signals, and governance adoption state;
- text and strict JSON v1.0 results preserve deterministic versus advisory
  classification and stable exit semantics;
- adoption, doctor, onboarding-plan, and next-action JSON keep contract version
  separate from the producing AgentGov version in strict `tool` metadata;
- `governance/artifacts` is treated as optional explicit export output rather
  than an unresolved core onboarding path;
- fixture tests cover healthy, unconfigured, conflict, stale `.venv`, old
  Python, deep Windows path, no-write, JSON, and missing-path behavior.
- `agentgov onboard . --dry-run` produces text or strict JSON v1.0 plans,
  preserves existing files and blocks conflicts;
- non-interactive onboarding previews explicitly set `write_authorized` to
  false and leave repository files, project environments, and Git state
  unchanged.
- redirected input, EOF, cancellation, lowercase or alternative confirmation,
  and `--non-interactive` execution cannot authorize writes;
- exact interactive `ADOPT` applies only the reviewed plan using exclusive
  file creation after a complete conflict preflight; existing files are never
  overwritten.
- `agentgov next .` returns exactly one deterministic-work,
  incomplete-evidence, human-judgment, or complete action with its source
  finding and blocking semantics;
- text and strict JSON v1.0 next-action results never execute the selected
  command or authorize repository, Git, or release changes.
- installed deep-path rehearsal completed doctor, preview, confirmed creation,
  automatic first check, and next-action selection while leaving the target
  `.venv` empty;
- the bilingual HTML Quickstarts expose this sequence only as a development
  preview until a fresh uncoached human pilot is recorded.

Stable update and release validation on 2026-07-25:

- 302 unit tests passed on Python 3.12; one platform-limited symbolic-link test
  was skipped;
- the final universal wheel built successfully;
- GitHub Actions release run `30157093313` completed successfully;
- GitHub Release `v0.1.0` published the wheel and
  `release-manifest.json`;
- the public `latest/download/release-manifest.json` endpoint resolved to
  `0.1.0`;
- the downloaded wheel SHA-256 independently matched
  `1e22d736a8701377f8ab7f15bf4ea5a34c80ae0ae944ce84973da6925ffbb18f`;
- `agentgov update --check .` used the public discovery path, reported
  installed and available version `0.1.0`, required no repository refresh,
  modified nothing, and exited `0`.

Latest local validation on 2026-07-24:

- Python 3.11.9: 212 tests passed; one Windows symbolic-link test skipped
  because the current user lacks link-creation privilege.
- User guides now preserve the Taxi-tested command order, use
  `python -m agentgov`, explain Windows nested-path failures and invalid
  `check` syntax, and provide accessible copy controls for command blocks.
- Repository self-check: 16 PASS, 2 WARN, 0 FAIL, 4 ADVISORY.
- Isolated wheel rehearsal: build, install, initialize, Capability
  Dependencies schema and declaration presence, dependency PASS, completeness
  ADVISORY, and repository check passed with zero deterministic failures.
- `git diff --check`: passed.

Integration closure on 2026-07-24:

- Capability Dependencies PR #8 merged to `main` as commit `9007fce`.
- All six pull-request CI jobs passed on Ubuntu and Windows for Python 3.11,
  3.12, and 3.13.
- The post-merge `main` CI run passed.
- Local `main` is synchronized with `origin/main`; no deterministic CI failure
  remains.

The authoritative local baseline is:

```powershell
$env:PYTHONPATH = "src"
python -m unittest discover -s tests -v
python -m agentgov check repository .
git diff --check
```

CI is the source of truth for the full supported operating-system and Python
version matrix.
