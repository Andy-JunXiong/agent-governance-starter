"""Deterministic repository-local reference integrity checks."""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Mapping

from agentgov.capability import load_capability_manifest, validate_capability_manifest


class ReferenceStatus(str, Enum):
    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"


class ReferencePolicyError(Exception):
    """Raised when the check cannot safely interpret the supplied contract."""


@dataclass(frozen=True)
class ReferenceFinding:
    status: ReferenceStatus
    check_id: str
    message: str


@dataclass(frozen=True)
class ReferenceReport:
    manifest: Path
    capability_name: str
    findings: tuple[ReferenceFinding, ...]

    @property
    def has_failures(self) -> bool:
        return any(finding.status is ReferenceStatus.FAIL for finding in self.findings)

    def count(self, status: ReferenceStatus) -> int:
        return sum(finding.status is status for finding in self.findings)


def _repository_root(path: Path) -> Path:
    if path.is_symlink():
        raise ReferencePolicyError(f"repository root must not be a symbolic link: {path}")
    if not path.exists():
        raise FileNotFoundError(path)
    if not path.is_dir():
        raise ValueError(f"repository root is not a directory: {path}")
    return path.resolve()


def _resolve_path_inside(root: Path, path: Path, *, label: str) -> Path:
    candidate = path if path.is_absolute() else root / path
    resolved = candidate.resolve(strict=False)
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ReferencePolicyError(
            f"{label} must stay within repository root: {path}"
        ) from exc

    cursor = candidate
    while True:
        if cursor.is_symlink():
            raise ReferencePolicyError(
                f"{label} must not use a symbolic link: {path}"
            )
        if cursor.resolve(strict=False) == root:
            break
        if cursor.parent == cursor:
            break
        cursor = cursor.parent
    return resolved


def _resolve_reference(root: Path, reference: str, *, label: str) -> Path:
    path_text = reference.split("#", 1)[0]
    if not path_text or "://" in path_text:
        raise ReferencePolicyError(
            f"{label} must be a repository-relative path: {reference}"
        )
    path = Path(path_text)
    if path.is_absolute() or path.drive:
        raise ReferencePolicyError(
            f"{label} must be relative to repository root: {reference}"
        )
    return _resolve_path_inside(root, path, label=label)


def _load_valid_manifest(path: Path) -> Mapping[str, Any]:
    manifest = load_capability_manifest(path)
    errors = validate_capability_manifest(manifest)
    if errors:
        raise ReferencePolicyError("invalid capability manifest: " + "; ".join(errors))
    return manifest


def _check_file_references(
    root: Path,
    references: list[str],
    *,
    label: str,
) -> list[str]:
    errors: list[str] = []
    for reference in references:
        try:
            path = _resolve_reference(root, reference, label=label)
        except ReferencePolicyError as exc:
            errors.append(str(exc))
            continue
        if not path.exists():
            errors.append(f"{label} does not exist: {reference}")
        elif not path.is_file():
            errors.append(f"{label} is not a file: {reference}")
    return errors


def _check_schema_references(root: Path, references: list[str]) -> list[str]:
    errors: list[str] = []
    for reference in references:
        try:
            path = _resolve_reference(root, reference, label="contract schema")
        except ReferencePolicyError as exc:
            errors.append(str(exc))
            continue
        if not path.exists():
            errors.append(f"contract schema does not exist: {reference}")
            continue
        if not path.is_file():
            errors.append(f"contract schema is not a file: {reference}")
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except UnicodeError as exc:
            errors.append(f"contract schema is not valid UTF-8: {reference}: {exc}")
            continue
        except json.JSONDecodeError as exc:
            errors.append(
                f"contract schema is invalid JSON at line {exc.lineno}, "
                f"column {exc.colno}: {reference}: {exc.msg}"
            )
            continue
        if not isinstance(payload, Mapping):
            errors.append(f"contract schema root must be an object: {reference}")
    return errors


def _finding(
    capability_name: str,
    category: str,
    errors: list[str],
    *,
    pass_message: str,
) -> ReferenceFinding:
    if errors:
        return ReferenceFinding(
            ReferenceStatus.FAIL,
            f"references:{capability_name}:{category}",
            "; ".join(errors),
        )
    return ReferenceFinding(
        ReferenceStatus.PASS,
        f"references:{capability_name}:{category}",
        pass_message,
    )


def check_capability_references(
    manifest_path: Path,
    *,
    repository: Path,
) -> ReferenceReport:
    """Check declared file references without importing capability runtime code."""

    root = _repository_root(repository)
    safe_manifest = _resolve_path_inside(root, manifest_path, label="manifest path")
    if not safe_manifest.exists():
        raise FileNotFoundError(safe_manifest)
    if not safe_manifest.is_file():
        raise ValueError(f"manifest path is not a file: {manifest_path}")
    manifest = _load_valid_manifest(safe_manifest)
    name = str(manifest["name"])

    contract_refs = [
        str(manifest["contracts"]["input_schema"]),
        str(manifest["contracts"]["output_schema"]),
    ]
    findings = [
        _finding(
            name,
            "contracts",
            _check_schema_references(root, contract_refs),
            pass_message="input and output contract schemas are readable JSON objects",
        ),
        _finding(
            name,
            "callers",
            _check_file_references(
                root,
                list(manifest["called_by"]),
                label="declared caller",
            ),
            pass_message=(
                "all declared caller files exist"
                if manifest["called_by"]
                else "no caller files are declared"
            ),
        ),
        _finding(
            name,
            "sources",
            _check_file_references(
                root,
                list(manifest["provenance"]["source_refs"]),
                label="provenance source",
            ),
            pass_message="all provenance source files exist",
        ),
    ]

    evidence_refs = list(manifest["evaluation"]["evidence_refs"])
    if evidence_refs:
        evidence_errors: list[str] = []
        for reference in evidence_refs:
            try:
                path = _resolve_reference(root, reference, label="evaluation evidence")
            except ReferencePolicyError as exc:
                evidence_errors.append(str(exc))
                continue
            if not path.exists():
                evidence_errors.append(f"evaluation evidence does not exist: {reference}")
        findings.append(
            _finding(
                name,
                "evaluation",
                evidence_errors,
                pass_message="all declared evaluation evidence exists",
            )
        )
    else:
        findings.append(
            ReferenceFinding(
                ReferenceStatus.WARN,
                f"references:{name}:evaluation",
                "no evaluation evidence is declared for "
                f"{manifest['evaluation']['readiness']} readiness",
            )
        )

    return ReferenceReport(
        manifest=safe_manifest,
        capability_name=name,
        findings=tuple(findings),
    )
