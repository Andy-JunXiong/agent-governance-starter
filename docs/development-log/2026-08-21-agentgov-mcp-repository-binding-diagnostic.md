# Governance MCP repository-binding diagnostic - 2026-08-21

Native proposal review admitted
`p0-mcp-repository-binding-diagnostic`, and the product owner separately took
up that exact task. The requirement is limited to bounded startup diagnostics,
tests, and current documentation. It does not authorize changing Git trust,
weakening repository validation, modifying successful MCP behavior, or
performing Git or publication actions.

The preceding differential isolated the real-host startup failure before the
first MCP request. A dependency-free stub passed standalone, sandbox Codex,
and real-host Codex. The same stub continued to pass after importing the real
AgentGov MCP module. The complete AgentGov server passed in sandbox Codex but
failed on the real host during repository resolution, before initialize was
read. A privacy-bounded classifier identified Git dubious-ownership rejection.
The complete server passed on the real host without a Git exception when its
disposable worktree was created by the real-host operating-system identity.
This evidence attributes the observed failure to disposable-worktree ownership,
not JSON-RPC framing, encoding, flush behavior, module import, the console
launcher, protocol negotiation, or tool schemas.

The implementation adds one narrow `CodexHookPolicyError` boundary around
Governance MCP startup. It returns the existing stable error exit and writes a
fixed actionable diagnostic to `stderr`. It does not interpolate the exception
message, so raw Git output, rejected paths, and host identity are not exposed.
Protocol `stdout` remains empty on this startup failure. Existing handling for
MCP, operating-system, and Unicode errors is unchanged.

The regression test injects a repository-binding exception containing private
placeholder text and proves the exact bounded diagnostic, nonzero exit, empty
stdout, and absence of the injected text. The existing protocol-purity test
continues to prove that successful STDIO operation emits only JSON-RPC lines.
The user guide now explains the failure, safety boundary, and correct operational
remedy without recommending a global trust bypass.

The admitted focused Governance MCP and Codex hook suites pass all 50 tests
under Python 3.11.9. The repository-wide suite passes all 947 tests with 3
platform-limited skips in 268.110 seconds. Task governance reports
`PASS=3 WARN=1 FAIL=0 ADVISORY=3`, repository governance reports
`PASS=26 WARN=2 FAIL=0 ADVISORY=4`, and `git diff --check` passes. Scope admits
all 6 task-owned paths and rejects only the 3 explicit exclusions. A bounded
scan of this task's added content finds no credential-shaped values or absolute
host paths.

An initial attempt under the ambient Anaconda interpreter
failed before collection because that interpreter lacks the supported standard
library and local test-package resolution; it is not product-test evidence.
The supported runtime subsequently executed the exact admitted commands.

This fully specified task did not start an alignment journey. A distinct
current-Agent review narrowed the exception handler to the `_git_root` call so
future serving or tool failures cannot be mislabeled as startup binding errors.
It found the requirement, privacy boundary, fail-closed Git semantics, scope,
documentation, and validation consistent.

A subsequent isolated no-model consumer replay used the same retained Python,
current source launcher, disposable worktree, and App Server probe in both
execution identities. Sandbox Codex initialized and completed `thread/start`.
Real-host Codex reproduced the required-MCP `-32603` failure before
`thread/started`. Privacy-bounded classifiers found neither the fixed AgentGov
diagnostic nor raw Git ownership details in App Server stderr; binary-safe
matching found neither value in the isolated Codex log databases. This proves
the server-side diagnostic does not reach the caller through the tested Codex
App Server path. It does not justify weakening Git validation or expanding the
AgentGov exception boundary.

The current callable governance inventory does not expose
`agentgov_task_completion_record`, so no native completion record was
fabricated. The missing tool does not change the passing local validation and
grants no human acceptance or downstream authority.
