# Codex hooks Adapter

Status: implemented in development source on 2026-08-06. This optional Adapter
does not change stable 0.2.1 or immutable `v0.3.0rc1`, and it is not installed
in this repository by this change.

## Purpose

The Adapter connects reviewed Codex project lifecycle hooks to AgentGov's
existing vendor-neutral foreground coordinator. It uses the project
`.codex/hooks.json` surface documented in the official
[Codex hooks reference](https://developers.openai.com/codex/config-advanced#hooks).
The hook command runs in the session working directory, validates that the
payload and selected repository resolve to the same Git worktree, then derives
governance facts locally.

## Lifecycle mapping

| Codex callback | AgentGov event | Bounded response |
| --- | --- | --- |
| `SessionStart` | `repository.activated` | activation/task context |
| `UserPromptSubmit` | host-side work-request routing context | no-write work proceeds without a task; repository changes use structured routing before modification |
| `PermissionRequest` | no lifecycle event | preserve Codex's normal human tool approval prompt |
| `PostToolUse` | `implementation.changed` | scope context; block decision after a failing observation |
| `Stop` | `completion.requested` | completion context or bounded continuation |

The managed hook command is `agentgov adapter codex-hook`. It accepts one Codex
hook JSON object on stdin and writes only the structured hook result to stdout.
Policy errors go to stderr without echoing the rejected payload.

Command hooks remain lifecycle and context adapters; they are not an LLM
execution surface. Current Codex runs only command hook handlers, while parsed
`prompt` and `agent` handlers are skipped. The optional foreground
[governance MCP Adapter](governance-mcp-adapter.md) supplies model-controlled
alignment and active-Agent self-review tools. `UserPromptSubmit` tells the
current Agent to use those tools when available without forwarding the prompt
to AgentGov Core.

`PostToolUse` runs after the tool. A blocking result states that AgentGov
observed a failure and does not claim that the completed side effect was undone.
A repeated `Stop` callback with `stop_hook_active: true` returns immediately and
does not rerun completion, preventing a continuation loop.

`PermissionRequest` is deliberately different. The Adapter returns neither
`allow` nor `deny`, records no AgentGov lifecycle event, and leaves Codex's
normal approval prompt in control. Tool permission does not admit a task,
expand scope, approve an exception, or accept completion.

## Host interaction capability

AgentGov Core now emits vendor-neutral interaction requests for missing task
admission, material scope resolution, and review-ready completion. The Codex
binding declares all three as `context_only` with decision recording
`unavailable`. Current Codex Hooks can add model-visible context and participate
in tool permission, but they do not expose arbitrary project-defined buttons or
a trusted callback for custom governance decisions.

Accordingly, action names shown in Codex context are not buttons and no decision
is inferred from the user's prompt. This is recorded product drift, not a claim
that native task/scope/completion approval is complete.

Coding Agent responses now include `agentgov.human-decision-prompt` 1.0 for a
real gate. Codex context receives its why-now explanation, safe recommendation,
and numbered option labels proactively, but the Hook cannot return the trusted
`agentgov.human-decision-result` 1.0 required to apply a custom governance
choice. A conversational reply or tool permission is not converted into that
result by Core.

## Privacy boundary

The Adapter checks the shape of host fields it needs for event routing, hashes
session and turn identity into bounded event/correlation identifiers, and
discards these sensitive values before constructing an AgentGov event or Codex
hook result:

- `prompt`;
- `tool_input` and `tool_response`;
- `transcript_path`;
- `last_assistant_message`;
- `model`;
- absolute host path values such as `cwd`.

It does not infer task scope, admission, approval, semantic acceptance, or
authority from prompt or assistant text. It does not upload local state or add a
daemon, App Server dependency, or network request.

For `UserPromptSubmit`, the conversational Coding Agent still sees the user's
request through the host, but the Hook does not send that prompt to AgentGov
Core. It returns the strict work-request vocabulary: no-write work proceeds
without a task; active work must match local task identity; a new repository
change must route a normalized proposal before modification.

## Preview and apply

Preview the exact managed project configuration without writing:

```powershell
agentgov integrate codex-hooks . --dry-run
```

Use `--format json --non-interactive` for a machine-readable, read-only plan.
The plan explicitly reports that repository writes, hook trust, plugin
installation, and Git/release operations are not authorized.

To create a missing file interactively, omit `--dry-run` and type the exact
confirmation `INTEGRATE`. This create-missing-only integration does not grant
hook trust and:

- creates only `.codex/hooks.json` when it is missing;
- preserves the exact already-managed file;
- refuses to overwrite, replace, or merge a different existing file;
- rechecks the path before exclusive creation;
- installs no plugin and grants no Codex trust.

After creation, review the hook definition separately through Codex `/hooks`.
Codex may disable project hooks through user or managed configuration; AgentGov
does not bypass that decision.

## Authority boundary

Hook callbacks are observations and requests, not governance authority. The
Adapter grants no scope expansion, exception, commit, push, merge, release,
publication, deployment, or external-system permission. Missing task admission
is returned as bounded routing context; no task is invented from the user's
prompt and not every prompt is forced through human admission.

The MCP config and Hook config are separate reviewed files. Hooks do not grant
MCP trust, MCP tools do not replace native tool permission, and neither surface
can silently install or authorize the other.
