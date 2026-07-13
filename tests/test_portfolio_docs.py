import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
CASE_STUDY = ROOT / "docs/case-study.md"


class PortfolioDocumentationTests(unittest.TestCase):
    def test_readme_opens_with_portfolio_positioning_and_required_sections(self) -> None:
        text = README.read_text(encoding="utf-8")
        expected_opening = (
            "# Agent Governance Starter Kit\n\n"
            "A reference implementation for repository-native capability, evidence, "
            "and human-review contracts in AI-assisted software development."
        )

        self.assertTrue(text.startswith(expected_opening))
        for heading in (
            "## The problem",
            "## What this project demonstrates",
            "## What makes the design different",
            "## Thirty-second demo",
            "## Example findings",
            "## Architecture",
            "## Project status and non-goals",
            "## Project navigation",
        ):
            self.assertIn(heading, text)
        self.assertLess(text.index("## The problem"), text.index("## Repository layout"))

    def test_readme_demo_findings_and_mermaid_match_implemented_contracts(self) -> None:
        text = README.read_text(encoding="utf-8")

        for command in (
            'agentgov init $Project --project-name "Portfolio Demo"',
            "agentgov check repository $Project",
            'agentgov report repository $Project --output "$Project/governance-report.md"',
        ):
            self.assertIn(command, text)
        for finding in (
            "PASS capability:prompt-governance/capabilities/example-capability.json:",
            "WARN evaluation:evaluation/example-capability: needs_seed_cases:",
            "FAIL artifact:example-capability:",
            "ADVISORY governance:human-review:",
        ):
            self.assertIn(finding, text)

        mermaid = re.search(r"```mermaid\n(.*?)```", text, flags=re.DOTALL)
        self.assertIsNotNone(mermaid)
        diagram = mermaid.group(1)
        self.assertTrue(diagram.startswith("flowchart TD\n"))
        for edge in ("CLI", "A --> B", "B --> C", "C --> D", "D --> E", "E --> F", "F --> G"):
            self.assertIn(edge, diagram)

    def test_prominent_local_navigation_targets_exist(self) -> None:
        required_paths = (
            "docs/case-study.md",
            "docs/governance-model.md",
            "docs/v0.1-adoption-rehearsal.md",
            "docs/ai-radar-extraction-map.md",
            "src/agentgov/cli.py",
            "tests",
            "prompt-governance/capability.schema.json",
            "prompt-governance/fixtures/valid/runtime-low-risk.json",
            "evaluation/schemas/evaluation-manifest.schema.json",
            "schemas/repository-report.schema.json",
        )
        text = README.read_text(encoding="utf-8")

        for relative_path in required_paths:
            with self.subTest(path=relative_path):
                self.assertIn(f"]({relative_path})", text)
                self.assertTrue((ROOT / relative_path).exists())

    def test_case_study_preserves_scope_and_honest_limits(self) -> None:
        text = CASE_STUDY.read_text(encoding="utf-8")

        for heading in (
            "## Context",
            "## Problem",
            "## Product decisions",
            "## Trust boundary",
            "## Architecture",
            "## Implementation",
            "## Validation",
            "## Competitive and market learning",
            "## Current limitations",
            "## Future product direction",
        ):
            self.assertIn(heading, text)
        self.assertIn("independent Python package", text)
        self.assertIn("not a runtime dependency", text)
        self.assertIn("That UI does not currently exist", text)
        self.assertIn("stable integration boundary", text)
        self.assertIn("product hypothesis", text)
        self.assertNotRegex(text, r"\b\d+%")


if __name__ == "__main__":
    unittest.main()
