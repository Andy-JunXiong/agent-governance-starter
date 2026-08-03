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
  -> Bounded Implementation
  -> AI Capability Governance
  -> Reviewable Artifacts
  -> Development Verification
  -> Completion Reconciliation
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

### Architecture memory

Records durable decisions and invariants so an agent can recover design intent
instead of inferring it only from current code. ADRs explain tradeoffs;
invariants identify constraints that ordinary feature work must preserve.

### Agent operating protocols

Provide scenario-specific development and operations procedures. They remain
separate from product runtime prompts and should state triggers, non-triggers,
required context, checks, stop conditions, and expected output.

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

Governance Inventory is the identity authority for configured capability
control mappings, evidence claims, and explicit capability dependencies.
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
           -> Reconcile -> Human Decision -> PR/CI Replay -> Observe -> Learn
```

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
