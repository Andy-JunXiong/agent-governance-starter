"""Allocate and remove one privacy-bounded short artifact-build root.

This is deliberately repository-internal development tooling.  It does not
build a distribution, select an artifact, access a network, or authorize a
consumer journey.  Its only write is one verified direct child of the resolved
operating-system temporary directory; cleanup accepts only that exact shape.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
import secrets
import shutil
import tempfile
from typing import Any, Mapping, Sequence
import unicodedata


CONTRACT = "agentgov.short-build-root"
SCHEMA_VERSION = "1.0"
ROOT_PREFIX = "agv-"
TOKEN_BYTES = 4
DEFAULT_MAX_ROOT_PATH = 72
DEFAULT_MAX_PROJECTED_PATH = 240
MAX_WINDOWS_PATH_WITHOUT_EXTENDED_PREFIX = 259
_ROOT_NAME_RE = re.compile(r"^agv-[0-9a-f]{8}$")
_SHA256_IDENTITY_RE = re.compile(r"^sha256:[0-9a-f]{64}$")


class BuildRootError(RuntimeError):
    """The requested short build-root boundary is unsafe or unavailable."""


@dataclass(frozen=True)
class ShortBuildRoot:
    """One verified task-owned temporary root.

    Host paths are intentionally excluded from ``repr`` and the normalized
    report.  Callers performing the admitted local work can use ``path`` and
    must pass this exact object back to :func:`remove_short_build_root`.
    """

    path: Path = field(repr=False)
    _temporary_root: Path = field(repr=False)
    root_name: str
    projected_path_limit: int
    longest_projected_length: int

    def normalized_report(self) -> Mapping[str, Any]:
        return {
            "contract": CONTRACT,
            "schema_version": SCHEMA_VERSION,
            "root_name_pattern": ROOT_PREFIX + "<8-hex>",
            "root_is_direct_temporary_child": True,
            "projected_path_limit": self.projected_path_limit,
            "longest_projected_length": self.longest_projected_length,
            "authority_boundary": {
                "builds_artifact": False,
                "selects_artifact": False,
                "uses_network": False,
                "authorizes_git_operations": False,
                "authorizes_publication": False,
                "authorizes_release": False,
                "authorizes_deployment": False,
                "authorizes_external_write": False,
            },
        }


@dataclass(frozen=True)
class EvidenceReceipt:
    """One verified repository-relative durable-evidence identity.

    Resolved host paths are deliberately private and excluded from ``repr``.
    The receipt is revalidated immediately before gated cleanup, so creating a
    receipt alone never authorizes a later removal after the evidence changes.
    """

    _repository: Path = field(repr=False)
    _evidence_path: Path = field(repr=False)
    relative_path: str
    sha256_identity: str

    def normalized_report(self) -> Mapping[str, Any]:
        return {
            "contract": "agentgov.short-build-root-evidence-receipt",
            "schema_version": SCHEMA_VERSION,
            "evidence_reference_kind": "repository_relative_regular_file",
            "evidence_sha256": self.sha256_identity,
            "reads_stdin": False,
            "depends_on_tty": False,
            "authorizes_cleanup": False,
        }


@dataclass(frozen=True)
class EvidenceGatedCleanupResult:
    """Privacy-bounded confirmation of one evidence-gated cleanup."""

    evidence_sha256: str
    evidence_revalidated: bool
    cleanup_removed: bool

    def normalized_report(self) -> Mapping[str, Any]:
        return {
            "contract": "agentgov.short-build-root-evidence-gated-cleanup",
            "schema_version": SCHEMA_VERSION,
            "evidence_sha256": self.evidence_sha256,
            "evidence_revalidated": self.evidence_revalidated,
            "cleanup_removed": self.cleanup_removed,
            "reads_stdin": False,
            "depends_on_tty": False,
            "authority_boundary": {
                "builds_artifact": False,
                "retries_build": False,
                "uses_network": False,
                "authorizes_git_operations": False,
                "authorizes_publication": False,
                "authorizes_release": False,
                "authorizes_deployment": False,
                "authorizes_external_write": False,
            },
        }


def _resolved_temporary_root() -> Path:
    candidate = Path(tempfile.gettempdir())
    if candidate.is_symlink():
        raise BuildRootError("temporary root must not be a symbolic link")
    if not candidate.exists() or not candidate.is_dir():
        raise BuildRootError("temporary root must be an existing directory")
    try:
        resolved = candidate.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise BuildRootError("temporary root could not be resolved") from exc
    if resolved.is_symlink():
        raise BuildRootError("resolved temporary root must not be a symbolic link")
    return resolved


def _resolved_repository(repository: str | Path) -> Path:
    if not isinstance(repository, (str, Path)):
        raise BuildRootError("evidence repository must be a filesystem path")
    candidate = Path(repository)
    if candidate.is_symlink():
        raise BuildRootError("evidence repository must not be a symbolic link")
    if not candidate.exists() or not candidate.is_dir():
        raise BuildRootError("evidence repository must be an existing directory")
    try:
        resolved = candidate.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise BuildRootError("evidence repository could not be resolved") from exc
    if resolved.is_symlink():
        raise BuildRootError("resolved evidence repository must not be a symbolic link")
    return resolved


def _evidence_parts(relative_path: str) -> tuple[str, ...]:
    if (
        not isinstance(relative_path, str)
        or not relative_path
        or relative_path != relative_path.strip()
        or any(
            unicodedata.category(character).startswith("C")
            for character in relative_path
        )
    ):
        raise BuildRootError("evidence path must be normalized relative text")
    if "\\" in relative_path:
        raise BuildRootError("evidence path must use portable forward slashes")
    posix = PurePosixPath(relative_path)
    windows = PureWindowsPath(relative_path)
    if posix.is_absolute() or windows.is_absolute() or windows.drive:
        raise BuildRootError("evidence path must be repository relative")
    if any(part in {"", ".", ".."} for part in posix.parts):
        raise BuildRootError("evidence path must not contain traversal segments")
    if posix.as_posix() != relative_path:
        raise BuildRootError("evidence path must be normalized")
    return posix.parts


def _sha256_identity(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as stream:
            while chunk := stream.read(1024 * 1024):
                digest.update(chunk)
    except OSError as exc:
        raise BuildRootError("durable evidence could not be read") from exc
    return "sha256:" + digest.hexdigest()


def _verify_evidence(
    *,
    repository: str | Path,
    relative_path: str,
    expected_sha256: str,
) -> tuple[Path, str]:
    if (
        not isinstance(expected_sha256, str)
        or not _SHA256_IDENTITY_RE.fullmatch(expected_sha256)
    ):
        raise BuildRootError("evidence digest must be canonical sha256 identity")
    root = _resolved_repository(repository)
    parts = _evidence_parts(relative_path)
    candidate = root
    for part in parts:
        candidate = candidate / part
        if candidate.is_symlink():
            raise BuildRootError("evidence path must not use symbolic links")
        if not candidate.exists():
            raise BuildRootError("durable evidence file does not exist")
    if not candidate.is_file():
        raise BuildRootError("durable evidence must be a regular file")
    try:
        resolved = candidate.resolve(strict=True)
        resolved.relative_to(root)
    except (OSError, RuntimeError, ValueError) as exc:
        raise BuildRootError("evidence path escaped its repository boundary") from exc
    observed = _sha256_identity(resolved)
    if observed != expected_sha256:
        raise BuildRootError("durable evidence digest does not match")
    return resolved, observed


def create_evidence_receipt(
    *,
    repository: str | Path,
    relative_path: str,
    expected_sha256: str,
) -> EvidenceReceipt:
    """Verify durable evidence without reading stdin or authorizing cleanup."""

    evidence_path, observed = _verify_evidence(
        repository=repository,
        relative_path=relative_path,
        expected_sha256=expected_sha256,
    )
    return EvidenceReceipt(
        _repository=_resolved_repository(repository),
        _evidence_path=evidence_path,
        relative_path=relative_path,
        sha256_identity=observed,
    )


def _projected_parts(value: str) -> tuple[str, ...]:
    if (
        not isinstance(value, str)
        or not value
        or value != value.strip()
        or any(unicodedata.category(character).startswith("C") for character in value)
    ):
        raise BuildRootError("projected paths must be normalized relative text")
    if "\\" in value:
        raise BuildRootError("projected paths must use portable forward slashes")
    posix = PurePosixPath(value)
    windows = PureWindowsPath(value)
    if posix.is_absolute() or windows.is_absolute() or windows.drive:
        raise BuildRootError("projected paths must be relative")
    if any(part in {"", ".", ".."} for part in posix.parts):
        raise BuildRootError("projected paths must not contain traversal segments")
    normalized = posix.as_posix()
    if normalized != value:
        raise BuildRootError("projected paths must be normalized")
    return posix.parts


def _validate_limits(*, maximum_root_path: int, maximum_projected_path: int) -> None:
    if not isinstance(maximum_root_path, int) or maximum_root_path < 1:
        raise BuildRootError("maximum root path must be a positive integer")
    if (
        not isinstance(maximum_projected_path, int)
        or maximum_projected_path < 1
        or maximum_projected_path > MAX_WINDOWS_PATH_WITHOUT_EXTENDED_PREFIX
    ):
        raise BuildRootError(
            "maximum projected path must fit the non-extended Windows boundary"
        )


def create_short_build_root(
    projected_relative_paths: Sequence[str],
    *,
    maximum_root_path: int = DEFAULT_MAX_ROOT_PATH,
    maximum_projected_path: int = DEFAULT_MAX_PROJECTED_PATH,
) -> ShortBuildRoot:
    """Create one short direct child after validating every projected path.

    The operating-system temporary directory and a cryptographic random
    eight-hex token are always used. Tests replace those providers with mocks;
    callers cannot select an alternate write boundary through this function.
    """

    _validate_limits(
        maximum_root_path=maximum_root_path,
        maximum_projected_path=maximum_projected_path,
    )
    if (
        isinstance(projected_relative_paths, (str, bytes))
        or not projected_relative_paths
    ):
        raise BuildRootError("at least one projected relative path is required")
    projected = tuple(_projected_parts(item) for item in projected_relative_paths)
    base = _resolved_temporary_root()

    for _ in range(16):
        token = secrets.token_hex(TOKEN_BYTES)
        if not isinstance(token, str) or not re.fullmatch(r"[0-9a-f]{8}", token):
            raise BuildRootError("token factory must return exactly eight lowercase hex")
        name = ROOT_PREFIX + token
        candidate = base / name
        if len(str(candidate)) > maximum_root_path:
            raise BuildRootError("operating-system temporary base is too long")
        lengths = tuple(len(str(candidate.joinpath(*parts))) for parts in projected)
        longest = max(lengths)
        if longest > maximum_projected_path:
            raise BuildRootError("projected build path exceeds the declared budget")
        try:
            candidate.mkdir(mode=0o700)
        except FileExistsError:
            continue
        except OSError as exc:
            raise BuildRootError("short build root could not be created") from exc
        if candidate.is_symlink() or candidate.parent.resolve(strict=True) != base:
            try:
                candidate.rmdir()
            except OSError:
                pass
            raise BuildRootError("created build root failed its ownership boundary")
        return ShortBuildRoot(
            path=candidate,
            _temporary_root=base,
            root_name=name,
            projected_path_limit=maximum_projected_path,
            longest_projected_length=longest,
        )
    raise BuildRootError("a unique short build-root name was unavailable")


def remove_short_build_root(root: ShortBuildRoot) -> None:
    """Remove only the exact verified direct-child root represented by ``root``."""

    if not isinstance(root, ShortBuildRoot):
        raise BuildRootError("cleanup requires a verified short build-root object")
    base = _resolved_temporary_root()
    if root._temporary_root != base:
        raise BuildRootError("cleanup temporary boundary no longer matches allocation")
    candidate = root.path
    if not _ROOT_NAME_RE.fullmatch(root.root_name) or candidate.name != root.root_name:
        raise BuildRootError("cleanup target name is not task-owned")
    if candidate.parent.resolve(strict=True) != base:
        raise BuildRootError("cleanup target must be a direct temporary child")
    if candidate.is_symlink():
        raise BuildRootError("cleanup target must not be a symbolic link")
    if not candidate.exists() or not candidate.is_dir():
        raise BuildRootError("cleanup target must be an existing directory")
    try:
        resolved = candidate.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise BuildRootError("cleanup target could not be resolved") from exc
    if resolved != candidate or resolved.parent != base:
        raise BuildRootError("cleanup target escaped its temporary boundary")
    try:
        shutil.rmtree(candidate)
    except OSError as exc:
        raise BuildRootError("cleanup target could not be removed") from exc


def remove_short_build_root_after_evidence(
    root: ShortBuildRoot,
    receipt: EvidenceReceipt,
) -> EvidenceGatedCleanupResult:
    """Remove one verified root only after revalidating explicit evidence.

    This function deliberately has no prompt, stdin, or TTY branch. Interactive
    and noninteractive orchestrators must both supply the same explicit receipt.
    """

    if not isinstance(receipt, EvidenceReceipt):
        raise BuildRootError("evidence-gated cleanup requires a verified receipt")
    evidence_path, observed = _verify_evidence(
        repository=receipt._repository,
        relative_path=receipt.relative_path,
        expected_sha256=receipt.sha256_identity,
    )
    if evidence_path != receipt._evidence_path or observed != receipt.sha256_identity:
        raise BuildRootError("durable evidence no longer matches its receipt")
    remove_short_build_root(root)
    if root.path.exists() or root.path.is_symlink():
        raise BuildRootError("evidence-gated cleanup did not remove its exact root")
    return EvidenceGatedCleanupResult(
        evidence_sha256=observed,
        evidence_revalidated=True,
        cleanup_removed=True,
    )
