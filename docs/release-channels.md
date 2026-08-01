# Release channels

AgentGov uses separate GitHub Actions workflows for stable releases and release
candidates. Neither workflow runs from an ordinary branch push. An explicitly
pushed, version-matched tag is the human-controlled publication switch.

## Release candidate

A tag such as `v0.2.0rc1` triggers **Release candidate**. The workflow:

1. verifies that the tag is an RC version and exactly matches the package;
2. requires matching release notes under `docs/releases/`;
3. reruns the complete source test suite;
4. builds the universal wheel;
5. generates and validates a `release-candidate` manifest; and
6. creates a GitHub Pre-release containing the wheel and manifest.

The Pre-release appears in the repository's **Actions** and **Releases** pages.
Because it is marked as a pre-release and explicitly not marked `latest`, the stable
`releases/latest/download/release-manifest.json` update path remains on the
latest stable version. Consumer upgrade planning also rejects RC manifests.

`agentgov review release` remains a pre-tag review step. Its evidence is tied
to the selected consumer pilot, such as NYC, so the release workflow does not
replace that evidence with a generic or self-referential review.

## Stable release

A final tag such as `v0.2.0` triggers **Stable release**. It validates the final
package version, reruns tests, builds the wheel, generates a `stable` manifest,
and creates the GitHub Release used by the normal update channel.

## Authority boundary

Creating or pushing either tag requires separate human approval. The workflows
do not create tags, update consumer repositories, open upgrade pull requests,
merge changes, publish to PyPI, or deploy software. A successful RC workflow is
release evidence; it does not approve promotion to stable.
