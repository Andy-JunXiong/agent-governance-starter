# ADR-0007: Separate Upgrade Proposal From Merge Authority

## Decision gate

How may AgentGov remove the maintainer-as-bridge upgrade bottleneck without
turning a tool update into implicit authority to rewrite or merge a consumer
repository?

## Context

Consumer CI can detect that a newer stable AgentGov release exists, but the
current workflow only preserves update state as an artifact. A person must
translate that signal into project changes. Fully automatic replacement would
be unsafe when a workflow is customized, a repository migration is declared,
or the target layout is not readable by the new release.

## Decision

Adopt a two-stage boundary:

1. a read-only planner validates the stable release manifest, compatibility,
   current managed workflow, exact before/after hashes, and proposed PR text;
2. a separately authorized GitHub integration may later materialize that exact
   plan as a branch and pull request, but it may never merge it.

The first implementation slice is `agentgov plan upgrade-pr`. It produces
`current`, `candidate`, or `blocked` and performs no repository or Git write.

## Owns

- upgrade PR plan schema and state semantics;
- fixed managed-workflow target scope;
- stable release and SHA-256 requirements;
- compatibility, customization, and repository-migration blocking rules;
- exact proposal branch, title, body, content, and hashes;
- the boundary between proposing and merging.

## Does not own

- GitHub authentication or installation;
- organization-wide rollout policy;
- repository-specific workflow customization;
- automatic merge, publication, release, deployment, or production execution;
- migration of human-authored governance decisions.

## Consequences

- A future bot can create a reviewable upgrade PR without a person copying
  release details between repositories.
- Customized workflows and releases with repository migrations stop for human
  handling instead of being overwritten.
- The initial slice does not yet create a PR; it establishes the deterministic
  input contract required before write authority is considered.

## Alternatives considered

- Automatically update and merge every consumer repository: rejected because
  compatibility and governance choices require repository authority.
- Depend only on a badge or update artifact: insufficient because a person
  remains the mechanical bridge.
- Allow arbitrary workflow rewriting: rejected because it would overwrite
  project-owned behavior.

## Implementation plan

1. Ship and pilot the read-only plan contract.
2. Release the planner through the normal stable channel.
3. Add an opt-in GitHub workflow with only `contents: write` and
   `pull-requests: write` for the proposal job.
4. Revalidate hashes immediately before one branch/PR write.
5. Keep merge and every downstream transition human-controlled.

## Validation

Deterministic tests cover current, candidate, customized, incompatible,
migration-declared, malformed-manifest, and no-write states. Human review must
confirm that a repository owner accepts installation of the future PR creator.

## Rollback or replacement

Remove the optional proposal workflow. The read-only CI check, pinned consumer
workflow, and repository governance files remain valid independently.
