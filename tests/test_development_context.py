import contextlib
import io
import json
import shutil
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from agentgov.cli import EXIT_FAIL, EXIT_PASS, main
from agentgov.development_context import (
    CONTEXT_CONTRACT,
    CONTEXT_SCHEMA_VERSION,
    ContextPolicyError,
    render_development_context_json,
    render_development_context_markdown,
    render_development_context_terminal,
    select_development_context,
)


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "governance/fixtures/context/valid-repository"
TASK = FIXTURE / "governance/tasks/compact-task.json"
SCHEMA = ROOT / "schemas/development-context.schema.json"


def run_cli(*args: str) -> tuple[int, str, str]:
    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        exit_code = main(list(args))
    return exit_code, stdout.getvalue(), stderr.getvalue()


def fixture_snapshot(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


class DevelopmentContextTests(unittest.TestCase):
    def test_schema_is_strict_and_denies_mutating_authority(self) -> None:
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))

        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(schema["properties"]["contract"]["const"], CONTEXT_CONTRACT)
        self.assertEqual(
            schema["properties"]["schema_version"]["const"],
            CONTEXT_SCHEMA_VERSION,
        )
        authority = schema["properties"]["authority_boundary"]
        self.assertFalse(authority["additionalProperties"])
        for value in authority["properties"].values():
            self.assertIs(value["const"], False)

    def test_compact_task_selects_only_declared_and_related_governance(self) -> None:
        context = select_development_context(TASK, repository=FIXTURE)
        selected = {item.path: item for item in context.selected_governance}

        self.assertEqual(context.task_id, "fixture-app-change")
        self.assertEqual(context.task_profile, "compact")
        self.assertEqual(
            context.active_triggers,
            ("task.admitted", "architecture.candidate"),
        )
        for path in (
            "AGENTS.md",
            "AI_CONTEXT.md",
            "docs/requirement.md",
            "docs/adr/0001-app-boundary.md",
            "docs/adr/INVARIANTS.md",
            "agent-skills/development-slice/SKILL.md",
            "agent-skills/context-first-review/SKILL.md",
            "governance/capabilities/example-app.json",
            "governance/controls/example-app.json",
            "governance/dependencies/example-app.json",
            "governance/tasks/compact-task.json",
        ):
            self.assertIn(path, selected)
        self.assertNotIn("docs/other.md", selected)
        self.assertEqual(
            selected["agent-skills/development-slice/SKILL.md"].selection_mode,
            "required",
        )
        architecture_skill = selected[
            "agent-skills/context-first-review/SKILL.md"
        ]
        self.assertEqual(architecture_skill.selection_mode, "advisory_candidate")
        self.assertEqual(architecture_skill.classification, "advisory")
        self.assertEqual(
            selected["governance/capabilities/example-app.json"].selection_mode,
            "path_match",
        )
        self.assertEqual(context.registry_summary["skill"], 2)
        self.assertTrue(all(value is False for value in context.authority_boundary.values()))

    def test_serializations_are_stable_and_keep_reason_content_and_limits(self) -> None:
        first = select_development_context(TASK, repository=FIXTURE)
        second = select_development_context(TASK, repository=FIXTURE)

        first_json = render_development_context_json(first)
        self.assertEqual(first_json, render_development_context_json(second))
        payload = json.loads(first_json)
        self.assertEqual(payload["contract"], CONTEXT_CONTRACT)
        self.assertTrue(payload["selected_governance"][0]["reason"])
        self.assertEqual(payload["content_mode"], "references")
        self.assertIsNone(payload["selected_governance"][0]["content"])
        self.assertFalse(payload["selected_governance"][0]["content_included"])
        self.assertIn("architecture candidates remain advisory", payload["known_limits"])

        embedded = json.loads(
            render_development_context_json(first, include_content=True)
        )
        self.assertEqual(embedded["content_mode"], "embedded")
        self.assertTrue(embedded["selected_governance"][0]["content_included"])
        self.assertIsInstance(embedded["selected_governance"][0]["content"], str)

        markdown = render_development_context_markdown(first)
        self.assertIn("# Development context: fixture-app-change", markdown)
        self.assertIn("## Selected governance", markdown)
        self.assertIn("Content mode: `references`", markdown)
        self.assertNotIn("~~~~text", markdown)
        embedded_markdown = render_development_context_markdown(
            first,
            include_content=True,
        )
        self.assertIn("~~~~text", embedded_markdown)
        terminal = render_development_context_terminal(first)
        self.assertIn("SELECT advisory_candidate advisory skill:", terminal)
        self.assertIn("did not authorize implementation", terminal)

    def test_selection_does_not_modify_the_fixture_repository(self) -> None:
        before = fixture_snapshot(FIXTURE)

        select_development_context(TASK, repository=FIXTURE)

        self.assertEqual(fixture_snapshot(FIXTURE), before)

    def test_non_admitted_task_is_not_eligible_for_context(self) -> None:
        with TemporaryDirectory() as temp_dir:
            repository = Path(temp_dir) / "repository"
            shutil.copytree(FIXTURE, repository)
            task = repository / "governance/tasks/compact-task.json"
            document = json.loads(task.read_text(encoding="utf-8"))
            document["decision"]["state"] = "draft"
            task.write_text(
                json.dumps(document, indent=2) + "\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ContextPolicyError, "requires an admitted task"):
                select_development_context(task, repository=repository)

    def test_cli_json_is_pure_and_draft_is_a_policy_failure(self) -> None:
        exit_code, stdout, stderr = run_cli(
            "context",
            "task",
            str(TASK),
            "--repository",
            str(FIXTURE),
            "--format",
            "json",
        )

        self.assertEqual(exit_code, EXIT_PASS)
        self.assertEqual(json.loads(stdout)["task_id"], "fixture-app-change")
        self.assertEqual(json.loads(stdout)["content_mode"], "references")
        self.assertEqual(stderr, "")

        with TemporaryDirectory() as temp_dir:
            repository = Path(temp_dir) / "repository"
            shutil.copytree(FIXTURE, repository)
            task = repository / "governance/tasks/compact-task.json"
            document = json.loads(task.read_text(encoding="utf-8"))
            document["decision"]["state"] = "paused"
            task.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")

            exit_code, stdout, stderr = run_cli(
                "context",
                "task",
                str(task),
                "--repository",
                str(repository),
            )

        self.assertEqual(exit_code, EXIT_FAIL)
        self.assertIn("FAIL context task:", stdout)
        self.assertIn("requires an admitted task", stdout)
        self.assertEqual(stderr, "")


if __name__ == "__main__":
    unittest.main()
