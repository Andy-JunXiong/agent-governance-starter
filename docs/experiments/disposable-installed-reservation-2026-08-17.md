# Disposable installed reservation rehearsal — 2026-08-17

## Claim boundary

This is one stopped local installation measurement for a synthetic disposable
reservation rehearsal. Its outcome is
`BLOCKED_INSTALLATION_PRECONDITION`. It does not establish reservation
behavior, interactive confirmation, exclusive marker creation, bridge
compatibility, replay behavior, consumer portability, or product
effectiveness.

The admitted task permitted one offline installation attempt and required no
retry after any uncertain or failed result. No model session, network call,
real consumer, Git remote, publication, release, or deployment was involved.

## Read-only installed-state preflight

The existing global command reports `agentgov 0.3.0rc1` but does not expose
`reserve`; invoking its reservation help returns the argparse unsupported-
command result. The existing pipx installation was therefore not used as the
system under rehearsal and was never modified.

The source-side command at committed starter `HEAD`
`514f5023d7883aeee648ddda63b3e944d4116eac` does expose
`reserve replay-correlation`. The rehearsal used `git archive HEAD` so the
temporary source contained only committed files. Archive inspection confirmed
that it did not contain the untracked `.codex` configuration.

## Single offline installation attempt

A new temporary Python 3.11 virtual environment was created and one local
installation was attempted from the extracted archive with network index,
dependency installation, and build isolation disabled. The attempt exited `1`
during package metadata preparation.

The disposable environment supplied `setuptools 65.5.0`, below the repository
build requirement `setuptools>=69`. That backend rejected the current SPDX
`project.license = "MIT"` representation under its older project-metadata
schema. The failure occurred before an `agentgov` entry point was installed.
It is installation-environment evidence, not a reservation-contract or CLI
failure.

Per the admitted one-shot boundary, there was no retry, fallback installer,
dependency download, build-tool upgrade, manual module copy, or modification
of the existing pipx environment.

## Stopped result and disposition

- installation exit code: `1`;
- disposable `agentgov` entry point present: `false`;
- disposable consumer entry count: `0`;
- reservation invocation count: `0`;
- visible terminal started: `false`;
- marker created: `false`;
- reserved bridge validation run: `false`.

Pre- and post-attempt SHA-256 checks matched for the existing exposed launcher
and installed pipx package module, so the existing pipx installation remained
byte-unchanged. The empty consumer directory was never initialized as Git and
contains no plan, Adapter metadata, marker registry, marker, task, or remote.

The temporary source archive, failed virtual environment, and empty consumer
directory remain in the operating-system temporary area because cleanup was
not authorized. Their absolute path and the raw installation transcript are
not retained in repository evidence. A new installation strategy or another
rehearsal requires a separate product decision and task; this record grants no
retry, cleanup, replay, Git, publication, release, or deployment authority.
