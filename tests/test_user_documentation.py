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
            "## `inspect` reports `MISSING`",
            "## `inspect` or `adopt` reports `CONFLICT`",
            "## Repository check returns WARN",
            "## Repository check returns ADVISORY",
            "## Repository check returns FAIL",
            "## Exit codes",
        ):
            self.assertIn(heading, text)
        self.assertIn("No exit code grants approval", text)

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


if __name__ == "__main__":
    unittest.main()
