import contextlib
import io
import json
import os
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from agentgov.cli import EXIT_ERROR, EXIT_FAIL, EXIT_PASS, main


ROOT = Path(__file__).resolve().parents[1]
VALID_MANIFEST = (
    ROOT
    / "prompt-governance"
    / "fixtures"
    / "valid"
    / "runtime-low-risk.json"
)
INVALID_MANIFEST = (
    ROOT
    / "prompt-governance"
    / "fixtures"
    / "invalid"
    / "high-risk-without-review.json"
)


def run_cli(*args: str) -> tuple[int, str, str]:
    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        exit_code = main(list(args))
    return exit_code, stdout.getvalue(), stderr.getvalue()


class CapabilityCliTests(unittest.TestCase):
    def test_no_arguments_orients_first_time_user_without_error(self) -> None:
        exit_code, stdout, stderr = run_cli()

        self.assertEqual(exit_code, EXIT_PASS)
        self.assertIn("Check repository-native AI governance contracts.", stdout)
        self.assertIn("Start here:", stdout)
        self.assertIn("agentgov doctor .", stdout)
        self.assertIn("agentgov next .", stdout)
        self.assertIn("agentgov status .", stdout)
        self.assertEqual(stderr, "")

    def test_help_includes_first_time_user_entry_points(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            with self.assertRaises(SystemExit) as raised:
                main(["--help"])

        self.assertEqual(raised.exception.code, EXIT_PASS)
        self.assertIn("Start here:", stdout.getvalue())
        self.assertEqual(stderr.getvalue(), "")

    def test_check_help_includes_replay_preflight(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            with self.assertRaises(SystemExit) as raised:
                main(["check", "--help"])

        self.assertEqual(raised.exception.code, EXIT_PASS)
        self.assertIn("replay-preflight", stdout.getvalue())
        self.assertEqual(stderr.getvalue(), "")

    def test_reserve_help_includes_replay_correlation(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            with self.assertRaises(SystemExit) as raised:
                main(["reserve", "--help"])

        self.assertEqual(raised.exception.code, EXIT_PASS)
        self.assertIn("replay-correlation", stdout.getvalue())
        self.assertEqual(stderr.getvalue(), "")

    def test_valid_manifest_returns_pass(self) -> None:
        exit_code, stdout, stderr = run_cli("check", "capability", str(VALID_MANIFEST))

        self.assertEqual(exit_code, EXIT_PASS)
        self.assertIn("PASS capability:", stdout)
        self.assertEqual(stderr, "")

    def test_contract_violation_returns_fail_with_field_errors(self) -> None:
        exit_code, stdout, stderr = run_cli("check", "capability", str(INVALID_MANIFEST))

        self.assertEqual(exit_code, EXIT_FAIL)
        self.assertIn("FAIL capability:", stdout)
        self.assertIn("$.human_review.required must be true", stdout)
        self.assertEqual(stderr, "")

    def test_missing_file_returns_operational_error(self) -> None:
        missing = ROOT / "prompt-governance" / "fixtures" / "missing.json"

        exit_code, stdout, stderr = run_cli("check", "capability", str(missing))

        self.assertEqual(exit_code, EXIT_ERROR)
        self.assertEqual(stdout, "")
        self.assertIn("ERROR capability: file not found:", stderr)

    def test_malformed_json_returns_operational_error_without_file_contents(self) -> None:
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "malformed.json"
            path.write_text('{"secret_example": "do-not-echo",', encoding="utf-8")

            exit_code, stdout, stderr = run_cli("check", "capability", str(path))

        self.assertEqual(exit_code, EXIT_ERROR)
        self.assertEqual(stdout, "")
        self.assertIn("ERROR capability: invalid JSON:", stderr)
        self.assertNotIn("do-not-echo", stderr)

    def test_non_object_json_returns_operational_error(self) -> None:
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "array.json"
            path.write_text(json.dumps(["not", "an", "object"]), encoding="utf-8")

            exit_code, stdout, stderr = run_cli("check", "capability", str(path))

        self.assertEqual(exit_code, EXIT_ERROR)
        self.assertEqual(stdout, "")
        self.assertIn("root must be an object", stderr)

    def test_module_entry_point_preserves_process_exit_code(self) -> None:
        environment = os.environ.copy()
        environment["PYTHONPATH"] = str(ROOT / "src")
        environment["PYTHONDONTWRITEBYTECODE"] = "1"

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "agentgov",
                "check",
                "capability",
                str(INVALID_MANIFEST),
            ],
            cwd=ROOT,
            env=environment,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, EXIT_FAIL)
        self.assertIn("FAIL capability:", result.stdout)
        self.assertEqual(result.stderr, "")

    def test_missing_manifest_argument_uses_standard_usage_exit_code(self) -> None:
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            with self.assertRaises(SystemExit) as raised:
                main(["check", "capability"])

        self.assertEqual(raised.exception.code, EXIT_ERROR)
        self.assertIn("usage: agentgov check capability", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
