import contextlib
import io
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from agentgov.cli import EXIT_PASS, main


def run_cli(*args: str) -> tuple[int, str, str]:
    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        exit_code = main(list(args))
    return exit_code, stdout.getvalue(), stderr.getvalue()


class CleanRepositoryAdoptionTests(unittest.TestCase):
    def test_initialized_repository_reaches_report_without_policy_failures(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "adopted-project"
            capability = (
                root / "governance/capabilities/example-capability.json"
            )
            evaluation = root / "evaluation/example-capability"
            artifact = (
                root / "governance/artifacts/example-capability"
            )
            report_path = root / "governance-report.md"

            steps = (
                (
                    ("init", str(root), "--project-name", "Adoption Rehearsal"),
                    "PASS init:",
                ),
                (("check", "capability", str(capability)), "PASS capability:"),
                (
                    (
                        "check",
                        "references",
                        str(capability),
                        "--repository",
                        str(root),
                    ),
                    "SUMMARY PASS=3 WARN=1 FAIL=0",
                ),
                (
                    ("check", "evaluation", str(evaluation)),
                    "WARN evaluation:needs_seed_cases:",
                ),
                (
                    ("check", "agent-skills", str(root / "agent-skills")),
                    "SUMMARY PASS=4 FAIL=0",
                ),
                (
                    (
                        "export",
                        "capability",
                        str(capability),
                        "--repository",
                        str(root),
                    ),
                    "PASS export capability: example-capability",
                ),
                (
                    (
                        "check",
                        "artifact",
                        str(artifact),
                        "--repository",
                        str(root),
                    ),
                    "PASS artifact:",
                ),
                (
                    ("check", "repository", str(root)),
                    "SUMMARY PASS=12 WARN=3 FAIL=0 ADVISORY=1",
                ),
                (
                    (
                        "report",
                        "repository",
                        str(root),
                        "--output",
                        str(report_path),
                    ),
                    "REPORT ",
                ),
            )

            for arguments, expected_output in steps:
                with self.subTest(command="agentgov " + " ".join(arguments)):
                    exit_code, stdout, stderr = run_cli(*arguments)
                    self.assertEqual(exit_code, EXIT_PASS)
                    self.assertIn(expected_output, stdout)
                    self.assertEqual(stderr, "")

            report = report_path.read_text(encoding="utf-8")

        self.assertIn("| PASS | 12 |", report)
        self.assertIn("| WARN | 3 |", report)
        self.assertIn("| FAIL | 0 |", report)
        self.assertIn("| ADVISORY | 1 |", report)
        self.assertIn("`governance:placeholders`", report)
        self.assertIn("`references:example-capability:evaluation`", report)
        self.assertIn("`evaluation:evaluation/example-capability`", report)
        self.assertIn("## How to interpret this report", report)
        self.assertIn("## Human decisions still required", report)
        self.assertIn("the checks ran; it does not mean governance is complete", report)
        self.assertIn("does not mean governance is complete", report)
        self.assertIn("does not authorize merge, publish, release, or deploy", report)
        self.assertNotRegex(report, r"\b\d+%")


if __name__ == "__main__":
    unittest.main()
