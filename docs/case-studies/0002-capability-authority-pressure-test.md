---
layout: reference
title: Capability and authority pressure test
source_path: docs/case-studies/0002-capability-authority-pressure-test.md
---

# Case study 0002: Capability and authority pressure test

## Case identity

- Case: `AG-AUTH-001`
- Date reviewed: 2026-08-09
- Classification: domain-independence architecture pressure test
- Finding semantics: repository facts plus advisory architecture judgment
- Implementation decision: record for later validation; no Core redesign

## Goal and evidence boundary

This case asks whether an available consequential capability can remain
separate from authority to use it, and whether an observed outcome can remain
separate from admission of a future behaviour change.

It is intentionally domain-neutral. It does not propose a general execution
engine, new business-risk vocabulary, a runtime policy service, or an
autonomous learning system. The review uses the current repository contracts,
ADRs, Adapter behavior, and declared non-goals. It does not prove that AgentGov
intercepts capabilities it does not mediate.

## Pressure-test sequence

The abstract action sequence is:

```text
Capability available
  -> Current state established
  -> Required evidence bound
  -> Structural transition validated
  -> Advisory reasoning reviewed when applicable
  -> Responsible authority decides when required
  -> Exact admitted transition may execute
  -> Outcome becomes evidence, not automatic policy
```

The related learning sequence is:

```text
Outcome
  -> Learning candidate
  -> Validation
  -> Separate admission
  -> Versioned future behaviour
```

The second sequence is an architecture acceptance scenario, not an implemented
runtime-learning contract.

## Findings

### 1. Capability and authority remain distinct

**Assessment: preserved.** Capability manifests distinguish implementation
and decision authority. Development state and trigger contracts carry explicit
negative authority boundaries. ADR-0015 additionally states that MCP tool
permission is transport permission and not task admission.

### 2. State, evidence, permission, and transition validity

**Assessment: expressive as a responsibility model, bounded in current
implementation.** The current development contracts already bind task and
state identity, evidence freshness, exact decisions, actor class, and allowed
transitions. Those responsibilities are domain-independent. The concrete
schemas are deliberately coding-development contracts, however; AgentGov does
not currently expose a universal consequential-action authorization schema.
Permission is represented through admitted tasks, standing policy, bounded
human decisions, and explicit negative authority fields rather than one
universal `Permission` object. That is a product-scope limit, not a reason to
generalize before observed use.

### 3. Structural, reasoning, and human gates

**Assessment: meaningful if they remain distinct responsibilities, not one
authorization score.** The structural gate validates form, identity, state,
evidence, and transition preconditions. The reasoning gate supplies explicitly
advisory semantic judgment through a host Provider or accountable reviewer.
The human gate supplies authority where policy requires it. Passing an earlier
gate cannot synthesize a later decision. These labels describe the existing
separation; they are not a new canonical three-stage runtime API.

### 4. Native MCP Adapter

**Assessment: it does not equate availability with authorization for the
transitions it owns.** Capability negotiation controls whether form tools are
advertised. Exact form decisions, bound digests, current state, and create-only
revalidation control whether their declared write occurs. Clients without the
required decision surface retain the smaller tool set, and ordinary tool
permission does not substitute for admission.

### 5. Tool versus governance plane

**Assessment: open architecture, but no current independent enforcement
plane.** AgentGov is currently delivered through repository-native Core
contracts plus optional commands, hooks, and MCP tools. When invoked, it can
govern its own transitions. It cannot deterministically force a host Agent to
select AgentGov before another tool, nor does it mechanically wrap arbitrary
host capability calls. ADR-0009 and ADR-0013 already reject claims of runtime
enforcement or a hostile-agent security boundary.

Vendor-neutral Core transitions and replaceable adapters leave room for a
future host mediation point. If the product later claims authority over
arbitrary consequential tool execution, the mediation or enforcement point,
threat model, failure mode, and authority source must be decided separately.

### 6. Learning candidate to admitted learning

**Assessment: representable without domain concepts, not first-class runtime
behavior today.** An outcome can be stored as evidence or an observation; a
candidate change can then follow the existing advisory review, human-owned
requirement or policy admission, versioned artifact, and validated transition
pattern. No outcome may directly expand authority or activate future behavior.

The repository does not yet define a generic learning-candidate schema or bind
an admitted candidate to a runtime behavior version. Adding either before an
observed product need would exceed the current lightweight coding-governance
scope. Benefit and Learning views must continue to distinguish observations,
inferences, feedback, and unknowns rather than applying behavior changes.

### 7. Pre-v1 Core decision

**Assessment: no Core flaw requiring a pre-v1 redesign.** The current
principles already separate deterministic facts, advisory judgment, human
authority, and transport permission. The real gap is claim and validation
scope: the Native MCP Adapter is not an independent policy-enforcement point,
and learning admission is not an implemented runtime feature.

This case therefore adds one general invariant and remains a later portability
and architecture validation scenario. It does not change the existing roadmap,
release identity, product behavior, or authority.

## Future validation signals

This scenario is satisfied only when a future relevant implementation can
show all of the following without domain-specific policy in Core:

- capability discovery and transport permission remain insufficient to apply
  a consequential transition;
- current state, required evidence, exact decision, and authority can be
  reconstructed from bounded records;
- structural failure, advisory uncertainty, and missing human authority remain
  different outcomes;
- a missing or stale admission fails closed at the actual mediation point;
- an outcome may create a learning candidate but cannot directly change active
  behavior or expand authority;
- product language states honestly which capabilities AgentGov mediates and
  which remain outside its enforcement boundary.

## Stop conditions

- Stop if validation requires consumer-specific business objects, thresholds,
  strategies, or risk calculations in Core.
- Stop if an optional AgentGov tool call is described as mechanical coverage of
  unrelated host tools.
- Stop if evidence, advisory model output, or a prior outcome can silently
  become permission, human authority, or active future behavior.
- Stop before implementing a generic executor, runtime security boundary, or
  self-modifying policy system without a separate human-approved requirement
  and ADR.
