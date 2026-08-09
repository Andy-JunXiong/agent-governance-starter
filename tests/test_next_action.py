import contextlib
import io
import json
import shutil
import subprocess
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from agentgov import __version__
from agentgov.cli import EXIT_ERROR, EXIT_FAIL, EXIT_PASS, main
from agentgov.development_session import (
    DevelopmentSession,
    apply_start_plan,
    build_compact_task,
    build_start_plan,
)
from agentgov.event_store import append_governance_event
from agentgov.initializer import initialize_project
from agentgov.next_action import (
    ActionKind,
    render_next_action_json,
    select_next_action,
    select_report_next_action,
)
from agentgov.repository import Finding, FindingStatus, RepositoryReport


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


def create_development_repository(parent: Path) -> tuple[Path, DevelopmentSession]:
    root = parent / "repository"
    root.mkdir()
    initialize_project(root, project_name="Development Next Fixture", dry_run=False)
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
            title="Exercise guided next routing",
            include_paths=("README.md",),
            validation_commands=("python -m unittest",),
        )
    )
    return root, result.session


def add_progress_event(
    root: Path,
    session: DevelopmentSession,
    *,
    event_type: str,
    outcome: str,
    occurred_at: str | None = None,
) -> None:
    append_governance_event(
        root,
        event_type=event_type,
        actor_class="coding_agent",
        actor_label="fixture-agent",
        task_id=session.task_id,
        task_digest=session.task_digest,
        outcome=outcome,
        evidence_ref=None,
        reason_codes=("next_action_fixture",),
        metrics={},
        occurred_at=occurred_at,
    )


def run_cli(*args: str) -> tuple[int, str, str]:
    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        exit_code = main(list(args))
    return exit_code, stdout.getvalue(), stderr.getvalue()


class NextActionTests(unittest.TestCase):
    def test_empty_repository_points_to_adoption_preview(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            before = tuple(root.rglob("*"))

            action = select_next_action(root)
            after = tuple(root.rglob("*"))

        self.assertEqual(before, after)
        self.assertIs(action.kind, ActionKind.DETERMINISTIC_WORK)
        self.assertFalse(action.blocking)
        self.assertEqual(action.source_check_id, "governance:constitution")
        self.assertIn("agentgov onboard", action.command or "")
        self.assertIn("--dry-run", action.command or "")

    def test_path_conflict_is_the_first_blocking_action(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "AGENTS.md").mkdir()

            action = select_next_action(root)

        self.assertTrue(action.blocking)
        self.assertEqual(action.source_check_id, "governance:constitution")
        self.assertIn("conflict", action.title.lower())

    def test_repository_failure_precedes_warning_and_advisory(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            initialize_project(root, project_name="Failing Fixture", dry_run=False)
            (root / "governance/artifacts").mkdir()
            manifest = root / "governance/capabilities/example-capability.json"
            manifest.write_text("{}\n", encoding="utf-8")

            action = select_next_action(root)

        self.assertIs(action.kind, ActionKind.DETERMINISTIC_WORK)
        self.assertTrue(action.blocking)
        self.assertEqual(
            action.source_check_id,
            "capability:governance/capabilities/example-capability.json",
        )

    def test_initialized_repository_routes_to_development_before_warn_or_advisory(
        self,
    ) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            initialize_project(root, project_name="Warning Fixture", dry_run=False)
            (root / "governance/artifacts").mkdir()

            action = select_next_action(root)

        self.assertIs(action.kind, ActionKind.DETERMINISTIC_WORK)
        self.assertFalse(action.blocking)
        self.assertEqual(action.source_check_id, "development-session:missing")
        self.assertIn("agentgov govern start", action.command or "")
        self.assertIn("--title", action.command or "")
        self.assertIn("--dry-run", action.command or "")

    def test_multiple_admitted_tasks_require_explicit_human_choice(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            initialize_project(root, project_name="Multiple Tasks", dry_run=False)
            task_root = root / "governance" / "tasks"
            task_root.mkdir(parents=True, exist_ok=True)
            for title in ("First task", "Second task"):
                document = build_compact_task(
                    title=title,
                    task_id=None,
                    requirement=None,
                    include_paths=("README.md",),
                    exclude_paths=(),
                    validation_commands=("python -m unittest",),
                    owner="Human product owner",
                )
                path = task_root / f"{document['task_id']}.json"
                path.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")

            action = select_next_action(root)

        self.assertEqual(action.source_check_id, "development-session:missing")
        self.assertIn('"<TASK_JSON>"', action.command or "")
        self.assertNotIn("first-task.json", action.command or "")
        self.assertNotIn("second-task.json", action.command or "")
        self.assertIn("2 admitted tasks", action.reason)

    def test_evaluation_warning_uses_scoped_check_command(self) -> None:
        root = Path("evaluation-warning-fixture")
        report = RepositoryReport(
            root,
            (
                Finding(
                    FindingStatus.WARN,
                    "evaluation:evaluation/example-capability",
                    "needs_seed_cases: next review draft seed case "
                    "seed-cases/basic-request.json",
                ),
            ),
        )

        action = select_report_next_action(root, report)

        self.assertIs(action.kind, ActionKind.INCOMPLETE_EVIDENCE)
        self.assertIn("incomplete evaluation evidence", action.title.lower())
        self.assertEqual(
            action.command,
            f'agentgov check evaluation "{root.resolve() / "evaluation/example-capability"}"',
        )

    def test_unconfigured_evaluation_bundle_uses_repository_check(self) -> None:
        root = Path("evaluation-bundles-fixture")
        report = RepositoryReport(
            root,
            (
                Finding(
                    FindingStatus.WARN,
                    "evaluation:bundles",
                    "no evaluation bundles are configured",
                ),
            ),
        )

        action = select_report_next_action(root, report)

        self.assertIs(action.kind, ActionKind.INCOMPLETE_EVIDENCE)
        self.assertEqual(
            action.command,
            f'agentgov check repository "{root.resolve()}"',
        )

    def test_json_result_is_read_only_and_does_not_execute_action(self) -> None:
        with TemporaryDirectory() as temp_dir:
            action = select_next_action(Path(temp_dir))
            payload = json.loads(
                render_next_action_json(action, non_interactive=True)
            )

        self.assertEqual(payload["mode"], "read_only")
        self.assertEqual(
            payload["tool"],
            {"name": "agentgov", "version": __version__},
        )
        self.assertEqual(payload["interaction"], "non_interactive")
        self.assertEqual(
            payload["authority_boundary"],
            {
                "action_executed": False,
                "modifies_repository": False,
                "authorizes_git_or_release_operations": False,
            },
        )

    def test_advisory_maps_to_non_blocking_human_judgment_without_command(
        self,
    ) -> None:
        root = Path("advisory-fixture")
        report = RepositoryReport(
            root,
            (
                Finding(
                    FindingStatus.ADVISORY,
                    "governance:human-review",
                    "record accountable human judgment",
                ),
            ),
        )

        action = select_report_next_action(root, report)

        self.assertIs(action.kind, ActionKind.HUMAN_JUDGMENT)
        self.assertFalse(action.blocking)
        self.assertIsNone(action.command)

    def test_report_without_open_findings_maps_to_complete(self) -> None:
        root = Path("complete-fixture")
        report = RepositoryReport(
            root,
            (Finding(FindingStatus.PASS, "required:test", "configured"),),
        )

        action = select_report_next_action(root, report)

        self.assertIs(action.kind, ActionKind.COMPLETE)
        self.assertFalse(action.blocking)
        self.assertIsNone(action.source_check_id)


@unittest.skipUnless(shutil.which("git"), "Git is required for guided next fixtures")
class DevelopmentNextActionTests(unittest.TestCase):
    def test_active_lifecycle_routes_start_check_finish_and_monitor_without_writing(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root, session = create_development_repository(Path(temp_dir))
            pointer = root / ".agentgov" / "current-task.json"
            pointer_before = pointer.read_bytes()
            event_count_before = len(tuple((root / ".agentgov/events").glob("*.json")))

            started = select_next_action(root)
            add_progress_event(root, session, event_type="scope.checked", outcome="passed")
            checked = select_next_action(root)
            add_progress_event(
                root,
                session,
                event_type="validation.completed",
                outcome="passed",
            )
            validated = select_next_action(root)
            add_progress_event(
                root,
                session,
                event_type="completion.reconciled",
                outcome="needs_evidence",
            )
            incomplete = select_next_action(root)
            add_progress_event(
                root,
                session,
                event_type="completion.reconciled",
                outcome="verified",
            )
            verified = select_next_action(root)
            pointer_after = pointer.read_bytes()
            event_count_after = len(tuple((root / ".agentgov/events").glob("*.json")))

        self.assertEqual(started.source_check_id, "development-session:started")
        self.assertIn("govern check", started.command or "")
        self.assertEqual(checked.source_check_id, "development-session:scope-passed")
        self.assertIn("govern finish", checked.command or "")
        self.assertEqual(
            validated.source_check_id,
            "development-session:validation-recorded",
        )
        self.assertIn("govern finish", validated.command or "")
        self.assertEqual(incomplete.source_check_id, "development-session:needs-evidence")
        self.assertIn("govern finish", incomplete.command or "")
        self.assertIs(verified.kind, ActionKind.COMPLETE)
        self.assertEqual(verified.source_check_id, "development-session:verified")
        self.assertIn("monitor development", verified.command or "")
        self.assertEqual(pointer_after, pointer_before)
        self.assertEqual(event_count_after, event_count_before + 4)

    def test_failed_scope_is_one_blocking_action(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root, session = create_development_repository(Path(temp_dir))
            add_progress_event(root, session, event_type="scope.checked", outcome="failed")

            action = select_next_action(root)

        self.assertTrue(action.blocking)
        self.assertEqual(action.source_check_id, "development-session:scope-failed")
        self.assertIn("govern check", action.command or "")

    def test_task_drift_fails_closed_with_replace_preview_only(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root, session = create_development_repository(Path(temp_dir))
            task = root / session.task_path
            pointer = root / ".agentgov/current-task.json"
            pointer_before = pointer.read_bytes()
            document = json.loads(task.read_text(encoding="utf-8"))
            document["goal"] = "Changed after the reviewed start"
            task.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")

            action = select_next_action(root)
            pointer_after = pointer.read_bytes()

        self.assertTrue(action.blocking)
        self.assertEqual(action.source_check_id, "development-session:task-drift")
        self.assertIn("--replace-active --dry-run", action.command or "")
        self.assertEqual(pointer_after, pointer_before)

    def test_unavailable_comparison_base_is_a_blocking_result(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root, _ = create_development_repository(Path(temp_dir))
            pointer = root / ".agentgov/current-task.json"
            document = json.loads(pointer.read_text(encoding="utf-8"))
            document["comparison_base_sha"] = "f" * 40
            pointer.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")

            action = select_next_action(root)

        self.assertTrue(action.blocking)
        self.assertEqual(action.source_check_id, "development-session:task-drift")
        self.assertIn("comparison base", action.reason)

    def test_missing_start_event_fails_closed_without_inventing_repair(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root, _ = create_development_repository(Path(temp_dir))
            for path in (root / ".agentgov/events").glob("*.json"):
                path.unlink()

            action = select_next_action(root)

        self.assertTrue(action.blocking)
        self.assertEqual(action.source_check_id, "development-session:start-event")
        self.assertIsNone(action.command)

    def test_malformed_session_is_a_blocking_result_not_an_operational_crash(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            initialize_project(root, project_name="Invalid Session", dry_run=False)
            state = root / ".agentgov"
            state.mkdir()
            pointer = state / "current-task.json"
            pointer.write_text("{broken\n", encoding="utf-8")
            before = pointer.read_bytes()

            action = select_next_action(root)
            after = pointer.read_bytes()

        self.assertTrue(action.blocking)
        self.assertEqual(action.source_check_id, "development-session:invalid")
        self.assertIsNone(action.command)
        self.assertEqual(after, before)

    def test_tracked_session_pointer_is_blocking_and_does_not_change_git_state(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root, _ = create_development_repository(Path(temp_dir))
            run_git(root, "add", ".agentgov/current-task.json")
            before = run_git(root, "status", "--short")

            action = select_next_action(root)
            after = run_git(root, "status", "--short")

        self.assertTrue(action.blocking)
        self.assertEqual(action.source_check_id, "development-session:invalid")
        self.assertIn("tracked", action.reason)
        self.assertEqual(after, before)

    def test_old_matching_event_does_not_replace_current_session_start(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root, session = create_development_repository(Path(temp_dir))
            add_progress_event(
                root,
                session,
                event_type="completion.reconciled",
                outcome="verified",
                occurred_at="2020-01-01T00:00:00.000Z",
            )

            action = select_next_action(root)

        self.assertEqual(action.source_check_id, "development-session:started")
        self.assertIn("govern check", action.command or "")


class NextActionCliTests(unittest.TestCase):
    def test_cli_outputs_exactly_one_non_blocking_action_for_empty_repository(
        self,
    ) -> None:
        with TemporaryDirectory() as temp_dir:
            exit_code, stdout, stderr = run_cli("next", temp_dir)

        self.assertEqual(exit_code, EXIT_PASS)
        self.assertEqual(stdout.count("ACTION "), 1)
        self.assertIn("COMMAND agentgov onboard", stdout)
        self.assertIn("did not execute the action", stdout)
        self.assertEqual(stderr, "")

    def test_cli_blocking_action_preserves_failure_exit(self) -> None:
        with TemporaryDirectory() as temp_dir:
            (Path(temp_dir) / "AGENTS.md").mkdir()
            exit_code, stdout, stderr = run_cli("next", temp_dir)

        self.assertEqual(exit_code, EXIT_FAIL)
        self.assertIn("BLOCKING yes", stdout)
        self.assertEqual(stderr, "")

    def test_cli_json_is_pure_and_non_interactive(self) -> None:
        with TemporaryDirectory() as temp_dir:
            exit_code, stdout, stderr = run_cli(
                "next",
                temp_dir,
                "--format",
                "json",
                "--non-interactive",
            )
            payload = json.loads(stdout)

        self.assertEqual(exit_code, EXIT_PASS)
        self.assertEqual(payload["interaction"], "non_interactive")
        self.assertFalse(payload["authority_boundary"]["action_executed"])
        self.assertEqual(stderr, "")

    def test_cli_missing_path_is_operational_error(self) -> None:
        with TemporaryDirectory() as temp_dir:
            missing = Path(temp_dir) / "missing"
            exit_code, stdout, stderr = run_cli("next", str(missing))

        self.assertEqual(exit_code, EXIT_ERROR)
        self.assertEqual(stdout, "")
        self.assertIn("ERROR next: repository path not found:", stderr)

    def test_schema_is_strict_and_denies_execution_authority(self) -> None:
        schema = json.loads(
            (ROOT / "schemas/next-action.schema.json").read_text(encoding="utf-8")
        )

        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(schema["properties"]["mode"]["const"], "read_only")
        self.assertEqual(schema["properties"]["tool"]["properties"]["name"]["const"], "agentgov")
        self.assertIn("version", schema["properties"]["tool"]["required"])
        authority = schema["properties"]["authority_boundary"]
        self.assertFalse(authority["additionalProperties"])
        for property_schema in authority["properties"].values():
            self.assertIs(property_schema["const"], False)


if __name__ == "__main__":
    unittest.main()
