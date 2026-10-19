# Foreground runtime maintenance - 2026-10-19

Task: `p0-runtime-foreground-install-v1`.

Current result: paused for the day at the human's request. The first operator
invocation stopped before installation with `UnicodeDecodeError`. The encoding
repair passes preflight and regression checks, but the renewed native review
request was rejected because the journey had already started self-review.
No replacement readiness receipt exists; installation remains blocked.
No live package replacement, existing-process termination, configuration
change, client restart, rollback of the live installation or cleanup occurred.

The first readiness receipt was created after validation and native advisory
review. It is now preserved as `ready-before-encoding-repair.json`; no current
`ready.json` authorizes the corrected helper to proceed. Historical raw-file
SHA-256 identities at the first handoff (superseded for repaired helper files):

| Maintenance-root file | SHA-256 |
| --- | --- |
| `maintain.py` | `2c920e15d736b3b38430817a80219acc32c18f5c682517e6a8917b89de295c14` |
| `protocol_probe.py` | `44b59ff642999dc14b64c1c4e8771d7d903721677051715b7eb1d34fe45055d0` |
| `test_maintain.py` | `4df33e4ec8a7bacca753f867a5911862274fd429f7d584e3818505f85954c5c0` |
| `ready.json` | `ea007b42d9084e1a74c124aecf89bb1b6dcdbbd5e1ec9c227c209b44a027942c` |

## Bound identities

- Human-resolved direction: `mcpj-c21aa3e2cada41919a227d20a7f3a7b9`.
- Native task admission succeeded; task digest:
  `sha256:af1a58c09fd218545f4ec5af66e46b39d5ea3befe680145fc2300c5d0c9ae977`.
- The human separately entered `REPLACE` in the visible terminal. The active
  task started at `2026-10-19T08:25:46.177Z`, against Git base
  `72175984801fa7a83653f1dc5a8eb8d33d1c4ba7`.
- New maintenance temporary child: **`agv-21b9dbfa`**. Its private owner record
  binds this task, repository and original recovery locator.
- Read-only recovery child: **`agv-fa6298a1`**, still owned by
  `p0-runtime-recovery-materials-reprepare-v1`. Its original owner, snapshot,
  staging and wheel are preserved.
- Recovery-manifest SHA-256:
  `5d3b050f83f665c2ff26409a36a9082b4bd9cd14626ea49b4bf41e326f7f40ed`.
- Candidate wheel: `agent_governance_starter-0.3.0rc1-py3-none-any.whl`;
  SHA-256 `35f6914712616edc84728f5b2b12c1851d6e72c688e765d1b170ca52289fb9aa`.
- Source: 188 manifest inputs; path digest
  `sha256:23a850bd924f45a8888fcfe7cbc591ed1edfb30c1735810d60a5833bc210fb54`;
  content digest
  `sha256:f222e756b70a8f57ae5ef49db95b257729ad515cdf8066400ab67bf483fb8162`.

## Foreground maintenance behavior

`maintain.py preflight` verifies the task, active-session binding, both root
owners, complete original and backup file sets, configuration, launcher,
source and wheel identities. It reports process occupancy without installing.

`maintain.py install` requires a real terminal and exact human `INSTALL`.
It checks identities and process occupancy before prompting, and repeats
them after confirmation. It also checks the reviewed helper hashes, Git
base and original task-start scope baseline. A completed validation/review
receipt is required. No timer, daemon, scheduled task or automatic retry runs.

The process check obtains a fresh Windows process catalog and checks paths
and command arguments for the exact environment and exposed launcher.
Missing path or command-line visibility for candidate runtime executables
blocks installation. Unrelated protected Windows processes may have hidden
fields; this is a bounded target-runtime check, not universal process-memory
inspection. Process counts are transient observations, not maintenance locks.

Installation uses the existing environment's Python and the exact wheel,
with `--force-reinstall --no-deps --no-index --no-compile`, isolated pip,
disabled user configuration and no index credentials. It verifies all 78
Python modules and 107 shared data files, package `0.3.0rc1`, Adapter `1.7.0`,
protocol `2026-07-28` and no runtime dependencies. The exposed launcher is
refreshed only if the verified installed inner launcher differs. Project
configuration and pipx metadata must remain byte-identical.

The fresh-process probe sends five synthetic requests: initialization,
discovery, invalid exploration, correction, and exploration with a remaining
question. It checks rejection diagnostics, corrected state and non-granting
authority. Output and duration are bounded. Only its own test subprocess may
be stopped on failure; it never terminates an existing host or MCP process.

If installation or its checks fail, recovery rechecks the bound backup,
target paths and zero-process condition. It restores the original file set
and exposed launcher only within those exact targets. A failed recovery
precondition stops further writes and retains evidence. Fixture restoration
tests are not proof that restoration of the live installation has occurred.

## Human maintenance steps

Historical first-handoff procedure. Do not execute it after this closeout:
readiness is invalid and the authorized commit advances HEAD beyond the
helper's bound comparison base. Resume only after the governed review and
comparison-base prerequisites are re-established, without editing old task
decisions or fabricating review completion.

1. Keep this repository and both temporary roots unchanged. Confirm that
   `ready.json` exists in the maintenance root and that the task has a recorded
   advisory review. Do not modify the receipt or bypass a failing check.
2. Identify and close only the affected AgentGov connections using the host's
   normal controls. Existing MCP process chains share a Codex parent; process
   ancestry does not establish per-conversation ownership. If ownership is
   unclear or other work needs those connections, defer installation.
3. Keep an independent PowerShell terminal available. The task-start terminal
   can be used. Do not close or restart unrelated coding sessions. No command
   here disconnects the host or changes persistent configuration.
4. After the affected connections have closed, explicitly invoke:

   ```powershell
   py -3.11 -B (Join-Path ([IO.Path]::GetTempPath()) 'agv-21b9dbfa/maintain.py') install
   ```

   The prepared independent PowerShell window provides the equivalent
   `Install-AgentGovNow` function. It is defined but not executed on window
   startup; typing the function name is the explicit foreground invocation.

5. The program exits if any prerequisite fails. If it reaches the reviewed
   prompt, enter `INSTALL` to perform the foreground operation. Keep the
   terminal open until it reports the result. A result file prevents an
   unreviewed repeated installation.
6. Reconnect the intended client only after the terminal reports
   `INSTALLED_FRESH_PROCESS_VERIFIED_ACTIVATION_PENDING`. Return to this chat
   for evidence reconciliation and explicit activation verification. Do not
   describe a successful subprocess probe as current-client activation.
7. If the result is `FAILED_ORIGINAL_RESTORED`, the old runtime was restored
   and must be reviewed before retry. If it is
   `FAILED_MANUAL_RECOVERY_REQUIRED`, retain both roots and stop; do not
   improvise deletion or another install.

The original foreground alignment journey is process-local and may be lost
on disconnection. Its pre-maintenance advisory review must complete before
the handoff. A later lost required journey or governance call is reported as
a bounded failure, never fabricated as completed. There is no native
task-completion tool on the current connection.

## Evidence and limits

Private host locators, helper code and raw local validation output remain in
`agv-21b9dbfa`. The repository retains only normalized identities and outcomes.
The dated development log owns validation and advisory-review checkpoints.
All six declared checks passed; 134 repository tests and 15 helper tests ran,
with three and one platform skips respectively. Native separate-pass advisory
review `srv-3c282bdd44c3e8d0d4d2fa370b9e930d` completed for the prepared
handoff. A five-request protocol probe passed against source only.
Installation and client activation are unfinished. No new product capability
or published release is claimed; the next product feature is not yet decided.

## Operator retry diagnosis and encoding correction

The operator reported `STOPPED_WITHOUT_INSTALLATION` / `UnicodeDecodeError`.
Read-only checks found no `runtime-result.json`, no pip output logs, unchanged
Adapter 1.6.0 and coherent original/backup hashes. The prior helper hashes
still matched the original readiness receipt; this was not file drift.

A synthetic Windows PowerShell CP936 output fixture reproduces rejection by
the helper's unconditional UTF-8 decoding. The process catalog now serializes
explicit UTF-8 JSON to base64 in PowerShell, then decodes validated ASCII
base64 in Python. This preserves Chinese paths across console encodings
without dropping or replacing characters. Malformed encoding stops with a
normalized diagnostic. CP936 and UTF-8 fixture checks pass; 17 helper tests
ran with one platform skip. Fresh live preflight again verified all bound
identities and found six matching runtime processes.

The old receipt was invalidated before editing. The previous native review
is historical evidence for the initial helper, not a claim that this repair
has received a renewed native review. Do not retry installation until that
boundary is resolved and a fresh receipt is created.

## End-of-day stop and retained correction

The renewed self-review call returned
`self-review has already started for this journey`, with error code
`mcp_invalid_request` and `retryable=false`. This is a concrete governance
stop, not proof that the repaired helper passed native review. The user then
requested stopping work and a separate documentation/Git closeout. No runtime
work, readiness renewal, process control or cleanup followed that request.

Current corrected temporary-file SHA-256 identities are retained for later
fresh verification; these hashes are not installation authority:

| File | SHA-256 |
| --- | --- |
| `maintain.py` | `446917530b4d15260dd078bfa72958b9c338d4dd579e97d5dd77348787ee603d` |
| `test_maintain.py` | `81f334a1b53d78605e2f81d54c76ef976e9dc78ae4d65f877bdf3b79e3575279` |
| `protocol_probe.py` | `44b59ff642999dc14b64c1c4e8771d7d903721677051715b7eb1d34fe45055d0` |

Closeout inspection found `ready.json` absent, its historical predecessor
retained, and no installation result file. Original recovery child
`agv-fa6298a1` and maintenance child `agv-21b9dbfa` remain local only. Their
availability and integrity must be checked again on resumption. Committing
the evidence does not repair the old session baseline or approve installation.
