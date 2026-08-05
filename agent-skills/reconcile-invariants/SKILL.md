---
name: reconcile-invariants
description: Reconcile an admitted task, scoped architecture decisions, implementation, and fresh evidence before completion. Use when completion or handoff is requested. Do not use to scan the whole repository or automatically rewrite governance memory.
triggers: ["completion.requested"]
non_triggers: ["task.requested", "task.draft"]
applies_to: ["development_task"]
---

# Reconcile Invariants

## Goal

Perform scoped reconciliation before completion so drift among the task,
architecture, implementation, evidence, and governance memory remains visible
to the accountable human.

## Required context

- Read the admitted task and only its selected constitution, ADR, invariant,
  capability, control, dependency, and Skill references.
- Inspect the final change set and fresh validation evidence.
- Preserve observed facts, supported inferences, review judgments, and
  unresolved unknowns as separate categories.

## Inputs

- Task identity, goal, non-goals, scope, architecture references, acceptance
  signals, and stop conditions.
- Final changed paths and fresh verification evidence.
- Any proposed durable governance update.

## Workflow

1. Build a scoped reconciliation table from each applicable task and
   architecture obligation to implementation and evidence.
2. Classify every row as aligned, drift, unknown, or not applicable, with a
   reason and source reference.
3. Identify changes that imply a durable decision not represented in the
   selected governance memory.
4. For each governance-memory mismatch, produce a proposed diff for human
   review. Do not automatically rewrite an ADR, invariant, task, capability,
   control, dependency, or Skill.
5. Separate deterministic evidence gaps from advisory semantic judgments.
6. Return aligned, drift, or pending-human-decision; never convert fresh tests
   into proof of requirement or architecture correctness.

## Required checks

- Every applicable acceptance signal and scoped invariant has implementation
  and evidence references or an explicit unknown.
- Changed paths remain inside admitted scope unless a human-approved exception
  is recorded.
- Proposed governance changes preserve source boundaries and authority.

## Stop conditions

Stop when fresh evidence is missing, selected governance sources conflict,
scope expanded without authority, or completion depends on an unresolved
semantic judgment.

## Human escalation

Present the exact drift, observed facts, supported inferences, review
judgments, unresolved unknowns, proposed diff, and the accountable decision.
Do not claim completion while a required decision remains pending.

## Expected output

Report the reconciliation state, scoped obligation table, deterministic gaps,
advisory drift judgments, proposed diffs, evidence limits, and pending human
decisions.
