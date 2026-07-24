"""Read-only environment and adoption diagnosis for guided onboarding."""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Sequence

from agentgov.adoption import AdoptionState, inspect_adoption


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


def diagnose_repository(
    root: Path,
    *,
    python_version: Sequence[int] | None = None,
    python_executable: Path | None = None,
    platform_name: str | None = None,
) -> DoctorReport:
    """Diagnose onboarding prerequisites without modifying the repository."""

    version = tuple(python_version or sys.version_info[:3])
    executable = python_executable or Path(sys.executable)
    platform = platform_name or os.name
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
