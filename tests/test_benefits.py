import contextlib
import io
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from agentgov.benefits import (
    compare_repository_reports,
    render_benefit_comparison_json,
)
from agentgov.cli import EXIT_ERROR, EXIT_PASS, main


ROOT = Path(__file__).resolve().parents[1]


def run_cli(*args: str) -> tuple[int, str, str]:
    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        exit_code = main(list(args))
    return exit_code, stdout.getvalue(), stderr.getvalue()


def report_document(repository: str, findings: list[dict[str, str]]) -> dict[str, object]:
    summary = {"pass": 0, "warn": 0, "fail": 0, "advisory": 0}
    for finding in findings:
        summary[finding["status"].lower()] += 1
    gaps = [finding for finding in findings if finding["status"] != "PASS"]
    return {
        "schema_version": "1.0",
        "tool": {"name": "agentgov", "version": "0.1.0"},
        "repository": repository,
        "summary": summary,
        "findings": findings,
        "known_gaps": gaps,
        "recommended_actions": [
            {
                "check_id": finding["check_id"],
                "status": finding["status"],
                "action": "review",
            }
            for finding in gaps
        ],
        "scope_limitations": ["fixture"],
    }


def finding(check_id: str, status: str) -> dict[str, str]:
    return {"check_id": check_id, "status": status, "message": "fixture"}


def write_report(path: Path, findings: list[dict[str, str]]) -> None:
    path.write_text(
        json.dumps(report_document("same-repository", findings)),
        encoding="utf-8",
    )


class BenefitComparisonTests(unittest.TestCase):
    def test_comparison_reports_matched_transitions_with_denominators(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            before = root / "before.json"
            after = root / "after.json"
            write_report(
                before,
                [
                    finding("stable", "PASS"),
                    finding("fixed", "FAIL"),
                    finding("reviewed", "WARN"),
                    finding("removed", "PASS"),
                ],
            )
            write_report(
                after,
                [
                    finding("stable", "PASS"),
                    finding("fixed", "PASS"),
                    finding("reviewed", "PASS"),
                    finding("added", "FAIL"),
                ],
            )

            comparison = compare_repository_reports(before, after)

        self.assertEqual(comparison.before_finding_count, 4)
        self.assertEqual(comparison.after_finding_count, 4)
        self.assertEqual(comparison.matched_check_count, 3)
        self.assertEqual(comparison.deterministic_failures_resolved, ("fixed",))
        self.assertEqual(
            comparison.non_passing_findings_cleared,
            ("fixed", "reviewed"),
        )
        self.assertEqual(comparison.added_checks, ("added",))
        self.assertEqual(comparison.removed_checks, ("removed",))
        self.assertEqual(comparison.deterministic_failures_introduced, ())

    def test_added_fail_is_not_mislabeled_as_matched_regression(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            before = root / "before.json"
            after = root / "after.json"
            write_report(before, [finding("stable", "PASS")])
            write_report(
                after,
                [finding("stable", "PASS"), finding("new-check", "FAIL")],
            )

            comparison = compare_repository_reports(before, after)

        self.assertEqual(comparison.deterministic_failures_introduced, ())
        self.assertEqual(comparison.added_checks, ("new-check",))

    def test_different_repository_is_rejected(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            before = root / "before.json"
            after = root / "after.json"
            before.write_text(
                json.dumps(report_document("one", [finding("x", "PASS")])),
                encoding="utf-8",
            )
            after.write_text(
                json.dumps(report_document("two", [finding("x", "PASS")])),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "same repository"):
                compare_repository_reports(before, after)

    def test_duplicate_check_id_is_rejected(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            before = root / "before.json"
            after = root / "after.json"
            write_report(before, [finding("x", "PASS"), finding("x", "WARN")])
            write_report(after, [finding("x", "PASS")])

            with self.assertRaisesRegex(ValueError, "duplicate check_id"):
                compare_repository_reports(before, after)

    def test_tampered_summary_is_rejected(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            before = root / "before.json"
            after = root / "after.json"
            document = report_document("same-repository", [finding("x", "FAIL")])
            document["summary"]["fail"] = 0
            before.write_text(json.dumps(document), encoding="utf-8")
            write_report(after, [finding("x", "PASS")])

            with self.assertRaisesRegex(ValueError, "does not match findings"):
                compare_repository_reports(before, after)

    def test_json_contract_has_denominators_and_no_roi_claim(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            before = root / "before.json"
            after = root / "after.json"
            write_report(before, [finding("x", "FAIL")])
            write_report(after, [finding("x", "PASS")])
            payload = json.loads(
                render_benefit_comparison_json(
                    compare_repository_reports(before, after)
                )
            )

        self.assertEqual(payload["mode"], "read_only")
        self.assertEqual(payload["denominators"]["matched_check_count"], 1)
        self.assertEqual(
            payload["evidence"]["deterministic_failures_resolved"],
            ["x"],
        )
        self.assertTrue(any("ROI" in item for item in payload["scope_limitations"]))
        self.assertNotIn("coverage_percentage", json.dumps(payload))
        for value in payload["authority_boundary"].values():
            self.assertFalse(value)

    def test_cli_is_read_only_and_explains_limits(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            before = root / "before.json"
            after = root / "after.json"
            write_report(before, [finding("x", "FAIL")])
            write_report(after, [finding("x", "PASS")])
            before_bytes = before.read_bytes()
            after_bytes = after.read_bytes()

            exit_code, stdout, stderr = run_cli(
                "benefits", "compare", str(before), str(after)
            )

            self.assertEqual(before.read_bytes(), before_bytes)
            self.assertEqual(after.read_bytes(), after_bytes)

        self.assertEqual(exit_code, EXIT_PASS)
        self.assertIn("DENOMINATOR before=1 after=1 matched=1", stdout)
        self.assertIn("failures_resolved=1", stdout)
        self.assertIn("do not prove causality", stdout)
        self.assertEqual(stderr, "")

    def test_cli_missing_report_is_operational_error(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            missing = root / "missing.json"
            exit_code, stdout, stderr = run_cli(
                "benefits", "compare", str(missing), str(missing)
            )

        self.assertEqual(exit_code, EXIT_ERROR)
        self.assertEqual(stdout, "")
        self.assertIn("report not found", stderr)

    def test_schema_is_strict_and_requires_denominators(self) -> None:
        schema = json.loads(
            (ROOT / "schemas/benefit-comparison.schema.json").read_text(
                encoding="utf-8"
            )
        )

        self.assertFalse(schema["additionalProperties"])
        self.assertIn("denominators", schema["required"])
        authority = schema["properties"]["authority_boundary"]
        for property_schema in authority["properties"].values():
            self.assertIs(property_schema["const"], False)


if __name__ == "__main__":
    unittest.main()
