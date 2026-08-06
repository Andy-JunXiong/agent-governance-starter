import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
CASE_STUDY = ROOT / "docs/case-study.md"
ARCHITECTURE_DRIFT_CASE = (
    ROOT / "docs/case-studies/0001-pr-center-architecture-drift.md"
)
PRODUCT_ARCHITECTURE_PLAN = (
    ROOT / "docs/proposals/2026-08-02-agentgov-product-and-architecture-plan.zh-CN.md"
)
TRIGGER_ROUTING_SPEC = ROOT / "docs/specs/development-trigger-routing-v1.md"
FRESH_EVIDENCE_SPEC = ROOT / "docs/specs/fresh-validation-evidence-v1.md"
DEVELOPMENT_EVENT_EXPORT = ROOT / "docs/development-event-export.md"
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
            "agent-governance-starter/releases/download/v0.2.1/"
            'agent_governance_starter-0.2.1-py3-none-any.whl"',
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
            "Not in stable 0.2.1",
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
            "docs/case-studies/0001-pr-center-architecture-drift.md",
            "docs/development-task-contract.md",
            "docs/task-proposal-admission.md",
            "docs/admission-routing.md",
            "docs/human-decision-prompts.md",
            "docs/clarification-dialogue.md",
            "docs/development-context.md",
            "docs/development-session.md",
            "docs/development-scope-check.md",
            "docs/development-evidence.md",
            "docs/development-event-export.md",
            "docs/development-monitor.md",
            "docs/experiments/installed-development-governance-pilot.md",
            "docs/proposals/2026-08-02-agentgov-product-and-architecture-plan.zh-CN.md",
            "docs/specs/development-trigger-routing-v1.md",
            "docs/specs/fresh-validation-evidence-v1.md",
            "docs/governance-model.md",
            "docs/v0.1-adoption-rehearsal.md",
            "docs/ai-radar-extraction-map.md",
            "src/agentgov/cli.py",
            "tests",
            "governance/capability.schema.json",
            "evaluation/schemas/evaluation-manifest.schema.json",
            "schemas/repository-report.schema.json",
            "schemas/development-task.schema.json",
            "schemas/task-proposal.schema.json",
            "schemas/task-admission-plan.schema.json",
            "schemas/admission-routing-policy.schema.json",
            "schemas/work-request.schema.json",
            "schemas/admission-route.schema.json",
            "schemas/human-decision-prompt.schema.json",
            "schemas/human-decision-result.schema.json",
            "schemas/alignment-context.schema.json",
            "schemas/clarification-dialogue.schema.json",
            "schemas/clarification-prompt.schema.json",
            "schemas/clarification-update.schema.json",
            "schemas/coding-agent-alignment-response.schema.json",
            "schemas/development-context.schema.json",
            "schemas/development-session.schema.json",
            "schemas/development-scope-report.schema.json",
            "schemas/development-evidence.schema.json",
            "schemas/development-completion.schema.json",
            "schemas/governance-event.schema.json",
            "schemas/development-event-export.schema.json",
            "schemas/development-monitor.schema.json",
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

    def test_architecture_drift_case_separates_evidence_from_judgment(self) -> None:
        text = ARCHITECTURE_DRIFT_CASE.read_text(encoding="utf-8")

        for phrase in (
            "Case: `AG-DRIFT-001`",
            "deterministic history plus advisory interpretation",
            "The original requirement did not change",
            "This case is the first acceptance scenario",
            "before PR creation",
        ):
            self.assertIn(phrase, text)
        self.assertIn("must not be emitted\nas a deterministic failure", text)
        self.assertIn("ADR-0009", text)

    def test_installed_development_pilot_preserves_exact_evidence_and_claim_limits(self) -> None:
        text = (
            ROOT / "docs/experiments/installed-development-governance-pilot.md"
        ).read_text(encoding="utf-8")

        for phrase in (
            "9ead26aaebe84317723018bf4f880100e513a3873b08bfb33917ec7beb2a884b",
            "no AI Radar code",
            "actual consumption",
            "Invalid Skill gate",
            "Validation-artifact gate",
            "needs_evidence",
            "verified",
            "`partial` history",
            "not an uncoached human study",
            "one run cannot",
            "0.3.0.dev0",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)
        self.assertNotRegex(text, r"C:\\Users\\")

    def test_product_plan_connects_governance_observation_and_monitoring(self) -> None:
        text = PRODUCT_ARCHITECTURE_PLAN.read_text(encoding="utf-8")

        for phrase in (
            "Govern -> Observe -> Monitor",
            "Governance Registry",
            "Governance Router",
            "governance-event",
            "Monitor / Dashboard",
            "AGENTS.md",
            "AI_CONTEXT.md",
            "INVARIANTS.md",
            "Agent Skills",
            "PR/CI",
            "GitHub Release",
            "给 Claude 的 Review Prompt",
        ):
            self.assertIn(phrase, text)
        self.assertIn("不能自动宣称", text)
        self.assertIn("不得修改源码、Git index 或分支", text)
        self.assertIn("不在 v1 建立中央 SaaS telemetry 服务", text)
        self.assertIn("不落 `governance/registry.json`", text)
        self.assertIn("自然语言 scope 不参与 FAIL", text)
        self.assertIn("v1 禁止全文语义推断", text)
        self.assertIn("CI Dashboard 只能诚实显示 `ci_only`", text)
        self.assertIn("change-set digest", text)
        self.assertIn("文件 mtime 不能作为主要 freshness oracle", text)
        self.assertIn("`compact` 和 `standard` profile", text)
        self.assertIn("一个真实 Coding Agent 使用 context output", text)
        self.assertIn("Revision 3", text)
        self.assertIn("Revision 4", text)
        for provider_phrase in (
            "SemanticReviewProvider",
            "model-free",
            "self_review",
            "separate_pass",
            "isolated_context",
            "different_model",
            "different_provider",
            "不得静默降级",
            "用户或组织一次性配置",
            "API Key、Token、原始聊天",
            "Multi-Agent",
            "风险路由 ADR/contract",
            "ADR-0014",
            "三个严格契约",
            "当前 Agent self-review materializer",
            "ReferenceAlignmentAdapter",
            "规范化临时上下文",
            "安装宿主回调",
        ):
            self.assertIn(provider_phrase, text)
        self.assertIn("每个 working copy 一个 active task", text)
        self.assertIn("Phase 3 hard gate", text)

    def test_split_specs_fix_phase_two_and_three_policy_semantics(self) -> None:
        trigger_text = TRIGGER_ROUTING_SPEC.read_text(encoding="utf-8")
        evidence_text = FRESH_EVIDENCE_SPEC.read_text(encoding="utf-8")

        for phrase in (
            "path-segment boundaries",
            "must not use raw string `startswith`",
            "Exclusion always overrides inclusion",
            "both its old and new path",
            "Natural-language descriptions",
            "`architecture.candidate`",
            "Required Phase 2 policy tests",
        ):
            self.assertIn(phrase, trigger_text)

        for phrase in (
            "`comparison_base_sha`",
            "`snapshot_head_sha`",
            "git ls-files --others --exclude-standard",
            "tracked changes are never hidden",
            "changed tracked `.gitignore`",
            "`S0` immediately before",
            "edit -> commit -> validate -> govern finish",
            "A raw “digest mismatch” is insufficient",
            "Required Phase 3 policy tests",
        ):
            self.assertIn(phrase, evidence_text)

    def test_development_export_docs_preserve_privacy_and_claim_boundaries(self) -> None:
        text = DEVELOPMENT_EVENT_EXPORT.read_text(encoding="utf-8")

        for phrase in (
            "metadata_only_v1",
            "exact `EXPORT`",
            "Actor labels and local evidence references were removed",
            "cross-stage finding identity",
            "not telemetry",
            "does not add the artifact download, upload, retention, or workflow",
        ):
            self.assertIn(phrase, text)
        self.assertNotRegex(text, r"C:\\Users\\")


if __name__ == "__main__":
    unittest.main()
