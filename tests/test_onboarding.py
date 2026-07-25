import contextlib
import io
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from agentgov import __version__
from agentgov.cli import EXIT_ERROR, EXIT_FAIL, EXIT_PASS, main
from agentgov.onboarding import (
    OnboardingConflictError,
    apply_onboarding_plan,
    plan_onboarding,
    render_onboarding_plan_json,
    request_onboarding_confirmation,
)


ROOT = Path(__file__).resolve().parents[1]


class FakeTerminal(io.StringIO):
    def isatty(self) -> bool:
        return True


def run_cli(*args: str) -> tuple[int, str, str]:
    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        try:
            exit_code = main(list(args))
        except SystemExit as exc:
            exit_code = int(exc.code)
    return exit_code, stdout.getvalue(), stderr.getvalue()


class OnboardingPlanTests(unittest.TestCase):
    def test_empty_repository_plan_is_complete_and_read_only(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            before = tuple(root.rglob("*"))

            plan = plan_onboarding(root, project_name="Guided Project")
            after = tuple(root.rglob("*"))

        self.assertEqual(before, after)
        self.assertTrue(plan.adoption.dry_run)
        self.assertEqual(len(plan.adoption.planned_files), 25)
        self.assertEqual(plan.adoption.preserved_files, ())

    def test_existing_files_are_preserved_in_preview(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            existing = root / "AGENTS.md"
            existing.write_text("existing policy\n", encoding="utf-8")

            plan = plan_onboarding(root, project_name="Guided Project")
            content_after = existing.read_text(encoding="utf-8")

        self.assertEqual(content_after, "existing policy\n")
        self.assertIn(Path("AGENTS.md"), plan.adoption.preserved_files)
        self.assertNotIn(
            Path("AGENTS.md"),
            {item.relative_path for item in plan.adoption.planned_files},
        )

    def test_existing_capability_area_does_not_receive_example_capability(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            capability_area = root / "governance/capabilities"
            capability_area.mkdir(parents=True)
            existing = capability_area / "real-capability.json"
            existing.write_text("{}\n", encoding="utf-8")

            plan = plan_onboarding(root, project_name="Existing Governance")
            planned = {
                item.relative_path.as_posix()
                for item in plan.adoption.planned_files
            }

        self.assertNotIn(
            "governance/capabilities/example-capability.json",
            planned,
        )
        self.assertFalse(any(path.startswith("governance/") for path in planned))

    def test_json_plan_denies_every_write_authority(self) -> None:
        with TemporaryDirectory() as temp_dir:
            plan = plan_onboarding(
                Path(temp_dir),
                project_name="Automation Preview",
            )
            payload = json.loads(
                render_onboarding_plan_json(plan, non_interactive=True)
            )

        self.assertEqual(payload["mode"], "dry_run")
        self.assertEqual(
            payload["tool"],
            {"name": "agentgov", "version": __version__},
        )
        self.assertEqual(payload["interaction"], "non_interactive")
        self.assertEqual(
            payload["authority_boundary"],
            {
                "modifies_repository": False,
                "write_authorized": False,
                "repairs_project_environment": False,
                "installs_project_dependencies": False,
                "authorizes_git_or_release_operations": False,
            },
        )
        self.assertEqual(len(payload["plan"]["create"]), 25)

    def test_confirmation_requires_exact_adopt_from_interactive_terminal(self) -> None:
        with TemporaryDirectory() as temp_dir:
            plan = plan_onboarding(Path(temp_dir), project_name="Decision Fixture")

        self.assertTrue(
            request_onboarding_confirmation(
                plan,
                decision_reader=lambda _: "ADOPT",
                is_interactive_terminal=True,
            )
        )
        for decision, interactive in (
            ("adopt", True),
            ("yes", True),
            ("ADOPT", False),
        ):
            with self.subTest(decision=decision, interactive=interactive):
                self.assertFalse(
                    request_onboarding_confirmation(
                        plan,
                        decision_reader=lambda _, value=decision: value,
                        is_interactive_terminal=interactive,
                    )
                )

    def test_apply_revalidates_every_target_before_writing(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            plan = plan_onboarding(root, project_name="Race Fixture")
            appeared = root / "docs/adr/TEMPLATE.md"
            appeared.parent.mkdir(parents=True)
            appeared.write_text("appeared\n", encoding="utf-8")

            with self.assertRaises(OnboardingConflictError):
                apply_onboarding_plan(plan)

            agents_was_not_created = not (root / "AGENTS.md").exists()

        self.assertTrue(agents_was_not_created)


class OnboardingCliTests(unittest.TestCase):
    def test_text_preview_shows_exact_target_plan_and_no_write_notes(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            exit_code, stdout, stderr = run_cli(
                "onboard",
                str(root),
                "--project-name",
                "CLI Preview",
                "--dry-run",
            )
            files_after = tuple(root.rglob("*"))

        self.assertEqual(exit_code, EXIT_PASS)
        self.assertEqual(files_after, ())
        self.assertIn(f"TARGET onboard: {root.resolve()}", stdout)
        self.assertIn("PLAN AGENTS.md", stdout)
        self.assertIn("SUMMARY CREATE=25 PRESERVE=0", stdout)
        self.assertIn("does not authorize a later write", stdout)
        self.assertEqual(stderr, "")

    def test_non_interactive_json_is_pure_and_does_not_write(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            exit_code, stdout, stderr = run_cli(
                "onboard",
                str(root),
                "--project-name",
                "Automation Preview",
                "--dry-run",
                "--format",
                "json",
                "--non-interactive",
            )
            payload = json.loads(stdout)
            files_after = tuple(root.rglob("*"))

        self.assertEqual(exit_code, EXIT_PASS)
        self.assertEqual(files_after, ())
        self.assertEqual(payload["interaction"], "non_interactive")
        self.assertFalse(payload["authority_boundary"]["write_authorized"])
        self.assertEqual(stderr, "")

    def test_redirected_confirmation_text_cannot_authorize_writes(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            redirected = io.StringIO("ADOPT\n")
            with patch("sys.stdin", redirected):
                exit_code, stdout, stderr = run_cli(
                    "onboard",
                    temp_dir,
                    "--project-name",
                    "Redirected Input",
                )
            files_after = tuple(root.rglob("*"))

        self.assertEqual(exit_code, EXIT_PASS)
        self.assertEqual(files_after, ())
        self.assertIn("CANCELLED onboard:", stdout)
        self.assertEqual(stderr, "")

    def test_non_interactive_mode_without_dry_run_is_rejected(self) -> None:
        with TemporaryDirectory() as temp_dir:
            exit_code, stdout, stderr = run_cli(
                "onboard",
                temp_dir,
                "--project-name",
                "Automation Write",
                "--non-interactive",
            )

        self.assertEqual(exit_code, EXIT_ERROR)
        self.assertEqual(stdout, "")
        self.assertIn("--non-interactive never authorizes writes", stderr)

    def test_interactive_cancellation_leaves_repository_unchanged(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            terminal = FakeTerminal("NO\n")
            with patch("sys.stdin", terminal):
                exit_code, stdout, stderr = run_cli(
                    "onboard",
                    str(root),
                    "--project-name",
                    "Cancelled Adoption",
                )
            files_after = tuple(root.rglob("*"))

        self.assertEqual(exit_code, EXIT_PASS)
        self.assertEqual(files_after, ())
        self.assertIn("CANCELLED onboard:", stdout)
        self.assertEqual(stderr, "")

    def test_exact_interactive_confirmation_creates_reviewed_files(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            terminal = FakeTerminal("ADOPT\n")
            with patch("sys.stdin", terminal):
                exit_code, stdout, stderr = run_cli(
                    "onboard",
                    str(root),
                    "--project-name",
                    "Confirmed Adoption",
                )

            created_agents = (root / "AGENTS.md").is_file()
            created_example = (
                root / "governance/capabilities/example-capability.json"
            ).is_file()

        self.assertEqual(exit_code, EXIT_PASS)
        self.assertTrue(created_agents)
        self.assertTrue(created_example)
        self.assertIn("PASS onboard: created 25 reviewed file(s)", stdout)
        self.assertIn(
            "CHECK onboard: running the first read-only repository check",
            stdout,
        )
        self.assertIn("SUMMARY PASS=14 WARN=4 FAIL=0 ADVISORY=4", stdout)
        self.assertIn("NEXT onboard: run `agentgov next`", stdout)
        self.assertIn("does not authorize Git", stdout)
        self.assertEqual(stderr, "")

    def test_conflict_blocks_preview_without_writing(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            conflict = root / "AGENTS.md"
            conflict.mkdir()

            exit_code, stdout, stderr = run_cli(
                "onboard",
                str(root),
                "--project-name",
                "Conflict Preview",
                "--dry-run",
            )
            paths_after = tuple(root.rglob("*"))

        self.assertEqual(exit_code, EXIT_FAIL)
        self.assertEqual(paths_after, (conflict,))
        self.assertIn("FAIL onboard: resolve adoption conflicts first:", stdout)
        self.assertIn("no repository files were created or modified", stdout)
        self.assertEqual(stderr, "")

    def test_missing_path_is_operational_error(self) -> None:
        with TemporaryDirectory() as temp_dir:
            missing = Path(temp_dir) / "missing"
            exit_code, stdout, stderr = run_cli(
                "onboard",
                str(missing),
                "--project-name",
                "Missing Preview",
                "--dry-run",
            )

        self.assertEqual(exit_code, EXIT_ERROR)
        self.assertEqual(stdout, "")
        self.assertIn("ERROR onboard: repository path not found:", stderr)

    def test_schema_is_strict_and_denies_write_authority(self) -> None:
        schema = json.loads(
            (ROOT / "schemas/onboarding-plan.schema.json").read_text(
                encoding="utf-8"
            )
        )

        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(schema["properties"]["mode"]["const"], "dry_run")
        self.assertEqual(schema["properties"]["tool"]["properties"]["name"]["const"], "agentgov")
        self.assertIn("version", schema["properties"]["tool"]["required"])
        authority = schema["properties"]["authority_boundary"]
        self.assertFalse(authority["additionalProperties"])
        for property_schema in authority["properties"].values():
            self.assertIs(property_schema["const"], False)


if __name__ == "__main__":
    unittest.main()
