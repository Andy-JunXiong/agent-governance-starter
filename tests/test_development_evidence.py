import base64
import json
import contextlib
import io
import os
import shutil
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

from agentgov.development_evidence import (
    COMPLETION_CONTRACT,
    EVIDENCE_CONTRACT,
    EvidenceError,
    _validation_process_argv,
    reconcile_task_completion,
    render_completion_json,
    render_validation_json,
    run_task_validation,
)
from agentgov.cli import EXIT_FAIL, EXIT_PASS, main
from agentgov.task_start_scope_baseline import (
    capture_task_start_baseline,
    task_start_baseline_path,
    write_baseline,
)


ROOT = Path(__file__).resolve().parents[1]


def run_cli(*args: str) -> tuple[int, str, str]:
    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        exit_code = main(list(args))
    return exit_code, stdout.getvalue(), stderr.getvalue()


def run_git(repository: Path, *args: str) -> str:
    completed = subprocess.run(
        ("git", "-C", str(repository), *args),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        raise AssertionError(completed.stderr.decode("utf-8", errors="replace"))
    return completed.stdout.decode("ascii", errors="replace").strip()


def write(repository: Path, relative: str, content: str) -> Path:
    path = repository.joinpath(*relative.split("/"))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def python_validation_command(source: str) -> str:
    command = f'"{sys.executable}" -c "{source}"'
    return f"& {command}" if os.name == "nt" else command


def task_document(command: str) -> dict[str, object]:
    return {
        "contract": "agentgov.development-task",
        "schema_version": "1.1",
        "profile": "compact",
        "task_id": "fixture-fresh-evidence",
        "title": "Verify fixture task completion",
        "requirement": {
            "summary": "Change and validate only the admitted fixture source paths.",
            "source_refs": ["docs/requirement.md"],
        },
        "scope": {
            "include_paths": ["src", "docs", "governance/tasks/task.json", ".gitignore", ".agentgov/tracked.txt"],
            "exclude_paths": [],
        },
        "architecture_refs": ["docs/adr/0001.md"],
        "acceptance_signals": ["The declared validation command passes."],
        "validation_commands": [command],
        "owner": "Fixture owner",
        "risk": {"level": "low", "items": []},
        "decision": {
            "state": "admitted",
            "decided_by": "Fixture owner",
            "rationale": "The fixture owner admits this validation exercise.",
        },
    }


def create_repository(parent: Path, command: str | None = None) -> tuple[Path, Path, str]:
    repository = parent / "repository"
    repository.mkdir()
    run_git(repository, "init", "--quiet")
    run_git(repository, "config", "user.email", "fixture@example.invalid")
    run_git(repository, "config", "user.name", "Fixture Author")
    write(repository, ".gitignore", ".cache/\n")
    write(repository, "AGENTS.md", "# Fixture authority\n")
    write(repository, "docs/requirement.md", "# Requirement\n")
    write(repository, "docs/adr/0001.md", "# ADR\n")
    write(repository, "src/app.py", "VALUE = 1\n")
    validation = command or python_validation_command("print('fixture-pass')")
    task = write(
        repository,
        "governance/tasks/task.json",
        json.dumps(task_document(validation), indent=2) + "\n",
    )
    run_git(repository, "add", ".")
    run_git(repository, "commit", "--quiet", "-m", "baseline")
    return repository, task, run_git(repository, "rev-parse", "HEAD")


def capture_start_baseline(repository: Path, task: Path, base: str) -> str:
    baseline_ref = task_start_baseline_path("fixture-fresh-evidence")
    baseline = capture_task_start_baseline(
        repository,
        task_path=task.relative_to(repository).as_posix(),
        comparison_base=base,
    )
    write_baseline(baseline, repository=repository, output_path=baseline_ref)
    return baseline_ref


@unittest.skipUnless(shutil.which("git"), "Git is required for evidence fixtures")
class DevelopmentEvidenceTests(unittest.TestCase):
    def test_windows_validation_argv_is_encoded_noninteractive_powershell(self) -> None:
        command = '$env:FIXTURE_VALUE = "quoted value"; Write-Output $env:FIXTURE_VALUE'

        argv = _validation_process_argv(command, platform_name="nt")
        script = base64.b64decode(argv[-1]).decode("utf-16-le")

        self.assertEqual(
            argv[:-1],
            (
                "powershell.exe",
                "-NoLogo",
                "-NoProfile",
                "-NonInteractive",
                "-EncodedCommand",
            ),
        )
        self.assertIn(command, script)
        self.assertIn("$agentgovCommandSucceeded = $?", script)
        self.assertIn("exit $agentgovNativeExitCode", script)

    def test_windows_quoted_executable_compatibility_adds_call_operator(self) -> None:
        command = f'"{sys.executable}" -c "print(\'fixture-pass\')"'

        argv = _validation_process_argv(command, platform_name="nt")
        script = base64.b64decode(argv[-1]).decode("utf-16-le")

        self.assertTrue(script.startswith(f"& {command}\n"))

    def test_posix_validation_argv_uses_explicit_bin_sh(self) -> None:
        command = "printf 'fixture-pass\\n'"

        argv = _validation_process_argv(command, platform_name="posix")

        self.assertEqual(argv, ("/bin/sh", "-c", command))

    def test_unsupported_validation_platform_fails_closed(self) -> None:
        with self.assertRaisesRegex(EvidenceError, "unsupported on platform"):
            _validation_process_argv("true", platform_name="fixture-os")

    def test_unavailable_validation_shell_fails_before_evidence_is_written(self) -> None:
        with TemporaryDirectory() as temp_dir:
            repository, task, base = create_repository(Path(temp_dir))
            with mock.patch(
                "agentgov.development_evidence._validation_process_argv",
                return_value=("agentgov-fixture-missing-shell",),
            ):
                with self.assertRaisesRegex(EvidenceError, "validation shell is unavailable"):
                    run_task_validation(task, repository=repository, comparison_base=base)

            evidence_paths = list((repository / ".agentgov" / "evidence").glob("*.json"))
            event_paths = list((repository / ".agentgov" / "events").glob("*.json"))

        self.assertEqual(evidence_paths, [])
        self.assertEqual(event_paths, [])

    @unittest.skipUnless(
        os.name == "nt" and shutil.which("powershell.exe"),
        "Windows PowerShell is required for the native validation fixture",
    )
    def test_windows_powershell_preserves_quoting_and_environment_assignment(self) -> None:
        command = (
            '$env:AGENTGOV_FIXTURE = "quoted value"; '
            'if ($env:AGENTGOV_FIXTURE -eq "quoted value") { '
            'Write-Output "fixture-pass" } else { exit 9 }'
        )
        with TemporaryDirectory() as temp_dir:
            repository, task, base = create_repository(Path(temp_dir), command)

            run = run_task_validation(task, repository=repository, comparison_base=base)

        self.assertEqual(run.evidence.outcome, "passed")
        self.assertEqual(run.evidence.commands[0].exit_code, 0)
        self.assertIn("fixture-pass", run.transient_outputs[0][0])

    @unittest.skipUnless(
        os.name == "nt" and shutil.which("powershell.exe"),
        "Windows PowerShell is required for the native validation fixture",
    )
    def test_windows_powershell_propagates_native_and_shell_failures(self) -> None:
        scenarios = (
            (python_validation_command("import sys; sys.exit(7)"), 7),
            ('Write-Error "fixture-shell-failure"', 1),
        )
        for command, expected_exit in scenarios:
            with self.subTest(command=command), TemporaryDirectory() as temp_dir:
                repository, task, base = create_repository(Path(temp_dir), command)

                run = run_task_validation(task, repository=repository, comparison_base=base)

            self.assertEqual(run.evidence.outcome, "failed")
            self.assertEqual(run.evidence.commands[0].exit_code, expected_exit)

    @unittest.skipUnless(
        os.name == "posix" and Path("/bin/sh").exists(),
        "/bin/sh is required for the POSIX validation fixture",
    )
    def test_posix_shell_propagates_success_and_failure(self) -> None:
        scenarios = (("printf 'fixture-pass\\n'", 0), ("exit 5", 5))
        for command, expected_exit in scenarios:
            with self.subTest(command=command), TemporaryDirectory() as temp_dir:
                repository, task, base = create_repository(Path(temp_dir), command)

                run = run_task_validation(task, repository=repository, comparison_base=base)

            self.assertEqual(run.evidence.commands[0].exit_code, expected_exit)
            self.assertEqual(
                run.evidence.outcome,
                "passed" if expected_exit == 0 else "failed",
            )

    def test_validate_then_finish_before_commit_is_verified_and_local_events_do_not_stale_it(self) -> None:
        with TemporaryDirectory() as temp_dir:
            repository, task, base = create_repository(Path(temp_dir))
            write(repository, "src/app.py", "VALUE = 2\n")

            run = run_task_validation(task, repository=repository, comparison_base=base)
            report = reconcile_task_completion(task, repository=repository)
            evidence_payload = json.loads((repository / run.evidence_ref).read_text(encoding="utf-8"))
            rendered = render_validation_json(run)

        self.assertEqual(run.evidence.outcome, "passed")
        self.assertEqual(report.state, "verified")
        self.assertEqual(evidence_payload["contract"], EVIDENCE_CONTRACT)
        self.assertNotIn("fixture-pass", rendered)
        self.assertNotIn(str(repository), rendered)
        self.assertTrue(run.event_ref.startswith(".agentgov/events/"))
        self.assertTrue(report.event_ref.startswith(".agentgov/events/"))

    def test_commit_before_validation_is_verified(self) -> None:
        with TemporaryDirectory() as temp_dir:
            repository, task, base = create_repository(Path(temp_dir))
            write(repository, "src/app.py", "VALUE = 2\n")
            run_git(repository, "add", "src/app.py")
            run_git(repository, "commit", "--quiet", "-m", "task work")

            run = run_task_validation(task, repository=repository, comparison_base=base)
            report = reconcile_task_completion(task, repository=repository)

        self.assertEqual(run.evidence.outcome, "passed")
        self.assertEqual(report.state, "verified")
        committed = next(layer for layer in run.evidence.snapshot_after.layers if layer.name == "committed")
        self.assertTrue(committed.changes)

    def test_validation_generated_nonignored_artifact_is_stale_and_actionable(self) -> None:
        command = python_validation_command(
            "from pathlib import Path; Path('generated.txt').write_text('generated')"
        )
        with TemporaryDirectory() as temp_dir:
            repository, task, base = create_repository(Path(temp_dir), command)

            run = run_task_validation(task, repository=repository, comparison_base=base)
            report = reconcile_task_completion(task, repository=repository)

        self.assertEqual(run.evidence.outcome, "stale")
        self.assertEqual(report.state, "needs_evidence")
        self.assertTrue(any("generated.txt" in reason for reason in run.evidence.mutation_reasons))
        self.assertTrue(any("remove disposable output" in finding.message for finding in report.findings))

    def test_failed_validation_cannot_verify_and_raw_output_is_not_persisted(self) -> None:
        command = python_validation_command(
            "print('private-failure-output'); raise SystemExit(3)"
        )
        with TemporaryDirectory() as temp_dir:
            repository, task, base = create_repository(Path(temp_dir), command)

            run = run_task_validation(task, repository=repository, comparison_base=base)
            report = reconcile_task_completion(task, repository=repository)
            persisted = (repository / run.evidence_ref).read_text(encoding="utf-8")

        self.assertEqual(run.evidence.outcome, "failed")
        self.assertEqual(report.state, "needs_evidence")
        self.assertNotIn("private-failure-output", persisted)
        self.assertNotIn(command, persisted)

    def test_validation_stops_after_first_failed_command(self) -> None:
        with TemporaryDirectory() as temp_dir:
            repository, task, base = create_repository(Path(temp_dir))
            document = json.loads(task.read_text(encoding="utf-8"))
            document["validation_commands"] = [
                python_validation_command("raise SystemExit(4)"),
                python_validation_command(
                    "from pathlib import Path; Path('should-not-run').write_text('ran')"
                ),
            ]
            task.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")

            run = run_task_validation(task, repository=repository, comparison_base=base)
            second_command_ran = (repository / "should-not-run").exists()

        self.assertEqual(run.evidence.outcome, "failed")
        self.assertEqual(len(run.evidence.commands), 1)
        self.assertEqual(run.evidence.commands[0].exit_code, 4)
        self.assertFalse(second_command_ran)

    def test_ignored_validation_artifact_does_not_stale_evidence(self) -> None:
        command = python_validation_command(
            "from pathlib import Path; Path('.cache').mkdir(exist_ok=True); "
            "Path('.cache/out').write_text('ignored')"
        )
        with TemporaryDirectory() as temp_dir:
            repository, task, base = create_repository(Path(temp_dir), command)

            run = run_task_validation(task, repository=repository, comparison_base=base)
            report = reconcile_task_completion(task, repository=repository)

        self.assertEqual(run.evidence.outcome, "passed")
        self.assertEqual(report.state, "verified")

    def test_post_validation_mutations_cannot_verify(self) -> None:
        scenarios = ("edit", "stage", "commit", "rename", "gitignore", "task")
        for scenario in scenarios:
            with self.subTest(scenario=scenario), TemporaryDirectory() as temp_dir:
                repository, task, base = create_repository(Path(temp_dir))
                run_task_validation(task, repository=repository, comparison_base=base)
                if scenario == "edit":
                    write(repository, "src/app.py", "VALUE = 3\n")
                elif scenario == "stage":
                    write(repository, "src/app.py", "VALUE = 3\n")
                    run_git(repository, "add", "src/app.py")
                elif scenario == "commit":
                    write(repository, "src/app.py", "VALUE = 3\n")
                    run_git(repository, "add", "src/app.py")
                    run_git(repository, "commit", "--quiet", "-m", "after validation")
                elif scenario == "rename":
                    run_git(repository, "mv", "src/app.py", "src/moved.py")
                elif scenario == "gitignore":
                    write(repository, ".gitignore", ".cache/\nbuild/\n")
                else:
                    document = json.loads(task.read_text(encoding="utf-8"))
                    document["title"] = "Changed valid fixture task title"
                    task.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")

                report = reconcile_task_completion(task, repository=repository)

            self.assertEqual(report.state, "needs_evidence")
            self.assertTrue(any(finding.status == "FAIL" for finding in report.findings))

    def test_tracked_agentgov_change_is_not_hidden(self) -> None:
        with TemporaryDirectory() as temp_dir:
            repository, task, base = create_repository(Path(temp_dir))
            write(repository, ".agentgov/tracked.txt", "baseline\n")
            run_git(repository, "add", "-f", ".agentgov/tracked.txt")
            run_git(repository, "commit", "--quiet", "-m", "tracked local state fixture")
            run_task_validation(task, repository=repository, comparison_base=base)
            write(repository, ".agentgov/tracked.txt", "changed\n")

            report = reconcile_task_completion(task, repository=repository)

        self.assertEqual(report.state, "needs_evidence")
        self.assertTrue(any(".agentgov/tracked.txt" in finding.message for finding in report.findings))

    def test_committed_change_outside_task_scope_prevents_verified_completion(self) -> None:
        with TemporaryDirectory() as temp_dir:
            repository, task, base = create_repository(Path(temp_dir))
            write(repository, "outside.py", "OUTSIDE = True\n")
            run_git(repository, "add", "outside.py")
            run_git(repository, "commit", "--quiet", "-m", "outside task scope")

            run = run_task_validation(task, repository=repository, comparison_base=base)
            report = reconcile_task_completion(task, repository=repository)

        self.assertEqual(run.evidence.outcome, "passed")
        self.assertEqual(report.state, "needs_evidence")
        self.assertTrue(any(item.check_id == "scope.changed" and item.status == "FAIL" for item in report.findings))

    def test_unchanged_preexisting_exclusion_is_visible_and_does_not_block_completion(self) -> None:
        with TemporaryDirectory() as temp_dir:
            repository, task, _ = create_repository(Path(temp_dir))
            document = json.loads(task.read_text(encoding="utf-8"))
            document["scope"]["exclude_paths"] = ["legacy.txt"]
            task.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
            run_git(repository, "add", task.relative_to(repository).as_posix())
            run_git(repository, "commit", "--quiet", "-m", "declare predecessor exclusion")
            base = run_git(repository, "rev-parse", "HEAD")
            write(repository, "legacy.txt", "predecessor\n")
            capture_start_baseline(repository, task, base)
            write(repository, "src/app.py", "VALUE = 2\n")

            run_task_validation(task, repository=repository, comparison_base=base)
            report = reconcile_task_completion(task, repository=repository)

        self.assertEqual(report.state, "verified")
        preserved = [item for item in report.findings if item.check_id == "scope.preserved"]
        self.assertEqual(len(preserved), 1)
        self.assertEqual(preserved[0].status, "PASS")
        self.assertIn("non-owned", preserved[0].message)
        self.assertIn("legacy.txt", preserved[0].message)

    def test_changed_or_malformed_preexisting_exclusion_fails_closed(self) -> None:
        for scenario in ("changed", "malformed"):
            with self.subTest(scenario=scenario), TemporaryDirectory() as temp_dir:
                repository, task, _ = create_repository(Path(temp_dir))
                document = json.loads(task.read_text(encoding="utf-8"))
                document["scope"]["exclude_paths"] = ["legacy.txt"]
                task.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
                run_git(repository, "add", task.relative_to(repository).as_posix())
                run_git(repository, "commit", "--quiet", "-m", "declare predecessor exclusion")
                base = run_git(repository, "rev-parse", "HEAD")
                write(repository, "legacy.txt", "predecessor\n")
                baseline_ref = capture_start_baseline(repository, task, base)
                if scenario == "changed":
                    write(repository, "legacy.txt", "changed after start\n")
                else:
                    (repository / baseline_ref).write_text("{}\n", encoding="utf-8")
                write(repository, "src/app.py", "VALUE = 2\n")

                run_task_validation(task, repository=repository, comparison_base=base)
                report = reconcile_task_completion(task, repository=repository)

            self.assertEqual(report.state, "needs_evidence")
            self.assertTrue(
                any(
                    item.status == "FAIL" and item.check_id == "scope.baseline"
                    for item in report.findings
                )
            )

    def test_missing_baseline_retains_strict_legacy_scope_behavior(self) -> None:
        with TemporaryDirectory() as temp_dir:
            repository, task, _ = create_repository(Path(temp_dir))
            document = json.loads(task.read_text(encoding="utf-8"))
            document["scope"]["exclude_paths"] = ["legacy.txt"]
            task.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
            run_git(repository, "add", task.relative_to(repository).as_posix())
            run_git(repository, "commit", "--quiet", "-m", "declare predecessor exclusion")
            base = run_git(repository, "rev-parse", "HEAD")
            write(repository, "legacy.txt", "predecessor\n")

            run_task_validation(task, repository=repository, comparison_base=base)
            report = reconcile_task_completion(task, repository=repository)

        self.assertEqual(report.state, "needs_evidence")
        self.assertTrue(
            any(item.status == "FAIL" and item.check_id == "scope.changed" for item in report.findings)
        )

    def test_missing_evidence_is_needs_evidence_not_verified(self) -> None:
        with TemporaryDirectory() as temp_dir:
            repository, task, _ = create_repository(Path(temp_dir))

            report = reconcile_task_completion(task, repository=repository)
            payload = json.loads(render_completion_json(report))

        self.assertEqual(report.state, "needs_evidence")
        self.assertEqual(payload["contract"], COMPLETION_CONTRACT)
        self.assertIsNone(payload["evidence_id"])

    def test_internally_inconsistent_evidence_cannot_verify(self) -> None:
        with TemporaryDirectory() as temp_dir:
            repository, task, base = create_repository(Path(temp_dir))
            run = run_task_validation(task, repository=repository, comparison_base=base)
            evidence_path = repository / run.evidence_ref
            payload = json.loads(evidence_path.read_text(encoding="utf-8"))
            payload["commands"][0]["exit_code"] = 7
            evidence_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

            report = reconcile_task_completion(
                task,
                repository=repository,
                evidence_path=Path(run.evidence_ref),
            )

        self.assertEqual(report.state, "needs_evidence")
        self.assertTrue(any(item.check_id == "evidence.integrity" for item in report.findings))

    def test_schemas_are_strict_and_all_authority_is_false(self) -> None:
        for name, contract in (
            ("development-evidence.schema.json", EVIDENCE_CONTRACT),
            ("development-completion.schema.json", COMPLETION_CONTRACT),
            ("governance-event.schema.json", "agentgov.governance-event"),
        ):
            with self.subTest(schema=name):
                schema = json.loads((ROOT / "schemas" / name).read_text(encoding="utf-8"))
                self.assertFalse(schema["additionalProperties"])
                self.assertEqual(schema["properties"]["contract"]["const"], contract)

    def test_govern_finish_cli_runs_validation_and_emits_pure_json(self) -> None:
        with TemporaryDirectory() as temp_dir:
            repository, task, base = create_repository(Path(temp_dir))
            write(repository, "src/app.py", "VALUE = 2\n")

            exit_code, stdout, stderr = run_cli(
                "govern", "finish", str(task),
                "--repository", str(repository),
                "--base", base,
                "--format", "json",
            )
            payload = json.loads(stdout)
            write(repository, "src/app.py", "VALUE = 3\n")
            stale_code, stale_stdout, _ = run_cli(
                "govern", "finish", str(task),
                "--repository", str(repository),
                "--format", "json",
            )

        self.assertEqual(exit_code, EXIT_PASS)
        self.assertEqual(payload["state"], "verified")
        self.assertEqual(stderr, "")
        self.assertEqual(stale_code, EXIT_FAIL)
        self.assertEqual(json.loads(stale_stdout)["state"], "needs_evidence")

    def test_govern_check_cli_appends_scope_event_without_mixing_json(self) -> None:
        with TemporaryDirectory() as temp_dir:
            repository, task, _ = create_repository(Path(temp_dir))
            write(repository, "src/app.py", "VALUE = 2\n")

            exit_code, stdout, stderr = run_cli(
                "govern", "check", str(task),
                "--repository", str(repository),
                "--format", "json",
            )
            events = list((repository / ".agentgov" / "events").glob("*.json"))
            event_payload = json.loads(events[0].read_text(encoding="utf-8"))

        self.assertEqual(exit_code, EXIT_PASS)
        self.assertEqual(json.loads(stdout)["task_id"], "fixture-fresh-evidence")
        self.assertEqual(stderr, "")
        self.assertEqual(len(events), 1)
        self.assertEqual(event_payload["event_type"], "scope.checked")


if __name__ == "__main__":
    unittest.main()
