# Disposable automatic-journey rehearsal v3 - 2026-08-23

## Outcome

`STOPPED_BEFORE_EPHEMERAL_THREAD_AND_MODEL_TURN`

Native proposal review admitted exact task
`p0-disposable-automatic-journey-rehearsal-v3` through proposal
`prp-8a42b6c98f4242bf89fe0b4c8d911958`, and the product owner separately
started that task.

The v3 design removed the v2 dependency on project-scoped trust. One Codex
App Server process received the AgentGov MCP definition only through one-run
CLI configuration overrides. App Server initialization succeeded, but its
only `thread/start` request returned an RPC error before an ephemeral thread,
MCP status inventory, or model turn existed. The attempt stopped immediately
without repair, restart, or retry.

## Prepared boundary

The retained synthetic Harbor Notes repository from v2 was reused. Read-only
checks confirmed that it was the same available Git worktree, clean at one
local baseline commit, and configured with zero remotes. Its generated name,
absolute path, commit identity, and source content are not retained here.

The user-level Codex configuration parsed successfully. Before launch, the
synthetic project had zero matching trusted-project entries. A byte digest of
the complete user configuration was captured without retaining its content or
digest value.

Readiness identified Codex CLI `0.146.0` and AgentGov `0.3.0rc1`. The installed
AgentGov command passed its repository doctor check. The v2 retained evidence
already identifies Adapter `1.6.0`; v3 did not start a second direct MCP probe
to repeat that measurement.

## App Server preflight and first deviation

Exactly one App Server process was launched over stdio with strict
configuration parsing. Its one-run CLI override supplied only the AgentGov MCP
server command, arguments, synthetic working directory, `required=true`, the
eight-tool allow-list, automatic tool approval mode, and bounded startup and
tool timeouts. The synthetic project-local `.codex/config.toml` was not used as
the source of this binding.

The client declared structured MCP form elicitation support and completed the
App Server initialize handshake. It then sent exactly one `thread/start`
request with the synthetic repository as the working directory and
`ephemeral=true`. That request returned a bounded RPC failure before a thread
response or `thread/started` event. Because the required MCP is initialized as
part of thread startup, the retained evidence cannot safely distinguish an
MCP initialize failure from another thread-start boundary. No raw error,
stderr, protocol event, or path is retained to speculate further.

The first deviation is:

```text
stage: app_server_thread_start
code: app_server_thread_start_rpc_error
expected: required AgentGov MCP initializes and one ephemeral thread is returned before model use
observed: initialize succeeded, the only thread/start returned an RPC error, and no thread, tool inventory, or model turn was created
```

The task required stopping at this point. No configuration adjustment,
diagnostic restart, direct MCP probe, second App Server process, second thread
request, or model request followed.

## Interaction and friction record

| Measure | Observed result |
| --- | --- |
| Native Starter task-admission decisions | 1 |
| Separate Starter task take-up | 1 |
| App Server processes | 1 |
| App Server initialize handshakes | 1, completed |
| `thread/start` requests | 1, RPC failure |
| Ephemeral threads created | 0 |
| MCP status inventories | 0 |
| External model turns | 0 |
| Native consumer forms | 0 |
| Consumer AgentGov tool calls | 0 |
| Consumer tasks admitted | 0 |
| Consumer implementation writes | 0 |
| Consumer validation runs | 0 |
| Consumer completion records | 0 |
| Consumer self-reviews | 0 |
| Project-trust prompts | 0 |
| Model-session retries | 0 |
| App Server restarts | 0 |

The pre-model stop was visible in the current human surface. No consumer
Monitor event or protection-resolution link existed because there was no
thread or Agent turn. Protection-event resolution visibility therefore
remains `unknown`, not passed.

## Post-state verification

After the stopped process exited:

- the complete user-level Codex configuration byte digest exactly matched its
  pre-launch value;
- the synthetic project still had zero trusted-project matches;
- the synthetic repository remained clean at one commit with zero remotes;
- no matching App Server or AgentGov governance-MCP process remained; and
- the Starter repository had received no replay implementation write.

This proves the v3 attempt did not recreate the v2 trust-entry mutation. It
does not prove the one-run MCP override initialized successfully, because the
thread failed before status discovery.

## Benefit and Learning evidence

- `observed_fact`: the one-run App Server path completed initialization without
  a project-trust prompt or user-configuration change.
- `observed_fact`: the required pre-model thread gate stopped the attempt before
  any model request when `thread/start` failed.
- `observed_fact`: the retained synthetic repository and user configuration
  matched their pre-launch bounded state after process exit.
- `supported_inference`: one-run CLI configuration plus an ephemeral-thread
  requirement is a safer trust lifecycle than the v2 interactive project-trust
  path for this host. It does not establish that AgentGov initialized or that
  the governed journey works.
- `unknown`: the normalized cause of the `thread/start` RPC failure, successful
  eight-tool discovery through this exact path, form presentation, separate
  consumer take-up, implementation, validation, completion, current-Agent
  review, cross-host behavior, causal benefit, ROI, and real-consumer value.

## Preservation and authority boundary

The retained synthetic repository remains available, clean, remote-free, and
at its single baseline commit. The v3 task grants no authority to remove it,
repair the thread-start boundary, retry the App Server path, or start another
model turn.

No existing consumer repository, Starter product source, dependency, user
configuration, remote Git state, publication, release, deployment, CI, or
production system changed during the measured attempt. No raw request,
response, transcript, source content, validation output, credential, private
path, external session identity, configuration digest, or model-private
reasoning is retained in this record.

This rehearsal does not satisfy the independent automatic-experience gate and
is not a fresh uncoached human pilot. A later product review may consider a
separately admitted no-model diagnostic that classifies the required-MCP
thread-start failure without launching a model. This suggestion grants no
diagnostic, repair, replay, Git, publication, release, deployment, or external
authority.

## Starter validation

All 46 focused user-documentation tests passed. The supported Python 3.11 full
suite passed all 998 tests with 3 platform-limited skips in 152.646 seconds.
Task governance reported `PASS=3 WARN=1 FAIL=0 ADVISORY=3`, and repository
governance reported `PASS=26 WARN=2 FAIL=0 ADVISORY=4`.

Scope reconciliation admitted all 6 v3 task-owned paths. It retained five
failures for pre-existing, explicitly excluded, and untouched state: the
user-owned `.codex/config.toml`, both v1 task/evidence paths, and both v2
task/evidence paths. No exception, ownership transfer, or v3 mutation of those
paths is inferred.

The v3 task JSON parsed, corrected bounded privacy scans over the v3-owned
record and shared new-identity surfaces returned zero matches, and
`git diff --check` passed. The current callable Starter governance inventory
does not expose `agentgov_task_completion_record`, so no Starter completion
record is fabricated.

## Current-Agent advisory review

A distinct bounded current-Agent review found no correction required within
the admitted v3 evidence scope. The task admission, single-process and
single-request limits, first-deviation stop, zero-model boundary, unchanged
user configuration, clean synthetic post-state, privacy boundary, validation,
and non-publication authority remain consistent with the retained evidence.

The review keeps the RPC failure cause, required-MCP initialization, successful
tool discovery, form behavior, consumer journey, and causal product benefit as
unknown. It is not a native self-review because v3 had no resolved alignment
journey, and it is not an independent review. It grants no diagnostic, repair,
replay, Git, publication, release, deployment, or external authority.
