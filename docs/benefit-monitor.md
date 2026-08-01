# Continuous governance benefit evidence

AgentGov reports observed governance changes without inferring ROI, causality,
prevented incidents, or labor savings.

## Manual two-snapshot comparison

```powershell
agentgov benefits compare before.json after.json
agentgov benefits compare before.json after.json --format json
```

This reports explicit denominators, matched status transitions, deterministic
failures resolved or introduced, non-passing findings cleared, and checks added
or removed. Added and removed checks are not automatically classified as good
or bad.

## Continuous monitor bundle

The 0.3+ managed workflow creates a portable bundle on every run:

```text
agentgov-benefit-monitor/
├── BENEFIT_MONITOR.md
├── benefit-monitor.json
└── benefit-monitor.html
```

The bundle also contains `PR_REVIEW.md`. Pull-request runs append only that
author-facing delta and action summary. Trusted default-branch runs append
`BENEFIT_MONITOR.md`, repository status, history, and upgrade administration.
The HTML file is a self-contained independent page in the `agentgov-reports`
artifact. JSON is the strict machine-readable contract.

The equivalent local command is:

```powershell
agentgov benefits monitor agentgov-report.json `
  --baseline-report previous-report.json `
  --baseline-monitor previous-monitor.json `
  --repository owner/repository `
  --ref refs/heads/main `
  --commit 0123456789abcdef0123456789abcdef01234567 `
  --run-id 12345 `
  --run-attempt 1 `
  --event push `
  --observed-at 2026-08-02T00:00:00Z `
  --output agentgov-benefit-monitor
```

Each snapshot records repository, ref, commit, run identity, observation time,
AgentGov version, finding counts, and the exact report SHA-256. A baseline report
is accepted only when its digest matches the prior monitor identity.

## Trusted GitHub baseline

The workflow does not download the newest artifact with a matching name. It:

1. asks GitHub for completed runs of the same AgentGov workflow on the default
   branch;
2. accepts only push, schedule, or workflow-dispatch runs;
3. selects the baseline artifact from that exact run;
4. verifies the restored report against its monitor SHA-256; and
5. retains at most 20 trend points in the next monitor.

The default-branch baseline is retained for 90 days. Pull-request runs may read
that baseline but never become the trusted `main` baseline. If no baseline is
available or it expired, the monitor reports `baseline_missing` and makes no
trend claim. The weekday scheduled run refreshes the trusted baseline even for
low-activity repositories, so the 90-day retention period is not the normal
lifecycle boundary.

Monitor states are observational:

- `baseline_missing`;
- `unchanged`;
- `improvement_observed`;
- `regression_observed`;
- `mixed_change`;
- `change_observed`.

These diagnostic states map to four action-oriented UI states: `missing`,
`unchanged`, `improved`, and `needs_review`. Regression, mixed change, and an
otherwise unclassified change all require review even though their internal
evidence states remain distinct.

FAIL is rendered as a blocking error annotation. WARN and ADVISORY are warning
annotations and remain non-blocking. A trusted default-branch regression makes
a separate read-only job fail so GitHub can deliver its normal Actions failure
notification. Pull-request jobs receive no comment or issue write permission.

Portable JSON, Markdown, HTML, annotations, and upgrade evidence redact common
runner/user home paths, credential assignments, bearer values, and GitHub token
shapes before presentation. Structured identities are allowlisted.

“Improvement observed” means defined report statuses changed in a favorable
direction. It does not mean AgentGov caused the change.

## Upgrade automation observation

The Draft PR job records a separate upgrade observation:

```powershell
agentgov benefits observe-upgrade agentgov-upgrade-pr.json `
  --repository owner/repository `
  --commit 0123456789abcdef0123456789abcdef01234567 `
  --run-id 12345 `
  --started-epoch 1785630000 `
  --completed-epoch 1785630012 `
  --output agentgov-upgrade-observation
```

It may report:

- elapsed workflow seconds from starting the validated upgrade check to the
  Draft PR result;
- whether a Draft PR was created in that run;
- zero mechanical bridge actions requested by that automated path; and
- whether a human merge decision is still required.

Elapsed workflow time is not human time saved. Zero observed bridge actions is
not an estimate of counterfactual actions avoided.

## Evidence limits

The monitor does not observe project-test results, merged PRs, runtime behavior,
production incidents, false positives, user satisfaction, or financial impact.
Those require separately defined data sources and denominators. No governance
coverage percentage or weighted benefit score is produced.
