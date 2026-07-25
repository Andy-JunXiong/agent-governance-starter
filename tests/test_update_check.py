import contextlib
import io
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from agentgov.cli import EXIT_ERROR, EXIT_FAIL, EXIT_PASS, main
from agentgov.update_check import (
    check_for_updates,
    comparable_version_key,
    load_repository_layout,
)


ROOT = Path(__file__).resolve().parents[1]
CURRENT = ROOT / "release/current.json"
RC = ROOT / "release/fixtures/valid-rc.json"


def run_cli(*args: str) -> tuple[int, str, str]:
    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        exit_code = main(list(args))
    return exit_code, stdout.getvalue(), stderr.getvalue()


class UpdateCheckTests(unittest.TestCase):
    def test_supported_versions_follow_pep_440_stage_order(self) -> None:
        ordered = [
            "0.1.0.dev0",
            "0.1.0.dev1",
            "0.1.0a1",
            "0.1.0b1",
            "0.1.0rc1",
            "0.1.0",
            "0.1.1.dev0",
        ]

        self.assertEqual(
            sorted(ordered, key=comparable_version_key),
            ordered,
        )

    def test_versioned_repository_is_current_and_readable(self) -> None:
        report = check_for_updates(ROOT, manifest_path=CURRENT)

        self.assertEqual(report.repository_layout, "1.0")
        self.assertTrue(report.readable)
        self.assertFalse(report.repository_refresh_required)
        self.assertFalse(report.tool_update_available)

    def test_unversioned_repository_requires_refresh_without_writing(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            before = tuple(root.iterdir())

            report = check_for_updates(root, manifest_path=CURRENT)

            self.assertEqual(before, tuple(root.iterdir()))
            self.assertIsNone(report.repository_layout)
            self.assertTrue(report.readable)
            self.assertTrue(report.repository_refresh_required)

    def test_unknown_layout_is_not_readable(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "governance").mkdir()
            (root / "governance/contract.json").write_text(
                json.dumps({
                    "contract": "agentgov.repository-contract",
                    "schema_version": "1.0",
                    "layout_version": "9.0",
                }),
                encoding="utf-8",
            )

            report = check_for_updates(root, manifest_path=CURRENT)

        self.assertFalse(report.readable)
        self.assertTrue(report.repository_refresh_required)

    def test_contract_is_strict(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "governance").mkdir()
            (root / "governance/contract.json").write_text(
                '{"contract":"agentgov.repository-contract","schema_version":"1.0",'
                '"layout_version":"1.0","extra":true}',
                encoding="utf-8",
            )
            with self.assertRaises(ValueError):
                load_repository_layout(root)


class UpdateCheckCliTests(unittest.TestCase):
    def test_text_check_is_read_only_and_reports_unversioned_repository(self) -> None:
        with TemporaryDirectory() as temp_dir:
            exit_code, stdout, stderr = run_cli(
                "update", "--check", temp_dir, "--manifest", str(CURRENT)
            )

        self.assertEqual(exit_code, EXIT_PASS)
        self.assertIn("REPOSITORY contract=unversioned target=1.0", stdout)
        self.assertIn("refresh=yes", stdout)
        self.assertIn("no tool was installed or updated", stdout)
        self.assertIn("no repository files or Git state were modified", stdout)
        self.assertEqual(stderr, "")

    def test_json_check_has_explicit_authority_boundary(self) -> None:
        exit_code, stdout, stderr = run_cli(
            "update", "--check", str(ROOT), "--manifest", str(CURRENT),
            "--format", "json",
        )
        payload = json.loads(stdout)

        self.assertEqual(exit_code, EXIT_PASS)
        self.assertEqual(payload["mode"], "read_only")
        self.assertEqual(
            payload["authority_boundary"],
            {"tool_updated": False, "repository_modified": False},
        )
        self.assertEqual(stderr, "")

    def test_unreadable_layout_returns_policy_failure(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "governance").mkdir()
            (root / "governance/contract.json").write_text(
                '{"contract":"agentgov.repository-contract","schema_version":"1.0",'
                '"layout_version":"9.0"}',
                encoding="utf-8",
            )
            exit_code, stdout, stderr = run_cli(
                "update", "--check", str(root), "--manifest", str(CURRENT)
            )

        self.assertEqual(exit_code, EXIT_FAIL)
        self.assertIn("readable=no", stdout)
        self.assertEqual(stderr, "")

    def test_invalid_repository_contract_is_operational_error(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "governance").mkdir()
            (root / "governance/contract.json").write_text("[]", encoding="utf-8")
            exit_code, stdout, stderr = run_cli(
                "update", "--check", str(root), "--manifest", str(RC)
            )

        self.assertEqual(exit_code, EXIT_ERROR)
        self.assertEqual(stdout, "")
        self.assertIn("root must be an object", stderr)


if __name__ == "__main__":
    unittest.main()
