"""Read-only guided onboarding planning."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from agentgov.adoption import (
    AdoptionState,
    ExistingRepositoryAdoption,
    adopt_existing_repository,
    inspect_adoption,
)
from agentgov.doctor import DoctorReport, DoctorStatus, diagnose_repository


@dataclass(frozen=True)
class OnboardingPlan:
    root: Path
    project_name: str
    diagnosis: DoctorReport
    adoption: ExistingRepositoryAdoption


@dataclass(frozen=True)
class OnboardingResult:
    root: Path
    created_files: tuple[Path, ...]
    preserved_files: tuple[Path, ...]


class OnboardingConflictError(Exception):
    """Raised when the reviewed onboarding plan is no longer safe to apply."""


ONBOARDING_PLAN_VERSION = "1.0"


def _scaffold_area(path: Path) -> str:
    value = path.as_posix()
    if value == "AGENTS.md":
        return "constitution"
    if value == "docs/adr/TEMPLATE.md":
        return "adr-template"
    if value == "docs/adr/INVARIANTS.md":
        return "invariants"
    if value.startswith("evaluation/"):
        return "evaluation"
    if value.startswith("agent-skills/"):
        return "agent-skills"
    return "capabilities"


def plan_onboarding(root: Path, *, project_name: str) -> OnboardingPlan:
    """Build a complete adoption preview without writing repository files."""

    diagnosis = diagnose_repository(root)
    adoption = adopt_existing_repository(
        root,
        project_name=project_name,
        dry_run=True,
    )
    inspection = inspect_adoption(root)
    missing_areas = {
        item.check_id.removeprefix("governance:")
        for item in inspection.items
        if item.state is AdoptionState.MISSING
    }
    safe_planned_files = tuple(
        item
        for item in adoption.planned_files
        if _scaffold_area(item.relative_path) in missing_areas
    )
    adoption = ExistingRepositoryAdoption(
        root=adoption.root,
        planned_files=safe_planned_files,
        preserved_files=adoption.preserved_files,
        dry_run=True,
    )
    return OnboardingPlan(
        root=root.resolve(),
        project_name=project_name,
        diagnosis=diagnosis,
        adoption=adoption,
    )


def render_onboarding_plan_json(
    plan: OnboardingPlan,
    *,
    non_interactive: bool,
) -> str:
    payload = {
        "contract_version": ONBOARDING_PLAN_VERSION,
        "repository": str(plan.root),
        "mode": "dry_run",
        "interaction": "non_interactive" if non_interactive else "no_prompt",
        "project_name": plan.project_name,
        "diagnosis": {
            "summary": {
                status.value: plan.diagnosis.count(status)
                for status in DoctorStatus
            },
            "findings": [
                {
                    "status": finding.status.value,
                    "check_id": finding.check_id,
                    "message": finding.message,
                    "classification": finding.classification,
                }
                for finding in plan.diagnosis.findings
            ],
        },
        "plan": {
            "create": [
                item.relative_path.as_posix()
                for item in plan.adoption.planned_files
            ],
            "preserve": [
                path.as_posix() for path in plan.adoption.preserved_files
            ],
        },
        "next_action": (
            "review the exact target and planned files; this dry-run does not "
            "authorize a later write"
        ),
        "authority_boundary": {
            "modifies_repository": False,
            "write_authorized": False,
            "repairs_project_environment": False,
            "installs_project_dependencies": False,
            "authorizes_git_or_release_operations": False,
        },
    }
    return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"


def apply_onboarding_plan(plan: OnboardingPlan) -> OnboardingResult:
    """Create exactly the reviewed files after a complete conflict preflight."""

    for generated_file in plan.adoption.planned_files:
        destination = plan.root / generated_file.relative_path
        current = plan.root
        for part in generated_file.relative_path.parts[:-1]:
            current = current / part
            if current.is_symlink():
                raise OnboardingConflictError(
                    "parent path became a symbolic link after preview: "
                    f"{current.relative_to(plan.root).as_posix()}"
                )
            if current.exists() and not current.is_dir():
                raise OnboardingConflictError(
                    "parent path became a non-directory after preview: "
                    f"{current.relative_to(plan.root).as_posix()}"
                )
        if destination.exists() or destination.is_symlink():
            raise OnboardingConflictError(
                "planned target appeared after preview and was not overwritten: "
                f"{generated_file.relative_path.as_posix()}"
            )

    created: list[Path] = []
    for generated_file in plan.adoption.planned_files:
        destination = plan.root / generated_file.relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        try:
            with destination.open("x", encoding="utf-8", newline="") as handle:
                handle.write(generated_file.content)
        except FileExistsError as exc:
            raise OnboardingConflictError(
                "planned target appeared during adoption and was not overwritten: "
                f"{generated_file.relative_path.as_posix()}"
            ) from exc
        created.append(generated_file.relative_path)

    return OnboardingResult(
        root=plan.root,
        created_files=tuple(created),
        preserved_files=plan.adoption.preserved_files,
    )


def request_onboarding_confirmation(
    plan: OnboardingPlan,
    *,
    decision_reader: Callable[[str], str],
    is_interactive_terminal: bool,
) -> bool:
    """Return write authority only for an exact decision from a real terminal."""

    if not is_interactive_terminal:
        return False
    decision = decision_reader(
        f'Type ADOPT to create {len(plan.adoption.planned_files)} file(s) '
        f'in "{plan.root}": '
    )
    return decision == "ADOPT"
