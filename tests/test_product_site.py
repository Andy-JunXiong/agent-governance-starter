import re
import unittest
from html import unescape
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "docs/index.html"


class ProductSiteTests(unittest.TestCase):
    def test_product_site_explains_value_in_plain_language(self) -> None:
        content = SITE.read_text(encoding="utf-8")

        for phrase in (
            "Keep humans in control of AI-written code.",
            "AgentGov records what an AI agent was asked to change",
            "See a real example",
            "An AI changes how customer refunds are handled.",
            "Without AgentGov",
            "With AgentGov",
            "See facts, gaps, and human decisions in one place.",
            "What checks confirmed",
            "What is still missing",
            "What a human must decide",
            "Three steps. The human stays in charge.",
            "Set the boundaries",
            "AgentGov keeps those limits connected to the work.",
            "Check the work",
            "Let a person decide",
            "Start with one repository.",
            "Illustrative example",
            "Passing checks never approve a merge, release, or deployment.",
        ):
            self.assertIn(phrase, content)

        nav = content.split("<nav>", 1)[1].split("</nav>", 1)[0]
        product_journey = (
            "Example",
            "Report",
            "How it works",
            "Quickstart",
        )
        positions = [nav.index(label) for label in product_journey]
        self.assertEqual(positions, sorted(positions))

        self.assertEqual(content.count("<section"), 4)
        hero = content.split('<div class="shell hero">', 1)[1].split(
            "</header>", 1
        )[0]
        heading = re.search(r"<h1>(.*?)</h1>", hero, re.DOTALL)
        support = re.search(
            r'<p class="hero-support">(.*?)</p>', hero, re.DOTALL
        )
        self.assertIsNotNone(heading)
        self.assertIsNotNone(support)
        hero_copy = unescape(
            re.sub(r"<[^>]+>", " ", heading.group(1) + " " + support.group(1))
        )
        self.assertLessEqual(
            len(re.findall(r"[A-Za-z]+(?:[-'][A-Za-z]+)*", hero_copy)), 35
        )
        main = content.split("<main>", 1)[1].split("</main>", 1)[0]
        main_copy = unescape(re.sub(r"<[^>]+>", " ", main))
        self.assertLessEqual(
            len(re.findall(r"[A-Za-z]+(?:[-'][A-Za-z]+)*", main_copy)), 500
        )

        self.assertNotIn("Inspect the detailed development milestone history", content)
        self.assertNotIn("Adapter <code>1.5.0</code>", content)
        self.assertNotIn("cryptographic personal identity,", content)
        self.assertNotIn("Current development evidence", content)
        self.assertNotIn("immutable reservation", main)
        self.assertNotIn("No governance score. On purpose.", content)
        self.assertNotIn("PASS · FACT SATISFIED", content)
        self.assertNotIn("Small files make the invisible contract reviewable.", content)
        self.assertNotIn("Actual fixture validation output", content)
        self.assertNotIn("pipx install", content)
        self.assertIn('href="portfolio.html#boundary"', content)
        self.assertIn("Sanitized <code>0.3.0rc1</code> sample", content)
        self.assertIn("Stable CLI:", content)
        self.assertIn(
            "releases/download/v0.2.1/"
            "agent_governance_starter-0.2.1-py3-none-any.whl",
            content,
        )
        self.assertIn('<details class="footer-evidence">', content)
        self.assertIn(
            ".hero > *,", content
        )
        self.assertIn(
            "min-width: 0;",
            content,
        )

    def test_product_site_is_local_only_and_links_the_real_demo(self) -> None:
        content = SITE.read_text(encoding="utf-8")

        self.assertIn('href="demo-governance-report.html"', content)
        self.assertIn('href="interview-guide.html"', content)
        self.assertTrue((ROOT / "docs/interview-guide.html").is_file())
        self.assertTrue((ROOT / "docs/demo-governance-report.html").is_file())
        self.assertIn("https://github.com/Andy-JunXiong/agent-governance-starter", content)
        self.assertNotIn("script-src 'unsafe-inline'", content)
        self.assertIn("prefers-reduced-motion", content)
        self.assertIn(":focus-visible", content)
        self.assertIn("position: sticky", content)
        self.assertIn("background: var(--navy)", content)
        self.assertIn('<div class="shell nav-inner">', content)
        self.assertIn(
            "https://github.com/Andy-JunXiong/agent-governance-starter/blob/main/LICENSE",
            content,
        )
        self.assertIn(
            "https://github.com/Andy-JunXiong/agent-governance-starter/blob/main/README.md",
            content,
        )
        self.assertIn('href="quickstart.zh-CN.html"', content)
        self.assertTrue((ROOT / "docs/quickstart.zh-CN.html").is_file())
        self.assertIn('hreflang="zh-CN"', content)
        self.assertIn(">中文快速入门</a", content)
        self.assertIn("README on GitHub ↗", content)
        self.assertIn("MIT License ↗", content)
        self.assertIn('href="quickstart.html"', content)
        self.assertIn("Never approves for you", content)
        self.assertIn("HUMAN REVIEW", content)
        self.assertNotIn("Open live governance report", content)
        self.assertNotIn("{{", content)
        self.assertNotIn("}}", content)
        self.assertNotIn('role="img"', content)
        self.assertIn('<figcaption class="sr-only">', content)
        self.assertNotIn("agentgov adopt .", content)
        self.assertIn("stable 0.2.1 · 0.3 development preview", content)
        self.assertNotIn("v0.1 technical preview", content)
        self.assertNotIn("python -m pip install --no-deps .", content)
        self.assertNotIn("See what the CLI finds", content)
        self.assertIn("See current evidence and limits", content)
        quickstart_html = ROOT / "docs/quickstart.zh-CN.html"
        self.assertTrue(quickstart_html.is_file())
        quickstart = quickstart_html.read_text(encoding="utf-8")
        self.assertIn('lang="zh-CN"', quickstart)
        self.assertIn("10 分钟接入路径", quickstart)
        self.assertIn("agentgov inspect .", quickstart)
        self.assertIn('href="quickstart.html" lang="en"', quickstart)
        self.assertIn(
            'href="quickstart.zh-CN.html" lang="zh-CN" aria-current="page"',
            quickstart,
        )
        self.assertIn("Bash / zsh", quickstart)
        self.assertIn("PowerShell", quickstart)
        for english_page, chinese_page in (
            ("existing-repository-adoption.html", "existing-repository-adoption.zh-CN.html"),
            ("generated-files-guide.html", "generated-files-guide.zh-CN.html"),
            ("troubleshooting.html", "troubleshooting.zh-CN.html"),
        ):
            self.assertIn(f'href="{chinese_page}"', quickstart)
            chinese_guide = ROOT / "docs" / chinese_page
            english_guide = ROOT / "docs" / english_page
            self.assertTrue(chinese_guide.is_file())
            self.assertTrue(english_guide.is_file())
            self.assertIn('lang="zh-CN"', chinese_guide.read_text(encoding="utf-8"))
            self.assertIn('lang="en"', english_guide.read_text(encoding="utf-8"))
        english_quickstart = ROOT / "docs/quickstart.html"
        self.assertTrue(english_quickstart.is_file())
        english = english_quickstart.read_text(encoding="utf-8")
        self.assertIn('lang="en"', english)
        self.assertIn("Bash / zsh", english)
        self.assertIn("PowerShell", english)
        self.assertIn('href="quickstart.zh-CN.html"', english)
        self.assertIn('href="existing-repository-adoption.html"', english)
        self.assertIn('href="generated-files-guide.html"', english)
        self.assertIn('href="troubleshooting.html"', english)
        self.assertNotIn("http://", content)
        self.assertNotIn("<script src=", content)
        self.assertNotIn('rel="stylesheet"', content)
        self.assertNotIn("C:\\Users", content)
        self.assertNotIn("Relevance AI", content)

    def test_readme_links_both_html_surfaces(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn("](docs/index.html)", readme)
        self.assertIn("](docs/demo-governance-report.html)", readme)
        self.assertIn("](docs/interview-guide.md)", readme)
        self.assertIn("Interview snapshot", readme)


if __name__ == "__main__":
    unittest.main()
