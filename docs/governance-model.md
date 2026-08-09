---
layout: reference
title: Governance model
source_path: docs/governance-model.md
---

# Governance model

## Problem

Coding agents can change software faster than a team can review the intent,
risk, and downstream consequences of every change. Existing coding tools,
CI/CD systems, pull-request workflows, and model-evaluation products each cover
part of that lifecycle. This project focuses on the repository-level contracts
that connect those parts.

## Model

The starter kit uses the following governance chain:

```text
Constitution
  -> Requirement Admission
  -> Architecture Memory
  -> Agent Operating Protocols
  -> Automatic Session Orchestration
  -> Bounded Implementation
  -> AI Capability Governance
  -> Reviewable Artifacts
  -> Development Verification
  -> Completion Reconciliation
  -> Protection and Benefit Dashboard
  -> Human Approval
  -> PR/CI Independent Replay
  -> Monitoring and Learning
```

These stages describe responsibilities, not a requirement to install nine
separate systems.

### Constitution

Defines repository scope, permissions, prohibited actions, approval boundaries,
validation requirements, and escalation rules. `AGENTS.md` is the default
portable artifact.

### Requirement admission

Turns a concrete development request into an explicit goal, non-goals,
smallest scope, risks, acceptance signals, stop conditions, and human decision
boundaries. Natural-language intent remains human-owned; AgentGov may preserve
and check the declared contract but must not claim that it objectively inferred
the user's meaning.

Development source now accepts `agentgov.task-proposal` 1.0 as a strict,
non-authoritative Coding Agent interpretation. It rejects raw-prompt fields and
unsafe or authoritative claims, previews the exact compact task, and requires
an explicit human decision before exclusive task creation. A planned low-risk
review uses a digest-bound proactive single-select prompt; the exact
interactive `ADMIT` flow remains a recovery fallback. Codex development source
can instead bind the exact plan to one native MCP form decision; only explicit
admission writes, and ordinary tool permission does not count. Admission and session
start remain separate. A reference host Adapter now invokes one replaceable
semantic materializer for ordinary request text and passes only its normalized
draft into this existing preview path. The offline fixture proves the contract
boundary. Codex development source separately binds the current Agent and its
native MCP form; it does not prove live semantic fidelity or another host.

Development source also distinguishes observation from admission through
`agentgov.work-request`, `agentgov.admission-routing-policy`, and
`agentgov.admission-route` 1.0. No-write work and exact active-task iteration
are not task-admission events. A bounded low-risk task may be admitted without
a new interruption only when an admitted, tracked, clean human-owned policy
already delegates its scope and validation envelope. Material characteristics
always route to review. Git state and owner fields are auditable attestations,
not cryptographic proof of semantic correctness or human identity.

`agentgov.human-decision-prompt` and `agentgov.human-decision-result` 1.0
separate display from choice. The prompt proactively explains why a decision
is needed and recommends a safe option without selecting it. A capable host
returns one human selection bound to the exact prompt, source, option, and
predeclared transition; no free-text rationale or magic word is required.

When meaning has not converged, `agentgov.alignment-context` and the
clarification-dialogue contracts keep the current center and observed drift
separate. The host asks one natural-language question at a time and Core keeps
only normalized rolling summaries. Business, requirement, and architecture
drift remain advisory. Clarification turns are not approval events and have no
semantic turn cap. Only after material unknowns are resolved and option effects
are stable does the existing human-decision contract record one re-centering
choice. That structured result does not itself edit an ADR, admit a task, or
grant implementation authority.

### Architecture memory

Records durable decisions and invariants so an agent can recover design intent
instead of inferring it only from current code. ADRs explain tradeoffs;
invariants identify constraints that ordinary feature work must preserve.

### Agent operating protocols

Provide scenario-specific development and operations procedures. They remain
separate from product runtime prompts and should state triggers, non-triggers,
required context, checks, stop conditions, and expected output.

### Automatic session orchestration

Coordinates the existing task, context, scope, evidence, completion, Monitor,
and handoff primitives from vendor-neutral coding-agent events. Ordinary users
should not poll workflow state or compose the internal command sequence.
Automatic behavior is limited to declared repository observation,
deterministic checks, pre-approved validation, privacy-bounded local evidence,
Dashboard refresh, and feedback to the coding agent. Material scope,
architecture, exception, semantic, and consequential authority remain human
decisions.

The first product slice is an explicit foreground or adapter-owned session,
not a hidden daemon. Codex, Claude Code, IDE, and other integrations are
optional adapters rather than Core governance authority.

Development source now contains the first internal contracts for this stage:
the read-only `agentgov.development-state` 1.0 lifecycle projection and the
strict `agentgov.development-trigger` 1.0 adapter envelope. It also implements
one explicit `agentgov.foreground-cycle` 1.0 through `agentgov dev`: the
minimal reference adapter invokes admitted scope/completion cores and refreshes
the Dashboard. Development source now also accepts privacy-bounded live JSONL
coding-agent events in one foreground process and returns bounded task and
completion cards. The first packaged Codex lifecycle-hook Adapter maps reviewed
project callbacks while discarding sensitive host fields before event
construction. Vendor-neutral capability and interaction-request contracts now
separate a displayed human gate from an applied decision. Codex's normal native
tool permission remains host-managed, while custom task/scope/completion gates
are context-only and unrecorded. Other host adapters and a real custom-decision
surface are not yet implemented. See `docs/development-automation-contracts.md`.

### Bounded implementation

Keeps the coding agent inside the admitted requirement and architecture
boundary while it edits, tests, diagnoses failures, and iterates. A closed loop
grants responsibility for safe iteration inside the approved scope, not wider
autonomy, Git authority, or permission to invent new architecture.

### AI capability governance

Treats deterministic, model, prompt, or hybrid behavior as a versioned
capability with identity, purpose, input/output contracts, call sites, risk,
implementation mode, decision authority, autonomy, human-review requirements,
provenance, and evaluation readiness.

Governance Inventory is the capability-identity authority for configured
control mappings, evaluation bundles, review artifacts, and explicit
capability dependencies.
Dependency declarations validate graph identity and cycles. Readiness is
ordered only for an edge that deliberately declares `minimum_readiness`; no
threshold is inferred from different readiness labels.

### Reviewable artifacts

Expose capability metadata, schemas, examples, failure cases, source hashes,
and quality notes in forms that humans and automated checks can inspect.

### Development verification

Separate deterministic facts from judgment:

- structural, schema, metadata, and drift checks may produce hard pass/fail;
- incomplete evidence should produce an explicit readiness state;
- architecture sufficiency and policy quality may require advisory review.

Development verification also compares actual changed files and fresh evidence
with the admitted task. It should surface drift before a pull request exists.

### Completion reconciliation

Checks the task, architecture decisions, implementation, tests, evaluation
evidence, and governance memory for scoped drift before the coding agent claims
completion. It proposes follow-up when durable decisions changed; it does not
automatically rewrite core governance files.

### Protection and benefit Dashboard

Turns validated events into automatically refreshed Overview, Live Sessions,
Protection Events, Task Detail, Benefit, and Learning views. The Dashboard
protects users by making scope, authority, stale evidence, and unresolved
decisions visible, and protects coding agents by making bounded intent,
relevant architecture, repeated attempts, environmental failures, and
responsibility limits explicit.

Benefit reporting separates observed facts, reproduced comparisons with
documented denominators, supported inference, attributed human feedback, and
unknowns. It does not infer causal prevention, ROI, governance completeness, or
a combined score from event counts.

### Human approval

Preserves explicit human control for high-risk decisions. A starter kit may
verify that an approval policy exists; it cannot prove that a reviewer made a
sound decision merely by finding text in a repository.

### PR/CI independent replay

Reproduces deterministic development facts outside the coding agent's local
session, prevents silent bypass, and preserves durable review evidence. PR and
CI are a final backstop rather than AgentGov's primary product interaction.

### Monitoring and learning

Uses review outcomes and incidents to improve policies and checks. Runtime
monitoring platforms are integrations, not part of the repository-native core.

## Finding semantics

The CLI reporting model emits:

- `PASS`: a required, deterministic condition is satisfied;
- `WARN`: a deterministic gap exists but policy does not make it blocking;
- `FAIL`: a required, deterministic condition is not satisfied;
- `ADVISORY`: human judgment is required before assigning compliance.

The repository report does not emit a separate `NOT_APPLICABLE` finding
status. Capability control mappings can declare
`applicability: not_applicable` with a required rationale; deterministic
validation of that declaration produces a mapping `PASS`, not evidence that
the rationale is semantically justified.

The project does not calculate a single governance coverage percentage.
Control applicability is explicit, but a documented denominator, weighting
model, and semantic evidence rules have not been defined.

Dependency completeness is also advisory. A valid acyclic graph proves only
that declared edges are internally consistent; it does not prove that every
runtime or organizational relationship was discovered.

## Coding-agent development loop

```text
Understand -> Admit -> Ground -> Bound -> Implement -> Verify
           -> Reconcile -> Protect/Explain -> Human Decision
           -> PR/CI Replay -> Observe -> Learn
```

The primary product automates this loop after activation. The implemented
`next`, `govern start/check/finish`, Monitor, and handoff commands remain
headless and recovery primitives while the automatic coordinator and adapter
surface are implemented.

Not every repository needs every stage at the same maturity. Small changes may
use a compact task contract, while architecture or high-risk work needs deeper
context and approval. Reports should show readiness and missing evidence rather
than treating unconfigured controls as successful.

## Architecture-drift learning case

The starter kit's own [PR-center architecture drift](case-studies/0001-pr-center-architecture-drift.md)
is the first acceptance scenario for this loop. It shows how individually
bounded, tested work on adoption, CI, and upgrade delivery accumulated until a
supporting surface displaced development-time governance as the effective
product center.

Commit history, declared task references, changed paths, and validation
evidence are deterministic inputs. Whether those facts amount to architecture
drift remains an advisory human judgment. A green test suite proves that the
implemented behavior satisfies its contracts; it does not prove that the
implementation still advances the original requirement.

## Capability-authority pressure test

The domain-neutral [capability and authority pressure test](case-studies/0002-capability-authority-pressure-test.md)
checks a second boundary: an available tool or transport permission is not
authority to apply a consequential transition. Current contracts can bind
state, evidence, exact decisions, and human ownership for the development
transitions they implement, but AgentGov does not claim to intercept unrelated
host tools or act as a runtime security boundary.

The same case treats an outcome as possible evidence for a learning candidate,
not automatic admission of changed behavior. A future behavior or authority
change would require its own validation and admitted, reconstructable
transition. This is a later architecture validation scenario, not a new Core
runtime-learning feature or roadmap priority.

## Report integration boundary

One repository check produces one ordered findings model. Terminal output,
Markdown, and JSON serialize that same model; integrations must not reconstruct
governance meaning by parsing Markdown. The versioned JSON contract is defined
by [the repository report schema](../schemas/repository-report.schema.json).

Contract version `1.0` exposes repository identity, status counts, findings,
known gaps, recommended actions, and scope limitations. It intentionally omits
timestamps, scores, and governance coverage percentages. Consuming the JSON
does not turn deterministic file-presence checks into quality judgments and
does not grant approval to merge, publish, release, or deploy.
