# App Server Parser-Preflight Static Comparison v3

## Outcome

The human-admitted static comparison stopped with normalized result:

```text
STOPPED_AT_PARSER_PREFLIGHT_BEFORE_SCHEMA_GENERATION
```

Fresh host and command-discovery gates passed. The retained synthetic baseline
was clean and remote-free, user trust remained absent, no relevant process or
task-owned temporary directory existed, and exactly one platform-native
Windows Codex entry point was available while the PowerShell script wrapper
remained unselected.

The exact planned parser was then invoked once against an in-memory synthetic
schema. Its process exited nonzero without returning the required normalized
self-test result. The task stopped at that first deviation. The parser was not
changed, rerun, or replaced; Codex was not invoked; no schema was generated;
and no temporary directory, App Server daemon, thread, MCP, or model turn was
created.

The normalized first deviation is:

```text
stage: parser_self_test
code: parser_self_test_process_failed_without_normalized_result
expected: the exact parser returns a normalized compatible result for the in-memory synthetic schema
observed: the single parser self-test process exited nonzero before returning a normalized result
```

No raw error output was retained. Whether the failure arose from invocation,
serialization, parser implementation, or another local precondition remains
unknown. The installed App Server schema and v3 request were not inspected, so
their compatibility remains `indeterminate`.

## Goal and boundaries

Task `p0-app-server-parser-preflight-static-comparison-v3` authorized a
static-only comparison only after the exact parser passed an in-memory
self-test. The self-test had to cover recursive discovery, local-reference
resolution, enum and primitive-type extraction, and normalized classification.
Schema generation could occur exactly once only after every earlier gate
passed.

The task prohibited parser replacement after preflight, retry, a second
schema-generation attempt, App Server launch, initialize, `thread/start`,
`turn/start`, MCP startup, prompt, and model turn. It did not authorize changes
to the synthetic repository, user configuration, Starter product source,
dependencies, Git state, publication, release, deployment, CI, or production
systems.

## Preflight

Before the parser self-test, bounded checks confirmed:

- the retained Harbor Notes repository was clean at one local commit with zero
  remotes;
- its governance scaffold and project configuration were present;
- the normalized user-level trusted-project match count was zero;
- the complete user Codex configuration byte digest was captured without
  retaining its value or content;
- no matching App Server, AgentGov governance-MCP, parser, or task-owned
  temporary process or directory existed;
- command discovery returned exactly one platform-native `codex.cmd`; and
- the discovered PowerShell script wrapper was not selected.

These gates permitted the parser self-test only. They did not authorize schema
generation after that self-test failed.

## Static trace

| Measure | Observed result |
| --- | --- |
| Native Starter task-admission decisions | 1 |
| Separate Starter task take-up | 1 |
| Platform-native Codex entries discovered | 1 |
| PowerShell script wrappers selected | 0 |
| Parser self-test processes | 1, nonzero exit |
| Normalized parser self-test results | 0 |
| Codex invocations | 0 |
| Schema-help queries | 0 |
| Schema-generation subcommands | 0 |
| Task-owned temporary directories | 0 |
| Generated-schema analyses | 0 |
| Static compatibility classifications | 1, `indeterminate` |
| App Server daemon processes | 0 |
| Initialize requests | 0 |
| `thread/start` requests | 0 |
| `turn/start` requests | 0 |
| MCP startups | 0 |
| External model turns | 0 |
| Parser or inspection retries | 0 |

## Post-state verification

After the stop:

- the complete user Codex configuration byte digest exactly matched its
  pre-inspection value;
- the synthetic trusted-project match count remained zero;
- the synthetic repository remained clean at one commit with zero remotes;
- no matching task-owned temporary directory or parser process existed;
- no matching App Server or AgentGov governance-MCP process existed; and
- no consumer or Starter product implementation write occurred.

No raw parser error, source payload, schema, executable path, temporary path,
protocol payload, credential, private identity, configuration digest, or
model-private reasoning is retained.

## Benefit and learning evidence

- `observed_fact`: the parser gate prevented schema generation after its own
  self-test failed.
- `observed_fact`: command, trust, repository, process, and configuration
  preflight remained stable before and after the stop.
- `supported_inference`: a reusable, directly testable Adapter diagnostic is a
  safer next design input than another unverified inline parser invocation.
  This does not authorize or prove that design.
- `unknown`: the parser failure cause, installed `thread/start` constraints,
  v3 request compatibility, required-MCP initialization, the v3 RPC cause,
  cross-host behavior, causal benefit, ROI, and real-user value.

This inspection does not satisfy the independent automatic-experience gate
and is not a fresh uncoached human pilot.

## Next product-review input

A later product review should decide whether to stop one-off inspection tasks
and instead design a small, reusable Adapter diagnostic with ordinary unit
tests before any further schema or App Server rehearsal. That suggestion
grants no source change, parser diagnosis, schema generation, App Server
request, repair, replay, Git, publication, release, deployment, or external
authority.

## Starter validation

All 49 focused user-documentation tests passed. The supported Python 3.11 full
suite passed all 1001 tests with 3 platform-limited skips in 157.029 seconds.
Task governance reported `PASS=3 WARN=1 FAIL=0 ADVISORY=3`, and repository
governance reported `PASS=26 WARN=2 FAIL=0 ADVISORY=4`.

Scope reconciliation admitted all 6 parser-v3-owned paths. It retained eleven
failures for pre-existing, explicitly excluded, and untouched state: the
user-owned `.codex/config.toml`, the five earlier v1-v3, diagnostic-v1, and
static-v2 task paths, and their five experiment records. No exception,
ownership transfer, or parser-v3 mutation of those paths is inferred.

The task JSON parsed, the bounded primary-record privacy scan returned zero
matches, and `git diff --check` passed. The current callable Starter governance
inventory does not expose `agentgov_task_completion_record`, so no Starter
completion record is fabricated.

## Current-Agent advisory review

A distinct bounded current-Agent review found the admission, parser gate,
first-deviation stop, zero-Codex and zero-model claims, post-state, scope,
privacy, and non-publication boundary consistent with the retained evidence.
It confirmed that the record does not claim a parser diagnosis, schema
generation, or protocol compatibility result.

The review identified a repeated implementation-pattern concern: three
successive one-off diagnostics stopped at command, controller, or parser
plumbing before completing the intended static comparison. Continuing with
another inline inspection would risk activity without product progress. A
small reusable Adapter diagnostic with ordinary unit tests is the stronger
product-review candidate, but its product fit, scope, and ten-minute-adoption
impact remain undecided. This review is not native because the fully specified
task had no resolved alignment journey, and it is not independent. It grants
no source change, diagnostic, parser work, schema generation, App Server
request, Git, publication, release, deployment, or external authority.
