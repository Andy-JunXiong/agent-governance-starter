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
    def test_public_readme_routes_clean_target_detail_to_existing_owners(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        preflight = (ROOT / "docs/clean-target-replay-preflight.md").read_text(
            encoding="utf-8"
        )
        harness = (ROOT / "docs/harness-contract-v1.md").read_text(encoding="utf-8")
        owned_detail = " ".join((preflight + "\n" + harness).split())

        self.assertIn("](docs/clean-target-replay-preflight.md)", readme)
        self.assertIn("](docs/harness-contract-v1.md)", readme)
        self.assertNotIn("agentgov check replay-preflight", readme)
        for phrase in (
            "agentgov check replay-preflight",
            "READY",
            "BLOCKED",
            "UNKNOWN",
            "agentgov reserve replay-correlation",
            "agentgov claim replay-correlation",
            "agentgov recover replay-claim",
            "agentgov.replay-correlation-bridge",
            "host.repository_correlation",
            "does not create replacement ownership",
        ):
            self.assertIn(phrase, owned_detail)

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

    def test_public_readme_routes_airbnb_completion_evidence_to_status(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        status = " ".join((ROOT / "STATUS.md").read_text(encoding="utf-8").split())

        self.assertIn("](STATUS.md)", readme)
        self.assertNotIn("all 79 tests", readme)
        for phrase in (
            "Python 3.11.9",
            "all 79 tests",
            "Completion Verified",
            "Bounded Handoff",
            "does not prove the automatic primary experience",
            "consumer working tree remains uncommitted and unpushed",
        ):
            self.assertIn(phrase, status)

    def test_public_readme_routes_native_completion_install_block_to_evidence(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        evidence = " ".join(
            (
                ROOT
                / "docs/experiments/airbnb-native-completion-isolated-live-replay-2026-08-21.md"
            ).read_text(encoding="utf-8").split()
        )

        self.assertIn("](STATUS.md)", readme)
        self.assertNotIn("setuptools 65.5.0", readme)
        for phrase in (
            "BLOCKED_BEFORE_INSTALLATION",
            "setuptools 65.5.0",
            "setuptools>=69",
            "before building or installing a package",
            "no MCP process or Codex session started",
            "omits `agentgov_task_completion_record`",
        ):
            self.assertIn(phrase, evidence)

    def test_public_readme_routes_native_completion_live_start_block_to_evidence(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        evidence = " ".join(
            (
                ROOT
                / "docs/experiments/airbnb-native-completion-end-to-end-recovery-2026-08-21.md"
            ).read_text(encoding="utf-8").split()
        )

        self.assertIn("](STATUS.md)", readme)
        self.assertNotIn("setuptools 84.0.0", readme)
        for phrase in (
            "setuptools 84.0.0",
            "agent-governance-starter 0.3.0rc1",
            "eight tools with form elicitation and six without it",
            "BLOCKED_BEFORE_MODEL_MCP_INITIALIZATION",
            "MCP handshake closed while producing the initialize response",
            "No native proposal form",
        ):
            self.assertIn(phrase, evidence)

    def test_public_readme_routes_bounded_nyc_completion_evidence_to_status(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        status = " ".join((ROOT / "STATUS.md").read_text(encoding="utf-8").split())

        self.assertIn("](STATUS.md)", readme)
        self.assertNotIn("all 68 tests", readme)
        for phrase in (
            "second independent bounded consumer result",
            "all 68 tests",
            "Completion Verified",
            "Bounded Handoff",
            "formal CI remains on AgentGov 0.2.1",
            "not a formal upgrade",
            "does not prove uncoached adoption",
            "Its consumer changes remain uncommitted and unpushed",
        ):
            self.assertIn(phrase, status)

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
            "six base `agentgov_*` governance tools",
            "`agentgov_task_completion_record` is available",
            "`agentgov_task_proposal_review` and `agentgov_drift_review_record`",
            "readable, validated `governance/tasks/*.json` record",
            "explicitly authorizes that exact requested change",
            "A direct chat request, approval, authorization, tool permission",
            "Do not call it for read-only work",
            "Do not modify the repository until the resulting task record exists",
            "After implementing an exact admitted task",
        ):
            self.assertIn(phrase, normalized)


if __name__ == "__main__":
    unittest.main()
