---
name: requirement-admission
description: Turn a requested coding task into a human-owned, bounded development decision before meaningful implementation. Use when a feature, fix, refactor, or governance change is requested but has not been admitted. Do not use after admission or to approve work on the human's behalf.
triggers: ["task.requested"]
non_triggers: ["task.admitted", "task.paused"]
applies_to: ["development_task"]
---

# Requirement Admission

## Goal

Route the request with the least governance friction that still preserves
human authority. Produce a task proposal only when repository change is
actually requested.

## Required context

- Read the repository instructions and the directly relevant requirement,
  product, architecture, and status sources.
- Preserve the distinction between an observed problem, a proposed solution,
  and the accountable human's decision.
- Treat semantic value, priority, and trade-off judgments as advisory.

## Inputs

- The requested outcome and why now.
- Evidence of the current problem or opportunity.
- Candidate scope, non-goals, acceptance signals, risks, and validation.
- The locally verified active task identity, when one exists.
- The repository's admitted, tracked, clean admission-routing policy, when
  fast-track delegation is being considered.

## Workflow

1. Classify the request as `question`, `explanation`, `status_query`,
   `read_only_diagnosis`, `active_task_continuation`, or `repository_change`.
   The first four require no task and no confirmation while no repository
   write occurs.
2. For active-task continuation, verify the local admitted task identity and
   stay inside its goal and scope. Do not readmit ordinary in-scope iteration.
3. Restate the concrete problem separately from the requested solution.
4. Ask why now and identify the evidence supporting priority and expected
   benefit. If the discussion exposes business, requirement, or architecture
   drift, preserve the current center and record the drift as advisory rather
   than silently rewriting the request.
5. While a material unknown remains or the resolution options are unstable,
   enter governed clarification. Show the current center and observed drift,
   then ask exactly one highest-priority material question in natural language.
   A clarification answer is discussion, not admission or a governance
   decision. Retain only a normalized summary, never raw chat or a transcript.
6. Continue the conversation for as many turns as meaning requires. Keep a
   bounded rolling operational record without treating that storage window as
   a semantic turn limit. Do not consume the ordinary human-interruption
   budget for clarification turns.
   In a connected foreground Adapter, submit only the strict normalized
   `agentgov.alignment-context`; then carry the exact human-originated
   `agentgov.clarification-update` returned by the host conversation. Never
   forward the raw prompt or answer as a substitute for either contract.
   A host may use the reference Alignment Adapter boundary so the Coding Agent
   returns only normalized draft fields and the Adapter supplies contract IDs,
   digests, timestamps, actors, privacy declarations, and result records. The
   human must not be asked to author those internal fields.
7. Define the smallest coherent slice, its non-goals, affected paths,
   acceptance signals, validation commands, and stop conditions.
8. Surface material alternatives, risks, and trade-offs without presenting an
   advisory preference as fact.
9. Mark every material characteristic explicitly. Architecture, dependency,
   authentication/authorization, security, data schema/migration, destructive,
   external-write, infrastructure/deployment, public-API, governance-policy,
   ambiguous, or unknown-scope work requires full review.
   When semantic review is available, label whether it came from the active
   Agent's self-review or an independent Reviewer and disclose the context,
   model, or provider independence level. Missing independent review must
   route to human review, explicit lower-assurance self-review, or setup; never
   silently describe self-review as independent evidence.
   When the semantic-review contracts are available, accept only the exact
   Provider and route digest bindings; do not locally substitute a Provider,
   select an unavailable-path option for the user, or treat `ADVISORY` as task
   or scope authority.
   Active-Agent materialization may run only after the human-owned alignment
   resolution. Pass normalized context and explicitly allowed evidence refs,
   never raw conversation or undeclared source content; the same Agent's result
   remains `self_review` even when it runs as a separate pass.
10. For a new repository change, emit `agentgov.work-request` 1.0 with a nested
   `agentgov.task-proposal` 1.0. Do not copy the raw prompt or transcript into
   either contract.
11. Use `fast_track` only when an admitted human-owned policy is Git-tracked,
   clean, and every declared scope, validation, risk, assumption, unknown, and
   material-characteristic limit passes. Agent classification is never the
   authority source.
12. Only after material unknowns are resolved and two or more effects are
   stable, offer one final alignment choice: return to the current center,
   adopt an explicitly patched center, split a separate requirement, continue
   exploration when a non-material question remains, or stop. Display and
   dialogue alone change no task, architecture, scope, code, Git, deployment,
   or release state.
13. When review is genuinely required, proactively present one concise
   `agentgov.human-decision-prompt` 1.0. Explain what is being decided, why it
   is needed now, the effect of every option, and one clearly marked safe
   recommendation. Do not wait for the human to discover a command or ask what
   to do next.
14. Return exactly one route: `observe_only`, `continue_active`, `fast_track`,
   `human_review`, or `full_review`. Only the accountable human or their clean
   standing policy may admit work.
15. For a planned low-risk `human_review`, request exactly one bounded choice:
   approve the exact task, request changes, or reject. Prefer the host's native
   single-select control; the reference terminal fallback accepts one number.
   Do not require a magic word or free-text rationale. For `full_review`, stop
   before any repository write and present the material questions explicitly.
16. Accept a decision only as a strict `agentgov.human-decision-result` 1.0
   from a host that declared real decision-recording support. Display alone,
   the recommended option, ordinary agent text, and Codex context-only Hooks
   are not decisions.
17. Apply only the predeclared transition bound to the selected option. An
   approval may create the exact reviewed low-risk task after digest and race
   rechecks; revise or reject writes nothing.
   Only the accountable human may change the task to admitted.
18. Preserve the existing review disposition vocabulary: return `draft`, `admit`, `revise`, or `no-go`
   after the structured selection, without asking
   the user to type those internal values.
19. Do not begin implementation or repository modification while the route
   requires review or the task remains requested or draft.

## Required checks

- Goal, non-goals, scope, acceptance, validation, risk, and authority are
  explicit and mutually consistent.
- Referenced repository paths exist and no secret, credential, or private data
  is requested.
- High-impact or materially ambiguous decisions have named human ownership.
- No-write, verified active-task continuation, and policy fast-track routes
  each require zero human interruptions; ordinary bounded review requires at
  most one.
- A human-review prompt requires one selection and zero free-text fields; its
  result is bound to the exact prompt, source request, option, and transition.
- A clarification prompt asks exactly one natural-language question, remains
  digest-bound to the current dialogue revision, records only a normalized
  human answer summary, and increments no governance-decision counter.
- A final alignment choice is unavailable while any material unknown remains
  or fewer than two stable resolution effects exist.
- Live Adapter responses declare foreground-memory-only persistence, return
  exactly one clarification or decision prompt, and fail closed on stale,
  duplicate, cross-dialogue, or cross-Adapter records.
- A natural-language Adapter journey retains no raw conversation, asks the
  human for no JSON or internal commands, and does not count clarification
  turns as governance decision episodes.

## Stop conditions

Pause implementation and continue clarification when intent is materially
ambiguous. Stop the workflow when the user chooses stop, evidence needed to
form a useful next question is missing, the smallest coherent slice cannot be
bounded, required authority is absent, or the change would import
project-specific policy into a portable contract.

## Human escalation

During exploration, present the current center, observed drift, why the next
question matters, and one natural-language question. Once meaning has
converged, present the alternatives, trade-offs, and smallest single-select
resolution. Never self-admit a task or treat the recommended safe default as
selected.

## Expected output

Return the strict work-request and route identity, reason codes, friction
budget, and denied authority. Include a task proposal only for a new repository
change. For review routes, report the problem and why-now evidence, proposed
slice, non-goals, acceptance and validation, risks and trade-offs, human owner,
and exact decision needed before implementation.
