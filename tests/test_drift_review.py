from __future__ import annotations

import contextlib
import io
import json
import sys
import unittest
from dataclasses import asdict
from pathlib import Path
from tempfile import TemporaryDirectory

from agentgov.cli import EXIT_PASS, main
from agentgov.drift_review import (
    DriftReviewPolicyError,
    build_drift_review_record,
    build_drift_review_status,
    drift_review_policy_from_payload,
    load_drift_review_records,
    render_drift_review_status_github,
    write_drift_review_record,
)
from agentgov.event_store import append_governance_event


ROOT = Path(__file__).resolve().parents[1]
DIGEST = "sha256:" + "1" * 64


def create_repository(parent: Path) -> Path:
    root = parent / "repository"
    root.mkdir()
    return root


def add_verified_completion(root: Path, task_id: str, occurred_at: str) -> None:
    append_governance_event(
        root,
        event_type="completion.reconciled",
        actor_class="coding_agent",
        actor_label="fixture.adapter",
        task_id=task_id,
        task_digest=DIGEST,
        outcome="verified",
        evidence_ref=None,
        occurred_at=occurred_at,
    )


def run_cli(*args: str) -> tuple[int, str, str]:
    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        code = main(list(args))
    return code, stdout.getvalue(), stderr.getvalue()


class InteractiveInput(io.StringIO):
    def isatty(self) -> bool:
        return True


def run_cli_interactive(stdin_text: str, *args: str) -> tuple[int, str, str]:
    stdout = io.StringIO()
    stderr = io.StringIO()
    original_stdin = sys.stdin
    try:
        sys.stdin = InteractiveInput(stdin_text)
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = main(list(args))
    finally:
        sys.stdin = original_stdin
    return code, stdout.getvalue(), stderr.getvalue()


class DriftReviewTests(unittest.TestCase):
    def test_missing_baseline_is_due_but_semantic_drift_remains_advisory(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = create_repository(Path(temp_dir))
            status = build_drift_review_status(root, as_of="2026-08-09T00:00:00.000Z")

        self.assertEqual(status.state, "due")
        self.assertEqual(status.reason_codes, ("initial_review_required",))
        self.assertEqual(status.review_request["semantics"], "advisory")
        self.assertFalse(status.authority_boundary["decides_semantic_drift"])
        self.assertEqual(status.observations["policy_source"], "built_in_default")

    def test_three_unique_verified_tasks_make_review_due(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = create_repository(Path(temp_dir))
            record = build_drift_review_record(
                root,
                action="review_completed",
                outcome="no_drift_evidence",
                recorded_at="2026-08-01T00:00:00.000Z",
                record_id="drr-" + "1" * 32,
            )
            write_drift_review_record(root, record)
            add_verified_completion(root, "task-one", "2026-08-02T00:00:00.000Z")
            add_verified_completion(root, "task-two", "2026-08-03T00:00:00.000Z")
            add_verified_completion(root, "task-three", "2026-08-04T00:00:00.000Z")
            add_verified_completion(root, "task-three", "2026-08-04T01:00:00.000Z")

            status = build_drift_review_status(root, as_of="2026-08-05T00:00:00.000Z")

        self.assertEqual(status.state, "due")
        self.assertEqual(status.reason_codes, ("completed_task_threshold_reached",))
        self.assertEqual(status.observations["completed_tasks_since_review"], 3)

    def test_seven_days_make_review_due_without_completed_tasks(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = create_repository(Path(temp_dir))
            record = build_drift_review_record(
                root,
                action="review_completed",
                outcome="insufficient_evidence",
                recorded_at="2026-08-01T00:00:00.000Z",
                record_id="drr-" + "2" * 32,
            )
            write_drift_review_record(root, record)

            status = build_drift_review_status(root, as_of="2026-08-08T00:00:00.000Z")

        self.assertEqual(status.state, "due")
        self.assertEqual(status.reason_codes, ("age_threshold_reached",))

    def test_human_snooze_is_non_due_until_its_exact_expiry(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = create_repository(Path(temp_dir))
            record = build_drift_review_record(
                root,
                action="snoozed",
                recorded_at="2026-08-09T00:00:00.000Z",
                record_id="drr-" + "3" * 32,
            )
            write_drift_review_record(root, record)

            before = build_drift_review_status(root, as_of="2026-08-15T23:59:59.000Z")
            at_expiry = build_drift_review_status(root, as_of="2026-08-16T00:00:00.000Z")

        self.assertEqual(before.state, "not_due")
        self.assertEqual(before.reason_codes, ("snoozed",))
        self.assertEqual(at_expiry.state, "due")
        self.assertEqual(at_expiry.reason_codes, ("initial_review_required",))

    def test_policy_rejects_deterministic_semantic_classification(self) -> None:
        policy = {
            "contract": "agentgov.drift-review-policy",
            "schema_version": "1.0",
            "cadence": {"max_age_days": 7, "max_completed_tasks": 3, "snooze_days": 7},
            "dimensions": ["requirement", "architecture", "functionality"],
            "semantic_classification": "deterministic",
            "authority_boundary": {
                "decides_semantic_drift": False,
                "authorizes_governance_mutation": False,
                "authorizes_scope_expansion": False,
                "authorizes_exception": False,
                "authorizes_commit": False,
                "authorizes_merge": False,
                "authorizes_deployment": False,
            },
        }
        with self.assertRaisesRegex(DriftReviewPolicyError, "remain advisory"):
            drift_review_policy_from_payload(policy)

    def test_review_records_are_create_only_and_schema_shaped(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = create_repository(Path(temp_dir))
            record = build_drift_review_record(
                root,
                action="review_completed",
                outcome="candidate_drift",
                recorded_at="2026-08-09T00:00:00.000Z",
                record_id="drr-" + "4" * 32,
            )
            written = write_drift_review_record(root, record)
            with self.assertRaisesRegex(DriftReviewPolicyError, "already exists"):
                write_drift_review_record(root, record)
            loaded = load_drift_review_records(root)
            schema = json.loads(
                (ROOT / "schemas/drift-review-record.schema.json").read_text(encoding="utf-8")
            )

        self.assertEqual(loaded, (record,))
        self.assertEqual(set(asdict(record)), set(schema["required"]))
        self.assertEqual(written.name, record.record_id + ".json")

    def test_github_output_warns_without_presenting_a_failure(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = create_repository(Path(temp_dir))
            status = build_drift_review_status(root, as_of="2026-08-09T00:00:00.000Z")
            output = render_drift_review_status_github(status)

        self.assertIn("::warning", output)
        self.assertIn("ADVISORY", output)
        self.assertNotIn("::error", output)
        self.assertIn("not a failing check", output)

    def test_cli_status_and_explicit_record_preview_are_non_failing(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = create_repository(Path(temp_dir))
            status_code, status_out, status_err = run_cli(
                "review", "drift", str(root), "--format", "github", "--as-of", "2026-08-09T00:00:00.000Z"
            )
            preview_code, preview_out, preview_err = run_cli(
                "review",
                "drift",
                str(root),
                "--record-outcome",
                "no_drift_evidence",
                "--as-of",
                "2026-08-09T00:00:00.000Z",
            )

        self.assertEqual((status_code, preview_code), (EXIT_PASS, EXIT_PASS))
        self.assertEqual(status_err + preview_err, "")
        self.assertIn("::warning", status_out)
        self.assertIn("DRY_RUN no review record was written", preview_out)
        self.assertFalse((root / "governance/drift-reviews").exists())

    def test_cli_apply_creates_one_record_and_resets_cadence_without_git_authority(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = create_repository(Path(temp_dir))
            code, output, error = run_cli_interactive(
                "RECORD\n",
                "review",
                "drift",
                str(root),
                "--record-outcome",
                "no_drift_evidence",
                "--as-of",
                "2026-08-09T00:00:00.000Z",
                "--apply",
            )
            status = build_drift_review_status(
                root,
                as_of="2026-08-10T00:00:00.000Z",
            )
            records = load_drift_review_records(root)

        self.assertEqual(code, EXIT_PASS)
        self.assertEqual(error, "")
        self.assertIn("RECORDED governance/drift-reviews/", output)
        self.assertIn("grants no scope, Git, release, or deployment authority", output)
        self.assertEqual(len(records), 1)
        self.assertEqual(status.state, "not_due")
        self.assertEqual(status.reason_codes, ("within_cadence",))

    def test_cli_noninteractive_apply_is_rejected_without_a_record(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = create_repository(Path(temp_dir))
            code, output, error = run_cli(
                "review",
                "drift",
                str(root),
                "--snooze",
                "--as-of",
                "2026-08-09T00:00:00.000Z",
                "--apply",
            )

        self.assertNotEqual(code, EXIT_PASS)
        self.assertEqual(error, "")
        self.assertIn("CANCELLED", output)
        self.assertFalse((root / "governance/drift-reviews").exists())


if __name__ == "__main__":
    unittest.main()
