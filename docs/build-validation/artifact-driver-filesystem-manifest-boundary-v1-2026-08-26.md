# Artifact driver filesystem manifest boundary v1

Date: 2026-08-26

## Result

PASS for the admitted fixture-only repair. No real replay, artifact build,
evidence receipt, or cleanup was executed by this task.

The fixed controller still performs the sole Git-backed manifest admission
before Harness invocation. Its internally bound exact manifest paths, path
count, path digest, and content digest now pass through the private caller
request to the driver. Immediately before short-root allocation, the driver
re-derives distribution inputs and recomputes both identities from repository
files only. It does not import or call the Git-backed checker and does not
require `PATH`.

## Failure semantics

Malformed facts, a path-list difference, or content drift stops as
`manifest_preflight_failed` before short-root allocation. The bounded failure
has zero artifact-action attempts, no recovery root, no evidence write, and no
cleanup claim. Readiness and driver remain single-attempt; no retry was added.

## Validation

- 30 focused controller/caller/driver tests passed with one Windows
  privilege-limited symbolic-link skip.
- 78 combined controller, Harness, caller, readiness, driver, manifest, and
  short-root tests passed with five platform-limited skips.
- The complete supported Python 3.11 suite passed 1102 tests with five skips in
  181.228 seconds.
- The 186-path distribution manifest passed with path identity
  `sha256:cfea3a3632bd75d1f4db51168d257c465987d3fe620fda2449abcd86f42fcd03`
  and content identity
  `sha256:a986da7096e257b90e984084373f923ad460ff4c95f172a08fe4cf2d1fccacaf`.
- Task governance reported `PASS=3 WARN=1 FAIL=0 ADVISORY=3`; repository
  governance reported `PASS=26 WARN=2 FAIL=0 ADVISORY=4`.
- Captured scope reported `PASS=24 PRESERVED=25 FAIL=0 TOTAL=49`; all 55
  user-documentation tests, task JSON, zero-short-root observation, real
  evidence absence, whitespace, and `git diff --check` passed.
- Distinct native current-Agent self-review
  `srv-eb8aa23dc7ebbc322763565fa624c0ca` completed as advisory separate-pass
  review. It retained the unknown real replay and cross-platform outcomes.

## Evidence limits

This proves the repaired static and fixture behavior on the current Windows
host. It does not prove that the next separately admitted real replay will
complete the offline wheel build, durable evidence write, receipt validation,
or gated cleanup. Cross-platform behavior, repeated reliability, interview
response, adoption, time savings, causal benefit, and return on investment
remain unknown.

The native task completion-record tool was not exposed in this session, so no
completion record is claimed.
