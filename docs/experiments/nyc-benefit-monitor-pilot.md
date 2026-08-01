# NYC benefit monitor pilot

## Current state

NYC is pinned to the published AgentGov 0.2.1 managed workflow. It already shows
governance reports, status, and upgrade review in GitHub Actions, but it does not
yet have continuous trend restoration or the Draft PR observation metrics.

## 0.3 pilot experience

After the one-time reviewed 0.3 two-workflow migration, a NYC maintainer will
use:

1. a PR's **AgentGov Summary** for only that PR's delta, blocking failures, and
   non-blocking warnings/advisories;
2. **Actions > AgentGov > Summary** on trusted `main` or scheduled runs for the
   repository report, owner trend, and observed change from the prior baseline;
3. **Artifacts > agentgov-reports** for the portable JSON, Markdown, and
   self-contained `benefit-monitor.html` page;
4. **Artifacts > agentgov-main-baseline** for the exact retained report and
   monitor identity used by the next run; and
5. **Actions > AgentGov Upgrade Proposal** for the separate schedule/dispatch
   writer, an automatically created Draft PR, and its target-version dry-run
   evidence
   when a later compatible AgentGov release is discovered.

The first 0.3 NYC run will display `baseline_missing` and establish the first
trusted baseline. The second eligible run can display `unchanged` or an observed
change. This prevents a single snapshot from being presented as a trend.

## Pilot acceptance signals

- The baseline comes from an exact completed default-branch AgentGov run.
- A PR run cannot replace the trusted main baseline.
- Report and monitor SHA-256 identities agree.
- Actions Summary shows denominators and transitions without a percentage.
- PR runs omit trend and upgrade administration, and receive no write token.
- A new default-branch regression makes a separate read-only signal job red.
- The upgrade workflow has no PR or push trigger, and the Draft PR includes
  exact current/target report summaries and SHA-256 values.
- The HTML artifact renders the recent trend independently of the repository.
- Upgrade observation distinguishes workflow elapsed time from labor saved.
- Human merge, release, deploy, and production authority remain unchanged.

## Not measured by this pilot

The pilot does not claim that AgentGov caused a defect reduction, prevented an
incident, saved a quantified number of hours, or generated ROI. NYC project
tests and runtime/production metrics remain separate evidence sources.
