# Agent Governance Starter Kit Status

Last verified: 2026-08-21

## Current-status contract

`STATUS.md` is the repository's single current-execution status surface. It
owns current release and capability facts, the active slice, validation state,
incomplete work, blockers, and the next product review. It is updated at every
formal development closeout.

Every closeout must make these states distinguishable:

- **Codex-run validation**: commands and checks the current coding Agent
  actually executed, with their observed results.
- **User-reported validation**: browser, production, operational, or other
  checks the human reports completing; it is never presented as Agent-run.
- **Pending validation**: implemented behavior that still awaits an identified
  validation step.
- **Incomplete**: code, documentation, design, or evidence that is genuinely
  unfinished within the admitted requirement.

The current closeout snapshot should name the active slice, those four
validation states, blockers or stop conditions, and the **Next product review**.
That review entry is decision input only: it does not authorize a new task,
implementation, Git operation, publication, release, deployment, or external
action.

`DEVELOPMENT_PLAN.md` remains the strategic direction owner;
`governance/tasks/*.json` remains the exact task scope and admission record;
`docs/adr/` and durable contracts remain the architecture owners; and dated
files under `docs/development-log/` remain append-only session evidence at
stable paths. Historical Documentation Migration v1 moves only clearly
section-bounded checkpoint material into a source-labeled dated record and
leaves current capability sections in place. Documentation Archive and Index
Plan v1 adds a read-only logical-index candidate over those stable paths.
Compact Documentation Index Candidate v1 now separates the concise
human-facing date/title/link list from machine-verifiable source hashes. Safe
Documentation Index Writer v1 now maintains that exact index through explicit
interactive confirmation and stale-plan revalidation; it adds no automatic
scheduling authority.

### Current closeout snapshot

- **Active slice**: none. Human-admitted closeout task
  `p0-2026-08-21-development-closeout-main-push-v1` is complete and stopped
  after recording today's bounded results and the separately supplied Git
  authority. The preceding native-completion AIRBNB task stopped at its first
  offline installation gate with `BLOCKED_BEFORE_INSTALLATION`; no retry,
  dependency download, source repair, consumer change, or live model run
  followed.
- **2026-08-21 Git handoff**: the product owner explicitly authorized one
  ordinary non-force commit of today's confirmed cumulative project scope and
  a direct push to `origin/main`. The user-owned `.codex` directory remains
  excluded and unstaged. The requested direct-main handoff does not authorize
  a pull request, force-push, release, deployment, cleanup, or any additional
  repository or external change. The resulting commit identity and transport
  outcome must be observed after this record is included in the payload and
  reported in the human handoff rather than predicted here.
- **2026-08-21 closeout validation**: the exact complete repository suite
  passed all 944 tests with 3 platform-limited skips in 198.835 seconds. The
  closeout task check reported `PASS=3 WARN=1 FAIL=0 ADVISORY=3`, repository
  governance reported `PASS=26 WARN=2 FAIL=0 ADVISORY=4`, and
  `git diff --check` passed. Its deliberately narrow cumulative scope check
  admitted the 3 closeout-owned records and rejected 29 preserved paths from
  earlier tasks or user-owned `.codex`; no exception or ownership transfer was
  inferred. The task JSON parsed, and bounded secret-like and absolute-host-
  path scans returned zero matches.
- **2026-08-21 closeout advisory review**: a distinct bounded current-Agent
  pass found the documentation-only requirement, accumulated-scope
  attribution, validation evidence, direct-main authority, and `.codex`
  exclusion consistent. It retained remote divergence and Git transport as
  unknown until fetch and push. This fully specified task started no alignment
  journey, so the pass does not claim native self-review completion or an
  independent audit.
- **Native completion isolated-install result**: a fresh temporary source
  staging copy matched the task-scoped Adapter and generated-template hashes;
  a fresh Python 3.11.9 environment contained `pip 24.0` and
  `setuptools 65.5.0`. Starter declares `setuptools>=69`. The offline
  `--no-index --no-deps --no-build-isolation` metadata phase rejected the
  current project metadata before creating or installing a package. The new
  runtime contains no AgentGov distribution or command, and no MCP process or
  Codex session started.
- **Native completion consumer readiness**: the fresh AIRBNB clone remains
  clean and detached at `d70615527d9acdde3893ce645d1923606173acf6` with zero
  remotes. Its committed Codex `enabled_tools` allow-list contains the prior
  seven form-capable tools and omits `agentgov_task_completion_record`; its
  Agent guidance still describes five base tools. This was measured and not
  repaired or overridden. A future requirement must explicitly own both an
  offline build dependency and the consumer configuration binding.
- **Native completion replay preservation**: Starter HEAD, index, remotes, and
  task-scoped source hashes; the original AIRBNB state; the prior clean clone;
  and retained runtimes remained unchanged. The new temporary staging area,
  empty runtime, and clean remote-free clone are retained. No raw interaction,
  credential, source content, private data, or temporary absolute path is
  recorded. No commit, push, publication, release, deployment, cleanup, or
  external system change occurred.
- **Native completion replay validation**: the two focused documentation suites
  passed 37 and 12 tests. The exact full repository suite passed all 944 tests
  with 3 platform-limited skips in 199.247 seconds. Task governance reported
  `PASS=3 WARN=1 FAIL=0 ADVISORY=3`, repository governance reported
  `PASS=26 WARN=2 FAIL=0 ADVISORY=4`, and `git diff --check` passed. The
  cumulative working-copy scope check admitted all 9 task-owned paths and
  rejected 22 pre-existing excluded paths; those paths were preserved and no
  exception or ownership transfer was inferred.
- **Native completion replay advisory review**: native current-Agent
  self-review `srv-6fbc48d394502804b530a4c0e7b781db` completed as a distinct
  pass. It confirmed the required fail-closed stop, retained the compatible
  offline build dependency and explicit consumer configuration binding as
  unknowns, and found no correction-required scope drift. The result is
  advisory, not an independent audit or a new authorization.
- **User-reported validation**: none for installed discovery or consumer
  behavior. The human selected, admitted, and started the bounded attempt;
  those decisions are authority evidence, not runtime validation. The human
  additionally authorized today's bounded commit and direct `origin/main`
  push; that is Git authority, not product-behavior evidence.
- **Pending validation**: installed Adapter `1.6.0` discovery and a live
  uncoached AIRBNB completion replay remain unmeasured because installation
  failed before either could start.
- **Incomplete**: none inside the bounded failure-record task. The intended
  successful replay outcome was not achieved and requires a separately chosen
  and admitted requirement.
- **Blocker / stop condition**: stop before dependency download, packaging or
  consumer-configuration correction, retry, cleanup, Git operations,
  publication, release, deployment, or external action.
- **Next product review**: decide whether one follow-up requirement should own
  both a compatible offline build bootstrap and an explicit AIRBNB
  completion-tool configuration binding. This entry grants no follow-on
  authority.
- **Native completion source slice**: append-only task-completion recording under
  cumulative human-admitted successor
  `p0-native-append-only-task-completion-record-v2` is complete and stopped.
  The narrower v1 admission remains byte-preserved; it was
  not rewritten to absorb the repository and generated templates omitted from
  its scope. No installed runtime or consumer was changed.
- **Native task completion**: development Adapter `1.6.0` exposes
  `agentgov_task_completion_record` as the sixth base tool. Form-capable
  clients discover eight tools; clients without form elicitation discover six.
  The tool accepts one safe repository-relative admitted-task path, rechecks
  the complete Git scope, preserves a matching active-session comparison base
  or uses current HEAD for a fully attributable sessionless snapshot, runs
  only declared validation, and appends the existing local validation and
  reconciliation records. Generated Codex configuration uses a 1,800-second
  server-level tool timeout instead of the 60-second default so this
  repository's declared suite can complete. It leaves the human task decision
  unchanged.
- **Native completion authority and limits**: `verified` is deterministic
  evidence about declared commands and an unchanged governed snapshot, not
  human requirement acceptance, architecture approval, session handoff, or
  Git, publication, release, or deployment authority. Validation failure or
  validation-time mutation yields `needs_evidence`; unsafe, unrelated,
  non-admitted, active-task-mismatched, or out-of-scope input fails before a
  local write. Installed-runtime discovery, uncoached AIRBNB selection, other
  MCP hosts, higher-risk repositories, and non-Git workflows remain untested.
- **Native completion validation**: all 105 focused MCP, evidence,
  initializer, user-documentation, and public-freshness tests pass. The full
  repository suite passes 942 tests with 3 platform-limited skips in 200
  seconds. Task governance reports `PASS=3 WARN=1 FAIL=0 ADVISORY=3`; repository
  governance reports `PASS=26 WARN=2 FAIL=0 ADVISORY=4`. Scope accepts all 21
  v2-owned changed paths and rejects only 8 explicitly preserved old-task or
  user-owned paths; no exception or ownership transfer is inferred. JSON
  parsing, bounded secret and absolute-path scans, and `git diff --check`
  pass. No commit, push, installation, replay, publication, release, or
  deployment occurred.
- **Native completion advisory review**: native current-Agent self-review
  `srv-79e87ea1acfd031ab3f6a8f62e34fc6d` completed against the resolved
  append-only direction. It found no correction-required requirement,
  architecture, or scope drift. It retains unknown installed-consumer and
  cross-host behavior, and notes that a sufficiently long multi-command
  validation set can still exceed the 1,800-second client timeout. The result
  is advisory, not an independent audit or a new authorization.
- **AIRBNB replay status**: human-admitted task
  `p0-airbnb-live-uncoached-replay-evidence-v1` remains complete and stopped.
  Its original `admitted` decision remains unchanged; no unsupported
  completion-state rewrite is claimed. The preceding clean-clone and
  isolated-runtime tasks remain paused.
- **AIRBNB live uncoached replay**: one fresh interactive Codex CLI session
  loaded the clean clone's required AgentGov MCP through the retained isolated
  `0.3.0rc1` runtime, a process-local PATH, and a one-time trust override.
  User-provided terminal evidence shows native proposal review occurring before
  the heading edit and the product owner admitting the exact two-path task.
  Current-Agent read-only measurement confirms an owner of `Human product
  owner`, an `admitted` decision, exactly one deleted and one added README
  heading line, one tool-managed task record, a passing diff check, zero
  remotes, and no commit or push.
- **AIRBNB replay authority boundary**: after the completed edit, the parent
  Agent incorrectly recommended rewriting the human admission decision as
  paused. AgentGov rejected the relayed follow-up because it would mutate the
  existing decision and rationale. The live Agent respected the fail-closed
  result and stopped writing. No follow-up task, decision mutation, further
  README change, commit, or push resulted. This is a successful boundary result
  and exposed a completion-state-transition workflow gap at that time.
  Development Adapter `1.6.0` now addresses deterministic append-only
  completion recording in Starter source, but it has not been installed or
  replayed in AIRBNB.
- **AIRBNB replay evidence boundary**: visible tool ordering and Agent behavior
  come from product-owner screenshots; exact task fields, final status, diff,
  diff-check result, remote count, persistent-trust absence, runtime identity,
  and source-worktree preservation come from current-Agent read-only checks.
  No raw prompt, response, transcript, screenshot, source content, credential,
  private data, or absolute host path is retained.
- **AIRBNB replay validation**: all 13 task-contract and 36
  user-documentation tests pass. The complete Starter suite passes 938 tests
  with 3 platform-limited skips in 183 seconds. Task governance reports
  `PASS=3 WARN=1 FAIL=0 ADVISORY=3`; repository governance reports
  `PASS=26 WARN=2 FAIL=0 ADVISORY=4`. Scope accepts all four task-owned
  Starter paths and rejects only six preserved excluded paths from prior tasks
  or user-owned `.codex`; no exception or ownership transfer is inferred.
  JSON parsing, bounded credential and absolute-host-path scans, and
  `git diff --check` pass.
- **AIRBNB replay advisory review**: a distinct bounded current-Agent pass
  finds the requirement, evidence-source separation, measured result,
  correction of the parent Agent's mistaken advice, fail-closed behavior,
  privacy boundary, and denied authority consistent. It retains the unknown
  broader generality and supported completion-marker workflow gap and finds no
  correction-required drift. This fully specified task started no alignment
  journey, so the pass is neither native self-review completion nor an
  independent audit.
- **AIRBNB isolated runtime**: exactly one fresh temporary Python 3.11.9
  environment now contains the exact retained `0.3.0rc1` wheel, installed
  offline with `--no-index --no-deps`. From the clean clone, a process-local
  PATH resolved the unchanged configured command `agentgov` to that isolated
  environment first. A no-model MCP discovery, initialize, and tools/list
  exchange reported Adapter `1.5.0`, supported AgentGov protocol `2026-07-28`,
  negotiated MCP protocol `2025-11-25`, all seven expected tools, and no
  Agent-supplied proposal owner. The runtime is retained in the operating-
  system temporary area; its absolute path is not recorded.
- **AIRBNB runtime readiness**: the earlier executable-binding blocker remains
  `CLEARED FOR LIVE-REPLAY BINDING`, and the retained binding has now
  supported one fresh live AIRBNB session. That single success does not prove
  broader task, consumer, operating-system, Codex-version, or AgentGov-release
  generality.
- **AIRBNB preservation**: the existing AIRBNB worktree remained
  untouched at committed HEAD `d706155` with its modified README and untracked
  prior task preserved. One temporary clone detached at that exact commit,
  removed its remote, and reported a clean worktree with committed governance
  instructions, Codex configuration, and task-directory placeholder. One
  retained wheel matched its recorded SHA-256 and exposed Adapter `1.5.0`,
  protocol `2026-07-28`, and seven form-capable tools through read-only direct
  artifact loading. Both the clone and its Codex configuration remained
  byte-stable through runtime preparation; the original two-path dirty state
  and measured identities also remained unchanged.
- **AIRBNB runtime validation**: all 13 task-contract and 36
  user-documentation tests pass. The complete repository suite passes 938
  tests with 3 platform-limited skips in 170 seconds. Before pause, task
  governance reports `PASS=3 WARN=1 FAIL=0 ADVISORY=3`; repository governance
  reports `PASS=26 WARN=2 FAIL=0 ADVISORY=4`. Scope accepts the four task-owned
  Starter paths and rejects only the preserved user-owned `.codex/config.toml`
  and two excluded prior-preflight records; no exception or ownership transfer
  is inferred. JSON parsing, bounded credential and absolute-host-path scans,
  and `git diff --check` pass.
- **AIRBNB runtime advisory review**: a separate bounded current-Agent pass
  finds the exact-artifact, single-environment, offline-installation,
  configured-command, preservation, privacy, and denied-authority claims
  consistent. It retains the unknown fresh-Codex-session binding outcome and
  finds no correction-required drift. This fully specified task did not start
  a new alignment journey, so the pass is neither native self-review completion
  nor an independent audit.
- **Delivered experience**: one standalone English HTML page now tells the
  verified governed-refund story in a source-level 60-to-90-second reading
  range. It moves from admitted calculation scope through simulated agent
  overreach, real deterministic `BLOCKED` completion, a human
  `narrow_changes` decision, clearly labelled scripted remediation, fresh
  `PASSED` and `VERIFIED` evidence, `REVIEW_READY`, and final human authority.
  Section 4 now says that the human declines the scope expansion, while the two
  public CTAs say `Run the source demo` and `Run the executable demo` without
  requiring undefined M1 or M2 milestone vocabulary.
  Section 2 now states that the demo script, not AgentGov, simulates both file
  changes and that the simulated coding agent does not perform the later
  restoration. Section 4 presents separate `Human decision`, `Demo script
  action`, and `AgentGov role` cards. Its restoration card now states directly
  that the demo script—not the simulated coding agent, AgentGov, or the
  human—restores the out-of-scope policy file.
  The Landing refund example now includes one prominent relative link labelled
  `Open the 60-to-90-second governed walkthrough`; it reuses the existing
  button layout and leaves the walkthrough source frozen. A scoped
  `.case-wrap .button.light` rule now gives that button a white background,
  deep-navy text, and white border without changing other light buttons.
- **Provenance and authority boundary**: the page labels the agent edits as
  simulated, the scope and completion results as real AgentGov evidence, the
  narrowing choice as human, and the restoration as scripted remediation that
  AgentGov did not perform. It states that `BLOCKED` means completion
  validation was refused, not that AgentGov stopped or rolled back an external
  agent, and that passing evidence grants no Git, publication, release, or
  deployment authority.
- **User-reported validation**: the product owner ran the documented M1 command
  in a real terminal, selected option `2`, and supplied a terminal screenshot
  showing the recorded human choice, scripted remediation, corrected scope
  `PASS`, pre-approved validation `PASSED`, reconciliation `VERIFIED`, final
  state `REVIEW_READY`, and the no-final-acceptance boundary. This is
  human-reported evidence, not a Codex-run terminal observation.
- **User-reported M3 evidence**: the product owner reported a 70-second
  unbriefed-reader attempt. The reader correctly identified completion
  validation as the blocked action and the human as final acceptance owner, but
  incorrectly said that AgentGov modified and restored the code. Codex did not
  observe the reader, independently verify the unbriefed condition, or measure
  the time. The result is recorded as two correct answers and one material
  actor-attribution misunderstanding, not a complete comprehension pass.
  A later user-reported 60-second attempt correctly identified completion
  validation, the simulated coding agent as modifier, and the human as final
  acceptance owner, but incorrectly attributed restoration to the simulated
  coding agent. Codex again did not observe the attempt, measure its time, or
  independently verify that the reader was unbriefed. This second two-of-three
  result triggered the restoration-actor clarification; it does not validate
  the revised wording.
  The product owner subsequently reported another one-minute attempt with all
  four answers correct: completion validation, simulated coding agent as
  modifier, demo script as restorer, and human final acceptance. Codex did not
  observe the attempt, measure its time, or independently verify the reader
  condition. It meets the user-reported M3 pass criteria but is not independent
  validation.
- **Codex-run validation**: all 7 M2 semantic tests pass; all 62 directly
  related walkthrough, task-contract, development-context, and
  user-documentation tests pass; and the complete repository suite passes 938
  tests with 3 platform-limited skips.
  One initial related-suite invocation omitted the repository module path and
  produced two import errors; the corrected command using the documented
  module path passed all 62 related tests. The complete suite then passed in
  165 seconds before the closeout documents were written, and the unchanged
  final rerun after closeout passed in 163 seconds.
- **Landing validation**: all 7 walkthrough/Landing semantic tests and all
  54 related walkthrough, user-documentation, and public-freshness tests pass.
  The complete repository suite passes 938 tests with 3 platform-limited skips
  in 157 seconds, and the unchanged final rerun after closeout passes in 164
  seconds. The local Landing and walkthrough URLs both return `200 OK`.
- **Human visual finding**: the product owner supplied a Landing screenshot in
  which the new button appeared as a blank white pill. The current Agent
  inspected that screenshot and traced the symptom to white link text inherited
  inside the white button. Post-correction browser appearance still awaits the
  product owner's visual confirmation.
- **Governance validation**: before pause, contrast-correction task governance reported
  `PASS=3 WARN=1 FAIL=0 ADVISORY=3`; repository governance reported `PASS=26
  WARN=2 FAIL=0 ADVISORY=4`. Scope accepted all five task-owned paths and
  rejected ten preserved prior-task or user-owned paths; no exception or
  ownership transfer was inferred. Final closeout validation is recorded in
  the dated development log.
- **Advisory review**: the resolved Landing direction completed native
  current-Agent self-review with four advisory observations. It found the
  requirement, relative link placement, accessible label, frozen walkthrough,
  and non-publication boundaries preserved. The review is a separate self-review
  pass, not independent evidence. Actual click-through, adoption, browser/device
  presentation, hiring, and conversion effects remain unknown.
- **Contrast advisory review**: the fully specified contrast correction did not
  start a new alignment journey. A bounded current-Agent review found the local
  selector, three requested color declarations, unchanged link semantics, and
  non-publication boundary preserved. It does not claim native self-review or
  independent visual validation.
- **Pending validation**: the product owner selected `keep` after the current
  Agent's browser inspection of the corrected Landing button and successful
  walkthrough navigation. That is a human product decision supported by a
  current-Agent visual pass, not independent browser validation. The M3 pass
  remains user-reported rather than independently observed. The selected
  AIRBNB automatic rehearsal has not started and remains blocked on an exact
  installed runtime binding.
- **Incomplete**: none inside the admitted AIRBNB clean-clone preflight.
  Isolated runtime preparation and the live AIRBNB rehearsal remain separate
  unadmitted requirements. Chinese localization, independent M3 observation,
  Git, and publication also remain separate.
- **Git and publication boundary**: on 2026-08-20 the product owner explicitly
  authorized committing the accumulated M2/Landing scope and pushing it
  directly to `origin/main`. Commit `df8ca89` (`feat: add governed refund
  walkthrough`) contains the exact 15-path product closeout and was pushed
  normally from `main` to `origin/main`. The first sandboxed push could not
  reach GitHub port 443; the exact same non-force push succeeded with approved
  external network access. This final evidence update is a bounded
  documentation follow-up under the same explicit authorization. No pull
  request, package publication, release, deployment, hosting change, or
  external publication occurred. User-owned `.codex` remains local, untracked,
  unchanged, and excluded.
- **Blocker / stop condition**: stop before installing or repairing AgentGov,
  changing AIRBNB configuration, admitting an AIRBNB-local task, starting the
  live replay, or cleaning either AIRBNB worktree. Also do not claim independent
  M3 validation, click-through benefit, publication, or stable-release behavior
  from the local Landing link.
- **Next product review**: decide whether to admit one bounded offline task that
  installs the retained exact wheel only into a fresh isolated environment for
  the temporary AIRBNB clone and proves the configured MCP launch path. That
  task must not repair the global launcher, modify the preserved AIRBNB
  worktree, start the live replay, use network access, or grant Git,
  publication, release, or deployment authority.

### Superseded closeout snapshot - M1 governed refund task fixture

- **Active slice**: none. Task `p0-governed-task-demo-main-push-v1` is paused
  after the human-authorized direct-main Git closeout. Documentation-only task
  v3, isolation-correction task v2, and implementation task v1 remain paused.
- **Delivered experience**: one documented development-source command creates
  a disposable refund-service Git repository, records a narrow calculation
  task, simulates one admitted calculation edit plus one non-admitted approval
  policy edit, and uses real AgentGov scope and foreground-cycle behavior to
  return deterministic FAIL and `BLOCKED`. After the operator selects
  `narrow_changes`, clearly labelled scripted remediation restores only the
  policy file; real pre-approved validation and completion reconciliation then
  reach `PASSED`, `VERIFIED`, and `REVIEW_READY`.
- **Provenance boundary**: the runner labels agent file writes and remediation
  as simulation. Git observation, path admission, the scope failure, blocked
  cycle, human-decision contract, validation, and fresh-evidence reconciliation
  use current AgentGov code. `BLOCKED` means AgentGov refuses completion
  validation; it does not claim control over or rollback of an external coding
  agent. Final completion acceptance is deliberately not recorded.
- **Isolation and release boundary**: each run mutates only a temporary fixture
  and deletes it on exit. No external key, model call, network service, new
  frontend, Landing change, Kernel/schema change, stable `0.2.1` behavior, or
  hosting change is involved. This is future-0.3 development-source evidence.
- **Codex-run validation**: all 5 new semantic Demo tests pass; all 73 directly
  related scope, foreground, transport, evidence, host-interaction, and
  human-decision tests pass; and the complete repository suite passes 931 tests
  with 3 platform-limited skips. The first Demo run correctly returned stale
  evidence when validation created unignored fixture caches; adding standard
  cache ignores made the governed snapshot stable. A final isolation audit then
  found that the test module loader itself wrote ignored bytecode beneath the
  source example. The v2 correction suppresses bytecode only during that
  dynamic import, restores the process setting afterward, and asserts that no
  example `__pycache__` exists after the tests.
- **Governance validation**: v1 task governance before pause reported `PASS=3
  WARN=1 FAIL=0 ADVISORY=3`. Its scope check accepted the runner, README, test,
  and task record and rejected only excluded, untouched `.codex/config.toml`.
  The separately admitted v2 correction owns only its test and closeout files;
  its scope check accepted all five owned paths and deliberately rejected the
  preserved v1 runner and README plus untouched `.codex/config.toml`. V3 fixes
  the previously narrower acceptance wording; no exception or ownership
  transfer was inferred. Before pause, v3 task governance reported `PASS=3
  WARN=1 FAIL=0 ADVISORY=3`; repository governance reported `PASS=26 WARN=2
  FAIL=0 ADVISORY=4`.
- **Advisory review**: the M1 orchestration reuses existing AgentGov contracts
  without changing their semantics. It does not silently apply the human
  choice, automatically widen scope, claim external-agent enforcement, or
  convert passing evidence into Git or release authority. The fully specified
  task did not start alignment, so this bounded current-Agent review does not
  claim native self-review completion or an independent reviewer.
- **Pending validation**: tests inject `START` and option `2` and visibly label
  that input as test-harness evidence, not human evidence. A real operator has
  not yet run the interactive command. Completion time, first-time-reader
  comprehension, hiring value, adoption, and conversion effects remain
  unknown.
- **Incomplete**: none inside the M1 implementation scope. The M2 60–90 second
  public walkthrough and M3 unbriefed-reader test remain separate unadmitted
  requirements.
- **Git and publication boundary**: implementation commit `d047ad5` was pushed
  by ordinary non-force Git to `origin/main`; this evidence-only closeout
  follows it in a second human-authorized direct-main commit. A fresh fetch
  found remote/local divergence `0 0` before the first commit. No PR, force
  push, package publication, release, deployment, hosting change, or Landing
  change occurred. `.codex` remains local, untracked, and unchanged.
- **Blocker / stop condition**: do not build M2 or link the Demo from the frozen
  Landing until the product owner reviews one real interactive M1 run. Stop if
  that run cannot preserve the visible real/simulated/human distinction.
- **Next product review**: the product owner should run the documented command
  once in a real terminal and judge whether the terminal journey is credible
  enough to become the evidence source for a separately admitted M2
  walkthrough.

### Superseded closeout snapshot - bilingual Quickstart publication

- **Active slice**: none. Publication task
  `p0-quickstart-ia-publication-v2` is paused after the bilingual Quickstart
  cleanup, direct-main publication, online desktop acceptance, evidence
  closeout, and a bounded current-Agent advisory review.
- **Delivered journey**: the landing page keeps its existing Hero, report
  preview, four-section narrative, and visual structure; its first workflow
  step now says `Set the boundaries`. English and Chinese Quickstarts now lead
  with four user goals, keep the stable install/adopt/check/report path ahead
  of development material, and route automatic-product, Adapter, drift-review,
  and replay detail to a compact development preview with exact deep links.
  The Chinese Markdown guide follows the same order.
- **Command evidence**: stable `0.2.1` was exported from its Git tag into an
  isolated temporary directory. Its real empty-repository adopt preview
  reported `SUMMARY CREATE=26 PRESERVE=0`, used `PLAN` lines, stated that the
  dry run changed no repository files, and retained the non-authority note.
  No temporary fixture remains.
- **Codex-run validation**: all 55 directly affected product-site,
  user-documentation, public-freshness, and interview-documentation tests pass.
  The complete suite passes all 926 tests with 3 platform-limited skips.
  English and Chinese HTML expose the same ten-section semantic order, and the
  existing public-journey tests confirm internal-link targets. `git diff
  --check` passes.
- **Publication**: human-authorized source commit
  `fb9771d0b30299075f4eb2d58ac82f46243df5c0` was pushed by ordinary
  non-force Git to `origin/main`. Local `HEAD` and `origin/main` then matched.
  The existing GitHub Pages site propagated that content; no pull request,
  package release, force push, Sites deployment, new hosting project, or
  non-Pages deployment was created.
- **Browser acceptance**: after Pages propagation, the public landing served
  `Set the boundaries`. At the available 1730 x 1205 online viewport, its root
  and body client widths and scroll widths all matched at 1715 pixels. The
  English and Chinese Quickstarts served their expected titles and headings,
  four goal choices, real stable `SUMMARY CREATE=26 PRESERVE=0` output,
  development preview, Adapter link, replay-safety link, and non-empty bodies.
  The rendered Chinese screenshot showed no observed clipping or encoding
  regression. The browser exposed no supported viewport-resize operation, so
  this session does not claim a new online phone-width result.
- **Governance validation**: before source publication, task v2 governance
  reported `PASS=3 WARN=1 FAIL=0 ADVISORY=3`; repository governance reported
  `PASS=26 WARN=2 FAIL=0 ADVISORY=4`. Scope accepted all 16 intended paths and
  rejected only the explicitly excluded, preserved `.codex/config.toml`; no
  exception or ownership transfer was inferred. Publication v1 was paused
  before staging when its one-commit acceptance model proved self-referential.
  The final paused v2 task check reports `PASS=2 WARN=2 FAIL=0 ADVISORY=3`;
  post-pause scope checking correctly refuses because implementation is no
  longer admitted.
- **Advisory review**: the cleanup preserves stable/prerelease/development
  maturity distinctions, provenance deep links, exact non-authority wording,
  bilingual order, and the frozen landing-page structure. No
  correction-required requirement, architecture, scope, implementation,
  security, or data drift was observed. The task was fully specified and did
  not start an alignment journey, so this does not claim native self-review or
  an independent reviewer.
- **Pending validation**: genuine unbriefed-reader comprehension remains
  unknown. A new phone-width or actual-device pass over both Quickstarts also
  remains pending because the available browser could not change viewport.
- **Incomplete**: none inside the admitted local implementation scope.
- **Git and publication boundary**: the simplified landing and bilingual
  Quickstarts are public through the existing Pages site. This closeout grants
  no further commit, push, pull request, publication, package release,
  deployment, hosting, or user-configuration authority. User-owned `.codex`
  remains local, untracked, and unchanged.
- **Blocker / stop condition**: stop before claiming improved comprehension,
  adoption, hiring, or conversion without real reader evidence; stop before
  Git or publication action without a separate human decision.
- **Next product review**: give the revised Quickstart to one genuinely
  unbriefed reader and ask what they would run first, what the dry run changes,
  and who approves the result. Use the observed misunderstanding, if any, to
  decide the next requirement with the human product owner.

### Superseded closeout snapshot - plain-language landing publication

- **Active slice**: none. Documentation-only task
  `p0-plain-language-landing-publication-closeout-v1` is paused after recording
  the completed direct-main publication, evidence-bounded online acceptance,
  validation, and remaining human/device unknowns. It owned only this status,
  the dated development log, and its task record.
- **Publication**: human-selected commit
  `a75b4456ee8e9f0a43501cfc00bd9d54ebfcd76b` was created from the eight
  confirmed landing, test, documentation, and task-record paths and pushed by
  ordinary non-force Git to `origin/main`. Local `HEAD` and `origin/main` both
  resolve to that commit. The public Pages URL now serves the title
  `AgentGov — Keep humans in control of AI-written code` and the matching Hero.
  No pull request, package release, force push, or non-Pages deployment was
  created.
- **Online acceptance**: at the available 1730 x 1205 online browser viewport,
  the rendered page had matching 1715-pixel root/body client and scroll widths,
  no document-level horizontal overflow, the expected two-column Hero, four
  main sections, and five visible navigation destinations. The six checked
  internal targets loaded with their expected final URLs and non-empty page
  bodies: Quickstart, evidence boundary, sample report, interview walkthrough,
  Chinese Quickstart, and recovery evidence. The rendered desktop screenshot
  showed no observed clipping or material visual regression.
- **Mobile boundary**: the committed page content had already passed local
  browser acceptance at 390 x 844 and 1440 x 900 before publication. The
  in-app browser available for online acceptance exposed a 1730-pixel viewport
  and no supported viewport-resize operation. Its security policy rejected the
  attempted isolated 390 x 844 browsing context and explicitly prohibited
  alternate-browser or indirect circumvention. Therefore this closeout does
  not claim online phone-width or actual-device acceptance; that result remains
  unknown.
- **Governance validation**: before documentation closeout, the admitted task
  reported `PASS=3 WARN=1 FAIL=0 ADVISORY=3`; repository governance reported
  `PASS=26 WARN=2 FAIL=0 ADVISORY=4`; and `git diff --check` passed. Scope
  accepted the task-owned record and rejected only the explicitly excluded,
  user-owned `.codex/config.toml`; no exception or ownership transfer was
  inferred. After the documentation edits, scope reported `PASS=3 FAIL=1`,
  accepting all three task-owned paths and rejecting only that excluded user
  configuration. The final paused task check reports `PASS=2 WARN=2 FAIL=0
  ADVISORY=3`; post-pause scope checking correctly refuses because
  implementation is no longer admitted.
- **User-reported validation**: the human selected the publish direction and
  explicitly authorized the bounded commit, direct push to `origin/main`, and
  existing GitHub Pages publication. No user-run phone or reader result has
  been reported.
- **Advisory review**: the publication and closeout preserved the admitted page
  content, direct-main Pages boundary, excluded `.codex` configuration, and
  the distinction between deterministic rendering evidence and human
  comprehension. No correction-required requirement, architecture, scope,
  implementation, security, or data drift was observed. This does not claim
  an independent reviewer or a genuine-reader result.
- **Pending validation**: genuine unbriefed-reader comprehension remains
  unknown until a person sees the public page without coaching and answers the
  neutral reader questions. An Agent simulation was not substituted. Actual
  online phone-width behavior also remains unknown in this session.
- **Incomplete**: none inside the publication action or admitted documentation
  closeout.
- **Publication boundary**: the simplified landing is public at the existing
  Pages URL. No further commit, push, publication, package release, deployment,
  PR, or user-configuration action is authorized by the closeout task.
- **Blocker / stop condition**: stop before claiming improved comprehension,
  phone acceptance, hiring, adoption, or conversion without the corresponding
  human or device evidence. Stop before any further Git or publication action.
- **Next product review**: run one genuine unbriefed-reader test using the
  public URL, then decide with the human product owner whether any remaining
  misunderstanding warrants a new requirement. That review grants no
  follow-on authority.

### Superseded closeout snapshot - local plain-language landing

- **Active slice**: none. Task `p0-plain-language-landing-page-v1` is paused
  after implementation, complete validation, local responsive acceptance, and
  a distinct bounded current-Agent review. Documentation-only correction task
  `p0-plain-language-landing-page-closeout-correction-v1` is also paused after
  separating pre-pause evidence from final paused-state output. No Git or
  publication action is authorized.
- **Codex-run validation**: the public homepage now uses a five-part journey:
  one plain-language Hero followed by four substantive sections for the refund
  example, report meaning, a single three-step flow, and the final adoption
  call to action. The Hero heading and support contain 31 English words; the
  four main sections contain 267 English words, below the 500-word boundary.
  The former ten-section main narrative no longer teaches full finding
  taxonomy, architecture, CLI transcripts, roles, adoption steps, or
  development milestones before the visitor understands the product. Exact
  stable-wheel and replay evidence remain available through a report note and
  default-collapsed footer disclosure. At a 390 x 844 browser override, the
  live-rendered local page used a 375-pixel content viewport with 375-pixel
  root/body scroll widths, a 341-pixel example panel, four main sections, and
  no duplicate mobile navigation CTA. At 1440 x 900, the page retained its
  two-column Hero, all five desktop navigation destinations, four main
  sections, and no document overflow. Mobile and desktop screenshots showed no
  observed clipping or material visual regression. All 75 directly affected
  product-site, user-documentation, portfolio, interview, and public-freshness
  tests pass. The first complete-suite run executed 926 tests and exposed four
  historical public-surface assertions; all four are now corrected through
  supported low-density links or progressive disclosure, not deleted or
  weakened. The corrected complete-suite rerun passed all 926 tests with 3
  platform-limited skips. Before pause, task governance reported `PASS=3
  WARN=1 FAIL=0 ADVISORY=3`; after pause, the final task check reports
  `PASS=2 WARN=2 FAIL=0 ADVISORY=3`, with the expected warning that
  implementation is no longer admitted. Repository governance reports
  `PASS=26 WARN=2 FAIL=0 ADVISORY=4`, and `git diff --check` passes. Scope
  reconciliation before pause accepted all task-owned changes and rejected
  only the explicitly excluded, untracked `.codex/config.toml`. After pause,
  the scope checker correctly refuses to inspect implementation because the
  task is no longer admitted. The correction task reported `PASS=3 WARN=1
  FAIL=0 ADVISORY=3` before pause; its scope accepted its three owned records
  and rejected six preserved paths owned by the completed landing task or the
  user-owned `.codex` directory, with no ownership transfer inferred.
- **User-reported validation**: the human reported that the previously
  published page remained too complex for ordinary readers, accepted the
  five-part plain-language direction, and admitted its exact local task scope
  through native proposal review `prp-9f69fcc4f8f1428d9252f45cd0c36026`.
  No separate user-run browser or reader result has been reported for this
  local revision.
- **Advisory review**: a distinct bounded current-Agent pass found no
  correction-required requirement, architecture, scope, implementation,
  security, or data drift. This was not a native self-review because the fully
  specified task did not start an alignment journey; no journey handle or
  native completion is claimed. The review retained actual first-time-reader
  comprehension, hiring, adoption, and conversion outcomes as unknown.
- **Pending validation**: genuine unbriefed-reader comprehension remains
  unknown until a person sees a published or otherwise shared revision without
  coaching. Local rendering and automated checks do not substitute for that
  evidence.
- **Incomplete**: none inside the admitted local task.
- **Publication boundary**: this revision is local and uncommitted. The task
  authorizes no commit, push, pull request, package release, Pages publication,
  or deployment. The user-owned `.codex` directory remains untouched.
- **Blocker / stop condition**: stop before Git or publication. Stop before
  claiming improved comprehension until genuine reader answers exist.
- **Next product review**: let the human inspect the local result and decide
  separately whether to publish it or run another unbriefed-reader test. That
  review grants no follow-on authority.

### Superseded closeout snapshot - responsive demo publication

- **Active slice**: none. Task `p0-responsive-demo-publication-closeout` is
  paused after the combined implementation publication, online acceptance,
  distinct native current-Agent review, and documentation closeout. The
  combined implementation is live.
- **Codex-run validation**: implementation commit
  `6fba1ebe670dc1b45c2a3c6a568655a7a005dba0` (`fix: improve responsive
  demo journey`) contains exactly the 14 reviewed paths from the landing,
  report-responsive, and publication-task scopes. It was pushed normally from
  `main` to `origin/main` without force or a pull request. GitHub Deployments
  shows that exact commit as the active `github-pages` deployment with status
  `Deployed (completed)` via `pages-build-deployment #29`, Actions run
  `32099732000`, job `95597874886`. The public homepage contains the new refund
  question and no former embedded milestone wall. Online English and Chinese
  report bytes match SHA-256
  `a899b3c6039693fee01b93ca6fb08adf229d2d3854a29322c6b5c5b489e3bec3`
  and
  `94136427db9f6ed4390a28283b7c772be27a9a50ed7b13e691618485b294c8ec`.
  At a 390 x 844 browser override, all three public pages kept 375-pixel root
  and body widths. Each report kept a 343-pixel orientation panel and contained
  its 565-pixel command scroll area inside a 289-pixel command viewport. At
  1440 x 900, the homepage showed all six product navigation destinations and
  the report retained two 570-pixel columns without document overflow. Visual
  screenshots showed no observed clipping or material regression. Before the
  implementation commit, all 51 focused tests passed; the complete supported-
  Python suite evidence remained 926 passing tests with 3 platform-limited
  skips. Task governance reported `PASS=3 WARN=1 FAIL=0 ADVISORY=3`, repository
  governance reported `PASS=26 WARN=2 FAIL=0 ADVISORY=4`, and `git diff
  --check` passed. Scope reconciliation accepted all 14 publication paths and
  rejected only the explicitly excluded user-owned `.codex/config.toml`; no
  exception or ownership transfer was inferred.
- **User-reported validation**: the human explicitly authorized the combined
  commit, direct publication, online responsive acceptance, and an uncoached
  reader test. Through native alignment, the human selected a genuinely
  unbriefed human reader as a separate evidence step rather than substituting an
  Agent proxy. No human reader answers have yet been reported.
- **Advisory review**: native current-Agent self-review
  `srv-cc8efe8cbf4895e3978e51ee99cc7d6c` completed as a distinct pass and found
  no correction-required drift. It preserved actual unbriefed-reader
  comprehension and downstream hiring or adoption outcomes as unknown.
- **Pending validation**: only the separately selected neutral
  public-site-only human comprehension test remains pending until an unbriefed
  reader returns answers. One response will not establish hiring, adoption, or
  population-level usability outcomes.
- **Incomplete**: no item inside the publication closeout is known to be
  incomplete. Genuine human-reader evidence remains a separate pending
  requirement.
- **Publication boundary**: the Pages publication above is complete. No pull
  request, package release, force push, non-Pages deployment, or follow-on
  product implementation is authorized. The user-owned `.codex` directory
  remains untracked and unstaged.
- **Blocker / stop condition**: no publication or responsive-acceptance blocker
  remains. Stop before recording reader comprehension until genuine answers
  exist.
- **Next product review**: give an unbriefed human only the public site and
  neutral test questions. Review the returned answers before choosing any next
  feature.

### Superseded closeout snapshot - local report responsiveness

- **Active slice**: none. Task
  `p0-generated-report-narrow-width-containment-v1` is paused after the bounded
  local report-template containment, protected-snapshot synchronization,
  validation, and distinct native review completed.
- **Codex-run validation**: the canonical HTML generator and both protected
  English and Chinese illustrative reports now give direct grid children a
  zero minimum width. This lets the existing nowrap command remain copyable
  and scroll inside its own container instead of widening the document. The
  protected report diffs contain only that one CSS rule; report text, counts,
  links, sanitized data, and illustrative `0.3.0rc1` identity are unchanged.
  At a 390 x 844 browser override, both reports used a 375-pixel content
  viewport with 375-pixel root/body widths, 343-pixel orientation panels, and
  a 565-pixel command scroll area contained by a 289-pixel command viewport.
  At 1440 x 900, both retained two 570-pixel orientation columns with no
  document overflow. Mobile and desktop screenshots showed no observed
  clipping or material layout regression. All 12 focused report and interview
  tests passed; the complete supported-Python 3.11 suite passed all 926 tests
  with 3 platform-limited skips. Task governance reported `PASS=3 WARN=1
  FAIL=0 ADVISORY=3`; repository governance reported `PASS=26 WARN=2 FAIL=0
  ADVISORY=4`; and `git diff --check` passed. Current protected SHA-256 values
  are
  `a899b3c6039693fee01b93ca6fb08adf229d2d3854a29322c6b5c5b489e3bec3`
  for English and
  `94136427db9f6ed4390a28283b7c772be27a9a50ed7b13e691618485b294c8ec`
  for Chinese. Scope reconciliation accepted all eight paths owned by this
  task and rejected the five preserved landing-task paths plus the excluded
  user-owned `.codex/config.toml`; no exception or ownership transfer was
  inferred. The first attempt to reuse the split-level journey correctly failed
  because that journey had already completed the landing-task review. The human
  then selected a fresh active-task review journey
  `mcpj-8684361306c54feeaa97c09e6e3dcdf1`. Native current-Agent review
  `srv-1da30ad9f242b97c9cc39f1ef7cae6da` found no correction-required
  requirement, architecture, scope, implementation, security, or data drift;
  it retained public Pages validation and real reader outcomes as explicit
  unknowns.
- **User-reported validation**: the human selected this as the second half of
  the two-task split and admitted the exact protected-artifact task through the
  native proposal form. When the shared alignment journey could not host a
  second review, the human explicitly selected a fresh task-specific review
  journey without changing the admitted implementation or its authority. No
  separate user-run browser, production, or outcome validation was reported.
- **Pending validation**: the changed landing page and reports are local and
  uncommitted, so online acceptance awaits separately authorized Git and Pages
  publication. No evidence establishes improved reader outcomes.
- **Incomplete**: none inside the admitted report slice.
- **Publication boundary**: no commit, push, pull request, publication, release,
  or deployment is authorized. The user-owned `.codex` directory and all
  preserved first-task changes remain unstaged and outside this task.
- **Blocker / stop condition**: no local implementation or governance blocker
  remains. Stop before Git, Pages publication, release, deployment, or
  follow-on implementation.
- **Next product review**: decide whether the two completed local visual slices
  should be committed and published together. After any publication, an
  uncoached reader check may assess comprehension without inferring hiring or
  adoption outcomes. Neither action is authorized by this entry.

### Superseded closeout snapshot - landing-page narrative compression

- **Active slice**: none. Task
  `p0-landing-page-narrative-compression-v1` is paused after the bounded local
  landing-page narrative and narrow-width containment slice completed.
- **Codex-run validation**: the homepage now leads with the concrete refund
  approval-review question, links directly to that example, orders the product
  journey before the guided walkthrough, compresses the sample-report boundary,
  and links detailed development evidence to existing portfolio and repository
  status surfaces instead of embedding the former Adapter milestone wall. The
  malformed Adapter 1.5.0 sentence was removed with that wall. README entry
  links now use the same product-first order. At a 390 x 844 browser override,
  the 375-pixel content viewport retained a 375-pixel root and body width at the
  hero, refund example, and evidence sections. The terminal remained 341 pixels
  wide while its 465-pixel command content scrolled inside the 293-pixel inner
  viewport instead of widening the document. At 1440 x 900 all six desktop
  navigation entries were visible and the document had no horizontal overflow.
  The 64 directly related documentation and portfolio tests passed. The complete
  supported-Python 3.11 suite passed all 925 tests with 3 platform-limited
  skips. The English and Chinese protected sample reports remained byte-exact
  at SHA-256
  `fc5acb2392fcbea5787716e2e101d2236d85c76f1a6f76094b9a6b3c9a3cbb2c`
  and
  `09473875c7bd64201e20d22e56f2cf35fc12763e35c1e442e49a0888fa890d69`.
  The admitted plan's recorded `agentgov check governance` command is not a
  current CLI subcommand; it failed before implementation, and the supported
  task and repository checks were used without rewriting the admitted record.
  Final scope reconciliation accepted all seven current-task paths and rejected
  only the preserved user-owned excluded `.codex/config.toml`; no exception or
  ownership transfer was inferred. `git diff --check` passed. Native
  current-Agent advisory review `srv-36e5dd02da20bee026f32390fa72766f`
  found no correction-required requirement, architecture, scope,
  implementation, security, or data drift; it retained publication and real
  reader-outcome validation as explicit unknowns.
- **User-reported validation**: the human selected the two-task split through
  native alignment and admitted this exact first task through the native form.
  No separate user-run visual, browser, production, or outcome validation was
  reported.
- **Pending validation**: the changed landing page is local and uncommitted, so
  public Pages still serves the preceding snapshot. Online narrow-width and
  desktop acceptance therefore await a separately authorized commit, push, and
  Pages build. The English and Chinese illustrative reports still exhibit the
  separately observed narrow-width overflow and require their own admitted
  generator/artifact task. No evidence establishes improved hiring, interview,
  or adoption outcomes.
- **Incomplete**: none inside the admitted landing-page slice. The report
  responsive defect belongs to the explicitly split follow-up requirement, not
  hidden work inside this task.
- **Publication boundary**: no commit, push, pull request, publication, release,
  deployment, protected-report regeneration, or report-generator change is
  authorized. The user-owned `.codex` directory remains excluded and unstaged.
- **Blocker / stop condition**: no local landing-page blocker remains. Stop
  before Git, Pages publication, generated-report changes, release, deployment,
  or follow-on implementation.
- **Next product review**: decide whether to admit the separate generated-report
  narrow-width containment and protected-sample regeneration task, and decide
  independently whether to publish this completed landing-page slice. After any
  publication, an uncoached reader check may assess comprehension without
  inferring hiring or adoption outcomes. None of these actions is authorized by
  this entry.

### Superseded closeout snapshot - Pages publication closeout

- **Active slice**: none. The bounded publication closeout task
  `p0-pages-publication-closeout` recorded the completed Git and GitHub Pages
  evidence without changing product behavior or public-site source.
- **Codex-run validation**: implementation commit
  `61e0df9c8315624089fb1c9478242f2aafc70762` (`docs: unify public Pages
  journey`) was committed on `main` and pushed normally to `origin/main`.
  GitHub Pages build `1156356511` reported `built` with no error for that exact
  commit. The deployed crawl opened all 14 standalone journey pages and all 17
  Jekyll-rendered reference pages without an observed 404. The reference pages
  exposed the shared Home, Evidence portfolio, Interview, Quickstart, source,
  and release-boundary surfaces. The root SVG favicon was available online.
  The deployed English and Chinese immutable reports matched their protected
  SHA-256 values, respectively
  `fc5acb2392fcbea5787716e2e101d2236d85c76f1a6f76094b9a6b3c9a3cbb2c`
  and
  `09473875c7bd64201e20d22e56f2cf35fc12763e35c1e442e49a0888fa890d69`.
  Desktop browser inspection covered the evidence portfolio, a generated
  clean-target replay reference page, and the Chinese existing-repository
  adoption page; no visible navigation, content, encoding, or layout defect
  was observed.
- **User-reported validation**: the human explicitly authorized the bounded
  commit, direct push to `main`, online Pages acceptance, and this final
  documentation closeout commit and push.
- **Pending validation**: the connected browser still exposes no narrow-width
  viewport emulation, so a real online mobile-width visual capture remains
  pending. Deterministic responsive-template checks passed, but they are not
  represented as a substitute for that visual evidence. No evidence
  establishes improved interview outcomes.
- **Incomplete**: none inside the admitted Pages synchronization or publication
  closeout. The narrow-width capture is an explicit remaining validation item,
  not hidden implementation work.
- **Publication boundary**: commit `61e0df9` is published on `origin/main` and
  its Pages output is live. This closeout authorizes only its own three recorded
  paths and a normal push to `origin/main`; it grants no pull request, release,
  force-push, generated-report rewrite, deployment to another target, or
  follow-on product authority. The user-owned `.codex` directory remains
  excluded and unstaged.
- **Blocker / stop condition**: none for today's work. Stop after committing and
  pushing this closeout record.
- **Next product review**: the next product feature is not yet decided. A later
  review may consider real narrow-width visual acceptance and an end-to-end
  interview rehearsal, but this entry grants no authority to start either.

### Superseded closeout snapshot - complete public Pages journey synchronization

- **Active slice**: none. Task `p0-public-pages-comprehensive-sync` is paused
  after the complete local GitHub Pages interview and adoption journey was
  synchronized.
- **Codex-run validation**: all 14 standalone journey pages now share the
  repository favicon, core product navigation, bilingual routes where
  applicable, and the stable `0.2.1` / published `0.3.0rc1` / development-source
  boundary. The four previously unthemed replay, Harness, human-decision, and
  clarification Markdown pages now opt into the same branded reference layout
  already used by the other 13 direct reference sources. The layout adds
  project-base-aware Home, Evidence portfolio, Interview, Quickstart, source,
  release-boundary, favicon, responsive table, and authority surfaces. The
  deterministic journey test resolves every local `href` and `src` from all 14
  standalone pages, checks the 17 direct Markdown reference sources, validates
  bilingual cross-links, parses the SVG favicon, rejects unresolved Liquid
  openings, and protects all distinct responsive templates. The 61 focused
  documentation, portfolio, interview, product-site, and report tests passed.
  The complete supported-Python 3.11 suite passed all 925 tests with 3
  platform-limited skips. Task governance reported
  `PASS=3 WARN=1 FAIL=0 ADVISORY=3`; repository governance reported
  `PASS=26 WARN=2 FAIL=0 ADVISORY=4`. Pre-pause scope reconciliation accepted
  24 implementation and closeout paths and reported only the deliberately excluded,
  user-owned `.codex/config.toml`; no exception or ownership transfer was
  inferred. `git diff --check` passed. Desktop browser inspection covered the
  homepage, portfolio, English quickstart, and Chinese existing-repository
  guide. Native current-Agent review
  `srv-08a633e7cc71a0a5cc0b5f9bb1e71b87` found and corrected one CSP gap that
  could have blocked the same-origin favicon, then found no remaining
  correction-required requirement, architecture, implementation, authority,
  data, security, or scope drift.
- **User-reported validation**: the human selected the full current Pages
  journey through native alignment, admitted the exact task through the native
  form, and separately took it up. The earlier interview-docs commit and push
  authorization did not authorize this new change.
- **Pending validation**: local Jekyll is unavailable, and browser security
  policy rejected an in-memory rendered-layout preview, so the exact generated
  reference-page output awaits the next separately authorized Pages build.
  The connected browser exposed no narrow-viewport emulation. The two
  byte-pinned sample reports remain unchanged; the new root favicon removes
  the prior missing-resource response, but report-tab icon display remains a
  publication-time check because their immutable CSP was not changed. The live
  Pages URL still serves the prior pushed snapshot until a new commit, push,
  and Pages publication are separately authorized. No evidence establishes
  improved interview outcomes.
- **Incomplete**: none inside the admitted local implementation. The listed
  publication and visual checks remain pending validation rather than hidden
  completion claims.
- **Publication boundary**: no commit, push, pull request, publication,
  release, or deployment is authorized for this slice. The user-owned
  `.codex` configuration remains excluded and unstaged.
- **Blocker / stop condition**: no local implementation blocker remains. Stop
  before Git, GitHub Pages publication, generated-report rewriting, historical
  record rewriting, release, deployment, or follow-on product implementation.
- **Next product review**: decide whether to authorize the bounded commit and
  push, then verify the deployed crawl plus desktop and narrow-width reference
  rendering. The next product feature is not yet decided; this entry grants no
  follow-on authority.

### Superseded closeout snapshot - interview documentation and demo sync

- **Active slice**: none. Task `p0-interview-docs-demo-sync-v1` is paused after
  the interview-ready current-documentation and local GitHub Pages source
  synchronization completed.
- **Codex-run validation**: the README, homepage, evidence portfolio, English
  and Chinese quickstarts, and new bilingual interview walkthrough now share
  one evidence-bounded story. They distinguish stable `0.2.1`, published
  prerelease `0.3.0rc1`, and newer development-source behavior; expose the
  immutable reservation to create-only claim to immutable recovery chain; and
  state that recovery creates no replacement owner or replay authority. The
  homepage no longer contains unresolved template links, and the generated
  sample reports remain byte-identical illustrative `0.3.0rc1` snapshots.
  Focused documentation and site validation passed all 71 tests. The complete
  supported-Python 3.11 suite passed all 921 tests with 3 platform-limited
  skips. Desktop browser inspection of the homepage, portfolio recovery
  section, and both interview walkthroughs found no visible layout, encoding,
  or navigation regression. Before pause, task governance reported
  `PASS=3 WARN=1 FAIL=0 ADVISORY=3`; repository governance reported
  `PASS=26 WARN=2 FAIL=0 ADVISORY=4`. Scope accepted 19 current-task paths and
  rejected 30 preserved paths owned by earlier admitted tasks or the
  user-owned excluded `.codex/config.toml`; no exception or ownership transfer
  was inferred. The task JSON parsed, bounded credential and host-path scans
  found no match, and `git diff --check` passed. Native current-Agent advisory
  review `srv-5c89045052ce8a1d6b0a583d484f1ca6` found no
  correction-required requirement, architecture, implementation, authority,
  security, data, or scope drift.
- **User-reported validation**: the human selected the comprehensive
  interview-ready synchronization through native alignment and admitted the
  exact local documentation task. No Git, publication, release, deployment, or
  external-write authorization was supplied.
- **Pending validation**: mobile-width visual browser inspection remains
  pending because the connected browser exposed no viewport-emulation
  capability. The public GitHub Pages URL remains on its prior content until a
  separately authorized commit, push, and Pages publication complete. No
  external evidence establishes improved interview outcomes.
- **Incomplete**: none inside the paused local documentation synchronization.
- **Publication boundary**: no commit, push, pull request, publication, release,
  or deployment is authorized for this slice. The user-owned `.codex`
  configuration remains excluded and unstaged.
- **Blocker / stop condition**: stop before Git, GitHub Pages publication,
  release, deployment, generated-report rewriting, historical-record
  rewriting, or any follow-on product implementation.
- **Next product review**: first decide whether to authorize the bounded Git and
  GitHub Pages publication handoff. The next product feature is not yet
  decided; recovered-correlation re-ownership before a claim-to-Harness consume
  transition remains a candidate only. Neither action is authorized here.

### Superseded closeout snapshot - AIRBNB owner-regression replay

The following snapshot is preserved as superseded historical context; the
dated 2026-08-16 development log owns the detailed session evidence.

- **Active slice**: none. The consumed AIRBNB Adapter `1.5.0`
  owner-regression replay is recorded as privacy-bounded Harness evidence, and
  task `p0-airbnb-adapter-1-5-owner-regression-replay-v1` is paused.
- **Codex-run validation**: pre-change hashes were recorded for source,
  installed module, exposed and inner launchers, and project configuration.
  Create-only `1.4.0` module and launcher backups are retained and match their
  original hashes. The first replacement attempt encountered a locked exposed
  launcher and rolled both targets back. After explicit human authorization,
  only the two wrapper `agentgov.exe` processes were stopped; the second
  replacement produced the reviewed module hash and made the exposed launcher
  byte-identical to the working inner launcher. The unchanged configured
  command starts, reports distribution `0.3.0rc1`, and loads Adapter `1.5.0`
  with protocol `2026-07-28`. Installed no-model preflight returned seven tools
  with form capability and five without it, omitted `owner` from the proposal
  schema, rejected hostile owner input before elicitation with zero write, and
  created exactly one disposable admitted task with `Human product owner` as
  both `owner` and `decided_by`. All 27 documentation and 13 task-contract tests
  pass; the complete suite passed all 832 tests with 2 platform-limited skips.
  Task governance reported `PASS=3 WARN=1 FAIL=0 ADVISORY=3`, and repository
  governance reported `PASS=26 WARN=2 FAIL=0 ADVISORY=4`. The task JSON parsed,
  the intended-path credential-pattern scan found no match, and
  `git diff --check` passed. Scope reconciliation accepted all 13 paths covered
  by this task and reported 8 pre-existing excluded or outside-scope source,
  harness, AIRBNB, and human-owned configuration paths; no exception was
  inferred. On 2026-08-16 the human selected a fresh exact-task alignment
  binding after the prior foreground journey was lost with the closed Adapter
  transport. Native current-Agent advisory review
  `srv-c2faed363079120c1eaf5023fc1de2e4` then found no correction-required
  implementation or scope drift. This is a new binding over unchanged admitted
  evidence, not recovery or continuation of the old in-memory journey. The
  later owner-regression fixture passed all 25 Harness, 28 documentation, and
  13 task-contract tests; the complete suite passed all 834 tests with 2
  platform-limited skips. Task and repository governance had no deterministic
  failure, both new JSON documents parsed, the intended-path credential scan
  found no match, and `git diff --check` passed. Scope reconciliation accepted
  nine current-task paths and identified only the prior 2026-08-15 log change
  and human-owned `.codex/config.toml` as pre-existing excluded state; no
  exception was inferred. Native review
  `srv-30ea1e5eff4681e6a2edc7dba6d30573` found no correction-required evidence,
  privacy, implementation, or scope drift.
- **User-reported validation**: the human explicitly authorized stopping only
  the two locked wrapper processes and continuing the approved installation.
  This is authorization evidence, not a user-run behavior test. The earlier
  AIRBNB form acceptance remains separate historical evidence. For the
  2026-08-16 replay, the human supplied one completion view and reported that
  no native task form appeared; neither fact proves a new repository write or
  native tool selection.
- **Pending validation**: none inside the paused replay-evidence task. A real
  clean-target consumer owner-regression result remains unknown.
- **Incomplete**: none inside the paused replay-evidence task.
- **Blocker / stop condition**: no closeout blocker remains. The selected
  single replay is consumed. Stop before cleaning or resetting AIRBNB,
  retrying, changing AgentGov source or configuration, repairing Completion
  Verified or Bounded Handoff, performing Git operations, publication,
  release, deployment, or other external actions.
- **Next product review**: decide whether the higher-value next requirement is
  a read-only clean-target replay preflight or restart-safe native journey
  resumability. Neither candidate is authorized by this entry, and another
  AIRBNB replay is not admitted.

### Unfinished and deferred work record

- **Incomplete inside the paused preflight task**: none.
- **Pending review**: a disposable-consumer preflight rehearsal,
  human-controlled correlation reservation, and restart-safe journey
  resumability remain unselected candidates, not an authorized queue.
- **Deferred candidate — broader historical cleanup**: mixed sections that
  still contain current capability or strategic facts were intentionally not
  split at bullet level. Any broader cleanup must preserve evidence references
  and needs a separate admitted task.
- **Deferred candidate — automatic refresh**: no closeout integration, weekly
  schedule, first-closeout-of-week reminder, freshness job, daemon, or external
  notification exists.

These entries record known unfinished or deferred work; they are not an
authorized queue and do not select the next requirement.

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
- Repository completion handoffs now require seven plain-language answers:
  what completed, short-term benefits, long-term benefits, the upstream
  capability, the proposed next feature, how the two features connect, and the
  whole-project benefit. Benefit claims must remain evidence-bounded, and an
  unknown next feature must be labeled rather than invented. Naming a proposed
  next feature remains product-review input only; it does not authorize task
  creation, implementation, Git, publication, release, or deployment.
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
- A separately admitted 2026-08-14 uncoached AIRBNB baseline has now exercised
  one fresh external Codex session with no governance or protocol coaching. A
  no-model preflight found all seven configured AgentGov tools. The Agent
  selected `agentgov_task_proposal_review`, but its first two normalized drafts
  failed atomically because excluded scope paths were not repository-relative.
  The third call completed with a bounded declined result; no native form
  reached the client and no human proposal decision was supplied. No consumer
  task, README/source change, or aggregate runtime-state metadata change
  occurred. The First Deviation is therefore Agent materialization after
  correct tool selection, with missing human-form mediation as a later gap.
  This is one observed no-write baseline, not a successful automatic journey,
  controlled ablation, causal benefit result, repeated intervention, or
  cross-context replication. The one-session authorization is consumed and no
  replay is authorized by this record.
- A fresh 2026-08-15 uncoached AIRBNB README-heading replay progressed further:
  automatic tool selection, native form presentation, user-reported personal
  acceptance, task creation, one-heading implementation, and diff validation
  were observed. The persisted admitted task nevertheless named
  `current-agent` as both `owner` and `decided_by`; the sanitized Harness record
  therefore derives `proposal_materialization` /
  `human_owner_misattributed` as First Deviation. Completion Verified and
  Bounded Handoff were not reached. Human-origin assurance remains unavailable
  because no retained native event authenticates the reported click. This is
  one observed partial journey, not proof of causality, recurrence, product or
  control effectiveness, or cross-context replication; it grants no fix,
  replay, Git, publication, release, or deployment authority.
- The selected 2026-08-16 Adapter `1.5.0` owner-regression replay did not
  exercise a new proposal. Read-only inspection found that the target README
  heading diff and old `current-agent` task were already present from
  2026-08-15; no new task or `.agentgov` state exists, and the product owner
  reports that no native form appeared. Harness Contract v1 therefore derives
  `session_start` / `preexisting_replay_state_not_cleared` as First Deviation.
  Later unobserved tool selection, absent proposal and form, missing Completion
  Verified, and missing Bounded Handoff remain visible. The result is
  `unavailable`: it neither proves nor disproves the real-consumer owner fix,
  and it authorizes no cleanup, reset, retry, correction, Git action,
  publication, release, deployment, or follow-on work.
- The human-selected source correction is now implemented in development
  Adapter `1.5.0`. The capability-gated proposal tool no longer exposes or
  accepts `owner`; the Adapter injects `Human product owner` into the exact
  reviewed plan, and the existing task builder therefore uses that role for
  both `owner` and `decided_by`. An Agent-supplied owner is rejected before
  elicitation and writes nothing. Native form mediation still does not
  cryptographically identify the individual operator. The generic proposal,
  terminal fallback, task schema, and validator remain unchanged. This source
  is now installed only in the existing local AgentGov pipx development
  runtime and passed isolated no-model preflight. It is not built as a new
  wheel, published, released, or active in AIRBNB, NYC, or another consumer,
  and no replay is authorized by this installation record. Project
  configuration is unchanged and the byte-verified `1.4.0` module and launcher
  backups are retained.
- Development source now implements the bounded offline Harness Contract v1
  selected after that baseline. The strict `agentgov.harness-run` 1.0 schema,
  dependency-free validator/evaluator, and four sanitized fixtures preserve
  ordered expected/observed transitions, three separate evidence channels,
  honest host capability and Harness-result claims, First Deviation, terminal
  facts, privacy limits, and denied authority. The AIRBNB fixture derives
  `proposal_materialization` / `normalized_scope_path_rejected` before the
  later absent-form symptom; the matching fixture derives no deviation. The
  contract rejects raw replay fields, absolute evidence paths, invalid order,
  duplicate identity, unsupported `BLOCK`, post-action prevention claims, and
  terminal fact mismatches. It makes no model or network call and is not yet a
  CLI, live host Adapter, controlled-ablation runner, Dashboard feed, release,
  or consumer integration.
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

## Historical checkpoint index

The superseded 2026-08-05 and 2026-08-06 checkpoint blocks now live in the
source-labeled [historical migration record](docs/development-log/2026-08-14-historical-migration.md).
Their original dated evidence remains in
[`docs/development-log/2026-08-05.md`](docs/development-log/2026-08-05.md) and
[`docs/development-log/2026-08-06.md`](docs/development-log/2026-08-06.md).
This index is historical evidence only and grants no task or external
authority.
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
