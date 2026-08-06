from __future__ import annotations

import contextlib
import io
import json
import shutil
import subprocess
import sys
import tomllib
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from agentgov.cli import EXIT_ERROR, EXIT_FAIL, EXIT_PASS, main
from agentgov.codex_hooks import (
    CODEX_HOOKS_PATH,
    CodexHookPolicyError,
    CodexHooksAction,
    CodexHooksIntegrationError,
    apply_codex_hooks_plan,
    codex_hook_from_payload,
    plan_codex_hooks_integration,
    process_codex_hook,
    render_codex_hook_output,
    render_codex_hooks_config,
    render_codex_hooks_plan_json,
    request_codex_hooks_confirmation,
)
from agentgov.development_session import (
    apply_start_plan,
    build_compact_task,
    build_start_plan,
)
from agentgov.event_store import load_governance_events
from agentgov.initializer import initialize_project


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
    return completed.stdout.decode("utf-8", errors="replace").strip()


def create_repository(parent: Path, *, active_task: bool) -> Path:
    root = parent / "repository"
    root.mkdir()
    initialize_project(root, project_name="Codex Hooks Fixture", dry_run=False)
    run_git(root, "init", "--quiet")
    run_git(root, "config", "user.email", "fixture@example.invalid")
    run_git(root, "config", "user.name", "Fixture Author")
    (root / "README.md").write_text("# Fixture\n", encoding="utf-8")
    task_path = root / "governance/tasks/codex-hooks-fixture.json"
    if active_task:
        task_path.parent.mkdir(parents=True, exist_ok=True)
        document = build_compact_task(
            title="Exercise Codex lifecycle hooks",
            task_id="codex-hooks-fixture",
            requirement="Exercise the packaged Codex lifecycle hook Adapter.",
            include_paths=("README.md",),
            exclude_paths=(),
            validation_commands=("git --version",),
            owner="Fixture owner",
        )
        task_path.write_text(
            json.dumps(document, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    run_git(root, "add", ".")
    run_git(root, "commit", "--quiet", "-m", "baseline")
    if active_task:
        apply_start_plan(
            build_start_plan(
                root,
                task=task_path,
            )
        )
    return root


def hook_payload(root: Path, event_name: str, *, stop_hook_active: bool = False) -> dict:
    payload = {
        "session_id": "thr-private-session-123",
        "transcript_path": str(root / ".codex/private-rollout.jsonl"),
        "cwd": str(root),
        "hook_event_name": event_name,
        "model": "private-model-slug",
        "permission_mode": "default",
    }
    if event_name == "SessionStart":
        payload["source"] = "startup"
    else:
        payload["turn_id"] = "turn-private-456"
    if event_name == "UserPromptSubmit":
        payload["prompt"] = "TOP SECRET USER PROMPT"
    elif event_name == "PostToolUse":
        payload.update(
            {
                "tool_name": "apply_patch",
                "tool_use_id": "call-private-789",
                "tool_input": {"command": "SECRET SOURCE PATCH"},
                "tool_response": {"output": "SECRET TOOL OUTPUT"},
            }
        )
    elif event_name == "PermissionRequest":
        payload.update(
            {
                "tool_name": "Bash",
                "tool_input": {
                    "command": "SECRET ESCALATED COMMAND",
                    "description": "SECRET APPROVAL REASON",
                },
            }
        )
    elif event_name == "Stop":
        payload["stop_hook_active"] = stop_hook_active
        payload["last_assistant_message"] = "SECRET ASSISTANT MESSAGE"
    return payload


def run_cli_with_stdin(stdin_text: str, *args: str) -> tuple[int, str, str]:
    stdout = io.StringIO()
    stderr = io.StringIO()
    with (
        patch.object(sys, "stdin", io.StringIO(stdin_text)),
        contextlib.redirect_stdout(stdout),
        contextlib.redirect_stderr(stderr),
    ):
        code = main(list(args))
    return code, stdout.getvalue(), stderr.getvalue()


@unittest.skipUnless(shutil.which("git"), "Git is required for Codex hook fixtures")
class CodexHookAdapterTests(unittest.TestCase):
    def test_hook_identity_is_hashed_and_sensitive_values_are_discarded(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = create_repository(Path(temp_dir), active_task=False)
            payload = hook_payload(root, "UserPromptSubmit")

            envelope, selected = codex_hook_from_payload(payload, repository=root)
            rendered = json.dumps(envelope.__dict__)

        self.assertEqual(selected, root.resolve())
        self.assertRegex(envelope.event_id, r"^evt-[0-9a-f]{32}$")
        self.assertRegex(envelope.correlation_id, r"^codex-[0-9a-f]{32}$")
        self.assertEqual(envelope.actor_class, "human")
        self.assertEqual(
            envelope.discarded_fields,
            ("model", "prompt", "transcript_path"),
        )
        self.assertNotIn("TOP SECRET", rendered)
        self.assertNotIn(str(root), rendered)
        self.assertNotIn("thr-private", rendered)

    def test_session_start_returns_task_context_without_host_data(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = create_repository(Path(temp_dir), active_task=True)

            result = process_codex_hook(
                hook_payload(root, "SessionStart"), repository=root
            )
            output = render_codex_hook_output(result)

        self.assertEqual(result.status, "processed")
        self.assertEqual(result.response.card.kind, "task")
        self.assertEqual(
            result.output["hookSpecificOutput"]["hookEventName"], "SessionStart"
        )
        self.assertIn("AgentGov status", output)
        self.assertNotIn("private-model", output)
        self.assertNotIn("private-rollout", output)

    def test_user_prompt_requests_routing_without_forcing_every_prompt_through_admission(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = create_repository(Path(temp_dir), active_task=False)
            payload = hook_payload(root, "UserPromptSubmit")

            result = process_codex_hook(payload, repository=root)
            output = render_codex_hook_output(result)

        self.assertEqual(result.status, "routing_context")
        self.assertIsNone(result.response)
        self.assertIn("agentgov.work-request 1.0", output)
        self.assertIn("need no task and zero confirmation", output)
        self.assertIn("Before a new repository change", output)
        self.assertNotIn(payload["prompt"], output)
        self.assertNotIn("thr-private-session", output)

    def test_post_tool_no_change_is_ignored_without_repeated_scope_event(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = create_repository(Path(temp_dir), active_task=True)
            before = load_governance_events(root / ".agentgov/events").events

            result = process_codex_hook(
                hook_payload(root, "PostToolUse"), repository=root
            )
            after = load_governance_events(root / ".agentgov/events").events

        self.assertEqual(result.status, "ignored_no_change")
        self.assertEqual(result.output, {})
        self.assertIsNone(result.response)
        self.assertEqual(len(after), len(before))

    def test_post_tool_scope_failure_does_not_claim_completed_action_was_undone(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = create_repository(Path(temp_dir), active_task=True)
            (root / "OUTSIDE.md").write_text("outside\n", encoding="utf-8")
            payload = hook_payload(root, "PostToolUse")

            result = process_codex_hook(payload, repository=root)
            output = render_codex_hook_output(result)

        self.assertEqual(result.response.cycle.status, "blocked")
        self.assertEqual(result.output["decision"], "block")
        self.assertIn("was not undone", result.output["reason"])
        self.assertNotIn("SECRET SOURCE PATCH", output)
        self.assertNotIn("SECRET TOOL OUTPUT", output)

    def test_stop_runs_completion_once_and_repeat_stop_cannot_loop(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = create_repository(Path(temp_dir), active_task=True)
            (root / "README.md").write_text("# Fixture\n\nCompleted.\n", encoding="utf-8")

            first = process_codex_hook(hook_payload(root, "Stop"), repository=root)
            event_count = len(load_governance_events(root / ".agentgov/events").events)
            repeat = process_codex_hook(
                hook_payload(root, "Stop", stop_hook_active=True),
                repository=root,
            )
            repeat_count = len(load_governance_events(root / ".agentgov/events").events)

        self.assertEqual(first.response.cycle.status, "review_ready")
        self.assertTrue(first.output["continue"])
        self.assertNotIn("SECRET ASSISTANT MESSAGE", render_codex_hook_output(first))
        self.assertEqual(repeat.status, "ignored_repeat_stop")
        self.assertEqual(repeat.output, {"continue": True})
        self.assertIsNone(repeat.response)
        self.assertEqual(repeat_count, event_count)

    def test_hook_rejects_repository_mismatch_and_invalid_event_shape(self) -> None:
        with TemporaryDirectory() as first_dir, TemporaryDirectory() as second_dir:
            first = create_repository(Path(first_dir), active_task=False)
            second = create_repository(Path(second_dir), active_task=False)
            mismatch = hook_payload(first, "SessionStart")
            invalid = hook_payload(first, "Stop")
            invalid["stop_hook_active"] = "false"

            with self.assertRaises(CodexHookPolicyError):
                codex_hook_from_payload(mismatch, repository=second)
            with self.assertRaises(CodexHookPolicyError):
                codex_hook_from_payload(invalid, repository=first)

    def test_permission_request_preserves_native_human_prompt_without_deciding(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = create_repository(Path(temp_dir), active_task=True)
            before = load_governance_events(root / ".agentgov/events").events

            result = process_codex_hook(
                hook_payload(root, "PermissionRequest"), repository=root
            )
            output = render_codex_hook_output(result)
            after = load_governance_events(root / ".agentgov/events").events

        self.assertEqual(result.status, "delegated_native_permission")
        self.assertIsNone(result.response)
        self.assertNotIn("decision", result.output)
        self.assertNotIn("behavior", output)
        self.assertIn("normal human approval flow", output)
        self.assertIn("does not admit task scope", output)
        self.assertNotIn("SECRET", output)
        self.assertEqual(after, before)

    def test_cli_emits_only_codex_hook_json_and_redacts_rejected_input(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = create_repository(Path(temp_dir), active_task=False)
            payload = hook_payload(root, "UserPromptSubmit")
            code, stdout, stderr = run_cli_with_stdin(
                json.dumps(payload), "adapter", "codex-hook", str(root)
            )
            bad_code, bad_stdout, bad_stderr = run_cli_with_stdin(
                '{"prompt":"TOP SECRET"}', "adapter", "codex-hook", str(root)
            )

        self.assertEqual(code, EXIT_PASS)
        self.assertEqual(stderr, "")
        self.assertIsInstance(json.loads(stdout), dict)
        self.assertNotIn(payload["prompt"], stdout)
        self.assertEqual(bad_code, EXIT_ERROR)
        self.assertEqual(bad_stdout, "")
        self.assertNotIn("TOP SECRET", bad_stderr)


@unittest.skipUnless(shutil.which("git"), "Git is required for Codex hook fixtures")
class CodexHooksIntegrationTests(unittest.TestCase):
    def test_rendered_config_matches_packaged_template_and_official_hook_surface(self) -> None:
        rendered = render_codex_hooks_config()
        template = (ROOT / "templates/codex-hooks.template.json").read_text(
            encoding="utf-8"
        )
        payload = json.loads(rendered)

        self.assertEqual(rendered, template)
        self.assertEqual(
            set(payload["hooks"]),
            {
                "SessionStart",
                "UserPromptSubmit",
                "PermissionRequest",
                "PostToolUse",
                "Stop",
            },
        )
        self.assertEqual(
            payload["hooks"]["SessionStart"][0]["matcher"],
            "startup|resume|clear|compact",
        )
        self.assertNotIn("dangerously-bypass-hook-trust", rendered)
        self.assertNotIn('"behavior": "allow"', rendered)
        self.assertNotIn('"behavior": "deny"', rendered)
        self.assertTrue(
            all(
                hook["command"] == "agentgov adapter codex-hook"
                for groups in payload["hooks"].values()
                for group in groups
                for hook in group["hooks"]
            )
        )
        package = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
        packaged_templates = package["tool"]["setuptools"]["data-files"][
            "share/agent-governance-starter/templates"
        ]
        self.assertIn("templates/*.template.json", packaged_templates)

    def test_plan_is_create_preserve_or_conflict_without_overwrite(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = create_repository(Path(temp_dir), active_task=False)
            create = plan_codex_hooks_integration(root)
            result = apply_codex_hooks_plan(create)
            preserve = plan_codex_hooks_integration(root)
            target = root / CODEX_HOOKS_PATH
            target.write_text('{"custom": true}\n', encoding="utf-8")
            conflict = plan_codex_hooks_integration(root)

        self.assertIs(create.action, CodexHooksAction.CREATE)
        self.assertEqual(result.created_files, (CODEX_HOOKS_PATH,))
        self.assertIs(preserve.action, CodexHooksAction.PRESERVE)
        self.assertIs(conflict.action, CodexHooksAction.CONFLICT)
        self.assertIn("will not be overwritten or merged", conflict.reason)

    def test_apply_revalidates_exclusive_target_and_confirmation_is_exact(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = create_repository(Path(temp_dir), active_task=False)
            plan = plan_codex_hooks_integration(root)
            target = root / CODEX_HOOKS_PATH
            target.parent.mkdir(parents=True)
            target.write_text("appeared\n", encoding="utf-8")

            with self.assertRaises(CodexHooksIntegrationError):
                apply_codex_hooks_plan(plan)

        self.assertTrue(
            request_codex_hooks_confirmation(
                plan,
                decision_reader=lambda _: "INTEGRATE",
                is_interactive_terminal=True,
            )
        )
        self.assertFalse(
            request_codex_hooks_confirmation(
                plan,
                decision_reader=lambda _: "integrate",
                is_interactive_terminal=True,
            )
        )
        self.assertFalse(
            request_codex_hooks_confirmation(
                plan,
                decision_reader=lambda _: "INTEGRATE",
                is_interactive_terminal=False,
            )
        )

    def test_json_preview_denies_write_trust_plugin_and_git_authority(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = create_repository(Path(temp_dir), active_task=False)
            plan = plan_codex_hooks_integration(root)
            payload = json.loads(
                render_codex_hooks_plan_json(plan, non_interactive=True)
            )
            schema = json.loads(
                (ROOT / "schemas/codex-hooks-integration-plan.schema.json").read_text(
                    encoding="utf-8"
                )
            )

        self.assertEqual(payload["mode"], "dry_run")
        self.assertEqual(payload["interaction"], "non_interactive")
        self.assertFalse(schema["additionalProperties"])
        self.assertTrue(all(value is False for value in payload["authority_boundary"].values()))

    def test_cli_dry_run_is_read_only_and_existing_custom_hooks_fail(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = create_repository(Path(temp_dir), active_task=False)
            code, stdout, stderr = run_cli_with_stdin(
                "",
                "integrate",
                "codex-hooks",
                str(root),
                "--dry-run",
            )
            target = root / CODEX_HOOKS_PATH
            target.parent.mkdir(parents=True)
            target.write_text('{"custom": true}\n', encoding="utf-8")
            conflict_code, conflict_stdout, conflict_stderr = run_cli_with_stdin(
                "",
                "integrate",
                "codex-hooks",
                str(root),
                "--dry-run",
            )

        self.assertEqual(code, EXIT_PASS)
        self.assertIn("CREATE .codex/hooks.json", stdout)
        self.assertIn("hook trust remains a separate user decision", stdout)
        self.assertEqual(stderr, "")
        self.assertEqual(conflict_code, EXIT_FAIL)
        self.assertIn("CONFLICT .codex/hooks.json", conflict_stdout)
        self.assertEqual(conflict_stderr, "")


if __name__ == "__main__":
    unittest.main()
