# ADR-0015: Use MCP elicitation for Codex task-proposal admission

Status: accepted on 2026-08-07 by the human product owner through selection of
the Codex production materializer and native proposal-review direction.

## Decision gate

Choose how a real Codex host converts an ordinary request into the implemented
strict task proposal and records the human's review without treating model
output or generic tool permission as task-admission authority.

## Context

Development source already provides `ReferenceTaskProposalAdapter`, the strict
`agentgov.task-proposal` contract, read-only admission previews, and exclusive
task creation after a separate human decision. The installed Codex MCP Adapter
already lets the current Coding Agent send normalized meaning to Core, but its
five tools are read-only and do not cover task proposals.

Current Codex documentation and the locally generated app-server schema expose
MCP form elicitation. A server may issue `elicitation/create` while a tool call
is pending; the client presents a native form and returns `accept`, `decline`,
or `cancel`. The MCP specification requires client capability negotiation and
forbids using form elicitation to collect secrets.

Sources:

- [Codex App Server protocol](https://learn.chatgpt.com/docs/app-server)
- [MCP elicitation specification](https://modelcontextprotocol.io/specification/2025-11-25/client/elicitation)
- [MCP lifecycle and capability negotiation](https://modelcontextprotocol.io/specification/2025-11-25/basic/lifecycle)

## Decision

Extend the existing foreground Codex MCP Adapter with one host-materialization
tool. The current Codex Agent supplies only a normalized low-risk proposal
draft; it does not supply proposal identity, privacy declarations, authority,
repository identity, an accountable-owner identity, or a human decision. The
native Adapter supplies the repository's canonical `Human product owner` role
to the reviewed plan. This role attribution is grounded in the native decision
boundary but is not cryptographic proof of which individual operates the
client.

The Adapter derives the repository locally, creates and validates the strict
proposal plus exact admission plan, and then issues one MCP form elicitation
containing the complete bounded preview and its digests. The form has one
required decision: admit the exact task, request changes, or reject it.
Its `requestedSchema` uses only the restricted MCP form-schema root fields and
a titled single-select enum. Elicitation-result top-level protocol extensions
are ignored and never echoed; the standard action and accepted content remain
strictly validated.

Only the conjunction of MCP `action=accept` and the exact `admit` form value may
apply the revalidated plan. Decline, cancel, request-changes, reject, malformed
content, missing capability, transport loss, target drift, and target races
write nothing. Ordinary MCP tool permission is transport permission only and
never substitutes for the elicited governance decision.

The proposal tool is advertised only when the initialized client declares MCP
form elicitation support. Existing clients retain the original five-tool
read-only surface.

For repository-changing work, the host should select this tool when no
human-admitted task matches and explicitly authorizes the exact requested
change. An unrelated, measurement-only, or differently scoped admitted task
does not count; read-only work does not trigger proposal review. This clarifies
host-routing guidance only. It does not change the Adapter protocol, form, task
schema, decision mapping, or human authority, and deterministic validation
cannot force model tool selection.

## Owns

- Codex-host normalized task-proposal tool input;
- MCP form-elicitation request and response binding;
- proposal preview size and privacy limits;
- exact human decision mapping;
- exclusive task creation after revalidation;
- compatibility behavior when elicitation is unavailable.

## Does not own

- OpenAI account identity, Codex authentication, or cryptographic proof of the
  person operating the client;
- raw conversation storage or semantic inference inside AgentGov Core;
- medium/high-risk task admission, standing-policy fast-track, session start,
  code changes, scope exceptions, Git operations, publication, deployment, or
  release;
- custom App Server clients, web components, MCP Apps UI, or another host;
- installation, external replay, consumer adoption, or stable release identity.

## Consequences

Users can review a proposal inside their current Codex surface without typing
internal JSON or a special terminal word. The current Agent acts as the
production semantic materializer using its existing conversation and model
entitlement, while AgentGov adds no model, credential, or network call.

The proposal tool is intentionally write-capable only after elicitation, so its
MCP annotations cannot claim read-only behavior. Codex may impose an additional
tool-permission gate; that platform permission is not counted as admission.
Client support, UI clarity, and actual interruption burden require a separately
authorized installed-runtime rehearsal.

## Alternatives considered

### Build a custom Codex App Server client

Rejected for this slice. It would create and maintain another client surface
when the current Codex client already supports the required MCP interaction.

### Use the ordinary MCP tool approval prompt as task admission

Rejected. Tool permission answers whether a tool may execute; it does not prove
that the user reviewed the exact governed task contract and digests.

### Use Codex lifecycle Hooks for the decision

Rejected. Command Hooks can add context or enforce lifecycle policy, but they
do not provide the digest-bound custom form response required here.

### Keep terminal `ADMIT` as the only Codex path

Retained only as a recovery fallback. It does not meet the selected native
review experience and adds a special confirmation word outside the host UI.

## Implementation plan

1. Admit a bounded Adapter `1.3.0` task and preserve the existing five tools.
2. Add strict normalized proposal input and local repository binding.
3. Add capability-gated MCP elicitation with exact preview and decision schema.
4. Revalidate and exclusively create only after explicit native admission.
5. Add offline protocol, failure-atomicity, privacy, compatibility, config, and
   documentation tests.
6. Treat installation and a fresh Codex replay as separate human-controlled
   actions after source review.

Implementation status: the exact `1.3.0` source is now installed in the
existing local pipx environment and installed-runtime protocol preflight
passes. Standalone authentication is repaired. One separately authorized
UTF-8-safe App Server replay completed a real read-only turn without surfacing
a native form, but its text-presence heuristic could not prove whether the
proposal tool was called. That run is `INVALID_MEASUREMENT`. Test-only
structured normalization now accepts only exact proposal-call, elicitation,
result, and terminal events. A following authorized replay completed a real
ephemeral read-only turn with normalized state `not_called`, zero exact
proposal calls, and zero forms. This is valid evidence that the end-to-end
journey did not enter the Adapter path for that request. Because the bounded
evidence intentionally excludes tool inventory, it does not distinguish
discovery/configuration from Agent invocation and is not evidence that the
Adapter passed or failed. Its authorization is consumed; another replay is not
admitted.

A subsequent no-turn App Server `config/read` and `mcpServerStatus/list`
diagnostic confirmed that the project layer loaded and all six AgentGov tools
were exposed. That read-only result isolates the remaining observed gap to
Agent invocation under the formerly ambiguous matching-task trigger; it does
not convert the replay into Adapter pass/fail evidence. Development source now
contains the clarified trigger above. A separately authorized installation-only
step then replaced only the existing AgentGov pipx runtime with an offline-built,
hash-recorded wheel from that exact source. Installed discovery confirms the
same Adapter, protocol, six/five-tool negotiation, and trigger metadata. Project
configuration remained byte-for-byte unchanged, and no replay was started.

The product owner then separately authorized exactly one fresh ephemeral
read-only replay. Its no-model preflight confirmed the project configuration,
ready AgentGov server, all six tools, and the proposal tool. During the one
ordinary repository-change turn, the exact proposal tool started once; the turn
then completed without an AgentGov form-elicitation request. The bridge supplied
no decision, created no task or implementation, changed no repository state,
and did not retry. This demonstrates invocation under the clarified trigger but
not the decided native journey. Diagnosis of the invocation-to-elicitation gap
is a later requirement, not an amendment to this decision.

That bounded diagnosis found no reason to amend this ADR. Current official App
Server documentation and generated schemas support the exact standard form
request and capability surface used here. Two no-model direct calls with the
same valid normalized arguments caused App Server to parse the Adapter's elicitation and
return `decline` when no active turn could host it; the Adapter produced its
expected zero-write non-admission result. The live replay summary retained call
start, form count, and terminal state but not whether a completed item carried
an `agentgov.mcp-tool-error`. Therefore the live result cannot yet distinguish
pre-elicitation input rejection from forwarding or presentation behavior. This
is an evidence-contract gap, not a new architecture decision or proof of a
product-layer defect.

The following human-selected correction changes only the test replay evidence
reducer. It records deduplicated completion count and status, represents an
unrecognized completed result as `completion_unknown`, and retains at most
eight strictly validated `agentgov.mcp-tool-error` records containing only code,
the matching proposal-tool stage, bounded field path, rule, and retryability.
Raw error messages, arguments, content, and extensions remain excluded. This
does not alter the Adapter, App Server protocol, native form, admission
authority, or this ADR, and it cannot reconstruct the historical replay.

## Implementation correction — 2026-08-15 human-owner role binding

The fresh uncoached AIRBNB heading replay reached native form acceptance but
persisted `current-agent` as both task `owner` and `decided_by`. The cause was
inside the native proposal boundary: Adapter `1.4.0` accepted `owner` from the
Coding Agent's normalized tool arguments, and the shared task builder correctly
copied that untrusted value into both durable fields.

Development Adapter `1.5.0` removes `owner` from the capability-gated native
tool schema and exact argument parser. It injects the Adapter-owned canonical
role `Human product owner` before rendering the exact admission plan. A client-
bound `accept` plus `admit` response may therefore create only the reviewed task
with that human role in both `owner` and `decided_by`; an Agent-supplied owner
is rejected before elicitation and writes nothing. Missing capability and every
non-admission or invalid response remain zero-write.

This correction is deliberately native-Adapter-specific. It does not change
the vendor-neutral `agentgov.task-proposal` 1.0 contract, the reference host
materializer, the terminal `ADMIT` fallback, the development-task schema, or
the task validator. Native form mediation establishes the human decision role,
not the personal or account identity of the operator. Published package and
release identities remain unchanged.

A separately admitted local installation step has now placed the exact
reviewed `1.5.0` module into the existing AgentGov pipx development runtime and
repaired only its exposed launcher from the working inner launcher. The
project configuration hash remained unchanged, and byte-verified `1.4.0`
module and launcher backups were retained. Installed no-model preflight
confirmed protocol `2026-07-28`, seven/form and five/base tool discovery,
owner-free proposal schema, pre-elicitation hostile-owner zero-write, and one
accepted disposable task with `Human product owner` as both `owner` and
`decided_by`. This direct file repair is not a wheel, publication, release,
consumer activation, live replay, or personal identity proof. A new consumer
replay still requires separate authority.

## Validation

Deterministic validation covers schemas, client-capability negotiation,
elicitation request/response IDs, exact decision values, plan digests, target
races, no-write outcomes, existing five-tool compatibility, config rendering,
task/scope/repository governance, and the full Python suite.

Advisory review evaluates whether the native form is understandable, whether a
second platform tool-permission prompt appears, whether the current Agent
materializes faithful proposals, and whether the interruption budget remains
acceptable. Fixture success cannot prove those live-host qualities.

## Rollback or replacement

Disable or remove the proposal tool from the Codex MCP config. Existing task
proposal, terminal admission, alignment, and self-review contracts remain
independent. A later ADR may replace MCP elicitation with a trusted host-native
decision API if that produces stronger identity or usability evidence.
