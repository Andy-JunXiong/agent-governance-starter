import contextlib
import io
import json
import unittest
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory

from agentgov.cli import EXIT_ERROR, EXIT_FAIL, EXIT_PASS, main
from agentgov.evidence_freshness import (
    EvidenceFreshnessStatus,
    check_evidence_freshness,
)


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "governance/fixtures/evidence-freshness"
AS_OF = "2026-08-21"


def run_cli(*args: str) -> tuple[int, str, str]:
    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        exit_code = main(list(args))
    return exit_code, stdout.getvalue(), stderr.getvalue()


def fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def write_record(document: dict, directory: str) -> Path:
    path = Path(directory) / "evidence-freshness.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    return path


class EvidenceFreshnessSchemaTests(unittest.TestCase):
    def test_schema_is_strict_and_versioned(self) -> None:
        schema = json.loads(
            (ROOT / "schemas/evidence-freshness.schema.json").read_text(
                encoding="utf-8"
            )
        )

        self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(
            schema["properties"]["contract"]["const"],
            "agentgov.evidence-freshness",
        )
        self.assertEqual(schema["properties"]["schema_version"]["const"], "1.0")


class EvidenceFreshnessTests(unittest.TestCase):
    def test_current_evidence_passes(self) -> None:
        result = check_evidence_freshness(FIXTURES / "current.json", as_of=AS_OF)

        self.assertIs(result.status, EvidenceFreshnessStatus.PASS)
        self.assertEqual(result.reason_codes, ("current",))

    def test_review_due_is_warning_and_not_inferred_expiry(self) -> None:
        result = check_evidence_freshness(FIXTURES / "review-due.json", as_of=AS_OF)

        self.assertIs(result.status, EvidenceFreshnessStatus.WARN)
        self.assertEqual(result.reason_codes, ("review_due",))
        self.assertIn("elapsed time alone does not invalidate", result.messages[0])

    def test_explicit_expiry_fails(self) -> None:
        result = check_evidence_freshness(FIXTURES / "expired.json", as_of=AS_OF)

        self.assertIs(result.status, EvidenceFreshnessStatus.FAIL)
        self.assertIn("explicitly_expired", result.reason_codes)

    def test_unknown_policy_is_advisory(self) -> None:
        result = check_evidence_freshness(
            FIXTURES / "policy-unknown.json", as_of=AS_OF
        )

        self.assertIs(result.status, EvidenceFreshnessStatus.ADVISORY)
        self.assertEqual(result.reason_codes, ("policy_validity_unknown",))

    def test_explicit_not_applicable_record_is_not_applicable(self) -> None:
        result = check_evidence_freshness(
            FIXTURES / "not-applicable.json", as_of=AS_OF
        )

        self.assertIs(result.status, EvidenceFreshnessStatus.NOT_APPLICABLE)
        self.assertEqual(result.reason_codes, ("declared_not_applicable",))

    def test_superseded_policy_and_matching_invalidation_event_fail(self) -> None:
        cases = (
            ("superseded", None, "policy_superseded"),
            ("current", "evaluation-policy-changed", "invalidation_event_observed"),
        )
        for policy_status, event, reason in cases:
            with self.subTest(reason=reason), TemporaryDirectory() as temp_dir:
                document = fixture("current.json")
                document["validity"]["policy_status"] = policy_status
                if event:
                    document["invalidation"]["observed_events"] = [event]
                result = check_evidence_freshness(
                    write_record(document, temp_dir), as_of=AS_OF
                )

            self.assertIs(result.status, EvidenceFreshnessStatus.FAIL)
            self.assertIn(reason, result.reason_codes)

    def test_unmatched_observed_event_does_not_invalidate_evidence(self) -> None:
        with TemporaryDirectory() as temp_dir:
            document = fixture("current.json")
            document["invalidation"]["observed_events"] = ["documentation-updated"]
            result = check_evidence_freshness(
                write_record(document, temp_dir), as_of=AS_OF
            )

        self.assertIs(result.status, EvidenceFreshnessStatus.PASS)

    def test_malformed_contract_is_fail_with_actionable_field_messages(self) -> None:
        with TemporaryDirectory() as temp_dir:
            document = fixture("current.json")
            document["unexpected"] = True
            document["review"]["reviewed_at"] = "2026-02-30"
            result = check_evidence_freshness(
                write_record(document, temp_dir), as_of=AS_OF
            )

        self.assertIs(result.status, EvidenceFreshnessStatus.FAIL)
        self.assertEqual(result.reason_codes, ("contract_invalid",))
        self.assertTrue(any("exactly" in message for message in result.messages))
        self.assertTrue(any("calendar date" in message for message in result.messages))

    def test_repository_references_reject_absolute_traversal_and_windows_paths(self) -> None:
        invalid_refs = ("/tmp/evidence.json", "../evidence.json", "C:/evidence.json", "docs\\evidence.json")
        for invalid_ref in invalid_refs:
            with self.subTest(reference=invalid_ref), TemporaryDirectory() as temp_dir:
                document = fixture("current.json")
                document["evidence_refs"] = [invalid_ref]
                result = check_evidence_freshness(
                    write_record(document, temp_dir), as_of=AS_OF
                )

            self.assertIs(result.status, EvidenceFreshnessStatus.FAIL)
            self.assertTrue(any("repository-relative POSIX" in item for item in result.messages))

    def test_secret_like_content_is_rejected_without_echoing_it(self) -> None:
        with TemporaryDirectory() as temp_dir:
            document = fixture("not-applicable.json")
            document["applicability"]["reason"] = "password=private-example"
            result = check_evidence_freshness(
                write_record(document, temp_dir), as_of=AS_OF
            )

        self.assertIs(result.status, EvidenceFreshnessStatus.FAIL)
        rendered = " ".join(result.messages)
        self.assertIn("secret-like material", rendered)
        self.assertNotIn("private-example", rendered)

    def test_oversized_references_and_event_lists_fail_closed(self) -> None:
        with TemporaryDirectory() as temp_dir:
            document = fixture("current.json")
            document["validity"]["policy_ref"] = "docs/" + "x" * 240
            document["invalidation"]["declared_events"] = [
                f"event-{index}" for index in range(51)
            ]
            result = check_evidence_freshness(
                write_record(document, temp_dir), as_of=AS_OF
            )

        self.assertIs(result.status, EvidenceFreshnessStatus.FAIL)
        self.assertTrue(any("repository-relative path" in item for item in result.messages))
        self.assertTrue(any("at most 50 items" in item for item in result.messages))

    def test_future_review_date_fails_against_reproducible_as_of_date(self) -> None:
        with TemporaryDirectory() as temp_dir:
            document = fixture("current.json")
            document["review"]["reviewed_at"] = "2026-09-01"
            document["review"]["review_due_on"] = "2026-10-01"
            result = check_evidence_freshness(
                write_record(document, temp_dir), as_of=AS_OF
            )

        self.assertIs(result.status, EvidenceFreshnessStatus.FAIL)
        self.assertIn("reviewed_in_future", result.reason_codes)


class EvidenceFreshnessCliTests(unittest.TestCase):
    def test_cli_reports_warning_without_blocking(self) -> None:
        code, stdout, stderr = run_cli(
            "check",
            "evidence-freshness",
            str(FIXTURES / "review-due.json"),
            "--as-of",
            AS_OF,
        )

        self.assertEqual(code, EXIT_PASS)
        self.assertIn("WARN evidence-freshness:review-due-evaluation-baseline", stdout)
        self.assertIn("review_due", stdout)
        self.assertEqual(stderr, "")

    def test_cli_blocks_explicit_expiry(self) -> None:
        code, stdout, stderr = run_cli(
            "check",
            "evidence-freshness",
            str(FIXTURES / "expired.json"),
            "--as-of",
            AS_OF,
        )

        self.assertEqual(code, EXIT_FAIL)
        self.assertIn("FAIL evidence-freshness:expired-evaluation-baseline", stdout)
        self.assertIn("explicitly_expired", stdout)
        self.assertEqual(stderr, "")

    def test_cli_invalid_as_of_is_operational_error(self) -> None:
        code, stdout, stderr = run_cli(
            "check",
            "evidence-freshness",
            str(FIXTURES / "current.json"),
            "--as-of",
            "not-a-date",
        )

        self.assertEqual(code, EXIT_ERROR)
        self.assertEqual(stdout, "")
        self.assertIn("as_of must use YYYY-MM-DD", stderr)

    def test_cli_malformed_json_does_not_echo_contents(self) -> None:
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "malformed.json"
            path.write_text('{"password": "private-example",', encoding="utf-8")
            code, stdout, stderr = run_cli(
                "check", "evidence-freshness", str(path), "--as-of", AS_OF
            )

        self.assertEqual(code, EXIT_ERROR)
        self.assertEqual(stdout, "")
        self.assertIn("invalid JSON", stderr)
        self.assertNotIn("private-example", stderr)
