# Development automation contracts

Status: state/trigger contracts and the first explicit foreground cycle are
implemented in development source on 2026-08-05. This is not yet the primary
installed user experience or a live Codex/Claude/IDE integration.

## Purpose

AgentGov's existing `next`, `govern start`, `govern check`, `govern finish`,
Monitor, and handoff commands remain deterministic development and recovery
primitives. The automatic product path needs stable internal contracts that can
use those cores without making a coding-agent vendor, a hidden daemon, or a
Dashboard the governance authority.

This slice introduces two contracts:

- `agentgov.development-state` `1.0`: a read-only projection of the exact active
  task and its validated local event stream;
- `agentgov.development-trigger` `1.0`: a strict vendor-neutral input envelope
  for foreground coding-agent adapters.

## Development state projection

`src/agentgov/development_state.py` maps the current session event stream to
one stage and one recommended operation:

| Stage | Recommended operation | Blocking |
|---|---|---:|
| `active_unchecked` | `check_scope` | no |
| `scope_passed` | `validate_and_reconcile` | no |
| `scope_blocked` | `check_scope` after fixing or reviewing scope | yes |
| `validation_recorded` | `reconcile_completion` | no |
| `needs_evidence` | `validate_and_reconcile` | no |
| `review_ready` | `refresh_dashboard` | no |
| `handed_off` | `rollover` | no |
| `invalid` | `require_human` | yes |

The projection executes nothing and grants no code-change, exception, Git,
merge, or deployment authority. `agentgov next` now consumes this projection
for active-session routing while preserving its existing command-oriented
headless output.

## Adapter trigger contract

The trigger vocabulary is:

- `task.requested`;
- `repository.activated`;
- `implementation.changed`;
- `scope.decision_requested`;
- `scope.decision_recorded`;
- `completion.requested`;
- `validation.completed`;
- `session.reviewed`.

Triggers contain a hashed working-copy correlation value, an adapter identity,
an actor class, optional task identity, and only bounded facts needed by the
trigger type. They reject absolute paths, parent traversal, unknown fields,
cross-event facts, non-human scope decisions, and any consequential authority
flag set to true. Raw prompts, responses, source contents, credentials, and
host paths are not part of the contract.

`scope.decision_requested` and `scope.decision_recorded` are deliberately
separate. A coding agent can request a decision, but only a human-originated
record can carry the decision. Even that record is input to the coordinator;
the trigger envelope alone does not rewrite the admitted task or authorize an
exception.

## Current boundary

Implemented now:

- pure lifecycle state projection;
- strict JSON schemas packaged with the tool;
- strict Python trigger validation;
- privacy-bounded working-copy correlation;
- existing `next` active-session routing backed by the projection;
- Monitor 1.4 Live Sessions and Protection Events read models, with stable
  source-event-derived identity and explicitly unknown resolution;
- `agentgov.foreground-cycle` 1.0 and `agentgov dev`, which run one disclosed
  foreground adapter/coordinator cycle without hand-authored JSON;
- a minimal reference adapter that derives working-copy identity, active task
  identity, and changed paths from repository state;
- automatic scope observation on `implementation.changed`;
- automatic scope check, task-declared pre-approved validation, completion
  reconciliation, and Dashboard refresh on `completion.requested`;
- human-originated `session.reviewed: accepted` handoff without special
  confirmation text in the adapter path;
- fail-closed treatment of missing admission, mismatched working-copy/task
  identity, scope violations, and adapter-reported validation that is not
  AgentGov evidence;
- fixture tests for stages, operations, authority denial, trigger facts, path
  safety, and adapter neutrality.

Not yet implemented:

- explicit cross-event protection resolution links;
- a live coding-agent event transport for Codex, Claude Code, or an IDE that
  invokes the reference adapter automatically during editing;
- task drafting/admission from a natural-language request;
- visual task, scope-decision, and completion cards; the current coordinator
  returns their strict machine-readable gate data;
- a persistent foreground session process; current `agentgov dev` performs one
  event cycle and exits;
- Benefit and Learning views.

## Next slice

Connect one real coding-agent surface to the reference adapter so repository
activation, implementation changes, completion requests, and human review
events invoke `agentgov dev` without the ordinary user composing lifecycle
commands. Add concise task and completion cards while keeping task admission,
material scope, architecture, exception, semantic review, and consequential
authority human-owned.
