# ADR-0004: Use isolated tool execution for onboarding

Status: Accepted

Date: 2026-07-25

## Decision gate

Choose the v0.1 execution model before implementing guided onboarding or
asking another pilot user to install AgentGov.

## Context

The first Taxi adoption installed AgentGov into an active Python environment.
That avoided copying the starter into the target repository, but it still made
the governance tool appear coupled to the project's environment. A stale
project `.venv` then looked like an AgentGov prerequisite even though the
governance checks do not import the adopting project's code or dependencies.

The supported path needs one interpreter to run every AgentGov subcommand,
must not install the adopting project's dependencies, and must have explicit
update and uninstall operations.

## Decision

Use a persistent, isolated Python tool environment as the v0.1 onboarding
model. Use `pipx` as the first verified implementation:

```powershell
pipx install "git+https://github.com/Andy-JunXiong/agent-governance-starter.git@main"
agentgov --help
```

The Git `main` specification is a development-channel command, not a stable
release pin. Replace it with a reviewed version tag before making it the
primary stable Quickstart command.

The lifecycle commands are:

```powershell
pipx upgrade agent-governance-starter
pipx uninstall agent-governance-starter
```

An ephemeral runner such as `uvx` remains a valid future convenience after it
has its own Windows rehearsal. It is not required for v0.1 and is not the
primary contract while it would add a second prerequisite that has not been
validated in the pilot environment.

## Owns

- Isolation of AgentGov from an adopting repository's Python environment.
- The supported install, update, and uninstall lifecycle.
- The rule that all AgentGov subcommands use the same isolated installation.
- The release-pin requirement for the stable Quickstart.

## Does not own

- Repairing, replacing, or activating a target project's `.venv`.
- Installing target-project dependencies.
- Guided `doctor`, `onboard`, or `next` command behavior.
- Package publication, version approval, tagging, or release.

## Consequences

- A broken project environment is not an AgentGov blocker when the selected
  pipx interpreter is usable.
- Repeated commands avoid rebuilding an ephemeral environment.
- Users need Python 3.11 or newer and pipx before installing AgentGov.
- A PATH refresh may be required after first installing pipx.
- The isolated environment remains independently removable.

## Alternatives considered

### Install into the active project environment

Rejected as the supported experience because it couples tool availability to
project environment health and makes unrelated dependency failures look
relevant to governance adoption.

### Use an ephemeral runner as the only path

Deferred. Official uv tooling supports Git sources and isolated ephemeral
execution, but uv was not present in the Windows pilot environment and has not
completed the required end-to-end rehearsal.

### Add a repository bootstrap script

Rejected for v0.1 because it would create another maintained installer and
trust surface while still needing to provision an isolated Python environment.

## Validation

The 2026-07-25 Windows rehearsal recorded in
`docs/isolated-tool-execution-rehearsal.md` verifies installation from GitHub,
help, inspection, adoption preview, create-missing-only adoption, repository
checking, upgrade, and uninstall. The target was a realistically deep path and
contained an unrelated `.venv` directory.

## Rollback or replacement

A later ADR may select a version-pinned `uvx` or another isolated runner after
equivalent Windows and cross-platform evidence exists. It must preserve the
environment-isolation and human-authority boundaries in this decision.
