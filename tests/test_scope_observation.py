from __future__ import annotations

import json
import shutil
import subprocess
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from agentgov.event_store import load_governance_events
from agentgov.scope_observation import (
    ScopeObservationError,
    load_scope_observation,
    record_scope_observation,
)


def run_git(repository: Path, *args: str) -> None:
    completed = subprocess.run(
        ("git", "-C", str(repository), *args),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        raise AssertionError(completed.stderr.decode("utf-8", errors="replace"))


def create_repository(parent: Path) -> tuple[Path, Path]:
    root = parent / "repository"
    root.mkdir()
    run_git(root, "init", "--quiet")
    run_git(root, "config", "user.email", "fixture@example.invalid")
    run_git(root, "config", "user.name", "Fixture Author")
    (root / "src").mkdir()
    (root / "src/app.py").write_text("VALUE = 1\n", encoding="utf-8")
    task_path = root / "governance/tasks/fixture-scope-observation.json"
    task_path.parent.mkdir(parents=True)
    task_path.write_text(
        json.dumps(
            {
                "contract": "agentgov.development-task",
                "schema_version": "1.1",
                "profile": "compact",
                "task_id": "fixture-scope-observation",
                "title": "Observe fixture scope",
                "requirement": {
                    "summary": "Observe exact changed paths for the admitted fixture task.",
                    "source_refs": [],
                },
                "scope": {
                    "include_paths": ["src/app.py", task_path.relative_to(root).as_posix()],
                    "exclude_paths": [],
                },
                "acceptance_signals": ["The scope observation records exact path evidence."],
                "validation_commands": ["python --version"],
                "owner": "Fixture owner",
                "risk": {"level": "low", "items": []},
                "decision": {
                    "state": "admitted",
                    "decided_by": "Fixture owner",
                    "rationale": "The fixture owner admitted this exact observation task.",
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    run_git(root, "add", ".")
    run_git(root, "commit", "--quiet", "-m", "baseline")
    return root, task_path


@unittest.skipUnless(shutil.which("git"), "Git is required for scope observation fixtures")
class ScopeObservationTests(unittest.TestCase):
    def test_records_path_level_artifact_and_binds_event(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root, task_path = create_repository(Path(temp_dir))
            (root / "src/app.py").write_text("VALUE = 2\n", encoding="utf-8")

            observation = record_scope_observation(
                root,
                task_path,
                actor_class="coding_agent",
                actor_label="fixture-adapter",
                reason_codes=("explicit_check_requested",),
            )
            events = load_governance_events(root / ".agentgov/events").events
            payload = load_scope_observation(
                root,
                observation.evidence_ref,
                expected_task_id=observation.report.task_id,
                expected_task_digest=observation.report.task_digest,
            )

        self.assertEqual(events[-1].event_type, "scope.checked")
        self.assertEqual(events[-1].evidence_ref, observation.evidence_ref)
        self.assertEqual(payload["changes"][0]["path"], "src/app.py")
        self.assertTrue(payload["changes"][0]["endpoints"][0]["admitted"])
        self.assertTrue(observation.evidence_ref.startswith(".agentgov/evidence/scp-"))

    def test_reuses_identical_artifact_but_appends_distinct_events(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root, task_path = create_repository(Path(temp_dir))
            (root / "src/app.py").write_text("VALUE = 2\n", encoding="utf-8")

            first = record_scope_observation(
                root,
                task_path,
                actor_class="coding_agent",
                actor_label=None,
                reason_codes=("explicit_check_requested",),
            )
            second = record_scope_observation(
                root,
                task_path,
                actor_class="coding_agent",
                actor_label=None,
                reason_codes=("explicit_check_requested",),
            )

            evidence_files = list((root / ".agentgov/evidence").glob("scp-*.json"))
            events = load_governance_events(root / ".agentgov/events").events

        self.assertEqual(first.evidence_ref, second.evidence_ref)
        self.assertNotEqual(first.event_ref, second.event_ref)
        self.assertEqual(len(evidence_files), 1)
        self.assertEqual(len(events), 2)

    def test_rejects_mismatched_task_binding_and_unsupported_reference(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root, task_path = create_repository(Path(temp_dir))
            observation = record_scope_observation(
                root,
                task_path,
                actor_class="coding_agent",
                actor_label=None,
                reason_codes=("explicit_check_requested",),
            )

            with self.assertRaisesRegex(ScopeObservationError, "task_id"):
                load_scope_observation(
                    root,
                    observation.evidence_ref,
                    expected_task_id="different-task",
                    expected_task_digest=observation.report.task_digest,
                )
            with self.assertRaisesRegex(ScopeObservationError, "unsupported or unsafe"):
                load_scope_observation(
                    root,
                    "outside/report.json",
                    expected_task_id=observation.report.task_id,
                    expected_task_digest=observation.report.task_digest,
                )

    def test_expected_adapter_paths_fail_before_any_local_record(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root, task_path = create_repository(Path(temp_dir))
            (root / "src/app.py").write_text("VALUE = 2\n", encoding="utf-8")

            with self.assertRaisesRegex(ScopeObservationError, "paths changed"):
                record_scope_observation(
                    root,
                    task_path,
                    actor_class="coding_agent",
                    actor_label=None,
                    reason_codes=("implementation_changed",),
                    expected_changed_paths=("different.py",),
                )

            self.assertFalse((root / ".agentgov").exists())


if __name__ == "__main__":
    unittest.main()
