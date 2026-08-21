# AIRBNB native-completion end-to-end recovery - 2026-08-21

## Outcome

`BLOCKED_BEFORE_MODEL_MCP_INITIALIZATION`

The product owner selected the single end-to-end recovery direction through
resolved alignment journey `mcpj-ae9d3edf5fe34791beacced68b6e59be`. Native
proposal review admitted exact task
`p0-native-completion-airbnb-end-to-end-recovery-v1`, and the product owner
separately started it.

The bounded build and no-model consumer gates passed. The single approved live
Codex launch then failed while its required AgentGov MCP server was
initializing, before a usable thread or Agent turn existed. The attempt stopped
without a repair or replay retry.

## Build-bootstrap evidence

- A fresh operating-system temporary root received an archive of exact Starter
  HEAD `0bb72f0d062d20e466a1e571bbc841aeea89b4ef`, a fresh Python 3.11.9
  environment, and an empty bootstrap cache.
- The staged Adapter, Codex integration, Agent template, Codex MCP template,
  and project metadata hashes matched the Starter worktree.
- One explicitly approved dependency command downloaded only
  `setuptools 84.0.0`, satisfying the declared `setuptools>=69` backend. Its
  wheel SHA-256 is
  `51A52592B3B99E102B609654876BD65F19F999935166D1352678931132B0C670`.
- The staged source then built offline and installed
  `agent-governance-starter 0.3.0rc1`. The AgentGov wheel SHA-256 is
  `DD0ACA8F5030EB0CB3036B6B82CAF00754C80854D2E3B6DABDC58C69EE0D87EC`.
  The installed runtime reported Adapter `1.6.0`, eight form-capable tools, six
  base tools, and `agentgov_task_completion_record`.

No pip upgrade, second dependency download, project-metadata edit, source
repair, current pipx change, or retained-runtime change occurred.

## Consumer binding and no-model evidence

A first local clone command was rejected before object copying by Git's
cross-identity safe-directory check. Its unused target was retained. A second
fresh target used one exact process-local safe-directory exception, detached at
AIRBNB commit `d70615527d9acdde3893ce645d1923606173acf6`, removed its remote,
and began clean.

Only that disposable clone's `.codex/config.toml` and `AGENTS.md` were changed
for the consumer binding. The allow-list gained
`agentgov_task_completion_record`, the server timeout became 1,800 seconds,
the base-tool count became six, and the Agent guidance gained the append-only
completion rule. `git diff --check` passed and the clone retained zero remotes.

Direct no-model MCP initialization from the bound clone reported protocol
`2025-11-25`, Adapter `1.6.0`, eight tools with form elicitation and six
without it. The completion tool exposed only `task_path`. A Codex CLI
no-model list using the exact inline-table worktree trust override then found
the required `agentgov_governance` server with the 1,800-second timeout. The
user-level Codex configuration remained byte-unchanged and contains no
persistent temporary-worktree trust entry.

## First live deviation

The product owner explicitly approved one interactive Codex launch using the
fresh runtime on process-local `PATH`, the exact temporary worktree trust
override, and the clone's project MCP configuration. Codex identified the
temporary repository and selected its configured default model, but
`thread/start` failed during TUI bootstrap because the required
`agentgov_governance` MCP handshake closed while producing the initialize
response (`-32603`).

No usable session or Agent turn followed. No native proposal form, human
consumer-task admission, governance task write, README heading edit,
validation call, task-completion record, or current-Agent consumer review was
observed. The README still contains `### One-command demo`. The task required
a bounded failure instead of MCP repair, coaching, or a second live replay, so
the attempt stopped at this first live deviation.

## Preservation and privacy boundary

The disposable clone remains detached, remote-free, and changed only at the
two pre-replay binding paths. The original AIRBNB worktree, prior clones and
runtimes, Starter source, HEAD, index, remotes, user Codex configuration, and
credentials remain unchanged. The new bootstrap wheel, AgentGov wheel,
runtime, source staging area, unused clone target, and bound clone are retained;
no cleanup occurred.

This record contains no raw prompt, response, transcript, screenshot, source
content, credential, private data, temporary absolute path, or external-model
payload. It retains only deterministic identities and the normalized startup
failure. No commit, push, pull request, publication, release, deployment,
original-consumer mutation, or broader activation occurred.

The bounded recovery task is complete as a failure record. A later product
review may decide whether to admit an installed Codex-to-AgentGov initialize
handshake diagnostic. This record grants no retry, diagnosis, source change,
consumer change, Git, release, deployment, cleanup, or external authority.

## Starter validation

The exact complete Starter repository suite passed all 946 tests on the fresh
Python 3.11.9 runtime, with 3 platform-limited skips, in 258.165 seconds. An
earlier invocation resolved to unsupported Python 3.9.7 and produced 7
failures and 32 errors across 713 executed tests because that runtime lacks
required language and standard-library features. No test was weakened or
deleted; the supported-runtime pass is the product validation result and the
unsupported-runtime outcome is retained as environment evidence.

After the evidence write-back, the final exact suite again passed all 946 tests
with 3 platform-limited skips in 261.439 seconds. Focused documentation suites
passed 38 and 13 tests. The task check returned
`PASS=3 WARN=1 FAIL=0 ADVISORY=3`, repository governance returned
`PASS=26 WARN=2 FAIL=0 ADVISORY=4`, and `git diff --check` passed. Scope
reconciliation admitted all 9 task-owned paths and retained 3 failures for
pre-existing, explicitly excluded user paths; no exception or ownership
transfer was inferred. The task JSON parsed, and bounded secret-like and host-
absolute-path scans returned zero matches.

The current Agent's callable governance inventory did not expose the native
task-completion-record tool, so no Starter completion record was fabricated.
Native current-Agent self-review `srv-4f6ab60826ed1c5b3755bf0f627faa7b`
completed separately with five advisory observations. It found the bounded
failure classification, admitted-path ownership, validation, privacy, and stop
boundaries consistent. It retained the initialize root cause, host/runtime
attribution, the unmeasured proposal-to-completion path, and package provenance
beyond recorded digests as unknown. The review grants no new authority.
