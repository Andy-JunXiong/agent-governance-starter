# Codex initialize schema/version differential - 2026-08-31

## Goal and admitted boundary

Resolved alignment journey `mcpj-a8e7b33cccb044c3ac013b523a2e032f`
selected a read-only initialize and tool-schema differential before any repair
or another real Codex replay. Native proposal
`prp-fe9f9caf3db54f6a823175fbd4ded2df` admitted task
`p0-codex-initialize-schema-version-differential-v1`, and the human separately
replaced the active task pointer.

The direct upstream real-client replay is task
`p0-codex-live-client-initialize-boundary-replay-v1`; the preceding successful
local STDIO diagnostic established the `1.6.0` and `1.7.0` labels used here.

The task authorized one installed and one current-source local MCP process,
the same form-capable request sequence, in-memory normalization, and bounded
evidence. It excluded retry, real Codex startup, package or runtime repair,
permanent configuration changes, AgentGov tool invocation, stateful workflow,
Git, publication, deployment, and release.

## Execution and stop

The wrapper started each binding exactly once in the same disposable working
context. Both exited `2`, emitted no JSON or other standard-output line, and
had non-empty standard error. Neither reached an initialize or tools-list
result. The wrapper discarded request, response, and standard-error content and
retained only normalized counts and presence markers.

The identical pre-response stop means no version, capability, description, or
input-schema comparison is available. Empty difference collections reflect
absent responses, not schema equality. No process was retried.

The earlier successful local comparison ran in repository context, while this
task used a disposable working context. That difference may explain the stop,
but the exact exit reason is unknown because the raw diagnostic stream was not
retained. A corrected repository-context comparison would be a new retry and
is outside this task.

## Preservation and validation boundary

The permanent Codex configuration retained SHA-256
`4cca2d57edeaddfe52d3e6c4dd4d774192bbdbcab4e84e07df73e14a861c0348`,
and the installed executable retained SHA-256
`7dada88a8ccff3dfa40dd52783719e5aced5b293202979ba3d5b75f027b498e7`.
No package, AgentGov runtime source, permanent configuration, real Codex
client, or AgentGov workflow state changed. Excluded worktree paths retain
their prior ownership.

Validation and the distinct current-Agent advisory review are recorded below.
No downstream action is authorized by this log.

## Validation and advisory review

All 61 focused documentation tests and all 1,117 repository tests pass, with
five Windows privilege-limited symbolic-link skips. Task governance reports
`PASS=3 WARN=1 FAIL=0 ADVISORY=3`; repository governance reports
`PASS=26 WARN=2 FAIL=0 ADVISORY=4`; whitespace, privacy, and hash checks pass.
The read-only raw scope view reports `PASS=5 FAIL=19 ADVISORY=0` because it
keeps nineteen pre-existing excluded paths visible as failures. It grants no
exception or ownership transfer.

Native current-Agent advisory self-review
`srv-fee8df2987d96b8fd8f51223205cd8c1` completed as a distinct pass over
requirement conformance, implementation attribution, scope, privacy,
architecture, and bounded value. It confirmed that the no-retry execution and
absent-response classification are accurate, while the required schema
comparison remains incomplete. Concrete exit cause, compatibility, repeat
reliability, independent privacy assurance, portability, stateful semantics,
and external outcomes remain unknown.

No commit, push, publication, deployment, release, repair, retry, or stateful
governance invocation is claimed or authorized.
