"""Vendor-neutral coding-agent task proposals and human-only admission."""

from __future__ import annotations

import hashlib
import json
import os
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Callable, Mapping

from agentgov.path_policy import is_segment_prefix, scope_path_error
from agentgov.task_contract import canonical_task_digest, validate_development_task_document


TASK_PROPOSAL_CONTRACT = "agentgov.task-proposal"
TASK_PROPOSAL_SCHEMA_VERSION = "1.0"
TASK_ADMISSION_PLAN_CONTRACT = "agentgov.task-admission-plan"
TASK_ADMISSION_PLAN_SCHEMA_VERSION = "1.0"
MAX_PROPOSAL_BYTES = 65_536

_PROPOSAL_ID_RE = re.compile(r"^prp-[0-9a-f]{32}$")
_TASK_ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_ADAPTER_ID_RE = re.compile(r"^[a-z0-9]+(?:[._-][a-z0-9]+)*$")
_SENSITIVE_RE = re.compile(
    r"(?i)(?:api[_-]?key|access[_-]?token|auth[_-]?token|password|passwd|secret)\s*[:=]"
)
_ABSOLUTE_PATH_RE = re.compile(r"(?i)(?:^|\s)(?:[a-z]:[\\/]|/(?:users|home|var|etc|tmp)/)")

_AUTHORITY_FIELDS = {
    "admits_task",
    "starts_session",
    "authorizes_code_change",
    "authorizes_scope_expansion",
    "authorizes_exception",
    "authorizes_git_operations",
    "authorizes_deployment",
    "authorizes_release",
}
_CONTENT_BOUNDARY_FIELDS = {
    "contains_raw_prompt",
    "contains_transcript",
    "contains_source_content",
    "contains_credentials",
    "contains_absolute_paths",
}


class TaskProposalPolicyError(ValueError):
    """A proposal or admission action is invalid, ambiguous, or unsafe."""


@dataclass(frozen=True)
class TaskAdmissionPlan:
    root: Path
    proposal: Mapping[str, Any]
    proposal_digest: str
    target: str
    task_document: Mapping[str, Any]
    task_digest: str

    @property
    def targets(self) -> tuple[str, ...]:
        return (self.target,)


@dataclass(frozen=True)
class TaskAdmissionResult:
    target: str
    task_id: str
    task_digest: str


def _fields(
    value: Mapping[str, Any],
    *,
    path: str,
    required: set[str],
    allowed: set[str],
    errors: list[str],
) -> None:
    missing = sorted(required - set(value))
    unexpected = sorted(set(value) - allowed, key=str)
    if missing:
        errors.append(f"{path} is missing required fields: {', '.join(missing)}")
    if unexpected:
        errors.append(
            f"{path} contains unsupported fields: {', '.join(str(item) for item in unexpected)}"
        )


def _mapping(value: Any, path: str, errors: list[str]) -> Mapping[str, Any] | None:
    if not isinstance(value, Mapping):
        errors.append(f"{path} must be an object")
        return None
    return value


def _text(
    value: Any,
    path: str,
    errors: list[str],
    *,
    minimum: int = 1,
    maximum: int = 1_000,
    safe_content: bool = True,
) -> str | None:
    if not isinstance(value, str) or len(value.strip()) < minimum:
        errors.append(f"{path} must be a non-empty string of at least {minimum} characters")
        return None
    if len(value) > maximum:
        errors.append(f"{path} exceeds the {maximum}-character limit")
    if any(unicodedata.category(character).startswith("C") for character in value):
        errors.append(f"{path} contains unsupported control characters")
    if safe_content and (_SENSITIVE_RE.search(value) or _ABSOLUTE_PATH_RE.search(value)):
        errors.append(f"{path} contains sensitive or host-local content")
    return value


def _text_list(
    value: Any,
    path: str,
    errors: list[str],
    *,
    minimum: int = 0,
    maximum_items: int = 25,
    safe_content: bool = True,
) -> list[str] | None:
    if not isinstance(value, list):
        errors.append(f"{path} must be an array")
        return None
    if len(value) < minimum:
        errors.append(f"{path} must contain at least {minimum} item(s)")
    if len(value) > maximum_items:
        errors.append(f"{path} exceeds the {maximum_items}-item limit")
    output: list[str] = []
    for index, item in enumerate(value):
        text = _text(item, f"{path}[{index}]", errors, safe_content=safe_content)
        if text is not None:
            output.append(text)
    if len(output) != len(set(output)):
        errors.append(f"{path} must not contain duplicate items")
    return output


def validate_task_proposal_document(document: Mapping[str, Any]) -> list[str]:
    """Validate one strict, non-authoritative Coding Agent proposal."""

    errors: list[str] = []
    top_fields = {
        "contract",
        "schema_version",
        "proposal_id",
        "source",
        "task",
        "content_boundary",
        "authority_boundary",
    }
    _fields(document, path="$", required=top_fields, allowed=top_fields, errors=errors)
    if document.get("contract") != TASK_PROPOSAL_CONTRACT:
        errors.append(f"$.contract must equal {TASK_PROPOSAL_CONTRACT!r}")
    if document.get("schema_version") != TASK_PROPOSAL_SCHEMA_VERSION:
        errors.append(f"$.schema_version must equal {TASK_PROPOSAL_SCHEMA_VERSION!r}")
    proposal_id = _text(document.get("proposal_id"), "$.proposal_id", errors, maximum=36)
    if proposal_id and not _PROPOSAL_ID_RE.fullmatch(proposal_id):
        errors.append("$.proposal_id must use prp- followed by 32 lowercase hexadecimal characters")

    source = _mapping(document.get("source"), "$.source", errors)
    if source is not None:
        fields = {"adapter_id", "actor_class"}
        _fields(source, path="$.source", required=fields, allowed=fields, errors=errors)
        adapter_id = _text(source.get("adapter_id"), "$.source.adapter_id", errors, maximum=100)
        if adapter_id and not _ADAPTER_ID_RE.fullmatch(adapter_id):
            errors.append("$.source.adapter_id must be a portable lowercase identifier")
        if source.get("actor_class") != "coding_agent":
            errors.append("$.source.actor_class must equal 'coding_agent'")

    task = _mapping(document.get("task"), "$.task", errors)
    if task is not None:
        fields = {
            "task_id",
            "title",
            "requirement_summary",
            "scope",
            "acceptance_signals",
            "validation_commands",
            "owner",
            "risk",
            "assumptions",
            "unknowns",
        }
        _fields(task, path="$.task", required=fields, allowed=fields, errors=errors)
        task_id = _text(task.get("task_id"), "$.task.task_id", errors, maximum=100)
        if task_id and not _TASK_ID_RE.fullmatch(task_id):
            errors.append("$.task.task_id must use kebab-case")
        _text(task.get("title"), "$.task.title", errors, minimum=5, maximum=200)
        _text(task.get("requirement_summary"), "$.task.requirement_summary", errors, minimum=10)
        _text_list(task.get("acceptance_signals"), "$.task.acceptance_signals", errors, minimum=1)
        _text_list(
            task.get("validation_commands"),
            "$.task.validation_commands",
            errors,
            minimum=1,
            safe_content=True,
        )
        _text(task.get("owner"), "$.task.owner", errors, maximum=100)
        _text_list(task.get("assumptions"), "$.task.assumptions", errors)
        _text_list(task.get("unknowns"), "$.task.unknowns", errors)

        scope = _mapping(task.get("scope"), "$.task.scope", errors)
        if scope is not None:
            fields = {"include_paths", "exclude_paths"}
            _fields(scope, path="$.task.scope", required=fields, allowed=fields, errors=errors)
            includes = _text_list(
                scope.get("include_paths"),
                "$.task.scope.include_paths",
                errors,
                minimum=1,
                safe_content=False,
            )
            excludes = _text_list(
                scope.get("exclude_paths"),
                "$.task.scope.exclude_paths",
                errors,
                safe_content=False,
            )
            for name, values in (("include_paths", includes), ("exclude_paths", excludes)):
                for index, value in enumerate(values or []):
                    if scope_path_error(value):
                        errors.append(f"$.task.scope.{name}[{index}] must be a safe repository-relative path")
            if includes is not None and excludes is not None and set(includes) & set(excludes):
                errors.append("$.task.scope must not include and exclude the same path")

        risk = _mapping(task.get("risk"), "$.task.risk", errors)
        if risk is not None:
            fields = {"level", "items"}
            _fields(risk, path="$.task.risk", required=fields, allowed=fields, errors=errors)
            if risk.get("level") != "low":
                errors.append("$.task.risk.level must equal 'low' for proposal admission")
            _text_list(risk.get("items"), "$.task.risk.items", errors)

    content = _mapping(document.get("content_boundary"), "$.content_boundary", errors)
    if content is not None:
        _fields(
            content,
            path="$.content_boundary",
            required=_CONTENT_BOUNDARY_FIELDS,
            allowed=_CONTENT_BOUNDARY_FIELDS,
            errors=errors,
        )
        for field in sorted(_CONTENT_BOUNDARY_FIELDS):
            if content.get(field) is not False:
                errors.append(f"$.content_boundary.{field} must equal false")

    authority = _mapping(document.get("authority_boundary"), "$.authority_boundary", errors)
    if authority is not None:
        _fields(
            authority,
            path="$.authority_boundary",
            required=_AUTHORITY_FIELDS,
            allowed=_AUTHORITY_FIELDS,
            errors=errors,
        )
        for field in sorted(_AUTHORITY_FIELDS):
            if authority.get(field) is not False:
                errors.append(f"$.authority_boundary.{field} must equal false")
    return errors


def load_task_proposal(path: Path) -> Mapping[str, Any]:
    """Load and validate one bounded UTF-8 proposal without retaining source bytes."""

    if path.is_symlink():
        raise TaskProposalPolicyError("proposal input must not be a symbolic link")
    size = path.stat().st_size
    if size > MAX_PROPOSAL_BYTES:
        raise TaskProposalPolicyError(f"proposal input exceeds {MAX_PROPOSAL_BYTES} bytes")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise TaskProposalPolicyError(
            f"proposal input is not valid JSON at line {exc.lineno}, column {exc.colno}"
        ) from exc
    if not isinstance(value, Mapping):
        raise TaskProposalPolicyError("task proposal root must be an object")
    errors = validate_task_proposal_document(value)
    if errors:
        raise TaskProposalPolicyError("task proposal is invalid: " + "; ".join(errors))
    return json.loads(json.dumps(value, ensure_ascii=False))


def canonical_proposal_digest(document: Mapping[str, Any]) -> str:
    canonical = json.dumps(
        document,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(canonical).hexdigest()


def _safe_root(repository: Path) -> Path:
    if repository.is_symlink():
        raise TaskProposalPolicyError("repository root must not be a symbolic link")
    if not repository.exists():
        raise FileNotFoundError(repository)
    if not repository.is_dir():
        raise TaskProposalPolicyError("repository root must be a directory")
    return repository.resolve()


def _safe_task_target(root: Path, relative: str) -> Path:
    pure = PurePosixPath(relative)
    if pure.is_absolute() or scope_path_error(relative):
        raise TaskProposalPolicyError("task target must be a safe repository-relative path")
    cursor = root
    for part in pure.parts[:-1]:
        cursor = cursor / part
        if cursor.is_symlink():
            raise TaskProposalPolicyError("task target parent must not use a symbolic link")
        if not cursor.exists() or not cursor.is_dir():
            raise TaskProposalPolicyError("governance/tasks must exist as real directories before admission")
    target = cursor / pure.name
    try:
        target.resolve(strict=False).relative_to(root)
    except ValueError as exc:
        raise TaskProposalPolicyError("task target must stay within the repository") from exc
    return target


def _build_task_document(proposal: Mapping[str, Any]) -> Mapping[str, Any]:
    task = proposal["task"]
    scope = task["scope"]
    task_id = task["task_id"]
    target = f"governance/tasks/{task_id}.json"
    if any(is_segment_prefix(path, target) for path in scope["exclude_paths"]):
        raise TaskProposalPolicyError("the proposed task excludes its own governance contract")
    includes = list(scope["include_paths"])
    if not any(is_segment_prefix(path, target) for path in includes):
        includes.append(target)
    risks = list(task["risk"]["items"])
    risks.extend(f"Reviewed assumption: {item}" for item in task["assumptions"])
    risks.extend(f"Reviewed unknown: {item}" for item in task["unknowns"])
    document: Mapping[str, Any] = {
        "contract": "agentgov.development-task",
        "schema_version": "1.1",
        "profile": "compact",
        "task_id": task_id,
        "title": task["title"],
        "requirement": {"summary": task["requirement_summary"], "source_refs": []},
        "scope": {"include_paths": includes, "exclude_paths": list(scope["exclude_paths"])},
        "acceptance_signals": list(task["acceptance_signals"]),
        "validation_commands": list(task["validation_commands"]),
        "owner": task["owner"],
        "risk": {"level": "low", "items": risks},
        "decision": {
            "state": "admitted",
            "decided_by": task["owner"],
            "rationale": (
                f"The accountable human reviewed structured proposal {proposal['proposal_id']} "
                "and admitted that exact task through an explicit admission control."
            ),
        },
    }
    errors = validate_development_task_document(document)
    if errors:
        raise TaskProposalPolicyError("proposed task is invalid: " + "; ".join(errors))
    return document


def build_task_admission_plan(
    repository: Path,
    proposal: Mapping[str, Any],
) -> TaskAdmissionPlan:
    """Build a complete read-only preview; the proposal remains non-authoritative."""

    errors = validate_task_proposal_document(proposal)
    if errors:
        raise TaskProposalPolicyError("task proposal is invalid: " + "; ".join(errors))
    root = _safe_root(repository)
    normalized = json.loads(json.dumps(proposal, ensure_ascii=False))
    task_document = _build_task_document(normalized)
    target = f"governance/tasks/{task_document['task_id']}.json"
    target_path = _safe_task_target(root, target)
    if target_path.exists() or target_path.is_symlink():
        raise TaskProposalPolicyError("task target already exists and will not be overwritten")
    return TaskAdmissionPlan(
        root=root,
        proposal=normalized,
        proposal_digest=canonical_proposal_digest(normalized),
        target=target,
        task_document=task_document,
        task_digest=canonical_task_digest(task_document),
    )


def _plan_payload(plan: TaskAdmissionPlan) -> Mapping[str, Any]:
    return {
        "contract": TASK_ADMISSION_PLAN_CONTRACT,
        "schema_version": TASK_ADMISSION_PLAN_SCHEMA_VERSION,
        "proposal": plan.proposal,
        "proposal_digest": plan.proposal_digest,
        "action": "create",
        "target": plan.target,
        "task_document": plan.task_document,
        "task_digest": plan.task_digest,
        "targets": list(plan.targets),
        "authority_boundary": {
            "repository_modified": False,
            "task_admitted": False,
            "session_started": False,
            "authorizes_code_change": False,
            "authorizes_scope_expansion": False,
            "authorizes_exception": False,
            "authorizes_git_operations": False,
            "authorizes_deployment": False,
            "authorizes_release": False,
        },
    }


def render_task_admission_plan_json(plan: TaskAdmissionPlan) -> str:
    return json.dumps(_plan_payload(plan), ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def render_task_admission_plan_terminal(plan: TaskAdmissionPlan) -> str:
    task = plan.proposal["task"]
    lines = [
        "TASK ADMISSION PREVIEW",
        f"PROPOSAL {plan.proposal['proposal_id']}",
        f"PROPOSAL_DIGEST {plan.proposal_digest}",
        f"SOURCE_ADAPTER {plan.proposal['source']['adapter_id']}",
        "ACTION create",
        f"TARGET {plan.target}",
        f"TASK_DIGEST {plan.task_digest}",
        f"ASSUMPTIONS {len(task['assumptions'])}",
    ]
    lines.extend(f"  - {item}" for item in task["assumptions"])
    lines.append(f"UNKNOWNS {len(task['unknowns'])}")
    lines.extend(f"  - {item}" for item in task["unknowns"])
    lines.append("TASK_DOCUMENT")
    lines.append(json.dumps(plan.task_document, ensure_ascii=False, indent=2, sort_keys=True))
    lines.append(
        "AUTHORITY repository_modified=false task_admitted=false session_started=false "
        "code_change=false scope_expansion=false exception=false git_operations=false "
        "deployment=false release=false"
    )
    lines.append("NOTE the proposal is a Coding Agent interpretation, not a human decision")
    lines.append("NOTE admission creates only the reviewed task file and does not start development")
    return "\n".join(lines) + "\n"


def request_task_admission_confirmation(
    plan: TaskAdmissionPlan,
    *,
    decision_reader: Callable[[str], str],
    is_interactive_terminal: bool,
) -> bool:
    """Accept admission authority only from exact human terminal confirmation."""

    if not is_interactive_terminal:
        return False
    try:
        decision = decision_reader(
            f'Type ADMIT to create the reviewed task in "{plan.root}": '
        )
    except EOFError:
        return False
    return decision == "ADMIT"


def apply_task_admission_plan(plan: TaskAdmissionPlan) -> TaskAdmissionResult:
    """Exclusively create the exact reviewed task and nothing else."""

    proposal_errors = validate_task_proposal_document(plan.proposal)
    if proposal_errors or canonical_proposal_digest(plan.proposal) != plan.proposal_digest:
        raise TaskProposalPolicyError("proposal changed after preview; build and review a new plan")
    task_errors = validate_development_task_document(plan.task_document)
    if task_errors or canonical_task_digest(plan.task_document) != plan.task_digest:
        raise TaskProposalPolicyError("task document changed after preview; build and review a new plan")
    rebuilt = _build_task_document(plan.proposal)
    if canonical_task_digest(rebuilt) != plan.task_digest:
        raise TaskProposalPolicyError("proposal and task plan no longer match")
    try:
        target = _safe_task_target(plan.root, plan.target)
    except TaskProposalPolicyError as exc:
        raise TaskProposalPolicyError("task parent changed after preview") from exc
    if target.exists() or target.is_symlink():
        raise TaskProposalPolicyError("task target appeared after preview and was not overwritten")
    encoded = (
        json.dumps(plan.task_document, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    created = False
    try:
        descriptor = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        created = True
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
    except BaseException:
        if created and target.exists():
            try:
                if target.read_bytes() == encoded:
                    target.unlink()
            except OSError:
                pass
        raise
    return TaskAdmissionResult(
        target=plan.target,
        task_id=str(plan.task_document["task_id"]),
        task_digest=plan.task_digest,
    )
