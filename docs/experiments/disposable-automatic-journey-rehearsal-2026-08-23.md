# Disposable automatic-journey rehearsal - 2026-08-23

## Outcome

`BLOCKED_BEFORE_GIT_BASELINE_AND_MODEL_SESSION`

The product owner selected one independent non-NYC automatic-journey
rehearsal through resolved alignment journey
`mcpj-2c53eb797bb04cf9b3665c635a50d0dd`. Native proposal review admitted exact
task `p0-disposable-automatic-journey-rehearsal-v1` through proposal
`prp-e2fda91144164dd0b569328f668193c2`, and the product owner separately
started that task.

The rehearsal stopped during deterministic readiness review. No external
Codex model session, ordinary work request, native consumer proposal form,
consumer task take-up, implementation, validation, completion record, or
consumer self-review ran.

## Prepared synthetic boundary

A fresh operating-system temporary directory received a governance scaffold
from the current development source. It contained no consumer data and was
not an existing consumer repository. Scaffold creation completed but reported
47 unresolved adaptation placeholders. The directory was retained without
cleanup, and its generated name and absolute path are not recorded here.

Starter HEAD was
`02d4a954fa8c784a207cf68b36a30e302587cc7c`. Read-only identity checks observed
development AgentGov `0.3.0rc1` and Codex CLI `0.146.0`. The bare `codex`
PowerShell shim was blocked by local script-execution policy; the read-only
identity check then used `codex.cmd`. This is command-discovery friction, not
a model-session retry.

Official Codex configuration guidance was reviewed for project-scoped trust,
stdio MCP `command`, `cwd`, `env`, required-server behavior, and tool
allow-list fields. No temporary project MCP configuration was written because
the earlier Git-baseline gate failed.

## First deviation

The admitted task requires the temporary repository to remain uncommitted and
states that no commit occurs. The same task expects native task completion and
a clean synthetic baseline. Current AgentGov scope and completion contracts
require a valid Git `HEAD` commit and a commit-identified comparison base:

- scope inspection resolves the worktree root and runs `git rev-parse HEAD`;
- canonical snapshots require a commit-shaped `snapshot_head_sha` and
  `comparison_base_sha`;
- completion tests create a baseline commit before recording evidence.

Creating that baseline commit would violate the exact admitted task. Omitting
it would make the requested completion trace ineligible. The first deviation
is therefore:

```text
stage: deterministic_readiness
code: task_contract_baseline_conflict
expected: committed Git baseline available to native scope and completion
observed: exact task prohibits every commit and requires the target to remain uncommitted
```

The Agent did not reinterpret “no commit” as “no post-baseline commit,” mutate
the admitted task decision, or use a repository without a valid baseline.

## Interaction and friction record

| Measure | Observed result |
| --- | --- |
| Visible human governance decisions | 1 native task-admission selection |
| Separate human take-up | 1 explicit start instruction |
| External model sessions | 0 |
| Model turns | 0 |
| Native consumer forms | 0 |
| Manual repository preparation writes | 2: temporary directory creation and scaffold initialization |
| Interruptions | 1 deterministic preflight stop |
| Model-session retries | 0 |
| Restarts | 0 |

Protection was visible as the fail-closed stop reported in the current human
surface. No automatic Monitor protection event or cross-event resolution link
was produced because no governed consumer session started. Protection-event
resolution visibility therefore remains `unknown`, not passed.

## Benefit and Learning evidence

- `observed_fact`: deterministic contract review exposed the incompatible
  baseline and no-commit requirements before any external model session.
- `observed_fact`: no existing consumer, product source, user-owned `.codex`
  state, dependency, retained runtime, remote, or external Git state changed.
- `supported_inference`: the fail-closed workflow prevented this run from being
  mislabeled as a complete automatic journey. This does not prove avoided
  harm or causal product benefit.
- `learning`: a future proposal must either explicitly permit one local
  synthetic baseline commit before the measured request or point to an
  already committed disposable fixture. This is product-review input only and
  grants no repair or replay authority.
- `unknown`: native form presentation in this CLI, autonomous tool selection,
  separate take-up behavior inside the consumer session, completion recording,
  protection resolution links, end-to-end interaction burden, broader
  usefulness, causal benefit, ROI, and real-consumer usability.

## Preservation and authority boundary

The temporary directory remains retained and was never made into a usable Git
baseline. No external Codex session, dependency download, product-source
change, existing-consumer mutation, runtime change, cleanup, commit, push,
pull request, publication, release, deployment, CI change, or production action
occurred. No raw prompt, response, transcript, source content, validation
output, credential, private data, temporary absolute path, or model-private
reasoning is retained in this record.

This failed rehearsal does not satisfy the independent automatic-experience
gate and is not a fresh uncoached human pilot. Another attempt requires a new
human-selected and separately admitted task; this record authorizes none.

## Starter validation

All 44 focused user-documentation tests passed. The supported Python 3.11 full
suite passed all 996 tests with 3 platform-limited skips in 153.967 seconds.
Task governance reported `PASS=3 WARN=1 FAIL=0 ADVISORY=3`, and repository
governance reported `PASS=26 WARN=2 FAIL=0 ADVISORY=4`.

Scope reconciliation admitted all 6 task-owned paths and retained one failure
for the pre-existing, explicitly excluded, and untouched user-owned
`.codex/config.toml`; no exception or ownership transfer is inferred. The task
JSON parsed, the bounded retained-evidence privacy scan returned zero matches,
and `git diff --check` passed. A metadata-only preservation check found the
temporary directory still present with 31 files and no `.git` directory; it
did not inspect file contents.

Native current-Agent self-review
`srv-a419b87ea09ed7659242d53cf3992ba3` completed as a distinct separate pass.
It found the requirement-level stop, Git-snapshot architecture evidence,
task-owned repository scope, cross-document result, validation, privacy, and
authority boundaries consistent. It retained the intended interpretation of
“uncommitted,” possible future support for unborn Git repositories, native
consumer behavior, and the temporary directory's later lifecycle as unknown.
The review is advisory and grants no correction, retry, Git, publication,
release, deployment, or external authority.

The current callable governance inventory does not expose
`agentgov_task_completion_record`, so no Starter completion record is
fabricated.
