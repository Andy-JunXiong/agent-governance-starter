import contextlib
import io
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from agentgov.cli import EXIT_ERROR, EXIT_FAIL, EXIT_PASS, main
from agentgov.consumer_ci import (
    UPGRADE_WORKFLOW_PATH,
    WORKFLOW_PATH,
    apply_integration_plan,
    plan_github_actions_integration,
    render_consumer_workflow,
    render_consumer_upgrade_workflow,
)
from agentgov.initializer import initialize_project


ROOT = Path(__file__).resolve().parents[1]


def run_cli(*args: str) -> tuple[int, str, str]:
    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        exit_code = main(list(args))
    return exit_code, stdout.getvalue(), stderr.getvalue()


def declare_synthetic_caller(root: Path) -> None:
    manifest_path = root / "governance/capabilities/example-capability.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["called_by"] = ["src/example_caller.py"]
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    caller = root / "src/example_caller.py"
    caller.parent.mkdir(parents=True)
    caller.write_text("# synthetic status fixture\n", encoding="utf-8")


class StatusCommandTests(unittest.TestCase):
    def test_status_explains_adoption_usage_and_manual_only_ci(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            initialize_project(root, project_name="Visible Fixture")
            declare_synthetic_caller(root)

            exit_code, stdout, stderr = run_cli("status", temp_dir)

        self.assertEqual(exit_code, EXIT_PASS)
        self.assertIn("ADOPTION configured=yes layout=1.0", stdout)
        self.assertIn("CI state=missing", stdout)
        self.assertIn("CAPABILITY example-capability:", stdout)
        self.assertIn("USED_BY example-capability:", stdout)
        self.assertIn("SURFACE repository_validation: state=available", stdout)
        self.assertIn("SURFACE pull_request_visibility: state=missing", stdout)
        self.assertIn("SURFACE benefit_evidence: state=not_configured", stdout)
        self.assertIn("SURFACE upgrade_automation: state=review_ready", stdout)
        self.assertIn("agentgov integrate github-actions", stdout)
        self.assertEqual(stderr, "")

    def test_status_reports_managed_ci_as_active(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            initialize_project(root, project_name="Integrated Fixture")
            apply_integration_plan(plan_github_actions_integration(root))

            exit_code, stdout, stderr = run_cli("status", temp_dir)

        self.assertEqual(exit_code, EXIT_PASS)
        self.assertIn("CI state=managed", stdout)
        self.assertIn("SURFACE pull_request_visibility: state=active", stdout)
        self.assertIn("SURFACE benefit_evidence: state=ready_to_collect", stdout)
        self.assertIn("SURFACE upgrade_automation: state=review_ready", stdout)
        self.assertEqual(stderr, "")

    def test_status_makes_0_3_draft_pr_automation_visible(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            initialize_project(root, project_name="Proposal Fixture")
            target = root / WORKFLOW_PATH
            target.parent.mkdir(parents=True)
            target.write_text(
                render_consumer_workflow(
                    version="0.3.0",
                    wheel_sha256="f" * 64,
                ),
                encoding="utf-8",
            )
            upgrade_target = root / UPGRADE_WORKFLOW_PATH
            upgrade_target.write_text(
                render_consumer_upgrade_workflow(
                    version="0.3.0",
                    wheel_sha256="f" * 64,
                ),
                encoding="utf-8",
            )

            exit_code, stdout, stderr = run_cli("status", temp_dir)

        self.assertEqual(exit_code, EXIT_PASS)
        self.assertIn("SURFACE benefit_evidence: state=monitor_enabled", stdout)
        self.assertIn("SURFACE upgrade_automation: state=proposal_enabled", stdout)
        self.assertIn("merge remains human-controlled", stdout)
        self.assertEqual(stderr, "")

    def test_status_does_not_claim_writer_when_only_read_only_0_3_workflow_exists(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            initialize_project(root, project_name="Read-only 0.3 Fixture")
            target = root / WORKFLOW_PATH
            target.parent.mkdir(parents=True)
            target.write_text(
                render_consumer_workflow(version="0.3.0", wheel_sha256="f" * 64),
                encoding="utf-8",
            )

            exit_code, stdout, stderr = run_cli("status", temp_dir)

        self.assertEqual(exit_code, EXIT_PASS)
        self.assertIn("SURFACE benefit_evidence: state=monitor_enabled", stdout)
        self.assertIn("SURFACE upgrade_automation: state=review_ready", stdout)
        self.assertNotIn("state=proposal_enabled", stdout)
        self.assertEqual(stderr, "")

    def test_json_status_is_read_only_and_preserves_exact_usage(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            initialize_project(root, project_name="JSON Fixture")
            declare_synthetic_caller(root)

            exit_code, stdout, stderr = run_cli(
                "status", temp_dir, "--format", "json", "--non-interactive"
            )
            payload = json.loads(stdout)

        self.assertEqual(exit_code, EXIT_PASS)
        self.assertEqual(payload["mode"], "read_only")
        self.assertEqual(payload["interaction"], "non_interactive")
        self.assertTrue(payload["adoption"]["configured"])
        self.assertEqual(payload["ci"]["state"], "missing")
        self.assertEqual(payload["capabilities"][0]["name"], "example-capability")
        self.assertGreaterEqual(len(payload["capabilities"][0]["called_by"]), 1)
        for value in payload["authority_boundary"].values():
            self.assertFalse(value)
        self.assertEqual(stderr, "")

    def test_markdown_status_is_job_summary_ready_and_read_only(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            initialize_project(root, project_name="Markdown Fixture")
            declare_synthetic_caller(root)

            first = run_cli(
                "status", temp_dir, "--format", "markdown", "--non-interactive"
            )
            second = run_cli(
                "status", temp_dir, "--format", "markdown", "--non-interactive"
            )

        exit_code, stdout, stderr = first
        self.assertEqual(first, second)
        self.assertEqual(exit_code, EXIT_PASS)
        self.assertTrue(stdout.startswith("# AgentGov Status\n"))
        self.assertIn("## Governed capabilities", stdout)
        self.assertIn("`example-capability`", stdout)
        self.assertIn("`pull_request_visibility`", stdout)
        self.assertIn("## Next action", stdout)
        self.assertIn("## Authority boundary", stdout)
        self.assertIn("Repository files were not modified.", stdout)
        self.assertIn("agentgov check repository .", stdout)
        self.assertNotIn(str(root.resolve()), stdout)
        self.assertEqual(stderr, "")

    def test_markdown_status_preserves_failure_exit_semantics(self) -> None:
        with TemporaryDirectory() as temp_dir:
            exit_code, stdout, stderr = run_cli(
                "status", temp_dir, "--format", "markdown"
            )

        self.assertEqual(exit_code, EXIT_FAIL)
        self.assertIn("| PASS | WARN | FAIL | ADVISORY |", stdout)
        self.assertEqual(stderr, "")

    def test_repository_failure_remains_a_failing_status_exit(self) -> None:
        with TemporaryDirectory() as temp_dir:
            exit_code, stdout, stderr = run_cli("status", temp_dir)

        self.assertEqual(exit_code, EXIT_FAIL)
        self.assertIn("ADOPTION configured=no", stdout)
        self.assertIn("FAIL=", stdout)
        self.assertEqual(stderr, "")

    def test_invalid_contract_is_visible_and_failing(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            initialize_project(root, project_name="Contract Fixture")
            (root / "governance/contract.json").write_text("{}\n", encoding="utf-8")

            exit_code, stdout, stderr = run_cli("status", temp_dir)

        self.assertEqual(exit_code, EXIT_FAIL)
        self.assertIn("layout=invalid", stdout)
        self.assertIn("FAIL repository-contract:", stdout)
        self.assertEqual(stderr, "")

    def test_missing_path_is_operational_error(self) -> None:
        with TemporaryDirectory() as temp_dir:
            missing = Path(temp_dir) / "missing"
            exit_code, stdout, stderr = run_cli("status", str(missing))

        self.assertEqual(exit_code, EXIT_ERROR)
        self.assertEqual(stdout, "")
        self.assertIn("ERROR status: repository path not found", stderr)

    def test_schema_is_strict_and_read_only(self) -> None:
        schema = json.loads(
            (ROOT / "schemas/status-report.schema.json").read_text(encoding="utf-8")
        )

        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(schema["properties"]["mode"]["const"], "read_only")
        authority = schema["properties"]["authority_boundary"]
        for property_schema in authority["properties"].values():
            self.assertIs(property_schema["const"], False)


if __name__ == "__main__":
    unittest.main()
