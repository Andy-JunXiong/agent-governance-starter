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
ISOLATED_EXECUTION_ADR = (
    ROOT / "docs/adr/0004-use-isolated-tool-execution-for-onboarding.md"
)
ISOLATED_EXECUTION_REHEARSAL = ROOT / "docs/isolated-tool-execution-rehearsal.md"
GUIDE_SCRIPT = ROOT / "docs/guide.js"
GUIDE_STYLE = ROOT / "docs/guide.css"


class UserDocumentationTests(unittest.TestCase):
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
