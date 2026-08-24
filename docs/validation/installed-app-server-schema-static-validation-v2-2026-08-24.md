# Installed App Server schema static validation v2

## Result

```text
STOPPED_AT_PROCESS_PREFLIGHT_BEFORE_SCHEMA_GENERATION
```

The first-deviation code is `process_record_invalid`. The normalized schema
compatibility status remains `indeterminate` because no installed schema was
generated or analyzed.

## Authorized boundary

Human-admitted task `p0-installed-app-server-schema-static-validation-v2`
authorized a dependency-free, read-only Windows process observer, a controlled
validation driver, and at most one installed experimental schema-generation
subcommand. The task allowed a complete nonzero ambient baseline but required
complete identity and lineage evidence, a stop at the first non-ready state,
and no retry.

It prohibited stopping or modifying ambient processes, executable
substitution, a second generation, App Server daemon launch, initialize,
`thread/start`, MCP startup, prompts, model requests, and model turns. It
granted no Git, publication, release, deployment, CI, or production authority.

## Implemented boundary

The new internal `windows_process_observer` transiently reads only the Windows
process fields required for relevant-class recognition, identity, and ancestry.
It immediately reduces them to normalized `codex_host`, `agentgov_service`, or
`python_service` facts and exposes only counts, readiness states, and stable
reason codes. Raw names, command lines, executable paths, process identifiers,
parent identifiers, usernames, and unrelated process data are not present in
public results or retained evidence.

The new internal `installed_schema_validation` driver verifies one native
`codex.cmd` and its bounded schema-generation help surface, composes the
existing `process_attribution_gate` and `app_server_schema_diagnostic`, limits
temporary output and JSON discovery, and registers exact temporary-directory
cleanup. It is not a public `agentgov` CLI feature. The two existing upstream
modules remained byte-identical.

## Controlled attempt

Before the host attempt, 28 new deterministic observer and driver tests, the 20
existing schema-diagnostic tests, and the 19 existing process-attribution tests
passed. Read-only command discovery selected one platform-native Windows entry,
and one help query confirmed the expected `generate-json-schema`, `--out`, and
`--experimental` surface.

The first process snapshot reduced the relevant ambient population to three
`codex_host` processes and one `agentgov_service` process. The observer also
returned `process_record_invalid`, so the deterministic preflight remained
`indeterminate` and the driver stopped before temporary-directory creation or
schema generation.

The retained attempt measures are:

| Normalized measure | Retained result |
| --- | --- |
| New deterministic observer tests before attempt | 14 passed |
| New deterministic driver tests before attempt | 14 passed |
| Existing schema-diagnostic tests before attempt | 20 passed |
| Existing process-attribution tests before attempt | 19 passed |
| Native command help queries | 1 |
| Ambient `codex_host` count | 3 |
| Ambient `agentgov_service` count | 1 |
| Schema-generation attempts | 0 |
| Task-owned temporary directories created | 0 |
| JSON documents discovered | 0 |
| JSON documents analyzed | 0 |
| App Server daemon launches | 0 |
| Initialize requests | 0 |
| `thread/start` requests | 0 |
| MCP startups | 0 |
| External model requests or turns | 0 |
| Retries or substitutions | 0 |
| Normalized compatibility status | 1, `indeterminate` |

## First-deviation diagnosis and correction

A separate privacy-bounded read-only count found exactly one Windows system
idle root record and no records with a missing name, missing creation time, or
invalid parent category. No raw record or identifier was retained. This
identifies that normalized root category as the cause of the observer's generic
invalid-record finding.

The observer now accepts that unrelated root record while still rejecting a
relevant process with an incomplete identity. A dedicated observer test
protects that Windows case. A post-stop, read-only normalized snapshot reports
`ready` with the same three `codex_host` and one `agentgov_service` counts and
no reason code. This is post-state evidence only, not a validation retry.

The admitted first-deviation rule was preserved: the full driver was not run
again, no schema was generated, and installed-schema compatibility was not
classified. Because the stopped driver returned before its post-state
fingerprint comparison, unchanged configuration, trust, and repository state
across the host attempt are not claimed. A bounded temporary-root count after
the stop was zero.

## Interpretation

- `observed_fact`: the reusable observer and controlled driver have
  deterministic privacy, process-lineage, one-attempt, schema-boundary, and
  cleanup coverage.
- `observed_fact`: the real v2 attempt honored the first-deviation stop and
  consumed zero schema-generation attempts.
- `observed_fact`: the Windows system idle root parsing defect is corrected and the
  normalized ambient baseline is now read-only `ready`.
- `unknown`: whether a fresh, separately admitted validation would generate a
  schema and classify the normalized request as compatible, incompatible, or
  indeterminate.
- `unknown`: runtime thread creation, required-MCP readiness, the earlier RPC
  cause, cross-host behavior, causal benefit, return on investment, and
  real-user value.

This stopped run is not an independent automatic-experience proof or a fresh
uncoached human pilot. No commit, push, pull request, publication, release,
deployment, CI, or production action occurred.

## Closeout validation and review

After the first-deviation correction, a distinct native current-Agent
self-review found two additional safety edges: the temporary-root validator
resolved before rejecting a supplied symbolic link, and a generation-timeout
branch could reach cleanup while its launched process remained active. It also
found that executable-path collection was unnecessary. The final source now
rejects the supplied root before resolution, waits for the single generation
process to exit without terminating it, and omits executable paths and
usernames from the host query. The full driver was not rerun.

The final 16 observer tests pass. All 16 driver tests pass except one
platform-limited file-symlink test that is skipped because link creation is
unavailable; the temporary-root link boundary remains covered without a real
link. All 54 user-documentation tests pass. The supported Python 3.11 full
suite passes all 1083 tests with 4 platform-limited skips in 176.055 seconds.

Task governance reports `PASS=3 WARN=1 FAIL=0 ADVISORY=3`; repository
governance reports `PASS=26 WARN=2 FAIL=0 ADVISORY=4`; task JSON parsing,
privacy scanning, upstream source hashing, and `git diff --check` pass. Scope
inspection passes all 12 admitted changed paths and reports 32 exact excluded
pre-existing paths. All 44 changed paths match an include or exclude, so the
unclassified count is zero; the non-green scope exit grants no exception or
ownership transfer.

Native advisory self-review
`srv-d80976dfa2b2f4877d59645e6c814970` completed as a separate pass after the
corrections and final validation. It is current-Agent review rather than
independent external assurance and grants no task acceptance, schema retry,
Git, publication, release, deployment, or external authority.
