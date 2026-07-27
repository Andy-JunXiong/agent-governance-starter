# Taxi semantic-relation gap analysis

Status: Prepared; no Taxi observation recorded

Date prepared: 2026-07-27

## Purpose

Determine whether a real Taxi governance problem requires a new AgentGov
semantic relation, a small extension to an existing contract, an existing
standard reference, documentation only, or no change.

This is an evidence record for ADR-0006. It is not a semantic-model
specification and must not be completed from hypothetical examples.

## Evidence boundary

- Inspect only a Taxi repository the participant is authorized to use.
- Record the exact source repository path and commit before inspecting it.
- Do not copy Taxi code, data, credentials, infrastructure, policies, or
  domain-specific schema into AgentGov.
- Record wrong turns, missing declarations, and existing checks unchanged.
- Do not optimize the result toward a new feature.
- A successful AgentGov check does not prove semantic completeness.

## Session

- Date:
- Observer:
- Taxi repository source path:
- Taxi commit:
- Repository was non-sensitive and authorized: yes / no
- AgentGov version:
- Existing Taxi adoption record:
- Timing source:
- Timed start:
- Timed stop:

Stop if the source path, commit, authorization, or evidence boundary cannot be
recorded.

## Existing-contract baseline

Record the result before proposing a semantic remedy.

- Inventory result:
- Capability result:
- Reference result:
- Control Mapping result:
- Dependencies result:
- Evaluation result:
- Artifact drift result:
- Repository summary:
- Report path:

## Candidate gap record

Create one copy of this section for each observed problem. Do not create a
candidate merely because a relationship would be convenient to draw.

### Candidate identifier

- Short name:
- Observed repository fact:
- Governance consequence:
- Exact current file or finding:

### Authority and addressability

- Authoritative subject:
- Subject identity source:
- Authoritative object:
- Object identity source:
- Required granularity: capability / output / evidence / artifact / other
- Does the current capability contract provide a stable address for that
  granularity?
- If an output must be addressed, can the existing `output_schema` plus JSON
  Pointer or JSON Schema `$anchor` identify it safely?
- Would either endpoint be a new free-form name?

If an endpoint lacks an authoritative stable identity, stop relation design
and evaluate identity/addressability as the actual gap.

### Existing mechanisms considered

| Existing authority | Can it express the fact? | Evidence and limitation |
|---|---|---|
| Governance Inventory |  |  |
| Capability manifest and input/output schemas |  |  |
| Control Mapping |  |  |
| Capability Dependencies |  |  |
| Evaluation evidence references |  |  |
| Artifact provenance and drift |  |  |
| Repository report or documentation |  |  |

### Net-new validation value

List every proposed finding, its complete precondition, authoritative inputs,
and why an existing check does not already emit it.

| Finding | Deterministic preconditions | Authority source | Existing-check overlap | Status |
|---|---|---|---|---|
|  |  |  |  | PASS / WARN / FAIL / ADVISORY |

- Net-new deterministic finding after overlap is removed:
- Structural fact that could trigger human review:
- Judgment reserved for a human:

Do not claim that the checker can decide evidence sufficiency, business truth,
domain completeness, or authority fitness.

### Remedy decision

Apply the remedy order from ADR-0006:

1. existing contract or standard reference;
2. smallest compatible extension to an existing contract;
3. one bounded experimental relation;
4. defer.

- Selected remedy:
- Why higher-priority remedies are insufficient:
- Backward-compatibility effect:
- Adoption and migration cost:
- Ten-minute adoption-path effect:
- Proposed owner:
- Decision status: pending / admitted-for-second-pilot / rejected / deferred

## Output-addressability decision

Complete this section even if no relation candidate is admitted.

- Does Taxi require evidence to map to a specific output rather than the whole
  capability?
- Does the output schema already expose a stable JSON Pointer or `$anchor`?
- Would schema refactoring silently change the address?
- Would an optional `output_evidence` field in the Capability or Evaluation
  contract express the need without a relation file?
- Is output-level mapping useful to a second domain?
- Decision:
- Evidence:

## Pilot conclusion

- Candidates observed:
- Candidates rejected because existing checks already cover them:
- Candidates rejected because an endpoint lacks authoritative identity:
- Candidates best solved by an existing-contract extension:
- Candidates eligible for a second-domain pilot:
- Semantic relation file required: yes / no / unresolved
- Smallest next action:
- Maintainer:
- Review date:

## Promotion or kill review

Do not complete until Taxi and one second-domain pilot have been reviewed.

- Second domain and record:
- Same missing relation reproduced: yes / no
- Net-new deterministic finding reproduced: yes / no
- Single source of truth preserved: yes / no
- Ten-minute adoption path preserved: yes / no
- Outcome: promote / fold into existing contract / delete / archive / defer
- Rationale:
- Runtime experiment removed if not promoted: yes / not applicable
- Reviewer:
- Decision date:

Regardless of outcome, retain this review as evidence for why the experiment
was promoted, folded into an existing contract, deleted, archived, or
deferred.
