"""Read-only inspection for adopting governance in an existing repository."""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from agentgov import __version__
from agentgov.initializer import InitFile, build_scaffold_files


class AdoptionState(str, Enum):
    PRESENT = "PRESENT"
    MISSING = "MISSING"
    DISCOVERED = "DISCOVERED"
    CONFLICT = "CONFLICT"


@dataclass(frozen=True)
class AdoptionItem:
    state: AdoptionState
    check_id: str
    path: Path
    message: str


@dataclass(frozen=True)
class AdoptionReport:
    root: Path
    items: tuple[AdoptionItem, ...]
    recommendations: tuple[str, ...]

    def count(self, state: AdoptionState) -> int:
        return sum(item.state is state for item in self.items)

    @property
    def has_conflicts(self) -> bool:
        return any(item.state is AdoptionState.CONFLICT for item in self.items)


class AdoptionConflictError(Exception):
    """Raised when existing repository paths make safe adoption impossible."""


@dataclass(frozen=True)
class ExistingRepositoryAdoption:
    root: Path
    planned_files: tuple[InitFile, ...]
    preserved_files: tuple[Path, ...]
    dry_run: bool


ADOPTION_REPORT_VERSION = "1.0"

_GOVERNANCE_PATHS = (
    ("constitution", Path("AGENTS.md"), "file"),
    ("adr-template", Path("docs/adr/TEMPLATE.md"), "file"),
    ("invariants", Path("docs/adr/INVARIANTS.md"), "file"),
    ("capabilities", Path("governance/capabilities"), "directory"),
    ("evaluation", Path("evaluation"), "directory"),
    ("agent-skills", Path("agent-skills"), "directory"),
)

_INSTRUCTION_PATHS = (
    Path("CLAUDE.md"),
    Path("GEMINI.md"),
    Path(".github/copilot-instructions.md"),
    Path(".cursor/rules"),
    Path(".cursorrules"),
    Path(".windsurfrules"),
)


def inspect_adoption(root: Path) -> AdoptionReport:
    """Inspect adoption signals without creating or modifying repository files."""

    if root.is_symlink():
        raise ValueError(f"repository path must not be a symbolic link: {root}")
    if not root.exists():
        raise FileNotFoundError(root)
    if not root.is_dir():
        raise ValueError(f"repository path is not a directory: {root}")

    items: list[AdoptionItem] = []
    for check_id, relative_path, expected_type in _GOVERNANCE_PATHS:
        path = root / relative_path
        if path.is_symlink():
            state = AdoptionState.CONFLICT
            detail = "is a symbolic link and requires human resolution"
        elif not path.exists():
            state = AdoptionState.MISSING
            detail = "is not configured"
        elif (expected_type == "file" and path.is_file()) or (
            expected_type == "directory" and path.is_dir()
        ):
            state = AdoptionState.PRESENT
            detail = "already exists and must be preserved"
        else:
            state = AdoptionState.CONFLICT
            detail = f"exists but is not the expected {expected_type}"
        items.append(
            AdoptionItem(
                state,
                f"governance:{check_id}",
                relative_path,
                f"{relative_path.as_posix()} {detail}",
            )
        )

    discovered: list[Path] = []
    for relative_path in _INSTRUCTION_PATHS:
        path = root / relative_path
        if path.exists() or path.is_symlink():
            discovered.append(relative_path)
            items.append(
                AdoptionItem(
                    AdoptionState.DISCOVERED,
                    "instruction:existing",
                    relative_path,
                    f"review {relative_path.as_posix()} before adapting governance policy",
                )
            )

    missing = [item.path for item in items if item.state is AdoptionState.MISSING]
    conflicts = [item.path for item in items if item.state is AdoptionState.CONFLICT]
    recommendations: list[str] = []
    if conflicts:
        recommendations.append(
            "resolve governance path type or symbolic-link conflicts before adoption"
        )
    if discovered:
        recommendations.append(
            "review discovered instruction files for compatible authority, review, and "
            "escalation boundaries; do not merge their text automatically"
        )
    if missing:
        recommendations.append(
            "adapt only the missing governance paths from the starter templates in a "
            "separate reviewable change"
        )
    else:
        recommendations.append(
            "run `agentgov check repository` to validate the configured governance contracts"
        )
    recommendations.append(
        "keep merge, publish, release, and deploy as separate human-authorized actions"
    )

    return AdoptionReport(root, tuple(items), tuple(recommendations))


def render_adoption_report_json(report: AdoptionReport) -> str:
    """Render the read-only adoption report as deterministic JSON v1.0."""

    payload = {
        "contract_version": ADOPTION_REPORT_VERSION,
        "tool": {"name": "agentgov", "version": __version__},
        "repository": str(report.root),
        "mode": "read_only",
        "summary": {
            state.value: report.count(state) for state in AdoptionState
        },
        "items": [
            {
                "state": item.state.value,
                "check_id": item.check_id,
                "path": item.path.as_posix(),
                "message": item.message,
                "classification": "deterministic",
            }
            for item in report.items
        ],
        "recommended_steps": list(report.recommendations),
        "human_decisions": [
            "decide how existing instruction files relate to repository governance",
            "review every proposed governance file before any later write operation",
        ],
        "authority_boundary": {
            "inspection_modifies_repository": False,
            "authorizes_merge_publish_release_or_deploy": False,
        },
    }
    return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"


def adopt_existing_repository(
    root: Path,
    *,
    project_name: str,
    dry_run: bool,
) -> ExistingRepositoryAdoption:
    """Create only missing scaffold files after a complete conflict preflight."""

    inspection = inspect_adoption(root)
    if inspection.has_conflicts:
        paths = ", ".join(
            item.path.as_posix()
            for item in inspection.items
            if item.state is AdoptionState.CONFLICT
        )
        raise AdoptionConflictError(f"resolve adoption conflicts first: {paths}")

    files = build_scaffold_files(project_name)
    planned: list[InitFile] = []
    preserved: list[Path] = []
    for generated_file in files:
        destination = root / generated_file.relative_path
        current = root
        for part in generated_file.relative_path.parts[:-1]:
            current = current / part
            if current.is_symlink():
                raise AdoptionConflictError(
                    f"parent path must not be a symbolic link: {current.relative_to(root).as_posix()}"
                )
            if current.exists() and not current.is_dir():
                raise AdoptionConflictError(
                    f"parent path is not a directory: {current.relative_to(root).as_posix()}"
                )
        if destination.is_symlink() or destination.is_dir():
            raise AdoptionConflictError(
                f"target is not a safe regular file: {generated_file.relative_path.as_posix()}"
            )
        if destination.is_file():
            preserved.append(generated_file.relative_path)
        else:
            planned.append(generated_file)

    if not dry_run:
        for generated_file in planned:
            destination = root / generated_file.relative_path
            destination.parent.mkdir(parents=True, exist_ok=True)
            try:
                with destination.open("x", encoding="utf-8", newline="") as handle:
                    handle.write(generated_file.content)
            except FileExistsError as exc:
                raise AdoptionConflictError(
                    f"target appeared during adoption and was not overwritten: "
                    f"{generated_file.relative_path.as_posix()}"
                ) from exc

    return ExistingRepositoryAdoption(
        root=root,
        planned_files=tuple(planned),
        preserved_files=tuple(preserved),
        dry_run=dry_run,
    )
