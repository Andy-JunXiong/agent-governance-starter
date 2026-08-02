import contextlib
import io
import json
import shutil
import subprocess
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from agentgov.change_scope import (
    SCOPE_REPORT_CONTRACT,
    SCOPE_REPORT_SCHEMA_VERSION,
    ScopeFindingStatus,
    check_development_scope,
    render_scope_report_json,
    render_scope_report_markdown,
    render_scope_report_terminal,
)
from agentgov.cli import EXIT_ERROR, EXIT_FAIL, EXIT_PASS, main


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas/development-scope-report.schema.json"


def run_cli(*args: str) -> tuple[int, str, str]:
    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        exit_code = main(list(args))
    return exit_code, stdout.getvalue(), stderr.getvalue()


def run_git(repository: Path, *args: str) -> bytes:
    completed = subprocess.run(
        ("git", "-C", str(repository), *args),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        raise AssertionError(completed.stderr.decode("utf-8", errors="replace"))
    return completed.stdout


def write(repository: Path, relative: str, content: str) -> Path:
    path = repository.joinpath(*relative.split("/"))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def create_repository(parent: Path) -> tuple[Path, Path]:
    repository = parent / "repository"
    repository.mkdir()
    run_git(repository, "init", "--quiet")
    run_git(repository, "config", "user.email", "fixture@example.invalid")
    run_git(repository, "config", "user.name", "Fixture Author")
    write(repository, ".gitignore", ".cache/\n")
    write(repository, "AGENTS.md", "# Fixture authority\n")
    write(repository, "docs/requirement.md", "# Requirement\n")
    write(repository, "docs/adr/0001-scope.md", "# ADR\n")
    write(repository, "src/route/handler.py", "VALUE = 1\n")
    write(repository, "src/route/delete.py", "DELETE = True\n")
    write(repository, "src/route/generated/client.py", "GENERATED = True\n")
    write(repository, "src/router/handler.py", "ROUTER = True\n")
    write(repository, "outside/file.py", "OUTSIDE = True\n")
    task = write(
        repository,
        "governance/tasks/scope-task.json",
        json.dumps(
            {
                "contract": "agentgov.development-task",
                "schema_version": "1.1",
                "profile": "compact",
                "task_id": "fixture-scope-check",
                "title": "Check fixture working tree",
                "requirement": {
                    "summary": "Change only the admitted fixture route and documentation paths.",
                    "source_refs": ["docs/requirement.md"],
                },
                "scope": {
                    "include_paths": [
                        "src/route",
                        "docs",
                        "governance/tasks/scope-task.json",
                    ],
                    "exclude_paths": ["src/route/generated"],
                },
                "architecture_refs": ["docs/adr/0001-scope.md"],
                "acceptance_signals": ["Every working-tree path is classified."],
                "validation_commands": [
                    "python -m unittest tests.test_change_scope -v"
                ],
                "owner": "Fixture owner",
                "risk": {"level": "low", "items": []},
                "decision": {
                    "state": "admitted",
                    "decided_by": "Fixture owner",
                    "rationale": "The fixture owner admits this low-risk scope test.",
                },
            },
            indent=2,
        )
        + "\n",
    )
    run_git(repository, "add", ".")
    run_git(repository, "commit", "--quiet", "-m", "fixture baseline")
    return repository, task


@unittest.skipUnless(shutil.which("git"), "Git is required for scope fixtures")
class DevelopmentScopeTests(unittest.TestCase):
    def test_schema_is_strict_and_denies_git_authority(self) -> None:
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))

        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(
            schema["properties"]["contract"]["const"],
            SCOPE_REPORT_CONTRACT,
        )
        self.assertEqual(
            schema["properties"]["schema_version"]["const"],
            SCOPE_REPORT_SCHEMA_VERSION,
        )
        for value in schema["properties"]["authority_boundary"]["properties"].values():
            self.assertIs(value["const"], False)

    def test_inventory_covers_layers_deletion_untracked_and_ignored_boundary(self) -> None:
        with TemporaryDirectory() as temp_dir:
            repository, task = create_repository(Path(temp_dir))
            write(repository, "src/route/handler.py", "VALUE = 2\n")
            write(repository, "src/route/new.py", "NEW = True\n")
            write(repository, "outside.txt", "outside\n")
            write(repository, ".cache/output.txt", "ignored\n")
            write(repository, "docs/requirement.md", "# Updated requirement\n")
            run_git(repository, "add", "docs/requirement.md")
            run_git(repository, "rm", "--quiet", "src/route/delete.py")
            before = run_git(repository, "status", "--porcelain=v1", "-z")

            report = check_development_scope(task, repository=repository)

            after = run_git(repository, "status", "--porcelain=v1", "-z")

        self.assertEqual(after, before)
        facts = {(item.layer, item.status, item.path) for item in report.changes}
        self.assertIn(("staged", "modified", "docs/requirement.md"), facts)
        self.assertIn(("staged", "deleted", "src/route/delete.py"), facts)
        self.assertIn(("unstaged", "modified", "src/route/handler.py"), facts)
        self.assertIn(("untracked", "untracked", "src/route/new.py"), facts)
        self.assertIn(("untracked", "untracked", "outside.txt"), facts)
        self.assertFalse(any(item.path.startswith(".cache") for item in report.changes))
        self.assertTrue(report.has_failures)
        self.assertEqual(report.count(ScopeFindingStatus.FAIL), 1)
        self.assertEqual(report.count(ScopeFindingStatus.ADVISORY), 1)

    def test_rename_requires_both_endpoints_to_be_admitted(self) -> None:
        scenarios = (
            ("src/route/handler.py", "src/route/moved.py", True),
            ("src/route/handler.py", "outside/moved.py", False),
            ("outside/file.py", "src/route/from-outside.py", False),
        )
        for old_path, new_path, admitted in scenarios:
            with self.subTest(old=old_path, new=new_path):
                with TemporaryDirectory() as temp_dir:
                    repository, task = create_repository(Path(temp_dir))
                    run_git(repository, "mv", old_path, new_path)

                    report = check_development_scope(task, repository=repository)

                rename = next(item for item in report.changes if item.status == "renamed")
                self.assertEqual(rename.old_path, old_path)
                self.assertEqual(rename.path, new_path)
                self.assertEqual(len(rename.endpoints), 2)
                self.assertEqual(rename.admitted, admitted)
                self.assertEqual(report.has_failures, not admitted)

    def test_exclusion_and_similar_string_prefix_are_failures(self) -> None:
        with TemporaryDirectory() as temp_dir:
            repository, task = create_repository(Path(temp_dir))
            write(repository, "src/route/generated/client.py", "GENERATED = False\n")
            write(repository, "src/router/handler.py", "ROUTER = False\n")

            report = check_development_scope(task, repository=repository)

        failed = {
            endpoint.path: endpoint
            for change in report.changes
            for endpoint in change.endpoints
            if not endpoint.admitted
        }
        self.assertEqual(failed["src/route/generated/client.py"].matched_exclude, "src/route/generated")
        self.assertIsNone(failed["src/router/handler.py"].matched_include)
        self.assertEqual(report.count(ScopeFindingStatus.FAIL), 2)

    def test_clean_worktree_reports_no_changes_and_committed_change_limit(self) -> None:
        with TemporaryDirectory() as temp_dir:
            repository, task = create_repository(Path(temp_dir))

            report = check_development_scope(task, repository=repository)

        self.assertFalse(report.has_failures)
        self.assertEqual(report.changes, ())
        self.assertEqual(report.findings[0].check_id, "scope:working-tree:no-changes")
        self.assertTrue(
            any("committed-since-base" in item for item in report.known_limits)
        )

    def test_untracked_agentgov_state_is_excluded_but_tracked_state_is_not_hidden(self) -> None:
        with TemporaryDirectory() as temp_dir:
            repository, task = create_repository(Path(temp_dir))
            write(repository, ".agentgov/current-task.json", "{}\n")

            local_report = check_development_scope(task, repository=repository)
            run_git(repository, "add", ".agentgov/current-task.json")
            tracked_report = check_development_scope(task, repository=repository)

        self.assertFalse(any(change.path.startswith(".agentgov/") for change in local_report.changes))
        self.assertTrue(any(change.path == ".agentgov/current-task.json" for change in tracked_report.changes))
        self.assertTrue(tracked_report.has_failures)

    def test_renderers_are_stable_and_json_is_machine_readable(self) -> None:
        with TemporaryDirectory() as temp_dir:
            repository, task = create_repository(Path(temp_dir))
            write(repository, "src/route/handler.py", "VALUE = 2\n")

            report = check_development_scope(task, repository=repository)
            payload = json.loads(render_scope_report_json(report))

        self.assertEqual(payload["contract"], SCOPE_REPORT_CONTRACT)
        self.assertEqual(payload["findings"][0]["status"], "PASS")
        self.assertTrue(all(value is False for value in payload["authority_boundary"].values()))
        self.assertIn("# Development scope report", render_scope_report_markdown(report))
        self.assertIn("SUMMARY PASS=1 FAIL=0 ADVISORY=1", render_scope_report_terminal(report))

    def test_cli_returns_pass_or_fail_without_mixing_json(self) -> None:
        with TemporaryDirectory() as temp_dir:
            repository, task = create_repository(Path(temp_dir))
            write(repository, "src/route/handler.py", "VALUE = 2\n")

            exit_code, stdout, stderr = run_cli(
                "check",
                "scope",
                str(task),
                "--repository",
                str(repository),
                "--format",
                "json",
            )

            self.assertEqual(exit_code, EXIT_PASS)
            self.assertEqual(json.loads(stdout)["task_id"], "fixture-scope-check")
            self.assertEqual(stderr, "")

            write(repository, "outside.txt", "outside\n")
            exit_code, stdout, stderr = run_cli(
                "check",
                "scope",
                str(task),
                "--repository",
                str(repository),
                "--format",
                "json",
            )

        self.assertEqual(exit_code, EXIT_FAIL)
        self.assertEqual(json.loads(stdout)["findings"][1]["status"], "FAIL")
        self.assertEqual(stderr, "")

    def test_non_git_repository_is_an_operational_error(self) -> None:
        with TemporaryDirectory() as temp_dir:
            repository, task = create_repository(Path(temp_dir))
            nongit = Path(temp_dir) / "nongit"
            shutil.copytree(repository, nongit, ignore=shutil.ignore_patterns(".git"))
            nongit_task = nongit / task.relative_to(repository)

            exit_code, stdout, stderr = run_cli(
                "check",
                "scope",
                str(nongit_task),
                "--repository",
                str(nongit),
            )

        self.assertEqual(exit_code, EXIT_ERROR)
        self.assertEqual(stdout, "")
        self.assertIn("ERROR scope:", stderr)


if __name__ == "__main__":
    unittest.main()
