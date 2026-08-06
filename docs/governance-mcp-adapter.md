# Native governance MCP Adapter

Status: implemented in development source on 2026-08-06. This is a foreground
tool integration and an offline host-compatibility proof. It is not included in
stable 0.2.1 or immutable `v0.3.0rc1`.

## What it does in plain language

The Coding Agent can now use AgentGov as a set of native tools. The user keeps
talking normally. When meaning needs alignment, the Agent submits only a small
normalized center, drift observation, and question. AgentGov returns the next
question or final choices. After the user selects a direction, the same Agent
can request a clearly labeled medium-risk second look and return normalized
observations.

The user does not write JSON-RPC, contract IDs, digests, timestamps, or review
records. AgentGov generates and validates those fields. The user also does not
configure a second model or repeat the direction decision for self-review.

```text
ordinary host conversation
  -> current Coding Agent calls normalized MCP alignment tools
  -> AgentGov returns one question at a time
  -> human selects one offered direction in the host conversation
  -> current Coding Agent calls medium-risk self-review tools
  -> AgentGov accepts only the exact advisory result
```

## Why MCP is the native boundary

Current Codex command hooks can add context, enforce lifecycle checks, and ask
the current Agent to continue, but command hooks do not themselves perform LLM
inference. Released `prompt` and `agent` hook handlers are parsed but skipped.
The official [Codex hooks reference](https://developers.openai.com/codex/config-advanced#hooks)
documents that boundary.

Codex supports project-scoped foreground STDIO MCP servers and model-controlled
tools through `.codex/config.toml`. Its CLI, IDE extension, and desktop app
share that configuration. MCP also avoids putting a Codex vendor branch in
AgentGov Core and provides the portable tool boundary needed by Claude Code or
other MCP-capable IDE hosts.

The Adapter implements current MCP discovery and tool calls while retaining the
legacy initialize handshake needed by existing clients. Every journey receives
an explicit opaque handle, following the current MCP guidance that application
state should be represented by a visible handle rather than an implicit
transport session. State remains in the foreground process and is lost on
restart.

## Tool workflow

The server advertises exactly five tools in a fixed order:

1. `agentgov_alignment_start` starts from normalized meaning;
2. `agentgov_alignment_update` applies one normalized answer to the exact
   pending clarification prompt;
3. `agentgov_alignment_resolve` records the human-selected offered direction;
4. `agentgov_self_review_start` prepares one exact medium-risk active-host
   materialization request;
5. `agentgov_self_review_complete` validates normalized observations and
   returns the accepted advisory result.

The model must carry the journey handle and exact prompt/request digest returned
by AgentGov. Unknown, stale, duplicate, out-of-order, cross-journey, or
post-restart calls fail without advancing state. Input schemas reject unknown
fields at every governance-bearing object boundary.

## Privacy, cost, and authority

The tools reject raw prompts, raw answers, transcripts, assistant messages,
full source content, credentials, model prompts, absolute paths, and undeclared
authority. Repository paths may appear only as bounded evidence references;
source content is not sent.

The host's existing current-Agent entitlement supplies semantic reasoning.
AgentGov reports zero model and network calls, stores no credential, launches no
second Agent, writes no repository/runtime state from tool calls, and retains
no journey after process restart. Results remain `ADVISORY`; they cannot admit
a task, start development, change requirements or architecture, expand scope,
approve exceptions, or authorize code, Git, release, deployment, or external
writes.

## Codex project integration

Preview the exact create-missing-only project configuration:

```powershell
agentgov integrate codex-mcp . --dry-run
```

The preview creates nothing. Interactive apply requires exact `INTEGRATE` once
as an installation decision. It can create only `.codex/config.toml` when that
file is missing, preserves the exact managed file, and refuses to overwrite or
merge any existing custom configuration. Codex trusted-project/config review
remains separate and cannot be granted by AgentGov.

The generated config launches:

```text
agentgov adapter governance-mcp --host-profile codex
```

Daily alignment and self-review require no additional installation command or
manual protocol input after the host has loaded the reviewed MCP server.

## Honest implementation limit

Unit and CLI tests prove the STDIO protocol, tool state machine, Codex project
configuration, and shared Codex/Claude Code Provider path offline. They do not
prove that a production model will always choose the right tool, normalize
meaning correctly, or ask the human before claiming a selection. A live
uncoached Codex session using the reviewed config is still required. Native
Claude Code and other IDE configuration packages, authenticated custom decision
recording, and independent high-risk Reviewer execution remain later slices.

## Feature connections

- Upstream: governed clarification, resolved human alignment, Provider/risk
  routing, and live active-Agent self-review transport.
- Current: model-controlled native tools over one foreground MCP Adapter.
- Downstream: one uncoached Codex host rehearsal, followed by another MCP host
  installation proof and then optional independent high-risk review.
