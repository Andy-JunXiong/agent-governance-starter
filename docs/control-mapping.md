# Capability Control Mapping

`governance/controls/<capability-name>.json` declares repository-native
controls for one capability already listed in `governance/inventory.json`.

The contract records inspectable claims. It does not certify that a control is
effective, sufficient, or correctly exempted.

## Minimal applicable control

```json
{
  "contract": "agentgov.control-mapping",
  "schema_version": "1.0",
  "capability_name": "example-capability",
  "controls": [
    {
      "control_id": "human-review-boundary",
      "objective": "Preserve explicit human authority for governed repository transitions.",
      "applicability": "applicable",
      "enforcement_mode": "human_procedural",
      "implementation_refs": ["AGENTS.md"],
      "verification_refs": ["docs/adr/INVARIANTS.md"],
      "owner": "Owning team or maintainer",
      "exception_authority": "Named repository maintainer"
    }
  ]
}
```

Supported enforcement modes are:

- `deterministic`: repository logic evaluates a repeatable condition;
- `platform_enforced`: a declared external platform enforces the boundary;
- `human_procedural`: an accountable human follows a documented procedure;
- `advisory_only`: the declaration guides review without claiming enforcement.

The mode is a declared classification, not proof that implementation matches
the classification.

## Not applicable

Not-applicable controls omit enforcement and evidence fields and require a
reviewable rationale:

```json
{
  "control_id": "runtime-model-routing",
  "objective": "Govern runtime selection between multiple hosted model providers.",
  "applicability": "not_applicable",
  "owner": "Owning team or maintainer",
  "exception_authority": "Named repository maintainer",
  "rationale": "This capability has no runtime model route or hosted provider."
}
```

This is a contract value, not an additional repository finding status. A valid
not-applicable declaration contributes to a mapping `PASS`, while its semantic
justification remains part of the effectiveness advisory.

## Deterministic checks

The repository check verifies that:

- the mapping uses the supported strict contract and schema version;
- the filename and declared capability name agree;
- when the Governance Inventory is valid, the capability is listed in it;
- control IDs are unique within a mapping and across the repository;
- applicable controls use a supported enforcement mode;
- implementation and verification references are unique, safe,
  repository-relative, readable UTF-8 files;
- applicable controls have both implementation and verification references;
- not-applicable controls omit enforcement and evidence fields and provide a
  meaningful rationale;
- owners and exception authorities are present.

Missing `governance/controls/` is a non-blocking `WARN` for compatibility with
repositories created before this contract. When some mappings are configured,
an Inventory capability without a mapping is also a `WARN`. A malformed,
unsafe, duplicate, or orphan configured mapping is a deterministic `FAIL`.
When the Inventory is missing or invalid, capability closure is not enforced;
the Inventory finding reports that condition without cascading orphan claims
from an unreliable declaration set.

## Advisory boundary

A deterministically valid control mapping also emits
`ADVISORY controls:effectiveness`. Static validation cannot decide:

- whether the control objective is sufficient for the real risk;
- whether the declared mode matches runtime enforcement;
- whether referenced verification genuinely tests the control;
- whether a not-applicable rationale or exception authority is appropriate;
- whether all necessary controls were declared.

No control coverage percentage or weighted score is calculated.

## Validation

Run:

```powershell
agentgov check repository .
```

Review the `control:governance/controls/...` findings together with
`controls:effectiveness`.
