# ADR-0006: Admit semantic relations only from verified gaps

Status: Accepted

Date: 2026-07-27

## Decision gate

Decide whether AgentGov should add a general governance semantic model or a
new relation contract before cross-domain evidence demonstrates a gap in the
existing repository-native contracts.

## Context

The Governance Inventory, capability manifest, control mapping, capability
dependencies, evaluation bundle, artifact provenance, and repository report
already form an implicit governance semantic model. They declare identities,
owners, risks, controls, dependencies, evidence readiness, source references,
and authority boundaries through separate versioned contracts.

A proposed semantic layer could connect outputs, evidence, approvals, tools,
data sources, and domain objects. Predefining those entities and relations
would also risk creating a second source of truth, an open-ended ontology
language, and adoption work unsupported by observed repository problems.

The current capability contract references one input schema and one output
schema. It does not assign stable identities to individual outputs. A relation
such as `derived_from` therefore cannot use a free-form output name without
introducing an unresolved endpoint. The verified gap may be output
addressability or output-level evidence mapping rather than the absence of a
separate relation file.

The next evidence cycle uses Taxi first and a second domain such as GLAP only
to test whether the same missing relation recurs. No reference-project code,
data, policy, or domain object is admitted into AgentGov Core by this decision.

## Decision

Do not implement a general semantic model, entity registry, relation registry,
or semantic checker now.

Admit a semantic feature by rejection-by-default. A candidate must start with
one observed governance problem that the existing contracts cannot express.
The admission question is not whether a relation can be represented, but
whether it produces new, actionable governance evidence without duplicating
an existing authority.

Use this remedy order:

1. Reuse an existing authoritative AgentGov contract or a standard reference
   mechanism such as a schema reference, JSON Pointer, or JSON Schema anchor.
2. Extend the closest existing AgentGov contract with the smallest compatible
   optional field.
3. Introduce one bounded experimental relation contract only when the first
   two remedies cannot express the verified gap.
4. Defer the feature when its governance value does not justify adoption,
   migration, and maintenance cost.

Facts expressible by Inventory, Capability, Control Mapping, Dependencies,
Evaluation, Artifact, or report contracts must remain in those contracts.
An experimental relation must reference their identities and must never
redeclare a capability, control, owner, authority, evidence item, or risk.

Do not predefine `requires_approval`, `relates_to`, `capability_reads`,
`capability_produces`, or `derived_from`. Each relation requires separate
admission evidence. In particular:

- approval relations require an authoritative subject, authority, and risk
  declaration before any missing-approval result can be deterministic;
- generic `relates_to` has no admitted governance check;
- reads and produces declarations may duplicate capability contracts and
  provenance;
- output-level `derived_from` remains only a candidate until stable output
  addressing and net-new checks are demonstrated.

Any future deterministic finding must state all machine-verifiable
preconditions and the authoritative source for each one. Human sufficiency,
business truth, evidence quality, and authority fitness remain review
judgments. A checker may state the structural fact that triggered review, but
must not imply that it evaluated semantic adequacy.

Passing a future semantic contract would prove only that declared structural
conditions hold. It would not prove governance completeness, system safety,
evidence sufficiency, or authorization to merge, publish, release, deploy, or
perform a production action.

## Owns

- Admission criteria for new cross-contract semantic relations.
- The existing-contract-first remedy order.
- The boundary between structural findings and semantic review prompts.
- Pilot promotion, deletion, and archival conditions.
- Compatibility expectations for any future optional experiment.

## Does not own

- Taxi, GLAP, AI Radar, or other domain models.
- A general ontology, RDF or OWL model, graph database, or SaaS control plane.
- Runtime policy enforcement or automatic discovery.
- Approval, change, decision, incident, tool, model, prompt, or data-source
  entity systems.
- Governance scoring or a completeness percentage.
- Merge, publication, release, deployment, or production authority.

## Consequences

- No schema, CLI command, report field, or migration is added by this ADR.
- Taxi analysis begins by testing the limits of existing contracts.
- Output addressability is evaluated before any output-to-evidence relation.
- A small extension to an existing contract is preferred over a parallel
  relation file.
- Cross-domain repetition is necessary but not sufficient for promotion.
- Some plausible relations may remain documentation-only or be rejected.

The additional design work protects the ten-minute adoption path and avoids
maintaining declarations whose only check is endpoint existence already
covered elsewhere.

## Alternatives considered

### Implement a general semantic model now

Rejected because the proposed entity and relation set is broader than current
evidence and would turn a lightweight repository checker toward an ontology
platform.

### Add a fixed experimental relation set now

Rejected because the initial candidates contain unresolved identities,
duplicate existing contracts, or lack net-new deterministic findings.

### Add output identifiers to every capability now

Rejected pending evidence that output-level addressability is required across
domains and cannot use existing schema references safely.

### Keep the implicit model undocumented

Rejected because an explicit admission boundary prevents future features from
silently creating parallel authorities.

## Implementation plan

1. Record Taxi observations using
   `docs/experiments/semantic-relations/taxi-gap-analysis.md`.
2. For each observed problem, identify the authoritative subject and object,
   the existing mechanisms considered, the net-new deterministic finding, and
   the smallest remedy.
3. Test stable output addressing through existing schema references before
   proposing a new field.
4. If Taxi supports a candidate, repeat the analysis in a second domain such
   as GLAP without adding domain-specific concepts to AgentGov Core.
5. Record a promotion review whether the outcome is promotion, folding the
   remedy into an existing contract, deletion, archival, or deferral.
6. Implement no schema or checker until that review admits one bounded slice.

## Validation

Current deterministic validation confirms that:

- the existing capability schema has an `output_schema` reference but no
  contract-level identity for individual outputs;
- canonical Inventory, Capability, Control Mapping, and Dependencies contracts
  exist;
- the repository report already separates `PASS`, `WARN`, `FAIL`, and
  `ADVISORY`.

Future admission evidence must enumerate every proposed deterministic finding
and subtract checks already supplied by inventory closure, safe reference
validation, evidence references, and artifact drift.

If an optional experiment is later implemented, repositories without its file
must retain the same exit code, finding order, JSON report bytes, and Markdown
report bytes for stable fixtures. Strict byte comparison is the default;
normalization requires a documented unavoidable unstable field.

Human review must decide whether a relation represents the real domain,
whether evidence substantively supports an output, and whether an accountable
authority is appropriate.

## Rollback or replacement

After Taxi and one second-domain pilot, record the decision and evidence even
if no feature is admitted. If promotion criteria are not met, delete any
experimental runtime contract or validator before the next minor release and
archive the learning in documentation.

A later ADR may replace this decision only if it preserves single sources of
truth, deterministic/advisory separation, backward compatibility, explicit
human authority, and evidence-based admission.
