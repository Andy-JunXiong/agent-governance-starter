# App Server Thread-Start No-Model Diagnostic v1

## Outcome

The human-admitted diagnostic stopped with normalized result:

```text
STOPPED_BEFORE_PROTOCOL_COMPARISON_AND_APP_SERVER_REQUEST
```

The first deviation was not the v3 `thread/start` RPC failure. The read-only
protocol-inspection batch invoked the installed `codex` command from
PowerShell, which resolved to a script wrapper blocked by the local execution
policy. Both already-started help requests returned that same boundary. The
Agent observed the batch result, stopped, and did not substitute another
executable, compare the installed protocol, or start an App Server.

The normalized first deviation is:

```text
stage: installed_protocol_inspection
code: powershell_codex_script_wrapper_blocked
expected: read-only installed App Server help and schema inspection succeeds before any live request
observed: the inspection batch was blocked at the PowerShell script-wrapper boundary before protocol output or an App Server process existed
```

This result does not classify the cause of the v3 `thread/start` failure.
Request shape, sandbox policy, required-MCP startup, host capability
negotiation, and other App Server preconditions all remain unknown.

## Goal and boundaries

Task `p0-app-server-thread-start-no-model-diagnostic-v1` authorized one
trust-independent, no-model diagnostic. Read-only local protocol inspection
had to precede any live confirmation. A live phase could use at most one App
Server process and one ephemeral `thread/start` request, but only if every
earlier gate passed. The task prohibited `turn/start`, prompts, model turns,
configuration repair, executable substitution after a deviation, restart,
second thread request, and retry.

It did not authorize changes to the retained synthetic repository, user Codex
configuration, Starter product source, dependencies, Git state, publication,
release, deployment, CI, or production systems.

## Preflight

Before the inspection batch, bounded checks confirmed:

- the single retained Harbor Notes baseline was available and semantically
  identified without retaining its private path;
- its worktree was clean at one local commit with zero remotes;
- its governance scaffold and project configuration were present;
- the normalized user-level trusted-project match count was zero;
- the complete user Codex configuration byte digest was captured without
  retaining its value or content; and
- no matching App Server or AgentGov governance-MCP process was running.

These gates permitted static inspection. They did not authorize or prove a
live App Server request.

## Diagnostic trace

| Measure | Observed result |
| --- | --- |
| Native Starter task-admission decisions | 1 |
| Separate Starter task take-up | 1 |
| Read-only protocol-inspection commands | 2, one parallel batch |
| Protocol-inspection commands completed | 0 successful; 2 wrapper-blocked |
| Installed protocol comparisons | 0 |
| App Server processes started | 0 |
| `thread/start` requests | 0 |
| Ephemeral threads created | 0 |
| `turn/start` requests | 0 |
| External model turns | 0 |
| Native consumer forms | 0 |
| Consumer AgentGov tool calls | 0 |
| Consumer repository writes | 0 |
| Diagnostic retries | 0 |
| App Server restarts | 0 |

The two help commands were launched together before either result was
observed. No command, executable substitution, or live request followed the
first observed deviation.

## Post-state verification

After the stop:

- the complete user Codex configuration byte digest exactly matched its
  pre-inspection value;
- the synthetic trusted-project match count remained zero;
- the synthetic repository remained clean at one commit with zero remotes;
- no matching App Server or AgentGov governance-MCP process remained; and
- no consumer or Starter product implementation write occurred.

No raw command output, protocol payload, source content, validation output,
credential, private path, external identity, configuration digest, or
model-private reasoning is retained here.

## Benefit and learning evidence

- `observed_fact`: the stop occurred before any App Server process, ephemeral
  thread, MCP startup, or model request.
- `observed_fact`: pre-state and post-state matched across the bounded user
  configuration, trust, synthetic Git, remote, and process checks.
- `observed_fact`: the selected PowerShell command name is not a usable
  read-only inspection entry point on this host under its current execution
  policy.
- `supported_inference`: executable resolution is a prerequisite that should
  be verified before a future protocol diagnostic begins. This does not
  explain the v3 RPC failure.
- `unknown`: the installed `thread/start` contract, the v3 request mismatch if
  any, required-MCP initialization, successful tool discovery, consumer
  journey behavior, cross-host behavior, causal benefit, ROI, and real-user
  value.

This diagnostic does not satisfy the independent automatic-experience gate
and is not a fresh uncoached human pilot.

## Next product-review input

A later product review may decide whether to admit a corrected static-only
inspection that selects the platform-native executable before execution,
compares the installed protocol, and still stops before an App Server request.
That suggestion grants no diagnostic, executable substitution, repair, replay,
Git, publication, release, deployment, or external authority.

## Starter validation

All 47 focused user-documentation tests passed. The supported Python 3.11 full
suite passed all 999 tests with 3 platform-limited skips in 149.716 seconds.
Task governance reported `PASS=3 WARN=1 FAIL=0 ADVISORY=3`, and repository
governance reported `PASS=26 WARN=2 FAIL=0 ADVISORY=4`.

Scope reconciliation admitted all 6 diagnostic-owned paths. It retained seven
failures for pre-existing, explicitly excluded, and untouched state: the
user-owned `.codex/config.toml`, all three v1-v3 task paths, and all three
v1-v3 experiment records. No exception, ownership transfer, or diagnostic
mutation of those paths is inferred.

The task JSON parsed, the bounded primary-record privacy scan returned zero
matches, and `git diff --check` passed. The current callable Starter governance
inventory does not expose `agentgov_task_completion_record`, so no Starter
completion record is fabricated.

## Current-Agent advisory review

A distinct bounded current-Agent review found the admission, first-deviation
stop, zero-App-Server and zero-model claims, post-state, scope, privacy, and
non-publication boundary consistent with the retained evidence. No evidence
correction is required inside the admitted task.

The review identified one implementation-process observation: executable
resolution was not itself verified before the two-command inspection batch,
so the diagnostic stopped before its intended protocol comparison. Whether a
platform-native entry point would expose usable protocol evidence remains
unknown and requires a new human decision, not an inferred retry. This review
is not native because the fully specified task had no resolved alignment
journey, and it is not independent. It grants no diagnostic, substitution,
repair, replay, Git, publication, release, deployment, or external authority.
