# ADR-0003: Identify capability contracts and bound legacy support

Status: Accepted

Date: 2026-07-24

## Decision gate

Adopt an explicit contract identity before adding repository inventory,
control mapping, capability dependencies, or cross-domain pilot contracts.

## Context

The canonical AI Capability schema and the legacy Prompt Capability schema
both used `schema_version: "1.0"` while requiring incompatible field families.
The validator therefore inferred the contract family from field names. A
version identifies a revision within a contract family; it does not identify
the family itself.

The legacy layout remains a read-only compatibility surface. Existing
repositories must not fail solely because they predate explicit contract
identity, and the tool must not silently rewrite human-owned governance data.

## Decision

Canonical manifests must declare:

```json
{
  "contract": "agentgov.ai-capability",
  "schema_version": "1.0"
}
```

Legacy manifests may declare:

```json
{
  "contract": "agentgov.prompt-capability",
  "schema_version": "1.0"
}
```

Legacy manifests without `contract` remain readable during the compatibility
window. The legacy directory continues to produce a migration `WARN`.
An explicit contract identity that conflicts with the manifest field family
is a deterministic `FAIL`.

New scaffolds emit only the canonical identity and canonical `governance/`
layout. Automatic migration is not provided.

## Owns

- Capability contract-family identity.
- Compatibility behavior for legacy manifests without identity.
- Deterministic rejection of identity and field-family conflicts.
- The boundary against silent migration.

## Does not own

- Inventory, control mapping, dependencies, or domain profiles.
- Automatic discovery of AI capabilities.
- A removal release for legacy support.
- Cross-domain pilot design.

## Consequences

- A manifest can identify its governing contract without field-shape inference.
- `schema_version` retains one meaning: version within the named contract.
- Old repositories remain readable and receive an explicit migration warning.
- Removing legacy compatibility requires a later ADR, migration guidance, and
  a documented release boundary.

## Alternatives considered

### Rename the canonical version to `2.0`

Rejected because a version number still does not explicitly identify the
contract family.

### Continue field-shape inference indefinitely

Rejected because manifest identity would remain implicit and schema lifecycle
would be difficult to govern.

### Automatically rewrite legacy manifests

Rejected because rewriting can overwrite accountable human governance choices.

## Implementation plan

1. Require the canonical contract identity in the schema and validator.
2. Emit it from the initializer template.
3. Accept legacy manifests without identity during the compatibility window.
4. Reject explicit identity and field-family conflicts.
5. Preserve the legacy-layout migration warning.

## Validation

- Canonical manifest with canonical identity passes.
- Canonical manifest without identity fails.
- Legacy manifest without identity remains readable.
- Explicit identity and field-family conflicts fail.
- Mixed legacy and canonical fields fail.
- Dual canonical and legacy layouts fail.

## Rollback or replacement

A later ADR may remove legacy compatibility only after migration documentation,
fixtures, and release notes identify the breaking boundary. It must not make
silent rewriting the default.
