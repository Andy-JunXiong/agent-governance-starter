---
adr: "0001"
title: "Separate evaluation readiness from evaluation decisions"
status: Accepted
created: "2026-07-23"
owners:
  - "Project owner"
related:
  - "evaluation/readiness-policy.md"
---

# ADR-0001: Separate evaluation readiness from evaluation decisions

## Decision gate

- [x] Reversing the decision later would have meaningful cost.
- [x] Future maintainers would lose important context without this record.
- [x] At least two plausible alternatives have a real tradeoff.

## Context

Evaluation readiness currently describes whether reviewed cases, baseline
evidence, and regression thresholds are configured. Cross-domain use cases also
need to record whether a reviewed candidate was accepted or rejected. Treating
rejection as a low-readiness state would incorrectly describe complete
evaluation evidence as incomplete. Treating `regression_ready` as permission to
release would contradict the project's human-authorization boundary.

Traditional model evaluations may also use relative metrics such as WAPE or
RMSE against a named baseline rather than a case pass rate.

## Decision

Evidence readiness and evaluation decision are separate, orthogonal concepts.

- `declared_readiness` continues to describe evidence configuration only.
- An optional `decision` records `pending`, `accepted`,
  `accepted_with_conditions`, or `rejected`.
- A completed decision requires a reason, reviewer, review date, and evidence.
- Regression readiness supports exactly one configured threshold form: numeric
  case pass rate or comparison with a named baseline.
- Neither readiness nor decision grants permission to publish, release, merge,
  or deploy.

The v1.0 additions remain optional for compatibility. Once declared, their
contents are validated strictly.

## Owns

- The repository contract separating evidence maturity from evaluation outcome.
- The machine-readable forms of pass-rate and baseline-comparison thresholds.

## Does not own

- Model execution, metric calculation, semantic quality judgment, release
  authorization, or domain-specific acceptance thresholds.

## Invariants created or changed

- Invariant record: `none`
- Enforcement point: `src/agentgov/evaluation.py` and
  `evaluation/schemas/evaluation-manifest.schema.json`

## Consequences

### Benefits

- Complete evidence can accompany an honest rejected outcome.
- Prompt cases and traditional model comparisons share one evidence contract
  without pretending their thresholds are identical.

### Costs and risks

- Consumers must not collapse readiness and decision into one status.
- Date fields record review context but do not imply an expiry policy.

### Operational impact

- None. The starter validates repository files and does not run evaluations.

## Alternatives considered

### Add `evaluated_rejected` to readiness

This conflates evidence completeness with outcome and makes rejected,
well-evaluated candidates appear less mature.

### Keep evaluation prompt-specific

This avoids schema growth but prevents honest representation of common model
release gates.

### Build a general evaluation runner

This exceeds the starter's scope and would duplicate project-specific harnesses.

## Implementation plan

1. Extend the manifest schema and zero-dependency checker compatibly.
2. Add accepted/rejected examples, tests, and user-facing policy guidance.

Release remains a separate human approval gate.

## Validation

- Automated: `$env:PYTHONPATH = "src"; python -m unittest discover -s tests -v`
- Manual: inspect the rejected regression fixture for semantic clarity.
- Success signal: legacy fixtures still pass and a regression-ready rejected
  candidate validates without being described as production-ready.

## Rollback or replacement

Remove the optional fields only in a new schema version and migrate consumers
that use them. Do not reinterpret existing readiness values as decisions.

## Open questions

- Whether decision expiry belongs in this manifest or a repository policy.
- Whether capability dependencies require readiness-specific gates.
