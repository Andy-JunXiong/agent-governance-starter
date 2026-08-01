import hashlib
import contextlib
import io
import json
import sys
import unittest
import zipfile
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from agentgov.cli import EXIT_ERROR, EXIT_FAIL, EXIT_PASS, main
from agentgov.release_review import (
    CommandEvidence,
    ReleaseReviewConflictError,
    ReleaseReviewError,
    ReleaseReviewEvidence,
    ReleaseReviewResult,
    _run,
    create_release_review_bundle,
)


ROOT = Path(__file__).resolve().parents[1]
STABLE_ONLY_REASON = (
    "only a validated stable release can produce an upgrade PR candidate"
)


def run_cli(*args: str) -> tuple[int, str, str]:
    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        exit_code = main(list(args))
    return exit_code, stdout.getvalue(), stderr.getvalue()


def write_candidate(root: Path) -> tuple[Path, Path]:
    wheel = root / "agent_governance_starter-0.2.0rc1-py3-none-any.whl"
    with zipfile.ZipFile(wheel, "w") as archive:
        archive.writestr(
            "agent_governance_starter-0.2.0rc1.dist-info/METADATA",
            "Metadata-Version: 2.1\n"
            "Name: agent-governance-starter\n"
            "Version: 0.2.0rc1\n",
        )
    digest = hashlib.sha256(wheel.read_bytes()).hexdigest()
    manifest = root / "release-manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "contract": "agentgov.release-manifest",
                "schema_version": "1.0",
                "distribution_name": "agent-governance-starter",
                "tool_version": "0.2.0rc1",
                "channel": "release-candidate",
                "supported_from": ["0.1.0"],
                "readable_layout_versions": ["1.0"],
                "target_layout_version": "1.0",
                "repository_changes_declared": False,
                "declared_migrations": [],
                "release_notes_url": "https://example.invalid/0.2.0rc1",
                "artifact": {
                    "filename": wheel.name,
                    "url": (
                        "https://github.com/Andy-JunXiong/"
                        "agent-governance-starter/releases/download/v0.2.0rc1/"
                        + wheel.name
                    ),
                    "sha256": digest,
                    "install_method": "pipx",
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )
    return wheel, manifest


def evidence(*, source_exit: int = 0) -> ReleaseReviewEvidence:
    return ReleaseReviewEvidence(
        source_tests=CommandEvidence(source_exit, "tests\n", ""),
        installed_version=CommandEvidence(0, "agentgov 0.2.0rc1\n", ""),
        manifest_check=CommandEvidence(0, "PASS\n", ""),
        consumer_check=CommandEvidence(0, "SUMMARY PASS=1 WARN=0 FAIL=0\n", ""),
        consumer_status=CommandEvidence(0, "# AgentGov Status\n", ""),
        upgrade_plan=CommandEvidence(
            1,
            json.dumps(
                {
                    "state": "blocked",
                    "reasons": [STABLE_ONLY_REASON],
                }
            )
            + "\n",
            "",
        ),
    )


class ReleaseReviewBundleTests(unittest.TestCase):
    def test_command_evidence_preserves_unicode_on_windows(self) -> None:
        result = _run([sys.executable, "-c", "print('桌面')"])

        self.assertEqual(result.exit_code, 0)
        self.assertEqual(result.stdout, "桌面\n")

    def test_candidate_bundle_is_atomic_portable_and_pending_human_review(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "source"
            consumer = root / "consumer"
            source.mkdir()
            consumer.mkdir()
            wheel, manifest = write_candidate(root)
            output = root / "review"

            result = create_release_review_bundle(
                source,
                wheel=wheel,
                manifest_path=manifest,
                consumer=consumer,
                output=output,
                evidence_collector=lambda *_: evidence(),
            )
            document = json.loads((output / "review.json").read_text(encoding="utf-8"))
            files = sorted(path.name for path in output.iterdir())

        self.assertEqual(result.state, "ready_for_human_review")
        self.assertEqual(
            files,
            [
                "REVIEW.md",
                "agent_governance_starter-0.2.0rc1-py3-none-any.whl",
                "candidate-checks.txt",
                "consumer-check.txt",
                "consumer-status.md",
                "release-manifest.json",
                "review.json",
                "source-tests.txt",
                "upgrade-plan.json",
            ],
        )
        self.assertEqual(document["source"], {"name": "source"})
        self.assertEqual(document["consumer"], {"name": "consumer"})
        self.assertEqual(document["human_decision"]["state"], "pending")
        self.assertTrue(all(not value for value in document["authority_boundary"].values()))
        self.assertNotIn(str(root), json.dumps(document))

    def test_source_test_failure_creates_blocked_review_evidence(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "source"
            consumer = root / "consumer"
            source.mkdir()
            consumer.mkdir()
            wheel, manifest = write_candidate(root)

            result = create_release_review_bundle(
                source,
                wheel=wheel,
                manifest_path=manifest,
                consumer=consumer,
                output=root / "review",
                evidence_collector=lambda *_: evidence(source_exit=1),
            )

        self.assertTrue(result.blocked)
        source_gate = next(gate for gate in result.gates if gate["id"] == "source-tests")
        self.assertEqual(source_gate["status"], "FAIL")

    def test_digest_mismatch_is_rejected_before_evidence_collection(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "source"
            consumer = root / "consumer"
            source.mkdir()
            consumer.mkdir()
            wheel, manifest = write_candidate(root)
            wheel.write_bytes(wheel.read_bytes() + b"tampered")
            called = False

            def collector(*_args: Path) -> ReleaseReviewEvidence:
                nonlocal called
                called = True
                return evidence()

            with self.assertRaisesRegex(ReleaseReviewError, "SHA-256"):
                create_release_review_bundle(
                    source,
                    wheel=wheel,
                    manifest_path=manifest,
                    consumer=consumer,
                    output=root / "review",
                    evidence_collector=collector,
                )

        self.assertFalse(called)

    def test_existing_output_is_never_overwritten(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "source"
            consumer = root / "consumer"
            output = root / "review"
            source.mkdir()
            consumer.mkdir()
            output.mkdir()
            marker = output / "human.txt"
            marker.write_text("keep\n", encoding="utf-8")
            wheel, manifest = write_candidate(root)

            with self.assertRaises(ReleaseReviewConflictError):
                create_release_review_bundle(
                    source,
                    wheel=wheel,
                    manifest_path=manifest,
                    consumer=consumer,
                    output=output,
                    evidence_collector=lambda *_: evidence(),
                )

            self.assertEqual(marker.read_text(encoding="utf-8"), "keep\n")

    def test_schema_is_strict_and_denies_release_authority(self) -> None:
        schema = json.loads(
            (ROOT / "schemas/release-review.schema.json").read_text(encoding="utf-8")
        )

        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(schema["properties"]["mode"]["const"], "local_review")
        authority = schema["properties"]["authority_boundary"]
        self.assertTrue(
            all(item["const"] is False for item in authority["properties"].values())
        )


class ReleaseReviewCliTests(unittest.TestCase):
    def test_ready_bundle_returns_pass_and_keeps_decision_pending(self) -> None:
        result = ReleaseReviewResult(
            Path("review"),
            "ready_for_human_review",
            ({"id": "artifact-integrity", "status": "PASS", "detail": "ok"},),
        )
        with patch("agentgov.cli.create_release_review_bundle", return_value=result):
            exit_code, stdout, stderr = run_cli(
                "review",
                "release",
                ".",
                "--wheel",
                "candidate.whl",
                "--manifest",
                "manifest.json",
                "--consumer",
                "consumer",
                "--output",
                "review",
            )

        self.assertEqual(exit_code, EXIT_PASS)
        self.assertIn("STATE ready_for_human_review", stdout)
        self.assertIn("DECISION pending", stdout)
        self.assertIn("no Git, tag, push, publish, release, or deploy", stdout)
        self.assertEqual(stderr, "")

    def test_blocked_bundle_retains_policy_failure_exit(self) -> None:
        result = ReleaseReviewResult(
            Path("review"),
            "blocked",
            ({"id": "source-tests", "status": "FAIL", "detail": "failed"},),
        )
        with patch("agentgov.cli.create_release_review_bundle", return_value=result):
            exit_code, stdout, stderr = run_cli(
                "review",
                "release",
                "--wheel",
                "candidate.whl",
                "--manifest",
                "manifest.json",
                "--consumer",
                "consumer",
                "--output",
                "review",
            )

        self.assertEqual(exit_code, EXIT_FAIL)
        self.assertIn("STATE blocked", stdout)
        self.assertEqual(stderr, "")

    def test_existing_output_conflict_is_a_policy_failure(self) -> None:
        with patch(
            "agentgov.cli.create_release_review_bundle",
            side_effect=ReleaseReviewConflictError("review output already exists"),
        ):
            exit_code, stdout, stderr = run_cli(
                "review",
                "release",
                "--wheel",
                "candidate.whl",
                "--manifest",
                "manifest.json",
                "--consumer",
                "consumer",
                "--output",
                "review",
            )

        self.assertEqual(exit_code, EXIT_FAIL)
        self.assertIn("FAIL review release", stdout)
        self.assertEqual(stderr, "")

    def test_invalid_artifact_is_an_operational_error(self) -> None:
        with patch(
            "agentgov.cli.create_release_review_bundle",
            side_effect=ReleaseReviewError("artifact mismatch"),
        ):
            exit_code, stdout, stderr = run_cli(
                "review",
                "release",
                "--wheel",
                "candidate.whl",
                "--manifest",
                "manifest.json",
                "--consumer",
                "consumer",
                "--output",
                "review",
            )

        self.assertEqual(exit_code, EXIT_ERROR)
        self.assertEqual(stdout, "")
        self.assertIn("ERROR review release: artifact mismatch", stderr)


if __name__ == "__main__":
    unittest.main()
