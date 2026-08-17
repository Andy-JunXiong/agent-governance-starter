# Reproducible local wheel build validation — 2026-08-17

## Claim boundary

This is a local packaging and installed-help validation for committed starter
revision `514f5023d7883aeee648ddda63b3e944d4116eac`. It establishes that this
revision can produce one installable wheel when its declared build prerequisite
is available and a short Windows temporary path is used. It does not establish
reservation creation, interactive confirmation, bridge behavior, replay
behavior, consumer portability, publication readiness, or product
effectiveness.

No `RESERVE` input, reservation apply command, consumer initialization, marker
write, model session, Git remote operation, publication, release, or deployment
occurred. The existing global and pipx installations were not used as build or
install targets.

## Committed source and build prerequisite

Both build attempts used a fresh `git archive HEAD` of exact revision
`514f5023d7883aeee648ddda63b3e944d4116eac`. The two independently created
archives had the same SHA-256:
`54E3D66DD054ACF26DE8C2D9153848925233E10D50672B6164F7900ECF6DBC7A`.
The successful archive contained 630 members. It contained neither `.codex`
nor the uncommitted `src/agentgov/replay_correlation_bridge.py`, confirming
that working-tree-only content was excluded.

No suitable local build-tool wheel was cached. After explicit permission, one
fixed `setuptools 80.9.0` wheel was downloaded into the disposable tools
directory. Its SHA-256 was
`062D34222AD13E0CC312A4C02D73F059E86A4ACBFBDEA8F8F76B28C99F306922`.
It was installed with `--no-index --no-deps` only in disposable Python 3.11.9
build environments. No global package was upgraded.

## Build attempts

The first build reached `bdist_wheel` but failed while copying the long
`*.data/data/share/.../templates/admission-routing-policy.template.json` path.
No wheel was emitted. This was a Windows temporary-path-depth failure, not the
earlier metadata-precondition failure. The failed environment was retained.

A second fresh build used the same archive and downloaded build-tool wheel
under a shorter temporary root. The command disabled index access, dependency
resolution, and build isolation. It emitted exactly one unpublished wheel:

- filename: `agent_governance_starter-0.3.0rc1-py3-none-any.whl`;
- size: `475529` bytes;
- SHA-256:
  `78D6A216FE7344A2E3DA01086A7A92B9F3310BE61DAD2E690B0705003221FDE6`;
- member count: `173`;
- canonical member-inventory SHA-256:
  `2BB649EB6EF281260C083E567CC8F92DDE0F50BB6975C700DE17C075115DF5AC`.

The canonical inventory is the UTF-8 SHA-256 of all member paths sorted
ordinally, joined by LF, with one final LF. Its complete partition is:

- `agentgov/`: 67 Python package members;
- `agent_governance_starter-0.3.0rc1.data/data/share/agent-governance-starter/`:
  100 shared governance members;
- `agent_governance_starter-0.3.0rc1.dist-info/`: 6 distribution metadata
  members.

The 67 package members are:

```text
agentgov/__init__.py
agentgov/__main__.py
agentgov/active_agent_self_review.py
agentgov/admission_routing.py
agentgov/adoption.py
agentgov/agent_skills.py
agentgov/alignment_transport.py
agentgov/artifacts.py
agentgov/benefit_monitor.py
agentgov/benefits.py
agentgov/capability.py
agentgov/change_scope.py
agentgov/clarification_dialogue.py
agentgov/cli.py
agentgov/codex_hooks.py
agentgov/codex_mcp.py
agentgov/coding_agent_transport.py
agentgov/consumer_ci.py
agentgov/controls.py
agentgov/dependencies.py
agentgov/development_context.py
agentgov/development_event_export.py
agentgov/development_evidence.py
agentgov/development_handoff.py
agentgov/development_monitor.py
agentgov/development_session.py
agentgov/development_state.py
agentgov/development_trigger.py
agentgov/doctor.py
agentgov/documentation_archive.py
agentgov/drift_review.py
agentgov/evaluation.py
agentgov/event_store.py
agentgov/foreground_coordinator.py
agentgov/git_snapshot.py
agentgov/governance_mcp.py
agentgov/harness_contract.py
agentgov/host_interaction.py
agentgov/html_reporting.py
agentgov/human_decision.py
agentgov/initializer.py
agentgov/inventory.py
agentgov/next_action.py
agentgov/onboarding.py
agentgov/path_policy.py
agentgov/redaction.py
agentgov/reference_adapter.py
agentgov/reference_alignment_adapter.py
agentgov/reference_task_proposal_adapter.py
agentgov/references.py
agentgov/refresh.py
agentgov/release_metadata.py
agentgov/release_review.py
agentgov/replay_preflight.py
agentgov/replay_reservation.py
agentgov/reporting.py
agentgov/repository.py
agentgov/self_review_transport.py
agentgov/semantic_review.py
agentgov/software_update.py
agentgov/status.py
agentgov/task_contract.py
agentgov/task_proposal.py
agentgov/update_check.py
agentgov/upgrade_pr.py
agentgov/upgrade_review.py
agentgov/upgrade_writer.py
```

The 100 shared governance members are:

```text
agent_governance_starter-0.3.0rc1.data/data/share/agent-governance-starter/agent-skills/action-loop-stagnation/SKILL.md
agent_governance_starter-0.3.0rc1.data/data/share/agent-governance-starter/agent-skills/context-first-review/SKILL.md
agent_governance_starter-0.3.0rc1.data/data/share/agent-governance-starter/agent-skills/development-slice/SKILL.md
agent_governance_starter-0.3.0rc1.data/data/share/agent-governance-starter/agent-skills/incident-attribution/SKILL.md
agent_governance_starter-0.3.0rc1.data/data/share/agent-governance-starter/agent-skills/incident-response/SKILL.md
agent_governance_starter-0.3.0rc1.data/data/share/agent-governance-starter/agent-skills/README.md
agent_governance_starter-0.3.0rc1.data/data/share/agent-governance-starter/agent-skills/reconcile-invariants/SKILL.md
agent_governance_starter-0.3.0rc1.data/data/share/agent-governance-starter/agent-skills/requirement-admission/SKILL.md
agent_governance_starter-0.3.0rc1.data/data/share/agent-governance-starter/evaluation/readiness-policy.md
agent_governance_starter-0.3.0rc1.data/data/share/agent-governance-starter/evaluation/schemas/evaluation-manifest.schema.json
agent_governance_starter-0.3.0rc1.data/data/share/agent-governance-starter/evaluation/schemas/failure-case.schema.json
agent_governance_starter-0.3.0rc1.data/data/share/agent-governance-starter/evaluation/schemas/golden-example.schema.json
agent_governance_starter-0.3.0rc1.data/data/share/agent-governance-starter/evaluation/schemas/seed-case.schema.json
agent_governance_starter-0.3.0rc1.data/data/share/agent-governance-starter/governance/capability.schema.json
agent_governance_starter-0.3.0rc1.data/data/share/agent-governance-starter/governance/capability-dependencies.schema.json
agent_governance_starter-0.3.0rc1.data/data/share/agent-governance-starter/governance/control-mapping.schema.json
agent_governance_starter-0.3.0rc1.data/data/share/agent-governance-starter/governance/inventory.schema.json
agent_governance_starter-0.3.0rc1.data/data/share/agent-governance-starter/release/current.json
agent_governance_starter-0.3.0rc1.data/data/share/agent-governance-starter/schemas/active-agent-self-review-draft.schema.json
agent_governance_starter-0.3.0rc1.data/data/share/agent-governance-starter/schemas/active-agent-self-review-start.schema.json
agent_governance_starter-0.3.0rc1.data/data/share/agent-governance-starter/schemas/active-agent-self-review-stream-response.schema.json
agent_governance_starter-0.3.0rc1.data/data/share/agent-governance-starter/schemas/admission-route.schema.json
agent_governance_starter-0.3.0rc1.data/data/share/agent-governance-starter/schemas/admission-routing-policy.schema.json
agent_governance_starter-0.3.0rc1.data/data/share/agent-governance-starter/schemas/adoption-report.schema.json
agent_governance_starter-0.3.0rc1.data/data/share/agent-governance-starter/schemas/alignment-context.schema.json
agent_governance_starter-0.3.0rc1.data/data/share/agent-governance-starter/schemas/benefit-comparison.schema.json
agent_governance_starter-0.3.0rc1.data/data/share/agent-governance-starter/schemas/benefit-monitor.schema.json
agent_governance_starter-0.3.0rc1.data/data/share/agent-governance-starter/schemas/ci-integration-plan.schema.json
agent_governance_starter-0.3.0rc1.data/data/share/agent-governance-starter/schemas/clarification-dialogue.schema.json
agent_governance_starter-0.3.0rc1.data/data/share/agent-governance-starter/schemas/clarification-prompt.schema.json
agent_governance_starter-0.3.0rc1.data/data/share/agent-governance-starter/schemas/clarification-update.schema.json
agent_governance_starter-0.3.0rc1.data/data/share/agent-governance-starter/schemas/codex-hooks-integration-plan.schema.json
agent_governance_starter-0.3.0rc1.data/data/share/agent-governance-starter/schemas/codex-mcp-integration-plan.schema.json
agent_governance_starter-0.3.0rc1.data/data/share/agent-governance-starter/schemas/coding-agent-alignment-response.schema.json
agent_governance_starter-0.3.0rc1.data/data/share/agent-governance-starter/schemas/coding-agent-event.schema.json
agent_governance_starter-0.3.0rc1.data/data/share/agent-governance-starter/schemas/coding-agent-response.schema.json
agent_governance_starter-0.3.0rc1.data/data/share/agent-governance-starter/schemas/development-completion.schema.json
agent_governance_starter-0.3.0rc1.data/data/share/agent-governance-starter/schemas/development-context.schema.json
agent_governance_starter-0.3.0rc1.data/data/share/agent-governance-starter/schemas/development-event-export.schema.json
agent_governance_starter-0.3.0rc1.data/data/share/agent-governance-starter/schemas/development-evidence.schema.json
agent_governance_starter-0.3.0rc1.data/data/share/agent-governance-starter/schemas/development-monitor.schema.json
agent_governance_starter-0.3.0rc1.data/data/share/agent-governance-starter/schemas/development-scope-report.schema.json
agent_governance_starter-0.3.0rc1.data/data/share/agent-governance-starter/schemas/development-session.schema.json
agent_governance_starter-0.3.0rc1.data/data/share/agent-governance-starter/schemas/development-state.schema.json
agent_governance_starter-0.3.0rc1.data/data/share/agent-governance-starter/schemas/development-task.schema.json
agent_governance_starter-0.3.0rc1.data/data/share/agent-governance-starter/schemas/development-trigger.schema.json
agent_governance_starter-0.3.0rc1.data/data/share/agent-governance-starter/schemas/doctor-report.schema.json
agent_governance_starter-0.3.0rc1.data/data/share/agent-governance-starter/schemas/documentation-archive-plan.schema.json
agent_governance_starter-0.3.0rc1.data/data/share/agent-governance-starter/schemas/drift-review-policy.schema.json
agent_governance_starter-0.3.0rc1.data/data/share/agent-governance-starter/schemas/drift-review-record.schema.json
agent_governance_starter-0.3.0rc1.data/data/share/agent-governance-starter/schemas/drift-review-status.schema.json
agent_governance_starter-0.3.0rc1.data/data/share/agent-governance-starter/schemas/foreground-cycle.schema.json
agent_governance_starter-0.3.0rc1.data/data/share/agent-governance-starter/schemas/governance-event.schema.json
agent_governance_starter-0.3.0rc1.data/data/share/agent-governance-starter/schemas/harness-contract-v1.schema.json
agent_governance_starter-0.3.0rc1.data/data/share/agent-governance-starter/schemas/host-interaction-capabilities.schema.json
agent_governance_starter-0.3.0rc1.data/data/share/agent-governance-starter/schemas/host-interaction-request.schema.json
agent_governance_starter-0.3.0rc1.data/data/share/agent-governance-starter/schemas/human-decision-prompt.schema.json
agent_governance_starter-0.3.0rc1.data/data/share/agent-governance-starter/schemas/human-decision-result.schema.json
agent_governance_starter-0.3.0rc1.data/data/share/agent-governance-starter/schemas/interaction-card.schema.json
agent_governance_starter-0.3.0rc1.data/data/share/agent-governance-starter/schemas/mcp-tool-error.schema.json
agent_governance_starter-0.3.0rc1.data/data/share/agent-governance-starter/schemas/next-action.schema.json
agent_governance_starter-0.3.0rc1.data/data/share/agent-governance-starter/schemas/onboarding-plan.schema.json
agent_governance_starter-0.3.0rc1.data/data/share/agent-governance-starter/schemas/refresh-plan.schema.json
agent_governance_starter-0.3.0rc1.data/data/share/agent-governance-starter/schemas/release-manifest.schema.json
agent_governance_starter-0.3.0rc1.data/data/share/agent-governance-starter/schemas/release-review.schema.json
agent_governance_starter-0.3.0rc1.data/data/share/agent-governance-starter/schemas/replay-correlation-reservation-v1.schema.json
agent_governance_starter-0.3.0rc1.data/data/share/agent-governance-starter/schemas/replay-preflight-v1.schema.json
agent_governance_starter-0.3.0rc1.data/data/share/agent-governance-starter/schemas/repository-contract.schema.json
agent_governance_starter-0.3.0rc1.data/data/share/agent-governance-starter/schemas/repository-report.schema.json
agent_governance_starter-0.3.0rc1.data/data/share/agent-governance-starter/schemas/semantic-review-provider-capabilities.schema.json
agent_governance_starter-0.3.0rc1.data/data/share/agent-governance-starter/schemas/semantic-review-result.schema.json
agent_governance_starter-0.3.0rc1.data/data/share/agent-governance-starter/schemas/semantic-review-route.schema.json
agent_governance_starter-0.3.0rc1.data/data/share/agent-governance-starter/schemas/status-report.schema.json
agent_governance_starter-0.3.0rc1.data/data/share/agent-governance-starter/schemas/task-admission-plan.schema.json
agent_governance_starter-0.3.0rc1.data/data/share/agent-governance-starter/schemas/task-proposal.schema.json
agent_governance_starter-0.3.0rc1.data/data/share/agent-governance-starter/schemas/update-check.schema.json
agent_governance_starter-0.3.0rc1.data/data/share/agent-governance-starter/schemas/upgrade-observation.schema.json
agent_governance_starter-0.3.0rc1.data/data/share/agent-governance-starter/schemas/upgrade-pr-plan.schema.json
agent_governance_starter-0.3.0rc1.data/data/share/agent-governance-starter/schemas/upgrade-pr-write.schema.json
agent_governance_starter-0.3.0rc1.data/data/share/agent-governance-starter/schemas/upgrade-review.schema.json
agent_governance_starter-0.3.0rc1.data/data/share/agent-governance-starter/schemas/work-request.schema.json
agent_governance_starter-0.3.0rc1.data/data/share/agent-governance-starter/templates/admission-routing-policy.template.json
agent_governance_starter-0.3.0rc1.data/data/share/agent-governance-starter/templates/ADR.template.md
agent_governance_starter-0.3.0rc1.data/data/share/agent-governance-starter/templates/AGENTS.template.md
agent_governance_starter-0.3.0rc1.data/data/share/agent-governance-starter/templates/capability-dependencies.template.json
agent_governance_starter-0.3.0rc1.data/data/share/agent-governance-starter/templates/codex-hooks.template.json
agent_governance_starter-0.3.0rc1.data/data/share/agent-governance-starter/templates/control-mapping.template.json
agent_governance_starter-0.3.0rc1.data/data/share/agent-governance-starter/templates/development-task.template.json
agent_governance_starter-0.3.0rc1.data/data/share/agent-governance-starter/templates/drift-review-policy.template.json
agent_governance_starter-0.3.0rc1.data/data/share/agent-governance-starter/templates/evaluation-manifest.template.json
agent_governance_starter-0.3.0rc1.data/data/share/agent-governance-starter/templates/example-capability.input.schema.template.json
agent_governance_starter-0.3.0rc1.data/data/share/agent-governance-starter/templates/example-capability.output.schema.template.json
agent_governance_starter-0.3.0rc1.data/data/share/agent-governance-starter/templates/governance-inventory.template.json
agent_governance_starter-0.3.0rc1.data/data/share/agent-governance-starter/templates/INVARIANTS.template.md
agent_governance_starter-0.3.0rc1.data/data/share/agent-governance-starter/templates/prompt-capability.template.json
agent_governance_starter-0.3.0rc1.data/data/share/agent-governance-starter/templates/prompt-source.template.md
agent_governance_starter-0.3.0rc1.data/data/share/agent-governance-starter/templates/repository-contract.template.json
agent_governance_starter-0.3.0rc1.data/data/share/agent-governance-starter/templates/task-proposal.template.json
agent_governance_starter-0.3.0rc1.data/data/share/agent-governance-starter/templates/tasks.keep
agent_governance_starter-0.3.0rc1.data/data/share/agent-governance-starter/templates/work-request.template.json
```

The six distribution metadata members are:

```text
agent_governance_starter-0.3.0rc1.dist-info/entry_points.txt
agent_governance_starter-0.3.0rc1.dist-info/licenses/LICENSE
agent_governance_starter-0.3.0rc1.dist-info/METADATA
agent_governance_starter-0.3.0rc1.dist-info/RECORD
agent_governance_starter-0.3.0rc1.dist-info/top_level.txt
agent_governance_starter-0.3.0rc1.dist-info/WHEEL
```

The 100 shared members comprise 8 agent-skill files, 5 evaluation files, 4
governance schemas, 1 release manifest, 63 runtime schemas, and 19 adoption
templates. Together with the canonical inventory digest, these partitions
record the complete wheel member inventory without retaining a host path.

## Offline installed-help result

A second fresh Python 3.11 virtual environment installed the built wheel with
`--no-index --no-deps`. The installed command reported `agentgov 0.3.0rc1`.
`agentgov reserve replay-correlation --help` exited `0`, named the
`replay-correlation` command, and began with the expected argparse usage line.

Only help and version commands were invoked. Reservation apply invocation
count was `0`; `RESERVE` input count was `0`; marker created was `false`; and
the temporary tree contained zero `.agentgov` state directories.

The existing exposed launcher retained SHA-256
`7DADA88A8CCFF3DFA40DD52783719E5ACED5B293202979BA3D5B75F027B498E7`.
The existing pipx package module retained SHA-256
`5C9A876E01F8013AB3492C72E155E1F25F2E87D07E64EAAD228C8BDF5BEA7E83`.
The existing installation therefore remained byte-unchanged at both measured
surfaces.

## Disposition and next boundary

The downloaded build prerequisite, failed deep-path build, successful
short-path build, wheel, and isolated install remain in the operating-system
temporary area because cleanup was not authorized. Their absolute paths and
raw command transcripts are omitted from repository evidence.

This result clears the packaging prerequisite that blocked the earlier
installed reservation rehearsal. It does not revive or retry that paused
one-shot task. A new one-shot reservation rehearsal still requires a separate
product review and admitted task.
