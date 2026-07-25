import contextlib
import io
import tomllib
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from agentgov.agent_skills import check_agent_skills
from agentgov.capability import load_capability_manifest, validate_capability_manifest
from agentgov.cli import EXIT_ERROR, EXIT_FAIL, EXIT_PASS, main
from agentgov.controls import ControlStatus, check_control_mapping
from agentgov.evaluation import EvaluationStatus, check_evaluation_bundle
from agentgov.initializer import InitConflictError, initialize_project
from agentgov.inventory import InventoryStatus, check_inventory
from agentgov.references import ReferenceStatus, check_capability_references


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_OUTPUTS = {
    Path("AGENTS.md"),
    Path("docs/adr/TEMPLATE.md"),
    Path("docs/adr/INVARIANTS.md"),
    Path("governance/capability.schema.json"),
    Path("governance/capability-dependencies.schema.json"),
    Path("governance/control-mapping.schema.json"),
    Path("governance/inventory.schema.json"),
    Path("governance/inventory.json"),
    Path("governance/contract.json"),
    Path("governance/capabilities/example-capability.json"),
    Path("governance/controls/example-capability.json"),
    Path("governance/dependencies/example-capability.json"),
    Path("governance/contracts/example-capability.input.schema.json"),
    Path("governance/contracts/example-capability.output.schema.json"),
    Path("governance/evidence/example-capability.md"),
    Path("evaluation/example-capability/evaluation-manifest.json"),
    Path("evaluation/readiness-policy.md"),
    Path("evaluation/schemas/evaluation-manifest.schema.json"),
    Path("evaluation/schemas/seed-case.schema.json"),
    Path("evaluation/schemas/golden-example.schema.json"),
    Path("evaluation/schemas/failure-case.schema.json"),
    Path("agent-skills/README.md"),
    Path("agent-skills/context-first-review/SKILL.md"),
    Path("agent-skills/development-slice/SKILL.md"),
    Path("agent-skills/incident-attribution/SKILL.md"),
    Path("agent-skills/incident-response/SKILL.md"),
}


def run_cli(*args: str) -> tuple[int, str, str]:
    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        exit_code = main(list(args))
    return exit_code, stdout.getvalue(), stderr.getvalue()


class InitializerTests(unittest.TestCase):
    def test_dry_run_plans_expected_files_without_writing(self) -> None:
        with TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "new-project"

            report = initialize_project(target, project_name="Demo Project", dry_run=True)

            self.assertFalse(target.exists())
            self.assertEqual({item.relative_path for item in report.files}, EXPECTED_OUTPUTS)
            self.assertNotIn("{{PROJECT_NAME}}", "".join(item.content for item in report.files))
            self.assertTrue(report.unresolved_placeholders)

    def test_init_writes_scaffold_and_valid_capability(self) -> None:
        with TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "new-project"

            report = initialize_project(target, project_name="Demo Project")

            self.assertFalse(report.dry_run)
            for relative_path in EXPECTED_OUTPUTS:
                self.assertTrue((target / relative_path).is_file())
            agents_text = (target / "AGENTS.md").read_text(encoding="utf-8")
            self.assertIn("# AGENTS.md - Demo Project", agents_text)
            self.assertNotIn("{{PROJECT_NAME}}", agents_text)
            capability_path = target / "governance/capabilities/example-capability.json"
            self.assertEqual(
                validate_capability_manifest(load_capability_manifest(capability_path)),
                [],
            )
            evaluation_result = check_evaluation_bundle(
                target / "evaluation/example-capability"
            )
            self.assertIs(evaluation_result.status, EvaluationStatus.WARN)
            self.assertEqual(evaluation_result.readiness, "needs_seed_cases")
            self.assertFalse(check_agent_skills(target / "agent-skills").has_failures)
            prompt_source = (
                target / "governance/evidence/example-capability.md"
            ).read_text(encoding="utf-8")
            self.assertNotIn("{{", prompt_source)
            self.assertIn("Demo Project", prompt_source)
            reference_report = check_capability_references(
                capability_path,
                repository=target,
            )
            self.assertFalse(reference_report.has_failures)
            self.assertEqual(reference_report.count(ReferenceStatus.PASS), 3)
            self.assertEqual(reference_report.count(ReferenceStatus.WARN), 1)
            inventory_report = check_inventory(target)
            self.assertIs(inventory_report.status, InventoryStatus.PASS)
            control_report = check_control_mapping(
                target,
                target / "governance/controls/example-capability.json",
            )
            self.assertIs(control_report.status, ControlStatus.PASS)

    def test_non_empty_target_is_rejected_without_overwriting(self) -> None:
        with TemporaryDirectory() as temp_dir:
            target = Path(temp_dir)
            existing = target / "existing.txt"
            existing.write_text("human work\n", encoding="utf-8")

            with self.assertRaises(InitConflictError):
                initialize_project(target, project_name="Demo Project")

            self.assertEqual(existing.read_text(encoding="utf-8"), "human work\n")
            self.assertEqual({path.name for path in target.iterdir()}, {"existing.txt"})

    def test_project_name_rejects_template_delimiter_injection(self) -> None:
        with TemporaryDirectory() as temp_dir:
            with self.assertRaises(ValueError):
                initialize_project(
                    Path(temp_dir) / "target",
                    project_name="{{PROJECT_NAME}}",
                    dry_run=True,
                )

    def test_templates_are_configured_as_installable_data_files(self) -> None:
        pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
        data_files = pyproject["tool"]["setuptools"]["data-files"]

        self.assertIn("share/agent-governance-starter/templates", data_files)
        self.assertIn("share/agent-governance-starter/evaluation", data_files)
        self.assertIn("share/agent-governance-starter/evaluation/schemas", data_files)
        self.assertIn("share/agent-governance-starter/governance", data_files)
        self.assertIn("share/agent-governance-starter/agent-skills", data_files)
        self.assertIn(
            "share/agent-governance-starter/agent-skills/context-first-review",
            data_files,
        )
        self.assertIn(
            "share/agent-governance-starter/agent-skills/development-slice",
            data_files,
        )
        self.assertIn(
            "share/agent-governance-starter/agent-skills/incident-attribution",
            data_files,
        )
        self.assertIn(
            "share/agent-governance-starter/agent-skills/incident-response",
            data_files,
        )


class InitCliTests(unittest.TestCase):
    def test_cli_requires_project_name_as_usage_contract(self) -> None:
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            with self.assertRaises(SystemExit) as raised:
                main(["init", "new-project", "--dry-run"])

        self.assertEqual(raised.exception.code, EXIT_ERROR)
        self.assertIn("--project-name", stderr.getvalue())

    def test_cli_dry_run_returns_pass_and_does_not_write(self) -> None:
        with TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "preview"

            exit_code, stdout, stderr = run_cli(
                "init", str(target), "--project-name", "Preview Project", "--dry-run"
            )

            self.assertEqual(exit_code, EXIT_PASS)
            self.assertFalse(target.exists())
            self.assertIn("PLAN AGENTS.md", stdout)
            self.assertIn("WARN init:", stdout)
            self.assertIn("PASS init dry-run:", stdout)
            self.assertIn("NEXT init dry-run:", stdout)
            self.assertIn("does not authorize merge, publish, release, or deploy", stdout)
            self.assertEqual(stderr, "")

    def test_cli_init_writes_files_and_reports_unresolved_placeholders(self) -> None:
        with TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "created"

            exit_code, stdout, stderr = run_cli(
                "init", str(target), "--project-name", "Created Project"
            )

            self.assertEqual(exit_code, EXIT_PASS)
            self.assertTrue((target / "AGENTS.md").exists())
            self.assertIn("CREATE AGENTS.md", stdout)
            self.assertIn("WARN init:", stdout)
            self.assertIn("PASS init:", stdout)
            self.assertIn("NEXT init: review", stdout)
            self.assertIn("agentgov check repository", stdout)
            self.assertIn("does not mean governance is complete", stdout)
            self.assertIn("does not authorize merge, publish, release, or deploy", stdout)
            self.assertEqual(stderr, "")

    def test_cli_refuses_non_empty_target_as_policy_failure(self) -> None:
        with TemporaryDirectory() as temp_dir:
            target = Path(temp_dir)
            existing = target / "keep.txt"
            existing.write_text("keep\n", encoding="utf-8")

            exit_code, stdout, stderr = run_cli(
                "init", str(target), "--project-name", "Blocked Project"
            )

            self.assertEqual(exit_code, EXIT_FAIL)
            self.assertIn("FAIL init: target directory is not empty:", stdout)
            self.assertEqual(stderr, "")
            self.assertEqual(existing.read_text(encoding="utf-8"), "keep\n")

    def test_cli_invalid_project_name_is_usage_error(self) -> None:
        with TemporaryDirectory() as temp_dir:
            exit_code, stdout, stderr = run_cli(
                "init",
                str(Path(temp_dir) / "target"),
                "--project-name",
                "  ",
                "--dry-run",
            )

        self.assertEqual(exit_code, EXIT_ERROR)
        self.assertEqual(stdout, "")
        self.assertIn("ERROR init: project name must not be empty", stderr)


if __name__ == "__main__":
    unittest.main()
