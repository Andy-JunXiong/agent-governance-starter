# Real Codex initialize-boundary replay v1 - 2026-08-31

## Outcome

`REAL_CODEX_INITIALIZE_BOUNDARY_DIVERGED_CURRENT_SOURCE_FAILED`

Codex CLI 0.146.0 started exactly once against the configured installed
AgentGov launcher and exactly once against current repository source. The
installed binding completed its turn. The current-source binding failed before
a model turn began, with normalized standard-error markers for `initialize`,
`closed`, `-32603`, and the configured AgentGov server name.

No AgentGov tool was invoked in either startup. The replay stopped after the
two authorized observations and did not retry or repair either binding.

## Replay contract

Both real-client startups used the same bounded no-tool instruction and
equivalent process-local MCP settings: a required server, the canonical
eight-tool allow-list, automatic tool approval, a ten-second startup timeout,
and a sixty-second tool timeout. Both also used an ephemeral Codex run,
ignored persistent user configuration, disabled web search, prohibited command
approval, and selected the read-only sandbox. The only intentional binding
difference was the AgentGov launcher; current source also received the source
module binding needed to execute repository code.

Official Codex documentation states that local Codex supports STDIO MCP
servers and `enabled_tools` filtering:
<https://developers.openai.com/codex/mcp/>. It also documents configuration
override precedence:
<https://developers.openai.com/codex/config-basic/>.

A local wrapper captured each client stream in memory and emitted only the
normalized fields below. One wrapper command had a quoting error before the
current-source Codex process could be created. After that local pre-launch
error was corrected, the authorized current-source client was started exactly
once. That client startup was not retried.

## Normalized comparison

| Observation | Installed launcher | Current source |
| --- | --- | --- |
| Real Codex startups | exactly one | exactly one |
| Client exit | `0` | `1` |
| JSON event count | `4` | `0` |
| Event types | thread started, turn started, item completed, turn completed | none |
| Standard error present | yes | yes |
| `-32603` marker | absent | present |
| `initialize` marker | absent | present |
| `closed` marker | absent | present |
| startup-failed marker | absent | absent |
| timed-out marker | absent | absent |
| AgentGov tool-call events | `0` | `0` |
| Turn completed | yes | no |

The installed standard-error stream was non-empty, but none of the retained
failure markers matched. Its content was not retained, so this evidence does
not classify that stream further.

## First attributable difference

The first observable live-client divergence is before current-source thread or
turn events: the current-source MCP initialization closed with `-32603`, while
the installed binding proceeded to a completed turn. This reproduces the
initialize-closure signature at the real Codex boundary, but on current source
rather than the installed launcher implicated by the earlier discovery attempt.

The preceding local STDIO diagnostic established only that the installed
launcher reports Adapter `1.6.0`, current source reports `1.7.0`, and both pass
the same minimal local initialize and tool-list sequence. Taken together, the
observations locate the divergence at the real Codex client boundary for these
two bindings. They do not establish whether version skew, request shape,
environment, timing, source worktree state, or another client interaction
caused it.

## Preservation and evidence limits

The permanent project Codex configuration retained SHA-256
`4cca2d57edeaddfe52d3e6c4dd4d774192bbdbcab4e84e07df73e14a861c0348`.
The configured installed executable retained SHA-256
`7dada88a8ccff3dfa40dd52783719e5aced5b293202979ba3d5b75f027b498e7`.
No installed package, AgentGov runtime source, or permanent Codex configuration
was changed. No completion, drift, or other AgentGov state transition occurred.

This is one first-party observation per binding, not a reliability sample or
independent assurance. It does not prove root cause, repeatability, cross-host
or cross-version portability, stateful workflow semantics, adoption, prevented
incidents, or business benefit. It grants no authority for repair, retry,
package refresh, Git, publication, deployment, or release.
