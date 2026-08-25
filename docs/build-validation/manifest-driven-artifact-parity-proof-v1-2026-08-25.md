# Manifest-driven artifact parity proof v1

Date: 2026-08-25

## Outcome

`STOPPED_AT_EVIDENCE_HANDSHAKE_TRANSPORT_AFTER_ARTIFACT_PARITY`

The one permitted offline wheel build succeeded, and every selected package
and setuptools data-file payload passed exact member and byte-identity gates.
The foreground driver then received closed standard input while waiting for
the evidence-before-cleanup continuation. This is the first orchestration
deviation. The build is not retried and the overall task is not presented as a
full pass.

This record was first written while the one verified short task root and its
wheel still existed. At that point cleanup had not been attempted. The
post-cleanup result is appended only after that first durable write.

## Governed setup

- Alignment journey: `mcpj-307fd958853441f29d111205b412e4ec`.
- Human direction: `adopt_new_center` (`Artifact parity proof`).
- Native proposal: `prp-e8a01255bf104341a8e76ca3b613d934`.
- Admitted task: `p0-manifest-driven-artifact-parity-proof-v1`.
- Task-start baseline:
  `sha256:b097edf3232e23ea7664c4f37461319333622ad8987e06fb86ff8086d5b4be38`.

## Preflight and staging observations

| Observation | Result |
| --- | --- |
| Existing short task roots | 0 |
| Retained setuptools 84.0.0 candidates / digest matches | 1 / 1 |
| Compatible retained backend runtime | setuptools 84.0.0 |
| Short-root helper files / identity matches | 3 / 3 |
| Current manifest check | PASS |
| Manifest paths | 186 |
| Source path digest | `sha256:cfea3a3632bd75d1f4db51168d257c465987d3fe620fda2449abcd86f42fcd03` |
| Source content digest | `sha256:a986da7096e257b90e984084373f923ad460ff4c95f172a08fe4cf2d1fccacaf` |
| Copied inputs / source-stage byte matches | 186 / 186 |
| Staged regular inputs before build | 186 |
| Staged links | 0 |
| Staged path-set and both digest matches | PASS / PASS / PASS |
| Longest projected path / limit | 114 / 240 |

No package or dependency was installed. The retained backend environment was
used as found after its wheel identity and runtime version were checked.

## Single build and payload observations

| Observation | Result |
| --- | --- |
| Offline no-isolation build attempts | 1 |
| Build return code | 0 |
| Wheels emitted | 1 |
| Wheel SHA-256 | `sha256:bba4350f3bff9313eb16273d8cac425a6542e16d9a86183d557cf6ce79aac023` |
| Wheel regular members | 189 |
| Member-inventory SHA-256 | `sha256:15919824a78e07f1d69e2585a76845af009283164ab7b6235a5fe075c5a8a9c2` |
| Expected / actual package payloads | 76 / 76 |
| Missing / extra package payloads | 0 / 0 |
| Expected / actual data payloads | 107 / 107 |
| Missing / extra data payloads | 0 / 0 |
| Payload byte matches / mismatches | 183 / 0 |
| Generated metadata members | 6 |
| Generated-member inventory SHA-256 | `sha256:7afd3c8d423d038df21d83d86adfd9cfd30564122d312b11d871297c88aebf09` |
| Unexpected unmanaged members | 0 |

The member-inventory identities hash the sorted member names with one trailing
newline per name. Package and data payloads are source-selected evidence;
generated distribution metadata remains a separate backend-owned category.
This one local observation does not prove cross-platform or future-setuptools
parity.

## First deviation and retained boundary

After emitting the sanitized parity result, the foreground process attempted
to read the exact evidence-before-cleanup continuation. Its standard input was
already closed, so the process exited with an input-transport error. It did not
attempt a second build, repair, alternate backend, dependency installation, or
cleanup.

Read-only inspection after that exit found exactly one short root and one
wheel. The wheel identity still matched the build observation. The source
stage also contained backend-generated build files at that point; the exact
186-input gate had already been measured before the build.

## Privacy and authority

No absolute host path, source content, raw command output, credential, process
identity, prompt, response, or session identity is retained here. No network,
external Agent, model, consumer form, user configuration, package declaration,
runtime source, checker, helper, test, Git mutation, commit, push, publication,
release, deployment, or full journey was used or authorized.

Artifact payload parity passed for this one build. Overall task acceptance is
not claimed because the evidence-handshake transport deviated. Adoption,
reliability improvement, causal benefit, time savings, and return on investment
remain unknown.

## Cleanup continuation

After the first durable evidence write, bounded cleanup independently required
exactly one direct `agv-<8-hex>` temporary child and exactly one wheel matching
`sha256:bba4350f3bff9313eb16273d8cac425a6542e16d9a86183d557cf6ce79aac023`.
It created a verified short-root value for that exact target, removed 1 of 1
task roots through the existing helper, and found 0 remaining short roots.
Cleanup status is `PASS`. This safe cleanup does not repair the earlier
evidence-handshake transport deviation or change the overall stopped outcome.

## Formal validation and advisory review

All eight task-declared validation commands were invoked and passed:

- the final task-start scope check returned
  `PASS=17 PRESERVED=40 FAIL=0 TOTAL=57`;
- the distribution-input manifest checker passed at 186 paths with both
  canonical digests unchanged;
- the 18 focused manifest and short-root tests passed with 2
  platform-limited skips;
- the complete supported Python 3.11 suite passed all 1102 tests with 5
  platform-limited skips in 168.724 seconds;
- task governance returned `PASS=3 WARN=1 FAIL=0 ADVISORY=3`;
- repository governance returned `PASS=26 WARN=2 FAIL=0 ADVISORY=4`;
- the task JSON parse and `git diff --check` passed; and
- final read-only inspection found zero remaining short task roots.

Distinct native current-Agent advisory review
`srv-b6844e103871c733be7ddc28a3e35ec6` found the selected stopped requirement,
single-build boundary, managed-payload result, metadata separation, scope,
privacy, cleanup, authority denial, and remaining unknowns consistent. It did
not reinterpret the evidence-handshake deviation as acceptance and is not
independent assurance.

The native task completion-record tool is not exposed in this session, so no
completion record is claimed or fabricated. These validation and review facts
do not change the overall stopped outcome or grant Git, publication, release,
deployment, external-write, retry, or follow-on task authority.
