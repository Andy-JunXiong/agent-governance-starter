---
adr: "0002"
title: "Generalize AI capabilities and adopt the governance layout"
status: Accepted
created: "2026-07-23"
owners:
  - "Project owner"
related:
  - "docs/adr/0001-separate-evaluation-readiness-and-decision.md"
---

# ADR-0002: Generalize AI capabilities and adopt the governance layout

## Context

The original contract describes prompt-backed capabilities through
`capability_kind` and a required `model_route`. That is natural for LLM
features but cannot describe deterministic decision engines, traditional ML
inference, or hybrid systems without misleading placeholders. The
`prompt-governance/` name reinforces that limitation.

Existing v0.1 development users may already have valid legacy manifests, so an
immediate read-time removal would create migration risk without governance
benefit.

## Decision

The canonical capability contract uses four orthogonal fields:

- `capability_type`;
- `implementation_mode`;
- `decision_authority`;
- `autonomy_level`.

New scaffolds use `governance/` with `capabilities`, `contracts`, `evidence`,
and `artifacts` subdirectories. `model_route` is no longer a universal
requirement.

The validator and repository checker retain read-only support for the complete
legacy `capability_kind` plus `model_route` form. A manifest may use the legacy
or canonical field family, never both. A repository containing both
`governance/` and `prompt-governance/` fails deterministically because silently
merging two sources of truth would be unsafe.

Legacy support does not authorize automatic file moves or rewrites.

## Owns

- Capability identity fields and canonical repository layout.
- Compatibility behavior for legacy manifests and repository paths.

## Does not own

- Domain taxonomies, runtime enforcement, model routing, inventory, control
  mappings, automatic migration, or release approval.

## Consequences

### Benefits

- Rules, traditional models, prompts, and hybrid capabilities share one
  governance contract.
- New adopters receive domain-neutral paths and examples.
- Existing manifests remain inspectable during an explicit migration.

### Costs and risks

- The Python validator temporarily understands two complete field families.
- Documentation must distinguish compatibility from canonical guidance.

## Alternatives considered

### Expand `capability_kind`

This leaves implementation, authority, and autonomy coupled in one growing
enumeration and retains a universal model-route assumption.

### Only decouple evaluation

This provides a useful pilot surface but leaves cross-domain ownership, risk,
controls, and provenance without a general capability identity.

### Automatically migrate repositories

Automatic rewriting could overwrite human governance choices and violates the
starter's create-missing-only safety boundary.

## Validation

- Automated: `$env:PYTHONPATH = "src"; python -m unittest discover -s tests -v`
- Manual: inspect one canonical and one legacy manifest plus a dual-layout
  repository.
- Success signal: canonical scaffolds pass; legacy repositories remain
  readable with a migration warning; dual layouts fail.

## Open questions

- Removal version for legacy compatibility.
- Inventory and control-mapping contracts in the next vertical slice.
