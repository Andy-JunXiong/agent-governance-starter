# Disposable Codex-home initialize differential - 2026-08-21

## Purpose and authority

Native proposal review admitted
`p0-disposable-codex-home-initialize-differential-v1` through proposal
`prp-0175f96bf9bb407d8e4f5a3328615e45`, and the product owner separately
started the task. The task permitted exactly one separately approved
user-host Codex App Server startup using a fresh disposable Codex home. It did
not authorize a model turn, retry, repair, home inspection, cleanup, Git
operation, publication, release, deployment, or broader activation.

## Matched preflight

Starter HEAD remained `0bb72f0d062d20e466a1e571bbc841aeea89b4ef`.
The retained remote-free AIRBNB clone remained detached at
`d70615527d9acdde3893ce645d1923606173acf6` with only its two existing binding
changes. Retained Python `3.11.9`, AgentGov `0.3.0rc1`, Codex
`0.149.0-alpha.4`, project configuration, Agent guidance, README, and user
configuration identities matched the preceding diagnostic.

The retained AgentGov executable digest was
`FA2F2CDB39B2199CE4E37D3298123CA412EEF550AB7A35BC22BF1E7E99A3ED0E`,
and the retained Python executable digest was
`21BB438C0D4A6F1F164B9A646F6EE000340185E5871180AEC06DB8D3F07C0082`.
The process-local environment placed the retained runtime first on `PATH`,
used the existing project binding and one-time trust override, assigned a
fresh operating-system temporary directory as `CODEX_HOME`, and removed
`PYTHONPATH` and `ELECTRON_RUN_AS_NODE` from the diagnostic child. No
persistent configuration changed.

## Single differential startup

The fresh disposable home was created without reading or copying the real
user home. The diagnostic started one user-host App Server, sent only
`initialize`, `initialized`, and one `thread/start`, and stopped before
`turn/start`.

Connection initialization succeeded. The only `thread/start` then failed
with the same required-MCP initialize-response closure and `-32603` observed
against the real user home. No `thread/started`, turn, item, prompt, model
payload, Agent response, or tool-call event occurred. Four stderr lines were
classified only as the known shell-snapshot warning; their raw content was not
retained. The exact diagnostic process exited, and the pre-existing Codex,
AgentGov, and Python process counts were preserved.

## Classification

The deterministic outcome is
`DISPOSABLE_CODEX_HOME_REPRODUCED_USER_HOST_INITIALIZE_FAILURE`:

- fresh disposable `CODEX_HOME`: pass;
- App Server connection initialize: pass;
- required AgentGov MCP initialize: fail with reproduced `-32603`;
- thread creation: fail before `thread/started`;
- model turn: not run.

Existing user-home files and persistent user configuration are therefore not
necessary for this failure to reproduce under the matched launch. This result
rules out cleanup or migration of the existing Codex home as a justified next
repair. It does not identify the remaining cause. The remaining boundary is a
home-independent difference between the passing sandboxed App Server path and
the failing user-host App Server/project-MCP initialization path. Exact
initialize-response code flow, other host-process state, and possible
background network behavior remain unknown.

## Privacy and preservation

The disposable home is retained without cleanup or content inspection. Its
absolute path, generated names, contents, session identity, and any internal
metadata were not retained. The real user configuration digest and byte
length remained unchanged. Retained runtime and clone identities, Starter
HEAD and index, remotes, credentials, and pre-existing processes were not
changed.

This record contains no raw protocol response, prompt, transcript, source
content, credential, private data, absolute host path, process identity, raw
command line, complete environment value, or external-model payload. No
retry, repair, dependency download, cleanup, commit, push, publication,
release, deployment, or broader activation occurred.

## Validation and advisory review

The focused documentation suites passed 38 and 13 tests. The exact supported
Python 3.11.9 repository suite passed all 946 tests with 3 platform-limited
skips in 254.303 seconds. Task governance returned
`PASS=3 WARN=1 FAIL=0 ADVISORY=3`, repository governance returned
`PASS=26 WARN=2 FAIL=0 ADVISORY=4`, and `git diff --check` passed. Scope
reconciliation admitted the 4 exact task-owned paths and retained 16 failures
for explicitly excluded prior-task or user-owned paths; no exception or
ownership transfer was inferred. The task JSON parsed, and bounded absolute-
host-path and recognized credential-marker scans returned zero matches.

This fully specified diagnostic did not start an alignment journey, so the
distinct bounded current-Agent advisory pass does not claim native self-review
completion. Requirement, architecture, scope, implementation, and security
review found the one-variable comparison, narrow inference, admitted-path
ownership, validation, privacy, and stop boundaries consistent. It retained
the exact initialize-response code flow, complete child environment,
home-independent host state, disposable-home contents, and possible
background network attempts as unknown.

The current callable governance inventory did not expose
`agentgov_task_completion_record`; no completion record was fabricated. The
review granted no task, scope, exception, repair, Git, publication, release,
deployment, or external authority.
