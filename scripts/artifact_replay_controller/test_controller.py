from __future__ import annotations

import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts.artifact_replay_controller import controller
from scripts.distribution_input_manifest.manifest import check_manifest
from scripts.artifact_replay_harness.harness import (
    ArtifactReplayHarnessError,
    ArtifactReplayHarnessResult,
)


REPOSITORY = Path(__file__).resolve().parents[2]
DIGEST = "sha256:" + "a" * 64


class ArtifactReplayControllerTests(unittest.TestCase):
    def test_current_manifest_matches_source_and_controller_binding(self) -> None:
        observed = check_manifest(REPOSITORY, Path(controller.MANIFEST_RELATIVE))
        self.assertEqual(observed["status"], "PASS", observed["errors"])
        self.assertEqual(observed["path_count"], controller.EXPECTED_PATH_COUNT)
        self.assertEqual(observed["path_digest"], controller.EXPECTED_PATH_DIGEST)
        self.assertEqual(observed["content_digest"], controller.EXPECTED_CONTENT_DIGEST)

    def test_stale_path_identity_or_count_stops_before_harness(self) -> None:
        for field, value in (("path_count", controller.EXPECTED_PATH_COUNT - 1),
                             ("path_digest", DIGEST)):
            with self.subTest(field=field):
                harness = mock.Mock()
                with self.assertRaises(controller.ArtifactReplayControllerError) as caught:
                    controller.run_artifact_replay_controller(
                        self.request(), repository=REPOSITORY, harness_runner=harness,
                        manifest_checker=lambda _repo, _manifest: {
                            **self.manifest_result(), field: value,
                        },
                    )
                harness.assert_not_called()
                self.assertEqual(caught.exception.normalized_report()["reason_code"],
                                 "manifest_preflight_failed")

    def request(self) -> controller.ArtifactReplayControllerRequest:
        return controller.ArtifactReplayControllerRequest(
            python_executable=Path("private-python"),
            backend_wheel=Path("private-wheel.whl"),
            backend_wheel_sha256=DIGEST,
            expected_python_version="3.11.9",
            expected_pip_version="24.0",
            expected_setuptools_version="84.0.0",
            evidence_relative_path="docs/build-validation/new-evidence.md",
            timeout_seconds=10,
        )

    def valid_payload(self) -> dict:
        return {
            "contract": controller.REQUEST_CONTRACT,
            "schema_version": controller.SCHEMA_VERSION,
            "python_executable": "private-python",
            "backend_wheel": "private-wheel.whl",
            "backend_wheel_sha256": DIGEST,
            "expected_python_version": "3.11.9",
            "expected_pip_version": "24.0",
            "expected_setuptools_version": "84.0.0",
            "evidence_relative_path": "docs/build-validation/new-evidence.md",
            "timeout_seconds": 10,
        }

    def manifest_result(self) -> dict:
        return {
            "status": "PASS",
            "path_count": controller.EXPECTED_PATH_COUNT,
            "path_digest": controller.EXPECTED_PATH_DIGEST,
            "content_digest": controller.EXPECTED_CONTENT_DIGEST,
        }

    def manifest_facts(self) -> controller._ManifestFacts:
        return controller._ManifestFacts(
            path_count=controller.EXPECTED_PATH_COUNT,
            path_digest=controller.EXPECTED_PATH_DIGEST,
            content_digest=controller.EXPECTED_CONTENT_DIGEST,
        )

    def test_direct_harness_handoff_uses_internal_source_and_private_request(self) -> None:
        captured = []

        def harness(request):
            captured.append(request)
            return ArtifactReplayHarnessResult(10, DIGEST, 16, DIGEST)

        result = controller.run_artifact_replay_controller(
            self.request(),
            repository=REPOSITORY,
            harness_runner=harness,
            manifest_checker=lambda _repository, _manifest: self.manifest_result(),
        )
        self.assertEqual(result.normalized_report()["status"], "PASS")
        self.assertEqual(len(captured), 1)
        source = captured[0].source
        self.assertIn("execute_real_replay_source", source)
        self.assertIn("ARTIFACT_REPLAY_SOURCE_IDENTITY", source)
        self.assertIn('"manifest_path_count":188', source)
        self.assertIn(controller.EXPECTED_PATH_DIGEST, source)
        self.assertIn(controller.EXPECTED_CONTENT_DIGEST, source)
        self.assertNotIn("check_manifest", source)
        self.assertNotIn("python -c", source)
        self.assertNotIn("source=", repr(captured[0]))
        self.assertNotIn("private-python", repr(self.request()))

    def test_harness_failure_is_bounded_and_never_retried(self) -> None:
        attempts = []

        def harness(_request):
            attempts.append(1)
            raise ArtifactReplayHarnessError(
                "source_execution_failed",
                phase="actual",
                worker_phase="execute",
                dry_attempts=1,
                actual_attempts=1,
            )

        with self.assertRaises(controller.ArtifactReplayControllerError) as caught:
            controller.run_artifact_replay_controller(
                self.request(),
                repository=REPOSITORY,
                harness_runner=harness,
                manifest_checker=lambda _repository, _manifest: self.manifest_result(),
            )
        self.assertEqual(len(attempts), 1)
        report = caught.exception.normalized_report()
        self.assertEqual(report["reason_code"], "harness_source_execution_failed")
        self.assertEqual((report["dry_attempts"], report["actual_attempts"]), (1, 1))

    def test_manifest_preflight_precedes_harness_and_failure_never_launches_it(self) -> None:
        order = []

        def manifest_checker(repository, manifest):
            order.append("manifest")
            self.assertEqual(repository, REPOSITORY.resolve())
            self.assertEqual(manifest, repository / controller.MANIFEST_RELATIVE)
            return self.manifest_result()

        def harness(_request):
            order.append("harness")
            return ArtifactReplayHarnessResult(10, DIGEST, 16, DIGEST)

        controller.run_artifact_replay_controller(
            self.request(),
            repository=REPOSITORY,
            harness_runner=harness,
            manifest_checker=manifest_checker,
        )
        self.assertEqual(order, ["manifest", "harness"])

        order.clear()
        with self.assertRaises(controller.ArtifactReplayControllerError) as caught:
            controller.run_artifact_replay_controller(
                self.request(),
                repository=REPOSITORY,
                harness_runner=harness,
                manifest_checker=lambda _repository, _manifest: {
                    **self.manifest_result(),
                    "content_digest": DIGEST,
                },
            )
        self.assertEqual(order, [])
        self.assertEqual(
            caught.exception.normalized_report(),
            {
                "contract": controller.RESULT_CONTRACT,
                "schema_version": controller.SCHEMA_VERSION,
                "status": "STOPPED_AT_FIRST_DEVIATION",
                "phase": "preflight",
                "reason_code": "manifest_preflight_failed",
                "controller_attempts": 1,
                "dry_attempts": 0,
                "actual_attempts": 0,
                "request_transport": "json_stdin",
                "reads_stdin": True,
                "depends_on_tty": False,
                "authority_boundary": controller._authority_boundary(),
            },
        )

    def test_strict_json_request_excludes_source_and_rejects_extra_fields(self) -> None:
        payload = self.valid_payload()
        request = controller._request_from_mapping(payload)
        self.assertIsInstance(request, controller.ArtifactReplayControllerRequest)
        for invalid in (
            {**payload, "source": "forbidden"},
            {**payload, "timeout_seconds": 0},
            {**payload, "evidence_relative_path": "../outside"},
            {**payload, "backend_wheel_sha256": "bad"},
        ):
            with self.assertRaises(controller.ArtifactReplayControllerError):
                controller._request_from_mapping(invalid)

    def test_main_returns_only_bounded_json_for_success_and_failure(self) -> None:
        payload = json.dumps(self.valid_payload()).encode("utf-8")
        output = io.StringIO()
        code = controller.main(
            io.BytesIO(payload),
            output,
            runner=lambda _request: controller.ArtifactReplayControllerResult(
                10, DIGEST, 16, DIGEST
            ),
        )
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(output.getvalue())["status"], "PASS")
        failed = io.StringIO()
        self.assertEqual(controller.main(io.BytesIO(b"{}"), failed), 1)
        report = json.loads(failed.getvalue())
        self.assertEqual(report["reason_code"], "request_invalid")
        self.assertNotIn("private", failed.getvalue())

    def test_fixed_module_rejects_malformed_input_without_traceback(self) -> None:
        completed = subprocess.run(
            [sys.executable, "-B", "-m", "scripts.artifact_replay_controller"],
            cwd=REPOSITORY,
            input=b"{}",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=10,
            check=False,
        )
        self.assertEqual(completed.returncode, 1)
        self.assertEqual(completed.stderr, b"")
        report = json.loads(completed.stdout.decode("utf-8"))
        self.assertEqual(report["reason_code"], "request_invalid")

    def test_runtime_identity_and_dry_mode_stop_before_caller(self) -> None:
        identity = {
            "source_length": 10,
            "source_sha256": DIGEST,
            "encoded_length": 16,
            "encoded_sha256": DIGEST,
        }
        self.assertEqual(tuple(identity), controller.IDENTITY_KEYS)
        with self.assertRaises(RuntimeError):
            controller._validated_identity({**identity, "extra": 1})

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            launcher = root / "python.exe"
            wheel = root / "backend.whl"
            launcher.write_bytes(b"launcher")
            wheel.write_bytes(b"wheel")
            request = controller.ArtifactReplayControllerRequest(
                python_executable=launcher,
                backend_wheel=wheel,
                backend_wheel_sha256=controller._sha256_bytes(wheel.read_bytes()),
                expected_python_version="3.11.9",
                expected_pip_version="24.0",
                expected_setuptools_version="84.0.0",
                evidence_relative_path="docs/build-validation/new-evidence.md",
                timeout_seconds=10,
            )
            configuration = controller._runtime_mapping(
                request, self.manifest_facts()
            )
            with (
                mock.patch.object(
                    controller,
                    "_filesystem_manifest_preflight",
                    return_value=("pyproject.toml",),
                ) as filesystem_check,
                mock.patch.object(controller, "_short_root_count", return_value=0),
                mock.patch.object(controller, "run_ready_artifact_replay") as caller,
            ):
                controller.execute_real_replay_source(
                    mode="dry", identity=identity, configuration=configuration
                )
            filesystem_check.assert_called_once()
            caller.assert_not_called()

            caller_result = mock.Mock()
            caller_result.normalized_report.return_value = {
                "status": "PASS",
                "readiness_attempts": 1,
                "driver_attempts": 1,
                "readiness": {"probe_attempts": 1},
                "driver": {
                    "action_attempts": 1,
                    "cleanup_removed": True,
                    "root_absent": True,
                },
            }
            request_type = controller.ArtifactInvocationCallerRequest
            with (
                mock.patch.object(
                    controller,
                    "_filesystem_manifest_preflight",
                    return_value=("pyproject.toml",),
                ),
                mock.patch.object(controller, "_short_root_count", return_value=0),
                mock.patch.object(
                    controller,
                    "ArtifactInvocationCallerRequest",
                    wraps=request_type,
                ) as request_constructor,
                mock.patch.object(
                    controller,
                    "run_ready_artifact_replay",
                    return_value=caller_result,
                ),
            ):
                controller.execute_real_replay_source(
                    mode="actual", identity=identity, configuration=configuration
                )
            forwarded = request_constructor.call_args.kwargs
            self.assertEqual(forwarded["manifest_relative_paths"], ("pyproject.toml",))
            self.assertEqual(
                forwarded["manifest_path_count"], controller.EXPECTED_PATH_COUNT
            )
            self.assertEqual(
                forwarded["manifest_path_digest"], controller.EXPECTED_PATH_DIGEST
            )
            self.assertEqual(
                forwarded["manifest_content_digest"],
                controller.EXPECTED_CONTENT_DIGEST,
            )

    def test_worker_manifest_revalidation_uses_filesystem_only_and_detects_drift(self) -> None:
        request = self.request()
        config = controller._runtime_config(
            controller._runtime_mapping(request, self.manifest_facts())
        )
        with mock.patch.object(controller.subprocess, "run") as process:
            paths = controller._filesystem_manifest_preflight(REPOSITORY, config)
        self.assertEqual(len(paths), controller.EXPECTED_PATH_COUNT)
        process.assert_not_called()

        with (
            mock.patch.object(
                controller,
                "canonical_content_digest",
                return_value=DIGEST,
            ),
            self.assertRaisesRegex(
                RuntimeError, "manifest_filesystem_revalidation_failed"
            ),
        ):
            controller._filesystem_manifest_preflight(REPOSITORY, config)


if __name__ == "__main__":
    unittest.main()
