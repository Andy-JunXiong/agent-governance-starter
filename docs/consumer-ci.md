# Consumer CI and visible governance status

## Purpose

Repository files alone do not prove that governance participates in normal
development. AgentGov separates three observable states:

1. governance contracts are present;
2. maintainers can run repository checks manually;
3. project CI runs the checks and preserves a report for every change.

`agentgov status` makes those distinctions visible. The bounded GitHub Actions
integration moves an adopting repository from manual-only validation to an
automatic pull-request check without installing project dependencies or
running project, production, release, or deployment workflows.

## Inspect usage

```powershell
agentgov status .
agentgov status . --format json --non-interactive
agentgov status . --format markdown --non-interactive
```

The result includes:

- repository adoption and layout version;
- managed, custom, missing, or conflicting GitHub Actions integration;
- declared capabilities, owners, risk, evaluation readiness, and callers;
- repository validation, pull-request visibility, evaluation evidence,
  benefit-evidence readiness, upgrade-automation state, artifact drift, and
  human-authority surfaces;
- the same PASS, WARN, FAIL, and ADVISORY counts used by repository reports;
- one next action without executing it.

Status is descriptive. It does not infer that every capability or dependency
was discovered, judge semantic quality, run the adopting project, or grant any
approval.

## Preview and create consumer CI

Always review the complete workflow before authorizing its creation:

```powershell
agentgov integrate github-actions . --dry-run
agentgov integrate github-actions .
```

The second command accepts only exact `INTEGRATE` from an interactive terminal.
Redirected input, JSON output, and `--non-interactive` execution never authorize
writes. The command creates only `.github/workflows/agentgov.yml`; it preserves
an exact managed workflow and reports a conflict instead of overwriting any
different existing file.

The generated workflow:

- uses read-only repository permissions and disables persisted checkout
  credentials;
- downloads a fixed AgentGov GitHub Release wheel, verifies its SHA-256, and
  installs it without adopting-project dependencies;
- records the latest stable update state as JSON;
- writes the versioned repository report as JSON;
- writes the human-readable governance report into the GitHub Actions job
  summary;
- beginning with the future stable 0.2 workflow, also writes the richer
  `agentgov status` usage map into the job summary and uploads it as
  `agentgov-status.md`;
- beginning with stable 0.2, downloads the latest stable release manifest once,
  reuses it for update inspection and consumer-local upgrade review, appends an
  available review to the job summary, and uploads the complete review bundle;
- beginning with stable 0.2, checks on weekday pushes and pull requests as well
  as a scheduled 13:00 UTC weekday run, so update discovery does not depend on
  repository activity;
- uploads both files as a GitHub Actions artifact even when governance has a
  deterministic failure;
- blocks on AgentGov `FAIL`, while WARN and ADVISORY remain non-blocking;
- states that no result authorizes merge, release, deployment, or production
  execution.

## What changes when CI is enabled

Without CI integration, capability contracts and evidence can still be checked
locally, but a contributor may never run the command. Broken references, false
readiness claims, dependency cycles, and artifact drift can therefore reach a
pull request without an AgentGov result.

With CI integration, every pushed change receives the same deterministic
repository check and a preserved machine-readable report. Reviewers can see
which declared relationship failed and which questions still require human
judgment. This improves visibility and repeatability; it does not turn static
governance into runtime enforcement or compliance certification.

## Update boundary

The workflow automatically records whether a newer stable AgentGov version or
repository refresh is available. Beginning with stable 0.2, it also generates
the consumer upgrade review in the same read-only job. Version installation and
repository migration remain explicit human-reviewed actions through
`agentgov update .`. The workflow does not open, merge, or publish an upgrade
pull request automatically.

The development-source `agentgov plan upgrade-pr` command defines the read-only
`current`, `candidate`, and `blocked` contract used by the review layer. See
[`upgrade-pr-automation.md`](upgrade-pr-automation.md). No branch or pull
request is created.

The NYC pilot's first stable 0.2.0 run verified the public wheel digest but
exposed that pip rejects a downloaded wheel renamed to `agentgov.whl`. Patch
0.2.1 preserves the canonical wheel filename. The exact public patch must pass
consumer-local review before it replaces NYC's managed workflow.
