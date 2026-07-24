import contextlib
import io
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from agentgov.cli import EXIT_ERROR, EXIT_FAIL, EXIT_PASS, main
from agentgov.doctor import (
    DoctorStatus,
    WINDOWS_PATH_ADVISORY_THRESHOLD,
    diagnose_repository,
    render_doctor_report_json,
)
from agentgov.initializer import initialize_project


ROOT = Path(__file__).resolve().parents[1]


def run_cli(*args: str) -> tuple[int, str, str]:
    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        exit_code = main(list(args))
    return exit_code, stdout.getvalue(), stderr.getvalue()


class DoctorTests(unittest.TestCase):
    def test_unconfigured_repository_is_non_blocking_and_read_only(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            before = tuple(root.iterdir())

            report = diagnose_repository(
                root,
                python_version=(3, 12, 10),
                python_executable=Path("isolated/python.exe"),
                platform_name="nt",
            )
            after = tuple(root.iterdir())

        self.assertEqual(before, after)
        self.assertFalse(report.has_failures)
        self.assertTrue(
            any(
                finding.check_id == "adoption:state"
                and finding.status is DoctorStatus.WARN
                for finding in report.findings
            )
        )

    def test_configured_git_repository_is_healthy(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            initialize_project(root, project_name="Doctor Fixture", dry_run=False)
            (root / ".git").mkdir()
            (root / "governance/artifacts").mkdir()

            report = diagnose_repository(
                root,
                python_version=(3, 11, 9),
                platform_name="nt",
            )

        statuses = {
            finding.check_id: finding.status for finding in report.findings
        }
        self.assertIs(statuses["environment:python"], DoctorStatus.PASS)
        self.assertIs(statuses["repository:git-context"], DoctorStatus.PASS)
        self.assertIs(statuses["adoption:state"], DoctorStatus.PASS)
        self.assertFalse(report.has_failures)

    def test_governance_conflict_is_a_deterministic_failure(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "AGENTS.md").mkdir()

            report = diagnose_repository(root, python_version=(3, 12, 0))

        conflict = next(
            finding
            for finding in report.findings
            if finding.check_id == "adoption:conflicts"
        )
        self.assertIs(conflict.status, DoctorStatus.FAIL)
        self.assertEqual(conflict.classification, "deterministic")
        self.assertTrue(report.has_failures)

    def test_stale_project_venv_is_advisory_and_not_repaired(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            environment = root / ".venv"
            environment.mkdir()

            report = diagnose_repository(root, python_version=(3, 12, 0))
            environment_still_exists = environment.is_dir()

        finding = next(
            item
            for item in report.findings
            if item.check_id == "environment:project-venv"
        )
        self.assertIs(finding.status, DoctorStatus.ADVISORY)
        self.assertIn("not used or repaired", finding.message)
        self.assertTrue(environment_still_exists)
        self.assertFalse(report.has_failures)

    def test_unsupported_python_is_a_failure_without_project_repair(self) -> None:
        with TemporaryDirectory() as temp_dir:
            report = diagnose_repository(
                Path(temp_dir),
                python_version=(3, 10, 14),
            )

        finding = next(
            item
            for item in report.findings
            if item.check_id == "environment:python"
        )
        self.assertIs(finding.status, DoctorStatus.FAIL)
        self.assertIn("will not be modified", finding.message)

    def test_windows_deep_path_risk_is_a_warning(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            while len(str(root.resolve())) < WINDOWS_PATH_ADVISORY_THRESHOLD:
                root = root / "deep-segment"
            root.mkdir(parents=True)

            report = diagnose_repository(
                root,
                python_version=(3, 12, 0),
                platform_name="nt",
            )

        finding = next(
            item
            for item in report.findings
            if item.check_id == "environment:windows-path"
        )
        self.assertIs(finding.status, DoctorStatus.WARN)
        self.assertEqual(finding.classification, "advisory")
        self.assertIn("avoid cloning AgentGov inside", finding.message)

    def test_json_contract_is_pure_read_only_and_non_interactive(self) -> None:
        with TemporaryDirectory() as temp_dir:
            report = diagnose_repository(
                Path(temp_dir),
                python_version=(3, 12, 10),
            )
            payload = json.loads(
                render_doctor_report_json(report, non_interactive=True)
            )

        self.assertEqual(payload["contract_version"], "1.0")
        self.assertEqual(payload["mode"], "read_only")
        self.assertEqual(payload["interaction"], "non_interactive")
        self.assertEqual(
            payload["authority_boundary"],
            {
                "modifies_repository": False,
                "repairs_project_environment": False,
                "installs_project_dependencies": False,
                "authorizes_git_or_release_operations": False,
            },
        )


class DoctorCliTests(unittest.TestCase):
    def test_cli_prints_target_runtime_findings_and_no_write_note(self) -> None:
        with TemporaryDirectory() as temp_dir:
            exit_code, stdout, stderr = run_cli("doctor", temp_dir)

        self.assertEqual(exit_code, EXIT_PASS)
        self.assertIn("TARGET doctor:", stdout)
        self.assertIn("RUNTIME doctor: Python", stdout)
        self.assertIn("WARN adoption:state:", stdout)
        self.assertIn("no repository files or project environments were modified", stdout)
        self.assertEqual(stderr, "")

    def test_cli_json_non_interactive_is_pure_json(self) -> None:
        with TemporaryDirectory() as temp_dir:
            exit_code, stdout, stderr = run_cli(
                "doctor",
                temp_dir,
                "--format",
                "json",
                "--non-interactive",
            )
            payload = json.loads(stdout)

        self.assertEqual(exit_code, EXIT_PASS)
        self.assertEqual(payload["interaction"], "non_interactive")
        self.assertEqual(stderr, "")

    def test_cli_conflict_returns_policy_failure(self) -> None:
        with TemporaryDirectory() as temp_dir:
            (Path(temp_dir) / "AGENTS.md").mkdir()
            exit_code, stdout, stderr = run_cli("doctor", temp_dir)

        self.assertEqual(exit_code, EXIT_FAIL)
        self.assertIn("FAIL adoption:conflicts:", stdout)
        self.assertEqual(stderr, "")

    def test_cli_missing_path_is_operational_error(self) -> None:
        with TemporaryDirectory() as temp_dir:
            missing = Path(temp_dir) / "missing"
            exit_code, stdout, stderr = run_cli("doctor", str(missing))

        self.assertEqual(exit_code, EXIT_ERROR)
        self.assertEqual(stdout, "")
        self.assertIn("ERROR doctor: repository path not found:", stderr)

    def test_distributed_schema_declares_strict_read_only_contract(self) -> None:
        schema = json.loads(
            (ROOT / "schemas/doctor-report.schema.json").read_text(encoding="utf-8")
        )

        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(schema["properties"]["mode"]["const"], "read_only")
        authority = schema["properties"]["authority_boundary"]
        self.assertFalse(authority["additionalProperties"])
        for property_schema in authority["properties"].values():
            self.assertIs(property_schema["const"], False)


if __name__ == "__main__":
    unittest.main()
