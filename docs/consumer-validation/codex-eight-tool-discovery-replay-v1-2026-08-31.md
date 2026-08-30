# Real Codex eight-tool discovery replay v1 - 2026-08-31

## Outcome

`EIGHT_TOOL_DISCOVERY_CONFIRMED_NO_STATEFUL_INVOCATION`

Codex CLI 0.146.0 discovered exactly the canonical eight AgentGov MCP tools
from a one-off current-source STDIO binding. The successful confirmation ran
outside the repository working directory, so project rule text could not supply
the names. The replay used deferred tool discovery through tool search and did
not call an AgentGov tool.

## Consumer and configuration facts

The official OpenAI Codex MCP documentation at
<https://developers.openai.com/codex/mcp/> states that local Codex clients
support STDIO servers and `enabled_tools` filtering. Codex configuration also
supports a one-off configuration override with higher precedence than project
configuration.

The replay supplied only process-local server, timeout, required-server, and
eight-tool allow-list values. A read-only MCP inventory confirmed that the
temporary AgentGov STDIO binding was enabled with a ten-second startup timeout
and sixty-second tool timeout. The permanent project configuration was not
edited. Its SHA-256 digest was identical before and after the replay:

`4cca2d57edeaddfe52d3e6c4dd4d774192bbdbcab4e84e07df73e14a861c0348`

No command path, working-directory path, local identity, authentication
material, conversation content, or process/session identifier is retained in
this evidence.

## Deferred discovery observation

A negative-control turn that prohibited every tool returned no AgentGov names.
That result is consistent with deferred tool discovery and is not treated as an
absence of MCP tools.

The bounded positive replay then allowed only Codex tool search. It prohibited
AgentGov calls plus shell and filesystem tools. The normalized result contained
these eight fully qualified MCP tool suffixes:

1. `agentgov_alignment_resolve`
2. `agentgov_alignment_start`
3. `agentgov_alignment_update`
4. `agentgov_drift_review_record`
5. `agentgov_self_review_complete`
6. `agentgov_self_review_start`
7. `agentgov_task_completion_record`
8. `agentgov_task_proposal_review`

The names are an exact set match for the canonical eight-tool source contract.
The machine event stream contained no AgentGov tool-call event. In particular,
`agentgov_task_completion_record` and `agentgov_drift_review_record` were
discovered but not invoked.

## Installed-launcher observation

An earlier attempt using the launcher referenced by the permanent project
configuration reached MCP initialization but closed while generating the
initialize response. The successful evidence therefore uses a one-off binding
to the current repository source. This difference is recorded as a possible
installed-distribution compatibility gap, not silently presented as a passing
installed-launcher result. Diagnosing or repairing it is outside this task.

## Evidence and authority limits

This is one first-party discovery-only observation plus one rule-isolated
repeat, not independent assurance. Discovery does not prove invocation,
stateful workflow semantics, repeat reliability, cross-host compatibility,
adoption, incident reduction, business benefit, or return on investment.

The replay changes no AgentGov runtime, permanent Codex configuration, external
consumer, Git history, publication, deployment, or release state. It grants no
authority for completion, drift recording, code change, scope expansion, Git,
publication, deployment, or release.
