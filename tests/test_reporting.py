import contextlib
import io
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from agentgov.artifacts import export_capability_artifact
from agentgov.cli import EXIT_ERROR, EXIT_FAIL, EXIT_PASS, main
from agentgov.initializer import initialize_project
from agentgov.reporting import render_repository_report
from agentgov.repository import Finding, FindingStatus, RepositoryReport, check_repository


def run_cli(*args: str) -> tuple[int, str, str]:
    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        exit_code = main(list(args))
    return exit_code, stdout.getvalue(), stderr.getvalue()


class MarkdownReportTests(unittest.TestCase):
    def test_report_contains_required_sections_and_no_percentage(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "project"
            initialize_project(root, project_name="Report Project")
            report = check_repository(root)

            markdown = render_repository_report(report)

        for heading in (
            "# Agent Governance Report",
            "## Summary",
            "## How to interpret this report",
            "## Human decisions still required",
            "## Findings",
            "## Known gaps",
            "## Recommended actions",
            "## Scope limitations",
        ):
            self.assertIn(heading, markdown)
        self.assertIn("| PASS | 11 |", markdown)
        self.assertIn("| WARN | 4 |", markdown)
        self.assertIn("| ADVISORY | 1 |", markdown)
        self.assertIn("`artifacts:directory`", markdown)
        self.assertIn("the checks ran; it does not mean governance is complete", markdown)
        self.assertIn(
            "This report does not authorize merge, publish, release, or deploy",
            markdown,
        )
        self.assertIn(
            "Complete or explicitly defer each WARN finding:",
            markdown,
        )
        self.assertIn(
            "Treat merge, publish, release, and deploy as separate human-controlled",
            markdown,
        )
        self.assertIn(
            "Reference checks establish existence and structural readability, "
            "not semantic compatibility or runtime reachability.",
            markdown,
        )
        self.assertNotIn(
            "Referenced schema and call-site paths are not yet checked for existence.",
            markdown,
        )
        self.assertNotIn("Governance Coverage:", markdown)
        self.assertNotRegex(markdown, r"\b\d+%")

    def test_report_rendering_is_deterministic_and_escapes_table_pipes(self) -> None:
        report = RepositoryReport(
            root=Path("example"),
            findings=(
                Finding(FindingStatus.WARN, "example|check", "left | right"),
            ),
        )

        first = render_repository_report(report)
        second = render_repository_report(report)

        self.assertEqual(first, second)
        self.assertIn("`example\\|check`", first)
        self.assertIn("left \\| right", first)

    def test_report_surfaces_configured_artifact_drift_as_failure(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "project"
            initialize_project(root, project_name="Artifact Drift Report")
            source = root / "governance/evidence/example-capability.md"
            manifest = root / "governance/capabilities/example-capability.json"
            export_capability_artifact(manifest, repository=root)
            source.write_text("PROMPT = 'after'\n", encoding="utf-8")

            markdown = render_repository_report(check_repository(root))

        self.assertIn("| FAIL | `artifact:example-capability` |", markdown)
        self.assertIn("source drift detected", markdown)
        self.assertIn("Resolve each FAIL finding before claiming a pass:", markdown)


class ReportCliTests(unittest.TestCase):
    def test_stdout_report_returns_pass_when_only_warn_and_advisory_exist(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "project"
            initialize_project(root, project_name="Stdout Report")

            exit_code, stdout, stderr = run_cli("report", "repository", str(root))

        self.assertEqual(exit_code, EXIT_PASS)
        self.assertTrue(stdout.startswith("# Agent Governance Report\n"))
        self.assertIn("**WARN** `governance:placeholders`", stdout)
        self.assertIn("**WARN** `artifacts:directory`", stdout)
        self.assertEqual(stderr, "")

    def test_output_file_is_created_without_mixing_report_into_stdout(self) -> None:
        with TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            root = temp_root / "project"
            output = temp_root / "governance-report.md"
            initialize_project(root, project_name="File Report")

            exit_code, stdout, stderr = run_cli(
                "report", "repository", str(root), "--output", str(output)
            )

            content = output.read_text(encoding="utf-8")

        self.assertEqual(exit_code, EXIT_PASS)
        self.assertTrue(stdout.startswith(f"REPORT {output}\n"))
        self.assertIn("NEXT report: open the report", stdout)
        self.assertIn("Human decisions still required", stdout)
        self.assertIn(
            "does not authorize merge, publish, release, or deploy",
            stdout,
        )
        self.assertTrue(content.startswith("# Agent Governance Report\n"))
        self.assertEqual(stderr, "")

    def test_existing_output_is_not_overwritten(self) -> None:
        with TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            root = temp_root / "project"
            output = temp_root / "existing.md"
            initialize_project(root, project_name="No Overwrite")
            output.write_text("human report\n", encoding="utf-8")

            exit_code, stdout, stderr = run_cli(
                "report", "repository", str(root), "--output", str(output)
            )

            preserved = output.read_text(encoding="utf-8")

        self.assertEqual(exit_code, EXIT_FAIL)
        self.assertIn("FAIL report: output already exists", stdout)
        self.assertEqual(preserved, "human report\n")
        self.assertEqual(stderr, "")

    def test_failing_repository_still_emits_report_and_returns_fail(self) -> None:
        with TemporaryDirectory() as temp_dir:
            exit_code, stdout, stderr = run_cli(
                "report", "repository", str(Path(temp_dir))
            )

        self.assertEqual(exit_code, EXIT_FAIL)
        self.assertIn("| FAIL | 3 |", stdout)
        self.assertIn("## Recommended actions", stdout)
        self.assertEqual(stderr, "")

    def test_failing_repository_writes_output_before_returning_fail(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            output = root / "failed-governance-report.md"

            exit_code, stdout, stderr = run_cli(
                "report", "repository", str(root), "--output", str(output)
            )

            content = output.read_text(encoding="utf-8")

        self.assertEqual(exit_code, EXIT_FAIL)
        self.assertTrue(stdout.startswith(f"REPORT {output}\n"))
        self.assertIn("NEXT report: open the report", stdout)
        self.assertIn(
            "does not authorize merge, publish, release, or deploy",
            stdout,
        )
        self.assertIn("| FAIL | 3 |", content)
        self.assertEqual(stderr, "")

    def test_missing_repository_is_an_operational_error(self) -> None:
        with TemporaryDirectory() as temp_dir:
            missing = Path(temp_dir) / "missing"

            exit_code, stdout, stderr = run_cli(
                "report", "repository", str(missing)
            )

        self.assertEqual(exit_code, EXIT_ERROR)
        self.assertEqual(stdout, "")
        self.assertIn("ERROR report: repository path not found:", stderr)


if __name__ == "__main__":
    unittest.main()
