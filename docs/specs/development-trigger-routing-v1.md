# Development Trigger and Routing Semantics v1

Status: design contract; required before Phase 2 implementation
Owner: AgentGov development-governance architecture
Related decision: [ADR-0009](../adr/0009-govern-coding-agents-during-development.md)
Product context: [AgentGov product and architecture plan](../proposals/2026-08-02-agentgov-product-and-architecture-plan.zh-CN.md)

## Purpose

This specification defines which development-time triggers AgentGov v1 may
emit, how repository paths are compared, and which outcomes may be
deterministic. It closes the path-boundary ambiguity before changed-file scope
checking is implemented.

It does not authorize background monitoring, hooks, semantic architecture
classification, repository writes, or automatic governance-file changes.

## Sources of truth

Trigger and applicability declarations live only in their owning artifacts:

- the development task owns its admitted scope and explicit references;
- `SKILL.md` frontmatter owns skill triggers, non-triggers, and applicability;
- ADR and invariant metadata own their applicable paths or capabilities;
- capability, control, dependency, and evaluation contracts own their
  identities and declared relationships.

The Governance Registry is an in-memory derived index. Context and event
records are derived outputs with provenance; they do not become another source
of trigger or applicability declarations.

## Repository path semantics

All governed paths are canonical repository-relative POSIX paths. Absolute
paths, `..` traversal, backslashes, empty segments, and glob metacharacters are
invalid in a deterministic scope contract.

A prefix matches only on path-segment boundaries:

- `src/route` matches `src/route` and `src/route/handler.py`;
- `src/route` does not match `src/router/handler.py`;
- comparison must not use raw string `startswith`;
- comparison uses the Git-reported repository-relative spelling and does not
  silently case-fold paths.

For a changed path to be admitted:

1. it must equal or descend from at least one `include_paths` entry; and
2. it must not equal or descend from any `exclude_paths` entry.

Exclusion always overrides inclusion, including nested prefixes. A contract
that declares the exact same path in include and exclude remains structurally
invalid rather than relying on runtime precedence.

Rename and delete handling is explicit:

- a rename evaluates both its old and new path; both endpoints must be
  admitted for the rename to pass;
- a deletion evaluates the old path;
- an addition or non-rename modification evaluates its current path.

Natural-language descriptions may explain intent but never participate in a
deterministic path decision. If no valid structured path scope exists,
AgentGov may report an `ADVISORY` scope observation but must not emit
`scope.changed` as a deterministic failure.

## Trigger catalog

The v1 trigger catalog is:

| Trigger | Observable condition | Classification and action |
|---|---|---|
| `requirement.requested` | A person explicitly asks to admit a new requirement | Route to requirement admission; human decision required |
| `task.admitted` | A task contract contains a valid human admission decision | Produce selected context and enable the development slice |
| `implementation.check_requested` | A person or coding agent explicitly invokes a check | Compare declared scope, selected governance, and evidence state |
| `scope.changed` | A Git-reported changed path fails the structured segment-prefix policy | Deterministic `FAIL`, unless an explicit human exception contract applies |
| `architecture.candidate` | The task explicitly references an artifact, or a changed path overlaps artifact-owned `applies-to` paths | `ADVISORY` context-first review only |
| `action_loop.stagnating` | A coding agent explicitly reports structured attempts, hypotheses, and evidence | Record the facts and emit `ADVISORY`; do not infer stagnation automatically |
| `completion.requested` | A person or coding agent explicitly requests completion | Route to fresh evidence and invariant reconciliation |
| `human.decision_recorded` | A person records continue, narrow, pause, or override with a reason | Preserve the accountable decision |
| `ci.replay_requested` | CI explicitly invokes replay on push, PR, or the default branch | Independently reproduce deterministic facts available to CI |

`architecture.candidate` must not be triggered by full-text semantic guessing
in v1. Path overlap uses the same segment-aware comparison defined above and
can only select a candidate for review; it cannot objectively claim that an
architecture decision applies or has been violated.

## Required Phase 2 policy tests

Phase 2 implementation is blocked until fixture-based tests cover at least:

- `src/route` matching itself and descendants but not `src/router`;
- an included `src` path rejected by a nested `src/generated` exclusion;
- exact include/exclude conflicts rejected during task validation;
- rename inside-to-inside passing, inside-to-outside failing, and
  outside-to-inside failing;
- deletion, staged, unstaged, and non-ignored untracked paths;
- Windows separators, absolute paths, traversal, and glob declarations being
  rejected;
- natural-language-only scope producing no deterministic failure;
- explicit reference and path overlap producing only architecture
  `ADVISORY` findings.

The implementation must remain read-only with respect to source files, the Git
index, the current branch, and repository history.
