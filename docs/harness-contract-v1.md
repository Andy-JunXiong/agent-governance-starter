# Harness Contract v1

Status: implemented as a dependency-free offline contract, evaluator, and
fixture suite in development source. It is not yet a CLI, live host Adapter,
controlled-ablation runner, Dashboard feed, release, or consumer integration.

## Purpose

Harness Contract v1 turns a privacy-bounded expected and observed transition
trace into one deterministic answer:

> Where did the observed journey first diverge from the expected journey?

The contract does not ask whether AgentGov generally works. It keeps three
different questions separate:

1. Did the Agent select the expected governance capability?
2. Did AgentGov make the correct deterministic governance decision?
3. What transition outcome actually occurred?

A passing governance decision does not imply that the Agent supplied valid
input, that a host presented a human form, or that governance caused the final
outcome. Each channel has its own status, reason code, evidence references, and
bounded summary.

## Boundary

The v1 slice consumes normalized JSON only. It does not launch an Agent,
inspect a repository, replay a model session, invoke a host hook, modify a
consumer, or make a human decision. The schema and evaluator grant no task,
code, exception, Git, publication, release, deployment, external-write, or
session authority.

The following data is prohibited:

- raw prompts or transcripts;
- model output or reasoning;
- raw tool input or output;
- source content or credentials;
- absolute paths;
- unbounded payloads.

Repository evidence references are relative paths. Every object uses an exact
field allow-list, and bounded arrays, strings, identifiers, and transition
counts prevent a fixture from becoming a transcript container.

## Contract shape

`agentgov.harness-run` 1.0 contains:

- a stable run and scenario identity;
- evidence strength and repository-relative source references;
- Adapter, host, provider, repository-correlation, and capability facts;
- ordered expected and observed transition traces;
- the three independent evidence channels;
- the declared and deterministically derived First Deviation;
- a Harness result, terminal facts, privacy boundary, claim limits, and denied
  authority.

The machine-readable schema is
[`schemas/harness-contract-v1.schema.json`](../schemas/harness-contract-v1.schema.json).
The dependency-free parser and evaluator are in
[`src/agentgov/harness_contract.py`](../src/agentgov/harness_contract.py).

## Host capability honesty

The host declaration records observation, mediation, blocking, execution,
decision delivery and recording, human-origin assurance, failure and timeout
behavior, coverage, configuration, bypass conditions, confidence, and evidence.
Provider identity is metadata; it does not grant a host capability.
Concrete booleans separately declare action observation, trusted pre-action
hooks, human decision UI, mediation, blocking, post-action evidence, and a
semantic materializer.

Harness results reuse the existing governance effects:

| Effect | Honest meaning |
| --- | --- |
| `OBSERVE` | The Adapter recorded a transition fact. |
| `ADVISE` | The result supplies non-authoritative guidance. |
| `MEDIATE` | The transition was routed through a declared decision boundary. |
| `BLOCK` | A supported pre-action mechanism prevented the exact named transition. |

`BLOCK` is invalid unless the host declares `block_mode: supported`, both
`pre_action_hook` and `block_action` are true, the result names the prevented
transition, and the effect had not already completed.
A post-action observation can report a violation but cannot claim rollback or
prevention.

## Transition trace and First Deviation

Each trace contains unique, contiguous transition identities in lifecycle
order. Expected and observed traces must use the same ordered identities and
stages. If a stage was not reached, the normalized outcome must say so
explicitly rather than silently omitting the stage.

The evaluator compares each pair in order using:

1. actor class;
2. normalized outcome;
3. governance effect;
4. runtime disposition;
5. completed-side-effect fact.

The first mismatching pair is the First Deviation. A bounded observed reason
code becomes the deviation code; otherwise the evaluator derives a stable
field-mismatch code. A later failure cannot replace an earlier deviation.
The declared `first_deviation` object must exactly match the derived result or
the contract is invalid.

Structural and semantic contract violations are deterministic failures.
Channel summaries and broader judgments remain evidence-bounded observations;
the evaluator does not turn them into objective product-effectiveness claims.

## Evidence strength

Harness Contract v1 names four levels without automatically promoting between
them:

1. `observed`: one bounded observed run;
2. `paired_counterfactual`: one governed run and one controlled ablation;
3. `repeated_intervention`: repeated paired evidence with a stable difference;
4. `cross_context_replication`: the same direction reproduced across declared
   consumers, hosts, or Agents.

A fixture passing validation does not upgrade its evidence strength. The
contract publishes no causal-effectiveness, governance-coverage, or protection
percentage.

## Reference fixtures

Two sanitized fixtures establish the first vertical slice:

- `matching-no-write.json` supplies a no-deviation mediated human decline that
  leaves the repository unchanged;
- `airbnb-uncoached-baseline.json` records correct Agent selection, invalid
  proposal materialization, AgentGov's atomic rejection, later absent form
  mediation, and a fail-safe no-write terminal outcome.

The AIRBNB fixture deterministically locates the First Deviation at
`proposal_materialization` with code `normalized_scope_path_rejected`. The
later `human_form_not_presented` result remains visible but cannot overwrite
the earlier deviation. The fixture retains no consumer source or replay
payload.

## Python use

The first slice is intentionally a source API rather than a public CLI:

```python
from pathlib import Path

from agentgov.harness_contract import evaluate_harness_run, load_harness_run

document = load_harness_run(Path("path/to/normalized-run.json"))
evaluation = evaluate_harness_run(document)

if not evaluation.valid:
    raise ValueError(evaluation.errors)

print(evaluation.first_deviation)
```

## Product connection

This slice builds on the host-enforcement capability audit, the existing
host-interaction and authority contracts, the privacy-bounded replay normalizer,
and the 2026-08-14 uncoached AIRBNB baseline. It makes the baseline repeatable
without another model call or consumer mutation.

The next capability is not yet decided. Reasonable later connections include a
read-only CLI, additional deterministic mechanism fixtures, Codex pre-action
conformance, or a separately designed controlled-ablation runner. None is
authorized by this contract.
