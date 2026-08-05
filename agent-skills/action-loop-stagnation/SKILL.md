---
name: action-loop-stagnation
description: Detect repeated coding-agent approaches, missing verification, and false completion during an admitted development task. Use when attempts repeat without new evidence or a handoff is proposed before verification. Do not use as a mechanical runtime halt or as an incident-response substitute.
triggers: ["development.stagnation_suspected"]
non_triggers: ["task.requested", "task.draft", "incident.active"]
applies_to: ["development_task"]
---

# Action-loop Stagnation

## Goal

Interrupt an unproductive reasoning pattern with an advisory protocol before
repeated actions, missing evidence, or false completion cause wider drift.

## Required context

- Read the admitted task, selected architecture and invariants, current diff,
  validation contract, and the most recent attempts.
- Use only observed tool results and explicit agent reports; do not infer hidden
  reasoning or claim runtime telemetry that is unavailable.

## Inputs

- A failure packet containing the attempted action, hypothesis, result, and
  evidence for each relevant attempt.
- The expected verification oracle and current task boundary.
- Any proposed completion or handoff claim.

## Workflow

1. Normalize the recent attempts into a failure packet without deleting
   contradictory or unsuccessful evidence.
2. Compare hypotheses, actions, and results to identify repetition, missing
   verification, or a false completion claim.
3. Require a structurally different hypothesis tied to a falsifiable next
   check and the declared verification oracle.
4. If no materially new hypothesis or evidence exists, stop the action loop
   and request a human decision instead of repeating the approach.
5. Keep any proposed code change inside the admitted scope and re-run fresh
   verification before completion or handoff.
6. State explicitly that this protocol request is not a mechanical runtime
   halt and grants no new authority.

## Required checks

- Every diagnosis cites the corresponding attempt and observed result.
- The next hypothesis differs in structure, not only wording or command order.
- Completion is not reported without the task's verification oracle and fresh
  evidence.

## Stop conditions

Stop when attempts lack comparable evidence, the next action requires broader
scope or authority, the verification oracle is unavailable, or a structurally
different hypothesis cannot be stated.

## Human escalation

Provide the failure packet, repeated pattern, missing evidence, safest options,
and the precise scope, architecture, or priority decision required. Do not
silently continue or manufacture evidence.

## Expected output

Report the advisory stagnation finding, supporting attempts, false-completion
risk, structurally different hypothesis, verification oracle, stop decision,
and required human action.
