# Windows short build-root contract v1

Date: 2026-08-25

## Outcome

`STOPPED_AFTER_WHEEL_BUILD_AT_INSTALLED_SHARED_TEMPLATE_CHECK`

The repository-internal short-root contract is implemented and its one allowed
exact-current-source validation produced a wheel. The ordered validation then
stopped at the combined installed shared-template presence-and-byte-digest
gate. The temporary root was removed, so the available evidence cannot
distinguish a wrong installed-location assumption from a missing file or a
byte mismatch. No second build, alternate path, artifact substitution, or
download was used.

This outcome clears the specific v1 wheel-build gate but does not satisfy every
acceptance signal of this repair task and does not authorize independent
rehearsal v2.

## Governed setup

- Alignment journey: `mcpj-85e00f9b9e04452fae958be7ecd5d788`.
- Human direction: `split_new_requirement` (`Repair then rehearse`).
- Proposal: `prp-9e8bbf31c5a94d8aa0709e0a93602951`.
- Admitted task: `p0-windows-short-build-root-contract-v1`.
- Task-start baseline:
  `sha256:af8055546857e4f557adb01f4ca181f8886385156ab6717f82ffe20a4ff0abe0`.
- The retained `setuptools 84.0.0` wheel was the sole local candidate and
  matched expected SHA-256
  `51A52592B3B99E102B609654876BD65F19F999935166D1352678931132B0C670`.

## Implemented contract

The internal `scripts.short_build_root` helper:

- always derives its write boundary from the operating-system temporary
  directory; callers cannot select another base;
- allocates one exclusive direct child named `agv-` plus eight lowercase hex
  characters;
- limits the root path to 72 characters and projected paths to 240 characters,
  below the 259-character non-extended Windows boundary;
- requires at least one normalized portable relative projected path and rejects
  absolute, driven, traversal, backslash, whitespace, control-character, and
  over-budget inputs before creating a directory;
- exposes neither the temporary base nor the allocated absolute path in its
  object representation or normalized report;
- cleans only an existing, non-symbolic-link, exact direct child that still
  matches the original operating-system temporary boundary; and
- grants no artifact selection, network, Git, publication, release,
  deployment, or external-write authority.

Focused tests exercise allocation, uniqueness, budgeting, unsafe paths,
privacy-safe representation, collision exhaustion, exact cleanup, forged
cleanup rejection, missing-target rejection, and symbolic-link rejection. The
symbolic-link case is platform-limited when Windows does not grant link
creation permission.

## One-shot artifact validation

The validation driver itself was passed to Python without a repository file.
Its first invocation was rejected by Python parsing after PowerShell removed
embedded quotes. That invocation created zero temporary roots and made zero
build attempts. Encoding the unchanged driver before invocation corrected the
transport only; the real artifact build remained a single attempt.

| Observation | Recorded result |
| --- | --- |
| Exact current distribution deltas | 7 files, exact expected set |
| Binary-safe current overlays | 7 matched source/stage byte digests |
| Committed archive regular files | 199 |
| Task-owned short roots created | 1 |
| Projected formerly failing target | 207 characters |
| v1 measured failing target | 264 characters |
| Wheel-build attempts | 1 |
| Wheel-build retries | 0 |
| Wheels produced | 1 |
| Wheel members | 188 |
| Wheel SHA-256 | `sha256:9f10b4a55eb45912e3e5ee3a39a968a2ba8cb8da534173f1c73d248d586f72fd` |
| Wheel member-inventory SHA-256 | `sha256:6ca19e08b0658442eab2616ec25f260265ddfcc8fed734e50a0e47f54fbd05da` |
| Installed runtime version gate | passed before the later template gate |
| Installed shared-template gate | stopped: absence versus digest mismatch unknown |
| Network calls | 0 |
| External Codex sessions | 0 |
| External model turns | 0 |
| Native consumer forms | 0 |
| Task-owned short roots removed | 1 |

The current source wheel and runtime were inside the removed root and are not
retained. The ordered driver reached the template gate only after the offline
runtime installation and installed-version match; that control-flow fact does
not establish the missing template subcondition.

## Privacy, cleanup, and authority

Persisted evidence excludes absolute paths, process and parent identifiers,
raw command output, archive content, source content, patches, credentials,
prompts, responses, transcripts, and host session identifiers. The sole local
build-backend digest is retained because it is an artifact identity rather than
a credential.

The one short root was removed through the exact helper ownership boundary. No
task-owned asynchronous process was started. No Starter or consumer Git
operation, commit, push, publication, release, deployment, credential change,
external write, Codex session, or model request was performed or authorized.

## Remaining boundary

The short-root allocator is now backed by focused tests and one real successful
wheel build, reducing the projected failing target from 264 to 207 characters.
Whether installed data was checked at the wrong location, absent, or byte-
different remains unknown. A later separately admitted diagnostic should
resolve that exact shared-data question without rebuilding before product
review decides whether to admit independent rehearsal v2. This record grants
no such authority.

## Closeout validation

All 7 focused short-root tests pass with 1 platform-limited symbolic-link skip.
The complete supported Python 3.11 product suite passes all 1102 tests with 5
platform-limited skips in 160.340 seconds. Task governance is
`PASS=3 WARN=1 FAIL=0 ADVISORY=3`; repository governance is
`PASS=26 WARN=2 FAIL=0 ADVISORY=4`. The task JSON parses and
`git diff --check` passes.

The final task-start comparison is
`PASS=17 PRESERVED=22 FAIL=0 TOTAL=39`: all post-start changes are inside the
admitted scope and every captured excluded path remains byte-identical. The
bounded allowed-path privacy scan reports zero findings.

Distinct native current-Agent advisory review
`srv-ff4abd2557c7c69c7d286775516c201d` found the partial-requirement
attribution, internal-tool architecture, scope, implementation and test seam,
cleanup security, privacy, unknowns, and denied-authority boundaries
consistent. It explicitly retained the installed shared-template signal as
unsatisfied. This is a separate current-Agent pass, not independent assurance.
No completion record is claimed because the full task acceptance contract was
not satisfied and the native completion-record tool is not exposed in this
session.
