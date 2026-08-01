# Upgrade pull-request automation

AgentGov now defines the read-only contract required to remove the person who
copies release information between AgentGov and each adopting project.

```powershell
agentgov plan upgrade-pr . --manifest release-manifest.json
agentgov plan upgrade-pr . --manifest release-manifest.json --format json
```

The planner returns:

- `current` when the managed workflow already pins the latest stable release;
- `candidate` with one exact workflow change, hashes, branch, title, and body;
- `blocked` when the workflow is missing or customized, compatibility is not
  declared, the layout is unreadable, or the release declares migrations.

The manifest must be a valid stable AgentGov release manifest with a fixed-tag
wheel and SHA-256 digest. The candidate updates only
`.github/workflows/agentgov.yml`. Planning never writes a repository file,
creates a branch or PR, merges, releases, or deploys.

The consumer-facing review layer is now implemented:

```powershell
agentgov review upgrade . --manifest release-manifest.json `
  --output agentgov-upgrade-review
```

It turns the plan into a create-new-only review bundle with a Markdown UI,
portable JSON contract, exact workflow patch, current consumer status, and a
pending approve/change/reject decision. The planned workflow remains unchanged.
See [`consumer-upgrade-review.md`](consumer-upgrade-review.md).

The reporting-only 0.2+ consumer workflow now downloads the latest stable
manifest and publishes this review in the job summary and artifact. The
remaining implementation slice is an authenticated, opt-in writer that
revalidates the exact before hash and creates or updates one draft PR. It will
not auto-merge. This write layer must not be activated until the planner is
present in a published stable AgentGov release and the consumer repository
owner authorizes its permissions.
