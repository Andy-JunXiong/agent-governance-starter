from __future__ import annotations

import re
import unittest
from pathlib import Path
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
ENGLISH = DOCS / "interview-demo.html"
CHINESE = DOCS / "interview-demo.zh-CN.html"


class InterviewDemoTests(unittest.TestCase):
    def test_bilingual_demo_has_one_six_step_scenario(self) -> None:
        english = ENGLISH.read_text(encoding="utf-8")
        chinese = CHINESE.read_text(encoding="utf-8")

        self.assertIn('<html lang="en">', english)
        self.assertIn('<html lang="zh-CN">', chinese)
        self.assertIn('href="interview-demo.zh-CN.html"', english)
        self.assertIn('href="interview-demo.html"', chinese)
        self.assertIn('aria-current="page"', english)
        self.assertIn('aria-current="page"', chinese)

        for page in (english, chinese):
            self.assertEqual(page.count("data-demo-step="), 6)
            self.assertEqual(page.count("data-progress-step"), 6)
            self.assertEqual(page.count('data-demo-action="back"'), 1)
            self.assertEqual(page.count('data-demo-action="next"'), 1)
            self.assertEqual(page.count('data-demo-action="restart"'), 1)
            self.assertEqual(
                len(re.findall(r'data-demo-step="[2-6]"[^>]* hidden', page)), 5
            )
            self.assertIn("refunds/calculation.py", page)
            self.assertIn("refunds/approval_policy.py", page)
            self.assertIn("BLOCKED", page)
            self.assertIn("REVIEW_READY", page)
            self.assertIn("0.2.1", page)
            self.assertNotIn("sha256:", page.lower())

    def test_actor_and_permission_boundaries_are_concise_and_explicit(self) -> None:
        english = ENGLISH.read_text(encoding="utf-8")
        for phrase in (
            "based on a verified future-0.3 scenario, not a live run",
            "Person</strong><p>Defines the task and allows one file.",
            "Coding agent</strong><p>Works on the requested change.",
            "AgentGov</strong><p>Checks the changed files against that boundary.",
            "Demo script</strong><p>Replays the example",
            "The work is not automatically undone.",
            "The approval rule is not part of this task.",
            "the demo script restores <code>approval_policy.py</code>",
            "<code>REVIEW_READY</code> is not permission to merge, release, or deploy.",
        ):
            self.assertIn(phrase, english)

        for repeated_disclaimer in (
            "The demo script—not AgentGov—",
            "AgentGov changes neither file.",
            "not the simulated coding Agent, AgentGov, or the human",
            "No check or demo authorizes",
        ):
            self.assertNotIn(repeated_disclaimer, english)

        stages = (
            "The person sets the boundary.",
            "The agent fixes the bug—and one thing it was not asked to.",
            "AgentGov catches the extra change.",
            "A person decides what happens next.",
            "The out-of-scope change is reverted.",
            "Ready for review—not accepted.",
        )
        positions = [english.index(stage) for stage in stages]
        self.assertEqual(positions, sorted(positions))

    def test_demo_assets_and_interaction_contract_are_local(self) -> None:
        english = ENGLISH.read_text(encoding="utf-8")
        script = (DOCS / "interview-demo.js").read_text(encoding="utf-8")
        css = (DOCS / "interview-demo.css").read_text(encoding="utf-8")

        self.assertIn("default-src 'none'; style-src 'self'; script-src 'self'; img-src 'self'", english)
        self.assertIn('href="interview-demo.css"', english)
        self.assertIn('src="interview-demo.js" defer', english)
        self.assertNotIn("<style", english)
        self.assertNotRegex(english, r"<script(?![^>]+src=)")
        for action in ("back", "next", "restart"):
            self.assertIn(f'data-demo-action="{action}"', script)
        self.assertIn('aria-current", "step"', script)
        self.assertIn('aria-live="polite"', english)
        self.assertIn(":focus-visible", css)
        self.assertIn("prefers-reduced-motion", css)
        self.assertIn("@media (max-width: 680px)", css)

    def test_public_demo_and_story_links_resolve_exactly(self) -> None:
        pages = (
            ENGLISH,
            CHINESE,
            DOCS / "project-interview.html",
            DOCS / "project-interview.zh-CN.html",
        )
        for page in pages:
            content = page.read_text(encoding="utf-8")
            for reference in re.findall(r'(?:href|src)="([^"]+)"', content):
                if reference.startswith(("http://", "https://", "mailto:")):
                    continue
                parsed = urlsplit(reference)
                target = (page.parent / parsed.path).resolve() if parsed.path else page
                self.assertTrue(
                    target.exists(),
                    f"{page.name}: linked target does not exist: {reference}",
                )

        story = (DOCS / "project-interview.html").read_text(encoding="utf-8")
        self.assertIn('href="interview-demo.html"', story)
        self.assertIn('href="artifact-replay-interview.html"', story)
        self.assertNotIn("Taxi adoption", story)
        self.assertNotIn("Airbnb replay", story)
        self.assertNotIn("taxi-cross-domain-adoption-pilot.html", story)
        self.assertNotIn("airbnb-live-uncoached-replay-2026-08-21.html", story)

    def test_demo_is_primary_and_other_surfaces_have_narrow_roles(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        home = (DOCS / "index.html").read_text(encoding="utf-8")
        guide = (DOCS / "interview-guide.md").read_text(encoding="utf-8")
        story = (DOCS / "project-interview.html").read_text(encoding="utf-8")

        self.assertIn("Open the interviewer-facing demo", readme)
        self.assertIn("docs/interview-demo.html", readme)
        self.assertIn('href="interview-demo.html"', home)
        self.assertIn(">Interview demo</a", home)
        self.assertIn("owns what the interviewer sees", guide)
        self.assertIn("optional background", guide)
        self.assertIn('href="interview-demo.html"', story)

    def test_architecture_flow_uses_contained_responsive_columns(self) -> None:
        css = (DOCS / "project-interview.css").read_text(encoding="utf-8")
        architecture = css.split(".architecture-flow {", 1)[1].split("}", 1)[0]
        self.assertIn("repeat(4, minmax(0, 1fr))", architecture)
        self.assertNotIn("minmax(90px", architecture)
        node_rule = css.split(".architecture-flow span {", 1)[1].split("}", 1)[0]
        self.assertIn("overflow-wrap: anywhere", node_rule)
        self.assertIn("repeat(2, minmax(0, 1fr))", css)
        self.assertIn("grid-template-columns: 1fr;", css)


if __name__ == "__main__":
    unittest.main()
