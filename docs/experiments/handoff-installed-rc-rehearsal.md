# Installed 0.3.0rc1 handoff and rollover rehearsal

## Status and boundary

Date: 2026-08-05

Result: passed in three fresh independent disposable Git repositories using the
exact locally built `0.3.0rc1` wheel.

This was an agent-operated deterministic integration rehearsal under explicit
human authorization. It is not an uncoached usability study, semantic task
acceptance, a stable release, a consumer migration, or proof of general
effectiveness. No AgentGov source-repository commit, push, tag, release, merge,
or deployment occurred during the rehearsal.

## Exact artifact

- Wheel: `agent_governance_starter-0.3.0rc1-py3-none-any.whl`.
- Size: 266304 bytes.
- SHA-256:
  `069d9470ef7acabe0cd827f7957be31f261fd8f39e2053935ee664b7b0a06540`.
- Runtime: Python 3.11 in a fresh virtual environment.
- Installation: `pip install --no-deps` from the built wheel.
- Import identity: `agentgov 0.3.0rc1` loaded from the disposable runtime
  environment's `site-packages`, with source-checkout leakage explicitly
  rejected.
- The generated immutable release-candidate manifest passed
  `agentgov check release-manifest` and carried the same artifact digest.
- Wheel inspection found the new `agentgov/development_handoff.py`, bundled
  `release/current.json`, and package metadata.

The first build command was intentionally run from the source repository and
failed because the existing local `build/` directory shadowed the Python
package named `build`. The successful gate ran the standard PEP 517 builder
from a temporary directory against the same source tree. No existing build
output was deleted or used as release evidence.

## Exercised lifecycle

Each scenario initialized and committed a fresh repository baseline, then used
the installed CLI path for exact-confirmation `START`, changed one in-scope
source file, ran `govern check`, reached verified completion through `govern
finish`, generated the Development Monitor, previewed handoff, supplied exact
`HANDOFF`, and inspected read-only rollover routing.

The automation shell was not a real terminal. The installed CLI received a
simulated terminal object with the exact already-authorized `START`, `HANDOFF`,
and `REPLACE` words. Existing CLI tests separately enforce real-terminal
detection. This rehearsal therefore proves the installed command path and
confirmation semantics, not physical-terminal usability.

## Results

| Admitted tasks | Post-handoff route | Events | Handoffs | Replace applied |
|---:|---|---:|---:|---|
| 1 | compact-task placeholders (`<TASK_TITLE>`, `<PATH>`) | 5 | 1 | no |
| 2 | exact second task path | 6 | 1 | yes, with exact `REPLACE` |
| 3 | explicit `<TASK_JSON>` choice | 5 | 1 | no |

Across all three scenarios:

- pre-handoff `next` selected Monitor and did not change normalized Git state;
- Monitor printed the handoff dry-run guidance and stated that it does not
  prove review;
- handoff preserved `.agentgov/current-task.json` byte-for-byte;
- a repeated matching handoff was idempotent and created no second event;
- post-handoff `next` always included a separate `--replace-active --dry-run`
  preview and did not change normalized Git state;
- the same handed-off task digest was not automatically restarted;
- all event authority flags remained false.

## Claim limit

This evidence supports packaging integrity, installed routing behavior,
fresh-evidence handoff, idempotence, pointer preservation, zero/one/many choice
semantics, and exact replacement confirmation for these fixtures. It does not
establish requirement correctness, architecture quality, validation
sufficiency, human acceptance, cross-platform behavior, stable update safety,
or consumer readiness.
