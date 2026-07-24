import contextlib
import io
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from agentgov.cli import EXIT_ERROR, EXIT_FAIL, EXIT_PASS, main
from agentgov import __version__
from agentgov.initializer import initialize_project
from agentgov.reporting import (
    REPORT_SCHEMA_VERSION,
    render_repository_report,
    render_repository_report_json,
)
from agentgov.repository import Finding, FindingStatus, RepositoryReport, check_repository


def run_cli(*args: str) -> tuple[int, str, str]:
    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        exit_code = main(list(args))
    return exit_code, stdout.getvalue(), stderr.getvalue()


class JsonReportContractTests(unittest.TestCase):
    def test_default_and_explicit_markdown_output_are_identical(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "project"
            initialize_project(root, project_name="Markdown Compatibility")

            default_result = run_cli("report", "repository", str(root))
            explicit_result = run_cli(
                "report",
                "repository",
                str(root),
                "--format",
                "markdown",
            )

        self.assertEqual(default_result, explicit_result)
        self.assertEqual(default_result[0], EXIT_PASS)
        self.assertTrue(default_result[1].startswith("# Agent Governance Report\n"))

    def test_json_contract_serializes_all_statuses_and_summary(self) -> None:
        report = RepositoryReport(
            root=Path("example"),
            findings=(
                Finding(FindingStatus.PASS, "check:pass", "pass message"),
                Finding(FindingStatus.WARN, "check:warn", "warn message"),
                Finding(FindingStatus.FAIL, "check:fail", "fail message"),
                Finding(
                    FindingStatus.ADVISORY,
                    "check:advisory",
                    "advisory message",
                ),
            ),
        )

        payload = json.loads(render_repository_report_json(report))

        self.assertEqual(
            set(payload),
            {
                "schema_version",
                "tool",
                "repository",
                "summary",
                "findings",
                "known_gaps",
                "recommended_actions",
                "scope_limitations",
            },
        )
        self.assertEqual(payload["schema_version"], REPORT_SCHEMA_VERSION)
        self.assertEqual(
            payload["tool"],
            {"name": "agentgov", "version": __version__},
        )
        self.assertEqual(payload["repository"], "example")
        self.assertEqual(
            payload["summary"],
            {"pass": 1, "warn": 1, "fail": 1, "advisory": 1},
        )
        self.assertEqual(
            [finding["status"] for finding in payload["findings"]],
            ["PASS", "WARN", "FAIL", "ADVISORY"],
        )
        self.assertEqual(
            [finding["status"] for finding in payload["known_gaps"]],
            ["WARN", "FAIL", "ADVISORY"],
        )
        self.assertEqual(
            [action["check_id"] for action in payload["recommended_actions"]],
            ["check:warn", "check:fail", "check:advisory"],
        )
        self.assertNotIn("timestamp", payload)
        self.assertNotIn("score", payload)
        self.assertNotIn("coverage_percentage", payload)
        self.assertIn(
            "Reference checks establish existence and structural readability, "
            "not semantic compatibility or runtime reachability.",
            payload["scope_limitations"],
        )
        self.assertNotIn(
            "Referenced schema and call-site paths are not yet checked for existence.",
            payload["scope_limitations"],
        )

    def test_json_rendering_is_deterministic(self) -> None:
        report = RepositoryReport(
            root=Path("deterministic"),
            findings=(
                Finding(FindingStatus.WARN, "check:one", "review this"),
                Finding(FindingStatus.ADVISORY, "check:two", "judge this"),
            ),
        )

        self.assertEqual(
            render_repository_report_json(report),
            render_repository_report_json(report),
        )

    def test_markdown_and_json_render_the_same_repository_findings(self) -> None:
        report = RepositoryReport(
            root=Path("same-findings"),
            findings=(
                Finding(FindingStatus.PASS, "check:pass", "contract passed"),
                Finding(FindingStatus.WARN, "check:warn", "configuration gap"),
                Finding(FindingStatus.FAIL, "check:fail", "contract failed"),
                Finding(
                    FindingStatus.ADVISORY,
                    "check:advisory",
                    "human judgment",
                ),
            ),
        )

        markdown = render_repository_report(report)
        payload = json.loads(render_repository_report_json(report))

        self.assertEqual(
            payload["findings"],
            [
                {
                    "check_id": finding.check_id,
                    "status": finding.status.value,
                    "message": finding.message,
                }
                for finding in report.findings
            ],
        )
        for finding in report.findings:
            self.assertIn(finding.check_id, markdown)
            self.assertIn(finding.message, markdown)

    def test_json_cli_checks_repository_once_and_emits_pure_json(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "project"
            initialize_project(root, project_name="JSON CLI")
            report = check_repository(root)

            with patch("agentgov.cli.check_repository", return_value=report) as checker:
                exit_code, stdout, stderr = run_cli(
                    "report",
                    "repository",
                    str(root),
                    "--format",
                    "json",
                )

        payload = json.loads(stdout)
        checker.assert_called_once_with(root)
        self.assertEqual(exit_code, EXIT_PASS)
        self.assertEqual(
            payload["findings"],
            [
                {
                    "check_id": finding.check_id,
                    "status": finding.status.value,
                    "message": finding.message,
                }
                for finding in report.findings
            ],
        )
        self.assertEqual(stderr, "")

    def test_fail_findings_create_json_file_and_retain_failing_exit_code(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            output = root / "failed-governance-report.json"

            exit_code, stdout, stderr = run_cli(
                "report",
                "repository",
                str(root),
                "--format",
                "json",
                "--output",
                str(output),
            )

            payload = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(exit_code, EXIT_FAIL)
        self.assertGreater(payload["summary"]["fail"], 0)
        self.assertTrue(any(item["status"] == "FAIL" for item in payload["findings"]))
        self.assertTrue(stdout.startswith(f"REPORT {output}\n"))
        self.assertEqual(stderr, "")

    def test_json_output_does_not_overwrite_existing_file(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "project"
            output = Path(temp_dir) / "existing.json"
            initialize_project(root, project_name="JSON No Overwrite")
            output.write_text('{"owned_by":"human"}\n', encoding="utf-8")

            exit_code, stdout, stderr = run_cli(
                "report",
                "repository",
                str(root),
                "--format",
                "json",
                "--output",
                str(output),
            )

            preserved = output.read_text(encoding="utf-8")

        self.assertEqual(exit_code, EXIT_FAIL)
        self.assertIn("FAIL report: output already exists", stdout)
        self.assertEqual(preserved, '{"owned_by":"human"}\n')
        self.assertEqual(stderr, "")

    def test_unsupported_format_uses_operational_error_exit_code(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()

        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            with self.assertRaises(SystemExit) as raised:
                main(["report", "repository", ".", "--format", "yaml"])

        self.assertEqual(raised.exception.code, EXIT_ERROR)
        self.assertEqual(stdout.getvalue(), "")
        self.assertIn("invalid choice", stderr.getvalue())

    def test_distributed_schema_declares_the_v1_contract(self) -> None:
        repository_root = Path(__file__).resolve().parents[1]
        schema_path = repository_root / "schemas/repository-report.schema.json"

        schema = json.loads(schema_path.read_text(encoding="utf-8"))

        self.assertEqual(
            schema["properties"]["schema_version"]["const"],
            REPORT_SCHEMA_VERSION,
        )
        self.assertEqual(
            set(schema["required"]),
            {
                "schema_version",
                "tool",
                "repository",
                "summary",
                "findings",
                "known_gaps",
                "recommended_actions",
                "scope_limitations",
            },
        )
        pyproject = (repository_root / "pyproject.toml").read_text(encoding="utf-8")
        self.assertIn('"schemas/*.schema.json"', pyproject)


if __name__ == "__main__":
    unittest.main()
