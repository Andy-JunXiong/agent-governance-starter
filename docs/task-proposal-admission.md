# Coding-agent task proposal and human admission

Development source provides a vendor-neutral boundary between a user's
natural-language request, a Coding Agent's interpretation, and AgentGov's
authoritative task contract.

This is a review fallback and Adapter integration surface, not a universal
per-request gate. Risk-based routing may observe no-write work, reuse an exact
active task, or admit a bounded proposal through clean standing human policy
without invoking `ADMIT`. A user should not have to write this JSON by hand. A Codex,
Claude Code, IDE, or other Adapter may prepare the strict proposal, but the
proposing agent cannot admit it.

## Contracts

`agentgov.task-proposal` 1.0 contains only a normalized task identity, title,
requirement summary, repository-relative scope, acceptance signals, validation
commands, low-risk declaration, accountable owner, assumptions, and unknowns.
It also declares that the envelope contains no raw prompt, transcript, source
content, credentials, or absolute paths and grants no authority.

The schema is strict. Unknown fields, unsafe paths, sensitive assignments,
host-local paths, non-low risk, missing validation, or any true authority flag
fail before a plan exists. Static validation cannot prove that a free-text
summary perfectly represents the user's intent; human review remains the
semantic gate.

See [risk-based admission routing](admission-routing.md) for the preceding
classification and zero-interruption paths. This document applies when routing
selects `human_review` or no standing policy is available.

For a planned low-risk `human_review`, AgentGov may now present the exact task
through `agentgov.human-decision-prompt` 1.0 and accept one structured
approve/change/reject selection. See
[proactive minimal-input human decisions](human-decision-prompts.md). The
special-word flow below remains the terminal recovery fallback.

`agentgov.task-admission-plan` 1.0 is the read-only result. It contains the
normalized proposal, stable proposal digest, only planned target, exact final
`agentgov.development-task` document, stable task digest, and denied authority.
Assumptions and unknowns are preserved as reviewed risk items in the resulting
compact task instead of disappearing after admission.

## Preview and admission

Preview a Coding Agent proposal without writing:

```powershell
agentgov propose task path/to/proposal.json --repository . --dry-run
```

Use `--format json` only with `--dry-run` for an Adapter-readable plan. The
preview does not admit the task and does not authorize a later write.

Rerunning without `--dry-run` prints the same complete plan. Only exact
`ADMIT` entered through a real interactive terminal creates the task. Piped
stdin, CI, a command flag, environment data, ordinary non-interactive Coding
Agent execution, and inferred intent cannot confirm it.

This is an operator-attestation fallback, not cryptographic proof of human
identity. A host that gives an agent control of an interactive terminal could
weaken that attribution. A genuinely authenticated human decision still needs
a trusted host interaction and decision callback; AgentGov records that as a
remaining integration need instead of overstating the fallback.

Admission is exclusive create. AgentGov rechecks proposal and task digests,
the existing task contract, repository-relative paths, real parent
directories (including every ancestor symlink), and target nonexistence
immediately before writing. A changed plan or raced target fails without
overwrite.

The apply step creates only `governance/tasks/<task-id>.json`. It does not:

- create `.agentgov` session state or lifecycle events;
- start implementation or execute validation commands;
- expand scope or approve an exception;
- authorize commit, push, merge, publication, deployment, or release.

Starting the admitted task remains a separate reviewed action:

```powershell
agentgov govern start governance/tasks/<task-id>.json --repository . --dry-run
```

This separation lets every host reuse the same Core contract. A future Adapter
with a genuine native decision callback can present and record the equivalent
human decision without adding vendor-specific fields to Core. Current Codex
Hooks remain context-only for custom task decisions, so they do not silently
invoke this terminal fallback.

## Privacy boundary

The proposal input is transiently parsed and the admission plan contains only
the normalized proposal. The created task contains the normalized requirement,
scope, acceptance, validation, risks, assumptions, and unknowns. AgentGov does
not add a raw prompt, transcript, response, source body, model identity,
credential, or host path to the task.

Adapters are responsible for producing the normalized proposal without copying
raw conversation content into free-text summary fields. The content-boundary
flags make that responsibility explicit; they are a contract assertion, not a
claim that static code can infer whether two pieces of prose are semantically
equivalent.
