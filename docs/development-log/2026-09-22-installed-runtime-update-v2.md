# Development log - 2026-09-22 - installed runtime update v2

## Goal, authority and stop conditions

Update the existing isolated local AgentGov development installation from
the exact reviewed package, preserving configuration and tool exposure. The
human selected `adopt_new_center` in alignment journey
`mcpj-0c29d30bd80a437e87705373c7b20a91`. Native proposal
`prp-9869c0ba88f74da3a081f70b18ced1c6` admitted
`governance/tasks/p0-installed-runtime-update-v2.json` with task digest
`sha256:91b61aabd19e1952aa12791466747d158124d267b24ed0d92f57b6ee87ef4933`.
The human then separately supplied exact `REPLACE`; start event
`evt-08e4761aa0554cffba0776a4044c2faa` captured the predecessor scope baseline.

The bounded change includes STATUS, this log, the normalized experiment and
the exact task record. Source, tests, scripts, manifest, configuration and
predecessor records are excluded. Before the v2 form, all 176 existing changed
paths were classified: one included and 175 excluded. No unrelated changes
were staged or discarded.

Success requires byte-verified inputs and recovery material, safe replacement
of only the existing environment, installed payload and fresh-process checks,
and an explicit client activation boundary. Stop if source/backup/target
identity changes, processes still use the environment, host permissions fail,
or a required governance or validation operation cannot be completed safely.
No source behavior, tool allowlist, release identity, Git, publication,
deployment, consumer repository or external model-session change is included.

## Preparation and observed corrections

- The unused v1 proposal named an internal manifest module instead of the
  executable CLI package. This was found before take-up; v2 corrects the
  command and preserves the original record. The actual manifest command
  passed with 188 paths and the exact task-bound path/content digests.
- The first start invocation incorrectly combined execution with JSON output,
  which supports dry-run only. It exited before writing; the ordinary terminal
  invocation then accepted the human's exact `REPLACE` and started v2.
- Created one verified direct child of the system temporary directory, with
  projected path length 142 under the declared 240-character limit. No link or
  reparse point was accepted in the installation backup inputs.
- Copied and hash-verified all 272 files (4,673,348 bytes) of the old isolated
  environment and the separate exposed launcher. Rechecked the live file set,
  source inputs, launcher and configuration after backup and build.
- Downloaded only the same pinned setuptools, wheel and packaging binary
  artifacts used in the earlier successful isolated verification, checking
  their exact recorded hashes. Subprocess environment excluded user pip
  configuration and credentialed indexes. Project build used no index,
  dependency resolution or build isolation.
- The 543,036-byte local-only wheel contains exactly 78 expected Python
  modules and 107 shared data payloads, all matching staged/source bytes.
  Its archive hash differs from the earlier build; payload identity, rather
  than an unchanged archive hash, establishes the reviewed source binding.
- A temporary metadata check assumed LF delimiters and rejected CRLF wheel
  metadata. A standard email metadata parser confirmed version `0.3.0rc1`
  and no runtime dependencies; all payload checks were retained. No product
  code, tests or task requirement was weakened or edited for this correction.
- The initial narrow executable-path observation found one target process.
  The subsequent check also included the exposed launcher and runtime paths
  in Python/AgentGov process arguments: three matching processes remained,
  all with governance-MCP arguments. These may be a launcher chain; the count
  does not establish three independent client connections. No process-control
  operation was attempted.

## Pending-state handoff

State is `PREPARED_AWAITING_QUIESCENCE`. Installation has not run. The verified
wheel, exact original backup, private per-file hashes and recovery instructions
remain in the task-owned temporary root. Its absolute locator stays outside
repository evidence. No background installer or delayed mutation exists.

After the human disconnects the old runtime, observe the process boundary
again and revalidate all identities before any installation. The existing
environment write still requires the host permission boundary. If actual
installation or verification fails, restore only the verified original
snapshot at a safe no-process boundary; if that cannot be proved safe, retain
recovery material and stop. Client reconnection and final cleanup are pending.

STATUS owns this current pending state. README, user guides, release metadata,
public/localized HTML, architecture contracts and strategic plans require no
change at this checkpoint: no installed capability, public behavior, release
or strategic decision has changed. Historical installation evidence remains
historical. The previous unstaffed comprehension observation remains stopped.

## Product context

This preparation makes the reviewed package and byte-verified recovery material
available for the existing installed workflow. It builds on the exploration
precondition repair, isolated package verification and synchronized input
manifest. The observed short-term benefit is exact input and recovery evidence;
the repaired behavior is not yet available to the current client. Long-term
benefit is unknown. The next step within this same requirement is safe
installation and fresh-connection verification; the next feature is not yet
decided. Keeping source, package and current-client claims separate supports
the project's evidence-based governance objective without claiming acceptance.

## Validation and advisory review

Preparation validation and a distinct native review are recorded below when
executed. They do not mark this unfinished installation requirement complete.

- All six task-declared commands passed in
  `.agentgov/evidence/evd-f031e4a46eb946bc91d2d46e46e36e91.json`, with no
  validation-time mutations. The focused suite ran 134 tests in 25.837 seconds
  with three platform-conditioned skips. Task governance reported three
  passes, one warning and three advisories; repository governance reported
  26 passes, two warnings and four advisories. Neither reported a failure.
- A distinct read-only baseline comparison found five passing findings and
  eighteen preserved predecessor exclusions, no scope failures and unchanged
  Git head. A separate hash pass reconfirmed original runtime, backup,
  launcher, configuration and source-input preservation.
- Native current-Agent review `srv-61c6b9d3b90b48a7afb94646312a46ae` completed
  on the original resolved alignment connection. It retained the incomplete
  installation outcome, byte-level recovery evidence and unchanged scope.
  Actual restoration, installed-process verification and client activation
  remain unknown. It is advisory and a separate pass, not independent review
  or human acceptance.
- Only the three admitted status/evidence documents changed after take-up.
  Their retained data consists of normalized counts, hashes, versions,
  repository-relative evidence and bounded observations; private host paths
  and raw process or protocol payloads were not added.
- These final documentation annotations are validated once more with all
  six declared commands. The final evidence identity is reported in the
  handoff without editing these files again. Only validation evidence is
  recorded: completion reconciliation is intentionally not requested while
  the installation requirement remains incomplete.

## End-of-day suspension and separately authorized Git handoff

The human requested stopping for the day, updating the related documentation,
and committing and pushing today's work to GitHub main. This suspension note
uses the current admitted task's existing STATUS/log/experiment scope; it
changes no requirement, installation or task decision. Git authority comes
from the separate explicit human request and the repository Git procedure,
not from this installation task or its validation evidence.

The final preparation validation record before this suspension was
`evd-a569ae4265e34ea5b51ac5c3a38d839f`: six commands passed without mutation,
including 134 focused tests with three platform skips. Today's earlier source
repair also has passing full-suite evidence
`evd-232562b487874546b675177e4a417232`, and the manifest/controller repair has
passing evidence `evd-7bb9c016652a47b89fd597779e8e5495`. These are distinct
historical validations, not new end-of-day runs.

The reviewed commit scope is today's exploration precondition source/tests
and guide, manifest/controller synchronization and regression tests, four
dated development records, two normalized experiment records, five exact task
records (including the unused, explicitly superseded installation v1), and
today's STATUS additions. Earlier uncommitted observation sections in STATUS
are preserved in the worktree but excluded from the staged version together
with their three related files. Local `.agentgov` state, `.codex` configuration,
temporary build tools, wheel and recovery backup are not committed.

Origin was fetched before staging; local main and origin/main initially
matched. The exact staged tree is reviewed and checked before one ordinary
commit and an explicit non-force push to origin main. The resulting commit
identity and remote confirmation are reported in the final handoff, not
preclaimed here. No pull request, release, deployment or force-push is part of
this request.

The existing native advisory review remains the review of prepared installation
evidence. A separate supplemental current-Agent pass checks this fully
specified suspension note, selected Git scope, private-data exclusions and
truthful incomplete state; it does not claim another native review run or
installation acceptance. Final documentation validation and staged-tree
verification are reported with the handoff.

The user can now recover today's reasoning and tested source from the reviewed
repository history while the actual installation remains pending. This builds
on the repair, isolated verification and manifest synchronization; the concrete
short-term benefit is a reviewable recovery point. Long-term benefit is unknown.
The next step remains the same installation requirement after fresh task,
source, backup, Git and process checks; the next feature is not yet decided.
Pre-commit scope baselines and completion evidence remain historical and must
not be silently reused as fresh evidence after the Git transition. Retained
temporary materials must still exist and match their recorded hashes; if they
do not, stop before installation and report the missing recovery boundary.
