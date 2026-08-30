# Codex repository-context schema differential v1 - 2026-08-31

## Outcome

`LOCAL_MCP_RESPONSES_MATCH_EXCEPT_INSTRUCTIONS_AND_SERVER_VERSION`

The configured installed binding and current repository source were each
started exactly once from the repository working context. Each received the
same form-capable initialize, initialized-notification, and tools-list
sequence. Both exited `0`, emitted two JSON response lines, emitted no
non-JSON standard-output line, and had empty standard error. No retry occurred.

At this retained local boundary, capabilities, the eight-tool set, every tool
description, every tool input schema, and the complete tools-list response were
equal. The first comparable non-version difference was the initialize
`instructions` scalar. The other difference was `serverInfo.version`:
installed Adapter `1.6.0` and current source `1.7.0`.

No real Codex client was started and no AgentGov tool or stateful workflow was
invoked.

## Diagnostic contract

One in-memory wrapper supplied each binding the same three-message sequence:

1. form-capable initialize for protocol `2025-11-25`;
2. initialized notification;
3. tools list.

Both processes used the repository working context. The installed binding
received no source-tree module override; current source received only the
module binding required to execute repository code. The wrapper retained only
process status, safe marker booleans, field names, counts, lengths, and
SHA-256 fingerprints. It did not retain protocol payloads, instruction
content, or diagnostic streams.

## Normalized observation

| Observation | Installed binding | Current-source binding |
| --- | --- | --- |
| Local process starts | exactly one | exactly one |
| Exit code | `0` | `0` |
| JSON response lines | `2` | `2` |
| Non-JSON standard-output lines | `0` | `0` |
| Standard error | empty | empty |
| Configured safe stderr markers | all false | all false |
| Protocol version | `2025-11-25` | `2025-11-25` |
| Server version | `1.6.0` | `1.7.0` |
| Tool count | `8` | `8` |

Both initialize results had the same top-level fields: `capabilities`,
`instructions`, `protocolVersion`, and `serverInfo`. Their normalized
capabilities shared SHA-256
`59bb371ffee5d4d65405a3ca79103f886881dba33946165a2bc7200951d5ca19`.

The exact eight tools were `agentgov_alignment_start`,
`agentgov_alignment_update`, `agentgov_alignment_resolve`,
`agentgov_self_review_start`, `agentgov_self_review_complete`,
`agentgov_task_proposal_review`, `agentgov_task_completion_record`, and
`agentgov_drift_review_record`. The entire normalized tools-list response
shared SHA-256
`41a738c82d05b3bdbf4f036c1e153f81d09f4c931944ac223153d8dc0894ca90`.
Installed-only and current-only tool counts were both zero. Tool field,
description, and input-schema difference counts were all zero.

The initialize `instructions` values differed without their content being
retained. The installed JSON-encoded scalar length was `2435`, with SHA-256
`501dbb994307b54c2fb050a90765f85e8a3fa12a3d645d0f2d68c3d197e1ad88`;
the current-source length was `2661`, with SHA-256
`de376b10ca9261c1ddf35565ecfcdb6213192b8ca5fb31ac5b5878e261960d27`.
The only initialize difference paths were `/initialize/instructions` and
`/initialize/serverInfo/version`.

## Interpretation

This corrected repository-context run removes the preceding comparison's
shared exit-2 stop. A single successful run does not prove that working context
caused that earlier stop.

The result rules out a tool-set, tool-description, tool-input-schema, or
capabilities difference at this normalized local fixture boundary. It does not
establish that the instructions difference, version difference, or any other
factor caused the real Codex client's current-source `-32603` initialize
closure. The real-client root cause remains unknown.

## Preservation and evidence limits

The permanent project Codex configuration retained SHA-256
`4cca2d57edeaddfe52d3e6c4dd4d774192bbdbcab4e84e07df73e14a861c0348`.
The configured installed executable retained SHA-256
`7dada88a8ccff3dfa40dd52783719e5aced5b293202979ba3d5b75f027b498e7`.
No installed package, AgentGov runtime source, or permanent Codex configuration
was changed. No repair, completion, drift, or other stateful workflow ran.

This one-run local fixture does not establish real Codex compatibility,
causality, portability, repeat reliability, stateful semantics, independent
assurance, adoption, incident reduction, or business benefit. It grants no
authority for another replay, repair, Git, publication, deployment, or release.
