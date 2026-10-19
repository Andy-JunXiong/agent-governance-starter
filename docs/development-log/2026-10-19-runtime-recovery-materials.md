# Runtime recovery material preparation - 2026-10-19

## Slice contract

Operating mode: bounded local recovery preparation under admitted task
`p0-runtime-recovery-materials-reprepare-v1`.

The goal is a freshly verified original-environment backup and local wheel
from the unchanged reviewed distribution inputs, plus a reviewable foreground
maintenance handoff. Expected repository changes are this log,
`docs/experiments/runtime-recovery-materials-2026-10-19.md`, `STATUS.md`,
and the separately human-admitted task record. Temporary build and recovery
material stays in one task-owned short root.

Success requires exact 188-input manifest identity, coherent byte-verified
backup, exact wheel module/data parity, preserved live runtime/configuration,
declared checks and a distinct native advisory review. Stop on input drift,
links or reparse entries, moving live files, unexpected package content,
missing pinned artifacts, permission failure, validation failure or required
governance failure. No runtime replacement, process control, persistent
configuration change, source/test edit, Git action, release, deployment or
publication is in scope.

## Human decisions and execution boundary

The human chose recovery preparation in resolved alignment journey
`mcpj-abeaab29bb7a414180ad054e4a89cf55`. The first resolve call supplied the
dialogue-source digest instead of the full decision-prompt digest; the
retryable stale-binding error was corrected using the canonical full prompt,
without altering the human-selected option or skipping the governance call.

Two native task forms returned `declined` with no task decision. The human
reported absent controls and supplied a screenshot showing the decision label
without visible options or submission controls. Static inspection found that
both the installed and source Adapter use `oneOf`, and the local extension
contains support for it. The rendering failure's cause remains unproved; a
protocol `decline` is not represented as deliberate human rejection.

The human explicitly authorized the documented real-terminal admission
fallback for this task. The displayed terminal proposal was reconstructed
from exactly the same normalized fields and matched the latest native
proposal digest
`sha256:885d5d41bfc02c132018b1b382f3e065ceeb7a181554cf2502f23bbeff593a5f`
and task digest
`sha256:914a2872963d3b07d25b89f1c9d11c8064bc4d026c9669214315db4a27bf0ace`.
The human entered exact `ADMIT` in the independent visible terminal. The
Agent did not supply that confirmation. The generated admitted file was
separately validated.

The human then entered exact `REPLACE` in a separate reviewed terminal
start. Current-task state records this task, the same digest, start time
`2026-10-19T06:08:12.102Z` and comparison base
`72175984801fa7a83653f1dc5a8eb8d33d1c4ba7`. The existing source-generated
task-start baseline owns subsequent scope comparison. Terminal fallback is
operator attestation, not cryptographic authentication or native-form success.

Before admission, all 174 existing changed paths were classified: STATUS was
included and 173 paths were excluded. Existing STATUS content and predecessor
records remain preserved. The admitted task retains its original decision;
preparation results do not transition human acceptance.

## Preparation evidence

- The current source manifest passed with 188 inputs and both exact task-bound
  digests. Fresh source staging copied only those declared inputs.
- Created the verified temporary child `agv-fa6298a1`; the longest declared
  projected path was 157 characters within the 240-character limit.
- Exclusively copied all 272 original environment files (4,673,348 bytes),
  pipx metadata within that set, and the separate exposed launcher. Rejected
  links/reparse entries and rechecked the exact original and backup file
  sets/hashes around copying and the complete build.
- Downloaded only the three previously reviewed public-PyPI binary build
  wheels and verified their historical hashes. Build tools were installed
  offline into an isolated temporary environment. Project build used no
  index, dependency installation or build isolation.
- The resulting 543,036-byte local wheel contains exactly 78 expected Python
  modules and 107 shared data files, all byte-matched to staging. Standard
  metadata parsing verifies local-only version `0.3.0rc1` and no runtime
  dependencies; static AST inspection verifies Adapter `1.7.0` and protocol
  `2026-07-28`.
- Final comparison confirms preservation of the original Adapter, complete
  environment, launcher, project configuration and pipx metadata. No live
  environment package installation, process termination/restart, client
  reconnection or cleanup occurred.
- The experiment records normalized hashes, counts, versions, the exact
  temporary basename and the later foreground-maintenance boundaries.
  Private host paths and per-file manifests stay in the task-owned root.

## Sources of truth

STATUS is updated for the fresh preparation and remaining installation
boundary. The September installation snapshot is explicitly historical;
its claim of retained old material is not reused as current evidence.
README, strategic plan, ADRs, guides, public/localized HTML and release
metadata need no change: no product behavior, architecture, strategy or
release identity changed. The task record remains the scope/decision owner.
The new experiment owns the detailed recovery handoff.

## Product-owner context

The project now has freshly verified recovery material and a candidate package
that can be reviewed for a later safe installation. The concrete short-term
benefit is a discoverable recovery locator and current byte-level evidence,
replacing dependence on an unlocated historical temporary directory.
Long-term benefit is unknown. This builds on the exploration-precondition
repair, distribution-input manifest synchronization and prior installation
preparation. The next step within the overall update is review of the exact
foreground disconnect/install/reconnect path; the next product feature is
not yet decided. The material supplies the recovery prerequisites for that
step and supports truthful separation of preparation, installation and
activation across the project. It grants no downstream authority.

## Validation checkpoint

The package and preservation checks above passed. Task-declared repository
validation and native current-Agent advisory review are pending and will be
appended below. Installation and restoration execution remain unproved.

## Task-declared validation result

All six declared commands passed. The focused suite ran 134 tests in 25.619
seconds with three platform-conditioned skips. Task governance reported
`PASS=3 WARN=1 FAIL=0 ADVISORY=3`; repository governance reported
`PASS=26 WARN=2 FAIL=0 ADVISORY=4`. The manifest, task JSON and whitespace
checks also passed. Warnings and advisory findings are retained rather than
represented as deterministic failures.

A separate read-only task-start scope comparison reported five passing
findings, eight byte-preserved predecessor exclusions and no failures;
Git HEAD remained `72175984801fa7a83653f1dc5a8eb8d33d1c4ba7`. Local untracked
AgentGov state is omitted by the baseline's documented inventory boundary,
so eight preserved findings are not a claim about all 173 pre-admission
excluded paths. The original STATUS additions remain in the working tree.
A bounded scan of this task and its two new evidence documents found no
absolute Windows host paths or credential assignments. This is a limited
scan, not proof that arbitrary secrets cannot exist elsewhere.

Validation command results and raw local output remain in the task-owned
temporary root. They are Agent-run observations, not native completion
reconciliation or human acceptance. The native task-completion-record tool
is not exposed in this connection. A distinct native self-review follows.

## Advisory review and preparation closeout

Native current-Agent self-review
`srv-77ba92e6a9aa3bffce8f3c4460d82b78` completed on the resolved recovery
journey after implementation and declared validation. It covered requirement,
scope, implementation, security, data and business observations. It retained
the distinction between verified bytes and an executed restore, terminal
operator attestation and native approval success, and preparation versus
installation/client activation. This is a separate current-Agent pass, not
independent assurance, human acceptance or downstream authorization.

The preparation outcome is complete within its admitted scope. The task
decision remains human-admitted; no semantic-acceptance transition, native
completion reconciliation, session handoff or follow-on task is claimed.
Temporary child `agv-fa6298a1` remains available for later fresh verification.
The final documentation annotations receive a focused documentation check,
scope comparison and byte-preservation recheck before the user handoff; those
results are reported in the handoff without rewriting this historical entry.

The next review is of these materials and the exact foreground maintenance
operation. The original installation is still unfinished, and the native
approval UI issue remains unresolved. Neither needs to be fixed to truthfully
complete this preparation-only task. No later operation starts automatically.

## End-of-day retention checkpoint

The human stopped development for the day. This preparation remains complete
and its original recovery material is retained. The later installation did
not occur; its encoding correction and review blocker are recorded in
`2026-10-19-runtime-foreground-install.md`. The separate documentation/Git
closeout is recorded in `2026-10-19-session-closeout-main-push.md`. No recovery
material was modified or cleaned up by the closeout.
