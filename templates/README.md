# Templates

Portable repository-governance templates live here. They use neutral
placeholders and do not include reference-project infrastructure or business
rules.

## Included templates

- `AGENTS.template.md`: repository constitution, safety boundaries, operating
  modes, approval gates, validation, and escalation.
- `ADR.template.md`: durable architecture-decision record with an admission
  gate, ownership boundary, consequences, and implementation follow-up.
- `INVARIANTS.template.md`: architecture-constraint register with explicit
  authority, enforcement-point, and verification metadata.
- `prompt-capability.template.json`: contract-valid starting manifest for a
  governed AI capability implemented by deterministic logic, a model, a
  prompt, or a hybrid.
- `governance-inventory.template.json`: honest repository declaration linking
  the example capability to its accountable owner without claiming automatic
  discovery.
- `example-capability.*.schema.template.json`: minimal repository-local input
  and output contracts referenced by the example capability.
- `prompt-source.template.md`: explicit prompt-source placeholder referenced
  by the example capability.
- `evaluation-manifest.template.json`: honest `needs_seed_cases` starting point
  that does not invent evaluation evidence.

## Placeholder contract

Markdown templates use `{{UPPER_SNAKE_CASE}}` placeholders. Replace every
placeholder deliberately before adopting a template. Do not mechanically fill
unknown values with invented policy.

The prompt-capability template is different: it is valid JSON and passes the
v0.1 capability contract as shipped. Replace its neutral example values while
preserving the schema. Check the result with:

```powershell
agentgov check capability path/to/capability.json
agentgov check references path/to/capability.json --repository .
```

These files are the single reviewed source used by `agentgov init`. Packaging
installs the same files under the distribution data directory; there is no
second generated template copy to keep in sync.

Initialize a new or empty directory with:

```powershell
agentgov init path/to/project --project-name "Example Project"
```

Use `--dry-run` to preview the exact output paths without writing. The command
replaces only `{{PROJECT_NAME}}`; every remaining governance placeholder is
reported and must be resolved by a human. v0.1 deliberately refuses non-empty
targets and provides no force or overwrite option.

Initialization also installs the evaluation schemas and readiness policy, then
creates `evaluation/example-capability/evaluation-manifest.json`. Its initial
readiness is `needs_seed_cases`, so repository checks report WARN until real
reviewed evidence is added. The example capability's required schema and source
references exist immediately; replace their placeholder content rather than
leaving broken paths.

Initialization also creates `governance/inventory.json`. Its example capability
is `provisional`, and its empty exclusions array makes no unsupported claim
about repository paths.
