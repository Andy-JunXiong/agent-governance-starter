# Real-action artifact-driver replay v1

Date: 2026-08-26

## Outcome before gated cleanup

REAL_ACTION_PAYLOAD_PARITY_PASS_EVIDENCE_DURABLE_CLEANUP_PENDING

The persisted repository-internal artifact replay driver invoked exactly one
offline wheel-build action. This action returned this sanitized document to
the driver after artifact payload analysis passed. The document contains no
post-cleanup claim: the driver writes and fsyncs it, creates its exact receipt,
and only then calls the existing evidence-gated cleanup.

## Governed boundary

- Admitted task: p0-real-action-artifact-driver-replay-v1.
- Resolved alignment: mcpj-3c98a91e04bb41a79af117293ec4f37e.
- Driver contract: agentgov.internal-artifact-replay-driver.
- Real action attempts: 1.
- Build attempts: 1.
- Retry, repair, alternate backend, dependency installation, or network: 0.
- Standard-input reads and TTY-dependent branches: 0.

## Frozen preflight and staging

| Observation | Result |
| --- | --- |
| Manifest paths | 186 |
| Manifest path identity | sha256:cfea3a3632bd75d1f4db51168d257c465987d3fe620fda2449abcd86f42fcd03 |
| Manifest content identity | sha256:a986da7096e257b90e984084373f923ad460ff4c95f172a08fe4cf2d1fccacaf |
| Retained backend | Python 3.11 / pip 24.0 / setuptools 84.0.0 |
| Retained backend wheel candidates / identity matches | 1 / 1 |
| Copied inputs / byte matches | 186 / 186 |
| Staged regular inputs / links | 186 / 0 |
| Staged path identity | sha256:cfea3a3632bd75d1f4db51168d257c465987d3fe620fda2449abcd86f42fcd03 |
| Staged content identity | sha256:a986da7096e257b90e984084373f923ad460ff4c95f172a08fe4cf2d1fccacaf |

## Single artifact observation

| Observation | Result |
| --- | --- |
| Build return code / wheels emitted | 0 / 1 |
| Wheel SHA-256 | sha256:247b1a7fb72ff8ea941d884e1e2e76613730d4c91ba0ab59ee521b9ae74ab217 |
| Wheel regular members | 189 |
| Member-inventory SHA-256 | sha256:15919824a78e07f1d69e2585a76845af009283164ab7b6235a5fe075c5a8a9c2 |
| Package payloads / data payloads | 76 / 107 |
| Managed payload byte matches / mismatches | 183 / 0 |
| Generated metadata members | 6 |
| Generated-member inventory SHA-256 | sha256:7afd3c8d423d038df21d83d86adfd9cfd30564122d312b11d871297c88aebf09 |
| Unexpected unmanaged members | 0 |

## Evidence, privacy, and authority

The driver owns the evidence target, durable write, canonical SHA-256 receipt,
cleanup call, and normalized result. This action owns only staging, one build,
artifact inspection, and the returned sanitized payload. No absolute host path,
raw process output, source content, credential, or process identity is retained.

This evidence grants no Git, publication, release, deployment, external-Agent,
model, consumer-form, scheduling, retry, repair, or broader journey authority.

## Remaining unknowns

This one local build does not prove cross-platform, concurrent-adversarial,
future-toolchain, recovery, repeated-reliability, adoption, time-saving, causal
benefit, or return-on-investment outcomes. Whether to admit a broader
end-to-end governance journey remains a separate human product decision.
