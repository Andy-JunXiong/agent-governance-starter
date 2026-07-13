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
  -> Architecture Memory
  -> Agent Operating Protocols
  -> Prompt Capability Governance
  -> Reviewable Artifacts
  -> Evaluation and Policy Checks
  -> Human Approval
  -> Controlled Change
  -> Monitoring and Learning
```

These stages describe responsibilities, not a requirement to install nine
separate systems.

### Constitution

Defines repository scope, permissions, prohibited actions, approval boundaries,
validation requirements, and escalation rules. `AGENTS.md` is the default
portable artifact.

### Architecture memory

Records durable decisions and invariants so an agent can recover design intent
instead of inferring it only from current code. ADRs explain tradeoffs;
invariants identify constraints that ordinary feature work must preserve.

### Agent operating protocols

Provide scenario-specific development and operations procedures. They remain
separate from product runtime prompts and should state triggers, non-triggers,
required context, checks, stop conditions, and expected output.

### Prompt capability governance

Treats a prompt-backed behavior as a versioned capability with an identity,
purpose, input/output contract, call sites, risk classification, model route,
human-review requirement, provenance, and evaluation readiness.

### Reviewable artifacts

Expose capability metadata, schemas, examples, failure cases, source hashes,
and quality notes in forms that humans and automated checks can inspect.

### Evaluation and policy checks

Separate deterministic facts from judgment:

- structural, schema, metadata, and drift checks may produce hard pass/fail;
- incomplete evidence should produce an explicit readiness state;
- architecture sufficiency and policy quality may require advisory review.

### Human approval

Preserves explicit human control for high-risk decisions. A starter kit may
verify that an approval policy exists; it cannot prove that a reviewer made a
sound decision merely by finding text in a repository.

### Controlled change

Connects proposal, context review, invariant review, implementation, tests,
evaluation, approval, merge or release, and post-change observation.

### Monitoring and learning

Uses review outcomes and incidents to improve policies and checks. Runtime
monitoring platforms are integrations, not part of the v0.1 core.

## Finding semantics

The initial reporting model uses:

- `PASS`: a required, deterministic condition is satisfied;
- `WARN`: a deterministic gap exists but policy does not make it blocking;
- `FAIL`: a required, deterministic condition is not satisfied;
- `ADVISORY`: human judgment is required before assigning compliance;
- `NOT_APPLICABLE`: the control does not apply to this repository.

The project will not calculate a single governance coverage percentage until
control applicability, weighting, and evidence rules are specified and tested.

## Controlled-upgrade loop

```text
Understand -> Admit -> Design -> Implement -> Verify
           -> Evaluate -> Approve -> Release -> Observe -> Learn
```

Not every repository needs every stage at the same maturity. Reports should
show readiness and missing evidence rather than treating unconfigured controls
as successful.
