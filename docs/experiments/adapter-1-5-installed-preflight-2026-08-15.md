# Adapter 1.5.0 local installation preflight — 2026-08-15

## Claim boundary

This record covers one offline, local-only repair of the existing AgentGov
pipx development runtime and one no-model preflight. It is installation
evidence, not a package build, publication, release, consumer activation,
Codex live replay, user-interface test, personal identity authentication,
or product-effectiveness result.

The project configuration, `.codex/config.toml`, was not edited. AIRBNB and NYC
were not opened or changed. No model or network resource was used.

## Installation action

The existing runtime reported distribution version `0.3.0rc1` and MCP Adapter
`1.4.0`. Because the local pipx CLI and offline wheel-build dependencies were
unavailable, the approved repair replaced only two exact runtime files:

- installed `agentgov/governance_mcp.py`, from the reviewed repository source;
- the broken exposed `agentgov.exe`, from the working launcher inside the same
  pipx environment.

Before replacement, create-only backups were written beside both targets and
retained. The first copy attempt encountered a locked exposed launcher and
rolled both targets back successfully. After the human explicitly authorized
stopping only the two wrapper `agentgov.exe` processes, the second attempt
completed. Python MCP child processes were not targeted.

Recorded SHA-256 values:

| Surface | Before / retained backup | Installed result |
| --- | --- | --- |
| `governance_mcp.py` | `7E84D0D828DC0A56E002E132D7D6A123E8E032902799B482929C112273D63188` | `9452D42C33ED9E52615E9B44FA0D7982C1C89F5E2B8C5AC5AD7E110DC8AAA610` |
| exposed `agentgov.exe` | `E8E99022E267C23A8976B9DBBB25C6CD1B44F1100B7E944E2E0966277C126B10` | `7DADA88A8CCFF3DFA40DD52783719E5ACED5B293202979BA3D5B75F027B498E7` |
| project `.codex/config.toml` | `4CCA2D57EDEADDFE52D3E6C4DD4D774192BBDBCAB4E84E07DF73E14A861C0348` | unchanged |

The exposed launcher now matches the working inner launcher byte-for-byte.
The unchanged configured command starts and reports `agentgov 0.3.0rc1`; an
import outside the source repository reports Adapter `1.5.0`, canonical owner
`Human product owner`, and the installed pipx module path. Protocol identity is
`2026-07-28`.

## No-model installed-runtime preflight

All proposal checks ran through the installed pipx Python in an automatically
removed temporary Git repository:

Sanitized outcome keys are `seven/form`, `five/base`, `hostile-owner`, and
`accepted-admit`.

- form-capable discovery returned 7 tools; discovery without form capability
  returned the 5 base tools;
- the native proposal input schema did not contain `owner`;
- hostile `owner=current-agent` input returned
  `tool_arguments_invalid` before elicitation and created no task;
- a bound `accept` plus `admit` response emitted one elicitation and created
  exactly one disposable task;
- the admitted task recorded both `owner` and `decided_by` as
  `Human product owner`.

## Remaining unknowns and denied authority

Direct file replacement does not prove that a future wheel or published
package contains the same bytes. The reason the earlier exposed launcher was
invalid remains unknown. Native form mediation establishes the accountable
human role but does not cryptographically authenticate an individual.

No AIRBNB replay, consumer change, project-config change, backup removal,
rollback, Git operation, publication, release, deployment, or follow-on
implementation is authorized by this record.
