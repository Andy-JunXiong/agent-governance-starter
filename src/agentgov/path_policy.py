"""Portable repository-path policy shared by context and scope checks."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Iterable


_WINDOWS_DRIVE_RE = re.compile(r"^[A-Za-z]:")
_GLOB_CHARACTERS = set("*?[]")


@dataclass(frozen=True)
class PathScopeDecision:
    path: str
    admitted: bool
    matched_include: str | None
    matched_exclude: str | None
    reason: str


def scope_path_error(value: str) -> str | None:
    """Return one deterministic declaration error for a scope path."""

    if "\\" in value:
        return "must use forward slashes"
    if "://" in value or _WINDOWS_DRIVE_RE.match(value):
        return "must be a repository-relative path"
    if any(character in value for character in _GLOB_CHARACTERS):
        return "must be an exact path or path prefix, not a glob"
    relative = PurePosixPath(value)
    if relative.is_absolute() or value in {"", "."} or ".." in relative.parts:
        return "must not be empty, absolute, '.', or contain parent traversal"
    if any(part == "" for part in value.split("/")):
        return "must not contain empty path segments"
    return None


def _require_path(value: str) -> None:
    error = scope_path_error(value)
    if error:
        raise ValueError(f"path {value!r} {error}")


def path_segments(value: str) -> tuple[str, ...]:
    _require_path(value)
    return PurePosixPath(value).parts


def is_segment_prefix(prefix: str, path: str) -> bool:
    """Return true only for equality or a complete path-segment prefix."""

    prefix_parts = path_segments(prefix)
    path_parts = path_segments(path)
    return len(prefix_parts) <= len(path_parts) and path_parts[: len(prefix_parts)] == prefix_parts


def paths_overlap(left: str, right: str) -> bool:
    """Return true when either valid path is a segment prefix of the other."""

    return is_segment_prefix(left, right) or is_segment_prefix(right, left)


def evaluate_path_scope(
    path: str,
    *,
    includes: Iterable[str],
    excludes: Iterable[str],
) -> PathScopeDecision:
    """Evaluate one actual Git path; an exclusion always overrides inclusion."""

    _require_path(path)
    include_matches = sorted(
        (prefix for prefix in includes if is_segment_prefix(prefix, path)),
        key=lambda value: (len(path_segments(value)), value),
        reverse=True,
    )
    exclude_matches = sorted(
        (prefix for prefix in excludes if is_segment_prefix(prefix, path)),
        key=lambda value: (len(path_segments(value)), value),
        reverse=True,
    )
    matched_include = include_matches[0] if include_matches else None
    matched_exclude = exclude_matches[0] if exclude_matches else None
    if matched_exclude is not None:
        return PathScopeDecision(
            path=path,
            admitted=False,
            matched_include=matched_include,
            matched_exclude=matched_exclude,
            reason=f"path is excluded by admitted prefix {matched_exclude!r}",
        )
    if matched_include is None:
        return PathScopeDecision(
            path=path,
            admitted=False,
            matched_include=None,
            matched_exclude=None,
            reason="path is outside every admitted include prefix",
        )
    return PathScopeDecision(
        path=path,
        admitted=True,
        matched_include=matched_include,
        matched_exclude=None,
        reason=f"path is admitted by include prefix {matched_include!r}",
    )


def scope_intersects_reference(
    reference: str,
    *,
    includes: Iterable[str],
    excludes: Iterable[str],
) -> bool:
    """Return true when an artifact path overlaps some non-excluded scope."""

    _require_path(reference)
    for included in includes:
        if not paths_overlap(included, reference):
            continue
        intersection = (
            included
            if len(path_segments(included)) >= len(path_segments(reference))
            else reference
        )
        if any(is_segment_prefix(excluded, intersection) for excluded in excludes):
            continue
        return True
    return False
