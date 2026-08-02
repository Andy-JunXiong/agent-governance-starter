import contextlib
import io
import json
import shutil
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from agentgov.cli import EXIT_FAIL, EXIT_PASS, main
from agentgov.development_monitor import build_development_monitor
from agentgov.development_session import (
    SESSION_CONTRACT,
    SessionPolicyError,
    apply_start_plan,
    build_start_plan,
    discover_admitted_tasks,
    load_active_session,
    request_start_confirmation,
    resolve_active_task,
)
from agentgov.event_store import load_governance_events


ROOT = Path(__file__).resolve().parents[1]


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


def task_document(task_id: str = "fixture-session") -> dict[str, object]:
    return {
        "contract": "agentgov.development-task",
        "schema_version": "1.1",
        "profile": "compact",
        "task_id": task_id,
        "title": "Develop the fixture session",
        "requirement": {
            "summary": "Change and validate only the admitted fixture source paths.",
            "source_refs": [],
        },
        "scope": {
            "include_paths": ["src", f"governance/tasks/{task_id}.json"],
            "exclude_paths": [],
        },
        "acceptance_signals": ["The fixture validation command passes."],
        "validation_commands": [f'"{sys.executable}" -c "print(\'session-pass\')"'],
        "owner": "Fixture owner",
        "risk": {"level": "low", "items": []},
        "decision": {
            "state": "admitted",
            "decided_by": "Fixture owner",
            "rationale": "The fixture owner explicitly admits this development task.",
        },
    }


def create_repository(parent: Path, *, tasks: int = 1) -> tuple[Path, list[Path], str]:
    repository = parent / "repository"
    repository.mkdir()
    run_git(repository, "init", "--quiet")
    run_git(repository, "config", "user.email", "fixture@example.invalid")
    run_git(repository, "config", "user.name", "Fixture Author")
    write(repository, "AGENTS.md", "# Fixture authority\n")
    write(repository, "pyproject.toml", "[project]\nname='fixture'\nversion='0.0.0'\n")
    write(repository, "tests/test_fixture.py", "# fixture\n")
    write(repository, "src/app.py", "VALUE = 1\n")
    task_paths = []
    for index in range(tasks):
        task_id = "fixture-session" if index == 0 else f"fixture-session-{index + 1}"
        task_paths.append(
            write(
                repository,
                f"governance/tasks/{task_id}.json",
                json.dumps(task_document(task_id), indent=2) + "\n",
            )
        )
    run_git(repository, "add", ".")
    run_git(repository, "commit", "--quiet", "-m", "baseline")
    return repository, task_paths, run_git(repository, "rev-parse", "HEAD")


def run_cli(*args: str) -> tuple[int, str, str]:
    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        code = main(list(args))
    return code, stdout.getvalue(), stderr.getvalue()


class InteractiveInput(io.StringIO):
    def isatty(self) -> bool:
        return True


@unittest.skipUnless(shutil.which("git"), "Git is required for session fixtures")
class DevelopmentSessionTests(unittest.TestCase):
    def test_existing_task_plan_is_read_only_and_lists_exact_targets(self) -> None:
        with TemporaryDirectory() as temp_dir:
            repository, tasks, base = create_repository(Path(temp_dir))
            plan = build_start_plan(repository, task=tasks[0])

            self.assertFalse((repository / ".agentgov").exists())

        self.assertEqual(plan.session.comparison_base_sha, base)
        self.assertEqual(plan.targets[0], ".agentgov/current-task.json")
        self.assertEqual(plan.targets[1], f".agentgov/events/{plan.event_id}.json")
        self.assertEqual(plan.selected_governance, ("AGENTS.md", "governance/tasks/fixture-session.json"))

    def test_confirmation_requires_exact_word_and_interactive_terminal(self) -> None:
        with TemporaryDirectory() as temp_dir:
            repository, tasks, _ = create_repository(Path(temp_dir))
            plan = build_start_plan(repository, task=tasks[0])

            self.assertFalse(request_start_confirmation(plan, decision_reader=lambda _: "START", is_interactive_terminal=False))
            self.assertFalse(request_start_confirmation(plan, decision_reader=lambda _: "start", is_interactive_terminal=True))
            self.assertTrue(request_start_confirmation(plan, decision_reader=lambda _: "START", is_interactive_terminal=True))

    def test_apply_new_compact_task_writes_pointer_and_start_observation(self) -> None:
        with TemporaryDirectory() as temp_dir:
            repository, _, _ = create_repository(Path(temp_dir), tasks=0)
            plan = build_start_plan(
                repository,
                title="Add guided session",
                include_paths=("src",),
                actor_label="fixture-owner",
            )
            result = apply_start_plan(plan)
            session = load_active_session(repository)
            events = load_governance_events(repository / ".agentgov/events").events
            monitor = build_development_monitor(repository)
            created = json.loads((repository / result.session.task_path).read_text(encoding="utf-8"))

        self.assertIsNotNone(session)
        assert session is not None
        self.assertEqual(session.contract, SESSION_CONTRACT)
        self.assertIn("governance/tasks/add-guided-session.json", created["scope"]["include_paths"])
        self.assertTrue(result.created_task)
        self.assertEqual(events[0].event_type, "task.started")
        self.assertEqual(events[0].outcome, "started")
        self.assertEqual(events[0].governance_refs, ("AGENTS.md", "governance/tasks/add-guided-session.json"))
        self.assertEqual(monitor.overview["task_starts"], 1)
        self.assertEqual(monitor.timeline[0]["governance_refs"], ["AGENTS.md", "governance/tasks/add-guided-session.json"])

    def test_noninteractive_start_previews_but_never_writes(self) -> None:
        with TemporaryDirectory() as temp_dir:
            repository, tasks, _ = create_repository(Path(temp_dir))
            code, stdout, stderr = run_cli(
                "govern", "start", str(tasks[0]), "--repository", str(repository)
            )

            self.assertFalse((repository / ".agentgov").exists())

        self.assertEqual(code, EXIT_FAIL)
        self.assertIn("GOVERN START PREVIEW", stdout)
        self.assertIn("CANCELLED", stdout)
        self.assertEqual(stderr, "")

    def test_cli_exact_confirmation_applies_the_reviewed_start(self) -> None:
        with TemporaryDirectory() as temp_dir:
            repository, tasks, _ = create_repository(Path(temp_dir))
            with patch.object(sys, "stdin", InteractiveInput("START\n")):
                code, stdout, stderr = run_cli(
                    "govern", "start", str(tasks[0]), "--repository", str(repository)
                )
            session = load_active_session(repository)
            event_count = len(load_governance_events(repository / ".agentgov/events").events)

        self.assertEqual(code, EXIT_PASS)
        self.assertIsNotNone(session)
        self.assertIn("STARTED fixture-session", stdout)
        self.assertIn("SELECTED_GOVERNANCE 2", stdout)
        self.assertEqual(event_count, 1)
        self.assertEqual(stderr, "")

    def test_json_start_preview_is_pure_and_dry_run_only(self) -> None:
        with TemporaryDirectory() as temp_dir:
            repository, tasks, _ = create_repository(Path(temp_dir))
            code, stdout, stderr = run_cli(
                "govern", "start", str(tasks[0]), "--repository", str(repository),
                "--dry-run", "--format", "json",
            )
            rejected, rejected_stdout, rejected_stderr = run_cli(
                "govern", "start", str(tasks[0]), "--repository", str(repository),
                "--format", "json",
            )

            self.assertFalse((repository / ".agentgov").exists())

        self.assertEqual(code, EXIT_PASS)
        self.assertEqual(json.loads(stdout)["action"], "start")
        self.assertEqual(stderr, "")
        self.assertNotEqual(rejected, EXIT_PASS)
        self.assertEqual(rejected_stdout, "")
        self.assertIn("requires --dry-run", rejected_stderr)

    def test_task_drift_fails_closed_and_does_not_change_pointer(self) -> None:
        with TemporaryDirectory() as temp_dir:
            repository, tasks, _ = create_repository(Path(temp_dir))
            plan = build_start_plan(repository, task=tasks[0])
            apply_start_plan(plan)
            pointer_before = (repository / ".agentgov/current-task.json").read_bytes()
            payload = json.loads(tasks[0].read_text(encoding="utf-8"))
            payload["scope"]["include_paths"].append("docs")
            tasks[0].write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

            with self.assertRaisesRegex(SessionPolicyError, "changed after govern start"):
                resolve_active_task(repository)

            self.assertEqual((repository / ".agentgov/current-task.json").read_bytes(), pointer_before)

    def test_discovery_never_chooses_among_multiple_admitted_tasks(self) -> None:
        with TemporaryDirectory() as temp_dir:
            repository, _, _ = create_repository(Path(temp_dir), tasks=2)

            self.assertEqual(len(discover_admitted_tasks(repository)), 2)
            with self.assertRaisesRegex(SessionPolicyError, "multiple admitted tasks"):
                build_start_plan(repository)

    def test_different_active_task_requires_replace_preview_and_replace_word(self) -> None:
        with TemporaryDirectory() as temp_dir:
            repository, tasks, _ = create_repository(Path(temp_dir), tasks=2)
            first = build_start_plan(repository, task=tasks[0])
            apply_start_plan(first)

            with self.assertRaisesRegex(SessionPolicyError, "--replace-active"):
                build_start_plan(repository, task=tasks[1])
            replacement = build_start_plan(repository, task=tasks[1], replace_active=True)

        self.assertTrue(replacement.replace_active)
        self.assertFalse(request_start_confirmation(replacement, decision_reader=lambda _: "START", is_interactive_terminal=True))
        self.assertTrue(request_start_confirmation(replacement, decision_reader=lambda _: "REPLACE", is_interactive_terminal=True))

    def test_check_and_finish_default_to_active_task_and_recorded_base(self) -> None:
        with TemporaryDirectory() as temp_dir:
            repository, tasks, _ = create_repository(Path(temp_dir))
            apply_start_plan(build_start_plan(repository, task=tasks[0]))
            write(repository, "src/app.py", "VALUE = 2\n")

            check_code, check_stdout, check_stderr = run_cli(
                "govern", "check", "--repository", str(repository)
            )
            finish_code, finish_stdout, finish_stderr = run_cli(
                "govern", "finish", "--repository", str(repository), "--format", "json"
            )

        self.assertEqual(check_code, EXIT_PASS, (check_stdout, check_stderr))
        self.assertIn("EVENT .agentgov/events/", check_stdout)
        self.assertEqual(check_stderr, "")
        self.assertEqual(finish_code, EXIT_PASS)
        self.assertEqual(json.loads(finish_stdout)["state"], "verified")
        self.assertEqual(finish_stderr, "")

    def test_session_schema_is_strict(self) -> None:
        schema = json.loads((ROOT / "schemas/development-session.schema.json").read_text(encoding="utf-8"))
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(schema["properties"]["contract"]["const"], SESSION_CONTRACT)


if __name__ == "__main__":
    unittest.main()
