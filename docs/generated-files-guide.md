# Generated files guide

The scaffold is a reviewable starting point, not a completed policy. This guide explains what a human should decide in each generated area.

## AGENTS.md

Define repository scope, authority boundaries, required validation, stop conditions, and handoff expectations. Replace placeholders with repository-specific facts. If CLAUDE.md, Copilot instructions, Cursor rules, or similar files exist, document which file is authoritative and how conflicts are resolved; do not mechanically concatenate their text.

## docs/adr/TEMPLATE.md

Use the template for consequential and durable decisions. Record context, options, decision, consequences, verification, and follow-up. Do not rewrite historical decisions to match a later outcome.

## docs/adr/INVARIANTS.md

Record properties that must remain true, their scope, responsible owner, enforcement mechanism, verification command, and exception authority. Only claim deterministic enforcement when an actual deterministic check exists.

## prompt-governance/capabilities

Replace the example manifest with one bounded capability at a time. Confirm:

- `purpose`, `triggers`, and `not_for` describe real behavior;
- input and output schemas exist inside the repository;
- `called_by` and provenance source paths resolve;
- owner and risk level are accountable and current;
- high or critical risk requires human review;
- evaluation readiness matches available evidence.

Do not use a capability manifest as proof that the implementation is correct.

## prompt-governance/schemas

Describe the structural input and output contract. Keep objects strict where appropriate, avoid undocumented fields, and version breaking changes. Schema validity does not establish semantic quality.

## prompt-governance/sources

Keep the actual repository source authoritative. Generated review artifacts contain hashes and references, not copied private source content. Never add credentials, production data, or secret-like examples.

## evaluation

Start with an honest early readiness state. Add reviewed seed cases, golden examples, and failure cases as evidence becomes available. Production-derived cases must be sanitized. `baseline_ready` and `regression_ready` require the evidence and human approval declared by the contract.

The starter validates readiness structure; it does not execute models or judge model-output quality.

## agent-skills

Adapt protocols only when their triggers, non-use conditions, workflow, safety boundaries, escalation, and handoff contract remain explicit. Keep them portable and free from credentials or project-specific infrastructure unless the repository deliberately owns that specialization.

## prompt-governance/artifacts

Create artifacts with the explicit export command after reviewing a valid capability:

```powershell
agentgov export capability prompt-governance/capabilities/example.json --repository .
```

Artifacts are deterministic review snapshots. A matching hash proves declared content has not changed; it does not prove that the content is correct or approved.

## Before accepting the change

Run:

```powershell
agentgov check repository .
agentgov report repository . --output governance-report.md
```

Then review every WARN and ADVISORY. A successful process exit does not authorize merge, publication, release, or deployment.
