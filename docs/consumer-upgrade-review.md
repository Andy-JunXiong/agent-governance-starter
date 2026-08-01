# Consumer upgrade review

Release approval and consumer upgrade approval are separate decisions.
AgentGov maintainers review a release in the AgentGov repository. An adopting
project owner reviews whether to use that stable release inside the adopting
project.

Run this command from the consumer repository, or point it at that repository
from CI:

```powershell
agentgov review upgrade . `
  --manifest release-manifest.json `
  --output agentgov-upgrade-review
```

The manifest must describe a valid stable release. A release-candidate
manifest produces a visible `blocked` review and cannot produce an upgrade
proposal.

## Consumer-facing UI

The new directory contains:

```text
agentgov-upgrade-review/
├── UPGRADE_REVIEW.md
├── upgrade-review.json
├── upgrade-plan.json
├── workflow.patch
├── current-status.md
└── release-manifest.json
```

`UPGRADE_REVIEW.md` is the human interface for a GitHub job summary, CI
artifact, or future draft pull request. It shows:

- the current and proposed AgentGov versions;
- the exact managed workflow path and before/after hashes;
- the current consumer governance findings;
- stable-release, compatibility, bounded-change, and consumer-check gates;
- approve, request-changes, and reject choices;
- the operations that remain unauthorized.

`agentgov status .` exposes this consumer capability as the
`upgrade_automation` surface with state `review_ready`.

The AgentGov-managed 0.2+ GitHub Actions workflow performs this reporting
automatically. It downloads the latest stable manifest over HTTPS, reuses that
exact file for update inspection and upgrade review, appends
`UPGRADE_REVIEW.md` to the GitHub job summary when present, and uploads the
complete directory in the `agentgov-reports` artifact. The workflow retains
`contents: read` and uses no credentials or project dependencies.

`workflow.patch` is evidence only. Creating the bundle does not apply that
patch. The machine-readable `upgrade-review.json` follows
`schemas/upgrade-review.schema.json` and uses the consumer name instead of its
absolute local path.

## Meaning of states

- `ready_for_human_review`: one compatible stable workflow update is available
  and deterministic gates passed;
- `no_upgrade_needed`: the managed workflow already uses the available stable
  release;
- `blocked`: the release is not stable, compatibility is absent, the workflow
  is customized or unsafe, a migration is declared, or the consumer has a
  deterministic governance failure.

## Authority and evidence limits

The review command creates only the explicitly named evidence directory. It
does not modify governed files, apply the proposed workflow, download or run
the release wheel, run project tests, create a branch or pull request, merge,
release, or deploy. The release artifact still requires digest verification at
installation time.

The authenticated 0.3+ write layer lives in a separate schedule/dispatch-only
workflow and uses the same plan to create or recover a Draft PR after the
consumer owner explicitly enables write permissions. It runs the exact current
and proposed versions first, revalidates the remote before hash, permits only
the managed governance workflow path, and never auto-merges.
