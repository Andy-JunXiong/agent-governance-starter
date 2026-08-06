# Guided development governance session

`agentgov govern start` is the guided entry point for development-time
governance. It connects one admitted requirement and path scope to derived
architecture/Skill context, a comparison base, development checks, fresh
validation, completion reconciliation, and the local Monitor.

This is the future-0.3 development-source interface. It is not part of the
published stable 0.2.1 package yet.

These commands expose the lifecycle primitives for development, headless use,
CI, diagnostics, tests, fallback, and recovery. ADR-0013 explicitly rejects this manual
sequence as the final ordinary-user journey. The accepted product direction is
a foreground automatic coordinator plus coding-agent adapters that invoke the
same checked state machine, update the Dashboard automatically, and ask the
user only at material semantic or authority boundaries. Development source now
implements the `agentgov dev` coordinator, a strict live foreground JSONL
process transport, bounded task/scope/completion cards, vendor-neutral host
interaction requests, and the first packaged Codex lifecycle-hook Adapter.
It also implements a vendor-neutral Coding Agent task-proposal and exact human
admission fallback plus proactive digest-bound prompt/result contracts and a
reference one-number human-review path. Automatic proposal generation, other
host adapters, and a native authenticated custom-decision surface remain open. See
[Automatic coding-agent governance product requirements](product-requirements-automatic-governance.md).

## Foreground development cycle

A coding-agent adapter can keep one foreground process open and send strict
`agentgov.coding-agent-event` 1.0 JSONL records:

```powershell
Get-Content .agentgov-adapter/events.jsonl |
  agentgov dev . --stream --format json
```

Each accepted record produces one flushed response and an optional bounded
task or completion card. The stream rejects raw prompt/source fields, host
paths, changed-path or task-identity claims, unknown fields, and non-human
decisions. AgentGov derives repository facts locally. The process exits at the
first rejected record and reports its exact input line.

After a human-owned alignment result is resolved, the same connection also
accepts an Adapter-owned active-Agent self-review start. AgentGov returns one
`materialization_required` context request; the same Adapter returns observation
drafts bound to that request; AgentGov returns the completed advisory result.
This two-stage exchange uses foreground memory only. It is not an extra user
prompt: the Coding Agent Adapter emits the records and uses its existing model
entitlement, while AgentGov itself makes no model or network call.

The existing adapter/headless fallback can still invoke one cycle directly:

```powershell
agentgov dev . --event implementation.changed
agentgov dev . --event completion.requested
```

The first event derives actual changed paths and records a deterministic scope
observation. The second first checks scope, then runs only validation commands
already admitted in the active task, reconciles completion, and refreshes
`.agentgov/dashboard.html`. Out-of-scope changes block validation.

A human-originated review event may hand off an exact verified session without
typing the legacy fallback word:

```powershell
agentgov dev . --event session.reviewed `
  --actor-class human --review-outcome accepted
```

These commands expose the reference adapter for development, recovery, and
integration testing. The intended normal experience is for a packaged Codex,
Claude Code, or IDE adapter to emit the JSONL events automatically. A missing
admitted task returns a task card and machine-readable `task_admission` gate,
then refreshes the Dashboard; it does not infer scope or create a task from raw
prompt text.

## Codex project-hook Adapter

The optional development-source Codex Adapter maps reviewed project callbacks
without forwarding prompt, tool payload, transcript, assistant-message, model,
or absolute host-path values:

| Codex callback | AgentGov event |
| --- | --- |
| `SessionStart` | `repository.activated` |
| `UserPromptSubmit` | `task.requested` |
| `PostToolUse` | `implementation.changed` |
| `Stop` | `completion.requested` |

Preview the exact create-only project hook file with:

```powershell
agentgov integrate codex-hooks . --dry-run
```

Interactive apply requires exact `INTEGRATE`, refuses to overwrite or merge an
existing `.codex/hooks.json`, and does not grant hook trust. Review and enable
the definition separately through Codex `/hooks`. `PostToolUse` findings are
after-the-fact observations and do not undo a tool side effect. A repeated
`Stop` callback with `stop_hook_active` does not rerun completion. See
[Codex hooks Adapter](codex-hooks-adapter.md).

The managed configuration also observes `PermissionRequest`, but AgentGov
returns neither allow nor deny. Codex keeps its normal human tool approval
prompt, and that permission is not treated as task admission, scope expansion,
exception approval, or completion acceptance.

Task-admission, scope-resolution, and completion-review cards now carry a
vendor-neutral `agentgov.host-interaction-request` when a real human gate
exists. The request declares delivery and decision-recording capability and
always reports `decision_applied=false`. Current Codex Hooks deliver these
custom gates as context only and cannot record their decision.

Codex `UserPromptSubmit` is no longer treated as proof that a development task
exists. The Hook discards the prompt and tells the conversational Agent to
classify a strict `agentgov.work-request` host-side. Questions, explanations,
status queries, and read-only diagnosis need no task; repository modification
must route before it begins.

## Risk-based admission routing

`agentgov route request` separates five outcomes: `observe_only`,
`continue_active`, `fast_track`, `human_review`, and `full_review`. The first
three have a zero-interruption budget. `fast_track` additionally requires an
admitted, Git-tracked, clean standing policy and every scope, validation, risk,
assumption, unknown, and material-characteristic constraint to pass.

Only `--apply-fast-track` may create the bounded task without a per-task human
decision. It creates no session and executes no code. See
[risk-based admission routing](admission-routing.md).

## Structured task proposal fallback

A host Adapter or Coding Agent may prepare a strict normalized low-risk
proposal for separate human review:

```powershell
agentgov propose task path/to/proposal.json --repository . --dry-run
```

The proposal contract excludes raw prompts, transcripts, source content,
credentials, absolute paths, and authority. Preview shows the exact compact
task, assumptions, unknowns, digests, and sole target. A planned low-risk
review may proactively accept one numbered approve/change/reject selection;
exact interactive `ADMIT` remains a fallback. Either admission path creates
only that task file and does not start this development session. See
[task proposal and human admission](task-proposal-admission.md) and
[minimal-input human decisions](human-decision-prompts.md).

## Normal workflow

Start from an existing admitted task:

```powershell
agentgov govern start governance/tasks/my-task.json
```

The command first prints the task identity, exact comparison-base commit,
selected governance paths, every planned write target, and the denied authority
boundary. A real terminal must then enter exactly `START`. It creates only the
untracked working-copy pointer and one immutable start event. A different
active task requires `--replace-active`, a new preview, and exact `REPLACE`.

For a low-risk task, the same entry point can scaffold the compact contract:

```powershell
agentgov govern start `
  --title "Add request timeout" `
  --include src/http `
  --include tests/http
```

Python unittest, npm test, Cargo, and Go validation entry points are detected
only when their conventional project files exist. Otherwise `--validate` is
required. The preview contains the complete proposed JSON. AgentGov never
guesses semantic scope: at least one machine-checkable `--include` is required,
and the generated task file is included in its own scope.

During and at the end of work, the task and base no longer need to be repeated:

```powershell
agentgov govern check
agentgov govern finish
agentgov monitor development .
```

`check` observes current scope. `finish` defaults to the recorded comparison
base, runs every task-declared validation command, and returns `verified` only
when the fresh evidence and completion snapshot are unchanged and in scope.
The Monitor displays the start, selected governance paths, checks, validation,
and completion events. Selection is observed; actual coding-agent consumption
remains unknown until a separate consumption event exists.

## Read-only next-action routing

The future-0.3 source implementation of `agentgov next .` now reads the same
strict session pointer and immutable event stream to select one step without
executing it:

| Current working-copy state | Selected command family |
|---|---|
| No active session | Dry-run `govern start` preview |
| Matching `task.started` | `govern check` |
| Latest scope passed | `govern finish` |
| Validation recorded or completion needs evidence | `govern finish` |
| Completion verified | `monitor development` |
| Session explicitly handed off | Dry-run `govern start --replace-active` rollover |

Adoption conflicts, missing scaffold, and deterministic repository `FAIL`
remain higher-priority gates. Multiple admitted tasks produce an explicit
`<TASK_JSON>` choice rather than filename or semantic inference. Repository
WARN and ADVISORY findings remain visible through `check`, `report`, and
`status`, but they do not displace the current development step.

Session or task drift, tracked/malformed pointers, missing matching start
events, invalid event stores, and failed scope are blocking results. `next`
does not repair those states or invent a safe command when the existing
contracts do not define one. Events older than the exact session start do not
establish current progress.

This routing is read-only: text and strict JSON return exactly one action with
`action_executed=false`, and no prompt, task write, validation, Monitor
generation, Git operation, or authority transition occurs.

## Verified-session terminal boundary

Development source implements ADR-0012 without deleting
`.agentgov/current-task.json` or treating Monitor generation as proof of human
review:

```powershell
agentgov govern handoff --repository . --dry-run
agentgov govern handoff --repository .
agentgov next . --non-interactive
```

The preview re-establishes the exact task, comparison base, latest verified
completion, evidence identity, full Git snapshot, and scope. It names the
retained pointer and exactly one append-only `session.handed_off` target. The
write requires exact `HANDOFF` from a real terminal, repeats the freshness
check, and is idempotent for the stable session event identity. Redirected,
cancelled, stale, drifted, malformed, and unsupported-progress paths append
nothing.

The retained pointer continues to identify the exact task digest, base, and
session; handoff means only that automatic routing responsibility ended. A
later read-only `next` recommendation previews a separate
`govern start --replace-active --dry-run`, excludes the same handed-off digest,
and preserves explicit choice among multiple tasks. A changed digest can enter
only through the normal reviewed replacement and exact `REPLACE`. Published
stable 0.2.1 does not include this development-source interface.

## Discovery and automation behavior

- With no task or `--title`, start selects only when exactly one valid admitted
  task exists under `governance/tasks/`.
- Zero candidates require compact task inputs. Multiple candidates require an
  explicit task path; AgentGov does not choose one semantically.
- `--dry-run` renders the complete plan and writes nothing.
- A non-interactive terminal never grants write authority and therefore only
  previews before returning `CANCELLED`.
- A task content or decision change invalidates the pointer. Check and finish
  fail closed until the new task is reviewed through start and
  `--replace-active`.
- One active task is supported per Git working copy. Separate Git worktrees
  have separate `.agentgov/current-task.json` pointers.

This preserves the productization direction: installation and update routing,
CI artifact adoption, and IDE/agent integration can later automate safe
discovery and defaults around this contract. It does not justify hidden hooks,
background daemons, silent governance edits, or unattended approval.

## Local state and source of truth

`.agentgov/current-task.json` contains only:

- repository-relative task path and identity digest;
- the exact comparison-base commit;
- start time and the confirming human's optional vendor-neutral label.

It contains no requirement, ADR, invariant, Skill, source code, validation
output, credential, or approval authority. The task, `AGENTS.md`, ADRs,
invariants, and `SKILL.md` metadata remain the only governance declarations.
The pointer must stay untracked. Untracked `.agentgov/` files are canonically
excluded from scope and fresh-evidence snapshots; tracked `.agentgov/` changes
remain visible and can fail scope.

## Retained low-level interfaces

Advanced users and tests can still call `check task`, `context task`, `check
scope`, explicit-task `govern check`, and explicit-task/base `govern finish`.
They are stable composition surfaces, not the intended final daily workflow.

Start, check, finish, events, and the Monitor do not authorize implementation,
exceptions, commits, pushes, pull requests, merges, deployments, publication,
or release.
