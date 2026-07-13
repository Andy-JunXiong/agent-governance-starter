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

The checker validates configuration and evidence shape. It does not run a model
or determine whether outputs are semantically correct.
