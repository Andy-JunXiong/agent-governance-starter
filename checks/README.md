# Governance checks

Checks distinguish hard facts from advisory judgment and include fixture-based
tests.

## Repository check

```powershell
agentgov check repository path/to/repository
```

The v0.1 repository check covers only:

- required `AGENTS.md`, ADR template, and invariant register files;
- unresolved `{{PLACEHOLDER}}` values in those required files;
- JSON capability manifests under `prompt-governance/capabilities/`;
- a human-review advisory that static checks cannot resolve.

Status semantics:

- `PASS`: a deterministic requirement is satisfied;
- `WARN`: configuration is incomplete but non-blocking;
- `FAIL`: a deterministic required condition is violated;
- `ADVISORY`: human judgment is required.

WARN and ADVISORY findings return process exit code `0`. Any FAIL returns `1`.
Unreadable or invalid repository targets return `2`. The command does not
calculate a coverage percentage or judge architecture quality.

## Markdown report

```powershell
agentgov report repository path/to/repository
agentgov report repository path/to/repository --output governance-report.md
```

The report reuses the same repository findings and adds a Markdown summary,
finding table, known gaps, recommended actions, and scope limitations. It has
no timestamp or weighted score, so unchanged inputs produce stable output.

Standard output is the default. `--output` writes only to a new file whose
parent directory already exists; existing files and symbolic links are never
overwritten. A report is still generated when governance checks fail, and the
process returns `1` so automation can preserve both the artifact and failure
signal.
