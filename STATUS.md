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

Pre-pilot credibility hardening:

- explicit capability contract identity;
- bounded legacy lifecycle and migration semantics;
- truthful repository status;
- consistent AI Capability terminology;
- report producer metadata;
- repository self-governance in CI.

## Known gaps

- No completed cross-domain pilot.
- Governance Inventory, control mapping, and capability dependency contracts
  remain planned rather than implemented.
- Legacy removal release remains undecided.
- A successful check does not prove semantic governance sufficiency.

## Validation

Latest local validation on 2026-07-24:

- Python 3.11.9: 165 tests passed; one Windows symbolic-link test skipped
  because the current user lacks link-creation privilege.
- Repository self-check: 13 PASS, 2 WARN, 0 FAIL, 1 ADVISORY.
- Isolated wheel rehearsal: build, install, initialize, check, and JSON report
  generation passed with zero deterministic failures.
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
