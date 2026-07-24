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
- implementation and local validation are complete; PR review, CI, and
  human-controlled integration remain.

## Remaining TODOs

- [ ] Review the Capability Dependencies PR and the full supported CI matrix.
- [ ] Resolve any deterministic CI failures without weakening tests or policy.
- [ ] Obtain explicit human approval before marking the PR ready or merging.
- [ ] After merge, synchronize local `main` and record the final merge and CI
  state here.
- [ ] Schedule Taxi or another cross-domain pilot separately; do not include it
  in this upgrade.

## Known gaps

- No completed cross-domain pilot.
- Dependency risk propagation and repository profiles are not implemented.
- Legacy removal release remains undecided.
- A successful check does not prove semantic governance sufficiency.

## Validation

Latest local validation on 2026-07-24:

- Python 3.11.9: 210 tests passed; one Windows symbolic-link test skipped
  because the current user lacks link-creation privilege.
- Repository self-check: 16 PASS, 2 WARN, 0 FAIL, 4 ADVISORY.
- Isolated wheel rehearsal: build, install, initialize, Capability
  Dependencies schema and declaration presence, dependency PASS, completeness
  ADVISORY, and repository check passed with zero deterministic failures.
- `git diff --check`: passed.

The authoritative local baseline is:

```powershell
$env:PYTHONPATH = "src"
python -m unittest discover -s tests -v
python -m agentgov check repository .
git diff --check
```

CI is the source of truth for the full supported operating-system and Python
version matrix.
