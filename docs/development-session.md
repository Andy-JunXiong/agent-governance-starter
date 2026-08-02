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

This preserves the productization direction: later installation, update,
onboarding, CI artifact wiring, and IDE/agent integration can automate safe
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
