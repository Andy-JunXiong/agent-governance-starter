"""Canonical, read-only Git snapshots for development evidence."""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import subprocess
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any, Iterable

from agentgov.path_policy import is_segment_prefix, scope_path_error


GIT_SNAPSHOT_FORMAT = "agentgov.git-change-set.v1"
_LAYER_NAMES = ("committed", "staged", "unstaged", "untracked")
_STATUS_NAMES = {
    "A": "added",
    "C": "copied",
    "D": "deleted",
    "M": "modified",
    "R": "renamed",
    "T": "type_changed",
    "U": "unmerged",
    "X": "unknown",
}
_SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_GIT_SHA_RE = re.compile(r"^[0-9a-f]{40,64}$")
_EXCLUSIONS = (
    "ignored untracked paths are omitted by git ls-files --exclude-standard",
    "untracked paths beneath .agentgov are local tool state and are excluded",
    "tracked .agentgov paths and tracked .gitignore changes remain included",
)


class GitSnapshotError(RuntimeError):
    """Git or the filesystem could not produce a trustworthy snapshot."""


@dataclass(frozen=True)
class SnapshotChange:
    layer: str
    status: str
    path: str
    old_path: str | None
    content_digest: str | None = None
    content_kind: str | None = None


@dataclass(frozen=True)
class SnapshotLayer:
    name: str
    identity_digest: str
    changes: tuple[SnapshotChange, ...]


@dataclass(frozen=True)
class CanonicalGitSnapshot:
    format_version: str
    comparison_base_sha: str
    snapshot_head_sha: str
    change_set_digest: str
    layers: tuple[SnapshotLayer, ...]
    exclusions: tuple[str, ...]


def snapshot_to_payload(snapshot: CanonicalGitSnapshot) -> dict[str, Any]:
    return asdict(snapshot)


def snapshot_from_payload(payload: Any) -> CanonicalGitSnapshot:
    """Load a persisted snapshot using strict structural checks."""

    if not isinstance(payload, dict) or set(payload) != {
        "format_version",
        "comparison_base_sha",
        "snapshot_head_sha",
        "change_set_digest",
        "layers",
        "exclusions",
    }:
        raise GitSnapshotError("persisted Git snapshot has unexpected fields")
    if payload.get("format_version") != GIT_SNAPSHOT_FORMAT:
        raise GitSnapshotError("persisted Git snapshot format is unsupported")
    layers_value = payload.get("layers")
    if not isinstance(layers_value, list):
        raise GitSnapshotError("persisted Git snapshot layers must be an array")
    layers: list[SnapshotLayer] = []
    for layer_value in layers_value:
        if not isinstance(layer_value, dict) or set(layer_value) != {"name", "identity_digest", "changes"}:
            raise GitSnapshotError("persisted Git layer has unexpected fields")
        changes_value = layer_value.get("changes")
        if not isinstance(changes_value, list):
            raise GitSnapshotError("persisted Git layer changes must be an array")
        changes: list[SnapshotChange] = []
        for change_value in changes_value:
            if not isinstance(change_value, dict) or set(change_value) != {
                "layer",
                "status",
                "path",
                "old_path",
                "content_digest",
                "content_kind",
            }:
                raise GitSnapshotError("persisted Git change has unexpected fields")
            path = change_value.get("path")
            old_path = change_value.get("old_path")
            if not isinstance(path, str) or scope_path_error(path):
                raise GitSnapshotError("persisted Git change path is unsafe")
            if old_path is not None and (not isinstance(old_path, str) or scope_path_error(old_path)):
                raise GitSnapshotError("persisted Git old path is unsafe")
            if change_value.get("layer") != layer_value.get("name"):
                raise GitSnapshotError("persisted Git change layer does not match its container")
            if change_value.get("status") not in set(_STATUS_NAMES.values()) | {"untracked"}:
                raise GitSnapshotError("persisted Git change status is invalid")
            content_digest = change_value.get("content_digest")
            content_kind = change_value.get("content_kind")
            if content_digest is not None and (not isinstance(content_digest, str) or not _SHA256_RE.fullmatch(content_digest)):
                raise GitSnapshotError("persisted untracked content digest is invalid")
            if content_kind not in {None, "file", "symlink"}:
                raise GitSnapshotError("persisted untracked content kind is invalid")
            if layer_value.get("name") == "untracked":
                if change_value.get("status") != "untracked" or content_digest is None or content_kind is None:
                    raise GitSnapshotError("persisted untracked identity is incomplete")
            elif content_digest is not None or content_kind is not None:
                raise GitSnapshotError("tracked Git changes must not contain source identities")
            changes.append(SnapshotChange(**change_value))
        identity_digest = layer_value.get("identity_digest")
        if not isinstance(identity_digest, str) or not _SHA256_RE.fullmatch(identity_digest):
            raise GitSnapshotError("persisted Git layer identity is invalid")
        layers.append(
            SnapshotLayer(
                name=layer_value["name"],
                identity_digest=layer_value["identity_digest"],
                changes=tuple(changes),
            )
        )
        if tuple(changes) != tuple(sorted(changes, key=lambda item: (item.path, item.old_path or "", item.status))):
            raise GitSnapshotError("persisted Git changes are not canonically ordered")
        if layer_value.get("name") == "untracked":
            expected_untracked = _sha256(_canonical_json([asdict(item) for item in changes]))
            if identity_digest != expected_untracked:
                raise GitSnapshotError("persisted untracked layer identity is invalid")
    if tuple(layer.name for layer in layers) != _LAYER_NAMES:
        raise GitSnapshotError("persisted Git layers are not canonical")
    exclusions = payload.get("exclusions")
    if not isinstance(exclusions, list) or tuple(exclusions) != _EXCLUSIONS:
        raise GitSnapshotError("persisted Git snapshot exclusions are not canonical")
    for key in ("comparison_base_sha", "snapshot_head_sha"):
        if not isinstance(payload.get(key), str) or not _GIT_SHA_RE.fullmatch(payload[key]):
            raise GitSnapshotError(f"persisted Git snapshot {key} is invalid")
    if not isinstance(payload.get("change_set_digest"), str) or not _SHA256_RE.fullmatch(payload["change_set_digest"]):
        raise GitSnapshotError("persisted Git snapshot change_set_digest is invalid")
    snapshot = CanonicalGitSnapshot(
        format_version=payload["format_version"],
        comparison_base_sha=payload["comparison_base_sha"],
        snapshot_head_sha=payload["snapshot_head_sha"],
        change_set_digest=payload["change_set_digest"],
        layers=tuple(layers),
        exclusions=tuple(exclusions),
    )
    if snapshot.change_set_digest != _snapshot_digest(snapshot):
        raise GitSnapshotError("persisted Git snapshot digest does not match its canonical fields")
    return snapshot


def _sha256(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def _canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _snapshot_digest(snapshot: CanonicalGitSnapshot) -> str:
    identity = {
        "format_version": snapshot.format_version,
        "comparison_base_sha": snapshot.comparison_base_sha,
        "snapshot_head_sha": snapshot.snapshot_head_sha,
        "layers": [asdict(layer) for layer in snapshot.layers],
        "exclusions": snapshot.exclusions,
    }
    return _sha256(_canonical_json(identity))


def _safe_root(repository: Path) -> Path:
    if repository.is_symlink():
        raise GitSnapshotError("repository root must not be a symbolic link")
    if not repository.exists() or not repository.is_dir():
        raise GitSnapshotError("repository root must be an existing directory")
    return repository.resolve()


def _git(root: Path, *arguments: str, allow_status: Iterable[int] = (0,)) -> bytes:
    completed = subprocess.run(
        ("git", "-c", "core.quotepath=false", "-C", str(root), *arguments),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=30,
    )
    if completed.returncode not in set(allow_status):
        message = completed.stderr.decode("utf-8", errors="replace").strip()
        raise GitSnapshotError(message or f"git {' '.join(arguments)} failed")
    return completed.stdout


def _decode_path(value: bytes) -> str:
    try:
        path = value.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise GitSnapshotError("Git reported a path that is not valid UTF-8") from exc
    error = scope_path_error(path)
    if error:
        raise GitSnapshotError(f"Git reported unsafe path {path!r}: {error}")
    return path


def _repository_identity(root: Path) -> str:
    try:
        reported = _git(root, "rev-parse", "--show-toplevel").decode("utf-8").strip()
    except UnicodeDecodeError as exc:
        raise GitSnapshotError("Git repository root is not valid UTF-8") from exc
    if Path(reported).resolve() != root:
        raise GitSnapshotError("repository must be the Git worktree root")
    try:
        return _git(root, "rev-parse", "--verify", "HEAD^{commit}").decode("ascii").strip()
    except UnicodeDecodeError as exc:
        raise GitSnapshotError("Git HEAD is not a valid commit identifier") from exc


def resolve_comparison_base(repository: Path, revision: str) -> str:
    """Resolve an explicit base and require it to be an ancestor of HEAD."""

    root = _safe_root(repository)
    head = _repository_identity(root)
    try:
        base = _git(root, "rev-parse", "--verify", f"{revision}^{{commit}}").decode("ascii").strip()
    except UnicodeDecodeError as exc:
        raise GitSnapshotError("comparison base is not a valid commit identifier") from exc
    completed = subprocess.run(
        ("git", "-C", str(root), "merge-base", "--is-ancestor", base, head),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        check=False,
        timeout=30,
    )
    if completed.returncode == 1:
        raise GitSnapshotError("comparison base must be an ancestor of snapshot HEAD")
    if completed.returncode != 0:
        message = completed.stderr.decode("utf-8", errors="replace").strip()
        raise GitSnapshotError(message or "could not compare base with HEAD")
    return base


def _parse_name_status(output: bytes, *, layer: str) -> tuple[SnapshotChange, ...]:
    tokens = output.split(b"\0")
    if tokens and tokens[-1] == b"":
        tokens.pop()
    changes: list[SnapshotChange] = []
    index = 0
    while index < len(tokens):
        try:
            status_token = tokens[index].decode("ascii")
        except UnicodeDecodeError as exc:
            raise GitSnapshotError(f"Git reported a non-ASCII status in {layer}") from exc
        index += 1
        status_code = status_token[:1]
        if status_code in {"R", "C"}:
            if index + 1 >= len(tokens):
                raise GitSnapshotError(f"Git returned an incomplete {status_token} record")
            old_path = _decode_path(tokens[index])
            path = _decode_path(tokens[index + 1])
            index += 2
        else:
            if index >= len(tokens):
                raise GitSnapshotError(f"Git returned an incomplete {status_token} record")
            old_path = None
            path = _decode_path(tokens[index])
            index += 1
        changes.append(
            SnapshotChange(
                layer=layer,
                status=_STATUS_NAMES.get(status_code, "unknown"),
                path=path,
                old_path=old_path,
            )
        )
    return tuple(sorted(changes, key=lambda item: (item.path, item.old_path or "", item.status)))


def _tracked_layer(
    root: Path,
    *,
    name: str,
    name_status_arguments: tuple[str, ...],
    patch_arguments: tuple[str, ...],
) -> SnapshotLayer:
    changes = _parse_name_status(_git(root, *name_status_arguments), layer=name)
    patch = _git(root, *patch_arguments)
    return SnapshotLayer(name=name, identity_digest=_sha256(patch), changes=changes)


def _untracked_change(root: Path, relative: str) -> SnapshotChange:
    path = root.joinpath(*relative.split("/"))
    try:
        metadata = path.lstat()
    except OSError as exc:
        raise GitSnapshotError(f"cannot inspect untracked path {relative!r}: {exc}") from exc
    if stat.S_ISLNK(metadata.st_mode):
        try:
            content = os.readlink(path).encode("utf-8")
        except OSError as exc:
            raise GitSnapshotError(f"cannot read untracked link {relative!r}: {exc}") from exc
        kind = "symlink"
    elif stat.S_ISREG(metadata.st_mode):
        try:
            content = path.read_bytes()
        except OSError as exc:
            raise GitSnapshotError(f"cannot read untracked file {relative!r}: {exc}") from exc
        kind = "file"
    else:
        raise GitSnapshotError(f"untracked path {relative!r} is not a regular file or symlink")
    return SnapshotChange(
        layer="untracked",
        status="untracked",
        path=relative,
        old_path=None,
        content_digest=_sha256(content),
        content_kind=kind,
    )


def _untracked_layer(root: Path) -> SnapshotLayer:
    output = _git(root, "ls-files", "--others", "--exclude-standard", "-z")
    paths = sorted(_decode_path(value) for value in output.split(b"\0") if value)
    changes = tuple(
        _untracked_change(root, path)
        for path in paths
        if not is_segment_prefix(".agentgov", path)
    )
    identity = _sha256(_canonical_json([asdict(item) for item in changes]))
    return SnapshotLayer(name="untracked", identity_digest=identity, changes=changes)


def capture_git_snapshot(
    repository: Path,
    *,
    comparison_base: str,
) -> CanonicalGitSnapshot:
    """Capture canonical Git-layer identities without modifying the repository."""

    root = _safe_root(repository)
    head = _repository_identity(root)
    base = resolve_comparison_base(root, comparison_base)
    common = ("--binary", "--full-index", "--no-ext-diff", "--no-textconv", "--no-color", "--find-renames")
    layers = (
        _tracked_layer(
            root,
            name="committed",
            name_status_arguments=("diff", "--name-status", "-z", "--find-renames", base, head, "--"),
            patch_arguments=("diff", *common, base, head, "--"),
        ),
        _tracked_layer(
            root,
            name="staged",
            name_status_arguments=("diff", "--cached", "--name-status", "-z", "--find-renames", head, "--"),
            patch_arguments=("diff", "--cached", *common, head, "--"),
        ),
        _tracked_layer(
            root,
            name="unstaged",
            name_status_arguments=("diff", "--name-status", "-z", "--find-renames", "--"),
            patch_arguments=("diff", *common, "--"),
        ),
        _untracked_layer(root),
    )
    if tuple(layer.name for layer in layers) != _LAYER_NAMES:
        raise AssertionError("canonical layer ordering changed")
    snapshot = CanonicalGitSnapshot(
        format_version=GIT_SNAPSHOT_FORMAT,
        comparison_base_sha=base,
        snapshot_head_sha=head,
        change_set_digest="",
        layers=layers,
        exclusions=_EXCLUSIONS,
    )
    return replace(snapshot, change_set_digest=_snapshot_digest(snapshot))


def snapshot_paths(snapshot: CanonicalGitSnapshot) -> tuple[str, ...]:
    paths = {
        path
        for layer in snapshot.layers
        for change in layer.changes
        for path in (change.old_path, change.path)
        if path is not None
    }
    return tuple(sorted(paths))


def explain_snapshot_difference(
    expected: CanonicalGitSnapshot,
    current: CanonicalGitSnapshot,
) -> tuple[str, ...]:
    """Explain identity changes without exposing source content."""

    reasons: list[str] = []
    if expected.format_version != current.format_version:
        reasons.append("Git snapshot format changed")
    if expected.comparison_base_sha != current.comparison_base_sha:
        reasons.append("comparison base changed")
    if expected.snapshot_head_sha != current.snapshot_head_sha:
        reasons.append("snapshot HEAD changed after validation")
    expected_layers = {layer.name: layer for layer in expected.layers}
    current_layers = {layer.name: layer for layer in current.layers}
    for name in _LAYER_NAMES:
        before = expected_layers.get(name)
        after = current_layers.get(name)
        if before is None or after is None or before.identity_digest != after.identity_digest:
            paths = sorted(
                {
                    path
                    for layer in (before, after)
                    if layer is not None
                    for change in layer.changes
                    for path in (change.old_path, change.path)
                    if path is not None
                }
            )
            suffix = f": {', '.join(paths)}" if paths else ""
            reasons.append(f"{name} Git layer changed{suffix}")
    if expected.change_set_digest != current.change_set_digest and not reasons:
        reasons.append("canonical change-set identity changed")
    return tuple(reasons)
