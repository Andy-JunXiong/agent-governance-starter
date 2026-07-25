import contextlib
import io
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from agentgov import __version__
from agentgov.cli import EXIT_ERROR, EXIT_FAIL, EXIT_PASS, main
from agentgov.initializer import initialize_project
from agentgov.next_action import (
    ActionKind,
    render_next_action_json,
    select_next_action,
    select_report_next_action,
)
from agentgov.repository import Finding, FindingStatus, RepositoryReport


ROOT = Path(__file__).resolve().parents[1]


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

    def test_initialized_repository_maps_first_warning_to_incomplete_evidence(
        self,
    ) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            initialize_project(root, project_name="Warning Fixture", dry_run=False)
            (root / "governance/artifacts").mkdir()

            action = select_next_action(root)

        self.assertIs(action.kind, ActionKind.INCOMPLETE_EVIDENCE)
        self.assertFalse(action.blocking)
        self.assertIsNotNone(action.source_check_id)

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
