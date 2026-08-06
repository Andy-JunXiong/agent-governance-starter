"""Risk-based request routing with human-owned standing delegation."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import unicodedata
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Mapping

from agentgov.development_session import SessionPolicyError, resolve_active_task
from agentgov.path_policy import is_segment_prefix, scope_path_error
from agentgov.task_contract import canonical_task_digest
from agentgov.task_proposal import (
    TaskAdmissionPlan,
    TaskAdmissionResult,
    TaskProposalPolicyError,
    apply_task_admission_plan,
    build_task_admission_plan,
    canonical_proposal_digest,
    validate_task_proposal_document,
)


ROUTING_POLICY_CONTRACT = "agentgov.admission-routing-policy"
ROUTING_POLICY_SCHEMA_VERSION = "1.0"
WORK_REQUEST_CONTRACT = "agentgov.work-request"
WORK_REQUEST_SCHEMA_VERSION = "1.0"
ADMISSION_ROUTE_CONTRACT = "agentgov.admission-route"
ADMISSION_ROUTE_SCHEMA_VERSION = "1.0"
MAX_INPUT_BYTES = 65_536

NO_WRITE_CLASSES = {
    "question",
    "explanation",
    "status_query",
    "read_only_diagnosis",
}
REQUEST_CLASSES = NO_WRITE_CLASSES | {"repository_change", "active_task_continuation"}
ROUTES = {"observe_only", "continue_active", "fast_track", "human_review", "full_review"}
MATERIAL_CHARACTERISTICS = {
    "ambiguous_intent",
    "unknown_scope",
    "architecture_change",
    "dependency_change",
    "authentication_or_authorization_change",
    "security_boundary_change",
    "data_schema_change",
    "data_migration",
    "destructive_operation",
    "external_write",
    "infrastructure_change",
    "deployment_change",
    "public_api_change",
    "governance_policy_change",
}
_CONTENT_FIELDS = {
    "contains_raw_prompt",
    "contains_transcript",
    "contains_source_content",
    "contains_credentials",
    "contains_absolute_paths",
}
_REQUEST_AUTHORITY_FIELDS = {
    "admits_task",
    "authorizes_repository_write",
    "starts_session",
    "authorizes_scope_expansion",
    "authorizes_exception",
    "authorizes_git_operations",
    "authorizes_deployment",
    "authorizes_release",
}
_POLICY_AUTHORITY_FIELDS = {
    "permits_noninteractive_fast_track_task_creation",
    "permits_session_start",
    "permits_code_change",
    "permits_scope_expansion",
    "permits_exception",
    "permits_git_operations",
    "permits_deployment",
    "permits_release",
}
_REQUEST_ID_RE = re.compile(r"^wrq-[0-9a-f]{32}$")
_POLICY_ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_ADAPTER_ID_RE = re.compile(r"^[a-z0-9]+(?:[._-][a-z0-9]+)*$")
_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_SENSITIVE_RE = re.compile(
    r"(?i)(?:api[_-]?key|access[_-]?token|auth[_-]?token|password|passwd|secret)\s*[:=]"
)
_ABSOLUTE_PATH_RE = re.compile(r"(?i)(?:^|\s)(?:[a-z]:[\\/]|/(?:users|home|var|etc|tmp)/)")
_SHELL_CONTROL_RE = re.compile(r"[;&|><`^]|\$\(")


class AdmissionRoutingError(ValueError):
    """A routing input or application cannot be handled safely."""


@dataclass(frozen=True)
class AdmissionRoute:
    root: Path
    policy_path: Path
    policy_relative_path: str
    policy: Mapping[str, Any]
    policy_digest: str
    policy_tracked_clean: bool
    request: Mapping[str, Any]
    request_digest: str
    route: str
    reason_codes: tuple[str, ...]
    planned_human_interruptions: int
    max_human_interruptions: int
    admission_plan: TaskAdmissionPlan | None


def _fields(
    value: Mapping[str, Any],
    *,
    path: str,
    required: set[str],
    allowed: set[str],
    errors: list[str],
) -> None:
    missing = sorted(required - set(value), key=str)
    unexpected = sorted(set(value) - allowed, key=str)
    if missing:
        errors.append(f"{path} is missing required fields: {', '.join(str(item) for item in missing)}")
    if unexpected:
        errors.append(f"{path} contains unsupported fields: {', '.join(str(item) for item in unexpected)}")


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
        errors.append(f"{path} must be a string of at least {minimum} characters")
        return None
    if len(value) > maximum:
        errors.append(f"{path} exceeds the {maximum}-character limit")
    if any(unicodedata.category(character).startswith("C") for character in value):
        errors.append(f"{path} contains unsupported control characters")
    if safe_content and (_SENSITIVE_RE.search(value) or _ABSOLUTE_PATH_RE.search(value)):
        errors.append(f"{path} contains sensitive or host-local content")
    return value


def _string_list(
    value: Any,
    path: str,
    errors: list[str],
    *,
    minimum: int = 0,
    maximum: int = 50,
    safe_content: bool = True,
) -> list[str] | None:
    if not isinstance(value, list):
        errors.append(f"{path} must be an array")
        return None
    if len(value) < minimum:
        errors.append(f"{path} must contain at least {minimum} item(s)")
    if len(value) > maximum:
        errors.append(f"{path} exceeds the {maximum}-item limit")
    result: list[str] = []
    for index, item in enumerate(value):
        parsed = _text(item, f"{path}[{index}]", errors, safe_content=safe_content)
        if parsed is not None:
            result.append(parsed)
    if len(result) != len(set(result)):
        errors.append(f"{path} must not contain duplicate items")
    return result


def _nonnegative_int(value: Any, path: str, errors: list[str], *, maximum: int) -> int | None:
    if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= maximum:
        errors.append(f"{path} must be an integer from 0 through {maximum}")
        return None
    return value


def validate_admission_routing_policy(document: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    fields = {
        "contract", "schema_version", "policy_id", "owner", "no_task_classes",
        "fast_track", "friction_budget", "authority", "decision",
    }
    _fields(document, path="$", required=fields, allowed=fields, errors=errors)
    if document.get("contract") != ROUTING_POLICY_CONTRACT:
        errors.append(f"$.contract must equal {ROUTING_POLICY_CONTRACT!r}")
    if document.get("schema_version") != ROUTING_POLICY_SCHEMA_VERSION:
        errors.append(f"$.schema_version must equal {ROUTING_POLICY_SCHEMA_VERSION!r}")
    policy_id = _text(document.get("policy_id"), "$.policy_id", errors, maximum=100)
    if policy_id and not _POLICY_ID_RE.fullmatch(policy_id):
        errors.append("$.policy_id must use kebab-case")
    owner = _text(document.get("owner"), "$.owner", errors, maximum=100)
    no_task = _string_list(document.get("no_task_classes"), "$.no_task_classes", errors)
    if no_task is not None and set(no_task) != NO_WRITE_CLASSES:
        errors.append("$.no_task_classes must contain every fixed no-write request class")

    fast = _mapping(document.get("fast_track"), "$.fast_track", errors)
    if fast is not None:
        fast_fields = {
            "enabled", "allowed_scope_prefixes", "denied_scope_prefixes",
            "validation_command_prefixes", "max_include_paths", "max_exclude_paths",
            "max_validation_commands", "max_risk_items", "max_assumptions",
            "require_no_unknowns", "forbidden_characteristics",
        }
        _fields(fast, path="$.fast_track", required=fast_fields, allowed=fast_fields, errors=errors)
        if not isinstance(fast.get("enabled"), bool):
            errors.append("$.fast_track.enabled must be a boolean")
        allowed = _string_list(
            fast.get("allowed_scope_prefixes"), "$.fast_track.allowed_scope_prefixes", errors,
            minimum=1 if fast.get("enabled") is True else 0, safe_content=False,
        )
        denied = _string_list(
            fast.get("denied_scope_prefixes"), "$.fast_track.denied_scope_prefixes", errors,
            safe_content=False,
        )
        for name, paths in (("allowed_scope_prefixes", allowed), ("denied_scope_prefixes", denied)):
            for index, path in enumerate(paths or []):
                if scope_path_error(path):
                    errors.append(f"$.fast_track.{name}[{index}] must be a safe repository-relative path")
        commands = _string_list(
            fast.get("validation_command_prefixes"),
            "$.fast_track.validation_command_prefixes",
            errors,
            minimum=1 if fast.get("enabled") is True else 0,
        )
        for index, command in enumerate(commands or []):
            if _SHELL_CONTROL_RE.search(command):
                errors.append(
                    f"$.fast_track.validation_command_prefixes[{index}] contains shell control syntax"
                )
        for key, maximum in (
            ("max_include_paths", 25), ("max_exclude_paths", 25),
            ("max_validation_commands", 10), ("max_risk_items", 25),
            ("max_assumptions", 25),
        ):
            _nonnegative_int(fast.get(key), f"$.fast_track.{key}", errors, maximum=maximum)
        if fast.get("require_no_unknowns") is not True:
            errors.append("$.fast_track.require_no_unknowns must equal true")
        forbidden = _string_list(
            fast.get("forbidden_characteristics"),
            "$.fast_track.forbidden_characteristics",
            errors,
        )
        if forbidden is not None and set(forbidden) != MATERIAL_CHARACTERISTICS:
            errors.append("$.fast_track.forbidden_characteristics must contain every material characteristic")

    friction = _mapping(document.get("friction_budget"), "$.friction_budget", errors)
    if friction is not None:
        friction_fields = {
            "observe_only_max_human_interruptions", "continue_active_max_human_interruptions",
            "fast_track_max_human_interruptions", "human_review_max_human_interruptions",
            "full_review_max_human_interruptions",
        }
        _fields(
            friction, path="$.friction_budget", required=friction_fields,
            allowed=friction_fields, errors=errors,
        )
        for key in (
            "observe_only_max_human_interruptions",
            "continue_active_max_human_interruptions",
            "fast_track_max_human_interruptions",
        ):
            if friction.get(key) != 0:
                errors.append(f"$.friction_budget.{key} must equal 0")
        if friction.get("human_review_max_human_interruptions") != 1:
            errors.append("$.friction_budget.human_review_max_human_interruptions must equal 1")
        full = _nonnegative_int(
            friction.get("full_review_max_human_interruptions"),
            "$.friction_budget.full_review_max_human_interruptions",
            errors,
            maximum=2,
        )
        if full is not None and full < 1:
            errors.append("$.friction_budget.full_review_max_human_interruptions must be at least 1")

    authority = _mapping(document.get("authority"), "$.authority", errors)
    if authority is not None:
        _fields(
            authority, path="$.authority", required=_POLICY_AUTHORITY_FIELDS,
            allowed=_POLICY_AUTHORITY_FIELDS, errors=errors,
        )
        if not isinstance(authority.get("permits_noninteractive_fast_track_task_creation"), bool):
            errors.append("$.authority.permits_noninteractive_fast_track_task_creation must be a boolean")
        for key in sorted(_POLICY_AUTHORITY_FIELDS - {"permits_noninteractive_fast_track_task_creation"}):
            if authority.get(key) is not False:
                errors.append(f"$.authority.{key} must equal false")

    decision = _mapping(document.get("decision"), "$.decision", errors)
    if decision is not None:
        decision_fields = {"state", "decided_by", "rationale"}
        _fields(decision, path="$.decision", required=decision_fields, allowed=decision_fields, errors=errors)
        if decision.get("state") not in {"draft", "admitted", "paused"}:
            errors.append("$.decision.state must be draft, admitted, or paused")
        decided_by = _text(decision.get("decided_by"), "$.decision.decided_by", errors, maximum=100)
        _text(decision.get("rationale"), "$.decision.rationale", errors, minimum=10)
        if decision.get("state") == "admitted" and owner and decided_by != owner:
            errors.append("$.decision.decided_by must equal $.owner for an admitted policy")
    if (
        fast is not None and fast.get("enabled") is True
        and authority is not None
        and authority.get("permits_noninteractive_fast_track_task_creation") is not True
    ):
        errors.append("$.authority must explicitly permit noninteractive task creation when fast-track is enabled")
    return errors


def validate_work_request(document: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    fields = {
        "contract", "schema_version", "request_id", "source", "request_class",
        "active_task", "proposal", "characteristics", "content_boundary", "authority_boundary",
    }
    _fields(document, path="$", required=fields, allowed=fields, errors=errors)
    if document.get("contract") != WORK_REQUEST_CONTRACT:
        errors.append(f"$.contract must equal {WORK_REQUEST_CONTRACT!r}")
    if document.get("schema_version") != WORK_REQUEST_SCHEMA_VERSION:
        errors.append(f"$.schema_version must equal {WORK_REQUEST_SCHEMA_VERSION!r}")
    request_id = _text(document.get("request_id"), "$.request_id", errors, maximum=36)
    if request_id and not _REQUEST_ID_RE.fullmatch(request_id):
        errors.append("$.request_id must use wrq- followed by 32 lowercase hexadecimal characters")
    request_class = document.get("request_class")
    if request_class not in REQUEST_CLASSES:
        errors.append("$.request_class is unsupported")

    source = _mapping(document.get("source"), "$.source", errors)
    if source is not None:
        source_fields = {"adapter_id", "actor_class"}
        _fields(source, path="$.source", required=source_fields, allowed=source_fields, errors=errors)
        adapter = _text(source.get("adapter_id"), "$.source.adapter_id", errors, maximum=100)
        if adapter and not _ADAPTER_ID_RE.fullmatch(adapter):
            errors.append("$.source.adapter_id must be a portable lowercase identifier")
        if source.get("actor_class") != "coding_agent":
            errors.append("$.source.actor_class must equal 'coding_agent'")

    characteristics = _mapping(document.get("characteristics"), "$.characteristics", errors)
    if characteristics is not None:
        _fields(
            characteristics, path="$.characteristics", required=MATERIAL_CHARACTERISTICS,
            allowed=MATERIAL_CHARACTERISTICS, errors=errors,
        )
        for key in sorted(MATERIAL_CHARACTERISTICS):
            if not isinstance(characteristics.get(key), bool):
                errors.append(f"$.characteristics.{key} must be a boolean")

    content = _mapping(document.get("content_boundary"), "$.content_boundary", errors)
    if content is not None:
        _fields(content, path="$.content_boundary", required=_CONTENT_FIELDS, allowed=_CONTENT_FIELDS, errors=errors)
        for key in sorted(_CONTENT_FIELDS):
            if content.get(key) is not False:
                errors.append(f"$.content_boundary.{key} must equal false")

    authority = _mapping(document.get("authority_boundary"), "$.authority_boundary", errors)
    if authority is not None:
        _fields(
            authority, path="$.authority_boundary", required=_REQUEST_AUTHORITY_FIELDS,
            allowed=_REQUEST_AUTHORITY_FIELDS, errors=errors,
        )
        for key in sorted(_REQUEST_AUTHORITY_FIELDS):
            if authority.get(key) is not False:
                errors.append(f"$.authority_boundary.{key} must equal false")

    active = document.get("active_task")
    proposal = document.get("proposal")
    if request_class in NO_WRITE_CLASSES:
        if active is not None or proposal is not None:
            errors.append("no-write requests must not contain active_task or proposal")
        if isinstance(characteristics, Mapping) and any(characteristics.values()):
            errors.append("no-write requests must not claim repository-change characteristics")
    elif request_class == "active_task_continuation":
        active_mapping = _mapping(active, "$.active_task", errors)
        if active_mapping is not None:
            active_fields = {"task_id", "task_digest"}
            _fields(active_mapping, path="$.active_task", required=active_fields, allowed=active_fields, errors=errors)
            task_id = _text(active_mapping.get("task_id"), "$.active_task.task_id", errors, maximum=100)
            if task_id and not _POLICY_ID_RE.fullmatch(task_id):
                errors.append("$.active_task.task_id must use kebab-case")
            digest = _text(active_mapping.get("task_digest"), "$.active_task.task_digest", errors, maximum=71)
            if digest and not _DIGEST_RE.fullmatch(digest):
                errors.append("$.active_task.task_digest must be a sha256 digest")
        if proposal is not None:
            errors.append("active-task continuation must not contain a new proposal")
    elif request_class == "repository_change":
        if active is not None:
            errors.append("new repository changes must not claim an active task")
        proposal_mapping = _mapping(proposal, "$.proposal", errors)
        if proposal_mapping is not None:
            proposal_errors = validate_task_proposal_document(proposal_mapping)
            errors.extend(f"$.proposal{item.removeprefix('$')}" for item in proposal_errors)
            task = proposal_mapping.get("task")
            if isinstance(task, Mapping) and task.get("unknowns"):
                if not isinstance(characteristics, Mapping) or characteristics.get("unknown_scope") is not True:
                    errors.append("$.characteristics.unknown_scope must be true when proposal unknowns are present")
    return errors


def _load_json(path: Path, *, label: str) -> Mapping[str, Any]:
    if path.is_symlink():
        raise AdmissionRoutingError(f"{label} must not be a symbolic link")
    if path.stat().st_size > MAX_INPUT_BYTES:
        raise AdmissionRoutingError(f"{label} exceeds {MAX_INPUT_BYTES} bytes")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise AdmissionRoutingError(
            f"{label} is not valid JSON at line {exc.lineno}, column {exc.colno}"
        ) from exc
    if not isinstance(value, Mapping):
        raise AdmissionRoutingError(f"{label} root must be an object")
    return value


def load_admission_routing_policy(path: Path) -> Mapping[str, Any]:
    value = _load_json(path, label="admission routing policy")
    errors = validate_admission_routing_policy(value)
    if errors:
        raise AdmissionRoutingError("admission routing policy is invalid: " + "; ".join(errors))
    return json.loads(json.dumps(value, ensure_ascii=False))


def load_work_request(path: Path) -> Mapping[str, Any]:
    value = _load_json(path, label="work request")
    errors = validate_work_request(value)
    if errors:
        raise AdmissionRoutingError("work request is invalid: " + "; ".join(errors))
    return json.loads(json.dumps(value, ensure_ascii=False))


def _digest(document: Mapping[str, Any]) -> str:
    encoded = json.dumps(document, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _safe_root(repository: Path) -> Path:
    if repository.is_symlink():
        raise AdmissionRoutingError("repository root must not be a symbolic link")
    if not repository.exists():
        raise FileNotFoundError(repository)
    if not repository.is_dir():
        raise AdmissionRoutingError("repository root must be a directory")
    return repository.resolve()


def _safe_policy_path(root: Path, policy_path: Path) -> tuple[Path, str]:
    candidate = policy_path if policy_path.is_absolute() else root / policy_path
    resolved = candidate.resolve(strict=False)
    try:
        relative = resolved.relative_to(root).as_posix()
    except ValueError as exc:
        raise AdmissionRoutingError("admission policy must stay within the repository") from exc
    if not relative or scope_path_error(relative):
        raise AdmissionRoutingError("admission policy must be a safe repository-relative file")
    cursor = root
    for part in PurePosixPath(relative).parts:
        cursor = cursor / part
        if cursor.is_symlink():
            raise AdmissionRoutingError("admission policy path must not use a symbolic link")
    return resolved, relative


def _policy_is_tracked_clean(root: Path, relative: str) -> bool:
    tracked = subprocess.run(
        ("git", "-C", str(root), "ls-files", "--error-unmatch", "--", relative),
        stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        check=False, timeout=30,
    )
    if tracked.returncode != 0:
        return False
    clean = subprocess.run(
        ("git", "-C", str(root), "diff", "--quiet", "HEAD", "--", relative),
        stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        check=False, timeout=30,
    )
    return clean.returncode == 0


def _command_allowed(command: str, prefixes: list[str]) -> bool:
    if _SHELL_CONTROL_RE.search(command):
        return False
    return any(command == prefix or command.startswith(prefix + " ") for prefix in prefixes)


def _scope_allowed(path: str, allowed: list[str], denied: list[str]) -> bool:
    if not any(is_segment_prefix(prefix, path) for prefix in allowed):
        return False
    return not any(
        is_segment_prefix(prefix, path) or is_segment_prefix(path, prefix)
        for prefix in denied
    )


def _route_budget(policy: Mapping[str, Any], route: str) -> tuple[int, int]:
    key = f"{route}_max_human_interruptions"
    maximum = int(policy["friction_budget"][key])
    planned = 0 if route in {"observe_only", "continue_active", "fast_track"} else 1
    return planned, maximum


def build_admission_route(
    repository: Path,
    *,
    policy_path: Path,
    request: Mapping[str, Any],
) -> AdmissionRoute:
    """Build one complete read-only route from structured, non-authoritative facts."""

    request_errors = validate_work_request(request)
    if request_errors:
        raise AdmissionRoutingError("work request is invalid: " + "; ".join(request_errors))
    root = _safe_root(repository)
    resolved_policy, relative_policy = _safe_policy_path(root, policy_path)
    policy = load_admission_routing_policy(resolved_policy)
    normalized_request = json.loads(json.dumps(request, ensure_ascii=False))
    policy_digest = _digest(policy)
    request_digest = _digest(normalized_request)
    tracked_clean = _policy_is_tracked_clean(root, relative_policy)
    request_class = normalized_request["request_class"]
    material = sorted(
        key for key, value in normalized_request["characteristics"].items() if value
    )
    route: str
    reasons: list[str]
    plan: TaskAdmissionPlan | None = None

    if request_class in NO_WRITE_CLASSES:
        route = "observe_only"
        reasons = ["request_declares_no_repository_write", "no_task_or_confirmation_required"]
    elif material:
        route = "full_review"
        reasons = ["material_characteristic_declared", *[f"material_{item}" for item in material]]
    elif request_class == "active_task_continuation":
        try:
            task_path, session = resolve_active_task(root)
            document = json.loads(task_path.read_text(encoding="utf-8"))
            claimed = normalized_request["active_task"]
            if (
                claimed["task_id"] == session.task_id
                and claimed["task_digest"] == session.task_digest
                and canonical_task_digest(document) == session.task_digest
            ):
                route = "continue_active"
                reasons = ["local_active_task_identity_matches", "no_material_change_declared"]
            else:
                route = "human_review"
                reasons = ["active_task_identity_mismatch"]
        except (FileNotFoundError, OSError, ValueError, SessionPolicyError):
            route = "human_review"
            reasons = ["active_task_not_locally_verified"]
    else:
        proposal = normalized_request["proposal"]
        fast = policy["fast_track"]
        task = proposal["task"]
        constraints: list[str] = []
        if policy["decision"]["state"] != "admitted":
            constraints.append("policy_not_admitted")
        if not tracked_clean:
            constraints.append("policy_not_tracked_and_clean")
        if fast["enabled"] is not True:
            constraints.append("fast_track_disabled")
        if policy["authority"]["permits_noninteractive_fast_track_task_creation"] is not True:
            constraints.append("fast_track_authority_not_delegated")
        scope = task["scope"]
        if len(scope["include_paths"]) > fast["max_include_paths"]:
            constraints.append("include_path_budget_exceeded")
        if len(scope["exclude_paths"]) > fast["max_exclude_paths"]:
            constraints.append("exclude_path_budget_exceeded")
        if not all(
            _scope_allowed(path, fast["allowed_scope_prefixes"], fast["denied_scope_prefixes"])
            for path in scope["include_paths"]
        ):
            constraints.append("scope_outside_standing_delegation")
        if len(task["validation_commands"]) > fast["max_validation_commands"]:
            constraints.append("validation_command_budget_exceeded")
        if not all(
            _command_allowed(command, fast["validation_command_prefixes"])
            for command in task["validation_commands"]
        ):
            constraints.append("validation_command_outside_standing_delegation")
        if len(task["risk"]["items"]) > fast["max_risk_items"]:
            constraints.append("risk_item_budget_exceeded")
        if len(task["assumptions"]) > fast["max_assumptions"]:
            constraints.append("assumption_budget_exceeded")
        if task["unknowns"]:
            constraints.append("proposal_has_unknowns")
        try:
            plan = build_task_admission_plan(root, proposal)
        except TaskProposalPolicyError:
            constraints.append("task_admission_plan_requires_review")
        if constraints:
            route = "human_review"
            reasons = constraints
        else:
            if plan is not None:
                route = "fast_track"
                reasons = ["admitted_clean_policy_delegates_bounded_low_risk_task"]
            else:  # Defensive: plan construction above must either succeed or add a constraint.
                route = "human_review"
                reasons = ["task_admission_plan_requires_review"]

    planned, maximum = _route_budget(policy, route)
    return AdmissionRoute(
        root=root,
        policy_path=resolved_policy,
        policy_relative_path=relative_policy,
        policy=policy,
        policy_digest=policy_digest,
        policy_tracked_clean=tracked_clean,
        request=normalized_request,
        request_digest=request_digest,
        route=route,
        reason_codes=tuple(reasons),
        planned_human_interruptions=planned,
        max_human_interruptions=maximum,
        admission_plan=plan,
    )


def admission_route_document(
    route: AdmissionRoute,
    *,
    decision_applied: bool = False,
) -> Mapping[str, Any]:
    """Return the strict machine-readable route document used for digest binding."""

    task_plan = None
    if route.admission_plan is not None:
        task_plan = {
            "target": route.admission_plan.target,
            "task_id": route.admission_plan.task_document["task_id"],
            "task_digest": route.admission_plan.task_digest,
        }
    standing = route.route == "fast_track"
    return {
        "contract": ADMISSION_ROUTE_CONTRACT,
        "schema_version": ADMISSION_ROUTE_SCHEMA_VERSION,
        "policy": {
            "path": route.policy_relative_path,
            "policy_id": route.policy["policy_id"],
            "policy_digest": route.policy_digest,
            "state": route.policy["decision"]["state"],
            "tracked_clean": route.policy_tracked_clean,
        },
        "request": {
            "request_id": route.request["request_id"],
            "request_digest": route.request_digest,
            "request_class": route.request["request_class"],
        },
        "route": route.route,
        "reason_codes": list(route.reason_codes),
        "friction": {
            "planned_human_interruptions": route.planned_human_interruptions,
            "max_human_interruptions": route.max_human_interruptions,
            "within_budget": route.planned_human_interruptions <= route.max_human_interruptions,
        },
        "task_plan": task_plan,
        "authority_boundary": {
            "standing_policy_authorizes_task_admission": standing,
            "decision_applied": decision_applied,
            "repository_modified": decision_applied,
            "task_admitted": decision_applied,
            "session_started": False,
            "authorizes_code_change": False,
            "authorizes_scope_expansion": False,
            "authorizes_exception": False,
            "authorizes_git_operations": False,
            "authorizes_deployment": False,
            "authorizes_release": False,
        },
    }


def render_admission_route_json(route: AdmissionRoute, *, decision_applied: bool = False) -> str:
    return json.dumps(
        admission_route_document(route, decision_applied=decision_applied),
        ensure_ascii=False, indent=2, sort_keys=True,
    ) + "\n"


def render_admission_route_terminal(route: AdmissionRoute) -> str:
    lines = [
        "ADMISSION ROUTE",
        f"REQUEST {route.request['request_id']} ({route.request['request_class']})",
        f"REQUEST_DIGEST {route.request_digest}",
        f"POLICY {route.policy['policy_id']} ({route.policy_relative_path})",
        f"POLICY_DIGEST {route.policy_digest}",
        f"POLICY_TRACKED_CLEAN {str(route.policy_tracked_clean).lower()}",
        f"ROUTE {route.route}",
        f"HUMAN_INTERRUPTION_BUDGET {route.planned_human_interruptions}/{route.max_human_interruptions}",
    ]
    lines.extend(f"REASON {reason}" for reason in route.reason_codes)
    if route.admission_plan is not None:
        lines.extend(
            (
                f"TASK {route.admission_plan.task_document['task_id']}",
                f"TARGET {route.admission_plan.target}",
                f"TASK_DIGEST {route.admission_plan.task_digest}",
            )
        )
    lines.append(
        "AUTHORITY decision_applied=false repository_modified=false session_started=false "
        "code_change=false scope_expansion=false exception=false git_operations=false "
        "deployment=false release=false"
    )
    if route.route == "observe_only":
        lines.append("NEXT answer or inspect read-only; create no task and perform no repository write")
    elif route.route == "continue_active":
        lines.append("NEXT continue only inside the locally verified active task; do not readmit it")
    elif route.route == "fast_track":
        lines.append("NEXT apply the standing-policy route or leave this preview read-only")
    elif route.route == "human_review":
        lines.append("NEXT use the existing task proposal preview and one human decision")
    else:
        lines.append("NEXT perform full human review before any repository change")
    return "\n".join(lines) + "\n"


def apply_fast_track_route(route: AdmissionRoute) -> TaskAdmissionResult:
    """Apply only a still-valid route whose authority comes from standing policy."""

    if route.route != "fast_track" or route.admission_plan is None:
        raise AdmissionRoutingError("only a fast_track route can be applied non-interactively")
    if _digest(route.policy) != route.policy_digest or _digest(route.request) != route.request_digest:
        raise AdmissionRoutingError("routing inputs changed after preview")
    current_policy = load_admission_routing_policy(route.policy_path)
    if _digest(current_policy) != route.policy_digest:
        raise AdmissionRoutingError("admission policy changed after routing")
    target = route.root / Path(*PurePosixPath(route.admission_plan.target).parts)
    if target.exists() or target.is_symlink():
        raise AdmissionRoutingError("task target appeared after routing and was not overwritten")
    rebuilt = build_admission_route(
        route.root,
        policy_path=route.policy_path,
        request=route.request,
    )
    if (
        rebuilt.route != "fast_track"
        or rebuilt.policy_digest != route.policy_digest
        or rebuilt.request_digest != route.request_digest
        or rebuilt.admission_plan is None
        or rebuilt.admission_plan.task_digest != route.admission_plan.task_digest
    ):
        raise AdmissionRoutingError("fast-track authority or task plan changed after routing")
    try:
        return apply_task_admission_plan(route.admission_plan)
    except TaskProposalPolicyError as exc:
        raise AdmissionRoutingError(str(exc)) from exc
