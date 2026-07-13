# Evaluation readiness policy

Evaluation readiness describes the evidence configuration around a capability.
It does not claim that the capability is accurate, safe, or production-ready.

## States

| State | Meaning | Check outcome |
|---|---|---|
| `not_configured` | No usable evaluation bundle has been configured. | `WARN` |
| `schema_only` | Contracts exist, but evaluation cases are not yet curated. | `WARN` |
| `needs_seed_cases` | Evaluation work is acknowledged but still needs reviewed seed material. | `WARN` |
| `baseline_ready` | Reviewed seed, golden, and failure cases exist, with explicit human baseline approval and evidence. | `PASS` |
| `regression_ready` | Baseline requirements pass and a numeric regression threshold is configured. | `PASS` |

## Reverse burden of proof

A higher label must be supported by the artifacts it names. Missing or invalid
evidence is a `FAIL`, not an automatic downgrade. This prevents a manifest from
claiming `baseline_ready` while silently behaving as `schema_only`.

For `baseline_ready` and `regression_ready`, the bundle must include at least:

- one reviewed seed case;
- one human-approved golden example;
- one reviewed failure case with a regression assertion;
- a named baseline reviewer;
- one baseline evidence reference.

`regression_ready` additionally requires a configured `minimum_pass_rate`
between `0` and `1`. The checker verifies configuration, not actual pass rate.

## Evidence boundaries

- Production-derived material must be explicitly marked `sanitized=true`.
- Draft seed cases do not support baseline readiness.
- Golden examples require named human approval and rationale.
- Failure cases must describe observed failure, expected behavior, and a
  machine-inspectable regression assertion.
- Case references must remain relative to the bundle and cannot traverse out of
  it or use symbolic links.
- Seed and curated examples are not a held-out benchmark unless a separate
  benchmark protocol establishes that status.

## Non-goals

This policy does not run models, score semantics, compare providers, set product
risk tolerance, or replace human adjudication.
