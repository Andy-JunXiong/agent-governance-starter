# Artifact replay interview walkthrough

Use this as a three-to-five-minute engineering story. It describes one bounded
Windows replay from current development source; it is not a stable-package,
cross-platform, or repeated-reliability claim.

Present it in the browser: [English HTML](artifact-replay-interview.html) or
[简体中文 HTML](artifact-replay-interview.zh-CN.html).

## Thirty-second answer

I built a fail-closed artifact replay chain for an AI-agent governance project.
The hard part was not invoking a build: it was proving that the inputs admitted
outside a restricted worker were the same inputs used inside it, allowing only
one attempt, persisting privacy-bounded evidence, and deleting the temporary
build root only after the evidence receipt had been revalidated. The final
no-retry replay invoked the controller once, completed one dry and one actual
attempt, built one wheel from 186 byte-matched inputs, verified its contents,
wrote durable evidence, revalidated the receipt, and left zero short roots.

## Three-to-five-minute talk track

### 1. Problem - 45 seconds

A successful build alone would not close the governance question. I needed to
show which repository inputs were admitted, prevent silent retry or dependency
fallback, avoid leaking paths and raw subprocess output, and make cleanup
conditional on a durable evidence receipt. If the chain drifted before the
action, it had to fail without allocating a recovery root or claiming cleanup.

### 2. Architecture - 60 seconds

```text
fixed controller
  -> Git-backed manifest admission
  -> bounded Harness: one dry attempt, then at most one actual attempt
  -> immutable source-identity bridge and readiness gate
  -> caller
  -> driver filesystem revalidation
  -> one offline wheel action
  -> exclusive evidence write and receipt revalidation
  -> evidence-gated short-root cleanup
```

The controller owns the outer Git observation and binds the exact manifest
path list, count, path digest, and content digest. The caller forwards those
facts privately. Immediately before allocating the short build root, the
driver re-derives the inputs from regular repository files and recomputes both
digests. Only normalized status, identities, phases, reasons, and attempt counts
cross the public boundary.

### 3. Two boundary failures and repairs - 60 seconds

The first real attempt stopped during the dry worker. The worker deliberately
had no `PATH`, while the manifest check tried to launch bare `git`. The repair
moved the sole Git-backed admission to the controller, before Harness
invocation, and passed only validated manifest facts into the restricted path.

Read-only inspection then found a second instance of the same coupling on the
actual path: the driver still imported the Git-backed checker. The second
repair made the driver consume the controller-bound facts and independently
revalidate them from the filesystem. A malformed fact or drift now stops as
`manifest_preflight_failed` before root allocation, with zero action attempts,
no evidence write, and no cleanup claim.

This preserved the `PATH`-free worker instead of weakening it and kept Git
admission separate from point-in-time filesystem equality.

### 4. Sole post-repair result - 60 seconds

The post-repair controller was invoked exactly once and returned `PASS`:

| Fact | Observed result |
| --- | --- |
| Controller / dry / actual attempts | 1 / 1 / 1 |
| Readiness probes / drivers / actions / builds | 1 / 1 / 1 / 1 |
| Manifest inputs copied / byte matches | 186 / 186 |
| Wheels emitted | 1 |
| Wheel SHA-256 | `sha256:64f48914b60ae9a7638275f1a9f3b3727bc15b7226c76b37babe08475bae685a` |
| Regular wheel members | 189 |
| Managed byte matches / mismatches | 183 / 0 |
| Generated metadata / unexpected unmanaged members | 6 / 0 |
| Durable evidence SHA-256 | `ffc06da3060b459ff39c8602365126a860e8228dd6320c8c88f69cbc8c6b8715` |
| Final short-root count | 0 |

There was no controller retry, repair during execution, alternate backend,
manual cleanup, network access, dependency installation, Git mutation,
publication, release, deployment, external Agent, or model action.

### 5. Tradeoffs and honest close - 45 seconds

- The chain is intentionally strict: a first deviation ends the task rather
  than maximizing build availability.
- The Harness is containment, not an adversarial security sandbox.
- The durable evidence template intentionally stops its own claim before gated
  cleanup. The controller result and final zero-root observation are separate
  post-cleanup facts; the receipt-validated evidence was not edited afterward.
- One local Windows success does not prove cross-platform behavior, recovery,
  future-toolchain compatibility, repeated reliability, adoption, time saving,
  interview improvement, causal benefit, or return on investment.

## Likely interviewer questions

### Why not give the worker `git` or restore `PATH`?

That would widen the execution boundary to solve a data-flow problem. The
controller already had authority to observe Git state, so it admitted the
manifest once and passed immutable facts inward. The driver still checks
point-in-time filesystem equality before allocating resources.

### Why check the manifest more than once?

The checks answer different questions. The controller proves Git-backed
admission before execution. The driver proves that the files about to be built
still match the admitted identities. Neither observation is treated as
permanent.

### Why preserve a failed temporary root?

Deleting before durable evidence would destroy diagnostic state and make an
unsupported cleanup claim. Cleanup is therefore allowed only after an
exclusive evidence write and receipt revalidation; otherwise the private root
is retained for separately authorized recovery.

### What would you improve next?

The next requirement is not yet authorized. Reasonable review candidates are
an evidence-template version that distinguishes pre- and post-cleanup claims,
or a separately admitted portability/repetition study. Neither follows from
this single replay automatically.

## Evidence to open

- [Immutable replay evidence](build-validation/post-repair-no-retry-artifact-replay-v1-2026-08-27.md)
  records the build inputs, artifact identities, inventory, attempt boundaries,
  privacy boundary, and pre-cleanup wording limit.
- [Current repository status](../STATUS.md) records the controller `PASS`,
  receipt revalidation, gated cleanup, final zero-root observation, and
  validation closeout.
- [2026-08-27 development log](development-log/2026-08-27.md) records the sole
  post-repair execution and the later documentation closeout.
- [Filesystem manifest-boundary repair](build-validation/artifact-driver-filesystem-manifest-boundary-v1-2026-08-26.md)
  records the fixture-validated driver repair without claiming a real replay.
