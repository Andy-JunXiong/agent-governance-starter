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

## Host-side generation

`ReferenceTaskProposalAdapter` now supplies the missing host contract seam for
ordinary-language requests. A host provides a replaceable
`HostTaskProposalMaterializer`; that materializer sees the request once and
returns only `TaskProposalDraft`, a small normalized description of the task.
The Adapter, rather than the materializer, creates the proposal ID, Coding
Agent source identity, low-risk classification, privacy declarations, and
denied authority. It then calls the existing read-only admission planner.

The resulting `TaskProposalPreparation` contains the same
`TaskAdmissionPlan` used below and reports one host-materializer invocation,
zero AgentGov model calls, zero AgentGov network calls, no raw request in the
result or Core input, no repository mutation, and no granted authority. It does
not expose an apply method. Hosts must continue through the existing human
review and admission boundary.

The standalone reference materializer remains a protocol exercised by an
offline fixture. Development Adapter `1.3.0` now adds the first production-host
binding for Codex: the current Codex Agent materializes only the normalized
`TaskProposalDraft` fields through `agentgov_task_proposal_review`; AgentGov
still performs no model or network call. Static code can validate the
normalized contract but cannot prove semantic fidelity, so Codex presents the
exact resulting plan through native MCP form elicitation before any write.

Development Adapter `1.5.0` narrows that native input relative to the generic
draft: the Codex Agent no longer supplies `owner`. The Adapter injects the
canonical `Human product owner` role into the exact plan, where the existing
task builder uses it for both `owner` and `decided_by`. The generic proposal
contract, reference materializer, and terminal recovery path continue to carry
an explicit accountable owner because those non-native paths have separate
operator-attestation boundaries.

## Codex native review

When Codex negotiates MCP form elicitation, the foreground Adapter advertises
`agentgov_task_proposal_review` as a sixth tool. The tool input deliberately
omits raw conversation, repository identity, proposal identity, privacy and
authority declarations, the accountable-owner identity, and the decision. The
Adapter binds the local Git root, adds those invariant fields and the canonical
`Human product owner` role, builds the existing read-only admission plan, and
sends the complete bounded plan back to Codex with three choices: admit the
exact task, request changes, or reject.

Triggering is scoped to the exact requested repository change. A
human-admitted task counts only when its requirement, goal, scope, and
acceptance signals match and authorize that change. An unrelated,
measurement-only, or differently scoped admitted task does not bypass native
proposal review. Read-only work does not trigger proposal review. This is
host guidance: deterministic validation protects the published wording and
contracts but cannot force a model to select the tool.

Only an MCP response with `action=accept` and `decision=admit`, bound to that
elicitation request, may exclusively create the planned task file. Request
changes, reject, decline, cancel, malformed responses, interruption, missing
client capability, stale digests, and target races write nothing. Ordinary MCP
tool permission is not task admission. Admission still does not start a
session or authorize implementation, scope expansion, Git, release, or
deployment. Clients without form elicitation retain the original five
read-only governance tools and use the terminal recovery flow when needed.
An Agent-supplied `owner` is an unsupported native input and fails before the
form or any write. Native form mediation supports attribution to the human
product-owner role; it does not cryptographically authenticate the individual
operator or their account.

The repository initializer now creates a tracked
`governance/tasks/.gitkeep`. It is an inert directory bootstrap, not a task,
decision, or authority record. Its presence lets the first proposal build a
read-only plan while preserving the existing rule that admission creates only
the exact reviewed JSON file and never creates or follows an unsafe parent.
Repositories initialized before this correction need a reviewed adoption
update that creates the real directory before native proposal review can run.

The tool returns the vendor-neutral
`agentgov.task-proposal-review-result` contract. MCP clients may attach
protocol extension fields to the elicitation result; the Adapter ignores those
fields, never returns them, and still requires the exact action/content
decision shape before any write.

This deterministic behavior now also has installed-runtime protocol evidence,
including extension compatibility, exclusive admission, and zero-write failure
paths. The later matching-task trigger clarification is now installed and its
server/tool metadata plus capability-gated six/five-tool discovery match the
reviewed source. Project configuration remained unchanged. In one later
authorized Codex replay, the exact proposal tool started once; the turn
completed without an AgentGov form request. It supplied no human decision and created no task or
implementation. Two local no-model direct App Server calls with the same valid
arguments then parsed the Adapter form and returned zero-write `decline` because no
active turn hosted it. The retained replay summary cannot distinguish a
structured pre-form error from live forwarding or presentation behavior. Live
semantic quality and any later replay remain separate human-controlled
follow-up questions. The selected test-only
correction now records completion count/status, explicit unknown completion,
and a bounded allow-list of AgentGov error fields without raw error or tool
payloads. It cannot change the already discarded historical evidence.

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

This separation lets every host reuse the same Core contract. Codex now uses
MCP form elicitation for the equivalent bounded decision without adding
vendor-specific fields to Core; other hosts may supply their own trusted
interaction. Current Codex Hooks remain context-only for custom task decisions,
so they do not silently invoke either admission path.

## Privacy boundary

The proposal input is transiently parsed and the admission plan contains only
the normalized proposal. The created task contains the normalized requirement,
scope, acceptance, validation, risks, assumptions, and unknowns. AgentGov does
not add a raw prompt, transcript, response, source body, model identity,
credential, or host path to the task.

Adapters and their host materializers are responsible for producing the
normalized proposal without copying raw conversation content into free-text
summary fields. The reference Adapter does not retain the request and does not
pass it to the Core planner. The content-boundary flags make that responsibility
explicit; they are a contract assertion, not a claim that static code can infer
whether two pieces of prose are semantically equivalent.
