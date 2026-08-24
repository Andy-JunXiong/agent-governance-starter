# Reusable foreground STDIO controller v1 - 2026-08-24

## Outcome

`STOPPED_AT_WORKTREE_WIDE_SCOPE_VALIDATION`

Alignment journey `mcpj-b77dbda52f914a6584640733541723fa` records the
product owner's selection of a reusable fixture-tested controller. Native
proposal review admitted exact task
`p0-reusable-foreground-stdio-controller-v1` through proposal
`prp-ca0bc405c04044d9a45acc9ecc808f42`, and the product owner separately
instructed the Agent to execute it.

## Implemented boundary

The repository-internal controller lives only under
`scripts/foreground_stdio`. Its programmatic interface accepts an explicit
argv, existing working directory, finite ordered JSON messages, explicit
limits, optional environment, and standard-error policy. It always launches
with `shell=False` and has no public command-line or installed-package entry.

For every outbound request with an ID, the controller waits for the exact
typed response ID. Bounded notifications may intervene. Duplicate, missing,
mismatched, and unexpected responses are reported without retaining their raw
identities. Input closes after the declared sequence. Step, overall,
message-count, stdout-byte, stderr-byte, retained-notification, and shutdown
limits are explicit.

The result contains only its normalized outcome, counts, booleans, bounded
method names, response or limit categories, termination facts, and one timing
bucket. It does not contain raw argv, absolute paths, environment values,
process identifiers, request or response payloads, stdout, or stderr. Timeout
recovery calls terminate and then, if required, kill only on the exact direct
child object. It performs no process enumeration or process-tree operation.

## Fixture evidence

The inert standard-library fixture simulates normal responses, notifications,
early or nonzero exit, missing and wrong responses, duplicate responses,
malformed JSONL, delay, stdout overflow, message overflow, standard error, and
post-input linger. It opens no network connection and imports no AgentGov,
Codex, MCP, or model component.

All 16 fixture-backed tests pass. They cover:

- ordered success, exact typed response matching, and observed input closure;
- bounded and normalized notification method retention;
- shell-disabled launch and normalized spawn failure;
- early exit, missing, duplicate, mismatched, and unexpected responses;
- malformed JSONL, step timeout, overall timeout, and output limits;
- standard-error policy and byte limit, plus nonzero exit;
- direct-child termination and termination-failure classification; and
- absence of private argv, path, environment, and message values in results.

## Validation and preservation

All 16 controller tests and all 54 documentation tests pass. The first complete
supported Python 3.11 baseline after implementation passes all 1083 tests with
4 platform-limited skips in the final 187.333-second run. Task governance reports
`PASS=3 WARN=1 FAIL=0 ADVISORY=3`; repository governance reports
`PASS=26 WARN=2 FAIL=0 ADVISORY=4`; and `git diff --check` passes.

The declared scope command admits all 10 task-owned changed paths plus 8
preserved predecessor paths. It also reports 44 pre-existing paths matching
explicit task exclusions as failures, so its summary is
`PASS=18 FAIL=44 ADVISORY=0`. The checker inspects the whole current worktree
and exposes no task-start comparison baseline. Changing, staging, committing,
stashing, or hiding that excluded work is outside the task. The task therefore
stops at this deterministic validation boundary and is not claimed complete;
the functional controller result is preserved rather than mislabeled as a
completed governance result.

Native current-Agent self-review
`srv-571379960e3db07b6911d4a0ca430186` completed as a distinct advisory pass.
It confirms the fixture-tested implementation, privacy reduction, and exact
direct-child boundary; retains real Codex compatibility as unknown; and
separately reports the scope failure and absent task-start baseline. It is not
independent assurance, an exception, or authority to alter earlier work.
Its scope observation said 8 task-owned paths; direct recount after review
corrected that to 10 task-owned paths plus 8 preserved predecessor paths. The
scope total remains `PASS=18`, and the 44 failures are unchanged.

The task does not change AgentGov Core, Adapter, public CLI, installed package,
release metadata, predecessor tasks or evidence, user Codex configuration,
consumer state, HEAD, or remotes. Earlier worktree changes remain outside this
task. Codex, AgentGov, MCP servers, models, network clients, consumer writes,
Git transport, publication, release, deployment, and cleanup actions are zero.

Real Codex framing and shutdown compatibility, Codex-to-MCP initialization,
ephemeral thread creation, tool discovery through Codex, form and model
behavior, completion handoff, cross-host behavior, causal benefit, and return
on investment remain unknown. This controller is a tested prerequisite, not
proof of those outcomes and not authority to attempt them.
