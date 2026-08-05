import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
QUICKSTART_ZH = ROOT / "docs/quickstart.zh-CN.md"
QUICKSTART_WEB = ROOT / "docs/quickstart.html"
QUICKSTART_ZH_WEB = ROOT / "docs/quickstart.zh-CN.html"
ADOPTION_GUIDE = ROOT / "docs/existing-repository-adoption.md"
GENERATED_FILES_GUIDE = ROOT / "docs/generated-files-guide.md"
TROUBLESHOOTING = ROOT / "docs/troubleshooting.md"
CONSUMER_CI = ROOT / "docs/consumer-ci.md"
DEVELOPMENT_MONITOR = ROOT / "docs/development-monitor.md"
DEVELOPMENT_SESSION = ROOT / "docs/development-session.md"
DEVELOPMENT_PLAN = ROOT / "docs/development-plan.md"
AUTOMATIC_PRODUCT_REQUIREMENTS = (
    ROOT / "docs/product-requirements-automatic-governance.md"
)
AUTOMATION_CONTRACTS = ROOT / "docs/development-automation-contracts.md"
EXTRACTION_MAP = ROOT / "docs/ai-radar-extraction-map.md"
STATUS = ROOT / "STATUS.md"
AGENT_SKILLS_README = ROOT / "agent-skills/README.md"
GUIDED_NEXT_ADR = ROOT / "docs/adr/0010-route-next-through-development-lifecycle.md"
BOOTSTRAP_UPDATE_ADR = ROOT / "docs/adr/0011-separate-bootstrap-from-update-routing.md"
SESSION_HANDOFF_ADR = ROOT / "docs/adr/0012-handoff-verified-development-sessions.md"
AUTOMATIC_EXPERIENCE_ADR = (
    ROOT / "docs/adr/0013-make-automatic-governance-and-dashboard-primary.md"
)
DEVELOPMENT_RELEASE = ROOT / "release/current.json"
ISOLATED_EXECUTION_ADR = (
    ROOT / "docs/adr/0004-use-isolated-tool-execution-for-onboarding.md"
)
ISOLATED_EXECUTION_REHEARSAL = ROOT / "docs/isolated-tool-execution-rehearsal.md"
GUIDE_SCRIPT = ROOT / "docs/guide.js"
GUIDE_STYLE = ROOT / "docs/guide.css"


class UserDocumentationTests(unittest.TestCase):
    def test_automatic_governance_and_dashboard_are_the_primary_direction(self) -> None:
        readme = README.read_text(encoding="utf-8")
        status = STATUS.read_text(encoding="utf-8")
        plan = DEVELOPMENT_PLAN.read_text(encoding="utf-8")
        requirements = AUTOMATIC_PRODUCT_REQUIREMENTS.read_text(encoding="utf-8")
        decision = AUTOMATIC_EXPERIENCE_ADR.read_text(encoding="utf-8")
        session = DEVELOPMENT_SESSION.read_text(encoding="utf-8")
        monitor = DEVELOPMENT_MONITOR.read_text(encoding="utf-8")
        automation = AUTOMATION_CONTRACTS.read_text(encoding="utf-8")

        for path in (AUTOMATIC_PRODUCT_REQUIREMENTS, AUTOMATIC_EXPERIENCE_ADR):
            self.assertTrue(path.is_file())

        for text in (readme, status, plan, requirements, decision):
            self.assertIn("automatic", text.lower())
            self.assertIn("Dashboard", text)

        for text in (readme, plan, requirements, decision, session):
            self.assertIn("fallback", text)

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

        self.assertIn("independent non-NYC", plan)
        self.assertLess(plan.index("independent non-NYC"), plan.index("NYC shadow"))
        self.assertIn("not yet implemented as the primary", requirements)
        self.assertIn("not yet implemented", decision)
        self.assertIn("not yet implemented", monitor)
        for text in (readme, status, plan, requirements, decision, session, automation):
            self.assertIn("agentgov dev", text)
        self.assertIn("agentgov.foreground-cycle", automation)
        self.assertIn("live coding-agent", automation.lower())

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

        self.assertIn("Accepted automatic product direction", english)
        self.assertIn("not implemented in stable 0.2.1", english)
        self.assertIn("one-cycle", english)
        self.assertIn("agentgov dev", english)
        self.assertIn("开发源自动化状态", chinese)
        self.assertIn("agentgov dev", chinese)
        self.assertIn("已接受的自动化产品方向", chinese)
        self.assertIn("尚未包含在 stable 0.2.1", chinese)
        for text in (english, chinese):
            self.assertIn("product-requirements-automatic-governance.html", text)

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

        self.assertIn("govern the\ncoding agent during development", readme)
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

        self.assertIn("Development source now implements ADR-0012", readme)
        self.assertIn("implements ADR-0012", session)
        self.assertIn("Monitor schema 1.4", monitor)
        for text in (readme, session):
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
        self.assertIn("matching handoff\nis idempotent", readme)
        self.assertIn("Published\nstable 0.2.1 does not include", session)

    def test_bootstrap_and_update_decision_has_no_self_install_or_fake_release(self) -> None:
        readme = README.read_text(encoding="utf-8")
        decision = BOOTSTRAP_UPDATE_ADR.read_text(encoding="utf-8")
        quickstart = QUICKSTART_WEB.read_text(encoding="utf-8")
        development_release = DEVELOPMENT_RELEASE.read_text(encoding="utf-8")

        stable_install = 'pipx install "https://github.com/Andy-JunXiong/'
        self.assertLess(readme.index(stable_install), readme.index("python -m agentgov next ."))
        self.assertLess(quickstart.index(stable_install), quickstart.index("agentgov next ."))
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

        for text in (readme, session, decision):
            self.assertIn("govern start", text)
            self.assertIn("govern check", text)
            self.assertIn("govern finish", text)
            self.assertIn("monitor development", text)
            self.assertIn("deterministic repository `FAIL`", text)
            self.assertRegex(text.lower(), r"multiple admitted\s+tasks")
        self.assertIn("action_executed=false", readme)
        self.assertIn("action_executed=false", session)
        self.assertIn("never executes", decision)
        self.assertIn("Older events", decision)

    def test_development_monitor_artifact_docs_preserve_opt_in_and_source_boundaries(self) -> None:
        readme = README.read_text(encoding="utf-8")
        monitor = DEVELOPMENT_MONITOR.read_text(encoding="utf-8")
        consumer_ci = CONSUMER_CI.read_text(encoding="utf-8")

        for text in (readme, monitor, consumer_ci):
            self.assertIn("publish_development_monitor", text)
            self.assertIn("agentgov-development-monitor.html", text)
            self.assertIn("default-off", text)
            self.assertIn("development_export", text)
        self.assertIn("future 0.3", readme)
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
        self.assertIn("不授权合并、发布或部署", text)

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

    def test_web_quickstarts_label_guided_onboarding_as_development_preview(
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
            ):
                self.assertIn(command, content)
            self.assertIn("ADOPT", content)
        self.assertIn("development preview", english)
        self.assertIn("does not replace the primary steps", english)
        self.assertIn("开发预览", chinese)
        self.assertIn("暂不替换", chinese)

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


if __name__ == "__main__":
    unittest.main()
