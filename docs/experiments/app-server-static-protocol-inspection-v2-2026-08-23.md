# App Server Static Protocol Inspection v2

## Outcome

The human-admitted static inspection stopped with normalized result:

```text
STOPPED_AFTER_SCHEMA_GENERATION_BEFORE_PROTOCOL_COMPARISON
```

Read-only command discovery found exactly one platform-native Windows
`codex.cmd` entry point and separately identified the PowerShell script wrapper
that blocked v1. One bounded help query through the native entry point
succeeded. Exactly one experimental App Server schema-generation subcommand
then completed inside one task-owned operating-system temporary directory.

Before the generated schema was analyzed, the comparison controller attempted
to use an encoding helper that is unavailable in the current execution
isolate. The task stopped at that first observed deviation. It did not replace
the helper, reread the schema, generate a second schema, start an App Server,
or retry. The task-created temporary directory was removed by the already
registered cleanup path.

The normalized first deviation is:

```text
stage: generated_schema_analysis
code: schema_analysis_controller_base64_encoder_unavailable
expected: the single generated schema is reduced to normalized thread/start compatibility facts
observed: schema generation succeeded, but the controller's encoding helper was unavailable before schema analysis began
```

The installed protocol was not compared with the v3 request. The required
classification therefore remains `indeterminate`; no compatibility or
incompatibility is inferred.

## Goal and boundaries

Task `p0-app-server-static-protocol-inspection-v2` authorized only a corrected
static comparison. It required platform-native command discovery before Codex
invocation, at most one schema-generation attempt, one verified task-owned
temporary directory, cleanup of that exact directory, and a stop at the first
deviation.

It prohibited an App Server daemon, initialize request, `thread/start`,
`turn/start`, MCP startup, prompt, model turn, executable substitution after
invocation, configuration repair, second schema generation, and retry. It did
not authorize changes to the retained synthetic repository, user Codex
configuration, Starter product source, dependencies, Git state, publication,
release, deployment, CI, or production systems.

## Preflight

Before any Codex invocation, bounded checks confirmed:

- the retained Harbor Notes baseline was clean at one local commit with zero
  remotes;
- its governance scaffold and project configuration were present;
- the normalized user-level trusted-project match count was zero;
- the complete user Codex configuration byte digest was captured without
  retaining its value or content;
- no matching App Server or AgentGov governance-MCP process was running;
- command discovery returned exactly one platform-native `codex.cmd`; and
- the discovered PowerShell script wrapper was not selected.

The native entry point's schema-generation help returned successfully and
confirmed bounded output and experimental-schema options. These facts prove
only command-surface availability, not protocol compatibility.

## Static trace

| Measure | Observed result |
| --- | --- |
| Native Starter task-admission decisions | 1 |
| Separate Starter task take-up | 1 |
| Platform-native Codex entries selected | 1 |
| PowerShell script wrappers selected | 0 |
| Native schema-help queries | 1, successful |
| Task-owned temporary directories | 1 created, 1 removed |
| Schema-generation subcommands | 1, successful |
| Generated-schema analyses | 0 |
| Static compatibility classifications | 1, `indeterminate` |
| App Server daemon processes | 0 |
| Initialize requests | 0 |
| `thread/start` requests | 0 |
| `turn/start` requests | 0 |
| MCP startups | 0 |
| External model turns | 0 |
| Inspection retries | 0 |

No raw schema, help output, executable path, temporary path, or protocol
payload is retained.

## Post-state verification

After the stop:

- the complete user Codex configuration byte digest exactly matched its
  pre-inspection value;
- the synthetic trusted-project match count remained zero;
- the synthetic repository remained clean at one commit with zero remotes;
- no matching task-owned temporary directory remained;
- no matching App Server or AgentGov governance-MCP process remained; and
- no consumer or Starter product implementation write occurred.

## Benefit and learning evidence

- `observed_fact`: platform-native Windows command discovery avoided the
  PowerShell script-wrapper boundary from v1.
- `observed_fact`: one experimental App Server schema-generation subcommand
  completed without starting an App Server daemon or model turn.
- `observed_fact`: cleanup and bounded host-state verification completed after
  the controller failure.
- `supported_inference`: parser prerequisites must be verified before schema
  generation if a future static comparison is admitted. This does not establish
  request compatibility.
- `unknown`: the installed `thread/start` fields and value constraints, v3
  request compatibility, required-MCP initialization, the v3 RPC cause,
  cross-host behavior, causal benefit, ROI, and real-user value.

This inspection does not satisfy the independent automatic-experience gate
and is not a fresh uncoached human pilot.

## Next product-review input

A later product review may decide whether to admit one parser-preflighted
static comparison that verifies its normalization mechanism before generating
schema. That suggestion grants no new inspection, parser replacement, schema
generation, App Server request, repair, replay, Git, publication, release,
deployment, or external authority.

## Starter validation

All 48 focused user-documentation tests passed. The supported Python 3.11 full
suite passed all 1000 tests with 3 platform-limited skips in 158.675 seconds.
Task governance reported `PASS=3 WARN=1 FAIL=0 ADVISORY=3`, and repository
governance reported `PASS=26 WARN=2 FAIL=0 ADVISORY=4`.

Scope reconciliation admitted all 6 static-v2-owned paths. It retained nine
failures for pre-existing, explicitly excluded, and untouched state: the
user-owned `.codex/config.toml`, the four earlier v1-v3 and diagnostic-v1 task
paths, and their four experiment records. No exception, ownership transfer, or
static-v2 mutation of those paths is inferred.

The task JSON parsed, the bounded primary-record privacy scan returned zero
matches, and `git diff --check` passed. The current callable Starter governance
inventory does not expose `agentgov_task_completion_record`, so no Starter
completion record is fabricated.

## Current-Agent advisory review

A distinct bounded current-Agent review found the admission, native-entry
selection, one-generation limit, first-deviation stop, cleanup, zero-daemon and
zero-model claims, post-state, scope, privacy, and non-publication boundary
consistent with the retained evidence. It confirmed that the record does not
claim the generated schema was analyzed or that the v3 request is compatible.

The review identified one current-Agent implementation-process observation:
the comparison controller did not preflight its encoding mechanism before
schema generation. That sequencing defect caused the admitted comparison to
stop after generation and leaves compatibility `indeterminate`. Whether a
preflighted parser would complete the comparison remains unknown and requires
a new human decision, not an inferred retry. This review is not native because
the fully specified task had no resolved alignment journey, and it is not
independent. It grants no inspection, parser replacement, schema generation,
App Server request, Git, publication, release, deployment, or external
authority.
