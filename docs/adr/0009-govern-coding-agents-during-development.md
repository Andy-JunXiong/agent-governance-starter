# ADR-0009: Govern Coding Agents During Development

## Decision gate

Should AgentGov remain primarily a pull-request and CI governance backstop, or
should it govern coding-agent work while requirements, architecture, and code
changes are being developed?

## Context

AgentGov was extracted from governance patterns proven in AI Radar. A current
read-only revalidation of AI Radar at commit
`3a9323cb2a9ef575da42d29fb17d330ef872afd3` shows that its coding-agent
governance is active before and during implementation:

- `AGENTS.md` keeps repository scope, prohibitions, permissions, task modes,
  context routing, and approval boundaries visible;
- requirement and sprint protocols decide whether a concrete change should
  proceed and at what smallest scope;
- architecture context, ADRs, and invariants ground proposed work before code
  changes;
- development-slice and closed-loop protocols constrain implementation and
  require fresh verification evidence;
- action-loop review detects repeated approaches, false completion, and
  premature handoff;
- scoped reconciliation checks whether completed work drifted from governance
  memory.

AgentGov's current product surfaces are strongest after code reaches GitHub.
That preserves useful evidence, but it discovers constraints too late and does
not match the primary governance moment in the reference system.

Consistency with AI Radar means preserving this responsibility model, not
copying AI Radar filenames, business gates, runtime code, individual-specific
rules, infrastructure, or product workflows. The detailed source and reuse
decisions are recorded in `docs/ai-radar-extraction-map.md`.

## Decision

Make development-time coding-agent governance the core AgentGov product.

The primary lifecycle is:

```text
Admit requirement
  -> Ground architecture
  -> Bound implementation
  -> Verify during development
  -> Reconcile before completion
  -> Replay independently in PR/CI
```

AgentGov should help a human and coding agent establish and maintain:

- the task goal, non-goals, smallest scope, risks, and acceptance signals;
- the relevant repository constitution, architecture decisions, invariants,
  capabilities, dependencies, controls, and human approvals;
- the admitted implementation boundary and stop conditions;
- the relationship between actual changed files and the admitted task;
- fresh test, evaluation, and review evidence before completion;
- unresolved deterministic blockers and advisory human judgments.

PR and CI integration remains supported as an independent deterministic replay,
bypass-prevention, and durable evidence surface. It is not the first or primary
place where a developer or coding agent should discover governance constraints.

Repository protocols and CLI findings do not automatically become a mechanical
agent runtime gate. They may instruct, inspect, classify, and request a stop.
Any hook, daemon, IDE control, autonomous interruption mechanism, or additional
write authority requires a separate decision, threat model, and validation.

## Owns

- development-time coding-agent governance as the primary product boundary;
- the ordered requirement, architecture, implementation, verification,
  reconciliation, and CI-replay responsibilities;
- the requirement that task-specific output exclude irrelevant repository-wide
  detail;
- the distinction between deterministic facts, advisory judgment, and human
  authority throughout the development loop;
- PR/CI as a retained backstop rather than the core interaction.

## Does not own

- final CLI command names or durable task-context storage paths;
- semantic interpretation of arbitrary natural-language requirements as an
  objective fact;
- code style, general code quality, or replacement of project-specific tests;
- a universal IDE, coding-agent, or vendor integration;
- runtime enforcement, process termination, autonomous commit or merge, or
  deployment authority;
- AI Radar product runtime gates, schemas, prompts, cognitive logs, or business
  workflows.

## Consequences

Positive:

- governance becomes useful while a change is still cheap to correct;
- coding agents receive task-relevant architecture and authority context before
  editing;
- completion claims can be compared with admitted scope and fresh evidence;
- GitHub reuses the same deterministic facts instead of defining a separate
  governance model;
- the product direction becomes consistent with the source governance system.

Costs and limits:

- task context, change identity, and architecture relevance need new explicit
  contracts;
- natural-language requirement and relevance judgments cannot all be
  deterministic;
- development protocols can add friction and must remain proportional to task
  risk and size;
- existing 0.3 GitHub delivery work becomes supporting infrastructure rather
  than the next product-defining release by itself.

## Alternatives considered

### Keep PR and CI as the product center

Rejected. It provides late evidence but does not govern the coding agent when
requirements, architecture choices, and implementation scope are being shaped.

### Replace PR and CI with local-only agent guidance

Rejected. A coding agent could skip or misreport local checks. Independent CI
replay and durable evidence remain necessary.

### Build a mechanical coding-agent runtime controller first

Rejected. It would add vendor coupling and significant authority before the
repository-native task and evidence contracts are proven.

### Copy AI Radar's governance files directly

Rejected. Their AWS, product, individual, evidence, and workflow rules are not
portable. AgentGov extracts responsibility boundaries and contracts only.

## Implementation plan

1. Define a minimal, vendor-neutral task contract for goal, non-goals, scope,
   acceptance signals, risks, human approvals, and stop conditions.
2. Produce a read-only task context that selects relevant constitution,
   architecture, invariant, capability, dependency, control, and evidence
   references.
3. Compare staged, unstaged, untracked, and renamed files with the admitted
   task boundary without modifying repository or Git state.
4. Add a completion check that requires fresh validation evidence and exposes
   unresolved advisory decisions without claiming semantic certainty.
5. Make local terminal, Markdown, and JSON surfaces primary; reuse the same
   deterministic facts in existing PR and CI integration.
6. Validate the flow first on synthetic fixtures, then against bounded AI Radar
   development scenarios and an independent consumer repository.
7. Defer watch mode, pre-commit, IDE hooks, runtime interruption, and expanded
   write authority until observed use demonstrates a need.

## Validation

Deterministic validation should cover task-contract structure, safe paths,
declared references, Git change classification, stable serialization, no-write
behavior, and reproducible CI replay.

Advisory validation should review whether selected architecture context is
relevant, whether the task framing reflects human intent, whether an exception
is justified, and whether the workflow creates acceptable development
friction. No coverage percentage or architecture-quality score is implied.

## Rollback or replacement

A later ADR may replace the task contract or admit a mechanical integration
after real use. The repository check, report contracts, and PR/CI backstop can
remain independently useful if the development-loop interface changes.
