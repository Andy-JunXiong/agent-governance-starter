---
layout: reference
title: Evidence freshness semantics v1
source_path: docs/specs/evidence-freshness-v1.md
---

# Evidence Freshness Semantics v1

Status: implemented in development source; optional and not part of stable `0.2.1`
Owner: AgentGov evidence-validity contract
Schema: [`schemas/evidence-freshness.schema.json`](../../schemas/evidence-freshness.schema.json)

## Purpose

Evidence Freshness v1 records whether longer-lived governance evidence is
still usable under explicit review, expiry, policy, and change-event facts. It
does not inspect source content or decide whether the original evidence was
sufficient.

This contract is separate from
[Fresh Validation Evidence v1](fresh-validation-evidence-v1.md). Fresh
Validation Evidence binds one validation run to an unchanged task and Git
snapshot. Evidence Freshness v1 evaluates a declared record after that evidence
already exists. Neither contract grants approval or consequential authority.

## Record

An `agentgov.evidence-freshness` 1.0 record contains:

- a kebab-case evidence identity;
- explicit `applicable` or `not_applicable` status;
- repository-relative POSIX evidence references;
- `reviewed_at` and optional `review_due_on` dates;
- optional explicit `expires_on`, plus `current`, `superseded`, or `unknown`
  policy status and a repository-relative policy reference;
- normalized declared invalidating events and observed events.

Applicable evidence requires at least one evidence reference, a review date,
and a policy reference. A not-applicable record requires a reason and must not
carry evidence, review, validity, or event facts. This makes not-applicability
an explicit contract state rather than an absent-file assumption.

Example:

```json
{
  "contract": "agentgov.evidence-freshness",
  "schema_version": "1.0",
  "evidence_id": "current-evaluation-baseline",
  "applicability": {"status": "applicable", "reason": null},
  "evidence_refs": ["evaluation/evaluation-manifest.json"],
  "review": {
    "reviewed_at": "2026-07-01",
    "review_due_on": "2026-10-01"
  },
  "validity": {
    "expires_on": "2027-01-01",
    "policy_status": "current",
    "policy_ref": "evaluation/readiness-policy.md"
  },
  "invalidation": {
    "declared_events": ["evaluation-policy-changed"],
    "observed_events": []
  }
}
```

## Status semantics

The checker evaluates facts against an explicit `as_of` date. A date is due
or expired when `as_of` is on or after that date.

| Status | Meaning | CLI exit |
|---|---|---:|
| `PASS` | No explicit expiry or invalidating condition is active. | 0 |
| `WARN` | `review_due_on` has been reached. Review is due, but elapsed time alone does not invalidate evidence. | 0 |
| `FAIL` | The contract is malformed, the review date is in the future, explicit expiry has been reached, policy is superseded, or an observed event exactly matches a declared invalidating event. | 1 |
| `ADVISORY` | Policy validity is `unknown` and requires accountable human review. | 0 |
| `NOT_APPLICABLE` | The record explicitly declares that this evidence type does not apply. | 0 |

When multiple conditions exist, `FAIL` takes precedence, followed by `WARN`,
`ADVISORY`, and `PASS`. All detected reason codes remain visible. An expired
record may therefore also show that review is due without weakening the hard
failure.

The checker never calculates expiry from `reviewed_at` or `review_due_on`.
Expiry exists only when the record supplies `expires_on`. Likewise, it does
not discover repository changes. An accountable producer must supply observed
event identities, and invalidation occurs only on exact membership in the
declared event set.

## Command

Use an explicit date for reproducible local or CI checks:

```powershell
agentgov check evidence-freshness governance/evidence/example.json --as-of 2026-08-21
```

Without `--as-of`, the checker uses the current UTC date. The command reads one
record and writes nothing. `WARN`, `ADVISORY`, and `NOT_APPLICABLE` remain
non-blocking; only `FAIL` returns exit code 1. Missing files, malformed JSON,
and invalid command dates are operational errors and return exit code 2.

## Privacy and authority

Evidence and policy references must stay repository-relative and use POSIX
separators. Absolute paths, traversal, Windows-style paths, and secret-like
material are rejected. The record stores references and event identities, not
raw evidence, prompts, source content, credentials, or host-local paths.

The checker does not automatically scan a repository, infer policy quality,
approve evidence, change a decision, refresh evidence, edit files, or
authorize Git, publication, release, deployment, or any other consequential
action.
