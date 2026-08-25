from __future__ import annotations

import contextlib
import io
import json
import sys
import unittest
from dataclasses import asdict
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from agentgov.cli import EXIT_PASS, main
from agentgov.event_store import LocalStateError, append_governance_event
from agentgov.learning_review import (
    LEARNING_DISPOSITIONS,
    LearningReviewPolicyError,
    build_learning_review,
    learning_candidate_digest,
    learning_review_from_payload,
    load_learning_reviews,
    revalidate_learning_review,
    write_learning_review,
)


ROOT = Path(__file__).resolve().parents[1]
DIGEST = "sha256:" + "a" * 64


def add_scope_failure(
    repository: Path,
    *,
    identity_digit: str,
    occurred_at: str,
    task_id: str = "fixture-task",
) -> str:
    event, _ = append_governance_event(
        repository,
        event_type="scope.checked",
        actor_class="coding_agent",
        actor_label="fixture-agent",
        task_id=task_id,
        task_digest=DIGEST,
        outcome="failed",
        evidence_ref=None,
        reason_codes=("changed_path_outside_scope",),
        occurred_at=occurred_at,
        event_id="evt-" + identity_digit * 32,
    )
    return event.event_id


def repeated_scope_candidate(repository: Path) -> tuple[str, str]:
    first = add_scope_failure(
        repository,
        identity_digit="1",
        occurred_at="2026-08-25T01:00:00.000Z",
    )
    second = add_scope_failure(
        repository,
        identity_digit="2",
        occurred_at="2026-08-25T02:00:00.000Z",
        task_id="other-task",
    )
    return first, second


def run_cli(*args: str) -> tuple[int, str, str]:
    stdout = io.StringIO()
    stderr = io.StringIO()
    original_stdin = sys.stdin
    try:
        sys.stdin = io.StringIO("")
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = main(list(args))
    finally:
        sys.stdin = original_stdin
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


class LearningReviewTests(unittest.TestCase):
    def test_candidate_digest_requires_sorted_unique_repeated_events(self) -> None:
        identities = ("evt-" + "1" * 32, "evt-" + "2" * 32)
        digest = learning_candidate_digest("scope_boundary", identities)

        self.assertRegex(digest, r"^sha256:[0-9a-f]{64}$")
        with self.assertRaisesRegex(LearningReviewPolicyError, "at least two"):
            learning_candidate_digest("scope_boundary", identities[:1])
        with self.assertRaisesRegex(LearningReviewPolicyError, "sorted unique"):
            learning_candidate_digest("scope_boundary", tuple(reversed(identities)))

    def test_record_is_schema_shaped_attributed_and_denies_authority(self) -> None:
        with TemporaryDirectory() as temp_dir:
            repository = Path(temp_dir)
            identities = repeated_scope_candidate(repository)
            review = build_learning_review(
                repository,
                signal_class="scope_boundary",
                disposition="confirmed_constraint_gap",
                reason_codes=("owner_confirmed",),
                recorded_at="2026-08-25T03:00:00.000Z",
                review_id="lrv-" + "3" * 32,
            )
            schema = json.loads(
                (ROOT / "schemas/learning-review.schema.json").read_text(encoding="utf-8")
            )

        self.assertEqual(review.source_event_ids, identities)
        self.assertEqual(review.actor, {"class": "human", "role": "human_product_owner"})
        self.assertEqual(set(asdict(review)), set(schema["required"]))
        self.assertTrue(all(value is False for value in review.authority_boundary.values()))

    def test_all_fixed_dispositions_validate_without_resolution_claims(self) -> None:
        with TemporaryDirectory() as temp_dir:
            repository = Path(temp_dir)
            repeated_scope_candidate(repository)
            for index, disposition in enumerate(LEARNING_DISPOSITIONS):
                with self.subTest(disposition=disposition):
                    review = build_learning_review(
                        repository,
                        signal_class="scope_boundary",
                        disposition=disposition,
                        review_id="lrv-" + format(index + 4, "x") * 32,
                    )
                    self.assertEqual(review.disposition, disposition)
                    self.assertFalse(review.authority_boundary["authorizes_resolution"])

    def test_records_are_create_only_load_in_order_and_reject_malformed_data(self) -> None:
        with TemporaryDirectory() as temp_dir:
            repository = Path(temp_dir)
            repeated_scope_candidate(repository)
            review = build_learning_review(
                repository,
                signal_class="scope_boundary",
                disposition="false_positive",
                recorded_at="2026-08-25T03:00:00.000Z",
                review_id="lrv-" + "a" * 32,
            )
            relative = write_learning_review(repository, review)
            with self.assertRaisesRegex(LocalStateError, "already exists"):
                write_learning_review(repository, review)
            loaded = load_learning_reviews(repository)
            payload = asdict(review)
            payload["candidate_digest"] = "sha256:" + "0" * 64
            with self.assertRaisesRegex(LearningReviewPolicyError, "candidate_digest"):
                learning_review_from_payload(payload)

        self.assertEqual(relative, ".agentgov/learning-reviews/" + review.review_id + ".json")
        self.assertEqual(loaded, (review,))

    def test_preview_becomes_stale_when_current_candidate_changes(self) -> None:
        with TemporaryDirectory() as temp_dir:
            repository = Path(temp_dir)
            repeated_scope_candidate(repository)
            review = build_learning_review(
                repository,
                signal_class="scope_boundary",
                disposition="improvement_candidate",
            )
            add_scope_failure(
                repository,
                identity_digit="3",
                occurred_at="2026-08-25T04:00:00.000Z",
            )

            with self.assertRaisesRegex(LearningReviewPolicyError, "stale"):
                revalidate_learning_review(repository, review)

    def test_one_event_and_free_text_like_reason_fail_closed(self) -> None:
        with TemporaryDirectory() as temp_dir:
            repository = Path(temp_dir)
            add_scope_failure(
                repository,
                identity_digit="1",
                occurred_at="2026-08-25T01:00:00.000Z",
            )
            with self.assertRaisesRegex(LearningReviewPolicyError, "at least two"):
                build_learning_review(
                    repository,
                    signal_class="scope_boundary",
                    disposition="false_positive",
                )
            add_scope_failure(
                repository,
                identity_digit="2",
                occurred_at="2026-08-25T02:00:00.000Z",
            )
            with self.assertRaisesRegex(LearningReviewPolicyError, "snake_case"):
                build_learning_review(
                    repository,
                    signal_class="scope_boundary",
                    disposition="false_positive",
                    reason_codes=("free text is not retained",),
                )

    def test_symbolic_link_review_state_is_rejected_when_supported(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            repository = root / "repository"
            repository.mkdir()
            state = repository / ".agentgov"
            state.mkdir()
            outside = root / "outside"
            outside.mkdir()
            try:
                (state / "learning-reviews").symlink_to(
                    outside, target_is_directory=True
                )
            except OSError as exc:
                self.skipTest(f"symbolic links unavailable: {exc}")

            with self.assertRaisesRegex(
                LearningReviewPolicyError, "non-symbolic-link directory"
            ):
                load_learning_reviews(repository)

    def test_cli_preview_is_read_only_and_noninteractive_apply_is_cancelled(self) -> None:
        with TemporaryDirectory() as temp_dir:
            repository = Path(temp_dir)
            repeated_scope_candidate(repository)
            common = (
                "review",
                "learning",
                str(repository),
                "--signal-class",
                "scope_boundary",
                "--disposition",
                "false_positive",
                "--as-of",
                "2026-08-25T03:00:00.000Z",
            )
            preview_code, preview_out, preview_err = run_cli(*common)
            apply_code, apply_out, apply_err = run_cli(*common, "--apply")

        self.assertEqual(preview_code, EXIT_PASS)
        self.assertEqual(preview_err + apply_err, "")
        self.assertIn("DRY_RUN no Learning review was written", preview_out)
        self.assertNotEqual(apply_code, EXIT_PASS)
        self.assertIn("requires an interactive terminal", apply_out)

    def test_cli_exact_confirmation_creates_one_record_and_alternatives_do_not(self) -> None:
        with TemporaryDirectory() as temp_dir:
            repository = Path(temp_dir)
            repeated_scope_candidate(repository)
            args = (
                "review",
                "learning",
                str(repository),
                "--signal-class",
                "scope_boundary",
                "--disposition",
                "consumer_configuration_needed",
                "--reason-code",
                "consumer_owner_confirmed",
                "--apply",
            )
            cancel_code, cancel_out, cancel_err = run_cli_interactive("record\n", *args)
            accepted_code, accepted_out, accepted_err = run_cli_interactive("RECORD\n", *args)
            reviews = load_learning_reviews(repository)

        self.assertNotEqual(cancel_code, EXIT_PASS)
        self.assertIn("CANCELLED", cancel_out)
        self.assertEqual(cancel_err + accepted_err, "")
        self.assertEqual(accepted_code, EXIT_PASS)
        self.assertIn("RECORDED .agentgov/learning-reviews/", accepted_out)
        self.assertIn("grants no resolution, scope, code, Git", accepted_out)
        self.assertEqual(len(reviews), 1)

    def test_cli_revalidates_changed_candidate_after_confirmation(self) -> None:
        with TemporaryDirectory() as temp_dir:
            repository = Path(temp_dir)
            repeated_scope_candidate(repository)
            stdout = io.StringIO()
            stderr = io.StringIO()
            original_stdin = sys.stdin

            def confirm_after_change(_prompt: str) -> str:
                add_scope_failure(
                    repository,
                    identity_digit="3",
                    occurred_at="2026-08-25T04:00:00.000Z",
                )
                return "RECORD"

            try:
                sys.stdin = InteractiveInput("")
                with patch("builtins.input", side_effect=confirm_after_change), contextlib.redirect_stdout(
                    stdout
                ), contextlib.redirect_stderr(stderr):
                    code = main(
                        [
                            "review",
                            "learning",
                            str(repository),
                            "--signal-class",
                            "scope_boundary",
                            "--disposition",
                            "false_positive",
                            "--apply",
                        ]
                    )
            finally:
                sys.stdin = original_stdin
            reviews = load_learning_reviews(repository)

        self.assertNotEqual(code, EXIT_PASS)
        self.assertIn("stale", stderr.getvalue())
        self.assertEqual(reviews, ())


if __name__ == "__main__":
    unittest.main()
