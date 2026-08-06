import contextlib
import io
import json
import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

from agentgov.cli import EXIT_ERROR, EXIT_FAIL, EXIT_PASS, main
from agentgov.task_contract import validate_development_task_document
from agentgov.task_proposal import (
    TASK_ADMISSION_PLAN_CONTRACT,
    TASK_PROPOSAL_CONTRACT,
    TaskProposalPolicyError,
    apply_task_admission_plan,
    build_task_admission_plan,
    canonical_proposal_digest,
    load_task_proposal,
    render_task_admission_plan_json,
    request_task_admission_confirmation,
    validate_task_proposal_document,
)


ROOT = Path(__file__).resolve().parents[1]


def proposal(task_id: str = "add-health-check") -> dict:
    return {
        "contract": "agentgov.task-proposal",
        "schema_version": "1.0",
        "proposal_id": "prp-0123456789abcdef0123456789abcdef",
        "source": {"adapter_id": "example-agent", "actor_class": "coding_agent"},
        "task": {
            "task_id": task_id,
            "title": "Add a bounded health check",
            "requirement_summary": "Expose one repository-local health check with deterministic tests.",
            "scope": {"include_paths": ["src", "tests"], "exclude_paths": ["release"]},
            "acceptance_signals": ["The health check and its focused tests pass."],
            "validation_commands": ["python -m unittest tests.test_health -v"],
            "owner": "Human product owner",
            "risk": {"level": "low", "items": ["A route name may already exist."]},
            "assumptions": ["The project already has an HTTP application."],
            "unknowns": ["The final route name still needs human review."],
        },
        "content_boundary": {
            "contains_raw_prompt": False,
            "contains_transcript": False,
            "contains_source_content": False,
            "contains_credentials": False,
            "contains_absolute_paths": False,
        },
        "authority_boundary": {
            "admits_task": False,
            "starts_session": False,
            "authorizes_code_change": False,
            "authorizes_scope_expansion": False,
            "authorizes_exception": False,
            "authorizes_git_operations": False,
            "authorizes_deployment": False,
            "authorizes_release": False,
        },
    }


def repository(path: Path) -> Path:
    (path / "governance/tasks").mkdir(parents=True)
    return path


def write_proposal(path: Path, value: dict) -> Path:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def run_cli(*args: str) -> tuple[int, str, str]:
    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        code = main(list(args))
    return code, stdout.getvalue(), stderr.getvalue()


class TaskProposalTests(unittest.TestCase):
    def test_contract_is_strict_low_risk_and_non_authoritative(self) -> None:
        value = proposal()

        self.assertEqual(validate_task_proposal_document(value), [])
        value["raw_prompt"] = "please copy the whole conversation"
        value["task"]["risk"]["level"] = "medium"
        value["authority_boundary"]["admits_task"] = True
        errors = validate_task_proposal_document(value)

        self.assertTrue(any("unsupported fields" in item for item in errors))
        self.assertIn("$.task.risk.level must equal 'low' for proposal admission", errors)
        self.assertIn("$.authority_boundary.admits_task must equal false", errors)

    def test_sensitive_or_host_local_content_fails_without_echoing_value(self) -> None:
        value = proposal()
        value["task"]["requirement_summary"] = "Use password=do-not-repeat-this in C:\\Users\\someone\\repo"

        errors = validate_task_proposal_document(value)
        rendered = "; ".join(errors)

        self.assertIn("sensitive or host-local content", rendered)
        self.assertNotIn("do-not-repeat-this", rendered)

    def test_terminal_control_and_multiline_command_content_is_rejected(self) -> None:
        value = proposal()
        value["task"]["validation_commands"] = [
            "python -m unittest tests.test_health\npython hidden.py"
        ]

        errors = validate_task_proposal_document(value)

        self.assertTrue(any("control characters" in item for item in errors))

    def test_load_is_bounded_and_returns_valid_copy(self) -> None:
        with TemporaryDirectory() as temp_dir:
            path = write_proposal(Path(temp_dir) / "proposal.json", proposal())
            before = path.read_bytes()
            loaded = load_task_proposal(path)

            loaded["task"]["title"] = "Changed only in memory"
            self.assertEqual(path.read_bytes(), before)
            self.assertNotEqual(loaded["task"]["title"], proposal()["task"]["title"])

    def test_preview_builds_exact_compact_task_and_preserves_uncertainty(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = repository(Path(temp_dir))
            value = proposal()
            plan = build_task_admission_plan(root, value)

            self.assertFalse((root / plan.target).exists())
            self.assertEqual(plan.target, "governance/tasks/add-health-check.json")
            self.assertEqual(plan.task_document["profile"], "compact")
            self.assertEqual(plan.task_document["decision"]["state"], "admitted")
            self.assertIn(plan.target, plan.task_document["scope"]["include_paths"])
            self.assertIn(
                "Reviewed assumption: The project already has an HTTP application.",
                plan.task_document["risk"]["items"],
            )
            self.assertIn(
                "Reviewed unknown: The final route name still needs human review.",
                plan.task_document["risk"]["items"],
            )
            self.assertEqual(validate_development_task_document(plan.task_document), [])
            payload = json.loads(render_task_admission_plan_json(plan))
            self.assertEqual(payload["contract"], TASK_ADMISSION_PLAN_CONTRACT)
            self.assertEqual(payload["proposal"]["contract"], TASK_PROPOSAL_CONTRACT)
            self.assertFalse(payload["authority_boundary"]["repository_modified"])
            self.assertFalse(payload["authority_boundary"]["task_admitted"])
            self.assertFalse(payload["authority_boundary"]["session_started"])

    def test_exact_admit_requires_an_interactive_terminal(self) -> None:
        with TemporaryDirectory() as temp_dir:
            plan = build_task_admission_plan(repository(Path(temp_dir)), proposal())

            self.assertFalse(
                request_task_admission_confirmation(
                    plan, decision_reader=lambda _: "ADMIT", is_interactive_terminal=False
                )
            )
            self.assertFalse(
                request_task_admission_confirmation(
                    plan, decision_reader=lambda _: "admit", is_interactive_terminal=True
                )
            )
            self.assertTrue(
                request_task_admission_confirmation(
                    plan, decision_reader=lambda _: "ADMIT", is_interactive_terminal=True
                )
            )

    def test_apply_creates_only_the_reviewed_task_without_starting_a_session(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = repository(Path(temp_dir))
            plan = build_task_admission_plan(root, proposal())
            result = apply_task_admission_plan(plan)

            target = root / result.target
            self.assertTrue(target.is_file())
            self.assertEqual(json.loads(target.read_text(encoding="utf-8")), plan.task_document)
            self.assertFalse((root / ".agentgov").exists())
            self.assertEqual(
                sorted(path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file()),
                [result.target],
            )

    def test_existing_or_raced_target_is_never_overwritten(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = repository(Path(temp_dir))
            plan = build_task_admission_plan(root, proposal())
            target = root / plan.target
            target.write_text("owned by someone else\n", encoding="utf-8")

            with self.assertRaisesRegex(TaskProposalPolicyError, "appeared after preview"):
                apply_task_admission_plan(plan)
            self.assertEqual(target.read_text(encoding="utf-8"), "owned by someone else\n")

    def test_plan_drift_fails_closed(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = repository(Path(temp_dir))
            plan = build_task_admission_plan(root, proposal())
            plan.task_document["title"] = "Changed after preview"

            with self.assertRaisesRegex(TaskProposalPolicyError, "changed after preview"):
                apply_task_admission_plan(plan)
            self.assertFalse((root / plan.target).exists())

    def test_existing_target_fails_during_preview(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = repository(Path(temp_dir))
            target = root / "governance/tasks/add-health-check.json"
            target.write_text("existing\n", encoding="utf-8")

            with self.assertRaisesRegex(TaskProposalPolicyError, "will not be overwritten"):
                build_task_admission_plan(root, proposal())
            self.assertEqual(target.read_text(encoding="utf-8"), "existing\n")

    def test_parent_symlink_cannot_redirect_task_outside_repository(self) -> None:
        with TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            root = base / "repository"
            outside = base / "outside"
            root.mkdir()
            (outside / "tasks").mkdir(parents=True)
            try:
                os.symlink(outside, root / "governance", target_is_directory=True)
            except OSError as exc:
                self.skipTest(f"directory symlinks are unavailable: {exc}")

            with self.assertRaisesRegex(TaskProposalPolicyError, "symbolic link"):
                build_task_admission_plan(root, proposal())
            self.assertEqual(list((outside / "tasks").iterdir()), [])

    def test_cli_dry_run_is_read_only_and_json_requires_dry_run(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = repository(Path(temp_dir))
            input_path = write_proposal(root / "proposal.json", proposal())
            before = input_path.read_bytes()
            code, stdout, stderr = run_cli(
                "propose", "task", str(input_path), "--repository", str(root), "--dry-run", "--format", "json"
            )
            rejected, rejected_stdout, rejected_stderr = run_cli(
                "propose", "task", str(input_path), "--repository", str(root), "--format", "json"
            )

            self.assertEqual(code, EXIT_PASS, stderr)
            self.assertEqual(json.loads(stdout)["action"], "create")
            self.assertEqual(input_path.read_bytes(), before)
            self.assertFalse((root / "governance/tasks/add-health-check.json").exists())
            self.assertEqual(rejected, EXIT_ERROR)
            self.assertEqual(rejected_stdout, "")
            self.assertIn("requires --dry-run", rejected_stderr)

    def test_cli_noninteractive_apply_cancels_without_writing(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = repository(Path(temp_dir))
            input_path = write_proposal(root / "proposal.json", proposal())
            with mock.patch("agentgov.cli.sys.stdin.isatty", return_value=False):
                code, stdout, stderr = run_cli(
                    "propose", "task", str(input_path), "--repository", str(root)
                )

            self.assertEqual(code, EXIT_FAIL)
            self.assertIn("CANCELLED", stdout)
            self.assertEqual(stderr, "")
            self.assertFalse((root / "governance/tasks/add-health-check.json").exists())

    def test_cli_interactive_exact_admit_creates_task_only(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = repository(Path(temp_dir))
            input_path = write_proposal(root / "proposal.json", proposal())
            with mock.patch("agentgov.cli.sys.stdin.isatty", return_value=True), mock.patch(
                "builtins.input", return_value="ADMIT"
            ):
                code, stdout, stderr = run_cli(
                    "propose", "task", str(input_path), "--repository", str(root)
                )

            self.assertEqual(code, EXIT_PASS, (stdout, stderr))
            self.assertIn("ADMITTED add-health-check", stdout)
            self.assertIn("did not start development", stdout)
            self.assertEqual(stderr, "")
            self.assertTrue((root / "governance/tasks/add-health-check.json").is_file())
            self.assertFalse((root / ".agentgov").exists())

    def test_schema_files_are_strict_and_match_contract_constants(self) -> None:
        proposal_schema = json.loads(
            (ROOT / "schemas/task-proposal.schema.json").read_text(encoding="utf-8")
        )
        plan_schema = json.loads(
            (ROOT / "schemas/task-admission-plan.schema.json").read_text(encoding="utf-8")
        )

        self.assertFalse(proposal_schema["additionalProperties"])
        self.assertEqual(proposal_schema["properties"]["contract"]["const"], TASK_PROPOSAL_CONTRACT)
        self.assertFalse(plan_schema["additionalProperties"])
        self.assertEqual(plan_schema["properties"]["contract"]["const"], TASK_ADMISSION_PLAN_CONTRACT)

    def test_digest_is_stable_across_key_order(self) -> None:
        value = proposal()
        reordered = {key: value[key] for key in reversed(tuple(value))}
        self.assertEqual(canonical_proposal_digest(value), canonical_proposal_digest(reordered))


if __name__ == "__main__":
    unittest.main()
