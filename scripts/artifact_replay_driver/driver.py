"""Compose one manifest preflight, artifact action, evidence write, and cleanup.

This module is repository-internal development tooling.  It does not provide a
CLI, build an artifact itself, choose a backend, access a network, retry an
action, or grant Git, publication, release, deployment, or external-Agent
authority.  A caller injects one action and receives only privacy-bounded
normalized success or failure state.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
from typing import Any, Callable, Mapping, Sequence
import unicodedata

from scripts.distribution_input_manifest.manifest import (
    canonical_content_digest,
    canonical_path_digest,
    derive_distribution_inputs,
)
from scripts.short_build_root import (
    ShortBuildRoot,
    create_evidence_receipt,
    create_short_build_root,
    remove_short_build_root_after_evidence,
)


CONTRACT = "agentgov.internal-artifact-replay-driver"
SCHEMA_VERSION = "1.0"
MAX_EVIDENCE_BYTES = 1024 * 1024
_SHA256_IDENTITY_RE = re.compile(r"^sha256:[0-9a-f]{64}$")


@dataclass(frozen=True)
class ArtifactEvidence:
    """One caller-sanitized UTF-8 evidence document.

    The payload is deliberately excluded from representations.  The driver
    validates its bounded textual form and writes the exact UTF-8 bytes; it
    cannot independently prove the truth or completeness of caller-authored
    semantic claims.
    """

    text: str = field(repr=False)


@dataclass(frozen=True)
class ArtifactReplayResult:
    """Privacy-bounded success from one completed internal replay."""

    evidence_sha256: str
    manifest_path_count: int
    manifest_path_digest: str
    manifest_content_digest: str
    action_attempts: int
    evidence_written: bool
    evidence_revalidated: bool
    cleanup_removed: bool
    root_absent: bool

    def normalized_report(self) -> Mapping[str, Any]:
        return {
            "contract": CONTRACT,
            "schema_version": SCHEMA_VERSION,
            "status": "PASS",
            "manifest": {
                "status": "PASS",
                "path_count": self.manifest_path_count,
                "path_digest": self.manifest_path_digest,
                "content_digest": self.manifest_content_digest,
            },
            "action_attempts": self.action_attempts,
            "evidence_sha256": self.evidence_sha256,
            "evidence_written": self.evidence_written,
            "evidence_revalidated": self.evidence_revalidated,
            "cleanup_removed": self.cleanup_removed,
            "root_absent": self.root_absent,
            "reads_stdin": False,
            "depends_on_tty": False,
            "authority_boundary": _authority_boundary(),
        }


class ArtifactReplayDriverError(RuntimeError):
    """A normalized first deviation, with a private recovery root if allocated."""

    def __init__(
        self,
        reason_code: str,
        *,
        root: ShortBuildRoot | None,
        action_attempts: int,
        evidence_written: bool,
    ) -> None:
        super().__init__(reason_code)
        self.reason_code = reason_code
        self._root = root
        self.action_attempts = action_attempts
        self.evidence_written = evidence_written

    @property
    def recovery_root(self) -> ShortBuildRoot | None:
        """Return the exact private root for separately controlled recovery."""

        return self._root

    def normalized_report(self) -> Mapping[str, Any]:
        root_present = bool(
            self._root is not None
            and (self._root.path.exists() or self._root.path.is_symlink())
        )
        return {
            "contract": CONTRACT,
            "schema_version": SCHEMA_VERSION,
            "status": "STOPPED_AT_FIRST_DEVIATION",
            "reason_code": self.reason_code,
            "action_attempts": self.action_attempts,
            "evidence_written": self.evidence_written,
            "cleanup_removed": False,
            "root_preserved": root_present,
            "reads_stdin": False,
            "depends_on_tty": False,
            "authority_boundary": _authority_boundary(),
        }


ArtifactAction = Callable[[ShortBuildRoot], ArtifactEvidence]


def _authority_boundary() -> Mapping[str, bool]:
    return {
        "builds_artifact": False,
        "retries_action": False,
        "installs_dependencies": False,
        "uses_network": False,
        "starts_external_agent": False,
        "uses_model": False,
        "authorizes_git_operations": False,
        "authorizes_publication": False,
        "authorizes_release": False,
        "authorizes_deployment": False,
    }


def _stop(
    reason_code: str,
    *,
    root: ShortBuildRoot | None = None,
    action_attempts: int = 0,
    evidence_written: bool = False,
) -> ArtifactReplayDriverError:
    return ArtifactReplayDriverError(
        reason_code,
        root=root,
        action_attempts=action_attempts,
        evidence_written=evidence_written,
    )


def _resolved_repository(value: str | Path) -> Path:
    if not isinstance(value, (str, Path)):
        raise _stop("repository_invalid")
    candidate = Path(value)
    if candidate.is_symlink() or not candidate.is_dir():
        raise _stop("repository_invalid")
    try:
        resolved = candidate.resolve(strict=True)
    except (OSError, RuntimeError):
        raise _stop("repository_invalid") from None
    if resolved.is_symlink():
        raise _stop("repository_invalid")
    return resolved


def _relative_parts(value: str, *, reason_code: str) -> tuple[str, ...]:
    if (
        not isinstance(value, str)
        or not value
        or value != value.strip()
        or "\\" in value
        or any(unicodedata.category(character).startswith("C") for character in value)
    ):
        raise _stop(reason_code)
    posix = PurePosixPath(value)
    windows = PureWindowsPath(value)
    if (
        posix.is_absolute()
        or windows.is_absolute()
        or bool(windows.drive)
        or any(part in {"", ".", ".."} for part in posix.parts)
        or posix.as_posix() != value
    ):
        raise _stop(reason_code)
    return posix.parts


def _existing_manifest(repository: Path, relative_path: str) -> Path:
    parts = _relative_parts(relative_path, reason_code="manifest_reference_invalid")
    candidate = repository.joinpath(*parts)
    if candidate.is_symlink() or not candidate.is_file():
        raise _stop("manifest_reference_invalid")
    try:
        resolved = candidate.resolve(strict=True)
        resolved.relative_to(repository)
    except (OSError, RuntimeError, ValueError):
        raise _stop("manifest_reference_invalid") from None
    return resolved


def _new_evidence_target(repository: Path, relative_path: str) -> Path:
    parts = _relative_parts(relative_path, reason_code="evidence_reference_invalid")
    candidate = repository.joinpath(*parts)
    parent = repository
    for part in parts[:-1]:
        parent = parent / part
        if parent.is_symlink() or not parent.is_dir():
            raise _stop("evidence_reference_invalid")
    try:
        parent.resolve(strict=True).relative_to(repository)
    except (OSError, RuntimeError, ValueError):
        raise _stop("evidence_reference_invalid") from None
    if candidate.exists() or candidate.is_symlink():
        raise _stop("evidence_target_exists")
    return candidate


def _evidence_bytes(value: object, *, root: ShortBuildRoot) -> bytes:
    if not isinstance(value, ArtifactEvidence) or not isinstance(value.text, str):
        raise _stop(
            "evidence_payload_invalid", root=root, action_attempts=1
        )
    text = value.text
    if (
        not text.strip()
        or not text.endswith("\n")
        or "\r" in text
        or any(ord(character) < 32 and character not in {"\n", "\t"} for character in text)
        or "\x7f" in text
    ):
        raise _stop(
            "evidence_payload_invalid", root=root, action_attempts=1
        )
    try:
        payload = text.encode("utf-8", errors="strict")
    except UnicodeEncodeError:
        raise _stop(
            "evidence_payload_invalid", root=root, action_attempts=1
        ) from None
    if len(payload) > MAX_EVIDENCE_BYTES:
        raise _stop(
            "evidence_payload_invalid", root=root, action_attempts=1
        )
    return payload


def _write_exclusive_durable(path: Path, payload: bytes) -> None:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_BINARY"):
        flags |= os.O_BINARY
    descriptor = os.open(path, flags, 0o600)
    try:
        with os.fdopen(descriptor, "wb", closefd=False) as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
    finally:
        os.close(descriptor)


def _manifest_observation(
    repository: Path,
    relative_paths: Sequence[str],
    path_count: int,
    path_digest: str,
    content_digest: str,
) -> tuple[int, str, str]:
    if (
        not isinstance(relative_paths, Sequence)
        or isinstance(relative_paths, (str, bytes))
        or not relative_paths
        or not all(isinstance(path, str) for path in relative_paths)
        or not isinstance(path_count, int)
        or isinstance(path_count, bool)
        or path_count < 1
        or not isinstance(path_digest, str)
        or not _SHA256_IDENTITY_RE.fullmatch(path_digest)
        or not isinstance(content_digest, str)
        or not _SHA256_IDENTITY_RE.fullmatch(content_digest)
    ):
        raise _stop("manifest_preflight_failed")
    try:
        derived = derive_distribution_inputs(repository)
        observed_path_digest = canonical_path_digest(derived)
        observed_content_digest = canonical_content_digest(repository, derived)
    except Exception:
        raise _stop("manifest_preflight_failed") from None
    if (
        list(relative_paths) != derived
        or len(derived) != path_count
        or observed_path_digest != path_digest
        or observed_content_digest != content_digest
    ):
        raise _stop("manifest_preflight_failed")
    return path_count, path_digest, content_digest


def run_artifact_replay(
    *,
    repository: str | Path,
    manifest_relative_path: str,
    manifest_relative_paths: Sequence[str],
    manifest_path_count: int,
    manifest_path_digest: str,
    manifest_content_digest: str,
    projected_relative_paths: Sequence[str],
    evidence_relative_path: str,
    action: ArtifactAction,
) -> ArtifactReplayResult:
    """Run one injected action and clean only after durable evidence validates.

    Every failure is normalized at its first observed boundary.  The function
    never retries the injected action and never performs failure cleanup that
    lacks a validated evidence receipt.
    """

    root_repository = _resolved_repository(repository)
    _existing_manifest(root_repository, manifest_relative_path)
    evidence_path = _new_evidence_target(root_repository, evidence_relative_path)
    if not callable(action):
        raise _stop("artifact_action_invalid")
    path_count, path_digest, content_digest = _manifest_observation(
        root_repository,
        manifest_relative_paths,
        manifest_path_count,
        manifest_path_digest,
        manifest_content_digest,
    )
    try:
        root = create_short_build_root(projected_relative_paths)
    except Exception:
        raise _stop("root_allocation_failed") from None

    try:
        evidence = action(root)
    except Exception:
        raise _stop(
            "artifact_action_failed", root=root, action_attempts=1
        ) from None
    payload = _evidence_bytes(evidence, root=root)
    try:
        _write_exclusive_durable(evidence_path, payload)
    except (OSError, ValueError):
        raise _stop(
            "evidence_write_failed",
            root=root,
            action_attempts=1,
            evidence_written=evidence_path.is_file() and not evidence_path.is_symlink(),
        ) from None
    identity = "sha256:" + hashlib.sha256(payload).hexdigest()
    try:
        receipt = create_evidence_receipt(
            repository=root_repository,
            relative_path=evidence_relative_path,
            expected_sha256=identity,
        )
    except Exception:
        raise _stop(
            "evidence_receipt_failed",
            root=root,
            action_attempts=1,
            evidence_written=True,
        ) from None
    try:
        cleanup = remove_short_build_root_after_evidence(root, receipt)
    except Exception:
        raise _stop(
            "gated_cleanup_failed",
            root=root,
            action_attempts=1,
            evidence_written=True,
        ) from None
    root_absent = not root.path.exists() and not root.path.is_symlink()
    if (
        not cleanup.evidence_revalidated
        or not cleanup.cleanup_removed
        or cleanup.evidence_sha256 != identity
        or not root_absent
    ):
        raise _stop(
            "gated_cleanup_result_invalid",
            root=root,
            action_attempts=1,
            evidence_written=True,
        )
    return ArtifactReplayResult(
        evidence_sha256=identity,
        manifest_path_count=path_count,
        manifest_path_digest=path_digest,
        manifest_content_digest=content_digest,
        action_attempts=1,
        evidence_written=True,
        evidence_revalidated=True,
        cleanup_removed=True,
        root_absent=True,
    )
