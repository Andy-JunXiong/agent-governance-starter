import json
import contextlib
import io
import shutil
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from agentgov.development_evidence import (
    COMPLETION_CONTRACT,
    EVIDENCE_CONTRACT,
    reconcile_task_completion,
    render_completion_json,
    render_validation_json,
    run_task_validation,
)
from agentgov.cli import EXIT_FAIL, EXIT_PASS, main


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
    validation = command or f'"{sys.executable}" -c "print(\'fixture-pass\')"'
    task = write(
        repository,
        "governance/tasks/task.json",
        json.dumps(task_document(validation), indent=2) + "\n",
    )
    run_git(repository, "add", ".")
    run_git(repository, "commit", "--quiet", "-m", "baseline")
    return repository, task, run_git(repository, "rev-parse", "HEAD")


@unittest.skipUnless(shutil.which("git"), "Git is required for evidence fixtures")
class DevelopmentEvidenceTests(unittest.TestCase):
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
        command = (
            f'"{sys.executable}" -c "from pathlib import Path; '
            "Path('generated.txt').write_text('generated')\""
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
        command = f'"{sys.executable}" -c "print(\'private-failure-output\'); raise SystemExit(3)"'
        with TemporaryDirectory() as temp_dir:
            repository, task, base = create_repository(Path(temp_dir), command)

            run = run_task_validation(task, repository=repository, comparison_base=base)
            report = reconcile_task_completion(task, repository=repository)
            persisted = (repository / run.evidence_ref).read_text(encoding="utf-8")

        self.assertEqual(run.evidence.outcome, "failed")
        self.assertEqual(report.state, "needs_evidence")
        self.assertNotIn("private-failure-output", persisted)
        self.assertNotIn(command, persisted)

    def test_ignored_validation_artifact_does_not_stale_evidence(self) -> None:
        command = (
            f'"{sys.executable}" -c "from pathlib import Path; '
            "Path('.cache').mkdir(exist_ok=True); Path('.cache/out').write_text('ignored')\""
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
