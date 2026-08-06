# ADR-0014: Route semantic review through host Providers

Status: Accepted

Implementation status: contract and host-neutral active-Agent self-review
Adapter slices are implemented in development source; production host callbacks
and real model calls remain open.

## Decision gate

Who supplies LLM inference for requirement, architecture, and Skill-driven
semantic review, and how does AgentGov route risk without making a second model
mandatory or granting model output governance authority?

## Context

AgentGov already verifies deterministic repository facts and now has a
host-side natural-language Alignment Adapter. Semantic questions such as
whether a requirement was misunderstood, an architecture center drifted, or a
Grill-style challenge exposed an unknown require LLM or human judgment. Using
only the developing Agent risks confirmation bias; requiring a new model for
all users adds cost, latency, privacy exposure, configuration work, and vendor
coupling.

## Decision

AgentGov Core remains model-free. It owns deterministic facts, risk
classification, minimal context boundaries, Provider and assurance disclosure,
strict result validation, state, and denied authority. Semantic inference is a
host Adapter responsibility represented by vendor-neutral Provider contracts.

Risk routing is:

- low risk: no semantic model call when deterministic checks are sufficient;
- medium risk: use the active Coding Agent's existing entitlement for a
  disclosed `self_review` in a separate pass or isolated context;
- high risk: use an optional user- or organization-provided
  `independent_review` with at least isolated context;
- high risk without qualifying independence: offer exactly human review,
  explicit lower-assurance self-review, or Provider setup. Select none and do
  not silently downgrade.

Independence is disclosed as `same_turn`, `separate_pass`,
`isolated_context`, `different_model`, or `different_provider`. A different
model or Provider raises independence but does not prove correctness. An active
host entitlement can declare only self-review. All results remain
evidence-linked `ADVISORY` observations.

Provider credentials, cost, retention, and transfer policy belong to the user,
organization, or a separately approved future hosted service. Raw prompts,
answers, transcripts, assistant responses, source content, credentials, model
prompts, and absolute host paths are excluded from Core contracts.

## Owns

- semantic-review Provider capability semantics;
- low, medium, and high semantic risk routing;
- independence and assurance disclosure;
- unavailable independent-review choices and no-silent-downgrade behavior;
- result binding, advisory semantics, privacy boundary, and denied authority;
- the distinction between single-Agent self-review and Multi-Agent independent
  review.

## Does not own

- a model SDK, endpoint, account, API key, credential store, or billing system;
- semantic correctness or objective architecture judgment;
- a production materializer, sub-agent runtime, host callback, or UI;
- an AgentGov-hosted Reviewer service;
- task admission, requirement or ADR mutation, code or scope authority,
  exceptions, Git, publication, release, deployment, or production operations.

## Consequences

Ordinary use remains zero-configuration and vendor-neutral. High-risk teams can
add independent review once at user or organization level. Results disclose
real assurance and cannot claim that self-review is independent. The cost is a
small Provider/routing contract surface and a future Adapter implementation per
host family.

## Alternatives considered

- Bundle a default LLM in Core: rejected because it creates credential,
  privacy, billing, network, and vendor dependencies.
- Always use the active Agent: rejected for high risk because it hides
  confirmation bias and cannot claim independence.
- Require a second model for installation: rejected because it violates the
  lightweight and ten-minute adoption path.
- Silently fall back when Reviewer access fails: rejected because it
  misrepresents assurance.

## Implementation plan

1. Completed: strict Provider, route, and advisory result contracts plus
   cross-agent fixtures; no model call.
2. Completed: connect the existing `ReferenceAlignmentAdapter` to an
   `ActiveAgentSelfReviewMaterializer` callback while preserving the same Core
   contracts; Codex and Claude Code fixtures rehearse the portable path offline.
3. Install a real callback in one Coding Agent surface, then rehearse the
   independent-review path before any hosted Provider decision.

## Validation

Deterministic tests validate field closure, mode/independence combinations,
risk routing, the exact three unavailable choices, digest bindings, privacy,
advisory-only semantics, vendor-neutral Core, and denied authority. Human
review remains responsible for whether the risk policy, selected Provider, and
reported conclusion are appropriate and correct.

## Rollback or replacement

A later ADR may add a hosted Provider or revise assurance levels after real
host evidence. It must preserve explicit opt-in, no silent downgrade,
advisory-only results, portable Core contracts, and human final authority, or
explicitly supersede this decision.
