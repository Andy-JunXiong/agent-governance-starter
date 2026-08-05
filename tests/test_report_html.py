import contextlib
import io
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from agentgov.cli import EXIT_FAIL, EXIT_PASS, main
from agentgov.html_reporting import render_repository_report_html
from agentgov.initializer import initialize_project
from agentgov.repository import Finding, FindingStatus, RepositoryReport, check_repository


def run_cli(*args: str) -> tuple[int, str, str]:
    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        exit_code = main(list(args))
    return exit_code, stdout.getvalue(), stderr.getvalue()


class HtmlReportTests(unittest.TestCase):
    def test_shipped_demo_is_sanitized_and_matches_real_report_semantics(self) -> None:
        demo = (
            Path(__file__).resolve().parents[1] / "docs/demo-governance-report.html"
        ).read_text(encoding="utf-8")

        self.assertIn("<code>governed-demo</code>", demo)
        self.assertIn('<span>PASS</span><strong>12</strong>', demo)
        self.assertIn('<span>WARN</span><strong>3</strong>', demo)
        self.assertIn('<span>FAIL</span><strong>0</strong>', demo)
        self.assertIn('<span>ADVISORY</span><strong>1</strong>', demo)
        self.assertIn('href="index.html">← Back to main page</a>', demo)
        self.assertIn('"version": "0.3.0rc1"', demo)
        self.assertIn("header{position:sticky;top:0;z-index:100", demo)
        self.assertNotIn("C:\\Users", demo)
        self.assertNotIn("maki8", demo)

        chinese_demo = (
            Path(__file__).resolve().parents[1]
            / "docs/demo-governance-report.zh-CN.html"
        ).read_text(encoding="utf-8")
        self.assertIn('href="index.html">← 返回主页</a>', chinese_demo)
        self.assertIn('"version": "0.3.0rc1"', chinese_demo)
        self.assertIn("header{position:sticky;top:0;z-index:100", chinese_demo)

    def test_html_is_self_contained_explanatory_and_deterministic(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "project"
            initialize_project(root, project_name="HTML Report")
            report = check_repository(root)

            first = render_repository_report_html(report)
            second = render_repository_report_html(report)

        self.assertEqual(first, second)
        self.assertTrue(first.startswith("<!doctype html>"))
        for phrase in (
            "Repository governance, made visible",
            "Know what still needs a human.",
            "What needs attention",
            "How it works",
            "How this report was made",
            "How to read this report",
            "What it does not prove",
            "docs/adr/",
            "INVARIANTS.md",
            "agent-skills/",
            "Next:",
            "Work in:",
            "agentgov report repository . --format html",
            "The declared deterministic contract was satisfied. This is not approval.",
            "Static checks cannot decide; an accountable human must review.",
            "All findings",
            "Scope limitations",
            "This report does not authorize merge, publish, release, or deploy.",
            "No external network requests",
        ):
            self.assertIn(phrase, first)
        self.assertIn('data-filter="WARN"', first)
        self.assertIn('id="filter-note" aria-live="polite"', first)
        self.assertIn('data-status="ADVISORY"', first)
        self.assertIn("governance:placeholders", first)
        self.assertIn("Replace each repository placeholder", first)
        self.assertIn("AGENTS.md, ADR/invariant files", first)
        self.assertNotIn("<link ", first)
        self.assertNotIn("<script src=", first)
        self.assertNotIn("https://", first)
        self.assertNotIn("Governance Coverage", first)
        self.assertNotIn("governance coverage percentage:", first.lower())
        self.assertNotIn("An AI drafts customer refund replies.", first)

    def test_html_escapes_repository_findings_and_embedded_json(self) -> None:
        report = RepositoryReport(
            root=Path("repo<script>alert(1)"),
            findings=(
                Finding(
                    FindingStatus.FAIL,
                    'check"><script>alert(2)</script>',
                    "unsafe <img src=x onerror=alert(3)>",
                ),
            ),
        )

        content = render_repository_report_html(report)

        self.assertNotIn("<script>alert", content)
        self.assertNotIn("<img src=x", content)
        self.assertIn("&lt;script&gt;alert(1)", content)
        self.assertIn("&lt;img src=x onerror=alert(3)&gt;", content)

    def test_html_uses_portable_repository_name_instead_of_absolute_path(self) -> None:
        report = RepositoryReport(
            root=Path("C:/Users/example/private-parent/governed-project"),
            findings=(),
        )

        content = render_repository_report_html(report)

        self.assertIn("<code>governed-project</code>", content)
        self.assertIn('"repository": "governed-project"', content)
        self.assertNotIn("private-parent", content)

    def test_cli_writes_html_and_preserves_repository_exit_semantics(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "project"
            output = Path(temp_dir) / "governance-report.html"
            initialize_project(root, project_name="HTML CLI")

            exit_code, stdout, stderr = run_cli(
                "report", "repository", str(root), "--format", "html", "--output", str(output)
            )
            content = output.read_text(encoding="utf-8")

        self.assertEqual(exit_code, EXIT_PASS)
        self.assertIn(f"REPORT {output}", stdout)
        self.assertIn("NEXT report: open the report", stdout)
        self.assertEqual(stderr, "")
        self.assertTrue(content.startswith("<!doctype html>"))

    def test_failing_repository_still_gets_html_and_failure_exit(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            output = root / "failed-report.html"

            exit_code, stdout, stderr = run_cli(
                "report", "repository", str(root), "--format", "html", "--output", str(output)
            )

            content = output.read_text(encoding="utf-8")

        self.assertEqual(exit_code, EXIT_FAIL)
        self.assertIn('data-status="FAIL"', content)
        self.assertIn("Resolve this deterministic failure", content)
        self.assertEqual(stderr, "")


if __name__ == "__main__":
    unittest.main()
