import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
CASE_STUDY = ROOT / "docs/case-study.md"
DEMO_ASSET = ROOT / "docs/assets/agentgov-demo.svg"


class PortfolioDocumentationTests(unittest.TestCase):
    def test_readme_opens_with_portfolio_positioning_and_required_sections(self) -> None:
        text = README.read_text(encoding="utf-8")
        expected_opening = (
            "# Agent Governance Starter Kit\n\n"
            "**Make AI-assisted repositories reviewable by default.**"
        )

        self.assertTrue(text.startswith(expected_opening))
        for heading in (
            "## Why this exists",
            "## Architecture at a glance",
            "## What makes it different",
            "## What this project demonstrates",
            "## Scope boundaries",
            "## Runnable CLI example",
            "## Example findings",
            "## Detailed architecture",
            "## Project status and non-goals",
            "## Project navigation",
        ):
            self.assertIn(heading, text)
        self.assertLess(
            text.index("## Why this exists"), text.index("## Repository layout")
        )
        self.assertLess(
            text.index("## Architecture at a glance"),
            text.index("![Agent Governance CLI"),
        )

    def test_readme_demo_visual_uses_real_sanitized_cli_output(self) -> None:
        text = README.read_text(encoding="utf-8")

        self.assertIn(
            "![Agent Governance CLI detecting incomplete evidence, source drift, "
            "and a human-review advisory](docs/assets/agentgov-demo.svg)",
            text,
        )
        self.assertTrue(DEMO_ASSET.is_file())

        asset = DEMO_ASSET.read_text(encoding="utf-8")
        for finding in (
            "WARN evaluation:evaluation/example-capability:",
            "FAIL artifact:example-capability:",
            "ADVISORY governance:human-review:",
            "SUMMARY PASS=11 WARN=3 FAIL=1 ADVISORY=1",
        ):
            self.assertIn(finding, asset)
        self.assertNotIn("payment-summary", asset)
        self.assertNotIn("C:\\Users", asset)
        self.assertNotRegex(asset, r"\b\d+%")

    def test_readme_explains_value_and_finding_semantics(self) -> None:
        text = README.read_text(encoding="utf-8")

        for phrase in (
            "| Without explicit contracts | With Agent Governance Starter Kit |",
            "Artifact hashes report deterministic source drift.",
            "Human approval remains an external boundary.",
            "### How to read the result",
            "`PASS` — a deterministic contract is satisfied.",
            "`WARN` — a valid, non-blocking configuration or evidence state is incomplete.",
            "`FAIL` — a deterministic requirement is broken or a reviewed artifact is stale.",
            "`ADVISORY` — accountable human judgment is still required.",
            "They do not authorize merge,\npublication, release, or deployment.",
        ):
            self.assertIn(phrase, text)

    def test_readme_demo_findings_and_mermaid_match_implemented_contracts(self) -> None:
        text = README.read_text(encoding="utf-8")

        for command in (
            'pipx install "https://github.com/Andy-JunXiong/'
            "agent-governance-starter/releases/download/v0.1.0/"
            'agent_governance_starter-0.1.0-py3-none-any.whl"',
            "agentgov --help",
            'python -m agentgov init $Project --project-name "Portfolio Demo"',
            "python -m agentgov check repository $Project",
            'python -m agentgov report repository $Project '
            '--output "$Project/governance-report.md"',
            'python -m agentgov init "$project" --project-name "Portfolio Demo"',
        ):
            self.assertIn(command, text)
        self.assertLess(
            text.index('pipx install "https://github.com/'),
            text.index(
                'python -m agentgov init $Project --project-name "Portfolio Demo"'
            ),
        )
        for finding in (
            "PASS capability:governance/capabilities/example-capability.json:",
            "WARN evaluation:evaluation/example-capability: needs_seed_cases:",
            "FAIL artifact:example-capability:",
            "ADVISORY governance:human-review:",
        ):
            self.assertIn(finding, text)

        diagrams = re.findall(r"```mermaid\n(.*?)```", text, flags=re.DOTALL)
        self.assertEqual(len(diagrams), 2)
        overview, diagram = diagrams
        for label in (
            "Policy · Capability · Owner · Risk",
            "Implementation · Contracts · Evidence",
            "References · Readiness · Drift",
            "PASS · WARN · FAIL · ADVISORY",
            "Accountable human authority",
        ):
            self.assertIn(label, overview)
        self.assertTrue(diagram.startswith("flowchart TB\n"))
        for label in (
            "Repository-local contracts and evidence",
            "agentgov governance operations",
            "Review and integration surfaces",
            "Separate explicit write command",
            "Read-only drift detection",
            "Ordered RepositoryReport",
            "Consumer CI",
            "Pinned check · Report artifact",
            "Not included in v0.1",
        ):
            self.assertIn(label, diagram)
        for edge in (
            "SOURCES --> VALIDATE",
            "CAPABILITY --> EXPORT",
            "SOURCES --> EXPORT",
            "EXPORT --> ARTIFACT",
            "ARTIFACT --> DRIFT",
            "VALIDATE --> FINDINGS",
            "DRIFT --> FINDINGS",
            "FINDINGS --> TERMINAL",
            "FINDINGS --> MARKDOWN",
            "FINDINGS --> JSON",
            "FINDINGS --> STATUS_SURFACE",
            "JSON --> CONSUMER_CI",
            "JSON -.-> FUTURE",
            'HUMAN -->|"Separate explicit authority"| TRANSITION',
        ):
            self.assertIn(edge, diagram)
        self.assertNotIn("Reject · Escalate", diagram)
        self.assertNotIn("A --> B", diagram)
        self.assertIn(
            "The bounded consumer CI integration runs the JSON report without "
            "installing\nthe adopting project's dependencies. Artifact export is "
            "a separate explicit\nwrite command, not a stage inside repository "
            "checking.",
            text,
        )
        self.assertIn(
            "merge, publication, release,\nand deployment remain separate "
            "human-authorized actions.",
            text,
        )

    def test_prominent_local_navigation_targets_exist(self) -> None:
        required_paths = (
            "docs/case-study.md",
            "docs/governance-model.md",
            "docs/v0.1-adoption-rehearsal.md",
            "docs/ai-radar-extraction-map.md",
            "src/agentgov/cli.py",
            "tests",
            "governance/capability.schema.json",
            "evaluation/schemas/evaluation-manifest.schema.json",
            "schemas/repository-report.schema.json",
            "docs/consumer-ci.md",
            "docs/upgrade-pr-automation.md",
            "docs/benefit-monitor.md",
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
