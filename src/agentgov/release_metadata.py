"""Strict validation for machine-readable AgentGov release manifests."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Mapping


RELEASE_MANIFEST_CONTRACT = "agentgov.release-manifest"
RELEASE_MANIFEST_SCHEMA_VERSION = "1.0"
RELEASE_CHANNELS = {"development", "release-candidate", "stable"}

_FIELDS = {
    "contract",
    "schema_version",
    "distribution_name",
    "tool_version",
    "channel",
    "supported_from",
    "readable_layout_versions",
    "target_layout_version",
    "repository_changes_declared",
    "declared_migrations",
    "release_notes_url",
}
_VERSION_RE = re.compile(
    r"^[0-9]+\.[0-9]+\.[0-9]+(?:(?:a|b|rc)[0-9]+|\.dev[0-9]+)?$"
)
_LAYOUT_VERSION_RE = re.compile(r"^[0-9]+\.[0-9]+$")
_MIGRATION_ID_RE = re.compile(r"^[a-z0-9]+(?:[.-][a-z0-9]+)*$")


def _string_list(
    value: Any,
    path: str,
    errors: list[str],
    *,
    pattern: re.Pattern[str],
) -> list[str] | None:
    if not isinstance(value, list):
        errors.append(f"{path} must be an array")
        return None
    if any(not isinstance(item, str) or not pattern.fullmatch(item) for item in value):
        errors.append(f"{path} contains an unsupported value")
        return None
    if len(set(value)) != len(value):
        errors.append(f"{path} must contain unique items")
    return value


def validate_release_manifest(document: Mapping[str, Any]) -> list[str]:
    """Return deterministic structural errors for one release manifest."""

    errors: list[str] = []
    for field in sorted(_FIELDS - set(document)):
        errors.append(f"$.{field} is required")
    for field in sorted(set(document) - _FIELDS):
        errors.append(f"$.{field} is not allowed")

    if document.get("contract") != RELEASE_MANIFEST_CONTRACT:
        errors.append(f"$.contract must equal {RELEASE_MANIFEST_CONTRACT!r}")
    if document.get("schema_version") != RELEASE_MANIFEST_SCHEMA_VERSION:
        errors.append(
            "$.schema_version must equal "
            f"{RELEASE_MANIFEST_SCHEMA_VERSION!r}"
        )
    if document.get("distribution_name") != "agent-governance-starter":
        errors.append(
            "$.distribution_name must equal 'agent-governance-starter'"
        )

    tool_version = document.get("tool_version")
    if not isinstance(tool_version, str) or not _VERSION_RE.fullmatch(tool_version):
        errors.append("$.tool_version must be a supported PEP 440 release version")

    channel = document.get("channel")
    if channel not in RELEASE_CHANNELS:
        errors.append(
            "$.channel must be one of development, release-candidate, stable"
        )
    elif isinstance(tool_version, str) and _VERSION_RE.fullmatch(tool_version):
        if channel == "development" and ".dev" not in tool_version:
            errors.append("$.channel development requires a .dev tool version")
        if channel == "release-candidate" and "rc" not in tool_version:
            errors.append("$.channel release-candidate requires an rc tool version")
        if channel == "stable" and ("rc" in tool_version or ".dev" in tool_version):
            errors.append("$.channel stable requires a final tool version")

    _string_list(
        document.get("supported_from"),
        "$.supported_from",
        errors,
        pattern=_VERSION_RE,
    )
    readable_layouts = _string_list(
        document.get("readable_layout_versions"),
        "$.readable_layout_versions",
        errors,
        pattern=_LAYOUT_VERSION_RE,
    )
    if readable_layouts == []:
        errors.append("$.readable_layout_versions must contain at least one item")

    target_layout = document.get("target_layout_version")
    if not isinstance(target_layout, str) or not _LAYOUT_VERSION_RE.fullmatch(
        target_layout
    ):
        errors.append("$.target_layout_version must use major.minor format")
    elif readable_layouts is not None and target_layout not in readable_layouts:
        errors.append(
            "$.target_layout_version must be listed in "
            "$.readable_layout_versions"
        )

    changes_declared = document.get("repository_changes_declared")
    if not isinstance(changes_declared, bool):
        errors.append("$.repository_changes_declared must be a boolean")
    migrations = _string_list(
        document.get("declared_migrations"),
        "$.declared_migrations",
        errors,
        pattern=_MIGRATION_ID_RE,
    )
    if migrations and changes_declared is not True:
        errors.append(
            "$.repository_changes_declared must be true when migrations are declared"
        )

    release_notes_url = document.get("release_notes_url")
    if not isinstance(release_notes_url, str) or not release_notes_url.startswith(
        "https://"
    ):
        errors.append("$.release_notes_url must be an https URL")
    return errors


def load_release_manifest(path: Path) -> Mapping[str, Any]:
    """Load one release manifest without interpreting untrusted fields."""

    with path.open(encoding="utf-8") as handle:
        document = json.load(handle)
    if not isinstance(document, Mapping):
        raise TypeError("release manifest root must be an object")
    return document
