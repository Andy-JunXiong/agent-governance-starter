# Distribution manifest scope-observation synchronization - 2026-09-22

## Goal, admission, and boundary

Restore exact current distribution inputs and the fixed replay controller's
matching identity. The human requested this bounded repair after reviewing
the isolated package verification. Native proposal
`prp-4d6fcf19232c4e44afaa83785d0a85d7` admitted task
`p0-distribution-manifest-scope-observation-sync-v1`; human `REPLACE`
separately started it with event `evt-411ec162366e46c0b398bf3b61a34fed`.

Acceptance requires the exact independently derived 188-path list, matching
path/content identities, synchronized controller constants, passing regression
and declared checks, and preserved historical evidence. Scope is the manifest,
controller, its tests, STATUS, this log, and the exact task record. Stop if the
repair requires changing selection, packaging, source behavior, authority,
request shape, retry, cleanup, or any wider scope.

No artifact build, install, download, client/model session, Git write,
publication, release, or deployment is part of this repair.

## Reproduction and changes

Read-only derivation found only `src/agentgov/scope_observation.py` missing
from the durable manifest, with no obsolete path to remove. The old manifest
and controller both retained 187-path identities. A new regression checking
actual current derivation against both owners first failed on the missing
input and stale digests, reproducing the defect before repair.

The sorted manifest now includes that module exactly once. Manifest and
controller now both bind 188 paths with these identities:

- Path digest: `sha256:23a850bd924f45a8888fcfe7cbc591ed1edfb30c1735810d60a5833bc210fb54`.
- Content digest: `sha256:f222e756b70a8f57ae5ef49db95b257729ad515cdf8066400ab67bf483fb8162`.

Only the controller's count and two identity constants changed. Existing
content-mismatch rejection remains covered; added fixtures also verify that
stale count and path identity stop before any harness invocation. The
current-input regression catches source/manifest/controller drift together.
The focused suite ran 21 tests successfully with one platform-conditioned
skip. Task-declared closeout checks and distinct advisory review are pending.

## Source-of-truth review

The existing distribution contract and derivation algorithm already require
exact current inputs; their semantics do not change. README, strategic plan,
ADRs/contracts, user guides, release metadata, public/localized pages, and
packaged source require no changes. STATUS owns the newly passing current
state. Earlier 187-path observations and the isolated-verification manifest
failure remain historical evidence at their original stable paths.

The new identities match the temporary snapshot independently recorded in
the prior isolated verification. That relationship does not make this a new
build, protocol replay, or consumer activation result.

## Product handoff context

The durable input declaration and fixed artifact gate can now recognize the
current source consistently. This closes the static gap observed during the
isolated package verification and adds an early regression signal for future
identity drift. It builds on independent distribution derivation and the
fixed replay controller. Long-term maintenance savings and reliability
benefits remain unknown. The proposed next review is the full installed/source
difference before any real-client activation; this repaired identity can
support that review. No next feature or installation has been selected.

## Validated closeout

All six exact task-declared commands passed in evidence
`evd-01c104c849064d7c99f77debd7f81caf`: current manifest derivation and identity
check, focused manifest/controller/documentation tests, task governance,
repository governance, task JSON, and diff whitespace checks. Validation
observed no mutation, and task-start baseline reconciliation returned
`verified` while preserving the excluded pre-existing changes. The current
native completion-record tool is unavailable; repository `govern finish`
recorded the evidence without editing the human task decision. No full
product-suite rerun or artifact execution is claimed for this static task.

After validation, a distinct current-Agent advisory review inspected the
complete implementation diff against the admitted task and existing
distribution contract. Exactly one independently derived module was added;
the count and both digests match current inputs and the fixed controller.
The new test independently checks current source/manifest/controller parity,
while existing content mismatch and new path/count mismatch cases preserve
the pre-launch rejection boundary. Packaging selection, request shape,
authority, retry, cleanup, and historical evidence were unchanged. The
new record's host-path and credential-value scans found zero matches.

This was a fully specified repair with no new alignment journey. The review
is a separate current-Agent advisory pass, not native self-review completion,
independent assurance, or human acceptance. Future activation and long-term
benefits remain unknown. The pending closeout statement above is superseded.

Final documentation annotations are revalidated once against this scope.
The latest evidence identity is reported in the handoff without another
tracked edit, preserving the final snapshot's validation identity.
