"""Fail-closed readiness evidence for a future artifact invocation.

The checker accepts transport metadata, private file references, expected
backend identities, and denied authority only.  It never accepts payload
bytes or caller source, decodes content, invokes the artifact driver, creates
or removes a short root, builds an artifact, installs dependencies, uses a
network, reads stdin, branches on TTY state, or retries.

Its only process operation is one fixed, module-owned launcher capability
probe after every non-process gate passes.  The resulting receipt is bounded
point-in-time evidence.  A future caller owns ordering; the existing artifact
driver neither consumes nor enforces this receipt.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import tempfile
from typing import Any, Mapping


CONTRACT = "agentgov.artifact-invocation-transport-readiness"
SCHEMA_VERSION = "1.0"
ENCODING_ALGORITHM = "base64_utf8_v1"
MAX_ENCODED_LENGTH = 1024 * 1024
PROBE_TIMEOUT_SECONDS = 10
MAX_PROBE_OUTPUT_BYTES = 4096

AUTHORITY_KEYS = (
    "execute_caller_source",
    "invoke_artifact_driver",
    "allocate_short_root",
    "remove_short_root",
    "build_artifact",
    "read_stdin",
    "depend_on_tty",
    "install_dependencies",
    "use_network",
    "retry",
    "start_external_agent",
    "use_model",
    "authorize_git_operations",
    "authorize_publication",
    "authorize_release",
    "authorize_deployment",
)

_SHA256_IDENTITY_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_VERSION_RE = re.compile(r"^[0-9]+(?:\.[0-9]+)+(?:[A-Za-z0-9._+-]{0,24})$")
# The repository's current allocator uses 8 hex characters.  The admitted
# transport task retained a 16-character future contract assumption.  Treat
# either exact shape as task-owned so the readiness check cannot miss a live
# root during the transition.
_SHORT_ROOT_RE = re.compile(r"^agv-(?:[0-9a-f]{8}|[0-9a-f]{16})$")

_PROBE_SCRIPT = """\
import importlib.metadata
import importlib.util
import json
import platform
import setuptools.build_meta

print(json.dumps({
    "python_version": platform.python_version(),
    "pip_version": importlib.metadata.version("pip"),
    "setuptools_version": importlib.metadata.version("setuptools"),
    "build_wheel_callable": callable(getattr(setuptools.build_meta, "build_wheel", None)),
    "vendored_wheel_available": importlib.util.find_spec("setuptools._vendor.wheel") is not None,
}, sort_keys=True, separators=(",", ":")))
"""


def denied_authority_request() -> Mapping[str, bool]:
    """Return the exact authority request accepted by this checker."""

    return {key: False for key in AUTHORITY_KEYS}


@dataclass(frozen=True)
class InvocationTransportRequest:
    """Normalized metadata and private host references for one readiness check."""

    encoding_algorithm: str
    encoded_length: int
    encoded_sha256: str
    launcher_path: Path = field(repr=False)
    backend_wheel_path: Path = field(repr=False)
    backend_wheel_sha256: str
    expected_python_version: str
    expected_pip_version: str
    expected_setuptools_version: str
    authority_request: Mapping[str, bool]


@dataclass(frozen=True)
class InvocationReadinessResult:
    """Privacy-bounded PASS receipt for one point-in-time observation."""

    encoding_algorithm: str
    encoded_length: int
    encoded_sha256: str
    backend_wheel_sha256: str
    python_version: str
    pip_version: str
    setuptools_version: str
    build_wheel_callable: bool
    vendored_wheel_available: bool

    def normalized_report(self) -> Mapping[str, Any]:
        return {
            "contract": CONTRACT,
            "schema_version": SCHEMA_VERSION,
            "status": "PASS",
            "transport": {
                "encoding_algorithm": self.encoding_algorithm,
                "encoded_length": self.encoded_length,
                "encoded_sha256": self.encoded_sha256,
            },
            "backend": {
                "wheel_sha256": self.backend_wheel_sha256,
                "python_version": self.python_version,
                "pip_version": self.pip_version,
                "setuptools_version": self.setuptools_version,
                "build_wheel_callable": self.build_wheel_callable,
                "vendored_wheel_available": self.vendored_wheel_available,
            },
            "probe_attempts": 1,
            "short_root_count": 0,
            "reads_stdin": False,
            "depends_on_tty": False,
            "authority_request": denied_authority_request(),
        }


class InvocationReadinessError(RuntimeError):
    """One normalized first deviation without private path or process detail."""

    def __init__(self, reason_code: str, *, probe_attempts: int = 0) -> None:
        super().__init__(reason_code)
        self.reason_code = reason_code
        self.probe_attempts = probe_attempts

    def normalized_report(self) -> Mapping[str, Any]:
        return {
            "contract": CONTRACT,
            "schema_version": SCHEMA_VERSION,
            "status": "STOPPED_AT_FIRST_DEVIATION",
            "reason_code": self.reason_code,
            "probe_attempts": self.probe_attempts,
            "reads_stdin": False,
            "depends_on_tty": False,
            "authority_request": denied_authority_request(),
        }


def _stop(reason_code: str, *, probe_attempts: int = 0) -> InvocationReadinessError:
    return InvocationReadinessError(reason_code, probe_attempts=probe_attempts)


def _validate_request(request: InvocationTransportRequest) -> None:
    if not isinstance(request, InvocationTransportRequest):
        raise _stop("request_invalid")
    if request.encoding_algorithm != ENCODING_ALGORITHM:
        raise _stop("encoding_algorithm_invalid")
    if (
        isinstance(request.encoded_length, bool)
        or not isinstance(request.encoded_length, int)
        or request.encoded_length <= 0
        or request.encoded_length > MAX_ENCODED_LENGTH
        or request.encoded_length % 4 != 0
    ):
        raise _stop("encoded_length_invalid")
    if not _SHA256_IDENTITY_RE.fullmatch(request.encoded_sha256):
        raise _stop("encoded_sha256_invalid")
    if not _SHA256_IDENTITY_RE.fullmatch(request.backend_wheel_sha256):
        raise _stop("backend_wheel_sha256_invalid")
    for value in (
        request.expected_python_version,
        request.expected_pip_version,
        request.expected_setuptools_version,
    ):
        if not isinstance(value, str) or not _VERSION_RE.fullmatch(value):
            raise _stop("expected_version_invalid")
    authority = request.authority_request
    if (
        not isinstance(authority, Mapping)
        or set(authority) != set(AUTHORITY_KEYS)
        or any(authority[key] is not False for key in AUTHORITY_KEYS)
    ):
        raise _stop("authority_request_denied")


def _regular_non_link_file(value: object, reason_code: str) -> Path:
    if not isinstance(value, Path):
        raise _stop(reason_code)
    try:
        file_stat = value.lstat()
        if stat.S_ISLNK(file_stat.st_mode) or not stat.S_ISREG(file_stat.st_mode):
            raise _stop(reason_code)
        resolved = value.resolve(strict=True)
        resolved_stat = resolved.lstat()
        if stat.S_ISLNK(resolved_stat.st_mode) or not stat.S_ISREG(resolved_stat.st_mode):
            raise _stop(reason_code)
    except InvocationReadinessError:
        raise
    except (OSError, RuntimeError):
        raise _stop(reason_code) from None
    return resolved


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            for block in iter(lambda: handle.read(64 * 1024), b""):
                digest.update(block)
    except OSError:
        raise _stop("backend_wheel_unreadable") from None
    return "sha256:" + digest.hexdigest()


def _short_root_count() -> int:
    try:
        temporary_root = Path(tempfile.gettempdir())
        root_stat = temporary_root.lstat()
        if stat.S_ISLNK(root_stat.st_mode) or not stat.S_ISDIR(root_stat.st_mode):
            raise _stop("temporary_root_invalid")
        return sum(
            1
            for child in temporary_root.iterdir()
            if _SHORT_ROOT_RE.fullmatch(child.name)
            and (child.exists() or child.is_symlink())
        )
    except InvocationReadinessError:
        raise
    except (OSError, RuntimeError):
        raise _stop("temporary_root_unobservable") from None


def _bounded_environment() -> Mapping[str, str]:
    environment = {
        "PYTHONNOUSERSITE": "1",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PIP_DISABLE_PIP_VERSION_CHECK": "1",
        "PIP_NO_INPUT": "1",
        "NO_COLOR": "1",
    }
    for key in ("SYSTEMROOT", "WINDIR"):
        value = os.environ.get(key)
        if value:
            environment[key] = value
    return environment


def _run_fixed_probe(launcher: Path) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        [str(launcher), "-I", "-c", _PROBE_SCRIPT],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=str(launcher.parent),
        env=dict(_bounded_environment()),
        timeout=PROBE_TIMEOUT_SECONDS,
        check=False,
    )


def _probe_observation(
    completed: subprocess.CompletedProcess[bytes],
) -> Mapping[str, Any]:
    if not isinstance(completed, subprocess.CompletedProcess):
        raise _stop("probe_result_invalid", probe_attempts=1)
    if completed.returncode != 0:
        raise _stop("probe_nonzero_exit", probe_attempts=1)
    stdout = completed.stdout
    if (
        not isinstance(stdout, bytes)
        or not stdout
        or len(stdout) > MAX_PROBE_OUTPUT_BYTES
    ):
        raise _stop("probe_output_invalid", probe_attempts=1)
    try:
        observation = json.loads(stdout.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise _stop("probe_output_invalid", probe_attempts=1) from None
    expected_keys = {
        "python_version",
        "pip_version",
        "setuptools_version",
        "build_wheel_callable",
        "vendored_wheel_available",
    }
    if not isinstance(observation, dict) or set(observation) != expected_keys:
        raise _stop("probe_output_invalid", probe_attempts=1)
    for key in ("python_version", "pip_version", "setuptools_version"):
        if not isinstance(observation[key], str) or not _VERSION_RE.fullmatch(
            observation[key]
        ):
            raise _stop("probe_output_invalid", probe_attempts=1)
    for key in ("build_wheel_callable", "vendored_wheel_available"):
        if not isinstance(observation[key], bool):
            raise _stop("probe_output_invalid", probe_attempts=1)
    return observation


def check_invocation_readiness(
    request: InvocationTransportRequest,
) -> InvocationReadinessResult:
    """Return bounded readiness evidence or stop at the first deviation."""

    _validate_request(request)
    launcher = _regular_non_link_file(request.launcher_path, "launcher_invalid")
    backend_wheel = _regular_non_link_file(
        request.backend_wheel_path, "backend_wheel_invalid"
    )
    if backend_wheel.suffix.lower() != ".whl":
        raise _stop("backend_wheel_invalid")
    if _file_sha256(backend_wheel) != request.backend_wheel_sha256:
        raise _stop("backend_wheel_digest_mismatch")
    if _short_root_count() != 0:
        raise _stop("short_roots_existing")

    try:
        completed = _run_fixed_probe(launcher)
    except subprocess.TimeoutExpired:
        raise _stop("probe_timeout", probe_attempts=1) from None
    except (OSError, RuntimeError, ValueError):
        raise _stop("probe_exception", probe_attempts=1) from None
    observation = _probe_observation(completed)

    if observation["python_version"] != request.expected_python_version:
        raise _stop("python_version_mismatch", probe_attempts=1)
    if observation["pip_version"] != request.expected_pip_version:
        raise _stop("pip_version_mismatch", probe_attempts=1)
    if observation["setuptools_version"] != request.expected_setuptools_version:
        raise _stop("setuptools_version_mismatch", probe_attempts=1)
    if not observation["build_wheel_callable"]:
        raise _stop("build_wheel_unavailable", probe_attempts=1)
    if not observation["vendored_wheel_available"]:
        raise _stop("vendored_wheel_unavailable", probe_attempts=1)
    if _short_root_count() != 0:
        raise _stop("short_roots_existing", probe_attempts=1)

    return InvocationReadinessResult(
        encoding_algorithm=request.encoding_algorithm,
        encoded_length=request.encoded_length,
        encoded_sha256=request.encoded_sha256,
        backend_wheel_sha256=request.backend_wheel_sha256,
        python_version=observation["python_version"],
        pip_version=observation["pip_version"],
        setuptools_version=observation["setuptools_version"],
        build_wheel_callable=observation["build_wheel_callable"],
        vendored_wheel_available=observation["vendored_wheel_available"],
    )
