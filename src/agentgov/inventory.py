"""Deterministic governance inventory validation and declaration closure checks."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Mapping

from agentgov.capability import (
    CANONICAL_CONTRACT,
    load_capability_manifest,
    validate_capability_manifest,
)


INVENTORY_CONTRACT = "agentgov.governance-inventory"
INVENTORY_SCHEMA_VERSION = "1.0"
GOVERNANCE_STATUSES = {"provisional", "active", "retired"}
_INVENTORY_PATH = Path("governance/inventory.json")
_CAPABILITY_DIRECTORY = Path("governance/capabilities")
_NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class InventoryStatus(str, Enum):
    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"


@dataclass(frozen=True)
class InventoryReport:
    path: Path
    status: InventoryStatus
    messages: tuple[str, ...]
    configured: bool
    capability_names: tuple[str, ...] = ()
    capability_readiness: tuple[tuple[str, str], ...] = ()


def _mapping(value: Any, path: str, errors: list[str]) -> Mapping[str, Any] | None:
    if not isinstance(value, Mapping):
        errors.append(f"{path} must be an object")
        return None
    return value


def _fields(
    value: Mapping[str, Any],
    *,
    path: str,
    required: set[str],
    allowed: set[str],
    errors: list[str],
) -> None:
    for field in sorted(required - set(value)):
        errors.append(f"{path}.{field} is required")
    for field in sorted(set(value) - allowed):
        errors.append(f"{path}.{field} is not allowed")


def _string(value: Any, path: str, errors: list[str], *, minimum: int = 1) -> str | None:
    if not isinstance(value, str) or len(value.strip()) < minimum:
        errors.append(f"{path} must be a string with at least {minimum} characters")
        return None
    return value


def validate_inventory_document(document: Mapping[str, Any]) -> list[str]:
    """Return deterministic structural violations for one inventory document."""

    errors: list[str] = []
    top_fields = {"contract", "schema_version", "capabilities", "exclusions"}
    _fields(
        document,
        path="$",
        required=top_fields,
        allowed=top_fields,
        errors=errors,
    )
    if document.get("contract") != INVENTORY_CONTRACT:
        errors.append(f"$.contract must equal {INVENTORY_CONTRACT!r}")
    if document.get("schema_version") != INVENTORY_SCHEMA_VERSION:
        errors.append(
            f"$.schema_version must equal {INVENTORY_SCHEMA_VERSION!r}"
        )

    capabilities = document.get("capabilities")
    if not isinstance(capabilities, list):
        errors.append("$.capabilities must be an array")
    else:
        seen_names: set[str] = set()
        seen_manifests: set[str] = set()
        for index, item in enumerate(capabilities):
            item_path = f"$.capabilities[{index}]"
            capability = _mapping(item, item_path, errors)
            if capability is None:
                continue
            fields = {"name", "manifest", "owner", "governance_status"}
            _fields(
                capability,
                path=item_path,
                required=fields,
                allowed=fields,
                errors=errors,
            )
            name = _string(capability.get("name"), f"{item_path}.name", errors)
            if name:
                if not _NAME_RE.fullmatch(name):
                    errors.append(f"{item_path}.name must use kebab-case")
                if name in seen_names:
                    errors.append(f"{item_path}.name duplicates {name!r}")
                seen_names.add(name)
            manifest = _string(
                capability.get("manifest"),
                f"{item_path}.manifest",
                errors,
            )
            if manifest:
                if manifest in seen_manifests:
                    errors.append(
                        f"{item_path}.manifest duplicates {manifest!r}"
                    )
                seen_manifests.add(manifest)
            _string(capability.get("owner"), f"{item_path}.owner", errors)
            status = capability.get("governance_status")
            if status not in GOVERNANCE_STATUSES:
                errors.append(
                    f"{item_path}.governance_status must be one of "
                    f"{sorted(GOVERNANCE_STATUSES)}"
                )

    exclusions = document.get("exclusions")
    if not isinstance(exclusions, list):
        errors.append("$.exclusions must be an array")
    else:
        seen_paths: set[str] = set()
        for index, item in enumerate(exclusions):
            item_path = f"$.exclusions[{index}]"
            exclusion = _mapping(item, item_path, errors)
            if exclusion is None:
                continue
            fields = {"path", "reason"}
            _fields(
                exclusion,
                path=item_path,
                required=fields,
                allowed=fields,
                errors=errors,
            )
            path = _string(exclusion.get("path"), f"{item_path}.path", errors)
            if path:
                if path in seen_paths:
                    errors.append(f"{item_path}.path duplicates {path!r}")
                seen_paths.add(path)
            _string(
                exclusion.get("reason"),
                f"{item_path}.reason",
                errors,
                minimum=10,
            )
    return errors


def _safe_reference(root: Path, reference: str, *, label: str) -> Path:
    if "\\" in reference:
        raise ValueError(f"{label} must use forward slashes: {reference}")
    if "://" in reference:
        raise ValueError(f"{label} must be a repository-relative path: {reference}")
    relative = Path(reference)
    if not relative.parts or reference in {".", ""} or ".." in relative.parts:
        raise ValueError(
            f"{label} must not be empty or contain parent traversal: {reference}"
        )
    if relative.is_absolute() or relative.drive:
        raise ValueError(f"{label} must be relative to repository root: {reference}")
    candidate = root / relative
    resolved = candidate.resolve(strict=False)
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ValueError(
            f"{label} must stay within repository root: {reference}"
        ) from exc

    cursor = candidate
    while True:
        if cursor.is_symlink():
            raise ValueError(f"{label} must not use a symbolic link: {reference}")
        if cursor.resolve(strict=False) == root or cursor.parent == cursor:
            break
        cursor = cursor.parent
    return resolved


def _load_inventory(path: Path) -> Mapping[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError("inventory root must be an object")
    return payload


def check_inventory(repository: Path) -> InventoryReport:
    """Validate the canonical inventory and its declared manifest closure."""

    if repository.is_symlink():
        raise ValueError(f"repository root must not be a symbolic link: {repository}")
    if not repository.exists():
        raise FileNotFoundError(repository)
    if not repository.is_dir():
        raise ValueError(f"repository root is not a directory: {repository}")
    root = repository.resolve()
    inventory_path = root / _INVENTORY_PATH
    if inventory_path.is_symlink():
        return InventoryReport(
            inventory_path,
            InventoryStatus.FAIL,
            ("governance/inventory.json must not be a symbolic link",),
            True,
        )
    if not inventory_path.exists():
        return InventoryReport(
            inventory_path,
            InventoryStatus.WARN,
            ("governance/inventory.json is not configured",),
            False,
        )
    if not inventory_path.is_file():
        return InventoryReport(
            inventory_path,
            InventoryStatus.FAIL,
            ("governance/inventory.json is not a file",),
            True,
        )

    try:
        document = _load_inventory(inventory_path)
    except UnicodeError as exc:
        return InventoryReport(
            inventory_path,
            InventoryStatus.FAIL,
            (f"inventory is not valid UTF-8: {exc}",),
            True,
        )
    except json.JSONDecodeError as exc:
        return InventoryReport(
            inventory_path,
            InventoryStatus.FAIL,
            (
                "inventory is invalid JSON at "
                f"line {exc.lineno}, column {exc.colno}: {exc.msg}",
            ),
            True,
        )
    except ValueError as exc:
        return InventoryReport(
            inventory_path,
            InventoryStatus.FAIL,
            (str(exc),),
            True,
        )
    except OSError as exc:
        return InventoryReport(
            inventory_path,
            InventoryStatus.FAIL,
            (f"inventory could not be read: {exc}",),
            True,
        )

    errors = validate_inventory_document(document)
    if errors:
        return InventoryReport(
            inventory_path,
            InventoryStatus.FAIL,
            tuple(errors),
            True,
        )

    listed_manifests: set[str] = set()
    capability_readiness: dict[str, str] = {}
    for item in document["capabilities"]:
        reference = str(item["manifest"])
        try:
            manifest_path = _safe_reference(
                root,
                reference,
                label="inventory manifest",
            )
        except ValueError as exc:
            errors.append(str(exc))
            continue
        try:
            relative_manifest = manifest_path.relative_to(root)
        except ValueError:
            errors.append(
                f"inventory manifest must stay within repository root: {reference}"
            )
            continue
        listed_manifests.add(relative_manifest.as_posix())
        if (
            not relative_manifest.parts[:2]
            == _CAPABILITY_DIRECTORY.parts
            or manifest_path.suffix != ".json"
        ):
            errors.append(
                "inventory manifest must reference a JSON file under "
                f"governance/capabilities/: {reference}"
            )
            continue
        if not manifest_path.exists():
            errors.append(f"inventory manifest does not exist: {reference}")
            continue
        if not manifest_path.is_file():
            errors.append(f"inventory manifest is not a file: {reference}")
            continue
        try:
            manifest = load_capability_manifest(manifest_path)
        except (json.JSONDecodeError, UnicodeError, OSError, ValueError) as exc:
            errors.append(f"inventory manifest is unreadable: {reference}: {exc}")
            continue
        manifest_errors = validate_capability_manifest(manifest)
        if manifest_errors:
            errors.append(
                f"inventory manifest is invalid: {reference}: "
                + "; ".join(manifest_errors)
            )
            continue
        if manifest.get("contract") != CANONICAL_CONTRACT:
            errors.append(
                f"inventory manifest must use {CANONICAL_CONTRACT!r}: {reference}"
            )
        if manifest.get("name") != item["name"]:
            errors.append(
                f"inventory name {item['name']!r} does not match manifest "
                f"name {manifest.get('name')!r}: {reference}"
            )
        if manifest.get("owner") != item["owner"]:
            errors.append(
                f"inventory owner {item['owner']!r} does not match manifest "
                f"owner {manifest.get('owner')!r}: {reference}"
            )
        evaluation = manifest.get("evaluation")
        if isinstance(evaluation, Mapping):
            readiness = evaluation.get("readiness")
            if isinstance(readiness, str):
                capability_readiness[str(item["name"])] = readiness

    capability_root = root / _CAPABILITY_DIRECTORY
    if capability_root.is_symlink():
        errors.append(
            "canonical capability directory must not be a symbolic link: "
            "governance/capabilities"
        )
    elif capability_root.is_dir():
        for manifest_path in sorted(capability_root.rglob("*.json")):
            if manifest_path.is_symlink():
                continue
            reference = manifest_path.relative_to(root).as_posix()
            if reference not in listed_manifests:
                errors.append(
                    f"canonical capability manifest is not listed in inventory: "
                    f"{reference}"
                )

    for item in document["exclusions"]:
        reference = str(item["path"])
        try:
            excluded_path = _safe_reference(
                root,
                reference,
                label="inventory exclusion",
            )
        except ValueError as exc:
            errors.append(str(exc))
            continue
        if not excluded_path.exists():
            errors.append(f"inventory exclusion does not exist: {reference}")

    if errors:
        return InventoryReport(
            inventory_path,
            InventoryStatus.FAIL,
            tuple(errors),
            True,
        )
    return InventoryReport(
        inventory_path,
        InventoryStatus.PASS,
        (
            f"inventory declaration closure is valid for "
            f"{len(document['capabilities'])} capability(s) and "
            f"{len(document['exclusions'])} exclusion(s)",
        ),
        True,
        tuple(sorted(str(item["name"]) for item in document["capabilities"])),
        tuple(sorted(capability_readiness.items())),
    )
