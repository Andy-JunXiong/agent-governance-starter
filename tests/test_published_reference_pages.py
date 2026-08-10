import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


class PublishedReferencePageTests(unittest.TestCase):
    def test_authoritative_markdown_uses_the_shared_agentgov_layout(self) -> None:
        markdown_names = (
            "development-task-contract.md",
            "development-context.md",
            "development-scope-check.md",
            "development-evidence.md",
            "consumer-ci.md",
            "governance-model.md",
            "kernel-boundary-classification-2026-08-10.md",
            "ai-radar-extraction-map.md",
            "adr/0009-govern-coding-agents-during-development.md",
            "adr/0016-establish-minimum-sufficient-kernel-architecture.md",
            "case-studies/0001-pr-center-architecture-drift.md",
            "specs/development-trigger-routing-v1.md",
            "specs/fresh-validation-evidence-v1.md",
        )

        for markdown_name in markdown_names:
            with self.subTest(markdown=markdown_name):
                source = DOCS / markdown_name
                text = source.read_text(encoding="utf-8")
                self.assertTrue(text.startswith("---\nlayout: reference\n"))
                self.assertIn(f"source_path: docs/{markdown_name}", text)

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
