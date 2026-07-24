"""Zero-dependency validation for repository-native capability control mappings."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Mapping


CONTROL_MAPPING_CONTRACT = "agentgov.control-mapping"
CONTROL_MAPPING_SCHEMA_VERSION = "1.0"
APPLICABILITY_STATUSES = {"applicable", "not_applicable"}
ENFORCEMENT_MODES = {
    "deterministic",
    "platform_enforced",
    "human_procedural",
    "advisory_only",
}
_CONTROL_DIRECTORY = Path("governance/controls")
_NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_CONTROL_ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class ControlStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"


@dataclass(frozen=True)
class ControlReport:
    path: Path
    status: ControlStatus
    messages: tuple[str, ...]
    capability_name: str | None
    control_ids: tuple[str, ...]


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


def _string(
    value: Any,
    path: str,
    errors: list[str],
    *,
    minimum: int = 1,
) -> str | None:
    if not isinstance(value, str) or len(value.strip()) < minimum:
        errors.append(f"{path} must be a string with at least {minimum} characters")
        return None
    return value


def _string_list(
    value: Any,
    path: str,
    errors: list[str],
    *,
    minimum: int = 0,
) -> list[str] | None:
    if not isinstance(value, list):
        errors.append(f"{path} must be an array")
        return None
    if len(value) < minimum:
        errors.append(f"{path} must contain at least {minimum} item(s)")
    if any(not isinstance(item, str) or not item.strip() for item in value):
        errors.append(f"{path} must contain only non-empty strings")
        return None
    if len(set(value)) != len(value):
        errors.append(f"{path} must contain unique items")
    return value


def validate_control_mapping_document(document: Mapping[str, Any]) -> list[str]:
    """Return deterministic structural violations for one control mapping."""

    errors: list[str] = []
    top_fields = {"contract", "schema_version", "capability_name", "controls"}
    _fields(
        document,
        path="$",
        required=top_fields,
        allowed=top_fields,
        errors=errors,
    )
    if document.get("contract") != CONTROL_MAPPING_CONTRACT:
        errors.append(f"$.contract must equal {CONTROL_MAPPING_CONTRACT!r}")
    if document.get("schema_version") != CONTROL_MAPPING_SCHEMA_VERSION:
        errors.append(
            f"$.schema_version must equal {CONTROL_MAPPING_SCHEMA_VERSION!r}"
        )
    capability_name = _string(
        document.get("capability_name"),
        "$.capability_name",
        errors,
    )
    if capability_name and not _NAME_RE.fullmatch(capability_name):
        errors.append("$.capability_name must use kebab-case")

    controls = document.get("controls")
    if not isinstance(controls, list):
        errors.append("$.controls must be an array")
        return errors
    if not controls:
        errors.append("$.controls must contain at least 1 item(s)")

    seen_ids: set[str] = set()
    common_fields = {
        "control_id",
        "objective",
        "applicability",
        "owner",
        "exception_authority",
    }
    applicable_fields = {
        "enforcement_mode",
        "implementation_refs",
        "verification_refs",
    }
    for index, item in enumerate(controls):
        item_path = f"$.controls[{index}]"
        control = _mapping(item, item_path, errors)
        if control is None:
            continue
        applicability = control.get("applicability")
        if applicability == "applicable":
            required = common_fields | applicable_fields
            allowed = required
        elif applicability == "not_applicable":
            required = common_fields | {"rationale"}
            allowed = required
        else:
            required = common_fields
            allowed = common_fields | applicable_fields | {"rationale"}
        _fields(
            control,
            path=item_path,
            required=required,
            allowed=allowed,
            errors=errors,
        )

        control_id = _string(
            control.get("control_id"),
            f"{item_path}.control_id",
            errors,
        )
        if control_id:
            if not _CONTROL_ID_RE.fullmatch(control_id):
                errors.append(f"{item_path}.control_id must use kebab-case")
            if control_id in seen_ids:
                errors.append(
                    f"{item_path}.control_id duplicates {control_id!r}"
                )
            seen_ids.add(control_id)
        _string(
            control.get("objective"),
            f"{item_path}.objective",
            errors,
            minimum=10,
        )
        if applicability not in APPLICABILITY_STATUSES:
            errors.append(
                f"{item_path}.applicability must be one of "
                f"{sorted(APPLICABILITY_STATUSES)}"
            )
        _string(control.get("owner"), f"{item_path}.owner", errors)
        _string(
            control.get("exception_authority"),
            f"{item_path}.exception_authority",
            errors,
        )

        if applicability == "applicable":
            mode = control.get("enforcement_mode")
            if mode not in ENFORCEMENT_MODES:
                errors.append(
                    f"{item_path}.enforcement_mode must be one of "
                    f"{sorted(ENFORCEMENT_MODES)}"
                )
            _string_list(
                control.get("implementation_refs"),
                f"{item_path}.implementation_refs",
                errors,
                minimum=1,
            )
            _string_list(
                control.get("verification_refs"),
                f"{item_path}.verification_refs",
                errors,
                minimum=1,
            )
        elif applicability == "not_applicable":
            _string(
                control.get("rationale"),
                f"{item_path}.rationale",
                errors,
                minimum=10,
            )
    return errors


def _safe_readable_reference(root: Path, reference: str, *, label: str) -> Path:
    if "\\" in reference:
        raise ValueError(f"{label} must use forward slashes: {reference}")
    path_text = reference.split("#", 1)[0]
    if not path_text or "://" in path_text:
        raise ValueError(
            f"{label} must be a repository-relative file path: {reference}"
        )
    relative = Path(path_text)
    if relative.is_absolute() or relative.drive:
        raise ValueError(f"{label} must be relative to repository root: {reference}")
    if not relative.parts or path_text == "." or ".." in relative.parts:
        raise ValueError(
            f"{label} must not be empty or contain parent traversal: {reference}"
        )

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
    if not resolved.exists():
        raise ValueError(f"{label} does not exist: {reference}")
    if not resolved.is_file():
        raise ValueError(f"{label} is not a file: {reference}")
    try:
        resolved.read_text(encoding="utf-8")
    except UnicodeError as exc:
        raise ValueError(f"{label} is not valid UTF-8: {reference}: {exc}") from exc
    except OSError as exc:
        raise ValueError(f"{label} could not be read: {reference}: {exc}") from exc
    return resolved


def _load_mapping(path: Path) -> Mapping[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError("control mapping root must be an object")
    return payload


def check_control_mapping(repository: Path, mapping_path: Path) -> ControlReport:
    """Validate one canonical mapping and its repository-local references."""

    if repository.is_symlink():
        raise ValueError(f"repository root must not be a symbolic link: {repository}")
    if not repository.exists():
        raise FileNotFoundError(repository)
    if not repository.is_dir():
        raise ValueError(f"repository root is not a directory: {repository}")
    root = repository.resolve()
    candidate = mapping_path if mapping_path.is_absolute() else root / mapping_path
    if candidate.is_symlink():
        return ControlReport(
            candidate,
            ControlStatus.FAIL,
            ("control mapping must not be a symbolic link",),
            None,
            (),
        )
    resolved = candidate.resolve(strict=False)
    try:
        relative_path = resolved.relative_to(root)
    except ValueError:
        return ControlReport(
            resolved,
            ControlStatus.FAIL,
            ("control mapping must stay within repository root",),
            None,
            (),
        )
    cursor = candidate
    while True:
        if cursor.is_symlink():
            return ControlReport(
                resolved,
                ControlStatus.FAIL,
                ("control mapping must not use a symbolic link",),
                None,
                (),
            )
        if cursor.resolve(strict=False) == root or cursor.parent == cursor:
            break
        cursor = cursor.parent
    if (
        relative_path.parent != _CONTROL_DIRECTORY
        or relative_path.suffix != ".json"
    ):
        return ControlReport(
            resolved,
            ControlStatus.FAIL,
            (
                "control mapping must be a direct JSON child of "
                "governance/controls/",
            ),
            None,
            (),
        )
    if not resolved.exists():
        raise FileNotFoundError(resolved)
    if not resolved.is_file():
        return ControlReport(
            resolved,
            ControlStatus.FAIL,
            ("control mapping path is not a file",),
            None,
            (),
        )

    try:
        document = _load_mapping(resolved)
    except UnicodeError as exc:
        return ControlReport(
            resolved,
            ControlStatus.FAIL,
            (f"control mapping is not valid UTF-8: {exc}",),
            None,
            (),
        )
    except json.JSONDecodeError as exc:
        return ControlReport(
            resolved,
            ControlStatus.FAIL,
            (
                "control mapping is invalid JSON at "
                f"line {exc.lineno}, column {exc.colno}: {exc.msg}",
            ),
            None,
            (),
        )
    except (OSError, ValueError) as exc:
        return ControlReport(
            resolved,
            ControlStatus.FAIL,
            (str(exc),),
            None,
            (),
        )

    raw_name = document.get("capability_name")
    capability_name = (
        raw_name
        if isinstance(raw_name, str) and _NAME_RE.fullmatch(raw_name)
        else None
    )
    raw_controls = document.get("controls")
    control_ids: tuple[str, ...] = ()
    if isinstance(raw_controls, list):
        control_ids = tuple(
            str(item["control_id"])
            for item in raw_controls
            if isinstance(item, Mapping)
            and isinstance(item.get("control_id"), str)
            and _CONTROL_ID_RE.fullmatch(str(item["control_id"]))
        )

    errors = validate_control_mapping_document(document)
    if capability_name and resolved.stem != capability_name:
        errors.append(
            f"control mapping filename {resolved.name!r} must match "
            f"capability_name {capability_name!r}"
        )
    if not errors:
        for control in document["controls"]:
            if control["applicability"] != "applicable":
                continue
            control_id = str(control["control_id"])
            for field in ("implementation_refs", "verification_refs"):
                label = f"control {control_id!r} {field[:-1]} reference"
                for reference in control[field]:
                    try:
                        _safe_readable_reference(
                            root,
                            str(reference),
                            label=label,
                        )
                    except ValueError as exc:
                        errors.append(str(exc))

    if errors:
        return ControlReport(
            resolved,
            ControlStatus.FAIL,
            tuple(errors),
            capability_name,
            control_ids,
        )
    applicable_count = sum(
        item["applicability"] == "applicable" for item in document["controls"]
    )
    not_applicable_count = len(document["controls"]) - applicable_count
    return ControlReport(
        resolved,
        ControlStatus.PASS,
        (
            f"control mapping is valid for {applicable_count} applicable and "
            f"{not_applicable_count} not-applicable control(s)",
        ),
        capability_name,
        control_ids,
    )
