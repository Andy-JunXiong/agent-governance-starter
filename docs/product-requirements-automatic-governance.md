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

The first implementation is an explicit one-cycle foreground orchestrator,
`agentgov dev`, plus a minimal repository-state reference adapter. It now
handles activation, implementation-change scope checks, completion-triggered
pre-approved validation and reconciliation, human-reviewed handoff, and
Dashboard refresh in development source. A live coding-agent event transport,
natural-language task drafting/admission, and visual approval/completion cards
remain open. The target remains an adapter-owned foreground experience, not a
hidden system daemon or a requirement that ordinary users type event commands.

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
4. replace routine text confirmations with a bounded approval interface while
   retaining safe headless fallbacks;
5. make Monitor refresh automatic and add Dashboard protection views;
6. add denominator-aware benefit and learning views;
7. prove the complete automatic journey in an independent non-NYC repository;
8. run one low-risk NYC shadow pilot as a consumer;
9. classify feedback as consumer-local, generic, adapter, usability,
   insufficient-evidence, or rejected;
10. change AgentGov Core only for admitted general gaps, then replay in the
    independent repository and NYC before any stable promotion.
