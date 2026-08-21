# Doctor Git worktree access preflight - 2026-08-21

Native alignment journey `mcpj-757b4ac06b474e7f800a90015451224f`
offered bounded next directions after the repository-binding diagnosis. The
product owner chose the doctor-preflight direction, admitted proposal
`prp-92a6100e77834ab9ac4aa995ad804272`, and separately started exact task
`p0-doctor-git-worktree-access-preflight`. The task authorizes a read-only
doctor check, related tests, and current documentation. It does not authorize
Git trust mutation, MCP protocol changes, Codex configuration changes, Git
publication, release, deployment, or follow-on implementation.

Official Codex behavior and the local differential establish the boundary for
this slice. A required MCP server can fail before a thread is loaded. The
tested App Server path reports a generic startup failure and does not forward
the AgentGov server diagnostic. A non-required probe can expose a generic
startup event but still not raw server stderr. AgentGov can therefore provide
a user-run preflight before activation; it cannot claim automatic Codex UI
error forwarding.

The implementation exposes the existing bounded Git-worktree resolver for
reuse while preserving its private compatibility wrapper for current hook and
CLI callers. Doctor adds one deterministic `repository:git-access` finding
when a `.git` marker is present. Accessible worktrees pass. A bounded resolver
failure produces a fixed actionable failure without interpolating the original
exception. Non-Git onboarding retains its existing warning and does not invoke
Git.

The check is read-only. It never writes repository content or Git
configuration, adds `safe.directory`, suppresses ownership enforcement, starts
MCP, or changes required-server behavior. Existing doctor text and JSON result
structure remain intact. The user documentation labels the command as a
development-source preflight so it does not overstate the stable 0.2.1 release.

Focused doctor and Codex-hook validation passed all 28 tests under Python
3.11.9. The complete repository suite passed all 949 tests with 3 platform-
limited skips in 306.681 seconds. A real current-source differential returned
exit 0 and `repository:git-access=PASS` for the accessible Starter worktree,
then exit 1 and `repository:git-access=FAIL` for the retained real-host-owned
worktree under the sandbox identity. The failure contained the fixed bounded
message and no raw Git ownership marker or selected host path.

The documentation and status suites passed all 49 tests. Task governance
reported `PASS=3 WARN=1 FAIL=0 ADVISORY=3`, and repository governance reported
`PASS=26 WARN=2 FAIL=0 ADVISORY=4`. Scope reconciliation admitted all 8 current
task changes and retained 3 failures for the explicit exclusions. Task JSON
parsing, bounded concrete-host-path and credential-marker scans, full diff
review, and `git diff --check` passed.

Native current-Agent self-review
`srv-0d58c231534639f70005611bfde4f876` completed as a distinct advisory pass.
It found the requirement, shared-resolver architecture, implementation
evidence, admitted scope, and security boundary consistent. It records the
existing nested-directory behavior and future Codex host forwarding behavior
as unknowns and grants no new authority. The current callable governance
inventory does not expose `agentgov_task_completion_record`, so no native
completion record was fabricated.

Unrelated user-owned `.codex`, the social-cover asset, and the external AIRBNB
task record remain excluded and unchanged. No commit, push, publication,
release, deployment, or follow-on implementation is authorized by this task.
