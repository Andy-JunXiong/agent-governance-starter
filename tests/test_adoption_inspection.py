import contextlib
import io
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from agentgov import __version__
from agentgov.adoption import (
    ADOPTION_REPORT_VERSION,
    AdoptionConflictError,
    AdoptionState,
    adopt_existing_repository,
    inspect_adoption,
    render_adoption_report_json,
)
from agentgov.cli import EXIT_ERROR, EXIT_FAIL, EXIT_PASS, main
from agentgov.initializer import initialize_project


def run_cli(*args: str) -> tuple[int, str, str]:
    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        exit_code = main(list(args))
    return exit_code, stdout.getvalue(), stderr.getvalue()


class AdoptionInspectionTests(unittest.TestCase):
    def test_empty_existing_repository_reports_missing_without_writing(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            before = tuple(root.iterdir())

            report = inspect_adoption(root)

            after = tuple(root.iterdir())

        self.assertEqual(before, after)
        self.assertEqual(report.count(AdoptionState.MISSING), 6)
        self.assertEqual(report.count(AdoptionState.PRESENT), 0)
        self.assertIn("missing governance paths", " ".join(report.recommendations))

    def test_existing_instruction_files_are_discovered_but_not_interpreted(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / ".github").mkdir()
            (root / "CLAUDE.md").write_text("private policy\n", encoding="utf-8")
            (root / ".github/copilot-instructions.md").write_text(
                "other policy\n", encoding="utf-8"
            )

            report = inspect_adoption(root)

        discovered = [
            item.path.as_posix()
            for item in report.items
            if item.state is AdoptionState.DISCOVERED
        ]
        self.assertEqual(discovered, ["CLAUDE.md", ".github/copilot-instructions.md"])
        self.assertNotIn("private policy", repr(report))
        self.assertNotIn("other policy", repr(report))

    def test_initialized_repository_is_present_and_points_to_validation(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "project"
            initialize_project(root, project_name="Existing Project")

            report = inspect_adoption(root)

        self.assertEqual(report.count(AdoptionState.PRESENT), 6)
        self.assertEqual(report.count(AdoptionState.MISSING), 0)
        self.assertNotIn(
            "governance/artifacts",
            {item.path.as_posix() for item in report.items},
        )

    def test_wrong_path_type_is_a_deterministic_conflict(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "AGENTS.md").mkdir()

            report = inspect_adoption(root)

        conflict = next(
            item for item in report.items if item.check_id == "governance:constitution"
        )
        self.assertIs(conflict.state, AdoptionState.CONFLICT)
        self.assertIn("not the expected file", conflict.message)
        self.assertTrue(report.has_conflicts)

    def test_json_rendering_is_deterministic_and_preserves_authority_boundary(self) -> None:
        with TemporaryDirectory() as temp_dir:
            report = inspect_adoption(Path(temp_dir))
            first = render_adoption_report_json(report)
            second = render_adoption_report_json(report)

        self.assertEqual(first, second)
        payload = json.loads(first)
        self.assertEqual(payload["contract_version"], ADOPTION_REPORT_VERSION)
        self.assertEqual(
            payload["tool"],
            {"name": "agentgov", "version": __version__},
        )
        self.assertEqual(payload["mode"], "read_only")
        self.assertFalse(payload["authority_boundary"]["inspection_modifies_repository"])
        self.assertFalse(
            payload["authority_boundary"]["authorizes_merge_publish_release_or_deploy"]
        )

    def test_cli_returns_non_blocking_plan_and_is_read_only(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)

            exit_code, stdout, stderr = run_cli("inspect", str(root))

            self.assertEqual(tuple(root.iterdir()), ())

        self.assertEqual(exit_code, EXIT_PASS)
        self.assertIn("MISSING governance:constitution:", stdout)
        self.assertIn("SUMMARY PRESENT=0 MISSING=6 DISCOVERED=0 CONFLICT=0", stdout)
        self.assertIn("NOTE inspect: no repository files were created or modified", stdout)
        self.assertEqual(stderr, "")

    def test_cli_json_is_pure_json_and_conflict_returns_policy_failure(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "evaluation").write_text("wrong type\n", encoding="utf-8")

            exit_code, stdout, stderr = run_cli(
                "inspect", str(root), "--format", "json"
            )

        payload = json.loads(stdout)
        self.assertEqual(exit_code, EXIT_FAIL)
        self.assertEqual(payload["summary"]["CONFLICT"], 1)
        self.assertEqual(stderr, "")

    def test_distributed_schema_declares_the_v1_contract(self) -> None:
        schema_path = Path(__file__).resolve().parents[1] / "schemas/adoption-report.schema.json"
        schema = json.loads(schema_path.read_text(encoding="utf-8"))

        self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(schema["properties"]["contract_version"]["const"], "1.0")
        self.assertEqual(schema["properties"]["tool"]["properties"]["name"]["const"], "agentgov")
        self.assertIn("version", schema["properties"]["tool"]["required"])

    def test_cli_missing_repository_is_an_operational_error(self) -> None:
        with TemporaryDirectory() as temp_dir:
            missing = Path(temp_dir) / "missing"
            exit_code, stdout, stderr = run_cli("inspect", str(missing))

        self.assertEqual(exit_code, EXIT_ERROR)
        self.assertEqual(stdout, "")
        self.assertIn("ERROR inspect: repository path not found:", stderr)


class ExistingRepositoryAdoptionTests(unittest.TestCase):
    def test_dry_run_plans_missing_files_and_writes_nothing(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            existing = root / "AGENTS.md"
            existing.write_text("existing policy\n", encoding="utf-8")

            report = adopt_existing_repository(
                root,
                project_name="Adopted Project",
                dry_run=True,
            )

            files_after = tuple(path.relative_to(root) for path in root.rglob("*"))

        self.assertEqual(files_after, (Path("AGENTS.md"),))
        self.assertIn(Path("AGENTS.md"), report.preserved_files)
        self.assertNotIn(
            Path("AGENTS.md"),
            {item.relative_path for item in report.planned_files},
        )

    def test_adoption_creates_only_missing_files_and_preserves_existing_content(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            existing = root / "AGENTS.md"
            existing.write_text("existing policy\n", encoding="utf-8")

            report = adopt_existing_repository(
                root,
                project_name="Adopted Project",
                dry_run=False,
            )

            preserved_content = existing.read_text(encoding="utf-8")
            created_adr = (root / "docs/adr/TEMPLATE.md").is_file()

        self.assertEqual(preserved_content, "existing policy\n")
        self.assertTrue(created_adr)
        self.assertIn(Path("AGENTS.md"), report.preserved_files)
        self.assertGreater(len(report.planned_files), 0)

    def test_adoption_rejects_parent_path_conflict_before_writing(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "docs").write_text("not a directory\n", encoding="utf-8")

            with self.assertRaises(AdoptionConflictError):
                adopt_existing_repository(
                    root,
                    project_name="Conflict Project",
                    dry_run=False,
                )

            files_after = tuple(path.relative_to(root) for path in root.iterdir())

        self.assertEqual(files_after, (Path("docs"),))

    def test_cli_adopt_dry_run_and_write_have_explicit_semantics(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            dry_code, dry_stdout, dry_stderr = run_cli(
                "adopt",
                str(root),
                "--project-name",
                "CLI Adoption",
                "--dry-run",
            )
            empty_after_dry_run = tuple(root.iterdir())
            write_code, write_stdout, write_stderr = run_cli(
                "adopt",
                str(root),
                "--project-name",
                "CLI Adoption",
            )

        self.assertEqual(dry_code, EXIT_PASS)
        self.assertEqual(empty_after_dry_run, ())
        self.assertIn("PLAN AGENTS.md", dry_stdout)
        self.assertIn("no repository files were created or modified", dry_stdout)
        self.assertEqual(dry_stderr, "")
        self.assertEqual(write_code, EXIT_PASS)
        self.assertIn("CREATE AGENTS.md", write_stdout)
        self.assertIn("does not authorize merge", write_stdout)
        self.assertEqual(write_stderr, "")


if __name__ == "__main__":
    unittest.main()
