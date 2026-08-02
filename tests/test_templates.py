import re
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from agentgov.capability import load_capability_manifest, validate_capability_manifest
from agentgov.evaluation import EvaluationStatus, check_evaluation_bundle


ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "templates"


class GovernanceTemplateTests(unittest.TestCase):
    def test_expected_template_set_exists(self) -> None:
        expected = {
            "AGENTS.template.md",
            "ADR.template.md",
            "INVARIANTS.template.md",
            "prompt-capability.template.json",
            "evaluation-manifest.template.json",
            "development-task.template.json",
        }

        actual = {path.name for path in TEMPLATES.iterdir() if path.is_file()}

        self.assertTrue(expected.issubset(actual))

    def test_markdown_templates_are_free_of_reference_project_coupling(self) -> None:
        forbidden = {
            "ai radar",
            "ai-radar",
            "aws_profile",
            "s3://",
            "blocked_downstream_actions",
            "project takeaway",
        }

        for path in sorted(TEMPLATES.glob("*.md")):
            with self.subTest(template=path.name):
                text = path.read_text(encoding="utf-8").lower()
                for term in forbidden:
                    self.assertNotIn(term, text)

    def test_agents_template_contains_required_governance_boundaries(self) -> None:
        text = (TEMPLATES / "AGENTS.template.md").read_text(encoding="utf-8")
        required_headings = {
            "## Repository scope",
            "## Non-negotiable rules",
            "## Operating modes",
            "## Core-file approval gate",
            "## Worktree safety",
            "## Secrets and private-data boundary",
            "## External systems boundary",
            "## Validation",
            "## Human escalation",
            "## Trust hierarchy",
        }

        for heading in required_headings:
            self.assertIn(heading, text)
        self.assertIn("{{PROJECT_NAME}}", text)
        self.assertIn("{{PRIMARY_VALIDATION_COMMAND}}", text)

    def test_adr_template_preserves_decision_and_follow_up_contract(self) -> None:
        text = (TEMPLATES / "ADR.template.md").read_text(encoding="utf-8")
        for heading in (
            "## Decision gate",
            "## Context",
            "## Decision",
            "## Owns",
            "## Does not own",
            "## Consequences",
            "## Alternatives considered",
            "## Implementation plan",
            "## Validation",
            "## Rollback or replacement",
        ):
            self.assertIn(heading, text)

    def test_invariant_template_requires_authority_and_verification(self) -> None:
        text = (TEMPLATES / "INVARIANTS.template.md").read_text(encoding="utf-8")

        self.assertIn("- Authority: `{{ADR_OR_POLICY_REFERENCE}}`", text)
        self.assertIn("### Enforcement points", text)
        self.assertIn("### Verification", text)
        self.assertIn("### Failure response", text)
        self.assertIn("deterministic", text)
        self.assertIn("review", text)

    def test_markdown_placeholders_follow_one_portable_format(self) -> None:
        placeholder_pattern = re.compile(r"\{\{([A-Z][A-Z0-9_|-]*)\}\}")

        for path in sorted(TEMPLATES.glob("*.template.md")):
            with self.subTest(template=path.name):
                text = path.read_text(encoding="utf-8")
                placeholders = placeholder_pattern.findall(text)
                self.assertTrue(placeholders)
                scrubbed = placeholder_pattern.sub("", text)
                self.assertNotIn("{{", scrubbed)
                self.assertNotIn("}}", scrubbed)

    def test_prompt_capability_template_passes_the_contract(self) -> None:
        path = TEMPLATES / "prompt-capability.template.json"

        errors = validate_capability_manifest(load_capability_manifest(path))

        self.assertEqual(errors, [])

    def test_evaluation_template_is_an_honest_incomplete_start(self) -> None:
        with TemporaryDirectory() as temp_dir:
            bundle = Path(temp_dir)
            source = TEMPLATES / "evaluation-manifest.template.json"
            (bundle / "evaluation-manifest.json").write_text(
                source.read_text(encoding="utf-8"),
                encoding="utf-8",
            )

            result = check_evaluation_bundle(bundle)

        self.assertIs(result.status, EvaluationStatus.WARN)
        self.assertEqual(result.readiness, "needs_seed_cases")

    def test_development_task_template_is_an_honest_draft(self) -> None:
        from agentgov.task_contract import (
            load_development_task,
            validate_development_task_document,
        )

        task = load_development_task(TEMPLATES / "development-task.template.json")

        self.assertEqual(validate_development_task_document(task), [])
        self.assertEqual(task["profile"], "compact")
        self.assertEqual(task["decision"]["state"], "draft")
        self.assertEqual(task["requirement"]["source_refs"], [])
        self.assertNotIn("architecture_refs", task)
        self.assertEqual(len(task["validation_commands"]), 1)


if __name__ == "__main__":
    unittest.main()
