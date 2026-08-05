from __future__ import annotations

import json
import unittest
from dataclasses import replace
from pathlib import Path

from agentgov.development_session import DevelopmentSession
from agentgov.development_state import (
    DevelopmentOperation,
    DevelopmentStage,
    development_state_payload,
    project_development_state,
)
from agentgov.event_store import GovernanceEvent


ROOT = Path(__file__).resolve().parents[1]
TASK_DIGEST = "sha256:" + "a" * 64
STARTED_AT = "2026-08-05T00:00:00.000Z"


def session() -> DevelopmentSession:
    return DevelopmentSession(
        contract="agentgov.development-session",
        schema_version="1.0",
        task_path="governance/tasks/fixture-task.json",
        task_id="fixture-task",
        task_digest=TASK_DIGEST,
        comparison_base_sha="b" * 40,
        started_at=STARTED_AT,
        actor={"class": "human"},
    )


def event(
    event_type: str,
    outcome: str,
    *,
    index: int,
    occurred_at: str | None = None,
) -> GovernanceEvent:
    return GovernanceEvent(
        contract="agentgov.governance-event",
        schema_version="1.2",
        event_id="evt-" + f"{index:032x}",
        occurred_at=occurred_at or f"2026-08-05T00:00:0{index}.000Z",
        event_type=event_type,
        actor={"class": "coding_agent"},
        task_id="fixture-task",
        task_digest=TASK_DIGEST,
        observation_scope="local_development",
        outcome=outcome,
        evidence_ref=None,
        governance_refs=(),
        reason_codes=("fixture",),
        metrics={},
        authority_boundary={
            "authorizes_code_change": False,
            "authorizes_exception": False,
            "authorizes_commit": False,
            "authorizes_merge": False,
            "authorizes_deployment": False,
        },
    )


class DevelopmentStateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.session = session()
        self.started = event(
            "task.started",
            "started",
            index=0,
            occurred_at=STARTED_AT,
        )

    def test_projects_implemented_lifecycle_into_stable_operations(self) -> None:
        cases = (
            (
                (self.started,),
                DevelopmentStage.ACTIVE_UNCHECKED,
                DevelopmentOperation.CHECK_SCOPE,
            ),
            (
                (self.started, event("scope.checked", "passed", index=1)),
                DevelopmentStage.SCOPE_PASSED,
                DevelopmentOperation.VALIDATE_AND_RECONCILE,
            ),
            (
                (self.started, event("scope.checked", "failed", index=1)),
                DevelopmentStage.SCOPE_BLOCKED,
                DevelopmentOperation.CHECK_SCOPE,
            ),
            (
                (self.started, event("validation.completed", "passed", index=1)),
                DevelopmentStage.VALIDATION_RECORDED,
                DevelopmentOperation.RECONCILE_COMPLETION,
            ),
            (
                (self.started, event("completion.reconciled", "needs_evidence", index=1)),
                DevelopmentStage.NEEDS_EVIDENCE,
                DevelopmentOperation.VALIDATE_AND_RECONCILE,
            ),
            (
                (self.started, event("completion.reconciled", "verified", index=1)),
                DevelopmentStage.REVIEW_READY,
                DevelopmentOperation.REFRESH_DASHBOARD,
            ),
        )
        for events, stage, operation in cases:
            with self.subTest(stage=stage.value):
                state = project_development_state(self.session, events)
                self.assertEqual(state.stage, stage.value)
                self.assertEqual(state.recommended_operation, operation.value)
                self.assertIs(state.blocking, stage is DevelopmentStage.SCOPE_BLOCKED)
                self.assertTrue(all(value is False for value in state.authority_boundary.values()))

    def test_missing_cross_session_and_unsorted_events_fail_closed(self) -> None:
        missing = project_development_state(self.session, ())
        foreign_event = replace(
            event("task.started", "started", index=0, occurred_at=STARTED_AT),
            task_id="other-task",
        )
        foreign = project_development_state(self.session, (foreign_event,))
        unsorted = project_development_state(
            self.session,
            (
                self.started,
                event("scope.checked", "passed", index=2),
                event("validation.completed", "passed", index=1),
            ),
        )

        self.assertEqual(missing.reason_code, "missing_start_event")
        self.assertEqual(foreign.reason_code, "event_outside_session")
        self.assertEqual(unsorted.reason_code, "events_not_chronological")
        self.assertTrue(missing.blocking and foreign.blocking and unsorted.blocking)

    def test_payload_matches_strict_packaged_schema_contract(self) -> None:
        payload = development_state_payload(
            project_development_state(self.session, (self.started,))
        )
        schema = json.loads(
            (ROOT / "schemas/development-state.schema.json").read_text(encoding="utf-8")
        )

        self.assertEqual(payload["contract"], schema["properties"]["contract"]["const"])
        self.assertEqual(payload["schema_version"], schema["properties"]["schema_version"]["const"])
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(set(payload), set(schema["required"]))


if __name__ == "__main__":
    unittest.main()
