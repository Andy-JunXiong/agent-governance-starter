# Shell-aware validation execution repair

Date: 2026-08-31

## Governed scope

The product owner first selected a separate shell-execution repair instead of
combining it with the unresolved excluded-path completion policy. A second
alignment decision retained the existing `validation_commands` string contract
and selected explicit platform-native shells. Native proposal
`prp-ecb7aa64b869471e8dbe3a98e839930e` admitted
`governance/tasks/p0-shell-aware-validation-execution-v1.json`; the owner then
entered exact `REPLACE` for the new development session.

The admitted implementation paths are the validation runner, its focused test
module, the durable fresh-evidence specification, two user workflow guides,
`STATUS.md`, this dated record, and the task record. Existing instruction
comparison artifacts, `tests/test_user_documentation.py`, `.agentgov`, and
`.codex` are explicitly outside this task and were preserved.

## Implementation

- Replaced `subprocess.run(..., shell=True)` with explicit argv construction.
- Windows uses `powershell.exe -NoLogo -NoProfile -NonInteractive
  -EncodedCommand`. The payload is UTF-16LE/Base64 so PowerShell assignments,
  quotes, Unicode, and separators survive Windows process argument parsing.
- The Windows suffix captures the command result immediately: success exits
  zero, native failures retain their nonzero exit, and other PowerShell
  failures exit one.
- Existing admitted Windows strings beginning with a quoted path-like
  executable receive only an execution-time PowerShell call operator. Their
  task text and SHA-256 command identity remain unchanged; `cmd.exe` is not
  used.
- POSIX uses explicit `/bin/sh -c` with the original string.
- Unsupported platforms and missing shells raise a bounded `EvidenceError`
  before validation evidence or events are written.
- Existing timeout, first-failure stop, transient raw output, persisted output
  digests, snapshot mutation checks, and authority denial were retained.

## Validation evidence

The first focused run exposed PowerShell's requirement for the call operator
when invoking a quoted absolute executable. After correcting the focused
fixtures, 21 tests passed with one POSIX-only skip. A first complete repository
run then reported 12 failures, all from historical test fixtures storing that
same quoted-executable Windows shape. No production evidence, handoff, session,
or MCP contract failed independently of that parse boundary.

The bounded compatibility adapter was added in the runner rather than editing
the 12 fixtures outside task scope. The four affected modules then passed all
81 tests with one POSIX-only skip. The final complete repository run passed all
1,129 tests with six platform-limited skips. The final focused module contains
22 tests: Windows argv/encoding, environment assignment and quoting, native
exit 7, PowerShell exit 1, quoted-executable compatibility, unsupported and
missing shell failure, POSIX argv and platform-gated outcomes, privacy,
snapshot freshness, and first-failure behavior.

Post-documentation evidence and user-documentation validation passed all 86
tests with one POSIX-only skip. Task governance returned
`PASS=3 WARN=1 FAIL=0 ADVISORY=3`; repository governance returned
`PASS=26 WARN=2 FAIL=0 ADVISORY=4`. `git diff --check` and the bounded
secret-like assignment scan passed. Raw scope returned `PASS=8 FAIL=5` because
it preserves the five pre-existing paths explicitly excluded by this task.

Distinct native current-Agent self-review
`srv-8b63ec4d375b689fa1c1a5630cd02e5a` found no requirement, architecture,
implementation, privacy, or authority expansion. It retained POSIX real-host
behavior, external consumer interpretation, hostile-local-actor protection,
adoption, time savings, and business value as unknown, and identified the
excluded-path completion question as a separate product review.

The native completion tool was not exposed in this Codex session. The first
repository fallback invoked with an explicit task but no base correctly
reported missing evidence and ran no command. The active-session fallback then
used its recorded comparison base and created evidence
`evd-108a26df4e044d18a919f7d06c73033d`: all five declared commands exited zero,
the validation outcome was `passed`, and mutation reasons were empty. Final
completion remained `needs_evidence` only because reconciliation retained the
five pre-existing excluded paths as visible scope failures. A final fallback
after this closeout edit leaves its generated reference only in local
`.agentgov` state to avoid a further self-invalidating tracked edit.

## Preserved limits

This repair does not sandbox project commands, migrate task commands to
structured metadata, reinterpret Windows commands through `cmd.exe`, change
excluded-path scope or completion policy, modify prior task decisions or
evidence, or authorize commit, push, release, publication, or deployment.
POSIX real execution remains CI/platform evidence rather than an observation
from this Windows host. External adoption, prevented incidents, time savings,
and business benefit remain unknown.

## Product connection

The repair builds directly on fresh validation evidence and completion
reconciliation. It removes the shell mismatch that prevented a PowerShell-form
task command from producing governed evidence. The next product review is the
separate excluded-path completion question, because a reliable command runner
lets that policy be evaluated without conflating it with process-launch
failure. That next review is not authorized implementation.
