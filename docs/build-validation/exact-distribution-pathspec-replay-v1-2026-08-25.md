# Exact distribution pathspec replay v1

Date: 2026-08-25

## Outcome

`PASSED_EXACT_DISTRIBUTION_PATHSPEC_REPLAY`

The one exact replay archived exactly 199 committed distribution inputs and
no unrelated committed file, then applied the exact seven current distribution
overlays. All seven overlays matched their prior task-start Git-layer
identities and their staged byte digests matched their current source bytes.

One offline wheel build and one fresh offline runtime installation passed all
declared shared-template gates. The verified short root, wheel, staged source,
build environment, and installed runtime remained retained while this evidence
was made durable. The exact foreground cleanup continuation then removed the
one task-owned root and every contained artifact.

## Governed boundary

- Resolved alignment journey: `mcpj-d41c9a8d895b4c18ad80ddded912ff50`.
- Selected direction: exact distribution pathspec replay.
- Native proposal: `prp-ca02c6a4b12d4de0b5981c169b778672`.
- Admitted task: `p0-exact-distribution-pathspec-replay-v1`.
- Task-start baseline:
  `sha256:eae7535ba08225739df4ff62e7c14f4392c2d6d84badf4736f3e7370e071c7fb`.

The sole retained `setuptools 84.0.0` wheel matched expected SHA-256
`51a52592b3b99e102b609654876bd65f19f999935166d1352678931132b0c670`
before the one short root was created.

## Exact source staging

| Observation | Result |
| --- | --- |
| Repository `HEAD` versus task baseline | matched |
| Exact committed distribution inputs | 199 |
| Committed input-manifest SHA-256 | `f81a12e42e8fa1739b6af6c708e8b254374fc8e04dcb03af19251ae7e08331c5` |
| Archived regular files | 199 |
| Current distribution overlays | exact expected set of 7 |
| Overlay prior-identity matches | 7 |
| Overlay source/stage byte matches | 7 |
| Overlay manifest SHA-256 | `861b869c153f11e35b619085a63e43b59984df0f319a8bf988e69ae4f5695122` |
| Staged regular files after two new overlays | 201 |
| Short-root helper prior-identity matches | 3 |
| Task roots created | 1 |
| Longest projected target / limit | 207 / 240 characters |

The three nested governance schema files included by the prior
`governance/*.schema.json` Git/PowerShell path semantics account for the
difference between a strict single-directory interpretation of 196 inputs and
the protocol's exact 199 inputs. The archive was created from the explicit
199-file manifest rather than a broad `git archive HEAD`.

## Build, install, and separated gates

| Observation | Result |
| --- | --- |
| Build-backend install attempts | 1 |
| Wheel-build attempts / retries | 1 / 0 |
| Wheels produced | 1 |
| Wheel SHA-256 | `60040e7d9beb6d8e063ca6db7aa8817a6dce7509b4fec9b79d01494bcf031c7e` |
| Wheel members | 188 |
| Wheel member-inventory SHA-256 | `6ca19e08b0658442eab2616ec25f260265ddfcc8fed734e50a0e47f54fbd05da` |
| Runtime creations / install attempts | 1 / 1 |
| Installed version | `0.3.0rc1` |
| Repairs / substitutions | 0 / 0 |
| Network calls / model calls | 0 / 0 |
| Rehearsal v2 started | no |

| Shared-template gate | Result |
| --- | --- |
| Exact wheel member | **PASS**: exactly one `.data/data/share/.../example-capability.input.schema.template.json` member |
| Wheel member versus source | **PASS** |
| Actual runtime data scheme | **PASS**: `scheme.data` equals the fresh runtime root |
| Installed-file presence | **PASS**: regular, non-link file at the scheme-derived target |
| Source versus installed bytes | **PASS** |

Source, wheel-member, and installed template SHA-256 all equal
`e596a428f37f914c6652d650c36df7a47261d6d75118858b6a6ebf99abd91fd6`.
The wheel retained the same 188-member canonical inventory digest as the two
earlier short-root builds.

## Cleanup, privacy, and authority

This record was written while the verified foreground process retained the
exact short-root object and all artifacts. The exact cleanup continuation then
returned **1 created / 1 removed** and exited successfully.

Persisted evidence excludes absolute paths, root token, process identifiers,
raw command output, archive or source content, prompts, responses, credentials,
and host session identities. No product source, packaging declaration, test,
helper behavior, consumer fixture, network, credential, model, Git mutation,
commit, push, publication, release, deployment, external write, or rehearsal
v2 was used or authorized.

## Validation state

The retained-artifact and exact-root cleanup gates above are complete.

- all 7 focused short-root tests passed with 1 platform-limited symbolic-link
  skip;
- the complete supported Python 3.11 suite passed all 1102 tests with 5
  platform-limited skips in 173.347 seconds;
- task governance returned `PASS=3 WARN=1 FAIL=0 ADVISORY=3`;
- repository governance returned `PASS=26 WARN=2 FAIL=0 ADVISORY=4`;
- task JSON parsing and `git diff --check` passed;
- task-start scope comparison returned
  `PASS=10 PRESERVED=35 FAIL=0 TOTAL=45`;
- the bounded task-delta privacy scan found zero absolute-path or sensitive-
  assignment shapes; and
- post-cleanup inspection found zero current short roots.

The first full-suite invocation mistakenly used an interactive terminal. It
blocked at the expected confirmation-reader test and was interrupted without
changing the repository. The same declared command then ran once
non-interactively and produced the complete passing result above. This was a
validation transport correction, not an artifact build, installation, repair,
or retry.

Distinct native current-Agent advisory review
`srv-4ca63255d2c567f06599266e2c23db5e` found the exact requirement result,
scope preservation, single-attempt artifact implementation, evidence-before-
cleanup sequence, cleanup security, privacy boundary, and denied authority
consistent. It retained cross-version, released-artifact, repeatability,
product-owner acceptance, usability, adoption, causal benefit, ROI, and
rehearsal-v2 behavior as unknown. This is a separate self-review pass, not
independent assurance. The native `agentgov_task_completion_record` tool is
not exposed in this session, so no native completion record is claimed or
fabricated. The exact task result and declared validation are otherwise
complete.
