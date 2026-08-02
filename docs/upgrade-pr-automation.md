# Upgrade pull-request automation

AgentGov separates read-only upgrade planning from an authenticated, bounded
Draft PR writer. This removes the person who copies release information between
AgentGov and each adopting project without granting merge authority.

```powershell
agentgov plan upgrade-pr . --manifest release-manifest.json
agentgov plan upgrade-pr . --manifest release-manifest.json --format json
```

The planner returns:

- `current` when the managed workflow already pins the latest stable release;
- `candidate` with one or two exact managed workflow changes, actions, hashes,
  branch, title, and body;
- `blocked` when the workflow is missing or customized, compatibility is not
  declared, the layout is unreadable, or the release declares an unsupported
  migration.

The manifest must be a valid stable AgentGov release manifest with a fixed-tag
wheel and SHA-256 digest. The candidate is limited to
`.github/workflows/agentgov.yml` and, for 0.3+, the separate
`.github/workflows/agentgov-upgrade.yml`. The read-only planner recognizes only
the named `consumer-ci-v2` migration when moving from the legacy one-workflow
layout to the two-workflow layout. Planning never writes a repository file,
creates a branch or PR, merges, releases, or deploys.

The consumer-facing review command remains read-only:

```powershell
agentgov review upgrade . --manifest release-manifest.json `
  --output agentgov-upgrade-review
```

It creates a Markdown UI, portable JSON contract, exact workflow patch, current
consumer status, and a pending approve/change/reject decision. See
[`consumer-upgrade-review.md`](consumer-upgrade-review.md).

## Authenticated Draft PR writer

The explicit write command is:

```powershell
$env:GH_TOKEN = "<short-lived repository token>"
agentgov create upgrade-pr . `
  --manifest release-manifest.json `
  --repository owner/repository `
  --base main `
  --event workflow_dispatch `
  --current-report agentgov-current-report.json `
  --target-report agentgov-target-report.json
```

It accepts only `schedule` or `workflow_dispatch` as the authorizing event,
requires reports produced by the exact current and proposed AgentGov versions,
re-runs the complete plan, verifies the remote default-branch file against the
exact `before_sha256`, and may then:

1. create `agentgov/update-<version>` from the reviewed base SHA;
2. update only the existing managed AgentGov workflow set with the exact
   planned content;
3. create a Draft PR; or
4. recover/idempotently reuse an exact branch or open PR left by an earlier run.

Remote drift, an unrelated branch change, a customized workflow, absent
compatibility, or any create/delete migration blocks before further write.
Missing reports or a report whose tool version does not match the current or
proposed version also blocks before branch creation. The Draft PR body includes
current/target PASS, WARN, FAIL, and ADVISORY counts, newly introduced
deterministic failures, and both report SHA-256 values. This evidence is
generated before PR creation because a repository-token-created PR cannot be
assumed to trigger other workflows.
The token is read only from the named environment variable and is not included
in output or API errors. The writer cannot approve or merge the PR and has no
release, deployment, or production action.

When the writer returns a valid JSON result, the managed workflow also records
an `agentgov-upgrade-observation` artifact. It measures workflow elapsed seconds
from the validated upgrade check to the Draft PR response and records that the
automated path requested zero mechanical release-copy actions. This is an
observed execution fact, not a claim about labor saved or counterfactual actions
avoided. Human merge remains required.

## Managed 0.3+ workflows

The 0.3+ `.github/workflows/agentgov.yml` workflow is entirely read-only and
handles PR, push, scheduled baseline refresh, and owner visibility. A separate
`.github/workflows/agentgov-upgrade.yml` contains the
`propose-agentgov-upgrade` job with only `contents: write` and
`pull-requests: write`. The second workflow has no PR or push trigger. It runs
on the weekday schedule, or on a manual dispatch only when
`create_upgrade_pr` is explicitly selected.

Keeping the writer in a separate default-branch workflow prevents a pull
request from changing a conditional write job in the workflow it is currently
executing. The bootstrap writer may remain pinned while it installs the exact
managed current version and proposed target version in isolated environments
for dry-run evidence.

The repository owner must enable **Settings > Actions > General > Workflow
permissions > Allow GitHub Actions to create and approve pull requests**. The
workflow asks only to create a PR; it never submits an approval. GitHub documents
this setting in [Managing GitHub Actions settings](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/enabling-features-for-your-repository/managing-github-actions-settings-for-a-repository).

PR checks created with the repository `GITHUB_TOKEN` may appear in an
approval-required state. GitHub documents the recursion boundary and the option
to use a GitHub App or PAT when unattended PR checks are required in
[GITHUB_TOKEN](https://docs.github.com/en/actions/concepts/security/github_token).

## One-time 0.2 to 0.3 bootstrap

0.2.x is intentionally read-only and cannot retroactively acquire a writer.
The 0.3.0 release must therefore declare its consumer-workflow migration and be
reviewed once in each pilot repository. The review contains the exact update of
`agentgov.yml` and creation of `agentgov-upgrade.yml`; the authenticated writer
does not apply this bootstrap migration. After the 0.3 managed workflow set is
human-merged, compatible releases with `repository_changes_declared: false`
can create their own Draft upgrade PRs. Any later workflow architecture change
must again declare a migration and stop for human review.
