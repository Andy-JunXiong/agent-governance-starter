# Release review bundle

`agentgov review release` replaces a manual checklist of test, artifact, and
consumer commands with one create-new-only evidence bundle. It automates
evidence collection; it never makes the release decision.

```powershell
agentgov review release . `
  --wheel dist/agent_governance_starter-0.2.0rc1-py3-none-any.whl `
  --manifest dist/release-manifest.json `
  --consumer "C:\path\to\consumer-repository" `
  --output dist/review-0.2.0rc1
```

The wheel and manifest must already exist because artifact creation and review
are separate release stages. The command refuses symbolic-link inputs,
invalid manifests, mismatched filenames, wheel metadata, or SHA-256 digests.
It never downloads an AgentGov candidate from an unreviewed location.

## Automated evidence

The command:

1. runs the complete source test suite;
2. installs the exact wheel into a temporary isolated environment without
   project dependencies;
3. verifies the installed version and immutable manifest;
4. checks the selected consumer repository;
5. renders the consumer's portable Markdown status;
6. evaluates the consumer upgrade policy;
7. atomically creates the requested bundle only if that path does not exist.

For a release candidate, an upgrade-plan `blocked` result is the expected safe
state: only a stable manifest may produce a consumer upgrade candidate.

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
└── upgrade-plan.json
```

`review.json` follows `schemas/release-review.schema.json`. It contains portable
source and consumer names rather than absolute local paths. Raw local command
transcripts remain in the bundle and must be reviewed before the bundle is
shared outside the development environment.

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
