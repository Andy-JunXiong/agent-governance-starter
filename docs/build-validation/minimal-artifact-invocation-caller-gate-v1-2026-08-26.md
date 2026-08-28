# Minimal artifact invocation caller gate v1

Date: 2026-08-26
Task: `p0-minimal-artifact-invocation-caller-gate-v1`
Evidence kind: deterministic fixture-only implementation validation

## Boundary

The product owner selected the minimal caller direction through resolved
alignment journey `mcpj-af1b00ba2376472890d521fe1cfb1f4a`, admitted proposal
`prp-cfaca43bb260472687c1496e4a3eab1f`, and separately instructed task
take-up. Create-only baseline
`sha256:2bffc34f5073cff4df7571421b5710deb05644909d61e383a84ee563f9c25d23`
was captured before implementation.

This record is fixture-only. It does not run a real readiness probe, artifact
driver, root allocation or cleanup, artifact action or build, installation,
network, retry, repair, receipt persistence, Git operation, or downstream
journey.

## Implemented contract

The dependency-free `scripts.artifact_invocation_caller` package has no
`__main__.py`, installed surface, public CLI, generic command runner, receipt
store, backend selection, or build implementation. One frozen private request
composes the existing `InvocationTransportRequest` and unchanged artifact
driver arguments.

The wrapper calls the readiness checker once and validates the complete PASS
type and normalized report before the driver is reachable. It checks contract
and schema identities, normalized encoding and backend facts, matching
versions and required capabilities, `probe_attempts=1`, zero short roots,
no-input/no-TTY facts, and the exact all-false authority request. An upstream
deviation or exception, invalid type, malformed report, non-PASS state, or
authority drift stops in the readiness phase with zero driver calls.

After a validated fresh PASS, the wrapper calls the unchanged driver once with
the exact original arguments and action. It neither writes nor forwards the
readiness receipt. A driver deviation, exception, malformed type, report
drift, or authority drift stops after that one driver call. The wrapper
privately retains an exact `ArtifactReplayDriverError` so any existing private
root recovery handle is not lost, while public reports exclude it.

A combined success serializes the already validated upstream reports into a
stable in-memory result. It reports one readiness and one driver attempt,
no-input/no-TTY facts, and denied downstream authority. Host paths, caller
values, action representations, source, payloads, raw exceptions, and private
recovery state are excluded.

## Validation

- Focused caller, readiness, driver, and short-root suite: 46 tests passed; 4
  Windows privilege-limited symbolic-link tests skipped.
- Remaining formal checks: pending at this record's initial write; final
  results are owned by `STATUS.md` and the dated development log.

## Known limits

- The receipt is point-in-time and remains subject to the checker's documented
  concurrent file/root replacement limits.
- This fixture-only slice does not establish real composed or cross-platform
  execution behavior.
- Receipt persistence, driver-level receipt enforcement, and pre-capture
  launcher-output quotas remain separate decisions.
- Adoption, failure reduction, time savings, causal benefit, and return on
  investment are unknown.
