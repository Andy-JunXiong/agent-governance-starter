import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "docs/index.html"


class ProductSiteTests(unittest.TestCase):
    def test_product_site_explains_value_implementation_and_adoption(self) -> None:
        content = SITE.read_text(encoding="utf-8")

        for phrase in (
            "Make AI-assisted repositories reviewable by default.",
            "An AI drafts customer refund replies.",
            "Before governance",
            "With Agent Governance",
            "Small files make the invisible contract reviewable.",
            "Plain files and deterministic checks. No hidden AI judge.",
            "No governance score. On purpose.",
            "Illustrative example",
            "ADVISORY · HUMAN JUDGMENT",
            "A local Python CLI and repository file standard",
            "Inspect the implementation, not just the promise.",
            "Preview first. Create only what is missing.",
            "Developer",
            "Reviewer",
            "Team lead or CI",
        ):
            self.assertIn(phrase, content)

    def test_product_site_is_local_only_and_links_the_real_demo(self) -> None:
        content = SITE.read_text(encoding="utf-8")

        self.assertIn('href="demo-governance-report.html"', content)
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
        self.assertNotIn('role="img"', content)
        self.assertIn('<figcaption class="sr-only">', content)
        self.assertIn(
            'python -m pip install "git+https://github.com/'
            'Andy-JunXiong/agent-governance-starter.git@main"',
            content,
        )
        self.assertNotIn("python -m pip install --no-deps .", content)
        self.assertIn("See what the CLI finds", content)
        self.assertIn("PASS, WARN, FAIL and", content)
        self.assertIn("decisions that still need", content)
        quickstart_html = ROOT / "docs/quickstart.zh-CN.html"
        self.assertTrue(quickstart_html.is_file())
        quickstart = quickstart_html.read_text(encoding="utf-8")
        self.assertIn('lang="zh-CN"', quickstart)
        self.assertIn("10 分钟接入路径", quickstart)
        self.assertIn("python -m agentgov inspect .", quickstart)
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
        self.assertNotIn("<link ", content)
        self.assertNotIn("C:\\Users", content)
        self.assertNotIn("Relevance AI", content)

    def test_readme_links_both_html_surfaces(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn("](docs/index.html)", readme)
        self.assertIn("](docs/demo-governance-report.html)", readme)


if __name__ == "__main__":
    unittest.main()
