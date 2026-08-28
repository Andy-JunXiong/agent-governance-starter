from __future__ import annotations

import builtins
import hashlib
import io
import json
import os
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest import mock

from scripts.distribution_input_manifest.manifest import (
    canonical_content_digest,
    canonical_path_digest,
    derive_distribution_inputs,
)
from scripts.artifact_replay_driver import (
    ArtifactEvidence,
    ArtifactReplayDriverError,
    ArtifactReplayResult,
    run_artifact_replay,
)
from scripts.short_build_root import (
    BuildRootError,
    ShortBuildRoot,
    create_evidence_receipt,
    remove_short_build_root,
    remove_short_build_root_after_evidence,
)


EVIDENCE_TEXT = "# Fixture artifact evidence\n\nResult: PASS\n"
PYPROJECT = """\
[build-system]
requires = ["setuptools>=69"]
build-backend = "setuptools.build_meta"

[project]
name = "fixture"
version = "1.0"
readme = "README.md"
license = "MIT"

[tool.setuptools.packages.find]
where = ["src"]

[tool.setuptools.data-files]
"share/fixture" = ["data/*.txt"]
"""


class ClosedInput:
    def isatty(self) -> bool:
        return False

    def read(self, *_args, **_kwargs):
        raise EOFError("closed")


class ArtifactReplayDriverTests(unittest.TestCase):
    def fixture_repository(self, root: Path) -> Path:
        repository = root / "repository"
        (repository / "governance").mkdir(parents=True)
        (repository / "evidence").mkdir()
        (repository / "governance" / "manifest.json").write_text(
            "{}\n", encoding="utf-8"
        )
        (repository / "pyproject.toml").write_text(PYPROJECT, encoding="utf-8")
        (repository / "LICENSE").write_text("MIT fixture\n", encoding="utf-8")
        (repository / "README.md").write_text("fixture readme\n", encoding="utf-8")
        (repository / "src" / "fixture").mkdir(parents=True)
        (repository / "src" / "fixture" / "__init__.py").write_text(
            "VALUE = 1\n", encoding="utf-8"
        )
        (repository / "data").mkdir()
        (repository / "data" / "top.txt").write_text("top\n", encoding="utf-8")
        return repository

    def manifest_arguments(self, repository: Path) -> dict[str, object]:
        paths = derive_distribution_inputs(repository)
        return {
            "manifest_relative_paths": paths,
            "manifest_path_count": len(paths),
            "manifest_path_digest": canonical_path_digest(paths),
            "manifest_content_digest": canonical_content_digest(repository, paths),
        }

    def run_fixture(self, repository: Path, action, *, evidence: str = "evidence/run.md"):
        return run_artifact_replay(
            repository=repository,
            manifest_relative_path="governance/manifest.json",
            **self.manifest_arguments(repository),
            projected_relative_paths=["source/example.txt"],
            evidence_relative_path=evidence,
            action=action,
        )

    def cleanup_failure_root(self, error: ArtifactReplayDriverError) -> None:
        root = error.recovery_root
        if root is not None and root.path.exists():
            remove_short_build_root(root)

    def test_success_writes_exact_evidence_and_returns_private_report(self) -> None:
        with TemporaryDirectory() as raw:
            repository = self.fixture_repository(Path(raw))
            observed: list[ShortBuildRoot] = []

            def action(root: ShortBuildRoot) -> ArtifactEvidence:
                observed.append(root)
                (root.path / "fixture.bin").write_bytes(b"artifact")
                return ArtifactEvidence(EVIDENCE_TEXT)

            result = self.run_fixture(repository, action)
            self.assertIsInstance(result, ArtifactReplayResult)
            self.assertEqual(len(observed), 1)
            self.assertFalse(observed[0].path.exists())
            evidence = repository / "evidence" / "run.md"
            self.assertEqual(evidence.read_text(encoding="utf-8"), EVIDENCE_TEXT)
            report = result.normalized_report()
            self.assertEqual(report["status"], "PASS")
            self.assertEqual(report["action_attempts"], 1)
            self.assertTrue(report["evidence_written"])
            self.assertTrue(report["evidence_revalidated"])
            self.assertTrue(report["cleanup_removed"])
            self.assertTrue(report["root_absent"])
            self.assertFalse(report["reads_stdin"])
            rendered = repr(result) + json.dumps(report, sort_keys=True)
            self.assertNotIn(str(repository), rendered)
            self.assertNotIn(EVIDENCE_TEXT.strip(), rendered)

    def test_closed_redirected_and_tty_input_are_ignored(self) -> None:
        states = (ClosedInput(), io.StringIO("ignored"), mock.Mock(isatty=lambda: True))
        with TemporaryDirectory() as raw:
            base = Path(raw)
            for index, state in enumerate(states):
                with self.subTest(index=index):
                    repository = self.fixture_repository(base / str(index))
                    calls = 0

                    def action(_root: ShortBuildRoot) -> ArtifactEvidence:
                        nonlocal calls
                        calls += 1
                        return ArtifactEvidence(EVIDENCE_TEXT)

                    with mock.patch.object(sys, "stdin", state), mock.patch.object(
                        builtins,
                        "input",
                        side_effect=AssertionError("input must not be called"),
                    ):
                        result = self.run_fixture(repository, action)
                    self.assertEqual(calls, 1)
                    self.assertFalse(result.normalized_report()["depends_on_tty"])

    def test_manifest_preflight_is_filesystem_only_and_detects_content_drift(self) -> None:
        with TemporaryDirectory() as raw:
            repository = self.fixture_repository(Path(raw))
            arguments = self.manifest_arguments(repository)
            action = mock.Mock(return_value=ArtifactEvidence(EVIDENCE_TEXT))
            with mock.patch(
                "scripts.distribution_input_manifest.manifest.subprocess.run",
                side_effect=AssertionError("Git must not be launched"),
            ):
                result = run_artifact_replay(
                    repository=repository,
                    manifest_relative_path="governance/manifest.json",
                    **arguments,
                    projected_relative_paths=["source/example.txt"],
                    evidence_relative_path="evidence/run.md",
                    action=action,
                )
            self.assertEqual(result.manifest_path_count, len(arguments["manifest_relative_paths"]))
            action.assert_called_once()

            drifted = self.fixture_repository(Path(raw) / "drifted")
            drifted_arguments = self.manifest_arguments(drifted)
            (drifted / "README.md").write_text("changed\n", encoding="utf-8")
            drifted_action = mock.Mock()
            with mock.patch(
                "scripts.artifact_replay_driver.driver.create_short_build_root"
            ) as create_root, self.assertRaises(ArtifactReplayDriverError) as raised:
                run_artifact_replay(
                    repository=drifted,
                    manifest_relative_path="governance/manifest.json",
                    **drifted_arguments,
                    projected_relative_paths=["source/example.txt"],
                    evidence_relative_path="evidence/run.md",
                    action=drifted_action,
                )
            self.assertEqual(raised.exception.reason_code, "manifest_preflight_failed")
            self.assertEqual(raised.exception.action_attempts, 0)
            self.assertIsNone(raised.exception.recovery_root)
            create_root.assert_not_called()
            drifted_action.assert_not_called()

    def test_manifest_failure_stops_before_root_or_action(self) -> None:
        with TemporaryDirectory() as raw:
            repository = self.fixture_repository(Path(raw))
            action = mock.Mock()
            arguments = self.manifest_arguments(repository)
            arguments["manifest_content_digest"] = "sha256:" + "0" * 64
            with mock.patch(
                "scripts.artifact_replay_driver.driver.create_short_build_root"
            ) as create_root:
                with self.assertRaises(ArtifactReplayDriverError) as raised:
                    run_artifact_replay(
                        repository=repository,
                        manifest_relative_path="governance/manifest.json",
                        **arguments,
                        projected_relative_paths=["source/example.txt"],
                        evidence_relative_path="evidence/run.md",
                        action=action,
                    )
            self.assertEqual(raised.exception.reason_code, "manifest_preflight_failed")
            self.assertIsNone(raised.exception.recovery_root)
            create_root.assert_not_called()
            action.assert_not_called()

    def test_invalid_action_reference_and_projected_paths_fail_closed(self) -> None:
        with TemporaryDirectory() as raw:
            repository = self.fixture_repository(Path(raw))
            with mock.patch(
                "scripts.artifact_replay_driver.driver.create_short_build_root"
            ) as create_root, self.assertRaises(ArtifactReplayDriverError) as raised:
                run_artifact_replay(
                    repository=repository,
                    manifest_relative_path="governance/manifest.json",
                    **self.manifest_arguments(repository),
                    projected_relative_paths=["source/example.txt"],
                    evidence_relative_path="evidence/run.md",
                    action=None,
                )
            self.assertEqual(raised.exception.reason_code, "artifact_action_invalid")
            create_root.assert_not_called()

            with self.assertRaises(ArtifactReplayDriverError) as raised:
                run_artifact_replay(
                    repository=repository,
                    manifest_relative_path="governance/manifest.json",
                    **self.manifest_arguments(repository),
                    projected_relative_paths=[],
                    evidence_relative_path="evidence/run.md",
                    action=lambda _root: ArtifactEvidence(EVIDENCE_TEXT),
                )
            self.assertEqual(raised.exception.reason_code, "root_allocation_failed")
            self.assertIsNone(raised.exception.recovery_root)

            for manifest in ("../manifest.json", "C:/manifest.json", "missing.json"):
                with self.subTest(manifest=manifest), mock.patch(
                    "scripts.artifact_replay_driver.driver.create_short_build_root"
                ) as create_root, self.assertRaises(ArtifactReplayDriverError):
                    run_artifact_replay(
                        repository=repository,
                        manifest_relative_path=manifest,
                        **self.manifest_arguments(repository),
                        projected_relative_paths=["source/example.txt"],
                        evidence_relative_path="evidence/run.md",
                        action=lambda _root: ArtifactEvidence(EVIDENCE_TEXT),
                    )
                create_root.assert_not_called()

    def test_action_failure_is_one_attempt_and_preserves_root(self) -> None:
        with TemporaryDirectory() as raw:
            repository = self.fixture_repository(Path(raw))
            calls = 0

            def action(_root: ShortBuildRoot) -> ArtifactEvidence:
                nonlocal calls
                calls += 1
                raise RuntimeError("raw failure that must not escape")

            with self.assertRaises(ArtifactReplayDriverError) as raised:
                self.run_fixture(repository, action)
            error = raised.exception
            try:
                self.assertEqual(calls, 1)
                self.assertEqual(error.reason_code, "artifact_action_failed")
                self.assertTrue(error.normalized_report()["root_preserved"])
                self.assertNotIn("raw failure", str(error))
                self.assertFalse((repository / "evidence" / "run.md").exists())
            finally:
                self.cleanup_failure_root(error)

    def test_malformed_evidence_payloads_stop_and_preserve_root(self) -> None:
        invalid = (
            "wrong-type",
            ArtifactEvidence(""),
            ArtifactEvidence("missing final newline"),
            ArtifactEvidence("bad\r\n"),
            ArtifactEvidence("bad\x00value\n"),
            ArtifactEvidence("x" * (1024 * 1024 + 1) + "\n"),
        )
        with TemporaryDirectory() as raw:
            base = Path(raw)
            for index, value in enumerate(invalid):
                with self.subTest(index=index):
                    repository = self.fixture_repository(base / str(index))
                    with self.assertRaises(ArtifactReplayDriverError) as raised:
                        self.run_fixture(repository, lambda _root, value=value: value)
                    try:
                        self.assertEqual(
                            raised.exception.reason_code, "evidence_payload_invalid"
                        )
                        self.assertTrue(
                            raised.exception.normalized_report()["root_preserved"]
                        )
                    finally:
                        self.cleanup_failure_root(raised.exception)

    def test_unsafe_existing_and_linked_evidence_targets_fail_before_allocation(self) -> None:
        with TemporaryDirectory() as raw:
            repository = self.fixture_repository(Path(raw))
            existing = repository / "evidence" / "existing.md"
            existing.write_text("preserve\n", encoding="utf-8")
            cases = (
                "../escape.md",
                "/absolute.md",
                "C:/absolute.md",
                "evidence\\wrong.md",
                "evidence/existing.md",
                "missing-parent/run.md",
            )
            for value in cases:
                with self.subTest(value=value), mock.patch(
                    "scripts.artifact_replay_driver.driver.create_short_build_root"
                ) as create_root:
                    with self.assertRaises(ArtifactReplayDriverError):
                        self.run_fixture(
                            repository,
                            lambda _root: ArtifactEvidence(EVIDENCE_TEXT),
                            evidence=value,
                        )
                    create_root.assert_not_called()
            self.assertEqual(existing.read_text(encoding="utf-8"), "preserve\n")

            target = repository / "target"
            target.mkdir()
            linked = repository / "linked"
            try:
                linked.symlink_to(target, target_is_directory=True)
            except (OSError, NotImplementedError) as exc:
                self.skipTest(f"symbolic links unavailable: {exc}")
            with mock.patch(
                "scripts.artifact_replay_driver.driver.create_short_build_root"
            ) as create_root, self.assertRaises(ArtifactReplayDriverError):
                self.run_fixture(
                    repository,
                    lambda _root: ArtifactEvidence(EVIDENCE_TEXT),
                    evidence="linked/run.md",
                )
            create_root.assert_not_called()

    def test_exclusive_create_race_stops_and_preserves_root(self) -> None:
        with TemporaryDirectory() as raw:
            repository = self.fixture_repository(Path(raw))
            evidence = repository / "evidence" / "run.md"

            def action(_root: ShortBuildRoot) -> ArtifactEvidence:
                evidence.write_text("racing writer\n", encoding="utf-8")
                return ArtifactEvidence(EVIDENCE_TEXT)

            with self.assertRaises(ArtifactReplayDriverError) as raised:
                self.run_fixture(repository, action)
            try:
                self.assertEqual(raised.exception.reason_code, "evidence_write_failed")
                self.assertEqual(evidence.read_text(encoding="utf-8"), "racing writer\n")
                self.assertTrue(raised.exception.normalized_report()["root_preserved"])
            finally:
                self.cleanup_failure_root(raised.exception)

    def test_fsync_precedes_receipt_and_cleanup_and_digest_is_exact(self) -> None:
        with TemporaryDirectory() as raw:
            repository = self.fixture_repository(Path(raw))
            order: list[str] = []
            expected = "sha256:" + hashlib.sha256(
                EVIDENCE_TEXT.encode("utf-8")
            ).hexdigest()

            real_fsync = os.fsync
            real_receipt = create_evidence_receipt
            real_cleanup = remove_short_build_root_after_evidence

            def fsync(descriptor: int) -> None:
                order.append("fsync")
                real_fsync(descriptor)

            def receipt(**kwargs):
                self.assertEqual(order, ["fsync"])
                self.assertEqual(kwargs["expected_sha256"], expected)
                order.append("receipt")
                return real_receipt(**kwargs)

            def cleanup(root, value):
                self.assertEqual(order, ["fsync", "receipt"])
                order.append("cleanup")
                return real_cleanup(root, value)

            with mock.patch(
                "scripts.artifact_replay_driver.driver.os.fsync", side_effect=fsync
            ), mock.patch(
                "scripts.artifact_replay_driver.driver.create_evidence_receipt",
                side_effect=receipt,
            ), mock.patch(
                "scripts.artifact_replay_driver.driver.remove_short_build_root_after_evidence",
                side_effect=cleanup,
            ):
                result = self.run_fixture(
                    repository, lambda _root: ArtifactEvidence(EVIDENCE_TEXT)
                )
            self.assertEqual(order, ["fsync", "receipt", "cleanup"])
            self.assertEqual(result.evidence_sha256, expected)

    def test_write_receipt_change_and_cleanup_failures_preserve_root(self) -> None:
        with TemporaryDirectory() as raw:
            base = Path(raw)

            repository = self.fixture_repository(base / "write")
            with mock.patch(
                "scripts.artifact_replay_driver.driver.os.fsync",
                side_effect=OSError("fixture write failure"),
            ), self.assertRaises(ArtifactReplayDriverError) as raised:
                self.run_fixture(
                    repository, lambda _root: ArtifactEvidence(EVIDENCE_TEXT)
                )
            try:
                self.assertEqual(raised.exception.reason_code, "evidence_write_failed")
                self.assertTrue(raised.exception.normalized_report()["root_preserved"])
            finally:
                self.cleanup_failure_root(raised.exception)

            repository = self.fixture_repository(base / "receipt")
            with mock.patch(
                "scripts.artifact_replay_driver.driver.create_evidence_receipt",
                side_effect=BuildRootError("fixture receipt failure"),
            ), self.assertRaises(ArtifactReplayDriverError) as raised:
                self.run_fixture(
                    repository, lambda _root: ArtifactEvidence(EVIDENCE_TEXT)
                )
            try:
                self.assertEqual(raised.exception.reason_code, "evidence_receipt_failed")
                self.assertTrue(raised.exception.normalized_report()["root_preserved"])
            finally:
                self.cleanup_failure_root(raised.exception)

            repository = self.fixture_repository(base / "changed")

            def changed_receipt(**kwargs):
                value = create_evidence_receipt(**kwargs)
                (repository / "evidence" / "run.md").write_text(
                    "changed after receipt\n", encoding="utf-8"
                )
                return value

            with mock.patch(
                "scripts.artifact_replay_driver.driver.create_evidence_receipt",
                side_effect=changed_receipt,
            ), self.assertRaises(ArtifactReplayDriverError) as raised:
                self.run_fixture(
                    repository, lambda _root: ArtifactEvidence(EVIDENCE_TEXT)
                )
            try:
                self.assertEqual(raised.exception.reason_code, "gated_cleanup_failed")
                self.assertTrue(raised.exception.normalized_report()["root_preserved"])
            finally:
                self.cleanup_failure_root(raised.exception)

            repository = self.fixture_repository(base / "cleanup")
            with mock.patch(
                "scripts.artifact_replay_driver.driver.remove_short_build_root_after_evidence",
                side_effect=BuildRootError("fixture cleanup failure"),
            ), self.assertRaises(ArtifactReplayDriverError) as raised:
                self.run_fixture(
                    repository, lambda _root: ArtifactEvidence(EVIDENCE_TEXT)
                )
            try:
                self.assertEqual(raised.exception.reason_code, "gated_cleanup_failed")
                self.assertTrue(raised.exception.normalized_report()["root_preserved"])
            finally:
                self.cleanup_failure_root(raised.exception)

    def test_failure_report_and_evidence_repr_are_privacy_bounded(self) -> None:
        evidence = ArtifactEvidence("private fixture payload\n")
        self.assertNotIn("private fixture", repr(evidence))
        with TemporaryDirectory() as raw:
            repository = self.fixture_repository(Path(raw))
            with self.assertRaises(ArtifactReplayDriverError) as raised:
                self.run_fixture(
                    repository,
                    lambda _root: (_ for _ in ()).throw(RuntimeError(str(repository))),
                )
            try:
                rendered = repr(raised.exception) + json.dumps(
                    raised.exception.normalized_report(), sort_keys=True
                )
                self.assertNotIn(str(repository), rendered)
                self.assertNotIn("RuntimeError", rendered)
                self.assertEqual(raised.exception.action_attempts, 1)
            finally:
                self.cleanup_failure_root(raised.exception)

    def test_module_has_no_public_cli(self) -> None:
        module = Path(__file__).parent
        self.assertFalse((module / "__main__.py").exists())
        import scripts.artifact_replay_driver as exported

        self.assertEqual(
            exported.__all__,
            [
                "ArtifactEvidence",
                "ArtifactReplayDriverError",
                "ArtifactReplayResult",
                "run_artifact_replay",
            ],
        )


if __name__ == "__main__":
    unittest.main()
