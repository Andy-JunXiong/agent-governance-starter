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
- Monitor 1.9 Live Sessions, Protection Events, Benefit, Learning, and drift-review
  reminder read models, with stable source-event-derived identity,
  schema-bounded read-only
  guidance to matching Task Detail cards, prominent default-open protection
  context, subordinate collapsed machine JSON, explicitly unavailable affected
  paths under the unchanged count-only event contract, explicitly unknown
  protection resolution, and advisory-only semantic drift conclusions;
  Benefit uses a strict single-observation five-card projection over current
  validated counts, with comparison and attributed feedback unavailable,
  supported inference advisory, and causal benefit unknown;
  Learning uses a strict current-observation four-card projection over the
  existing Protection Event classes, with a fixed two-event advisory recurrence
  rule. An exact candidate-bound immutable local record may supply a canonical-
  role human judgment; stale records and non-local sources remain unavailable,
  while handling, resolution, generalization, and impact stay unknown;
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
- development Adapter `1.7.0` makes changed-path classification a prerequisite
  for native proposal elicitation. Its read-only Git inventory contains only
  normalized repository-relative path/status metadata, includes both endpoints
  of renames and copies, and requires every current path to match a proposed
  include or exclude. The exact inventory is bound to preparation and compared
  again after human admission but before the exclusive task-file write;
  incomplete or changed inventories fail closed with zero writes;
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

- explicit cross-event protection resolution evidence; Monitor 1.6 guidance
  links navigate within the read model but do not record handling or resolution;
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
- denominator-aware cross-window Benefit evidence and multi-observation trends;
  Monitor 1.9 includes only bounded single-observation Benefit, current-
  observation Learning candidates, and local exact candidate-bound human
  judgment records;

## Integrated task-start scope baseline

The deterministic implementation now belongs to the installed package at
`agentgov.task_start_scope_baseline`. The former
`scripts/task_start_scope_baseline` module is a compatibility alias, not a
second policy implementation.

Confirmed `govern start` captures the baseline before writing the session
pointer or start event. It validates the admitted task, requires every current
changed path to be classified, takes stable before/after canonical Git
snapshots, and derives a separate SHA-256 identity for every committed-since-
base, staged, unstaged, and untracked record. Both endpoints of renames and
copies remain in scope evaluation. A task-contract change, HEAD change,
unstable capture, unsafe or symbolic-link path, collision, or overwrite attempt
fails the start atomically.

Later comparison uses the captured scope rather than silently trusting a
changed task. Exact pre-existing excluded identities become `PRESERVED`, while
included post-start changes pass and changed or missing predecessor exclusions,
new exclusions, and unclassified endpoints fail. The record stores no raw
source or patch, absolute path, environment value, credential, process ID, or
human/host identity. It can be created only at an explicit relative path below
`.agentgov/scope-baselines`; that local record is excluded from canonical
untracked snapshots.

Completion and the native completion tool now use the same comparison. Exact
pre-existing excluded identities become visible, non-owned
`scope.preserved` passes; all mismatches fail. Missing baselines retain strict
raw-scope behavior, so already-active or historical tasks are not upgraded
retroactively. The low-level worktree-wide `govern check` remains a direct
current-scope observation and can still report preserved predecessor changes as
failures; completion is the baseline-aware lifecycle boundary.

The first governed use now exists. Task
`p0-reusable-foreground-stdio-controller-closeout-v1` captured its exclusive
local baseline as the first execution action after take-up and before any
repository write. The initial comparison returned
`PASS=20 PRESERVED=49 FAIL=0 TOTAL=69`; controller and baseline-tool fixtures
then passed without changing their captured excluded identities. Bounded
closeout documents are the only admitted post-start repository changes. That
historical first-use comparison remains evidence for the mechanism; current
integration does not rewrite or retroactively complete it.

## Internal replayable distribution-input manifest

`governance/distribution-input-manifest.json` is the repository-owned exact
input declaration for the currently supported packaging subset. Its strict
schema is `schemas/distribution-input-manifest.schema.json`, and the read-only
internal checker is invoked with:

```powershell
py -3.11 -m scripts.distribution_input_manifest check --repository . --manifest governance/distribution-input-manifest.json
```

The checker supports only the current string project readme, explicit
`tool.setuptools.packages.find.where` roots, and
`tool.setuptools.data-files` source patterns. `LICENSE` and `pyproject.toml`
are fixed metadata inputs. Package roots select regular `.py` files; data-file
patterns use Python glob semantics, so `*` is non-recursive unless the
declaration contains `**`. Unknown setuptools selection keys, unsafe or
non-normalized paths, empty patterns, links, non-regular files, Git changes
during observation, or filesystem changes during the double derivation fail
closed.

The persisted list must be safe, sorted, unique, and exactly equal to the
independently derived current list. The checker reports deterministic
identities for the canonical newline-separated path list and the path plus
per-file SHA-256 list. It classifies selected inputs as committed, tracked
delta, untracked overlay, or deletion using read-only Git commands. Output
contains repository-relative identities and digests only, never host paths or
source contents.

This contract explicitly supersedes the omitted 199-path observation from the
exact-distribution replay. It does not claim to recover those paths, validate
setuptools beyond the supported subset, prove an artifact, or authorize a
build, journey, Git write, publication, release, or deployment. Any future
consumer or rehearsal requires separate admission.

## Internal evidence-gated short-root cleanup

`scripts.short_build_root` now exposes a repository-internal evidence receipt
and evidence-gated cleanup operation for bounded artifact work. This extends
the existing verified short-root boundary; it is not part of the public
`agentgov` CLI or installed package.

The receipt accepts only a normalized repository-relative path, requires every
path component and the final regular file to be non-symbolic-link, resolves the
file beneath the supplied existing repository, and matches an exact canonical
`sha256:<64-lowercase-hex>` identity. Creating a receipt does not authorize or
perform cleanup. The gate revalidates the same file and identity immediately
before delegating exactly once to the existing exact-root removal helper.
Missing, changed, unsafe, linked, escaping, malformed, or byte-mismatched
evidence stops before removal.

The gate has no prompt, stdin read, or TTY branch. Interactive, redirected, and
closed-input callers supply the same explicit programmatic receipt, so EOF is
not a cleanup-control transport. Normalized reports retain only the digest,
booleans, contract identity, and denied authority; host paths and evidence
contents are excluded.

This contract neither runs nor retries a build, proves future artifact parity,
nor authorizes a consumer, external Agent, model, Git operation, publication,
release, deployment, or external write. Direct low-level cleanup remains for
older internal callers; a workflow claiming evidence-before-cleanup must use
the evidence-gated operation. A future artifact or journey run requires its own
task admission.

## Internal noninteractive artifact replay driver

`scripts.artifact_replay_driver` is a dependency-free repository-internal
orchestrator over the existing distribution-input manifest checker and
short-root evidence gate. It has no `__main__.py`, public `agentgov` command,
installed-package surface, scheduler, backend selector, network behavior, or
retry policy.

The driver accepts one repository, one normalized repository-relative
manifest reference, projected paths for the existing short-root allocator,
one normalized repository-relative evidence target, and one injected action.
It requires the existing manifest checker to return a bounded passing
observation before allocating at most one verified root. The action receives
only that exact `ShortBuildRoot` and is invoked at most once. The driver does
not interpret that callback as build, dependency, network, external-Agent,
model, Git, publication, release, or deployment authority.

The action returns `ArtifactEvidence`, whose text is excluded from
representations. The driver accepts only non-empty, LF-normalized, bounded
UTF-8 text without unsupported control characters. Semantic truth,
completeness, and sanitization remain caller responsibilities; the structural
check does not convert caller claims into verified facts. The evidence parent
must already be a real repository directory. Unsafe, linked, escaping,
missing-parent, or existing targets fail before allocation. The final file is
created exclusively, flushed, and `fsync`ed before its exact SHA-256 is passed
to `create_evidence_receipt`.

Only after receipt creation does the driver call
`remove_short_build_root_after_evidence`. It never prompts, reads stdin, or
branches on TTY state. Success reports contain manifest counts and digests,
one action attempt, the evidence digest, revalidation and cleanup booleans,
root absence, and denied authority; they exclude host paths and contents.

The first manifest, allocation, action, evidence, receipt, or cleanup
deviation stops without a second action. Before a validated receipt authorizes
removal, the exact root remains available only through a private recovery
handle on the normalized failure object. The driver does not silently perform
ungated failure cleanup. Recovery, a real artifact run, or an end-to-end
journey requires its own exact authority and evidence boundary.

## Internal artifact invocation transport readiness

`scripts.artifact_invocation_readiness` is a dependency-free, repository-
internal pre-action checker. It has no `__main__.py`, public `agentgov`
command, installed surface, generic command-runner interface, payload input,
or artifact-build dependency. The existing artifact replay driver is
unchanged and does not consume or enforce the readiness result. A future
caller must run this check before deciding that its driver/action transport is
available.

The frozen request accepts only the normalized `base64_utf8_v1` declaration,
encoded length and SHA-256 identity, private launcher and retained-backend
wheel references, the expected wheel digest and Python/pip/setuptools
versions, and the exact all-false authority mapping. It never accepts caller
source, encoded payload bytes, commands, or arguments, and therefore cannot
decode or execute caller content.

All non-process gates run first. The launcher and backend wheel must be
existing regular non-link files, and the wheel bytes must match the declared
identity. A read-only temporary-directory observation requires zero direct
task roots. For compatibility with the current allocator and the admitted
future assumption, exact lowercase `agv-<8-hex>` and `agv-<16-hex>` names are
both treated as task roots; any one stops readiness.

Only then may the checker run one module-owned Python capability probe. It
uses the selected launcher in isolated mode, a fixed source constant, closed
stdin, captured output, a bounded allowlist environment, and a ten-second
timeout. It reports normalized Python, pip, and setuptools versions plus
callable `build_wheel` and vendored-wheel booleans. It cannot accept a caller
command or retry. A second zero-root observation is required immediately
before PASS.

PASS exposes only contract and schema identities, bounded encoding and wheel
identities, normalized versions and capability booleans,
`probe_attempts=1`, `short_root_count=0`, no-stdin/no-TTY facts, and denied
authority. Malformed metadata, requested authority, unsafe files, digest or
version mismatch, an existing root, timeout, exception, nonzero exit,
malformed output, or missing capability returns the first bounded reason code
with zero or one probe attempt. Host paths, source, payloads, stdout, stderr,
environment values, and raw exceptions are never reported.

This receipt is point-in-time deterministic evidence, not execution or
downstream authority. File replacement and a root appearing after the final
observation remain race limits. The checker does not invoke the driver,
allocate or clean a root, build, install, use network, start an Agent or model,
mutate Git, publish, release, deploy, schedule, repair, or authorize any of
those actions.

## Internal minimal artifact invocation caller gate

`scripts.artifact_invocation_caller` is the first concrete repository-
internal caller that enforces the readiness-before-driver ordering. It is a
dependency-free wrapper over the unchanged
`scripts.artifact_invocation_readiness` checker and unchanged
`scripts.artifact_replay_driver`. It has no `__main__.py`, public command,
installed surface, scheduler, backend selection, generic command runner,
receipt store, or independent build behavior.

The frozen caller request contains one private `InvocationTransportRequest`
and the exact existing driver arguments. Private repository, manifest,
projected-path, evidence, launcher, backend, and action values are excluded
from representations and normalized reports. The wrapper accepts no caller
source, encoded payload bytes, command, or transport arguments beyond those
already owned by the two upstream contracts.

For every call, `check_invocation_readiness` is invoked exactly once. The
wrapper requires an `InvocationReadinessResult` whose complete normalized
schema, identities, versions, capabilities, zero-root fact, no-input/no-TTY
facts, one probe attempt, and all-false authority request match the existing
readiness contract. An upstream readiness deviation, exception, malformed
type, non-PASS state, schema drift, or authority drift stops in the readiness
phase with zero driver calls.

Only after that fresh receipt validates does the wrapper call
`run_artifact_replay` once with the exact original driver arguments and
action. The receipt stays in memory and is neither written nor passed into the
driver. The wrapper validates the complete returned `ArtifactReplayResult`
schema and its denied authority before composing a stable nested PASS report.
This does not change the driver's own manifest, root, action, evidence,
receipt, cleanup, recovery, or retry semantics.

A driver deviation is normalized as one driver-phase result without another
readiness check or driver call. When the unchanged driver exposes its private
recovery error, the wrapper retains that exact object behind a private
recovery property without placing a root or path in the public report.
Unexpected exceptions and malformed success results remain bounded and do not
leak their text.

Success reports contain the two validated upstream reports,
`readiness_attempts=1`, `driver_attempts=1`, no-input/no-TTY facts, and denied
downstream authority. The wrapper does not retry, repair, persist readiness,
build, install, use network, start an Agent or model, mutate Git, publish,
release, deploy, or schedule. The receipt remains point-in-time; a real
composed invocation, receipt persistence, or driver-level receipt enforcement
requires separate product review and task authority.

## Internal bounded artifact replay harness

`scripts.artifact_replay_harness` owns the repository-internal process
transport boundary that the first two composed replay attempts had implemented
as one-off shell text. It is dependency-free, has no installed or public CLI
surface, and does not select, create, or authorize replay source. A future
admitted replay may supply one private UTF-8 source and one fixed local Python
executable; that separate task remains responsible for every action performed
by the source.

The parent encodes the source exactly once. It records the raw and Base64 byte
lengths and SHA-256 identities, then sends the same encoded value and identities
first in `dry` mode and, only after dry PASS, once in `actual` mode. Both child
processes use the fixed argument vector `python -B -m
scripts.artifact_replay_harness.worker`, a repository-root working directory,
a bounded environment allowlist, JSON stdin, captured output, and one bounded
timeout. Replay source is never placed in a `python -c` argument.

The fixed worker strictly validates the request and both source identities,
decodes UTF-8, compiles with a synthetic filename, and executes initialization
with `ARTIFACT_REPLAY_MODE` set to `dry` or `actual`. Only after raw and encoded
identity validation, it also constructs the read-only
`ARTIFACT_REPLAY_SOURCE_IDENTITY` mapping. That mapping contains exactly the raw
and Base64 byte lengths and SHA-256 identities already supplied and validated
by the worker. The parent request and replay source have no field or parameter
for replacing those values.

The source must define a zero-argument `artifact_replay_main` entry point.
Source-owned imports resolve during initialization, before that entry point is
called. The worker checks that the identity global still refers to the exact
read-only mapping after initialization and again after entry-point execution.
Mutation raises a bounded source failure; replacement returns
`source_identity_context_drift`. Syntax, import, initialization,
missing-entry-point, and execution deviations retain their distinct stable
reason codes.

Python-level source stdout and stderr are discarded. The parent never exposes
captured stdout, stderr, traceback, source, host path, environment, credential,
or process details; malformed, oversized, non-UTF-8, mixed raw/protocol output
fails closed as `worker_protocol_invalid`. Launch errors, timeouts, and
unexpected transport exceptions are also normalized without their raw text.
The first dry deviation leaves actual attempts at zero, and an actual deviation
does not repeat either phase.

The harness is transport containment, not a security sandbox or authority
grant. Descriptor-level output can invalidate the bounded protocol, and hostile
source can still consume resources or perform actions available to the child
process. Any real caller, probe, driver, build, cleanup, network, Git,
publication, release, or deployment use therefore requires an independently
admitted task. The v1 fixture suite uses only harmless local source and proves
the fixed Windows module/stdin boundary without invoking those capabilities.

## Fixed artifact replay controller

`scripts.artifact_replay_controller` is the repository-owned entry point for a
single real artifact replay. Its external request is strict JSON on stdin and
contains only the fixed launcher, pinned backend wheel identity, expected tool
versions, repository-relative evidence target, and bounded timeout. The request
has no replay-source, command, build-argument, cleanup, retry, or persistence
field.

Before constructing replay source, the controller resolves the repository and
runs the existing Git-backed distribution manifest checker exactly once. A
deviation stops in controller preflight before either Harness worker can start.
Only the normalized path count, path digest, and content digest from a passing
result cross into the controller-owned runtime configuration; no Git
executable, command, `PATH`, raw output, or host path is added to the external
request or bounded report.

The controller constructs its replay source internally. That source imports one
fixed controller-owned function and forwards the worker-provided
`ARTIFACT_REPLAY_MODE`, immutable `ARTIFACT_REPLAY_SOURCE_IDENTITY`, and the
controller-owned configuration containing those manifest facts. The controller
then calls `scripts.artifact_replay_harness` directly. It never creates dynamic
parent `python -c` text and never accepts caller-controlled Python source.

Inside the worker, the fixed function re-derives distribution inputs from the
repository files, compares them with the declared manifest paths, and
recomputes the path and content identities. This second observation performs no
Git subprocess and does not depend on ambient executable search. A mismatch in
`dry` mode stops before readiness, caller, driver, action, evidence, or cleanup,
leaving actual attempts at zero. In `actual` mode, the same validated paths feed
the admitted sequence: readiness, caller, manifest staging, offline wheel
build, wheel-payload verification, evidence creation, and receipt-gated
cleanup. Every phase is attempted at most once. Any deviation returns one
bounded controller result and no retry is performed.

The actual caller-to-driver handoff carries the same controller-bound manifest
path list, path count, path digest, and content digest as private internal
arguments. Immediately before allocating a short build root, the driver
re-derives distribution inputs and recomputes both identities from regular
repository files. It no longer imports or calls the Git-backed manifest
checker. Invalid facts or point-in-time filesystem drift therefore stop at
driver preflight with zero artifact-action attempts and no root, evidence, or
cleanup claim. This third observation keeps the Harness environment `PATH`-free
without weakening the controller's outer Git-backed admission check.

This controller narrows invocation mechanics; it does not grant task, build,
cleanup, Git, publication, release, deployment, or external authority. Fixture
tests use harmless local substitutes. A real controller request is permitted
only by an independently admitted task whose exact scope covers all intended
effects and evidence.

The manifest-boundary repair was fixture-only. It changed no Harness child
environment, ran no real controller replay, and created no artifact evidence.
A real replay after this repair still requires a separately admitted task.

## Next requirement review

Do not select the next slice automatically. Review the completed
natural-language Alignment Adapter rehearsal with the human product owner.
The selected Codex production materialization/native review source slice is now
implemented. Remaining candidates include installing and freshly replaying it,
another host, full-journey wall-clock/interrupt observation, or explicit
cross-event protection-resolution evidence; their order must follow
product-owner review.
