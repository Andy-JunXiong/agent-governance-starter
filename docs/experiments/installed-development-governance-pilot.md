# Installed development-governance pilot

## Status

Date: 2026-08-02

Result: the exact locally built wheel completed an independent-repository
`start -> context consumption -> code change -> check -> finish -> monitor`
loop. The successful completion state was `verified`, with the architecture
conclusion retained as `ADVISORY`.

This was an internal Coding Agent pilot operated by the project developer. It
was not an uncoached human study, a published release test, cross-platform
evidence, or proof that AgentGov caused the correct result.

## Pilot contract

Environment:

- Windows;
- Python 3.11.9 runtime;
- fresh temporary virtual environment;
- fresh disposable Git repositories outside the AgentGov source tree;
- no AI Radar code, data, configuration, runtime dependency, or business rule;
- no project-source `PYTHONPATH` during installed-package execution.

Exact candidate:

- wheel: `agent_governance_starter-0.2.1-py3-none-any.whl`;
- size: `247865` bytes;
- SHA-256:
  `9ead26aaebe84317723018bf4f880100e513a3873b08bfb33917ec7beb2a884b`;
- installation: fresh virtual environment with `pip install --no-deps`;
- imported module location: the temporary environment's `site-packages`, not
  the AgentGov source checkout.

The wheel reports `agentgov 0.2.1` because development version promotion is
still deferred. The digest distinguishes this source-built candidate from the
published stable 0.2.1 artifact. This naming collision is a release blocker:
the development line must become `0.3.0.dev0` or an RC identity before any
candidate is distributed.

## Independent repository task

The repository contained one deliberately small pure-Python greeting
capability. Its admitted task required:

- `greet(name)` to trim a non-blank name and return `Hello, <name>!`;
- blank input to raise `ValueError`;
- no filesystem, network, environment, clock, logging, or process access;
- changes only to `src/greeting.py` or `tests/test_greeting.py`;
- `python -m unittest discover -s tests -v` as validation;
- no commit, push, PR, merge, deployment, or scope widening.

The task contract, requirement, product goal, ADR, invariants, `AGENTS.md`,
architecture overview, Skill, source stub, and tests were committed as a clean
disposable baseline before governance started. Baseline commits existed only
inside the temporary pilot repositories.

## Context routing and actual consumption

The installed Router selected eight artifacts:

| Selected artifact | Why selected | Coding Agent consumption | Observed effect |
|---|---|---|---|
| `AGENTS.md` | Required repository authority | Read | No scope widening or downstream Git action |
| `AI_CONTEXT.md` | Required architecture navigation | Read | Followed the ADR and invariant path |
| `agent-skills/bounded-python-change/SKILL.md` | `task.admitted` trigger | Read | Used the smallest-change and validation workflow |
| `docs/adr/0001-pure-greeting.md` | Declared architecture | Read | Kept implementation deterministic and I/O-free |
| `docs/adr/INVARIANTS.md` | Declared invariant | Read | Preserved blank-input and purity rules |
| `docs/product-goal.md` | Declared parent objective | Read | Added no unrelated interface or infrastructure |
| `docs/requirements/greeting.md` | Declared requirement | Read | Implemented trimming, output, and rejection behavior |
| `governance/tasks/greeting.json` | Current admitted task | Read | Changed only `src/greeting.py` and ran declared validation |

Registry counts for capability, control, dependency, and evaluation artifacts
were zero. No unrelated AgentGov repository documentation or AI Radar material
entered the task-specific output. Reference-mode JSON carried paths, reasons,
roles, hashes, triggers, limits, and denied authority without embedding source
content. Eight references were manageable for this small task; one run cannot
establish the right context size for larger repositories.

The implementation was:

```python
def greet(name: str) -> str:
    normalized = name.strip()
    if not normalized:
        raise ValueError("name must not be blank")
    return f"Hello, {normalized}!"
```

This consumption statement is an internal operator observation. The current
event contract records selected governance paths, not an independently
attested proof that a Coding Agent read or obeyed them.

## Fail-closed observations

### Build environment gate

An initial offline `--no-build-isolation` wheel attempt failed because the
available setuptools 65.5.0 did not satisfy the declared `setuptools>=69`
build requirement and could not parse the SPDX license string. Normal PEP 517
build isolation satisfied the declared requirement and built the candidate.
The validator and package metadata were not weakened.

### Invalid Skill gate

The first context attempt rejected the pilot's initially abbreviated Skill. It
reported the missing use condition and required headings. The Skill was fixed
and committed to the disposable pre-task baseline before context selection was
retried. AgentGov did not silently ignore invalid governance.

### Validation-artifact gate

The first governed repository intentionally lacked Python ignore rules.
Validation passed functionally but created untracked `__pycache__` files, so
fresh evidence became `stale` and completion remained `needs_evidence`.
AgentGov identified both repository-relative paths and did not hide them or
automatically edit `.gitignore`.

The failed repository was preserved. A second fresh repository was created
from the pre-task baseline, and its maintainer added standard `__pycache__/`
and `*.py[cod]` rules before the task started. The Coding Agent did not change
governance or ignore policy inside the admitted task.

### Interactive boundary

The automation harness could render the installed CLI dry-run but did not
provide a real TTY. The actual start used the installed package's same
plan/confirmation/apply functions with a simulated exact `START` response,
after this pilot had explicit human authorization. Existing CLI tests exercise
real-terminal detection and exact `START`/`REPLACE` semantics. This pilot does
not count as an uncoached interactive-start observation.

## Successful end-to-end result

The corrected fresh repository recorded:

| Stage | Observed result |
|---|---|
| Installed version | `agentgov 0.2.1`, loaded from isolated `site-packages` |
| Start preview | 8 selected governance paths, 2 disclosed local targets, all authority false |
| Scope check | `PASS=1 FAIL=0 ADVISORY=1` |
| Validation | 2 unittest cases passed; persisted event outcome `passed` |
| Completion | `verified`; fresh and in-scope checks passed; architecture remained advisory |
| Monitor | 1 task, 4 events, 1 start, 1 check, 1 validation, 1 verified completion |
| Git state after task | only `src/greeting.py` modified plus untracked `.agentgov/` local state |

The self-contained HTML Monitor was generated at the default local path. Its
JSON projection declared `local_session`, `partial` history, four events, and
cross-stage discovery unavailable. The `task.started` event listed all eight
selected governance references. Later events did not claim context
consumption.

## Claim layers

Observed:

- the exact wheel digest and isolated import location;
- selected governance paths and routing reasons;
- the file changed by the Coding Agent;
- scope, command exit, evidence freshness, completion, and Monitor event facts;
- the invalid-Skill and validation-artifact failures.

Inferred:

- the guided chain is usable for this small independent Python task;
- strict governance and artifact checks surfaced setup defects early enough to
  correct the repository before claiming completion.

Unknown:

- uncoached human adoption friction;
- whether another Coding Agent would read or follow the same context;
- effectiveness on a large or multi-language repository;
- causal benefit, ROI, requirement correctness, architecture correctness, or
  validation sufficiency;
- cross-machine and CI history, which awaits explicit redacted export.

## Product decisions from the pilot

1. Keep invalid Skills and non-ignored validation artifacts fail-closed; do not
   weaken checks to improve the happy path.
2. Add an actionable start-time readiness observation for likely validation
   artifacts before product release, without editing `.gitignore`
   automatically.
3. Promote the development package identity before any 0.3 candidate build so
   a source wheel cannot masquerade as published stable 0.2.1.
4. Keep real interactive confirmation as the default. Any future non-TTY apply
   mechanism requires an explicit reviewed plan identity and separate threat
   model; this pilot does not authorize it.
5. Proceed next to the redacted development-event export contract and honest CI
   artifact wiring. Do not label CI replay as exported development history.

No AgentGov source commit, push, tag, release, external publication, workflow
change, deployment, or reference-repository mutation occurred during this
pilot.

## Source-repository validation

- complete suite: 485 tests passed with one platform-limited skip;
- repository governance: `PASS=16 WARN=2 FAIL=0 ADVISORY=4`;
- admitted pilot task: `PASS=6 WARN=0 FAIL=0 ADVISORY=1`;
- `git diff --check`: passed.

The two baseline commits described above were confined to disposable temporary
pilot repositories. The AgentGov product repository remained uncommitted.
