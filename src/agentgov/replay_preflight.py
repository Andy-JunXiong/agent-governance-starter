"""Deterministic, read-only clean-target replay preflight."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from agentgov.path_policy import scope_path_error


REPLAY_PREFLIGHT_PLAN_CONTRACT = "agentgov.replay-preflight-plan"
REPLAY_PREFLIGHT_REPORT_CONTRACT = "agentgov.replay-preflight-report"
REPLAY_ADAPTER_METADATA_CONTRACT = "agentgov.replay-adapter-metadata"
REPLAY_PREFLIGHT_SCHEMA_VERSION = "1.0"

_CORRELATION_ID_RE = re.compile(r"^rpf-[0-9a-f]{16}$")
_GIT_SHA_RE = re.compile(r"^[0-9a-f]{40,64}$")
_NORMALIZED_ID_RE = re.compile(r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$")
_TASK_ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_VERSION_RE = re.compile(r"^[0-9]+(?:\.[0-9]+){1,3}(?:(?:a|b|rc)[0-9]+)?$")
_PROTOCOL_RE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")
_PRECONDITION_KINDS = {
    "path_absent",
    "text_absent",
    "text_present",
    "sha256_equals",
}

AUTHORITY_BOUNDARY = {
    "authorizes_cleanup": False,
    "authorizes_deployment": False,
    "authorizes_git_operations": False,
    "authorizes_publication": False,
    "authorizes_release": False,
    "authorizes_replay": False,
    "authorizes_repository_write": False,
    "authorizes_task_admission": False,
}


class ReplayPreflightPlanError(ValueError):
    """The replay-preflight plan is invalid or unsafe to interpret."""


class ReplayPreflightStatus(str, Enum):
    READY = "READY"
    BLOCKED = "BLOCKED"
    UNKNOWN = "UNKNOWN"


class ReplayPreflightFindingStatus(str, Enum):
    PASS = "PASS"
    BLOCKED = "BLOCKED"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class ReplayPreflightFinding:
    status: ReplayPreflightFindingStatus
    check_id: str
    reason_code: str | None
    message: str


@dataclass(frozen=True)
class ReplayPreflightReport:
    contract: str
    schema_version: str
    correlation_id: str
    status: ReplayPreflightStatus
    preconditions_ready: bool
    observed_head_sha: str | None
    findings: tuple[ReplayPreflightFinding, ...]
    reason_codes: tuple[str, ...]
    known_limits: tuple[str, ...]
    authority_boundary: Mapping[str, bool]


def _json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ReplayPreflightPlanError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _load_json(path: Path, *, label: str) -> Mapping[str, Any]:
    try:
        document = json.loads(
            path.read_text(encoding="utf-8"), object_pairs_hook=_json_object
        )
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ReplayPreflightPlanError(f"cannot read {label}: {exc}") from exc
    if not isinstance(document, Mapping):
        raise ReplayPreflightPlanError(f"{label} must contain a JSON object")
    return document


def _exact_fields(
    value: Any,
    *,
    path: str,
    fields: set[str],
    errors: list[str],
) -> Mapping[str, Any] | None:
    if not isinstance(value, Mapping):
        errors.append(f"{path} must be an object")
        return None
    actual = set(value)
    for field in sorted(fields - actual):
        errors.append(f"{path}.{field} is required")
    for field in sorted(actual - fields):
        errors.append(f"{path}.{field} is not allowed")
    return value


def _relative_path(value: Any, *, path: str, errors: list[str]) -> str | None:
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{path} must be a non-empty repository-relative path")
        return None
    problem = scope_path_error(value)
    if problem:
        errors.append(f"{path} {problem}")
        return None
    return value


def validate_replay_preflight_plan(document: Any) -> list[str]:
    """Return deterministic plan validation errors without inspecting a repository."""

    errors: list[str] = []
    root = _exact_fields(
        document,
        path="$",
        fields={
            "contract",
            "schema_version",
            "correlation",
            "repository",
            "targets",
            "related_tasks",
            "adapter",
            "authority_boundary",
        },
        errors=errors,
    )
    if root is None:
        return errors
    if root.get("contract") != REPLAY_PREFLIGHT_PLAN_CONTRACT:
        errors.append(f"$.contract must equal {REPLAY_PREFLIGHT_PLAN_CONTRACT!r}")
    if root.get("schema_version") != REPLAY_PREFLIGHT_SCHEMA_VERSION:
        errors.append(
            f"$.schema_version must equal {REPLAY_PREFLIGHT_SCHEMA_VERSION!r}"
        )

    correlation = _exact_fields(
        root.get("correlation"),
        path="$.correlation",
        fields={"correlation_id", "registry_directory"},
        errors=errors,
    )
    if correlation is not None:
        correlation_id = correlation.get("correlation_id")
        if not isinstance(correlation_id, str) or not _CORRELATION_ID_RE.fullmatch(
            correlation_id
        ):
            errors.append("$.correlation.correlation_id must match ^rpf-[0-9a-f]{16}$")
        _relative_path(
            correlation.get("registry_directory"),
            path="$.correlation.registry_directory",
            errors=errors,
        )

    repository = _exact_fields(
        root.get("repository"),
        path="$.repository",
        fields={"expected_head_sha"},
        errors=errors,
    )
    if repository is not None:
        expected_sha = repository.get("expected_head_sha")
        if not isinstance(expected_sha, str) or not _GIT_SHA_RE.fullmatch(expected_sha):
            errors.append("$.repository.expected_head_sha must be a lowercase Git SHA")

    targets = root.get("targets")
    target_paths: list[str] = []
    if not isinstance(targets, list) or not 1 <= len(targets) <= 50:
        errors.append("$.targets must contain between 1 and 50 target objects")
    else:
        for index, item in enumerate(targets):
            item_path = f"$.targets[{index}]"
            target = _exact_fields(
                item,
                path=item_path,
                fields={"path", "precondition"},
                errors=errors,
            )
            if target is None:
                continue
            target_path = _relative_path(
                target.get("path"), path=f"{item_path}.path", errors=errors
            )
            if target_path is not None:
                target_paths.append(target_path)
            precondition = _exact_fields(
                target.get("precondition"),
                path=f"{item_path}.precondition",
                fields={"kind", "value"},
                errors=errors,
            )
            if precondition is None:
                continue
            kind = precondition.get("kind")
            value = precondition.get("value")
            if kind not in _PRECONDITION_KINDS:
                errors.append(
                    f"{item_path}.precondition.kind must be one of {sorted(_PRECONDITION_KINDS)}"
                )
            elif kind == "path_absent":
                if value is not None:
                    errors.append(
                        f"{item_path}.precondition.value must be null for path_absent"
                    )
            elif not isinstance(value, str) or not value or len(value) > 400:
                errors.append(
                    f"{item_path}.precondition.value must be a non-empty string of at most 400 characters"
                )
            elif kind == "sha256_equals" and not re.fullmatch(
                r"[0-9a-f]{64}", value
            ):
                errors.append(
                    f"{item_path}.precondition.value must be a lowercase SHA-256 digest"
                )
        if len(target_paths) != len(set(target_paths)):
            errors.append("$.targets paths must be unique")

    related = _exact_fields(
        root.get("related_tasks"),
        path="$.related_tasks",
        fields={"directory", "absent_task_ids"},
        errors=errors,
    )
    if related is not None:
        _relative_path(
            related.get("directory"), path="$.related_tasks.directory", errors=errors
        )
        task_ids = related.get("absent_task_ids")
        if not isinstance(task_ids, list) or len(task_ids) > 50:
            errors.append("$.related_tasks.absent_task_ids must contain at most 50 ids")
        elif any(
            not isinstance(item, str) or not _TASK_ID_RE.fullmatch(item)
            for item in task_ids
        ):
            errors.append(
                "$.related_tasks.absent_task_ids must contain normalized task ids"
            )
        elif len(task_ids) != len(set(task_ids)):
            errors.append("$.related_tasks.absent_task_ids must be unique")

    adapter = _exact_fields(
        root.get("adapter"),
        path="$.adapter",
        fields={
            "metadata_path",
            "expected_adapter_id",
            "expected_adapter_version",
            "expected_protocol_version",
        },
        errors=errors,
    )
    if adapter is not None:
        _relative_path(
            adapter.get("metadata_path"), path="$.adapter.metadata_path", errors=errors
        )
        adapter_id = adapter.get("expected_adapter_id")
        if not isinstance(adapter_id, str) or not _NORMALIZED_ID_RE.fullmatch(adapter_id):
            errors.append("$.adapter.expected_adapter_id must be a normalized identifier")
        adapter_version = adapter.get("expected_adapter_version")
        if not isinstance(adapter_version, str) or not _VERSION_RE.fullmatch(
            adapter_version
        ):
            errors.append("$.adapter.expected_adapter_version must be a version")
        protocol = adapter.get("expected_protocol_version")
        if not isinstance(protocol, str) or not _PROTOCOL_RE.fullmatch(protocol):
            errors.append("$.adapter.expected_protocol_version must be YYYY-MM-DD")

    authority = root.get("authority_boundary")
    if not isinstance(authority, Mapping) or dict(authority) != AUTHORITY_BOUNDARY:
        errors.append("$.authority_boundary must deny every replay and action authority")
    return errors


def load_replay_preflight_plan(path: Path) -> Mapping[str, Any]:
    document = _load_json(path, label="replay-preflight plan")
    errors = validate_replay_preflight_plan(document)
    if errors:
        raise ReplayPreflightPlanError("; ".join(errors))
    return document


def _safe_root(repository: Path) -> Path:
    if repository.is_symlink():
        raise OSError("repository root must not be a symbolic link")
    if not repository.exists():
        raise OSError("repository root does not exist")
    if not repository.is_dir():
        raise OSError("repository root is not a directory")
    return repository.resolve()


def _run_git(root: Path, *arguments: str) -> bytes:
    completed = subprocess.run(
        ("git", "-c", "core.quotepath=false", "-C", str(root), *arguments),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=30,
    )
    if completed.returncode != 0:
        message = completed.stderr.decode("utf-8", errors="replace").strip()
        raise OSError(message or f"git {' '.join(arguments)} failed")
    return completed.stdout


def _decode_path(value: bytes) -> str:
    try:
        return value.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise OSError("Git reported a path that is not valid UTF-8") from exc


def _parse_changed_paths(output: bytes) -> set[str]:
    tokens = output.split(b"\0")
    if tokens and tokens[-1] == b"":
        tokens.pop()
    paths: set[str] = set()
    index = 0
    while index < len(tokens):
        try:
            status = tokens[index].decode("ascii")
        except UnicodeDecodeError as exc:
            raise OSError("Git reported a non-ASCII status") from exc
        index += 1
        count = 2 if status[:1] in {"R", "C"} else 1
        if index + count > len(tokens):
            raise OSError("Git returned an incomplete changed-path record")
        for _ in range(count):
            paths.add(_decode_path(tokens[index]))
            index += 1
    return paths


def _git_facts(root: Path) -> tuple[str, set[str]]:
    reported_root = Path(
        _run_git(root, "rev-parse", "--show-toplevel").decode("utf-8").strip()
    ).resolve()
    if reported_root != root:
        raise OSError(f"repository must be the Git worktree root; Git reported {reported_root}")
    head = _run_git(root, "rev-parse", "HEAD").decode("ascii").strip()
    if not _GIT_SHA_RE.fullmatch(head):
        raise OSError("Git reported an invalid HEAD revision")
    changed = _parse_changed_paths(
        _run_git(root, "diff", "HEAD", "--name-status", "-z", "--find-renames")
    )
    untracked = _run_git(root, "ls-files", "--others", "--exclude-standard", "-z")
    changed.update(_decode_path(item) for item in untracked.split(b"\0") if item)
    return head, changed


def _inside(root: Path, relative: str) -> Path:
    return root.joinpath(*relative.split("/"))


def _has_symlink_component(root: Path, relative: str) -> bool:
    candidate = root
    for segment in relative.split("/"):
        candidate = candidate / segment
        if candidate.is_symlink():
            return True
    return False


def _finding(
    status: ReplayPreflightFindingStatus,
    check_id: str,
    message: str,
    reason_code: str | None = None,
) -> ReplayPreflightFinding:
    return ReplayPreflightFinding(status, check_id, reason_code, message)


def _target_precondition_finding(
    root: Path, target: Mapping[str, Any]
) -> ReplayPreflightFinding:
    relative = str(target["path"])
    check_id = f"target:{relative}:prestate"
    path = _inside(root, relative)
    condition = target["precondition"]
    kind = condition["kind"]
    value = condition["value"]
    if _has_symlink_component(root, relative):
        return _finding(
            ReplayPreflightFindingStatus.UNKNOWN,
            check_id,
            f"target {relative!r} is a symbolic link and was not followed",
            "target_unreadable",
        )
    if kind == "path_absent":
        if path.exists():
            return _finding(
                ReplayPreflightFindingStatus.BLOCKED,
                check_id,
                f"target {relative!r} already exists",
                "target_prestate_failed",
            )
        return _finding(
            ReplayPreflightFindingStatus.PASS,
            check_id,
            f"target {relative!r} is absent as required",
        )
    if not path.exists() or not path.is_file():
        return _finding(
            ReplayPreflightFindingStatus.BLOCKED,
            check_id,
            f"target {relative!r} is not a readable regular file",
            "target_missing",
        )
    try:
        payload = path.read_bytes()
    except OSError:
        return _finding(
            ReplayPreflightFindingStatus.UNKNOWN,
            check_id,
            f"target {relative!r} could not be read",
            "target_unreadable",
        )
    if kind == "sha256_equals":
        matches = hashlib.sha256(payload).hexdigest() == value
    else:
        try:
            text = payload.decode("utf-8")
        except UnicodeDecodeError:
            return _finding(
                ReplayPreflightFindingStatus.UNKNOWN,
                check_id,
                f"target {relative!r} is not valid UTF-8",
                "target_unreadable",
            )
        matches = value not in text if kind == "text_absent" else value in text
    if not matches:
        return _finding(
            ReplayPreflightFindingStatus.BLOCKED,
            check_id,
            f"target {relative!r} does not satisfy {kind}",
            "target_prestate_failed",
        )
    return _finding(
        ReplayPreflightFindingStatus.PASS,
        check_id,
        f"target {relative!r} satisfies {kind}",
    )


def _adapter_findings(
    root: Path, expected: Mapping[str, Any]
) -> tuple[ReplayPreflightFinding, ...]:
    relative = str(expected["metadata_path"])
    path = _inside(root, relative)
    if _has_symlink_component(root, relative) or not path.is_file():
        return (
            _finding(
                ReplayPreflightFindingStatus.UNKNOWN,
                "adapter:metadata",
                f"local Adapter metadata {relative!r} is unavailable",
                "adapter_metadata_unavailable",
            ),
        )
    try:
        metadata = _load_json(path, label="Adapter metadata")
    except ReplayPreflightPlanError:
        return (
            _finding(
                ReplayPreflightFindingStatus.UNKNOWN,
                "adapter:metadata",
        "local Adapter metadata is invalid or unreadable",
                "adapter_metadata_invalid",
            ),
        )
    fields = {
        "contract",
        "schema_version",
        "adapter_id",
        "adapter_version",
        "protocol_version",
    }
    if set(metadata) != fields or (
        metadata.get("contract") != REPLAY_ADAPTER_METADATA_CONTRACT
        or metadata.get("schema_version") != REPLAY_PREFLIGHT_SCHEMA_VERSION
        or not isinstance(metadata.get("adapter_id"), str)
        or not _NORMALIZED_ID_RE.fullmatch(metadata["adapter_id"])
        or not isinstance(metadata.get("adapter_version"), str)
        or not _VERSION_RE.fullmatch(metadata["adapter_version"])
        or not isinstance(metadata.get("protocol_version"), str)
        or not _PROTOCOL_RE.fullmatch(metadata["protocol_version"])
    ):
        return (
            _finding(
                ReplayPreflightFindingStatus.UNKNOWN,
                "adapter:metadata",
                "local Adapter metadata does not match the strict metadata contract",
                "adapter_metadata_invalid",
            ),
        )
    observed = (
        metadata["adapter_id"],
        metadata["adapter_version"],
        metadata["protocol_version"],
    )
    wanted = (
        expected["expected_adapter_id"],
        expected["expected_adapter_version"],
        expected["expected_protocol_version"],
    )
    if observed != wanted:
        return (
            _finding(
                ReplayPreflightFindingStatus.BLOCKED,
                "adapter:identity",
                "local Adapter identity or protocol does not match the replay plan",
                "adapter_mismatch",
            ),
        )
    return (
        _finding(
            ReplayPreflightFindingStatus.PASS,
            "adapter:identity",
            "local Adapter identity and protocol match the replay plan",
        ),
    )


def evaluate_replay_preflight(
    document: Mapping[str, Any], *, repository: Path
) -> ReplayPreflightReport:
    """Evaluate one validated replay plan without changing local or external state."""

    errors = validate_replay_preflight_plan(document)
    if errors:
        raise ReplayPreflightPlanError("; ".join(errors))
    correlation_id = str(document["correlation"]["correlation_id"])
    findings: list[ReplayPreflightFinding] = []
    observed_head: str | None = None
    changed_paths: set[str] | None = None
    try:
        root = _safe_root(repository)
    except OSError as exc:
        findings.append(
            _finding(
                ReplayPreflightFindingStatus.UNKNOWN,
                "repository:git",
                f"repository facts are unavailable: {exc}",
                "git_unavailable",
            )
        )
        root = repository.resolve()
    else:
        try:
            observed_head, changed_paths = _git_facts(root)
        except (OSError, UnicodeError, subprocess.SubprocessError) as exc:
            findings.append(
                _finding(
                    ReplayPreflightFindingStatus.UNKNOWN,
                    "repository:git",
                    f"Git facts are unavailable: {exc}",
                    "git_unavailable",
                )
            )
        else:
            if observed_head != document["repository"]["expected_head_sha"]:
                findings.append(
                    _finding(
                        ReplayPreflightFindingStatus.BLOCKED,
                        "repository:head",
                        "repository HEAD does not match the replay plan",
                        "stale_repository_revision",
                    )
                )
            else:
                findings.append(
                    _finding(
                        ReplayPreflightFindingStatus.PASS,
                        "repository:head",
                        "repository HEAD matches the replay plan",
                    )
                )

    if root.exists() and root.is_dir():
        for target in document["targets"]:
            relative = str(target["path"])
            if changed_paths is None:
                findings.append(
                    _finding(
                        ReplayPreflightFindingStatus.UNKNOWN,
                        f"target:{relative}:clean",
                        f"target {relative!r} cleanliness cannot be established",
                        "git_unavailable",
                    )
                )
            elif relative in changed_paths:
                findings.append(
                    _finding(
                        ReplayPreflightFindingStatus.BLOCKED,
                        f"target:{relative}:clean",
                        f"target {relative!r} has staged, unstaged, renamed, or untracked changes",
                        "target_dirty",
                    )
                )
            else:
                findings.append(
                    _finding(
                        ReplayPreflightFindingStatus.PASS,
                        f"target:{relative}:clean",
                        f"target {relative!r} has no working-tree change",
                    )
                )
            findings.append(_target_precondition_finding(root, target))

        related = document["related_tasks"]
        task_directory = _inside(root, str(related["directory"]))
        if _has_symlink_component(root, str(related["directory"])) or (
            task_directory.exists() and not task_directory.is_dir()
        ):
            findings.append(
                _finding(
                    ReplayPreflightFindingStatus.UNKNOWN,
                    "tasks:registry",
                    "related-task directory cannot be inspected safely",
                    "task_registry_unavailable",
                )
            )
        else:
            for task_id in related["absent_task_ids"]:
                candidate = task_directory / f"{task_id}.json"
                if candidate.exists() or candidate.is_symlink():
                    findings.append(
                        _finding(
                            ReplayPreflightFindingStatus.BLOCKED,
                            f"task:{task_id}:absent",
                            f"related task {task_id!r} already exists",
                            "task_collision",
                        )
                    )
                else:
                    findings.append(
                        _finding(
                            ReplayPreflightFindingStatus.PASS,
                            f"task:{task_id}:absent",
                            f"related task {task_id!r} is absent",
                        )
                    )

        findings.extend(_adapter_findings(root, document["adapter"]))
        registry = _inside(root, str(document["correlation"]["registry_directory"]))
        if _has_symlink_component(
            root, str(document["correlation"]["registry_directory"])
        ) or (registry.exists() and not registry.is_dir()):
            findings.append(
                _finding(
                    ReplayPreflightFindingStatus.UNKNOWN,
                    "correlation:registry",
                    "correlation registry cannot be inspected safely",
                    "correlation_registry_unavailable",
                )
            )
        else:
            marker = registry / f"{correlation_id}.json"
            if marker.exists() or marker.is_symlink():
                findings.append(
                    _finding(
                        ReplayPreflightFindingStatus.BLOCKED,
                        "correlation:unique",
                        f"correlation identifier {correlation_id!r} already has a local marker",
                        "duplicate_correlation",
                    )
                )
            else:
                findings.append(
                    _finding(
                        ReplayPreflightFindingStatus.PASS,
                        "correlation:unique",
                        f"correlation identifier {correlation_id!r} has no local marker",
                    )
                )

    statuses = {item.status for item in findings}
    if ReplayPreflightFindingStatus.UNKNOWN in statuses:
        status = ReplayPreflightStatus.UNKNOWN
    elif ReplayPreflightFindingStatus.BLOCKED in statuses:
        status = ReplayPreflightStatus.BLOCKED
    else:
        status = ReplayPreflightStatus.READY
    reason_codes = tuple(
        dict.fromkeys(
            item.reason_code for item in findings if item.reason_code is not None
        )
    )
    return ReplayPreflightReport(
        contract=REPLAY_PREFLIGHT_REPORT_CONTRACT,
        schema_version=REPLAY_PREFLIGHT_SCHEMA_VERSION,
        correlation_id=correlation_id,
        status=status,
        preconditions_ready=status is ReplayPreflightStatus.READY,
        observed_head_sha=observed_head,
        findings=tuple(findings),
        reason_codes=reason_codes,
        known_limits=(
            "Explicit pre-state conditions do not prove semantic equivalence outside the named checks.",
            "A missing correlation marker means no recorded collision; this check does not reserve the identifier.",
            "READY establishes replay prerequisites only and grants no authority to start a replay.",
        ),
        authority_boundary=dict(AUTHORITY_BOUNDARY),
    )


def render_replay_preflight_json(report: ReplayPreflightReport) -> str:
    return json.dumps(asdict(report), indent=2, sort_keys=True) + "\n"


def render_replay_preflight_terminal(report: ReplayPreflightReport) -> str:
    lines = [
        f"PREFLIGHT correlation={report.correlation_id} status={report.status.value}",
        *(
            f"{item.status.value} {item.check_id}: {item.message}"
            for item in report.findings
        ),
    ]
    if report.status is ReplayPreflightStatus.READY:
        lines.append("NEXT prerequisites are ready; obtain separate human replay authorization")
    else:
        lines.append("BLOCK replay prerequisites are not ready; do not consume the replay")
    lines.append(
        "NOTE preflight is read-only and grants no cleanup, task, replay, Git, release, deployment, or publication authority"
    )
    return "\n".join(lines)
