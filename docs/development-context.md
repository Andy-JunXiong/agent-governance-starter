# Development governance context

## Status

Task-specific governance context selection is implemented in development
source for the future 0.3 line. It is not part of published stable 0.2.1 and
remains the read-only Router beneath the guided session workflow.

The command is deliberately retained as a low-level composition surface:

```powershell
$env:PYTHONPATH = "src"
python -m agentgov context task governance/tasks/p0-context-selection.json `
  --repository . --format terminal
```

`--format json` emits the strict
[`agentgov.development-context`](../schemas/development-context.schema.json)
contract. JSON and Markdown default to a lightweight `references` mode: paths,
roles, reasons, hashes, and limits are present, but source content is not
duplicated. Use `--include-content` only when a consumer cannot read the
selected repository paths directly.

`agentgov govern start` now calls this Router after exact human confirmation,
shows the selected paths, and records those references in `task.started`. That
event proves selection only; actual coding-agent consumption remains unknown.

## What is selected

The in-memory Registry discovers repository-owned artifacts; it is never
written as `registry.json`. The Router then selects:

1. root `AGENTS.md` and the current admitted task as required context;
2. requirement, parent-objective, architecture, invariant, and approval
   references explicitly declared by the task;
3. conventional `AI_CONTEXT.md` when an architecture-aware task declares
   architecture references and that file exists;
4. Skills whose artifact-owned `triggers`, `non_triggers`, and `applies_to`
   metadata match the task;
5. capabilities whose declared caller, source, contract, or evidence paths
   overlap the admitted task scope by path segment;
6. controls, dependencies, and configured evaluation manifests linked to a
   selected capability.

Every selected item includes its repository-relative path, artifact type,
role, selection mode, deterministic/advisory classification, human-readable
reason, and SHA-256 source hash. Full local content is optional. Duplicate
references collapse to one item while preserving all roles and reasons.

`context-first-review` remains an `advisory_candidate` when the task explicitly
names architecture context. Its selection is deterministic; whether the
architecture is sufficient is not.

## Compact and standard tasks

Task contract 1.1 provides two profiles in the same Schema:

- `compact` is limited to low-risk work and requires requirement summary,
  exact path scope, acceptance signals, at least one validation command,
  accountable owner, risk, and human decision;
- `standard` additionally requires parent objective, goal/non-goals,
  architecture references, approval contract, and stop conditions.

Compact omission of parent-objective or architecture detail stays visible as
`ADVISORY`; it is not silently treated as proof that those concerns do not
apply.

## Selection modes

| Mode | Meaning |
|---|---|
| `required` | Repository authority, current task, or a directly matched required protocol. |
| `declared` | The task explicitly names the artifact. |
| `path_match` | Task scope overlaps paths declared by the artifact itself. |
| `capability_link` | A selected capability declares this related governance surface. |
| `advisory_candidate` | A deterministic trigger found context that still needs semantic human judgment. |

Path comparison uses repository-relative POSIX segments. It does not use raw
string-prefix matching and does not infer relationships from full-text prose.

## Authority and limits

Context selection reads files only. It does not edit the task, create
`.agentgov/`, modify Git state, authorize implementation, or grant commit,
merge, release, or deployment authority.

The first Phase 1 consumption check found that unconditional embedding reached
85,660 characters for 13 selected artifacts, led by the full product and
development plans. That observed noise caused reference mode to become the default;
explicit embedding remains available. Future content budgeting or summaries
must preserve provenance and require a later measured design decision.

## Phase 1 consumption pilot

Codex consumed the generated context for admitted task
`p0-context-selection` while implementing this slice. After reference mode was
introduced, the same 13 selected artifacts produced 7,552 characters instead
of 85,660 embedded characters. The coding-agent run followed these selected
constraints:

- root `AGENTS.md` authority and the admitted task remained required;
- `development-slice` governed the bounded implementation;
- `context-first-review` remained an advisory architecture candidate;
- Skill routing declarations stayed in `SKILL.md`;
- Registry remained derived in memory, and context selection performed no Git
  or repository write;
- changed-file enforcement, events, fresh evidence, Dashboard, commit, and
  release stayed outside the slice.

Observed effect: the consumption check exposed an attention-cost defect before
handoff and caused the default serialization to change from embedded content
to references with explicit provenance. No constraint was knowingly ignored.
This was a same-agent, single-repository run, so it does not establish general
adherence, usability, or product benefit; an independent-repository pilot is
still required before release.
