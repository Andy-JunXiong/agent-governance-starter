# Release review bundle

`agentgov review release` replaces a manual checklist of test, artifact, and
consumer commands with one create-new-only evidence bundle. It automates
evidence collection; it never makes the release decision.

```powershell
agentgov review release . `
  --wheel dist/agent_governance_starter-0.2.0rc1-py3-none-any.whl `
  --manifest dist/release-manifest.json `
  --consumer "C:\path\to\consumer-repository" `
  --freshness-record governance/evidence/release-candidate-0-3-0rc1.json `
  --freshness-as-of 2026-08-22 `
  --output dist/review-0.2.0rc1
```

The wheel and manifest must already exist because artifact creation and review
are separate release stages. The command refuses symbolic-link inputs,
invalid manifests, mismatched filenames, wheel metadata, or SHA-256 digests.
It never downloads an AgentGov candidate from an unreviewed location.

The two freshness options are an optional development-source pilot and are not
part of the published `0.3.0rc1` command surface. They must be supplied
together. The record path is relative to the selected source repository, and
the explicit date keeps the result reproducible.

## Automated evidence

The command:

1. runs the complete source test suite;
2. installs the exact wheel into a temporary isolated environment without
   project dependencies;
3. verifies the installed version and immutable manifest;
4. checks the selected consumer repository;
5. renders the consumer's portable Markdown status;
6. evaluates the consumer upgrade policy;
7. optionally evaluates one producer-supplied Evidence Freshness record;
8. atomically creates the requested bundle only if that path does not exist.

For a release candidate, an upgrade-plan `blocked` result is the expected safe
state: only a stable manifest may produce a consumer upgrade candidate.

## Consumer governance summary

The human-facing `REVIEW.md` repeats the already-collected consumer Adoption
state and the `PASS`, `WARN`, `FAIL`, and `ADVISORY` finding counts from
`consumer-status.md`. This keeps incomplete adoption and non-blocking findings
visible on the main review page instead of requiring the reviewer to infer
them from a successful collection gate.

A `PASS` `consumer-repository` or `consumer-status` gate means the candidate
command completed and returned the expected evidence. It does **not** mean the
consumer's governance is complete, and consumer warnings or advisory findings
do not become release gates. The reviewer must open `consumer-status.md` for
the detailed findings.

This summary is presentation only. It is not added to the strict
`review.json` 1.0 contract and does not change gate identities, gate statuses,
`review_state`, exit behavior, the pending human decision, or any authority
boundary. If the collected status does not contain the supported Adoption and
Findings tables, the command fails before committing a partial review bundle
rather than guessing the summary.

## Bundle layout

```text
review-<version>/
├── REVIEW.md
├── review.json
├── release-manifest.json
├── agent_governance_starter-<version>-py3-none-any.whl
├── candidate-checks.txt
├── source-tests.txt
├── consumer-check.txt
├── consumer-status.md
├── upgrade-plan.json
└── evidence-freshness.json  # only when the pilot inputs are supplied
```

`review.json` follows `schemas/release-review.schema.json`. It contains portable
source and consumer names rather than absolute local paths. Raw local command
transcripts remain in the bundle and must be reviewed before the bundle is
shared outside the development environment.

`evidence-freshness.json` follows
`schemas/release-review-evidence-freshness-pilot.schema.json`. It contains only
the repository-relative record reference, evidence identity, explicit
`as_of` date, status, reason codes, messages, and non-authorizing boundary
facts. It does not copy the freshness record or raw referenced evidence.

## Non-blocking freshness pilot

`PASS`, `WARN`, `FAIL`, `ADVISORY`, and `NOT_APPLICABLE` freshness results are
all written as separate review context. None becomes an automated release gate,
changes `review.json`, changes `review_state`, or changes the command's exit
behavior. A freshness `FAIL` therefore means that the evidence should be
reconsidered; it does not by itself make the release-review bundle `blocked`.

The checker reads the supplied record exactly once. It does not scan the
repository, discover changes, add `observed_events`, refresh evidence, or edit
the record. Missing, outside-source, symbolic-link, malformed-JSON, or invalid-
date pilot inputs are operational errors and prevent partial bundle creation.

## Decision boundary

`ready_for_human_review` means the deterministic collection gates passed. It
does not mean approved. `blocked` means at least one required gate failed and
the bundle preserves the evidence for diagnosis.

The only human decision states are:

- `approve`;
- `request_changes`;
- `reject`.

The command does not record one of those decisions, modify either repository,
commit, tag, push, publish, release, or deploy. Decision recording and every
Git or release transition require separate explicit authority.
