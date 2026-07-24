# Legacy Prompt Capability compatibility

This directory documents the bounded, read-only compatibility surface for
repositories created before the canonical `governance/` layout. New
repositories and new manifests must use `governance/` and the
`agentgov.ai-capability` contract identity.

Legacy support does not authorize automatic migration. See
[`docs/adr/0003-identify-capability-contracts-and-bound-legacy-support.md`](../docs/adr/0003-identify-capability-contracts-and-bound-legacy-support.md).

`capability.schema.json` defines the v0.1 manifest for governed prompt-backed
capabilities.

The schema covers exactly three capability kinds:

- `product_runtime`
- `operator_guidance`
- `evaluation_judge`

Coding-agent operating protocols are deliberately excluded. They belong under
`agent-skills/<name>/SKILL.md` so development-time instructions cannot be
silently treated as product runtime prompts.

## Required governance fields

Every manifest declares identity and purpose, positive and negative triggers,
input/output schema references, call sites, ownership, risk, human review,
model routing, evaluation readiness, and provenance.

The contract also enforces these cross-field rules:

- `high` and `critical` risk require human review;
- required human review needs at least one review stage and an explanation;
- fixed and dynamic model routing require a route reference;
- `baseline_ready` and `regression_ready` require evaluation evidence;
- provenance always includes at least one source reference.

## Fixtures

Examples live under `fixtures/valid/` and `fixtures/invalid/`. Invalid fixtures
document policy failures rather than malformed JSON syntax. Tests validate the
same business rules without requiring a third-party JSON Schema package.

The zero-dependency validator is intentionally scoped to this manifest
contract. It is not advertised as a general JSON Schema implementation.

Run the contract check from a source checkout with:

```powershell
$env:PYTHONPATH = "src"
python -m agentgov check capability prompt-governance/fixtures/valid/runtime-low-risk.json
```
