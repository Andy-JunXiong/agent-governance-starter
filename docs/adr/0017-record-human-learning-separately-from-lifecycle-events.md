# ADR-0017: Record human Learning separately from lifecycle events

Status: accepted on 2026-08-25 by the human product owner through governed
alignment and exact task admission.

## Decision gate

Choose how to record a human judgment about a repeated Protection Event class
without corrupting task lifecycle state or presenting judgment as resolution.

## Context

Monitor 1.8 identifies repeated Protection Event classes within one current
observation. A candidate may span several tasks, while each existing
`agentgov.governance-event` belongs to exactly one task and participates in
session state, completion, and handoff projections. Adding a cross-task review
to that stream would give the record a false task owner and could change the
latest lifecycle state.

Human attribution is also not authenticated personal identity. The product
needs only the accountable workflow role and one bounded disposition. Free
text, names, and retrospective inference from later passing events are not
required.

## Decision

Use a separate, immutable `agentgov.learning-review` 1.0 local record under
`.agentgov/learning-reviews`. Bind each record to one signal class and the
sorted identities of every matching Protection Event in the exact current
candidate. A deterministic digest makes a preview stale when that candidate
changes.

The actor is the canonical `human_product_owner` role. Disposition is one fixed
enum: confirmed constraint gap, false positive, intentional override, consumer
configuration needed, improvement candidate, or no change needed. The record
has human-judgment semantics and grants no resolution, code, scope, exception,
Git, release, or deployment authority.

Creation is preview-first and requires exact interactive confirmation. The
command reloads and revalidates current events immediately before exclusive
creation. Monitor may project only records whose digest still matches a
current candidate. Stale records remain immutable but are not presented as the
current judgment.

## Owns

- Learning review identity, attribution, disposition, freshness, and authority
  limits;
- create-only local storage and exact candidate binding;
- Monitor presentation of matched versus unavailable human judgment.

## Does not own

- task lifecycle, completion, handoff, or Protection Event resolution;
- authentication of an individual person;
- amendments, revocation, supersession, or conflict resolution;
- redacted development-event export, cross-window trends, causal benefit, or
  external synchronization.

## Consequences

Cross-task Learning judgment no longer needs a synthetic task identity and
cannot alter lifecycle state. The cost is a second local input contract. The
existing redacted event export intentionally carries no Learning review, so an
export-backed Monitor must show human judgment as unavailable.

An exact-candidate digest favors evidence honesty over persistence: adding a
new same-class Protection Event makes the earlier review stale. A later
contract may define amendment or multi-observation behavior.

## Alternatives considered

### Extend the governance lifecycle event

Rejected because its single-task identity and latest-event projections do not
represent a cross-task candidate safely.

### Store only a disposition count in Monitor output

Rejected because generated output is not an immutable source record and cannot
support freshness revalidation.

### Accept human notes as free text

Rejected for privacy, deterministic rendering, and claim-boundary reasons.

## Implementation plan

1. Add the strict record schema, validator, loader, and exclusive local write.
2. Add preview, exact confirmation, and pre-write candidate revalidation.
3. Advance Monitor to 1.9 with matched, stale, and unavailable source states.
4. Add fixtures, browser review, documentation, and full validation.

## Validation

Deterministic tests cover contract shape, every disposition, candidate digest,
staleness, unsafe state, confirmation denial, exclusive creation, Monitor
parity, and unchanged lifecycle/export contracts. Human usefulness and the
semantic quality of a disposition remain advisory and unknown until used.

## Rollback or replacement

The command and Monitor projection can be removed while preserving immutable
records as historical local evidence. A replacement ADR must define migration,
freshness, conflict, identity, export, and authority behavior without silently
reclassifying old judgments as resolution.
