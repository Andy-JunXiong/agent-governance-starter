# Disposable automatic-journey rehearsal v2 - 2026-08-23

## Outcome

`STOPPED_AFTER_UNTRUSTED_PROJECT_FALLBACK`

The product owner selected one local synthetic baseline commit through resolved
alignment journey `mcpj-1cca8f6aaeba41f39c58c016d2e18623`. Native proposal
review admitted exact task
`p0-disposable-automatic-journey-rehearsal-v2` through proposal
`prp-5865e9f05bcb4b6397878c251d833176`, and the product owner separately
started that task.

The corrected baseline requirement passed. The measured session then exposed a
different host boundary: Codex did not apply temporary project trust to the
interactive session. It disabled project-local configuration, started one
model turn without AgentGov, and persisted a trust entry in user-level Codex
configuration. The Agent interrupted that turn, exited the same session, and
did not retry.

## Prepared synthetic boundary

A fresh operating-system temporary directory received a current
development-source governance scaffold plus a tiny synthetic Harbor Notes
module, one focused unit test, a bounded validation command, adapted
`AGENTS.md` instructions, and project-local MCP configuration. No existing
consumer content or non-synthetic data was used.

Exactly one local preparation commit established the baseline. Deterministic
checks confirmed one commit, a clean worktree, zero remotes, 37 tracked
baseline files, a parseable project configuration, and a passing initial unit
test. The temporary repository remains retained. Its generated name, absolute
path, commit identity, source content, and validation output are not retained
here.

Readiness evidence identified Codex CLI `0.146.0`, development AgentGov
`0.3.0rc1`, and AgentGov Adapter `1.6.0`. A direct no-model MCP handshake
with form elicitation declared returned exactly eight tools:

- the three alignment tools;
- the two current-Agent self-review tools;
- native task completion recording;
- native task proposal review;
- native drift review recording.

Codex configuration diagnostics recognized one locally consistent stdio MCP
server for the synthetic project. Official Codex configuration guidance was
reviewed for trusted-project loading and the stdio MCP command,
working-directory, environment, required-server, timeout, and tool allow-list
fields.

## Measured session and first deviation

Exactly one fresh external Codex interactive session was launched with one
ordinary bounded repository-change request. The request did not name AgentGov,
MCP, governance tool names, protocol objects, task files, special confirmation
words, or a lifecycle command sequence.

Before the model turn, the terminal required one compatibility confirmation
because `TERM=dumb`. Codex then displayed a project-trust decision. The
interactive session did not load the project-local configuration; its visible
state said that project config, hooks, and exec policies were disabled until
the project was trusted.

The same session subsequently started one model turn without the AgentGov MCP
tools. The turn performed bounded read-only repository inspection and stated
that it would verify governance authorization before editing. No proposal
tool call, native form, consumer task, source edit, validation run, completion
record, or consumer self-review occurred. The Agent interrupted the turn and
used the local quit command to end the session.

Post-session checks found the temporary repository still clean with its one
baseline commit, zero remotes, and no consumer task beyond the initializer's
tracked placeholder. They also found that Codex had persisted the temporary
project as trusted in user-level configuration even though the running session
had not loaded the project MCP. That retained-runtime mutation is disclosed
and was not removed because this task forbids repair, cleanup, or another
attempt after the first deviation.

The first deviation is:

```text
stage: external_session_startup
code: project_trust_not_effective_for_started_session
expected: project-local required AgentGov MCP loaded before the only model turn
observed: project configuration disabled, one ungoverned read-only model turn started, and a user-level trust entry persisted
```

## Interaction and friction record

| Measure | Observed result |
| --- | --- |
| Product direction decisions | 1 alignment selection |
| Native Starter task-admission decisions | 1 |
| Separate Starter task take-up | 1 |
| Preparation baseline commits | 1 local commit in the remote-free temporary repository |
| External Codex sessions | 1 |
| Model turns | 1, interrupted |
| Native consumer forms | 0 |
| Consumer AgentGov tool calls | 0 |
| Consumer tasks admitted | 0 |
| Consumer implementation writes | 0 |
| Consumer validation runs | 0 |
| Consumer completion records | 0 |
| Consumer self-reviews | 0 |
| Terminal compatibility confirmations | 1 |
| Project-trust prompts | 1 |
| Session-control interruptions | 2 |
| Local quit commands | 1 |
| Model-session retries | 0 |
| Session restarts | 0 |

The project-config warning and the interrupted session were visible in the
current human surface. No consumer Monitor protection event or
protection-resolution link was produced because the AgentGov MCP was absent
from the model turn. Protection-event resolution visibility therefore remains
`unknown`, not passed.

## Benefit and Learning evidence

- `observed_fact`: allowing one local baseline commit removed the v1
  Git-snapshot contradiction and made the synthetic repository eligible for
  no-model scope and completion preflight.
- `observed_fact`: the direct Adapter handshake exposed all eight intended
  tools, while the interactive session disabled project-local configuration.
- `observed_fact`: the ungoverned turn made no repository changes before it
  was interrupted.
- `observed_fact`: the interactive trust path created one user-level Codex
  trust entry despite not activating project MCP in that session.
- `supported_inference`: future automatic rehearsals need an explicitly
  reviewed trust-lifecycle design before the model turn, not only a valid
  project MCP file. This does not prove avoided harm or causal benefit.
- `unknown`: whether a pre-trusted fixed fixture, separately authorized
  temporary trust lifecycle, or App Server path best preserves native form
  visibility without retained user-state drift.
- `unknown`: native proposal quality, separate consumer take-up, completion
  recording, current-Agent review, protection links, end-to-end interaction
  burden, broader usefulness, causal benefit, ROI, and real-consumer usability.

## Preservation and authority boundary

The temporary repository remains retained, remote-free, clean, and at its
single synthetic baseline commit. No existing consumer repository, Starter
product source, dependency, publication, release, deployment, CI, remote Git
state, or production system changed during the measured session. No raw
request, response, transcript, source content, validation output, credential,
private data, temporary absolute path, external session identity, or
model-private reasoning is retained in this record.

The user-level trust entry is an unresolved retained-runtime mutation. This
task grants no authority to remove it, edit user configuration, clean up the
temporary repository, retry the session, or reinterpret the result as a
successful governed journey.

This rehearsal does not satisfy the independent automatic-experience gate and
is not a fresh uncoached human pilot. Another attempt requires a separately
reviewed trust-lifecycle direction and a new admitted task.

## Starter validation

All 45 focused user-documentation tests passed. The supported Python 3.11 full
suite passed all 997 tests with 3 platform-limited skips in 147.440 seconds.
Task governance reported `PASS=3 WARN=1 FAIL=0 ADVISORY=3`, and repository
governance reported `PASS=26 WARN=2 FAIL=0 ADVISORY=4`.

Scope reconciliation admitted all 6 v2 task-owned paths. It retained three
failures for the pre-existing, explicitly excluded, and untouched user-owned
`.codex/config.toml` plus the v1 task and experiment record from the preceding
completed slice. No exception, ownership transfer, or v2 mutation of those
paths is inferred.

The v2 task JSON parsed, the bounded retained-evidence privacy scan returned
zero matches, and `git diff --check` passed. The current callable Starter
governance inventory does not expose `agentgov_task_completion_record`, so no
Starter completion record is fabricated.

Native current-Agent self-review
`srv-ee553812dfda1bd52e6c657b0ef400b6` completed as a distinct separate pass.
It found the admitted baseline correction, trust-boundary stop, one-session
limit, zero consumer writes, task-owned scope, retained-evidence privacy,
validation, disclosed user-state mutation, and denied cleanup authority
consistent. It retained the best future trust design, same-host readiness
proof, later temporary-resource lifecycle, and effect of the persisted trust
entry as explicit unknowns. The review is advisory and grants no cleanup,
replay, Git, publication, release, deployment, or external authority.
