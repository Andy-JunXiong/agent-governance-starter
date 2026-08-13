# Agent Governance Starter Kit Status

Last verified: 2026-08-13

## Current state

- Version: published stable `0.2.1`; published Pre-release `v0.3.0rc1`.
- Maturity: experimental and suitable for repository-level evaluation.
- Canonical capability layout: `governance/`.
- Legacy `prompt-governance/` input remains a bounded, read-only compatibility
  surface.
- Portfolio links now target project-base-aware HTML outputs generated from
  authoritative repository Markdown. Commit `743f3b3` corrected a Jekyll
  same-destination collision by putting the AgentGov layout directly on those
  Markdown sources. The Pages build and all linked reference/schema surfaces
  are publicly verified; published schema copies remain byte-checked against
  their source contracts.
- Public entry and reference pages now declare canonical Open Graph and
  large-image card metadata backed by the repository-owned 1280 x 640
  `docs/assets/agentgov-social-preview.jpg`. GitHub repository cards require
  that same image to be uploaded separately through the repository Social
  preview setting; page metadata cannot change GitHub's repository card.
- Merge, publish, release, and deployment remain separate human-authorized
  actions.
- ADR-0016 now establishes the minimum sufficient Kernel baseline: the Kernel
  owns portable governance meaning and state semantics; Policy, Application,
  Adapter, Consumer Context, and Experiment responsibilities remain distinct;
  and enforcement is claimed per actual transition. The minimum journey keeps
  Completion Verified separate from Bounded Handoff. The accompanying
  2026-08-10 classification is diagnostic only. No runtime, schema, release,
  consumer, required-check, branch-protection, or merge-proof change is part of
  this baseline. New Kernel promotion is paused pending a structured concrete
  counterexample.
- An independent AIRBNB consumer rehearsal proved that a trusted project can
  load the configured AgentGov MCP server while still bypassing every native
  governance tool when its generated `AGENTS.md` lacks the selection journey.
  Development source now adds that portable journey to the generated template
  and protects initialization output: matching task admission precedes writes,
  material ambiguity uses human-resolved alignment, completion uses bounded
  self-review, due drift review remains human-owned, and required call failure
  remains fail-closed. A third replay with the stricter journey proactively
  selected `agentgov_task_proposal_review` and made no requested write, but the
  form could not open because the initialized consumer lacked a real
  `governance/tasks/` directory. Initializer output now tracks
  `governance/tasks/.gitkeep`, allowing the first proposal plan to remain
  create-only. AIRBNB has now adopted that repair. A fresh ordinary README
  usability request opened the native proposal form, received the exact human
  admission, created the matching consumer task record, changed only two
  command lines, passed `git diff --check`, and passed a read-only task check
  with `PASS=3 WARN=1 FAIL=0 ADVISORY=3`. A distinct advisory review found no
  scope or authority drift. That 2026-08-11 partial result is now superseded by
  a separately admitted 2026-08-13 cumulative consumer journey. In an isolated
  Python 3.11.9 environment, the documented research-only scenario ran with an
  illustrative 266 AUD MEDIUM result, all 5 delivery tests, all 13 serving
  tests, and all 79 tests passed with no skip, and repository governance had no
  deterministic failure. AgentGov reconciled the admitted cumulative scope,
  recorded fresh evidence and `completion.reconciled: verified`, then recorded
  a separate human-confirmed `session.handed_off: handed_off`; a repeated
  handoff preview was idempotent. Because the work was proposal-only, it used
  and disclosed a bounded current-Agent advisory review instead of fabricating
  native alignment self-review completion. This proves the previously missing
  runtime, Completion Verified, and Bounded Handoff transitions for one
  consumer journey. It does not prove the automatic primary experience,
  product effectiveness, independent review, consumer commit or push, CI
  enforcement, release, deployment, or production pricing authority. The
  consumer working tree remains uncommitted and unpushed.
- NYC now provides a second independent bounded consumer result. In an isolated
  Python 3.11.9 environment, its existing synthetic runtime scenario validated
  schema and exercised temporary Bronze, Silver, the demand quality gate, and
  non-empty Gold lineage. The focused scenario passed 1 test, the complete NYC
  suite passed all 68 tests, repository governance reported 17 PASS, 1 WARN,
  0 FAIL, and all 4 agent-skill contracts passed. AgentGov recorded fresh
  evidence, `completion.reconciled: verified`, and a distinct human-confirmed
  `session.handed_off: handed_off`; the repeat preview returned
  `already_handed_off`. NYC's formal CI remains on AgentGov 0.2.1, so the local
  0.3.0rc1 journey is not a formal upgrade. It does not prove uncoached
  adoption, production forecast quality, product effectiveness, independent
  review, control effectiveness, publication, release, deployment, or external
  authority. Its consumer changes remain uncommitted and unpushed.
- Development source now implements a combined drift-review reminder: one
  strict default cadence becomes due after three verified tasks or seven days,
  foreground cycles surface a subordinate non-blocking card, Monitor 1.5 shows
  the same state, and future workflow versions can emit a scheduled GitHub
  warning/summary without failing the job. Review and snooze records are
  create-only and human-confirmed. Requirement, architecture, and functionality
  conclusions remain `ADVISORY`; published 0.2.1 and v0.3.0rc1 workflows are
  unchanged, and no daemon or external notification writer was added. Focused
  regression passed 26 tests; the complete source suite passed 772 tests with
  2 platform-limited skips, and all 59 schemas parsed.
- Development source Adapter `1.4.0` now binds that due reminder to the
  capability-gated `agentgov_drift_review_record` native MCP form. The current
  Agent supplies only one advisory candidate, all three normalized dimension
  observations, and repository-relative evidence; the human selects record,
  snooze, or no record. Stale due state fails before a create-only write, and a
  successful record refreshes the local Monitor while retaining all denied
  authority. Clients without form elicitation still see only the five base
  read-only tools. The exact Adapter `1.4.0` source is now installed only in the
  existing local AgentGov pipx runtime; it remains unpublished and inactive in
  consumers, and the project MCP configuration is byte-unchanged. A bounded
  direct App Server replay in a disposable due repository advertised seven
  tools, called the drift tool once, reached one thread-bound form request with
  the exact record/snooze/no-record options, supplied no human decision, and
  wrote no record. This is installed forwarding evidence, not live Agent tool
  selection, UI presentation, semantic-review quality, or consumer proof.
  Source focused regression passed 66 tests; installed MCP/drift regression
  passed 40 tests. The earlier complete source suite passed 776 tests with 2
  platform-limited skips, and all 59 schemas parsed.
- ADR-0013 accepts an automatic, event-driven primary experience: users request
  work through a coding agent, AgentGov automatically coordinates context,
  scope, approved validation, fresh evidence, Monitor, and Dashboard updates,
  and humans are interrupted only at real semantic or authority boundaries.
  This direction is not yet implemented as the primary UI; current manual
  lifecycle commands remain development and fallback primitives.
- The first ADR-0013 implementation slice is now present in development source:
  a versioned read-only active-session state projection backs `next`, and a
  strict vendor-neutral trigger contract covers repository, task, change,
  scope-decision, validation, completion, and review events. Monitor 1.5 adds
  Live Sessions and Protection Events as honest read models with unknown
  resolution unless a future explicit link exists. Development source now also
  implements one `agentgov dev` foreground cycle and minimal reference adapter:
  scope and completion events invoke the existing deterministic cores and
  refresh the Dashboard; human review can hand off verified work. Development
  source now also accepts strict privacy-bounded coding-agent events over one
  foreground JSONL process and returns bounded task/scope/completion cards plus
  a subordinate non-blocking drift-review reminder card. The
  first packaged Codex lifecycle-hook Adapter is now present in development
  source.
  A vendor-neutral host-interaction capability/request contract now makes
  delivery and decision-recording support explicit. A strict task-proposal and
  human-admission fallback converts a normalized low-risk Coding Agent
  interpretation into one reviewed task without raw-prompt retention or
  session start. A reference host Adapter now accepts ordinary request text,
  invokes a replaceable semantic materializer once, adds Adapter-owned identity
  and denied authority, and returns that existing read-only admission plan.
  Development Codex Adapter `1.3.0` now connects that seam to the current Agent
  and a capability-gated native MCP form; only exact native admission creates
  the reviewed task. Standalone authentication and the installed runtime are
  now repaired. One separately authorized UTF-8-safe App Server replay
  initialized, created an ephemeral read-only thread, and completed a real
  turn, but surfaced no native form. Its text-search event heuristic could not
  distinguish an actual proposal-tool call from tool inventory or
  instructions, so the outcome is `INVALID_MEASUREMENT`, not Adapter evidence.
  Test-only structured event normalization now recognizes only exact proposal
  `mcpToolCall`, elicitation, and terminal events and retains no raw model or
  tool payload. One newly authorized replay then initialized, created an
  ephemeral read-only thread, and completed a real turn. Its normalized outcome
  was `not_called`: zero proposal calls and zero forms. This is valid negative
  end-to-end evidence. A later no-turn App Server configuration/status probe
  confirmed that the project MCP layer loaded and all six AgentGov tools were
  exposed, isolating the remaining observed gap to Agent invocation under an
  ambiguous trigger contract rather than discovery. Development guidance now
  requires an admitted task matching the exact requested repository change;
  this is not Adapter pass/fail evidence. The authorization is consumed and
  another replay is not admitted. After the clarified source was installed, a
  separately authorized single ephemeral read-only turn started the exact
  proposal tool once; the turn completed without a native form. It created no
  task or implementation and changed no repository state. Invocation is now
  demonstrated. Two no-model direct App Server probes then proved that valid
  arguments reach the Adapter form and that App Server parses it, returning a
  zero-write `decline` when no active turn can host the request. The replay
  normalizer did not retain whether its live completion carried a structured
  AgentGov error, so the remaining confirmed gap is evidence resolution between
  call start and form presentation, not a localized product defect. The
  selected test-only correction now records completion count/status, an
  explicit `completion_unknown` state, and only bounded structured AgentGov
  error fields. It cannot reconstruct or reclassify the historical replay. The
  new one-turn authorization is also consumed.
  Risk-based routing now keeps no-write requests and verified
  active-task iteration at zero interruptions, permits bounded low-risk
  fast-track only under clean human-owned standing policy, and reserves review
  for real ambiguity or material risk. Proactive digest-bound decision prompts
  and human results now let capable hosts request one selection with no free
  text; the reference low-risk review accepts one number and can create only
  the exact reviewed task. Governed clarification contracts now keep the
  current center visible during multi-turn business, requirement, or
  architecture drift discussion, ask one natural-language question per turn,
  and wait for stable options before one final human re-centering choice.
  The foreground Coding Agent stream now accepts normalized alignment context,
  human clarification updates, and final decision results and automatically
  returns the next question or stable choice through a memory-only alignment
  response. It does not retain raw chat or invoke a repository lifecycle cycle.
  A host-side reference Alignment Adapter now accepts ordinary request and
  answer text, delegates semantic normalization to a replaceable Coding Agent
  materializer, fills the strict Core envelopes, records the final host
  selection, and exposes privacy-safe interaction-burden evidence. The
  independent rehearsal uses an offline fixture materializer and is not a
  claim of general Core language understanding or a production host UI.
  Local installation and installed-runtime protocol proof for Codex proposal
  materialization and native review now pass. External live proof, additional
  production task-proposal hosts, Claude Code/IDE adapters, native authenticated recording for custom
  governance controls, protection resolution, and Benefit/Learning remain.
- ADR-0014 and three strict development contracts now implement the Revision 4
  model-free boundary: Provider capability declaration, low/medium/high risk
  routing, and digest-bound advisory results. Medium risk binds the active
  Coding Agent self-review with no new user configuration. High risk binds a
  qualifying independent Reviewer or returns exactly human review, explicit
  lower-assurance self-review, and Provider setup as unselected choices; it
  never silently downgrades. Four cross-host fixtures pass one vendor-neutral
  parser. AgentGov includes no model, credential, network call, or independent
  Reviewer host UI; Codex proposal materialization reuses the current Agent.
- `ReferenceAlignmentAdapter.self_review(...)` now connects a resolved
  human-alignment journey to the active-host medium-risk route and one
  host-neutral `ActiveAgentSelfReviewMaterializer` callback. It supplies only
  normalized ephemeral context and explicitly allowed repository evidence,
  generates observation IDs itself, and accepts only the exact digest-bound
  advisory result. Codex and Claude Code fixtures pass the same execution path;
  AgentGov makes zero model/network calls and no production host callback is
  installed yet.
- `agentgov dev --stream` now carries that self-review as a strict foreground
  start/request/draft/completed exchange. It binds the exact resolved dialogue,
  Coding Agent Adapter, Provider, evidence allow-list, and pending request
  digest; invalid input is atomic and reports the exact JSONL line. These are
  host-owned records, so the user types no JSON, makes no extra confirmation,
  and configures no second model. Native host installation and the independent
  high-risk Reviewer remain open.
- A dependency-free foreground STDIO MCP Adapter now exposes five strict
  model-controlled tools for alignment and medium-risk current-Agent
  self-review. Explicit journey/prompt/request bindings reuse the existing Core
  state machines and disappear on restart. A create-missing-only Codex
  `.codex/config.toml` plan is packaged without overwriting custom config or
  granting trust. Codex and Claude Code fixtures share the Core tool path;
  live uncoached Codex use, native Claude/IDE packaging, and the independent
  Reviewer remain open. The Codex rehearsal is now admitted. Its first
  preflight found no `agentgov` executable on `PATH` and no working TLS in the
  default Python, then resolved that bootstrap boundary through an authorized
  parallel official Python 3.12 runtime and exact current-source pipx install.
  No reference-project environment or absolute source path was substituted.
  Exact human `INTEGRATE` created the reviewed project config, and a real-user
  Codex preflight now discovers the enabled five-tool server with a healthy
  local configuration. A subsequent eligible session discovered all five
  tools and selected alignment without named-tool coaching, but Core rejected
  two normalized alignment-start attempts with only a generic error. Human
  direction selection and active-Agent self-review never occurred. The live
  product journey is recorded as failed while static regression remains
  healthy. The reviewed correction is now implemented in development source:
  question IDs are Adapter-owned rather than model inputs, known normalized
  failures return privacy-safe structured field/rule/retry metadata, and
  rejected start/update calls remain atomic. A fresh uncoached replay remains
  required before the live journey can be called successful. The first
  post-correction replay failed earlier in host selection: the Agent bypassed
  alignment, independently selected and implemented a change, and omitted
  current-Agent self-review. The admitted correction now makes the ordinary
  intent triggers, human-owned direction boundary, completion-time self-review,
  and fail-closed behavior explicit in both `AGENTS.md` and MCP metadata.
- The post-guidance uncoached replay automatically selected alignment, left the
  final direction to the human, and stopped without repository mutation when
  alignment start returned an unclassified non-retryable Core rejection. The
  admitted normalized-fixture diagnosis found the exact mismatch: the MCP
  schema allowed deterministic business, requirement, and architecture drift,
  while Core requires those judgment-bearing kinds to remain advisory. The
  development Adapter now advertises that rule and safely classifies violations
  as retryable without weakening Core or echoing rejected values. A fresh
  installed-runtime replay remains required; NYC, another host, publication,
  release, and deployment remain gated.
- The drift-semantics correction passed 29 focused tests. The official Python
  3.12 suite passed 728 tests with two platform-limited skips. The admitted task
  reported `PASS=6 WARN=0 FAIL=0 ADVISORY=1`; repository governance reported
  `PASS=26 WARN=2 FAIL=0 ADVISORY=4`; all 56 schemas parsed, source/tests
  compiled, and `git diff --check` passed. Combined working-copy scope reported
  `PASS=11 FAIL=2 ADVISORY=1`; both failures are preserved excluded files from
  prior work, not changes made by this requirement.
- The exact corrected source was locally built and hash-recorded, then installed
  into the existing isolated Python 3.12.10 pipx runtime after stopping only two
  read-only-identified AgentGov governance-MCP child-process chains. Installed
  preflight reports Adapter `1.2.1`, five tools, the advisory-only drift schema,
  retryable `advisory_required`, and a successful corrected retry into
  `exploring`. A fresh Codex session remains required for measured end-to-end
  replay; this active session did not claim that evidence.
- The required fresh Adapter `1.2.1` replay selected alignment without named-tool
  coaching, corrected one retryable drift error, and then stopped fail-closed
  on a second unclassified Core rejection without changing the repository. The
  normalized diagnosis found a second cross-field mismatch: MCP allowed a
  no-unknown context without Core's required two stable options and non-null
  recommendation. Development Adapter `1.2.2` now advertises that condition and
  returns precise retryable `stable_options_required` or
  `recommendation_required` diagnostics. Static validation is complete; no
  new installed-runtime or successful end-to-end replay claim has been made.
- The stable-options correction passed 30 focused tests and the official Python
  3.12 full suite passed 729 tests with two platform-limited skips. The task
  reported `PASS=6 WARN=0 FAIL=0 ADVISORY=1`; repository governance reported
  `PASS=26 WARN=2 FAIL=0 ADVISORY=4`; all 56 schemas parsed, source/tests
  compiled, and `git diff --check` passed. Combined scope reported
  `PASS=14 FAIL=2 ADVISORY=1`, with only the two previously excluded host-local
  files failing. Adapter `1.2.2` is validated in development source but is not
  installed; another replay is not yet admitted.
- The human admitted the installed replay preparation. Exact current source was
  built with SHA-256
  `329790D30064103669BA231302FEF87F92C190D5401E9C4817815736825BACB8` and
  installed into the existing Python 3.12.10 pipx environment after stopping
  only two read-only-identified AgentGov governance-MCP child-process chains.
  Installed Adapter `1.2.2` reports five tools, both retryable stable-options
  diagnostics, and a successful fully corrected transition to
  `ready_for_decision`. Only a newly created uncoached Codex session can supply
  the remaining end-to-end replay evidence.
- That fresh Adapter `1.2.2` session still reached an unclassified Core start
  rejection and stopped fail-closed without repository mutation. The reviewed
  follow-up replaces serial symptom repair with a complete Alignment Start
  parity audit. Development Adapter `1.2.3` validates all ten model-authored
  input families before Core, with 30 normalized repairable fixtures, and
  reserves `alignment_rejected_internal` / `unclassified` only for the eleventh
  generated-state family. The denominator and applicability are documented;
  no governance coverage percentage or semantic-correctness claim is made.
- Adapter `1.2.3` closeout passed 20 focused MCP tests, 13 current-task tests,
  and the official 732-test Python 3.12 suite with two platform-limited skips.
  The admitted task reported `PASS=6 WARN=0 FAIL=0 ADVISORY=1`; repository
  governance reported `PASS=26 WARN=2 FAIL=0 ADVISORY=4`; all 56 schemas
  parsed, source/tests compiled, and `git diff --check` passed. Scope reported
  `PASS=16 FAIL=2 ADVISORY=1`, limited to the two explicitly excluded local
  files. A distinct advisory review found no new privacy, authority,
  atomicity, schema-loosening, or compatibility issue. Development Adapter
  `1.2.3` was then built offline with SHA-256
  `F3F2B45B21636556FFD034C9C91370FEB790D794EDE2B2488568A8B1ADE9CECA` and
  installed into the existing Python 3.12.10 pipx environment. Installed
  discovery, five-tool inventory, representative retry, corrected
  `ready_for_decision`, and private non-retryable internal fallback all passed.
  A sandboxed Codex attempt exited before discovery because it could not reach
  the external service and is not counted as a replay. The human then approved
  one external transmission. That fresh session exited successfully and its
  final output had the shape of a human-selection boundary, but the first
  normalizer also scanned historical repository text and produced
  contradictory state markers. Because raw events were intentionally not
  retained, the run is `INVALID_MEASUREMENT`, not success evidence. A second
  external transmission was separately approved and measured only completed
  MCP tool-call events. The fresh ephemeral read-only session completed two
  `agentgov_alignment_start` calls: one retryable input rejection, followed by
  `ready_for_decision` and a final human-selection boundary. It produced no
  internal/unclassified rejection or operational error and changed no
  repository file. Alignment update, resolve, implementation, and self-review
  were intentionally not reached, so the result proves Start recovery rather
  than the complete post-selection journey.
- Adapter `1.2.3` replay closeout passed 20 focused MCP tests and 13 current-task
  tests. The task reported `PASS=6 WARN=0 FAIL=0 ADVISORY=1`; repository
  governance reported `PASS=26 WARN=2 FAIL=0 ADVISORY=4`; scope reported
  `PASS=17 FAIL=2 ADVISORY=1`, limited to the two explicitly excluded local
  files; `git diff --check` passed. A distinct advisory review found no raw
  replay retention, repository mutation, authority expansion, or overclaim
  beyond the measured Start/human-selection boundary.
- The human-selected next slice is implemented in development Adapter `1.2.4`.
  Alignment Resolve, current-Agent self-review start, and self-review completion
  now validate repairable normalized bindings, allowed evidence, and advisory
  observations before state mutation. Failures return privacy-safe field/rule
  diagnostics and corrected retries can continue in the same foreground
  journey. At that checkpoint this closed deterministic post-selection
  contract parity only, while the fresh live implementation/self-review
  journey remained open; the later live-replay bullet below supersedes that
  open-gate status.
  Final validation passed 22 focused MCP tests, 13 current-task tests, and all
  734 Python 3.12 tests with two platform-limited skips. A distinct advisory
  review found and closed one schema/runtime cardinality mismatch; no remaining
  privacy, authority, atomicity, compatibility, or overclaim issue was found.
  That conclusion is superseded by a later independent installation-gate
  audit. The audit reproduced five remaining Adapter/Core gaps for reason
  identifiers, evidence length, observation list bounds, evidence allow-list
  membership, and duplicate observations. Development source now validates all
  five before Core state mutation and exposes the same limits in the MCP
  schema. Renewed validation passed 22 focused MCP tests, 13 current-task tests,
  and all 734 Python 3.12 tests with two platform-limited skips. Independent
  probes confirmed precise retryable diagnostics, atomic failure, and corrected
  same-process completion. The exact wheel with SHA-256
  `09CC8C54A8613E1E3100F60850EBE7BD5DF53668CCD37FBAEBBAF2C8A73BF362`
  is now installed in the existing Python 3.12.10 pipx environment. Installed
  discovery reports Adapter `1.2.4`, five tools, the exact published limits,
  five precise retryable failures, atomic state, and corrected completion with
  zero AgentGov model or network calls. At the installation checkpoint, live
  external replay remained a separate human-controlled action; the next bullet
  records its later explicit approval and completion.
- The human product owner designated the current ephemeral Codex session as the
  single approved live post-selection replay and selected the recommended
  direction. That same session used the native MCP tools to reach the human
  decision boundary and bind the exact selection through Alignment Resolve
  without another session, Agent, host, or authority expansion. Focused MCP and
  task-contract validation passed 22 and 13 tests; the unchanged full Python
  3.12 suite passed all 734 tests with two platform-limited skips. The distinct
  current-Agent MCP self-review completed with three bounded advisory
  observations, zero AgentGov model/network calls, and no Adapter context
  retention. The measured current-host post-selection slice is complete; no
  automatic proposal-generation, cross-host, consumer, release, or deployment
  claim is inferred.
  The admitted task and repository checks have no deterministic failure and
  `git diff --check` passes. During the replay, combined scope reported four
  explicit failures because two transient `.tmp-replay` bridge files were
  still present beside the pre-existing Codex config and user-owned cover
  image. The outer host deleted the bridge after extracting only the normalized
  result; independent final scope revalidation reports
  `PASS=19 FAIL=2 ADVISORY=1`, with only those two pre-existing excluded files
  remaining and no exception inferred.
- Native MCP Adapter and affected governance regression passed 103 focused
  tests and the latest full Python 3.12 suite passed 724 tests with two
  platform-limited skips. The
  admitted task reported `PASS=6 WARN=0 FAIL=0 ADVISORY=1`; combined
  working-copy scope reported `PASS=110 FAIL=0 ADVISORY=1`; repository
  governance reported `PASS=26 WARN=2 FAIL=0 ADVISORY=4`; all 55 schemas parsed,
  source/tests compiled, and `git diff --check` passed.
- The MCP diagnostic correction passed 61 expanded focused tests and the full
  Python 3.12 suite passed 724 tests with two platform-limited skips. Repository
  governance remained `FAIL=0`; all 56 schemas parsed. Combined dirty-worktree
  scope remains honestly failing only for the retained host-local Codex config
  and unrelated user-owned social-cover image.
- The active-Agent self-review, Alignment Adapter/transport, semantic-review,
  clarification, Skill, task, documentation, and portfolio regression passed
  110 focused tests. The current
  contract task reported
  `PASS=6 WARN=0 FAIL=0 ADVISORY=1`; combined working-copy scope reported
  `PASS=97 FAIL=0 ADVISORY=1`; repository governance remained
  `PASS=26 WARN=2 FAIL=0 ADVISORY=4`; source/tests compiled and
  all 51 schemas parsed, `git diff --check` passed, and the full suite passed
  700 tests with two platform-limited skips.

## Development checkpoint - 2026-08-06

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

## Development checkpoint - 2026-08-05

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

## Product direction

- ADR-0009 makes development-time governance of coding-agent requirements,
  architecture context, implementation scope, verification evidence, and
  completion reconciliation the product core.
- The repository now ships seven portable operating protocols. The new
  `requirement-admission`, `action-loop-stagnation`, and
  `reconcile-invariants` Skills close the first protocol gaps while keeping
  semantic decisions and task admission human-owned; they are packaged into
  newly initialized repositories.
- The Inventory now declares `development-time-coding-agent-governance` as
  provisional. This records the real product capability without claiming that
  optional hooks, runtime enforcement, uncoached adoption, or benefit proof are
  complete.
- PR and CI reporting, benefit evidence, and upgrade automation remain retained
  backstop and delivery capabilities rather than the primary user interaction.
- This direction was revalidated against clean scoped governance files from AI
  Radar commit `3a9323cb2a9ef575da42d29fb17d330ef872afd3`; reuse and exclusion
  decisions are recorded in `docs/ai-radar-extraction-map.md`.
- Task contract 1.1 and read-only `agentgov check task` are implemented in
  development source with low-risk compact and full standard profiles, safe
  references, validation commands, and objective-alignment advisory review.
- Read-only `agentgov context task` now derives an in-memory Registry and emits
  terminal, JSON, or Markdown task context with artifact-owned Skill routing,
  explicit references, path-linked capability governance, selection reasons,
  source hashes, known limits, and denied mutation authority.
- Guided `agentgov govern start` is implemented in development source. It can
  select exactly one admitted task or preview a low-risk compact task, requires
  exact interactive confirmation, derives the governance context, records the
  comparison base, and writes a strict untracked single-task working-copy
  pointer plus one immutable start event. The future 0.3 workflow template now
  provides a separate default-off Monitor artifact path without transferring
  local state automatically.
- Read-only `agentgov check scope` now inventories staged, unstaged, deleted,
  renamed, and non-ignored untracked paths and applies segment-aware
  include/exclude rules. Explicit architecture references remain ADVISORY.
  The low-level scope-only report remains working-tree-specific; explicit
  exception records and action-loop self-reporting are not implemented yet.
- `agentgov govern check` now appends a privacy-bounded local scope event.
  `agentgov govern finish --base` captures canonical committed, staged,
  unstaged, renamed, and non-ignored untracked identities, runs every declared
  validation command, and reconciles `verified` versus `needs_evidence`.
  Evidence and one-file events live under untracked `.agentgov/` local state;
  tracked `.agentgov/` and `.gitignore` changes remain visible. These local
  records are not CI-visible unless a user explicitly creates and transfers a
  redacted development export.
- With an active session, `govern check` defaults to its task and `govern
  finish` defaults to its task and exact base. Changed task content fails
  closed until a reviewed replacement start. Untracked `.agentgov/` tool state
  is now consistently excluded by both scope and fresh-evidence inventories;
  tracked local state remains visible.
- `agentgov monitor development` now generates a self-contained static
  Overview, Activity Timeline, and Task Detail from validated local, exported,
  CI-only, or combined sources. Every output displays partial history, source
  counts, per-event source labels, missing inputs, unavailable cross-stage
  discovery, and separate observed, inferred, and unknown claims.
- `agentgov export development` now previews and, after exact interactive
  `EXPORT` confirmation, creates an immutable metadata-only bundle. It removes
  actor labels and local evidence references; rejects CI events, sensitive
  token/path shapes, tracked/existing/outside/symlink output, and integrity
  drift; and grants no upload, workflow, Git, approval, or deployment authority.
- The first exact-wheel independent development pilot is complete. A fresh
  isolated installation routed eight relevant governance artifacts; the Coding
  Agent read them, changed only the admitted Python source, passed scope and
  validation, reached `verified`, and produced a four-event Monitor. The pilot
  also preserved fail-closed evidence for an invalid Skill and unignored
  `__pycache__` output instead of weakening checks.
- The pilot is internal evidence, not uncoached human or general effectiveness
  evidence. Its source-identity blocker is resolved: development builds now
  report `0.3.0.dev0` instead of stable `0.2.1`. Actionable
  validation-artifact readiness guidance without editing `.gitignore` remains
  a pre-release action.

## Development-source P0 preview

- Runtime and bundled compatibility metadata now use `0.3.0rc1` with the
  `release-candidate` channel. Published stable 0.2.1 documentation and
  consumer pins remain unchanged; no public candidate artifact or digest is
  claimed until the tag-triggered release workflow succeeds.

- `schemas/development-task.schema.json` defines a strict, vendor-neutral task
  identity with compact/standard profiles, exact scope, acceptance and
  validation commands, owner, risk, and human decision. Standard adds parent
  objective, goal boundaries, architecture, approval, and stop conditions.
- `schemas/development-session.schema.json` defines the local task/base pointer;
  task, ADR, invariant, AGENTS.md, and Skill content remain artifact-owned.
- `agentgov check task <task.json> --repository .` validates the contract and
  readable repository-local references without modifying repository or Git
  state.
- Draft and incomplete tasks retain WARN and ADVISORY findings. Admission and
  approval inconsistencies, unsafe paths, and broken declared references fail
  deterministically.
- `governance/tasks/p0-minimal-task-contract.json` dogfoods the contract for
  this slice and links `AG-DRIFT-001`, ADR-0009, and the corrected P0 plan.
- `governance/tasks/p0-context-selection.json` admits the first Phase 1 slice;
  `schemas/development-context.schema.json` defines its derived output.
- This interface is not published in stable 0.2.1 and is not yet added to
  initialization, repository-wide checking, task Markdown/JSON reporting, or
  CI replay.

## Stable foundations

- Installable, zero-runtime-dependency Python CLI.
- Package metadata and `agentgov --version` derive from the single runtime
  version declared by `agentgov.__version__`.
- Strict release-manifest schema, fixtures, and
  `agentgov check release-manifest` validation.
- Verified one-command update flow: stable-release discovery, bounded temporary
  download, SHA-256 verification, pipx upgrade, new-process relaunch,
  repository refresh, explicit terminal states, and recovery guidance.
- Separate tag-triggered stable and release-candidate workflows publish the
  universal wheel and immutable machine-readable manifest. RC tags create a
  GitHub Pre-release and cannot enter the stable consumer update channel.
- Deterministic repository, capability, reference, evaluation, agent-skill,
  and artifact-drift checks.
- Explicit `PASS`, `WARN`, `FAIL`, and `ADVISORY` semantics.
- Markdown, JSON, and HTML report surfaces.
- Read-only `agentgov status` visibility for adoption, CI state, governed
  capabilities, active surfaces, repository findings, and the next action,
  including a portable Markdown view for GitHub job summaries.
- Create-missing-only `agentgov integrate github-actions` support for a pinned,
  read-only consumer CI workflow with exact interactive confirmation.
- Read-only `agentgov plan upgrade-pr` contract for current, candidate, and
  blocked managed-workflow upgrades with exact hashes and no Git authority.
- Read-only `agentgov benefits compare` evidence for two repository-report
  snapshots with explicit finding denominators and no causal or ROI claim.
- Create-new-only `agentgov review release` bundles exact wheel, manifest,
  source-test, consumer-check, status, and upgrade-policy evidence while leaving
  the approve/change/reject decision pending.
- Consumer-local `agentgov review upgrade` bundles a stable upgrade plan,
  current status, exact workflow patch, deterministic gates, and a pending
  project-owner decision without applying the proposed change.
- Managed 0.2+ consumer CI automatically publishes that upgrade review in the
  GitHub job summary and report artifact while retaining read-only permissions.
- Future 0.3 source separates read-only governance from its schedule/dispatch
  Draft PR writer and bounds upgrade plans to the two exact managed workflow
  paths. This behavior is not yet published or adopted by NYC.
- Windows and Ubuntu CI definitions for Python 3.11, 3.12, and 3.13.

## Current milestone

Future-0.3 development-governance integration and pre-release evidence:

- the repository-local architecture baseline is accepted in ADR-0016 and the
  dated boundary diagnosis finds no current need for a new Kernel concept;
  selecting and proving an external consumer remains a separate human-admitted
  task;

- Governance Inventory contract and zero-dependency validator implemented;
- canonical manifest, owner, identity, exclusion, and safe-path closure;
- evaluation and artifact contract claims close to Inventory declarations
  without filename inference;
- deterministic orphan failures with legacy-compatible non-cascading behavior;
- strict capability control mappings with explicit applicability, enforcement
  mode, ownership, exception authority, and safe evidence references;
- deterministic control identity and reference checks paired with an explicit
  effectiveness advisory;
- strict capability dependency declarations with Inventory-linked endpoints,
  deterministic self-dependency and cycle rejection, and optional explicit
  readiness floors;
- readiness differences remain non-blocking when no minimum is declared;
- explicit completeness advisories without automatic discovery claims;
- implementation, review, supported CI, and human-controlled integration are
  complete on `main`.
- the completed NYC Taxi consumer-CI pilot remains historical backstop
  evidence: validation runs on pull requests and pushes and publishes bounded
  evidence without transition authority. It is not evidence that the coding
  process itself was governed.
- NYC Taxi remains the first planned real-consumer development-loop shadow
  pilot, but it now follows a general automatic-experience gate. AgentGov must
  first complete an independent non-NYC rehearsal in which ordinary use needs
  no hand-authored internal JSON, repeated `next` queries, manual lifecycle
  command composition, or special confirmation words. NYC then supplies
  classified feedback; its paths, policy, data, workflows, and business
  semantics remain outside Core.
- ADR-0006 rejects a general semantic-model implementation until a verified
  cross-domain gap survives existing-contract-first review; no semantic
  schema, checker, report field, or migration has been added.

## Remaining TODOs

- [x] Design and test a low-friction installation path that keeps AgentGov
  independent from the adopting repository's Python environment. ADR-0004
  selects persistent isolated tool execution through pipx for v0.1; the
  Windows rehearsal covered Git install, inspect, dry-run, adopt, repository
  check, upgrade, and uninstall without using the target `.venv`.
- [ ] Complete the automatic primary product experience so a first-time user
  can request coding work, confirm only real boundaries, and review protection
  and benefit evidence without an AgentGov expert beside them. ADR-0005 defines
  bounded onboarding; ADR-0013 now makes the foreground coordinator,
  vendor-neutral adapter events, automatic Monitor refresh, and Dashboard the
  primary direction. The current
  `doctor`, `onboard`, and `next` interaction contracts, and the first
  read-only `agentgov doctor .` slice is implemented.
  `agentgov onboard . --dry-run` now combines diagnosis, exact target
  disclosure, create/preserve preview, and strict non-interactive write denial.
  Interactive onboarding now accepts only exact `ADOPT` from a real terminal,
  revalidates the complete reviewed plan before writing, and creates only the
  files shown in that plan. `agentgov next .` now selects one read-only action
  using adoption conflict, missing scaffold, repository FAIL, then strict
  development-session precedence. WARN and ADVISORY remain visible through
  checks and reports without displacing the active daily route. An isolated
  automated deep-path Windows rehearsal now covers the
  complete installed sequence and corrected `onboard` to run the first
  repository check automatically. These commands remain fallback and test
  surfaces. The foreground coordinator, minimal repository-state reference
  adapter, generic live JSONL process transport, bounded task/scope/completion
  cards, vendor-neutral host-interaction requests, and the first packaged Codex
  hooks Adapter are now implemented in development source. A structured
  Coding Agent proposal and exact human task-admission fallback is also
  implemented. Risk-based routing, clean standing low-risk delegation, active
  task reuse, and a machine-checkable friction budget are implemented in
  development source. Proactive digest-bound prompts/results and the reference
  one-number human-review path and the reference host-side proposal generation
  seam are also implemented. Codex development Adapter `1.3.0` now adds the
  production proposal materializer/native form review path, now installed and
  locally preflighted. Remaining work includes its external live proof, native
  authenticated recording for other custom decisions, explicit protection
  resolution links, Benefit/Learning views, an independent automatic
  rehearsal, and then a fresh uncoached human pilot. Additional host adapters
  remain optional portability work rather than a prerequisite for that gate.
  Existing facilitator material exercises the historical
  `doctor` → `onboard` → `next` path and must not be treated as validation of
  the newly accepted automatic journey; a replacement automatic-journey pilot
  record is required.
- [ ] Convert the Taxi adoption notes into a completed cross-domain pilot
  record, including timing, assistance required, unresolved release-gate
  findings, and final maintainer decisions. A bounded semantic-relation gap
  analysis record is prepared under `docs/experiments/semantic-relations/`;
  it contains no invented Taxi observations.
- [x] Decide whether the supported one-command experience should use an
  isolated tool installer, an ephemeral runner, or a small bootstrap command.
  The isolated installer is selected and the primary Quickstart now pins the
  reviewed `v0.1.0` Release wheel instead of mutable Git `main`.
- [x] Publish the first stable software-update channel. `agentgov update .`
  discovers the latest stable manifest, verifies the fixed-tag wheel digest,
  upgrades the pipx environment, relaunches the updated executable, and
  continues the bounded repository refresh.

## Known gaps

- Taxi supplied initial cross-domain adoption evidence, but the pilot record
  and maintainer decisions are not complete.
- Published 0.2.1 consumer CI reports stable-release update state but cannot
  open or merge dependency-update pull requests. The future 0.3 source writer
  remains unavailable to consumers until a separately approved release and
  one-time workflow migration.
- Stable `v0.2.1` is published. Its consumer workflow preserves the canonical
  wheel filename found missing by the first NYC 0.2 run.
- The first NYC 0.2 run exposed that pip rejects a valid wheel renamed to
  `agentgov.whl`; stable 0.2.1 corrected the generated workflow. No NYC
  business or production workflow was involved.
- Benefit evidence currently compares two downloaded report snapshots. It does
  not yet observe project-test outcomes, PR disposition, runtime incidents,
  human handling time, or false-positive decisions.
- Installation still depends on Python 3.11 or newer and pipx. GitHub Release
  is the current stable distribution channel; PyPI publication is not yet
  configured.
- Static HTML remains reference material and cannot adapt to repository state.
  The bilingual Quickstarts now label guided onboarding as a development
  preview; the primary path remains unchanged until an uncoached human pilot.
- Dependency risk propagation and repository profiles are not implemented.
- Output-level identity and evidence mapping remain an unverified cross-domain
  question. Existing schema references must be evaluated before any new
  semantic relation contract.
- Legacy removal release remains undecided.
- A successful check does not prove semantic governance sufficiency.

## Validation

Guided next-action development routing validation on 2026-08-05:

- the admitted task returned `PASS=6 WARN=0 FAIL=0 ADVISORY=1`;
- its combined working-copy scope returned `PASS=17 FAIL=0 ADVISORY=1`;
- 46 focused next-action, development-session, and documentation tests passed;
- all 527 source tests passed with one platform-limited skip;
- fixture coverage includes onboarding and FAIL precedence, zero/one/many task
  discovery, start/check/validation/completion routing, old-event isolation,
  failed scope, task drift, missing start events, malformed pointers, JSON
  purity, and no-write behavior;
- no command selected by `next` was executed and no task, session, event,
  evidence, Monitor, Git state, workflow, release, or deployment was changed by
  the router;
- repository governance returned `PASS=16 WARN=2 FAIL=0 ADVISORY=4` and
  `git diff --check` passed.

Opt-in Development Monitor artifact validation on 2026-08-05:

- the admitted task returned `PASS=6 WARN=0 FAIL=0 ADVISORY=1`;
- its final working-copy scope returned `PASS=11 FAIL=0 ADVISORY=1`;
- 34 focused consumer-workflow and documentation tests passed;
- all 517 source tests passed with one platform-limited skip;
- stable 0.1 workflow bytes retained their protected SHA-256 and the 0.2
  template retained no Development Monitor inputs or steps;
- repository governance returned `PASS=16 WARN=2 FAIL=0 ADVISORY=4`;
- `git diff --check` passed;
- no existing workflow, commit, push, tag, release, consumer migration,
  artifact upload, merge, or deployment was performed.

Published-reference-page validation on 2026-08-03:

- 511 unit tests passed with one platform-limited skip;
- 11 focused Portfolio and reference-page tests passed;
- the admitted reference-page task returned
  `PASS=6 WARN=0 FAIL=0 ADVISORY=1`, its working-copy scope returned
  `PASS=29 FAIL=0 ADVISORY=1`, and repository governance returned
  `PASS=16 WARN=2 FAIL=0 ADVISORY=4`;
- no Portfolio link ends in `.md` or starts with `../`, every local target
  exists, and both published schema JSON files are byte-identical to their
  authoritative source schemas;
- the first live Pages build exposed a same-destination layout collision for
  Markdown-backed HTML; follow-up commit `743f3b3` built successfully, all 13
  HTML reference pages returned 200 with the AgentGov layout, both schema JSON
  URLs returned valid JSON, and the Portfolio retained zero `.md` or `../`
  hrefs.

Documentation and development-source validation on 2026-08-03:

- 507 unit tests passed with one platform-limited skip;
- 46 focused product-site, portfolio, user-documentation, report, adoption, and
  documentation-freshness tests passed;
- all 12 public HTML files had resolvable repository-relative links;
- the public README and HTML surfaces no longer advertise the v0.1 wheel,
  mutable `main` installation, or the independent consumer project;
- `git diff --check` passed with only Git's existing line-ending notice for the
  Chinese HTML quickstart.
- the admitted documentation-sync task returned
  `PASS=6 WARN=0 FAIL=0 ADVISORY=1`, its combined working-copy scope returned
  `PASS=35 FAIL=0 ADVISORY=1`, and repository governance returned
  `PASS=16 WARN=2 FAIL=0 ADVISORY=4`.

Development-source identity validation on 2026-08-03:

- 497 unit tests passed with one platform-limited skip;
- focused package, release-metadata, and update validation passed 36 tests;
- an isolated wheel built as
  `agent_governance_starter-0.3.0.dev0-py3-none-any.whl`, installed with no
  runtime dependencies, and reported `agentgov 0.3.0.dev0`;
- bundled development release metadata passed its strict manifest contract;
- the admitted identity task returned `PASS=6 WARN=0 FAIL=0 ADVISORY=1`, and
  its working-copy scope returned `PASS=12 FAIL=0 ADVISORY=1`;
- repository self-check returned `PASS=16 WARN=2 FAIL=0 ADVISORY=4`;
- `git diff --check` passed;
- no workflow mutation, consumer migration, commit, push, tag, release,
  publication, or artifact upload was performed.

Development-source Phase 7 validation on 2026-08-03:

- 496 unit tests passed with one platform-limited skip;
- repository self-check returned `PASS=16 WARN=2 FAIL=0 ADVISORY=4`;
- the admitted redacted-export task returned
  `PASS=6 WARN=0 FAIL=0 ADVISORY=1`;
- export and four-scope Monitor CLI help rendered successfully;
- `git diff --check` passed;
- no commit, push, release, workflow mutation, artifact upload, or external
  telemetry action was performed.

Consumer CI pilot validation on 2026-08-01:

- 353 unit tests passed with the active supported interpreter; one
  platform-limited symbolic-link test was skipped;
- repository self-check completed with
  `PASS=16 WARN=2 FAIL=0 ADVISORY=4`;
- NYC dry-run revalidation returned `PRESERVE=1` and `CONFLICT=0` for the
  generated workflow;
- development-source status classified NYC CI as `managed` and pull-request
  visibility as active;
- the installed stable AgentGov 0.1.0 validated NYC with
  `PASS=17 WARN=1 FAIL=0 ADVISORY=4`;
- the broken pipx launcher was rebuilt against Python 3.11.9 from the original
  fixed v0.1.0 release URL and `agentgov --version` works again;
- `git diff --check` passed in both repositories; NYC emitted only line-ending
  warnings for unrelated pre-existing changes.

Release-candidate wheel validation on 2026-08-02:

- 370 unit tests passed with Python 3.11; one platform-limited symbolic-link
  test was skipped;
- built `agent_governance_starter-0.2.0rc1-py3-none-any.whl` in an isolated
  Python 3.11 environment;
- wheel SHA-256 was
  `504a80878ee3f13b0ab7162b194ab1ec1aa612b5a27f528ddebe93c40bf18bdd`;
- the wheel contains the status, consumer-CI, upgrade-PR, benefit, and release
  review modules plus their machine-readable schemas;
- an immutable rehearsal manifest passed validation, declared compatibility
  from stable 0.1.0, retained layout 1.0, declared no repository migrations,
  and matched the wheel digest;
- a fresh wheel-only environment reported `agentgov 0.2.0rc1`, validated NYC
  with `PASS=17 WARN=1 FAIL=0 ADVISORY=4`, and rendered its status as portable
  Markdown;
- NYC upgrade planning returned `blocked` because release-candidate manifests
  cannot authorize a consumer upgrade proposal; only a validated stable
  manifest may produce a candidate;
- `agentgov review release` produced an atomic NYC evidence bundle with all
  seven automated gates passing, state `ready_for_human_review`, and the human
  decision left `pending`;
- consumer-local NYC upgrade review correctly reported `blocked` for the RC
  manifest, preserved a passing NYC governance check, and applied no workflow
  or Git change;
- stable 0.1 workflow rendering remained byte-exact with NYC at SHA-256
  `9fa83b71b498b058afb2f5bdf777b23ed27933995faedc546faf4321f3974be8`,
  while the 0.2 preview retained `contents: read` and added one automatic
  consumer upgrade review.

Semantic-relation admission documentation validation on 2026-07-27:

- 302 unit tests passed with the active supported interpreter; one
  platform-limited symbolic-link test was skipped;
- repository self-check completed with
  `PASS=16 WARN=2 FAIL=0 ADVISORY=4`;
- `git diff --check` passed;
- no semantic schema, checker, CLI behavior, or report contract changed.

Isolated execution validation on 2026-07-25:

- Windows, Python 3.12.10, and pipx 1.11.1;
- public Git install into a pipx-managed environment;
- deep-path inspect, dry-run, create-missing-only adoption, and repository
  check completed with `PASS=14 WARN=4 FAIL=0 ADVISORY=4`;
- the unrelated target `.venv` was not used or modified;
- upgrade and uninstall behavior completed successfully.

Guided onboarding validation on 2026-07-25:

- ADR-0005 fixes read-only defaults, non-interactive write denial, target
  disclosure, and human authority boundaries;
- `agentgov doctor .` reports interpreter support, Git context, Windows path
  risk, project `.venv` signals, and governance adoption state;
- text and strict JSON v1.0 results preserve deterministic versus advisory
  classification and stable exit semantics;
- adoption, doctor, onboarding-plan, and next-action JSON keep contract version
  separate from the producing AgentGov version in strict `tool` metadata;
- `governance/artifacts` is treated as optional explicit export output rather
  than an unresolved core onboarding path;
- fixture tests cover healthy, unconfigured, conflict, stale `.venv`, old
  Python, deep Windows path, no-write, JSON, and missing-path behavior.
- `agentgov onboard . --dry-run` produces text or strict JSON v1.0 plans,
  preserves existing files and blocks conflicts;
- non-interactive onboarding previews explicitly set `write_authorized` to
  false and leave repository files, project environments, and Git state
  unchanged.
- redirected input, EOF, cancellation, lowercase or alternative confirmation,
  and `--non-interactive` execution cannot authorize writes;
- exact interactive `ADOPT` applies only the reviewed plan using exclusive
  file creation after a complete conflict preflight; existing files are never
  overwritten.
- `agentgov next .` returns exactly one deterministic-work,
  incomplete-evidence, human-judgment, or complete action with its source
  finding and blocking semantics;
- text and strict JSON v1.0 next-action results never execute the selected
  command or authorize repository, Git, or release changes.
- installed deep-path rehearsal completed doctor, preview, confirmed creation,
  automatic first check, and next-action selection while leaving the target
  `.venv` empty;
- the bilingual HTML Quickstarts expose this sequence only as a development
  preview until a fresh uncoached human pilot is recorded.

Stable update and release validation on 2026-07-25:

- 302 unit tests passed on Python 3.12; one platform-limited symbolic-link test
  was skipped;
- the final universal wheel built successfully;
- GitHub Actions release run `30157093313` completed successfully;
- GitHub Release `v0.1.0` published the wheel and
  `release-manifest.json`;
- the public `latest/download/release-manifest.json` endpoint resolved to
  `0.1.0`;
- the downloaded wheel SHA-256 independently matched
  `1e22d736a8701377f8ab7f15bf4ea5a34c80ae0ae944ce84973da6925ffbb18f`;
- `agentgov update --check .` used the public discovery path, reported
  installed and available version `0.1.0`, required no repository refresh,
  modified nothing, and exited `0`.

Latest local validation on 2026-07-24:

- Python 3.11.9: 212 tests passed; one Windows symbolic-link test skipped
  because the current user lacks link-creation privilege.
- User guides now preserve the Taxi-tested command order, use
  `python -m agentgov`, explain Windows nested-path failures and invalid
  `check` syntax, and provide accessible copy controls for command blocks.
- Repository self-check: 16 PASS, 2 WARN, 0 FAIL, 4 ADVISORY.
- Isolated wheel rehearsal: build, install, initialize, Capability
  Dependencies schema and declaration presence, dependency PASS, completeness
  ADVISORY, and repository check passed with zero deterministic failures.
- `git diff --check`: passed.

Integration closure on 2026-07-24:

- Capability Dependencies PR #8 merged to `main` as commit `9007fce`.
- All six pull-request CI jobs passed on Ubuntu and Windows for Python 3.11,
  3.12, and 3.13.
- The post-merge `main` CI run passed.
- Local `main` is synchronized with `origin/main`; no deterministic CI failure
  remains.

The authoritative local baseline is:

```powershell
$env:PYTHONPATH = "src"
python -m unittest discover -s tests -v
python -m agentgov check repository .
git diff --check
```

CI is the source of truth for the full supported operating-system and Python
version matrix.
