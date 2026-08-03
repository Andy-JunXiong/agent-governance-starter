# AGENTS.md - Agent Governance Starter Kit

## Purpose

This repository develops a portable, repo-native governance starter kit for
AI-assisted software development.

## Scope

In scope:

- governance methodology and templates;
- deterministic static checks;
- prompt-capability metadata and evaluation-readiness contracts;
- a minimal Python CLI;
- sanitized reference examples from real projects.

Out of scope:

- importing AI Radar runtime code or data;
- copying project-specific infrastructure, credentials, deployment targets, or
  business workflows;
- autonomous merge or deployment;
- pretending advisory judgment can always be reduced to a static check;
- becoming a general-purpose LLM evaluation platform.

## Non-negotiable rules

1. Keep the package independent from AI Radar and other reference projects.
2. Never copy credentials, private data, generated runtime data, or secret-like
   strings from a reference repository.
3. Mark every check as deterministic or advisory. Advisory findings must not be
   presented as objective failures.
4. Do not publish a governance coverage percentage without a documented
   denominator, applicability rules, and weighting model.
5. Do not weaken or delete failing tests to make a change pass.
6. Do not commit, push, publish, or release without explicit human approval.
7. Keep the starter lightweight; additions must support the documented
   ten-minute adoption path.
8. When behavior, product scope, release identity, commands, or user journeys
   change, update every affected source of truth in the same bounded change.
   Check at least `README.md`, `STATUS.md`, development plans/logs, ADRs or
   contracts, user guides, release metadata, public HTML, localized pages, and
   the tests that protect those surfaces. Historical records may keep their
   original version facts, but must be clearly labeled when superseded.

## Development workflow

For meaningful changes:

1. state the goal, non-goals, acceptance signals, and stop conditions;
2. inspect only the directly related files and contracts;
3. prefer a small vertical slice;
4. add tests for behavior and policy semantics;
5. run the relevant tests and report unresolved gaps;
6. keep commit, push, and release as separate human-controlled actions.

## Source boundaries

Reference repositories are read-only research inputs. Record the source path
and reuse decision in `docs/ai-radar-extraction-map.md` before adapting a
pattern. Copy concepts and contracts deliberately; do not mechanically copy
project-specific policy text or runtime code.

Use these classifications:

- `generic-reusable`: portable with minimal normalization;
- `rewrite-required`: useful pattern whose current wording or code is coupled;
- `reference-only`: evidence that the approach works, not starter-kit source;
- `ai-radar-specific`: excluded from this project.

## Validation

The baseline validation command is:

```powershell
$env:PYTHONPATH = "src"
python -m unittest discover -s tests -v
```

Future CLI checks must have fixture-based tests for passing, warning, failing,
advisory, and not-applicable behavior where those states are supported.
