# Codex installed launcher initialize diagnostic - 2026-08-31

## Goal and admitted boundary

The human selected the recommended direction in resolved alignment journey
`mcpj-8991aa45f87842a99038e6f78e50c9eb`: diagnose the configured installed
launcher before attempting stateful completion or drift replay. Native proposal
`prp-439c5c4d39c94938a36fa99f98fd9e75` admitted task
`p0-codex-installed-launcher-initialize-diagnostic-v1`, and the human separately
replaced the active task pointer.

The slice permits one read-only installed-versus-current-source comparison at
MCP initialize and tool-list boundaries. It excludes package repair,
installation change, permanent Codex configuration, AgentGov runtime source,
stateful tool calls, Git, publication, deployment, and release.

## Diagnostic observation

The same in-memory newline-delimited JSON-RPC sequence was sent to both
launchers: form-capable `initialize` for protocol `2025-11-25`, initialized
notification, and `tools/list`.

Both processes exited zero, emitted two parseable JSON lines and no standard
error, returned matching protocol and server names, and listed the same eight
AgentGov tools. No AgentGov tool call occurred. The first observed difference
was initialize `serverInfo.version`: installed reported `1.6.0`; current source
reported `1.7.0`.

The installed launcher therefore passed this minimal local STDIO boundary. The
earlier live Codex `-32603` initialize closure did not reproduce, so the version
skew is evidence of distribution difference but is not claimed as that closure's
cause. Exact client input, environment, timing, and other consumer boundaries
remain unknown.

## Preservation and validation boundary

The project Codex configuration retained SHA-256
`4cca2d57edeaddfe52d3e6c4dd4d774192bbdbcab4e84e07df73e14a861c0348`.
Excluded pre-existing worktree changes remain untouched and retain their prior
ownership. All 59 focused documentation tests and all 1,115 repository tests
pass, with five Windows privilege-limited symbolic-link skips. Task governance
reports `PASS=3 WARN=1 FAIL=0 ADVISORY=3`, repository governance reports
`PASS=26 WARN=2 FAIL=0 ADVISORY=4`, and whitespace and privacy checks pass. The
raw worktree scope view reports `PASS=5 FAIL=13 ADVISORY=0` because it keeps
pre-existing excluded paths visible as failures; it grants no exception or
ownership transfer.

Native current-Agent advisory self-review
`srv-e959070dab8852ed65e972d6ccc4963f` examined requirement conformance,
implementation attribution, scope, privacy, and architecture. It requested no
correction. It retained the exact live-client input and environment, causal
attribution, portability, repeat reliability, and independent privacy assurance
as unknown.

No commit, push, publication, deployment, release, package repair, or stateful
governance invocation is claimed or authorized.
