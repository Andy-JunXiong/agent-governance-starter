# Independent automatic-governance journey rehearsal v3

Date: 2026-08-31

## Outcome

`STOPPED_AT_DISTRIBUTION_MANIFEST_PREFLIGHT`

The rehearsal stopped at its first deterministic deviation, before any build,
installation, synthetic repository, or external Codex session. The committed
distribution manifest declares 186 paths, while fresh independent derivation
from exact current source returns 187 paths. The additional derived path is
`src/agentgov/task_start_scope_baseline.py`.

The manifest check also reports different path and content identities. The
declared path identity is
`sha256:cfea3a3632bd75d1f4db51168d257c465987d3fe620fda2449abcd86f42fcd03`;
the derived path identity is
`sha256:79839fec9be5dfb8bb30c41e74a0d8a9a6a11b3587001af6395f7f1b7c506e9a`.
The declared content identity is
`sha256:b00be073afa541c3130cc620c84bd2bba2afa7b48ec4e70a4ff74998bc7fb8d9`;
the derived content identity is
`sha256:a695fb5afcaadcc2f3382a7a878d4e182070539d61b5e39a0ea663b00874a96c`.

## Governed boundary

- Resolved alignment journey:
  `mcpj-e3a056c978254d30a602c2885f5c5edc`.
- Human-selected direction: resume the automatic journey.
- Native proposal: `prp-d8a070579b444e4cae5d17bf674b57f5`.
- Admitted task: `p0-independent-automatic-journey-rehearsal-v3`.
- Task-start baseline:
  `sha256:9ce1affec3832e9af4810d51d19b96c3a0d65c13fadbd5f7c1db296c2963f305`.
- Human task-start confirmation: exact `START` after the stale `REPLACE`
  preview was cancelled without writes.

The current-source start path created the immutable baseline before the
session pointer and start event. Fresh comparison preserves all three
pre-existing untracked exclusions byte-for-byte and reports no scope failure.

## First-deviation accounting

| Observation | Result |
| --- | --- |
| Gate | current distribution manifest consistency |
| Declared / derived paths | 186 / 187 |
| Missing manifest entries | 1 |
| Tracked distribution deltas | 0 |
| Untracked distribution overlays | 0 |
| Offline builds / wheels | 0 / 0 |
| Isolated runtime installs | 0 |
| Synthetic repositories / commits | 0 / 0 |
| External Codex sessions / requests | 0 / 0 |
| Native consumer forms / tool calls | 0 / 0 |
| Retries / repairs / substitutions | 0 / 0 / 0 |

This is a deterministic artifact-input contract mismatch, not an advisory
judgment about the feature. The newly delivered task-start baseline module is
present in exact current source but absent from the durable distribution
manifest. The v3 task excludes that manifest and all product source, so it
cannot repair the mismatch or attempt a build against a guessed input set.

## State, privacy, and authority

No task-owned temporary root was created, so no cleanup was needed. No source,
manifest, script, test, configuration, credential, trust state, process, or
existing consumer was changed. The three pre-existing untracked paths remain
excluded and byte-identical.

No dependency download, network request, build, installation, synthetic Git
commit, external Agent or model call, native consumer form, Git operation in
this repository, publication, release, or deployment occurred. Stored
evidence contains no raw prompt, response, transcript, validation output,
credential, host path, process identifier, or private reasoning.

## Validation

The task-start comparison and manifest preflight were run with the available
Python 3.12 runtime. The baseline comparison passed with three preserved
excluded paths, one unchanged included task record, and all three post-start
documentation deltas in scope. The focused documentation suite passed all 63
tests. The complete suite passed all 1,134 tests with six platform-limited
skips. Task governance reported `PASS=3 WARN=1 FAIL=0 ADVISORY=3`; repository
governance reported `PASS=26 WARN=2 FAIL=0 ADVISORY=4`. Task JSON and
`git diff --check` passed.

## Interpretation

The run establishes that the automatic journey is presently blocked before
artifact construction by stale distribution-input metadata. It provides no
new evidence about build success, installed behavior, automatic tool
selection, proposal review, task take-up, implementation, validation,
completion, self-review, Monitor visibility, handoff, adoption, repeatability,
causal benefit, time savings, or return on investment.

A separate product review may decide whether to admit a narrow distribution
manifest synchronization task. This record grants no authority to update the
manifest, retry v3, create v4, or perform Git, publication, release, deployment,
or external actions.

Distinct current-Agent advisory review
`srv-88c41660caae11d2bf57ded4ddbd33d7` found the first-deviation stop,
distribution-contract ownership, admitted scope, preserved exclusions,
privacy boundary, and denied authority consistent. It retained downstream
journey behavior, independent privacy assurance, adoption, reliability, time
savings, causal benefit, and return on investment as unknown. This is
self-review, not independent assurance or human result acceptance.
