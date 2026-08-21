import re
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
QUICKSTART_ZH = ROOT / "docs/quickstart.zh-CN.md"
QUICKSTART_WEB = ROOT / "docs/quickstart.html"
QUICKSTART_ZH_WEB = ROOT / "docs/quickstart.zh-CN.html"
INDEX_WEB = ROOT / "docs/index.html"
ADOPTION_GUIDE = ROOT / "docs/existing-repository-adoption.md"
GENERATED_FILES_GUIDE = ROOT / "docs/generated-files-guide.md"
TROUBLESHOOTING = ROOT / "docs/troubleshooting.md"
CONSUMER_CI = ROOT / "docs/consumer-ci.md"
DEVELOPMENT_MONITOR = ROOT / "docs/development-monitor.md"
DRIFT_REVIEW_REMINDERS = ROOT / "docs/drift-review-reminders.md"
DEVELOPMENT_SESSION = ROOT / "docs/development-session.md"
DEVELOPMENT_PLAN = ROOT / "docs/development-plan.md"
AUTOMATIC_PRODUCT_REQUIREMENTS = (
    ROOT / "docs/product-requirements-automatic-governance.md"
)
AUTOMATION_CONTRACTS = ROOT / "docs/development-automation-contracts.md"
CODEX_HOOKS_ADAPTER = ROOT / "docs/codex-hooks-adapter.md"
GOVERNANCE_MCP_ADAPTER = ROOT / "docs/governance-mcp-adapter.md"
TASK_PROPOSAL_ADMISSION = ROOT / "docs/task-proposal-admission.md"
ADMISSION_ROUTING = ROOT / "docs/admission-routing.md"
HUMAN_DECISIONS = ROOT / "docs/human-decision-prompts.md"
CLARIFICATION_DIALOGUE = ROOT / "docs/clarification-dialogue.md"
ACTIVE_AGENT_SELF_REVIEW = ROOT / "docs/active-agent-self-review.md"
DOCUMENTATION_ARCHIVE_PLAN = ROOT / "docs/documentation-archive-plan.md"
EXTRACTION_MAP = ROOT / "docs/ai-radar-extraction-map.md"
STATUS = ROOT / "STATUS.md"
HARNESS_GUIDE = ROOT / "docs/harness-contract-v1.md"
AIRBNB_HEADING_REPLAY = (
    ROOT / "docs/experiments/airbnb-uncoached-readme-heading-replay-2026-08-15.md"
)
AIRBNB_OWNER_REGRESSION_REPLAY = (
    ROOT
    / "docs/experiments/airbnb-adapter-1-5-owner-regression-replay-2026-08-16.md"
)
AIRBNB_NATIVE_COMPLETION_REPLAY_ATTEMPT = (
    ROOT
    / "docs/experiments/airbnb-native-completion-isolated-live-replay-2026-08-21.md"
)
AIRBNB_NATIVE_COMPLETION_END_TO_END_RECOVERY = (
    ROOT
    / "docs/experiments/airbnb-native-completion-end-to-end-recovery-2026-08-21.md"
)
CURRENT_NATIVE_COMPLETION_LOG = ROOT / "docs/development-log/2026-08-21.md"
ADAPTER_1_5_INSTALLED_PREFLIGHT = (
    ROOT / "docs/experiments/adapter-1-5-installed-preflight-2026-08-15.md"
)
CURRENT_DEVELOPMENT_LOG = ROOT / "docs/development-log/2026-08-15.md"
CURRENT_OWNER_REPLAY_LOG = ROOT / "docs/development-log/2026-08-16.md"
DISPOSABLE_INSTALLED_RESERVATION = (
    ROOT / "docs/experiments/disposable-installed-reservation-2026-08-17.md"
)
REPRODUCIBLE_LOCAL_WHEEL_BUILD = (
    ROOT / "docs/experiments/reproducible-local-wheel-build-2026-08-17.md"
)
WHEEL_BACKED_INSTALLED_RESERVATION = (
    ROOT / "docs/experiments/wheel-backed-installed-reservation-2026-08-17.md"
)
CONSUMER_COMPLETION_LOG = ROOT / "docs/development-log/2026-08-13.md"
HISTORICAL_MIGRATION_LOG = (
    ROOT / "docs/development-log/2026-08-14-historical-migration.md"
)
AGENT_SKILLS_README = ROOT / "agent-skills/README.md"
GUIDED_NEXT_ADR = ROOT / "docs/adr/0010-route-next-through-development-lifecycle.md"
BOOTSTRAP_UPDATE_ADR = ROOT / "docs/adr/0011-separate-bootstrap-from-update-routing.md"
SESSION_HANDOFF_ADR = ROOT / "docs/adr/0012-handoff-verified-development-sessions.md"
AUTOMATIC_EXPERIENCE_ADR = (
    ROOT / "docs/adr/0013-make-automatic-governance-and-dashboard-primary.md"
)
SEMANTIC_REVIEW_ADR = (
    ROOT / "docs/adr/0014-route-semantic-review-through-host-providers.md"
)
TASK_ADMISSION_ADR = (
    ROOT / "docs/adr/0015-use-mcp-elicitation-for-codex-task-admission.md"
)
KERNEL_BASELINE_ADR = (
    ROOT / "docs/adr/0016-establish-minimum-sufficient-kernel-architecture.md"
)
KERNEL_CLASSIFICATION = ROOT / "docs/kernel-boundary-classification-2026-08-10.md"
GOVERNANCE_MODEL = ROOT / "docs/governance-model.md"
DEVELOPMENT_RELEASE = ROOT / "release/current.json"
ISOLATED_EXECUTION_ADR = (
    ROOT / "docs/adr/0004-use-isolated-tool-execution-for-onboarding.md"
)
ISOLATED_EXECUTION_REHEARSAL = ROOT / "docs/isolated-tool-execution-rehearsal.md"
GUIDE_SCRIPT = ROOT / "docs/guide.js"
GUIDE_STYLE = ROOT / "docs/guide.css"
PUBLIC_JOURNEY_HTML = (
    "index.html",
    "portfolio.html",
    "quickstart.html",
    "quickstart.zh-CN.html",
    "interview-guide.html",
    "interview-guide.zh-CN.html",
    "existing-repository-adoption.html",
    "existing-repository-adoption.zh-CN.html",
    "generated-files-guide.html",
    "generated-files-guide.zh-CN.html",
    "troubleshooting.html",
    "troubleshooting.zh-CN.html",
    "demo-governance-report.html",
    "demo-governance-report.zh-CN.html",
)
PUBLIC_REFERENCE_SOURCES = (
    "drift-review-reminders.md",
    "human-decision-prompts.md",
    "clarification-dialogue.md",
    "product-requirements-automatic-governance.md",
    "development-task-contract.md",
    "development-context.md",
    "development-scope-check.md",
    "development-evidence.md",
    "specs/fresh-validation-evidence-v1.md",
    "consumer-ci.md",
    "clean-target-replay-preflight.md",
    "harness-contract-v1.md",
    "case-studies/0001-pr-center-architecture-drift.md",
    "adr/0009-govern-coding-agents-during-development.md",
    "governance-model.md",
    "ai-radar-extraction-map.md",
    "specs/development-trigger-routing-v1.md",
)


class UserDocumentationTests(unittest.TestCase):
    def test_readme_is_a_product_entry_not_an_evidence_archive(self) -> None:
        readme = README.read_text(encoding="utf-8")
        first_routes = readme[
            readme.index('<p align="center">') : readme.index("</p>")
        ]

        self.assertEqual(first_routes.count("<a href="), 3)
        for anchor in ("#quickstart", "#governed-example", "#architecture"):
            self.assertIn(anchor, first_routes)
        self.assertIn("## Product overview", readme)
        self.assertNotIn("## Interview snapshot", readme)
        self.assertNotIn("## Runnable CLI example", readme)
        self.assertNotIn("## Detailed architecture", readme)
        self.assertNotIn("## Project navigation", readme)
        self.assertEqual(readme.count("```mermaid"), 1)

        overview = readme[: readme.index("## Why AgentGov")]
        for channel in ("Stable `0.2.1`", "Published prerelease `0.3.0rc1`", "Current development source"):
            self.assertIn(channel, overview)
        self.assertIn("`repository:git-access`", readme)

        for owner in (
            "STATUS.md",
            "docs/development-log/INDEX.md",
            "docs/governance-model.md",
            "docs/interview-guide.md",
            "docs/portfolio.html",
        ):
            self.assertIn(f"]({owner})", readme)
        for historical_detail in (
            "setuptools 65.5.0",
            "setuptools 84.0.0",
            "all 79 tests",
            "all 68 tests",
            "BLOCKED_BEFORE_MODEL_MCP_INITIALIZATION",
        ):
            self.assertNotIn(historical_detail, readme)

    def test_native_proposal_owner_binding_is_adapter_owned_and_bounded(self) -> None:
        readme = README.read_text(encoding="utf-8")
        detailed_sources = tuple(
            path.read_text(encoding="utf-8")
            for path in (
                GOVERNANCE_MCP_ADAPTER,
                TASK_PROPOSAL_ADMISSION,
                TASK_ADMISSION_ADR,
            )
        )
        for text in detailed_sources:
            with self.subTest(source=text[:40]):
                self.assertIn("1.5.0", text)
                self.assertIn("Human product owner", text)
                self.assertIn("owner", text)
                self.assertIn("decided_by", text)
        for text in detailed_sources:
            self.assertIn("cryptographic", text.lower())
        self.assertIn("](docs/governance-mcp-adapter.md)", readme)
        self.assertIn("](docs/task-proposal-admission.md)", readme)
        self.assertNotIn("Adapter `1.5.0`", readme)

        for quickstart in (QUICKSTART_WEB, QUICKSTART_ZH_WEB):
            text = quickstart.read_text(encoding="utf-8")
            self.assertIn(
                "blob/main/docs/governance-mcp-adapter.md",
                text,
            )
            self.assertNotIn("Adapter <code>1.5.0</code>", text)
            self.assertNotIn("decided_by", text)

        landing = INDEX_WEB.read_text(encoding="utf-8")
        self.assertNotIn("Adapter <code>1.5.0</code>", landing)
        self.assertNotIn("cryptographic personal identity", landing)
        self.assertIn("portfolio.html#boundary", landing)
        self.assertIn("blob/main/STATUS.md", landing)

    def test_adapter_1_5_local_installation_is_evidenced_without_overclaim(self) -> None:
        readme = README.read_text(encoding="utf-8")
        evidence = ADAPTER_1_5_INSTALLED_PREFLIGHT.read_text(encoding="utf-8")
        detailed_surfaces = tuple(
            path.read_text(encoding="utf-8")
            for path in (
                GOVERNANCE_MCP_ADAPTER,
                TASK_ADMISSION_ADR,
            )
        )
        for text in detailed_surfaces:
            with self.subTest(source=text[:40]):
                self.assertIn("1.5.0", text)
                self.assertIn("pipx", text)
                self.assertIn("Human product owner", text)
        for quickstart in (QUICKSTART_WEB, QUICKSTART_ZH_WEB):
            text = quickstart.read_text(encoding="utf-8")
            self.assertIn("blob/main/docs/governance-mcp-adapter.md", text)
            self.assertNotIn("1.5.0", text)
            self.assertNotIn("Human product owner", text)
        landing = INDEX_WEB.read_text(encoding="utf-8")
        self.assertNotIn("Adapter <code>1.5.0</code>", landing)
        self.assertNotIn("Current development evidence", landing)
        self.assertNotIn("Trace the latest evidence chain", landing)
        self.assertIn('href="portfolio.html#boundary"', landing)
        self.assertIn("See current evidence and limits", landing)
        for phrase in (
            "local-only",
            "no-model",
            "seven/form",
            "five/base",
            "hostile-owner",
            "accepted-admit",
            "project configuration",
            "backups",
            "live replay",
        ):
            self.assertIn(phrase, " ".join(evidence.split()))
        self.assertIn("](docs/governance-mcp-adapter.md)", readme)
        self.assertNotIn("Adapter `1.5.0`", readme)
        self.assertIn("consumer", evidence)

    def test_documentation_archive_plan_is_read_only_and_explicit(self) -> None:
        readme = README.read_text(encoding="utf-8")
        guide = DOCUMENTATION_ARCHIVE_PLAN.read_text(encoding="utf-8")
        normalized = " ".join(guide.split())

        self.assertIn("docs/documentation-archive-plan.md", readme)
        self.assertNotIn("agentgov plan documentation-archive", readme)
        self.assertIn(
            "agentgov plan documentation-archive . --through 2026-08-14",
            guide,
        )
        for phrase in (
            "never consults the host clock",
            "logical inclusion",
            "human-facing candidate",
            "machine-verifiable",
            "never moves, renames, deletes, or rewrites",
            "deterministic",
            "advisory",
            "read-only by default",
            "requires a real interactive terminal",
            "APPLY INDEX",
            "never opens a dated log for write",
            "grants no scheduling, Git, publication, release, or deployment authority",
        ):
            self.assertIn(phrase, normalized)

    def test_documentation_state_separation_contract_is_consistent(self) -> None:
        instructions = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        plan = (ROOT / "DEVELOPMENT_PLAN.md").read_text(encoding="utf-8")
        public_plan = DEVELOPMENT_PLAN.read_text(encoding="utf-8")
        status = STATUS.read_text(encoding="utf-8")

        self.assertIn("## Documentation state ownership", instructions)
        self.assertIn("strategic development plan", plan)
        self.assertIn(
            "Do not add new session-level history to this plan",
            " ".join(plan.split()),
        )
        self.assertIn("## Documentation state contract", public_plan)
        self.assertIn("## Current-status contract", status)

        normalized_status = " ".join(status.split())
        for phrase in (
            "single current-execution status surface",
            "Codex-run validation",
            "User-reported validation",
            "Pending validation",
            "Incomplete",
            "Next product review",
            "Historical Documentation Migration v1",
        ):
            self.assertIn(phrase, normalized_status)

        for surface in (instructions, plan, public_plan, status):
            normalized = " ".join(surface.split())
            self.assertIn("governance/tasks", normalized)
            self.assertIn("docs/development-log/", normalized)

    def test_historical_documentation_migration_preserves_ownership(self) -> None:
        plan = (ROOT / "DEVELOPMENT_PLAN.md").read_text(encoding="utf-8")
        public_plan = DEVELOPMENT_PLAN.read_text(encoding="utf-8")
        status = STATUS.read_text(encoding="utf-8")
        migration_log = HISTORICAL_MIGRATION_LOG.read_text(encoding="utf-8")
        normalized_migration_log = " ".join(migration_log.split())

        self.assertIn("## Historical checkpoint index", status)
        self.assertIn("## Current-state reference", plan)
        self.assertIn("## Next product review reference", plan)
        self.assertIn("## Current checkpoint reference", public_plan)
        self.assertIn("## Next product review reference", public_plan)

        for heading in (
            "## Development checkpoint - 2026-08-06",
            "## Development checkpoint - 2026-08-05",
        ):
            self.assertNotIn(heading, status)
        for heading in (
            "## Current State",
            "## Foundation implementation history",
            "## Next Recommended Starting Point",
        ):
            self.assertNotIn(heading, plan)
        for heading in (
            "## Current checkpoint",
            "## Next-session starting point",
        ):
            self.assertNotIn(f"{heading}\n", public_plan)

        for phrase in (
            "not a claim that the older events occurred on this date",
            "No existing development-log path was renamed or rewritten",
            "grants no task or external authority",
        ):
            self.assertIn(phrase, normalized_migration_log)

        for phrase in (
            "### Development checkpoint - 2026-08-06",
            "### Development checkpoint - 2026-08-05",
            "### Current State",
            "### Foundation implementation history",
            "### Next Recommended Starting Point",
            "### Current checkpoint",
            "### Next-session starting point",
        ):
            self.assertIn(phrase, migration_log)

    def test_airbnb_completion_and_handoff_evidence_is_bounded(self) -> None:
        readme = README.read_text(encoding="utf-8")
        surfaces = (
            STATUS,
            HISTORICAL_MIGRATION_LOG,
            CONSUMER_COMPLETION_LOG,
        )

        self.assertIn("](STATUS.md)", readme)
        self.assertNotIn("all 79 tests", readme)

        self.assertTrue(CONSUMER_COMPLETION_LOG.is_file())
        for path in surfaces:
            text = path.read_text(encoding="utf-8")
            normalized = " ".join(text.split())
            with self.subTest(path=path.name):
                self.assertIn("AIRBNB", normalized)
                self.assertIn("Python 3.11.9", normalized)
                self.assertIn("Completion Verified", normalized)
                self.assertIn("Bounded Handoff", normalized)
                self.assertIn("product effectiveness", normalized)
                self.assertIn("independent review", normalized)
                self.assertIn("uncommitted and unpushed", normalized)

        log = CONSUMER_COMPLETION_LOG.read_text(encoding="utf-8")
        for phrase in (
            "5 delivery tests",
            "13 serving tests",
            "79-test suite",
            "proposal-only",
            "bounded advisory review",
            "not independent evidence",
            "not yet decided",
        ):
            self.assertIn(phrase, log)

    def test_airbnb_uncoached_heading_replay_keeps_evidence_sources_and_gaps_separate(self) -> None:
        surfaces = (
            STATUS,
            HARNESS_GUIDE,
            AIRBNB_HEADING_REPLAY,
            CURRENT_DEVELOPMENT_LOG,
        )

        self.assertTrue(AIRBNB_HEADING_REPLAY.is_file())
        for path in surfaces:
            normalized = " ".join(path.read_text(encoding="utf-8").split())
            with self.subTest(path=path.name):
                self.assertIn("human_owner_misattributed", normalized)
                self.assertIn("Completion Verified", normalized)
                self.assertIn("Bounded Handoff", normalized)
                self.assertIn("not", normalized.lower())

        experiment = AIRBNB_HEADING_REPLAY.read_text(encoding="utf-8")
        for phrase in (
            "Codex-read repository facts",
            "Human-reported interaction fact",
            "human_origin_assurance: unavailable",
            "First Deviation",
            "does not authorize a fix or another replay",
        ):
            self.assertIn(phrase, experiment)

    def test_airbnb_owner_regression_replay_preserves_precondition_failure(self) -> None:
        surfaces = (
            STATUS,
            HARNESS_GUIDE,
            AIRBNB_OWNER_REGRESSION_REPLAY,
            CURRENT_OWNER_REPLAY_LOG,
        )

        self.assertTrue(AIRBNB_OWNER_REGRESSION_REPLAY.is_file())
        for path in surfaces:
            normalized = " ".join(path.read_text(encoding="utf-8").split())
            with self.subTest(path=path.name):
                self.assertIn("preexisting_replay_state_not_cleared", normalized)
                self.assertIn("form", normalized.lower())
                self.assertIn("Completion Verified", normalized)
                self.assertIn("Bounded Handoff", normalized)

        experiment = AIRBNB_OWNER_REGRESSION_REPLAY.read_text(encoding="utf-8")
        for phrase in (
            "Human-visible completion evidence",
            "Human-reported interaction fact",
            "Codex-read repository facts",
            "no identifiable new repository state",
            "cannot evaluate whether installed Adapter 1.5.0",
            "authorizes no AIRBNB correction",
        ):
            self.assertIn(phrase, experiment)

    def test_airbnb_native_completion_replay_preserves_install_block(self) -> None:
        readme = README.read_text(encoding="utf-8")
        surfaces = (
            STATUS,
            GOVERNANCE_MCP_ADAPTER,
            AUTOMATIC_PRODUCT_REQUIREMENTS,
            AIRBNB_NATIVE_COMPLETION_REPLAY_ATTEMPT,
            CURRENT_NATIVE_COMPLETION_LOG,
        )

        self.assertIn("](STATUS.md)", readme)
        self.assertIn("](docs/governance-mcp-adapter.md)", readme)
        self.assertNotIn("setuptools 65.5.0", readme)

        self.assertTrue(AIRBNB_NATIVE_COMPLETION_REPLAY_ATTEMPT.is_file())
        for path in surfaces:
            normalized = " ".join(path.read_text(encoding="utf-8").split())
            with self.subTest(path=path.name):
                self.assertIn("setuptools 65.5.0", normalized)
                self.assertIn("setuptools>=69", normalized)
                self.assertIn("agentgov_task_completion_record", normalized)
                self.assertIn("no", normalized.lower())

        experiment = AIRBNB_NATIVE_COMPLETION_REPLAY_ATTEMPT.read_text(
            encoding="utf-8"
        )
        normalized_experiment = " ".join(experiment.split())
        for phrase in (
            "BLOCKED_BEFORE_INSTALLATION",
            "No AgentGov development package was installed",
            "zero remotes",
            "No compatible build dependency was available",
            "no MCP process or Codex session started",
            "contains no raw prompt",
            "authorizes no dependency download",
        ):
            self.assertIn(phrase, normalized_experiment)

    def test_airbnb_native_completion_end_to_end_recovery_is_bounded(self) -> None:
        readme = README.read_text(encoding="utf-8")
        surfaces = (
            STATUS,
            GOVERNANCE_MCP_ADAPTER,
            AUTOMATIC_PRODUCT_REQUIREMENTS,
            AIRBNB_NATIVE_COMPLETION_END_TO_END_RECOVERY,
            CURRENT_NATIVE_COMPLETION_LOG,
        )

        self.assertIn("](STATUS.md)", readme)
        self.assertIn("](docs/governance-mcp-adapter.md)", readme)
        self.assertNotIn("setuptools 84.0.0", readme)

        self.assertTrue(AIRBNB_NATIVE_COMPLETION_END_TO_END_RECOVERY.is_file())
        for path in surfaces:
            normalized = " ".join(path.read_text(encoding="utf-8").split())
            with self.subTest(path=path.name):
                self.assertIn("setuptools 84.0.0", normalized)
                self.assertIn("Adapter `1.6.0`", normalized)
                self.assertIn("BLOCKED_BEFORE_MODEL_MCP_INITIALIZATION", normalized)
                self.assertIn("-32603", normalized)

        experiment = AIRBNB_NATIVE_COMPLETION_END_TO_END_RECOVERY.read_text(
            encoding="utf-8"
        )
        normalized_experiment = " ".join(experiment.split())
        for phrase in (
            "eight tools with form elicitation and six without it",
            "The completion tool exposed only `task_path`",
            "No usable session or Agent turn followed",
            "No native proposal form",
            "The README still contains `### One-command demo`",
            "contains no raw prompt",
            "No commit, push, pull request, publication, release, deployment",
        ):
            self.assertIn(phrase, normalized_experiment)

    def test_nyc_completion_and_handoff_evidence_is_bounded(self) -> None:
        readme = README.read_text(encoding="utf-8")
        surfaces = (
            STATUS,
            HISTORICAL_MIGRATION_LOG,
            CONSUMER_COMPLETION_LOG,
        )

        self.assertIn("](STATUS.md)", readme)
        self.assertNotIn("all 68 tests", readme)

        for path in surfaces:
            normalized = " ".join(path.read_text(encoding="utf-8").split())
            with self.subTest(path=path.name):
                self.assertIn("NYC", normalized)
                self.assertIn("Python 3.11.9", normalized)
                self.assertIn("68", normalized)
                self.assertIn("Completion Verified", normalized)
                self.assertIn("Bounded Handoff", normalized)
                self.assertIn("formal CI remains on AgentGov 0.2.1", normalized)
                self.assertIn("not a formal upgrade", normalized)
                self.assertIn("product effectiveness", normalized)
                self.assertIn("uncommitted and unpushed", normalized)

        log = CONSUMER_COMPLETION_LOG.read_text(encoding="utf-8")
        for phrase in (
            "Bronze partition",
            "built Silver",
            "demand quality gate",
            "non-empty Gold lineage",
            "complete 68-test NYC suite",
            "already_handed_off",
            "not yet decided",
        ):
            self.assertIn(phrase, log)

    def test_minimum_sufficient_kernel_baseline_is_consistent_and_bounded(self) -> None:
        readme = README.read_text(encoding="utf-8")
        status = STATUS.read_text(encoding="utf-8")
        plan = DEVELOPMENT_PLAN.read_text(encoding="utf-8")
        governance_model = GOVERNANCE_MODEL.read_text(encoding="utf-8")
        decision = KERNEL_BASELINE_ADR.read_text(encoding="utf-8")
        classification = KERNEL_CLASSIFICATION.read_text(encoding="utf-8")

        for path in (KERNEL_BASELINE_ADR, KERNEL_CLASSIFICATION):
            self.assertTrue(path.is_file())

        for text in (readme, status, plan, governance_model, decision):
            self.assertIn("minimum sufficient Kernel", text)
            self.assertIn("Completion Verified", text)
            self.assertIn("Bounded Handoff", text)

        for phrase in (
            "Observe concretely",
            "Use the minimum sufficient abstraction",
            "Capability is not Authority",
            "Declared is not Configured",
            "Detected is not Prevented",
            "Self-authored Semantic Assertion is not Independent Evidence",
            "Attempted Transition is not Completed Transition",
            "Learning Candidate is not Admitted Learning",
            "necessity",
            "independence",
            "authority integrity",
            "evidence sufficiency",
            "Application / Product Surface",
            "Consumer Context",
            "Enforcement",
            "OBSERVE",
            "ADVISE",
            "MEDIATE",
            "BLOCK",
            "not a universal control plane",
            "structured counterexample",
        ):
            self.assertIn(phrase.lower(), decision.lower())

        for phrase in (
            "diagnostic snapshot",
            "not a permanent",
            "positive case",
            "negative case",
            "no current family demonstrates a missing Kernel concept",
        ):
            self.assertIn(phrase.lower(), classification.lower())

        combined = "\n".join((decision, classification, status, plan)).lower()
        for excluded_change in (
            "no runtime",
            "schema",
            "external consumer",
            "required-check",
            "branch protection",
        ):
            self.assertIn(excluded_change, combined)

    def test_automatic_governance_and_dashboard_are_the_primary_direction(self) -> None:
        readme = README.read_text(encoding="utf-8")
        status = STATUS.read_text(encoding="utf-8")
        plan = DEVELOPMENT_PLAN.read_text(encoding="utf-8")
        requirements = AUTOMATIC_PRODUCT_REQUIREMENTS.read_text(encoding="utf-8")
        decision = AUTOMATIC_EXPERIENCE_ADR.read_text(encoding="utf-8")
        semantic_review_decision = SEMANTIC_REVIEW_ADR.read_text(encoding="utf-8")
        session = DEVELOPMENT_SESSION.read_text(encoding="utf-8")
        monitor = DEVELOPMENT_MONITOR.read_text(encoding="utf-8")
        automation = AUTOMATION_CONTRACTS.read_text(encoding="utf-8")
        codex = CODEX_HOOKS_ADAPTER.read_text(encoding="utf-8")
        governance_mcp = GOVERNANCE_MCP_ADAPTER.read_text(encoding="utf-8")
        proposal_admission = TASK_PROPOSAL_ADMISSION.read_text(encoding="utf-8")
        admission_routing = ADMISSION_ROUTING.read_text(encoding="utf-8")
        human_decisions = HUMAN_DECISIONS.read_text(encoding="utf-8")
        clarification = CLARIFICATION_DIALOGUE.read_text(encoding="utf-8")
        active_agent_review = ACTIVE_AGENT_SELF_REVIEW.read_text(encoding="utf-8")
        codex_compact = " ".join(codex.split())
        governance_mcp_compact = " ".join(governance_mcp.split())

        for path in (
            AUTOMATIC_PRODUCT_REQUIREMENTS,
            AUTOMATIC_EXPERIENCE_ADR,
            SEMANTIC_REVIEW_ADR,
        ):
            self.assertTrue(path.is_file())

        for text in (readme, status, plan, requirements, decision):
            self.assertIn("automatic", text.lower())
            self.assertIn("Dashboard", text)

        for text in (readme, plan, requirements, decision, session):
            self.assertIn("fallback", text)

        alignment_docs = " ".join(
            "\n".join(
                (
                    readme,
                    status,
                    requirements,
                    decision,
                    semantic_review_decision,
                    automation,
                    clarification,
                    active_agent_review,
                )
            ).split()
        )
        for phrase in (
            "Live Sessions",
            "Protection Events",
            "Benefit",
            "Learning",
            "observed_fact",
            "reproduced_comparison",
            "supported_inference",
            "human_feedback",
            "unknown",
        ):
            self.assertIn(phrase, requirements)

        primary_p0 = " ".join(
            plan[
                plan.index("### P0 — automate the primary product experience") :
                plan.index(
                    "### P0 foundation — govern the coding agent during development"
                )
            ].split()
        )
        self.assertIn("independent non-NYC", primary_p0)
        self.assertLess(
            primary_p0.index("independent non-NYC"),
            primary_p0.index("NYC shadow"),
        )
        self.assertIn("not yet implemented as the primary", requirements)
        self.assertIn("not yet implemented", decision)
        self.assertIn("not yet implemented", monitor)
        for text in (readme, status, plan, requirements, decision, session, automation):
            self.assertIn("agentgov dev", text)
        self.assertIn("agentgov.foreground-cycle", automation)
        self.assertIn("live jsonl", " ".join(automation.lower().split()))
        self.assertIn("agentgov dev --stream", automation)
        self.assertIn("agentgov.coding-agent-event", automation)
        self.assertIn("task/scope/completion cards", status)
        for phrase in (
            "agentgov.host-interaction-capabilities",
            "agentgov.host-interaction-request",
            "context-only",
            "PermissionRequest",
        ):
            self.assertIn(phrase, "\n".join((status, automation, codex)))
        self.assertIn("returns neither `allow` nor `deny`", codex_compact)
        self.assertIn("recorded product drift", codex_compact)
        for text in (readme, status, plan, requirements, decision, session, automation):
            self.assertIn("Codex", text)
        for phrase in (
            "agentgov integrate codex-hooks . --dry-run",
            "create-missing-only",
            "stop_hook_active",
            "PostToolUse",
            "does not grant hook trust",
        ):
            self.assertIn(phrase, codex_compact)
        self.assertIn("docs/codex-hooks-adapter.md", readme)
        for phrase in (
            "agentgov.task-proposal",
            "agentgov.task-admission-plan",
            "agentgov propose task",
            "ADMIT",
            "does not start",
            "raw prompt",
        ):
            self.assertIn(phrase, "\n".join((readme, status, automation, proposal_admission)))
        self.assertIn("docs/task-proposal-admission.md", readme)
        for phrase in (
            "agentgov.work-request",
            "agentgov.admission-routing-policy",
            "agentgov.admission-route",
            "observe_only",
            "continue_active",
            "fast_track",
            "human_review",
            "full_review",
            "zero interruptions",
        ):
            self.assertIn(
                phrase,
                "\n".join((readme, status, automation, admission_routing)),
            )
        self.assertIn("docs/admission-routing.md", readme)
        for phrase in (
            "agentgov.human-decision-prompt",
            "agentgov.human-decision-result",
            "single-select",
            "no free text",
            "--prompt-human",
            "one number",
            "context_only",
            "unavailable",
        ):
            self.assertIn(
                phrase,
                "\n".join((readme, status, automation, admission_routing, human_decisions)),
            )
        self.assertIn("docs/human-decision-prompts.md", readme)
        for phrase in (
            "agentgov.alignment-context",
            "agentgov.clarification-dialogue",
            "one natural-language question",
            "governance decision episodes",
            "not a semantic conversation limit",
            "Business, requirement, and architecture drift",
            "does not edit requirements or ADRs",
        ):
            self.assertIn(phrase, alignment_docs)
        self.assertIn("docs/clarification-dialogue.md", readme)
        for phrase in (
            "agentgov.coding-agent-alignment-response",
            "foreground_memory",
            "survives_restart=false",
            "same `agentgov dev --stream` connection",
            "do not invoke the development lifecycle coordinator",
            "Coding Agent Adapter remains responsible",
            "ReferenceAlignmentAdapter",
            "HostSemanticMaterializer",
            "zero user-authored structured records",
            "not a claim that Core performs semantic inference",
            "model-free",
            "zero-configuration",
            "optional independent Reviewer",
            "silently downgrade",
            "lower-assurance",
            "Provider credentials",
            "agentgov.semantic-review-provider-capabilities",
            "agentgov.semantic-review-route",
            "agentgov.semantic-review-result",
            "digest-bound",
            "not model integrations",
            "ActiveAgentSelfReviewMaterializer",
            "resolved `ReferenceAlignmentAdapter`",
            "evidence allow-list",
            "production host callback",
        ):
            self.assertIn(phrase, alignment_docs)
        self.assertIn("docs/active-agent-self-review.md", readme)
        for phrase in (
            "agentgov integrate codex-mcp . --dry-run",
            "foreground STDIO MCP",
            "exactly six tools",
            "journey handle",
            "zero model and network calls",
            "do not prove that a production model will always choose the right tool",
            "live uncoached Codex session",
            "independent high-risk Reviewer",
        ):
            self.assertIn(phrase, governance_mcp_compact)
        for text in (automation, governance_mcp, proposal_admission):
            self.assertIn("agentgov_task_proposal_review", text)
        for text in (governance_mcp,):
            self.assertIn("Adapter `1.6.0`", text)
            self.assertIn("agentgov_task_completion_record", text)
            self.assertIn("eight tools", text)
            self.assertIn("sixth base tool", text)
        for text in (governance_mcp, proposal_admission):
            normalized_text = " ".join(text.split())
            self.assertIn("exact requested repository change", normalized_text)
            self.assertIn("measurement-only", normalized_text)
            self.assertIn("Read-only work does not trigger proposal review", normalized_text)
            self.assertIn("cannot force a model", normalized_text)
        self.assertIn("agentgov.task-proposal-review-result", proposal_admission)
        self.assertIn("six base tools", automation)
        self.assertNotIn("five fixed tools", automation)
        self.assertNotIn("every tool remains advisory/read-only", automation)
        self.assertNotIn(
            "Production natural-language task drafting, a native authenticated decision surface",
            requirements,
        )
        self.assertIn("Development Codex Adapter `1.3.0`", requirements)
        self.assertIn("native MCP form elicitation", session)
        self.assertIn("docs/governance-mcp-adapter.md", readme)

        for forbidden_primary_action in (
            "hand-author internal JSON",
            "repeated `next` queries",
            "manual lifecycle command composition",
            "special confirmation words",
        ):
            self.assertIn(
                forbidden_primary_action,
                " ".join(requirements.split()),
            )

    def test_public_quickstarts_label_the_automatic_direction_as_future(self) -> None:
        english = QUICKSTART_WEB.read_text(encoding="utf-8")
        chinese = QUICKSTART_ZH_WEB.read_text(encoding="utf-8")

        self.assertIn("Development preview", english)
        self.assertIn("fresh uncoached primary-product pilot remains unproven", english)
        self.assertIn("开发预览", chinese)
        self.assertIn("无指导主要产品真人试用仍未证明", chinese)
        for text in (english, chinese):
            self.assertIn("product-requirements-automatic-governance.html", text)
            self.assertIn("portfolio.html#boundary", text)
            self.assertIn("blob/main/docs/governance-mcp-adapter.md", text)
            self.assertIn("clean-target-replay-preflight.html", text)
            self.assertIn("drift-review-reminders.html", text)
            self.assertIn("0.2.1", text)
            self.assertIn("0.3.0rc1", text)
            self.assertNotIn("agentgov dev", text)
            self.assertNotIn("agentgov_task_proposal_review", text)
            self.assertNotIn("agentgov_drift_review_record", text)
            self.assertNotIn("Adapter <code>1.5.0</code>", text)

    def test_development_governance_sources_resist_pr_center_drift(self) -> None:
        readme = README.read_text(encoding="utf-8")
        status = STATUS.read_text(encoding="utf-8")
        plan = DEVELOPMENT_PLAN.read_text(encoding="utf-8")
        extraction = EXTRACTION_MAP.read_text(encoding="utf-8")
        skills = AGENT_SKILLS_README.read_text(encoding="utf-8")

        for skill_name in (
            "requirement-admission",
            "action-loop-stagnation",
            "reconcile-invariants",
        ):
            for text in (readme, status, skills):
                with self.subTest(skill=skill_name):
                    self.assertIn(skill_name, text)

        self.assertIn("automatic coding-agent loop", readme)
        self.assertIn("independent backstop", readme)
        self.assertIn(
            "first planned real-consumer development-loop shadow",
            status,
        )
        self.assertIn(
            "NYC development-loop shadow pilot",
            " ".join(plan.split()),
        )
        self.assertIn("before any PR or CI migration", plan)
        self.assertIn("NYC Taxi development-loop pilot boundary", extraction)
        self.assertIn("historical backstop evidence", extraction)
        self.assertIn("not a mechanical runtime halt", readme)

    def test_verified_session_handoff_contract_preserves_identity_and_authority(self) -> None:
        readme = README.read_text(encoding="utf-8")
        session = DEVELOPMENT_SESSION.read_text(encoding="utf-8")
        monitor = DEVELOPMENT_MONITOR.read_text(encoding="utf-8")
        decision = SESSION_HANDOFF_ADR.read_text(encoding="utf-8")

        self.assertIn("`Completion Verified` and `Bounded Handoff`", readme)
        self.assertIn("](docs/development-session.md)", readme)
        self.assertIn("implements ADR-0012", session)
        self.assertIn("Monitor schema 1.4", monitor)
        for text in (session,):
            self.assertIn("govern handoff --repository . --dry-run", text)
            self.assertIn("exact", text)
            self.assertIn("HANDOFF", text)
            self.assertIn("--replace-active", text)
        for phrase in (
            "session.handed_off",
            "exact `HANDOFF`",
            "does not delete",
            "matching existing handoff is idempotent",
            "--replace-active",
            "same handed-off task digest",
            "does not prove that a human read it",
            "one append-only target",
            "Development-source runtime now implements",
        ):
            self.assertIn(phrase, decision)
        self.assertNotIn("govern handoff --repository . --dry-run", readme)
        self.assertIn("Published\nstable 0.2.1 does not include", session)

    def test_bootstrap_and_update_decision_has_no_self_install_or_fake_release(self) -> None:
        readme = README.read_text(encoding="utf-8")
        decision = BOOTSTRAP_UPDATE_ADR.read_text(encoding="utf-8")
        quickstart = QUICKSTART_WEB.read_text(encoding="utf-8")
        development_release = DEVELOPMENT_RELEASE.read_text(encoding="utf-8")

        stable_install = 'pipx install "https://github.com/Andy-JunXiong/'
        self.assertLess(readme.index(stable_install), readme.index("agentgov next ."))
        self.assertLess(quickstart.index(stable_install), quickstart.index('id="development"'))
        for text in (readme, decision):
            self.assertIn("agentgov update --check", text)
            self.assertIn("before `agentgov next`", text)
        for phrase in (
            "fixed-tag HTTPS wheel URL",
            "artifact: null",
            "terminal handoff",
            "read-only check alone is not treated as progress",
            "never executes the recommendation",
        ):
            self.assertIn(phrase, decision)
        self.assertIn('"channel": "release-candidate"', development_release)
        self.assertIn('"artifact": null', development_release)

    def test_guided_next_docs_preserve_precedence_and_no_execution_boundary(self) -> None:
        readme = README.read_text(encoding="utf-8")
        session = DEVELOPMENT_SESSION.read_text(encoding="utf-8")
        decision = GUIDED_NEXT_ADR.read_text(encoding="utf-8")

        for text in (session, decision):
            self.assertIn("govern start", text)
            self.assertIn("govern check", text)
            self.assertIn("govern finish", text)
            self.assertIn("monitor development", text)
            self.assertIn("deterministic repository `FAIL`", text)
            self.assertRegex(text.lower(), r"multiple admitted\s+tasks")
        self.assertIn("](docs/development-session.md)", readme)
        self.assertNotIn("action_executed=false", readme)
        self.assertIn("action_executed=false", session)
        self.assertIn("never executes", decision)
        self.assertIn("Older events", decision)

    def test_development_monitor_artifact_docs_preserve_opt_in_and_source_boundaries(self) -> None:
        readme = README.read_text(encoding="utf-8")
        monitor = DEVELOPMENT_MONITOR.read_text(encoding="utf-8")
        consumer_ci = CONSUMER_CI.read_text(encoding="utf-8")

        for text in (monitor, consumer_ci):
            self.assertIn("publish_development_monitor", text)
            self.assertIn("agentgov-development-monitor.html", text)
            self.assertIn("default-off", text)
            self.assertIn("development_export", text)
        self.assertIn("](docs/development-monitor.md)", readme)
        self.assertNotIn("publish_development_monitor", readme)
        self.assertIn("future 0.3", monitor)
        self.assertIn("never uploads the development export", monitor)
        self.assertIn("actor-validated CI event files", monitor)
        self.assertIn("raw events, or `.agentgov/` local state", consumer_ci)

    def test_readme_links_all_user_onboarding_guides(self) -> None:
        text = README.read_text(encoding="utf-8")
        for path in (
            QUICKSTART_WEB,
            QUICKSTART_ZH_WEB,
            QUICKSTART_ZH,
            ADOPTION_GUIDE,
            GENERATED_FILES_GUIDE,
            TROUBLESHOOTING,
            CODEX_HOOKS_ADAPTER,
            GOVERNANCE_MCP_ADAPTER,
        ):
            relative = path.relative_to(ROOT).as_posix()
            with self.subTest(path=relative):
                self.assertTrue(path.is_file())
                self.assertIn(f"]({relative})", text)

    def test_existing_repository_guide_covers_safe_end_to_end_workflow(self) -> None:
        text = ADOPTION_GUIDE.read_text(encoding="utf-8")
        for required in (
            "agentgov inspect path/to/repository",
            "--format json",
            '--project-name "Example Project" --dry-run',
            "agentgov check repository path/to/repository",
            "agentgov report repository path/to/repository",
            "Existing files are not rewritten",
            "does not stage or commit",
            "Completion checklist",
        ):
            self.assertIn(required, text)
        self.assertIn("merge, publication, release, or deployment", text)

    def test_chinese_quickstart_preserves_finding_and_authority_semantics(self) -> None:
        text = QUICKSTART_ZH.read_text(encoding="utf-8")
        for status in ("`PRESENT`", "`MISSING`", "`DISCOVERED`", "`CONFLICT`"):
            self.assertIn(status, text)
        self.assertIn("--dry-run", text)
        self.assertIn("不覆盖已有普通文件", text)
        self.assertIn("不授权合并、发布、release 或部署", text)

    def test_generated_files_guide_keeps_evidence_claims_honest(self) -> None:
        text = GENERATED_FILES_GUIDE.read_text(encoding="utf-8")
        for heading in (
            "## AGENTS.md",
            "## docs/adr/TEMPLATE.md",
            "## docs/adr/INVARIANTS.md",
            "## governance/capabilities",
            "## evaluation",
            "## agent-skills",
            "## governance/artifacts",
        ):
            self.assertIn(heading, text)
        self.assertIn("does not execute models or judge model-output quality", text)
        self.assertIn("does not prove that the content is correct or approved", text)

    def test_troubleshooting_distinguishes_findings_and_exit_codes(self) -> None:
        text = TROUBLESHOOTING.read_text(encoding="utf-8")
        for heading in (
            "## Windows wheel build fails with `No such file or directory`",
            "## The virtual environment points to a missing Python",
            "## `check` says `invalid choice: '.'`",
            "## `inspect` reports `MISSING`",
            "## `inspect` or `adopt` reports `CONFLICT`",
            "## Repository check returns WARN",
            "## Repository check returns ADVISORY",
            "## Repository check returns FAIL",
            "## Exit codes",
        ):
            self.assertIn(heading, text)
        self.assertIn("No exit code grants approval", text)
        self.assertIn("agentgov check repository .", text)
        self.assertIn("is not valid syntax", text)

    def test_isolated_execution_decision_preserves_environment_boundaries(
        self,
    ) -> None:
        decision = ISOLATED_EXECUTION_ADR.read_text(encoding="utf-8")
        rehearsal = ISOLATED_EXECUTION_REHEARSAL.read_text(encoding="utf-8")

        for command in (
            'pipx install "git+https://github.com/'
            'Andy-JunXiong/agent-governance-starter.git@main"',
            "pipx upgrade agent-governance-starter",
            "pipx uninstall agent-governance-starter",
        ):
            self.assertIn(command, decision)
        self.assertIn("not a stable\nrelease pin", decision)
        self.assertIn("Repairing, replacing, or activating a target project's `.venv`", decision)
        self.assertIn("must not install the adopting project's dependencies", decision)

        for command in (
            "agentgov inspect <deep-target>",
            "--dry-run",
            "agentgov check repository <deep-target>",
        ):
            self.assertIn(command, rehearsal)
        self.assertIn("PASS=14 WARN=4 FAIL=0 ADVISORY=4", rehearsal)
        self.assertIn(
            "No commit, push, tag, package publication, release, or deployment",
            rehearsal,
        )

    def test_web_guides_are_bilingual_rich_and_return_to_quickstart(self) -> None:
        pairs = (
            ("existing-repository-adoption.html", "existing-repository-adoption.zh-CN.html"),
            ("generated-files-guide.html", "generated-files-guide.zh-CN.html"),
            ("troubleshooting.html", "troubleshooting.zh-CN.html"),
        )
        for english_name, chinese_name in pairs:
            with self.subTest(page=english_name):
                english = (ROOT / "docs" / english_name).read_text(encoding="utf-8")
                chinese = (ROOT / "docs" / chinese_name).read_text(encoding="utf-8")
                self.assertIn('href="quickstart.html"', english)
                self.assertIn('href="quickstart.zh-CN.html"', chinese)
                self.assertIn("<pre><code>", english)
                self.assertIn("<pre><code>", chinese)
            self.assertGreaterEqual(english.count("<section"), 5)
            self.assertGreaterEqual(chinese.count("<section"), 5)

        generated_english = (
            ROOT / "docs/generated-files-guide.html"
        ).read_text(encoding="utf-8")
        generated_chinese = (
            ROOT / "docs/generated-files-guide.zh-CN.html"
        ).read_text(encoding="utf-8")
        adoption_english = (
            ROOT / "docs/existing-repository-adoption.html"
        ).read_text(encoding="utf-8")
        adoption_chinese = (
            ROOT / "docs/existing-repository-adoption.zh-CN.html"
        ).read_text(encoding="utf-8")
        self.assertIn("optional generated output", generated_english)
        self.assertIn("可选的生成输出", generated_chinese)
        self.assertIn("not a core adoption path", adoption_english)
        self.assertIn("不是核心接入路径", adoption_chinese)

    def test_web_quickstarts_separate_stable_pipx_from_source_execution(
        self,
    ) -> None:
        english = QUICKSTART_WEB.read_text(encoding="utf-8")
        chinese = QUICKSTART_ZH_WEB.read_text(encoding="utf-8")

        for content in (english, chinese):
            self.assertIn(
                'pipx install "https://github.com/Andy-JunXiong/'
                "agent-governance-starter/releases/download/v0.2.1/"
                'agent_governance_starter-0.2.1-py3-none-any.whl"',
                content,
            )
            self.assertIn("python --version", content)
            self.assertIn("python -m agentgov --help", content)
            self.assertIn("agentgov inspect .", content)
            self.assertIn("agentgov check repository .", content)
            self.assertIn("\nagentgov --help", content)
            self.assertIn("Do not clone", english)
            self.assertIn("不要把 starter clone", chinese)

    def test_web_quickstarts_route_development_detail_to_deep_evidence(
        self,
    ) -> None:
        english = QUICKSTART_WEB.read_text(encoding="utf-8")
        chinese = QUICKSTART_ZH_WEB.read_text(encoding="utf-8")

        for content in (english, chinese):
            for command in (
                "agentgov doctor .",
                'agentgov onboard . --project-name "My Project" --dry-run',
                'agentgov onboard . --project-name "My Project"',
                "agentgov next .",
                "agentgov reserve replay-correlation",
                "agentgov claim replay-correlation",
                "agentgov recover replay-claim",
            ):
                self.assertNotIn(command, content)
            self.assertIn("product-requirements-automatic-governance.html", content)
            self.assertIn("clean-target-replay-preflight.html", content)
            self.assertIn("blob/main/docs/governance-mcp-adapter.md", content)
            self.assertLess(content.index("agentgov inspect ."), content.index('id="development"'))
        self.assertIn("Development preview", english)
        self.assertIn("not stable releases or consumer-active behavior", english)
        self.assertIn("开发预览", chinese)
        self.assertIn("不等于稳定发布或消费者已启用能力", chinese)

    def test_web_guides_add_accessible_copy_controls_to_code_blocks(self) -> None:
        guide_pages = (
            "quickstart.html",
            "quickstart.zh-CN.html",
            "existing-repository-adoption.html",
            "existing-repository-adoption.zh-CN.html",
            "generated-files-guide.html",
            "generated-files-guide.zh-CN.html",
            "troubleshooting.html",
            "troubleshooting.zh-CN.html",
        )
        for name in guide_pages:
            with self.subTest(page=name):
                content = (ROOT / "docs" / name).read_text(encoding="utf-8")
                self.assertIn("script-src 'self'", content)
                self.assertIn('<script src="guide.js" defer></script>', content)
                self.assertIn("<pre><code>", content)

        script = GUIDE_SCRIPT.read_text(encoding="utf-8")
        style = GUIDE_STYLE.read_text(encoding="utf-8")
        self.assertIn('document.querySelectorAll("pre > code")', script)
        self.assertIn("navigator.clipboard.writeText", script)
        self.assertIn('document.execCommand("copy")', script)
        self.assertIn('button.setAttribute("aria-label"', script)
        self.assertIn("复制失败", script)
        self.assertIn(".copy-code:focus-visible", style)

    def test_drift_review_reminders_preserve_advisory_and_notification_boundaries(self) -> None:
        guide = DRIFT_REVIEW_REMINDERS.read_text(encoding="utf-8")
        consumer = CONSUMER_CI.read_text(encoding="utf-8")
        monitor = DEVELOPMENT_MONITOR.read_text(encoding="utf-8")
        normalized_guide = " ".join(guide.split())

        for text in (guide, consumer, monitor):
            self.assertIn("advisory", text.lower())
        for phrase in (
            "three distinct verified task completions",
            "seven days",
            "job stays green",
            "does not open an issue",
            "hidden daemon",
            "v0.3.0rc1",
        ):
            self.assertIn(phrase, guide)
        self.assertIn("agentgov review drift . --format github", consumer)
        self.assertIn("Monitor contract 1.5", monitor)
        self.assertIn("agentgov_drift_review_record", guide)
        self.assertIn("cannot supply the human decision", guide)
        self.assertIn(
            "do not negotiate native form elicitation", normalized_guide
        )
        self.assertIn("installed only in the existing local AgentGov pipx", guide)
        self.assertIn("unpublished and consumer-inactive", guide)
        self.assertIn("without a human decision or record", normalized_guide)
        self.assertIn(
            "live Agent selection and end-user UI presentation remain unproven",
            normalized_guide,
        )

    def test_clean_target_replay_preflight_is_documented_as_a_non_authorizing_gate(self) -> None:
        guide = (ROOT / "docs/clean-target-replay-preflight.md").read_text(
            encoding="utf-8"
        )
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        harness = (ROOT / "docs/harness-contract-v1.md").read_text(encoding="utf-8")
        normalized_guide = " ".join(guide.split())

        for phrase in (
            "agentgov.replay-preflight-plan",
            "agentgov check replay-preflight",
            "agentgov.replay-correlation-reservation-preview",
            "agentgov.replay-correlation-reservation-result",
            "agentgov reserve replay-correlation",
            "agentgov.replay-correlation-claim",
            "agentgov claim replay-correlation",
            "READY_TO_CLAIM",
            "exact `CLAIM`",
            "agentgov recover replay-claim",
            "READY_TO_RECOVER",
            "exact `RECOVER`",
            "READY",
            "BLOCKED",
            "UNKNOWN",
            "does not authorize",
            "does not create or reserve a marker",
            "exclusive file create",
        ):
            self.assertIn(phrase, normalized_guide)
        self.assertIn("](docs/clean-target-replay-preflight.md)", readme)
        self.assertIn("implemented upstream gate", harness)
        self.assertIn("preflight -> reservation", harness)
        self.assertIn("reservation -> claim", harness)
        self.assertIn("Abandoned-claim recovery is a separate side branch", harness)
        self.assertIn("First Deviation rules", harness)
        for surface in (normalized_guide, harness):
            self.assertIn("agentgov.replay-correlation-bridge", surface)
            self.assertIn("host.repository_correlation", surface)
        self.assertIn("reserved", normalized_guide)
        self.assertIn("consumed", normalized_guide)
        self.assertIn("invalidated", normalized_guide)
        self.assertIn("unavailable", normalized_guide)
        self.assertIn("does not reserve, consume, invalidate", normalized_guide)
        for surface in (normalized_guide, " ".join(harness.split())):
            self.assertIn("does not authorize, launch, consume, expire, recover", surface)
        for phrase in (
            "VALID",
            "PARTIAL",
            "MALFORMED",
            "MISSING",
            "INCONSISTENT",
            "RECOVERED",
            "raw claim content is not copied",
            "not identity authentication",
            "does not create replacement ownership",
        ):
            self.assertIn(phrase, normalized_guide)

    def test_disposable_installed_reservation_records_install_block_without_retry(self) -> None:
        evidence = DISPOSABLE_INSTALLED_RESERVATION.read_text(encoding="utf-8")
        normalized = " ".join(evidence.split())

        for phrase in (
            "BLOCKED_INSTALLATION_PRECONDITION",
            "setuptools 65.5.0",
            "reservation invocation count: `0`",
            "visible terminal started: `false`",
            "marker created: `false`",
            "no retry",
            "existing pipx installation remained byte-unchanged",
            "does not establish reservation behavior",
        ):
            self.assertIn(phrase, normalized)

    def test_reproducible_local_wheel_build_records_installed_help_boundary(self) -> None:
        evidence = REPRODUCIBLE_LOCAL_WHEEL_BUILD.read_text(encoding="utf-8")
        normalized = " ".join(evidence.split())
        member_lines = [
            line
            for line in evidence.splitlines()
            if line.startswith(
                (
                    "agentgov/",
                    "agent_governance_starter-0.3.0rc1.data/",
                    "agent_governance_starter-0.3.0rc1.dist-info/",
                )
            )
        ]

        for phrase in (
            "514f5023d7883aeee648ddda63b3e944d4116eac",
            "setuptools 80.9.0",
            "exactly one unpublished wheel",
            "78D6A216FE7344A2E3DA01086A7A92B9F3310BE61DAD2E690B0705003221FDE6",
            "member count: `173`",
            "2BB649EB6EF281260C083E567CC8F92DDE0F50BB6975C700DE17C075115DF5AC",
            "agentgov reserve replay-correlation --help",
            "Reservation apply invocation count was `0`",
            "marker created was `false`",
            "existing installation therefore remained byte-unchanged",
            "does not revive or retry that paused one-shot task",
        ):
            self.assertIn(phrase, normalized)
        self.assertEqual(len(member_lines), 173)
        self.assertEqual(len(set(member_lines)), 173)

    def test_wheel_backed_installed_reservation_records_one_bounded_apply(self) -> None:
        evidence = WHEEL_BACKED_INSTALLED_RESERVATION.read_text(encoding="utf-8")
        normalized = " ".join(evidence.split())

        for phrase in (
            "78D6A216FE7344A2E3DA01086A7A92B9F3310BE61DAD2E690B0705003221FDE6",
            "READY_TO_RESERVE",
            "All six checks passed",
            "invoked exactly once",
            "exact interactive `RESERVE` confirmation",
            "registry contained exactly one JSON marker",
            "rrv-8727d1e62d0fde6e",
            "9cbd4cdb06486a78a554ec208c39d00cdba5bddd4b41c178f957c5106989c268",
            "Bridge validation returned zero errors",
            "Harness run and evidence fields remained null",
            "existing installation therefore remained byte-unchanged",
            "does not consume the reservation",
        ):
            self.assertIn(phrase, normalized)

    def test_complete_public_journey_has_resolvable_internal_resources(self) -> None:
        docs = ROOT / "docs"
        for name in PUBLIC_JOURNEY_HTML:
            page = docs / name
            text = page.read_text(encoding="utf-8")
            with self.subTest(page=name):
                self.assertNotIn("{{", text)
                self.assertNotIn("C:\\Users", text)
                for reference in re.findall(r'(?:href|src)="([^"]+)"', text):
                    parsed = urlsplit(reference)
                    if parsed.scheme or parsed.netloc:
                        continue
                    target = (page.parent / parsed.path).resolve() if parsed.path else page
                    self.assertTrue(target.is_relative_to(docs.resolve()))
                    rendered_source = (
                        target.with_suffix(".md") if target.suffix == ".html" else target
                    )
                    self.assertTrue(
                        target.exists() or rendered_source.exists(),
                        f"{name}: missing internal resource {reference}",
                    )
                    if parsed.fragment and target == page.resolve():
                        self.assertRegex(
                            text,
                            rf'id=["\']{re.escape(parsed.fragment)}["\']',
                            f"{name}: missing internal anchor {reference}",
                        )

    def test_public_reference_pages_share_brand_navigation_and_release_boundary(self) -> None:
        docs = ROOT / "docs"
        for relative in PUBLIC_REFERENCE_SOURCES:
            with self.subTest(source=relative):
                text = (docs / relative).read_text(encoding="utf-8")
                front_matter = text.split("---", 2)
                self.assertGreaterEqual(len(front_matter), 3)
                self.assertIn("layout: reference", front_matter[1])
                self.assertIn("title:", front_matter[1])
                self.assertIn("source_path:", front_matter[1])

        layout = (docs / "_layouts/reference.html").read_text(encoding="utf-8")
        for target in (
            "/index.html",
            "/portfolio.html",
            "/interview-guide.html",
            "/quickstart.html",
            "/favicon.ico",
        ):
            self.assertIn(f"'{target}' | relative_url", layout)
        for release in ("0.2.1", "0.3.0rc1", "development source"):
            self.assertIn(release, layout)
        self.assertIn("@media (max-width: 720px)", (docs / "reference.css").read_text(encoding="utf-8"))

    def test_mutable_public_pages_share_favicon_navigation_and_version_boundary(self) -> None:
        docs = ROOT / "docs"
        favicon = docs / "favicon.ico"
        root = ET.fromstring(favicon.read_text(encoding="utf-8"))
        self.assertTrue(root.tag.endswith("svg"))
        self.assertEqual(root.attrib["viewBox"], "0 0 64 64")

        mutable_pages = PUBLIC_JOURNEY_HTML[:-2]
        for name in mutable_pages:
            with self.subTest(page=name):
                text = (docs / name).read_text(encoding="utf-8")
                self.assertIn('rel="icon" href="favicon.ico"', text)
                self.assertIn("img-src 'self'", text)
                self.assertIn("0.2.1", text)
                if name == "index.html":
                    self.assertNotIn("0.3.0rc1", text)
                    self.assertIn('href="portfolio.html#boundary"', text)
                    self.assertIn("Illustrative example", text)
                else:
                    self.assertIn("0.3.0rc1", text)
                if name != "portfolio.html":
                    self.assertIn('href="portfolio.html"', text)
                self.assertIn('href="interview-guide', text)
                self.assertIn('href="quickstart', text)

        for page in PUBLIC_JOURNEY_HTML[-2:]:
            with self.subTest(report=page):
                self.assertIn('href="index.html"', (docs / page).read_text(encoding="utf-8"))

    def test_bilingual_guides_cross_link_and_templates_keep_narrow_layouts(self) -> None:
        docs = ROOT / "docs"
        for english, chinese in (
            ("quickstart.html", "quickstart.zh-CN.html"),
            ("interview-guide.html", "interview-guide.zh-CN.html"),
            ("existing-repository-adoption.html", "existing-repository-adoption.zh-CN.html"),
            ("generated-files-guide.html", "generated-files-guide.zh-CN.html"),
            ("troubleshooting.html", "troubleshooting.zh-CN.html"),
        ):
            with self.subTest(pair=english):
                en_text = (docs / english).read_text(encoding="utf-8")
                zh_text = (docs / chinese).read_text(encoding="utf-8")
                self.assertIn(f'href="{chinese}"', en_text)
                self.assertIn(f'href="{english}"', zh_text)
                self.assertIn('aria-current="page"', en_text)
                self.assertIn('aria-current="page"', zh_text)

        for template in (
            "index.html",
            "portfolio.css",
            "guide.css",
            "reference.css",
            "demo-governance-report.html",
            "demo-governance-report.zh-CN.html",
        ):
            with self.subTest(template=template):
                self.assertIn("@media", (docs / template).read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
