# Agent Governance Starter Kit

A lightweight, repo-native governance framework for AI-assisted software
development.

The project defines how coding agents operate inside a repository, how prompt
capabilities are described and reviewed, and how AI-assisted changes move
through verification and human approval before release.

## Project status

**Status: Experimental (`0.1.0.dev0`).** The project is ready for evaluation
and repository-level pilots. It is not a compliance certification, a security
boundary, or authorization for autonomous merge, publication, or deployment.

The v0.1 foundation and clean-repository adoption path are implemented. The CLI
initializes a portable governance scaffold, validates prompt capabilities and
their repository references, reports evaluation readiness, checks reusable
agent operating protocols, exports reviewable capability artifacts, and renders
a deterministic repository report. AI Radar remains a reference case rather
than a dependency.

## Design principles

- **Repo-native:** policy and evidence live beside the code they govern.
- **Human-controlled:** agents may prepare and verify changes, while people
  retain approval over high-risk transitions.
- **Explicit readiness:** incomplete evaluation is reported as incomplete, not
  presented as a passing benchmark.
- **Portable:** templates describe reusable contracts rather than one
  project's infrastructure or business rules.
- **Reviewable:** governance decisions, prompt metadata, checks, and reports
  are inspectable artifacts.

## v0.1 scope

The first usable release contains:

1. project constitution, ADR, invariant, and agent-protocol templates;
2. a prompt-capability metadata schema;
3. evaluation-readiness guidance;
4. a small set of deterministic repository checks;
5. a Markdown governance report;
6. AI Radar as a documented reference case, not a runtime dependency.

## Non-goals

v0.1 is not a SaaS control plane, policy engine, generic LLM evaluation
platform, real-time agent monitor, deployment system, or vendor-specific agent
runtime.

## Repository layout

```text
agent-governance-starter/
|-- agent-skills/       # Reusable coding-agent operating protocols
|-- checks/             # Deterministic governance checks
|-- docs/               # Methodology and reference material
|-- evaluation/         # Evaluation-readiness contracts
|-- prompt-governance/  # Prompt-capability schemas and examples
|-- src/agentgov/       # Python CLI and governance checks
|-- templates/          # Repository governance templates
`-- tests/              # Automated validation
```

## Development setup

Python 3.11 or newer is recommended.

```powershell
$env:PYTHONPATH = "src"
python -m unittest discover -s tests -v
```

## Clean-repository adoption path

After installing the package, initialize a new or empty project directory and
run the complete starter workflow:

```powershell
agentgov init path/to/new-project --project-name "Example Project"
agentgov check capability path/to/new-project/prompt-governance/capabilities/example-capability.json
agentgov check references path/to/new-project/prompt-governance/capabilities/example-capability.json --repository path/to/new-project
agentgov check evaluation path/to/new-project/evaluation/example-capability
agentgov check agent-skills path/to/new-project/agent-skills
agentgov export capability path/to/new-project/prompt-governance/capabilities/example-capability.json --repository path/to/new-project
agentgov check artifact path/to/new-project/prompt-governance/artifacts/example-capability --repository path/to/new-project
agentgov check repository path/to/new-project
agentgov report repository path/to/new-project --output path/to/new-project/governance-report.md
```

The initialized example intentionally remains at `needs_seed_cases`. Unresolved
governance placeholders and missing evaluation evidence are reported as
non-blocking warnings until a human adapts the scaffold. The workflow proves
that the package and contracts connect correctly; it does not claim that a
project's governance or model behavior is complete. The recorded installed
package rehearsal is documented in
[the v0.1 adoption rehearsal](docs/v0.1-adoption-rehearsal.md).

## Capability check

From a source checkout:

```powershell
$env:PYTHONPATH = "src"
python -m agentgov check capability prompt-governance/fixtures/valid/runtime-low-risk.json
```

After installing the package, the equivalent command is:

```powershell
agentgov check capability path/to/capability.json
```

Exit codes are stable for automation:

- `0`: the manifest passes the capability contract;
- `1`: the manifest is readable JSON but violates the contract;
- `2`: usage, file access, encoding, or JSON structure prevents the check.

Contract failures are printed to standard output as check findings. Operational
errors are printed to standard error. This slice validates manifest content;
repository-local reference integrity is checked separately.

Check contract schemas, declared callers, provenance sources, and evaluation
evidence with:

```powershell
$env:PYTHONPATH = "src"
python -m agentgov check references path/to/capability.json --repository .
```

Required or explicitly declared paths that are missing, unsafe, symbolic, or
malformed fail deterministically. Missing evaluation evidence for an honest
early readiness state is a non-blocking warning. Logical model-route names are
not treated as filesystem paths.

## Templates

The [template set](templates/README.md) includes a repository constitution, ADR
record, invariant register, and contract-valid prompt-capability starting
manifest. Markdown placeholders are explicit and must be reviewed before use.

Preview initialization without writing:

```powershell
$env:PYTHONPATH = "src"
python -m agentgov init path/to/new-project --project-name "Example Project" --dry-run
```

Remove `--dry-run` to generate the scaffold. v0.1 accepts only a new or empty
target directory, never overwrites existing files, and reports all unresolved
governance placeholders for human review. It also installs evaluation schemas,
the readiness policy, an honest `needs_seed_cases` starter bundle, and the
generic agent operating protocols.

## Agent operating protocols

Validate all direct child protocols under an `agent-skills` directory:

```powershell
$env:PYTHONPATH = "src"
python -m agentgov check agent-skills agent-skills
```

The check enforces portable frontmatter, explicit use and non-use conditions,
and a common workflow, safety, escalation, and handoff structure. The starter
protocols cover context-first proposal review, bounded development slices,
collaboration-failure attribution, and evidence-first operational incident
response; they contain no project-specific runtime or cloud dependency.

## Repository check

Check an initialized repository with:

```powershell
$env:PYTHONPATH = "src"
python -m agentgov check repository path/to/project
```

The command checks required governance files, unresolved placeholders, prompt
capability manifests, their repository-local references, discovered evaluation
bundles, agent protocols, and configured capability artifacts. Missing artifacts remain a non-blocking
`WARN`; malformed or stale configured artifacts are `FAIL`. It emits `PASS`,
`WARN`, `FAIL`, and `ADVISORY`
findings plus a deterministic summary. WARN and ADVISORY findings are
non-blocking; any FAIL returns exit code `1`. It does not calculate a governance
coverage percentage or infer architecture quality from matching text.

## Capability artifacts and source drift

Export a validated capability manifest as deterministic, repository-local
review artifacts:

```powershell
$env:PYTHONPATH = "src"
python -m agentgov export capability prompt-governance/capabilities/example.json `
  --repository .
```

The default output is
`prompt-governance/artifacts/<capability-name>/CAPABILITY.md` plus
`artifact.json`. Export hashes canonical manifest content and the declared
repository-relative source files. It never copies source content and refuses
to overwrite generated files unless `--replace` is explicit.

Check for manifest, source, or generated-file drift with:

```powershell
python -m agentgov check artifact `
  prompt-governance/artifacts/<capability-name> --repository .
```

Both manifest, sources, and output must stay inside the declared repository
root. A matching hash detects change, not capability quality or correctness.

## Markdown report

Render the same findings as deterministic Markdown:

```powershell
$env:PYTHONPATH = "src"
python -m agentgov report repository path/to/project
python -m agentgov report repository path/to/project --output governance-report.md
```

Reports contain summary counts, findings, known gaps, recommended actions, and
scope limitations. They contain no coverage percentage or timestamp. File
output refuses to overwrite an existing path; repositories with FAIL findings
still produce a report and return exit code `1`.

## Evaluation readiness

Validate an evaluation bundle and its declared readiness with:

```powershell
$env:PYTHONPATH = "src"
python -m agentgov check evaluation evaluation/fixtures/baseline-ready
```

The check distinguishes honest early-stage readiness (`WARN`) from supported
baseline/regression readiness (`PASS`) and unsupported maturity claims
(`FAIL`). It validates evidence structure and review metadata, not model quality
or benchmark performance.

## Reference implementation

The initial patterns were extracted from lessons learned while building AI
Radar. AI Radar remains a separate product and repository. This project does
not import AI Radar packages or reproduce its product-specific evidence and
workflow logic. See [the extraction map](docs/ai-radar-extraction-map.md).

## License

Released under the [MIT License](LICENSE).
