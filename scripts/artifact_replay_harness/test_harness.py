from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest import mock

from scripts.artifact_replay_harness import harness
from scripts.artifact_replay_harness import worker


REPOSITORY = Path(__file__).resolve().parents[2]
SAFE_SOURCE = """\
import scripts.artifact_replay_harness

def artifact_replay_main():
    if ARTIFACT_REPLAY_MODE not in {"dry", "actual"}:
        raise RuntimeError("invalid fixture mode")
    identity = ARTIFACT_REPLAY_SOURCE_IDENTITY
    if set(identity) != {"source_length", "source_sha256", "encoded_length", "encoded_sha256"}:
        raise RuntimeError("invalid fixture identity keys")
    if identity["source_length"] < 1 or identity["encoded_length"] < 1:
        raise RuntimeError("invalid fixture identity lengths")
    if not identity["source_sha256"].startswith("sha256:"):
        raise RuntimeError("invalid fixture source identity")
    if not identity["encoded_sha256"].startswith("sha256:"):
        raise RuntimeError("invalid fixture encoded identity")
"""


class ArtifactReplayHarnessTests(unittest.TestCase):
    def request(self, source: str = SAFE_SOURCE, *, timeout: float = 10.0):
        return harness.ArtifactReplayHarnessRequest(
            source=source,
            repository=REPOSITORY,
            python_executable=Path(sys.executable),
            timeout_seconds=timeout,
        )

    def test_real_module_transport_runs_same_source_dry_then_actual(self) -> None:
        result = harness.run_bounded_artifact_replay(self.request())
        report = result.normalized_report()
        source_bytes = SAFE_SOURCE.encode("utf-8")
        encoded = base64.b64encode(source_bytes)
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["dry_attempts"], 1)
        self.assertEqual(report["actual_attempts"], 1)
        self.assertEqual(report["transport"]["source_length"], len(source_bytes))
        self.assertEqual(report["transport"]["encoded_length"], len(encoded))
        self.assertEqual(
            report["transport"]["source_sha256"],
            "sha256:" + hashlib.sha256(source_bytes).hexdigest(),
        )
        self.assertTrue(all(value is False for value in report["authority_boundary"].values()))

    def test_worker_identity_context_is_exact_and_immutable(self) -> None:
        values = {
            "source_length": 123,
            "source_sha256": "sha256:" + "1" * 64,
            "encoded_length": 164,
            "encoded_sha256": "sha256:" + "2" * 64,
        }
        context = worker._source_identity_context(**values)
        self.assertEqual(dict(context), values)
        self.assertEqual(tuple(context), harness.SOURCE_IDENTITY_KEYS)
        with self.assertRaises(TypeError):
            context["source_length"] = 1

    def test_source_cannot_mutate_or_replace_identity_context(self) -> None:
        cases = (
            (
                "ARTIFACT_REPLAY_SOURCE_IDENTITY['source_length'] = 1\n"
                "def artifact_replay_main():\n    pass\n",
                "source_initialization_failed",
                "initialize",
            ),
            (
                "ARTIFACT_REPLAY_SOURCE_IDENTITY = {}\n"
                "def artifact_replay_main():\n    pass\n",
                "source_identity_context_drift",
                "initialize",
            ),
            (
                "def artifact_replay_main():\n"
                "    global ARTIFACT_REPLAY_SOURCE_IDENTITY\n"
                "    ARTIFACT_REPLAY_SOURCE_IDENTITY = {}\n",
                "source_identity_context_drift",
                "execute",
            ),
        )
        for source, reason, worker_phase in cases:
            with self.subTest(reason=reason, worker_phase=worker_phase), self.assertRaises(
                harness.ArtifactReplayHarnessError
            ) as caught:
                harness.run_bounded_artifact_replay(self.request(source))
            error = caught.exception
            self.assertEqual(error.reason_code, reason)
            self.assertEqual(error.worker_phase, worker_phase)
            self.assertEqual(error.dry_attempts, 1)
            self.assertEqual(error.actual_attempts, 0)

    def test_parent_request_has_no_caller_controlled_identity_fields(self) -> None:
        self.assertEqual(
            set(harness.ArtifactReplayHarnessRequest.__dataclass_fields__),
            {"source", "repository", "python_executable", "timeout_seconds"},
        )
        self.assertNotIn(harness.SOURCE_IDENTITY_GLOBAL, repr(self.request()))

    def test_compile_import_initialize_and_execute_failures_are_bounded(self) -> None:
        cases = (
            ("def broken(:\n    pass\n", "source_compile_failed", "compile"),
            ("import fixture_module_that_does_not_exist\n", "source_import_failed", "import"),
            ("raise RuntimeError('PRIVATE INIT')\n", "source_initialization_failed", "initialize"),
            ("fixture_value = 1\n", "source_entrypoint_invalid", "initialize"),
            (
                "def artifact_replay_main():\n    raise RuntimeError('PRIVATE EXEC')\n",
                "source_execution_failed",
                "execute",
            ),
        )
        for source, reason, worker_phase in cases:
            with self.subTest(reason=reason), self.assertRaises(
                harness.ArtifactReplayHarnessError
            ) as caught:
                harness.run_bounded_artifact_replay(self.request(source))
            error = caught.exception
            self.assertEqual(error.reason_code, reason)
            self.assertEqual(error.phase, "dry")
            self.assertEqual(error.worker_phase, worker_phase)
            self.assertEqual(error.dry_attempts, 1)
            self.assertEqual(error.actual_attempts, 0)
            serialized = json.dumps(error.normalized_report(), sort_keys=True)
            self.assertNotIn("PRIVATE", serialized)
            self.assertNotIn(str(REPOSITORY), serialized)

    def test_source_stdout_and_stderr_are_discarded(self) -> None:
        source = """\
import sys
print("PRIVATE TOP LEVEL")
sys.stderr.write("PRIVATE STDERR")

def artifact_replay_main():
    print("PRIVATE ENTRYPOINT")
"""
        result = harness.run_bounded_artifact_replay(self.request(source))
        serialized = json.dumps(result.normalized_report(), sort_keys=True)
        self.assertNotIn("PRIVATE", serialized)

    def test_os_descriptor_output_fails_closed_without_leaking(self) -> None:
        source = """\
import os

def artifact_replay_main():
    os.write(1, b"PRIVATE DESCRIPTOR OUTPUT")
"""
        with self.assertRaises(harness.ArtifactReplayHarnessError) as caught:
            harness.run_bounded_artifact_replay(self.request(source))
        self.assertEqual(caught.exception.reason_code, "worker_protocol_invalid")
        self.assertEqual(caught.exception.phase, "dry")
        self.assertEqual(caught.exception.actual_attempts, 0)
        self.assertNotIn("PRIVATE", json.dumps(caught.exception.normalized_report()))

    def test_actual_is_called_once_only_after_dry_pass_with_identical_identity(self) -> None:
        seen = []

        def completed(mode: str, payload: dict[str, object]) -> subprocess.CompletedProcess:
            report = {
                "contract": harness.WORKER_CONTRACT,
                "schema_version": harness.SCHEMA_VERSION,
                "status": "PASS",
                "mode": mode,
                "phase": "complete",
                "reason_code": None,
                "source_length": payload["source_length"],
                "source_sha256": payload["source_sha256"],
                "encoded_length": payload["encoded_length"],
                "encoded_sha256": payload["encoded_sha256"],
            }
            return subprocess.CompletedProcess([], 0, json.dumps(report).encode(), b"")

        def run(*args, **kwargs):
            payload = json.loads(kwargs["input"])
            seen.append((tuple(args[0]), payload))
            return completed(payload["mode"], payload)

        with mock.patch.object(harness.subprocess, "run", side_effect=run) as run_mock:
            result = harness.run_bounded_artifact_replay(self.request())
        self.assertEqual(run_mock.call_count, 2)
        self.assertEqual([entry[1]["mode"] for entry in seen], ["dry", "actual"])
        self.assertEqual(seen[0][0][1:], ("-B", "-m", harness.WORKER_MODULE))
        for key in (
            "source_base64",
            "source_length",
            "source_sha256",
            "encoded_length",
            "encoded_sha256",
        ):
            self.assertEqual(seen[0][1][key], seen[1][1][key])
        self.assertEqual(result.normalized_report()["actual_attempts"], 1)

    def test_actual_failure_stops_without_retry(self) -> None:
        calls = []

        def run(*args, **kwargs):
            payload = json.loads(kwargs["input"])
            calls.append(payload["mode"])
            failed = payload["mode"] == "actual"
            report = {
                "contract": harness.WORKER_CONTRACT,
                "schema_version": harness.SCHEMA_VERSION,
                "status": "STOPPED_AT_FIRST_DEVIATION" if failed else "PASS",
                "mode": payload["mode"],
                "phase": "execute" if failed else "complete",
                "reason_code": "source_execution_failed" if failed else None,
                "source_length": payload["source_length"],
                "source_sha256": payload["source_sha256"],
                "encoded_length": payload["encoded_length"],
                "encoded_sha256": payload["encoded_sha256"],
            }
            return subprocess.CompletedProcess(
                [], 1 if failed else 0, json.dumps(report).encode(), b""
            )

        with mock.patch.object(harness.subprocess, "run", side_effect=run), self.assertRaises(
            harness.ArtifactReplayHarnessError
        ) as caught:
            harness.run_bounded_artifact_replay(self.request())
        self.assertEqual(calls, ["dry", "actual"])
        self.assertEqual(caught.exception.phase, "actual")
        self.assertEqual(caught.exception.dry_attempts, 1)
        self.assertEqual(caught.exception.actual_attempts, 1)

    def test_timeout_launch_and_malformed_protocol_never_retry(self) -> None:
        cases = (
            (subprocess.TimeoutExpired("private", 1), "worker_timeout"),
            (OSError("PRIVATE PATH"), "worker_launch_failed"),
            (subprocess.CompletedProcess([], 1, b"PRIVATE TRACEBACK", b""), "worker_protocol_invalid"),
            (subprocess.CompletedProcess([], 1, b"{}", b"PRIVATE STDERR"), "worker_protocol_invalid"),
        )
        for effect, reason in cases:
            with self.subTest(reason=reason), mock.patch.object(
                harness.subprocess, "run", side_effect=effect if isinstance(effect, BaseException) else None,
                return_value=None if isinstance(effect, BaseException) else effect,
            ) as run_mock, self.assertRaises(harness.ArtifactReplayHarnessError) as caught:
                harness.run_bounded_artifact_replay(self.request())
            self.assertEqual(run_mock.call_count, 1)
            self.assertEqual(caught.exception.reason_code, reason)
            self.assertEqual(caught.exception.actual_attempts, 0)
            serialized = json.dumps(caught.exception.normalized_report())
            self.assertNotIn("PRIVATE", serialized)
            self.assertNotIn(str(REPOSITORY), serialized)

    def test_worker_rejects_identity_mismatch_with_bounded_protocol(self) -> None:
        source = b"def artifact_replay_main():\n    pass\n"
        encoded = base64.b64encode(source)
        payload = {
            "contract": harness.WORKER_CONTRACT,
            "schema_version": harness.SCHEMA_VERSION,
            "mode": "dry",
            "encoding_algorithm": harness.ENCODING_ALGORITHM,
            "source_base64": encoded.decode(),
            "source_length": len(source),
            "source_sha256": "sha256:" + "0" * 64,
            "encoded_length": len(encoded),
            "encoded_sha256": "sha256:" + hashlib.sha256(encoded).hexdigest(),
        }
        completed = subprocess.run(
            [sys.executable, "-B", "-m", harness.WORKER_MODULE],
            cwd=REPOSITORY,
            input=json.dumps(payload).encode(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=10,
            check=False,
        )
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        self.assertEqual(completed.stderr, b"")
        self.assertEqual(report["reason_code"], "source_identity_mismatch")
        self.assertEqual(report["phase"], "identity")
        self.assertNotIn("artifact_replay_main", completed.stdout.decode())

    def test_invalid_request_stops_before_process_and_representations_are_private(self) -> None:
        request = self.request()
        self.assertNotIn(SAFE_SOURCE, repr(request))
        self.assertNotIn(str(REPOSITORY), repr(request))
        with mock.patch.object(harness.subprocess, "run") as run_mock, self.assertRaises(
            harness.ArtifactReplayHarnessError
        ) as caught:
            harness.run_bounded_artifact_replay(object())
        self.assertEqual(run_mock.call_count, 0)
        self.assertEqual(caught.exception.dry_attempts, 0)
        self.assertEqual(caught.exception.actual_attempts, 0)


if __name__ == "__main__":
    unittest.main()
