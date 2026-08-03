---
layout: reference
title: Development task contract
source_path: docs/development-task-contract.md
---

# Development task contract

## Status

The development task contract is implemented in the current development
source as an experimental P0 interface. It is not part of published stable
AgentGov 0.2.1, is not yet created by `agentgov init`, and is not automatically
included in the repository-wide check.

Its purpose is to make the human-owned requirement, architecture boundary, and
coding-agent implementation scope explicit before code is written. It does not
infer whether the requirement is correct or whether the selected architecture
is sufficient.

## Contract

The strict JSON Schema is
[`schemas/development-task.schema.json`](../schemas/development-task.schema.json).
Start from
[`templates/development-task.template.json`](../templates/development-task.template.json)
and store an adopted contract in a repository-owned location such as
`governance/tasks/<task-id>.json`.

Contract version `1.1` supports `compact` and `standard` profiles in the same
Schema. Compact is limited to explicitly admitted low-risk work and provides a
ten-minute path without inventing architecture or approval facts. Standard
preserves the full task boundary.

This remains an unpublished development-preview contract. Repository fixtures
were migrated together from 1.0 to 1.1; the checker intentionally rejects the
old preview shape instead of silently guessing a profile or validation command.

The fields preserve:

| Field | Responsibility |
|---|---|
| `requirement` | Human-owned summary plus optional repository-local provenance. Missing provenance is a deterministic `WARN`, not invented evidence. |
| `objective` | Human-declared `core`, `supporting`, or `maintenance` relationship, parent-objective references, and rationale. Alignment remains `ADVISORY`. |
| `goal` and `non_goals` | The smallest intended outcome and explicit boundaries. |
| `scope` | Exact repository-relative path prefixes that are included or excluded. Globs, absolute paths, backslashes, and parent traversal are rejected. |
| `architecture_refs` | Repository-local architecture or invariant context. An empty list requires advisory human confirmation rather than automatic failure. |
| `acceptance_signals` | Observable conditions agreed before implementation. |
| `validation_commands` | At least one repository command agreed before implementation. Recording it does not yet make its result fresh evidence. |
| `profile` and `owner` | `compact` or `standard`, plus the accountable human role. Compact tasks must remain low risk. |
| `risk` and `approval` | Declared risk, approval requirement, status, owner, and evidence. High or critical risk requires approval. |
| `stop_conditions` | Conditions that return control to the accountable human. |
| `decision` | Human-owned `draft`, `admitted`, or `paused` state. The checker does not admit work itself. |

`completed` is deliberately not a supported decision state yet. Completion
requires the later fresh-evidence and reconciliation contract rather than a
claim embedded in the initial task declaration.

## Read-only check

From a source checkout:

```powershell
$env:PYTHONPATH = "src"
python -m agentgov check task governance/tasks/p0-minimal-task-contract.json `
  --repository .
```

The installed-command form for a future release is:

```powershell
agentgov check task governance/tasks/my-task.json --repository .
```

Exit codes follow the existing CLI boundary:

- `0`: no deterministic task failure was found; WARN and ADVISORY may remain;
- `1`: the readable task violates the structural contract or a declared
  repository reference is unsafe, missing, non-file, symbolic, or unreadable;
- `2`: usage, repository access, encoding, or JSON parsing prevented the
  check.

The command never creates or edits a task, changes the working tree or index,
runs Git, or authorizes implementation. An admitted state is accepted only as
a human declaration recorded in the contract.

## Finding boundary

Deterministic findings cover:

- contract identity, version, required and unknown fields, enums, and
  cross-field consistency;
- task IDs, exact scope-path syntax, unique entries, and include/exclude
  conflicts;
- readable repository-local requirement, parent-objective, architecture, and
  approval-evidence references;
- the rule that approval-required work cannot be admitted while approval is
  pending or rejected.

Advisory findings cover whether the declared objective role and rationale
actually advance the parent requirement, and whether omitted architecture
context is appropriate. AgentGov preserves those questions for an accountable
human.

## Self-governance scenario

The first completed contract slice is
[`governance/tasks/p0-minimal-task-contract.json`](../governance/tasks/p0-minimal-task-contract.json).
It links the corrected P0 plan, ADR-0009, and
[`AG-DRIFT-001`](case-studies/0001-pr-center-architecture-drift.md).

That case establishes an important contract requirement: a structurally valid
supporting task may still contribute to architecture drift. AgentGov may show
the declared role, parent references, changed surfaces, and repeated delivery
facts deterministically, but the conclusion that support work displaced the
product core remains advisory.

The current Phase 1 task is
[`governance/tasks/p0-context-selection.json`](../governance/tasks/p0-context-selection.json).
It exercises the same standard profile while the default template now uses the
low-risk compact profile.

## Follow-up work

This slice does not yet:

- create or edit task contracts interactively;
- compare staged, unstaged, untracked, or renamed files with `scope`;
- capture fresh validation evidence or reconcile completion;
- integrate the implemented context output into the higher-level
  `govern start` session workflow;
- replay task facts in CI;
- install a hook, daemon, IDE integration, or mechanical agent gate.

Those capabilities remain ordered P0 follow-up work. The contract will be
validated through real use before it is added to initialization or stable
repository-wide checks.
