# Isolated tool execution rehearsal

## Purpose

This rehearsal tests whether AgentGov can run independently from the adopting
repository's Python environment. It validates tool execution and package
lifecycle behavior; it does not validate project-specific governance quality
or authorize a release.

## Contract

Date: 2026-07-25

Environment:

- Windows PowerShell;
- Python 3.12.10 selected explicitly for the tool environment;
- pipx 1.11.1;
- AgentGov `0.1.0.dev0`;
- installation from the public Git repository's `main` branch;
- a target nested through seven additional path segments;
- an unrelated `.venv` directory present in the target.

The rehearsal did not activate, inspect, repair, or install dependencies into
the target `.venv`.

## Commands exercised

The isolated package lifecycle used:

```powershell
pipx install --python <python-3.11-or-newer> "git+https://github.com/Andy-JunXiong/agent-governance-starter.git@main"
agentgov --help
pipx upgrade agent-governance-starter
pipx uninstall agent-governance-starter
```

The installed executable then ran:

```powershell
agentgov inspect <deep-target>
agentgov adopt <deep-target> --project-name "Isolated Windows Rehearsal" --dry-run
agentgov adopt <deep-target> --project-name "Isolated Windows Rehearsal"
agentgov check repository <deep-target>
```

## Observed result

| Stage | Result |
|---|---|
| Git installation | `PASS`; isolated package installed with Python 3.12.10 |
| CLI discovery | `PASS`; `agentgov.exe` exposed the expected commands |
| Inspection | `PRESENT=0 MISSING=7 DISCOVERED=0 CONFLICT=0` |
| Adoption preview | `CREATE=25 PRESERVE=0`; no files written |
| Adoption | `CREATE=25 PRESERVE=0` |
| Repository check | `PASS=14 WARN=4 FAIL=0 ADVISORY=4` |
| Upgrade | `PASS`; already at `0.1.0.dev0` |
| Uninstall | `PASS` in the isolated rehearsal home |

WARN and ADVISORY findings remained visible. Successful execution did not
claim that scaffold placeholders, evidence, or human decisions were complete.

## Findings

- The target project's `.venv` was not needed for any AgentGov command.
- The isolated environment reported no runtime dependencies for AgentGov.
- A Git source works before an external package-index release exists.
- Installing from `main` is not a stable version pin and must remain labeled as
  a development-channel command.
- pipx warned when the rehearsal deliberately placed its private home under a
  workspace path containing spaces. Normal pipx user paths should be used by
  the supported workflow; the project must not instruct users to put
  `PIPX_HOME` inside the adopting repository.
- `uvx` remains unverified locally because uv was not installed. Its official
  tool contract supports isolated Git-source execution, but documentation is
  not a substitute for the required Windows rehearsal.

## Decision supported

ADR-0004 selects persistent isolated tool execution through pipx for v0.1.
The primary Quickstart must not switch from the current development guidance
until a reviewed release tag supplies a stable install pin.

No commit, push, tag, package publication, release, or deployment was
performed.
