---
layout: reference
title: "ADR-0016: Establish the minimum sufficient Kernel architecture"
source_path: docs/adr/0016-establish-minimum-sufficient-kernel-architecture.md
---

# ADR-0016: Establish the minimum sufficient Kernel architecture

Status: accepted on 2026-08-10 by the human product owner after a governed
alignment and task-admission journey.

## Decision gate

Define the smallest durable architecture baseline that preserves AgentGov's
governance meaning without turning every workflow concern into a Kernel
concept, claiming enforcement that has not been demonstrated, or reorganizing
the current implementation before a real consumer exposes a concrete gap.

## Context

AgentGov already has strict contracts for task admission, authority, evidence,
development state, completion, handoff, host interaction, and advisory review.
Those contracts grew through bounded vertical slices. The repository now needs
a stable test for deciding which meanings belong in the Kernel and which belong
in Policy, Application, Adapters, Consumer Context, or an Experiment.

The immediate risk is conceptual expansion rather than missing runtime code.
A larger ontology, new schema family, or implementation reorganization would
add compatibility and maintenance cost before an independent consumer has
shown that the current contracts cannot express a necessary outcome.

## Decision

Adopt the following one-page Kernel Constitution as the architecture baseline.

### Kernel Constitution

**Philosophy:** Observe concretely. Abstract minimally. Govern explicitly.
Learn cautiously.

**Principles:**

1. Seek invariants, not incidents.
2. Use the minimum sufficient abstraction.
3. Prefer composition over concept proliferation.
4. Preserve meaningful distinctions.

**Critical distinctions:**

- Capability is not Authority; Transport Permission is not Governance
  Authority.
- Evidence is not Decision; Readiness is not Approval.
- Deterministic Fact is not Semantic Judgment.
- Proposal is not Admission; Task Admission is not Downstream Authority.
- Declared is not Configured, and Configured is not Enforced.
- Detected is not Prevented.
- Attribution is not Authenticated Identity.
- Self-authored Semantic Assertion is not Independent Evidence.
- Attempted Transition is not Completed Transition.
- Learning Candidate is not Admitted Learning.
- Completion Verified is not Bounded Handoff.

**Admission questions for a new Kernel concept:**

1. **Necessity:** what distinction or governed outcome is lost if the concept
   is removed?
2. **Independence:** after substituting the host, protocol, UI, vendor, and
   consumer domain, does the meaning remain?
3. **Authority integrity:** would the concept duplicate or obscure the source
   of truth for state, evidence, scope, risk, authority, or decision?
4. **Evidence sufficiency:** is the supporting evidence traceable and
   proportionate to the claim, and is any claimed independence genuine?

A concept enters the Kernel only when all four questions have evidence-backed
answers. A single strong counterexample may reject promotion. Passing these
questions permits review; it does not automatically admit the concept.

### Responsibility model

- **Kernel:** governance meaning and state semantics, including the identities,
  distinctions, bindings, and transition preconditions that must remain true
  across hosts and consumers. It does not own storage merely because state is
  persisted.
- **Policy:** valid-path selection, defaults, thresholds, cadence, risk routing,
  and other replaceable governance choices.
- **Application / Product Surface:** journeys, orchestration, presentation,
  Monitor, Dashboard, cards, Benefit views, and user-facing sequencing.
- **Adapter:** host, provider, protocol, transport, and tool mechanics.
- **Consumer Context:** repository-specific ownership, trust boundary, local
  commands, domain rules, and deployment or business semantics.
- **Experiment:** candidate meanings that remain provisional until observed use
  supplies promotion evidence.
- **Enforcement:** a cross-cutting, per-transition claim, not a layer.

If violating an ordering rule would corrupt authority, evidence binding, or
state correctness, the rule is a Kernel transition precondition. If it affects
only experience or presentation, it belongs in the Application.

### Enforcement claim discipline

An enforcement claim must identify the actual journey transition and record
two independent axes:

- effect: `OBSERVE`, `ADVISE`, `MEDIATE`, or `BLOCK`;
- owner/location: AgentGov, Host, CI/SCM, or Human/External.

It must also name the mechanism, required evidence, what it can and cannot
prevent, bypass conditions, and failure or abort behavior. `BLOCK` must state
the exact transition it blocks. A workflow file proves declaration only;
configuration and demonstrated enforcement require separate evidence.

AgentGov's current identity is a **repo-native governance system with a
semantic Kernel, selective mediation, and independent deterministic replay**.
It is not a universal control plane. A stronger control-plane claim may be
earned only for individually declared and mediated transitions.

### Minimum governed journey

```text
Propose -> Admit -> Implement -> Scope/Evidence Check
        -> Completion Verified -> Bounded Handoff
```

Completion verifies the admitted work and evidence. Handoff is the distinct
human-controlled transition that closes responsibility for the bounded
session. Neither step grants commit, merge, release, deployment, or other
downstream authority.

### Promotion pause and reopening test

Pause new Kernel concept promotion until concrete evidence shows at least one
of the following:

1. a real journey has a necessary governed outcome the current Kernel cannot
   express;
2. the same semantic gap recurs in two independent consumer contexts; or
3. a transition-level enforcement analysis exposes an inconsistency in
   governance meaning or authority, not merely an implementation omission.

This is not a development freeze. Application, Adapter, Policy, consumer, and
bug-fix work may continue. Extending an existing Kernel contract's semantics
counts as promotion.

A structured counterexample in a reopening request must name the transition,
evidence, exact failure, the
failed distinction-loss or substitution test (or authority conflict), why an
existing non-Kernel layer is insufficient, and the net-new governed outcome.
Narrative preference alone is not sufficient.

## Owns

- the admission test for new Kernel concepts;
- the durable responsibility boundaries above;
- the distinction between completion verification and bounded handoff;
- per-transition honesty requirements for enforcement claims;
- the evidence threshold for reopening Kernel architecture work.

## Does not own

- a runtime or schema reorganization;
- a permanent classification registry for every repository file;
- selection or modification of an external consumer;
- required-check configuration, branch protection, or merge proof;
- a new identity, concurrency, telemetry, Learning, or enforcement subsystem;
- Git operations, publication, release, or deployment.

## Consequences

Architecture review now has a compact rejection-by-default baseline. Existing
contracts remain valid; the dated classification accompanying this ADR is a
diagnostic snapshot, not a migration plan. Product and Adapter work can proceed
without reopening the Kernel unless concrete evidence passes the reopening
test.

The cost is deliberate restraint: some boundary overlaps remain documented
rather than immediately removed. That is preferred to premature compatibility
commitments.

## Alternatives considered

### Introduce a larger canonical ontology now

Rejected. No independent consumer has demonstrated the required distinction or
outcome, and the additional concepts would precede evidence.

### Treat every persisted state or workflow step as Kernel-owned

Rejected. Storage and user-journey sequencing are implementation and
Application concerns unless governance meaning would otherwise be lost.

### Treat enforcement as a dedicated architectural layer

Rejected. Effect and owner are orthogonal and must be proved for each actual
transition.

## Implementation plan

1. Record this decision and one dated classification of current contract
   families.
2. Synchronize the invariants, governance model, README, status, and plans.
3. Add documentation tests that protect the baseline and its evidence limits.
4. Stop architecture expansion. Select any external consumer proof as a later,
   separately admitted requirement.

## Validation

Deterministic validation confirms that the baseline documents are linked,
preserve the named distinctions and responsibility boundaries, and do not
change repository behavior. The repository checks and complete unit suite must
still pass.

Advisory review evaluates whether the baseline is minimal, whether claims match
available evidence, and whether any wording accidentally grants or implies
authority.

## Rollback or replacement

A later ADR may supersede this decision only with a reopening request in the
form above and evidence from a real journey. It must state which distinction or
outcome this baseline loses and the compatibility impact of replacement.
