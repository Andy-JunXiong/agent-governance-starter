# Historical documentation migration - 2026-08-14

## Record purpose

This dated record preserves text relocated by Historical Documentation
Migration v1. It is a migration record created on 2026-08-14, not a claim that
the older events occurred on this date. Source headings are demoted by one
level only so the original section boundaries remain visible beneath their
source labels; factual wording is otherwise unchanged.

The migration separates current repository reality, strategic direction, and
append-only session evidence. It does not rewrite historical outcomes, change
product behavior, add archive automation, or authorize task, Git, publication,
release, deployment, or external actions.

This migration record grants no task or external authority.

## Source map

| Original surface and boundary | Current owner after migration | Supporting dated evidence |
| --- | --- | --- |
| `STATUS.md`: `Development checkpoint - 2026-08-06` through `Development checkpoint - 2026-08-05` | This record; `STATUS.md` retains a concise index | `docs/development-log/2026-08-05.md`, `docs/development-log/2026-08-06.md` |
| `DEVELOPMENT_PLAN.md`: `Current State` through `Foundation implementation history` | This record for the superseded snapshot; `STATUS.md` owns current reality | Dated logs from 2026-07-23 through 2026-08-14 and the referenced task/ADR records |
| `DEVELOPMENT_PLAN.md`: `Next Recommended Starting Point` | This record for the superseded checkpoint narrative; the plan retains strategy | Dated logs and exact admitted task records referenced by the text |
| `docs/development-plan.md`: `Current checkpoint` and `Next-session starting point` | This record; the public plan retains ordered strategy | Dated logs and exact admitted task records referenced by the text |

No existing development-log path was renamed or rewritten.

## Relocated from `STATUS.md`

Original boundary: `Development checkpoint - 2026-08-06` through the end of
`Development checkpoint - 2026-08-05`.
### Development checkpoint - 2026-08-06

- The development CLI now treats a bare `agentgov` invocation as a safe
  first-time orientation surface instead of a missing-command error. It prints
  help, recommends the read-only `doctor`, `next`, and `status` entry points,
  performs no repository inspection or write, and exits successfully.

- `ReferenceAlignmentAdapter` now connects a host's natural-language request,
  one natural-language clarification answer, and one final single-select to
  the existing strict in-memory Core flow. The human authors no JSON, IDs,
  digests, timestamps, actor metadata, confirmation words, or internal
  commands.
- `HostSemanticMaterializer` is an explicit replaceable host boundary. It
  returns only `AlignmentContextDraft` and `ClarificationUpdateDraft`; the
  Adapter creates and validates the strict contracts. Core still performs no
  arbitrary semantic inference.
- The privacy-safe journey retains only normalized Core responses and reports
  natural-language inputs, clarification turns, governance-decision episodes,
  selections, and zero user-authored structured records/internal commands.
  Invalid drafts and out-of-order or non-offered choices do not advance Core
  state or burden metrics.

- `agentgov.coding-agent-alignment-response` 1.0 now exposes the exact current
  dialogue and exactly one next clarification prompt or final decision prompt.
  It declares `foreground_memory`, `survives_restart=false`, and fully denied
  project authority.
- `agentgov dev --stream` now dispatches alignment context, human clarification
  update, and final human decision result records alongside unchanged lifecycle
  events. Duplicate, stale, wrong-prompt, cross-dialogue, cross-Adapter,
  missing-state, and out-of-order records fail before the session advances.
- Alignment-only records do not run the foreground development coordinator,
  update the Dashboard, or write the repository. The host's declared decision
  capability binds the final choice; Core remains vendor-neutral.

- `agentgov.alignment-context`, `agentgov.clarification-dialogue`,
  `agentgov.clarification-prompt`, and `agentgov.clarification-update` 1.0
  separate advisory drift observation, natural-language clarification, and
  final authority. Raw chat, transcripts, source content, host paths, and
  project-change authority are excluded.
- Clarification asks exactly one highest-priority material question, binds
  each normalized human answer to the exact dialogue/prompt revision, and
  keeps clarification turns separate from governance decision episodes. A
  100-record rolling snapshot does not cap the cumulative turn count.
- Final re-centering reuses the existing digest-bound single-select decision
  contracts only after material unknowns are resolved and at least two stable
  effects exist. It changes only structured dialogue state; task, architecture,
  scope, code, Git, deployment, and release authority remain denied.

- `agentgov.human-decision-prompt` 1.0 proactively explains the exact decision,
  why it is needed, one safe recommendation, every bounded option effect, and
  a one-selection/no-free-text input contract. Display grants no authority.
- `agentgov.human-decision-result` 1.0 records one human selection from a host
  that declared decision-recording support and binds prompt, source, option,
  and transition digests. Agent actors, substituted choices, drift, and
  unavailable hosts fail closed.
- `agentgov.coding-agent-response` 1.3 and `agentgov.interaction-card` 1.1 add
  the subordinate non-blocking drift reminder while retaining the proactive
  prompt whenever a real human gate exists. Scope/completion selections carry only their existing
  Core event; planned low-risk human review accepts one number and approval
  creates only the exact task. Codex Hooks remain context-only/unavailable for
  trusted custom decision recording.

- `agentgov.work-request` 1.0 classifies questions, explanations, status
  queries, read-only diagnosis, active-task continuation, and new repository
  changes without raw prompt/transcript content or authority.
- `agentgov.admission-routing-policy` 1.0 makes low-risk delegation explicitly
  human-owned, path/validation/risk bounded, Git-tracked and clean. The shipped
  template is a draft with fast-track disabled.
- `agentgov.admission-route` 1.0 deterministically selects `observe_only`,
  `continue_active`, `fast_track`, `human_review`, or `full_review` and reports
  the numeric human-interruption budget. The first three routes budget zero;
  ordinary bounded review budgets one.
- Non-interactive `--apply-fast-track` revalidates policy, request, route, task,
  and target identity and creates only the task. It does not start a session,
  run validation, modify code, or grant downstream authority.
- The portable requirement-admission Skill and missing-task cards now route
  before proposing. Codex `UserPromptSubmit` discards the prompt and returns
  routing context instead of forcing every prompt through task admission.

- `agentgov.task-proposal` 1.0 now accepts only a normalized low-risk Coding
  Agent interpretation with explicit assumptions, unknowns, privacy boundary,
  and denied authority. Unknown fields, raw-prompt-shaped fields, sensitive or
  host-local content, unsafe scope, missing validation, and non-low risk fail
  before an admission plan exists.
- `agentgov.task-admission-plan` 1.0 exposes the complete normalized proposal,
  stable proposal/task digests, exact final compact task, sole target, and a
  fully denied preview authority boundary.
- `ReferenceTaskProposalAdapter` now supplies the host-owned conversion seam:
  one ordinary-language request becomes a strict proposal and the existing
  read-only admission preview through one replaceable materializer invocation.
  The Adapter owns proposal identity, privacy, low-risk, and denied-authority
  fields; retains no raw request; makes zero AgentGov model/network calls; and
  cannot admit the task or write the repository. Offline fixtures prove the
  boundary, not production semantic quality or native host integration.
- Development Adapter `1.3.0` now provides the first Codex production-host
  materializer and native proposal review path. The current Codex Agent sends
  only normalized low-risk task fields to `agentgov_task_proposal_review`;
  AgentGov derives the strict proposal and exact admission plan, and Codex
  collects one bound decision through MCP form elicitation. Only exact native
  admission creates the planned task. All other decisions, interruption,
  malformed responses, stale plans, target races, and missing elicitation
  capability remain zero-write. Legacy clients keep the original five tools.
  The exact source is now installed in the existing local pipx environment.
  Installed discovery reports Adapter `1.3.0` and six tools with form
  capability, while clients without it retain five. Installed protocol,
  schema, extension-privacy, exclusive-admit, non-admission, malformed-response,
  and target-race preflight passed. A valid negative external replay has now
  completed, but no successful native proposal-review journey is claimed.
- The first approved event-level Adapter `1.3.0` proposal-review attempt was
  classified `INVALID_HOST_BRIDGE`: a Windows PowerShell 5.1 stderr callback
  stalled the App Server bridge before any observable thread, native form, tool
  result, or terminal event. The exact process was stopped, no raw material or
  repository write was retained, and a local no-thread probe confirmed the
  corrected null-stream drain. A separately authorized retry then exposed a
  second host boundary: local initialization and `thread/start` passed after
  using the runtime's verified `read-only` value, but the real request reached
  `starting_turn` and App Server closed before returning a turn, form, tool
  result, or error code. This result is `INVALID_APP_SERVER_EOF`, not an Adapter
  pass or failure. Standalone authentication and the installed runtime were
  later repaired, and one UTF-8-safe replay completed a real read-only turn
  without surfacing a form. Because its temporary normalizer used text
  presence rather than exact `mcpToolCall` fields, the observed
  `proposal_tool_seen` flag is invalid evidence. A test-only event normalizer
  now fails closed on unrelated text and accepts only the exact server, tool,
  form, result, and terminal shapes. No new task or other repository write
  occurred. A following authorized structured replay completed normally with
  `not_called`, zero exact proposal-tool calls, and zero forms. The journey did
  not enter the Adapter path for that bounded request. The retained replay
  evidence alone could not assign that result to tool discovery/configuration
  or Agent invocation. A later no-turn App Server configuration/status probe
  confirmed that the project MCP layer loaded and exposed all six AgentGov
  tools. The remaining observed gap is therefore Agent invocation under an
  ambiguous trigger contract, not discovery. A subsequent consumer replay
  loaded the generated journey but still treated direct chat authorization as
  admission and skipped proposal review and self-review. Development
  instructions and MCP metadata now require a readable, validated matching
  `governance/tasks/*.json` record with a human admitted or approved decision
  before any repository write. Direct chat authorization and tool permission
  do not count; every repository-changing task requires self-review, and
  read-only work remains exempt. This is
  advisory host guidance rather than deterministic model-routing enforcement.
  A separately authorized installation-only step built the exact reviewed
  source offline as a local-only `0.3.0rc1` wheel with SHA-256
  `F109E8A951605AE947374EE28BB76B569A344BC3DD20A752E1686AF8C317FDFE`
  and updated only the existing AgentGov pipx runtime. Installed package and
  import identity report `0.3.0rc1`; Adapter discovery reports `1.3.0`, protocol
  `2026-07-28`, six tools with form capability and five without it, and the
  clarified trigger metadata. The project config hash remained unchanged. The
  pre-existing pipx management metadata still names its original `0.1.0`
  install source, so `pipx list` is not used as installed-content identity.
  No Codex turn or replay occurred during installation. A later separately
  authorized replay preflight confirmed the same configuration, server, and
  six tools, then one ordinary repository-change turn started the exact
  proposal tool once. No AgentGov form request was observed before the turn
  completed. No human decision was supplied, no task or implementation was
  created, and no repository state changed. Two later local, no-model direct
  calls supplied the same valid normalized arguments. App Server parsed the resulting form and
  returned `decline` because no active turn hosted it; the Adapter reported its
  normal zero-write non-admission result. This rules out discovery, valid-input
  form generation, and schema parsing as general failures. The retained replay
  summary cannot distinguish a structured pre-form tool error from forwarding
  or presentation behavior because it dropped unrecognized completion results.
  Future summaries now retain deduplicated completion count/status and a strict
  eight-record maximum for allow-listed AgentGov error code, matching stage,
  bounded field path, rule, and retryability. Unknown completions are explicit;
  raw error text and payloads remain excluded. Historical evidence remains
  unchanged, and another replay is not admitted.
- `agentgov propose task ... --dry-run` is read-only. Its recovery fallback
  requires exact `ADMIT` from a real interactive terminal, rechecks drift and target races,
  and exclusively creates the reviewed task file. It does not create a
  session/event, execute validation, or authorize code, scope, Git,
  deployment, or release actions.
- Assumptions and unknowns are preserved in the admitted compact task as
  reviewed risk items. Static validation still cannot prove that the Coding
  Agent's normalized summary perfectly represents the user's meaning; human
  semantic review remains authoritative.
- Semantic-review contracts likewise validate declared capability, routing,
  assurance, privacy, result identity, and denied authority; they do not prove
  that an LLM observation is correct. The next implementation boundary is one
  real host callback installed in a Coding Agent surface; the portable
  active-Agent materializer seam no longer needs design work.
- Interactive-terminal presence blocks ordinary headless self-admission but is
  an operator attestation, not cryptographic proof of human identity. Codex MCP
  form elicitation now supplies a native bounded decision callback, but its
  human attribution is only as strong as the host session and is not claimed as
  cryptographic identity proof.
- Focused active-Agent self-review, Alignment Adapter/transport,
  semantic-review, clarification, Skill, task, documentation, and portfolio
  regression passed 110 tests. The complete Python 3.11 suite passed 700 tests
  with two platform-limited skips.
  The current task check reported `PASS=6 WARN=0 FAIL=0 ADVISORY=1`; combined
  working-copy scope reported `PASS=97 FAIL=0 ADVISORY=1`; repository governance reported
  `PASS=26 WARN=2 FAIL=0 ADVISORY=4`; all 51 repository schemas parsed,
  source/tests compiled, and `git diff --check` passed.

- `agentgov dev --stream` now consumes multiple strict
  `agentgov.coding-agent-event` 1.0 JSONL records in one foreground process and
  emits one `agentgov.coding-agent-response` per accepted event.
- The host envelope deliberately excludes raw prompts, responses, source,
  absolute host paths, changed-path claims, task identity, and authority flags.
  Unknown fields and unsafe evidence references stop the stream at the exact
  input line before that event reaches the coordinator.
- AgentGov derives working-copy identity, active task identity, and actual Git
  changes locally. Adapter validation remains context only; scope decisions
  and completion review still require human-originated events.
- Repository activation and task request events return concise task cards.
  Completion requests return concise completion cards sourced from AgentGov's
  scope, validation, and reconciliation results. Offered actions grant no
  scope, exception, commit, merge, release, or deployment authority.
- The existing single-cycle `agentgov dev` interface and headless lifecycle
  fallbacks remain compatible. Stable 0.2.1 and immutable `v0.3.0rc1` are
  unchanged; no consumer repository or external system was modified.
- Focused transport, coordinator, trigger, task, and documentation validation
  passed 56 tests. The complete supported-Python 3.11 suite passed 576 tests
  with one platform-limited skip. Repository governance reported
  `PASS=26 WARN=2 FAIL=0 ADVISORY=4`; the admitted task reported
  `PASS=6 FAIL=0 ADVISORY=1`; final changed-file scope reported
  `PASS=25 FAIL=0 ADVISORY=1`; all schemas parsed as JSON; and
  `git diff --check` passed.
- The follow-on Codex Adapter maps official `SessionStart`,
  `UserPromptSubmit`, `PostToolUse`, and `Stop` hook events to the existing
  vendor-neutral lifecycle. It hashes host session/turn identity and discards
  prompt, tool input/output, transcript, assistant-message, model, and absolute
  host-path values before producing AgentGov events or Codex hook output.
- `PostToolUse` reports scope failures as after-the-fact observations and never
  claims the completed tool side effect was undone. `Stop` uses
  `stop_hook_active` to prevent automatic completion-continuation loops.
- `agentgov integrate codex-hooks . --dry-run` previews an exact project
  `.codex/hooks.json`. Apply is create-missing-only with exact interactive
  confirmation, refuses overwrite/merge, installs no plugin, and leaves Codex
  hook trust as a separate user action.
- `agentgov.host-interaction-capabilities` 1.0 and
  `agentgov.host-interaction-request` 1.0 now separate Core human gates from
  host presentation. Missing admission, material scope resolution, and
  review-ready completion receive deterministic request IDs, bounded options,
  and an explicit delivery/recording mode; no displayed action applies a
  decision or grants consequential authority.
- The Codex binding declares task, scope, and completion interactions as
  `context_only` with decision recording `unavailable`. Its official
  `PermissionRequest` hook remains `native` and host-managed: AgentGov returns
  neither allow nor deny, so Codex keeps its normal human permission prompt.
  Tool permission is not treated as AgentGov task, scope, exception, or
  completion approval.
- Host-interaction closeout passed 599 Python 3.11 tests with one
  platform-limited skip. Repository governance reported
  `PASS=26 WARN=2 FAIL=0 ADVISORY=4`; the admitted task reported
  `PASS=6 WARN=0 FAIL=0 ADVISORY=1`; final scope reported
  `PASS=40 FAIL=0 ADVISORY=1`; 36 schemas parsed; the updated Codex integration
  preview remained read-only; and `git diff --check` passed.
- Codex Adapter closeout passed 589 Python 3.11 tests with one platform-limited
  skip. Repository governance reported `PASS=26 WARN=2 FAIL=0 ADVISORY=4`;
  the admitted task reported `PASS=6 WARN=0 FAIL=0 ADVISORY=1`; final scope
  reported `PASS=32 FAIL=0 ADVISORY=1`; 34 schemas parsed; the create-only
  integration preview stayed read-only; and `git diff --check` passed.

### Development checkpoint - 2026-08-05

- The future 0.3 managed governance workflow template now exposes a
  default-off `publish_development_monitor` manual-dispatch input and an
  optional repository-relative `development_export` input.
- An explicitly requested run renders `ci_only` by default,
  `exported_development` from a validated metadata-only export, or `combined`
  only when actor-validated CI event files are also present. The separate
  artifact uploads only `agentgov-development-monitor.html`, never the input
  export, raw events, or `.agentgov/` local state.
- Stable 0.1/0.2 rendered workflow bytes remain unchanged. No live workflow,
  release identity, consumer repository, NYC project, AI Radar runtime, merge
  automation, or deployment was changed.
- Read-only `agentgov next` now preserves adoption conflict, missing-scaffold,
  and repository-FAIL precedence, then selects exactly one dry-run start,
  check, finish, or Monitor action from the strict active session and its
  current immutable events. It never executes the selected command.
- ADR-0010 records the refined precedence. Multiple admitted tasks require an
  explicit human choice; old events cannot establish current progress; invalid
  sessions, missing starts, task drift, invalid events, and failed scope fail
  closed as one blocking action.
- Focused guided-next, session, and documentation validation passed 46 tests.
  The full source suite passed 527 tests with one platform-limited skip.
- The exact-wheel independent-repository rehearsal of this route is complete.
  The isolated `0.3.0.dev0` wheel moved from onboarding through explicit task
  choice, start, check, verified finish, and a four-event local Monitor while
  every `next` invocation left normalized Git status unchanged.
- ADR-0011 now separates the reviewed fixed-wheel public bootstrap from the
  installed `agentgov update --check` surface. Development metadata still has
  no release artifact, and a read-only update check alone cannot advance the
  action loop.
- ADR-0012's verified-session handoff/rollover is now implemented in
  development source. `govern handoff` re-establishes fresh evidence, previews
  one stable append-only `session.handed_off` event, requires exact interactive
  `HANDOFF`, retains the pointer and immutable evidence, and is idempotent.
- Monitor schema 1.4 retains schema 1.3's separation of verified completion
  from handed-off routing while adding Live Sessions and Protection Events.
  Read-only `next` excludes the same digest and offers a separate
  `--replace-active` preview for zero, one, or several remaining task choices.
- The exact `0.3.0rc1` wheel completed the independent terminal-route rehearsal
  in three disposable repositories. Verified finish, Monitor guidance, exact
  `HANDOFF`, pointer preservation, idempotence, zero/one/many rollover, and
  exact `REPLACE` passed without `next` changing Git state or importing from
  the source checkout.
- All 17 previously admitted delivered task contracts are now paused so they
  no longer compete in automatic discovery. Their rationales explicitly state
  that this is routing hygiene, not semantic completion or release evidence;
  one admitted RC closeout task remains discoverable.
- Source, bundled metadata, and release notes agree on `0.3.0rc1`. The tag and
  GitHub Pre-release were published from commit `66efecc`; the release workflow
  and its artifact-bound immutable manifest passed. The public rc1 manifest
  conservatively lists only `0.1.0` in `supported_from` because the candidate
  workflow omitted the reviewed metadata input. The source workflow now passes
  `release/current.json` for later candidates; immutable `v0.3.0rc1` is not
  rewritten. Stable promotion and consumer migration remain later work.
- Bootstrap/update documentation, `next`, and updater validation passed 56
  focused tests. The final full source suite passed 528 tests with one
  platform-limited skip.
- Verified-session handoff contract validation passed 65 focused tests. After
  recording the decision, the final full source suite passed 529 tests with
  one platform-limited skip.
- Verified-session handoff implementation validation passed 81 focused tests.
  The final full source suite passed 539 tests with one platform-limited skip.
- Installed RC handoff rehearsal evidence is recorded in
  `docs/experiments/handoff-installed-rc-rehearsal.md`; the exact wheel was
  266304 bytes with SHA-256
  `069d9470ef7acabe0cd827f7957be31f261fd8f39e2053935ee664b7b0a06540`.
- Final local RC gates: all 18 task contracts valid; closeout scope
  `PASS=63 FAIL=0 ADVISORY=1`; repository governance
  `PASS=16 WARN=2 FAIL=0 ADVISORY=4`; 539 tests passed with one
  platform-limited skip; bundled and generated RC manifests valid; diff check
  clean.
- The development-governance drift-correction slice adds three installable
  protocols and one provisional capability, preserves exactly one admitted
  task after routing cleanup, and changes no consumer repository, workflow,
  tag, release, or external system. Current validation passes 544 tests with
  one platform-limited skip and the repository check reports
  `PASS=26 WARN=2 FAIL=0 ADVISORY=4`.
## Relocated from `DEVELOPMENT_PLAN.md`: current state and foundation history

Original boundary: `Current State` through the end of `Foundation
implementation history`.
### Current State

Status: published stable `0.2.1`; published Pre-release `v0.3.0rc1`. The
repository-local minimum sufficient Kernel baseline is accepted in ADR-0016,
with a dated diagnostic classification and no runtime, schema, release, or
consumer change. This is an architecture stop condition, not a development
freeze. The
accepted automatic primary experience is not yet implemented. Its first
internal contract slice now provides a read-only active-session state
projection, vendor-neutral adapter trigger envelope, and Monitor 1.4 Live
Sessions / Protection Events read models. The next slice now also implements
one explicit `agentgov dev` foreground cycle, a minimal repository-state
reference adapter, automatic scope/completion actions, Dashboard refresh, and
human-review handoff. A generic strict JSONL foreground transport, bounded
task/scope/completion cards, and the first packaged Codex lifecycle-hook Adapter are
now implemented in development source. A vendor-neutral host-interaction
request/capability contract is also implemented, with Codex custom governance
decisions honestly limited to context-only delivery. A reference host Adapter
now converts ordinary request text through a replaceable semantic materializer
into the existing strict proposal and read-only admission plan. Development
Codex Adapter `1.3.0` now connects the current Agent as the first production
materializer and MCP form elicitation as its native exact-plan review surface;
local installation and installed-runtime preflight now pass. The first approved
event-level attempt stopped in its host bridge during App Server initialization
without an observable thread or proposal form. The separately approved
null-stream retry passed local initialization and thread probes, then its real
turn ended at App Server EOF before a form or tool result. The standalone CLI
then reported `Not logged in` with no inheritable credential environment
variable. Live proposal review remains unproven; authentication repair and
another replay are not admitted. Proactive prompt/result
contracts and a reference
single-selection review path are implemented; a native authenticated decision
surface and the complete automatic
journey remain open. A vendor-neutral governed clarification protocol now
keeps business, requirement, and architecture drift discussion separate from
the final human direction decision. The live foreground Coding Agent stream
now automatically carries normalized alignment context, human clarification
updates, and the final direction result in memory. A host-side reference
Alignment Adapter now proves the smaller natural-language alignment journey:
the host materializer derives normalized drafts, the Adapter supplies strict
envelopes, the user answers naturally and finishes with one selection, and the
privacy-safe trace reports zero user-authored JSON or commands. This is an
offline integration rehearsal, not a production semantic materializer or the
complete automatic development journey. No NYC
development-loop pilot or 0.3 consumer migration has occurred.

The 2026-08-06 native Codex MCP work now proves five-tool discovery, automatic
alignment selection for a delegated product choice, human ownership of the
final direction, and fail-closed stopping. The latest uncoached replay still
failed because the MCP schema allowed deterministic semantics for business,
requirement, and architecture drift while Core requires those judgment-bearing
kinds to remain advisory. The admitted bounded correction aligns that schema,
adds privacy-safe retry classification, and precedes one new installed-runtime
replay. NYC, another host, stable promotion, release, and
deployment remain gated on completion of human direction selection and
current-Agent advisory self-review.
The corrected local runtime is installed and has passed Adapter `1.2.1`,
five-tool, conditional-schema, and same-process retry preflight. A newly created
uncoached Codex session then corrected its first drift error but stopped on a
second unclassified rejection. Normalized diagnosis found that a no-unknown
context could omit Core's required stable option set or recommendation.
Development Adapter `1.2.2` now exposes and precisely classifies that rule;
full validation precedes any separately reviewed reinstall and replay.
Adapter `1.2.2` is now installed and its exact conditional schema plus
same-process two-error correction path have passed preflight. The remaining
newly created uncoached replay still stopped on another unclassified start
rejection. Development Adapter `1.2.3` now applies a complete, documented
eleven-family Alignment Start parity audit rather than another single-symptom
patch. Full validation passed, and the exact source is now installed in the
Python 3.12.10 pipx runtime with protocol preflight complete. The product owner
approved one external fresh session, but its normalizer mixed actual events
with historical repository text; raw events were not retained, so the outcome
is invalid rather than successful evidence. A separately approved replay used
an event-scoped normalizer and passed the intended Start boundary: the fresh
session corrected one retryable Start input, reached `ready_for_decision`, and
stopped for human selection without an internal/unclassified error. The human
then selected a bounded deterministic post-selection slice. Development Adapter
`1.2.4` now validates Resolve and current-Agent self-review inputs before state
mutation and supports corrected same-process retry. At that checkpoint a live
post-selection implementation, validation, and self-review journey remained
separately gated; the current-session continuation below later closed that
current-host gate.
The independent installation-gate review found and corrected five remaining
downstream parity gaps covering reason identifiers, evidence length and allow-
list membership, observation list bounds, and duplicate observations.
Renewed focused, full-suite, governance, and atomic-retry validation now passes;
the exact current wheel is installed in the existing Python 3.12.10 pipx
environment and installed-runtime protocol/schema/atomic-retry preflight passes.
The human product owner designated the current ephemeral Codex session as the
sole approved replay, selected the recommended direction, and prohibited another
session or Agent. The current native journey bound that human selection through
Alignment Resolve, and focused plus complete 734-test Python 3.12 validation
passes. Current-Agent MCP self-review then completed with bounded advisory
observations and no AgentGov model/network calls or Adapter context retention.
This slice is complete; another host, NYC, release, and its then-undecided next
requirement remain outside it. The later human-selected reference proposal
generation seam is now implemented separately.

ADR-0014 and the strict Provider-capability, risk-route, and advisory-result
contracts now implement the model-free semantic-review boundary. Low risk does
not request semantic review; medium risk binds the active Coding Agent's
existing entitlement as disclosed self-review; high risk binds a qualifying
independent Reviewer or exposes exactly three unselected human choices without
silent downgrade. Cross-host fixtures exercise one vendor-neutral parser, but
perform no inference. The host-neutral active-Agent materializer seam is now
connected to the resolved `ReferenceAlignmentAdapter` journey: it invokes one
supplied host callback with normalized ephemeral context and accepts only the
exact advisory result. The next bounded dependency is installing that callback
in one real Coding Agent surface; an external independent Reviewer remains a
later optional integration.

Current product priority: turn the now-implemented installation, update,
onboarding, task admission, architecture context, changed-file, fresh-evidence,
completion, event, Monitor, handoff, and routing primitives into one automatic,
event-driven coding-agent governance experience. Ordinary users should request
work through their coding agent, confirm only real scope or authority
boundaries, and review an automatically updated protection and benefit
Dashboard. The existing command sequence remains a development and fallback
surface. ADR-0013 and
`docs/product-requirements-automatic-governance.md` own this direction; the
detailed ordering is in `docs/development-plan.md`.

Implemented foundations:

- one package-version source shared by build metadata, structured producer
  metadata, and `agentgov --version`;
- a strict local release-manifest contract and validator for future RC
  compatibility metadata;
- verified stable-release discovery, bounded download, SHA-256 validation,
  pipx upgrade, new-process continuation, and repository refresh through
  `agentgov update .`;
- separate tag-triggered stable and release-candidate publication of an
  immutable release manifest and universal wheel through GitHub Releases;
- safe initialization of new or empty repositories;
- create-missing-only adoption for existing repositories;
- read-only repository inspection and checks;
- strict capability, evaluation, case, adoption-report, and repository-report
  contracts;
- repository-local reference validation;
- deterministic capability artifact export and artifact drift checks;
- Markdown, JSON, and self-contained HTML reports from one findings model;
- stable CLI exit semantics;
- agent-skill contracts;
- explicit human authority boundaries;
- cross-platform CI definition.

Completed on 2026-07-23:

- evaluation readiness was separated from evaluation decision outcome;
- relative baseline regression thresholds were added;
- review dates and accepted/rejected decision evidence were added;
- Prompt Capability was generalized into canonical AI Capability fields;
- new scaffolds moved to the `governance/` layout;
- read-only legacy support for `prompt-governance/` was retained;
- simultaneous canonical and legacy layouts became a deterministic conflict;
- ADR-0001 and ADR-0002 recorded the durable decisions.

### Foundation implementation history

The sections below preserve the foundation and adoption sequencing that
produced stable 0.2.1 and the future 0.3 source work. They are not the current
priority order. `docs/development-plan.md` owns the active P0 coding-agent
development loop defined by ADR-0009.

#### Pre-pilot credibility hardening

Goal:

Make the starter's own contracts, status, reports, and CI internally
consistent before adding repository inventory or beginning an external pilot.

In scope:

- explicit canonical capability contract identity;
- bounded read-only legacy compatibility and lifecycle documentation;
- truthful current status separated from historical development logs;
- AI Capability terminology on current product surfaces;
- report schema version separated from tool producer version;
- one truthful repository capability manifest;
- repository self-check and report artifact in CI.

Acceptance signals:

- canonical manifests cannot omit or contradict their contract identity;
- legacy manifests without identity remain readable with the existing
  layout-level migration warning;
- the repository's status does not describe committed work as uncommitted;
- JSON reports identify the producing agentgov version;
- the repository runs its own governance check in CI;
- the complete unit-test suite and `git diff --check` pass.

Stop conditions:

- do not add Taxi-specific contracts or policy;
- do not implement inventory, controls, dependency propagation, or profiles in
  this slice;
- do not weaken a deterministic failure to make self-check pass.

#### Repository Inventory and Control Evidence

Goal:

Create an explicit, reviewable chain from governed capability inventory to
implementation controls and verification evidence.

This track must not claim automatic AI-capability discovery. It validates the
completeness and consistency of declarations made by accountable repository
owners.

#### Slice 1 — Governance Inventory

Completed on 2026-07-24.

Planned canonical file:

```text
governance/inventory.json
```

Minimum contract:

- schema version;
- capability name;
- manifest reference;
- owner;
- governance status;
- explicit exclusions with path and reason.

Deterministic checks:

- every inventory capability references an existing manifest;
- every canonical manifest appears in the inventory;
- capability names are unique;
- capability and manifest identities agree;
- every capability has an owner;
- exclusions contain a non-empty reason;
- paths remain repository-relative and cannot escape through traversal or
  symbolic links.

Advisory boundary:

- the checker cannot prove that every real AI capability was declared;
- exclusions may be structurally valid while still requiring human judgment.

Acceptance signals:

- passing, warning, failing, and not-configured fixtures exist;
- initialized repositories receive an honest starter inventory;
- legacy repositories remain readable;
- no percentage or weighted score is emitted.

#### Slice 2 — Orphan Evidence Checks

Completed on 2026-07-24.

Goal:

Detect declared evaluation and artifact directories that cannot be connected
to the governed inventory.

Implemented checks:

- manifest not listed in inventory;
- inventory item without manifest;
- evaluation bundle with unknown capability;
- artifact directory with unknown capability;
- declared capability without expected evidence, where policy requires it.

Acceptance signals:

- orphan evaluation and orphan artifact fixtures fail deterministically;
- optional evidence remains WARN or not applicable according to explicit
  policy;
- no repository content is inferred from matching filenames alone.

#### Slice 3 — Control Mapping

Completed on 2026-07-24.

Canonical path:

```text
governance/controls/<capability-name>.json
```

Minimum control contract:

- capability name;
- control ID;
- objective;
- applicability;
- enforcement mode for applicable controls;
- implementation references;
- verification references;
- owner;
- exception authority;
- rationale for not-applicable controls.

Supported enforcement modes:

- `deterministic`;
- `platform_enforced`;
- `human_procedural`;
- `advisory_only`.

Deterministic checks:

- control IDs are unique;
- referenced capability exists;
- implementation and verification references are safe and readable;
- owner and exception authority are present;
- applicable enforcement mode is supported;
- not-applicable controls have a rationale and no enforcement evidence fields.

Advisory boundary:

- file existence does not prove that a control is effective;
- semantic sufficiency and exception quality remain human judgments.

#### Slice 4 — Capability Dependencies

Completed on 2026-07-24.

Goal:

Represent explicit capability-to-capability dependencies without assuming that
all pipelines share one readiness model.

Canonical path:

```text
governance/dependencies/<capability-name>.json
```

Implemented design:

```json
{
  "depends_on": [
    {
      "capability": "prepare-features",
      "minimum_readiness": "baseline_ready"
    }
  ]
}
```

Deterministic checks:

- referenced capabilities exist;
- declaration owners and endpoints close to Governance Inventory;
- self-dependencies fail;
- cycles fail;
- explicitly declared minimum readiness is satisfied.

Do not automatically fail merely because downstream and upstream readiness
labels differ when no minimum was declared.

Advisory boundary:

- an empty dependency array is a valid explicit declaration;
- static checks cannot prove that every runtime or organizational dependency
  was discovered;
- dependency declarations do not enable automatic risk propagation or runtime
  orchestration.
## Relocated from `DEVELOPMENT_PLAN.md`: next recommended starting point

Original boundary: `Next Recommended Starting Point` through its final
`Next session after the 2026-08-07 checkpoint` subsection.
### Next Recommended Starting Point

Review the accepted ADR-0016 baseline with the product owner before selecting
the next requirement. A real independent consumer journey is the next useful
source of Kernel counterevidence, but consumer selection, repository changes,
required checks, branch protection, and merge proof require a separate admitted
task. Do not reopen Kernel promotion without ADR-0016's structured failure
case.

The 2026-08-11 product review selected AIRBNB for the first bounded consumer
slice. Its repaired native path first demonstrated proposal review, exact human
admission, create-only task recording, a two-line README implementation,
static validation, and a distinct advisory review. A separately admitted
2026-08-13 cumulative journey has now closed the remaining bounded transition
gap: the research-only scenario and all 79 tests passed under Python 3.11.9,
AgentGov reconciled fresh evidence as Completion Verified, and the human
separately confirmed Bounded Handoff. Proposal-only work used a disclosed
bounded current-Agent advisory review and did not claim native alignment
self-review completion. This is one consumer's lifecycle evidence, not proof of
the automatic primary experience, product effectiveness, independent review,
consumer Git publication, CI enforcement, release, deployment, or production
pricing authority. The consumer working tree remains uncommitted and unpushed.
Review this completed requirement with the product owner before selecting
another consumer or product capability.

The product owner next selected a sanitized record of the completed NYC
consumer journey. Its existing synthetic sample exercised schema validation,
temporary Bronze and Silver construction, the demand quality gate, and
non-empty Gold lineage under Python 3.11.9. The focused scenario and all 68 NYC
tests passed; repository governance reported 17 PASS, 1 WARN, and 0 FAIL, and
all 4 agent-skill contracts passed. AgentGov reconciled fresh evidence as
Completion Verified and the human separately confirmed Bounded Handoff, with an
idempotent repeat preview. NYC's formal CI remains on AgentGov 0.2.1 and the
local 0.3.0rc1 journey is not a formal upgrade. This second consumer improves
portability evidence but does not prove automatic adoption, production forecast
quality, product effectiveness, independent review, release, deployment, or
external authority. Its consumer changes remain uncommitted and unpushed. The
next product capability is not yet decided.

On 2026-08-14 the product owner selected one fresh live AIRBNB uncoached
baseline after a governed comparison with an offline Harness-first route. The
single session discovered all seven configured tools and selected the correct
proposal-review capability without coaching. Its first two normalized proposal
drafts failed safely on non-repository-relative excluded scope paths; the third
completed with a bounded declined result, while no native form reached the
client and no human decision, task creation, README/source change, or aggregate
runtime-state metadata change occurred. The First Deviation is Agent
materialization, followed by incomplete host-form mediation. This is observed
no-write evidence only and does not close the automatic independent-rehearsal
gate. Harness Contract v1 is the next candidate connection for deterministic
transition and deviation fixtures; another live replay remains unauthorized.
The product owner subsequently selected and admitted that offline route.
Development source now implements `agentgov.harness-run` 1.0 as a strict schema,
dependency-free validator and First Deviation evaluator, plus sanitized
matching and AIRBNB fixtures. This first vertical slice keeps Agent selection,
AgentGov decision correctness, and intervention outcome separate; rejects raw
replay material and false host-enforcement claims; and names four bounded
evidence-strength levels without promoting fixture results into causal or
aggregate-effectiveness claims. A public CLI, live host Adapter, controlled
ablation, Dashboard integration, consumer adoption, release, and deployment
remain outside this requirement. The next product connection is not yet
decided.

Subject to that separate decision, continue productizing the implemented
ADR-0009 loop:

1. [Completed internal pilot] Preserve the installed-build independent
   repository evidence, including actual Coding Agent context consumption,
   fail-closed Skill and validation-artifact findings, and the explicit limit
   that this was not an uncoached human study;
2. [Completed development preview] Define the explicit redacted event-export
   contract so local history can be carried into CI without pretending the CI
   replay observed development. The metadata-only bundle is immutable,
   integrity-checked, explicitly confirmed, and now supports honest
   `exported_development` and `combined` Monitor views;
3. [Completed prerequisite] Give development source a distinct
   `0.3.0.dev0` runtime and bundled-metadata identity while retaining stable
   0.2.1 as the published consumer fact;
4. [Completed prerequisite] Synchronize README, status, plans, public HTML,
   localized guides, sample reports, release facts, and protecting tests; keep
   AgentGov's product page primary and AI Radar as a bounded origin reference;
   publish Portfolio evidence by applying the shared reference layout directly
   to authoritative Markdown, rather than raw Markdown, conflicting proxy
   outputs, or project-root-escaping schema links;
5. [Completed development preview] Wire the static Monitor as a default-off
   GitHub Actions artifact. The future 0.3 managed workflow now requires an
   explicit manual-dispatch boolean, accepts only an optional validated
   metadata-only development export plus actor-validated CI events, and uploads
   only the self-contained HTML read model. Stable workflow bytes, release
   identity, and consumer files remain unchanged;
6. [Low-level guided routing and installed rehearsal implemented] Converge installation, update,
   onboarding, task admission, and Monitor generation on the same small guided
   workflow without hidden hooks or daemon authority. `agentgov next` now
   bridges onboarding and deterministic repository failures into strict
   start/check/finish/Monitor session routing. An exact `0.3.0.dev0` wheel
   completed the independent zero-task, multiple-task, and full lifecycle
   rehearsal without `next` changing Git state. A truthful pre-install
   bootstrap boundary is now decided by ADR-0011: fixed stable installation
   precedes the CLI, while installed `update --check` remains separate from
   `next`. Runtime update routing remains blocked until a reviewed stable
   artifact and non-looping verified-session handoff exist. ADR-0012's
   event-only, pointer-preserving handoff and separate `--replace-active`
   rollover are now implemented in development source. The exact `0.3.0rc1`
   wheel completed verified finish, Monitor, handoff, zero/one/many rollover,
   and exact `REPLACE` in independent repositories without source-path leakage;
7. [Release candidate published] Preserve `v0.3.0rc1` as immutable evidence of
   the low-level lifecycle primitives; do not treat it as proof of the final
   user experience;
8. [Codex hooks Adapter implemented in development source] Preserve the strict
   `agentgov dev --stream` transport while mapping Codex `SessionStart`,
   `UserPromptSubmit`, `PermissionRequest`, `PostToolUse`, and `Stop` through a
   create-only, separately trusted project hook integration. Add another host
   only when portability evidence requires it;
9. [Proactive minimal-input decision contracts implemented; native authenticated
   UI remains] Preserve vendor-neutral capability, interaction-request,
   decision-prompt, and decision-result contracts. Capable hosts proactively
   present one recommended single-select choice and return only its exact
   transition; the reference terminal uses one number with no free text. Codex
   keeps its normal human tool permission prompt, but Hooks do not provide
   arbitrary trusted task/scope/completion button callbacks;
10. [Structured task admission and risk routing implemented] Preserve the strict
    vendor-neutral proposal and admission-plan contracts. A proactive numeric
    human-review selection may create the exact manually reviewed low-risk
    task; exact interactive `ADMIT` remains a fallback, while a
    clean human-owned standing policy may non-interactively fast-track only its
    narrow declared envelope. No-write and exact active-task continuation need
    no admission or interruption. The reference host-side natural-language
    proposal seam is implemented with an offline materializer fixture.
    Development Codex `1.3.0` connects the current Agent and native MCP form;
    local installation/preflight pass, while external live proof and other
    hosts remain separate work;
11. [Friction budget implemented] Preserve zero interruptions for no-write,
    active-task, and fast-track routes, at most one for ordinary bounded
    review, and full review for material characteristics;
12. [Governed clarification implemented] Preserve the current center while
    material meaning is unsettled, ask one natural-language question per turn,
    keep normalized discussion turns outside the governance-decision budget,
    and offer one digest-bound direction choice only after options stabilize.
    The foreground Adapter stream now returns those prompts automatically from
    strict normalized records, with no restart-persistence claim;
13. [Native MCP Adapter, proposal-review installation, and local preflight
    implemented; external replay remains] Preserve the five-tool normalized
    alignment/self-review journey and capability-gated sixth proposal tool,
    explicit foreground handle, exact pending bindings, and create-missing-only
    Codex config. Ordinary users add no protocol JSON, protocol question IDs,
    repeat confirmation, or second-model setup. Known invalid normalized input
    now receives privacy-safe structured field/rule/retry diagnostics without
    partial state. The exact `1.3.0` source is installed and locally preflighted;
    run a fresh external replay only after separate human approval. Another MCP
    host and the optional independent high-risk Reviewer path remain later
    choices;
14. [Per-cycle automation implemented; richer views remain] Extend the
   automatically refreshed Live Sessions, Protection Events, and Task Detail
   views with explicit resolution links, and add denominator-aware
   Benefit and Learning views without turning the Dashboard into a source of
   truth or a score;
15. [Gate before NYC] Prove one ordinary low-risk task in an independent
    non-NYC repository without hand-authored internal JSON, repeated state
    queries, manual lifecycle command composition, or special confirmation
    words in the primary UI;
16. [External feedback after the gate] Use NYC as the first real consumer,
    keep NYC-specific policy local, classify feedback before admission, and
    modify AgentGov only for general gaps;
17. Keep stable promotion, consumer migration, publication, and deployment as
    later, separate human-approved actions.

The automatic independent rehearsal, uncoached adoption evidence, NYC feedback
record, stable 0.3 promotion, NYC migration, and PyPI decision remain open.
NYC feedback cannot replace general product admission, and the low-level
command sequence cannot replace the automatic user experience as product core.

#### Next session after the 2026-08-07 checkpoint

Development Adapter `1.3.0`, the current-Agent proposal materializer, native
MCP proposal-review form, strict admission boundary, and installed-runtime
preflight are complete. The first two authorized external attempts did not
measure that Adapter path: the corrected bridge reached `turn/start`, then the
standalone Codex App Server closed before returning a form or tool call. The
same binary subsequently reported `Not logged in`, with no inheritable Codex or
OpenAI credential environment variable. This is a host-authentication gate,
not Adapter success or failure.

Resume in this order:

1. review and separately authorize repair of the standalone Codex host's
   authentication; do not change AgentGov Core, repository scope, or product
   authority to work around the host failure;
2. verify login status and complete a local initialization/thread/MCP
   capability preflight without sending a task;
3. obtain separate approval for one fresh event-level proposal-review replay;
4. if the native form appears, let the human review the exact proposal and
   record only the selected transition; do not implement an admitted proposal
   without another explicit product-owner decision;
5. review the resulting evidence with the product owner before selecting the
   next requirement. Another host, the independent non-NYC rehearsal, NYC,
   stable promotion, release, and deployment remain later gates.

Do not begin dependency risk propagation, repository profiles, governance
scoring, or taxonomy expansion before pilot evidence justifies the change.
## Relocated from `docs/development-plan.md`

Original boundary: `Current checkpoint` through the end of `Next-session
starting point`.
### Current checkpoint

The repository-local architecture baseline is now accepted in ADR-0016. It
defines a minimum sufficient Kernel, keeps Policy, Application,
Adapter, Consumer Context, Experiment, and per-transition enforcement distinct,
and preserves Completion Verified as separate from Bounded Handoff. The dated
2026-08-10 classification is diagnostic rather than a permanent registry. It
adds no runtime, schema, release, consumer, or external enforcement change.

New Kernel promotion is paused until a real journey supplies ADR-0016's
structured counterexample. This pause does not block bounded Application,
Adapter, Policy, consumer, or bug-fix work.

An independent AIRBNB consumer replay exposed a general adoption gap: Codex
loaded one healthy AgentGov MCP server in a trusted project, but the generated
consumer `AGENTS.md` lacked the native-tool selection journey, so the Agent
implemented a low-risk README fix with zero AgentGov calls. The generated
template and initializer protection now carry matching admission, alignment,
self-review, drift-review, and fail-closed triggers. A third replay proactively
selected native proposal review and made no requested write, but failed before
the form because the consumer lacked `governance/tasks/`. New scaffolds now
track `governance/tasks/.gitkeep`. AIRBNB has now adopted that repair. A fresh
form-presenting replay created an exact human-admitted task record, changed only
two README demo command lines, passed static diff and task validation, and
received a distinct advisory review with no observed scope or authority drift.
That partial 2026-08-11 evidence is now superseded for the remaining bounded
transitions. A separately admitted 2026-08-13 cumulative journey ran the
research-only scenario and all 79 tests under Python 3.11.9, reconciled admitted
scope and fresh evidence as Completion Verified, and recorded a separate
human-confirmed Bounded Handoff. Because these were proposal-only tasks, the
same Agent performed and disclosed the bounded advisory review without claiming
native alignment self-review completion. This does not prove the automatic
primary experience, product effectiveness, independent review, commit, push,
CI enforcement, release, deployment, production pricing authority, or another
consumer's result. The consumer working tree remains uncommitted and unpushed.

NYC now adds a second independent consumer journey. Its existing synthetic
sample ran schema validation, temporary Bronze and Silver construction, the
demand quality gate, and non-empty Gold lineage under Python 3.11.9. The
focused scenario and all 68 NYC tests passed, repository governance reported
17 PASS, 1 WARN, and 0 FAIL, and all 4 agent-skill contracts passed. AgentGov
reconciled fresh evidence as Completion Verified and the human separately
confirmed Bounded Handoff; the repeat preview was idempotent. NYC's formal CI
remains on AgentGov 0.2.1, and the local 0.3.0rc1 journey is not a formal
upgrade. This does not prove uncoached adoption, production forecast quality,
product effectiveness, independent review, release, deployment, or external
authority. The NYC consumer changes remain uncommitted and unpushed. A next
product capability has not yet been selected.

- Published stable: AgentGov 0.2.1; published Pre-release: v0.3.0rc1.
- NYC consumer: managed 0.2.1 workflow.
- Implemented locally for the future 0.3 line: persona-aware PR and owner UI,
  trusted-main benefit monitor, scheduled baseline refresh, redacted portable
  evidence, separate bounded Draft PR workflow, and pre-write current/target
  dry-run evidence. The managed governance template also has a default-off,
  manual-dispatch Development Monitor artifact path that uploads only the
  derived HTML.
- The generated two-workflow contract and fixture review is complete.
- Implemented in development source: a shared three-task/seven-day drift-review
  cadence, create-only human review/snooze records, a subordinate foreground
  reminder card, Development Monitor 1.5 state, and a future-version scheduled
  Actions warning/summary that remains green. Published 0.2.1 and v0.3.0rc1
  renderings remain unchanged; external notification writers remain deferred.
- Development Adapter `1.4.0` now binds that card to a capability-gated native
  MCP form. The Agent supplies only a normalized three-dimension advisory
  candidate and repository-relative evidence; the human records that exact
  candidate, snoozes, or writes nothing. Due-state revalidation, create-only
  records, and separately reported Monitor refresh prevent silent authority or
  retry drift. The exact source is now installed only in the existing local
  AgentGov pipx runtime and remains unpublished and consumer-inactive. One
  bounded direct App Server replay reached the form request and stopped without
  a human decision or write; live Agent selection and end-user presentation
  remain unproven.
- ADR-0009 now makes requirement, architecture, and coding-agent governance
  during development the primary product direction. PR/CI remains a backstop.
- Implemented in development source: compact/standard task-contract 1.1,
  read-only `agentgov check task`, artifact-owned Skill routing metadata, an
  in-memory Registry, and task-specific `agentgov context task` output in
  terminal, JSON, and Markdown with selection reasons and source hashes. The
  working-tree scope core now also inventories staged, unstaged, deleted,
  renamed, and non-ignored untracked paths and applies the deterministic
  segment-aware include/exclude policy through `agentgov check scope`.
  `agentgov govern check/finish` now adds local observations, canonical
  committed/dirty snapshot evidence, declared-command validation, and honest
  `verified`/`needs_evidence` reconciliation. `agentgov monitor development`
  now renders the validated local event stream as a static Overview, Activity
  Timeline, and Task Detail with explicit observation and claim limits. Guided
  `govern start` now previews and explicitly confirms one existing or compact
  task, derives selected governance, records one active task/base per working
  copy, and lets check/finish resume it without repeated arguments. Explicit
  `export development` now creates an immutable metadata-only bundle after
  preview and exact confirmation; Monitor ingestion supports honest
  `exported_development` and `combined` views with per-source event labels and
  counts. Read-only `agentgov next` now preserves onboarding and repository
  `FAIL` precedence, then derives exactly one start/check/finish/Monitor action
  from the strict active-session pointer and current-session events.
- Implemented in development source: ADR-0012's `govern handoff` re-establishes
  fresh verified evidence, previews one stable append-only event, requires
  exact interactive `HANDOFF`, preserves the pointer and prior artifacts, and
  makes repeated matching handoff idempotent. Monitor 1.5 retains the 1.3
  separation of verified completion from handed-off routing, and `next` filters the same digest before
  offering a separate `--replace-active` rollover.
- Not yet implemented: explicit exception records or action-loop
  self-reporting. Local-state transfer remains explicit; the workflow does not
  upload raw events or an export bundle.
- Completed independent installed-build pilot: the exact source wheel was
  installed with no runtime dependencies in a fresh environment and governed
  a real Coding Agent change in a repository with no AI Radar dependency. The
  corrected run reached `verified` and generated four Monitor events. The
  initial invalid Skill and unignored Python cache attempts remained visible as
  fail-closed product evidence.
- Completed exact-wheel guided-next rehearsal: an isolated `0.3.0.dev0` wheel
  preserved onboarding and explicit-choice boundaries, then selected check,
  finish, and Monitor in order for one verified task. All observed `next`
  calls were Git-non-mutating; the local Monitor contained four source-labeled
  events. This is internal deterministic plumbing evidence, not uncoached
  usability evidence.
- ADR-0011 completes the bootstrap/update boundary decision. Public fixed-wheel
  installation must precede the CLI; installed update inspection remains
  `agentgov update --check`; and update availability does not enter `next`
  while development metadata has no artifact or verified sessions lack a
  terminal handoff/rollover state.
- ADR-0012 completes the verified-session terminal contract. Exact `HANDOFF`
  now appends one `session.handed_off` event only after re-establishing
  fresh verified evidence; it retains the pointer and all prior artifacts, and
  leaves the next task to a separate reviewed `--replace-active` start. This is
  a routing transition, not approval or semantic completion.
- The source and bundled compatibility metadata identify as 0.3.0rc1,
  distinct from published stable 0.2.1. The GitHub candidate is published;
  its immutable manifest conservatively underclaims compatibility because the
  tag workflow omitted the reviewed metadata input. The source workflow is
  corrected for later candidates. Not yet completed: NYC 0.3 migration or
  evidence from real NYC runs. Those are supporting delivery tasks rather
  than the next product-defining slice.
- Public entry points now distinguish stable 0.2.1 from candidate source
  0.3.0rc1, use one isolated pipx user path, keep the AgentGov product page
  primary, and present AI Radar only as a bounded origin reference after the
  AgentGov evidence story.
- Portfolio raw-Markdown and out-of-root schema links now target project-local
  HTML. A live build exposed that same-name HTML proxies collide with Jekyll's
  Markdown output, so commit `743f3b3` applies the shared AgentGov layout
  directly to authoritative Markdown and removes those proxies. The follow-up
  Pages build and public URL replay passed for all reference and schema
  surfaces; published JSON schema copies remain byte-checked.

### Next-session starting point

First review the accepted baseline with the product owner and select the next
requirement separately. An independent consumer journey is the preferred next
evidence source, but no consumer, required check, branch protection, or merge
proof is authorized by the baseline task. Reject further Kernel expansion by
default unless a concrete transition fails the distinction-loss, substitution,
or authority-integrity test in ADR-0016.

The exact isolated `0.3.0rc1` wheel has completed the ADR-0012 rehearsal in
three independent repositories: verified completion, Monitor guidance,
handoff, zero/one/many rollover selection, and exact `REPLACE`. Seventeen
delivered historical tasks and the completed automatic-governance slices are
paused for routing hygiene. The native MCP alignment/self-review Adapter has
completed implementation and validation and is paused after human review. The
live uncoached Codex MCP rehearsal is the only admitted task. Its reviewed
project configuration is installed. Preparation found that the default
Python could not bootstrap pipx over TLS, so an authorized parallel official
Python 3.12 runtime was installed and used to build and pipx-install the exact
current-source `0.3.0rc1` wheel. `agentgov` is now available through the user
`PATH`, without borrowing another project environment or an absolute source
path. Exact human `INTEGRATE` then created the reviewed project config, and a
real-user Codex preflight discovered the enabled five-tool server with healthy
authentication and reachability. The eligible live journey then failed: the
host discovered and selected the tools, but Core rejected normalized alignment
before the human direction choice, so self-review did not begin. The reviewed
correction is implemented: MCP question meaning no longer carries a
model-authored protocol ID, known rejection returns bounded structured
diagnostics, and failed start/update calls remain atomic. Complete validation
passed. The post-correction replay still failed because the Agent bypassed the
tools, selected the product direction itself, and omitted self-review. The
tool-selection guidance task is complete and paused after its replay.
The post-guidance replay proved automatic selection, human direction ownership,
and fail-closed stopping, but alignment start still returned an unclassified
non-retryable Core rejection. The admitted bounded correction diagnoses that
remaining normalized Adapter/Core mismatch before another replay. NYC remains gated on a
replay that completes alignment and current-Agent self-review.
The corrected local runtime is now installed and has passed protocol, schema,
and same-process retry preflight. The sole remaining step is the fresh uncoached
Codex replay; this active preparation session is ineligible to supply it. That
fresh replay corrected the drift error but exposed the next unclassified
no-unknown/stable-options rule and stopped without mutation. Development source
now makes the two-option and recommendation requirements explicit; validation
and a separately reviewed reinstall/replay remain next.
Adapter `1.2.2` is now installed and has passed the exact five-tool,
conditional-schema, two-diagnostic, and corrected-ready preflight. Only a newly
created uncoached Codex session was eligible for the next measured replay. It
still stopped on an unclassified start rejection without mutation. Development
Adapter `1.2.3` now replaces serial fixes with a complete eleven-family Start
parity audit. Full validation and installed Python 3.12.10 pipx preflight now
pass. One approved external fresh session completed, but its normalized result
was contaminated by historical repository text and is not accepted as MCP-call
evidence. A separately approved replay measured only completed MCP tool-call
events and passed: two Alignment Start calls advanced from one retryable input
correction to `ready_for_decision`, then stopped at the human-selection
boundary. The product owner then selected the smallest deterministic
post-selection slice. Development Adapter `1.2.4` now gives Resolve and
current-Agent self-review repairable field/rule diagnostics before state
mutation, with corrected same-process retry. At that checkpoint live
post-selection implementation and self-review remained unproven and were not
implied by fixture evidence; the later current-session continuation below
supersedes that open-gate status for this host only.
An independent installation-gate audit then found and corrected five remaining
Adapter/Core boundary mismatches: reason identifiers, evidence length,
observation list bounds, evidence allow-list membership, and duplicate
observations. Renewed focused, full-suite, governance, and atomic-retry
validation passes. The exact current wheel is installed in the existing Python
3.12.10 pipx environment and installed-runtime protocol/schema/atomic-retry
preflight passes. At that installation checkpoint external replay remained a
separate human-controlled action; the following paragraph records its later
explicit approval and completion.

The human product owner then confirmed that the already-running ephemeral Codex
session was the one approved replay and prohibited another session or Agent.
Within that same session the native journey reached the human decision boundary,
recorded the selected `return_to_center` direction through Alignment Resolve,
and retained the denied authority boundary. Focused MCP/task-contract validation
and the complete 734-test Python 3.12 suite pass. The distinct current-Agent MCP
self-review also completed with bounded advisory observations, zero AgentGov
model/network calls, and no Adapter context retention. This live post-selection
slice is complete. The later human-selected reference proposal-generation seam
is now implemented separately; another host, NYC, release, production proposal
inference, and the next requirement remain outside it.

ADR-0013 now records the next product boundary: the implemented manual
`next/start/check/finish/Monitor/handoff` sequence is a set of internal and
fallback primitives, not the intended daily user experience. The next product
slice is a general, vendor-neutral, foreground automatic coordinator plus an
automatically refreshed protection and benefit Dashboard. It must pass an
independent non-NYC rehearsal before NYC is used as the first real consumer
feedback pilot.

The first two internal automation slices are now implemented in development source:
`agentgov.development-state` 1.0 projects validated active-session events into
one lifecycle stage and recommended operation, and
`agentgov.development-trigger` 1.0 defines privacy-bounded vendor-neutral
adapter events. Existing `next` active-session routing consumes the projection.
`agentgov.foreground-cycle` 1.0, `agentgov dev`, and the minimal reference
adapter now perform one explicit event cycle: implementation changes trigger
scope observation; completion requests trigger scope, admitted validation,
reconciliation, and Dashboard refresh; human review can hand off verified work.
Monitor 1.5 derives Live Sessions, Protection Events, and the advisory
drift-review reminder while keeping resolution unknown without an explicit
link. Development source now also
provides a strict foreground JSONL coding-agent process transport, bounded
task/scope/completion cards, a subordinate drift-review reminder card,
vendor-neutral host-interaction requests, and the
first packaged Codex lifecycle-hook Adapter. Codex preserves its native tool
permission prompt but custom governance decisions remain context-only and
unrecorded. Development source now also implements strict structured Coding
Agent proposal and exact human task-admission contracts without raw-prompt
retention or session start. A reference host Adapter now invokes one replaceable
semantic materializer for an ordinary request and produces that same strict
read-only admission plan. Development Codex Adapter `1.3.0` now binds the
current Agent as production materializer and MCP form elicitation as the native
exact-plan review surface. The exact source is now installed and locally
preflighted, and standalone authentication is repaired. A separately
authorized UTF-8-safe App Server replay completed a real read-only turn but
showed no native form. Its temporary text-presence heuristic conflated tool
inventory or instructions with a possible proposal call, so the run is
`INVALID_MEASUREMENT`, not Adapter pass/fail evidence. Test-only normalization
now fails closed unless exact proposal-call, elicitation, result, or terminal
event fields are present. One following authorized replay completed a real
ephemeral read-only turn with normalized state `not_called`, zero exact
proposal calls, and zero forms. This is valid evidence that the current Agent
did not enter the Adapter path for that bounded request; it is not an Adapter
pass/fail result.
Strict proactive prompt/result contracts now let a
capable host present one recommended single-select decision and carry only its
exact human-selected transition. Additional-host materializers, stronger
authenticated custom decision controls, protection resolution, and
Benefit/Learning remain.

After the `not_called` replay, the next-session gate was product review: decide
whether the observed `not_called` result reflects tool discovery, invocation
guidance, or a deliberate host-routing boundary, and whether addressing it is
still the right requirement. A no-turn App Server configuration/status probe
has now confirmed that the project MCP layer loaded and all six AgentGov tools
were exposed. A subsequent consumer replay loaded the generated journey but
still treated direct chat authorization as admission and skipped proposal
review and self-review. The selected bounded correction therefore requires a
readable, validated matching `governance/tasks/*.json` record with a human
admitted or approved decision before any repository write. Direct chat
authorization and tool permission do not count; every repository-changing
task requires self-review, while read-only work remains outside that path. This is a guidance
and metadata correction, not a protocol, schema, authority, or release change.
The separately authorized installation-only step is now complete: the exact
reviewed source was built offline, hash-recorded, installed only into the
existing AgentGov pipx environment, and locally preflighted with six/five-tool
capability behavior and the clarified trigger metadata. Project configuration
was unchanged and no Codex turn was started during installation. The product
owner then authorized exactly one fresh ephemeral read-only replay. Its
preflight again found the ready server and all six tools. During the one
ordinary turn, the exact proposal tool started once; the turn completed without
presenting an AgentGov form. No decision, task, implementation, or repository mutation
occurred, and no retry was sent. Product review must now decide whether the
invocation-to-elicitation gap is the next requirement. The completed bounded
diagnosis then confirmed official and generated-schema support for the form
request and used two no-model direct calls with the same valid arguments. App Server parsed
the Adapter elicitation and returned a zero-write `decline` because no active
turn hosted it. The live replay summary did not retain completion presence or
structured AgentGov tool-error fields, so it cannot localize the remaining
behavior. At that checkpoint product review had to decide whether a
privacy-bounded normalizer correction was next. The product owner selected that
evidence-only slice. The
test reducer now records deduplicated completion count/status, explicit
`completion_unknown`, and at most eight strictly validated AgentGov error
records while continuing to drop raw errors, arguments, content, and extensions.
This is a future-measurement correction, not a product or architecture change,
and it does not reclassify the historical replay. Product review must decide
whether any later replay is still valuable; it remains separately unauthorized.
Another host, the independent
non-NYC rehearsal, NYC adoption, stable promotion, release, and deployment
remain later gates.
Development source now also separates multi-turn natural-language
clarification from the final governance decision: it preserves the current
center, records business/requirement/architecture drift as advisory, retains
only normalized rolling summaries, and waits for stable choices before using
the existing single-select result. The same foreground Coding Agent stream now
accepts that normalized context and its human updates, then automatically
returns the next question or decision from memory-only state. A host-side
reference Alignment Adapter now rehearses natural request, natural
clarification, and one final single-select through a replaceable semantic
materializer. It retains only normalized evidence and reports zero
user-authored structured records or commands; production host materializers
remain open. See
`docs/development-automation-contracts.md`.

ADR-0014 and three strict contracts now implement the model-free
semantic-review boundary: Provider capability, risk route, and advisory result.
Low risk uses no semantic review; medium risk binds the active Coding Agent's
existing entitlement as disclosed self-review; high risk binds a qualifying
independent Reviewer or returns exactly three unselected choices without
silent downgrade. Cross-host fixtures prove contract portability, not model
inference. The resolved Alignment Adapter now exposes a host-neutral
active-Agent self-review materializer operation with evidence allow-list and
exact result binding. The same foreground stream now implements a strict
start/request/draft/completed exchange for that operation, including exact
alignment, Adapter, Provider, evidence, and pending-request binding. The next
bounded slice is now implemented as a foreground STDIO MCP Adapter with five
model-controlled tools and a create-missing-only Codex project configuration.
An uncoached live Codex rehearsal and then another native MCP-host proof remain;
optional independent-Reviewer integration follows only after that evidence.

The reviewed friction correction is now implemented in development source:
no-write requests and locally verified active-task continuation require zero
human interruptions; only a Git-tracked, clean, human-admitted standing policy
can fast-track a bounded low-risk task; ambiguity and material characteristics
route to review. Codex Prompt Hooks now request host-side structured routing
without forwarding the prompt or forcing every message through task admission.
The reference human-review path proactively shows approve/change/reject and
accepts one number without a magic word or free-text rationale. Codex Hooks
continue to disclose context-only/unavailable custom decision recording.

Do not rewrite `v0.3.0rc1`, publish another candidate, promote stable 0.3.0,
modify NYC, add automatic local-state upload, hidden daemon authority,
mechanical runtime interruption, merge authority, or deployment without a
separate decision.
