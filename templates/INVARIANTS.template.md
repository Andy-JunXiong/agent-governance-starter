# Architecture invariants - {{PROJECT_NAME}}

## Purpose

This register lists constraints that ordinary feature work must preserve. It
does not duplicate every ADR or coding convention. Each invariant must identify
its authority, enforcement point, and verification method.

## Status semantics

- `proposed`: under review and not yet an enforced project constraint;
- `active`: approved and currently enforced;
- `deprecated`: still visible during migration but must not be used for new
  work;
- `retired`: no longer enforced; replacement or retirement evidence is linked.

## Enforcement semantics

- `deterministic`: code, schema, configuration, or a repeatable check can decide
  pass or fail;
- `review`: a named human review is required because the boundary cannot be
  reduced to a reliable static check;
- `hybrid`: deterministic checks cover part of the boundary and review covers
  the remainder.

Do not label a judgment-based rule as deterministic merely because a document
contains matching words.

---

## {{INVARIANT_ID}} - {{INVARIANT_NAME}}

- Status: `{{INVARIANT_STATUS}}`
- Owner: `{{OWNER}}`
- Authority: `{{ADR_OR_POLICY_REFERENCE}}`
- Enforcement: `{{ENFORCEMENT_MODE}}`

### Statement

{{ONE_CLEAR_RULE_THAT_MUST_REMAIN_TRUE}}

### Rationale

{{WHY_BREAKING_THIS_RULE_WOULD_HARM_THE_SYSTEM}}

### Applies to

- `{{PATH_COMPONENT_OR_WORKFLOW}}`

### Does not apply to

- `{{EXPLICIT_EXCEPTION_OR_NONE}}`

### Enforcement points

- `{{CODE_SCHEMA_POLICY_OR_REVIEW_LOCATION}}`

### Verification

- Automated: `{{COMMAND_CHECK_OR_NOT_APPLICABLE}}`
- Review: `{{REVIEW_ROLE_OR_NOT_APPLICABLE}}`
- Passing evidence: `{{EXPECTED_ARTIFACT_OR_RESULT}}`

### Failure response

{{STOP_ESCALATE_ROLL_BACK_OR_MIGRATE_ACTION}}

### Change history

| Date | Change | Authority |
|---|---|---|
| {{YYYY-MM-DD}} | Created | `{{ADR_OR_APPROVAL_REFERENCE}}` |
