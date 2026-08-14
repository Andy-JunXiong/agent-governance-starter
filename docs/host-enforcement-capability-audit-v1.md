# Host Enforcement Capability Audit v1

Status: evidence-bounded technical audit completed on 2026-08-14. This document
does not implement a Harness Adapter, change Kernel semantics, install host
configuration, or prove that any particular consumer has enabled the described
host controls.

## Decision summary

AgentGov should define Harness v1 around a **host execution surface**, not around
the model provider. The current evidence changes one earlier assumption:

- current Codex documentation now exposes synchronous `PreToolUse` interception
  for Bash, `apply_patch`, MCP, and most local function tools. It can deny a
  supported tool call before execution;
- Claude Code exposes a broader and more mature pre-action hook surface, including
  deny, ask, defer, input rewriting, permission decisions, and MCP elicitation;
- DeepSeek publishes model APIs and integrations with existing hosts such as
  Codex and Claude Code. The reviewed official sources do not establish one
  canonical DeepSeek coding harness with its own portable lifecycle-hook
  contract. A DeepSeek model therefore inherits the capability of the selected
  host; `DeepSeek` alone is not a valid Harness capability key.

The honest v1 conclusion is therefore:

```text
model provider != execution host

Codex host + any supported model       -> Codex capability declaration
Claude Code host + any supported model -> Claude Code capability declaration
DeepSeek API without a named host      -> no host enforcement claim
```

Codex remains the recommended first conformance implementation because the
repository already has its lifecycle and MCP Adapters. The follow-on must add a
separately admitted Codex `PreToolUse` slice and conformance evidence rather than
continue treating the 2026-08-06 `PostToolUse`-only baseline as current.

## Claim discipline

This audit applies the existing Kernel vocabulary without extending it:

- `OBSERVE`: receive or derive evidence about an event;
- `ADVISE`: surface non-authoritative guidance;
- `MEDIATE`: require or route an intermediate decision before another governed
  transition can proceed;
- `BLOCK`: prevent one exact transition through an identified mechanism.

An effect applies to a named transition, not to an entire host. A post-action
hook may only `OBSERVE` the completed side effect while separately `MEDIATE` or
`BLOCK` a later transition such as returning the original result, starting the
next model call, or accepting completion.

`UNKNOWN` below means the reviewed official evidence does not establish the
claim. It is not a negative capability claim.

## Evidence method and limits

Primary evidence is current official vendor documentation accessed on
2026-08-14. Repository contracts and tests provide supporting evidence for the
current AgentGov integration. No host configuration was installed or changed,
and no live destructive or external-write probe was performed.

Documentation describes a product capability, not its activation in a specific
consumer. A production `BLOCK` claim still requires positive and negative
conformance tests bound to the exact host version, enabled configuration, hook
trust state, tool path, and failure behavior.

## Transition-level capability matrix

| Host surface | Exact transition | Timing | Mechanism and trusted decision path | Honest ceiling | Coverage, bypass, and failure behavior | Confidence |
| --- | --- | --- | --- | --- | --- | --- |
| Codex CLI/IDE/desktop local tool path | supported tool call -> execution | pre-action | synchronous command `PreToolUse`; deny JSON or exit code `2` rejects the tool promise before execution | `BLOCK` for the matched supported call | Covers Bash/unified exec, `apply_patch`, MCP, and most local function tools. Hosted tools are excluded, specialized paths may opt out, and later `write_stdin` traffic does not repeat the hook. Non-managed hooks require trust and may be disabled; background hooks cannot block. Invalid unsupported output is reported and the tool continues. | high for documented capability; unproven for this repository's Adapter |
| Codex local tool path | supported tool input -> rewritten execution | pre-action | `permissionDecision: allow` with `updatedInput` replaces supported arguments | `MEDIATE` | Rewrite support is limited to documented tool paths and shapes. It is not a human governance decision and does not grant task admission. | high |
| Codex approval flow | approval request -> approved or denied tool permission | pre-action, only when approval is required | `PermissionRequest` may allow, deny, or decline; any deny wins across matching hooks | `BLOCK` for that approval request | Does not run for calls that require no approval. Tool permission remains distinct from task admission, scope expansion, exception, or completion acceptance. | high |
| Codex local tool path | completed tool -> model/script continuation | post-action | `PostToolUse` can replace feedback, reject a nested code-mode promise, or alter subsequent processing | `OBSERVE` for the completed effect; `MEDIATE` for later processing | Cannot undo files, commands, network requests, or other completed side effects. | high |
| Codex turn | user prompt -> prompt processing | pre-processing | `UserPromptSubmit` may return block or exit `2` | `BLOCK` for prompt processing | Matcher is not supported for this event. Blocking a prompt is not task admission and does not itself create normalized task meaning. | high |
| Codex turn | stop request -> continuation | before turn termination | `Stop` block result creates a continuation prompt | `BLOCK` for the exact stop transition | Must guard repeated continuation with `stop_hook_active`; it does not prove semantic completion. | high |
| Codex session | session start -> first/continued model request | before model request | synchronous `SessionStart` context; `continue: false` can end the turn in documented cases | `ADVISE`, or `BLOCK` only for the exact subsequent model request | Session activation is not task admission. Hook trust and source configuration still apply. | medium-high |
| Codex native governance choice | MCP form request -> bound human response | foreground interaction | current repository MCP Adapter and installed-runtime evidence demonstrate a capability-gated native form path | `MEDIATE` | Public OpenAI documentation located in this audit did not provide a sufficient standalone elicitation contract. Treat this as repository/runtime evidence, not a universal Codex claim. Tool selection is still model-controlled unless a separate lifecycle gate forces the transition. | medium |
| Claude Code local and documented hosted tool paths | tool call -> execution | pre-action | synchronous `PreToolUse` supports allow, deny, ask, defer, and `updatedInput`; deny has highest precedence | `BLOCK` for the matched call; `MEDIATE` for ask/defer/rewrite | Covers documented Bash, PowerShell, file, search, agent, user-question, plan, and MCP tools. It does not fire for `@` file references or `EndConversation`. Path handling is platform-sensitive. Command, HTTP, and MCP-hook timeout or ordinary failure is non-blocking; an Agent SDK callback timeout blocks. | high |
| Claude Code approval flow | permission request -> permission decision | pre-action when a prompt would occur | `PermissionRequest` decision object can allow or deny; permission rules still apply | `BLOCK` for that permission request | Does not replace AgentGov authority. In non-interactive contexts, behavior and available callbacks differ. | high |
| Claude Code tool path | completed tool -> next model step | post-action | `PostToolUse` supplies feedback or replaces model-visible output; `PostToolBatch` can stop the loop before the next model call | `OBSERVE` for the completed effect; up to `BLOCK` for the next model call | Neither event undoes the completed side effect. Async hooks are not gates. | high |
| Claude Code task/turn | task completion or stop -> recorded completion/termination | before the named state change | `TaskCompleted`, `Stop`, and related hooks can reject the exact transition | `BLOCK` for the documented transition | A host task is not automatically an AgentGov admitted task, and a stopped turn is not semantic completion. | high |
| Claude Code MCP interaction | elicitation request -> human response -> server delivery | foreground interaction | native MCP form or URL dialog; `ElicitationResult` occurs before the response reaches the server | `MEDIATE`; potentially `BLOCK` for response delivery | `Elicitation` hooks can auto-respond and `ElicitationResult` hooks can modify or decline a response. A governance Adapter must declare whether policy prevents those substitutions before treating the result as trusted human authority. | high for capability, medium for authority trust |
| Claude Code configuration | untrusted or disabled hook -> hook activation | configuration boundary | workspace trust, settings precedence, and managed policy control whether hooks run | `UNKNOWN` until bound to deployment evidence | Users can disable unmanaged hooks for a run; managed policy can make managed hooks non-disableable below that level. | high |
| DeepSeek API by itself | model tool-call output -> external tool execution | outside model API | the client receives a structured tool request and executes the function itself | `UNKNOWN` as a Harness effect | The official API states that the model does not execute the function. No pre-action host hook, human UI, mediation, or block mechanism is supplied by the model API contract reviewed here. | high |
| DeepSeek model through Codex | any governed host transition | host-defined | DeepSeek is configured as Codex's model provider | inherit Codex row | Capability must be keyed to Codex surface and version, not to the DeepSeek model name. | high |
| DeepSeek model through Claude Code | any governed host transition | host-defined | DeepSeek is configured through its Anthropic-compatible endpoint | inherit Claude Code row | Capability must be keyed to Claude Code surface and version. API compatibility does not itself prove every host feature or governance decision path. | high |
| Unnamed “DeepSeek harness” | any lifecycle transition | unknown | no canonical host contract established by reviewed official sources | `UNKNOWN` | DeepSeek's official integration catalog points to multiple separate agent hosts. Select a concrete host before creating an Adapter or enforcement claim. | high that the term is ambiguous; no claim of universal absence |

## Host summaries

### Codex

The current OpenAI Docs materially supersede the repository's earlier Adapter
assumption. `PreToolUse` is now a real pre-execution hook for supported local
tool paths and can deny or rewrite a call. `PermissionRequest` can also allow or
deny an approval request. `PostToolUse` remains explicitly post-action.

The strongest honest statement is:

> Codex can `BLOCK` a matched supported local tool call before execution when a
> synchronous, enabled, trusted hook returns the documented deny result.

It is not honest to claim universal interception because hosted tools are not
covered, specialized tool paths may opt out, hook trust and configuration can
disable non-managed hooks, and invalid policy-hook output can allow the call to
continue. A managed deployment can strengthen the activation claim, but that
requires separate configuration and runtime evidence.

The repository's current Codex Adapter still has valuable evidence for privacy,
post-action honesty, duplicate `Stop` protection, routing, and authority
separation. It should be treated as the first conformance base, not as the final
current-host capability ceiling.

### Claude Code

Claude Code provides the richest documented host surface in this audit. Its
`PreToolUse` decision contract supports deny, ask, defer, allow, and input
rewriting over a broad tool set. It also exposes separate permission, post-tool,
batch, task, stop, and MCP elicitation transitions.

The important limitation is failure semantics. Most command, HTTP, and MCP hook
timeouts and ordinary failures are non-blocking, so the presence of a
`PreToolUse` hook alone is not a fail-closed enforcement proof. Agent SDK callback
timeouts behave differently and block. Harness capability declarations must
therefore identify the hook family, not merely the event name.

Native MCP elicitation is suitable for a human decision surface, but its result
is not automatically trustworthy for AgentGov authority: other hooks may
programmatically answer or alter it. The Adapter must bind the response and
declare the policy/configuration evidence that makes its human-origin claim
acceptable.

### DeepSeek

DeepSeek's official Tool Calls guide defines a model/API boundary: the model
returns a function request and the caller executes the function. Its official
agent-integration material shows DeepSeek models running inside several distinct
hosts, including Codex and Claude Code.

Consequently, Harness v1 should separate:

- `provider_family`, such as `deepseek`, `openai`, or `anthropic`;
- `host_family`, such as `codex` or `claude-code`;
- `host_surface` and version, such as CLI, IDE, desktop, SDK, or API wrapper.

A future “DeepSeek Adapter” is not a sufficiently scoped requirement. It must
name a concrete execution host such as Codex-with-DeepSeek,
Claude-Code-with-DeepSeek, OpenCode, or another specific harness. The enforcement
capability then comes from that host.

## Minimum Harness Contract v1 fields

The contract should extend the current host-interaction and coding-agent
contracts rather than introduce a parallel Kernel vocabulary. The minimum
portable fields are grouped below; exact schema names remain a follow-on design
decision.

### Contract and binding identity

- `contract`, `schema_version`, and `declaration_digest`;
- `adapter_id` and `adapter_version`;
- `host_family`, `host_surface`, and `host_version`;
- `provider_family` as separate, non-authoritative metadata;
- `repository_correlation` using the existing privacy-preserving local binding;
- `declared_at` or evidence snapshot date.

### Transition identity

- vendor-neutral `transition_type`;
- `phase`: `before`, `after`, or `between`;
- stable `event_id` and correlation identity;
- `action_class` and host tool/event name as Adapter metadata;
- `block_target`: the exact transition that a block result can prevent;
- `already_completed_effect`: explicit boolean so post-action results cannot
  imply rollback.

### Capability declaration

- `observation_mode` and evidence provenance;
- `mediation_mode`;
- `block_mode`: `supported`, `unsupported`, or `unknown`;
- `coverage`: included tool/event paths and known exclusions;
- `execution_mode`: synchronous or asynchronous;
- `decision_delivery` and `decision_recording` using the existing interaction
  vocabulary where possible;
- `human_origin_assurance`: mechanism plus trust/configuration evidence, never
  an Adapter inference;
- `failure_behavior`: fail open, fail closed, host default, or unknown;
- `timeout_behavior` separately from ordinary failure;
- `bypass_conditions`, `configuration_requirements`, and `evidence_refs`;
- `confidence`: documented, locally demonstrated, externally demonstrated, or
  unknown.

### Normalized event provenance and privacy

- `source_actor_class`: host, Agent, AgentGov, Human/External, or CI/SCM;
- `fact_kind`: host observation, locally derived deterministic fact, normalized
  semantic input, or human decision;
- an allow-listed bounded payload for the transition;
- explicit rejection of raw prompts, transcripts, model output, source content,
  credentials, raw tool input/output, and absolute paths in Core contracts;
- repository-relative evidence references only where the existing contracts
  allow them.

The host Adapter may inspect a vendor payload transiently to make a decision,
but it must discard disallowed data before constructing or persisting the
vendor-neutral event.

### Harness result

Runtime disposition and governance effect must remain separate:

- `disposition`: `continue`, `pause`, `abort`, or `no_op`;
- `effect`: existing `OBSERVE`, `ADVISE`, `MEDIATE`, or `BLOCK`;
- `status`: accepted, denied, unavailable, invalid, stale, duplicate, or error;
- stable `reason_code` and bounded model/user-facing explanation;
- exact `affected_transition` and, for `BLOCK`, `prevented_transition`;
- AgentGov state/evidence digest observed before the decision;
- post-result evidence confirming whether the host honored the disposition;
- denied authority fields matching the current contracts.

## Required conformance cases

The future conformance suite should be shared by every concrete host Adapter and
should not assume that all hosts reach the same ceiling.

1. A valid supported pre-action call is allowed and executes once.
2. An invalid supported pre-action call is denied and produces no side effect.
3. A post-action violation records `already_completed_effect: true` and never
   claims rollback.
4. An uncovered tool path returns `unsupported` or `unknown`; it does not inherit
   a `BLOCK` claim from another tool path.
5. Hook timeout, malformed output, unavailable process, disabled hook, and
   untrusted hook each produce the declared failure behavior.
6. Tool permission never creates task admission or other AgentGov authority.
7. A human decision is accepted only through the declared bound surface and is
   rejected after substitution, mismatch, replay, or staleness.
8. Duplicate and out-of-order events do not advance state twice.
9. A provider swap, including OpenAI/Anthropic to DeepSeek, does not silently
   change the host capability declaration.
10. A host version or configuration change invalidates stale capability proof.

## Recommended next bounded requirement

Create **AgentGov Harness Contract v1 and Codex pre-action conformance** as a
separately aligned and admitted requirement:

1. define strict capability-declaration, normalized-event, and Harness-result
   contracts by composing existing Kernel and host-interaction semantics;
2. extend the Codex Adapter with a privacy-bounded `PreToolUse` mapping for the
   exact supported local tool paths;
3. add positive and negative conformance fixtures, including fail-open/error,
   uncovered-path, post-action honesty, task-admission separation, and provider
   swap cases;
4. update the earlier Codex documentation and source-of-truth surfaces that
   still describe the 2026-08-06 capability ceiling;
5. leave Claude Code implementation and every specifically named third-party
   DeepSeek host as later, separately admitted Adapters.

This is Adapter/Application work unless conformance reveals a portable
governance meaning that the current Kernel cannot express. Under ADR-0016, the
audit itself does not meet the reopening test for new Kernel promotion.

## Sources

Official sources, accessed 2026-08-14:

- OpenAI, [Codex Hooks](https://learn.chatgpt.com/docs/hooks), especially hook
  trust, tool coverage, `PreToolUse`, `PermissionRequest`, `PostToolUse`, and
  `Stop` behavior.
- OpenAI, [Codex advanced configuration](https://learn.chatgpt.com/docs/config-file/config-advanced),
  especially trusted project config and managed hook configuration.
- Anthropic, [Claude Code hooks reference](https://code.claude.com/docs/en/hooks),
  especially timeouts, event-specific block behavior, `PreToolUse`,
  `PermissionRequest`, and `PostToolUse`.
- Anthropic, [Claude Code MCP](https://code.claude.com/docs/en/mcp), especially
  MCP elicitation and the client-owned confirmation boundary.
- DeepSeek, [Tool Calls](https://api-docs.deepseek.com/guides/tool_calls/),
  especially the caller-owned function execution step.
- DeepSeek, [Integrate with Codex](https://api-docs.deepseek.com/quick_start/agent_integrations/codex/)
  and [Integrate with Claude Code](https://api-docs.deepseek.com/quick_start/agent_integrations/claude_code/),
  establishing DeepSeek as the model/API provider inside named hosts.
- DeepSeek, [Using the Anthropic API](https://api-docs.deepseek.com/guides/anthropic_api/),
  documenting the compatibility boundary and unsupported fields.
- DeepSeek, [Awesome DeepSeek Agent](https://github.com/deepseek-ai/awesome-deepseek-agent),
  an official catalog of multiple distinct agent integrations rather than one
  canonical DeepSeek harness.

Repository evidence:

- `docs/adr/0016-establish-minimum-sufficient-kernel-architecture.md`;
- `docs/kernel-boundary-classification-2026-08-10.md`;
- `docs/codex-hooks-adapter.md`;
- `docs/governance-mcp-adapter.md`;
- `tests/test_codex_hooks.py`;
- `tests/test_coding_agent_transport.py`;
- `tests/test_governance_mcp.py`;
- `tests/test_host_interaction.py`.
