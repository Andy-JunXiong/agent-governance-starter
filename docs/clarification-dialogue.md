# Governed clarification and drift re-centering

AgentGov treats substantive discussion as part of governance, but not as an
approval gate. When the user's outcome, the proposed solution, and the current
architecture no longer line up, the system keeps the current center visible,
names the observed drift, and helps the user clarify the direction before it
offers a final bounded choice.

This protocol is vendor-neutral. Codex, Claude Code, an IDE, a terminal, or a
future host Adapter can use the same Core contracts. Host-specific UI and
authentication remain Adapter responsibilities.

## When dialogue is needed

No clarification dialogue is needed for a clear question, read-only diagnosis,
verified in-scope continuation, or a stable low-risk request. Start one when a
material unknown or observed business, requirement, or architecture drift
could change the outcome, success signals, constraints, non-goals, or durable
technical direction.

Business, requirement, and architecture drift are advisory observations. A
static checker can show contradictory files or changed paths, but it cannot
objectively decide which business meaning should win.

## Conversation model

Each turn shows:

- the current center in plain language;
- the observed drift and why it matters;
- exactly one highest-priority material question;
- a reminder that the user may answer naturally and that the turn grants no
  project authority.

The Adapter converts the answer into a normalized summary. Core does not retain
the raw answer, raw prompt, transcript, assistant response, source content,
credentials, or absolute host paths. The next dialogue revision is bound to
the exact previous revision and prompt digest, so stale or substituted answers
fail closed.

Clarification turns and governance decision episodes are deliberately separate
metrics. A discussion may take as many turns as the meaning requires and does
not consume the ordinary one-decision friction budget. The current contract
keeps only the latest 100 normalized records as an operational rolling window;
the cumulative clarification-turn counter continues beyond that window, so
100 is not a semantic conversation limit.

## Contracts and states

`agentgov.alignment-context` 1.0 separates the current center, observed drift,
assumptions, open questions, candidate resolutions, privacy declarations, and
denied authority.

`agentgov.clarification-dialogue` 1.0 moves through:

- `exploring` while a useful question remains;
- `ready_for_decision` only when no material unknown remains, at least two
  resolution effects are stable, and one safe recommendation is identified;
- `resolved` after a human-owned direction choice;
- `stopped` when the user ends the work.

`agentgov.clarification-prompt` 1.0 carries one natural-language question.
`agentgov.clarification-update` 1.0 carries one normalized human answer summary
and any explicit center patch, newly discovered questions, or stabilized
resolution candidates.

Unknown fields, non-human answers, wrong question IDs, stale revisions,
digest drift, raw-content declarations, unsafe evidence paths, and authority
claims fail closed.

## Final re-centering decision

Once the dialogue is ready, AgentGov reuses
`agentgov.human-decision-prompt` and `agentgov.human-decision-result`. The host
offers only the stable choices that apply:

- return to the current center;
- adopt an explicitly described new center;
- split the new outcome into a separate requirement;
- continue exploring when a non-material question remains;
- stop.

The safe recommendation is visible but never preselected. The selected result
updates only the structured dialogue center or resolution record.
It does not edit requirements or ADRs, admit or start a task, change scope or
code, grant an exception, or authorize Git, deployment, or release actions. Any resulting
repository change must still pass the normal requirement-admission flow.

## Reference implementation boundary

Development source provides strict Python parsers, the multi-turn state
transition functions, a terminal clarification renderer, and the existing
single-select decision contract for final resolution.

The disclosed `agentgov dev --stream` process now accepts three strict records
in the same connection as lifecycle events:

1. a Coding Agent Adapter's normalized `agentgov.alignment-context` starts the
   dialogue and automatically returns one question or a ready final choice;
2. a host-recorded human `agentgov.clarification-update` advances the exact
   question and automatically returns the next prompt;
3. a host-recorded `agentgov.human-decision-result` applies only the selected
   alignment resolution and returns the structured terminal or continuing
   state.

Each output is `agentgov.coding-agent-alignment-response` 1.0. It explicitly
declares `foreground_memory` and `survives_restart=false`. Duplicate, stale,
cross-dialogue, cross-prompt, cross-Adapter, or out-of-order inputs fail on the
exact JSONL line before state advances. Alignment records do not invoke the
development lifecycle coordinator or write the repository.

This does not claim that Core can semantically understand raw chat, that
current Codex Hooks provide a native authenticated custom button callback, or
that restart recovery and a finished production host UI exist. The Coding
Agent Adapter remains responsible for producing the normalized context and the
host remains responsible for authenticating its human conversation and choice.

## Natural-language reference Adapter

`ReferenceAlignmentAdapter` now rehearses that host responsibility end to end.
Its public journey methods accept one ordinary request, ordinary answers to the
exact Core question, and the ID of a host UI selection. A replaceable
`HostSemanticMaterializer` sees the natural language in host memory and returns
only `AlignmentContextDraft` or `ClarificationUpdateDraft`. The Adapter then
creates the strict IDs, digests, timestamps, actor bindings, privacy boundary,
and final human-result record; the user creates none of them.

The returned `AlignmentJourney` retains only normalized Core responses. Its
interaction-burden fields separate natural-language answers from governance
decision episodes and explicitly count user-authored structured records,
internal commands, and confirmation words as zero. Invalid drafts, premature
answers or decisions, and non-offered selections fail before either Core state
or those metrics advance.

The supplied automated rehearsal uses a deterministic offline materializer so
it is repeatable and makes no external call. It proves the host/Core boundary,
privacy shape, and three-interaction journey; it does not prove that AgentGov
Core understands arbitrary chat, provide a production model materializer, or
add native controls to Codex, Claude Code, or an IDE.

The approved production direction does not make a second model mandatory.
Medium-risk clarification can use the active Coding Agent for a disclosed
separate-pass or isolated-context self-review with the user's existing access.
High-risk work may use an optional independently configured Reviewer. If none
is available, the host must offer human review, an explicitly lower-assurance
self-review, or Provider setup rather than silently calling self-review
independent. All such semantic observations remain advisory; the dialogue's
human decision and denied project authority are unchanged.

ADR-0014's development contracts now make that routing explicit and
fail-closed: the Provider declares capability, Core chooses an assurance route,
and only a digest-bound advisory result can return. This still does not execute
a model by itself or grant the result authority.

That Adapter boundary is now executable in development source. Once the human
selects the final alignment resolution, `ReferenceAlignmentAdapter` can invoke
one host-supplied active-Agent self-review callback with only normalized center,
drift, assumptions, the selected resolution, and allowed evidence references.
The callback cannot run while the dialogue is exploring or waiting for the
selection. AgentGov still ships no production host model integration.
