from __future__ import annotations

import re
import unittest
from html import unescape
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "docs" / "governed-refund-walkthrough.html"


class GovernedRefundWalkthroughTests(unittest.TestCase):
    def test_walkthrough_preserves_the_verified_story_order(self) -> None:
        content = PAGE.read_text(encoding="utf-8")
        stages = (
            "The human sets the boundary",
            "The demo script simulates the overreach",
            "Real AgentGov evidence blocks completion",
            "A human declines the scope expansion",
            "Fresh evidence returns the work for review",
            "What REVIEW_READY means",
        )
        positions = [content.index(stage) for stage in stages]
        self.assertEqual(positions, sorted(positions))

        for phrase in (
            "refunds/calculation.py",
            "refunds/approval_policy.py",
            "Decline expansion and narrow the changes",
            "Corrected scope:",
            "Pre-approved validation:",
            "Fresh completion reconciliation:",
            "Final AgentGov state:",
            "REVIEW_READY",
        ):
            self.assertIn(phrase, content)

    def test_provenance_and_authority_boundaries_remain_explicit(self) -> None:
        content = PAGE.read_text(encoding="utf-8")
        for phrase in (
            "The demo script, not AgentGov, simulates a coding agent",
            "real governance cycle",
            "Recording this choice edits no code and grants no wider scope.",
            "scripted remediation",
            "AgentGov changes neither file.",
            "It does not modify or restore code.",
            "AgentGov refuses completion validation.",
            "does not claim that AgentGov stopped or rolled back an external coding agent.",
            "records no final acceptance",
            "Passing evidence does not authorize commit, merge, publication, release, or deployment.",
        ):
            self.assertIn(phrase, content)

        self.assertIn("future-0.3 development-source evidence", content)
        self.assertIn("not stable AgentGov 0.2.1 behavior", content)

    def test_code_change_actors_are_separate_and_scannable(self) -> None:
        content = PAGE.read_text(encoding="utf-8")
        actor_section = content.split(
            "<h2>4. A human declines the scope expansion</h2>", 1
        )[1].split("</section>", 1)[0]
        actor_labels = (
            "Human decision",
            "Demo script action",
            "AgentGov role",
        )

        positions = [actor_section.index(label) for label in actor_labels]
        self.assertEqual(positions, sorted(positions))
        self.assertIn("Recording this choice edits no code", actor_section)
        self.assertIn(
            "The demo script—not the simulated coding agent, AgentGov, or the human—",
            actor_section,
        )
        self.assertIn(
            "restores only the out-of-scope approval-policy file", actor_section
        )
        self.assertIn("does not modify or restore code", actor_section)

    def test_modifier_and_restorer_are_explicitly_different_actors(self) -> None:
        content = PAGE.read_text(encoding="utf-8")

        self.assertIn(
            "The simulated coding agent changes the files; it does not perform "
            "the restoration shown later.",
            content,
        )
        self.assertIn(
            "The demo script—not the simulated coding agent, AgentGov, or the human—"
            "performs clearly labelled scripted remediation",
            content,
        )

    def test_public_ctas_do_not_require_internal_milestone_vocabulary(self) -> None:
        content = PAGE.read_text(encoding="utf-8")

        self.assertIn(">Run the source demo</a>", content)
        self.assertIn(">Run the executable demo</a>", content)
        self.assertNotIn("Run M1 on GitHub", content)
        self.assertNotIn("Run the executable M1 demo", content)
        self.assertNotIn("M1", content)
        self.assertNotIn("M2", content)

    def test_page_is_short_local_and_accessible_by_default(self) -> None:
        content = PAGE.read_text(encoding="utf-8")
        main = content.split("<main", 1)[1].split("</main>", 1)[0]
        plain_text = unescape(re.sub(r"<[^>]+>", " ", main))
        word_count = len(re.findall(r"[A-Za-z0-9]+(?:[-'][A-Za-z0-9]+)*", plain_text))

        self.assertGreaterEqual(word_count, 190)
        self.assertLessEqual(word_count, 300)
        self.assertIn('name="viewport"', content)
        self.assertIn('href="guide.css"', content)
        self.assertIn('src="guide.js" defer', content)
        self.assertNotIn("<style", content)
        self.assertNotRegex(content, r"<script(?![^>]+src=)")
        self.assertNotIn("script-src 'unsafe-inline'", content)
        self.assertTrue((ROOT / "docs" / "guide.css").is_file())
        self.assertTrue((ROOT / "docs" / "guide.js").is_file())

    def test_readmes_and_landing_link_the_candidate(self) -> None:
        top_readme = (ROOT / "README.md").read_text(encoding="utf-8")
        demo_readme = (
            ROOT / "examples" / "governed-refund-demo" / "README.md"
        ).read_text(encoding="utf-8")
        landing = (ROOT / "docs" / "index.html").read_text(encoding="utf-8")

        self.assertIn("docs/governed-refund-walkthrough.html", top_readme)
        self.assertIn("../../docs/governed-refund-walkthrough.html", demo_readme)
        self.assertEqual(
            landing.count('href="governed-refund-walkthrough.html"'), 1
        )
        link_position = landing.index('href="governed-refund-walkthrough.html"')
        self.assertLess(landing.index('<section id="example">'), link_position)
        self.assertLess(link_position, landing.index('<section id="report">'))
        self.assertIn(
            "Open the 60-to-90-second governed walkthrough</a", landing
        )
        contrast_rule = landing.split(".case-wrap .button.light {", 1)[1].split(
            "}", 1
        )[0]
        for declaration in (
            "background: white;",
            "color: var(--navy);",
            "border-color: white;",
        ):
            self.assertIn(declaration, contrast_rule)


if __name__ == "__main__":
    unittest.main()
