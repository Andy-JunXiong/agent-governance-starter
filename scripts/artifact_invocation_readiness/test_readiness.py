from __future__ import annotations

from dataclasses import replace
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest import mock

from scripts.artifact_invocation_readiness import readiness


class InvocationReadinessTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="readiness-fixture-")
        self.root = Path(self.temporary.name)
        self.launcher = self.root / "python.exe"
        self.launcher.write_bytes(b"fixed launcher fixture")
        self.backend = self.root / "setuptools-fixture.whl"
        self.backend.write_bytes(b"fixed retained backend fixture")
        self.request = readiness.InvocationTransportRequest(
            encoding_algorithm=readiness.ENCODING_ALGORITHM,
            encoded_length=16,
            encoded_sha256="sha256:" + "1" * 64,
            launcher_path=self.launcher,
            backend_wheel_path=self.backend,
            backend_wheel_sha256=self._identity(self.backend),
            expected_python_version="3.11.9",
            expected_pip_version="24.0",
            expected_setuptools_version="84.0.0",
            authority_request=readiness.denied_authority_request(),
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    @staticmethod
    def _identity(path: Path) -> str:
        return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()

    @staticmethod
    def _completed(**updates: object) -> subprocess.CompletedProcess[bytes]:
        payload = {
            "python_version": "3.11.9",
            "pip_version": "24.0",
            "setuptools_version": "84.0.0",
            "build_wheel_callable": True,
            "vendored_wheel_available": True,
        }
        payload.update(updates)
        return subprocess.CompletedProcess(
            args=["private"],
            returncode=0,
            stdout=json.dumps(payload).encode("utf-8"),
            stderr=b"private stderr",
        )

    def _check(self, request=None):
        with mock.patch.object(readiness, "_short_root_count", return_value=0), mock.patch.object(
            readiness, "_run_fixed_probe", return_value=self._completed()
        ) as probe:
            result = readiness.check_invocation_readiness(request or self.request)
        return result, probe

    def assert_reason(self, reason: str, request=None, *, probe_attempts: int = 0):
        with mock.patch.object(readiness, "_short_root_count", return_value=0), mock.patch.object(
            readiness, "_run_fixed_probe", return_value=self._completed()
        ) as probe:
            with self.assertRaises(readiness.InvocationReadinessError) as caught:
                readiness.check_invocation_readiness(request or self.request)
        self.assertEqual(caught.exception.reason_code, reason)
        self.assertEqual(caught.exception.probe_attempts, probe_attempts)
        return probe

    def test_pass_receipt_is_bounded_and_private(self) -> None:
        result, probe = self._check()
        self.assertEqual(probe.call_count, 1)
        report = result.normalized_report()
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["probe_attempts"], 1)
        self.assertEqual(report["short_root_count"], 0)
        self.assertFalse(report["reads_stdin"])
        self.assertFalse(report["depends_on_tty"])
        serialized = json.dumps(report, sort_keys=True)
        self.assertNotIn(str(self.launcher), serialized)
        self.assertNotIn(str(self.backend), serialized)
        self.assertNotIn("private stderr", serialized)
        self.assertNotIn(str(self.launcher), repr(self.request))
        self.assertNotIn(str(self.backend), repr(self.request))

    def test_metadata_and_authority_fail_before_probe(self) -> None:
        cases = (
            (replace(self.request, encoding_algorithm="base64"), "encoding_algorithm_invalid"),
            (replace(self.request, encoded_length=15), "encoded_length_invalid"),
            (replace(self.request, encoded_sha256="bad"), "encoded_sha256_invalid"),
            (replace(self.request, backend_wheel_sha256="bad"), "backend_wheel_sha256_invalid"),
            (replace(self.request, expected_python_version="private path"), "expected_version_invalid"),
            (
                replace(
                    self.request,
                    authority_request={**readiness.denied_authority_request(), "retry": True},
                ),
                "authority_request_denied",
            ),
            (replace(self.request, authority_request={}), "authority_request_denied"),
        )
        for request, reason in cases:
            with self.subTest(reason=reason):
                self.assertEqual(self.assert_reason(reason, request).call_count, 0)

        with self.assertRaises(readiness.InvocationReadinessError) as caught:
            readiness.check_invocation_readiness(object())
        self.assertEqual(caught.exception.reason_code, "request_invalid")

        self.assertEqual(
            self.assert_reason(
                "encoded_length_invalid",
                replace(self.request, encoded_length=True),
            ).call_count,
            0,
        )

    def test_missing_nonregular_and_wrong_suffix_files_stop_before_probe(self) -> None:
        missing = self.root / "missing.exe"
        directory = self.root / "directory"
        directory.mkdir()
        wrong_suffix = self.root / "backend.zip"
        wrong_suffix.write_bytes(self.backend.read_bytes())
        cases = (
            (replace(self.request, launcher_path=missing), "launcher_invalid"),
            (replace(self.request, launcher_path=directory), "launcher_invalid"),
            (replace(self.request, backend_wheel_path=missing), "backend_wheel_invalid"),
            (
                replace(
                    self.request,
                    backend_wheel_path=wrong_suffix,
                    backend_wheel_sha256=self._identity(wrong_suffix),
                ),
                "backend_wheel_invalid",
            ),
        )
        for request, reason in cases:
            with self.subTest(reason=reason):
                self.assertEqual(self.assert_reason(reason, request).call_count, 0)

    @unittest.skipUnless(hasattr(os, "symlink"), "symbolic links unavailable")
    def test_linked_file_stops_before_probe(self) -> None:
        linked = self.root / "linked.exe"
        try:
            linked.symlink_to(self.launcher)
        except OSError as exc:
            self.skipTest(f"symbolic-link creation unavailable: {exc}")
        self.assertEqual(
            self.assert_reason(
                "launcher_invalid", replace(self.request, launcher_path=linked)
            ).call_count,
            0,
        )

    def test_backend_digest_mismatch_stops_before_probe(self) -> None:
        request = replace(self.request, backend_wheel_sha256="sha256:" + "2" * 64)
        self.assertEqual(
            self.assert_reason("backend_wheel_digest_mismatch", request).call_count, 0
        )

    def test_existing_root_stops_before_probe_and_after_probe(self) -> None:
        with mock.patch.object(readiness, "_short_root_count", return_value=1), mock.patch.object(
            readiness, "_run_fixed_probe", return_value=self._completed()
        ) as probe:
            with self.assertRaises(readiness.InvocationReadinessError) as caught:
                readiness.check_invocation_readiness(self.request)
        self.assertEqual(caught.exception.reason_code, "short_roots_existing")
        self.assertEqual(caught.exception.probe_attempts, 0)
        self.assertEqual(probe.call_count, 0)

        with mock.patch.object(readiness, "_short_root_count", side_effect=[0, 1]), mock.patch.object(
            readiness, "_run_fixed_probe", return_value=self._completed()
        ) as probe:
            with self.assertRaises(readiness.InvocationReadinessError) as caught:
                readiness.check_invocation_readiness(self.request)
        self.assertEqual(caught.exception.reason_code, "short_roots_existing")
        self.assertEqual(caught.exception.probe_attempts, 1)
        self.assertEqual(probe.call_count, 1)

    def test_root_observer_recognizes_current_and_retained_shapes(self) -> None:
        temporary_root = self.root / "temp"
        temporary_root.mkdir()
        (temporary_root / "agv-0123abcd").mkdir()
        (temporary_root / "agv-0123abcd0123abcd").mkdir()
        (temporary_root / "agv-fedcBA98").mkdir()
        (temporary_root / "agv-0123").mkdir()
        with mock.patch.object(tempfile, "gettempdir", return_value=str(temporary_root)):
            self.assertEqual(readiness._short_root_count(), 2)

    def test_unusable_temporary_root_stops_without_probe(self) -> None:
        not_a_directory = self.root / "not-a-directory"
        not_a_directory.write_bytes(b"fixture")
        with mock.patch.object(
            tempfile, "gettempdir", return_value=str(not_a_directory)
        ), mock.patch.object(readiness, "_run_fixed_probe") as probe:
            with self.assertRaises(readiness.InvocationReadinessError) as caught:
                readiness.check_invocation_readiness(self.request)
        self.assertEqual(caught.exception.reason_code, "temporary_root_invalid")
        self.assertEqual(caught.exception.probe_attempts, 0)
        self.assertEqual(probe.call_count, 0)

        with mock.patch.object(Path, "iterdir", side_effect=OSError("private")):
            with self.assertRaises(readiness.InvocationReadinessError) as caught:
                readiness._short_root_count()
        self.assertEqual(caught.exception.reason_code, "temporary_root_unobservable")

    def test_probe_failures_are_one_attempt_and_private(self) -> None:
        cases = (
            (subprocess.TimeoutExpired(cmd="private", timeout=1), "probe_timeout"),
            (OSError("private path"), "probe_exception"),
        )
        for effect, reason in cases:
            with self.subTest(reason=reason), mock.patch.object(
                readiness, "_short_root_count", return_value=0
            ), mock.patch.object(readiness, "_run_fixed_probe", side_effect=effect) as probe:
                with self.assertRaises(readiness.InvocationReadinessError) as caught:
                    readiness.check_invocation_readiness(self.request)
                self.assertEqual(caught.exception.reason_code, reason)
                self.assertEqual(caught.exception.probe_attempts, 1)
                self.assertEqual(probe.call_count, 1)
                self.assertNotIn("private", json.dumps(caught.exception.normalized_report()))

    def test_nonzero_malformed_and_mismatched_probe_outputs_stop_once(self) -> None:
        cases = (
            (
                subprocess.CompletedProcess([], 2, stdout=b"", stderr=b"private"),
                "probe_nonzero_exit",
            ),
            (subprocess.CompletedProcess([], 0, stdout=b"not-json", stderr=b""), "probe_output_invalid"),
            (self._completed(python_version="3.12.0"), "python_version_mismatch"),
            (self._completed(pip_version="25.0"), "pip_version_mismatch"),
            (self._completed(setuptools_version="85.0.0"), "setuptools_version_mismatch"),
            (self._completed(build_wheel_callable=False), "build_wheel_unavailable"),
            (self._completed(vendored_wheel_available=False), "vendored_wheel_unavailable"),
        )
        for completed, reason in cases:
            with self.subTest(reason=reason), mock.patch.object(
                readiness, "_short_root_count", return_value=0
            ), mock.patch.object(readiness, "_run_fixed_probe", return_value=completed) as probe:
                with self.assertRaises(readiness.InvocationReadinessError) as caught:
                    readiness.check_invocation_readiness(self.request)
                self.assertEqual(caught.exception.reason_code, reason)
                self.assertEqual(caught.exception.probe_attempts, 1)
                self.assertEqual(probe.call_count, 1)

    def test_invalid_and_oversized_probe_shapes_stop_once(self) -> None:
        invalid_values = (
            object(),
            subprocess.CompletedProcess([], 0, stdout=b"x" * 4097, stderr=b""),
            subprocess.CompletedProcess([], 0, stdout=b"[]", stderr=b""),
            subprocess.CompletedProcess(
                [],
                0,
                stdout=json.dumps(
                    {
                        "python_version": "3.11.9",
                        "pip_version": "24.0",
                        "setuptools_version": "84.0.0",
                        "build_wheel_callable": 1,
                        "vendored_wheel_available": True,
                    }
                ).encode(),
                stderr=b"",
            ),
        )
        for completed in invalid_values:
            with self.subTest(completed_type=type(completed).__name__), mock.patch.object(
                readiness, "_short_root_count", return_value=0
            ), mock.patch.object(readiness, "_run_fixed_probe", return_value=completed) as probe:
                with self.assertRaises(readiness.InvocationReadinessError) as caught:
                    readiness.check_invocation_readiness(self.request)
                self.assertEqual(caught.exception.reason_code, "probe_output_invalid" if isinstance(completed, subprocess.CompletedProcess) else "probe_result_invalid")
                self.assertEqual(caught.exception.probe_attempts, 1)
                self.assertEqual(probe.call_count, 1)

    def test_fixed_probe_is_isolated_closed_bounded_and_module_owned(self) -> None:
        completed = self._completed()
        with mock.patch.object(subprocess, "run", return_value=completed) as run:
            returned = readiness._run_fixed_probe(self.launcher)
        self.assertIs(returned, completed)
        args, kwargs = run.call_args
        self.assertEqual(args[0][0], str(self.launcher))
        self.assertEqual(args[0][1:3], ["-I", "-c"])
        self.assertIs(args[0][3], readiness._PROBE_SCRIPT)
        self.assertIs(kwargs["stdin"], subprocess.DEVNULL)
        self.assertIs(kwargs["stdout"], subprocess.PIPE)
        self.assertIs(kwargs["stderr"], subprocess.PIPE)
        self.assertEqual(kwargs["timeout"], readiness.PROBE_TIMEOUT_SECONDS)
        self.assertFalse(kwargs["check"])
        self.assertNotIn("PATH", kwargs["env"])
        self.assertEqual(kwargs["env"]["PIP_NO_INPUT"], "1")

    def test_module_has_no_payload_or_command_runner_surface(self) -> None:
        fields = set(readiness.InvocationTransportRequest.__dataclass_fields__)
        self.assertNotIn("payload", fields)
        self.assertNotIn("source", fields)
        self.assertNotIn("command", fields)
        self.assertNotIn("args", fields)
        package = Path(readiness.__file__).parent
        self.assertFalse((package / "__main__.py").exists())
        source = Path(readiness.__file__).read_text(encoding="utf-8")
        self.assertNotIn("artifact_replay_driver", source)
        self.assertNotIn("create_short_build_root", source)
        self.assertNotIn("input(", source)


if __name__ == "__main__":
    unittest.main()
