# Disposable Codex MCP initialization v1 - 2026-08-24

## Outcome

`STOPPED_BEFORE_INITIALIZE_AT_FOREGROUND_STDIO_SESSION_BOUNDARY`

Native proposal review admitted exact task
`p0-disposable-codex-mcp-initialization-v1` through proposal
`prp-6e555bf047be43b7811e6a9769162f59`. The product owner separately
instructed the Agent to execute it.

## Deterministic preflight

The retained consumer repository was clean, empty, and remote-free. Its fresh
Python 3.11 environment still contained only the offline-installed
`agent-governance-starter 0.3.0rc1` distribution with no declared dependency.
The exact retained wheel and all four predecessor task records retained their
pre-task SHA-256 identities. The user Codex configuration digest and byte
length were captured without reading or retaining its content or digest.

The packaged binding still declared all eight form-capable AgentGov tools,
required startup, automatic tool approval, a 10-second startup timeout, and a
1800-second tool timeout. Local command discovery identified Codex CLI
`0.146.0`. A PowerShell help probe selected the execution-policy-blocked script
wrapper; correcting only the read-only preflight selection to the platform-
native `codex.cmd` entry succeeded. App Server and schema-generation help were
available. The
[official Codex App Server documentation](https://developers.openai.com/codex/app-server)
confirmed the initialize, initialized, thread/start, and MCP-status lifecycle.
No App Server, MCP server, thread, or model started during preflight.

The native help command also emitted a warning that it could not remove an
older ambient temporary argument directory. This task did not inspect, change,
or remove that unrelated state.

## Single launch and first deviation

One fresh task-owned disposable Codex home was created without reading or
copying the real user Codex home. Exactly one foreground Codex App Server
command started from the retained disposable consumer repository. Process-
local configuration supplied only the packaged AgentGov command, arguments,
working directory, required status, eight-tool allow-list, automatic approval,
and timeouts. The retained runtime was first on process-local PATH.

The command returned exit code zero before the controller obtained a writable
foreground STDIO session. Therefore the controller sent no JSON-RPC message.
The admitted first-deviation rule stopped the task without a second launch,
transport substitution, configuration repair, or retry.

```text
stage: app_server_foreground_transport_startup
code: app_server_exited_before_writable_stdio_session
expected: one foreground App Server remains available for the initialize request
observed: the only command exited zero before the controller obtained a writable session; no request was sent
```

Two launch warnings were normalized rather than copied into this record. The
temporary Codex home was rejected as a location for PATH helper aliases. A
remote-control WebSocket task also started and exited before client readiness.
The retained output does not establish whether a network connection completed,
so zero background network activity is not claimed.

| Observation | Result |
| --- | --- |
| Fresh disposable Codex homes | 1 |
| Codex App Server launches | 1 |
| Initialize requests | 0 |
| Initialized notifications | 0 |
| Ephemeral thread requests | 0 |
| MCP status requests | 0 |
| AgentGov MCP starts | 0 observed |
| AgentGov tool calls | 0 |
| Model turns or payloads | 0 |
| Launch retries | 0 |
| Remaining task processes | 0 |

## Preservation and limits

The disposable Codex home is retained. After the stopped launch it contained
60 files and 29 directories; their names and contents were not inspected or
retained. The consumer repository remains empty, clean, and remote-free. The
user Codex configuration digest and byte length, retained wheel, four
predecessor task records, Starter HEAD and branch all match their pre-launch
state. No task-owned Codex, AgentGov, or Python process remains.

This is a controller-to-foreground-process transport failure, not evidence of
an AgentGov Adapter initialization failure. It proves only that the admitted
single launch was consumed before the controller could send initialize. Live
Codex-to-MCP initialization, ephemeral thread creation, eight-tool discovery,
form behavior, model behavior, completion execution, cross-host behavior,
causal benefit, and return on investment remain unknown.

No consumer product or configuration file, consumer task, completion record,
Starter source or test, user configuration, Git state, publication, release,
or deployment was changed. This record contains no raw protocol or warning
output, source content, credential, identity, absolute path, generated name,
process identifier, remote endpoint, session identifier, prompt, response,
transcript, screenshot, or model-private reasoning.

## Starter validation and review

All 67 user-documentation and public-documentation freshness tests pass. The
complete supported Python 3.11 suite passes all 1083 tests with 4
platform-limited skips in 162.118 seconds. Task governance reports
`PASS=3 WARN=1 FAIL=0 ADVISORY=3`; repository governance reports
`PASS=26 WARN=2 FAIL=0 ADVISORY=4`. Scope passes all 12 admitted paths and
reports 44 exact excluded pre-existing paths; all 56 paths are classified with
zero unclassified. Task JSON, the bounded task-change privacy scan,
preservation checks, and `git diff --check` pass.

The fully specified task did not start an alignment journey, so no native
self-review completion is claimed. A distinct bounded current-Agent review
confirmed the one-launch and zero-request counts, first-deviation stop,
unchanged Kernel and Adapter, exact scope, privacy reduction, preserved user
configuration and consumer, retained temporary evidence, and unused model,
completion, cleanup, Git, publication, release, and deployment authority. It
also confirmed that the remote-control warning prevents a zero-network claim
and that the outcome must not be presented as an Adapter failure. This is not
independent assurance. The cause of the foreground STDIO session boundary and
successful Codex-to-MCP initialization remain unknown.
