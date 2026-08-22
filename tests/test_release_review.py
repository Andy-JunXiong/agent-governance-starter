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
FRESHNESS_FIXTURES = ROOT / "governance/fixtures/evidence-freshness"
REAL_FRESHNESS_RECORD = ROOT / "governance/evidence/release-candidate-0-3-0rc1.json"
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
        consumer_status=CommandEvidence(
            0,
            "# AgentGov Status\n"
            "\n"
            "## At a glance\n"
            "\n"
            "| Area | State | Detail |\n"
            "|---|---|---|\n"
            "| Adoption | incomplete | Layout `unversioned` |\n"
            "\n"
            "## Findings\n"
            "\n"
            "| PASS | WARN | FAIL | ADVISORY |\n"
            "|---:|---:|---:|---:|\n"
            "| 4 | 7 | 0 | 1 |\n",
            "",
        ),
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
            markdown = (output / "REVIEW.md").read_text(encoding="utf-8")
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
        self.assertNotIn("consumer_governance", document)
        self.assertIn("## Consumer governance summary", markdown)
        self.assertIn("Adoption: **incomplete**", markdown)
        self.assertIn("| 4 | 7 | 0 | 1 |", markdown)
        self.assertIn(
            "does not mean consumer governance is complete",
            markdown,
        )

    def test_consumer_summary_renders_configured_and_incomplete_statuses(self) -> None:
        cases = (
            ("configured", (8, 0, 0, 1)),
            ("incomplete", (4, 7, 0, 1)),
        )
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "source"
            consumer = root / "consumer"
            source.mkdir()
            consumer.mkdir()
            wheel, manifest = write_candidate(root)
            review_documents: list[bytes] = []
            for index, (adoption, counts) in enumerate(cases):
                status = (
                    "# AgentGov Status\n\n"
                    "## At a glance\n\n"
                    "| Area | State | Detail |\n"
                    "|---|---|---|\n"
                    f"| Adoption | {adoption} | Layout `1.0` |\n\n"
                    "## Findings\n\n"
                    "| PASS | WARN | FAIL | ADVISORY |\n"
                    "|---:|---:|---:|---:|\n"
                    f"| {counts[0]} | {counts[1]} | {counts[2]} | {counts[3]} |\n"
                )
                collected = evidence()
                collected = ReleaseReviewEvidence(
                    source_tests=collected.source_tests,
                    installed_version=collected.installed_version,
                    manifest_check=collected.manifest_check,
                    consumer_check=collected.consumer_check,
                    consumer_status=CommandEvidence(0, status, ""),
                    upgrade_plan=collected.upgrade_plan,
                )
                output = root / f"review-{index}"

                result = create_release_review_bundle(
                    source,
                    wheel=wheel,
                    manifest_path=manifest,
                    consumer=consumer,
                    output=output,
                    evidence_collector=lambda *_, value=collected: value,
                )
                markdown = (output / "REVIEW.md").read_text(encoding="utf-8")
                document = json.loads(
                    (output / "review.json").read_text(encoding="utf-8")
                )
                review_documents.append((output / "review.json").read_bytes())

                self.assertEqual(result.state, "ready_for_human_review")
                self.assertIn(f"Adoption: **{adoption}**", markdown)
                self.assertIn(
                    f"| {counts[0]} | {counts[1]} | {counts[2]} | {counts[3]} |",
                    markdown,
                )
                self.assertNotIn("consumer_governance", document)

            self.assertEqual(review_documents[0], review_documents[1])

    def test_invalid_consumer_status_fails_atomically(self) -> None:
        cases = (
            "# AgentGov Status\n",
            (
                "| Adoption | partial | Layout `1.0` |\n"
                "| PASS | WARN | FAIL | ADVISORY |\n"
                "|---:|---:|---:|---:|\n"
                "| 4 | 0 | 0 | 1 |\n"
            ),
            (
                "| Adoption | configured | Layout `1.0` |\n"
                "| PASS | WARN | FAIL | ADVISORY |\n"
                "|---:|---:|---:|---:|\n"
                "| four | 0 | 0 | 1 |\n"
            ),
        )
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "source"
            consumer = root / "consumer"
            source.mkdir()
            consumer.mkdir()
            wheel, manifest = write_candidate(root)
            for index, status in enumerate(cases):
                collected = evidence()
                collected = ReleaseReviewEvidence(
                    source_tests=collected.source_tests,
                    installed_version=collected.installed_version,
                    manifest_check=collected.manifest_check,
                    consumer_check=collected.consumer_check,
                    consumer_status=CommandEvidence(0, status, ""),
                    upgrade_plan=collected.upgrade_plan,
                )
                output = root / f"review-invalid-{index}"

                with self.subTest(index=index), self.assertRaises(
                    ReleaseReviewError
                ):
                    create_release_review_bundle(
                        source,
                        wheel=wheel,
                        manifest_path=manifest,
                        consumer=consumer,
                        output=output,
                        evidence_collector=lambda *_, value=collected: value,
                    )
                self.assertFalse(output.exists())

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

    def test_real_freshness_record_is_portable_and_non_blocking(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            consumer = root / "consumer"
            consumer.mkdir()
            wheel, manifest = write_candidate(root)
            output = root / "review"

            result = create_release_review_bundle(
                ROOT,
                wheel=wheel,
                manifest_path=manifest,
                consumer=consumer,
                output=output,
                freshness_record=REAL_FRESHNESS_RECORD.relative_to(ROOT),
                freshness_as_of="2026-08-22",
                evidence_collector=lambda *_: evidence(),
            )
            document = json.loads((output / "review.json").read_text(encoding="utf-8"))
            freshness = json.loads(
                (output / "evidence-freshness.json").read_text(encoding="utf-8")
            )
            markdown = (output / "REVIEW.md").read_text(encoding="utf-8")

        self.assertEqual(result.state, "ready_for_human_review")
        self.assertFalse(result.blocked)
        self.assertEqual(freshness["mode"], "advisory_non_blocking")
        self.assertEqual(
            freshness["record_ref"],
            "governance/evidence/release-candidate-0-3-0rc1.json",
        )
        self.assertEqual(freshness["result"]["status"], "PASS")
        self.assertEqual(freshness["result"]["as_of"], "2026-08-22")
        self.assertTrue(all(value is False for value in freshness["effect"].values()))
        self.assertTrue(
            all(value is False for value in freshness["authority_boundary"].values())
        )
        self.assertNotIn("evidence_freshness", document)
        self.assertNotIn(str(ROOT), json.dumps(freshness))
        self.assertIn("Evidence Freshness pilot (non-blocking)", markdown)
        self.assertIn("does not change release-review gates, state, or exit", markdown)
        self.assertIn("no event was discovered or added automatically", markdown)

    def test_every_freshness_status_leaves_release_review_state_unchanged(self) -> None:
        cases = {
            "current.json": "PASS",
            "review-due.json": "WARN",
            "expired.json": "FAIL",
            "policy-unknown.json": "ADVISORY",
            "not-applicable.json": "NOT_APPLICABLE",
        }
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            consumer = root / "consumer"
            consumer.mkdir()
            wheel, manifest = write_candidate(root)
            for index, (fixture, expected_status) in enumerate(cases.items()):
                with self.subTest(status=expected_status):
                    result = create_release_review_bundle(
                        ROOT,
                        wheel=wheel,
                        manifest_path=manifest,
                        consumer=consumer,
                        output=root / f"review-{index}",
                        freshness_record=(FRESHNESS_FIXTURES / fixture).relative_to(ROOT),
                        freshness_as_of="2026-08-21",
                        evidence_collector=lambda *_: evidence(),
                    )

                    self.assertEqual(result.state, "ready_for_human_review")
                    self.assertFalse(result.blocked)
                    self.assertIsNotNone(result.freshness)
                    self.assertEqual(result.freshness["result"]["status"], expected_status)
                    self.assertNotIn(
                        "evidence-freshness",
                        {gate["id"] for gate in result.gates},
                    )

    def test_invalid_freshness_inputs_fail_atomically(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "source"
            consumer = root / "consumer"
            source.mkdir()
            consumer.mkdir()
            wheel, manifest = write_candidate(root)
            malformed = source / "malformed.json"
            malformed.write_text("{", encoding="utf-8")
            outside = root / "outside.json"
            outside.write_text("{}\n", encoding="utf-8")

            cases = (
                (Path("missing.json"), "2026-08-22", "regular file"),
                (Path("malformed.json"), "2026-08-22", "cannot evaluate"),
                (outside, "2026-08-22", "inside the source repository"),
                (Path("malformed.json"), "not-a-date", "cannot evaluate"),
                (Path("malformed.json"), None, "must be supplied together"),
                (None, "2026-08-22", "must be supplied together"),
            )
            for index, (record, as_of, message) in enumerate(cases):
                output = root / f"review-invalid-{index}"
                with self.subTest(index=index), self.assertRaisesRegex(
                    ReleaseReviewError, message
                ):
                    create_release_review_bundle(
                        source,
                        wheel=wheel,
                        manifest_path=manifest,
                        consumer=consumer,
                        output=output,
                        freshness_record=record,
                        freshness_as_of=as_of,
                        evidence_collector=lambda *_: evidence(),
                    )
                self.assertFalse(output.exists())

    def test_symbolic_link_freshness_input_is_rejected_before_collection(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "source"
            consumer = root / "consumer"
            source.mkdir()
            consumer.mkdir()
            wheel, manifest = write_candidate(root)
            output = root / "review"

            original = Path.is_symlink

            def pretend_link(path: Path) -> bool:
                if path.name == "freshness-link.json":
                    return True
                return original(path)

            with patch.object(Path, "is_symlink", autospec=True, side_effect=pretend_link):
                with self.assertRaisesRegex(ReleaseReviewError, "regular file"):
                    create_release_review_bundle(
                        source,
                        wheel=wheel,
                        manifest_path=manifest,
                        consumer=consumer,
                        output=output,
                        freshness_record=Path("freshness-link.json"),
                        freshness_as_of="2026-08-22",
                        evidence_collector=lambda *_: evidence(),
                    )

            self.assertFalse(output.exists())

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

        freshness_schema = json.loads(
            (
                ROOT
                / "schemas/release-review-evidence-freshness-pilot.schema.json"
            ).read_text(encoding="utf-8")
        )
        self.assertFalse(freshness_schema["additionalProperties"])
        self.assertEqual(
            freshness_schema["properties"]["mode"]["const"],
            "advisory_non_blocking",
        )
        self.assertTrue(
            all(
                item["const"] is False
                for item in freshness_schema["properties"]["effect"]["properties"].values()
            )
        )
        self.assertTrue(
            all(
                item["const"] is False
                for item in freshness_schema["properties"]["authority_boundary"]["properties"].values()
            )
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

    def test_freshness_flags_render_separate_non_blocking_status(self) -> None:
        freshness = {
            "result": {
                "status": "FAIL",
                "as_of": "2026-08-22",
            }
        }
        result = ReleaseReviewResult(
            Path("review"),
            "ready_for_human_review",
            ({"id": "artifact-integrity", "status": "PASS", "detail": "ok"},),
            freshness,
        )
        with patch(
            "agentgov.cli.create_release_review_bundle", return_value=result
        ) as create:
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
                "--freshness-record",
                "governance/evidence/example.json",
                "--freshness-as-of",
                "2026-08-22",
            )

        self.assertEqual(exit_code, EXIT_PASS)
        self.assertIn("FRESHNESS FAIL as-of 2026-08-22 (non-blocking)", stdout)
        self.assertEqual(stderr, "")
        self.assertEqual(
            create.call_args.kwargs["freshness_record"],
            Path("governance/evidence/example.json"),
        )
        self.assertEqual(create.call_args.kwargs["freshness_as_of"], "2026-08-22")

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
