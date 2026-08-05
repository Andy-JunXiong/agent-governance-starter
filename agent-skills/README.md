# Agent operating protocols

Reusable coding-agent protocols live under `agent-skills/<name>/SKILL.md`.
They are development-time instructions and remain separate from product
runtime prompts.

Each protocol uses YAML frontmatter with required `name` and `description`.
Routable protocols also own structured `triggers`, `non_triggers`, and
`applies_to` arrays in that same frontmatter. Arrays use inline JSON syntax so
the zero-dependency parser has one deterministic representation. No Registry
mapping file may redefine them. The body must contain these sections:

- `Goal`
- `Required context`
- `Inputs`
- `Workflow`
- `Required checks`
- `Stop conditions`
- `Human escalation`
- `Expected output`

The starter set contains:

- `requirement-admission`: human-owned problem, value, scope, trade-off, and
  admission decision before meaningful implementation;
- `context-first-review`: repository-grounded review of architecture,
  migration, prompt, and cross-module proposals;
- `development-slice`: bounded planning, implementation, validation, and
  handoff;
- `action-loop-stagnation`: advisory detection of repeated approaches,
  missing verification, and false completion during implementation;
- `reconcile-invariants`: scoped completion-time alignment across the task,
  architecture, implementation, evidence, and governance memory;
- `incident-attribution`: evidence-based collaboration learning and
  proportionate corrective decisions;
- `incident-response`: evidence-first operational triage and narrow recovery.

The first five protocols govern the development loop. Pull requests and CI
remain an independent deterministic backstop, not the point where governance
begins.

Validate the complete directory with:

```powershell
agentgov check agent-skills agent-skills
```
