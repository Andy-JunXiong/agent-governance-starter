# Agent Governance Starter Kit Status

Last verified: 2026-07-24

## Current state

- Version: `0.1.0.dev0`.
- Maturity: experimental and suitable for repository-level evaluation.
- Canonical capability layout: `governance/`.
- Legacy `prompt-governance/` input remains a bounded, read-only compatibility
  surface.
- Merge, publish, release, and deployment remain separate human-authorized
  actions.

## Stable foundations

- Installable, zero-runtime-dependency Python CLI.
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

## Remaining TODOs

- [ ] Tomorrow: design and test a low-friction installation path that keeps
  AgentGov independent from the adopting repository's Python environment.
  The happy path should not require cloning the starter into the target,
  repairing the target's `.venv`, or installing the target's development
  dependencies.
- [ ] Convert the Taxi adoption notes into a completed cross-domain pilot
  record, including timing, assistance required, unresolved release-gate
  findings, and final maintainer decisions.
- [ ] Decide whether the supported one-command experience should use an
  isolated tool installer, an ephemeral runner, or a small bootstrap command;
  verify it on Windows and document uninstall/update behavior before making it
  the primary Quickstart.

## Known gaps

- Taxi supplied initial cross-domain adoption evidence, but the pilot record
  and maintainer decisions are not complete.
- Installation still depends on a usable Python interpreter. The current
  GitHub-install workaround avoids a nested clone and Windows build-path
  failure, but it is not yet the intended final onboarding experience.
- Dependency risk propagation and repository profiles are not implemented.
- Legacy removal release remains undecided.
- A successful check does not prove semantic governance sufficiency.

## Validation

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
