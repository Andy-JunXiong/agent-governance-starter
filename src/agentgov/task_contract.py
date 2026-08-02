"""Zero-dependency validation for development-time coding-agent task contracts."""

from __future__ import annotations

import json
import hashlib
import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path, PurePosixPath
from typing import Any, Mapping

from agentgov.path_policy import scope_path_error


TASK_CONTRACT = "agentgov.development-task"
TASK_SCHEMA_VERSION = "1.1"
TASK_PROFILES = {"compact", "standard"}
OBJECTIVE_ROLES = {"core", "supporting", "maintenance"}
RISK_LEVELS = {"low", "medium", "high", "critical"}
APPROVAL_STATUSES = {"not_required", "pending", "approved", "rejected"}
DECISION_STATES = {"draft", "admitted", "paused"}

_TASK_ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_WINDOWS_DRIVE_RE = re.compile(r"^[A-Za-z]:")


class TaskFindingStatus(str, Enum):
    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"
    ADVISORY = "ADVISORY"


@dataclass(frozen=True)
class TaskFinding:
    status: TaskFindingStatus
    check_id: str
    message: str


@dataclass(frozen=True)
class TaskReport:
    root: Path
    path: Path
    task_id: str
    findings: tuple[TaskFinding, ...]

    @property
    def has_failures(self) -> bool:
        return any(
            finding.status is TaskFindingStatus.FAIL for finding in self.findings
        )

    def count(self, status: TaskFindingStatus) -> int:
        return sum(finding.status is status for finding in self.findings)


def _mapping(value: Any, path: str, errors: list[str]) -> Mapping[str, Any] | None:
    if not isinstance(value, Mapping):
        errors.append(f"{path} must be an object")
        return None
    return value


def _fields(
    value: Mapping[str, Any],
    *,
    path: str,
    required: set[str],
    allowed: set[str],
    errors: list[str],
) -> None:
    for field in sorted(required - set(value)):
        errors.append(f"{path}.{field} is required")
    for field in sorted(set(value) - allowed):
        errors.append(f"{path}.{field} is not allowed")


def _string(
    value: Any,
    path: str,
    errors: list[str],
    *,
    minimum: int = 1,
) -> str | None:
    if not isinstance(value, str) or len(value.strip()) < minimum:
        errors.append(f"{path} must be a string with at least {minimum} characters")
        return None
    return value


def _string_list(
    value: Any,
    path: str,
    errors: list[str],
    *,
    minimum: int = 0,
) -> list[str] | None:
    if not isinstance(value, list):
        errors.append(f"{path} must be an array")
        return None
    if len(value) < minimum:
        errors.append(f"{path} must contain at least {minimum} item(s)")
    if any(not isinstance(item, str) or not item.strip() for item in value):
        errors.append(f"{path} must contain only non-empty strings")
        return None
    if len(set(value)) != len(value):
        errors.append(f"{path} must contain unique items")
    return value


def _enum(
    value: Any,
    path: str,
    allowed: set[str],
    errors: list[str],
) -> str | None:
    if not isinstance(value, str) or value not in allowed:
        errors.append(f"{path} must be one of {sorted(allowed)}")
        return None
    return value


def _scope_path(value: str, path: str, errors: list[str]) -> None:
    error = scope_path_error(value)
    if error:
        errors.append(f"{path} {error}")


def _scope_path_list(
    value: Any,
    path: str,
    errors: list[str],
    *,
    minimum: int = 0,
) -> list[str] | None:
    items = _string_list(value, path, errors, minimum=minimum)
    if items is not None:
        for index, item in enumerate(items):
            _scope_path(item, f"{path}[{index}]", errors)
    return items


def validate_development_task_document(document: Mapping[str, Any]) -> list[str]:
    """Return deterministic structural violations for one task contract."""

    errors: list[str] = []
    top_fields = {
        "contract",
        "schema_version",
        "profile",
        "task_id",
        "title",
        "requirement",
        "objective",
        "goal",
        "non_goals",
        "scope",
        "architecture_refs",
        "acceptance_signals",
        "validation_commands",
        "owner",
        "risk",
        "approval",
        "stop_conditions",
        "decision",
    }
    common_required = {
        "contract",
        "schema_version",
        "profile",
        "task_id",
        "title",
        "requirement",
        "scope",
        "acceptance_signals",
        "validation_commands",
        "owner",
        "risk",
        "decision",
    }
    profile = document.get("profile")
    required_fields = set(common_required)
    if profile == "standard":
        required_fields.update(
            {
                "objective",
                "goal",
                "non_goals",
                "architecture_refs",
                "approval",
                "stop_conditions",
            }
        )
    _fields(
        document,
        path="$",
        required=required_fields,
        allowed=top_fields,
        errors=errors,
    )
    if document.get("contract") != TASK_CONTRACT:
        errors.append(f"$.contract must equal {TASK_CONTRACT!r}")
    if document.get("schema_version") != TASK_SCHEMA_VERSION:
        errors.append(f"$.schema_version must equal {TASK_SCHEMA_VERSION!r}")
    profile_value = _enum(profile, "$.profile", TASK_PROFILES, errors)

    task_id = _string(document.get("task_id"), "$.task_id", errors)
    if task_id and not _TASK_ID_RE.fullmatch(task_id):
        errors.append("$.task_id must use kebab-case")
    _string(document.get("title"), "$.title", errors, minimum=5)

    requirement = _mapping(document.get("requirement"), "$.requirement", errors)
    if requirement is not None:
        fields = {"summary", "source_refs"}
        _fields(
            requirement,
            path="$.requirement",
            required=fields,
            allowed=fields,
            errors=errors,
        )
        _string(requirement.get("summary"), "$.requirement.summary", errors, minimum=10)
        _string_list(requirement.get("source_refs"), "$.requirement.source_refs", errors)

    objective = None
    if "objective" in document:
        objective = _mapping(document.get("objective"), "$.objective", errors)
    if objective is not None:
        fields = {"role", "parent_refs", "rationale"}
        _fields(
            objective,
            path="$.objective",
            required=fields,
            allowed=fields,
            errors=errors,
        )
        _enum(objective.get("role"), "$.objective.role", OBJECTIVE_ROLES, errors)
        _string_list(
            objective.get("parent_refs"),
            "$.objective.parent_refs",
            errors,
            minimum=1,
        )
        _string(objective.get("rationale"), "$.objective.rationale", errors, minimum=10)

    if "goal" in document:
        _string(document.get("goal"), "$.goal", errors, minimum=10)
    if "non_goals" in document:
        _string_list(document.get("non_goals"), "$.non_goals", errors, minimum=1)

    scope = _mapping(document.get("scope"), "$.scope", errors)
    if scope is not None:
        fields = {"include_paths", "exclude_paths"}
        _fields(
            scope,
            path="$.scope",
            required=fields,
            allowed=fields,
            errors=errors,
        )
        include_paths = _scope_path_list(
            scope.get("include_paths"),
            "$.scope.include_paths",
            errors,
            minimum=1,
        )
        exclude_paths = _scope_path_list(
            scope.get("exclude_paths"),
            "$.scope.exclude_paths",
            errors,
        )
        if include_paths is not None and exclude_paths is not None:
            overlap = sorted(set(include_paths) & set(exclude_paths))
            if overlap:
                errors.append(
                    "$.scope paths must not be both included and excluded: "
                    + ", ".join(repr(item) for item in overlap)
                )

    if "architecture_refs" in document:
        _string_list(document.get("architecture_refs"), "$.architecture_refs", errors)
    _string_list(
        document.get("acceptance_signals"),
        "$.acceptance_signals",
        errors,
        minimum=1,
    )
    _string_list(
        document.get("validation_commands"),
        "$.validation_commands",
        errors,
        minimum=1,
    )
    _string(document.get("owner"), "$.owner", errors)

    risk = _mapping(document.get("risk"), "$.risk", errors)
    risk_level: str | None = None
    if risk is not None:
        fields = {"level", "items"}
        _fields(risk, path="$.risk", required=fields, allowed=fields, errors=errors)
        risk_level = _enum(risk.get("level"), "$.risk.level", RISK_LEVELS, errors)
        risk_items = _string_list(risk.get("items"), "$.risk.items", errors)
        if risk_level in {"high", "critical"} and risk_items == []:
            errors.append(f"$.risk.items must not be empty for {risk_level} risk")
        if profile_value == "compact" and risk_level not in {None, "low"}:
            errors.append("$.risk.level must equal 'low' for compact tasks")

    approval = None
    if "approval" in document:
        approval = _mapping(document.get("approval"), "$.approval", errors)
    approval_required: bool | None = None
    approval_status: str | None = None
    if approval is not None:
        fields = {"required", "status", "owner", "evidence_refs"}
        _fields(
            approval,
            path="$.approval",
            required=fields,
            allowed=fields,
            errors=errors,
        )
        approval_required_value = approval.get("required")
        if not isinstance(approval_required_value, bool):
            errors.append("$.approval.required must be a boolean")
        else:
            approval_required = approval_required_value
        approval_status = _enum(
            approval.get("status"),
            "$.approval.status",
            APPROVAL_STATUSES,
            errors,
        )
        _string(approval.get("owner"), "$.approval.owner", errors)
        evidence_refs = _string_list(
            approval.get("evidence_refs"),
            "$.approval.evidence_refs",
            errors,
        )
        if approval_required is False:
            if approval_status != "not_required":
                errors.append(
                    "$.approval.status must equal 'not_required' when approval is not required"
                )
            if evidence_refs:
                errors.append(
                    "$.approval.evidence_refs must be empty when approval is not required"
                )
        elif approval_required is True:
            if approval_status == "not_required":
                errors.append(
                    "$.approval.status must not be 'not_required' when approval is required"
                )
            if approval_status == "approved" and evidence_refs == []:
                errors.append(
                    "$.approval.evidence_refs must not be empty when approval is approved"
                )

    if "stop_conditions" in document:
        _string_list(
            document.get("stop_conditions"),
            "$.stop_conditions",
            errors,
            minimum=1,
        )

    decision = _mapping(document.get("decision"), "$.decision", errors)
    decision_state: str | None = None
    if decision is not None:
        fields = {"state", "decided_by", "rationale"}
        _fields(
            decision,
            path="$.decision",
            required=fields,
            allowed=fields,
            errors=errors,
        )
        decision_state = _enum(
            decision.get("state"),
            "$.decision.state",
            DECISION_STATES,
            errors,
        )
        _string(decision.get("decided_by"), "$.decision.decided_by", errors)
        _string(decision.get("rationale"), "$.decision.rationale", errors, minimum=10)

    if risk_level in {"high", "critical"} and approval_required is not True:
        errors.append("$.approval.required must be true for high or critical risk")
    if decision_state == "admitted" and approval_required is True:
        if approval_status != "approved":
            errors.append(
                "$.approval.status must be 'approved' before an approval-required task is admitted"
            )
    if decision_state == "admitted" and approval_status == "rejected":
        errors.append("$.decision.state cannot be 'admitted' when approval is rejected")

    return errors


def load_development_task(path: Path) -> Mapping[str, Any]:
    """Load one UTF-8 JSON task contract and require an object root."""

    document = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(document, Mapping):
        raise ValueError("development task root must be an object")
    return document


def canonical_task_digest(document: Mapping[str, Any]) -> str:
    """Return the stable identity of one validated or candidate task document."""

    canonical = json.dumps(
        document,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(canonical).hexdigest()


def _repository_root(path: Path) -> Path:
    if path.is_symlink():
        raise ValueError(f"repository root must not be a symbolic link: {path}")
    if not path.exists():
        raise FileNotFoundError(path)
    if not path.is_dir():
        raise ValueError(f"repository root is not a directory: {path}")
    return path.resolve()


def _resolve_inside(root: Path, path: Path, *, label: str) -> Path:
    candidate = path if path.is_absolute() else root / path
    resolved = candidate.resolve(strict=False)
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"{label} must stay within repository root: {path}") from exc

    cursor = candidate
    while True:
        if cursor.is_symlink():
            raise ValueError(f"{label} must not use a symbolic link: {path}")
        if cursor.resolve(strict=False) == root or cursor.parent == cursor:
            break
        cursor = cursor.parent
    return resolved


def _readable_reference(root: Path, reference: str, *, label: str) -> str | None:
    if "\\" in reference:
        return f"{label} must use forward slashes: {reference}"
    path_text = reference.split("#", 1)[0]
    if not path_text or "://" in path_text or _WINDOWS_DRIVE_RE.match(path_text):
        return f"{label} must be a repository-relative file path: {reference}"
    relative = PurePosixPath(path_text)
    if relative.is_absolute() or path_text == "." or ".." in relative.parts:
        return f"{label} must be a safe repository-relative file path: {reference}"
    try:
        resolved = _resolve_inside(root, Path(*relative.parts), label=label)
    except ValueError as exc:
        return str(exc)
    if not resolved.exists():
        return f"{label} does not exist: {reference}"
    if not resolved.is_file():
        return f"{label} is not a file: {reference}"
    try:
        resolved.read_text(encoding="utf-8")
    except UnicodeError as exc:
        return f"{label} is not valid UTF-8: {reference}: {exc}"
    except OSError as exc:
        return f"{label} could not be read: {reference}: {exc}"
    return None


def _reference_finding(
    root: Path,
    task_id: str,
    category: str,
    references: list[str],
    *,
    label: str,
    empty_status: TaskFindingStatus,
    empty_message: str,
) -> TaskFinding:
    if not references:
        return TaskFinding(
            empty_status,
            f"task:{task_id}:{category}",
            empty_message,
        )
    errors = [
        error
        for reference in references
        if (error := _readable_reference(root, reference, label=label)) is not None
    ]
    if errors:
        return TaskFinding(
            TaskFindingStatus.FAIL,
            f"task:{task_id}:{category}",
            "; ".join(errors),
        )
    return TaskFinding(
        TaskFindingStatus.PASS,
        f"task:{task_id}:{category}",
        f"all {len(references)} declared {label} reference(s) are readable",
    )


def check_development_task(task_path: Path, *, repository: Path) -> TaskReport:
    """Validate one task and its declared references without modifying the repository."""

    root = _repository_root(repository)
    safe_task_path = _resolve_inside(root, task_path, label="development task path")
    if not safe_task_path.exists():
        raise FileNotFoundError(safe_task_path)
    if not safe_task_path.is_file():
        raise ValueError(f"development task path is not a file: {task_path}")

    document = load_development_task(safe_task_path)
    task_id_value = document.get("task_id")
    task_id = task_id_value if isinstance(task_id_value, str) else "unknown"
    errors = validate_development_task_document(document)
    if errors:
        return TaskReport(
            root,
            safe_task_path,
            task_id,
            (
                TaskFinding(
                    TaskFindingStatus.FAIL,
                    f"task:{task_id}:contract",
                    "; ".join(errors),
                ),
            ),
        )

    requirement = document["requirement"]
    objective = document.get("objective")
    approval = document.get("approval")
    decision = document["decision"]
    assert isinstance(requirement, Mapping)
    assert objective is None or isinstance(objective, Mapping)
    assert approval is None or isinstance(approval, Mapping)
    assert isinstance(decision, Mapping)

    findings = [
        TaskFinding(
            TaskFindingStatus.PASS,
            f"task:{task_id}:contract",
            "development task satisfies the structural contract",
        ),
        _reference_finding(
            root,
            task_id,
            "requirement",
            list(requirement["source_refs"]),
            label="requirement source",
            empty_status=TaskFindingStatus.WARN,
            empty_message=(
                "the requirement is captured inline but has no repository-local "
                "source reference"
            ),
        ),
    ]

    if objective is None:
        findings.append(
            TaskFinding(
                TaskFindingStatus.ADVISORY,
                f"task:{task_id}:objective",
                "compact task omits a parent objective; the accountable owner must confirm alignment",
            )
        )
    else:
        findings.append(
            _reference_finding(
                root,
                task_id,
                "objective",
                list(objective["parent_refs"]),
                label="parent objective",
                empty_status=TaskFindingStatus.FAIL,
                empty_message="no parent objective reference is declared",
            )
        )

    findings.append(
        _reference_finding(
            root,
            task_id,
            "architecture",
            list(document.get("architecture_refs", [])),
            label="architecture",
            empty_status=TaskFindingStatus.ADVISORY,
            empty_message=(
                "no architecture reference is declared; an accountable human "
                "must confirm that architecture context is not applicable"
            ),
        )
    )

    if approval is None:
        findings.append(
            TaskFinding(
                TaskFindingStatus.PASS,
                f"task:{task_id}:approval",
                "compact low-risk task uses its accountable owner and human decision boundary",
            )
        )
    elif approval["status"] == "approved":
        findings.append(
            _reference_finding(
                root,
                task_id,
                "approval",
                list(approval["evidence_refs"]),
                label="approval evidence",
                empty_status=TaskFindingStatus.FAIL,
                empty_message="approved work has no approval evidence reference",
            )
        )
    elif approval["status"] in {"pending", "rejected"}:
        findings.append(
            TaskFinding(
                TaskFindingStatus.WARN,
                f"task:{task_id}:approval",
                f"approval status is {approval['status']}",
            )
        )
    else:
        findings.append(
            TaskFinding(
                TaskFindingStatus.PASS,
                f"task:{task_id}:approval",
                "the task declares that separate approval is not required",
            )
        )

    if decision["state"] == "admitted":
        findings.append(
            TaskFinding(
                TaskFindingStatus.PASS,
                f"task:{task_id}:decision",
                f"the task is admitted by {decision['decided_by']}",
            )
        )
    else:
        findings.append(
            TaskFinding(
                TaskFindingStatus.WARN,
                f"task:{task_id}:decision",
                f"the task decision state is {decision['state']}; implementation is not admitted",
            )
        )

    role = str(objective["role"]) if objective is not None else "compact"
    alignment_message = (
        f"an accountable human must confirm that the declared {role} "
        "objective role and rationale still advance the parent requirement"
        if objective is not None
        else (
            "an accountable human must confirm that the compact task still "
            "advances the parent requirement"
        )
    )
    findings.append(
        TaskFinding(
            TaskFindingStatus.ADVISORY,
            f"task:{task_id}:objective-alignment",
            alignment_message,
        )
    )
    return TaskReport(root, safe_task_path, task_id, tuple(findings))
