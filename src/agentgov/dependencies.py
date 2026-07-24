"""Zero-dependency validation for explicit capability dependency declarations."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Mapping

from agentgov.capability import EVALUATION_READINESS


CAPABILITY_DEPENDENCIES_CONTRACT = "agentgov.capability-dependencies"
CAPABILITY_DEPENDENCIES_SCHEMA_VERSION = "1.0"
READINESS_ORDER = (
    "not_configured",
    "schema_only",
    "needs_seed_cases",
    "baseline_ready",
    "regression_ready",
)
_READINESS_RANK = {value: index for index, value in enumerate(READINESS_ORDER)}
_DEPENDENCY_DIRECTORY = Path("governance/dependencies")
_NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class DependencyStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"


@dataclass(frozen=True)
class DependencyEdge:
    capability: str
    minimum_readiness: str | None


@dataclass(frozen=True)
class DependencyReport:
    path: Path
    status: DependencyStatus
    messages: tuple[str, ...]
    capability_name: str | None
    dependencies: tuple[DependencyEdge, ...]


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


def _name(value: Any, path: str, errors: list[str]) -> str | None:
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{path} must be a non-empty string")
        return None
    if not _NAME_RE.fullmatch(value):
        errors.append(f"{path} must use kebab-case")
        return None
    return value


def validate_dependency_document(document: Mapping[str, Any]) -> list[str]:
    """Return deterministic structural violations for one declaration."""

    errors: list[str] = []
    top_fields = {
        "contract",
        "schema_version",
        "capability_name",
        "depends_on",
    }
    _fields(
        document,
        path="$",
        required=top_fields,
        allowed=top_fields,
        errors=errors,
    )
    if document.get("contract") != CAPABILITY_DEPENDENCIES_CONTRACT:
        errors.append(
            f"$.contract must equal {CAPABILITY_DEPENDENCIES_CONTRACT!r}"
        )
    if document.get("schema_version") != CAPABILITY_DEPENDENCIES_SCHEMA_VERSION:
        errors.append(
            "$.schema_version must equal "
            f"{CAPABILITY_DEPENDENCIES_SCHEMA_VERSION!r}"
        )
    capability_name = _name(
        document.get("capability_name"),
        "$.capability_name",
        errors,
    )

    depends_on = document.get("depends_on")
    if not isinstance(depends_on, list):
        errors.append("$.depends_on must be an array")
        return errors

    seen_capabilities: set[str] = set()
    for index, item in enumerate(depends_on):
        item_path = f"$.depends_on[{index}]"
        dependency = _mapping(item, item_path, errors)
        if dependency is None:
            continue
        _fields(
            dependency,
            path=item_path,
            required={"capability"},
            allowed={"capability", "minimum_readiness"},
            errors=errors,
        )
        upstream = _name(
            dependency.get("capability"),
            f"{item_path}.capability",
            errors,
        )
        if upstream:
            if upstream in seen_capabilities:
                errors.append(
                    f"{item_path}.capability duplicates {upstream!r}"
                )
            seen_capabilities.add(upstream)
            if capability_name and upstream == capability_name:
                errors.append(
                    f"{item_path}.capability must not depend on itself"
                )

        if "minimum_readiness" in dependency:
            minimum = dependency.get("minimum_readiness")
            if minimum not in EVALUATION_READINESS:
                errors.append(
                    f"{item_path}.minimum_readiness must be one of "
                    f"{sorted(EVALUATION_READINESS)}"
                )
    return errors


def readiness_meets(actual: str, minimum: str) -> bool:
    """Return whether an actual readiness meets one explicitly declared floor."""

    if actual not in _READINESS_RANK:
        raise ValueError(f"unknown actual readiness: {actual}")
    if minimum not in _READINESS_RANK:
        raise ValueError(f"unknown minimum readiness: {minimum}")
    return _READINESS_RANK[actual] >= _READINESS_RANK[minimum]


def find_dependency_cycles(
    adjacency: Mapping[str, set[str]],
) -> tuple[tuple[str, ...], ...]:
    """Return deterministic strongly connected components that form cycles."""

    index = 0
    indices: dict[str, int] = {}
    lowlinks: dict[str, int] = {}
    stack: list[str] = []
    on_stack: set[str] = set()
    cycles: list[tuple[str, ...]] = []

    nodes = set(adjacency)
    for dependencies in adjacency.values():
        nodes.update(dependencies)

    def visit(node: str) -> None:
        nonlocal index
        indices[node] = index
        lowlinks[node] = index
        index += 1
        stack.append(node)
        on_stack.add(node)

        for dependency in sorted(adjacency.get(node, set())):
            if dependency not in indices:
                visit(dependency)
                lowlinks[node] = min(lowlinks[node], lowlinks[dependency])
            elif dependency in on_stack:
                lowlinks[node] = min(lowlinks[node], indices[dependency])

        if lowlinks[node] != indices[node]:
            return
        component: list[str] = []
        while True:
            member = stack.pop()
            on_stack.remove(member)
            component.append(member)
            if member == node:
                break
        if len(component) > 1 or node in adjacency.get(node, set()):
            cycles.append(tuple(sorted(component)))

    for node in sorted(nodes):
        if node not in indices:
            visit(node)
    return tuple(sorted(cycles))


def _load_declaration(path: Path) -> Mapping[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError("capability dependency declaration root must be an object")
    return payload


def check_dependency_declaration(
    repository: Path,
    declaration_path: Path,
) -> DependencyReport:
    """Validate one canonical capability dependency declaration."""

    if repository.is_symlink():
        raise ValueError(f"repository root must not be a symbolic link: {repository}")
    if not repository.exists():
        raise FileNotFoundError(repository)
    if not repository.is_dir():
        raise ValueError(f"repository root is not a directory: {repository}")
    root = repository.resolve()
    candidate = (
        declaration_path
        if declaration_path.is_absolute()
        else root / declaration_path
    )
    if candidate.is_symlink():
        return DependencyReport(
            candidate,
            DependencyStatus.FAIL,
            ("capability dependency declaration must not be a symbolic link",),
            None,
            (),
        )
    resolved = candidate.resolve(strict=False)
    try:
        relative_path = resolved.relative_to(root)
    except ValueError:
        return DependencyReport(
            resolved,
            DependencyStatus.FAIL,
            ("capability dependency declaration must stay within repository root",),
            None,
            (),
        )
    cursor = candidate
    while True:
        if cursor.is_symlink():
            return DependencyReport(
                resolved,
                DependencyStatus.FAIL,
                (
                    "capability dependency declaration must not use a "
                    "symbolic link",
                ),
                None,
                (),
            )
        if cursor.resolve(strict=False) == root or cursor.parent == cursor:
            break
        cursor = cursor.parent
    if (
        relative_path.parent != _DEPENDENCY_DIRECTORY
        or relative_path.suffix != ".json"
    ):
        return DependencyReport(
            resolved,
            DependencyStatus.FAIL,
            (
                "capability dependency declaration must be a direct JSON "
                "child of governance/dependencies/",
            ),
            None,
            (),
        )
    if not resolved.exists():
        raise FileNotFoundError(resolved)
    if not resolved.is_file():
        return DependencyReport(
            resolved,
            DependencyStatus.FAIL,
            ("capability dependency declaration path is not a file",),
            None,
            (),
        )

    try:
        document = _load_declaration(resolved)
    except UnicodeError as exc:
        return DependencyReport(
            resolved,
            DependencyStatus.FAIL,
            (f"capability dependency declaration is not valid UTF-8: {exc}",),
            None,
            (),
        )
    except json.JSONDecodeError as exc:
        return DependencyReport(
            resolved,
            DependencyStatus.FAIL,
            (
                "capability dependency declaration is invalid JSON at "
                f"line {exc.lineno}, column {exc.colno}: {exc.msg}",
            ),
            None,
            (),
        )
    except (OSError, ValueError) as exc:
        return DependencyReport(
            resolved,
            DependencyStatus.FAIL,
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
    dependencies: tuple[DependencyEdge, ...] = ()
    raw_dependencies = document.get("depends_on")
    if isinstance(raw_dependencies, list):
        dependencies = tuple(
            DependencyEdge(
                capability=str(item["capability"]),
                minimum_readiness=(
                    str(item["minimum_readiness"])
                    if "minimum_readiness" in item
                    and isinstance(item["minimum_readiness"], str)
                    else None
                ),
            )
            for item in raw_dependencies
            if isinstance(item, Mapping)
            and isinstance(item.get("capability"), str)
            and _NAME_RE.fullmatch(str(item["capability"]))
        )

    errors = validate_dependency_document(document)
    if capability_name and resolved.stem != capability_name:
        errors.append(
            f"capability dependency filename {resolved.name!r} must match "
            f"capability_name {capability_name!r}"
        )
    if errors:
        return DependencyReport(
            resolved,
            DependencyStatus.FAIL,
            tuple(errors),
            capability_name,
            dependencies,
        )
    minimum_count = sum(
        edge.minimum_readiness is not None for edge in dependencies
    )
    return DependencyReport(
        resolved,
        DependencyStatus.PASS,
        (
            f"capability dependency declaration is valid for "
            f"{len(dependencies)} dependency edge(s), including "
            f"{minimum_count} explicit minimum readiness requirement(s)",
        ),
        capability_name,
        dependencies,
    )
