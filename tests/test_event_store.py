import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from agentgov.event_store import LocalStateError, append_governance_event, load_governance_event


class EventStoreTests(unittest.TestCase):
    def test_events_are_unique_append_only_and_authority_denied(self) -> None:
        with TemporaryDirectory() as temp_dir:
            repository = Path(temp_dir)
            first, first_ref = append_governance_event(
                repository,
                event_type="validation.completed",
                actor_class="coding_agent",
                actor_label="fixture-agent",
                task_id="fixture-task",
                task_digest="sha256:" + "a" * 64,
                outcome="passed",
                evidence_ref=".agentgov/evidence/evd-" + "b" * 32 + ".json",
                metrics={"commands_passed": 1},
            )
            second, second_ref = append_governance_event(
                repository,
                event_type="completion.reconciled",
                actor_class="human",
                actor_label=None,
                task_id="fixture-task",
                task_digest="sha256:" + "a" * 64,
                outcome="verified",
                evidence_ref=".agentgov/evidence/evd-" + "b" * 32 + ".json",
            )
            payload = json.loads((repository / first_ref).read_text(encoding="utf-8"))

        self.assertNotEqual(first.event_id, second.event_id)
        self.assertNotEqual(first_ref, second_ref)
        self.assertEqual(payload["observation_scope"], "local_development")
        self.assertTrue(all(value is False for value in payload["authority_boundary"].values()))

    def test_absolute_paths_credentials_and_secret_token_shapes_are_rejected(self) -> None:
        values = (
            "C:\\Users\\person",
            "password=hunter2",
            "ghp_abcdefghijklmnopqrstuvwxyz123456",
            "sk-abcdefghijklmnopqrstuvwxyz123456",
        )
        for label in values:
            with self.subTest(label=label), TemporaryDirectory() as temp_dir:
                with self.assertRaises(LocalStateError):
                    append_governance_event(
                        Path(temp_dir),
                        event_type="validation.completed",
                        actor_class="coding_agent",
                        actor_label=label,
                        task_id="fixture-task",
                        task_digest="sha256:" + "a" * 64,
                        outcome="passed",
                        evidence_ref=None,
                    )

    def test_v1_event_without_governance_refs_remains_readable(self) -> None:
        with TemporaryDirectory() as temp_dir:
            repository = Path(temp_dir)
            _, relative = append_governance_event(
                repository,
                event_type="scope.checked",
                actor_class="coding_agent",
                actor_label=None,
                task_id="fixture-task",
                task_digest="sha256:" + "a" * 64,
                outcome="passed",
                evidence_ref=None,
            )
            path = repository / relative
            payload = json.loads(path.read_text(encoding="utf-8"))
            payload["schema_version"] = "1.0"
            payload.pop("governance_refs")
            path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

            event = load_governance_event(path)

        self.assertEqual(event.schema_version, "1.0")
        self.assertEqual(event.governance_refs, ())

    def test_v1_1_remains_readable_and_future_versions_fail_closed(self) -> None:
        with TemporaryDirectory() as temp_dir:
            repository = Path(temp_dir)
            _, relative = append_governance_event(
                repository,
                event_type="scope.checked",
                actor_class="coding_agent",
                actor_label=None,
                task_id="fixture-task",
                task_digest="sha256:" + "a" * 64,
                outcome="passed",
                evidence_ref=None,
            )
            path = repository / relative
            payload = json.loads(path.read_text(encoding="utf-8"))
            payload["schema_version"] = "1.1"
            path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
            legacy = load_governance_event(path)
            payload["schema_version"] = "1.3"
            path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(LocalStateError, "unsupported contract"):
                load_governance_event(path)

        self.assertEqual(legacy.schema_version, "1.1")

    def test_handoff_type_outcome_and_human_actor_are_one_versioned_pair(self) -> None:
        common = {
            "repository": Path("."),
            "task_id": "fixture-task",
            "task_digest": "sha256:" + "a" * 64,
            "evidence_ref": ".agentgov/evidence/evd-" + "b" * 32 + ".json",
        }
        with TemporaryDirectory() as temp_dir:
            common["repository"] = Path(temp_dir)
            with self.assertRaisesRegex(ValueError, "used together"):
                append_governance_event(
                    **common,
                    event_type="session.handed_off",
                    actor_class="human",
                    actor_label=None,
                    outcome="verified",
                )
            with self.assertRaisesRegex(ValueError, "human actor"):
                append_governance_event(
                    **common,
                    event_type="session.handed_off",
                    actor_class="coding_agent",
                    actor_label=None,
                    outcome="handed_off",
                )
            event, _ = append_governance_event(
                **common,
                event_type="session.handed_off",
                actor_class="human",
                actor_label=None,
                outcome="handed_off",
            )

        self.assertEqual(event.schema_version, "1.2")


if __name__ == "__main__":
    unittest.main()
