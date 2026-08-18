import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "docs/index.html"


class ProductSiteTests(unittest.TestCase):
    def test_product_site_explains_value_implementation_and_adoption(self) -> None:
        content = SITE.read_text(encoding="utf-8")

        for phrase in (
            "Make AI-assisted repositories reviewable by default.",
            "When an AI changes how refunds get approved",
            "See the refund example",
            "An AI drafts customer refund replies.",
            "Before governance",
            "With Agent Governance",
            "Small files make the invisible contract reviewable.",
            "Plain files and deterministic checks. No hidden AI judge.",
            "No governance score. On purpose.",
            "Illustrative example",
            "ADVISORY · HUMAN JUDGMENT",
            "A repository-native control layer",
            "Inspect the implementation, not just the promise.",
            "Preview first. Create only what is missing.",
            "Developer",
            "Reviewer",
            "Team lead or CI",
        ):
            self.assertIn(phrase, content)

        nav = content.split("<nav>", 1)[1].split("</nav>", 1)[0]
        product_journey = (
            "How it works",
            "Example",
            "Evidence",
            "Quickstart",
            "Guided walkthrough",
        )
        positions = [nav.index(label) for label in product_journey]
        self.assertEqual(positions, sorted(positions))

        self.assertNotIn("Inspect the detailed development milestone history", content)
        self.assertNotIn("Adapter <code>1.5.0</code>", content)
        self.assertNotIn("cryptographic personal identity,", content)
        self.assertIn('href="portfolio.html#boundary"', content)
        self.assertIn("Illustrative published <code>0.3.0rc1</code> sample report", content)
        self.assertIn("stable\n            <code>0.2.1</code> remains installable", content)
        self.assertIn("newer development-source\n            behavior is separate", content)
        self.assertIn(
            ".hero > *,\n"
            "      .evidence > * {\n"
            "        min-width: 0;\n"
            "      }",
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
        self.assertIn("No autonomous approval", content)
        self.assertIn("WARN</span> evaluation:needs_seed_cases", content)
        self.assertNotIn("Open live governance report", content)
        self.assertNotIn("{{", content)
        self.assertNotIn("}}", content)
        self.assertNotIn('role="img"', content)
        self.assertIn('<figcaption class="sr-only">', content)
        self.assertIn(
            'pipx install "https://github.com/Andy-JunXiong/'
            "agent-governance-starter/releases/download/v0.2.1/"
            'agent_governance_starter-0.2.1-py3-none-any.whl"',
            content,
        )
        self.assertIn("Stable 0.2.1 · 0.3 development preview", content)
        self.assertNotIn("v0.1 technical preview", content)
        self.assertNotIn("python -m pip install --no-deps .", content)
        self.assertIn("See what the CLI finds", content)
        self.assertIn("Inspect the evidence boundary", content)
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
