# Codex initialize schema/version differential v1 - 2026-08-31

## Outcome

`LOCAL_SCHEMA_DIFFERENTIAL_BLOCKED_BEFORE_MCP_RESPONSE`

The configured installed launcher and current repository source were each
started exactly once with the same bounded form-capable local MCP sequence.
Both processes exited `2` before emitting any JSON response. Each emitted no
standard-output line and had non-empty standard error. The comparison therefore
did not reach initialize metadata, capabilities, tool descriptions, or tool
input schemas.

The processes were not retried. No real Codex client was started and no
AgentGov tool was invoked.

## Diagnostic contract

One in-memory wrapper supplied each binding the same three-message sequence:

1. form-capable initialize for protocol `2025-11-25`;
2. initialized notification;
3. tools list.

Both processes used the same disposable working context. The installed binding
received no source module override; current source received only the module
binding required to execute repository code. The wrapper retained only process
status, output counts, schema counts, field paths, and fingerprints. It
discarded request, response, and standard-error content when the processes
ended.

## Normalized observation

| Observation | Installed binding | Current-source binding |
| --- | --- | --- |
| Local process starts | exactly one | exactly one |
| Exit code | `2` | `2` |
| JSON response lines | `0` | `0` |
| Non-JSON standard-output lines | `0` | `0` |
| Standard error present | yes | yes |
| Initialize result | absent | absent |
| Tools-list result | absent | absent |
| Retry | none | none |

Every response-difference collection is empty because neither process emitted
a comparable response. That is not evidence that the two versions have equal
initialize metadata, capabilities, descriptions, or schemas.

The `1.6.0` installed and `1.7.0` current-source labels remain upstream facts
from the preceding successful repository-context STDIO diagnostic; this run
did not independently reconfirm either version.

## First boundary and interpretation

The first shared boundary is process startup before MCP response generation.
The wrapper intentionally used a disposable working context, whereas the
preceding successful local comparison ran from the repository context. That
environment difference is a plausible explanation for the shared stop, but it
is an inference only. Because standard-error content was deliberately not
retained, this evidence cannot classify the concrete exit reason.

The intended schema/version differential is therefore incomplete. Repeating
the comparison from a repository context would be a retry and requires a new
human decision and separately admitted task. This task neither performs nor
authorizes that retry.

## Preservation and evidence limits

The permanent project Codex configuration retained SHA-256
`4cca2d57edeaddfe52d3e6c4dd4d774192bbdbcab4e84e07df73e14a861c0348`.
The configured installed executable retained SHA-256
`7dada88a8ccff3dfa40dd52783719e5aced5b293202979ba3d5b75f027b498e7`.
No installed package, AgentGov runtime source, or permanent Codex configuration
was changed. No completion, drift, or other AgentGov stateful workflow ran.

This blocked first-party observation does not identify a schema difference,
the real Codex closure's root cause, portability, repeated reliability,
stateful workflow compatibility, adoption, incident reduction, or business
benefit. It grants no authority for retry, repair, Git, publication,
deployment, or release.
