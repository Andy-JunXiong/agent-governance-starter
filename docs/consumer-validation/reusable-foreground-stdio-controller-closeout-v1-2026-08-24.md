# Reusable foreground STDIO controller baseline-backed closeout v1 — 2026-08-24

## Outcome

`REVIEW_READY_BASELINE_BACKED`

This is a later review layer for the already implemented repository-internal
foreground JSONL STDIO controller. It does not rewrite the historical
`STOPPED_AT_WORKTREE_WIDE_SCOPE_VALIDATION` outcome of task
`p0-reusable-foreground-stdio-controller-v1` and does not claim that its
original cumulative scope command passed.

## Trusted task boundary

After native proposal admission and explicit human take-up, the first execution
action was an exclusive capture to the local task boundary:

```text
.agentgov/scope-baselines/p0-reusable-foreground-stdio-controller-closeout-v1.json
```

The capture completed before any repository write. It bound:

- task digest
  `sha256:e4c7c14b853567e2bea7f66236bf7835491b75942e1e751a25dbd5cdb0d23f12`;
- baseline digest
  `sha256:f385023f03704e989480a77c0436e33dd785341c0f0af7cc6130c89d176b3874`;
- comparison base and HEAD identity;
- the admitted include/exclude scope; and
- privacy-reduced per-record identities across committed-since-base, staged,
  unstaged, and untracked Git layers.

The immediate no-write comparison returned:

```text
PASS=20 PRESERVED=49 FAIL=0 TOTAL=69
```

The local baseline is create-only and was not overwritten. Its path metadata
and digests remain local; no raw source, patch, validation output, absolute
path, credential, environment value, process identifier, or host identity is
retained in this evidence.

## Controller and baseline-tool validation

- all 16 foreground controller tests pass;
- all 17 task-start baseline tests pass, with one platform-limited symbolic-
  link skip;
- the complete supported Python 3.11 suite passes all 1083 tests with 4
  platform-limited skips in 173.471 seconds.

The controller tests start only the inert standard-library Python fixture.
They do not start Codex, AgentGov, an MCP server, a model, or a network client.

## Preservation result

The baseline scope explicitly excludes and freezes:

- all files under `scripts/foreground_stdio`;
- all files under `scripts/task_start_scope_baseline`;
- the original controller and baseline task records;
- the historical controller and baseline evidence;
- retained consumer/build evidence;
- Core source and product tests; and
- every other task-excluded predecessor path.

The final comparison is the authority for whether those identities remained
exact. A zero-failure result means the excluded predecessor identities were
preserved at their captured Git layers while only admitted closeout documents
changed. It does not establish semantic correctness, causal benefit, or
historical cumulative-scope success.

## Authority and execution boundary

This closeout review performs no controller repair, public CLI or package
change, Adapter or MCP change, dependency download, network call, model call,
Codex run, consumer write, Git transition, commit, push, cleanup, publication,
release, deployment, or host retry. The local baseline and this evidence grant
none of those authorities.

## Remaining unknowns

- real Codex App Server framing and shutdown compatibility;
- Codex-to-MCP initialization and eight-tool discovery;
- form and model behavior;
- cross-host behavior and large-worktree baseline performance;
- causal benefit, saved review time, and return on investment; and
- whether the product owner accepts `REVIEW_READY_BASELINE_BACKED` as sufficient
  to proceed to a separately admitted Codex retry.

## Final validation

After the six admitted closeout-document changes, the final baseline comparison
returned:

```text
PASS=26 PRESERVED=49 FAIL=0 TOTAL=75
```

The six post-start paths were exactly:

- `STATUS.md`;
- this new closeout evidence;
- `docs/development-automation-contracts.md`;
- `docs/development-log/2026-08-24.md`;
- `docs/governance-mcp-adapter.md`; and
- `docs/product-requirements-automatic-governance.md`.

All are included by the captured task. All 49 excluded predecessor identities
remain `PRESERVED`. The baseline reload retains the original baseline and task
digests and 69 captured records.

Additional results:

- all 54 documentation tests pass;
- the two task-declared `python -m agentgov.cli` governance commands return zero
  without executing the CLI because that module has no executable entry point;
- the supported `python -m agentgov check task ... --repository .` replacement
  reports `PASS=3 WARN=1 FAIL=0 ADVISORY=3`;
- the supported `python -m agentgov check repository .` replacement reports
  `PASS=26 WARN=2 FAIL=0 ADVISORY=4`;
- `git diff --check` passes; and
- the bounded closeout-path secret-pattern scan has no matches.

The admitted task record is not rewritten. Its inert command spelling is a
known validation-contract defect, and the successful supported-entry checks are
supplemental evidence rather than a claim that the declared commands performed
those checks.

This fully specified task did not start a new alignment journey, so no new
native self-review completion is claimed. A distinct bounded current-Agent
review found the requirement exact, no Core or implementation change, exactly
six admitted post-start paths, zero baseline failures, all authority flags
false, and no privacy-boundary drift. It retains real Codex compatibility,
public integration, causal benefit, and product-owner acceptance as unknown.
This is advisory current-Agent judgment, not independent assurance.

The native task-completion tool is absent from the current tool surface, so no
completion record is fabricated.
