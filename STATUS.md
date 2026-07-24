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

Repository Inventory, evidence closure, and control mapping:

- Governance Inventory contract and zero-dependency validator implemented;
- canonical manifest, owner, identity, exclusion, and safe-path closure;
- evaluation and artifact contract claims close to Inventory declarations
  without filename inference;
- deterministic orphan failures with legacy-compatible non-cascading behavior;
- strict capability control mappings with explicit applicability, enforcement
  mode, ownership, exception authority, and safe evidence references;
- deterministic control identity and reference checks paired with an explicit
  effectiveness advisory;
- explicit completeness advisory without automatic discovery claims;
- next slice: capability dependencies.

## Known gaps

- No completed cross-domain pilot.
- Capability dependency contracts remain planned rather than implemented.
- Legacy removal release remains undecided.
- A successful check does not prove semantic governance sufficiency.

## Validation

Latest local validation on 2026-07-24:

- Python 3.11.9: 194 tests passed; one Windows symbolic-link test skipped
  because the current user lacks link-creation privilege.
- Repository self-check: 15 PASS, 2 WARN, 0 FAIL, 3 ADVISORY.
- Isolated wheel rehearsal: build, install, initialize, Control Mapping asset
  presence, control PASS, effectiveness ADVISORY, and repository check passed
  with zero deterministic failures.
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
