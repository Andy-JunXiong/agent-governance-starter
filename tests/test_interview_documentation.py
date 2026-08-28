from __future__ import annotations

import hashlib
import re
import unittest
from pathlib import Path
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
PUBLIC_PAGES = (
    DOCS / "index.html",
    DOCS / "portfolio.html",
    DOCS / "quickstart.html",
    DOCS / "quickstart.zh-CN.html",
    DOCS / "interview-guide.html",
    DOCS / "interview-guide.zh-CN.html",
    DOCS / "interview-demo.html",
    DOCS / "interview-demo.zh-CN.html",
    DOCS / "project-interview.html",
    DOCS / "project-interview.zh-CN.html",
)
STABLE_WHEEL = (
    'pipx install "https://github.com/Andy-JunXiong/'
    "agent-governance-starter/releases/download/v0.2.1/"
    'agent_governance_starter-0.2.1-py3-none-any.whl"'
)
DEMO_HASHES = {
    "demo-governance-report.html": (
        "a899b3c6039693fee01b93ca6fb08adf229d2d3854a29322c6b5c5b489e3bec3"
    ),
    "demo-governance-report.zh-CN.html": (
        "94136427db9f6ed4390a28283b7c772be27a9a50ed7b13e691618485b294c8ec"
    ),
}


def _normalized(path: Path) -> str:
    return " ".join(path.read_text(encoding="utf-8").split())


def _local_target(page: Path, reference: str) -> tuple[Path, str]:
    parsed = urlsplit(reference)
    target = (page.parent / parsed.path).resolve() if parsed.path else page.resolve()
    return target, parsed.fragment


class InterviewDocumentationTests(unittest.TestCase):
    def test_interview_surfaces_present_one_consistent_story(self) -> None:
        readme = _normalized(ROOT / "README.md")
        home = _normalized(DOCS / "index.html")
        portfolio = _normalized(DOCS / "portfolio.html")
        english = _normalized(DOCS / "interview-guide.html")
        chinese = _normalized(DOCS / "interview-guide.zh-CN.html")
        markdown = _normalized(DOCS / "interview-guide.md")

        for text in (portfolio, english, markdown):
            self.assertIn("immutable reservation", text)
            self.assertIn("create-only claim", text)
            self.assertIn("immutable recovery", text)
            self.assertIn("no replacement owner", text)
            self.assertIn("no replay authority", text)

        self.assertIn("docs/interview-guide.md", readme)
        self.assertIn("docs/portfolio.html", readme)
        self.assertNotIn("immutable reservation", readme)
        self.assertNotIn("create-only claim", readme)
        self.assertNotIn("immutable recovery", readme)

        self.assertNotIn("immutable reservation", home)
        self.assertNotIn("create-only claim", home)
        self.assertNotIn("immutable recovery", home)
        self.assertNotIn("no replay authority", home)
        self.assertIn("If automated work is interrupted", home)
        self.assertIn("another agent permission to continue", home)
        self.assertIn('href="portfolio.html#recovery"', home)

        for text in (readme, portfolio, english, markdown):
            self.assertIn("0.2.1", text)
            self.assertIn("stable", text.lower())
            self.assertIn("0.3.0rc1", text)

        self.assertIn("illustrative sample governance report", readme.lower())

        for text in (english, markdown):
            self.assertIn("sample report", text.lower())
            self.assertIn("illustrative", text.lower())

        self.assertIn("Illustrative example", home)
        self.assertIn('href="portfolio.html#boundary"', home)

        for phrase in (
            "5–10 分钟",
            "不可变 reservation",
            "create-only claim",
            "immutable recovery",
            "不创建 replacement owner",
            "不授权 replay",
        ):
            self.assertIn(phrase, chinese)

    def test_quickstarts_route_replay_detail_to_deep_evidence(self) -> None:
        surfaces = (
            DOCS / "quickstart.html",
            DOCS / "quickstart.zh-CN.html",
            DOCS / "quickstart.zh-CN.md",
        )
        for surface in surfaces:
            with self.subTest(surface=surface.name):
                text = _normalized(surface)
                self.assertIn(STABLE_WHEEL, text)
                self.assertIn("clean-target-replay-preflight", text)
                self.assertIn("reservation", text)
                self.assertIn("claim", text)
                self.assertIn("recovery", text)
                self.assertIn("replay", text)
                self.assertIn("Git", text)
                self.assertIn("release", text)
                self.assertNotIn("reserve replay-correlation", text)
                self.assertNotIn("claim replay-correlation", text)
                self.assertNotIn("recover replay-claim", text)
                self.assertNotIn("releases/download/v0.1.0/", text)

    def test_public_pages_have_no_unrendered_templates_and_local_links_resolve(self) -> None:
        for page in PUBLIC_PAGES:
            with self.subTest(page=page.name):
                text = page.read_text(encoding="utf-8")
                self.assertNotIn("{{", text)
                self.assertNotIn("}}", text)
                self.assertNotIn("C:\\Users", text)
                references = re.findall(r'(?:href|src)="([^"]+)"', text)
                for reference in references:
                    if reference.startswith(("http://", "https://", "mailto:")):
                        continue
                    target, fragment = _local_target(page, reference)
                    rendered_source = (
                        target.with_suffix(".md")
                        if target.suffix == ".html"
                        else target
                    )
                    self.assertTrue(
                        target.exists() or rendered_source.exists(),
                        f"{page.name}: missing {reference}",
                    )
                    if fragment and target.resolve() == page.resolve():
                        self.assertRegex(
                            text,
                            rf'id=["\']{re.escape(fragment)}["\']',
                            f"{page.name}: missing fragment {reference}",
                        )

    def test_interview_pages_are_bilingual_and_cross_linked(self) -> None:
        english = (DOCS / "interview-guide.html").read_text(encoding="utf-8")
        chinese = (DOCS / "interview-guide.zh-CN.html").read_text(encoding="utf-8")

        self.assertIn('<html lang="en">', english)
        self.assertIn('<html lang="zh-CN">', chinese)
        self.assertIn('href="interview-guide.zh-CN.html"', english)
        self.assertIn('href="interview-guide.html"', chinese)
        self.assertIn('aria-current="page"', english)
        self.assertIn('aria-current="page"', chinese)

    def test_interview_guide_owns_delivery_without_duplicating_the_story(self) -> None:
        english = (DOCS / "interview-guide.html").read_text(encoding="utf-8")
        chinese = (DOCS / "interview-guide.zh-CN.html").read_text(encoding="utf-8")
        markdown = (DOCS / "interview-guide.md").read_text(encoding="utf-8")

        self.assertEqual(english.count('data-role-branch="'), 3)
        self.assertEqual(chinese.count('data-role-branch="'), 3)
        self.assertEqual(english.count('data-route-step="'), 6)
        self.assertEqual(chinese.count('data-route-step="'), 6)
        self.assertGreaterEqual(english.count("Cut point"), 4)
        self.assertGreaterEqual(chinese.count("停顿点"), 4)

        for page, story, replay in (
            (english, "project-interview.html", "artifact-replay-interview.html"),
            (
                chinese,
                "project-interview.zh-CN.html",
                "artifact-replay-interview.zh-CN.html",
            ),
        ):
            self.assertIn(f'href="{story}"', page)
            self.assertIn('href="governed-refund-walkthrough.html"', page)
            self.assertIn(f'href="{replay}"', page)
            self.assertIn('href="portfolio.html"', page)
            self.assertIn("0.2.1", page)
            self.assertIn("0.3.0rc1", page)
            self.assertNotIn("sha256:", page.lower())

        for phrase in (
            "Two-minute default route",
            "Five-to-seven-minute screen-share expansion",
            "Software or AI engineering",
            "Platform or infrastructure",
            "Product or technical product",
            "The Agent proposed most low-level repairs",
            "cannot detect product drift automatically",
        ):
            self.assertIn(phrase, markdown)

        for target in (
            "project-interview.html",
            "governed-refund-walkthrough.html",
            "artifact-replay-interview.html",
            "portfolio.html",
        ):
            self.assertIn(f"]({target})", markdown)

        self.assertIn("默认两分钟", chinese)
        self.assertIn("底层修复大多由 Agent 提出", chinese)
        self.assertIn("为什么不能自动检测产品漂移", chinese)
        self.assertIn("AI coding agents can write code that passes tests", english)
        self.assertIn("How drift happened", english)
        self.assertIn("偏移如何发生", chinese)
        self.assertNotIn(
            "No external evidence proves that this documentation improves interview outcomes.",
            english,
        )
        self.assertNotIn("没有外部证据证明这些页面能改善面试结果", chinese)

    def test_whole_project_story_is_bilingual_human_and_discoverable(self) -> None:
        english = (DOCS / "project-interview.html").read_text(encoding="utf-8")
        chinese = (DOCS / "project-interview.zh-CN.html").read_text(encoding="utf-8")
        home = (DOCS / "index.html").read_text(encoding="utf-8")

        self.assertIn('<html lang="en">', english)
        self.assertIn('<html lang="zh-CN">', chinese)
        self.assertIn('href="project-interview.zh-CN.html"', english)
        self.assertIn('href="project-interview.html"', chinese)
        self.assertIn('href="project-interview.html"', home)
        self.assertIn('aria-current="page"', english)
        self.assertIn('aria-current="page"', chinese)
        self.assertEqual(english.count('class="architecture-flow"'), 1)
        self.assertEqual(chinese.count('class="architecture-flow"'), 1)
        self.assertEqual(english.count('class="proof-card"'), 1)
        self.assertEqual(chinese.count('class="proof-card"'), 1)
        self.assertEqual(english.count('class="story-act"'), 4)
        self.assertEqual(chinese.count('class="story-act"'), 4)

        for page in (english, chinese):
            self.assertNotIn("sha256:", page.lower())
            self.assertNotIn("Observed / Derived / Unknown", page)
            self.assertNotIn("C:\\Users", page)
            self.assertIn("default-src 'none'; style-src 'self'; img-src 'self'", page)
            self.assertIn("project-interview.css", page)
            self.assertNotIn('class="act-label"', page)
            self.assertNotIn('class="cut-point"', page)
            self.assertNotIn('class="limits"', page)
            self.assertNotIn("Clean cut", page)

        for phrase in (
            "I built AgentGov",
            "center of gravity",
            "short-term benefit",
            "GitHub and delivery language were taking over the roadmap",
            "compared the accumulated work with the original requirement",
            "I did not throw away the PR or CI work",
            "Verification can prove a change works",
            "I now treat that as a development habit",
            "Open the refund demo",
        ):
            self.assertIn(phrase, english)

        for phrase in (
            "我做了 AgentGov",
            "短期价值",
            "GitHub 和交付语言越来越主导路线图",
            "把累积实现和最初需求放在一起检查",
            "我没有把 PR 或 CI 工作丢掉",
            "是不是还在做正确的产品",
            "我现在把这当成一个开发习惯",
            "打开退款 Demo",
        ):
            self.assertIn(phrase, chinese)

    def test_generated_demo_snapshots_remain_byte_identical(self) -> None:
        for name, expected in DEMO_HASHES.items():
            with self.subTest(name=name):
                digest = hashlib.sha256((DOCS / name).read_bytes()).hexdigest()
                self.assertEqual(expected, digest)


if __name__ == "__main__":
    unittest.main()
