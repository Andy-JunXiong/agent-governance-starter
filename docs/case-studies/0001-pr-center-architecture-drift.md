---
layout: reference
title: PR-center architecture drift case
source_path: docs/case-studies/0001-pr-center-architecture-drift.md
---

# Case study 0001: PR-center architecture drift

## Case identity

- Case: `AG-DRIFT-001`
- Repository: Agent Governance Starter Kit
- Observed period: 2026-07-13 through 2026-08-02
- Classification: architecture and product-boundary drift
- Finding semantics: deterministic history plus advisory interpretation
- Current decision authority: ADR-0009

## Why this case matters

AgentGov was created from AI Radar governance patterns for controlling how a
coding agent understands requirements, recovers architecture context, stays
inside an approved development slice, verifies its work, and hands decisions
back to a human. The original requirement did not change.

The implementation nevertheless became strongest at repository inspection,
consumer CI, upgrade review, and Draft PR delivery. Each individual slice was
bounded, tested, and useful, but the accumulated product emphasis moved from
governing development to reporting and distributing governance after code had
reached GitHub.

This is a concrete example of architecture drift that passing tests and safe
PR automation could not detect.

## Evidence boundary

The commit history, dated development logs, ADRs, extraction map, implemented
commands, and test suite provide deterministic evidence of what was added and
when. They do not objectively prove the motivation for each decision or that a
different sequence would have produced a better product.

The conclusion that supporting delivery work displaced the product core is an
`ADVISORY` architecture judgment. It is supported by the sequence below and
was accepted by the human product owner on 2026-08-02. It must not be emitted
as a deterministic failure merely because PR or CI functionality exists.

## Original requirement

The initial repository positioned AgentGov as a repository-native framework
that defines how coding agents operate, how AI-assisted changes are verified,
and where human approval remains required. Its reusable AI Radar sources
included the constitution, architecture memory, context-first review, bounded
development slices, evidence readiness, and explicit authority boundaries.

The intended responsibility chain was development-time governance:

```text
Requirement admission
  -> Architecture grounding
  -> Bounded coding-agent implementation
  -> Fresh development verification
  -> Completion reconciliation
  -> Independent PR/CI replay
```

## Observed drift timeline

| Date | Repository evidence | Locally reasonable decision | Accumulated effect |
|---|---|---|---|
| 2026-07-13 | `1eb96bb` established the starter kit and AI Radar extraction map. | Begin with portable schemas, static checks, and reusable agent-protocol templates. | The development protocols were documented and structurally checked, but did not become the executable product loop. |
| 2026-07-23 | `71930b3` generalized AI capability contracts and created the repository-governance development plan. | Prioritize inventory, evidence, control mappings, and dependencies that can be validated deterministically. | The primary governed object shifted from the coding agent's current task to repository capability declarations. |
| 2026-07-24 | Taxi adoption exposed installation, path, command, and interpretation friction. | Fix observed adoption problems before expanding the governance model. | Product attention moved to getting AgentGov into a repository rather than governing work once it was there. |
| 2026-07-25 | Guided onboarding, release metadata, self-update, and refresh were implemented. | Make adoption and maintenance safe, repeatable, and human-controlled. | Distribution and lifecycle machinery became a large share of the implementation. |
| 2026-08-01 | Consumer CI, repository status, upgrade planning, and consumer upgrade review were added. | Run existing deterministic checks independently and remove the maintainer-as-bridge bottleneck. | GitHub push and PR became the most visible governance interaction. |
| 2026-08-02 | Draft PR writing, persona delivery, and benefit-monitor work were developed. | Deliver upgrades safely and make governance outcomes observable. | The delivery backstop was being treated as the next product-defining surface. |
| 2026-08-02 | AI Radar was revalidated at `3a9323cb2a9ef575da42d29fb17d330ef872afd3`; ADR-0009 was accepted. | Compare the implementation with the source governance responsibility model. | Development-time governance was restored as P0; PR/CI was retained as independent replay. |

## Drift mechanism

The drift was not one explicit decision to turn AgentGov into a PR product. It
was a sequence of substitutions:

```text
Govern the coding agent
  -> Validate governance artifacts
  -> Improve adoption of the validator
  -> Run the validator in CI
  -> Maintain CI through upgrade PRs
  -> Measure the PR delivery path
```

Four conditions allowed the substitutions to accumulate:

1. The original extraction preserved development protocols as templates, but
   the executable CLI centered on deterministic repository state.
2. The first external evidence cycle exposed adoption friction, so the next
   slices correctly addressed installation and distribution problems.
3. Static checks, CI, and exact workflow changes were easier to specify and
   test than requirement relevance or architecture sufficiency, which require
   advisory human judgment.
4. No durable invariant required the first governance interaction to occur
   before or during implementation. Local acceptance criteria could therefore
   pass while the overall product boundary moved.

## What existing controls caught—and missed

Existing controls successfully preserved important safety properties:

- deterministic and advisory findings remained distinct;
- repository, Git, merge, release, and deployment authority stayed bounded;
- tests, schema contracts, hash checks, and no-write behavior remained valid;
- AI Radar runtime code, data, infrastructure, and business rules were not
  copied.

They did not ask whether the sequence of delivered slices still advanced the
original product requirement. Green tests proved that the implemented PR and
CI machinery behaved as specified; they did not prove that it was the right
machinery to prioritize.

## Expected development-time finding

A useful AgentGov review should have separated facts from judgment.

Deterministic context could report:

- the admitted task and its declared parent requirement;
- referenced ADRs and product-boundary invariants;
- the files and product surfaces changed by the task;
- whether fresh verification evidence exists;
- how many consecutive admitted slices target supporting delivery surfaces.

The architecture conclusion should remain advisory:

> Recent slices primarily extend governance distribution, CI, and upgrade-PR
> delivery, while the declared product core is development-time coding-agent
> governance. Confirm whether supporting work is intentionally taking priority,
> narrow the slice, or restore the core development loop.

That advisory would not automatically block the work. It would force the
priority change to become an explicit human decision while correction was
still inexpensive.

## Contract implications

This case is the first acceptance scenario for the P0 development-time task
contract. The design must be capable of preserving, without pretending to
infer intent:

- a human-declared requirement or parent-objective reference;
- task goal, non-goals, smallest scope, risks, acceptance signals, approvals,
  and stop conditions;
- relevant architecture and invariant references;
- whether a task advances the product core or a supporting surface, when a
  human chooses to declare that relationship;
- actual changed paths and fresh validation evidence;
- unresolved architecture-drift advisory decisions at completion.

The scenario passes only when deterministic facts are reproducible, the drift
interpretation remains advisory, and PR/CI can replay the facts without
becoming a second governance model.

## Resolution

ADR-0009 makes development-time requirement, architecture, and code governance
the primary product boundary. The active plan now prioritizes the task
contract, architecture-context selection, changed-file comparison, fresh
verification, and completion reconciliation. Existing PR/CI and upgrade
automation remain useful supporting infrastructure and regression-protected
backstops.

This case is not closed merely because the documents were corrected. Closure
requires the P0 task contract to exercise this scenario and surface the
deterministic evidence plus advisory architecture judgment before PR creation.
