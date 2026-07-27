# Agent Governance Starter Kit Status

Last verified: 2026-07-27

## Current state

- Version: `0.1.0`; stable GitHub Release published.
- Maturity: experimental and suitable for repository-level evaluation.
- Canonical capability layout: `governance/`.
- Legacy `prompt-governance/` input remains a bounded, read-only compatibility
  surface.
- Merge, publish, release, and deployment remain separate human-authorized
  actions.

## Stable foundations

- Installable, zero-runtime-dependency Python CLI.
- Package metadata and `agentgov --version` derive from the single runtime
  version declared by `agentgov.__version__`.
- Strict release-manifest schema, fixtures, and
  `agentgov check release-manifest` validation.
- Verified one-command update flow: stable-release discovery, bounded temporary
  download, SHA-256 verification, pipx upgrade, new-process relaunch,
  repository refresh, explicit terminal states, and recovery guidance.
- Tag-triggered GitHub Release workflow publishes the universal wheel and its
  immutable machine-readable manifest.
- Deterministic repository, capability, reference, evaluation, agent-skill,
  and artifact-drift checks.
- Explicit `PASS`, `WARN`, `FAIL`, and `ADVISORY` semantics.
- Markdown, JSON, and HTML report surfaces.
- Windows and Ubuntu CI definitions for Python 3.11, 3.12, and 3.13.

## Current milestone

Pre-pilot repository governance foundation:

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
