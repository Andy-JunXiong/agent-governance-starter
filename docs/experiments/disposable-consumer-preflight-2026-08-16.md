# Disposable-consumer replay preflight rehearsal - 2026-08-16

## Claim boundary

This record covers one synthetic local consumer and exactly one invocation of
the development-source replay-preflight CLI. It is portability evidence for
the named prerequisites only. It is not replay admission, a model-session
result, real-consumer evidence, product-effectiveness evidence, or authority
to modify, clean, commit, push, publish, release, or deploy anything.

## Synthetic setup

The rehearsal created one new Git repository under the operating-system
temporary directory. It had no remote and used one committed baseline with:

- `README.md` as the unchanged target;
- a tracked `governance/tasks/.gitkeep` and no related task named
  `p0-synthetic-readme-update`;
- strict local Adapter metadata for `openai.codex-mcp` version `1.5.0` and
  protocol `2026-07-28`;
- expected HEAD `448ad92321b9a87b213b5c9292dc4961af323901`;
- correlation identifier `rpf-7e3a91c4d2b865f0`, with no marker; and
- a `text_absent` precondition for `## Governed replay candidate` in the
  target.

The plan denied cleanup, deployment, Git operations, publication, release,
replay, repository writes, and task admission.

## One-shot result

The CLI was invoked exactly once with JSON output. It exited `0` with contract
`agentgov.replay-preflight-report` version `1.0`, status `READY`,
`preconditions_ready: true`, and no reason codes. All six findings passed:

- repository HEAD matched;
- the target had no working-tree change;
- the target satisfied the explicit text pre-state;
- the related task was absent;
- Adapter identity and protocol matched; and
- the correlation identifier had no local marker.

Read-only post-check inspection found the disposable consumer still clean,
with zero remotes, no related task, and no correlation marker. No second
preflight invocation or replay occurred.

## Limits and disposition

`READY` proves only that these exact synthetic prerequisites held at check
time. The plan does not cover unnamed semantic state, and the missing marker
does not reserve the identifier or remove the time-of-check/time-of-use race.
The disposable directory is retained under the local temporary area because
neither the report nor this rehearsal grants cleanup authority. Its absolute
path is intentionally omitted from repository evidence.

The originally declared focused-test command used import-style module names,
but this repository's `tests` directory is not an importable package, so both
imports failed. Equivalent file-pattern discovery then passed all 15
replay-preflight tests and all 10 CLI tests. This command correction did not
repeat the one-shot preflight.

The complete suite under supported Python 3.11.9 passed all 852 tests with 2
platform-limited skips. For transparency, PATH-default Python 3.9.7 was also
attempted: it ran 623 tests and ended with 27 compatibility errors, 7 failures,
and 2 skips. The errors included unavailable Python 3.11 language and standard-
library features, so this is environment evidence rather than a correction to
the rehearsal result.
