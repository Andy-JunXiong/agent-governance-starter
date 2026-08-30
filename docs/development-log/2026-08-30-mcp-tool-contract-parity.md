# MCP tool contract parity - 2026-08-30

## Goal and boundary

The product owner requested the final TREK-informed AgentGov solution, then
separately admitted and took up task `p0-mcp-tool-contract-parity-v1`. The task
keeps the stable six-base/eight-form-capable MCP catalog and adds no dynamic
lifecycle hiding, Git execution surface, authority registry, host audit event,
OAuth, RBAC, IAM, or Kernel ontology.

The pre-implementation audit found no current runtime safety failure: all 40
focused MCP tests passed. It did find one unprotected structural relation.
Base tools were dispatched by an Adapter-local map while the two native-form
tools were selected by a separate foreground-server branch. Catalog/name
tests would detect some drift, but no single definition guaranteed that every
discovered tool retained the intended route and effect classification.

## Implementation

The development MCP Adapter now defines one immutable policy item for each of
its eight tools. That policy owns only:

- tool identity and stable discovery gate;
- Adapter or native-form route and the concrete handler name;
- repository effect and persistence classification;
- human-decision source and enforcement owner; and
- explicit downstream non-grants.

The catalog names, six/eight discovery groups, dispatch route, and read-only
annotations now derive from the policy. Lifecycle, admission, scope, evidence,
and due-state predicates remain in their existing handlers and effect
boundaries; the new metadata does not duplicate or weaken them.

The parity test covers all eight unique policies, both discovery groups, public
catalog order, declared handler existence, read/write annotations, the exact
three repository-writing effects, shared downstream non-grants, and stable
tool discovery after process-local journey state changes. Existing feature
tests continue to exercise proposal, completion, drift review, alignment, and
self-review success and fail-closed behavior.

## Validation and authority boundary

Focused MCP validation passes 41 tests. The complete repository suite passes
1,112 tests with five Windows privilege-limited symbolic-link skips. Task
governance reports `PASS=3 WARN=1 FAIL=0 ADVISORY=3`; repository governance
reports `PASS=26 WARN=2 FAIL=0 ADVISORY=4`; and `git diff --check` passes.

The internal preservation baseline was not captured before implementation.
Baseline `sha256:09088ce4e4f401ace145c200e5d37b53d6bfe102af84c43448ea9d2d2d39715b`
was captured after implementation and therefore truthfully states that it
cannot prove earlier work. It does prove subsequent preservation. The excluded
`.codex/config.toml` has current file identity
`sha256:4cca2d57edeaddfe52d3e6c4dd4d774192bbdbcab4e84e07df73e14a861c0348`,
which matches its privacy-bounded identity in the earlier 2026-08-28 baseline;
the current Agent did not edit or disclose its content. The raw worktree-wide
scope command still reports that excluded path as a failure, while the internal
baseline comparison classifies its byte-identical state as `PRESERVED`. This
distinction is retained rather than waived.

The post-documentation comparison reports eight `PASS` findings, one `PRESERVED`
finding for the excluded `.codex/config.toml`, and zero failures. Because the
baseline was captured late, that result remains evidence only from its stated
capture boundary onward.

A distinct current-Agent advisory pass reviewed requirement fit, architecture,
functionality, security/authority, and scope. It found the implementation
consistent with the admitted narrow repair: the policy is structural metadata,
existing handlers retain fresh lifecycle and authorization checks, the three
repository-writing effects remain explicit, the public six/eight discovery
shape stays stable, and no secret, network, Git, publication, release, or
deployment path was introduced. The known evidence limitation is disclosed
rather than converted into an exception. This fully specified task has no
alignment journey, so no native self-review completion is claimed.

The active AgentGov connector did not expose
`agentgov_task_completion_record`, so no native completion record was created
or claimed. If that tool becomes available against the current worktree, its
raw scope prerequisite remains expected to fail closed on the pre-existing
excluded `.codex/config.toml` until the completion boundary can consume honest
preservation evidence. No exception is inferred from the late baseline.

No commit, push, publication, release, deployment, external write, or claim of
human product acceptance is authorized by this task.
