# Evidence-gated short-root cleanup v1

Date: 2026-08-25

## Outcome

`IMPLEMENTED_LOCAL_VALIDATION_PASS`

The repository-internal short-build-root helper now accepts an explicit durable
evidence receipt and revalidates it before one exact-root cleanup. It does not
read stdin or depend on TTY state, so closed input is no longer a cleanup
continuation transport. All admitted validation commands pass.

## Governance and scope

- Native proposal: `prp-2186fb4fb7254ea7acbbc6186c0c4f30`.
- Admitted task: `p0-evidence-gated-short-root-cleanup-v1`.
- Task digest:
  `sha256:07aaf5101066309560f094ba1310f5b1b7fca904861e0ef59e32e27e0fb212e0`.
- Task-start baseline:
  `sha256:5ef376aa1a268c566f0f4ec21dba55972a93896fad03f32920605636ee767731`.

The first capture invocation used the comparison option name `--baseline`
instead of capture's required `--output`. Argument parsing failed with zero
writes. Read-only inspection confirmed the baseline was absent, then the
correct create-only command captured it before implementation. The boundary
begins at that capture and does not prove earlier work.

## Implemented contract

- `create_evidence_receipt` accepts an existing repository, one normalized
  repository-relative evidence path, and one exact lowercase
  `sha256:<64-hex>` identity.
- Every evidence path component must exist without a symbolic link. The final
  target must be a regular file resolving beneath the repository, and its bytes
  must match the supplied identity.
- Receipt creation verifies evidence but does not authorize or perform cleanup.
- `remove_short_build_root_after_evidence` revalidates the path, boundary,
  type, and bytes immediately before delegating exactly once to the existing
  `remove_short_build_root` function.
- Any evidence deviation raises a bounded `BuildRootError` before removal, so
  the task-owned root remains available for diagnosis.
- Normalized receipt and cleanup reports exclude host paths and contents and
  explicitly deny build, retry, network, Git, publication, release,
  deployment, and external-write authority.

## Focused validation

All 12 short-root tests pass. Two symbolic-link tests are skipped because the
current Windows account cannot create the required links. The passing fixtures
cover:

- identical behavior with TTY-reported, redirected, and already-closed input;
- a patched `input` function that would fail the test if called;
- exact one-call delegation on valid evidence;
- missing, absolute, traversal, directory, malformed, mismatched, and changed
  evidence rejection;
- zero cleanup calls and a retained root after evidence revalidation failure;
  and
- privacy-bounded receipt and result representations.

## Boundaries and unknowns

No artifact build, retry, dependency installation, backend substitution,
network request, public CLI or installed-package change, consumer, external
Agent, model, credential, Git mutation, publication, release, deployment, or
external write occurred.

The historical manifest-driven artifact proof remains stopped at its recorded
EOF deviation; this task does not rewrite that fact. A future artifact driver
has not yet consumed the new gate. Cross-platform link behavior, future build
behavior, end-to-end journey behavior, adoption, reliability improvement,
causal benefit, time savings, and return on investment remain unknown.

## Formal validation

- all 12 focused short-root tests pass with 2 platform-limited symbolic-link
  skips;
- all 55 focused documentation tests pass;
- the complete supported Python 3.11 suite passes all 1102 tests with 5
  platform-limited skips in 163.241 seconds;
- task governance returns `PASS=3 WARN=1 FAIL=0 ADVISORY=3`;
- repository governance returns `PASS=26 WARN=2 FAIL=0 ADVISORY=4`;
- task JSON and `git diff --check` pass; and
- final task-start comparison returns
  `PASS=35 PRESERVED=28 FAIL=0 TOTAL=63`.

The exact seven post-capture paths are the three short-root implementation and
test files, this evidence record, `docs/development-automation-contracts.md`,
`STATUS.md`, and the dated development log. No predecessor task, baseline, or
build-validation record changed after capture.

## Distinct current-Agent advisory review

A separate bounded review found the requirement, receipt architecture,
evidence-before-removal call order, static repository containment, link and
file-type rejection, canonical digest validation, changed-evidence
revalidation, failure preservation, normalized privacy, exact changed paths,
and denied authority consistent.

The review also preserves these limits: the existing low-level cleanup helper
remains available to legacy internal callers; a future evidence-order claim
must explicitly use the new gate. Concurrent adversarial replacement of
filesystem components during one verification call is not proven absent, and
future driver integration is untested. Those limits do not contradict the
admitted local, task-controlled evidence contract but remain unknown beyond
it.

The task did not have a resolved alignment journey because the alignment tool
rejected its start contract before task admission; the product owner later
specified the exact repair and separately admitted and took up the resulting
task. No native self-review result is claimed or fabricated. The native task
completion-record tool is not exposed in this session, so no completion record
is claimed. Validation and advisory review grant no retry, follow-on task, Git,
publication, release, deployment, or external-write authority.
