from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LOCAL_PAGE = ROOT / "docs" / "evidence-freshness-rehearsal.html"
SITE = ROOT / "sites" / "evidence-freshness-rehearsal"
HOSTED_PAGE = SITE / "public" / "rehearsal.html"


class EvidenceFreshnessRehearsalSiteTests(unittest.TestCase):
    def test_hosted_page_matches_the_validated_local_page(self) -> None:
        local = LOCAL_PAGE.read_text(encoding="utf-8")
        hosted = HOSTED_PAGE.read_text(encoding="utf-8")
        robots = '  <meta name="robots" content="noindex, nofollow">\n'
        self.assertEqual(hosted.count(robots), 1)
        self.assertEqual(
            local,
            hosted.replace(robots, ""),
            "hosting may add only the bounded robots metadata to the validated page",
        )

    def test_root_route_redirects_to_the_rehearsal(self) -> None:
        page = (SITE / "app" / "page.tsx").read_text(encoding="utf-8")
        self.assertIn('redirect("/rehearsal.html")', page)
        self.assertNotIn("_sites-preview", page)

    def test_metadata_marks_the_test_site_not_for_indexing(self) -> None:
        layout = (SITE / "app" / "layout.tsx").read_text(encoding="utf-8")
        self.assertIn('lang="zh-CN"', layout)
        self.assertIn("index: false", layout)
        self.assertIn("follow: false", layout)
        self.assertNotIn("codex-preview", layout)

    def test_starter_only_capabilities_are_removed(self) -> None:
        package = json.loads((SITE / "package.json").read_text(encoding="utf-8"))
        all_dependencies = {
            **package.get("dependencies", {}),
            **package.get("devDependencies", {}),
        }
        for dependency in (
            "drizzle-orm",
            "drizzle-kit",
            "react-loading-skeleton",
            "tailwindcss",
            "@tailwindcss/postcss",
        ):
            self.assertNotIn(dependency, all_dependencies)

        for removed in (
            "app/_sites-preview",
            "app/chatgpt-auth.ts",
            "db",
            "drizzle",
            "examples",
            "tests/rendered-html.test.mjs",
        ):
            self.assertFalse((SITE / removed).exists())

    def test_hosting_metadata_contains_only_allowed_logical_keys(self) -> None:
        metadata = json.loads(
            (SITE / ".openai" / "hosting.json").read_text(encoding="utf-8")
        )
        self.assertLessEqual(set(metadata), {"project_id", "d1", "r2"})
        self.assertIsNone(metadata.get("d1"))
        self.assertIsNone(metadata.get("r2"))


if __name__ == "__main__":
    unittest.main()
