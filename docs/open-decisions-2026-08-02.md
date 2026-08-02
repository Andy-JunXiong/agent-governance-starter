# Open product decisions — 2026-08-02

This note records decisions that were deliberately left open after the AgentGov
and NYC integration review. It is not a claim that the described behavior is
already available in a published release or adopted by NYC.

## Product boundary: development-time versus pull-request governance

ADR-0009 resolves the boundary: development-time governance of requirements,
architecture, implementation scope, and fresh evidence is the product core.
Pull-request and CI governance remains an independent replay and evidence
backstop. This matches the responsibility separation revalidated against AI
Radar's current Layer A' coding-agent governance without importing its product
rules.

The current product is strongest at the GitHub boundary: it renders repository
checks, PR-facing findings, owner summaries, upgrade evidence, and retained
artifacts. That is a useful final backstop, but it is too late to be the primary
developer experience.

The first development-source slice now provides a strict task JSON contract
and a read-only validation entry point:

```text
agentgov check task governance/tasks/<task-id>.json --repository .
```

Task creation and changed-file entry points remain intentionally not final.
Possible later commands include `agentgov dev start` and `agentgov dev check`,
but the current check does not imply that either interface has been accepted.

The product boundary is decided. Interface decisions remain open:

- whether and how a future `start` command creates durable task context;
- deterministic versus advisory rules for mapping a task and changed files to
  capabilities, controls, dependencies, evaluation evidence, and approvals;
- treatment of staged, unstaged, untracked, renamed, and generated files;
- behavior when the base ref is unavailable or the repository is shallow;
- the stable JSON/Markdown context contract that coding agents can consume;
- how IDEs and agents discover and invoke the local check without a proprietary
  integration;
- whether pre-commit or watch mode adds enough value after the explicit command
  path is proven.

GitHub checks remain the independent, reproducible enforcement and evidence
surface. They should not require a developer to discover governance only after
opening a PR.

## Delivery and notification

The 0.3 implementation separates two personas:

- PR authors see only their change delta, blocking failures, and required
  action;
- project owners see trusted-main trend, benefit evidence, and upgrade state.

WARN and ADVISORY remain visible but non-blocking. A trusted-main regression
uses a red, read-only Actions job so GitHub can deliver its normal failure
notification. It does not post PR comments or create issues.

Still open:

- whether a later trusted workflow or GitHub App should push owner notifications
  through comments or issues;
- what rate limits, deduplication, acknowledgement, and close conditions would
  be required before granting that write authority;
- whether a README badge improves discovery without turning stale state into a
  misleading dashboard.

## Upgrade bootstrap and release boundary

Published 0.2.1 consumers are read-only. They cannot acquire the 0.3 Draft PR
writer without one human-reviewed workflow migration. The migration should be
generated and reviewed inside the adopting repository, not require the user to
operate from the AgentGov source repository.

Before a 0.3 release candidate:

- the release manifest must declare the two-workflow migration;
- the consumer-local review must show the exact permission and workflow diff;
- the upgrade writer must retain current- and target-version dry-run evidence,
  because a PR created with `GITHUB_TOKEN` cannot be assumed to trigger another
  workflow;
- the NYC pilot must exercise the migration and produce reviewable evidence.

Whether unattended PR checks justify a GitHub App or PAT remains open. The
default remains the lower-authority design: generate evidence before creating a
Draft PR and leave merge authority with a human.

## Benefit claims

AgentGov may report observed governance status transitions and delivery facts.
It must not turn `unchanged` into a benefit, imply causality, claim prevented
incidents, or estimate ROI from workflow duration.

NYC business code does not improve merely because its governance workflow is
upgraded. A credible case study needs either a real future change or a bounded
historical-change replay that demonstrates what AgentGov surfaced and when.
Project tests, runtime quality, and operational outcomes remain separate data
sources.

Open decisions:

- which historical NYC changes form the release-gate replay set;
- how to compare local development-time discovery with PR-time discovery;
- which project outcome signals, if any, have a defensible denominator and can
  be joined without claiming causality;
- how long low-activity repository history should remain available beyond the
  scheduled baseline refresh and 90-day artifact retention.

## Decision rule

New states or surfaces should exist only when they change a user's action or
preserve necessary evidence. Where several internal diagnostic states require
the same user response, the UI should continue to map them to one action state.
