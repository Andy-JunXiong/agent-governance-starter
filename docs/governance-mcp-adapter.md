# Native governance MCP Adapter

Status: implemented in development source on 2026-08-06. This is a foreground
tool integration and an offline host-compatibility proof. It is not included in
stable 0.2.1 or immutable `v0.3.0rc1`.

## What it does in plain language

The Coding Agent can now use AgentGov as a set of native tools. The user keeps
talking normally. When meaning needs alignment, the Agent submits only a small
normalized center, drift observation, and question. AgentGov returns the next
question or final choices. After the user selects a direction, the same Agent
can request a clearly labeled medium-risk second look and return normalized
observations.

The user does not write JSON-RPC, contract IDs, question IDs, digests,
timestamps, or review records. AgentGov generates and validates those fields.
The model supplies normalized question meaning and materiality, never a
protocol identity. The user also does not configure a second model or repeat
the direction decision for self-review.

```text
ordinary host conversation
  -> current Coding Agent calls normalized MCP alignment tools
  -> AgentGov returns one question at a time
  -> human selects one offered direction in the host conversation
  -> current Coding Agent calls medium-risk self-review tools
  -> AgentGov accepts only the exact advisory result
```

## Why MCP is the native boundary

Current Codex command hooks can add context, enforce lifecycle checks, and ask
the current Agent to continue, but command hooks do not themselves perform LLM
inference. Released `prompt` and `agent` hook handlers are parsed but skipped.
The official [Codex hooks reference](https://developers.openai.com/codex/config-advanced#hooks)
documents that boundary.

Codex supports project-scoped foreground STDIO MCP servers and model-controlled
tools through `.codex/config.toml`. Its CLI, IDE extension, and desktop app
share that configuration. MCP also avoids putting a Codex vendor branch in
AgentGov Core and provides the portable tool boundary needed by Claude Code or
other MCP-capable IDE hosts.

The Adapter implements current MCP discovery and tool calls while retaining the
legacy initialize handshake needed by existing clients. Every journey receives
an explicit opaque handle, following the current MCP guidance that application
state should be represented by a visible handle rather than an implicit
transport session. State remains in the foreground process and is lost on
restart.

## Tool workflow

Without form elicitation capability, the current server advertises exactly six
tools in a fixed order. The first five are read-only and the sixth performs
only the bounded local evidence writes described below:

1. `agentgov_alignment_start` starts from normalized meaning;
2. `agentgov_alignment_update` applies one normalized answer to the exact
   pending clarification prompt;
3. `agentgov_alignment_resolve` records the human-selected offered direction;
4. `agentgov_self_review_start` prepares one exact medium-risk active-host
   materialization request;
5. `agentgov_self_review_complete` validates normalized observations and
   returns the accepted advisory result;
6. `agentgov_task_completion_record` revalidates one exact admitted task and
   appends its declared-validation and deterministic completion evidence.

Development Adapter `1.3.0` conditionally advertises a sixth tool,
`agentgov_task_proposal_review`, only when the initialized client declares MCP
form elicitation support. The current Codex Agent supplies normalized low-risk
task meaning; the Adapter creates proposal identity and invariant privacy and
authority fields, binds the local repository, renders the exact existing task
admission plan, and requests one native approve/change/reject decision through
`elicitation/create`. Clients without that capability continue to see exactly
the original five tools.

Development source Adapter `1.4.0` adds a seventh capability-gated tool,
`agentgov_drift_review_record`, on that same negotiated native-form boundary.
After the foreground card becomes due and the current Agent completes a
distinct advisory review, the Agent supplies only one candidate outcome,
exactly three normalized dimension observations, and repository-relative
evidence refs. The Agent cannot supply the form decision. The human may record
the exact displayed candidate, snooze, or create no record. Before either
create-only write, the Adapter revalidates the due-state digest; after success
it returns the shared `not_due` state and refreshes the AgentGov-owned local
Monitor. A Monitor refresh error remains separate from the already-successful
record, preventing a misleading retry. Clients without form elicitation still
see only the five read-only base tools. This exact `1.4.0` source is now
installed only in the existing local AgentGov pipx runtime and remains
unpublished and consumer-inactive. A bounded direct App Server replay reached
one thread-bound form request and stopped without a human decision or record;
it does not prove live Agent selection or end-user UI presentation.

Development source Adapter `1.5.0` corrects the accountable-owner boundary of
the existing proposal tool. Its native input no longer contains `owner`, and
the exact parser rejects an Agent-supplied owner before elicitation. The
Adapter injects the canonical `Human product owner` role into the reviewed
plan, so only the bound native `accept` plus `admit` decision can persist that
role as both `owner` and `decided_by`. This is trusted human-role mediation,
not cryptographic authentication of the individual operator. The generic task-
proposal contract and terminal fallback remain unchanged. This development
module is now installed only in the existing local AgentGov pipx development
runtime. The unchanged configured command starts, and isolated no-model
preflight confirms protocol `2026-07-28`, seven/form and five/base tool
discovery, owner-free schema, pre-elicitation hostile-owner zero-write, and an
accepted task with `Human product owner` in both durable fields. Byte-verified
`1.4.0` module and launcher backups are retained. This was a direct local
module/launcher repair, not a wheel build, publication, release, consumer
activation, model run, or live replay.

Development source Adapter `1.6.0` adds the sixth base tool,
`agentgov_task_completion_record`. Its only input is one safe
repository-relative `governance/tasks/*.json` path. Before writing, the
Adapter revalidates human admission, canonical task identity, the active-task
binding when one exists, and every path in the complete Git snapshot. A
matching session retains its recorded comparison base; a sessionless call uses
current committed HEAD only after the complete current snapshot is within the
exact task scope. The Adapter then runs only the task's declared validation
commands and reuses `agentgov.development-evidence`,
`agentgov.development-completion`, `validation.completed`, and
`completion.reconciled`. Passing fresh evidence returns `verified`; failed,
stale, or insufficient evidence returns `needs_evidence`. Records are
exclusive-create local `.agentgov/` files, while the task decision and prior
records remain unchanged. This is deterministic evidence, not human
requirement acceptance or architecture approval, and it neither starts nor
hands off a session. Form-capable clients discover eight tools and clients
without form support discover six. Adapter `1.6.0` is not installed,
consumer-replayed, published, released, or deployed. Generated Codex
configuration raises the server-level tool timeout from the default 60 seconds
to 1,800 seconds so bounded task-declared validation can complete; this does
not change the per-command 1,800-second validation limit or prove that every
multi-command task finishes within the client timeout.

A separately admitted isolated AIRBNB installation and live-replay attempt
created a fresh source staging copy, Python 3.11.9 environment, and clean
remote-free clone, then stopped before installation. The fresh environment's
`setuptools 65.5.0` did not satisfy Starter's declared `setuptools>=69` build
backend and rejected current metadata during the exact offline no-dependency
install attempt. No AgentGov package, MCP process, Codex session, consumer
task, or completion record resulted. The committed consumer `enabled_tools`
allow-list also omits `agentgov_task_completion_record`; that separate binding
was measured but not repaired or overridden.

The later human-selected end-to-end recovery task cleared both deterministic
readiness gates in isolation. One approved bootstrap download supplied
`setuptools 84.0.0`; exact staged source built and installed distribution
`0.3.0rc1`, which reported Adapter `1.6.0`, eight form-capable tools, six base
tools, and completion input `task_path`. A fresh remote-free AIRBNB clone then
received the explicit completion allow-list, 1,800-second timeout, and Agent
guidance binding. Direct no-model discovery and a process-local Codex MCP list
passed without persisting worktree trust. The single approved live launch
still failed closed during `thread/start`: the required AgentGov MCP handshake
closed while producing its initialize response (`-32603`), before a usable
thread or Agent turn. No proposal form, consumer task, README edit, completion
record, current-Agent consumer review, repair, or replay retry followed. This
is `BLOCKED_BEFORE_MODEL_MCP_INITIALIZATION`, not installed live-completion
evidence.

The proposal trigger is scoped to the exact requested repository change. A
human-admitted task counts only when its requirement, goal, scope, and
acceptance signals match and authorize that change. An unrelated,
measurement-only, or differently scoped admitted task does not count.
Read-only work does not trigger proposal review. These server instructions and
tool metadata guide host selection; deterministic checks keep the surfaces in
sync but cannot force a model to choose the tool.

New initializer output includes an inert tracked
`governance/tasks/.gitkeep`, so the first native proposal can build its
read-only plan without relaxing safe-parent or create-only task semantics. It
does not represent task admission. Older consumers without the directory must
receive a reviewed adoption repair before retrying proposal review.

Only the response bound to that elicitation with `action=accept` and
`decision=admit` can exclusively create the reviewed task file. All other
decisions, malformed or interrupted responses, stale plans, and target races
are zero-write. A tool permission prompt does not count as task admission, and
admission grants no implementation, scope, Git, release, or deployment
authority. The current Agent supplies no accountable-owner identity through
this native tool; the Adapter-owned human role is visible in the exact plan
before the decision.

Server instructions and tool descriptions also disclose the host selection
boundary. Meaningful development with multiple reasonable directions—or a
request asking the Agent to choose what to build—starts alignment without the
human naming a tool. Read-only explanation, diagnosis, status, and fully
specified low-risk work do not start it merely for ceremony. The Agent must
leave the final offered direction to the human. After implementing and
validating that resolved direction, the same Agent starts a distinct advisory
self-review before its completion handoff. Repository `AGENTS.md` repeats this
host-visible rule; deterministic tests keep both surfaces synchronized.
After implementing any exact admitted task, the same guidance routes the Agent
through `agentgov_task_completion_record` before that advisory pass when the
tool is available. A completion-tool failure remains fail-closed and cannot be
recast as task acceptance.

The model must carry the journey handle and exact prompt/request digest returned
by AgentGov. Unknown, stale, duplicate, out-of-order, cross-journey, or
post-restart calls fail without advancing state. Input schemas reject unknown
fields at every governance-bearing object boundary. The drift schema mirrors
Core's judgment boundary: business, requirement, and architecture drift must
be advisory. Scope and implementation drift may be deterministic when their
evidence supports a deterministic classification.
When the start context has no open unknowns, the schema also requires at least
two stable candidate resolutions and one non-null recommendation so Core can
produce the human-owned final choice immediately.

Known normalized-input failures return `agentgov.mcp-tool-error` 1.0 with only
a stable error code, stage, bounded field path, validation rule, and retryable
flag. Rejected values, raw conversation, source, credentials, absolute paths,
arbitrary exception text, and stack traces are never included. A failed start
creates no journey, and a failed update does not advance its journey, so the
host may correct a retryable field in the same foreground process. An
unclassified Core rejection remains non-retryable and exposes no field path.
The Adapter safely classifies a violation of the advisory-only drift rule as
`drift.semantics` / `advisory_required`, allowing a corrected retry without
echoing the rejected value.
For a no-unknown context it separately reports
`candidate_resolutions` / `stable_options_required` or
`recommended_resolution_id` / `recommendation_required`; both are retryable
and preserve atomic start behavior.

### Alignment Start parity matrix

The audit denominator is the eleven validation families reachable from the
MCP Alignment Start call. It is a rule-family denominator, not a governance or
semantic coverage percentage. The first ten families are model-authored input;
the final family is Adapter/Core-generated state.

| # | Reachable family | Public/Adapter treatment | Failure class |
|---|---|---|---|
| 1 | top-level envelope | exact required fields, no extras | repairable input |
| 2 | subject type and identity | enum and normalized identifier | repairable input |
| 3 | center shape, text, lists, and success minimum | schema plus field validator | repairable input |
| 4 | drift shape, kind, semantics, text, and evidence | conditional schema plus field validator | repairable input |
| 5 | assumptions cardinality, text, and uniqueness | schema plus field validator | repairable input |
| 6 | unknown-question shape, text, materiality, and priority | schema plus Adapter-owned IDs | repairable input |
| 7 | candidate count, IDs, text, and center patches | conditional schema plus field validator | repairable input |
| 8 | recommendation identity | exact candidate binding | repairable input |
| 9 | no-unknown readiness | two stable options plus recommendation | repairable input |
| 10 | privacy and repository-path boundaries | value-free privacy/path rules | repairable input |
| 11 | generated IDs, authority, dialogue, and prompt invariants | Core validation after all input checks | internal, non-retryable |

Thirty normalized repairable-input fixtures exercise the first ten families,
with dedicated successful variants for advisory/deterministic drift and
no-unknown readiness. A synthetic future Core invariant exercises family 11
and remains `alignment_rejected_internal`, `unclassified`, non-retryable, with
no cause text returned. This matrix proves validation parity for the current
start contract; it does not prove semantic correctness or host behavior.

## Privacy, cost, and authority

The tools reject raw prompts, raw answers, transcripts, assistant messages,
full source content, credentials, model prompts, absolute paths, and undeclared
authority. Repository paths may appear only as bounded evidence references;
source content is not sent.

The host's existing current-Agent entitlement supplies semantic reasoning.
AgentGov reports zero model and network calls, stores no credential, launches no
second Agent, and retains no journey after process restart. The five alignment
and self-review tools write no repository/runtime state and remain `ADVISORY`.
The optional proposal-review tool has one narrower effect: after the bound
human native admission it may exclusively create the exact reviewed task file.
It cannot start development, change requirements or architecture, expand
scope, approve exceptions, or authorize code, Git, release, deployment, or
external writes.

## Codex project integration

Preview the exact create-missing-only project configuration:

```powershell
agentgov integrate codex-mcp . --dry-run
```

The preview creates nothing. Interactive apply requires exact `INTEGRATE` once
as an installation decision. It can create only `.codex/config.toml` when that
file is missing, preserves the exact managed file, and refuses to overwrite or
merge any existing custom configuration. Codex trusted-project/config review
remains separate and cannot be granted by AgentGov.

The generated config launches:

```text
agentgov adapter governance-mcp --host-profile codex
```

Daily alignment and self-review require no additional installation command or
manual protocol input after the host has loaded the reviewed MCP server.

## Honest implementation limit

The first live uncoached Codex session discovered all five tools and selected
alignment at the right moment, but it failed before human direction selection:
the tool asked the model for a Core-owned question identity and returned only a
generic rejection. Development source now keeps that identity Adapter-owned and
returns privacy-safe structured diagnostics with atomic retry. Static tests
prove the correction, not the production journey. A post-correction replay then
bypassed the tools, independently selected a change, and omitted self-review.
Development source now adds intent-oriented server/tool metadata and matching
repository guidance. The post-guidance replay selected alignment but exposed a
second contract mismatch: its schema allowed deterministic semantics for drift
kinds that Core requires to remain advisory. Development source now aligns the
schema and classifies that retry safely, but another fresh uncoached replay is
still required. That replay corrected its first drift error but exposed the
next undisclosed cross-field rule: a context with no unknowns needs at least
two stable options and one recommendation. Development source now advertises
and precisely classifies both missing parts. These changes do not prove that a
production model will always choose the right tool. Native Claude Code and
other IDE configuration packages,
authenticated custom decision recording, and independent high-risk Reviewer
execution remain later slices.

The complete `1.2.3` parity source is now installed in the local Python 3.12.10
pipx runtime. Installed discovery, schema, repairable retry, corrected
decision-readiness, and private internal-fallback preflight passed. A sandboxed
Codex process could not reach the external service and therefore did not begin
an eligible replay. The human approved one external retry; that session
completed, but its normalizer scanned both actual events and historical
repository text and therefore produced contradictory markers. Because raw
events were intentionally discarded, it is an invalid measurement rather than
success evidence. A separately approved replay used an event-scoped normalizer
and completed two real Alignment Start calls: one retryable input rejection,
then `ready_for_decision` with a human-owned selection boundary. No internal or
unclassified error occurred. Resolve and self-review were not invoked, so this
is Start-boundary evidence rather than a complete development journey.

Development Adapter `1.2.4` extends deterministic parity past the human choice.
Resolve rejects malformed, stale, or non-offered selections with bounded
`post_selection_invalid_field` metadata. Self-review start validates a resolved
journey, non-empty normalized reason codes, and safe repository-relative
evidence before creating a request. Completion binds the exact pending request
and validates normalized advisory observations before completing the run.
Rejected calls do not advance foreground state, so a corrected retry can use
the same journey. A later independent installation-gate audit tightened this
boundary to the exact downstream contracts: reason codes use the portable
120-character identifier, evidence paths are at most 240 characters,
assumptions and unknowns contain at most 20 items, cited evidence must belong
to the pending request's allow-list, and observations must be unique. These
guarantees are deterministic Adapter behavior; no new live-host or semantic-
correctness claim is made.

The exact corrected source is now installed in the local Python 3.12.10 pipx
environment as Adapter `1.2.4`. Installed STDIO discovery returned protocol
`2026-07-28` and all five tools. One foreground installed-package probe
confirmed all five bounded failures, unchanged state after rejection, corrected
completion in the same process, and zero AgentGov model or network calls. This
is installation evidence only; it does not prove an external host journey.

Development Adapter `1.3.0` now connects the existing strict proposal planner
to the current Codex Agent as production materializer and to MCP form
elicitation as the native human review surface. Focused fixtures prove
capability-gated discovery, exact preview/response binding, exclusive admit,
zero-write non-admission and interruption paths, privacy-safe diagnostics, and
legacy five-tool compatibility. The exact source is now installed in the
existing local pipx environment. Installed discovery and protocol preflight
confirm Adapter `1.3.0`, capability-gated six/five-tool behavior, the restricted
form schema, extension privacy, exclusive admit, and zero-write failure paths.
The later trigger clarification was also built offline and installed into that
same environment as a hash-recorded local-only wheel. Installed source identity,
server instructions, proposal-tool metadata, and six/five-tool discovery match
the reviewed source; project configuration was unchanged. During one later
authorized ephemeral read-only replay, the exact proposal tool started once;
the turn completed without an AgentGov form request. No decision, task, implementation, or
repository mutation occurred. This proves current-host invocation, not a
successful elicitation or admission journey. Two following no-model direct App
Server calls with the same valid normalized arguments parsed the Adapter form and
returned a zero-write `decline` because no active turn hosted it. This proves
valid-input Adapter generation and App Server schema parsing, but the retained
live summary cannot distinguish a structured pre-form error from forwarding or
presentation behavior. The selected test-only correction now records exact
completion count/status, `completion_unknown`, and at most eight strictly
validated AgentGov error records while dropping raw messages and payloads. It
improves future replay evidence only; historical events remain unrecoverable.

## Feature connections

- Upstream: governed clarification, resolved human alignment, Provider/risk
  routing, and live active-Agent self-review transport.
- Current: model-controlled native alignment/self-review plus Codex production
  proposal materialization and exact native human admission over one foreground
  MCP Adapter.
- Downstream: product review must decide whether a future replay is still
  valuable now that its completion/error evidence can be interpreted honestly.
  Another replay, another MCP host, and optional independent high-risk review
  remain separate later choices.
