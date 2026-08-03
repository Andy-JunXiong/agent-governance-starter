import contextlib
import io
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from agentgov import __version__
from agentgov.cli import EXIT_ERROR, EXIT_FAIL, EXIT_PASS, main
from agentgov.initializer import initialize_project
from agentgov.update_check import (
    check_for_updates,
    comparable_version_key,
    load_repository_layout,
    request_update_confirmation,
)


ROOT = Path(__file__).resolve().parents[1]
CURRENT = ROOT / "release/current.json"
RC = ROOT / "release/fixtures/valid-rc.json"


class TerminalInput(io.StringIO):
    def isatty(self) -> bool:
        return True


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

    def test_checkout_copy_of_installed_metadata_is_recognized_by_content(self) -> None:
        with TemporaryDirectory() as temp_dir:
            installed = Path(temp_dir) / "current.json"
            installed.write_bytes(CURRENT.read_bytes())

            with patch(
                "agentgov.update_check.default_release_manifest",
                return_value=installed,
            ):
                report = check_for_updates(ROOT, manifest_path=CURRENT)

        self.assertEqual(report.available_version, __version__)
        self.assertIsNone(report.artifact)

    def test_published_0_2_1_is_not_an_update_for_future_0_3_source(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            manifest = json.loads(CURRENT.read_text(encoding="utf-8"))
            manifest.update({"tool_version": "0.2.1", "channel": "stable"})
            manifest["artifact"] = {
                "filename": "agent_governance_starter-0.2.1-py3-none-any.whl",
                "url": (
                    "https://github.com/Andy-JunXiong/agent-governance-starter/"
                    "releases/download/v0.2.1/"
                    "agent_governance_starter-0.2.1-py3-none-any.whl"
                ),
                "sha256": "a" * 64,
                "install_method": "pipx",
            }
            manifest_path = root / "stable.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            report = check_for_updates(ROOT, manifest_path=manifest_path)

        self.assertEqual(report.available_version, "0.2.1")
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

    def test_update_confirmation_requires_exact_interactive_input(self) -> None:
        self.assertFalse(
            request_update_confirmation(
                repository=ROOT,
                change_count=1,
                decision_reader=lambda _: "UPDATE",
                is_interactive_terminal=False,
            )
        )
        self.assertFalse(
            request_update_confirmation(
                repository=ROOT,
                change_count=1,
                decision_reader=lambda _: "update",
                is_interactive_terminal=True,
            )
        )
        self.assertTrue(
            request_update_confirmation(
                repository=ROOT,
                change_count=1,
                decision_reader=lambda _: "UPDATE",
                is_interactive_terminal=True,
            )
        )


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

    def test_one_command_update_applies_refresh_after_exact_confirmation(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            initialize_project(root, project_name="Update Fixture")
            (root / "governance/contract.json").unlink()
            terminal = TerminalInput("UPDATE\n")
            with patch("sys.stdin", terminal):
                exit_code, stdout, stderr = run_cli(
                    "update", str(root), "--manifest", str(CURRENT)
                )

            contract = json.loads(
                (root / "governance/contract.json").read_text(encoding="utf-8")
            )

        self.assertEqual(exit_code, EXIT_PASS)
        self.assertEqual(contract["layout_version"], "1.0")
        self.assertIn("SUMMARY CREATE=1 PRESERVE=0 CONFLICT=0", stdout)
        self.assertIn("[1/4] CHECK", stdout)
        self.assertIn("[2/4] PLAN", stdout)
        self.assertIn("[3/4] APPLY", stdout)
        self.assertIn("[4/4] VALIDATE", stdout)
        self.assertIn("APPLIED update: 1 repository change(s)", stdout)
        self.assertIn("SUCCESS UPDATE_COMPLETE", stdout)
        self.assertIn("REPOSITORY contract=1.0 target=1.0", stdout)
        self.assertIn("SUMMARY PASS=14 WARN=4 FAIL=0 ADVISORY=4", stdout)
        self.assertEqual(stderr, "")

    def test_redirected_update_confirmation_cancels_without_writing(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            with patch("sys.stdin", io.StringIO("UPDATE\n")):
                exit_code, stdout, stderr = run_cli(
                    "update", str(root), "--manifest", str(CURRENT)
                )

            self.assertFalse((root / "governance/contract.json").exists())

        self.assertEqual(exit_code, EXIT_PASS)
        self.assertIn("CANCELLED UPDATE_NOT_CONFIRMED", stdout)
        self.assertEqual(stderr, "")

    def test_non_interactive_apply_is_rejected_but_check_is_allowed(self) -> None:
        with TemporaryDirectory() as temp_dir:
            apply_result = run_cli(
                "update", temp_dir, "--manifest", str(CURRENT), "--non-interactive"
            )
            check_result = run_cli(
                "update", "--check", temp_dir, "--manifest", str(CURRENT),
                "--non-interactive", "--format", "json",
            )

        self.assertEqual(apply_result[0], EXIT_ERROR)
        self.assertIn("never authorizes writes", apply_result[2])
        self.assertEqual(check_result[0], EXIT_PASS)
        json.loads(check_result[1])

    def test_newer_tool_without_stable_install_source_blocks_before_write(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            terminal = TerminalInput("UPDATE\n")
            with patch("sys.stdin", terminal):
                exit_code, stdout, stderr = run_cli(
                    "update", str(root), "--manifest", str(RC)
                )

            self.assertFalse((root / "governance/contract.json").exists())

        self.assertEqual(exit_code, EXIT_FAIL)
        self.assertIn("stable artifact metadata is missing", stdout)
        self.assertEqual(stderr, "")

    def test_keyboard_interrupt_during_confirmation_reports_zero_write_recovery(
        self,
    ) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            terminal = TerminalInput()
            with patch("sys.stdin", terminal), patch(
                "builtins.input",
                side_effect=KeyboardInterrupt,
            ):
                exit_code, stdout, stderr = run_cli(
                    "update", str(root), "--manifest", str(CURRENT)
                )

            self.assertFalse((root / "governance/contract.json").exists())

        self.assertEqual(exit_code, EXIT_ERROR)
        self.assertIn("INTERRUPTED UPDATE_INTERRUPTED", stdout)
        self.assertIn("stopped before writes", stdout)
        self.assertIn("RECOVERY agentgov update .", stdout)
        self.assertEqual(stderr, "")

    def test_interrupted_apply_reports_created_file_as_partial(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            terminal = TerminalInput("UPDATE\n")

            def interrupted_apply(plan):
                target = plan.update.repository / "governance/contract.json"
                target.parent.mkdir()
                target.write_text("{}\n", encoding="utf-8")
                raise KeyboardInterrupt

            with patch("sys.stdin", terminal), patch(
                "agentgov.cli.apply_refresh_plan",
                side_effect=interrupted_apply,
            ):
                exit_code, stdout, stderr = run_cli(
                    "update", str(root), "--manifest", str(CURRENT)
                )

        self.assertEqual(exit_code, EXIT_ERROR)
        self.assertIn("PARTIAL UPDATE_INTERRUPTED", stdout)
        self.assertIn("CREATED governance/contract.json", stdout)
        self.assertIn("RECOVERY agentgov check repository", stdout)
        self.assertEqual(stderr, "")

    def test_failed_post_validation_reports_partial_and_recovery(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            terminal = TerminalInput("UPDATE\n")
            with patch("sys.stdin", terminal):
                exit_code, stdout, stderr = run_cli(
                    "update", str(root), "--manifest", str(CURRENT)
                )

            self.assertTrue((root / "governance/contract.json").is_file())

        self.assertEqual(exit_code, EXIT_FAIL)
        self.assertIn("PARTIAL UPDATE_VALIDATION", stdout)
        self.assertIn("CREATED governance/contract.json", stdout)
        self.assertIn("RECOVERY agentgov check repository", stdout)
        self.assertEqual(stderr, "")

    def test_verified_tool_update_installs_then_relaunches_new_process(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            manifest = json.loads(CURRENT.read_text(encoding="utf-8"))
            manifest.update({"tool_version": "0.3.0", "channel": "stable"})
            manifest["artifact"] = {
                "filename": "agent_governance_starter-0.3.0-py3-none-any.whl",
                "url": (
                    "https://github.com/Andy-JunXiong/agent-governance-starter/"
                    "releases/download/v0.3.0/"
                    "agent_governance_starter-0.3.0-py3-none-any.whl"
                ),
                "sha256": "a" * 64,
                "install_method": "pipx",
            }
            manifest_path = root / "stable.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            terminal = TerminalInput("UPDATE\n")
            executable = Path("agentgov-new.exe")
            with patch("sys.stdin", terminal), patch(
                "agentgov.cli.download_verified_wheel"
            ) as download, patch(
                "agentgov.cli.install_wheel_with_pipx",
                return_value=executable,
            ) as install, patch(
                "agentgov.cli.relaunch_updated_agentgov",
                return_value=EXIT_PASS,
            ) as relaunch:
                exit_code, stdout, stderr = run_cli(
                    "update", str(root), "--manifest", str(manifest_path)
                )

        self.assertEqual(exit_code, EXIT_PASS)
        download.assert_called_once()
        install.assert_called_once()
        relaunch.assert_called_once()
        self.assertIn("[3/6] DOWNLOAD", stdout)
        self.assertIn("[4/6] VERIFY", stdout)
        self.assertIn("[5/6] INSTALL", stdout)
        self.assertIn("[6/6] RELAUNCH", stdout)
        self.assertEqual(stderr, "")


if __name__ == "__main__":
    unittest.main()
