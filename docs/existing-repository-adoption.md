# Existing repository adoption

This guide covers the complete read-only inspection and create-missing-only adoption workflow for an existing repository.

## Safety contract

`agentgov inspect` never creates or modifies repository files. `agentgov adopt` performs a complete conflict preflight, preserves existing regular files, and creates only missing scaffold files. Neither command reads or reconciles the contents of discovered vendor-specific instruction files, runs Git commands, or authorizes merge, publication, release, or deployment.

## Prerequisites

- Python 3.11 or newer;
- an existing local repository you are authorized to inspect and modify;
- a clean or reviewable working tree, so newly created files are easy to audit;
- a human-readable project name.

From the target repository root, activate its Python environment and install directly from GitHub. Do not clone the starter inside the target repository.

```powershell
python -m pip install "git+https://github.com/Andy-JunXiong/agent-governance-starter.git@main"
python -m agentgov --help
```

Bash:

```bash
python -m pip install "git+https://github.com/Andy-JunXiong/agent-governance-starter.git@main"
python -m agentgov --help
```

## Step 1: inspect without writing

```powershell
python -m agentgov inspect path/to/repository
```

For a machine-readable plan:

```powershell
python -m agentgov inspect path/to/repository --format json
```

The JSON format follows `schemas/adoption-report.schema.json` contract version `1.0`.

Interpret the states as follows:

| State | Meaning | Required response |
|---|---|---|
| `PRESENT` | A core governance path already exists. | Preserve and review it. |
| `MISSING` | A core path is not configured. | Decide whether to create it during adoption. |
| `DISCOVERED` | Another repository instruction path exists. | Review its authority and escalation relationship manually. |
| `CONFLICT` | A core path has the wrong type or is a symbolic link. | Resolve the deterministic conflict before adoption. |

Missing paths return exit code `0`. A deterministic conflict returns `1`; a missing repository or operational problem returns `2`.

## Step 2: preview adoption

Always review a dry run before writing:

```powershell
python -m agentgov adopt path/to/repository --project-name "Example Project" --dry-run
```

Bash:

```bash
python -m agentgov adopt path/to/repository --project-name "Example Project" --dry-run
```

`PLAN` identifies missing files that would be created. `PRESERVE` identifies existing files whose content will remain unchanged.

Stop if:

- the target repository is not the intended repository;
- an existing instruction file has an unclear authority relationship;
- any planned file should be owned by another team;
- a conflict requires moving, replacing, or deleting existing content;
- the proposed scope needs credentials, private prompt data, or production artifacts.

## Step 3: create missing files

After reviewing the plan:

```powershell
python -m agentgov adopt path/to/repository --project-name "Example Project"
```

The command uses exclusive file creation. If a destination appears after preflight, adoption stops instead of overwriting it. Existing files are not rewritten to match starter templates.

Review the resulting Git diff manually. The command does not stage or commit it.

## Step 4: adapt the scaffold

Use the [generated-files guide](generated-files-guide.md) to update the new files. At minimum:

1. replace or explicitly defer every `{{PLACEHOLDER}}`;
2. establish the authority relationship between AGENTS.md and discovered instructions;
3. replace the example capability with a real, bounded capability;
4. identify its owner and risk level;
5. configure honest evaluation readiness and evidence references;
6. preserve explicit human approval for high-risk transitions.

Do not remove warnings merely to obtain a green report.

## Step 5: validate

```powershell
agentgov check repository path/to/repository
agentgov report repository path/to/repository --output path/to/repository/governance-report.md
```

If another local tool needs the report:

```powershell
agentgov report repository path/to/repository --format json --output path/to/repository/governance-report.json
```

Review `Human decisions still required`, known gaps, recommended actions, and scope limitations before accepting the adoption change.

## Completion checklist

- [ ] Dry run was reviewed before writing.
- [ ] Existing files were preserved.
- [ ] Discovered instruction files were reviewed by a human.
- [ ] Placeholders were completed or explicitly deferred.
- [ ] Capability metadata reflects real repository behavior.
- [ ] Evaluation readiness does not overstate evidence.
- [ ] Repository check contains no unexplained deterministic failures.
- [ ] WARN and ADVISORY findings have owners or recorded decisions.
- [ ] Merge, publish, release, and deploy remain separately authorized.
