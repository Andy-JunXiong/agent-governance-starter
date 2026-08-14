import unittest
from pathlib import Path

from agentgov import __version__


ROOT = Path(__file__).resolve().parents[1]
STABLE_WHEEL = (
    "https://github.com/Andy-JunXiong/agent-governance-starter/"
    "releases/download/v0.2.1/"
    "agent_governance_starter-0.2.1-py3-none-any.whl"
)


class PublicDocumentationFreshnessTests(unittest.TestCase):
    def test_public_readme_reports_bounded_airbnb_completion_evidence(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        normalized = " ".join(readme.split())

        for phrase in (
            "Python 3.11.9",
            "all 79 tests",
            "Completion Verified",
            "Bounded Handoff",
            "not proof of the automatic primary experience",
            "consumer changes remain uncommitted and unpushed",
        ):
            self.assertIn(phrase, normalized)

    def test_public_readme_reports_bounded_nyc_completion_evidence(self) -> None:
        normalized = " ".join((ROOT / "README.md").read_text(encoding="utf-8").split())

        for phrase in (
            "second independent bounded consumer journey",
            "all 68 tests",
            "Completion Verified",
            "Bounded Handoff",
            "formal CI remains on AgentGov 0.2.1",
            "not a formal upgrade",
            "not proof of uncoached automatic adoption",
            "NYC consumer changes remain uncommitted and unpushed",
        ):
            self.assertIn(phrase, normalized)

    def test_current_install_surfaces_use_the_published_stable_wheel(self) -> None:
        surfaces = (
            ROOT / "README.md",
            ROOT / "docs/index.html",
            ROOT / "docs/quickstart.html",
            ROOT / "docs/quickstart.zh-CN.html",
            ROOT / "docs/quickstart.zh-CN.md",
            ROOT / "docs/existing-repository-adoption.md",
            ROOT / "docs/troubleshooting.html",
            ROOT / "docs/troubleshooting.zh-CN.html",
            ROOT / "docs/troubleshooting.md",
        )

        for surface in surfaces:
            with self.subTest(surface=surface.name):
                text = surface.read_text(encoding="utf-8")
                self.assertIn(STABLE_WHEEL, text)
                self.assertNotIn("releases/download/v0.1.0/", text)
                self.assertNotIn("agent-governance-starter.git@main", text)

    def test_public_demo_identifies_the_development_source_snapshot(self) -> None:
        for name in ("demo-governance-report.html", "demo-governance-report.zh-CN.html"):
            text = (ROOT / "docs" / name).read_text(encoding="utf-8")
            self.assertIn(f'"version": "{__version__}"', text)
            self.assertIn(f"{__version__}", text)

    def test_repository_instructions_require_related_documentation_updates(self) -> None:
        instructions = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        normalized = " ".join(instructions.split())

        for phrase in (
            "update every affected source of truth in the same bounded change",
            "README.md",
            "STATUS.md",
            "public HTML",
            "localized pages",
            "tests that protect those surfaces",
        ):
            self.assertIn(phrase, normalized)

    def test_repository_instructions_distinguish_git_and_gh_authentication(
        self,
    ) -> None:
        instructions = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        normalized = " ".join(instructions.split())

        for phrase in (
            "Direct Git transport authentication and GitHub CLI/API authentication are independent",
            "an invalid `gh auth status` does not prove that `git push` is unauthenticated",
            "git push origin HEAD:main",
            "credential.helper=manager",
            "git credential-manager github login",
            "retry the exact same non-force push once",
            "do not repeatedly ask the human to run `gh auth login`",
        ):
            self.assertIn(phrase, normalized)

    def test_repository_instructions_require_contextual_completion_explanations(
        self,
    ) -> None:
        instructions = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        normalized = " ".join(instructions.split())

        for phrase in (
            "## Completion communication",
            "plain language",
            "all seven questions",
            "What are the short-term benefits?",
            "What are the long-term benefits?",
            "What previous capability does it connect to or build on?",
            "What feature should be developed next?",
            "How does the completed feature connect to that next feature?",
            "How does it help the project as a whole?",
            "benefit claims evidence-bounded",
            "instead of inventing a relationship or roadmap commitment",
            "A proposed next feature is a product-review input only",
            "does not authorize the Agent to create a task",
            "Review the completed requirement with the human product owner first",
            "real unmet needs and observed drift",
            "jointly choose the next requirement",
        ):
            self.assertIn(phrase, normalized)

    def test_repository_instructions_bind_proposal_review_to_matching_tasks(
        self,
    ) -> None:
        instructions = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        normalized = " ".join(instructions.split())

        for phrase in (
            "five base `agentgov_*` governance tools",
            "sixth `agentgov_task_proposal_review` tool",
            "readable, validated `governance/tasks/*.json` record",
            "explicitly authorizes that exact requested change",
            "A direct chat request, approval, authorization, tool permission",
            "Do not call it for read-only work",
            "Do not modify the repository until the resulting task record exists",
            "After implementing and validating any repository-changing task",
        ):
            self.assertIn(phrase, normalized)


if __name__ == "__main__":
    unittest.main()
