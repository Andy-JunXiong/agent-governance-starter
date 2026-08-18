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
    def test_public_readme_connects_clean_target_preflight_to_harness(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        normalized = " ".join(readme.split())

        self.assertIn("agentgov check replay-preflight", normalized)
        self.assertIn("clean-target replay preflight guide", normalized)
        self.assertIn("READY", normalized)
        self.assertIn("BLOCKED", normalized)
        self.assertIn("UNKNOWN", normalized)
        self.assertIn("Harness still evaluates normalized evidence after it", normalized)
        self.assertIn("agentgov reserve replay-correlation", normalized)
        self.assertIn("requires an interactive `RESERVE`", normalized)
        self.assertIn("agentgov claim replay-correlation", normalized)
        self.assertIn("requires a pre-existing claim registry", normalized)
        self.assertIn("interactive exact `CLAIM`", normalized)
        self.assertIn("Preflight, reservation, claim, separately authorized replay", normalized)
        self.assertIn("agentgov recover replay-claim", normalized)
        self.assertIn("interactive exact `RECOVER`", normalized)
        self.assertIn("pre-existing recovery registry", normalized)
        self.assertIn("does not create replacement ownership", normalized)
        self.assertIn("agentgov.replay-correlation-bridge", normalized)
        self.assertIn("host.repository_correlation", normalized)
        self.assertIn("post-run correlation evidence", normalized)

    def test_public_plan_routes_historical_checkpoints_to_dated_evidence(self) -> None:
        public_plan = (ROOT / "docs/development-plan.md").read_text(
            encoding="utf-8"
        )
        migration_log = (
            ROOT / "docs/development-log/2026-08-14-historical-migration.md"
        ).read_text(encoding="utf-8")

        self.assertIn("## Current checkpoint reference", public_plan)
        self.assertIn("## Next product review reference", public_plan)
        self.assertIn("2026-08-14-historical-migration.md", public_plan)
        self.assertNotIn("## Current checkpoint\n", public_plan)
        self.assertNotIn("## Next-session starting point", public_plan)
        self.assertIn("## Relocated from `docs/development-plan.md`", migration_log)
        self.assertIn("### Current checkpoint", migration_log)
        self.assertIn("### Next-session starting point", migration_log)

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

    def test_current_install_surfaces_and_landing_disclosure_are_fresh(self) -> None:
        install_surfaces = (
            ROOT / "README.md",
            ROOT / "docs/quickstart.html",
            ROOT / "docs/quickstart.zh-CN.html",
            ROOT / "docs/quickstart.zh-CN.md",
            ROOT / "docs/existing-repository-adoption.md",
            ROOT / "docs/troubleshooting.html",
            ROOT / "docs/troubleshooting.zh-CN.html",
            ROOT / "docs/troubleshooting.md",
            ROOT / "docs/interview-guide.html",
            ROOT / "docs/interview-guide.zh-CN.html",
            ROOT / "docs/interview-guide.md",
        )

        for surface in install_surfaces:
            with self.subTest(surface=surface.name):
                text = surface.read_text(encoding="utf-8")
                self.assertIn(STABLE_WHEEL, text)
                self.assertNotIn("releases/download/v0.1.0/", text)
                self.assertNotIn("agent-governance-starter.git@main", text)

        landing = (ROOT / "docs/index.html").read_text(encoding="utf-8")
        self.assertIn('href="portfolio.html#boundary"', landing)
        self.assertIn("See current evidence and limits", landing)
        self.assertNotIn(STABLE_WHEEL, landing)

        portfolio = (ROOT / "docs/portfolio.html").read_text(encoding="utf-8")
        for provenance in ("0.2.1", "0.3.0rc1", "development source"):
            self.assertIn(provenance, portfolio)

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

    def test_repository_instructions_define_documentation_state_ownership(
        self,
    ) -> None:
        instructions = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        normalized = " ".join(instructions.split())

        for phrase in (
            "## Documentation state ownership",
            "Each documentation surface owns one kind of truth and has one update trigger",
            "`DEVELOPMENT_PLAN.md` owns strategic direction",
            "`STATUS.md` owns current repository reality",
            "Update it at every formal development closeout",
            "dated files under `docs/development-log/` own append-only session evidence",
            "No plan, status entry, development log, roadmap item, or proposed next feature grants",
            "Preserve historical facts",
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
