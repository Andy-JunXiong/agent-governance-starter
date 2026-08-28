# Artifact invocation transport readiness gate v1

Date: 2026-08-26
Task: `p0-artifact-invocation-transport-readiness-gate-v1`
Evidence kind: deterministic fixture-only implementation validation

## Boundary

The human selected a deterministic pre-action transport-readiness direction
through resolved alignment journey `mcpj-926e428f144e49d09b57d9921173384d`,
admitted proposal `prp-0b90697c46ab4f17b0625fea820a01f2`, and separately
instructed task take-up. Create-only baseline
`sha256:320f314ef368841d045f94ee2dbe1db65dedb6c38502d3cee25b7a6784cda36f`
was captured before implementation.

This validation uses fixtures only. It does not supply caller source or
payload bytes, run the real fixed capability probe, invoke the artifact
driver, allocate or clean a short root, run an artifact action or build,
install dependencies, use a network, retry, or perform Git or downstream
operations.

## Implemented contract

The dependency-free `scripts.artifact_invocation_readiness` package has no
`__main__.py` or installed/public CLI surface. Its frozen request accepts only
normalized encoding metadata, private launcher and backend-wheel references,
expected versions and wheel digest, and an exact all-false authority mapping.
It contains no payload, source, command, or argument field.

The checker validates every non-process precondition before the one permitted
process attempt. Private launcher and backend paths must be existing regular
non-link files, the `.whl` bytes must match the expected digest, and the
temporary directory must contain zero exact task roots. The observer treats
both the current allocator's 8-lowercase-hex suffix and the admitted future
16-lowercase-hex assumption as task-owned. This is a conservative transition
check, not a change to the existing allocator.

After those gates, the only callable process path uses the selected launcher,
isolated Python mode, a module-owned fixed script, closed stdin, captured
output, a bounded environment, and a ten-second timeout. It exposes no caller
command or source. The parsed observation must have the exact normalized
version and capability schema, match expected Python/pip/setuptools versions,
and report callable `build_wheel` plus an available vendored wheel. A second
zero-root observation is required before PASS.

Success and failure reports exclude host paths, content, stdout, stderr,
environment values, and raw exceptions. Each deviation returns one bounded
reason code and records zero or one probe attempt. The receipt denies all
execution and downstream authority, is point-in-time evidence only, and is
not consumed or enforced by the unchanged artifact driver.

## Validation

- Focused readiness, driver, and short-root suite: 37 tests passed; 4
  Windows privilege-limited symbolic-link tests skipped.
- Remaining formal checks: pending at the time of this immutable record's
  initial write; final results are owned by `STATUS.md` and the dated
  development log.

## Known limits

- Launcher/backend replacement and a root appearing after observation remain
  point-in-time filesystem race limits.
- Cross-platform execution of the real fixed probe is not established by this
  fixture-only task.
- The existing artifact driver does not consume the receipt. Persistence and
  mandatory caller integration require separate product decisions and task
  authority.
- Adoption, failure reduction, time savings, causal benefit, and return on
  investment are unknown.
