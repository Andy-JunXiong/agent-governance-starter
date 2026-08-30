# Real Codex initialize-boundary replay - 2026-08-31

## Goal and admitted boundary

Resolved alignment journey `mcpj-2560c6f047ee4c50a872521d35179ba3`
returned to the exact live-client initialization boundary. Native proposal
`prp-828e3a42dcbe4535a4ac781ed895571e` admitted task
`p0-codex-live-client-initialize-boundary-replay-v1`, and the human separately
replaced the active task pointer.

The slice authorized exactly one real Codex startup for the configured
installed launcher and exactly one equivalent startup for current source. It
excluded retries, package repair or refresh, permanent configuration changes,
AgentGov runtime changes, AgentGov tool invocation, stateful workflow
execution, Git, publication, deployment, and release.

## Observation

Codex CLI 0.146.0 received the same bounded no-tool task and equivalent
process-local server requirements, eight-tool allow-list, approval behavior,
timeouts, network setting, and read-only sandbox for both bindings.

The installed startup exited zero and emitted one each of thread-started,
turn-started, item-completed, and turn-completed events. It had non-empty
standard error, but none of the retained `-32603`, initialize, closure,
startup-failure, or timeout markers matched.

The current-source startup exited one before thread or turn events and emitted
no JSON event. Its normalized standard error matched `initialize`, `closed`,
`-32603`, and the configured AgentGov server name. Neither startup emitted a
tool-call event or invoked AgentGov.

A wrapper quoting error occurred before the second client process could be
created. It produced no real Codex startup. After correcting that local
pre-launch wrapper, current source received its one authorized startup. No
client startup was retried.

## Interpretation and preservation

The first live-client divergence is the current-source MCP initialize closure
before a model turn, versus the installed binding's completed turn. The prior
local diagnostic, task `p0-codex-installed-launcher-initialize-diagnostic-v1`,
showed Adapter versions `1.6.0` and `1.7.0` and successful minimal STDIO
initialization for both. The combined evidence narrows the
boundary but does not attribute the failure to version skew, request shape,
environment, timing, source worktree state, or another cause.

The permanent Codex configuration retained SHA-256
`4cca2d57edeaddfe52d3e6c4dd4d774192bbdbcab4e84e07df73e14a861c0348`,
and the installed executable retained SHA-256
`7dada88a8ccff3dfa40dd52783719e5aced5b293202979ba3d5b75f027b498e7`.
No package, runtime source, permanent configuration, or AgentGov state was
changed. Excluded dirty-worktree paths retain their prior ownership.

Validation and the distinct current-Agent advisory review are recorded below.
No downstream action is authorized by this log.

## Validation and advisory review

All 60 focused documentation tests and all 1,116 repository tests pass, with
five Windows privilege-limited symbolic-link skips. Task governance reports
`PASS=3 WARN=1 FAIL=0 ADVISORY=3`; repository governance reports
`PASS=26 WARN=2 FAIL=0 ADVISORY=4`; whitespace and privacy checks pass. The
read-only raw scope view reports `PASS=5 FAIL=16 ADVISORY=0` because it keeps
the sixteen pre-existing excluded paths visible as failures. It grants no
exception or ownership transfer.

Native current-Agent advisory self-review
`srv-4f8b243f2ff5bd9dd3eb60d4a3e33320` completed as a distinct pass over
requirement conformance, implementation attribution, scope, privacy,
architecture, and bounded value. It requested no correction. Root cause,
repeat reliability, independent privacy assurance, portability, stateful
semantics, and external outcomes remain unknown. The review suggested only a
future product question: whether to separately authorize an initialize-payload
comparison across Adapter `1.6.0` and `1.7.0` without retrying this replay.

No commit, push, publication, deployment, release, package repair, or stateful
governance invocation is claimed or authorized.
