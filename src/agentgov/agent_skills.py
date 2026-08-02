"""Deterministic checks for repository-native agent operating protocols."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path


_NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_FRONTMATTER_KEY_RE = re.compile(r"^([a-z_]+):(?:\s*(.*))?$")
_REQUIRED_FRONTMATTER = {"name", "description"}
_ALLOWED_FRONTMATTER = _REQUIRED_FRONTMATTER | {
    "triggers",
    "non_triggers",
    "applies_to",
}
_ROUTING_FIELDS = ("triggers", "non_triggers", "applies_to")
_ROUTING_VALUE_RE = re.compile(r"^[a-z][a-z0-9_.:-]*$")
_REQUIRED_HEADINGS = (
    "## Goal",
    "## Required context",
    "## Inputs",
    "## Workflow",
    "## Required checks",
    "## Stop conditions",
    "## Human escalation",
    "## Expected output",
)


@dataclass(frozen=True)
class AgentSkillFinding:
    passed: bool
    check_id: str
    message: str


@dataclass(frozen=True)
class AgentSkillsReport:
    root: Path
    findings: tuple[AgentSkillFinding, ...]

    @property
    def has_failures(self) -> bool:
        return any(not finding.passed for finding in self.findings)


@dataclass(frozen=True)
class AgentSkillMetadata:
    name: str
    description: str
    triggers: tuple[str, ...]
    non_triggers: tuple[str, ...]
    applies_to: tuple[str, ...]


def _parse_frontmatter(text: str) -> tuple[dict[str, str], str, list[str]]:
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        return {}, text, ["SKILL.md must start with YAML frontmatter"]

    try:
        closing_index = lines.index("---", 1)
    except ValueError:
        return {}, text, ["YAML frontmatter is missing its closing delimiter"]

    fields: dict[str, str] = {}
    errors: list[str] = []
    index = 1
    while index < closing_index:
        line = lines[index]
        match = _FRONTMATTER_KEY_RE.fullmatch(line)
        if not match:
            errors.append(f"unsupported frontmatter syntax on line {index + 1}")
            index += 1
            continue

        key, raw_value = match.groups()
        if key in fields:
            errors.append(f"frontmatter field {key!r} must appear once")
            index += 1
            continue

        if raw_value in {"|", ">"}:
            block: list[str] = []
            index += 1
            while index < closing_index and (
                lines[index].startswith(" ") or not lines[index]
            ):
                block.append(lines[index].strip())
                index += 1
            fields[key] = " ".join(part for part in block if part)
            continue

        fields[key] = (raw_value or "").strip().strip('"').strip("'")
        index += 1

    return fields, "\n".join(lines[closing_index + 1 :]), errors


def _routing_values(
    fields: dict[str, str],
    key: str,
    errors: list[str],
) -> tuple[str, ...]:
    if key not in fields:
        return ()
    try:
        value = json.loads(fields[key])
    except json.JSONDecodeError:
        errors.append(f"frontmatter {key} must be an inline JSON string array")
        return ()
    if not isinstance(value, list) or any(
        not isinstance(item, str) or not item for item in value
    ):
        errors.append(f"frontmatter {key} must contain only non-empty strings")
        return ()
    if len(set(value)) != len(value):
        errors.append(f"frontmatter {key} must contain unique items")
    for item in value:
        if not _ROUTING_VALUE_RE.fullmatch(item):
            errors.append(
                f"frontmatter {key} value {item!r} must use a portable routing identifier"
            )
    return tuple(value)


def read_agent_skill_metadata(path: Path) -> AgentSkillMetadata:
    """Read validated artifact-owned routing metadata for one skill."""

    errors = validate_agent_skill(path)
    if errors:
        raise ValueError("; ".join(errors))
    fields, _, _ = _parse_frontmatter(path.read_text(encoding="utf-8"))
    routing_errors: list[str] = []
    values = {
        key: _routing_values(fields, key, routing_errors) for key in _ROUTING_FIELDS
    }
    if routing_errors:
        raise ValueError("; ".join(routing_errors))
    return AgentSkillMetadata(
        name=fields["name"],
        description=fields["description"],
        triggers=values["triggers"],
        non_triggers=values["non_triggers"],
        applies_to=values["applies_to"],
    )


def validate_agent_skill(path: Path) -> list[str]:
    """Return contract errors for one SKILL.md path."""

    errors: list[str] = []
    if path.is_symlink():
        return ["SKILL.md must not be a symbolic link"]
    if not path.is_file():
        return ["SKILL.md is missing"]

    text = path.read_text(encoding="utf-8")
    fields, body, parse_errors = _parse_frontmatter(text)
    errors.extend(parse_errors)

    extra_fields = sorted(set(fields) - _ALLOWED_FRONTMATTER)
    if extra_fields:
        errors.append(
            "frontmatter contains unsupported field(s): " + ", ".join(extra_fields)
        )
    missing_fields = sorted(_REQUIRED_FRONTMATTER - set(fields))
    if missing_fields:
        errors.append("frontmatter is missing field(s): " + ", ".join(missing_fields))

    skill_name = fields.get("name", "")
    if skill_name and not _NAME_RE.fullmatch(skill_name):
        errors.append("frontmatter name must use lowercase kebab-case")
    if skill_name and skill_name != path.parent.name:
        errors.append("frontmatter name must match the skill directory name")

    description = fields.get("description", "")
    if description:
        if "use when" not in description.lower():
            errors.append("description must state when to use the skill")
        if "do not use" not in description.lower():
            errors.append("description must state when not to use the skill")

    routing = {
        key: _routing_values(fields, key, errors) for key in _ROUTING_FIELDS
    }
    routing_declared = any(key in fields for key in _ROUTING_FIELDS)
    if routing_declared:
        missing_routing = sorted(set(_ROUTING_FIELDS) - set(fields))
        if missing_routing:
            errors.append(
                "routable skill frontmatter is missing field(s): "
                + ", ".join(missing_routing)
            )
        if not routing["triggers"]:
            errors.append("routable skill frontmatter must declare at least one trigger")
        if not routing["applies_to"]:
            errors.append("routable skill frontmatter must declare at least one applies_to value")

    for heading in _REQUIRED_HEADINGS:
        if heading not in body.splitlines():
            errors.append(f"body is missing required heading: {heading}")
    return errors


def check_agent_skills(root: Path) -> AgentSkillsReport:
    """Validate every direct child skill without following symbolic links."""

    if root.is_symlink():
        raise ValueError(f"agent-skills path must not be a symbolic link: {root}")
    if not root.exists():
        raise FileNotFoundError(root)
    if not root.is_dir():
        raise ValueError(f"agent-skills path is not a directory: {root}")

    skill_directories = sorted(
        (path for path in root.iterdir() if path.name != "__pycache__" and path.is_dir()),
        key=lambda path: path.name,
    )
    if not skill_directories:
        return AgentSkillsReport(
            root=root,
            findings=(
                AgentSkillFinding(False, "agent-skills:directory", "no agent skills found"),
            ),
        )

    findings: list[AgentSkillFinding] = []
    for directory in skill_directories:
        check_id = f"agent-skill:{directory.name}"
        if directory.is_symlink():
            findings.append(
                AgentSkillFinding(False, check_id, "skill directory must not be a symbolic link")
            )
            continue
        errors = validate_agent_skill(directory / "SKILL.md")
        if errors:
            findings.append(AgentSkillFinding(False, check_id, "; ".join(errors)))
        else:
            findings.append(
                AgentSkillFinding(True, check_id, "SKILL.md satisfies the agent-skill contract")
            )
    return AgentSkillsReport(root=root, findings=tuple(findings))
