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

        for phrase in (
            "update every affected source of truth in the same bounded change",
            "README.md",
            "STATUS.md",
            "public HTML",
            "localized pages",
            "tests that protect those surfaces",
        ):
            self.assertIn(phrase, instructions)


if __name__ == "__main__":
    unittest.main()
