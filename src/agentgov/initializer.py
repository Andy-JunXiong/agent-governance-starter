"""Safe project scaffolding from the reviewed governance templates."""

from __future__ import annotations

import re
import sysconfig
from dataclasses import dataclass
from pathlib import Path


_ASSET_OUTPUTS = {
    Path("templates/AGENTS.template.md"): Path("AGENTS.md"),
    Path("templates/ADR.template.md"): Path("docs/adr/TEMPLATE.md"),
    Path("templates/INVARIANTS.template.md"): Path("docs/adr/INVARIANTS.md"),
    Path("templates/prompt-capability.template.json"): Path(
        "governance/capabilities/example-capability.json"
    ),
    Path("governance/capability.schema.json"): Path(
        "governance/capability.schema.json"
    ),
    Path("templates/example-capability.input.schema.template.json"): Path(
        "governance/contracts/example-capability.input.schema.json"
    ),
    Path("templates/example-capability.output.schema.template.json"): Path(
        "governance/contracts/example-capability.output.schema.json"
    ),
    Path("templates/prompt-source.template.md"): Path(
        "governance/evidence/example-capability.md"
    ),
    Path("templates/evaluation-manifest.template.json"): Path(
        "evaluation/example-capability/evaluation-manifest.json"
    ),
    Path("evaluation/readiness-policy.md"): Path("evaluation/readiness-policy.md"),
    Path("evaluation/schemas/evaluation-manifest.schema.json"): Path(
        "evaluation/schemas/evaluation-manifest.schema.json"
    ),
    Path("evaluation/schemas/seed-case.schema.json"): Path(
        "evaluation/schemas/seed-case.schema.json"
    ),
    Path("evaluation/schemas/golden-example.schema.json"): Path(
        "evaluation/schemas/golden-example.schema.json"
    ),
    Path("evaluation/schemas/failure-case.schema.json"): Path(
        "evaluation/schemas/failure-case.schema.json"
    ),
    Path("agent-skills/README.md"): Path("agent-skills/README.md"),
    Path("agent-skills/context-first-review/SKILL.md"): Path(
        "agent-skills/context-first-review/SKILL.md"
    ),
    Path("agent-skills/development-slice/SKILL.md"): Path(
        "agent-skills/development-slice/SKILL.md"
    ),
    Path("agent-skills/incident-attribution/SKILL.md"): Path(
        "agent-skills/incident-attribution/SKILL.md"
    ),
    Path("agent-skills/incident-response/SKILL.md"): Path(
        "agent-skills/incident-response/SKILL.md"
    ),
}
_PLACEHOLDER_RE = re.compile(r"\{\{[A-Z][A-Z0-9_-]*\}\}")


class InitConflictError(Exception):
    """Raised when initialization would overwrite or mix with existing files."""


@dataclass(frozen=True)
class InitFile:
    relative_path: Path
    content: str


@dataclass(frozen=True)
class InitReport:
    target: Path
    files: tuple[InitFile, ...]
    unresolved_placeholders: tuple[str, ...]
    dry_run: bool


def _asset_root() -> Path:
    source_checkout = Path(__file__).resolve().parents[2]
    if (
        (source_checkout / "templates").is_dir()
        and (source_checkout / "evaluation").is_dir()
        and (source_checkout / "agent-skills").is_dir()
    ):
        return source_checkout

    installed = (
        Path(sysconfig.get_path("data"))
        / "share"
        / "agent-governance-starter"
    )
    if (
        (installed / "templates").is_dir()
        and (installed / "evaluation").is_dir()
        and (installed / "agent-skills").is_dir()
    ):
        return installed

    raise FileNotFoundError("governance adoption assets are not installed")


def _validate_project_name(project_name: str) -> str:
    normalized = project_name.strip()
    if not normalized:
        raise ValueError("project name must not be empty")
    if len(normalized) > 100:
        raise ValueError("project name must not exceed 100 characters")
    if any(character in normalized for character in ("\r", "\n")):
        raise ValueError("project name must be a single line")
    if "{{" in normalized or "}}" in normalized:
        raise ValueError("project name must not contain template delimiters")
    return normalized


def build_scaffold_files(project_name: str) -> tuple[InitFile, ...]:
    """Build the reviewed scaffold files without writing them."""

    project_name = _validate_project_name(project_name)
    asset_root = _asset_root()
    files: list[InitFile] = []
    for asset_path, output_path in _ASSET_OUTPUTS.items():
        content = (asset_root / asset_path).read_text(encoding="utf-8")
        content = content.replace("{{PROJECT_NAME}}", project_name)
        files.append(InitFile(relative_path=output_path, content=content))
    return tuple(files)


def _assert_safe_target(target: Path) -> None:
    if target.is_symlink():
        raise InitConflictError(f"target must not be a symbolic link: {target}")
    if target.exists() and not target.is_dir():
        raise InitConflictError(f"target is not a directory: {target}")
    if target.is_dir() and next(target.iterdir(), None) is not None:
        raise InitConflictError(f"target directory is not empty: {target}")


def initialize_project(
    target: Path,
    *,
    project_name: str,
    dry_run: bool = False,
) -> InitReport:
    """Plan or write a governance scaffold without overwriting existing files."""

    _assert_safe_target(target)
    files = build_scaffold_files(project_name)
    placeholders = tuple(
        sorted(
            {
                placeholder
                for generated_file in files
                for placeholder in _PLACEHOLDER_RE.findall(generated_file.content)
            }
        )
    )

    if not dry_run:
        target.mkdir(parents=True, exist_ok=True)
        for generated_file in files:
            destination = target / generated_file.relative_path
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(generated_file.content, encoding="utf-8")

    return InitReport(
        target=target,
        files=files,
        unresolved_placeholders=placeholders,
        dry_run=dry_run,
    )
