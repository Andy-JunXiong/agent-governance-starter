from __future__ import annotations

import builtins
import json
from pathlib import Path
import sys
import unittest
from unittest import mock

from scripts.artifact_invocation_caller import caller
from scripts.artifact_invocation_readiness import (
    InvocationReadinessError,
    InvocationReadinessResult,
    InvocationTransportRequest,
)
from scripts.artifact_invocation_readiness.readiness import denied_authority_request
from scripts.artifact_replay_driver import (
    ArtifactReplayDriverError,
    ArtifactReplayResult,
)


class _InputState:
    def __init__(self, tty: bool) -> None:
        self._tty = tty

    def isatty(self) -> bool:
        return self._tty


class _DriftedReadinessResult(InvocationReadinessResult):
    def normalized_report(self):
        report = dict(super().normalized_report())
        report["authority_request"] = {
            **report["authority_request"],
            "retry": True,
        }
        return report


class _DriftedDriverResult(ArtifactReplayResult):
    def normalized_report(self):
        report = dict(super().normalized_report())
        report["driver_private_path"] = "private"
        return report


class ArtifactInvocationCallerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.transport = InvocationTransportRequest(
            encoding_algorithm="base64_utf8_v1",
            encoded_length=16,
            encoded_sha256="sha256:" + "1" * 64,
            launcher_path=Path("private-launcher"),
            backend_wheel_path=Path("private-backend.whl"),
            backend_wheel_sha256="sha256:" + "2" * 64,
            expected_python_version="3.11.9",
            expected_pip_version="24.0",
            expected_setuptools_version="84.0.0",
            authority_request=denied_authority_request(),
        )
        self.manifest_paths = ["LICENSE", "pyproject.toml"]
        self.projected = ["src/one.py"]
        self.action = lambda root: None
        self.request = caller.ArtifactInvocationCallerRequest(
            transport=self.transport,
            repository=Path("private-repository"),
            manifest_relative_path="governance/manifest.json",
            manifest_relative_paths=self.manifest_paths,
            manifest_path_count=2,
            manifest_path_digest="sha256:" + "4" * 64,
            manifest_content_digest="sha256:" + "5" * 64,
            projected_relative_paths=self.projected,
            evidence_relative_path="docs/evidence.md",
            action=self.action,
        )
        self.readiness = InvocationReadinessResult(
            encoding_algorithm="base64_utf8_v1",
            encoded_length=16,
            encoded_sha256="sha256:" + "1" * 64,
            backend_wheel_sha256="sha256:" + "2" * 64,
            python_version="3.11.9",
            pip_version="24.0",
            setuptools_version="84.0.0",
            build_wheel_callable=True,
            vendored_wheel_available=True,
        )
        self.driver = ArtifactReplayResult(
            evidence_sha256="sha256:" + "3" * 64,
            manifest_path_count=2,
            manifest_path_digest="sha256:" + "4" * 64,
            manifest_content_digest="sha256:" + "5" * 64,
            action_attempts=1,
            evidence_written=True,
            evidence_revalidated=True,
            cleanup_removed=True,
            root_absent=True,
        )

    def _run(self, *, readiness=None, driver=None):
        events = []

        def readiness_call(value):
            events.append(("readiness", value))
            return self.readiness if readiness is None else readiness

        def driver_call(**kwargs):
            events.append(("driver", kwargs))
            return self.driver if driver is None else driver

        with mock.patch.object(
            caller, "check_invocation_readiness", side_effect=readiness_call
        ) as readiness_mock, mock.patch.object(
            caller, "run_artifact_replay", side_effect=driver_call
        ) as driver_mock:
            result = caller.run_ready_artifact_replay(self.request)
        return result, events, readiness_mock, driver_mock

    def test_pass_is_strictly_ordered_and_forwards_exact_arguments_once(self) -> None:
        result, events, readiness_mock, driver_mock = self._run()
        self.assertEqual([event[0] for event in events], ["readiness", "driver"])
        readiness_mock.assert_called_once_with(self.transport)
        driver_mock.assert_called_once()
        kwargs = driver_mock.call_args.kwargs
        self.assertIs(kwargs["repository"], self.request.repository)
        self.assertIs(kwargs["manifest_relative_paths"], self.manifest_paths)
        self.assertIs(kwargs["projected_relative_paths"], self.projected)
        self.assertIs(kwargs["action"], self.action)
        self.assertEqual(kwargs["manifest_relative_path"], "governance/manifest.json")
        self.assertEqual(kwargs["manifest_path_count"], 2)
        self.assertEqual(kwargs["manifest_path_digest"], "sha256:" + "4" * 64)
        self.assertEqual(kwargs["manifest_content_digest"], "sha256:" + "5" * 64)
        self.assertEqual(kwargs["evidence_relative_path"], "docs/evidence.md")
        report = result.normalized_report()
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["readiness_attempts"], 1)
        self.assertEqual(report["driver_attempts"], 1)
        self.assertEqual(report["readiness"]["status"], "PASS")
        self.assertEqual(report["driver"]["status"], "PASS")
        self.assertTrue(all(value is False for value in report["authority_boundary"].values()))

    def test_readiness_deviations_never_invoke_driver(self) -> None:
        cases = (
            InvocationReadinessError("short_roots_existing", probe_attempts=0),
            InvocationReadinessError("PRIVATE value", probe_attempts=0),
            RuntimeError("private path"),
        )
        expected = (
            "readiness_short_roots_existing",
            "readiness_failed",
            "readiness_exception",
        )
        for effect, reason in zip(cases, expected):
            with self.subTest(reason=reason), mock.patch.object(
                caller, "check_invocation_readiness", side_effect=effect
            ) as readiness_mock, mock.patch.object(caller, "run_artifact_replay") as driver_mock:
                with self.assertRaises(caller.ArtifactInvocationCallerError) as caught:
                    caller.run_ready_artifact_replay(self.request)
                self.assertEqual(caught.exception.reason_code, reason)
                self.assertEqual(caught.exception.phase, "readiness")
                self.assertEqual(caught.exception.driver_attempts, 0)
                self.assertEqual(readiness_mock.call_count, 1)
                self.assertEqual(driver_mock.call_count, 0)
                self.assertNotIn("private", json.dumps(caught.exception.normalized_report()).lower())

    def test_malformed_or_drifted_readiness_result_never_invokes_driver(self) -> None:
        drifted = _DriftedReadinessResult(**self.readiness.__dict__)
        private_version = InvocationReadinessResult(
            **{**self.readiness.__dict__, "python_version": "private path"}
        )
        for value in (object(), drifted, private_version):
            with self.subTest(value_type=type(value).__name__), mock.patch.object(
                caller, "check_invocation_readiness", return_value=value
            ) as readiness_mock, mock.patch.object(caller, "run_artifact_replay") as driver_mock:
                with self.assertRaises(caller.ArtifactInvocationCallerError) as caught:
                    caller.run_ready_artifact_replay(self.request)
                self.assertEqual(caught.exception.reason_code, "readiness_result_invalid")
                self.assertEqual(readiness_mock.call_count, 1)
                self.assertEqual(driver_mock.call_count, 0)

    def test_driver_deviations_do_not_repeat_readiness_or_driver(self) -> None:
        driver_error = ArtifactReplayDriverError(
            "artifact_action_failed",
            root=None,
            action_attempts=1,
            evidence_written=False,
        )
        cases = (
            (driver_error, "driver_artifact_action_failed"),
            (RuntimeError("private path"), "driver_exception"),
        )
        for effect, reason in cases:
            with self.subTest(reason=reason), mock.patch.object(
                caller, "check_invocation_readiness", return_value=self.readiness
            ) as readiness_mock, mock.patch.object(
                caller, "run_artifact_replay", side_effect=effect
            ) as driver_mock:
                with self.assertRaises(caller.ArtifactInvocationCallerError) as caught:
                    caller.run_ready_artifact_replay(self.request)
                error = caught.exception
                self.assertEqual(error.reason_code, reason)
                self.assertEqual(error.phase, "driver")
                self.assertEqual(error.driver_attempts, 1)
                self.assertEqual(readiness_mock.call_count, 1)
                self.assertEqual(driver_mock.call_count, 1)
                if isinstance(effect, ArtifactReplayDriverError):
                    self.assertIs(error.recovery_driver_error, driver_error)
                else:
                    self.assertIsNone(error.recovery_driver_error)

    def test_malformed_or_drifted_driver_result_stops_after_one_call(self) -> None:
        drifted = _DriftedDriverResult(**self.driver.__dict__)
        malformed_count = ArtifactReplayResult(
            **{**self.driver.__dict__, "manifest_path_count": "private"}
        )
        for value in (object(), drifted, malformed_count):
            with self.subTest(value_type=type(value).__name__), mock.patch.object(
                caller, "check_invocation_readiness", return_value=self.readiness
            ) as readiness_mock, mock.patch.object(
                caller, "run_artifact_replay", return_value=value
            ) as driver_mock:
                with self.assertRaises(caller.ArtifactInvocationCallerError) as caught:
                    caller.run_ready_artifact_replay(self.request)
                self.assertEqual(caught.exception.reason_code, "driver_result_invalid")
                self.assertEqual(caught.exception.driver_attempts, 1)
                self.assertEqual(readiness_mock.call_count, 1)
                self.assertEqual(driver_mock.call_count, 1)

    def test_invalid_request_stops_before_both_upstreams(self) -> None:
        with mock.patch.object(caller, "check_invocation_readiness") as readiness_mock, mock.patch.object(
            caller, "run_artifact_replay"
        ) as driver_mock:
            with self.assertRaises(caller.ArtifactInvocationCallerError) as caught:
                caller.run_ready_artifact_replay(object())
        self.assertEqual(caught.exception.reason_code, "caller_request_invalid")
        self.assertEqual(caught.exception.readiness_attempts, 0)
        self.assertEqual(readiness_mock.call_count, 0)
        self.assertEqual(driver_mock.call_count, 0)

    def test_reports_and_representations_exclude_private_values(self) -> None:
        result, _, _, _ = self._run()
        serialized = json.dumps(result.normalized_report(), sort_keys=True)
        for private in (
            "private-repository",
            "private-launcher",
            "private-backend",
            "governance/manifest.json",
            "docs/evidence.md",
        ):
            self.assertNotIn(private, serialized)
            self.assertNotIn(private, repr(self.request))
        self.assertNotIn("lambda", repr(self.request))
        self.assertNotIn("sha256:" + "1" * 64, repr(result))

    def test_closed_redirected_and_tty_input_do_not_change_ordering(self) -> None:
        original = sys.stdin
        try:
            for state in (None, _InputState(False), _InputState(True)):
                with self.subTest(state=state):
                    sys.stdin = state
                    with mock.patch.object(
                        builtins, "input", side_effect=AssertionError("input called")
                    ):
                        result, events, _, _ = self._run()
                    self.assertEqual([event[0] for event in events], ["readiness", "driver"])
                    self.assertFalse(result.normalized_report()["reads_stdin"])
        finally:
            sys.stdin = original

    def test_module_has_no_cli_persistence_or_caller_content_surface(self) -> None:
        package = Path(caller.__file__).parent
        self.assertFalse((package / "__main__.py").exists())
        source = Path(caller.__file__).read_text(encoding="utf-8")
        fields = set(caller.ArtifactInvocationCallerRequest.__dataclass_fields__)
        self.assertNotIn("payload", fields)
        self.assertNotIn("source", fields)
        self.assertNotIn("command", fields)
        self.assertNotIn("receipt_path", fields)
        self.assertNotIn("open(", source)
        self.assertNotIn("input(", source)
        self.assertNotIn("subprocess", source)
        self.assertNotIn("requests", source)


if __name__ == "__main__":
    unittest.main()
