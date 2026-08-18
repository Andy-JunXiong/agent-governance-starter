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

        for text in (readme, home, portfolio, english, markdown):
            self.assertIn("immutable reservation", text)
            self.assertIn("create-only claim", text)
            self.assertIn("immutable recovery", text)
            self.assertIn("no replacement owner", text)
            self.assertIn("no replay authority", text)

        for text in (readme, home, english, markdown):
            self.assertIn("0.2.1", text)
            self.assertIn("stable", text.lower())
            self.assertIn("0.3.0rc1", text)
            self.assertIn("sample report", text.lower())
            self.assertIn("illustrative", text.lower())

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

    def test_generated_demo_snapshots_remain_byte_identical(self) -> None:
        for name, expected in DEMO_HASHES.items():
            with self.subTest(name=name):
                digest = hashlib.sha256((DOCS / name).read_bytes()).hexdigest()
                self.assertEqual(expected, digest)


if __name__ == "__main__":
    unittest.main()
