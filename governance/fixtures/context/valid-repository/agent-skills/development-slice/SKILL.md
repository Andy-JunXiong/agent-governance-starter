---
name: development-slice
description: Deliver one bounded fixture change. Use when a task is admitted. Do not use for incidents.
triggers: ["task.admitted"]
non_triggers: ["task.draft", "task.paused"]
applies_to: ["development_task"]
---

# Development Slice

## Goal
Deliver one bounded change.

## Required context
Read the admitted task.

## Inputs
Use selected governance.

## Workflow
1. Implement the smallest change.

## Required checks
Run the declared command.

## Stop conditions
Stop on scope conflict.

## Human escalation
Return unresolved decisions.

## Expected output
Report the result and evidence.
