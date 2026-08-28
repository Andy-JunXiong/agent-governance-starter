"""Run one digest-bound replay source through dry and actual worker modes.

The source is encoded once and sent over JSON stdin to a fixed repository
module.  The parent never places source text in a command argument, never
retries, and never exposes captured child output or exception text.  This
transport grants no authority to the source it executes.
"""

from __future__ import annotations

import base64
from dataclasses import dataclass, field
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
from typing import Any, Mapping


CONTRACT = "agentgov.bounded-artifact-replay-harness"
SCHEMA_VERSION = "1.0"
WORKER_CONTRACT = "agentgov.bounded-artifact-replay-worker"
WORKER_MODULE = "scripts.artifact_replay_harness.worker"
ENCODING_ALGORITHM = "base64_utf8_v1"
SOURCE_IDENTITY_GLOBAL = "ARTIFACT_REPLAY_SOURCE_IDENTITY"
SOURCE_IDENTITY_KEYS = (
    "source_length",
    "source_sha256",
    "encoded_length",
    "encoded_sha256",
)
MAX_SOURCE_BYTES = 1_000_000
MAX_RESPONSE_BYTES = 4_096
MAX_TIMEOUT_SECONDS = 60.0

_SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_REASON_RE = re.compile(r"^[a-z][a-z0-9_]{0,79}$")
_WORKER_PHASES = {"transport", "identity", "compile", "import", "initialize", "execute", "complete"}
_AUTHORITY_KEYS = (
    "authorizes_source_execution",
    "authorizes_artifact_build",
    "authorizes_dependency_installation",
    "authorizes_network",
    "authorizes_external_agent",
    "authorizes_model_use",
    "authorizes_git_operations",
    "authorizes_publication",
    "authorizes_release",
    "authorizes_deployment",
    "retries_worker",
)


def _authority_boundary() -> Mapping[str, bool]:
    return {key: False for key in _AUTHORITY_KEYS}


def _sha256(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


@dataclass(frozen=True)
class ArtifactReplayHarnessRequest:
    """Private source and fixed local process boundary for one two-phase run."""

    source: str = field(repr=False)
    repository: str | Path = field(repr=False)
    python_executable: str | Path = field(repr=False)
    timeout_seconds: float = field(default=10.0, repr=False)


@dataclass(frozen=True)
class _PreparedSource:
    source_base64: str = field(repr=False)
    source_length: int
    source_sha256: str
    encoded_length: int
    encoded_sha256: str


@dataclass(frozen=True)
class ArtifactReplayHarnessResult:
    """Stable bounded success facts from one dry and one actual attempt."""

    source_length: int
    source_sha256: str
    encoded_length: int
    encoded_sha256: str

    def normalized_report(self) -> Mapping[str, Any]:
        return {
            "contract": CONTRACT,
            "schema_version": SCHEMA_VERSION,
            "status": "PASS",
            "transport": {
                "encoding_algorithm": ENCODING_ALGORITHM,
                "source_length": self.source_length,
                "source_sha256": self.source_sha256,
                "encoded_length": self.encoded_length,
                "encoded_sha256": self.encoded_sha256,
            },
            "dry_attempts": 1,
            "actual_attempts": 1,
            "reads_stdin": False,
            "depends_on_tty": False,
            "authority_boundary": _authority_boundary(),
        }


class ArtifactReplayHarnessError(RuntimeError):
    """One privacy-bounded first deviation with exact attempt accounting."""

    def __init__(
        self,
        reason_code: str,
        *,
        phase: str,
        worker_phase: str,
        dry_attempts: int,
        actual_attempts: int,
        prepared: _PreparedSource | None = None,
    ) -> None:
        super().__init__(reason_code)
        self.reason_code = reason_code
        self.phase = phase
        self.worker_phase = worker_phase
        self.dry_attempts = dry_attempts
        self.actual_attempts = actual_attempts
        self._prepared = prepared

    def normalized_report(self) -> Mapping[str, Any]:
        transport: Mapping[str, Any] | None = None
        if self._prepared is not None:
            transport = {
                "encoding_algorithm": ENCODING_ALGORITHM,
                "source_length": self._prepared.source_length,
                "source_sha256": self._prepared.source_sha256,
                "encoded_length": self._prepared.encoded_length,
                "encoded_sha256": self._prepared.encoded_sha256,
            }
        return {
            "contract": CONTRACT,
            "schema_version": SCHEMA_VERSION,
            "status": "STOPPED_AT_FIRST_DEVIATION",
            "phase": self.phase,
            "worker_phase": self.worker_phase,
            "reason_code": self.reason_code,
            "transport": transport,
            "dry_attempts": self.dry_attempts,
            "actual_attempts": self.actual_attempts,
            "reads_stdin": False,
            "depends_on_tty": False,
            "authority_boundary": _authority_boundary(),
        }


def _stop(
    reason_code: str,
    *,
    phase: str,
    worker_phase: str = "transport",
    dry_attempts: int,
    actual_attempts: int,
    prepared: _PreparedSource | None,
) -> ArtifactReplayHarnessError:
    return ArtifactReplayHarnessError(
        reason_code,
        phase=phase,
        worker_phase=worker_phase,
        dry_attempts=dry_attempts,
        actual_attempts=actual_attempts,
        prepared=prepared,
    )


def _prepare(request: ArtifactReplayHarnessRequest) -> tuple[_PreparedSource, Path, Path, float]:
    if not isinstance(request, ArtifactReplayHarnessRequest):
        raise _stop(
            "harness_request_invalid",
            phase="preflight",
            dry_attempts=0,
            actual_attempts=0,
            prepared=None,
        )
    try:
        repository = Path(request.repository)
        launcher = Path(request.python_executable)
        timeout = float(request.timeout_seconds)
    except (TypeError, ValueError, OSError):
        raise _stop(
            "harness_request_invalid",
            phase="preflight",
            dry_attempts=0,
            actual_attempts=0,
            prepared=None,
        ) from None
    if (
        not isinstance(request.source, str)
        or not request.source
        or not repository.is_dir()
        or repository.is_symlink()
        or not launcher.is_file()
        or launcher.is_symlink()
        or timeout <= 0
        or timeout > MAX_TIMEOUT_SECONDS
    ):
        raise _stop(
            "harness_request_invalid",
            phase="preflight",
            dry_attempts=0,
            actual_attempts=0,
            prepared=None,
        )
    try:
        source_bytes = request.source.encode("utf-8", errors="strict")
    except UnicodeEncodeError:
        raise _stop(
            "source_utf8_invalid",
            phase="preflight",
            dry_attempts=0,
            actual_attempts=0,
            prepared=None,
        ) from None
    if not source_bytes or len(source_bytes) > MAX_SOURCE_BYTES:
        raise _stop(
            "source_length_invalid",
            phase="preflight",
            dry_attempts=0,
            actual_attempts=0,
            prepared=None,
        )
    encoded = base64.b64encode(source_bytes)
    prepared = _PreparedSource(
        source_base64=encoded.decode("ascii"),
        source_length=len(source_bytes),
        source_sha256=_sha256(source_bytes),
        encoded_length=len(encoded),
        encoded_sha256=_sha256(encoded),
    )
    return prepared, repository, launcher, timeout


def _worker_environment() -> Mapping[str, str]:
    allowed = ("SYSTEMROOT", "WINDIR", "COMSPEC", "PATHEXT", "TMP", "TEMP")
    environment = {key: os.environ[key] for key in allowed if key in os.environ}
    environment.update(
        {
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONIOENCODING": "utf-8",
            "PYTHONUTF8": "1",
        }
    )
    return environment


def _payload(prepared: _PreparedSource, mode: str) -> bytes:
    value = {
        "contract": WORKER_CONTRACT,
        "schema_version": SCHEMA_VERSION,
        "mode": mode,
        "encoding_algorithm": ENCODING_ALGORITHM,
        "source_base64": prepared.source_base64,
        "source_length": prepared.source_length,
        "source_sha256": prepared.source_sha256,
        "encoded_length": prepared.encoded_length,
        "encoded_sha256": prepared.encoded_sha256,
    }
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _valid_worker_report(
    value: object,
    *,
    mode: str,
    returncode: int,
    prepared: _PreparedSource,
) -> Mapping[str, Any] | None:
    expected = {
        "contract",
        "schema_version",
        "status",
        "mode",
        "phase",
        "reason_code",
        "source_length",
        "source_sha256",
        "encoded_length",
        "encoded_sha256",
    }
    if not isinstance(value, Mapping) or set(value) != expected:
        return None
    if (
        value.get("contract") != WORKER_CONTRACT
        or value.get("schema_version") != SCHEMA_VERSION
        or value.get("mode") != mode
        or value.get("phase") not in _WORKER_PHASES
        or value.get("source_length") != prepared.source_length
        or value.get("source_sha256") != prepared.source_sha256
        or value.get("encoded_length") != prepared.encoded_length
        or value.get("encoded_sha256") != prepared.encoded_sha256
        or not _SHA256_RE.fullmatch(str(value.get("source_sha256")))
        or not _SHA256_RE.fullmatch(str(value.get("encoded_sha256")))
    ):
        return None
    status = value.get("status")
    reason = value.get("reason_code")
    if status == "PASS":
        if returncode != 0 or value.get("phase") != "complete" or reason is not None:
            return None
    elif status == "STOPPED_AT_FIRST_DEVIATION":
        if returncode != 1 or not isinstance(reason, str) or _REASON_RE.fullmatch(reason) is None:
            return None
    else:
        return None
    return dict(value)


def _run_worker(
    *,
    mode: str,
    prepared: _PreparedSource,
    repository: Path,
    launcher: Path,
    timeout: float,
    dry_attempts: int,
    actual_attempts: int,
) -> None:
    try:
        completed = subprocess.run(
            [str(launcher), "-B", "-m", WORKER_MODULE],
            cwd=repository,
            env=dict(_worker_environment()),
            input=_payload(prepared, mode),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        raise _stop(
            "worker_timeout",
            phase=mode,
            dry_attempts=dry_attempts,
            actual_attempts=actual_attempts,
            prepared=prepared,
        ) from None
    except OSError:
        raise _stop(
            "worker_launch_failed",
            phase=mode,
            dry_attempts=dry_attempts,
            actual_attempts=actual_attempts,
            prepared=prepared,
        ) from None
    except Exception:
        raise _stop(
            "worker_transport_failed",
            phase=mode,
            dry_attempts=dry_attempts,
            actual_attempts=actual_attempts,
            prepared=prepared,
        ) from None

    stdout = completed.stdout
    stderr = completed.stderr
    if (
        not isinstance(stdout, bytes)
        or not isinstance(stderr, bytes)
        or stderr
        or not stdout
        or len(stdout) > MAX_RESPONSE_BYTES
    ):
        raise _stop(
            "worker_protocol_invalid",
            phase=mode,
            dry_attempts=dry_attempts,
            actual_attempts=actual_attempts,
            prepared=prepared,
        )
    try:
        decoded = stdout.decode("utf-8", errors="strict")
        value = json.loads(decoded)
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise _stop(
            "worker_protocol_invalid",
            phase=mode,
            dry_attempts=dry_attempts,
            actual_attempts=actual_attempts,
            prepared=prepared,
        ) from None
    report = _valid_worker_report(
        value,
        mode=mode,
        returncode=completed.returncode,
        prepared=prepared,
    )
    if report is None:
        raise _stop(
            "worker_protocol_invalid",
            phase=mode,
            dry_attempts=dry_attempts,
            actual_attempts=actual_attempts,
            prepared=prepared,
        )
    if report["status"] != "PASS":
        raise _stop(
            str(report["reason_code"]),
            phase=mode,
            worker_phase=str(report["phase"]),
            dry_attempts=dry_attempts,
            actual_attempts=actual_attempts,
            prepared=prepared,
        )


def run_bounded_artifact_replay(
    request: ArtifactReplayHarnessRequest,
) -> ArtifactReplayHarnessResult:
    """Run the exact prepared source once dry, then once actual after dry PASS."""

    prepared, repository, launcher, timeout = _prepare(request)
    _run_worker(
        mode="dry",
        prepared=prepared,
        repository=repository,
        launcher=launcher,
        timeout=timeout,
        dry_attempts=1,
        actual_attempts=0,
    )
    _run_worker(
        mode="actual",
        prepared=prepared,
        repository=repository,
        launcher=launcher,
        timeout=timeout,
        dry_attempts=1,
        actual_attempts=1,
    )
    return ArtifactReplayHarnessResult(
        source_length=prepared.source_length,
        source_sha256=prepared.source_sha256,
        encoded_length=prepared.encoded_length,
        encoded_sha256=prepared.encoded_sha256,
    )
