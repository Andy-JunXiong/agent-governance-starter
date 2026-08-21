import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


class EvidencePortfolioTests(unittest.TestCase):
    def setUp(self) -> None:
        self.portfolio = (DOCS / "portfolio.html").read_text(encoding="utf-8")
        self.readme = (ROOT / "README.md").read_text(encoding="utf-8")

    def test_home_page_links_to_evidence_portfolio(self) -> None:
        home = (DOCS / "index.html").read_text(encoding="utf-8")
        self.assertIn('href="portfolio.html"', home)
        self.assertIn("Explore the evidence story", home)

    def test_readme_exposes_a_rendered_showcase_entry(self) -> None:
        showcase = self.readme
        primary_routes = showcase[
            showcase.index('<p align="center">') : showcase.index("</p>")
        ]
        image_path = DOCS / "assets" / "agentgov-social-preview.jpg"

        self.assertEqual(primary_routes.count("<a href="), 4)
        self.assertIn(
            "[![Agent Governance from task intent to verified evidence]"
            "(docs/assets/agentgov-social-preview.jpg)]"
            "(https://andy-junxiong.github.io/agent-governance-starter/)",
            showcase,
        )
        self.assertLess(
            showcase.index("docs/assets/agentgov-social-preview.jpg"),
            showcase.index("## Product overview"),
        )
        self.assertIn(
            "https://andy-junxiong.github.io/agent-governance-starter/",
            showcase,
        )
        self.assertIn(
            "https://andy-junxiong.github.io/agent-governance-starter/portfolio.html",
            showcase,
        )
        self.assertNotIn("nyc", showcase.lower())
        self.assertNotIn("taxi", showcase.lower())
        self.assertTrue(image_path.read_bytes().startswith(b"\xff\xd8"))

    def test_portfolio_records_ai_radar_lineage_and_separation(self) -> None:
        self.assertIn('href="ai-radar-extraction-map.html"', self.portfolio)
        self.assertIn("A useful precedent, not a second product inside this one", self.portfolio)
        self.assertNotIn("https://app.ai-radar-lab.com", self.portfolio)

    def test_portfolio_uses_agentgov_navigation_and_story_priority(self) -> None:
        self.assertIn('href="index.html" aria-label="Agent Governance product home"', self.portfolio)
        self.assertLess(self.portfolio.index('id="lifecycle"'), self.portfolio.index('id="lineage"'))
        self.assertLess(self.portfolio.index('id="cases"'), self.portfolio.index('id="lineage"'))
        self.assertNotIn("data-theme-choice", self.portfolio)

    def test_portfolio_keeps_independent_consumer_projects_isolated(self) -> None:
        normalized = self.portfolio.lower()
        self.assertNotIn("nyc", normalized)
        self.assertNotIn("taxi", normalized)

    def test_all_relative_portfolio_links_resolve(self) -> None:
        hrefs = re.findall(r'href="([^"]+)"', self.portfolio)
        relative_links = [
            href.split("#", 1)[0]
            for href in hrefs
            if not href.startswith(("http://", "https://", "#"))
        ]

        missing = [
            href
            for href in relative_links
            if not (DOCS / href).resolve().exists()
            and not (
                href.endswith(".html")
                and (DOCS / f"{href[:-5]}.md").resolve().exists()
            )
        ]
        self.assertEqual([], missing)

    def test_public_portfolio_does_not_link_raw_markdown_or_escape_site_root(self) -> None:
        hrefs = re.findall(r'href="([^"]+)"', self.portfolio)

        self.assertEqual([], [href for href in hrefs if href.endswith(".md")])
        self.assertEqual([], [href for href in hrefs if href.startswith("../")])

    def test_portfolio_preserves_claim_and_authority_boundaries(self) -> None:
        self.assertIn("deterministic facts, advisory judgment", self.portfolio)
        self.assertIn("not that the requirement is correct", self.portfolio)
        self.assertIn("does not authorize commit, merge, publish, release, or deployment", self.portfolio)
        self.assertNotIn("governance coverage percentage", self.portfolio.lower())

    def test_portfolio_traces_immutable_claim_recovery_without_authority_drift(self) -> None:
        for phrase in (
            'id="recovery"',
            "Reserve correlation",
            "Claim ownership",
            "Inspect abandoned evidence",
            "Record immutable recovery",
            "READY_TO_RESERVE",
            "READY_TO_CLAIM",
            "READY_TO_RECOVER",
            "RECOVERED",
            "does not infer abandonment",
            "creates no replacement owner",
            "authorize replay",
        ):
            self.assertIn(phrase, self.portfolio)

        self.assertIn('href="interview-guide.html"', self.portfolio)
        self.assertIn('href="clean-target-replay-preflight.html"', self.portfolio)


if __name__ == "__main__":
    unittest.main()
