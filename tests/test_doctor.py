import contextlib
import io
import json
import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from types import SimpleNamespace

from agentgov import __version__
from agentgov.cli import EXIT_ERROR, EXIT_FAIL, EXIT_PASS, main
from agentgov.codex_hooks import CodexHookPolicyError
from agentgov.doctor import (
    DoctorStatus,
    MAX_MCP_CONFIG_BYTES,
    WINDOWS_PATH_ADVISORY_THRESHOLD,
    diagnose_repository,
    render_doctor_report_json,
)
from agentgov.codex_mcp import render_codex_mcp_config
from agentgov.initializer import initialize_project


ROOT = Path(__file__).resolve().parents[1]


def run_cli(*args: str) -> tuple[int, str, str]:
    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        exit_code = main(list(args))
    return exit_code, stdout.getvalue(), stderr.getvalue()


class DoctorTests(unittest.TestCase):
    @staticmethod
    def _mcp_findings(report):
        return {
            finding.check_id: finding
            for finding in report.findings
            if finding.check_id.startswith("mcp:")
        }

    @staticmethod
    def _write_config(root: Path, content: str) -> None:
        config = root / ".codex/config.toml"
        config.parent.mkdir(parents=True)
        config.write_text(content, encoding="utf-8")

    def _diagnose_mcp_config(self, content: str, *, binary: bool = False):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            config = root / ".codex/config.toml"
            config.parent.mkdir(parents=True)
            config.write_bytes(content if binary else content.encode("utf-8"))
            before = config.read_bytes()
            report = diagnose_repository(root, python_version=(3, 12, 0))
            after = config.read_bytes()
        return self._mcp_findings(report), before, after

    def test_mcp_generated_config_is_healthy_without_expanding_report_contract(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_config(root, render_codex_mcp_config())
            before = tuple(root.rglob("*"))
            report = diagnose_repository(root, python_version=(3, 12, 0))
            after = tuple(root.rglob("*"))

        findings = self._mcp_findings(report)
        self.assertEqual(
            set(findings),
            {
                "mcp:configuration", "mcp:enabled", "mcp:base-tools",
                "mcp:form-tools", "mcp:tool-timeout", "mcp:live-state",
            },
        )
        self.assertTrue(all(item.status is not DoctorStatus.FAIL for item in findings.values()))
        self.assertIs(findings["mcp:configuration"].status, DoctorStatus.PASS)
        self.assertIs(findings["mcp:enabled"].status, DoctorStatus.PASS)
        self.assertIs(findings["mcp:base-tools"].status, DoctorStatus.PASS)
        self.assertIs(findings["mcp:form-tools"].status, DoctorStatus.PASS)
        self.assertIs(findings["mcp:tool-timeout"].status, DoctorStatus.PASS)
        self.assertIs(findings["mcp:live-state"].status, DoctorStatus.ADVISORY)
        self.assertEqual(before, after)

    def test_mcp_old_six_tool_allowlist_reports_missing_optional_tools_separately(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_config(
                root,
                """
[mcp_servers.agentgov_governance]
enabled = true
enabled_tools = ["agentgov_alignment_start", "agentgov_alignment_update", "agentgov_alignment_resolve", "agentgov_self_review_start", "agentgov_self_review_complete", "agentgov_task_proposal_review"]
tool_timeout_sec = 60
""",
            )
            findings = self._mcp_findings(
                diagnose_repository(root, python_version=(3, 12, 0))
            )

        self.assertIs(findings["mcp:base-tools"].status, DoctorStatus.WARN)
        self.assertIs(findings["mcp:form-tools"].status, DoctorStatus.WARN)
        self.assertIn("agentgov_task_completion_record", findings["mcp:base-tools"].message)
        self.assertIn("agentgov_drift_review_record", findings["mcp:form-tools"].message)
        self.assertIs(findings["mcp:tool-timeout"].status, DoctorStatus.WARN)

    def test_mcp_allow_then_deny_precedence_and_unknown_name_privacy(self) -> None:
        private_name = "private_company_secret_tool"
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_config(
                root,
                f"""
[mcp_servers.agentgov_governance]
enabled = true
enabled_tools = ["agentgov_alignment_start", "agentgov_task_completion_record", "{private_name}"]
disabled_tools = ["agentgov_alignment_start"]
""",
            )
            findings = self._mcp_findings(
                diagnose_repository(root, python_version=(3, 12, 0))
            )

        self.assertIs(findings["mcp:base-tools"].status, DoctorStatus.WARN)
        self.assertNotIn(private_name, " ".join(item.message for item in findings.values()))
        self.assertNotIn(private_name, findings["mcp:configuration"].message)
        self.assertIn("agentgov_alignment_start", findings["mcp:base-tools"].message)

    def test_mcp_missing_config_is_not_applicable_and_live_state_is_unknown(self) -> None:
        with TemporaryDirectory() as temp_dir:
            findings = self._mcp_findings(
                diagnose_repository(Path(temp_dir), python_version=(3, 12, 0))
            )

        self.assertIs(findings["mcp:configuration"].status, DoctorStatus.PASS)
        self.assertIn("not applicable", findings["mcp:configuration"].message)
        self.assertIs(findings["mcp:live-state"].status, DoctorStatus.ADVISORY)
        self.assertIn("unknown", findings["mcp:live-state"].message.lower())

    def test_mcp_malformed_input_is_bounded_and_does_not_echo_config(self) -> None:
        secret = "do-not-echo-this-private-value"
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_config(
                root,
                f"""
[mcp_servers.agentgov_governance]
enabled = "yes"
enabled_tools = "{secret}"
tool_timeout_sec = nan
""",
            )
            report = diagnose_repository(root, python_version=(3, 12, 0))

        findings = self._mcp_findings(report)
        self.assertIs(findings["mcp:configuration"].status, DoctorStatus.WARN)
        self.assertTrue(all(item.status is not DoctorStatus.FAIL for item in findings.values()))
        self.assertNotIn(secret, " ".join(item.message for item in findings.values()))
        self.assertNotIn("nan", " ".join(item.message for item in findings.values()).lower())

    def test_mcp_omitted_timeout_is_advisory_about_inherited_setting(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_config(root, "[mcp_servers.agentgov_governance]\nenabled = true\n")
            finding = self._mcp_findings(
                diagnose_repository(root, python_version=(3, 12, 0))
            )["mcp:tool-timeout"]

        self.assertIs(finding.status, DoctorStatus.WARN)
        self.assertIn("unknown", finding.message.lower())
        self.assertIn("60", finding.message)

    def test_mcp_diagnostic_does_not_add_git_or_write_side_effects(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_config(root, "[mcp_servers.agentgov_governance]\nenabled = true\n")
            calls = []
            before = tuple(root.rglob("*"))

            def resolver(path: Path) -> Path:
                calls.append(path)
                return path.resolve()

            diagnose_repository(
                root,
                python_version=(3, 12, 0),
                git_worktree_resolver=resolver,
            )
            after = tuple(root.rglob("*"))

        self.assertEqual(calls, [])
        self.assertEqual(before, after)

    def test_mcp_invalid_fields_are_reported_independently_without_raw_values(self) -> None:
        cases = (
            ("enabled", 'enabled = "yes"', "enabled must be a boolean"),
            ("enabled_tools", 'enabled_tools = "private-value"', "enabled_tools must be a list"),
            ("disabled_tools", 'disabled_tools = [1]', "disabled_tools must be a list"),
            ("nan", "tool_timeout_sec = nan", "tool_timeout_sec must be a positive"),
            ("inf", "tool_timeout_sec = inf", "tool_timeout_sec must be a positive"),
            ("negative", "tool_timeout_sec = -1", "tool_timeout_sec must be a positive"),
            ("zero", "tool_timeout_sec = 0", "tool_timeout_sec must be a positive"),
            ("bool", "tool_timeout_sec = true", "tool_timeout_sec must be a positive"),
        )
        for label, field, expected in cases:
            with self.subTest(label=label):
                findings, before, after = self._diagnose_mcp_config(
                    "[mcp_servers.agentgov_governance]\n" + field + "\n"
                )
                self.assertIs(findings["mcp:configuration"].status, DoctorStatus.WARN)
                self.assertIn(expected, findings["mcp:configuration"].message)
                self.assertNotIn("private-value", findings["mcp:configuration"].message)
                self.assertEqual(before, after)

    def test_mcp_missing_server_and_empty_filters_are_nonblocking(self) -> None:
        cases = (
            "[mcp_servers.other]\nenabled = true\n",
            "[mcp_servers.agentgov_governance]\nenabled_tools = []\ndisabled_tools = []\n",
            "[mcp_servers.agentgov_governance]\n",
        )
        for content in cases:
            with self.subTest(content=content):
                findings, before, after = self._diagnose_mcp_config(content)
                self.assertNotEqual(findings, {})
                self.assertTrue(all(item.status is not DoctorStatus.FAIL for item in findings.values()))
                self.assertEqual(before, after)

    def test_mcp_disabled_server_is_warned_without_enable_advice(self) -> None:
        findings, _, _ = self._diagnose_mcp_config(
            "[mcp_servers.agentgov_governance]\nenabled = false\n"
        )
        self.assertIs(findings["mcp:enabled"].status, DoctorStatus.WARN)
        self.assertIn("disabled", findings["mcp:enabled"].message)
        self.assertIn("intentional", findings["mcp:enabled"].message)
        self.assertNotIn("enable", findings["mcp:enabled"].message.lower())

    def test_mcp_malformed_toml_and_invalid_utf8_are_normalized(self) -> None:
        for content, binary in (("[mcp_servers.agentgov_governance\n", False), (b"\xff\xfe", True)):
            with self.subTest(binary=binary):
                findings, before, after = self._diagnose_mcp_config(content, binary=binary)
                self.assertIs(findings["mcp:configuration"].status, DoctorStatus.WARN)
                self.assertNotIn("Traceback", findings["mcp:configuration"].message)
                self.assertEqual(before, after)

    def test_mcp_unreadable_and_oversized_files_are_bounded(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            config = root / ".codex/config.toml"
            config.parent.mkdir()
            config.write_text("[mcp_servers.agentgov_governance]\n", encoding="utf-8")
            before = config.read_bytes()
            with patch("agentgov.doctor.os.open", side_effect=PermissionError("private access")):
                findings = self._mcp_findings(diagnose_repository(root, python_version=(3, 12, 0)))
            self.assertIs(findings["mcp:configuration"].status, DoctorStatus.WARN)
            self.assertNotIn("private access", findings["mcp:configuration"].message)
            self.assertEqual(before, config.read_bytes())

            config.write_bytes(b"x" * (MAX_MCP_CONFIG_BYTES + 1))
            findings = self._mcp_findings(diagnose_repository(root, python_version=(3, 12, 0)))
            self.assertIs(findings["mcp:configuration"].status, DoctorStatus.WARN)
            self.assertIn("256 KiB", findings["mcp:configuration"].message)
            self.assertEqual(b"x" * (MAX_MCP_CONFIG_BYTES + 1), config.read_bytes())

    def test_mcp_wrong_file_types_and_reparse_metadata_are_rejected(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            codex = root / ".codex"
            codex.mkdir()
            target = codex / "config.toml"
            target.mkdir()
            findings = self._mcp_findings(diagnose_repository(root, python_version=(3, 12, 0)))
            self.assertIs(findings["mcp:configuration"].status, DoctorStatus.WARN)

            target.rmdir()
            target.write_text("[mcp_servers.agentgov_governance]\n", encoding="utf-8")
            original_lstat = Path.lstat

            def reparse_lstat(path):
                info = original_lstat(path)
                if path == target:
                    return SimpleNamespace(
                        st_mode=info.st_mode,
                        st_size=info.st_size,
                        st_dev=info.st_dev,
                        st_ino=info.st_ino,
                        st_file_attributes=0x400,
                    )
                return info

            with patch("agentgov.doctor.Path.lstat", autospec=True, side_effect=reparse_lstat), \
                    patch("agentgov.doctor.os.open", side_effect=AssertionError("unsafe target opened")):
                findings = self._mcp_findings(diagnose_repository(root, python_version=(3, 12, 0)))
            self.assertIs(findings["mcp:configuration"].status, DoctorStatus.WARN)
            self.assertIn("unsafe", findings["mcp:configuration"].message)

    def test_mcp_real_symlink_is_rejected_when_supported(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            codex = root / ".codex"
            codex.mkdir()
            real = codex / "real.toml"
            real.write_text("[mcp_servers.agentgov_governance]\n", encoding="utf-8")
            target = codex / "config.toml"
            try:
                target.symlink_to(real)
            except (OSError, NotImplementedError) as exc:
                self.skipTest(f"symbolic links unsupported: {exc}")
            with patch("agentgov.doctor.os.open", side_effect=AssertionError("symlink opened")):
                findings = self._mcp_findings(diagnose_repository(root, python_version=(3, 12, 0)))

        self.assertIs(findings["mcp:configuration"].status, DoctorStatus.WARN)
        self.assertIn("unsafe", findings["mcp:configuration"].message)

    def test_mcp_path_identity_change_before_read_is_rejected(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_config(root, "[mcp_servers.agentgov_governance]\n")
            original_fstat = os.fstat

            def changed_fstat(fd):
                info = original_fstat(fd)
                return SimpleNamespace(
                    st_mode=info.st_mode,
                    st_size=info.st_size,
                    st_dev=info.st_dev,
                    st_ino=info.st_ino + 1,
                    st_file_attributes=getattr(info, "st_file_attributes", 0),
                )

            with patch("agentgov.doctor.os.fstat", side_effect=changed_fstat):
                findings = self._mcp_findings(
                    diagnose_repository(root, python_version=(3, 12, 0))
                )

        self.assertIs(findings["mcp:configuration"].status, DoctorStatus.WARN)
        self.assertIn("identity changed", findings["mcp:configuration"].message)

    def test_mcp_recursion_error_is_normalized_without_raw_exception(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_config(root, "[mcp_servers.agentgov_governance]\n")
            with patch("agentgov.doctor.tomllib.loads", side_effect=RecursionError("deep")):
                findings = self._mcp_findings(diagnose_repository(root, python_version=(3, 12, 0)))

        self.assertIs(findings["mcp:configuration"].status, DoctorStatus.WARN)
        self.assertNotIn("deep", findings["mcp:configuration"].message)

    def test_mcp_optional_config_warnings_keep_cli_nonblocking_exit(self) -> None:
        cases = (
            "[mcp_servers.agentgov_governance]\nenabled = false\n",
            "[mcp_servers.agentgov_governance\n",
        )
        for index, content in enumerate(cases):
            with self.subTest(content=content), TemporaryDirectory() as temp_dir:
                self._write_config(Path(temp_dir), content)
                exit_code, stdout, stderr = run_cli("doctor", temp_dir)

            self.assertEqual(exit_code, EXIT_PASS)
            expected = "WARN mcp:enabled:" if index == 0 else "WARN mcp:configuration:"
            self.assertIn(expected, stdout)
            self.assertEqual(stderr, "")


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
                git_worktree_resolver=lambda path: path.resolve(),
            )

        statuses = {
            finding.check_id: finding.status for finding in report.findings
        }
        self.assertIs(statuses["environment:python"], DoctorStatus.PASS)
        self.assertIs(statuses["repository:git-context"], DoctorStatus.PASS)
        self.assertIs(statuses["repository:git-access"], DoctorStatus.PASS)
        self.assertIs(statuses["adoption:state"], DoctorStatus.PASS)
        self.assertFalse(report.has_failures)

    def test_git_access_failure_is_bounded_deterministic_and_read_only(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / ".git").mkdir()
            before = tuple(root.iterdir())

            def reject_worktree(_: Path) -> Path:
                raise CodexHookPolicyError(
                    "private rejected path and raw Git identity must not escape"
                )

            report = diagnose_repository(
                root,
                python_version=(3, 11, 9),
                git_worktree_resolver=reject_worktree,
            )
            after = tuple(root.iterdir())

        finding = next(
            item
            for item in report.findings
            if item.check_id == "repository:git-access"
        )
        self.assertEqual(before, after)
        self.assertIs(finding.status, DoctorStatus.FAIL)
        self.assertEqual(finding.classification, "deterministic")
        self.assertEqual(
            finding.message,
            "Git worktree access failed; confirm the selected path is a Git "
            "worktree trusted for the current OS account",
        )
        self.assertNotIn("private rejected path", finding.message)
        self.assertNotIn("raw Git identity", finding.message)
        self.assertTrue(report.has_failures)

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
        self.assertEqual(
            payload["tool"],
            {"name": "agentgov", "version": __version__},
        )
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

    def test_cli_git_access_failure_returns_bounded_policy_failure(self) -> None:
        with TemporaryDirectory() as temp_dir:
            (Path(temp_dir) / ".git").mkdir()
            with patch(
                "agentgov.doctor.resolve_git_worktree",
                side_effect=CodexHookPolicyError(
                    "private raw Git diagnostic must not escape"
                ),
            ):
                exit_code, stdout, stderr = run_cli("doctor", temp_dir)

        self.assertEqual(exit_code, EXIT_FAIL)
        self.assertIn("FAIL repository:git-access:", stdout)
        self.assertIn("trusted for the current OS account", stdout)
        self.assertNotIn("private raw Git diagnostic", stdout)
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
        self.assertEqual(schema["properties"]["tool"]["properties"]["name"]["const"], "agentgov")
        self.assertIn("version", schema["properties"]["tool"]["required"])
        authority = schema["properties"]["authority_boundary"]
        self.assertFalse(authority["additionalProperties"])
        for property_schema in authority["properties"].values():
            self.assertIs(property_schema["const"], False)


if __name__ == "__main__":
    unittest.main()
