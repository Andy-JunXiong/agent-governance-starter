# Exploration option precondition repair - 2026-09-22

## Goal, scope, and authority

Enforce the existing Core exploration precondition in the MCP Adapter before
presenting an unusable choice. Exact task
`governance/tasks/p0-exploration-option-precondition-v1.json` was admitted by
native form and separately taken up after the human supplied `REPLACE`.
The start event is `evt-3c63f52747aa4ae992033a7044694afb`.

Scope includes the Adapter, its tests and guide, STATUS, this record, and the
task record. Preserve the earlier STATUS changes and all excluded local and
observation records. Core semantics, authority changes, installation, live
replay, Git operations, publication, and release are outside this slice.
Stop if the repair requires those actions or any wider file scope.

## Diagnosis and implementation

An in-memory reproduction accepted a start with zero questions and an
exploration candidate, then failed on selection because Core requires a
remaining non-material question. The Adapter exposed only an unclassified
internal failure. A separate initial caller digest mistake was corrected
before that failure and is not changed by this repair.

The source repair rejects that invalid start before creating a journey and
checks ready updates against the effective remaining questions and inherited
or replacement candidates before mutation. The advertised start schema
matches the rule. Diagnostics retain bounded fields and no rejected values.

Acceptance requires atomic rejection, corrected retries, valid exploration,
preserved human authority and privacy, and passing task-declared checks.
Validation and distinct current-Agent advisory review are pending.

## Validation and advisory closeout

The initial focused run passed 124 tests. The later added exploratory-draft
test initially assumed an exploring state could have no questions. Core
correctly rejected that invalid fixture. The fixture was corrected to retain
a genuine material question, preserving Core's rule and the intended valid
draft test; the corrected focused case passed. The failed evidence
`evd-f859ca7777714c0e927f1a892e4d875f` remains historical evidence.

All six exact task-declared commands then passed in evidence
`evd-e25b7d3f3047494996291e3086a21f57`: focused tests, full tests, task check,
repository check, task JSON, and diff whitespace check. No mutation was
observed during validation. The completion result is `verified`.
The native completion-record tool is unavailable in this session; the
repository `govern finish` command performed the declared validation and
baseline reconciliation without editing the human task decision.

Raw scope observation reported four pre-existing excluded paths. Completion
compared them with the captured task-start baseline and confirmed each was
byte-identical and non-owned. No exception or scope expansion occurred.
The added-text scan found zero local host-path or credential-value matches.

After validation, a distinct current-Agent advisory review checked the exact
diff against the admitted requirement and Core precondition. It found the
start schema consistent with runtime validation, effective update questions
consistent with Core's answered-question removal and candidate inheritance,
and valid exploration and atomic correction covered. The fixed message uses
the existing `normalized_resolution` diagnostic category, with no schema
enum expansion or rejected-value disclosure. No authority is inferred from
the human option selection. This fully specified repair did not start a new
alignment journey; no native self-review completion is claimed. This review
is advisory, not independent assurance or human product acceptance.

The pending-validation statement above is superseded by this closeout.
Installed-client behavior remains unverified. The final documentation
annotation is validated once more against the same admitted scope; its final
evidence identity is reported in the handoff without another tracked edit.

## Product handoff

The source Adapter now catches an unusable exploration choice before asking
the human to choose it. The bounded short-term benefit is a clear corrective
error and preserved retry state. Long-term time savings and adoption benefit
remain unknown. This builds on the native alignment start/update journey and
existing Core precondition, improving the reliability of the project's
human-owned direction selection. A proposed next review is whether to admit
installed-client verification, which would check that the source fix reaches
the actual consumer. No next feature has been selected and no installation,
replay, Git, release, or external action is authorized.

## Source-of-truth review

The MCP guide owns this detailed input rule. README, strategic plan, ADRs,
release metadata, public HTML and localized pages do not describe this edge
condition; their product scope, commands, authority and release facts remain
unchanged. No Core contract or release identity changes. The existing skill
and task boundaries apply without modifications.
