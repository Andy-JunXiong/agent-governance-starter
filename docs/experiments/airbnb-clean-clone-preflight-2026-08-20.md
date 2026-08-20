# AIRBNB clean-clone automatic-rehearsal preflight - 2026-08-20

## Claim boundary

This record covers one local temporary clone of the human-selected AIRBNB
consumer and read-only checks of its clean-target state, committed governance
configuration, and one retained AgentGov wheel. It is prerequisite evidence
only. It is not a live Codex replay, AIRBNB task admission, consumer change,
product-effectiveness result, or authority to install, repair, commit, push,
publish, release, or deploy anything.

No raw prompt, transcript, model output, consumer source content, credential,
private data, or absolute host path is retained here.

## Preserved source worktree

Before the clone, the existing AIRBNB worktree was on `master` at committed
HEAD `d70615527d9acdde3893ce645d1923606173acf6`. It contained exactly one
modified `README.md` and one untracked prior-replay task,
`governance/tasks/rename-readme-demo-heading.json`.

The preflight did not clean, reset, stash, commit, overwrite, or otherwise
modify that worktree. After the clone and all read-only checks, the branch,
HEAD, two-path status, README blob identity, and prior task blob identity
remained unchanged.

## Clean-clone result

One new local clone was created from the exact committed AIRBNB HEAD using
copied Git objects. It was detached at the exact commit, and its local `origin`
was removed. The clone then reported:

- HEAD `d70615527d9acdde3893ce645d1923606173acf6`;
- zero working-tree changes;
- zero remotes;
- committed `AGENTS.md` and `.codex/config.toml`;
- a real committed `governance/tasks/.gitkeep`; and
- no copied modified README or untracked prior task.

The temporary clone is retained in the operating-system temporary area because
this task grants no cleanup authority. Its absolute path is deliberately
omitted.

## Exact candidate artifact

Read-only discovery found exactly one retained wheel named
`agent_governance_starter-0.3.0rc1-py3-none-any.whl`. It matched the previously
recorded size of `475529` bytes and SHA-256
`78D6A216FE7344A2E3DA01086A7A92B9F3310BE61DAD2E690B0705003221FDE6`.
The prior packaging record binds that wheel to committed Starter revision
`514f5023d7883aeee648ddda63b3e944d4116eac`; the current Starter HEAD is a
later commit and was not represented as the wheel source.

Without installing the wheel, Python zip import and an in-memory MCP
initialize/list-tools exchange reported:

- distribution identity `0.3.0rc1`;
- Adapter version `1.5.0`;
- AgentGov protocol `2026-07-28`;
- negotiated MCP protocol `2025-11-25`;
- seven tools with form elicitation, including proposal and drift review;
- no Agent-supplied `owner` input on the proposal tool; and
- a usable committed task directory in the clean clone.

This proves the named wheel can expose the expected read-only/native tool
catalog when loaded directly. It does not prove a Codex host can launch it
from the clone.

## Blocking runtime binding

The committed AIRBNB Codex configuration invokes `agentgov`. The exposed
launcher retained the previously recorded SHA-256
`7DADA88A8CCFF3DFA40DD52783719E5ACED5B293202979BA3D5B75F027B498E7`,
but `agentgov --version` failed before package startup because its Python
launcher binding could not be resolved. No standard local pipx AgentGov
environment was found, and the current PATH exposed no usable `pipx` command.
The available Python 3.11.9 interpreter contained neither AgentGov nor pipx.

The preflight therefore records the later live-replay readiness as
**BLOCKED** at the runtime-binding prerequisite. The clone and exact retained
wheel are ready inputs, but no installed executable currently binds them.
Installing the wheel, creating a wrapper, changing `.codex/config.toml`, or
repairing the global launcher would be a separate repository/environment
change and is not authorized by this task.

## Disposition

No external model turn, network request, AIRBNB-local task admission, consumer
source change, project validation, Git commit or push, publication, release,
deployment, or cleanup occurred. The next product review is whether to admit
one exact offline isolated-runtime preparation task for this retained wheel.
That decision would still not authorize the later single live replay.

All 13 task-contract tests and all 36 user-documentation tests passed. The
complete repository suite passed 938 tests with 3 platform-limited skips in
180 seconds. Task governance before pause reported `PASS=3 WARN=1 FAIL=0
ADVISORY=3`; repository governance reported `PASS=26 WARN=2 FAIL=0
ADVISORY=4`. Scope accepted all four task-owned Starter paths and rejected only
the pre-existing excluded `.codex/config.toml`; no exception or ownership
transfer was inferred. The task JSON parsed, bounded credential-pattern and
absolute-host-path scans returned zero matches, and `git diff --check` passed.

Native current-Agent advisory review
`srv-6030fa385782ccd98453cb047099e252` found the clean-clone direction,
preserved AIRBNB worktree, exact artifact facts, runtime-binding blocker,
four-path Starter scope, privacy boundary, and all-denied authority boundary
consistent. It retained the unknown isolated-installation and Codex host-launch
outcomes. This was a separate self-review pass, not an independent audit.
