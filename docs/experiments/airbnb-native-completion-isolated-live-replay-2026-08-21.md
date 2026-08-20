# AIRBNB native-completion isolated live-replay attempt - 2026-08-21

## Outcome

`BLOCKED_BEFORE_INSTALLATION`

The product owner selected a live uncoached AIRBNB replay through resolved
alignment journey `mcpj-26130afbf8444dadab2f3e42246e0de7`. Native proposal
review admitted exact task
`p0-native-completion-airbnb-isolated-live-replay-v1`, and the product owner
separately started it.

The attempt stopped at its first offline installation gate. No AgentGov
development package was installed, no MCP process or Codex session started,
and no consumer task or completion record was created.

## Deterministic setup evidence

- A fresh operating-system temporary root received a bounded source staging
  copy, a fresh Python 3.11.9 virtual environment, and a fresh AIRBNB clone.
- SHA-256 identities for the Adapter module, Codex integration module, Agent
  template, and Codex MCP template matched the Starter source at staging time.
- The disposable clone was clean at committed HEAD
  `d70615527d9acdde3893ce645d1923606173acf6` and had zero remotes.
- The original AIRBNB worktree retained its existing modified README,
  untracked prior task, branch, HEAD, remote, and measured Agent/config hashes.
- The previously retained Adapter `1.5.0` runtime still reported distribution
  `0.3.0rc1`, Adapter `1.5.0`, and seven form-capable tools.

## First deviation

The new virtual environment contained `pip 24.0` and `setuptools 65.5.0`.
Starter declares `setuptools>=69` for its build backend. The exact offline
command shape used `--no-index`, `--no-deps`, and `--no-build-isolation` against
the staged source. Its metadata phase rejected the current project metadata
under the older backend before building or installing a package.

No compatible build dependency was available in the checked local cache. The
task did not authorize downloading one, changing project metadata, manually
assembling a wheel, or retrying through a different installation path. The
attempt therefore stopped instead of manufacturing success.

## Independent consumer readiness finding

The AIRBNB commit's project MCP configuration allow-lists the prior seven
form-capable tools and omits `agentgov_task_completion_record`; its committed
Agent guidance also describes five base tools. Official Codex configuration
defines `enabled_tools` as the allow-list of tools exposed by an MCP server.
This means a later replay must explicitly own the consumer configuration
binding or a disclosed process-local override. This finding was measured
before any live session; it was not repaired or replayed here.

## Preservation and privacy boundary

The fresh runtime contains no AgentGov package or `agentgov` command. The fresh
clone remains clean, detached at the measured commit, and remote-free. Starter
HEAD, index, remotes, task-scoped source hashes, original AIRBNB state, retained
clone, and retained runtimes were not changed by the failed install. The new
temporary resources are retained and were not cleaned up.

This record contains no raw prompt, response, transcript, screenshot, source
content, credential, private data, temporary absolute path, or external-model
payload. All findings are current-Agent deterministic measurements; there is
no user-reported or model-run evidence in this attempt.

The result authorizes no dependency download, packaging correction, consumer
configuration change, retry, source repair, Git operation, publication,
release, deployment, cleanup, or external action.
