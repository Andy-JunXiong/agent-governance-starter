# Read-only MCP configuration diagnostic v1 — 2026-11-06

## Goal, scope and admission

The product owner selected a bounded read-only MCP configuration diagnostic
after the prior runtime installation was found already handed off. The native
alignment journey `mcpj-6084d46d09204671b1e031714f7fe6ec` recorded the exact
`return_to_center` selection at `2026-11-06T08:09:38.046Z`. This selection did
not admit a task or grant source-write authority.

The first native proposal call timed out after 60 seconds; the next returned
`task_proposal_elicitation_transport_required`. The human reported that no
native form appeared. Work stopped at that boundary. Subsequent read-only
inspection established that the installed module matches source and that a
still-pending native form dispatches a second form request through a path
which produces that error. This explains a possible retry failure, not the
unobserved cause of initial form non-delivery. The installed extension contains
native form handling and supports the supplied schema shape; lack of shipped
form support was not established. Native form repair remains outside this task.

The product owner explicitly allowed a one-time exception to use the existing
terminal human-admission flow for the previously selected diagnostic. A new
generic proposal was prepared through the existing reference materializer;
it was not represented as the timed-out native proposal. The read-only plan
validated before any repository write. Terminal admission does not implement
the native post-form inventory guarantee. Separate inventory checks before
review and after admission preserved the 12 pre-existing non-state records
(digest `sha256:820ab87151afacd60beaebb8f0f6c2982d36977a1c4dd6366562e0bb873e3d87`):
STATUS was included with unrelated work preserved; the other 11 paths and 178
local state paths were excluded from implementation.

Early terminal attempts created no task. The first helper saved insufficient
error detail. A later attempt captured exit 1 and the CLI cancellation result;
it did not report a filesystem-write error. Read-only console probes confirmed
real input handles. A separate harmless TEST probe retained no input text and
found an exact-case mismatch with no whitespace, control or full-width
characters; this does not reconstruct the earlier input. After clarification
of the existing uppercase requirement, the human successfully entered the
terminal confirmations. No Agent supplied ADMIT or REPLACE, changed the input
comparison, mocked terminal state or invoked an admission writer directly.

The supported CLI created
`governance/tasks/p0-mcp-config-readonly-diagnostic-v1.json` from proposal
`prp-eacf21955cd5481c96f661ff6cb3e75f`. The human separately started its session
at `2026-11-06T09:04:03.221Z`, comparison base
`338f55e67c37e8a9b1a89abd5652484db3524578`. Task validation and start preview
exited zero. The parent read the admitted task and independently matched its
canonical digest to the session before source edits.

Goal: explain local tool filtering and timeout differences through the existing
doctor command. Non-goals: changing live configuration, invoking governance
tools from the diagnostic, restarting services, repairing native elicitation,
new Kernel semantics, installation, Git operations or release. Acceptance:
bounded local reads; truthful non-blocking findings; private output; regression
coverage; synchronized current documentation/distribution identity; declared
validation and distinct native advisory review. Stop on failed required
governance, validation, identity or scope checks.

## Implementation checkpoint

The parent owns the diagnostic implementation, shared generated timeout
constant, detailed MCP guide, status, distribution identity and this record.
One bounded worker owns doctor/onboarding regression tests; another owns README,
bilingual troubleshooting and documentation regressions. Their ownership is
disjoint; the parent reviewed returned evidence rather than repeating searches.

The doctor report shape and exit policy remain unchanged. Only the selected
repository's `.codex/config.toml` is read, with a 256 KiB limit, regular-file,
reparse and pre-read identity checks. Missing integration is explicitly not
applicable. Known base and form-gated policy tool names are checked against an
optional allowlist followed by the deny list. Disabled or restricted tools can
be intentional. The 1,800-second generated timeout is shared with the existing
configuration generator; its rendered output is unchanged. Timeout comparison
is guidance, never proof of failure or sufficient duration. An omitted effective
setting and live activation remain unknown.

Raw configuration, unknown names, configured commands/environment values and
parser/OS exception text are not included in new findings. Existing doctor
repository/runtime metadata remains visible under its unchanged contract.
The diagnostic performs no configuration writes, MCP startup, network requests,
validation, task selection or lifecycle transition. The existing Git-access
preflight remains separate. Official filter order and timeout defaults were
checked against the [OpenAI MCP documentation](https://learn.chatgpt.com/docs/extend/mcp?surface=cli).

README, detailed MCP guidance and both troubleshooting languages identify this
as development-source behavior. Stable and published prerelease identities,
strategic direction, operating rules, ADR invariants, report schemas, public
quickstarts and historical evidence need no change. Tests protect these source
boundaries. The current source distribution identity and replay-controller
binding must be synchronized after final packaged-input edits.

## Validation checkpoint

Focused doctor/onboarding tests passed. Later safety tests strengthened real
metadata rejection, identity mismatch, recursion-error normalization and CLI
non-blocking behavior. The real symbolic-link fixture was skipped because this
Windows host lacks creation privilege; it is not presented as exercised proof.
The parent did not repeat unchanged focused tests.

A real source-CLI diagnostic exited zero and identified exactly the expected
local completion-record omission, drift-review omission and low timeout
guidance. A before/after digest confirmed unchanged configuration bytes. The
first observation wrapper used the wrong output decoder for the Windows locale;
it failed to parse CLI output. Repeating that read-only wrapper with explicit
Python UTF-8 mode succeeded. This was a wrapper correction, not a product change
or native-host activation claim.

Complete task-declared validation, scope reconciliation, distinct native
current-Agent advisory review and persistent completion recording are pending
at this checkpoint. Only supported application transitions may write local
evidence; task decisions and old records remain preserved.

## Product context

This connects the existing doctor preflight with the existing Adapter policy
catalog and generated configuration. The immediate observed benefit is a
specific explanation for the current project's filtered tools and timeout
difference, without changing its configuration. Long-term adoption and time
savings remain unknown. The next feature is not yet decided; native form
delivery and pending-request recovery are separate product-review inputs. The
diagnostic supplies evidence for that review while keeping human configuration
and development decisions explicit.

## Final validation and advisory-review checkpoint

This checkpoint supersedes the pending validation and review statements above.
The complete declared baseline command ran 1,169 tests in 282.713 seconds:
exit zero, no failures or errors, seven skips. The distribution-manifest and
artifact-controller command ran 21 tests: exit zero, no failures or errors,
one skip. Real symlink execution remains limited by this Windows account's
privileges; the doctor metadata and identity rejection fixtures passed.

The declared manifest check returned PASS with 188 paths, unchanged path
digest `sha256:23a850bd924f45a8888fcfe7cbc591ed1edfb30c1735810d60a5833bc210fb54`
and current content digest
`sha256:39945ac717e1495a22c8c8c0c8997ed01cd81eebc92ab378818b8307416a64ac`.
The replay controller uses that same identity. The task check returned
3 PASS, 1 WARN, 0 FAIL and 3 ADVISORY; the repository check returned
26 PASS, 2 WARN, 0 FAIL and 4 ADVISORY. These existing contract caveats remain
visible and are not claims of semantic acceptance. `git diff --check` passed.
Baseline-aware completion-scope inspection returned 26 PASS findings and no
failure, including preservation of the pre-existing exclusions.

The parent reviewed source, tests, documentation and distribution bindings.
One Markdown wording mismatch with the documentation regression expectation
was corrected before the full baseline completed. No test was weakened.
Repeated read-only diagnosis returned all six MCP findings and exit zero,
with configuration bytes unchanged. The current tool inventory still exposes
six governance tools and omits completion recording and drift review. This
does not establish the cause of native form non-delivery.

The resolved alignment journey accepted native self-review start request
`asq-144e90461dff0dbcb975c4ea495842aa`, then completed normalized observations
as result `srv-bcdb713631d74b0ff23f1428492e3011`. The parent performed a distinct
advisory pass over requirement, architecture, security, scope, implementation
and product benefit. Its assurance is `separate_pass` current-Agent
self-review, not an independent reviewer or human approval. The native result
is foreground-memory state and does not survive restart; this record retains
only its bounded identity and conclusions. No model/network invocation was
made by the review adapter.

No in-scope source implementation gap was found. Residual unknowns are live
host merges and form rendering, real symlink execution on this host, consumer
adoption and long-term benefit. Human acceptance and handoff remain separate.
Because the native task-completion tool is absent, the admitted supported
CLI lifecycle is used for final snapshot-bound validation and completion
recording after this documentation checkpoint. Its application-generated
evidence and completion records, followed by read-only freshness and handoff
preview, own the actual final outcome; this text does not manufacture those
events or claim human handoff. No configuration, installed runtime, Git,
publication or release action is part of the closeout.
