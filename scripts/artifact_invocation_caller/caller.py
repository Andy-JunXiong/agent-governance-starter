"""Require fresh transport readiness before one artifact-driver invocation.

This dependency-free repository-internal wrapper is the first concrete caller
of the readiness checker.  It validates one fresh in-memory readiness receipt
and only then invokes the unchanged artifact replay driver once.  It does not
persist the receipt, change either upstream contract, retry, provide a CLI,
or grant build, Git, publication, release, deployment, or external authority.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
import re
from typing import Any, Mapping, Sequence

from scripts.artifact_invocation_readiness import (
    AUTHORITY_KEYS as READINESS_AUTHORITY_KEYS,
    ENCODING_ALGORITHM,
    InvocationReadinessError,
    InvocationReadinessResult,
    InvocationTransportRequest,
    check_invocation_readiness,
)
from scripts.artifact_invocation_readiness.readiness import (
    CONTRACT as READINESS_CONTRACT,
    MAX_ENCODED_LENGTH,
    SCHEMA_VERSION as READINESS_SCHEMA_VERSION,
)
from scripts.artifact_replay_driver import (
    ArtifactReplayDriverError,
    ArtifactReplayResult,
    run_artifact_replay,
)
from scripts.artifact_replay_driver.driver import (
    ArtifactAction,
    CONTRACT as DRIVER_CONTRACT,
    SCHEMA_VERSION as DRIVER_SCHEMA_VERSION,
)


CONTRACT = "agentgov.minimal-artifact-invocation-caller-gate"
SCHEMA_VERSION = "1.0"

_SHA256_IDENTITY_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_REASON_CODE_RE = re.compile(r"^[a-z][a-z0-9_]{0,79}$")
_VERSION_RE = re.compile(r"^[0-9]+(?:\.[0-9]+)+(?:[A-Za-z0-9._+-]{0,24})$")

_CALLER_AUTHORITY_KEYS = (
    "persists_readiness_receipt",
    "retries_readiness",
    "retries_driver",
    "builds_artifact",
    "installs_dependencies",
    "uses_network",
    "starts_external_agent",
    "uses_model",
    "authorizes_git_operations",
    "authorizes_publication",
    "authorizes_release",
    "authorizes_deployment",
)

_DRIVER_AUTHORITY_KEYS = (
    "builds_artifact",
    "retries_action",
    "installs_dependencies",
    "uses_network",
    "starts_external_agent",
    "uses_model",
    "authorizes_git_operations",
    "authorizes_publication",
    "authorizes_release",
    "authorizes_deployment",
)


def _denied_authority(keys: Sequence[str]) -> Mapping[str, bool]:
    return {key: False for key in keys}


def _caller_authority() -> Mapping[str, bool]:
    return _denied_authority(_CALLER_AUTHORITY_KEYS)


@dataclass(frozen=True)
class ArtifactInvocationCallerRequest:
    """One private readiness request plus the unchanged driver arguments."""

    transport: InvocationTransportRequest = field(repr=False)
    repository: str | Path = field(repr=False)
    manifest_relative_path: str = field(repr=False)
    manifest_relative_paths: Sequence[str] = field(repr=False)
    manifest_path_count: int = field(repr=False)
    manifest_path_digest: str = field(repr=False)
    manifest_content_digest: str = field(repr=False)
    projected_relative_paths: Sequence[str] = field(repr=False)
    evidence_relative_path: str = field(repr=False)
    action: ArtifactAction = field(repr=False)


@dataclass(frozen=True)
class ArtifactInvocationCallerResult:
    """Stable privacy-bounded composition of two validated upstream reports."""

    _readiness_report_json: str = field(repr=False)
    _driver_report_json: str = field(repr=False)

    def normalized_report(self) -> Mapping[str, Any]:
        return {
            "contract": CONTRACT,
            "schema_version": SCHEMA_VERSION,
            "status": "PASS",
            "readiness": json.loads(self._readiness_report_json),
            "driver": json.loads(self._driver_report_json),
            "readiness_attempts": 1,
            "driver_attempts": 1,
            "reads_stdin": False,
            "depends_on_tty": False,
            "authority_boundary": _caller_authority(),
        }


class ArtifactInvocationCallerError(RuntimeError):
    """One bounded caller-phase deviation with optional private driver recovery."""

    def __init__(
        self,
        reason_code: str,
        *,
        phase: str,
        readiness_attempts: int,
        driver_attempts: int,
        driver_error: ArtifactReplayDriverError | None = None,
    ) -> None:
        super().__init__(reason_code)
        self.reason_code = reason_code
        self.phase = phase
        self.readiness_attempts = readiness_attempts
        self.driver_attempts = driver_attempts
        self._driver_error = driver_error

    @property
    def recovery_driver_error(self) -> ArtifactReplayDriverError | None:
        """Preserve the unchanged driver's private recovery handle when present."""

        return self._driver_error

    def normalized_report(self) -> Mapping[str, Any]:
        return {
            "contract": CONTRACT,
            "schema_version": SCHEMA_VERSION,
            "status": "STOPPED_AT_FIRST_DEVIATION",
            "phase": self.phase,
            "reason_code": self.reason_code,
            "readiness_attempts": self.readiness_attempts,
            "driver_attempts": self.driver_attempts,
            "reads_stdin": False,
            "depends_on_tty": False,
            "authority_boundary": _caller_authority(),
        }


def _stop(
    reason_code: str,
    *,
    phase: str,
    readiness_attempts: int = 1,
    driver_attempts: int,
    driver_error: ArtifactReplayDriverError | None = None,
) -> ArtifactInvocationCallerError:
    return ArtifactInvocationCallerError(
        reason_code,
        phase=phase,
        readiness_attempts=readiness_attempts,
        driver_attempts=driver_attempts,
        driver_error=driver_error,
    )


def _safe_upstream_reason(prefix: str, value: object) -> str:
    if isinstance(value, str) and _REASON_CODE_RE.fullmatch(value):
        return prefix + value
    return prefix + "failed"


def _exact_false_mapping(value: object, keys: Sequence[str]) -> bool:
    try:
        return (
            isinstance(value, Mapping)
            and set(value) == set(keys)
            and all(value[key] is False for key in keys)
        )
    except (KeyError, TypeError, ValueError):
        return False


def _sha256_identity(value: object) -> bool:
    return isinstance(value, str) and _SHA256_IDENTITY_RE.fullmatch(value) is not None


def _normalized_version(value: object) -> bool:
    return isinstance(value, str) and _VERSION_RE.fullmatch(value) is not None


def _positive_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _canonical_json(value: Mapping[str, Any]) -> str:
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    except (TypeError, ValueError):
        raise ValueError("report is not canonical JSON data") from None


def _valid_readiness_report(
    result: InvocationReadinessResult,
) -> Mapping[str, Any] | None:
    try:
        report = result.normalized_report()
    except Exception:
        return None
    expected_top = {
        "contract",
        "schema_version",
        "status",
        "transport",
        "backend",
        "probe_attempts",
        "short_root_count",
        "reads_stdin",
        "depends_on_tty",
        "authority_request",
    }
    if not isinstance(report, Mapping) or set(report) != expected_top:
        return None
    transport = report.get("transport")
    backend = report.get("backend")
    if (
        report.get("contract") != READINESS_CONTRACT
        or report.get("schema_version") != READINESS_SCHEMA_VERSION
        or report.get("status") != "PASS"
        or report.get("probe_attempts") != 1
        or isinstance(report.get("probe_attempts"), bool)
        or report.get("short_root_count") != 0
        or report.get("reads_stdin") is not False
        or report.get("depends_on_tty") is not False
        or not _exact_false_mapping(report.get("authority_request"), READINESS_AUTHORITY_KEYS)
        or not isinstance(transport, Mapping)
        or set(transport) != {"encoding_algorithm", "encoded_length", "encoded_sha256"}
        or transport.get("encoding_algorithm") != ENCODING_ALGORITHM
        or result.encoding_algorithm != ENCODING_ALGORITHM
        or transport.get("encoded_length") != result.encoded_length
        or not _positive_int(result.encoded_length)
        or result.encoded_length > MAX_ENCODED_LENGTH
        or result.encoded_length % 4 != 0
        or transport.get("encoded_sha256") != result.encoded_sha256
        or not _sha256_identity(result.encoded_sha256)
        or not isinstance(backend, Mapping)
        or set(backend)
        != {
            "wheel_sha256",
            "python_version",
            "pip_version",
            "setuptools_version",
            "build_wheel_callable",
            "vendored_wheel_available",
        }
        or backend.get("wheel_sha256") != result.backend_wheel_sha256
        or not _sha256_identity(result.backend_wheel_sha256)
        or backend.get("python_version") != result.python_version
        or not _normalized_version(result.python_version)
        or backend.get("pip_version") != result.pip_version
        or not _normalized_version(result.pip_version)
        or backend.get("setuptools_version") != result.setuptools_version
        or not _normalized_version(result.setuptools_version)
        or backend.get("build_wheel_callable") is not True
        or result.build_wheel_callable is not True
        or backend.get("vendored_wheel_available") is not True
        or result.vendored_wheel_available is not True
    ):
        return None
    return dict(report)


def _valid_driver_report(result: ArtifactReplayResult) -> Mapping[str, Any] | None:
    try:
        report = result.normalized_report()
    except Exception:
        return None
    expected_top = {
        "contract",
        "schema_version",
        "status",
        "manifest",
        "action_attempts",
        "evidence_sha256",
        "evidence_written",
        "evidence_revalidated",
        "cleanup_removed",
        "root_absent",
        "reads_stdin",
        "depends_on_tty",
        "authority_boundary",
    }
    manifest = report.get("manifest") if isinstance(report, Mapping) else None
    if (
        not isinstance(report, Mapping)
        or set(report) != expected_top
        or report.get("contract") != DRIVER_CONTRACT
        or report.get("schema_version") != DRIVER_SCHEMA_VERSION
        or report.get("status") != "PASS"
        or report.get("action_attempts") != 1
        or isinstance(report.get("action_attempts"), bool)
        or report.get("evidence_sha256") != result.evidence_sha256
        or not _sha256_identity(result.evidence_sha256)
        or report.get("evidence_written") is not True
        or result.evidence_written is not True
        or report.get("evidence_revalidated") is not True
        or result.evidence_revalidated is not True
        or report.get("cleanup_removed") is not True
        or result.cleanup_removed is not True
        or report.get("root_absent") is not True
        or result.root_absent is not True
        or report.get("reads_stdin") is not False
        or report.get("depends_on_tty") is not False
        or not _exact_false_mapping(report.get("authority_boundary"), _DRIVER_AUTHORITY_KEYS)
        or not isinstance(manifest, Mapping)
        or set(manifest) != {"status", "path_count", "path_digest", "content_digest"}
        or manifest.get("status") != "PASS"
        or manifest.get("path_count") != result.manifest_path_count
        or not _positive_int(result.manifest_path_count)
        or manifest.get("path_digest") != result.manifest_path_digest
        or not _sha256_identity(result.manifest_path_digest)
        or manifest.get("content_digest") != result.manifest_content_digest
        or not _sha256_identity(result.manifest_content_digest)
    ):
        return None
    return dict(report)


def run_ready_artifact_replay(
    request: ArtifactInvocationCallerRequest,
) -> ArtifactInvocationCallerResult:
    """Run readiness once, then the unchanged driver once only after PASS."""

    if not isinstance(request, ArtifactInvocationCallerRequest):
        raise _stop(
            "caller_request_invalid",
            phase="readiness",
            readiness_attempts=0,
            driver_attempts=0,
        )
    try:
        readiness_result = check_invocation_readiness(request.transport)
    except InvocationReadinessError as error:
        raise _stop(
            _safe_upstream_reason("readiness_", error.reason_code),
            phase="readiness",
            driver_attempts=0,
        ) from None
    except Exception:
        raise _stop("readiness_exception", phase="readiness", driver_attempts=0) from None
    if not isinstance(readiness_result, InvocationReadinessResult):
        raise _stop("readiness_result_invalid", phase="readiness", driver_attempts=0)
    readiness_report = _valid_readiness_report(readiness_result)
    if readiness_report is None:
        raise _stop("readiness_result_invalid", phase="readiness", driver_attempts=0)

    try:
        driver_result = run_artifact_replay(
            repository=request.repository,
            manifest_relative_path=request.manifest_relative_path,
            manifest_relative_paths=request.manifest_relative_paths,
            manifest_path_count=request.manifest_path_count,
            manifest_path_digest=request.manifest_path_digest,
            manifest_content_digest=request.manifest_content_digest,
            projected_relative_paths=request.projected_relative_paths,
            evidence_relative_path=request.evidence_relative_path,
            action=request.action,
        )
    except ArtifactReplayDriverError as error:
        raise _stop(
            _safe_upstream_reason("driver_", error.reason_code),
            phase="driver",
            driver_attempts=1,
            driver_error=error,
        ) from None
    except Exception:
        raise _stop("driver_exception", phase="driver", driver_attempts=1) from None
    if not isinstance(driver_result, ArtifactReplayResult):
        raise _stop("driver_result_invalid", phase="driver", driver_attempts=1)
    driver_report = _valid_driver_report(driver_result)
    if driver_report is None:
        raise _stop("driver_result_invalid", phase="driver", driver_attempts=1)

    try:
        readiness_json = _canonical_json(readiness_report)
        driver_json = _canonical_json(driver_report)
    except ValueError:
        raise _stop("combined_result_invalid", phase="driver", driver_attempts=1) from None
    return ArtifactInvocationCallerResult(
        _readiness_report_json=readiness_json,
        _driver_report_json=driver_json,
    )
