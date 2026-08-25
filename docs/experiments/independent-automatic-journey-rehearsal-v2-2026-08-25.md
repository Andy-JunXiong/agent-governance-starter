# Independent automatic-governance journey rehearsal v2

Date: 2026-08-25

## Outcome

`STOPPED_AT_NON_REPLAYABLE_EXACT_PATHSPEC_PREFLIGHT`

The rehearsal stopped before creating a temporary root, building an artifact,
creating a fixture, or starting an external Agent. The preceding exact replay
record preserves the expected committed-input count and manifest digest, but
does not preserve the 199 repository-relative paths or a deterministic rule
that recreates that exact set.

The current packaging declaration and committed source/data inputs
deterministically identify 188 paths. Their canonical manifest digest is
`3041c6be461ca4b564f92aabdfa7a73c9b9436b30d50e90b9aa5888c4eb26be9`,
not the preceding replay's
`f81a12e42e8fa1739b6af6c708e8b254374fc8e04dcb03af19251ae7e08331c5`.
A cryptographic digest cannot recover the missing 11 path identities.
Guessing paths and attempting the single permitted build would violate the
admitted exact-pathspec and first-deviation boundaries.

## Governed boundary

- Resolved alignment journey:
  `mcpj-9400f2a376c14d18962cd67fc1ea8c04`.
- Selected direction: one bounded independent automatic-governance rehearsal
  v2.
- Native proposal: `prp-dbf35246e84f4b40af0911160ac300a4`.
- Admitted task: `p0-independent-automatic-journey-rehearsal-v2`.
- Task-start baseline:
  `sha256:401b7cd6aa6ebeb59817ca306cbb0f0fe2441c0479cc950dc0a2998666de90cc`.

## Preflight observations

| Observation | Result |
| --- | --- |
| Starter `HEAD` versus preceding replay | matched |
| Preceding committed-input evidence | count 199 plus digest; exact path list absent |
| Deterministically reconstructable committed inputs | 188 |
| Reconstructed manifest versus preceding digest | mismatch |
| Expected current overlays | exact set of 7 |
| Current overlay manifest | matched preceding digest `861b869c153f11e35b619085a63e43b59984df0f319a8bf988e69ae4f5695122` |
| Retained build backend candidates / digest matches | 1 / 1 |
| Short-root helper files matching preceding identities | 3 / 3 |
| Existing task-owned short roots | 0 |
| External Agent client | available |
| Task roots created | 0 |
| Backend installs / wheel builds / runtime installs | 0 / 0 / 0 |
| Synthetic fixture repositories / commits | 0 / 0 |
| External Agent sessions / model turns | 0 / 0 |
| Native consumer forms / tool calls | 0 / 0 |

The seven-overlay result shows that current dirty distribution deltas remain
reproducible. It does not identify the missing committed inputs and therefore
cannot clear the committed-source gate.

## State, privacy, and authority

The project-local Codex configuration identity and absent project-local trust
record were observed by digest/existence only. Credential values and stores
were not read. Ambient processes were grouped only by normalized process name
for attribution readiness and were neither identified individually nor
controlled.

No source, package declaration, helper, test, consumer, user configuration,
trust state, credential, existing environment, or existing repository was
modified by the rehearsal. No temporary root required cleanup. No network
request, external Agent turn, model call, human consumer form, Starter Git
operation, commit, push, publication, release, deployment, or external write
occurred.

This result establishes only a local durable-evidence replayability defect.
It provides no evidence about automatic proposal selection, human admission,
separate take-up, implementation, validation, completion recording,
self-review, Monitor visibility, handoff quality, adoption, reliability,
causal benefit, or return on investment.

## Validation

The focused short-root suite passes all 7 tests with 1 platform-limited
symbolic-link skip. The focused documentation suite passes all 55 tests. The
complete supported Python 3.11 suite passes all 1102 tests with 5
platform-limited skips in 163.618 seconds. Task governance is
`PASS=3 WARN=1 FAIL=0 ADVISORY=3`; repository governance is
`PASS=26 WARN=2 FAIL=0 ADVISORY=4`. Task JSON and `git diff --check` pass.
The final task-start comparison is
`PASS=13 PRESERVED=34 FAIL=0 TOTAL=47`; the bounded added-evidence privacy scan
and final short-root count are both zero.

Three admitted validation commands have invalid current CLI syntax:

- the baseline command omits `--task` and `--baseline`;
- the task-governance command uses unsupported `check --task ... --format`;
- the repository-governance command uses unsupported `check --format`.

All three exact admitted invocations were run and failed at argument parsing
without repository writes. Their repository-standard equivalents passed, but
an equivalent does not make the admitted commands successful. The task record
was not changed to hide the defects. Consequently the evidence closeout is
complete and bounded, while the acceptance signal requiring every admitted
validation command to succeed remains unsatisfied.

Distinct native current-Agent advisory review
`srv-b672422d039e26b8dd8b604abf970621` found the first-deviation stop, omitted
path-level replay contract, bounded zero-attempt implementation, scope
preservation, privacy and authority boundaries, command defects, and retained
unknowns consistent. It explicitly did not treat the selected end-to-end
outcome or all-command acceptance signal as satisfied. This is a separate
self-review pass, not independent assurance. The native task completion-record
tool is not exposed in this session, so no native completion record is claimed
or fabricated.
