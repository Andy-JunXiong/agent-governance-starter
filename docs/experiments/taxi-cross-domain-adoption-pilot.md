# Taxi cross-domain adoption pilot — historical evidence closeout

Status: Closed historical record; strict timing unavailable

Closeout date: 2026-08-23

## Purpose and classification

This record closes the evidence account for the first Taxi cross-domain
adoption observed on 2026-07-24. It evaluates what AgentGov learned from one
real repository adoption; it is not a demonstration, a current product test,
or proof of a ten-minute adoption path.

The record is classified as a **historical assisted adoption with unavailable
strict timing**. It preserves observed friction and maintainer dispositions
without improving the historical result. It does not complete or replace the
separately planned automatic development-loop shadow pilot.

## Source and privacy boundary

- Historical adoption identity: Taxi commit
  `8145376ed31f58f6261591a3db74ac6c2387cd76` (`chore: adapt taxi governance`).
- Historical AgentGov evidence:
  [2026-07-24 development log](../development-log/2026-07-24.md) and
  [2026-07-25 development log](../development-log/2026-07-25.md).
- Later bounded consumer evidence:
  [2026-08-01 development log](../development-log/2026-08-01.md).
- Current supporting observation: one read-only repository check on
  2026-08-23 against Taxi commit
  `466e2164a15f72c69ee823dbb1f7528b2e769a80`, using AgentGov `0.3.0rc1`
  development source.

The Taxi repository remained a read-only research input during this closeout.
Its machine-specific absolute path is intentionally omitted. No Taxi code,
data, credentials, workflow content, business policy, generated runtime data,
or private payload is copied into this record.

## Historical adoption observation

The 2026-07-24 evidence establishes that governance inspection, dry-run,
scaffold creation, project adaptation, and repository checks completed. The
same evidence says the path required more assistance than the intended
ten-minute experience. Successful scaffold creation and `FAIL=0` did not mean
that project-specific governance or human decisions were complete.

The adoption commit identifies the resulting repository change. Its commit
timestamp is not a pilot start, stop, or duration measurement.

## Timing and assistance

- Timed start: not recorded.
- Timed stop: not recorded.
- Elapsed duration: not recorded.
- Timing source: unavailable; a commit timestamp is not substituted.
- Assistance required: yes, more than the intended adoption path.
- Exact intervention count, content, and timestamps: not recorded.

Because the start, stop, and elapsed time are unavailable, this record supports
no ten-minute pass, unassisted pass, completion-rate claim, or general
usability claim.

## Observed friction

Only friction preserved in the dated starter evidence is carried forward:

- building a wheel from a starter clone inside an already deeply nested
  Windows target path failed;
- direct installation avoided vendoring the starter into the target;
- invoking `python -m agentgov` was more reliable than assuming a scripts
  directory was present on `PATH`;
- the repository check required the exact `check repository .` command shape;
- an unrelated stale target-project environment was not a valid prerequisite
  for governance adoption; and
- successful command execution, scaffold creation, or `FAIL=0` could be
  mistaken for complete governance even while warnings, advisory findings,
  and human decisions remained.

These observations supported later installation and guidance work. They do not
measure how often another user or repository would encounter the same issues.

## Maintainer decisions

Later Taxi evidence records three historical decisions as resolved:

1. production transition actions retain a separate human approval boundary;
2. the initially incomplete evaluation evidence was reviewed into a recorded
   baseline rather than being hidden to obtain a green result; and
3. Python 3.11 was selected and verified side by side without overwriting the
   stale project environment.

On 2026-08-23 the human product owner selected the conservative disposition for
the remaining adoption follow-up:

- the explicit empty capability dependency graph is accepted as complete only
  for the current set of one declared capability; it does not prove that every
  real runtime or organizational dependency was discovered; and
- tracked capability artifacts are deferred because no concrete retained
  artifact and review need has been demonstrated. The artifact warning remains
  honest and non-blocking rather than being removed for presentation.

This disposition is bounded to the Taxi record. It is not a permanent
cross-project policy and does not prevent a later separately admitted artifact
task if real use evidence establishes a need.

## Current read-only check

The 2026-08-23 supporting check reported:

| PASS | WARN | FAIL | ADVISORY |
|---:|---:|---:|---:|
| 17 | 1 | 0 | 4 |

`PASS=17 WARN=1 FAIL=0 ADVISORY=4` is a current deterministic command result,
not the historical 2026-07-24 result. The one warning states that capability
artifacts are not configured. The advisory findings retain human judgment over
inventory completeness, control effectiveness, dependency completeness, and
approval or escalation fitness.

Static validation proves only the declared contract facts it checks. It does
not prove real-world completeness, control effectiveness, artifact value,
product benefit, or general usability.

## Semantic-relation boundary

The prepared
[Taxi semantic-relation gap analysis](semantic-relations/taxi-gap-analysis.md)
remains `Prepared; no Taxi observation recorded`. This historical adoption
closeout supplies no verified candidate relation, output-addressability need,
or net-new deterministic finding. No semantic schema, checker, report field,
migration, or Taxi policy is added.

## Conclusion and authority

The historical evidence account is closed with unavailable timing, recorded
assistance, bounded learning, and explicit maintainer dispositions. It is not a
successful ten-minute pilot and does not complete the future automatic
development-loop shadow pilot.

This record changes no AgentGov behavior or Taxi file. It authorizes no Git
operation, merge, publication, release, deployment, production workflow,
artifact configuration, or follow-on task.
