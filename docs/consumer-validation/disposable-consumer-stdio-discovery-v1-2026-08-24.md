# Disposable consumer STDIO discovery v1 - 2026-08-24

## Outcome

`PASSED_DISPOSABLE_CONSUMER_STDIO_DISCOVERY`

Native proposal review admitted exact task
`p0-disposable-consumer-stdio-discovery-v1` through proposal
`prp-542b3ee7e39a4aa6a2be756bf2fa0f75`. The product owner separately
instructed the Agent to execute it.

## Deterministic preparation

The retained wheel remained
`agent_governance_starter-0.3.0rc1-py3-none-any.whl` with SHA-256
`2C05FD3816D2006402F447788721B7D63DE1DF08CC31990B4DD38A86F6744C94`.
Its embedded distribution metadata still identified
`agent-governance-starter 0.3.0rc1`. The staging task, non-executed build v1
task, and completed build v2 task retained their pre-task SHA-256 hashes. No
Python process from the retained build root was running.

One fresh operating-system temporary root received one empty disposable Git
repository and one fresh Python 3.11 environment. The repository root matched
the intended disposable directory, had no remote, and contained no worktree
file. The environment installed the exact retained wheel with no index and no
dependencies. No dependency or package download occurred.

## Packaged binding and STDIO result

The installed packaged Codex binding was parsed in memory. It names the
installed `agentgov` command, enables all eight expected tools including
`agentgov_task_completion_record`, marks the server required, keeps automatic
tool approval, and declares the 1800-second timeout. No consumer configuration
or product file was written.

| Observation | Result |
| --- | --- |
| Runtime Python | `3.11.9` |
| Installed distribution | `agent-governance-starter 0.3.0rc1` |
| Declared runtime dependencies | none |
| Foreground Adapter processes | 2, sequential |
| Process working directory | disposable remote-free Git repository |
| MCP protocol | `2025-11-25` |
| Adapter version | `1.7.0` |
| Tools without form elicitation | 6 |
| Tools with form elicitation | 8 |
| Completion input | only `task_path` |
| Completion destructive hint | false |
| JSON-RPC output | 2 valid response lines per process |
| Process exits | both normal with empty standard error |
| Remaining task processes | 0 |

Each installed foreground process received only MCP `initialize` and
`tools/list`. Standard input then closed and the process exited normally. No
AgentGov tool, Codex process, external model, model session, or model turn was
started.

## Preservation and limits

The task root retains one disposable repository and one Python environment.
The repository still has no remote, no worktree file, and a clean status. No
task process remains. Predecessor task records, the retained wheel, Starter
source and tests, HEAD, remotes, release identity, and prior working-copy
changes remain preserved.

Consumer product content, a consumer governance task, a completion-tool call,
completion evidence or record, completion-card handoff, cleanup, Git transport,
publication, release, and deployment remain at zero. This result proves the
installed console entry point can complete process-level STDIO initialization
and tool discovery from a disposable consumer repository. It does not prove
Codex-to-MCP initialization during a live Agent thread, model behavior, actual
completion recording, the complete automatic journey, cross-host behavior,
causal benefit, or return on investment.

This record contains no raw command output, source content, credential, user
identity, absolute host or temporary path, prompt, response, transcript,
screenshot, or model-private reasoning.

## Starter validation and review

All 67 user-documentation and public-documentation freshness tests pass. The
complete supported Python 3.11 suite passes all 1083 tests with 4
platform-limited skips in 170.217 seconds. Task governance reports
`PASS=3 WARN=1 FAIL=0 ADVISORY=3`; repository governance reports
`PASS=26 WARN=2 FAIL=0 ADVISORY=4`. Scope passes all 10 admitted paths and
reports 44 exact excluded pre-existing paths; all 54 paths are classified with
zero unclassified. The bounded task-change privacy scan, retained-state and
hash checks, task JSON, and `git diff --check` pass.

The fully specified task did not start a new alignment journey, so no native
self-review completion is claimed. A distinct bounded current-Agent review
found the requirement exact, Kernel and Adapter source unchanged, the retained
wheel and predecessor hashes preserved, and the packaged binding and two real
STDIO process exchanges consistent with the admitted task. It found no
correction-required requirement, architecture, scope, implementation,
security, data, or authority drift. This is not independent assurance and does
not establish live Codex initialization, model behavior, completion execution,
cross-host behavior, causal benefit, or return on investment.
