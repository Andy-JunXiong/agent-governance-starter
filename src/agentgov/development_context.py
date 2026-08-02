"""Read-only, task-specific governance context selection."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Mapping

from agentgov.agent_skills import read_agent_skill_metadata
from agentgov.capability import load_capability_manifest, validate_capability_manifest
from agentgov.controls import validate_control_mapping_document
from agentgov.dependencies import validate_dependency_document
from agentgov.path_policy import scope_intersects_reference
from agentgov.task_contract import (
    canonical_task_digest,
    check_development_task,
    load_development_task,
)


CONTEXT_CONTRACT = "agentgov.development-context"
CONTEXT_SCHEMA_VERSION = "1.0"

_ADR_NAME_RE = re.compile(r"^[0-9]{4}-.+\.md$")
_SELECTION_PRIORITY = {
    "required": 0,
    "declared": 1,
    "path_match": 2,
    "capability_link": 3,
    "advisory_candidate": 4,
}


class ContextPolicyError(ValueError):
    """A deterministic contract fact prevents truthful context selection."""


@dataclass(frozen=True)
class SelectedGovernance:
    artifact_type: str
    path: str
    roles: tuple[str, ...]
    selection_mode: str
    classification: str
    reason: str
    source_hash: str
    content: str


@dataclass(frozen=True)
class DevelopmentContext:
    contract: str
    schema_version: str
    task_id: str
    task_profile: str
    task_path: str
    task_digest: str
    active_triggers: tuple[str, ...]
    registry_summary: Mapping[str, int]
    selected_governance: tuple[SelectedGovernance, ...]
    known_limits: tuple[str, ...]
    authority_boundary: Mapping[str, bool]


def _safe_root(repository: Path) -> Path:
    if repository.is_symlink():
        raise ValueError("repository root must not be a symbolic link")
    if not repository.exists():
        raise FileNotFoundError(repository)
    if not repository.is_dir():
        raise ValueError("repository root must be a directory")
    return repository.resolve()


def _relative_path(root: Path, path: Path) -> str:
    resolved = path.resolve(strict=False)
    try:
        relative = resolved.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"path must stay within repository root: {path}") from exc
    cursor = path
    while True:
        if cursor.is_symlink():
            raise ValueError(f"governance artifact must not use a symbolic link: {path}")
        if cursor.resolve(strict=False) == root or cursor.parent == cursor:
            break
        cursor = cursor.parent
    return relative.as_posix()


def _reference_path(reference: str) -> str:
    return reference.split("#", 1)[0]


def _path_from_relative(root: Path, relative: str) -> Path:
    pure = PurePosixPath(relative)
    if pure.is_absolute() or relative in {"", "."} or ".." in pure.parts:
        raise ValueError(f"unsafe repository-relative path: {relative}")
    path = root.joinpath(*pure.parts)
    _relative_path(root, path)
    return path


def _hash_bytes(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def _source(path: Path) -> tuple[str, str]:
    if not path.is_file():
        raise FileNotFoundError(path)
    raw = path.read_bytes()
    return _hash_bytes(raw), raw.decode("utf-8")


def _artifact_type(path: str, role: str) -> str:
    pure = PurePosixPath(path)
    if pure.name == "AGENTS.md":
        return "constitution"
    if pure.name == "INVARIANTS.md":
        return "invariant"
    if "adr" in pure.parts and _ADR_NAME_RE.fullmatch(pure.name):
        return "decision"
    return {
        "requirement": "requirement",
        "parent_objective": "objective",
        "architecture": "architecture_overview",
        "approval_evidence": "approval_evidence",
    }.get(role, role)


def _registry_summary(root: Path) -> dict[str, int]:
    candidates: dict[str, list[Path]] = {
        "constitution": [root / "AGENTS.md"],
        "task": list((root / "governance" / "tasks").glob("*.json")),
        "architecture_overview": [root / "AI_CONTEXT.md", root / "docs" / "AI_CONTEXT.md"],
        "decision": list((root / "docs" / "adr").glob("[0-9][0-9][0-9][0-9]-*.md")),
        "invariant": [root / "docs" / "adr" / "INVARIANTS.md"],
        "skill": list((root / "agent-skills").glob("*/SKILL.md")),
        "capability": list((root / "governance" / "capabilities").glob("*.json")),
        "control": list((root / "governance" / "controls").glob("*.json")),
        "dependency": list((root / "governance" / "dependencies").glob("*.json")),
        "evaluation": [
            path
            for path in (root / "evaluation").glob("*/evaluation-manifest.json")
            if "fixtures" not in path.relative_to(root / "evaluation").parts
        ],
    }
    return {
        artifact_type: sum(path.is_file() and not path.is_symlink() for path in paths)
        for artifact_type, paths in sorted(candidates.items())
    }


def _manifest_paths(document: Mapping[str, Any]) -> tuple[str, ...]:
    paths: list[str] = []
    for value in document.get("called_by", []):
        if isinstance(value, str):
            paths.append(_reference_path(value))
    contracts = document.get("contracts", {})
    if isinstance(contracts, Mapping):
        paths.extend(value for value in contracts.values() if isinstance(value, str))
    for section, field in (("evaluation", "evidence_refs"), ("provenance", "source_refs")):
        value = document.get(section, {})
        if isinstance(value, Mapping):
            paths.extend(
                _reference_path(item)
                for item in value.get(field, [])
                if isinstance(item, str)
            )
    return tuple(sorted(set(paths)))


def select_development_context(
    task_path: Path,
    *,
    repository: Path,
) -> DevelopmentContext:
    """Select governance for one admitted task without modifying the repository."""

    root = _safe_root(repository)
    report = check_development_task(task_path, repository=root)
    if report.has_failures:
        messages = "; ".join(item.message for item in report.findings)
        raise ContextPolicyError(f"task contract is not eligible for context: {messages}")

    document = load_development_task(report.path)
    decision = document["decision"]
    assert isinstance(decision, Mapping)
    if decision["state"] != "admitted":
        raise ContextPolicyError(
            f"task decision state is {decision['state']!r}; context requires an admitted task"
        )

    task_id = str(document["task_id"])
    task_profile = str(document["profile"])
    task_relative = _relative_path(root, report.path)
    active_triggers = ["task.admitted"]
    architecture_refs = list(document.get("architecture_refs", []))
    if architecture_refs:
        active_triggers.append("architecture.candidate")

    builders: dict[str, dict[str, Any]] = {}

    def add(
        path: Path,
        *,
        artifact_type: str,
        role: str,
        mode: str,
        classification: str,
        reason: str,
    ) -> None:
        relative = _relative_path(root, path)
        source_hash, content = _source(path)
        existing = builders.get(relative)
        if existing is None:
            builders[relative] = {
                "artifact_type": artifact_type,
                "path": relative,
                "roles": {role},
                "selection_mode": mode,
                "classification": classification,
                "reasons": {reason},
                "source_hash": source_hash,
                "content": content,
            }
            return
        existing["roles"].add(role)
        existing["reasons"].add(reason)
        if _SELECTION_PRIORITY[mode] < _SELECTION_PRIORITY[existing["selection_mode"]]:
            existing["selection_mode"] = mode
        if classification == "deterministic":
            existing["classification"] = "deterministic"
        if artifact_type in {"decision", "invariant", "constitution"}:
            existing["artifact_type"] = artifact_type

    add(
        root / "AGENTS.md",
        artifact_type="constitution",
        role="repository_authority",
        mode="required",
        classification="deterministic",
        reason="root AGENTS.md is required for every development task",
    )
    add(
        report.path,
        artifact_type="task",
        role="current_task",
        mode="required",
        classification="deterministic",
        reason="this is the admitted task used for context selection",
    )

    reference_groups = (
        ("requirement", document["requirement"]["source_refs"]),
        ("parent_objective", document.get("objective", {}).get("parent_refs", [])),
        ("architecture", architecture_refs),
        ("approval_evidence", document.get("approval", {}).get("evidence_refs", [])),
    )
    for role, references in reference_groups:
        for reference in references:
            relative = _reference_path(str(reference))
            add(
                _path_from_relative(root, relative),
                artifact_type=_artifact_type(relative, role),
                role=role,
                mode="declared",
                classification="deterministic",
                reason=f"task explicitly declares this {role.replace('_', ' ')} reference",
            )

    if architecture_refs:
        for relative in ("AI_CONTEXT.md", "docs/AI_CONTEXT.md"):
            candidate = _path_from_relative(root, relative)
            if candidate.is_file():
                add(
                    candidate,
                    artifact_type="architecture_overview",
                    role="architecture_navigation",
                    mode="required",
                    classification="deterministic",
                    reason="an admitted task with architecture references receives the conventional architecture overview",
                )

    skills_root = root / "agent-skills"
    if skills_root.is_dir() and not skills_root.is_symlink():
        for skill_path in sorted(skills_root.glob("*/SKILL.md")):
            metadata = read_agent_skill_metadata(skill_path)
            if "development_task" not in metadata.applies_to:
                continue
            if set(metadata.non_triggers) & set(active_triggers):
                continue
            matched = sorted(set(metadata.triggers) & set(active_triggers))
            if not matched:
                continue
            advisory = matched == ["architecture.candidate"]
            add(
                skill_path,
                artifact_type="skill",
                role="agent_protocol",
                mode="advisory_candidate" if advisory else "required",
                classification="advisory" if advisory else "deterministic",
                reason=f"SKILL.md owns matching trigger(s): {', '.join(matched)}",
            )

    scope = document["scope"]
    includes = tuple(scope["include_paths"])
    excludes = tuple(scope["exclude_paths"])
    capabilities_root = root / "governance" / "capabilities"
    for manifest_path in sorted(capabilities_root.glob("*.json")):
        manifest = load_capability_manifest(manifest_path)
        manifest_errors = validate_capability_manifest(manifest)
        if manifest_errors:
            raise ContextPolicyError(
                f"capability manifest is invalid: {_relative_path(root, manifest_path)}: "
                + "; ".join(manifest_errors)
            )
        declared_paths = _manifest_paths(manifest)
        matched_paths = [
            path
            for path in declared_paths
            if scope_intersects_reference(
                path,
                includes=includes,
                excludes=excludes,
            )
        ]
        if not matched_paths:
            continue
        capability_name = manifest.get("name")
        if not isinstance(capability_name, str) or not capability_name:
            raise ContextPolicyError(f"capability manifest has no valid name: {manifest_path}")
        add(
            manifest_path,
            artifact_type="capability",
            role="capability_governance",
            mode="path_match",
            classification="deterministic",
            reason="task scope overlaps artifact-declared path(s): " + ", ".join(matched_paths),
        )
        for directory, artifact_type in (("controls", "control"), ("dependencies", "dependency")):
            linked = root / "governance" / directory / f"{capability_name}.json"
            if linked.is_file():
                linked_document = json.loads(linked.read_text(encoding="utf-8"))
                if not isinstance(linked_document, Mapping):
                    raise ContextPolicyError(
                        f"linked {artifact_type} root must be an object: {_relative_path(root, linked)}"
                    )
                linked_errors = (
                    validate_control_mapping_document(linked_document)
                    if artifact_type == "control"
                    else validate_dependency_document(linked_document)
                )
                if linked_errors:
                    raise ContextPolicyError(
                        f"linked {artifact_type} is invalid: {_relative_path(root, linked)}: "
                        + "; ".join(linked_errors)
                    )
                add(
                    linked,
                    artifact_type=artifact_type,
                    role=f"{capability_name}_{artifact_type}",
                    mode="capability_link",
                    classification="deterministic",
                    reason=f"selected capability {capability_name!r} declares this linked governance surface",
                )
        evaluation = root / "evaluation" / capability_name / "evaluation-manifest.json"
        if evaluation.is_file():
            add(
                evaluation,
                artifact_type="evaluation",
                role=f"{capability_name}_evaluation",
                mode="capability_link",
                classification="deterministic",
                reason=f"selected capability {capability_name!r} has a configured evaluation manifest",
            )

    selected = tuple(
        SelectedGovernance(
            artifact_type=value["artifact_type"],
            path=value["path"],
            roles=tuple(sorted(value["roles"])),
            selection_mode=value["selection_mode"],
            classification=value["classification"],
            reason="; ".join(sorted(value["reasons"])),
            source_hash=value["source_hash"],
            content=value["content"],
        )
        for _, value in sorted(builders.items())
    )
    return DevelopmentContext(
        contract=CONTEXT_CONTRACT,
        schema_version=CONTEXT_SCHEMA_VERSION,
        task_id=task_id,
        task_profile=task_profile,
        task_path=task_relative,
        task_digest=canonical_task_digest(document),
        active_triggers=tuple(active_triggers),
        registry_summary=_registry_summary(root),
        selected_governance=selected,
        known_limits=(
            "selection proves declared references and path relationships, not architecture sufficiency",
            "architecture candidates remain advisory",
            "scope, fresh evidence, events, and completion are separate contracts selected by the guided govern workflow",
            "one coding-agent consumption run cannot establish general effectiveness",
        ),
        authority_boundary={
            "writes_repository": False,
            "modifies_git": False,
            "authorizes_implementation": False,
            "authorizes_commit": False,
            "authorizes_merge": False,
            "authorizes_release": False,
            "authorizes_deploy": False,
        },
    )


def render_development_context_json(
    context: DevelopmentContext,
    *,
    include_content: bool = False,
) -> str:
    """Render deterministic machine-readable task context."""

    payload = asdict(context)
    payload["content_mode"] = "embedded" if include_content else "references"
    for item in payload["selected_governance"]:
        item["content_included"] = include_content
        if not include_content:
            item["content"] = None
    return json.dumps(
        payload,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    ) + "\n"


def render_development_context_markdown(
    context: DevelopmentContext,
    *,
    include_content: bool = False,
) -> str:
    """Render task context for a human or Markdown-capable coding agent."""

    lines = [
        f"# Development context: {context.task_id}",
        "",
        f"- Contract: `{context.contract}` `{context.schema_version}`",
        f"- Task: `{context.task_path}` (`{context.task_profile}`)",
        f"- Task digest: `{context.task_digest}`",
        f"- Active triggers: {', '.join(f'`{item}`' for item in context.active_triggers)}",
        f"- Content mode: `{'embedded' if include_content else 'references'}`",
        "",
        "## Selected governance",
        "",
    ]
    for item in context.selected_governance:
        lines.extend(
            [
                f"### `{item.path}`",
                "",
                f"- Type: `{item.artifact_type}`",
                f"- Roles: {', '.join(f'`{role}`' for role in item.roles)}",
                f"- Selection: `{item.selection_mode}` / `{item.classification}`",
                f"- Reason: {item.reason}",
                f"- Source: `{item.source_hash}`",
                "",
            ]
        )
        if include_content:
            lines.extend(
                [
                    "~~~~text",
                    item.content.rstrip("\n"),
                    "~~~~",
                    "",
                ]
            )
    if not include_content:
        lines.extend(
            [
                "Read the selected repository-relative paths before acting; content was not duplicated into this context output.",
                "",
            ]
        )
    lines.extend(["## Known limits", ""])
    lines.extend(f"- {item}" for item in context.known_limits)
    lines.extend(
        [
            "",
            "## Authority boundary",
            "",
            *(
                f"- `{key}`: `{str(value).lower()}`"
                for key, value in sorted(context.authority_boundary.items())
            ),
            "",
        ]
    )
    return "\n".join(lines)


def render_development_context_terminal(context: DevelopmentContext) -> str:
    """Render a concise terminal index without duplicating full content."""

    lines = [
        f"CONTEXT task={context.task_id} profile={context.task_profile}",
        "TRIGGERS " + ",".join(context.active_triggers),
    ]
    lines.extend(
        f"SELECT {item.selection_mode} {item.classification} {item.artifact_type}:{item.path} -- {item.reason}"
        for item in context.selected_governance
    )
    lines.append(
        "REGISTRY "
        + " ".join(f"{key}={value}" for key, value in sorted(context.registry_summary.items()))
    )
    lines.append(
        "NOTE context selection was read-only and did not authorize implementation or Git transitions"
    )
    return "\n".join(lines) + "\n"
