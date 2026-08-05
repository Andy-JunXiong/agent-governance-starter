import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from agentgov.development_trigger import (
    TriggerContractError,
    development_trigger_from_payload,
    working_copy_digest,
)


ROOT = Path(__file__).resolve().parents[1]


def payload(trigger_type: str = "repository.activated") -> dict:
    return {
        "contract": "agentgov.development-trigger",
        "schema_version": "1.0",
        "trigger_id": "trg-" + "a" * 32,
        "occurred_at": "2026-08-05T00:00:00.000Z",
        "trigger_type": trigger_type,
        "source": {"adapter_id": "reference.coding-agent", "actor_class": "coding_agent"},
        "working_copy_digest": "sha256:" + "b" * 64,
        "correlation_id": "session-001",
        "task_ref": None,
        "facts": {
            "changed_paths": [],
            "validation_outcome": None,
            "evidence_ref": None,
            "scope_decision": None,
            "review_outcome": None,
        },
        "authority_boundary": {
            "authorizes_scope_expansion": False,
            "authorizes_exception": False,
            "authorizes_commit": False,
            "authorizes_merge": False,
            "authorizes_deployment": False,
        },
    }


class DevelopmentTriggerTests(unittest.TestCase):
    def test_accepts_vendor_neutral_changed_validation_and_review_facts(self) -> None:
        changed = payload("implementation.changed")
        changed["facts"]["changed_paths"] = ["src/example.py"]
        validated = payload("validation.completed")
        validated["facts"]["validation_outcome"] = "passed"
        validated["facts"]["evidence_ref"] = ".agentgov/evidence/example.json"
        reviewed = payload("session.reviewed")
        reviewed["source"]["actor_class"] = "human"
        reviewed["facts"]["review_outcome"] = "accepted"
        decided = payload("scope.decision_recorded")
        decided["source"]["actor_class"] = "human"
        decided["facts"]["scope_decision"] = "approved"

        events = tuple(
            development_trigger_from_payload(item)
            for item in (changed, validated, reviewed, decided)
        )

        self.assertEqual(events[0].facts["changed_paths"], ("src/example.py",))
        self.assertEqual(events[1].facts["validation_outcome"], "passed")
        self.assertEqual(events[2].facts["review_outcome"], "accepted")
        self.assertEqual(events[3].facts["scope_decision"], "approved")
        self.assertTrue(all(value is False for value in events[0].authority_boundary.values()))

    def test_rejects_cross_event_facts_paths_unknown_fields_and_authority(self) -> None:
        wrong_fact = payload("completion.requested")
        wrong_fact["facts"]["changed_paths"] = ["src/example.py"]
        wrong_evidence = payload("completion.requested")
        wrong_evidence["facts"]["evidence_ref"] = ".agentgov/evidence/example.json"
        absolute = payload("implementation.changed")
        absolute["facts"]["changed_paths"] = ["C:\\private\\example.py"]
        unknown = payload()
        unknown["vendor"] = "specific"
        authority = payload()
        authority["authority_boundary"]["authorizes_commit"] = True
        agent_decision = payload("scope.decision_recorded")
        agent_decision["facts"]["scope_decision"] = "approved"
        agent_review = payload("session.reviewed")
        agent_review["facts"]["review_outcome"] = "accepted"

        for item in (
            wrong_fact,
            wrong_evidence,
            absolute,
            unknown,
            authority,
            agent_decision,
            agent_review,
        ):
            with self.subTest(item=item["trigger_type"]), self.assertRaises(TriggerContractError):
                development_trigger_from_payload(item)

    def test_working_copy_identity_is_a_digest_not_a_disclosed_path(self) -> None:
        with TemporaryDirectory() as temp_dir:
            digest = working_copy_digest(Path(temp_dir))

        self.assertRegex(digest, r"^sha256:[0-9a-f]{64}$")
        self.assertNotIn(temp_dir, digest)

    def test_schema_tracks_required_trigger_vocabulary_and_denies_authority(self) -> None:
        schema = json.loads(
            (ROOT / "schemas/development-trigger.schema.json").read_text(encoding="utf-8")
        )
        trigger_types = set(schema["properties"]["trigger_type"]["enum"])

        self.assertEqual(
            trigger_types,
            {
                "task.requested",
                "repository.activated",
                "implementation.changed",
                "scope.decision_requested",
                "scope.decision_recorded",
                "completion.requested",
                "validation.completed",
                "session.reviewed",
            },
        )
        self.assertFalse(schema["additionalProperties"])
        for rule in schema["properties"]["authority_boundary"]["properties"].values():
            self.assertIs(rule["const"], False)


if __name__ == "__main__":
    unittest.main()
