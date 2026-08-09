# Generated files guide

The scaffold is a reviewable starting point, not a completed policy. This guide explains what a human should decide in each generated area.

## AGENTS.md

Define repository scope, authority boundaries, required validation, stop conditions, and handoff expectations. Replace placeholders with repository-specific facts. The generated native-governance section tells capable Coding Agents when to use alignment, matching task admission, current-Agent self-review, and due drift review, and to fail closed when a required governance call fails. Matching admission requires a readable, validated `governance/tasks/*.json` record with a human admitted or approved decision; direct chat authorization and tool permission do not count, and every repository-changing task requires a distinct advisory review. Native self-review tools require a resolved alignment journey; a fully specified task without one must use and disclose a bounded current-Agent review instead of fabricating a journey handle. The tracked `governance/tasks/.gitkeep` creates only the safe parent directory required for the first proposal preview; it is not a task or an admission decision. Keep both surfaces current when adapting the repository. If CLAUDE.md, Copilot instructions, Cursor rules, or similar files exist, document which file is authoritative and how conflicts are resolved; do not mechanically concatenate their text.

## docs/adr/TEMPLATE.md

Use the template for consequential and durable decisions. Record context, options, decision, consequences, verification, and follow-up. Do not rewrite historical decisions to match a later outcome.

## docs/adr/INVARIANTS.md

Record properties that must remain true, their scope, responsible owner, enforcement mechanism, verification command, and exception authority. Only claim deterministic enforcement when an actual deterministic check exists.

## governance/capabilities

Replace the example manifest with one bounded capability at a time. Confirm:

- `purpose`, `triggers`, and `not_for` describe real behavior;
- input and output schemas exist inside the repository;
- `called_by` and provenance source paths resolve;
- owner and risk level are accountable and current;
- high or critical risk requires human review;
- evaluation readiness matches available evidence.

Do not use a capability manifest as proof that the implementation is correct.

## governance/inventory.json

Keep one accountable declaration for every canonical capability manifest and
record exclusions only when a real repository path and reason exist. Inventory
closure validates declared identity, ownership, and paths; it cannot prove
that every real capability was discovered.

## governance/controls

Adapt each capability's control objectives, applicability, enforcement mode,
evidence references, owner, and exception authority. A structurally valid
mapping does not prove that the control is effective or sufficient.

## governance/dependencies

Keep one declaration per Inventory capability. An empty `depends_on` array is
valid and preferable to an invented relationship. Add only known capability
edges; use `minimum_readiness` only when the owning team has deliberately set
that floor. The checker rejects orphan endpoints, self-dependencies, cycles,
and unmet explicit floors, but dependency completeness remains advisory.

## governance/contracts

Describe the structural input and output contract. Keep objects strict where appropriate, avoid undocumented fields, and version breaking changes. Schema validity does not establish semantic quality.

## governance/evidence

Keep the actual repository source authoritative. Generated review artifacts contain hashes and references, not copied private source content. Never add credentials, production data, or secret-like examples.

## evaluation

Start with an honest early readiness state. Add reviewed seed cases, golden examples, and failure cases as evidence becomes available. Production-derived cases must be sanitized. `baseline_ready` and `regression_ready` require the evidence and human approval declared by the contract.

The starter validates readiness structure; it does not execute models or judge model-output quality.

## agent-skills

Adapt protocols only when their triggers, non-use conditions, workflow, safety boundaries, escalation, and handoff contract remain explicit. Keep them portable and free from credentials or project-specific infrastructure unless the repository deliberately owns that specialization.

## governance/artifacts

Create artifacts with the explicit export command after reviewing a valid capability:

```powershell
agentgov export capability governance/capabilities/example.json --repository .
```

Artifacts are deterministic review snapshots. A matching hash proves declared content has not changed; it does not prove that the content is correct or approved.
The directory is an optional generated-output location, not a core onboarding
path, and `doctor` does not require it for a configured repository.

## Before accepting the change

Run:

```powershell
agentgov check repository .
agentgov report repository . --output governance-report.md
```

Then review every WARN and ADVISORY. A successful process exit does not authorize merge, publication, release, or deployment.
