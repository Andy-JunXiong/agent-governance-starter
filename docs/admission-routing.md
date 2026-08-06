# Risk-based admission routing and friction budget

AgentGov observes development work without forcing every user message through
the same manual gate. Development source separates classification, standing
delegation, task admission, and session start.

The intended principle is simple: all work may be routed, but only work that
crosses a real risk or authority boundary should interrupt a human.

## Routes

| Route | Used for | Human interruptions | Repository effect |
| --- | --- | ---: | --- |
| `observe_only` | questions, explanations, status queries, read-only diagnosis | 0 | none |
| `continue_active` | ordinary iteration inside the exact locally verified active task | 0 | none from routing |
| `fast_track` | bounded low-risk proposal inside admitted standing policy | 0 | optional exclusive task creation |
| `human_review` | low-risk proposal outside delegation or with policy uncertainty | at most 1 | none until reviewed |
| `full_review` | ambiguity, unknown scope, architecture, dependency, auth, security, data, destructive, external, infrastructure, deployment, public API, or governance-policy change | 1-2 | none until reviewed |

`observe_only` authorizes no repository write. If a read-only diagnosis turns
into a request to fix something, the fix is a new repository-change request and
must be routed again.

`continue_active` does not trust a task name supplied by an Agent. AgentGov
loads the local session pointer, validates the admitted task, and compares the
exact task ID and digest. Material change flags still force full review.

## Standing policy

`agentgov.admission-routing-policy` 1.0 is the only source of fast-track
delegation. It declares:

- allowed and denied path prefixes;
- allowed validation-command prefixes;
- maximum include, exclude, validation, risk, and assumption counts;
- no unknowns and the complete non-fast-track material-risk set;
- zero-interruption budgets for observe, continue, and fast-track routes;
- whether non-interactive low-risk task creation is delegated;
- denied session, code, scope, exception, Git, deployment, and release authority.

Fast-track requires the policy to be admitted by its named human owner,
Git-tracked, and unchanged relative to `HEAD`. An untracked, draft, paused, or
dirty policy routes to human review. The portable template deliberately ships
as `draft` with fast-track disabled.

Git cleanliness and the policy's owner declaration are auditable attestations,
not cryptographic proof of who authored a commit. Repositories still need
human-controlled review and protected Git transitions for policy changes.

## Structured request

The host-side Coding Agent creates `agentgov.work-request` 1.0 without passing
the raw prompt to Core. It declares exactly one request class, every material
characteristic as a boolean, privacy boundaries, and zero authority. A new
repository change embeds `agentgov.task-proposal` 1.0; no-write requests embed
no task or proposal.

Agent-supplied classification is not authority. Fast-track exists only where a
clean human-owned policy independently delegates the exact scope, validation,
and risk envelope. Unknowns must be declared and force full review. Scope and
evidence checks continue after admission.

## CLI fallback and Adapter API

Preview one deterministic route without writing:

```powershell
agentgov route request path/to/request.json `
  --policy governance/admission-policy.json `
  --repository .
```

Use `--format json` for an Adapter-readable `agentgov.admission-route` 1.0.
The result carries stable request/policy digests, reason codes, friction budget,
optional task plan, and denied authority.

Only a `fast_track` route may be applied non-interactively:

```powershell
agentgov route request path/to/request.json `
  --policy governance/admission-policy.json `
  --repository . `
  --apply-fast-track
```

Apply reloads the policy, verifies its digest and Git cleanliness, rebuilds the
route, rechecks the exact task digest and exclusive target, and creates only
the compact task. It does not create `.agentgov` session state, append an
event, execute validation, modify code, or authorize downstream actions.

For a planned low-risk `human_review`, the reference surface can proactively
present one numbered choice instead of requesting a special confirmation word:

```powershell
agentgov route request path/to/request.json `
  --policy governance/admission-policy.json `
  --repository . `
  --prompt-human
```

The complete prompt is displayed before input. One selection approves the
exact task, requests changes, or rejects it; no free-text rationale is
required. Approval revalidates the route, prompt, result, task digest, and
exclusive target before creating only the reviewed task. A headless process
cannot use this interactive reference path. The exact `ADMIT` proposal flow
remains a diagnostic and recovery fallback. `full_review` cannot be reduced to
this low-risk single selection and stops before repository modification.

## Coding-agent hosts

The portable `requirement-admission` Skill now performs this classification
before producing a task proposal. Missing-task cards advertise
`agentgov.work-request` 1.0 and the `route_work_request` action.

Codex `UserPromptSubmit` no longer sends every prompt to Core as
`task.requested`. The Hook discards the prompt and returns bounded routing
context: no-write work needs no task; a repository change must produce the
structured request before modification. This is context guidance because
current Codex Hooks cannot record arbitrary custom decisions.

Every real human gate now also produces `agentgov.human-decision-prompt` 1.0 in
the Coding Agent response. It includes the reason, recommendation, option
effects, one-selection rule, and denied display authority. A trusted host
records `agentgov.human-decision-result` 1.0, bound to the exact prompt and
source digests. Scope and completion selections map only to their existing
Core events; task approval maps only to the exact reviewed task plan.

Other Coding Agent hosts can bind the same contracts without changing Core.
Hosts with a native button or choice surface should render it proactively and
return one structured option ID. Hosts without that capability may display the
prompt but cannot claim a recorded decision.

## Efficiency claim boundary

The numeric budget measures expected human interruptions, the dominant
blocking round trips in this workflow. It does not yet record wall-clock
time-to-start or prove that an Agent classified semantic intent correctly.
Those are observational product metrics for a future independent rehearsal,
not facts inferred by this static contract.
