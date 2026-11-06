"""Read-only environment and adoption diagnosis for guided onboarding."""

from __future__ import annotations

import json
import math
import os
import stat
import sys
import tomllib
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Callable, Sequence

from agentgov import __version__
from agentgov.adoption import AdoptionState, inspect_adoption
from agentgov.codex_hooks import CodexHookPolicyError, resolve_git_worktree


class DoctorStatus(str, Enum):
    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"
    ADVISORY = "ADVISORY"


@dataclass(frozen=True)
class DoctorFinding:
    status: DoctorStatus
    check_id: str
    message: str
    classification: str


@dataclass(frozen=True)
class DoctorReport:
    root: Path
    findings: tuple[DoctorFinding, ...]
    python_executable: Path
    python_version: str

    def count(self, status: DoctorStatus) -> int:
        return sum(finding.status is status for finding in self.findings)

    @property
    def has_failures(self) -> bool:
        return any(finding.status is DoctorStatus.FAIL for finding in self.findings)


DOCTOR_REPORT_VERSION = "1.0"
MINIMUM_PYTHON = (3, 11)
WINDOWS_PATH_ADVISORY_THRESHOLD = 180
MAX_MCP_CONFIG_BYTES = 256 * 1024


class _McpConfigReadError(ValueError):
    """A bounded local configuration observation is unavailable."""


def _unsafe_mcp_path(info: os.stat_result, *, directory: bool = False) -> bool:
    expected_type = stat.S_ISDIR if directory else stat.S_ISREG
    return not expected_type(info.st_mode) or bool(
        getattr(info, "st_file_attributes", 0)
        & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    )


def _mcp_path_identity(info: os.stat_result) -> tuple[int, int]:
    return info.st_dev, info.st_ino


def _read_local_mcp_config(root: Path) -> dict | None:
    """Read one bounded regular file, without following configuration links."""

    directory = root / ".codex"
    target = directory / "config.toml"
    try:
        directory_info = directory.lstat()
    except FileNotFoundError:
        return None
    if _unsafe_mcp_path(directory_info, directory=True):
        raise _McpConfigReadError("unsafe directory type or reparse point")
    try:
        expected = target.lstat()
    except FileNotFoundError:
        return None
    if _unsafe_mcp_path(expected):
        raise _McpConfigReadError("unsafe file type or reparse point")
    if expected.st_size > MAX_MCP_CONFIG_BYTES:
        raise _McpConfigReadError("file exceeds the 256 KiB read limit")

    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    with os.fdopen(os.open(target, flags), "rb") as stream:
        opened = os.fstat(stream.fileno())
        current_directory = directory.lstat()
        if (
            _unsafe_mcp_path(opened)
            or _unsafe_mcp_path(current_directory, directory=True)
            or not expected.st_ino
            or _mcp_path_identity(opened) != _mcp_path_identity(expected)
            or _mcp_path_identity(current_directory)
            != _mcp_path_identity(directory_info)
        ):
            raise _McpConfigReadError("path identity changed before reading")
        data = stream.read(MAX_MCP_CONFIG_BYTES + 1)
    if len(data) > MAX_MCP_CONFIG_BYTES:
        raise _McpConfigReadError("file exceeds the 256 KiB read limit")
    return tomllib.loads(data.decode("utf-8"))


def _mcp_configuration_findings(root: Path) -> tuple[DoctorFinding, ...]:
    """Describe local filters, never effective host policy or live readiness."""

    live_state = DoctorFinding(
        DoctorStatus.ADVISORY,
        "mcp:live-state",
        "project-local configuration only: merged user, ancestor, managed and plugin "
        "settings, trust, loaded version, live activation and native form support "
        "remain unknown; no configuration edits, network requests or server starts "
        "are performed",
        "advisory",
    )

    def unavailable(message: str) -> tuple[DoctorFinding, ...]:
        return (
            DoctorFinding(
                DoctorStatus.WARN, "mcp:configuration", message, "deterministic"
            ),
            live_state,
        )

    try:
        document = _read_local_mcp_config(root)
    except _McpConfigReadError as exc:
        # Only this private exception contains controlled, value-free wording.
        return unavailable(
            f"local .codex/config.toml was not inspected: {exc}; "
            "review the local file safely before retrying"
        )
    except (OSError, UnicodeError, ValueError, RecursionError):
        return unavailable(
            "local .codex/config.toml is unreadable or invalid UTF-8 TOML; "
            "review its encoding, syntax and access; raw content and errors are omitted"
        )

    servers = None if document is None else document.get("mcp_servers")
    if document is None or servers is None or (
        isinstance(servers, dict) and "agentgov_governance" not in servers
    ):
        return (
            DoctorFinding(
                DoctorStatus.PASS,
                "mcp:configuration",
                "not applicable: no repository-local AgentGov MCP server entry; "
                "MCP integration is optional and other configuration locations "
                "were not inspected",
                "deterministic",
            ),
            live_state,
        )
    if not isinstance(servers, dict) or not isinstance(
        servers.get("agentgov_governance"), dict
    ):
        return unavailable(
            "local mcp_servers.agentgov_governance must be a TOML table; "
            "review its structure; raw values are omitted"
        )
    server = servers["agentgov_governance"]
    if "enabled" in server and type(server["enabled"]) is not bool:
        return unavailable("local enabled must be a boolean; raw values are omitted")
    for field in ("enabled_tools", "disabled_tools"):
        if field in server and (
            not isinstance(server[field], list)
            or any(not isinstance(item, str) for item in server[field])
        ):
            return unavailable(
                f"local {field} must be a list of tool-name strings; "
                "raw values are omitted"
            )
    if "tool_timeout_sec" in server:
        timeout = server["tool_timeout_sec"]
        try:
            valid_timeout = (
                type(timeout) in (int, float)
                and math.isfinite(timeout)
                and timeout > 0
            )
        except OverflowError:
            valid_timeout = False
        if not valid_timeout:
            return unavailable(
                "local tool_timeout_sec must be a positive finite number; "
                "raw values are omitted"
            )

    # Lazy imports keep basic doctor import independent of Adapter initialization.
    from agentgov.codex_mcp import CODEX_MCP_TOOL_TIMEOUT_SEC
    from agentgov.governance_mcp import MCP_TOOL_POLICIES

    findings = [
        DoctorFinding(
            DoctorStatus.PASS,
            "mcp:configuration",
            "bounded repository-local AgentGov MCP configuration was inspected; "
            "only diagnostic fields and known policy tool names are reported",
            "deterministic",
        )
    ]
    enabled = server.get("enabled") is not False
    findings.append(
        DoctorFinding(
            DoctorStatus.PASS if enabled else DoctorStatus.WARN,
            "mcp:enabled",
            (
                "local server entry is not explicitly disabled; effective host "
                "enablement is unverified"
                if enabled
                else "local server entry is disabled; this may be intentional; "
                "review the intended integration before changing it"
            ),
            "deterministic",
        )
    )
    allowed = set(server["enabled_tools"]) if "enabled_tools" in server else None
    denied = set(server.get("disabled_tools", []))
    for gate, check_id, label in (
        ("base", "mcp:base-tools", "base"),
        ("form_elicitation", "mcp:form-tools", "form-gated"),
    ):
        names = [
            policy.name
            for policy in MCP_TOOL_POLICIES
            if policy.discovery_gate == gate
        ]
        omitted = [
            name
            for name in names
            if (allowed is not None and name not in allowed) or name in denied
        ]
        findings.append(
            DoctorFinding(
                DoctorStatus.WARN if omitted else DoctorStatus.PASS,
                check_id,
                (
                    f"local filters omit {label} policy tools: {', '.join(omitted)}; "
                    "restrictions may be intentional; review them before making changes"
                    if omitted
                    else f"local filters permit all known {label} policy tools; "
                    "this does not prove live discovery"
                ),
                "deterministic",
            )
        )
    timeout = server.get("tool_timeout_sec")
    if timeout is None:
        timeout_message = (
            "local tool_timeout_sec is omitted; the effective inherited setting is "
            "unknown (the documented host default is 60 seconds); AgentGov's "
            f"generated configuration recommends {CODEX_MCP_TOOL_TIMEOUT_SEC} seconds "
            "for task-declared validation; review the effective setting"
        )
        timeout_status = DoctorStatus.WARN
    elif timeout < CODEX_MCP_TOOL_TIMEOUT_SEC:
        timeout_message = (
            "local tool_timeout_sec is below AgentGov's generated recommendation "
            f"of {CODEX_MCP_TOOL_TIMEOUT_SEC} seconds for task-declared validation; "
            "review the intended timeout; this does not prove a call will time out"
        )
        timeout_status = DoctorStatus.WARN
    else:
        timeout_message = (
            "local tool_timeout_sec meets AgentGov's generated recommendation "
            f"of {CODEX_MCP_TOOL_TIMEOUT_SEC} seconds; this does not guarantee that "
            "every multi-command validation finishes within the client timeout"
        )
        timeout_status = DoctorStatus.PASS
    findings.append(
        DoctorFinding(timeout_status, "mcp:tool-timeout", timeout_message, "advisory")
    )
    findings.append(live_state)
    return tuple(findings)


def _project_environment_finding(root: Path) -> DoctorFinding:
    environment = root / ".venv"
    if not environment.exists() and not environment.is_symlink():
        return DoctorFinding(
            DoctorStatus.PASS,
            "environment:project-venv",
            "no project .venv was detected; AgentGov does not require one",
            "deterministic",
        )
    if environment.is_symlink() or not environment.is_dir():
        detail = "is not a regular directory"
    else:
        configuration = environment / "pyvenv.cfg"
        detail = (
            "has pyvenv.cfg"
            if configuration.is_file()
            else "has no readable pyvenv.cfg and may be stale or incomplete"
        )
    return DoctorFinding(
        DoctorStatus.ADVISORY,
        "environment:project-venv",
        f"project .venv {detail}; it is not used or repaired by AgentGov",
        "advisory",
    )


def _git_access_finding(
    root: Path,
    *,
    git_marker_exists: bool,
    resolver: Callable[[Path], Path],
) -> DoctorFinding:
    if not git_marker_exists:
        return DoctorFinding(
            DoctorStatus.WARN,
            "repository:git-access",
            "Git worktree access was not checked because no .git context was detected",
            "deterministic",
        )
    try:
        resolver(root)
    except (CodexHookPolicyError, OSError, UnicodeError, ValueError):
        return DoctorFinding(
            DoctorStatus.FAIL,
            "repository:git-access",
            "Git worktree access failed; confirm the selected path is a Git worktree "
            "trusted for the current OS account",
            "deterministic",
        )
    return DoctorFinding(
        DoctorStatus.PASS,
        "repository:git-access",
        "Git worktree access confirmed for the current OS account",
        "deterministic",
    )


def diagnose_repository(
    root: Path,
    *,
    python_version: Sequence[int] | None = None,
    python_executable: Path | None = None,
    platform_name: str | None = None,
    git_worktree_resolver: Callable[[Path], Path] | None = None,
) -> DoctorReport:
    """Diagnose onboarding prerequisites without modifying the repository."""

    version = tuple(python_version or sys.version_info[:3])
    executable = python_executable or Path(sys.executable)
    platform = platform_name or os.name
    resolver = git_worktree_resolver or resolve_git_worktree
    adoption = inspect_adoption(root)
    resolved = root.resolve()
    findings: list[DoctorFinding] = []

    if version[:2] >= MINIMUM_PYTHON:
        findings.append(
            DoctorFinding(
                DoctorStatus.PASS,
                "environment:python",
                f"AgentGov is running with supported Python {'.'.join(map(str, version[:3]))}",
                "deterministic",
            )
        )
    else:
        findings.append(
            DoctorFinding(
                DoctorStatus.FAIL,
                "environment:python",
                "AgentGov requires Python 3.11 or newer; the target project "
                "environment will not be modified",
                "deterministic",
            )
        )

    git_marker = root / ".git"
    findings.append(
        DoctorFinding(
            DoctorStatus.PASS if git_marker.exists() else DoctorStatus.WARN,
            "repository:git-context",
            (
                "Git repository context detected"
                if git_marker.exists()
                else "no .git context detected; AgentGov can inspect this path but "
                "reviewable change tracking is not yet available"
            ),
            "deterministic",
        )
    )
    findings.append(
        _git_access_finding(
            root,
            git_marker_exists=git_marker.exists(),
            resolver=resolver,
        )
    )

    if platform == "nt" and len(str(resolved)) >= WINDOWS_PATH_ADVISORY_THRESHOLD:
        findings.append(
            DoctorFinding(
                DoctorStatus.WARN,
                "environment:windows-path",
                f"resolved path length is {len(str(resolved))}; use isolated tool "
                "execution and avoid cloning AgentGov inside this repository",
                "advisory",
            )
        )
    else:
        findings.append(
            DoctorFinding(
                DoctorStatus.PASS,
                "environment:windows-path",
                "no elevated Windows path-length risk detected",
                "deterministic",
            )
        )

    findings.append(_project_environment_finding(root))
    findings.extend(_mcp_configuration_findings(resolved))

    if adoption.has_conflicts:
        findings.append(
            DoctorFinding(
                DoctorStatus.FAIL,
                "adoption:conflicts",
                f"{adoption.count(AdoptionState.CONFLICT)} governance path "
                "conflict(s) require human resolution before adoption",
                "deterministic",
            )
        )
    elif adoption.count(AdoptionState.MISSING):
        findings.append(
            DoctorFinding(
                DoctorStatus.WARN,
                "adoption:state",
                f"{adoption.count(AdoptionState.MISSING)} core governance path(s) "
                "are not configured; preview adoption before writing",
                "deterministic",
            )
        )
    else:
        findings.append(
            DoctorFinding(
                DoctorStatus.PASS,
                "adoption:state",
                "core governance paths are configured; run the repository check next",
                "deterministic",
            )
        )

    findings.append(
        DoctorFinding(
            DoctorStatus.ADVISORY,
            "onboarding:human-boundary",
            "diagnosis does not prove governance sufficiency or authorize writes, "
            "Git operations, merge, publish, release, or deploy",
            "advisory",
        )
    )
    return DoctorReport(
        root=resolved,
        findings=tuple(findings),
        python_executable=executable,
        python_version=".".join(map(str, version[:3])),
    )


def render_doctor_report_json(report: DoctorReport, *, non_interactive: bool) -> str:
    payload = {
        "contract_version": DOCTOR_REPORT_VERSION,
        "tool": {"name": "agentgov", "version": __version__},
        "repository": str(report.root),
        "mode": "read_only",
        "interaction": "non_interactive" if non_interactive else "no_prompt",
        "runtime": {
            "python_executable": str(report.python_executable),
            "python_version": report.python_version,
        },
        "summary": {
            status.value: report.count(status) for status in DoctorStatus
        },
        "findings": [
            {
                "status": finding.status.value,
                "check_id": finding.check_id,
                "message": finding.message,
                "classification": finding.classification,
            }
            for finding in report.findings
        ],
        "authority_boundary": {
            "modifies_repository": False,
            "repairs_project_environment": False,
            "installs_project_dependencies": False,
            "authorizes_git_or_release_operations": False,
        },
    }
    return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
