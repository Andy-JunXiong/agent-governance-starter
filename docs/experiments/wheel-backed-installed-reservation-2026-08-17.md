# Wheel-backed installed reservation rehearsal — 2026-08-17

## Claim boundary

This is one successful local reservation rehearsal in a synthetic disposable
consumer. It establishes that the wheel built from committed starter revision
`514f5023d7883aeee648ddda63b3e944d4116eac` can be installed offline and can
perform its human-confirmed, create-only replay-correlation reservation path.

It does not establish replay authorization, launch, consumption, completion,
Harness evidence, real-consumer portability, network-filesystem behavior, or
product effectiveness. No replay, model session, consume transition, real
consumer, network call, starter-repository Git operation, publication, release,
deployment, or cleanup occurred.

## Installed wheel and disposable consumer

Before installation, the retained wheel matched expected SHA-256
`78D6A216FE7344A2E3DA01086A7A92B9F3310BE61DAD2E690B0705003221FDE6`.
A fresh Python 3.11 environment installed it with `--no-index --no-deps` and
reported `agentgov 0.3.0rc1`. Installed
`agentgov reserve replay-correlation --help` exited `0` and exposed `--apply`.

The synthetic consumer was initialized as a local Git repository only after
the product owner explicitly approved its one baseline commit. It had no
remote. Baseline HEAD was
`5bcc3ee68cc6ff697187ceebe442b1c4c10f312d`. The commit contained only a
synthetic README and strict local Adapter metadata for `openai.codex-mcp`
Adapter `1.5.0`, protocol `2026-07-28`. The marker registry directory existed
but was empty, the target was unchanged, the working tree was clean, and the
related synthetic task id was absent.

## Read-only preview

The plan used unused correlation id `rpf-dec1d2c300000001`, expected the exact
baseline HEAD, required the named README text to be absent, bound the strict
local Adapter identity, and denied all cleanup, deployment, Git, publication,
release, replay, repository-write, and task-admission authority.

Installed JSON preview exited `0` with `READY_TO_RESERVE`. All six checks passed:
repository HEAD, clean target, target pre-state, related-task absence, Adapter
identity, and correlation uniqueness. The preview named marker path
`.agentgov/replay-correlations/rpf-dec1d2c300000001.json`, reservation id
`rrv-8727d1e62d0fde6e`, and plan digest
`sha256:8727d1e62d0fde6eb1cd990935d94c1e52f02e526bc15ed325da03d9960fcd2c`.
The marker did not exist before apply.

## Single human-confirmed apply

The installed apply command was invoked exactly once in one visible PowerShell
terminal. The product owner supplied the CLI's exact interactive `RESERVE`
confirmation. The process exited `0`; the invocation was not retried.

Afterward, the marker registry contained exactly one JSON marker. Its stable
facts were:

- contract: `agentgov.replay-correlation-reservation`;
- schema version: `1.0`;
- status: `reserved`;
- correlation id: `rpf-dec1d2c300000001`;
- reservation id: `rrv-8727d1e62d0fde6e`;
- marker path:
  `.agentgov/replay-correlations/rpf-dec1d2c300000001.json`;
- marker digest:
  `sha256:9cbd4cdb06486a78a554ec208c39d00cdba5bddd4b41c178f957c5106989c268`;
- expected and observed consumer HEAD:
  `5bcc3ee68cc6ff697187ceebe442b1c4c10f312d`;
- Adapter identity: `openai.codex-mcp` `1.5.0`, protocol `2026-07-28`;
- authority boundary: all actions denied.

The marker validator returned zero errors. Consumer HEAD and remote count were
unchanged, and the README and Adapter metadata SHA-256 values matched their
pre-apply values. The only working-tree addition was the untracked marker
registry content; no committed target or Adapter content changed.

## Reserved bridge validation

The development-source pure validator accepted one in-memory
`agentgov.replay-correlation-bridge` version `1.0` record in `reserved` state,
bound to the exact marker identity, path, and digest. Bridge validation returned
zero errors. Its unchanged Harness mapping target was
`host.repository_correlation`, with expected value
`rpf-dec1d2c300000001`; Harness run and evidence fields remained null.

This bridge result records correlation compatibility only. It does not consume
the reservation, authorize or launch a replay, or create Harness evidence.

## Existing installation and disposition

The existing exposed launcher retained SHA-256
`7DADA88A8CCFF3DFA40DD52783719E5ACED5B293202979BA3D5B75F027B498E7`.
The existing pipx package module retained SHA-256
`5C9A876E01F8013AB3492C72E155E1F25F2E87D07E64EAAD228C8BDF5BEA7E83`.
The existing installation therefore remained byte-unchanged at both measured
surfaces.

The wheel-backed environment, no-remote consumer, plan, Git metadata, and
marker remain in the operating-system temporary area because cleanup was not
authorized. Their absolute paths and the raw terminal transcript are omitted
from repository evidence. This completed reservation is intentionally not
reusable; any consume transition, replay, cleanup, or other follow-on action
requires a separate product decision and admitted authority.
