# Independent automatic user-journey rehearsal v1

Date: 2026-08-25

## Outcome

`STOPPED_AT_WHEEL_BUILD_PATH_LENGTH_BEFORE_FIXTURE_AND_MODEL`

The rehearsal stopped at its first observed deviation. The exact-current-source
wheel build attempted to copy a packaged template to a target path whose
measured length was 264 characters. The build returned a missing-directory
error at that target. This result is consistent with the legacy Windows path-
length boundary, but the available evidence does not prove that boundary was
the sole cause.

The admitted protocol required a stop without repair, substitution, or retry.
No shorter root, previously built artifact, source change, or second build was
used.

## Governed setup

- Alignment journey: `mcpj-faf96c23807f4bc0bc830544c1bb0dd4`.
- Admitted task: `p0-independent-automatic-journey-rehearsal-v1`.
- Proposal: `prp-de669814cffd463286b413e50387545f`.
- Task-start baseline:
  `sha256:e4adc21f159f708e18b175e06c2e97d2499172908ba49cd31e0ba3714c75c6ea`.
- Task-owned temporary roots created: 1.
- Committed distribution inputs were staged by binary-safe Git archive.
- Exact current distribution overlays: 7; all source/stage byte digests
  matched before build.
- The retained local build backend matched its expected byte digest and was
  installed offline into one fresh Python 3.11 build environment.
- Wheel build attempts: 1.
- Build retries, repairs, substitutions, or source changes: 0.

## First deviation

| Observation | Recorded result |
| --- | --- |
| Gate | exact-current-source wheel build |
| Normalized reason | `wheel_build_target_path_length_boundary` |
| Measured failing target-path length | 264 characters |
| Wheel artifacts produced | 0 |
| Fresh installed runtime environments produced | 0 |
| Synthetic fixture repositories created | 0 |
| Fixture Git baseline commits | 0 |
| External Codex sessions | 0 |
| External model requests or turns | 0 |
| Native consumer forms | 0 |
| Consumer AgentGov tool calls | 0 |
| Model-session retries | 0 |

Because the fixture gate was never reached, this record contains no evidence
about automatic proposal, human admission, task take-up, edit, validation,
completion, self-review, Monitor card, or handoff behavior. It does not satisfy
the independent automatic-experience gate and is not a fresh uncoached human
pilot.

## Cleanup and privacy

The one task-owned temporary root was resolved inside the operating-system
temporary boundary and removed. No task-owned asynchronous process was
started, so none remained to stop. The normalized ambient process preflight
was `ready`; ambient processes were observed only for attribution and were not
controlled.

This evidence omits absolute paths, process and parent identifiers, raw command
output, source contents, patches, model prompts or responses, human-form
content, credentials, tokens, and session identifiers. No fixture or model
transcript existed to retain.

## Authority and interpretation

The single local build attempt and temporary preparation were inside the
admitted rehearsal. No Starter source repair, Starter Git operation, consumer
Git operation, commit, push, publication, release, deployment, credential
change, or external write was performed or authorized.

The result establishes only that this admitted run reached and failed the
wheel-build gate, then stopped and cleaned up as specified. Whether a shorter
build root would succeed, whether the automatic journey works after build, and
whether users find it understandable remain unknown. A separately admitted
review may decide whether to harden the Windows build-root contract and run a
new rehearsal; this record grants no such authority.

## Closeout validation

The first focused documentation run found one traceability gap: the development
log did not name this record's stable path. That link was added without changing
the rehearsal outcome or retrying the build. The corrected focused run passes
all 55 tests. The complete supported Python 3.11 suite passes all 1102 tests
with 5 platform-limited skips in 157.801 seconds.

Task governance is `PASS=3 WARN=1 FAIL=0 ADVISORY=3`; repository governance is
`PASS=26 WARN=2 FAIL=0 ADVISORY=4`. The task JSON parses, the bounded persisted-
evidence privacy scan reports zero findings, and `git diff --check` passes. The
final task-start comparison is `PASS=15 PRESERVED=20 FAIL=0 TOTAL=35`.

Distinct native current-Agent advisory review
`srv-f7ba5d19b6d2810efe76f09515f8af79` found the first-deviation requirement,
artifact-preparation separation, task scope, evidence implementation, cleanup,
privacy, unknowns, and denied authority consistent. It is a separate current-
Agent pass, not independent assurance. The native task completion-record tool
is not exposed in this session, so no completion record is claimed or
fabricated.
