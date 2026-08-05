import contextlib
import io
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from agentgov.agent_skills import (
    check_agent_skills,
    read_agent_skill_metadata,
    validate_agent_skill,
)
from agentgov.cli import EXIT_ERROR, EXIT_FAIL, EXIT_PASS, main


ROOT = Path(__file__).resolve().parents[1]
AGENT_SKILLS = ROOT / "agent-skills"


def run_cli(*args: str) -> tuple[int, str, str]:
    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        exit_code = main(list(args))
    return exit_code, stdout.getvalue(), stderr.getvalue()


def valid_skill_text(name: str) -> str:
    return f"""---
name: {name}
description: Perform bounded work. Use when the workflow is needed. Do not use for unrelated tasks.
---

# Example

## Goal
Deliver one outcome.

## Required context
Read applicable instructions.

## Inputs
Use the request.

## Workflow
1. Inspect.
2. Act.

## Required checks
Validate behavior.

## Stop conditions
Stop on missing authority.

## Human escalation
State the required decision.

## Expected output
Report results and gaps.
"""


class AgentSkillContractTests(unittest.TestCase):
    def test_shipped_skills_pass_the_contract(self) -> None:
        report = check_agent_skills(AGENT_SKILLS)

        self.assertFalse(report.has_failures)
        self.assertEqual(len(report.findings), 7)

    def test_shipped_skills_own_structured_routing_metadata(self) -> None:
        metadata = {
            path.parent.name: read_agent_skill_metadata(path)
            for path in sorted(AGENT_SKILLS.glob("*/SKILL.md"))
        }

        self.assertEqual(metadata["development-slice"].triggers, ("task.admitted",))
        self.assertEqual(
            metadata["requirement-admission"].triggers,
            ("task.requested",),
        )
        self.assertEqual(
            metadata["action-loop-stagnation"].triggers,
            ("development.stagnation_suspected",),
        )
        self.assertEqual(
            metadata["reconcile-invariants"].triggers,
            ("completion.requested",),
        )
        self.assertEqual(
            metadata["context-first-review"].triggers,
            ("architecture.candidate",),
        )
        self.assertEqual(
            metadata["context-first-review"].applies_to,
            ("development_task",),
        )
        self.assertIn(
            "task.admitted",
            metadata["incident-response"].non_triggers,
        )

    def test_shipped_skills_are_free_of_reference_project_coupling(self) -> None:
        forbidden = {
            "ai radar",
            "ai-radar",
            "aws_profile",
            "s3://",
            "blocked_downstream_actions",
            "project takeaway",
        }

        for path in sorted(AGENT_SKILLS.glob("*/SKILL.md")):
            with self.subTest(skill=path.parent.name):
                text = path.read_text(encoding="utf-8").lower()
                for term in forbidden:
                    self.assertNotIn(term, text)

    def test_context_first_review_preserves_grounding_and_decision_semantics(self) -> None:
        text = (
            AGENT_SKILLS / "context-first-review" / "SKILL.md"
        ).read_text(encoding="utf-8")

        for required in (
            "observed facts",
            "supported inferences",
            "review judgments",
            "unresolved unknowns",
            "`go`, `modify`, or `no-go`",
            "Do not edit implementation or governance files",
        ):
            self.assertIn(required, text)

        output_labels = (
            "`Decision`",
            "`Grounded facts`",
            "`Conflicts`",
            "`Recommended shape`",
            "`Stop conditions`",
        )
        positions = [text.index(label) for label in output_labels]
        self.assertEqual(positions, sorted(positions))

    def test_requirement_admission_keeps_value_and_authority_human_owned(self) -> None:
        text = (
            AGENT_SKILLS / "requirement-admission" / "SKILL.md"
        ).read_text(encoding="utf-8")

        for required in (
            "why now",
            "smallest coherent slice",
            "trade-off",
            "human-owned",
            "`draft`, `admit`, `revise`, or `no-go`",
            "Only the accountable human may change the task to admitted.",
            "Do not begin implementation",
        ):
            self.assertIn(required, text)

    def test_stagnation_protocol_is_advisory_and_evidence_grounded(self) -> None:
        text = (
            AGENT_SKILLS / "action-loop-stagnation" / "SKILL.md"
        ).read_text(encoding="utf-8")

        for required in (
            "failure packet",
            "structurally different hypothesis",
            "verification oracle",
            "false completion",
            "not a mechanical runtime\n   halt",
            "grants no new authority",
        ):
            self.assertIn(required, text)

    def test_reconciliation_preserves_scope_and_human_decision(self) -> None:
        text = (
            AGENT_SKILLS / "reconcile-invariants" / "SKILL.md"
        ).read_text(encoding="utf-8")

        for required in (
            "scoped reconciliation",
            "observed facts",
            "supported inferences",
            "review judgments",
            "unresolved unknowns",
            "proposed diff",
            "Do not automatically rewrite",
            "pending-human-decision",
        ):
            self.assertIn(required, text)

    def test_incident_attribution_separates_learning_from_blame_and_operations(self) -> None:
        text = (
            AGENT_SKILLS / "incident-attribution" / "SKILL.md"
        ).read_text(encoding="utf-8")

        for stage in (
            "`problem_definition`",
            "`task_handoff`",
            "`reasoning_and_judgment`",
            "`execution`",
            "`verification`",
        ):
            self.assertIn(stage, text)
        for boundary in (
            "Do not assign blame or",
            "Do not promote one ordinary failure into a systemic pattern.",
            "authorization to edit, commit,",
            "Operational response and collaboration learning remain separate",
        ):
            self.assertIn(boundary, text)

    def test_extra_frontmatter_and_missing_heading_fail(self) -> None:
        with TemporaryDirectory() as temp_dir:
            skill_dir = Path(temp_dir) / "example-skill"
            skill_dir.mkdir()
            text = valid_skill_text("example-skill")
            text = text.replace("description:", "version: 1\ndescription:")
            text = text.replace("## Stop conditions", "## Pause conditions")
            path = skill_dir / "SKILL.md"
            path.write_text(text, encoding="utf-8")

            errors = validate_agent_skill(path)

        self.assertIn("frontmatter contains unsupported field(s): version", errors)
        self.assertIn("body is missing required heading: ## Stop conditions", errors)

    def test_invalid_routing_metadata_fails_deterministically(self) -> None:
        with TemporaryDirectory() as temp_dir:
            skill_dir = Path(temp_dir) / "example-skill"
            skill_dir.mkdir()
            text = valid_skill_text("example-skill").replace(
                "---\n\n# Example",
                'triggers: ["Task Admitted"]\nnon_triggers: []\napplies_to: []\n---\n\n# Example',
            )
            path = skill_dir / "SKILL.md"
            path.write_text(text, encoding="utf-8")

            errors = validate_agent_skill(path)

        self.assertTrue(any("portable routing identifier" in item for item in errors))
        self.assertIn(
            "routable skill frontmatter must declare at least one applies_to value",
            errors,
        )

    def test_frontmatter_name_must_match_directory(self) -> None:
        with TemporaryDirectory() as temp_dir:
            skill_dir = Path(temp_dir) / "expected-name"
            skill_dir.mkdir()
            path = skill_dir / "SKILL.md"
            path.write_text(valid_skill_text("different-name"), encoding="utf-8")

            errors = validate_agent_skill(path)

        self.assertIn("frontmatter name must match the skill directory name", errors)

    def test_empty_directory_is_a_policy_failure(self) -> None:
        with TemporaryDirectory() as temp_dir:
            report = check_agent_skills(Path(temp_dir))

        self.assertTrue(report.has_failures)
        self.assertEqual(report.findings[0].check_id, "agent-skills:directory")


class AgentSkillsCliTests(unittest.TestCase):
    def test_shipped_skills_return_pass(self) -> None:
        exit_code, stdout, stderr = run_cli("check", "agent-skills", str(AGENT_SKILLS))

        self.assertEqual(exit_code, EXIT_PASS)
        self.assertIn("PASS agent-skill:context-first-review:", stdout)
        self.assertIn("PASS agent-skill:development-slice:", stdout)
        self.assertIn("PASS agent-skill:requirement-admission:", stdout)
        self.assertIn("PASS agent-skill:action-loop-stagnation:", stdout)
        self.assertIn("PASS agent-skill:reconcile-invariants:", stdout)
        self.assertIn("PASS agent-skill:incident-attribution:", stdout)
        self.assertIn("PASS agent-skill:incident-response:", stdout)
        self.assertIn("SUMMARY PASS=7 FAIL=0", stdout)
        self.assertEqual(stderr, "")

    def test_invalid_skill_returns_fail(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill_dir = root / "bad-skill"
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text("# no frontmatter\n", encoding="utf-8")

            exit_code, stdout, stderr = run_cli("check", "agent-skills", str(root))

        self.assertEqual(exit_code, EXIT_FAIL)
        self.assertIn("FAIL agent-skill:bad-skill:", stdout)
        self.assertIn("SUMMARY PASS=0 FAIL=1", stdout)
        self.assertEqual(stderr, "")

    def test_missing_path_returns_operational_error(self) -> None:
        with TemporaryDirectory() as temp_dir:
            missing = Path(temp_dir) / "missing"

            exit_code, stdout, stderr = run_cli(
                "check", "agent-skills", str(missing)
            )

        self.assertEqual(exit_code, EXIT_ERROR)
        self.assertEqual(stdout, "")
        self.assertIn("ERROR agent-skills: path not found:", stderr)


if __name__ == "__main__":
    unittest.main()
