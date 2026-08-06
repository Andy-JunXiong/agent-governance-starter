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
- `control-mapping.template.json`: one explicit human-procedural starter
  control linked to readable repository references without claiming
  effectiveness.
- `capability-dependencies.template.json`: an honest empty dependency
  declaration that does not invent upstream capabilities or readiness floors.
- `example-capability.*.schema.template.json`: minimal repository-local input
  and output contracts referenced by the example capability.
- `prompt-source.template.md`: explicit prompt-source placeholder referenced
  by the example capability.
- `evaluation-manifest.template.json`: honest `needs_seed_cases` starting point
  that does not invent evaluation evidence.
- `development-task.template.json`: strict low-risk `compact` starting point
  for a human-owned coding-agent task. It stays `draft`, requires exact scope,
  acceptance, validation command, owner, risk, and decision, and does not
  invent parent-objective, approval, or architecture declarations.
- `task-proposal.template.json`: strict non-authoritative input for a Coding
  Agent or host Adapter to describe one normalized low-risk task, assumptions,
  unknowns, privacy boundary, and denied authority before human admission.
- `admission-routing-policy.template.json`: human-owned standing policy that
  ships as a draft with fast-track disabled and zero-interruption budgets for
  no-write, active-task, and future fast-track routes.
- `work-request.template.json`: zero-authority no-write request example for
  host-side classification without raw prompt or transcript content.
- `codex-hooks.template.json`: exact optional project hook definition for the
  packaged Codex Adapter. Install it only through the create-missing-only
  `agentgov integrate codex-hooks` flow and review trust separately in Codex.
- `codex-mcp.template.toml`: exact optional project configuration for the
  foreground AgentGov MCP Adapter. Install it only through the
  create-missing-only `agentgov integrate codex-mcp` flow and preserve Codex
  trusted-project/config review.

## Placeholder contract

Markdown templates use `{{UPPER_SNAKE_CASE}}` placeholders. Replace every
placeholder deliberately before adopting a template. Do not mechanically fill
unknown values with invented policy.

The JSON templates are structurally valid as shipped. The capability template
passes the v0.1 capability contract, while the development-task template is an
honest draft that retains WARN and ADVISORY review needs. Replace neutral
values while preserving the relevant schema. Check the results with:

```powershell
agentgov check capability path/to/capability.json
agentgov check references path/to/capability.json --repository .
agentgov check task path/to/development-task.json --repository .
agentgov propose task path/to/task-proposal.json --repository . --dry-run
agentgov route request path/to/work-request.json `
  --policy governance/admission-policy.json --repository .
```

Packaging installs these same reviewed files under the distribution data
directory; there is no second generated template copy to keep in sync. The
existing repository scaffold files are used by `agentgov init`; the
development-task and task-proposal templates remain explicit opt-in fallback
interfaces rather than the intended ordinary-user workflow.

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
about repository paths. The generated evaluation manifest and any exported
review artifact declare that same capability through their own
`capability_name`; the repository check uses those contract claims, not
directory names, for Inventory evidence closure.

Initialization also creates
`governance/controls/example-capability.json`. Adapt its objective, mode,
references, owner, and exception authority to the real repository. A
structurally valid mapping still emits an effectiveness advisory because
static checks cannot establish control sufficiency.

Initialization also creates
`governance/dependencies/example-capability.json`. Its empty `depends_on` array
is valid. Add only known Inventory capability edges, and add
`minimum_readiness` only when the owning team has deliberately established a
floor. Static checks reject self-dependencies, cycles, orphan endpoints, and
unmet explicit floors while keeping completeness advisory.
