import unittest

from agentgov.path_policy import (
    evaluate_path_scope,
    is_segment_prefix,
    paths_overlap,
    scope_intersects_reference,
    scope_path_error,
)


class PathPolicyTests(unittest.TestCase):
    def test_prefix_matches_only_on_path_segment_boundaries(self) -> None:
        self.assertTrue(is_segment_prefix("src/route", "src/route"))
        self.assertTrue(is_segment_prefix("src/route", "src/route/handler.py"))
        self.assertFalse(is_segment_prefix("src/route", "src/router/handler.py"))
        self.assertFalse(paths_overlap("src/route", "src/router"))

    def test_exclude_always_overrides_include(self) -> None:
        included = evaluate_path_scope(
            "src/app/main.py",
            includes=("src",),
            excludes=("src/generated",),
        )
        excluded = evaluate_path_scope(
            "src/generated/client.py",
            includes=("src",),
            excludes=("src/generated",),
        )

        self.assertTrue(included.admitted)
        self.assertEqual(included.matched_include, "src")
        self.assertFalse(excluded.admitted)
        self.assertEqual(excluded.matched_exclude, "src/generated")

    def test_outside_path_has_no_matching_prefix(self) -> None:
        decision = evaluate_path_scope(
            "tests/test_app.py",
            includes=("src",),
            excludes=(),
        )

        self.assertFalse(decision.admitted)
        self.assertIn("outside every admitted include", decision.reason)

    def test_broad_reference_can_overlap_non_excluded_narrow_scope(self) -> None:
        self.assertTrue(
            scope_intersects_reference(
                "src",
                includes=("src/app",),
                excludes=("src/generated",),
            )
        )
        self.assertFalse(
            scope_intersects_reference(
                "src/generated",
                includes=("src",),
                excludes=("src/generated",),
            )
        )

    def test_unsafe_or_ambiguous_paths_are_rejected(self) -> None:
        for path, phrase in (
            ("src\\app.py", "forward slashes"),
            ("../app.py", "parent traversal"),
            ("/src/app.py", "absolute"),
            ("C:/src/app.py", "repository-relative"),
            ("src/*.py", "not a glob"),
            ("src//app.py", "empty path segments"),
        ):
            with self.subTest(path=path):
                self.assertIn(phrase, scope_path_error(path) or "")


if __name__ == "__main__":
    unittest.main()
