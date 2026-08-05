# Guided development governance session

`agentgov govern start` is the guided entry point for development-time
governance. It connects one admitted requirement and path scope to derived
architecture/Skill context, a comparison base, development checks, fresh
validation, completion reconciliation, and the local Monitor.

This is the future-0.3 development-source interface. It is not part of the
published stable 0.2.1 package yet.

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
