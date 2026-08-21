# User-host Codex-to-AgentGov no-model comparison - 2026-08-21

## Purpose and authority

The product owner selected the user-host no-model comparison through resolved
alignment journey `mcpj-f565c4f45c9149588cece61d2f7afcd3`. Native proposal
review admitted
`p0-user-host-codex-agentgov-no-model-comparison-v1`, and the product owner
separately started it.

The task permitted one separately approved user-host Codex startup to compare
the remaining host boundary. It did not authorize repair, launcher pinning,
prompt submission, `turn/start`, a model interaction, retry, a second launch,
cleanup, Git operations, publication, release, deployment, or broader
activation.

## Read-only preflight

The retained Python 3.11.9 runtime still reported AgentGov `0.3.0rc1`. The
remote-free AIRBNB clone remained detached at
`d70615527d9acdde3893ce645d1923606173acf6`, changed only at its two existing
binding paths. Its project configuration still declared one required
`agentgov_governance` server using the bare `agentgov` command, Adapter host
profile, 10-second startup timeout, and eight enabled tools.

With the retained runtime Scripts directory first on the diagnostic parent
process `PATH`, the bare command resolved to the retained launcher. The user
Codex configuration contained no user-level MCP server and retained five
project trust entries. Its byte length and SHA-256 matched the preceding
diagnostic. Codex remained `0.149.0-alpha.4`.

The original AIRBNB repository retained HEAD
`e8cf191b0b31fe203ea6ee129de4cb94acb94aee`; its Codex configuration and Agent
guide hashes matched the preceding record. Its full status check retained a
permission warning for the existing local AgentGov directory, so this task
does not claim a clean original worktree from that command.

One existing AgentGov process and five existing Codex processes were recorded
before the diagnostic. They were treated as unrelated and were not stopped or
modified.

## Single user-host comparison

The product owner separately approved exactly one Codex App Server launch. It
used the retained runtime on process-local `PATH`, the remote-free clone as its
working directory, and the same process-local inline worktree-trust form used
by the prior bounded comparison. No user configuration was edited.

The App Server connection initialized successfully and identified the real
user Codex home rather than the sandbox-provided Codex home. The diagnostic
sent `initialized` and one `thread/start` request with `approvalPolicy=never`
and `sandbox=workspace-write`. It never sent `turn/start`.

During `thread/start`, the host recognized the clone's required
`agentgov_governance` server, reached its MCP handshake, and then returned
`-32603`: the connection closed while producing the initialize response. The
thread request failed. No `thread/started`, turn, item, prompt, model payload,
Agent response, or tool-call event occurred.

The exact diagnostic App Server process was terminated immediately after the
first result. No retry or second launch occurred. The pre-existing Codex and
AgentGov processes remained present and were not touched.

## Differential classification

The deterministic result is
`USER_HOST_INITIALIZE_FAILURE_REPRODUCED_NO_MODEL_TURN`:

- retained parent-process launcher resolution: pass;
- project configuration selection: pass, because the required server was
  recognized;
- user-host App Server connection initialize: pass;
- required AgentGov MCP initialize handshake: fail with the same `-32603`
  boundary as the earlier live TUI launch;
- thread creation: fail before `thread/started`;
- model turn or governed consumer journey: not run.

The previous sandboxed App Server comparison passed with the same Codex build,
retained runtime, remote-free clone, project binding, and no-turn lifecycle.
This comparison therefore localizes the reproducible deviation to the real
user-host Codex-home or host-process context. It does not distinguish whether
the remaining cause is child-process command resolution, inherited host
environment, user-home state, or another TUI/user-host-specific condition.
Resolving that smaller cause requires a separately selected and admitted
requirement; this task made no repair.

## State, privacy, and preservation

The user Codex configuration hash and byte length remained unchanged. The
retained clone HEAD, zero-remotes state, two changed binding paths, and the
three checked file hashes remained unchanged. No new file under the user Codex
home was observed from the startup-time metadata cutoff. Five existing files
were modified after that cutoff: two JSON files, one log, and two SQLite WAL
files. Because the five pre-existing Codex processes remained active, those
shared-file modifications cannot be attributed to this diagnostic. No file
content or session identity was inspected, and no cleanup was attempted.

This record contains no raw protocol response, prompt, transcript, source
content, credential, private data, user or temporary absolute path, thread
identity, installation identity, process identity, external-model payload, or
unbounded host log. No repair, launcher pinning, model turn, governed replay,
dependency download, cleanup, commit, push, publication, release, deployment,
or broader activation occurred.

## Starter validation

The exact Python 3.11.9 repository suite passed all 946 tests with 3 platform-
limited skips in 268.686 seconds. Task governance returned
`PASS=3 WARN=1 FAIL=0 ADVISORY=3`, repository governance returned
`PASS=26 WARN=2 FAIL=0 ADVISORY=4`, and `git diff --check` passed. Scope
reconciliation admitted the 4 exact task-owned paths and retained 12 failures
for explicitly excluded prior-task or user-owned paths; no exception or
ownership transfer was inferred. The task JSON parsed, and bounded host-
absolute-path and recognized credential-marker scans returned zero matches.

## Completion and advisory review

The current Agent's callable governance inventory did not expose
`agentgov_task_completion_record`, so no Starter completion record was
fabricated. Native current-Agent self-review
`srv-0022f90a035fd6310dc67aa983c2cbe7` completed as a distinct advisory pass
with requirement, architecture, scope, implementation, and security
observations. It found the single-launch outcome, differential classification,
admitted-path ownership, validation, privacy, and stop boundaries consistent.

The review retained child-process executable identity, inherited environment,
user-home state, the five shared-file modifications, and possible unobserved
background network attempts as unknown. It granted no task, repair, scope,
exception, Git, publication, release, deployment, or external authority.
After advisory evidence write-back, the focused documentation suites passed
38 and 13 tests, and the diff and privacy checks passed again.
