# Case study: repository-native agent governance

## Context

AI Radar accumulated practical rules for coding-agent scope, architectural
decisions, prompt metadata, evidence readiness, source drift, and human approval.
Those patterns were useful beyond one product, but its runtime code, AWS
infrastructure, private data, and business workflows were not portable.

Agent Governance Starter Kit extracts the reusable governance contracts and
implements them as an independent Python package. AI Radar is a documented
reference case, not a runtime dependency. The extraction and exclusion choices
are recorded in the [AI Radar extraction map](ai-radar-extraction-map.md).

## Problem

Agent instructions, prompt implementations, JSON schemas, evaluation cases,
review artifacts, and approval rules often exist as separate files. Their mere
presence does not answer whether they describe the same capability, whether
the evidence matches the declared readiness, or whether implementation sources
changed after review.

The product problem is therefore not simply generating an AGENTS.md file. It is
making capability identity, evidence state, artifact integrity, deterministic
checks, and human-review boundaries visible in one repository-local chain.

## Product decisions

- **Repository-native before SaaS:** policies and evidence remain beside the
  code so they are versioned, reviewable, and usable without a control plane.
- **Deterministic checks stay separate from judgment:** schema, path, hash, and
  declared-readiness facts may pass or fail; architecture sufficiency and
  approval quality remain human decisions.
- **Missing evidence stays incomplete:** `needs_seed_cases` and other early
  readiness states remain visible instead of being converted into success.
- **No unsupported coverage score:** the project does not publish a governance
  percentage without applicability, denominator, evidence, and weighting rules.
- **No automatic overwrite:** initialization accepts only a new or empty target,
  and generated artifacts require explicit replacement.
- **Hashes detect drift, not quality:** source hashing can show that declared
  content changed after artifact generation; it cannot certify correctness.

## Trust boundary

The CLI is trusted to perform deterministic local checks over readable
repository files. It validates supported schemas, repository-relative paths,
evaluation metadata, agent-skill contracts, generated artifact state, and
source hashes.

It is not trusted to decide whether prose is good policy, whether an
architecture is sufficient, whether an evaluation proves model quality, or
whether a high-risk transition should proceed. Those questions remain explicit
`ADVISORY` findings or human approval steps. A passing command never grants
authority to merge, publish, release, or deploy.

## Architecture

The implemented chain is:

```text
Capability manifest
  -> repository-local references
  -> evaluation readiness
  -> deterministic review artifact
  -> manifest/source/generated-output drift checks
  -> repository findings and Markdown or JSON v1.0 report
  -> accountable human review
```

The architecture deliberately uses files and a local CLI rather than a hosted
database. This keeps v0.1 inspectable and makes its claims reproducible from a
repository checkout.

## Implementation

The dependency-free runtime targets Python 3.11 or newer. The CLI exposes
initialization, capability and reference checks, evaluation-readiness checks,
agent-protocol checks, deterministic artifact export and verification,
repository checks, and Markdown/JSON reporting from one findings model.

The capability schema records purpose, input/output contracts, callers, owner,
risk, model route, human-review stages, evaluation readiness, and provenance.
Artifact export records canonical manifest and source hashes without copying
source content into the artifact. Repository checks aggregate the results as
`PASS`, `WARN`, `FAIL`, and `ADVISORY` while preserving stable exit semantics
for automation.

## Validation

Fixture-based tests cover valid and invalid capability contracts, path
containment, malformed data, honest incomplete readiness, false maturity
claims, artifact replacement, source and generated-output drift, repository
aggregation, reporting, and CLI exit behavior. CI installs the package and runs
the suite on Ubuntu and Windows with Python 3.11, 3.12, and 3.13.

An isolated wheel rehearsal verified the complete clean-repository workflow.
An internal usability rehearsal did not establish the ten-minute adoption claim:
timing evidence was missing and the participant needed help interpreting the
remaining human decisions. That result was preserved rather than rewritten as
a pass, and it directly informed clearer initialization and report guidance.

## Competitive and market learning

Generic multi-agent configuration linting has become a crowded category. This
project is therefore not positioned as another broad AGENTS.md or CLAUDE.md
linter and does not attempt to score instruction-writing quality.

Its narrower focus is the connection between capability declarations,
repository evidence, evaluation readiness, artifact integrity, deterministic
failure semantics, and human-review contracts. That positioning is still a
product hypothesis; broader productisation requires interviews, repository
pilots, and observed repeat use rather than a uniqueness claim.

## Current limitations

- Initialization supports only new or empty target directories. Existing
  repositories have read-only inspection and explicit create-missing-only
  adoption, but policy reconciliation remains manual.
- The CLI discovers a small documented set of existing instruction paths but
  does not read, reconcile, or judge their policy content.
- Static checks cannot judge semantic policy quality, architecture quality, or
  model-output quality.
- The project is not a runtime security boundary, compliance certification, or
  deployment authorization system.
- The JSON v1.0 repository-report contract exists, but no web UI, API server,
  GitHub Action integration, or repository discovery currently exists.
- A successful internal rehearsal is not evidence of universal adoption speed.

## Future product direction

The versioned JSON repository report now preserves the current finding
semantics as a stable integration boundary. A future UI could consume that
contract to show capability ownership, readiness, drift, exceptions, and
human-review queues without duplicating checker logic or moving policy
authority out of the repository.

That UI does not currently exist. Before building it, the project needs broader
user validation and a read-only adoption path for existing repositories. Those
are future directions, not capabilities claimed by v0.1.
