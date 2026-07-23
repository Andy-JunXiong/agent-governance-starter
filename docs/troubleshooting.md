# Troubleshooting

## `agentgov` is not recognized

Confirm that the intended Python environment is activated and reinstall the local package:

```powershell
python -m pip install --no-deps .
agentgov --help
```

From a source checkout, use:

```powershell
$env:PYTHONPATH = "src"
python -m agentgov --help
```

Bash equivalent:

```bash
PYTHONPATH=src python -m agentgov --help
```

## `init` says the target is not empty

This is intentional. `init` only supports a new or empty target. For an existing repository, use:

```powershell
agentgov inspect path/to/repository
agentgov adopt path/to/repository --project-name "Example Project" --dry-run
```

## `inspect` reports `MISSING`

`MISSING` is non-blocking adoption information. Review an `adopt --dry-run` plan before deciding to create the missing files.

## `inspect` or `adopt` reports `CONFLICT`

A core governance path is a symbolic link or has the wrong filesystem type. The tool does not move, delete, or replace it. Inspect the exact path, determine who owns it, and resolve it manually before rerunning the command.

## Existing CLAUDE.md or Copilot instructions were discovered

Discovery does not mean the files are invalid. Review their authority, approval, validation, and escalation rules. Decide explicitly how they relate to AGENTS.md. The CLI will not read or merge their contents.

## Repository check returns WARN

WARN represents incomplete but non-blocking configuration or evidence. Complete it or record an explicit deferral with an owner. Do not delete evidence requirements merely to suppress the warning.

## Repository check returns ADVISORY

Static analysis cannot resolve the finding. Record an accountable human judgment, rationale, and follow-up where appropriate.

## Repository check returns FAIL

FAIL is a deterministic contract violation. Read the check identifier and message, correct the referenced path or contract, and rerun the same command. Report generation can still preserve the failing findings for review.

## A report output file already exists

Report output refuses to overwrite existing files. Choose a new path or move the previous report through a separate human-controlled action.

## Artifact export refuses to replace output

Export is intentionally non-overwriting. Review the existing artifact and use the explicit `--replace` option only when regeneration is intended. Manual files outside the generated artifact contract remain out of scope.

## Windows symbolic-link test is skipped

Creating symbolic links may require Developer Mode or elevated rights on Windows. The skip does not weaken production path checks; run the suite in an environment with symbolic-link support for full cross-platform evidence.

## Exit codes

- `0`: the command completed without a blocking deterministic finding;
- `1`: a deterministic policy failure or adoption conflict exists;
- `2`: usage, path, encoding, permission, or other operational failure prevented the command.

WARN and ADVISORY remain visible but are non-blocking. No exit code grants approval to merge, publish, release, or deploy.
