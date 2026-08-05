from __future__ import annotations

import contextlib
import io
import json
import shutil
import subprocess
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from agentgov.cli import EXIT_PASS, main
from agentgov.development_session import DevelopmentSession, apply_start_plan, build_start_plan
from agentgov.event_store import load_governance_events
from agentgov.foreground_coordinator import (
    CoordinatorPolicyError,
    render_foreground_cycle_json,
    run_foreground_cycle,
)
from agentgov.initializer import initialize_project
from agentgov.reference_adapter import build_reference_trigger


ROOT = Path(__file__).resolve().parents[1]


def run_git(repository: Path, *args: str) -> str:
    completed = subprocess.run(
        ("git", "-C", str(repository), *args),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        raise AssertionError(completed.stderr.decode("utf-8", errors="replace"))
    return completed.stdout.decode("utf-8", errors="replace").strip()


def create_repository(parent: Path) -> tuple[Path, DevelopmentSession]:
    root = parent / "repository"
    root.mkdir()
    initialize_project(root, project_name="Foreground Coordinator Fixture", dry_run=False)
    run_git(root, "init", "--quiet")
    run_git(root, "config", "user.email", "fixture@example.invalid")
    run_git(root, "config", "user.name", "Fixture Author")
    (root / "pyproject.toml").write_text(
        "[project]\nname='fixture'\nversion='0.0.0'\n",
        encoding="utf-8",
    )
    (root / "README.md").write_text("# Fixture\n", encoding="utf-8")
    run_git(root, "add", ".")
    run_git(root, "commit", "--quiet", "-m", "baseline")
    result = apply_start_plan(
        build_start_plan(
            root,
            title="Exercise foreground coordination",
            include_paths=("README.md",),
            validation_commands=("python --version",),
        )
    )
    return root, result.session


def create_empty_git_repository(root: Path) -> Path:
    run_git(root, "init", "--quiet")
    run_git(root, "config", "user.email", "fixture@example.invalid")
    run_git(root, "config", "user.name", "Fixture Author")
    (root / "README.md").write_text("# Empty fixture\n", encoding="utf-8")
    run_git(root, "add", "README.md")
    run_git(root, "commit", "--quiet", "-m", "baseline")
    return root


def run_cli(*args: str) -> tuple[int, str, str]:
    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        code = main(list(args))
    return code, stdout.getvalue(), stderr.getvalue()


@unittest.skipUnless(shutil.which("git"), "Git is required for foreground fixtures")
class ForegroundCoordinatorTests(unittest.TestCase):
    def test_missing_task_returns_human_gate_and_refreshes_dashboard(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = create_empty_git_repository(Path(temp_dir))
            trigger = build_reference_trigger(root, trigger_type="repository.activated")

            cycle = run_foreground_cycle(root, trigger=trigger)

            self.assertEqual(cycle.status, "needs_human")
            self.assertEqual(cycle.human_gate["kind"], "task_admission")
            self.assertTrue((root / ".agentgov/dashboard.html").is_file())
            self.assertEqual(cycle.actions[-1]["name"], "refresh_dashboard")
            self.assertTrue(all(
                value is False
                for key, value in cycle.authority_boundary.items()
                if key.startswith("authorizes_")
            ))

    def test_implementation_change_checks_scope_and_surfaces_protection(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root, _ = create_repository(Path(temp_dir))
            (root / "OUTSIDE.md").write_text("outside\n", encoding="utf-8")
            trigger = build_reference_trigger(root, trigger_type="implementation.changed")

            cycle = run_foreground_cycle(root, trigger=trigger)
            events = load_governance_events(root / ".agentgov/events").events
            dashboard = (root / ".agentgov/dashboard.html").read_text(encoding="utf-8")

        self.assertEqual(cycle.status, "blocked")
        self.assertEqual(cycle.actions[0]["name"], "check_scope")
        self.assertEqual(cycle.actions[0]["outcome"], "blocked")
        self.assertEqual(events[-1].event_type, "scope.checked")
        self.assertEqual(events[-1].outcome, "failed")
        self.assertIn("Protection Events", dashboard)
        self.assertIn("scope boundary", dashboard)

    def test_completion_request_runs_only_admitted_validation_and_reconciles(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root, session = create_repository(Path(temp_dir))
            (root / "README.md").write_text("# Fixture\n\nCompleted.\n", encoding="utf-8")
            trigger = build_reference_trigger(root, trigger_type="completion.requested")

            cycle = run_foreground_cycle(root, trigger=trigger)

        self.assertEqual(cycle.status, "review_ready")
        self.assertEqual(cycle.task_ref["task_digest"], session.task_digest)
        self.assertEqual(
            [item["name"] for item in cycle.actions],
            [
                "check_scope",
                "run_preapproved_validation",
                "reconcile_completion",
                "refresh_dashboard",
            ],
        )
        self.assertEqual(cycle.state_after["stage"], "review_ready")
        self.assertIsNone(cycle.human_gate)
        self.assertEqual(cycle.findings, ())

    def test_human_review_event_hands_off_without_special_confirmation_text(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root, _ = create_repository(Path(temp_dir))
            (root / "README.md").write_text("# Fixture\n\nCompleted.\n", encoding="utf-8")
            completion = build_reference_trigger(root, trigger_type="completion.requested")
            run_foreground_cycle(root, trigger=completion)
            review = build_reference_trigger(
                root,
                trigger_type="session.reviewed",
                actor_class="human",
                review_outcome="accepted",
            )

            cycle = run_foreground_cycle(root, trigger=review)

        self.assertEqual(cycle.status, "handed_off")
        self.assertEqual(cycle.actions[0]["name"], "handoff_session")
        self.assertEqual(cycle.state_after["stage"], "handed_off")

    def test_premature_human_acceptance_is_a_block_not_an_operational_error(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root, _ = create_repository(Path(temp_dir))
            review = build_reference_trigger(
                root,
                trigger_type="session.reviewed",
                actor_class="human",
                review_outcome="accepted",
            )

            cycle = run_foreground_cycle(root, trigger=review)

        self.assertEqual(cycle.status, "blocked")
        self.assertEqual(cycle.findings[0]["code"], "review_not_ready")
        self.assertEqual(cycle.state_after["stage"], "active_unchecked")
        self.assertFalse(any(item["name"] == "handoff_session" for item in cycle.actions))

    def test_mismatched_working_copy_fails_before_any_action(self) -> None:
        with TemporaryDirectory() as first_dir, TemporaryDirectory() as second_dir:
            first = Path(first_dir)
            second = Path(second_dir)
            trigger = build_reference_trigger(first, trigger_type="repository.activated")

            with self.assertRaises(CoordinatorPolicyError):
                run_foreground_cycle(second, trigger=trigger)

            self.assertFalse((second / ".agentgov").exists())

    def test_external_validation_is_advisory_context_not_completion_evidence(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root, _ = create_repository(Path(temp_dir))
            trigger = build_reference_trigger(
                root,
                trigger_type="validation.completed",
                validation_outcome="passed",
                evidence_ref="adapter/evidence.json",
            )

            cycle = run_foreground_cycle(root, trigger=trigger)

        self.assertEqual(cycle.status, "observed")
        self.assertEqual(cycle.findings[0]["semantics"], "advisory")
        self.assertEqual(cycle.findings[0]["code"], "adapter_validation_is_context_only")
        self.assertEqual(cycle.state_after["stage"], "active_unchecked")

    def test_json_result_matches_strict_contract_shape(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = create_empty_git_repository(Path(temp_dir))
            cycle = run_foreground_cycle(
                root,
                trigger=build_reference_trigger(root, trigger_type="task.requested"),
            )
            payload = json.loads(render_foreground_cycle_json(cycle))
            schema = json.loads(
                (ROOT / "schemas/foreground-cycle.schema.json").read_text(encoding="utf-8")
            )

        self.assertEqual(payload["contract"], schema["properties"]["contract"]["const"])
        self.assertEqual(payload["schema_version"], schema["properties"]["schema_version"]["const"])
        self.assertEqual(set(payload), set(schema["required"]))
        self.assertFalse(schema["additionalProperties"])

    def test_cli_default_cycle_needs_human_without_manual_json(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = create_empty_git_repository(Path(temp_dir))
            code, stdout, stderr = run_cli("dev", str(root), "--format", "json")
            payload = json.loads(stdout)

        self.assertEqual(code, EXIT_PASS)
        self.assertEqual(stderr, "")
        self.assertEqual(payload["status"], "needs_human")
        self.assertEqual(payload["human_gate"]["kind"], "task_admission")
        self.assertEqual(payload["dashboard_ref"], ".agentgov/dashboard.html")


if __name__ == "__main__":
    unittest.main()
