import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


class PublishedReferencePageTests(unittest.TestCase):
    def test_portfolio_reference_proxies_use_the_shared_agentgov_layout(self) -> None:
        pairs = (
            ("development-task-contract.html", "development-task-contract.md"),
            ("development-context.html", "development-context.md"),
            ("development-scope-check.html", "development-scope-check.md"),
            ("development-evidence.html", "development-evidence.md"),
            ("consumer-ci.html", "consumer-ci.md"),
            ("governance-model.html", "governance-model.md"),
            ("ai-radar-extraction-map.html", "ai-radar-extraction-map.md"),
            (
                "adr/0009-govern-coding-agents-during-development.html",
                "adr/0009-govern-coding-agents-during-development.md",
            ),
            (
                "case-studies/0001-pr-center-architecture-drift.html",
                "case-studies/0001-pr-center-architecture-drift.md",
            ),
            (
                "specs/development-trigger-routing-v1.html",
                "specs/development-trigger-routing-v1.md",
            ),
            (
                "specs/fresh-validation-evidence-v1.html",
                "specs/fresh-validation-evidence-v1.md",
            ),
        )

        for html_name, markdown_name in pairs:
            with self.subTest(html=html_name):
                proxy = DOCS / html_name
                source = DOCS / markdown_name
                text = proxy.read_text(encoding="utf-8")
                self.assertTrue(source.is_file())
                self.assertIn("layout: reference", text)
                self.assertIn(
                    f"include_relative {source.name}",
                    text,
                )

    def test_published_schema_json_is_byte_identical_to_source(self) -> None:
        for name in (
            "development-task.schema.json",
            "development-scope-report.schema.json",
        ):
            with self.subTest(schema=name):
                self.assertEqual(
                    (ROOT / "schemas" / name).read_bytes(),
                    (DOCS / "schemas" / name).read_bytes(),
                )

                browser_page = (DOCS / "schemas" / name.replace(".json", ".html"))
                text = browser_page.read_text(encoding="utf-8")
                self.assertIn("layout: reference", text)
                self.assertIn(f"include_relative {name}", text)

    def test_reference_layout_keeps_agentgov_navigation_and_authority(self) -> None:
        layout = (DOCS / "_layouts/reference.html").read_text(encoding="utf-8")
        css = (DOCS / "reference.css").read_text(encoding="utf-8")

        self.assertIn("Agent Governance", layout)
        self.assertIn("Evidence portfolio", layout)
        self.assertIn("does not authorize commit, merge", layout)
        self.assertIn("--purple: #7157ff", css)
        self.assertIn("--navy: #10223f", css)


if __name__ == "__main__":
    unittest.main()
