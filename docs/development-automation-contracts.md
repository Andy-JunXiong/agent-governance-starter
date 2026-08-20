# Development automation contracts

Status: state/trigger contracts, the foreground coordinator, a strict live
JSONL process transport, bounded task/scope/completion cards, a subordinate
drift-review reminder card with a capability-gated native review form, a vendor-neutral
host-interaction contract, and the first packaged Codex lifecycle-hook Adapter
are implemented in development source as of 2026-08-06. This is not yet the
primary installed user experience.

## Purpose

AgentGov's existing `next`, `govern start`, `govern check`, `govern finish`,
Monitor, and handoff commands remain deterministic development and recovery
primitives. The automatic product path needs stable internal contracts that can
use those cores without making a coding-agent vendor, a hidden daemon, or a
Dashboard the governance authority.

The automation path now uses these contracts:

- `agentgov.development-state` `1.0`: a read-only projection of the exact active
  task and its validated local event stream;
- `agentgov.development-trigger` `1.0`: a strict vendor-neutral input envelope
  for foreground coding-agent adapters;
- `agentgov.coding-agent-event` `1.0`: a smaller host-process JSONL envelope
  that never accepts task identity, changed paths, prompts, source, host paths,
  or authority claims;
- `agentgov.coding-agent-response` `1.3` and
  `agentgov.interaction-card` `1.1`: one result per accepted host event and an
  optional bounded task, scope, completion, or subordinate drift-review
  surface;
- `agentgov.host-interaction-capabilities` `1.0` and
  `agentgov.host-interaction-request` `1.0`: vendor-neutral declarations of
  how a host can deliver a real human gate, whether it can record the decision,
  and which existing Core event an offered option would produce;
- `agentgov.human-decision-prompt` `1.0` and
  `agentgov.human-decision-result` `1.0`: one proactive, digest-bound,
  no-free-text selection plus the exact human option and predeclared
  transition returned by a trusted host;
- `agentgov.alignment-context`, `agentgov.clarification-dialogue`,
  `agentgov.clarification-prompt`, and `agentgov.clarification-update` `1.0`:
  advisory center/drift framing, one-question natural-language exploration,
  normalized human summaries, and readiness for the existing final decision;
- `agentgov.coding-agent-alignment-response` `1.0`: the exact in-memory
  dialogue revision plus either one next clarification prompt or one final
  decision prompt, explicit foreground-only persistence, and denied project
  authority;
- `openai.codex-hooks`: a host-specific mapper from reviewed Codex project
  hooks into the vendor-neutral foreground coordinator.

## Development state projection

`src/agentgov/development_state.py` maps the current session event stream to
one stage and one recommended operation:

| Stage | Recommended operation | Blocking |
|---|---|---:|
| `active_unchecked` | `check_scope` | no |
| `scope_passed` | `validate_and_reconcile` | no |
| `scope_blocked` | `check_scope` after fixing or reviewing scope | yes |
| `validation_recorded` | `reconcile_completion` | no |
| `needs_evidence` | `validate_and_reconcile` | no |
| `review_ready` | `refresh_dashboard` | no |
| `handed_off` | `rollover` | no |
| `invalid` | `require_human` | yes |

The projection executes nothing and grants no code-change, exception, Git,
merge, or deployment authority. `agentgov next` now consumes this projection
for active-session routing while preserving its existing command-oriented
headless output.

## Adapter trigger contract

The trigger vocabulary is:

- `task.requested`;
- `repository.activated`;
- `implementation.changed`;
- `scope.decision_requested`;
- `scope.decision_recorded`;
- `completion.requested`;
- `validation.completed`;
- `session.reviewed`.

Triggers contain a hashed working-copy correlation value, an adapter identity,
an actor class, optional task identity, and only bounded facts needed by the
trigger type. They reject absolute paths, parent traversal, unknown fields,
cross-event facts, non-human scope decisions, and any consequential authority
flag set to true. Raw prompts, responses, source contents, credentials, and
host paths are not part of the contract.

`scope.decision_requested` and `scope.decision_recorded` are deliberately
separate. A coding agent can request a decision, but only a human-originated
record can carry the decision. Even that record is input to the coordinator;
the trigger envelope alone does not rewrite the admitted task or authorize an
exception.

## Current boundary

Implemented now:

- pure lifecycle state projection;
- strict JSON schemas packaged with the tool;
- strict Python trigger validation;
- privacy-bounded working-copy correlation;
- existing `next` active-session routing backed by the projection;
- Monitor 1.5 Live Sessions, Protection Events, and drift-review reminder read
  models, with stable source-event-derived identity, explicitly unknown
  protection resolution, and advisory-only semantic drift conclusions;
- `agentgov.foreground-cycle` 1.0 and `agentgov dev`, which run one disclosed
  foreground adapter/coordinator cycle without hand-authored JSON;
- a minimal reference adapter that derives working-copy identity, active task
  identity, and changed paths from repository state;
- automatic scope observation on `implementation.changed`;
- automatic scope check, task-declared pre-approved validation, completion
  reconciliation, and Dashboard refresh on `completion.requested`;
- human-originated `session.reviewed: accepted` handoff without special
  confirmation text in the adapter path;
- fail-closed treatment of missing admission, mismatched working-copy/task
  identity, scope violations, and adapter-reported validation that is not
  AgentGov evidence;
- fixture tests for stages, operations, authority denial, trigger facts, path
  safety, and adapter neutrality.
- `agentgov dev --stream`, which consumes several strict JSONL host events in
  one foreground process and flushes one response per accepted record;
- local derivation of working-copy identity, active task identity, and actual
  Git changes instead of trusting those claims from the host;
- fail-closed stream framing: malformed JSON, unknown fields, unsafe evidence
  references, non-human decisions, and unsupported facts stop at the exact
  record before its coordinator action;
- duplicate event IDs and adapter/correlation identity drift are rejected
  within one stream. Cross-process duplicate detection is not claimed because
  host event IDs are not added to durable governance state;
- bounded task cards for activation/task-request events and completion cards
  backed by AgentGov scope, validation, and reconciliation outcomes.
- bounded scope-resolution cards and deterministic interaction request IDs;
- one non-blocking drift-review reminder card only when no task, scope, or
  completion card has priority; its due state is deterministic and its review
  outcome remains advisory. Development Adapter `1.4.0` routes a completed
  three-dimension advisory pass into one native form that only the human can
  use to record the exact candidate, snooze, or write nothing. The due binding
  is revalidated before a create-only record and the local Monitor refresh is
  reported separately;
- explicit `native`, `structured`, `context_only`, and `unsupported` delivery
  modes plus `adapter_event`, `host_managed`, and `unavailable` decision
  recording. Displaying a request never applies its decision;
- one proactive decision prompt in every Coding Agent response that contains a
  real human gate. It explains why now, marks a safe recommendation, exposes
  exact option effects, and requires one selection with no free text;
- a strict decision result bound to prompt/source digests and one predeclared
  transition. Agent actors, unavailable recording surfaces, substituted
  options, and drift fail closed;
- reference terminal single-selection (`1` through the displayed option
  count) for planned low-risk human review. Approval creates only the exact
  revalidated task; request-changes and reject selections write nothing;
- automatic conversion of selected scope and completion results into only the
  existing human-originated `scope.decision_recorded` and `session.reviewed`
  Coding Agent events;
- deterministic mappings from Codex `SessionStart`, `UserPromptSubmit`,
  `PostToolUse`, and `Stop` callbacks to the four supported lifecycle events;
- explicit discard of prompt, tool payload, transcript, assistant-message,
  model, and absolute host-path values before AgentGov event construction;
- create-missing-only `.codex/hooks.json` preview and explicit apply behavior
  that refuses overwrite/merge and leaves Codex hook trust to the user.
- an honest Codex capability binding: custom task, scope, and completion gates
  are context-only and cannot be recorded through current Hooks;
- a Codex `PermissionRequest` hook that returns neither allow nor deny, leaving
  the normal native human tool prompt in control. That tool permission is not
  treated as AgentGov governance approval.
- strict `agentgov.task-proposal` 1.0 and
  `agentgov.task-admission-plan` 1.0 contracts that keep a Coding Agent's
  normalized low-risk interpretation non-authoritative, expose assumptions and
  unknowns, and exclude raw prompt/transcript/source/host data;
- a read-only `agentgov propose task ... --dry-run` preview and exact
  interactive `ADMIT` fallback. Apply exclusively creates the reviewed task
  file and does not start a session, execute validation, or append an event.
- missing-task Coding Agent cards now advertise the strict proposal contract
  plus `agentgov.work-request` 1.0, `route_work_request`, and
  `prepare_task_proposal` while retaining existing review/decline actions. The
  reference host can now record one structured selection, while options that
  have no implemented Core transition remain guidance-only;
- a host-side `ReferenceTaskProposalAdapter` now accepts one ordinary-language
  work request, invokes a replaceable `HostTaskProposalMaterializer` once, and
  turns only its normalized `TaskProposalDraft` into the existing strict
  proposal and read-only admission plan;
- proposal identity, source actor, low-risk classification, privacy boundary,
  and denied authority are Adapter-owned. The preparation retains no raw
  request, performs zero AgentGov model/network calls, writes nothing, and
  leaves exact human admission to the existing path;
- `agentgov.admission-routing-policy` 1.0 and `agentgov.admission-route` 1.0
  provide human-owned standing delegation and deterministic observe-only,
  continue-active, fast-track, human-review, and full-review results;
- zero-interruption budgets are enforced for no-write, locally verified active
  task continuation, and clean-policy fast-track. Ordinary bounded review has
  at most one interruption, while material characteristics require full review;
- Codex `UserPromptSubmit` now discards the prompt and returns host-side routing
  context instead of sending every user message to Core as `task.requested`.
- `agentgov.alignment-context` 1.0 keeps the current outcome, why-now,
  success signals, constraints, and non-goals separate from an advisory
  business, requirement, or architecture drift observation;
- `agentgov.clarification-dialogue`, `agentgov.clarification-prompt`, and
  `agentgov.clarification-update` 1.0 implement digest-bound multi-turn
  clarification with exactly one natural-language question per prompt and no
  raw prompt, answer, transcript, source, credential, or host-path retention;
- clarification turns are not governance decision episodes and are not
  semantically capped. The latest 100 normalized records form a rolling
  operational window while the cumulative turn count continues;
- only a dialogue with no material unknown, at least two stable effects, and
  one recommendation can produce the existing single-select human decision.
  Resolution changes only the structured dialogue state and grants no task,
  architecture, scope, code, Git, deployment, or release authority.
- the same `agentgov dev --stream` connection now dispatches strict alignment
  contexts, human clarification updates, and final human decision results
  alongside unchanged lifecycle events. It returns the next question or final
  choice automatically without invoking a lifecycle coordinator cycle;
- one in-memory alignment session rejects duplicate, stale, cross-dialogue,
  cross-prompt, cross-Adapter, missing-state, and out-of-order inputs before
  state advances. The response declares `survives_restart=false` and no
  cross-process recovery is claimed;
- the final decision prompt binds the host capability supplied to the session,
  not a Coding Agent vendor encoded into Core.
- a host-side `ReferenceAlignmentAdapter` accepts natural-language requests
  and answers, while a replaceable `HostSemanticMaterializer` returns only
  small normalized drafts. The Adapter supplies strict IDs, digests,
  timestamps, actors, privacy declarations, and the final decision result;
- its `AlignmentJourney` retains normalized Core responses and measures
  clarification turns separately from governance decisions while reporting
  zero user-authored structured records, internal commands, and confirmation
  words. Invalid drafts or choices do not advance Core or the metrics;
- the deterministic fixture materializer proves this integration boundary
  offline. Production semantic inference and native host UI remain Adapter
  responsibilities and are not claimed as Core capability.

Implemented semantic-review contract boundary:

- `agentgov.semantic-review-provider-capabilities` 1.0 declares Provider
  source/access, availability, review mode, independence, cost owner, data
  policy, privacy exclusions, and denied authority without naming a vendor;
- `agentgov.semantic-review-route` 1.0 deterministically selects no review for
  low risk, active-Agent self-review for medium risk, and qualifying independent
  review for high risk. Missing high-risk capacity returns exactly three
  unselected choices: human review, explicit lower-assurance self-review, or
  Provider setup;
- `agentgov.semantic-review-result` 1.0 accepts only completed advisory
  observations bound to the exact route and Provider capability digests.
  Stale bindings, false assurance, raw/sensitive content, and authority claims
  fail closed;
- Core remains model-free; a host-side Provider will supply semantic inference;
- medium risk defaults to a disclosed self-review using the active Coding
  Agent's existing entitlement in a separate pass or isolated context, so no
  new user model configuration is required;
- high risk may route to an optional user- or organization-provided independent
  Reviewer. Separate context is mandatory; different model/provider increases
  the disclosed independence level but does not prove correctness;
- unavailable independent review produces human-review, explicit
  lower-assurance self-review, or setup choices. Silent downgrade is forbidden;
- Provider identity, assurance, availability, credentials, cost, retention,
  and external-transfer policy stay outside Core, and every result remains
  advisory with denied project and external-write authority.
- Codex, Claude Code, generic IDE, and unavailable-Provider fixtures all use
  the same parser. They are compatibility examples, not model integrations.
- `ReferenceAlignmentAdapter.self_review(...)` now requires an exact resolved
  alignment response, selects the medium-risk active-host route, and invokes a
  supplied `ActiveAgentSelfReviewMaterializer` exactly once. Its ephemeral
  context contains only normalized center/drift/assumptions, the selected
  resolution, exact route/Provider, and allowed evidence references;
- the Adapter, not the host callback, generates observation IDs and result
  bindings. Empty, malformed, duplicate, out-of-allow-list, sensitive, stale,
  non-advisory, or authority-bearing output fails before acceptance;
- Codex and Claude Code active-host fixtures both complete this execution seam
  offline. AgentGov reports zero model/network calls and retains no materializer
  context.
- `agentgov.active-agent-self-review-start`,
  `agentgov.active-agent-self-review-draft`, and
  `agentgov.active-agent-self-review-stream-response` 1.0 now carry that seam
  over `agentgov dev --stream`. Start requires the exact current resolved
  dialogue and medium-risk active-host Provider; the response returns one
  deterministic ephemeral materialization request; only a draft from the same
  Adapter and pending request can complete it;
- malformed, duplicate, out-of-order, stale, cross-Adapter, cross-request,
  unsafe-evidence, privacy, assurance, and authority drift fail atomically.
  JSON mode remains pure one-response-per-input JSONL with exact error lines;
- these start and draft records are generated by a host Adapter. They add no
  user confirmation, user-authored JSON, second account, Core model call,
  repository write, or restart persistence.

Implemented native MCP Adapter boundary:

- `agentgov adapter governance-mcp --host-profile codex` runs a dependency-free
  foreground STDIO JSON-RPC server. It supports current MCP discovery/tool
  calls and the legacy initialize handshake used by existing clients;
- six base tools start, update, and resolve alignment, start and complete
  medium-risk active-Agent self-review, and record deterministic completion
  for one exact admitted task. The first five remain advisory and read-only;
  `agentgov_task_completion_record` may run only task-declared validation and
  append local evidence after a complete scope preflight. Two capability-gated
  form tools, `agentgov_task_proposal_review` and
  `agentgov_drift_review_record`, handle exact task-proposal admission and due
  drift review. Every tool input rejects unknown
  governance-bearing fields; no tool grants session, code, Git, release,
  deployment, external-write, or open-world authority;
- the Adapter creates an explicit opaque journey handle. Later calls must carry
  that handle plus the exact pending prompt or review-request digest. State is
  in process memory only and a restarted server rejects the old handle;
- the current Coding Agent supplies only normalized meaning, including question
  text, reason, materiality, and priority. The Adapter creates question IDs and
  all other IDs, timestamps, records, Provider/route bindings, observation
  identities, privacy declarations, and denied authority through the existing
  alignment and self-review state machines;
- known normalized-input rejection returns `agentgov.mcp-tool-error` 1.0 with
  only a stable code, stage, bounded field path, rule, and retryable flag.
  Rejected values and arbitrary exception text remain hidden; failed start and
  update calls are atomic, while unclassified rejection is non-retryable;
- `agentgov integrate codex-mcp . --dry-run` previews an exact project-local
  `.codex/config.toml`. Interactive apply is create-missing-only; existing
  custom config is a conflict and Codex trusted-project/config review remains
  external;
- Codex and Claude Code Provider fixtures use the same Core MCP tool layer.
  Only Codex project configuration is packaged; offline tests do not prove
  production model tool selection or semantic quality.

Not yet implemented:

- explicit cross-event protection resolution links;
- a packaged Claude Code or IDE adapter; the first Codex Adapter is present in
  development source;
- external live proof for the installed Codex `1.3.0` production task-proposal
  materializer and native MCP form review; deterministic source behavior,
  installed-runtime protocol preflight, the reference host-side seam, and
  normalized Core admission are implemented;
- production Coding Agent materializers for the implemented natural-language
  alignment Adapter boundary; only the independent offline rehearsal exists;
- a successful live uncoached Codex session using the packaged MCP
  configuration. The first run discovered and selected the tools but exposed
  the now-corrected question-identity and generic-error boundary; a fresh replay
  is required before native Claude Code or another IDE installation evidence;
  no model SDK, account, endpoint, credential store, or network call is present
  in AgentGov;
- a packaged host with native custom buttons and authenticated decision
  callbacks for every governance card. The drift reminder now has one
  capability-gated MCP form path, and task proposal admission has its existing
  MCP form, but Codex Hooks still do not expose arbitrary trusted custom
  task/scope/completion decision callbacks;
- a background or cross-process session manager; stream mode is deliberately
  foreground and exists only for the lifetime of the connected host process;
- Benefit and Learning views.

## Next requirement review

Do not select the next slice automatically. Review the completed
natural-language Alignment Adapter rehearsal with the human product owner.
The selected Codex production materialization/native review source slice is now
implemented. Remaining candidates include installing and freshly replaying it,
another host, full-journey wall-clock/interrupt observation, or explicit
protection-resolution links; their order must follow product-owner review.
