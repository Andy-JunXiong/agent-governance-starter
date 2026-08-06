# Active-Agent self-review materializer

Development source implements the first executable semantic-review Adapter
slice. It connects a resolved `ReferenceAlignmentAdapter` journey to the
active Coding Agent host without adding a second model or teaching AgentGov
Core to call an LLM.

## Plain-language behavior

After the user has discussed and selected the working direction, AgentGov can
ask the same Coding Agent to take one clearly labeled second look. AgentGov
prepares the review envelope, checks the returned observations, and rejects
anything that changes identity, assurance, evidence, privacy, or authority.
The observation can advise the user; it cannot approve its own work.

```text
resolved human alignment
  -> exact medium-risk self-review route
  -> ephemeral normalized context + allowed repository evidence refs
  -> active host materializer callback (one invocation)
  -> small observation drafts
  -> Adapter-generated IDs and route/Provider digest binding
  -> accepted ADVISORY result with denied authority
```

## Implemented host boundary

`ActiveAgentSelfReviewMaterializer` is a structural Python protocol. A Codex,
Claude Code, IDE, or other Coding Agent Adapter can implement
`materialize_self_review(context)` with its current host entitlement. The
materializer receives:

- the resolved alignment dialogue identity and selected resolution;
- normalized center, advisory drift, and assumptions;
- the exact active-host Provider capability and self-review route;
- an explicit allow-list of repository evidence references;
- content and authority boundaries that are entirely false.

It returns one to twenty `SelfReviewObservationDraft` values. The host does not
choose observation IDs, route identity, Provider binding, assurance, semantics,
or authority. `ReferenceAlignmentAdapter.self_review(...)` creates and accepts
those fields through the existing semantic-review contracts.

## Implemented live foreground transport

The same capability is now available on `agentgov dev --stream` as a strict
two-stage exchange owned by the Coding Agent Adapter:

1. after the alignment response is `resolved`, the Adapter sends
   `agentgov.active-agent-self-review-start` with the exact dialogue digest,
   medium-risk reasons, active-host Provider declaration, and evidence
   allow-list;
2. AgentGov returns `materialization_required` with one deterministic,
   foreground-memory-only context request;
3. the same Adapter uses its existing Coding Agent entitlement to reason and
   sends `agentgov.active-agent-self-review-draft` with small observations;
4. AgentGov validates the pending request digest and returns `completed` with
   the accepted advisory run.

These JSONL records are an Adapter integration protocol, not text the ordinary
user must type. The user makes no additional confirmation and configures no
second model or account. AgentGov makes zero model and network calls; the
active host performs the single disclosed materialization pass.

The [native governance MCP Adapter](governance-mcp-adapter.md) now supplies the
first model-controlled host surface for this exchange. It carries explicit
journey and pending-request bindings while the foreground process is alive;
the ordinary user does not author its records.

## Failure behavior

The operation fails before an accepted result when:

- alignment has not reached a human-owned final resolution;
- risk is not medium;
- the Provider is unavailable, independent-only, or not the active host;
- the host callback fails or returns empty, oversized, duplicate, or malformed
  output;
- an observation cites evidence outside the explicit allow-list;
- content contains a secret-shaped value, an absolute/local path, or raw-data
  claim;
- route, Provider, result, assurance, advisory semantics, or authority drifts.

No failure advances the alignment dialogue or creates repository/runtime state.

## Privacy and authority

The Adapter does not pass raw requests, raw answers, transcripts, assistant
responses, full source content, credentials, model prompts, or absolute host
paths. It does not retain the ephemeral materializer context. Every accepted
result remains `ADVISORY` and denies requirement, architecture, task, session,
code, scope, exception, Git, publication, release, deployment, and external
write authority.

## Honest implementation limit

The callable execution seam, live vendor-neutral JSONL transport, and offline
Codex/Claude Code compatibility rehearsal are implemented. AgentGov still
ships no vendor SDK, model endpoint, credential store, background Agent, or
native Codex/Claude Code/IDE installation that emits these records. The active
Coding Agent host must supply actual semantic inference and its Adapter must
connect the transport. Independent high-risk Reviewer integration is a
separate later slice.

## Feature connections

- Upstream: governed clarification and the human-selected alignment center.
- Current: disclosed active-Agent self-review with exact evidence and assurance
  binding over the shared foreground stream.
- Downstream: install the protocol in one native coding-agent surface, then add
  the optional independent high-risk Reviewer path.
