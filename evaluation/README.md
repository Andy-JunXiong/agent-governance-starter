# Evaluation readiness

This directory defines evidence contracts for evaluation readiness without
claiming to be a production benchmark platform.

## Bundle contract

An evaluation bundle contains:

```text
evaluation-manifest.json
seed-cases/*.json
golden-examples/*.json
failure-cases/*.json
```

The manifest declares readiness and references every counted case. References
must stay inside the bundle, use forward slashes, and avoid symbolic links.

Schemas live under `schemas/`:

- `evaluation-manifest.schema.json`
- `seed-case.schema.json`
- `golden-example.schema.json`
- `failure-case.schema.json`

See [the readiness policy](readiness-policy.md) for the evidence required by
each label.

Readiness and outcome are deliberately separate. Use `declared_readiness` for
evidence maturity and the optional `decision` object for a reviewed `accepted`,
`accepted_with_conditions`, or `rejected` outcome. The
[`regression-ready-rejected`](fixtures/regression-ready-rejected) fixture shows
complete evidence for a candidate that did not outperform its named baseline.

## Check command

```powershell
agentgov check evaluation path/to/evaluation-bundle
```

- `not_configured`, `schema_only`, and `needs_seed_cases` produce `WARN` and
  exit `0` when honestly declared.
- Supported `baseline_ready` and `regression_ready` bundles produce `PASS`.
- Invalid artifacts or unsupported high-readiness claims produce `FAIL` and
  exit `1`.
- Path and read errors return `2`.

Regression thresholds may be a case pass rate or a relative comparison against
a named baseline. The checker validates configuration and evidence shape. It
does not run a model, calculate metrics, determine whether outputs are
semantically correct, or authorize release.
