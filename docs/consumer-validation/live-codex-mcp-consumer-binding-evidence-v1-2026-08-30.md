# Live Codex MCP consumer binding evidence v1 - 2026-08-30

## Outcome

`PARTIAL_COMPATIBILITY_CONFIRMED_WITH_CONFIGURED_SIX_TOOL_SURFACE`

The measured consumer is the current Codex host connected to the project-scoped
AgentGov foreground STDIO MCP server. The observation confirms that the host
loads and calls the six tools selected by the existing project configuration.
It does not prove the source contract's full eight-tool form-capable surface.

## Reproducible host and configuration facts

The official OpenAI Codex MCP documentation at
<https://developers.openai.com/codex/mcp/> states that local Codex clients can
connect to STDIO MCP servers, read server instructions, use project-scoped
`.codex/config.toml`, and filter server tools through `enabled_tools` and
`disabled_tools`.

One read-only `codex mcp list --json` invocation returned exit code zero and
reported `agentgov_governance` enabled with `startup_timeout_sec=10` and
`tool_timeout_sec=60`. A bounded parser inspected only non-sensitive structural
fields in the project configuration. It reported `enabled=true`,
`required=true`, automatic tool approval, the same timeouts, no deny-list, and
this exact `enabled_tools` allow-list:

1. `agentgov_alignment_start`
2. `agentgov_alignment_update`
3. `agentgov_alignment_resolve`
4. `agentgov_self_review_start`
5. `agentgov_self_review_complete`
6. `agentgov_task_proposal_review`

The current callable surface exposes the same six names. The configured server
and current host inventory therefore agree exactly at the tool-name boundary.
No command, argument, environment value, host path, user-level configuration,
or unrelated MCP server identity is retained in this record.

## Live call-path observation

In this foreground Codex session, native proposal review presented a bound form
and created only the human-admitted evidence task. Alignment start, update, and
resolve then completed the human-selected consumer-validation direction without
granting task, code, Git, publication, release, or deployment authority.

After 57 focused documentation tests and the 1,113-test repository suite
passed, `agentgov_self_review_start` and `agentgov_self_review_complete`
completed one distinct advisory current-Agent pass. The review confirmed the
requirement, host-binding attribution, implementation evidence, privacy
boundary, and admitted scope while retaining fresh eight-tool behavior,
repeated reliability, and independent privacy review as unknowns.

Across this measured journey, all six configured tool paths were exercised
successfully: proposal review, alignment start/update/resolve, and self-review
start/complete. These calls demonstrate the current configured surface only;
they do not establish universal Codex behavior or the two omitted tool paths.

## Source-contract comparison

Current AgentGov source defines six base tools and eight tools for a client that
negotiates form elicitation. The project allow-list predates the completion and
drift-review additions, so the real host does not currently expose:

- `agentgov_task_completion_record`
- `agentgov_drift_review_record`

These are host-configured omissions, not an Adapter failure. This task neither
changes nor proposes an exception to the project configuration. A fresh Codex
session with an eight-tool allow-list, successful completion and drift calls,
and repeated reliability all remain unproven.

## Evidence and authority limits

This is one first-party current-session observation and a separate self-review,
not independent assurance.
Cross-host compatibility, adoption, causal incident reduction, business value,
and return on investment remain unknown. No AgentGov runtime behavior, Codex
configuration, external consumer repository, Git state, publication, release,
or deployment is changed by this evidence slice.

The retained evidence excludes prompts, responses, conversations, source
payloads, secrets, authentication material, local identities, filesystem
locations, process identifiers, and model-private reasoning.
