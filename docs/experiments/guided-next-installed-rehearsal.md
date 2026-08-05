# Installed guided-next rehearsal

## Status

Date: 2026-08-05

Result: the exact current development wheel completed the read-only
`next` route from missing onboarding through explicit task choice, start,
check, finish, and Development Monitor. Every `next` observation selected one
action, reported `action_executed=false` and `modifies_repository=false`, and
left the disposable repository's normalized Git status unchanged.

This was an internal Coding Agent rehearsal, not an uncoached human study. The
automation shell did not provide a real TTY, so onboarding and start writes
used the installed package's same plan, exact-confirmation, and apply functions
with simulated `ADOPT` and `START` responses after human authorization. The
CLI's real-terminal guard was not bypassed or changed, and interactive usability
remains unknown.

## Exact installed candidate

- wheel: `agent_governance_starter-0.3.0.dev0-py3-none-any.whl`;
- size: `260487` bytes;
- SHA-256:
  `fbd16e767178aedd484ec060e9488632ef8191deec8008ff00fc07695828ef3c`;
- build: standard isolated PEP 517 build from the complete current working
  copy;
- installation: fresh Python 3.11 virtual environment with
  `pip install --no-deps`;
- import identity: `0.3.0.dev0` loaded from the disposable environment's
  `site-packages`, with no source-checkout `PYTHONPATH`.

The wheel remained only in a system temporary directory. It was not copied to
`dist/`, release metadata, a consumer, or an external artifact store.

## Independent repository route

The disposable Git repository contained no AgentGov source and no AI Radar
dependency. Two local baseline commits established the generated governance
scaffold and two compact task choices. No commit was created in the AgentGov
source repository and nothing was pushed.

| Observed state | Exactly one `next` action | Result |
|---|---|---|
| No governance scaffold | dry-run `agentgov onboard` | Correct; no mutation |
| Scaffold present, zero admitted tasks | compact-task `govern start` dry-run with explicit title/path placeholders | Correct; no invented task |
| Two admitted tasks | `govern start "<TASK_JSON>" --dry-run` | Correct; neither task was selected |
| Explicit task started | `govern check` | Correct |
| In-scope `work.py` edit and passed scope | `govern finish` | Correct |
| Fresh validation and completion reconciliation | `monitor development` | Correct |

The governed task changed only `work.py` from `STATUS = "todo"` to
`STATUS = "done"`. Scope reported `PASS=1 FAIL=0 ADVISORY=0`. The declared
unittest command passed with bytecode generation disabled so validation did
not create an unadmitted cache artifact. Completion was `verified` within its
declared limits.

The generated Monitor reported:

- scope `local_session` and history completeness `partial`;
- one task and four events;
- one `task.started`, one passed `scope.checked`, one passed
  `validation.completed`, and one verified `completion.reconciled`;
- all four source labels `local_session`;
- cross-stage discovery unavailable and no approval, causal-benefit, ROI, or
  semantic-correctness claim.

## Fail-closed and friction observations

- The compact-task builder rejected the second choice when its validation
  command list was empty. The fixture was corrected instead of weakening or
  bypassing the contract.
- A first harness print attempted to read a non-contract `StartResult`
  convenience attribute after the atomic start had succeeded. The installed
  session and event remained valid; `next` then derived `govern check` from
  them. This was a harness reporting error, not a product-state failure.
- PowerShell array comparison initially produced a misleading display for a
  dirty status. Rechecking normalized status text showed every `next` call was
  non-mutating.
- Zero-task routing is safe but still asks the user to supply title and scope
  placeholders. Multiple-task routing is safe but still requires the user to
  identify the task JSON. This rehearsal establishes deterministic plumbing,
  not a short uncoached journey.
- Installation cannot be selected by a CLI that is not installed yet. A future
  productization slice must define the bootstrap boundary honestly instead of
  pretending `agentgov next` can guide its own pre-install state.

## Validation and claim limits

Independent installed checks returned:

- task: `PASS=3 WARN=1 FAIL=0 ADVISORY=3`;
- working-copy scope: `PASS=1 FAIL=0 ADVISORY=0`;
- repository: `PASS=14 WARN=4 FAIL=0 ADVISORY=4`.

Observed evidence supports the wheel identity, isolated import, exact route,
Git non-mutation, scope facts, command result, completion state, and Monitor
event facts. It suggests the one-action router is mechanically coherent for
this small repository.

Unknowns remain uncoached onboarding and confirmation friction, whether users
understand or correctly fill compact-task placeholders, larger or
multi-language repositories, update discovery, semantic task correctness,
architecture sufficiency, causal benefit, ROI, and cross-machine or CI
history.

## Product consequence

The exact-wheel rehearsal gate for guided development routing is complete. The
next bounded product decision should define two separate surfaces:

1. an honest pre-install bootstrap path outside `agentgov next`; and
2. read-only installed-version/update-state routing inside the CLI, preserving
   onboarding conflict, missing scaffold, repository `FAIL`, active-session,
   exact confirmation, and release authority boundaries.

No install/update behavior, workflow, release identity, consumer migration,
exception record, hook, daemon, upload, merge, or deployment was added by this
rehearsal.
