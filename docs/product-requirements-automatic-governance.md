---
layout: reference
title: "Automatic coding-agent governance product requirements"
source_path: docs/product-requirements-automatic-governance.md
---

# Automatic coding-agent governance product requirements

Status: approved product direction; not yet implemented as the primary user
experience.

Date: 2026-08-05

## Product outcome

AgentGov is an independent, general-purpose governance and protection layer
between a person and a coding agent. A user should continue to request work in
natural language through Codex, Claude Code, or another coding-agent surface.
AgentGov should automatically establish the governed session, provide relevant
repository context, observe implementation scope, run pre-approved checks,
reconcile fresh evidence, and update a Monitor and Dashboard.

The normal low-risk journey has at most three visible human interactions:

1. request the task through the coding agent;
2. confirm one concise goal, scope, validation, and authority card when policy
   requires confirmation;
3. review the completion and protection summary.

Users must not need to hand-author internal JSON, query workflow state, type
special words such as `START`, `HANDOFF`, or `REPLACE`, or manually compose
`next`, `govern start`, `govern check`, `govern finish`, Monitor, and handoff
commands. Those commands remain supported internal primitives and headless,
diagnostic, CI, and recovery interfaces.

## Primary user scenarios

### Enable AgentGov once

The user installs AgentGov or a coding-agent adapter and enables it for one
repository. AgentGov detects the project, existing governance sources, Git and
validation surfaces, previews any repository writes, and requests one bounded
confirmation. It preserves existing files and does not silently merge vendor
instructions.

### Request ordinary coding work

The user asks the coding agent for a concrete change. The adapter emits a
vendor-neutral task event. AgentGov drafts a compact goal, non-goals, file
scope, validation plan, risk, and relevant architecture context. A configured
low-risk policy may proceed with a visible notification; ambiguity, material
scope, or higher risk requires one concise human confirmation.

### Work inside the admitted boundary

AgentGov automatically observes committed-since-base, staged, unstaged,
renamed, deleted, and non-ignored untracked changes. It supplies selected
architecture and protocol context to the adapter, checks scope at useful
events, and updates local governance evidence without asking the user to poll
for status.

### Handle a protection event

Out-of-scope changes, requirement expansion, architecture conflict, repeated
failed approaches, stale evidence, unapproved commands, or requested external
authority create a clear protection event. The user chooses whether to narrow,
review an expansion or exception, continue, or stop. AgentGov does not infer
new authority from apparent relevance.

### Reconcile completion

When the coding agent requests completion, AgentGov automatically runs the
pre-approved validation set, binds it to the current task and Git snapshot,
checks freshness and scope, and produces a review card. Passing evidence does
not become semantic acceptance or permission to commit, merge, release, or
deploy.

### Observe and learn

The Dashboard updates automatically throughout the session. A reviewer can
inspect current work, protection events, task history, evidence limitations,
benefit observations, and candidate product improvements without reading raw
event JSON.

## Automatic behavior

The primary product automatically performs:

- repository and tool diagnosis after activation;
- task-event intake and session routing;
- task-relevant context selection;
- read-only Git and changed-path observation;
- deterministic scope and freshness checks;
- execution of repository-declared, pre-approved validation commands;
- privacy-bounded local event recording;
- Monitor and Dashboard refresh;
- feedback to the coding agent;
- notification of deterministic failures and advisory human decisions.
- periodic requirement, architecture, and functionality review reminders from
  one shared task-count/time cadence, without automatically deciding drift.

The development implementation includes the foreground orchestrator,
repository-state reference adapter, and a strict `agentgov dev --stream` JSONL
process transport. It handles activation, implementation-change scope checks,
completion-triggered pre-approved validation and reconciliation,
human-reviewed handoff, Dashboard refresh, and bounded task/scope/completion
cards.
The transport contains no prompt, source, host-path, task-identity,
changed-path, or authority field; trusted facts are derived locally. Packaged
host-specific integration now exists for Codex project hooks in development
source. A vendor-neutral host capability/request contract represents human
gates without applying decisions. Strict proactive prompt/result contracts now
let a capable host present one recommended single-select choice and return the
exact human selection without free text; the reference terminal path accepts
one number instead of a magic word. Development source now also supports a
vendor-neutral governed clarification dialogue before that final choice:
current center and advisory drift remain visible, each turn asks one
natural-language question, raw chat is not retained, and material unknowns
must be resolved before the resolution options become selectable. Codex
retains its native tool-permission
prompt, but current Hooks cannot record arbitrary custom task, scope, or
completion decisions. Generic production natural-language materializers for
additional hosts and cryptographically authenticated custom decision controls
remain open. The reference task-proposal materializer seam described below is
implemented. Development Codex Adapter `1.3.0` now adds the first
production-host materializer and native MCP form review path. Local
installation and protocol preflight pass; external live proof remains open.
The target remains an adapter-owned foreground experience, not a hidden daemon.

That clarification is now connected to the development-source foreground
transport. A Coding Agent Adapter sends only strict normalized alignment
context; the host sends strict normalized human clarification updates and the
final decision result. AgentGov automatically returns the next one-question
prompt or stable final choice. The dialogue is memory-only for the disclosed
stream and explicitly does not survive restart. Automatic host-side creation
of the normalized context from arbitrary natural-language chat remains an
Adapter responsibility and is not claimed by Core.

Development source now provides that responsibility as a replaceable reference
boundary: a host semantic materializer converts an ordinary request or answer
into a small normalized draft, and `ReferenceAlignmentAdapter` supplies the
strict envelope and drives the existing Core session. Its offline rehearsal
reaches one final single-select with zero user-authored structured records,
internal commands, or confirmation words and retains no raw conversation in
the Adapter journey. This is interaction and integration evidence, not a claim
that Core performs semantic inference or that a production host UI/model
integration is complete.

The same host-owned pattern now covers low-risk task proposals.
`ReferenceTaskProposalAdapter` invokes one replaceable
`HostTaskProposalMaterializer`, adds Adapter-owned proposal identity, privacy,
low-risk, and denied-authority fields, and produces the existing read-only
admission plan. Its offline fixture reaches the unchanged human admission path
without raw request data entering Core or any AgentGov model/network call.
This remains the portable reference seam. Codex development source now uses the
current Agent as its production materializer through strict normalized MCP
input; AgentGov itself still performs no proposal inference or network call.

## Semantic review compute and risk routing

AgentGov Core remains model-free. It owns deterministic facts, risk routing,
minimal context disclosure, state, assurance labels, and authority boundaries.
Development source now implements the vendor-neutral Provider capability,
route, and advisory-result contracts from ADR-0014; semantic inference itself
still belongs to a future production host materializer.

The ordinary product remains zero-configuration:

- low-risk work uses no additional semantic-model call when deterministic
  checks are sufficient;
- medium-risk work reuses the active Coding Agent's existing model entitlement
  for one structured separate pass or isolated-context self-review;
- high-risk work may use an optional independent Reviewer supplied once by the
  user or organization through a second model, enterprise AI gateway, or
  internal model. A future AgentGov-hosted Reviewer is optional and requires a
  separate privacy, retention, compliance, and billing decision.

Same-agent review must be labeled `self_review`, even when it uses a fresh
pass. Separate context is the minimum independent-review property; different
model and different provider are progressively stronger disclosed independence
levels, not proof of correctness.

When high-risk independent review is required but unavailable, AgentGov must
proactively offer human review, explicit lower-assurance same-agent review, or
Provider setup. It must not silently downgrade, block ordinary installation,
or require a second account for medium-risk work. Every result identifies its
Provider source and assurance level, remains `ADVISORY`, and grants no task,
requirement, ADR, code, scope, exception, Git, publication, release,
deployment, production, or external-write authority.

Provider credentials and inference cost belong to the user, organization, or
an explicitly selected future hosted service. Secrets, raw conversation,
transcripts, and undeclared source content do not enter repository governance
records or AgentGov Core.

Contract acceptance is not semantic approval: matching digests prove which
declared route and Provider produced a normalized result, not that the result
is correct. Codex, Claude Code, generic IDE, and unavailable-Provider fixtures
exercise compatibility without calling a model. Human judgment remains final.

Development source now also implements the active-Agent execution seam. Only
after the alignment dialogue has a human-owned resolution,
`ReferenceAlignmentAdapter.self_review(...)` can give normalized ephemeral
context and an explicit evidence allow-list to one host-supplied
`ActiveAgentSelfReviewMaterializer` callback. AgentGov generates observation
identities and accepts only the exact medium-risk self-review result. This adds
no user decision or second-account setup. It is not yet a native production
Codex, Claude Code, or IDE callback and makes no claim that Core called a model.

Development source now also carries this operation over the existing
foreground `agentgov dev --stream` connection. A host Adapter sends a start
record only after the exact alignment resolution, receives one deterministic
ephemeral materialization request, and returns small observation drafts on the
same Adapter identity. AgentGov then emits the accepted advisory result. The
ordinary user does not author these records, confirm again, or configure a
second model. Native host installation and independent high-risk review remain
separate product work.

Development source implements the first native host tool boundary with a
foreground STDIO MCP Adapter. Five base tools carry normalized alignment and
medium-risk self-review; capability-gated development Adapter `1.3.0` adds
`agentgov_task_proposal_review` for current-Agent materialization and native MCP
form review. AgentGov returns an explicit journey handle and exact pending
bindings, generates all governance identities, including question IDs that are
absent from model inputs, and loses state on restart. Known normalized-input
failures return bounded privacy-safe diagnostics and preserve atomic retry. A
create-missing-only Codex project configuration is packaged, while the Core
tool layer is exercised with both Codex and Claude Code Provider fixtures.
Installed Adapter `1.2.4` completed the current-host post-selection journey.
The exact `1.3.0` source is now installed and its local installed-runtime
protocol preflight passes; a fresh external replay of `1.3.0`, plus another
native MCP host package, remain required. Local deterministic evidence is not
semantic-success evidence.

Development source Adapter `1.6.0` closes one bounded MCP lifecycle gap with
`agentgov_task_completion_record`. The sixth base tool reuses the existing
scope, Git-snapshot, declared-validation, evidence, and append-only completion
contracts for an exact admitted task. It adds no new Core completion meaning:
`verified` remains deterministic local evidence, the human task decision stays
immutable, and acceptance plus handoff remain separate. Form-capable clients
now discover eight tools and other clients discover six. Installation,
consumer replay, and broader host evidence remain separate work.

The first separately admitted attempt to obtain that evidence stopped before
installation: a fresh offline Python 3.11.9 environment supplied
`setuptools 65.5.0`, below the declared `setuptools>=69` build requirement, and
the metadata phase failed before a package was created or installed. The clean
AIRBNB clone also retained a prior seven-tool allow-list that omits native
completion. No MCP discovery or model replay ran. A later requirement must
explicitly own offline build bootstrap and consumer configuration binding;
this failed attempt grants neither.

The human subsequently selected and admitted one combined recovery task. A
single approved bootstrap download supplied `setuptools 84.0.0`; exact current
source built and installed Adapter `1.6.0`. A fresh remote-free AIRBNB clone
received the missing completion-tool, 1,800-second timeout, and Agent-guidance
bindings, and no-model discovery exposed eight form-capable and six base tools
with completion input `task_path`. The only approved live Codex launch then
failed during required MCP initialization before a usable thread or Agent
turn: `thread/start` reported that the AgentGov handshake closed while
producing the initialize response (`-32603`). No proposal form, consumer task,
README edit, completion evidence, self-review, repair, or retry followed. The
result is `BLOCKED_BEFORE_MODEL_MCP_INITIALIZATION`; installed Codex-to-MCP
handshake behavior remains an explicit product unknown.

## Human decision boundaries

AgentGov interrupts the user only for:

- ambiguous intent or material scope;
- scope, requirement, or architecture expansion;
- an exception to declared policy;
- a command outside the repository-approved validation set;
- unresolved semantic or high-risk judgment;
- commit, push, pull-request write, merge, publication, release, deployment,
  production action, or another external write authority.

Normal UI confirmation should use a concise card, button, or adapter approval
event. Exact terminal words remain only a safe headless fallback.

The card must be pushed when the boundary is reached, explain why the decision
is needed, mark one safe recommendation without selecting it, show the effect
of every option, and require at most one structured selection. Ordinary
low-risk review must not require a free-text rationale or a remembered special
word. Display alone is never approval.

The one-selection budget applies to the final governance decision, not to
substantive clarification. When business meaning, requirements, or architecture
direction are unsettled, the host may continue a natural-language dialogue for
as many turns as needed, asking one material question at a time. Those turns
change no project state and are measured separately from governance decision
episodes. A bounded rolling storage window must not become a semantic turn cap.

## Monitor and Dashboard

The Monitor and Dashboard are a core product surface, not an optional report.
They must provide:

1. **Overview** — active sessions, pending human decisions, verified sessions,
   scope interventions, stale evidence, repeated-loop advisories, and replay
   mismatches;
2. **Live Sessions** — task, coding-agent adapter, current state, admitted
   scope, changed-file count, latest evidence, and protection status;
3. **Protection Events** — what AgentGov observed, prevented, paused, assisted,
   or routed to human judgment;
4. **Task Detail** — requirement, scope, selected governance, changed paths,
   validation, exceptions, decisions, evidence, completion, and replay
   timeline;
5. **Benefit** — earlier discovery, avoided stale evidence, bounded retries,
   manual-governance actions, evidence quality, and explicitly sourced human
   feedback;
6. **Learning** — recurring friction, false positives, missed constraints,
   overrides, consumer-local configuration needs, and candidate general
   improvements.

The Monitor also keeps a periodic drift-review reminder visible. Cadence and
due-state are deterministic; requirement, architecture, and functionality
judgments remain advisory and require human confirmation. An advisory reminder
must not fail CI merely to obtain a notification.

Development Adapter `1.4.0` binds this reminder to the first capability-gated
native drift-review form. The Agent submits only a normalized advisory
candidate with all three dimension observations and repository-relative
evidence; the human chooses record, snooze, or no record. Accepted writes are
create-only, stale due-state bindings fail closed, and the local Monitor is
refreshed without granting any additional project or external authority.
Clients without native form elicitation do not see the write-capable tool.

The Dashboard is a read model. It does not become a governance source of truth
or expose merge, release, deployment, or policy-mutation controls.

## Benefit evidence semantics

Benefit reporting separates:

- `observed_fact`: validated events and direct counts;
- `reproduced_comparison`: a before/after or stage comparison with a documented
  denominator, applicability rules, and comparable observation windows;
- `supported_inference`: evidence-supported interpretation that does not prove
  causality;
- `human_feedback`: attributed reviewer or user judgment;
- `unknown`: missing history, counterfactual outcomes, semantic correctness,
  causal benefit, or ROI that the available evidence cannot establish.

AgentGov must not publish a single governance score, protection percentage, or
benefit percentage without the required denominator and applicability model.
It must not claim that an observed intervention prevented a production outcome
unless that outcome is independently evidenced.

## Protection model

AgentGov protects users and teams by making scope, authority, evidence, and
unresolved decisions visible before PR and CI. It protects coding agents by
supplying bounded intent and architecture, preventing responsibility from
silently expanding, identifying repeated or unsupported work, and separating
environment, requirement, architecture, and implementation failures.

This is governance and workflow protection, not a security sandbox. Mechanical
process termination or enforcement against a hostile actor requires a separate
threat model and decision.

## Portability and adapter boundary

Core contracts, events, findings, benefit semantics, and Dashboard data remain
vendor-neutral. Codex, Claude Code, IDE, terminal, or other integrations are
optional adapters. Host configuration and telemetry are inputs, not governance
authority. Repository-owned declarations and reviewable evidence remain the
source of truth.

No NYC, AI Radar, or other consumer path, business object, workflow, policy, or
threshold may enter AgentGov Core. NYC is the first real consumer feedback
pilot only after the general automatic experience passes an independent
rehearsal.

## Privacy and data boundary

Local repository task text and governance declarations may remain local.
Portable exports and CI artifacts must exclude raw prompts, source code,
validation output, credentials, absolute paths, user identity, and secret-like
values. Automatic local-state upload is out of scope.

## Acceptance journey

A new user installs and enables AgentGov, asks a coding agent for one bounded
change, reviews at most one task card, lets the coding agent work while
AgentGov automatically governs and updates the Dashboard, and reviews one
completion card. The journey succeeds without hand-authored internal JSON,
special confirmation words, repeated `next` queries, or manual lifecycle
command composition.

## Delivery order

1. expose the existing lifecycle as an internal state-machine API;
2. define vendor-neutral trigger and adapter contracts;
3. implement one foreground automatic orchestrator;
4. preserve the implemented vendor-neutral structured task-proposal,
   human-admission fallback, and reference host Adapter that produces the
   proposal from a natural-language request without sending raw conversation
   data to Core; development Codex `1.3.0` binds the current Agent as the first
   production materializer and native MCP form reviewer, while install/live
   proof and other hosts remain work;
5. preserve the implemented risk router and friction budget: no-write,
   verified active-task continuation, and clean-policy fast-track have zero
   human interruptions; ambiguity and material risk require review;
6. bind the implemented vendor-neutral interaction request contract to a host
   surface that can genuinely present and record custom human decisions while
   retaining safe headless fallbacks;
7. make Monitor refresh automatic and add Dashboard protection views;
8. add denominator-aware benefit and learning views;
9. prove the complete automatic journey in an independent non-NYC repository;
10. run one low-risk NYC shadow pilot as a consumer;
11. classify feedback as consumer-local, generic, adapter, usability,
   insufficient-evidence, or rejected;
12. change AgentGov Core only for admitted general gaps, then replay in the
    independent repository and NYC before any stable promotion.
