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
    "artifact",
}
_VERSION_RE = re.compile(
    r"^[0-9]+\.[0-9]+\.[0-9]+(?:(?:a|b|rc)[0-9]+|\.dev[0-9]+)?$"
)
_LAYOUT_VERSION_RE = re.compile(r"^[0-9]+\.[0-9]+$")
_MIGRATION_ID_RE = re.compile(r"^[a-z0-9]+(?:[.-][a-z0-9]+)*$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_WHEEL_RE = re.compile(r"^agent_governance_starter-[A-Za-z0-9_.]+-py3-none-any\.whl$")


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

    artifact = document.get("artifact")
    if artifact is not None:
        if not isinstance(artifact, Mapping):
            errors.append("$.artifact must be null or an object")
        else:
            fields = {"filename", "url", "sha256", "install_method"}
            for field in sorted(fields - set(artifact)):
                errors.append(f"$.artifact.{field} is required")
            for field in sorted(set(artifact) - fields):
                errors.append(f"$.artifact.{field} is not allowed")
            filename = artifact.get("filename")
            if not isinstance(filename, str) or not _WHEEL_RE.fullmatch(filename):
                errors.append("$.artifact.filename must be an AgentGov universal wheel")
            url = artifact.get("url")
            if (
                not isinstance(url, str)
                or not url.startswith(
                    "https://github.com/Andy-JunXiong/"
                    "agent-governance-starter/releases/download/"
                )
                or not isinstance(filename, str)
                or not url.endswith("/" + filename)
            ):
                errors.append(
                    "$.artifact.url must be the matching fixed-tag GitHub Release asset"
                )
            sha256 = artifact.get("sha256")
            if not isinstance(sha256, str) or not _SHA256_RE.fullmatch(sha256):
                errors.append(
                    "$.artifact.sha256 must be 64 lowercase hexadecimal characters"
                )
            if artifact.get("install_method") != "pipx":
                errors.append("$.artifact.install_method must equal 'pipx'")
    if channel == "stable" and artifact is None:
        errors.append("$.artifact is required for stable releases")
    return errors


def validate_installed_release_metadata(document: Mapping[str, Any]) -> list[str]:
    """Validate bundled version metadata without requiring a self-hash.

    A stable wheel cannot contain its own final SHA-256. The bundled
    ``release/current.json`` therefore carries compatibility identity but no
    artifact. Public release manifests remain strict under
    :func:`validate_release_manifest`.
    """

    errors = validate_release_manifest(document)
    self_hash_error = "$.artifact is required for stable releases"
    if document.get("channel") == "stable" and document.get("artifact") is None:
        errors = [error for error in errors if error != self_hash_error]
    return errors


def load_release_manifest(path: Path) -> Mapping[str, Any]:
    """Load one release manifest without interpreting untrusted fields."""

    with path.open(encoding="utf-8") as handle:
        document = json.load(handle)
    if not isinstance(document, Mapping):
        raise TypeError("release manifest root must be an object")
    return document
