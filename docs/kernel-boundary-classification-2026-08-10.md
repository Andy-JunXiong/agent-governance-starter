---
layout: reference
title: Kernel boundary classification - 2026-08-10
source_path: docs/kernel-boundary-classification-2026-08-10.md
---

# Kernel boundary classification - 2026-08-10

Status: diagnostic snapshot supporting ADR-0016. This is not a permanent
registry, migration plan, implementation map, or claim that every file has one
exclusive architectural owner.

## Purpose and evidence boundary

This snapshot classifies the major contract families already visible in the
repository. It tests whether the minimum Kernel boundary is sufficient before
any runtime, schema, or directory reorganization. Classification follows
meaning and authority, not filenames or storage location.

## Classification

| Responsibility | Current contract families | Boundary note |
|---|---|---|
| Kernel | contract identity and version binding; Capability/Authority; Evidence provenance and freshness; deterministic/advisory finding semantics; decision, permission, and transition bindings; task-admission meaning; attempted/completed transition state; completion verification and bounded handoff | Owns portable governance meaning and state semantics. It does not own persistence, UI, or host mechanics by default. |
| Policy | admission-routing policy; drift cadence and dimensions; risk-to-review routing; applicability, thresholds, defaults, and exception paths | Selects among Kernel-valid paths. A configured policy is not proof that a host or SCM enforces it. |
| Application / Product Surface | development sessions and foreground cycles; alignment and clarification journeys; human-prompt presentation; task/scope/completion cards; Monitor, Dashboard, Benefit, and Learning views | Orchestrates and explains Kernel contracts. Experience ordering remains here unless violation would corrupt authority, evidence, or state correctness. |
| Adapter | Codex hooks and MCP; generic coding-agent event transport; host interaction; Provider invocation and capability discovery; protocol error normalization | Translates host and protocol mechanics. Transport permission does not become governance authority. |
| Consumer Context | repository task contents; validation commands; local controls; owners; branch rules; domain policy and evidence; deployment and business workflow | Stays with the adopting repository. It is a trust and deployment boundary, not a Core runtime layer. |
| Experiment | semantic-relation candidates; future learned policies or checks; unvalidated generalizations from one consumer | Remains provisional until concrete, independent evidence passes ADR-0016's promotion questions. |
| Cross-cutting enforcement | effect, owner/location, mechanism, evidence, bypass, and failure behavior for an actual transition | Not a layer. Claims are made per transition using the Enforcement Matrix dimensions. |

## Deliberate boundary overlaps

These overlaps do not currently require new concepts or file moves:

- A human decision result has Kernel meaning; presenting the decision prompt is
  an Application and host concern.
- A semantic-review result has portable assurance meaning; review routing is
  Policy and Provider invocation is an Adapter concern.
- Drift observations may preserve advisory Kernel semantics; cadence and
  dimension selection are Policy, while reminder cards are Application.
- Governance-event identity and transition binding have Kernel meaning;
  collection, local persistence, export, and visualization are Application or
  Adapter concerns.
- Completion verification is a Kernel-governed state; bounded handoff is a
  separate governed transition surfaced by the Application.

## Enforcement diagnosis

The current repository demonstrates selective mediation and deterministic
replay, not universal interception. Enforcement claims should be captured only
for transitions an actual journey uses:

| Transition example | Effect | Owner/location | Honest current claim |
|---|---|---|---|
| task proposal to admitted task | `MEDIATE` | AgentGov plus Human/External | A matching human decision and revalidated task record are required by the native journey; this does not authorize implementation outside that task. |
| repository write under the project agent protocol | `ADVISE` / fail-closed journey requirement | Host plus AgentGov | The protocol requires admission and stop-on-tool-failure, but optional tool selection is not universal runtime interception. |
| deterministic repository check | `OBSERVE` or `BLOCK` when separately configured | AgentGov locally; CI/SCM when configured | A local failure is detection. A workflow declaration, required-check configuration, and demonstrated merge prevention are separate evidence states. |
| completion verification to bounded handoff | `MEDIATE` | AgentGov plus Human/External | Verified completion does not close the session or grant downstream authority. |
| merge, release, or deployment | outside current Kernel proof | CI/SCM or Human/External | AgentGov grants no such authority in this baseline. |

This table is diagnostic. It is not evidence that branch protection or required
checks are currently configured. A later enforcement proof must include both a
negative case (an invalid transition is blocked) and a positive case (a valid
transition succeeds), bound to the exact configuration and state.

## Result

No current family demonstrates a missing Kernel concept. The visible overlaps
can be expressed through composition of Kernel meaning, Policy choice,
Application journey, Adapter mechanics, and Consumer Context. Therefore no
schema, runtime, or directory change is admitted by this diagnosis.

Reclassification remains possible when a real journey supplies the structured
counterexample required by ADR-0016. Until then, new Kernel promotion is paused
and architecture invitations are rejected by default.
