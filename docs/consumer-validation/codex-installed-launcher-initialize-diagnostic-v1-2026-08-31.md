# Codex installed launcher initialize diagnostic v1 - 2026-08-31

## Outcome

`LOCAL_STDIO_INITIALIZE_PASSED_WITH_SERVER_VERSION_SKEW`

The configured installed AgentGov executable and the current repository source
both completed the same bounded local MCP sequence. Each returned a valid
initialize result, clean JSON-RPC output, and the same eight form-capable tools.
The first observed difference was initialize metadata: the installed launcher
reported Adapter server version `1.6.0`, while current source reported `1.7.0`.

## Diagnostic contract

The comparison sent each launcher the same newline-delimited messages:

1. `initialize` for protocol `2025-11-25`, with form elicitation declared;
2. `notifications/initialized`;
3. `tools/list`.

Both processes ran from the current repository context. The installed process
received no source-tree `PYTHONPATH`; the source process received only the
repository `src` binding needed to run current code. The harness captured output
in memory and retained only normalized result fields. It wrote no diagnostic
artifact, configuration, package, or process state.

## Normalized observation

| Observation | Installed launcher | Current source |
| --- | --- | --- |
| Process result | exit `0` | exit `0` |
| JSON-RPC output | two JSON lines, no non-JSON output | two JSON lines, no non-JSON output |
| Standard error | empty | empty |
| Initialize result | present | present |
| Protocol | `2025-11-25` | `2025-11-25` |
| Server | `agentgov-governance` | `agentgov-governance` |
| `serverInfo.version` | `1.6.0` | `1.7.0` |
| Tool-list result | present | present |
| Discovered tools | eight | eight |

Both tool lists contained the exact same names:

1. `agentgov_alignment_resolve`
2. `agentgov_alignment_start`
3. `agentgov_alignment_update`
4. `agentgov_drift_review_record`
5. `agentgov_self_review_complete`
6. `agentgov_self_review_start`
7. `agentgov_task_completion_record`
8. `agentgov_task_proposal_review`

No AgentGov tool was invoked.

## First deviation and interpretation

The first reproducible difference in this comparison is the initialize
`serverInfo.version` value. This establishes that the configured installed
launcher is not serving the same Adapter version as current source. It does not
establish that version skew caused the earlier live Codex `-32603` initialize
closure.

The earlier closure did not reproduce under the bounded local request sequence:
the installed launcher initialized and listed tools successfully. The remaining
unknown therefore sits beyond this minimal STDIO sequence and may involve a
different client payload, environment, timing, or another consumer boundary.
Those possibilities are not classified as causes here.

## Preservation and authority limits

The project `.codex/config.toml` SHA-256 digest remained
`4cca2d57edeaddfe52d3e6c4dd4d774192bbdbcab4e84e07df73e14a861c0348`.
This task did not change the installed package, current AgentGov source,
permanent Codex configuration, external consumer, or Git state. It did not call
completion or drift tools.

This first-party local diagnostic is not independent assurance and does not
prove live Codex compatibility, stateful workflow behavior, root cause,
portability, repeated reliability, adoption, incident reduction, or business
benefit. Repair and a closer live-client reproduction require separate human
decisions and separately admitted tasks.
