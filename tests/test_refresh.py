import contextlib
import io
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from agentgov.cli import EXIT_FAIL, EXIT_PASS, main
from agentgov.initializer import initialize_project
from agentgov.refresh import (
    RefreshAction,
    RefreshConflictError,
    apply_refresh_plan,
    plan_refresh,
    render_refresh_plan_json,
    request_refresh_confirmation,
)


ROOT = Path(__file__).resolve().parents[1]
CURRENT = ROOT / "release/current.json"


class TerminalInput(io.StringIO):
    def isatty(self) -> bool:
        return True


def run_cli(*args: str) -> tuple[int, str, str]:
    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        exit_code = main(list(args))
    return exit_code, stdout.getvalue(), stderr.getvalue()


class RefreshPlanTests(unittest.TestCase):
    def test_unversioned_repository_plans_only_contract_creation(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "governance").mkdir()
            before = tuple(root.rglob("*"))

            plan = plan_refresh(root, manifest_path=CURRENT)

            self.assertEqual(before, tuple(root.rglob("*")))
            self.assertEqual(plan.count(RefreshAction.CREATE), 1)
            self.assertFalse(plan.has_conflicts)
            item = plan.items[0]
            self.assertEqual(item.path, Path("governance/contract.json"))
            self.assertEqual(
                json.loads(item.content or "{}")["layout_version"],
                "1.0",
            )

    def test_current_contract_is_preserved(self) -> None:
        plan = plan_refresh(ROOT, manifest_path=CURRENT)

        self.assertEqual(plan.count(RefreshAction.PRESERVE), 1)
        self.assertIsNone(plan.items[0].content)

    def test_unsupported_existing_layout_is_conflict(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "governance").mkdir()
            (root / "governance/contract.json").write_text(
                '{"contract":"agentgov.repository-contract","schema_version":"1.0",'
                '"layout_version":"9.0"}',
                encoding="utf-8",
            )

            plan = plan_refresh(root, manifest_path=CURRENT)

        self.assertTrue(plan.has_conflicts)
        self.assertIn("not implemented", plan.items[0].reason)

    def test_json_plan_denies_write_and_apply_authority(self) -> None:
        plan = plan_refresh(ROOT, manifest_path=CURRENT)
        payload = json.loads(render_refresh_plan_json(plan))

        self.assertEqual(payload["mode"], "dry_run")
        self.assertEqual(
            payload["authority_boundary"],
            {
                "repository_modified": False,
                "git_state_modified": False,
                "apply_authorized": False,
            },
        )

    def test_confirmation_requires_exact_refresh_from_terminal(self) -> None:
        plan = plan_refresh(ROOT, manifest_path=CURRENT)

        self.assertFalse(
            request_refresh_confirmation(
                plan,
                decision_reader=lambda _: "REFRESH",
                is_interactive_terminal=False,
            )
        )
        self.assertFalse(
            request_refresh_confirmation(
                plan,
                decision_reader=lambda _: "refresh",
                is_interactive_terminal=True,
            )
        )
        self.assertTrue(
            request_refresh_confirmation(
                plan,
                decision_reader=lambda _: "REFRESH",
                is_interactive_terminal=True,
            )
        )

    def test_apply_revalidates_target_before_exclusive_create(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            plan = plan_refresh(root, manifest_path=CURRENT)
            (root / "governance").mkdir()
            target = root / "governance/contract.json"
            target.write_text("human content\n", encoding="utf-8")

            with self.assertRaises(RefreshConflictError):
                apply_refresh_plan(plan)

            self.assertEqual(target.read_text(encoding="utf-8"), "human content\n")


class RefreshCliTests(unittest.TestCase):
    def test_dry_run_prints_exact_create_content_without_writing(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            exit_code, stdout, stderr = run_cli(
                "refresh", str(root), "--dry-run", "--manifest", str(CURRENT)
            )

            self.assertFalse((root / "governance/contract.json").exists())

        self.assertEqual(exit_code, EXIT_PASS)
        self.assertIn("CREATE governance/contract.json", stdout)
        self.assertIn('"layout_version": "1.0"', stdout)
        self.assertIn("SUMMARY CREATE=1 PRESERVE=0 CONFLICT=0", stdout)
        self.assertIn("does not authorize a later write", stdout)
        self.assertEqual(stderr, "")

    def test_conflict_retains_policy_failure_exit(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "governance").mkdir()
            (root / "governance/contract.json").mkdir()

            exit_code, stdout, stderr = run_cli(
                "refresh", str(root), "--dry-run", "--manifest", str(CURRENT)
            )

        self.assertEqual(exit_code, EXIT_FAIL)
        self.assertIn("CONFLICT governance/contract.json", stdout)
        self.assertEqual(stderr, "")

    def test_json_output_is_pure(self) -> None:
        exit_code, stdout, stderr = run_cli(
            "refresh", str(ROOT), "--dry-run", "--manifest", str(CURRENT),
            "--format", "json",
        )
        payload = json.loads(stdout)

        self.assertEqual(exit_code, EXIT_PASS)
        self.assertEqual(payload["summary"]["PRESERVE"], 1)
        self.assertEqual(stderr, "")

    def test_redirected_confirmation_cancels_without_writing(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            redirected = io.StringIO("REFRESH\n")
            with patch("sys.stdin", redirected):
                exit_code, stdout, stderr = run_cli(
                    "refresh", str(root), "--manifest", str(CURRENT)
                )

            self.assertFalse((root / "governance/contract.json").exists())

        self.assertEqual(exit_code, EXIT_PASS)
        self.assertIn("CANCELLED refresh", stdout)
        self.assertEqual(stderr, "")

    def test_exact_interactive_confirmation_applies_and_rechecks(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            initialize_project(root, project_name="Refresh Fixture")
            (root / "governance/contract.json").unlink()
            terminal = TerminalInput("REFRESH\n")
            with patch("sys.stdin", terminal):
                exit_code, stdout, stderr = run_cli(
                    "refresh", str(root), "--manifest", str(CURRENT)
                )

            contract = json.loads(
                (root / "governance/contract.json").read_text(encoding="utf-8")
            )

        self.assertEqual(exit_code, EXIT_PASS)
        self.assertEqual(contract["layout_version"], "1.0")
        self.assertIn("PASS refresh: created 1 deterministic file(s)", stdout)
        self.assertIn("REPOSITORY contract=1.0 target=1.0", stdout)
        self.assertIn("SUMMARY PASS=14 WARN=4 FAIL=0 ADVISORY=4", stdout)
        self.assertIn("no Git, merge, publish", stdout)
        self.assertEqual(stderr, "")


if __name__ == "__main__":
    unittest.main()
