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

from agentgov.cli import EXIT_ERROR, EXIT_FAIL, EXIT_PASS, main
from agentgov.development_evidence import reconcile_task_completion, run_task_validation
from agentgov.development_handoff import (
    HandoffPolicyError,
    apply_handoff_plan,
    build_handoff_plan,
    render_handoff_plan_json,
    request_handoff_confirmation,
)
from agentgov.development_session import (
    SessionPolicyError,
    apply_start_plan,
    build_start_plan,
    load_active_session,
)
from agentgov.event_store import append_governance_event, load_governance_events
from agentgov.initializer import initialize_project
from agentgov.next_action import select_next_action


def run_git(repository: Path, *args: str) -> str:
    completed = subprocess.run(
        ("git", "-C", str(repository), *args),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        raise AssertionError(completed.stderr.decode("utf-8", errors="replace"))
    return completed.stdout.decode("utf-8", errors="replace").strip()


def write(repository: Path, relative: str, content: str) -> Path:
    path = repository.joinpath(*relative.split("/"))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def task_document(task_id: str) -> dict[str, object]:
    return {
        "contract": "agentgov.development-task",
        "schema_version": "1.1",
        "profile": "compact",
        "task_id": task_id,
        "title": f"Develop {task_id}",
        "requirement": {
            "summary": "Change and validate only the admitted fixture source paths.",
            "source_refs": [],
        },
        "scope": {
            "include_paths": ["src", f"governance/tasks/{task_id}.json"],
            "exclude_paths": [],
        },
        "acceptance_signals": ["The fixture validation command passes."],
        "validation_commands": [f'"{sys.executable}" -c "print(\'handoff-pass\')"'],
        "owner": "Fixture owner",
        "risk": {"level": "low", "items": []},
        "decision": {
            "state": "admitted",
            "decided_by": "Fixture owner",
            "rationale": "The fixture owner admits this task.",
        },
    }


def create_verified_repository(parent: Path, *, tasks: int = 1) -> tuple[Path, list[Path]]:
    repository = parent / "repository"
    repository.mkdir()
    initialize_project(repository, project_name="Handoff Fixture", dry_run=False)
    run_git(repository, "init", "--quiet")
    run_git(repository, "config", "user.email", "fixture@example.invalid")
    run_git(repository, "config", "user.name", "Fixture Author")
    write(repository, "pyproject.toml", "[project]\nname='fixture'\nversion='0.0.0'\n")
    write(repository, "tests/test_fixture.py", "# fixture\n")
    write(repository, "src/app.py", "VALUE = 1\n")
    task_paths: list[Path] = []
    for index in range(tasks):
        task_id = "handoff-task" if index == 0 else f"handoff-task-{index + 1}"
        task_paths.append(
            write(
                repository,
                f"governance/tasks/{task_id}.json",
                json.dumps(task_document(task_id), indent=2) + "\n",
            )
        )
    run_git(repository, "add", ".")
    run_git(repository, "commit", "--quiet", "-m", "baseline")
    session = apply_start_plan(build_start_plan(repository, task=task_paths[0])).session
    write(repository, "src/app.py", "VALUE = 2\n")
    validation = run_task_validation(
        task_paths[0],
        repository=repository,
        comparison_base=session.comparison_base_sha,
    )
    completion = reconcile_task_completion(
        task_paths[0],
        repository=repository,
        evidence_path=Path(validation.evidence_ref),
    )
    if completion.state != "verified":
        raise AssertionError(completion)
    return repository, task_paths


def run_cli(*args: str) -> tuple[int, str, str]:
    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        code = main(list(args))
    return code, stdout.getvalue(), stderr.getvalue()


class InteractiveInput(io.StringIO):
    def isatty(self) -> bool:
        return True


@unittest.skipUnless(shutil.which("git"), "Git is required for handoff fixtures")
class DevelopmentHandoffTests(unittest.TestCase):
    def test_preview_is_read_only_and_names_one_append_only_target(self) -> None:
        with TemporaryDirectory() as temp_dir:
            repository, _ = create_verified_repository(Path(temp_dir))
            pointer = repository / ".agentgov/current-task.json"
            pointer_before = pointer.read_bytes()
            events_before = tuple((repository / ".agentgov/events").glob("*.json"))

            plan = build_handoff_plan(repository, actor_label="fixture-owner")
            payload = json.loads(render_handoff_plan_json(plan))

            self.assertEqual(pointer.read_bytes(), pointer_before)
            self.assertEqual(tuple((repository / ".agentgov/events").glob("*.json")), events_before)

        self.assertEqual(payload["action"], "handoff")
        self.assertEqual(payload["targets"], [plan.event_target])
        self.assertEqual(payload["retained"][0], ".agentgov/current-task.json")
        self.assertTrue(payload["verified_evidence_ref"].startswith(".agentgov/evidence/"))
        self.assertTrue(all(value is False for value in payload["authority_boundary"].values()))

    def test_confirmation_requires_exact_word_and_real_terminal(self) -> None:
        with TemporaryDirectory() as temp_dir:
            repository, _ = create_verified_repository(Path(temp_dir))
            plan = build_handoff_plan(repository)

        self.assertFalse(request_handoff_confirmation(plan, decision_reader=lambda _: "HANDOFF", is_interactive_terminal=False))
        self.assertFalse(request_handoff_confirmation(plan, decision_reader=lambda _: "handoff", is_interactive_terminal=True))
        self.assertTrue(request_handoff_confirmation(plan, decision_reader=lambda _: "HANDOFF", is_interactive_terminal=True))

    def test_apply_preserves_pointer_and_is_idempotent(self) -> None:
        with TemporaryDirectory() as temp_dir:
            repository, _ = create_verified_repository(Path(temp_dir))
            pointer = repository / ".agentgov/current-task.json"
            pointer_before = pointer.read_bytes()
            plan = build_handoff_plan(repository, actor_label="fixture-owner")
            first = apply_handoff_plan(plan)
            raced = apply_handoff_plan(plan)
            repeated_plan = build_handoff_plan(repository)
            second = apply_handoff_plan(repeated_plan)
            events = load_governance_events(repository / ".agentgov/events").events

            self.assertEqual(pointer.read_bytes(), pointer_before)

        handoffs = [event for event in events if event.event_type == "session.handed_off"]
        self.assertEqual(len(handoffs), 1)
        self.assertEqual(handoffs[0].schema_version, "1.2")
        self.assertEqual(handoffs[0].outcome, "handed_off")
        self.assertEqual(handoffs[0].actor, {"class": "human", "label": "fixture-owner"})
        self.assertTrue(all(value is False for value in handoffs[0].authority_boundary.values()))
        self.assertFalse(first.already_handed_off)
        self.assertTrue(raced.already_handed_off)
        self.assertTrue(second.already_handed_off)
        self.assertEqual(first.event_ref, raced.event_ref)
        self.assertEqual(first.event_ref, second.event_ref)
        self.assertEqual(repeated_plan.targets, ())

    def test_stale_preview_and_later_progress_write_no_handoff(self) -> None:
        with TemporaryDirectory() as temp_dir:
            repository, _ = create_verified_repository(Path(temp_dir))
            plan = build_handoff_plan(repository)
            write(repository, "src/app.py", "VALUE = 3\n")
            with self.assertRaisesRegex(HandoffPolicyError, "no longer fresh"):
                apply_handoff_plan(plan)
            events_after_stale = load_governance_events(repository / ".agentgov/events").events

        self.assertFalse(any(event.event_type == "session.handed_off" for event in events_after_stale))

        with TemporaryDirectory() as temp_dir:
            repository, _ = create_verified_repository(Path(temp_dir))
            session = load_active_session(repository)
            assert session is not None
            append_governance_event(
                repository,
                event_type="scope.checked",
                actor_class="coding_agent",
                actor_label=None,
                task_id=session.task_id,
                task_digest=session.task_digest,
                outcome="passed",
                evidence_ref=None,
            )
            with self.assertRaisesRegex(HandoffPolicyError, "latest current-session event"):
                build_handoff_plan(repository)

    def test_cli_dry_run_cancel_exact_confirmation_and_json_boundary(self) -> None:
        with TemporaryDirectory() as temp_dir:
            repository, _ = create_verified_repository(Path(temp_dir))
            dry_code, dry_stdout, dry_stderr = run_cli(
                "govern", "handoff", "--repository", str(repository), "--dry-run"
            )
            cancel_code, cancel_stdout, cancel_stderr = run_cli(
                "govern", "handoff", "--repository", str(repository)
            )
            json_code, json_stdout, json_stderr = run_cli(
                "govern", "handoff", "--repository", str(repository),
                "--dry-run", "--format", "json",
            )
            monitor_code, monitor_stdout, monitor_stderr = run_cli(
                "monitor", "development", str(repository)
            )
            with patch.object(sys, "stdin", InteractiveInput("HANDOFF\n")):
                apply_code, apply_stdout, apply_stderr = run_cli(
                    "govern", "handoff", "--repository", str(repository)
                )
            handoffs = [
                event for event in load_governance_events(repository / ".agentgov/events").events
                if event.event_type == "session.handed_off"
            ]

        self.assertEqual(dry_code, EXIT_PASS)
        self.assertIn("DRY_RUN no files were written", dry_stdout)
        self.assertEqual(dry_stderr, "")
        self.assertEqual(cancel_code, EXIT_FAIL)
        self.assertIn("CANCELLED", cancel_stdout)
        self.assertEqual(cancel_stderr, "")
        self.assertEqual(json_code, EXIT_PASS)
        self.assertEqual(json.loads(json_stdout)["action"], "handoff")
        self.assertEqual(json_stderr, "")
        self.assertEqual(monitor_code, EXIT_PASS)
        self.assertIn("NEXT agentgov govern handoff", monitor_stdout)
        self.assertIn("does not prove review", monitor_stdout)
        self.assertEqual(monitor_stderr, "")
        self.assertEqual(apply_code, EXIT_PASS)
        self.assertIn("HANDED_OFF handoff-task", apply_stdout)
        self.assertEqual(apply_stderr, "")
        self.assertEqual(len(handoffs), 1)

    def test_next_rollover_handles_zero_one_and_many_without_restarting_digest(self) -> None:
        for task_count in (1, 2, 3):
            with self.subTest(task_count=task_count), TemporaryDirectory() as temp_dir:
                repository, tasks = create_verified_repository(Path(temp_dir), tasks=task_count)
                handed_digest = build_handoff_plan(repository).session.task_digest
                apply_handoff_plan(build_handoff_plan(repository))

                action = select_next_action(repository)

                self.assertEqual(action.source_check_id, "development-session:handed-off")
                self.assertIn("--replace-active", action.command or "")
                self.assertIn("--dry-run", action.command or "")
                if task_count == 1:
                    self.assertIn('"<TASK_TITLE>"', action.command or "")
                    self.assertIn('"<PATH>"', action.command or "")
                elif task_count == 2:
                    self.assertIn(str(tasks[1].resolve()), action.command or "")
                    self.assertNotIn(str(tasks[0].resolve()), action.command or "")
                else:
                    self.assertIn('"<TASK_JSON>"', action.command or "")
                    self.assertNotIn(str(tasks[1]), action.command or "")
                    self.assertNotIn(str(tasks[2]), action.command or "")

                with self.assertRaisesRegex(SessionPolicyError, "already handed off"):
                    build_start_plan(repository, task=tasks[0], replace_active=True)
                changed = json.loads(tasks[0].read_text(encoding="utf-8"))
                changed["title"] = "Reviewed changed task version"
                tasks[0].write_text(json.dumps(changed, indent=2) + "\n", encoding="utf-8")
                replacement = build_start_plan(repository, task=tasks[0], replace_active=True)
                self.assertNotEqual(replacement.session.task_digest, handed_digest)
                self.assertTrue(replacement.replace_active)

    def test_handoff_before_verified_completion_fails_closed(self) -> None:
        with TemporaryDirectory() as temp_dir:
            repository = Path(temp_dir) / "repository"
            repository.mkdir()
            initialize_project(repository, project_name="No Completion", dry_run=False)
            run_git(repository, "init", "--quiet")
            run_git(repository, "config", "user.email", "fixture@example.invalid")
            run_git(repository, "config", "user.name", "Fixture Author")
            task = write(
                repository,
                "governance/tasks/no-completion.json",
                json.dumps(task_document("no-completion"), indent=2) + "\n",
            )
            write(repository, "src/app.py", "VALUE = 1\n")
            run_git(repository, "add", ".")
            run_git(repository, "commit", "--quiet", "-m", "baseline")
            apply_start_plan(build_start_plan(repository, task=task))

            code, stdout, stderr = run_cli(
                "govern", "handoff", "--repository", str(repository), "--dry-run"
            )

        self.assertEqual(code, EXIT_ERROR)
        self.assertEqual(stdout, "")
        self.assertIn("run govern finish", stderr)


if __name__ == "__main__":
    unittest.main()
