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
repository identity, or a human decision.

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
passes. The fresh external Codex replay remains separately controlled and has
not occurred.

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
