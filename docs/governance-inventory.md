# Governance Inventory

`governance/inventory.json` is the repository owner's explicit declaration of
which canonical AI Capability manifests are governed and which repository
paths are deliberately excluded.

It provides declaration closure. It does not discover capabilities
automatically and cannot prove that every real AI capability was declared.

## Minimal contract

```json
{
  "contract": "agentgov.governance-inventory",
  "schema_version": "1.0",
  "capabilities": [
    {
      "name": "example-capability",
      "manifest": "governance/capabilities/example-capability.json",
      "owner": "Owning team or maintainer",
      "governance_status": "provisional"
    }
  ],
  "exclusions": []
}
```

Supported governance statuses are:

- `provisional`: declared but still being adapted or evidenced;
- `active`: currently governed under the declared repository contract;
- `retired`: retained for an explicit historical or migration reason.

The status does not authorize runtime execution, release, or deployment.

## Deterministic checks

The repository check verifies that:

- the inventory is strict, readable JSON with the supported contract identity;
- capability names and manifest references are unique;
- every inventory item references a valid canonical manifest under
  `governance/capabilities/`;
- inventory name and owner match the referenced manifest;
- every canonical manifest is listed;
- exclusion paths and manifest references remain inside the repository and do
  not traverse symbolic links;
- every exclusion has a non-empty path and a meaningful reason;
- every excluded path currently exists.

Missing `governance/inventory.json` is a non-blocking `WARN` so repositories
created before this contract remain readable. A configured but inconsistent
inventory is a deterministic `FAIL`.

## Advisory boundary

A passing inventory establishes consistency only for owner declarations. It
does not establish:

- that all real AI capabilities were found;
- that exclusions are semantically justified;
- that governance controls are effective;
- that a capability is safe, correct, or approved;
- a governance coverage percentage.

For this reason, a valid inventory also emits
`ADVISORY inventory:completeness`.

## Explicit exclusions

Use exclusions only for real repository paths whose omission is intentional:

```json
{
  "path": "docs/examples",
  "reason": "Documentation examples do not execute as repository capabilities."
}
```

Do not use exclusions to suppress unknown findings or to imply that unlisted
paths were automatically inspected.

## Validation

Run the repository check:

```powershell
agentgov check repository .
```

Review both:

- `inventory:governance/inventory.json`, which reports deterministic closure;
- `inventory:completeness`, which preserves the human judgment boundary.
