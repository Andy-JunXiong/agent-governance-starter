# Capability dependencies

Capability dependency declarations make known capability-to-capability
relationships reviewable without inferring architecture from filenames, call
sites, or readiness labels.

## Canonical path

Create one direct JSON child per Inventory capability:

```text
governance/dependencies/<capability-name>.json
```

The filename and `capability_name` must agree. An empty `depends_on` array is a
valid, honest declaration that the owner has not declared an upstream
capability dependency.

```json
{
  "contract": "agentgov.capability-dependencies",
  "schema_version": "1.0",
  "capability_name": "serve-recommendation",
  "depends_on": [
    {
      "capability": "prepare-features",
      "minimum_readiness": "baseline_ready"
    }
  ]
}
```

`minimum_readiness` is optional. Omitting it declares an identity edge without
inventing a readiness threshold.

## Deterministic semantics

When Governance Inventory passes, both the owner capability and every
dependency endpoint must appear in `governance/inventory.json`. The Inventory
manifest closure also supplies each capability's canonical
`evaluation.readiness`.

The checker rejects:

- malformed or non-canonical declarations;
- duplicate endpoints within one declaration;
- self-dependencies;
- Inventory-orphaned owners or endpoints;
- dependency cycles;
- an explicitly declared minimum readiness that the upstream capability does
  not meet.

For explicit thresholds only, readiness is ordered:

```text
not_configured
  < schema_only
  < needs_seed_cases
  < baseline_ready
  < regression_ready
```

A readiness difference is not a failure when the dependency edge omits
`minimum_readiness`. Downstream readiness is never used to invent an upstream
floor.

## Finding semantics

| Condition | Finding |
|---|---|
| Valid declaration, including an empty declaration | `PASS` |
| Dependency directory is absent or empty | `WARN` |
| Inventory capability has no declaration | `WARN` |
| Invalid identity, endpoint, self-edge, cycle, or explicit readiness floor | `FAIL` |
| All configured declarations pass, but real-world completeness is unknowable | `ADVISORY` |

If Inventory is absent or invalid, dependency files still receive local
structural validation, but Inventory endpoint and readiness checks are skipped
to avoid cascading claims from an unavailable authority.

The completeness advisory is intentional. Static declarations cannot prove
that every runtime or organizational dependency was discovered, and the
project does not turn dependency counts into a governance percentage.

## Adoption

`agentgov init` creates an empty declaration for `example-capability`. Replace
that identity when replacing the example capability. Add an edge only when the
relationship is known, and add `minimum_readiness` only when the owning team
has deliberately set that floor.

Run the repository check after editing:

```powershell
$env:PYTHONPATH = "src"
python -m agentgov check repository .
```

Capability dependencies do not authorize automatic risk propagation, runtime
orchestration, merge, release, or deployment.
