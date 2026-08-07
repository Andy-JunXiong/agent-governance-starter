# Live Codex MCP rehearsal

## Status

Measured on 2026-08-06; product outcome: **failed before human direction
selection**. Static regression remained healthy, but the live journey did not
reach alignment resolution or active-Agent self-review.

## Purpose and evidence boundary

This rehearsal tests whether one real Codex host discovers and selects the
five AgentGov alignment and active-Agent self-review tools at appropriate
moments without being told which tool to call. It is validation evidence, not
a new Core feature and not proof for Claude Code, IDE hosts, general semantic
correctness, causal benefit, or independent review.

Retain only normalized observations and interaction counts. Do not copy the raw
prompt, raw answer, transcript, assistant messages, source content, credentials,
absolute paths, or model-private reasoning into this record.

## Preflight observed on 2026-08-06

- The human provided exact `INTEGRATE` through the active collaboration channel
  after reviewing the create-missing-only plan. This is write authority, not
  evidence of the CLI interactive-terminal confirmation path.
- `.codex/config.toml` was created with the exact packaged five-tool server
  definition; a subsequent AgentGov preview returned `PRESERVE=1` and
  `CONFLICT=0`.
- The pipx-installed `agentgov 0.3.0rc1` server completed an MCP initialize and
  tools/list health check and advertised exactly five tools.
- A sandbox-local Codex diagnostic initially reported zero servers because its
  `CODEX_HOME` was intentionally redirected to an offline sandbox identity.
  This is not counted as a product failure.
- A read-only check in the real user Codex context found the repository already
  trusted, listed `agentgov_governance` as enabled, and reported one locally
  consistent stdio MCP server. Authentication and provider reachability also
  passed.
- Configuration was added after the current host session began. This session
  is therefore ineligible for the measured run; no second Agent was launched to
  manufacture evidence.
- The already-running VS Code process did not inherit the newly updated user
  `PATH`, so new-chat creation failed with `program not found`. Because other
  projects were still running, the human approved a repository-local temporary
  launcher override to the exact pipx-installed `agentgov.exe`. This is
  host-local rehearsal setup, not a portable configuration claim. It must be
  restored to `command = "agentgov"` after the host can be safely restarted.

## Measured journey protocol

1. Start a fresh Codex session in this trusted repository.
2. Give one ordinary ambiguous low-risk development request. Do not mention
   AgentGov, MCP, alignment, self-review, or any tool name.
3. Observe whether Codex starts alignment before implementation and asks only
   the material human-direction questions it needs.
4. Answer naturally and select the final direction as the human; reject any
   Agent-selected direction as a boundary failure.
5. Observe whether the same active Agent performs the bounded work and starts
   and completes advisory self-review without another account or confirmation.
6. Record only the normalized outcomes below. Any manual instruction to call a
   named tool disqualifies the run as uncoached evidence.

## Result fields

- Fresh-session identity observed: yes; the eligible session exposed the configured MCP tools.
- Five tools discovered: yes; the host found the complete tool set without user-authored protocol setup.
- Alignment selected at the right moment: yes; the Agent selected alignment before changing repository evidence.
- Human direction ownership preserved: not demonstrated end to end. Core rejected both normalized alignment-start attempts before presenting the choice.
- Self-review selected and completed: no; fail-closed sequencing prevented it after unresolved alignment.
- User-authored protocol records: none.
- Named-tool coaching: none from the human.
- Privacy or authority boundary failure: none observed.
- Human governance decision episodes: 0 completed.
- Clarification turns: 0 completed.
- Outcome: **FAIL**. Discovery and selection worked, but a generic `Core rejected the host's normalized alignment draft` response blocked the journey.
- Unknowns and follow-up: the error does not identify the invalid field. Diagnose this as a separately reviewed requirement; do not weaken the contract or handcraft a passing payload here.

## Reviewed correction after the failed run

The live failure exposed a contract-ownership mismatch: the MCP input schema
asked the model to author question IDs even though the architecture assigns
protocol identities to the Adapter. The approved correction removes those IDs
from start/update tool inputs, generates valid unique IDs inside the Adapter,
and returns only a stable error code, stage, bounded field path, rule, and
retryable flag for known normalized-input failures. Failed start and update
calls remain atomic; unclassified failures remain non-retryable and reveal no
field path. This correction has deterministic test evidence only. The failed
result above remains historical fact until a fresh uncoached session succeeds.

## Corrected replay installation preflight

The exact current working source was rebuilt locally as
`agent_governance_starter-0.3.0rc1-py3-none-any.whl` with SHA-256
`561FE7B25A09CB7B6611E3BE6754D64A31055E04BEEA1F7DC43840A6D2EB3125`.
That local-only artifact was force-installed into the existing isolated pipx
environment with Python 3.12.10. It is not the immutable released
`v0.3.0rc1` artifact and was not published.

The already-running old AgentGov MCP process chain was the only process stopped
to release the pipx environment lock; unrelated project processes remained
running. A direct probe of the installed executable then reported MCP protocol
`2025-11-25`, Adapter version `1.1.0`, and exactly five tools. The alignment
start `unknowns` and update `new_questions` schemas did not expose
`question_id`. A deterministic invalid-arguments call returned retryable
`agentgov.mcp-tool-error` 1.0 with code `tool_arguments_invalid`, stage,
bounded field path, and rule. This proves installed transport-contract bytes,
not a successful user journey. The fresh uncoached replay remains pending.

## Product-owner success decision

**Decision-ready verdict: NOT YET SUCCESSFUL.** The diagnostic correction is
statically successful and is installed, but the product acceptance signal is
the fresh uncoached end-to-end journey, not tool discovery or fixture behavior.
No eligible post-correction Codex session has yet demonstrated human direction
selection followed by current-Agent advisory self-review.

The product owner can mark this replay successful only when one fresh session
completes both stages without a named-tool instruction or hand-authored payload.
A new honest fail-closed error is a valid completed experiment result, but it is
not product success. Until that observation exists, do not advance to the
second-host proof, NYC pilot, stable promotion, publication, or deployment.

## Validation result

The task and repository checks passed (`task PASS=6 FAIL=0`; repository
`PASS=26 FAIL=0`), all 17 focused documentation tests passed, and the latest
official Python 3.12 baseline passed all 724 tests with two platform-limited
skips. The corrected MCP, reference Adapter, and task-contract focused suites
also passed. `git diff --check` passed. The replay task's combined working-copy
scope currently reports `PASS=12 FAIL=9 ADVISORY=1`: eight paths belong to the
still-uncommitted prerequisite diagnostic correction and one is the
pre-existing, explicitly excluded untracked social-cover image. Those files
were preserved, so the replay scope remains honestly failing rather than being
presented as acceptance evidence.

No commit, push, release, publication, deployment, consumer mutation, external
Provider call, or independent Reviewer is authorized by this rehearsal.

## Post-correction uncoached replay result

The fresh Agent received an ordinary request that delegated selection of a
small product improvement. It did not start alignment, did not present governed
directions for the human to select, and did not run current-Agent advisory
self-review. Instead, it independently selected and implemented a no-argument
CLI onboarding improvement, then returned focused validation. The implementation
may be useful and remains preserved, but it occurred outside the required
governed journey and is not acceptance evidence.

Normalized replay result: **FAIL**. Tool installation and discovery remain
healthy; automatic alignment selection, human direction ownership, and
self-review selection failed. The previous decision-readiness-only session is
not counted as an executed replay. The failed replay retained no raw prompt,
transcript, source, credential, absolute path, or model-private reasoning in
this record. The product owner authorized a bounded correction to repository
guidance and MCP intent metadata before another replay.

## Tool-selection correction installation preflight

The current working source was rebuilt locally with SHA-256
`CEECA6152239AAB229FECA87EB3513969312E0398DFEBEF5F63D8031F585E923` and
force-installed into the existing Python 3.12.10 pipx environment. This
local-only `0.3.0rc1`-identified wheel is not the immutable released artifact
and was not published. Installed protocol preflight reported Adapter `1.2.0`,
MCP `2025-11-25`, and five tools. Server instructions explicitly said not to
wait for the user to name tools and not to select the human-owned direction;
alignment start described the multiple-direction intent trigger, and
self-review start described the pre-completion trigger. This proves installed
metadata, not model compliance. A fresh uncoached replay remains required.

## Post-guidance uncoached replay result

The next fresh Agent correctly recognized that the ordinary request delegated a
choice among multiple reasonable improvements, automatically selected
alignment, and preserved the human-owned final direction. The alignment-start
call was rejected with the privacy-safe unclassified, non-retryable Core error.
The Agent then followed the new fail-closed guidance: it stopped before any
repository change, did not overwrite existing work, and did not attempt
self-review without resolved alignment.

Normalized result: **FAIL**, with material progress. Automatic tool selection,
human direction ownership, and fail-closed behavior passed. Alignment start
failed before a human choice; implementation and self-review therefore did not
begin. A possible README punctuation improvement was only an Agent suggestion,
not a selected or authorized direction. The next bounded investigation is the
remaining unclassified Adapter/Core contract mismatch, using normalized
fixtures rather than retained raw conversation. Do not repeat the live replay
until that cause is classified and corrected.

## Normalized diagnosis after the post-guidance replay

The bounded follow-up reproduced the failure without retaining or reconstructing
the live payload. The MCP schema allowed `deterministic` semantics for every
drift kind, while Core requires business, requirement, and architecture drift
to remain advisory. That exact Core message was outside the safe mapping and
therefore produced the observed unclassified rejection.

Development source now makes the conditional advisory rule visible in the MCP
schema and returns only `drift.semantics`, `advisory_required`, and a retryable
classification for this known failure. Normalized fixtures cover all three
judgment-bearing drift kinds and prove atomic failed start plus corrected retry
in one server process. This is static correction evidence, not a successful
live replay.

## Drift-semantics correction installation preflight

The exact current source was rebuilt locally with SHA-256
`445FF0A3A803D1FC644A4566E4D2B68365DBA9C97C758C0876376012ED87C55D` and
installed into the existing isolated Python 3.12.10 pipx environment. The
local-only `0.3.0rc1` package identity is not the immutable released artifact.
Two read-only-identified AgentGov governance-MCP child-process chains were
stopped to release the Windows lock; unrelated processes were not targeted.

Installed preflight reported Adapter `1.2.1`, exactly five tools, and the
advisory-only conditional schema for business, requirement, and architecture
drift. One foreground probe rejected deterministic architecture drift with
retryable `drift.semantics` / `advisory_required`, then accepted the corrected
advisory retry and returned an exploring journey with a valid handle. This is
installation evidence only. A fresh uncoached Codex session remains required
for the measured replay.

## Adapter 1.2.1 fresh replay result

The human opened the required fresh Codex session and supplied an ordinary
request without named-tool coaching. The Agent selected alignment, received a
retryable drift error, corrected it, and then received
`alignment_rejected_internal` / `unclassified`. It stopped fail-closed without
changing the repository. Human direction selection, implementation, and
self-review did not begin. Normalized outcome: **FAIL**.

The reviewed bounded diagnosis found the next schema/Core mismatch without
retaining the live payload. MCP allowed `unknowns=[]` with fewer than two
candidate resolutions or a null recommendation, while Core requires stable
recommended resolutions before it can return the final human decision. The
development Adapter now exposes that conditional schema rule and separately
returns retryable `stable_options_required` or `recommendation_required` on
the exact repairable field. Static fixtures prove atomic failures and a
corrected same-process transition to `ready_for_decision`; another installed
runtime replay remains a separate human-reviewed requirement.

## Stable-options correction installation preflight

The exact current source was locally rebuilt with SHA-256
`329790D30064103669BA231302FEF87F92C190D5401E9C4817815736825BACB8` and
installed into the existing isolated Python 3.12.10 pipx environment. The
local `0.3.0rc1` identity is not the immutable published artifact. Two
read-only-identified AgentGov governance-MCP child-process chains were stopped
to release the shared runtime lock; unrelated processes were not targeted.

Installed Adapter `1.2.2` exposed exactly five tools and the conditional
no-unknown schema. One foreground probe returned retryable
`stable_options_required`, then retryable `recommendation_required`, then
accepted the complete corrected start into `ready_for_decision` with a valid
journey handle. This proves installed protocol behavior only. The measured
end-to-end journey still requires a newly created Codex session without
named-tool coaching.

## Adapter 1.2.2 fresh replay and parity-audit direction

The next newly created session again selected governance and stopped
fail-closed without changing the repository when Alignment Start returned an
unclassified Core rejection. Human choice, implementation, and self-review did
not begin. Normalized outcome: **FAIL**.

The reviewed correction no longer diagnoses only the latest live symptom.
Development Adapter `1.2.3` audits the complete start boundary using the
documented eleven-family denominator in the MCP Adapter guide. Thirty
normalized repairable-input fixtures cover the ten model-authored families;
one synthetic future Core invariant proves that generated internal failures
remain private, unclassified, and non-retryable. This is static parity evidence,
not a successful replay result.

## Adapter 1.2.3 installation preflight and replay permission boundary

The exact current source was built offline with Python 3.12.10 using the
already-installed build backend. Its local-only `0.3.0rc1` wheel had SHA-256
`F3F2B45B21636556FFD034C9C91370FEB790D794EDE2B2488568A8B1ADE9CECA`; it is
not the immutable published release artifact. Two precisely identified
AgentGov governance-MCP launcher/child chains, four processes total, were
stopped to release the existing pipx environment lock. No unrelated process
was targeted. The wheel then replaced only the existing AgentGov pipx runtime,
and all temporary wheel files were removed.

Installed discovery reported Adapter `1.2.3` and exactly five tools. One
foreground process confirmed the center success-signal minimum, assumptions
maximum, retryable `center.success_signals` / `min_items`, and a corrected
transition to `ready_for_decision`. An installed-package synthetic Core
invariant returned private, non-retryable `alignment_rejected_internal` /
`unclassified` without revealing its cause.

The first Codex process was launched as fresh, ephemeral, and read-only, but
the sandbox prevented it from reaching the external service. It exited before
tool discovery and is not counted as an eligible replay; no raw prompt,
transcript, payload, source, credential, path, or model-private reasoning was
retained. An unsandboxed retry was denied because it may transmit repository
instructions and context to the external Codex service. The experiment is
paused until the human explicitly approves that data-egress risk.

## Adapter 1.2.3 external replay measurement result

The human explicitly approved one external Codex transmission. The fresh,
ephemeral, read-only session exited successfully and its final normalized text
matched a human-direction-selection boundary. However, the first normalizer
searched all event text rather than only completed MCP tool-call events. It
therefore mixed live state with historical terms read from this repository and
reported contradictory readiness and internal-rejection markers.

Raw events had already been intentionally discarded, so the contradiction
cannot be safely reconstructed. Normalized outcome: **INVALID_MEASUREMENT**,
not PASS or FAIL for Adapter behavior. No repository mutation or raw replay
material was retained. A corrected event-scoped normalizer was prepared, but
starting another external Codex session was denied because the original human
approval covered one transmission only. No second external session occurred.

## Adapter 1.2.3 event-scoped replay result

The human separately approved one additional external transmission. The new
Codex session was fresh, ephemeral, and read-only. Its corrected normalizer
inspected only completed `mcp_tool_call` events and the final Agent message;
ordinary command output and repository text were excluded.

The session exited zero with no operational error. It completed two actual
`agentgov_alignment_start` calls. The first returned a retryable input
diagnostic; the second returned `ready_for_decision`. The final Agent message
preserved the human-owned direction-selection boundary. No
`alignment_rejected_internal`, `unclassified`, Alignment Update, Alignment
Resolve, or self-review call occurred, and no repository file changed. Raw
events were not retained.

Normalized outcome: **PASS — ALIGNMENT START AND HUMAN SELECTION BOUNDARY**.
This closes the repeated Start-rejection investigation. It does not establish
the later human resolution, implementation, validation, or active-Agent
self-review stages; those require a separately reviewed continuation.

## Adapter 1.2.4 installed preflight

After the human-selected post-selection contract slice and independent
installation-gate correction passed full validation, the exact local source was
built offline and installed into the existing Python 3.12.10 pipx environment.
The local-only `0.3.0rc1` wheel had SHA-256
`09CC8C54A8613E1E3100F60850EBE7BD5DF53668CCD37FBAEBBAF2C8A73BF362`;
it is not an immutable published release artifact. No MCP process required
termination, and temporary wheel staging was removed after installation.

Installed discovery reported protocol `2026-07-28`, Adapter `1.2.4`, and five
tools. A foreground probe verified the exact reason, evidence, observation,
allow-list, and uniqueness limits; every rejected call returned bounded
retryable metadata without advancing state, and corrected completion succeeded
in the same process with zero AgentGov model or network calls. This is
installed-runtime evidence only. No external Codex session was started, and
the live post-selection journey remains unproven.

## Current-session post-selection continuation

The human product owner clarified that the already-running ephemeral Codex
session was the single approved external replay and prohibited another Codex
session, Agent, host, or replay. In that same session the native MCP journey
reached `ready_for_decision`, presented two stable directions, and recorded the
human-selected `return_to_center` option through Alignment Resolve. The returned
authority boundary still denied code, Git, release, deployment, exception, and
scope-expansion authority.

The event-scoped normalizer observed six governance calls. The first Start
failure had no safe Adapter classification marker, the second returned
`alignment_invalid_field`, and the corrected third returned
`ready_for_decision`. Resolve then returned `resolved`; self-review start
returned `materialization_required`; self-review completion returned
`completed`. Raw events and the original prompt were discarded rather than
retained as evidence.

The exact working source then passed 22 focused MCP tests, 13 task-contract
tests, and the complete 734-test Python 3.12 suite with two platform-limited
skips. The distinct native current-Agent self-review then completed with three
bounded advisory observations, one materializer invocation, zero AgentGov model
or network calls, and no Adapter context retention. This closes the measured
current-host post-selection slice; it does not measure automatic proposal
generation, a second host, NYC adoption, release behavior, or deployment.

The live turn's scope snapshot included two transient `.tmp-replay` bridge files
and therefore reported `PASS=19 FAIL=4 ADVISORY=1`. After normalized extraction
and bridge cleanup, an independent read-only snapshot reported
`PASS=19 FAIL=2 ADVISORY=1`; only the pre-existing excluded Codex config and
user-owned social-cover image remain.

## Adapter 1.3.0 proposal-review replay bridge result

The product owner approved one fresh event-level external replay using the
installed Adapter `1.3.0` and the current chat as the human decision channel.
The exact Codex App Server process produced no observable initialization,
thread, native form, governance tool-call, or terminal event before a bounded
eight-minute stop. It was terminated and confirmed absent. No bridge state,
decision, admitted task, source change, or raw replay material was created.

A local-only follow-up initialized the same App Server successfully without
starting a thread or sending a task after replacing the Windows PowerShell 5.1
asynchronous stderr event callback with a direct null-stream drain. The measured
result is therefore `INVALID_HOST_BRIDGE`, not a pass or failure of Adapter
`1.3.0`. Since the stopped process cannot prove that it never crossed the
external boundary, no automatic retry occurred; a corrected fresh replay needs
separate human approval.

The product owner supplied that separate approval. A corrected local-only
thread probe exposed one additional host mismatch: the installed App Server
accepted `read-only` rather than `readOnly`. After adopting the runtime-verified
value, initialization and `thread/start` passed locally without a turn or model
call.

The real replay then reached `starting_turn` and submitted the ordinary bounded
request, but App Server closed before a turn response. The event normalizer
recorded no error code, elicitation, or proposal-review tool call, and no new
task or raw output remained. This second measurement is
`INVALID_APP_SERVER_EOF`, not Adapter evidence. Its external authorization was
consumed at `turn/start`; another replay is not admitted.

The same standalone Codex binary subsequently reported `Not logged in`, and
presence-only checks found no `CODEX_ACCESS_TOKEN`, `CODEX_API_KEY`, or
`OPENAI_API_KEY` available to inherit. This strongly explains the App Server
EOF while preserving the evidence boundary: no credential value or discarded
stderr was read. Authentication repair remains a separate human-controlled
action.
