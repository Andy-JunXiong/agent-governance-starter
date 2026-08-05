---
name: requirement-admission
description: Turn a requested coding task into a human-owned, bounded development decision before meaningful implementation. Use when a feature, fix, refactor, or governance change is requested but has not been admitted. Do not use after admission or to approve work on the human's behalf.
triggers: ["task.requested"]
non_triggers: ["task.admitted", "task.paused"]
applies_to: ["development_task"]
---

# Requirement Admission

## Goal

Produce the smallest human-owned task decision that is clear enough to admit,
revise, or reject before meaningful implementation begins.

## Required context

- Read the repository instructions and the directly relevant requirement,
  product, architecture, and status sources.
- Preserve the distinction between an observed problem, a proposed solution,
  and the accountable human's decision.
- Treat semantic value, priority, and trade-off judgments as advisory.

## Inputs

- The requested outcome and why now.
- Evidence of the current problem or opportunity.
- Candidate scope, non-goals, acceptance signals, risks, and validation.

## Workflow

1. Restate the concrete problem separately from the requested solution.
2. Ask why now and identify the evidence supporting priority and expected
   benefit.
3. Define the smallest coherent slice, its non-goals, affected paths,
   acceptance signals, validation commands, and stop conditions.
4. Surface material alternatives, risks, and trade-offs without presenting an
   advisory preference as fact.
5. Ask the accountable human to restate or explicitly accept durable
   agent-shaped decisions so the rationale remains human-owned.
6. Return exactly one recommendation: `draft`, `admit`, `revise`, or `no-go`.
   Only the accountable human may change the task to admitted.
7. Do not begin implementation while the task remains requested or draft.

## Required checks

- Goal, non-goals, scope, acceptance, validation, risk, and authority are
  explicit and mutually consistent.
- Referenced repository paths exist and no secret, credential, or private data
  is requested.
- High-impact or materially ambiguous decisions have named human ownership.

## Stop conditions

Stop when intent is materially ambiguous, evidence is missing, the smallest
coherent slice cannot be bounded, required authority is absent, or the change
would import project-specific policy into a portable contract.

## Human escalation

Present the unresolved decision, evidence, alternatives, trade-offs, and the
smallest question the accountable human must answer. Never self-admit a task.

## Expected output

Report the recommended state, problem and why-now evidence, proposed slice,
non-goals, acceptance and validation, risks and trade-offs, human owner, and
the exact decision needed before implementation.
