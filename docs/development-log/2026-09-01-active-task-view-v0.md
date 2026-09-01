# Active Task View v0 - 2026-09-01

## Goal and boundaries

Implement the human-confirmed product requirement behind the TREK UI review:
let a first-time user understand one exact active governed task—its admitted
requirement and path boundary, directly observed evidence, current governance
state, next human boundary, and authority that remains ungranted—without
requiring knowledge of internal commands or contracts.

Native proposal `prp-50c8325a14c84818bcccc45f01e8401a` created and the human
product owner admitted exact task `p0-active-task-view-v0`. The slice excludes
new Kernel concepts, lifecycle event types, task mutation controls, automatic
decisions, and any commit, push, publication, release, or deployment.

## Implemented vertical slice

- Added an immutable content-addressed local scope-observation artifact that
  preserves the complete existing development-scope report and binds it to the
  existing `scope.checked` event through `evidence_ref`.
- Reused identical artifacts while retaining distinct observation events, and
  failed closed on unsafe references, altered content, task/digest mismatch,
  or foreground trigger-to-working-copy path drift.
- Advanced Development Monitor to contract 1.10 with one local-session-only
  Active Task projection over the exact active task, canonical development
  state, artifact-owned task context, existing activity-event identities,
  event-referenced scope paths, validation/completion summaries, read-only
  human guidance, claim limits, and denied downstream authority.
- Kept exported, CI-only, combined, missing-session, and invalid bindings
  explicitly unavailable. Existing Overview, Live Sessions, Protection
  Events, Timeline, Task Detail, Benefit, Learning, and drift reminder remain.
- Synchronized the strict source schema, byte-identical published JSON,
  browser wrapper, product documentation, strategic plan, README, status, and
  regression coverage.

## Validation

The exact supported Python 3.11.9 passed all 115 focused tests and the complete
1,143-test repository suite with six platform-conditioned skips. Python
3.12.10 independently passed the same complete suite with the same skips.

Task governance reports `PASS=3 WARN=1 FAIL=0 ADVISORY=3`; repository
governance reports `PASS=26 WARN=2 FAIL=0 ADVISORY=4`. Task JSON parsing and
`git diff --check` pass. The current-worktree scope check admits 19 task-owned
paths and reports three pre-existing explicitly excluded user paths as FAIL:
`.codex/config.toml`, `docs/assets/linkedin-github-repository-cover.png`, and
`governance/tasks/p0-airbnb-runtime-completion-handoff.json`. They were not
modified, deleted, staged, or claimed by this task; without a task-start
baseline, the low-level scope checker intentionally does not waive them.

## Advisory drift review

- **Requirement:** no observed drift. The result answers the confirmed five
  user questions for one exact task and keeps comprehension and benefit
  unproven pending a separate uncoached review.
- **Architecture:** no observed drift. Path evidence extends the existing
  local evidence area and existing `scope.checked` reference; Active Task is an
  Application/Product Surface projection over existing task, session, state,
  event, scope, validation, and completion concepts. No Kernel concept or
  lifecycle event type was added.
- **Functionality:** no observed drift. The low-level `check scope` remains
  read-only; governed checks persist only the admitted privacy-bounded local
  artifact and event. Aggregate Monitor views remain available, and missing or
  invalid path evidence is never inferred.

This is a bounded current-Agent advisory review, not independent assurance or
human acceptance. First-time comprehension, installed-consumer behavior,
cross-platform behavior beyond the test evidence, adoption, time savings,
error reduction, causal benefit, and ROI remain unknown.

## Authority and next product review

No commit, push, merge, publication, release, deployment, or external mutation
was performed or authorized. A sensible next review is one uncoached
first-time-user comprehension session using the generated Active Task page;
that suggestion grants no task or implementation authority.
