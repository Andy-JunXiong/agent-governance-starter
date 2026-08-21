# Installed Codex-to-AgentGov initialize diagnostic - 2026-08-21

## Outcome

`INITIALIZE_HANDSHAKE_NOT_REPRODUCED_IN_BOUNDED_APP_SERVER`

The product owner selected diagnose-initialization-first through resolved
alignment journey `mcpj-d3402c1828a34ea3bca54073af84e7bc`. Native proposal
review admitted exact task
`p0-installed-codex-agentgov-initialize-diagnostic-v1`, and the product owner
separately started it.

The bounded diagnostic proved that the retained AgentGov server starts,
answers MCP initialize, and becomes ready inside a Codex App Server thread.
The earlier live TUI failure was not reproduced. The smallest remaining
unknown is therefore specific to the prior live host environment, its command
resolution or Codex-home boundary, the TUI path, or a transient condition; the
evidence does not select among them.

## Identity and preservation preflight

- The retained Python runtime remained `3.11.9` with distribution
  `agent-governance-starter 0.3.0rc1`.
- The retained remote-free AIRBNB clone remained detached at
  `d70615527d9acdde3893ce645d1923606173acf6` and changed only at its existing
  `.codex/config.toml` and `AGENTS.md` binding paths.
- The configured MCP command remained the bare `agentgov` launcher with
  Adapter arguments, a 10-second startup timeout, a 1,800-second tool timeout,
  eight enabled tools, and task completion enabled. Process-local `PATH`
  resolved that launcher to the retained runtime.
- The clone README retained `### One-command demo`; it gained no task or
  AgentGov state.
- The original AIRBNB HEAD remained
  `e8cf191b0b31fe203ea6ee129de4cb94acb94aee`. Its Codex-config and Agent-guide
  hashes remained
  `5431EC09F10FAC4194D79BD4A645402C13D9CFD07442DD6789BD752AC744BF4D`
  and `9B83B26EE8464D879E887EEEA3BC20B6F5A16A34B4D2B89C800E1A9AF9F95C9F`.

## Direct AgentGov boundary

An initial diagnostic-harness invocation passed a modified `PATH` only to the
child environment after Windows executable resolution had already selected an
older global launcher. Its Adapter `1.4.0`, seven-tool result was classified as
a harness error, not a product result. No repository or configuration changed.

The corrected invocation updated the diagnostic parent process `PATH` before
resolving the configured command. It resolved to the retained runtime and
completed with exit zero, no stderr, MCP protocol `2025-11-25`, Adapter
`1.6.0`, eight tools, and `agentgov_task_completion_record`. Both initialize
and tools-list responses were present.

This proves that the retained AgentGov process and its direct initialize
response are not the current failure boundary.

## Codex App Server boundary

The diagnostic followed the official
[Codex App Server lifecycle](https://developers.openai.com/codex/app-server/):
initialize the connection, send `initialized`, then call `thread/start`. It
never sent `turn/start`.

Codex App Server `0.149.0-alpha.4` initialized successfully. The official page
currently shows camel-case `workspaceWrite` in its thread example, while this
installed version rejected that value with `-32600` and required
`workspace-write`. That rejected request created no thread and reached no MCP
boundary. The corrected request was sent on the same connection.

The corrected `thread/start` succeeded. It created one empty, turn-free thread
under the sandbox-provided Codex home, emitted `thread/started`, and reported
required server `agentgov_governance` first as `starting` and then `ready` with
no MCP error. No `turn/*` or `item/*` event occurred.

App Server startup attempted its own featured-plugin and curated-plugin network
refreshes; they failed in the restricted environment and installed nothing.
After the empty thread became ready, Codex also attempted to open a Responses
WebSocket, which failed TLS validation before a connection was established.
No turn request, model payload, Agent response, tool call, or source content
was sent. The exact diagnostic Codex and retained AgentGov processes were then
terminated; unrelated processes were left running.

## Classification and remaining unknown

The deterministic boundary result is:

- AgentGov process startup: pass;
- direct MCP initialize and tools-list: pass;
- Codex App Server connection initialize: pass;
- Codex-required AgentGov startup inside `thread/start`: pass;
- Codex thread creation without a turn: pass;
- reproduction of the prior TUI `-32603` initialize failure: no;
- model turn or governed consumer journey: not run.

The diagnostic narrows the prior failure away from the retained AgentGov
binary, its direct MCP response, and generic Codex App Server integration in
the sandboxed host. It does not prove whether the prior deviation came from
the user-host Codex home, TUI-specific behavior, command-resolution drift, or
a transient startup condition. Testing those alternatives would require a new
human-owned requirement because it could create user-local Codex state, reach
external services, change the consumer binding, or launch another live run.

## Starter validation

The first complete Starter-suite pass found one documentation consistency
failure: current status no longer contained the historical replay outcome
identifier required by the existing bounded-evidence test. Status was
corrected to retain that superseded result without weakening or deleting the
test.

The final Python 3.11.9 suite passed all 946 tests with 3 platform-limited
skips in 260.078 seconds. The focused user-documentation suite passed all 38
tests. Task governance returned `PASS=3 WARN=1 FAIL=0 ADVISORY=3`, repository
governance returned `PASS=26 WARN=2 FAIL=0 ADVISORY=4`, and
`git diff --check` passed. Scope reconciliation admitted the 4 exact
diagnostic-owned paths and retained 10 failures for explicitly excluded prior-
task or user paths; no exception or ownership transfer was inferred.
After advisory evidence write-back, the focused 38-test suite and diff check
passed again. The task JSON parsed, and bounded host-absolute-path and
recognized credential-marker scans returned zero matches.

## Completion and advisory review

The current Agent's callable governance inventory did not expose
`agentgov_task_completion_record`, so no Starter completion record was
fabricated. Native current-Agent self-review
`srv-47c9c47323b97e67fc4cd11c689df32a` completed as a distinct advisory pass
with requirement, architecture, scope, implementation, and security
observations. It found the no-model outcome, harness-error classification,
admitted-path ownership, validation, privacy, and stop boundaries consistent.

The review retained the earlier user-host TUI failure cause, user-host versus
sandboxed-host differences, TUI-specific behavior, command-resolution drift,
transient conditions, and future Codex schema behavior as unknown. It granted
no task, scope, exception, Git, release, deployment, publication, or external
authority.

## Privacy and authority boundary

The user Codex configuration remained byte-unchanged. Starter HEAD, index and
remotes; the original AIRBNB repository; the retained clone; and existing
runtimes remained unchanged. The empty sandbox-local thread artifact is
retained because cleanup was outside task authority.

This record contains no raw protocol response, prompt, transcript, source
content, credential, private data, temporary absolute path, thread identity,
installation identity, external-model payload, or unbounded host log. It
retains only normalized results. No product or consumer repair, dependency
download, model turn, second live replay, cleanup, commit, push, publication,
release, deployment, or broader activation occurred.
