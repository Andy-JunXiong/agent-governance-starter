from __future__ import annotations

import glob
import hashlib
import json
import os
import subprocess
import tomllib
from pathlib import Path, PurePosixPath
from typing import Any


CONTRACT = "agentgov.distribution-input-manifest"
RESULT_CONTRACT = "agentgov.distribution-input-manifest-check-result"
SCHEMA_VERSION = "1.0"
FIXED_METADATA_INPUTS = ("LICENSE", "pyproject.toml")


class ManifestError(RuntimeError):
    """A fail-closed contract or observation error."""


def _safe_relative(value: str, *, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ManifestError(f"{label} must be a non-empty string")
    if "\\" in value:
        raise ManifestError(f"{label} must use '/' separators: {value!r}")
    path = PurePosixPath(value)
    if (
        path.is_absolute()
        or value != path.as_posix()
        or any(part in ("", ".", "..") or ":" in part for part in path.parts)
    ):
        raise ManifestError(f"{label} is not a normalized safe relative path: {value!r}")
    return value


def _inside(repository: Path, relative: str) -> Path:
    candidate = repository.joinpath(*PurePosixPath(relative).parts)
    try:
        candidate.resolve(strict=False).relative_to(repository.resolve(strict=True))
    except (OSError, ValueError) as exc:
        raise ManifestError(f"path escapes repository: {relative!r}") from exc
    return candidate


def _regular_file(repository: Path, relative: str) -> Path:
    candidate = _inside(repository, relative)
    if candidate.is_symlink():
        raise ManifestError(f"symbolic links are unsupported distribution inputs: {relative}")
    if not candidate.is_file():
        raise ManifestError(f"distribution input is not a regular file: {relative}")
    return candidate


def _read_pyproject(repository: Path) -> dict[str, Any]:
    path = _regular_file(repository, "pyproject.toml")
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, tomllib.TOMLDecodeError) as exc:
        raise ManifestError(f"cannot read supported pyproject.toml: {exc}") from exc
    if not isinstance(data, dict):
        raise ManifestError("pyproject.toml root must be a table")
    return data


def _walk_python_files(repository: Path, root_relative: str) -> set[str]:
    root = _inside(repository, root_relative)
    if root.is_symlink() or not root.is_dir():
        raise ManifestError(f"package-find root must be a real directory: {root_relative}")
    selected: set[str] = set()
    for current, directories, files in os.walk(root, followlinks=False):
        current_path = Path(current)
        for name in directories:
            candidate = current_path / name
            if candidate.is_symlink():
                relative = candidate.relative_to(repository).as_posix()
                raise ManifestError(f"symbolic links under package-find roots are unsupported: {relative}")
        for name in files:
            if not name.endswith(".py"):
                continue
            candidate = current_path / name
            relative = candidate.relative_to(repository).as_posix()
            _regular_file(repository, relative)
            selected.add(relative)
    return selected


def _expand_data_pattern(repository: Path, pattern: str) -> set[str]:
    pattern = _safe_relative(pattern, label="data-files pattern")
    absolute_pattern = str(repository.joinpath(*PurePosixPath(pattern).parts))
    matches = glob.glob(absolute_pattern, recursive="**" in pattern)
    selected: set[str] = set()
    for raw in matches:
        candidate = Path(raw)
        try:
            relative = candidate.relative_to(repository).as_posix()
        except ValueError as exc:
            raise ManifestError(f"data-files match escaped repository: {pattern!r}") from exc
        _regular_file(repository, relative)
        selected.add(relative)
    if not selected:
        raise ManifestError(f"data-files pattern matched no regular files: {pattern!r}")
    return selected


def derive_distribution_inputs(repository: Path) -> list[str]:
    repository = repository.resolve(strict=True)
    data = _read_pyproject(repository)
    project = data.get("project")
    if not isinstance(project, dict):
        raise ManifestError("[project] is required")
    readme = project.get("readme")
    if not isinstance(readme, str):
        raise ManifestError("only a string [project].readme is supported")
    if not isinstance(project.get("license"), str):
        raise ManifestError("only a string [project].license with fixed LICENSE input is supported")
    project_dynamic = project.get("dynamic", [])
    if not isinstance(project_dynamic, list) or not all(isinstance(item, str) for item in project_dynamic) or set(project_dynamic) - {"version"}:
        raise ManifestError("only dynamic project version metadata is supported")

    tool = data.get("tool")
    setuptools = tool.get("setuptools") if isinstance(tool, dict) else None
    if not isinstance(setuptools, dict):
        raise ManifestError("[tool.setuptools] is required")
    unsupported_setuptools = sorted(set(setuptools) - {"dynamic", "packages", "data-files"})
    if unsupported_setuptools:
        raise ManifestError(f"unsupported [tool.setuptools] keys: {unsupported_setuptools}")
    packages = setuptools.get("packages")
    find = packages.get("find") if isinstance(packages, dict) else None
    if not isinstance(find, dict):
        raise ManifestError("[tool.setuptools.packages.find] is required")
    if set(packages) != {"find"}:
        raise ManifestError(f"unsupported [tool.setuptools.packages] keys: {sorted(set(packages) - {'find'})}")
    unsupported_find = sorted(set(find) - {"where"})
    if unsupported_find:
        raise ManifestError(f"unsupported package-find keys: {unsupported_find}")
    where = find.get("where")
    if not isinstance(where, list) or not where or not all(isinstance(item, str) for item in where):
        raise ManifestError("package-find where must be a non-empty string array")
    data_files = setuptools.get("data-files")
    if not isinstance(data_files, dict) or not data_files:
        raise ManifestError("[tool.setuptools.data-files] must be a non-empty table")
    dynamic = setuptools.get("dynamic")
    if dynamic is not None:
        if not isinstance(dynamic, dict) or set(dynamic) - {"version"}:
            raise ManifestError("only [tool.setuptools.dynamic].version is supported")
        version = dynamic.get("version")
        if not isinstance(version, dict) or set(version) != {"attr"} or not isinstance(version.get("attr"), str):
            raise ManifestError("dynamic version must use one attr string")

    selected = set(FIXED_METADATA_INPUTS)
    selected.add(_safe_relative(readme, label="project readme"))
    for root in where:
        selected.update(_walk_python_files(repository, _safe_relative(root, label="package-find root")))
    for destination, patterns in data_files.items():
        _safe_relative(destination, label="data-files destination")
        if not isinstance(patterns, list) or not patterns or not all(isinstance(item, str) for item in patterns):
            raise ManifestError(f"data-files entry {destination!r} must be a non-empty string array")
        for pattern in patterns:
            selected.update(_expand_data_pattern(repository, pattern))
    for relative in selected:
        _regular_file(repository, relative)
    return sorted(selected)


def canonical_path_digest(paths: list[str]) -> str:
    payload = "".join(f"{path}\n" for path in paths).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def canonical_content_digest(repository: Path, paths: list[str]) -> str:
    lines = []
    for relative in paths:
        digest = hashlib.sha256(_regular_file(repository, relative).read_bytes()).hexdigest()
        lines.append(f"{relative}\0{digest}\n")
    return "sha256:" + hashlib.sha256("".join(lines).encode("utf-8")).hexdigest()


def _git(repository: Path, *arguments: str) -> bytes:
    result = subprocess.run(
        ["git", *arguments], cwd=repository, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, check=False,
    )
    if result.returncode:
        message = result.stderr.decode("utf-8", errors="replace").strip()
        raise ManifestError(f"read-only Git command failed ({' '.join(arguments)}): {message}")
    return result.stdout


def _nul_paths(payload: bytes) -> set[str]:
    return {
        item.decode("utf-8", errors="surrogateescape").replace("\\", "/")
        for item in payload.split(b"\0") if item
    }


def _git_snapshot(repository: Path) -> dict[str, Any]:
    tracked = _nul_paths(_git(repository, "ls-files", "-z"))
    changed = _nul_paths(_git(repository, "diff", "--name-only", "-z", "HEAD", "--"))
    untracked = _nul_paths(_git(repository, "ls-files", "--others", "--exclude-standard", "-z"))
    identity = hashlib.sha256(
        ("\n".join(sorted(tracked)) + "\0" + "\n".join(sorted(changed)) + "\0" + "\n".join(sorted(untracked))).encode("utf-8", errors="surrogateescape")
    ).hexdigest()
    return {"tracked": tracked, "changed": changed, "untracked": untracked, "identity": identity}


def _load_manifest(repository: Path, manifest_path: Path) -> dict[str, Any]:
    absolute = manifest_path if manifest_path.is_absolute() else repository / manifest_path
    try:
        if absolute.is_symlink() or not absolute.is_file():
            raise ManifestError("manifest must be a regular file")
        data = json.loads(absolute.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ManifestError(f"cannot read manifest JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise ManifestError("manifest root must be an object")
    required = {"contract", "schema_version", "authority", "derivation", "supersession", "paths", "path_digest", "content_digest"}
    if set(data) != required:
        raise ManifestError(f"manifest keys must be exactly {sorted(required)}")
    if data["contract"] != CONTRACT or data["schema_version"] != SCHEMA_VERSION:
        raise ManifestError("unsupported manifest contract or schema version")
    authority = data["authority"]
    authority_keys = {
        "authorizes_build", "authorizes_git_write", "authorizes_journey",
        "authorizes_publication", "authorizes_release", "authorizes_deployment",
    }
    if not isinstance(authority, dict) or set(authority) != authority_keys or any(value is not False for value in authority.values()):
        raise ManifestError("manifest authority must be an explicit non-empty all-false object")
    paths = data["paths"]
    if not isinstance(paths, list) or not paths or not all(isinstance(path, str) for path in paths):
        raise ManifestError("manifest paths must be a non-empty string array")
    for path in paths:
        _safe_relative(path, label="manifest path")
    if paths != sorted(paths):
        raise ManifestError("manifest paths must be sorted")
    if len(paths) != len(set(paths)):
        raise ManifestError("manifest paths must be unique")
    derivation = data["derivation"]
    derivation_keys = {"pyproject", "fixed_metadata_inputs", "package_inputs", "data_file_inputs", "glob_semantics"}
    if (
        not isinstance(derivation, dict)
        or set(derivation) != derivation_keys
        or derivation.get("pyproject") != "pyproject.toml"
        or derivation.get("fixed_metadata_inputs") != ["LICENSE", "pyproject.toml"]
        or derivation.get("package_inputs") != "regular .py files below each tool.setuptools.packages.find.where root"
        or derivation.get("data_file_inputs") != "regular files matched by tool.setuptools.data-files source patterns"
        or derivation.get("glob_semantics") != "python-glob-nonrecursive-unless-double-star"
    ):
        raise ManifestError("manifest derivation metadata is unsupported")
    supersession = data["supersession"]
    supersession_keys = {"supersedes", "historical_observed_count", "recovered_historical_paths", "reason"}
    if (
        not isinstance(supersession, dict)
        or set(supersession) != supersession_keys
        or supersession.get("supersedes") != "exact-distribution-pathspec-replay-v1 omitted path list"
        or supersession.get("recovered_historical_paths") is not False
        or supersession.get("historical_observed_count") != 199
        or not isinstance(supersession.get("reason"), str)
        or not supersession["reason"].strip()
    ):
        raise ManifestError("manifest must explicitly deny recovery of the historical 199 paths")
    for field in ("path_digest", "content_digest"):
        value = data[field]
        if not isinstance(value, str) or len(value) != 71 or not value.startswith("sha256:"):
            raise ManifestError(f"{field} must be a sha256 identity")
    return data


def check_manifest(repository: Path, manifest_path: Path) -> dict[str, Any]:
    repository = repository.resolve(strict=True)
    before = _git_snapshot(repository)
    manifest = _load_manifest(repository, manifest_path)
    declared = manifest["paths"]
    derived = derive_distribution_inputs(repository)
    derived_path_digest = canonical_path_digest(derived)
    derived_content_digest = canonical_content_digest(repository, derived)
    # Re-derive and re-hash around a second Git observation to reject a moving input set.
    after = _git_snapshot(repository)
    repeated = derive_distribution_inputs(repository)
    repeated_content_digest = canonical_content_digest(repository, repeated)
    if before["identity"] != after["identity"] or derived != repeated or derived_content_digest != repeated_content_digest:
        raise ManifestError("Git or filesystem distribution inputs changed during observation")

    declared_set = set(declared)
    derived_set = set(derived)
    missing = sorted(declared_set - derived_set)
    extra = sorted(derived_set - declared_set)
    digest_errors = []
    if manifest["path_digest"] != derived_path_digest:
        digest_errors.append("path_digest")
    if manifest["content_digest"] != derived_content_digest:
        digest_errors.append("content_digest")
    tracked = before["tracked"]
    changed = before["changed"]
    classifications = {"committed": 0, "tracked_delta": 0, "untracked_overlay": 0, "deletion": 0}
    for path in derived:
        if path not in tracked:
            classifications["untracked_overlay"] += 1
        elif path in changed:
            classifications["tracked_delta"] += 1
        else:
            classifications["committed"] += 1
    for path in declared:
        if path in tracked and path in changed and not (repository / path).is_file():
            classifications["deletion"] += 1

    errors = []
    if missing:
        errors.append("manifest contains paths not independently derived")
    if extra:
        errors.append("independent derivation contains paths missing from manifest")
    if digest_errors:
        errors.append("manifest digest mismatch: " + ", ".join(digest_errors))
    return {
        "contract": RESULT_CONTRACT,
        "schema_version": SCHEMA_VERSION,
        "status": "PASS" if not errors else "FAIL",
        "path_count": len(derived),
        "path_digest": derived_path_digest,
        "content_digest": derived_content_digest,
        "classifications": classifications,
        "differences": {"missing": missing, "extra": extra},
        "errors": errors,
        "claims": {
            "historical_199_paths_recovered": False,
            "artifact_built": False,
            "host_paths_or_contents_disclosed": False,
        },
    }
