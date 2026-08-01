"""Read-only tool and repository update checks."""

from __future__ import annotations

import json
import re
import shutil
import sys
import sysconfig
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping

from agentgov import __version__
from agentgov.release_metadata import (
    load_release_manifest,
    validate_installed_release_metadata,
    validate_release_manifest,
)


REPOSITORY_CONTRACT = "agentgov.repository-contract"
REPOSITORY_CONTRACT_SCHEMA_VERSION = "1.0"
UPDATE_CHECK_CONTRACT_VERSION = "1.0"
_COMPARABLE_VERSION_RE = re.compile(
    r"^(?P<major>[0-9]+)\.(?P<minor>[0-9]+)\.(?P<patch>[0-9]+)"
    r"(?:(?P<pre>a|b|rc)(?P<pre_number>[0-9]+)|\.dev(?P<dev_number>[0-9]+))?$"
)


@dataclass(frozen=True)
class UpdateCheck:
    repository: Path
    executable: Path
    environment: str
    installed_version: str
    available_version: str
    channel: str
    manifest_source: Path
    repository_layout: str | None
    target_layout: str
    readable: bool
    tool_update_available: bool
    repository_refresh_required: bool
    shadowed_by_project_venv: bool
    artifact: Mapping[str, str] | None


def _asset_root() -> Path:
    source_checkout = Path(__file__).resolve().parents[2]
    if (source_checkout / "release/current.json").is_file():
        return source_checkout
    installed = Path(sysconfig.get_path("data")) / "share" / "agent-governance-starter"
    if (installed / "release/current.json").is_file():
        return installed
    raise FileNotFoundError("bundled release/current.json is not installed")


def default_release_manifest() -> Path:
    return _asset_root() / "release/current.json"


def comparable_version_key(value: str) -> tuple[int, int, int, int, int]:
    """Order the exact PEP 440 subset accepted by release manifests."""

    match = _COMPARABLE_VERSION_RE.fullmatch(value)
    if match is None:
        raise ValueError(f"unsupported comparable tool version: {value}")
    stage = 4
    stage_number = 0
    if match["dev_number"] is not None:
        stage = 0
        stage_number = int(match["dev_number"])
    elif match["pre"] is not None:
        stage = {"a": 1, "b": 2, "rc": 3}[match["pre"]]
        stage_number = int(match["pre_number"])
    return (
        int(match["major"]),
        int(match["minor"]),
        int(match["patch"]),
        stage,
        stage_number,
    )


def load_repository_layout(root: Path) -> str | None:
    path = root / "governance/contract.json"
    if not path.exists():
        return None
    if path.is_symlink() or not path.is_file():
        raise ValueError("governance/contract.json must be a regular file")
    document = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(document, Mapping):
        raise ValueError("governance/contract.json root must be an object")
    expected = {"contract", "schema_version", "layout_version"}
    if set(document) != expected:
        raise ValueError("governance/contract.json must contain exactly contract, schema_version, and layout_version")
    if document.get("contract") != REPOSITORY_CONTRACT:
        raise ValueError(f"governance/contract.json contract must equal {REPOSITORY_CONTRACT!r}")
    if document.get("schema_version") != REPOSITORY_CONTRACT_SCHEMA_VERSION:
        raise ValueError("governance/contract.json schema_version must equal '1.0'")
    layout = document.get("layout_version")
    if not isinstance(layout, str) or len(layout.split(".")) != 2 or not all(
        part.isdigit() for part in layout.split(".")
    ):
        raise ValueError("governance/contract.json layout_version must use major.minor format")
    return layout


def check_for_updates(
    root: Path,
    *,
    manifest_path: Path | None = None,
    allow_contract_path_conflict: bool = False,
) -> UpdateCheck:
    resolved = root.resolve()
    if not resolved.exists():
        raise FileNotFoundError(root)
    if not resolved.is_dir():
        raise ValueError(f"repository path is not a directory: {root}")

    bundled_source = default_release_manifest().resolve()
    source = (manifest_path or bundled_source).resolve()
    manifest = load_release_manifest(source)
    errors = (
        validate_installed_release_metadata(manifest)
        if source == bundled_source
        else validate_release_manifest(manifest)
    )
    if errors:
        raise ValueError("invalid release manifest: " + "; ".join(errors))

    contract_path = resolved / "governance/contract.json"
    if allow_contract_path_conflict and (
        contract_path.is_symlink() or contract_path.is_dir()
    ):
        layout = None
    else:
        layout = load_repository_layout(resolved)
    readable_layouts = manifest["readable_layout_versions"]
    target = manifest["target_layout_version"]
    executable = Path(sys.executable).resolve()
    invoked = Path(sys.argv[0])
    if invoked.name.lower() in {"agentgov", "agentgov.exe"} and invoked.exists():
        executable = invoked.resolve()
    else:
        command = shutil.which("agentgov")
        if command:
            executable = Path(command).resolve()
    project_venv = (resolved / ".venv").resolve()
    shadowed = executable == project_venv / "Scripts/agentgov.exe" or project_venv in executable.parents
    executable_text = str(executable).lower()
    pipx_venv = Path.home() / "pipx/venvs/agent-governance-starter"
    exposed_by_pipx = (
        executable == (Path.home() / ".local/bin/agentgov.exe").resolve()
        and pipx_venv.is_dir()
    )
    environment = (
        "pipx"
        if ("pipx" in executable_text and "venvs" in executable_text) or exposed_by_pipx
        else ("project-venv" if shadowed else "unknown")
    )
    available = str(manifest["tool_version"])
    raw_artifact = manifest.get("artifact")
    artifact = (
        {str(key): str(value) for key, value in raw_artifact.items()}
        if isinstance(raw_artifact, Mapping)
        else None
    )
    return UpdateCheck(
        repository=resolved,
        executable=executable,
        environment=environment,
        installed_version=__version__,
        available_version=available,
        channel=str(manifest["channel"]),
        manifest_source=source,
        repository_layout=layout,
        target_layout=str(target),
        readable=layout is None or layout in readable_layouts,
        tool_update_available=(
            comparable_version_key(available) > comparable_version_key(__version__)
        ),
        repository_refresh_required=layout != target,
        shadowed_by_project_venv=shadowed,
        artifact=artifact,
    )


def render_update_check_json(report: UpdateCheck) -> str:
    payload: dict[str, Any] = {
        "contract_version": UPDATE_CHECK_CONTRACT_VERSION,
        "mode": "read_only",
        "tool": {
            "installed_version": report.installed_version,
            "available_version": report.available_version,
            "update_available": report.tool_update_available,
            "executable": str(report.executable),
            "environment": report.environment,
            "shadowed_by_project_venv": report.shadowed_by_project_venv,
        },
        "release": {
            "channel": report.channel,
            "manifest_source": str(report.manifest_source),
            "artifact": dict(report.artifact) if report.artifact else None,
        },
        "repository": {
            "path": str(report.repository),
            "layout_version": report.repository_layout,
            "target_layout_version": report.target_layout,
            "readable": report.readable,
            "refresh_required": report.repository_refresh_required,
        },
        "authority_boundary": {
            "tool_updated": False,
            "repository_modified": False,
        },
    }
    return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"


def request_update_confirmation(
    *,
    repository: Path,
    change_count: int,
    decision_reader: Callable[[str], str],
    is_interactive_terminal: bool,
) -> bool:
    """Grant orchestration authority only for exact interactive confirmation."""

    if not is_interactive_terminal:
        return False
    decision = decision_reader(
        f'Type UPDATE to apply {change_count} repository change(s) in '
        f'"{repository}": '
    )
    return decision == "UPDATE"
