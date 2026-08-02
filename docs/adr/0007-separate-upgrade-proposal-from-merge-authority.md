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
2. a separately authorized GitHub integration may materialize that exact plan
   as a bounded managed-workflow change set and Draft PR, but it may never
   merge it.

`agentgov plan upgrade-pr` produces `current`, `candidate`, or `blocked` and
performs no repository or Git write. `agentgov create upgrade-pr` is a separate
write boundary restricted to scheduled or explicitly opted-in dispatch events.

## Owns

- upgrade PR plan schema and state semantics;
- fixed two-path managed-workflow target scope;
- stable release and SHA-256 requirements;
- compatibility, customization, and repository-migration blocking rules;
- exact proposal branch, title, body, content, and hashes;
- the boundary between proposing and merging.

## Does not own

- organization-wide GitHub authentication and token policy;
- organization-wide rollout policy;
- repository-specific workflow customization;
- automatic merge, publication, release, deployment, or production execution;
- migration of human-authored governance decisions.

## Consequences

- A repository-owned workflow can create a reviewable upgrade PR without a person copying
  release details between repositories.
- Customized workflows and unsupported repository migrations stop for human
  handling instead of being overwritten. The planner may render the named
  `consumer-ci-v2` bootstrap for review, but the authenticated writer cannot
  apply its file creation.
- An exact existing branch or PR is reusable after an interrupted run; drift or
  unrelated changes block instead of being overwritten.

## Alternatives considered

- Automatically update and merge every consumer repository: rejected because
  compatibility and governance choices require repository authority.
- Depend only on a badge or update artifact: insufficient because a person
  remains the mechanical bridge.
- Allow arbitrary workflow rewriting: rejected because it would overwrite
  project-owned behavior.

## Implementation plan

1. Ship and pilot the read-only plan contract. (complete in 0.2)
2. Add an opt-in GitHub workflow with only `contents: write` and
   `pull-requests: write` for the proposal job. (implemented for 0.3)
3. Revalidate all remote hashes immediately before one bounded branch/PR
   write. (implemented)
4. Bootstrap one pilot through a migration-declared 0.3 review. (pending release)
5. Keep merge and every downstream transition human-controlled. (invariant)

## Validation

Deterministic tests cover current, candidate, customized, incompatible,
migration-declared, malformed-manifest, no-write, exact one- and two-workflow
writes, partial-write recovery, remote drift, unrelated branch content,
idempotence, and event authorization states.
Human review must confirm that a repository owner accepts installation of the
PR creator and enables the repository permission needed by `GITHUB_TOKEN`.

## Rollback or replacement

Remove the optional proposal workflow. The read-only CI check, pinned consumer
workflow, and repository governance files remain valid independently.
