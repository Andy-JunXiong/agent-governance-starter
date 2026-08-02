"""Read-only Git change inventory and admitted-task scope comparison."""

from __future__ import annotations

import json
import subprocess
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Mapping

from agentgov.path_policy import PathScopeDecision, evaluate_path_scope, is_segment_prefix
from agentgov.task_contract import (
    canonical_task_digest,
    check_development_task,
    load_development_task,
)


SCOPE_REPORT_CONTRACT = "agentgov.development-scope-report"
SCOPE_REPORT_SCHEMA_VERSION = "1.0"

_LAYER_ORDER = {"staged": 0, "unstaged": 1, "untracked": 2}
_STATUS_NAMES = {
    "A": "added",
    "C": "copied",
    "D": "deleted",
    "M": "modified",
    "R": "renamed",
    "T": "type_changed",
    "U": "unmerged",
    "X": "unknown",
}


class ScopeFindingStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    ADVISORY = "ADVISORY"


class ScopePolicyError(ValueError):
    """A deterministic task fact blocks a truthful scope comparison."""


class GitInspectionError(RuntimeError):
    """Git could not produce a trustworthy read-only inventory."""


@dataclass(frozen=True)
class ScopeEndpoint:
    role: str
    path: str
    admitted: bool
    matched_include: str | None
    matched_exclude: str | None
    reason: str


@dataclass(frozen=True)
class GitChange:
    layer: str
    status: str
    path: str
    old_path: str | None
    endpoints: tuple[ScopeEndpoint, ...]

    @property
    def admitted(self) -> bool:
        return all(endpoint.admitted for endpoint in self.endpoints)


@dataclass(frozen=True)
class ScopeFinding:
    status: ScopeFindingStatus
    check_id: str
    message: str


@dataclass(frozen=True)
class DevelopmentScopeReport:
    contract: str
    schema_version: str
    task_id: str
    task_path: str
    task_digest: str
    head_sha: str
    changes: tuple[GitChange, ...]
    findings: tuple[ScopeFinding, ...]
    known_limits: tuple[str, ...]
    authority_boundary: Mapping[str, bool]

    @property
    def has_failures(self) -> bool:
        return any(item.status is ScopeFindingStatus.FAIL for item in self.findings)

    def count(self, status: ScopeFindingStatus) -> int:
        return sum(item.status is status for item in self.findings)


def _safe_root(repository: Path) -> Path:
    if repository.is_symlink():
        raise ValueError("repository root must not be a symbolic link")
    if not repository.exists():
        raise FileNotFoundError(repository)
    if not repository.is_dir():
        raise ValueError("repository root must be a directory")
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
        raise GitInspectionError(message or f"git {' '.join(arguments)} failed")
    return completed.stdout


def _decode_path(value: bytes) -> str:
    try:
        return value.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise GitInspectionError("Git reported a path that is not valid UTF-8") from exc


def _require_repository_root(root: Path) -> str:
    reported = _run_git(root, "rev-parse", "--show-toplevel")
    try:
        git_root = Path(reported.decode("utf-8").strip()).resolve()
    except UnicodeDecodeError as exc:
        raise GitInspectionError("Git repository root is not valid UTF-8") from exc
    if git_root != root:
        raise GitInspectionError(
            f"repository must be the Git worktree root; Git reported {git_root}"
        )
    return _run_git(root, "rev-parse", "HEAD").decode("ascii").strip()


def _parse_name_status(output: bytes, *, layer: str) -> list[tuple[str, str, str | None]]:
    tokens = output.split(b"\0")
    if tokens and tokens[-1] == b"":
        tokens.pop()
    changes: list[tuple[str, str, str | None]] = []
    index = 0
    while index < len(tokens):
        try:
            status_token = tokens[index].decode("ascii")
        except UnicodeDecodeError as exc:
            raise GitInspectionError(f"Git reported a non-ASCII status in {layer}") from exc
        index += 1
        status_code = status_token[:1]
        if status_code in {"R", "C"}:
            if index + 1 >= len(tokens):
                raise GitInspectionError(f"Git returned an incomplete {status_token} record")
            old_path = _decode_path(tokens[index])
            path = _decode_path(tokens[index + 1])
            index += 2
        else:
            if index >= len(tokens):
                raise GitInspectionError(f"Git returned an incomplete {status_token} record")
            old_path = None
            path = _decode_path(tokens[index])
            index += 1
        changes.append((_STATUS_NAMES.get(status_code, "unknown"), path, old_path))
    return changes


def _inventory_changes(root: Path) -> tuple[str, list[tuple[str, str, str, str | None]]]:
    head_sha = _require_repository_root(root)
    staged = _parse_name_status(
        _run_git(root, "diff", "--cached", "--name-status", "-z", "--find-renames"),
        layer="staged",
    )
    unstaged = _parse_name_status(
        _run_git(root, "diff", "--name-status", "-z", "--find-renames"),
        layer="unstaged",
    )
    untracked_output = _run_git(root, "ls-files", "--others", "--exclude-standard", "-z")
    untracked = [
        ("untracked", _decode_path(value), None)
        for value in untracked_output.split(b"\0")
        if value and not is_segment_prefix(".agentgov", _decode_path(value))
    ]
    records = [
        *(("staged", status, path, old_path) for status, path, old_path in staged),
        *(("unstaged", status, path, old_path) for status, path, old_path in unstaged),
        *(("untracked", status, path, old_path) for status, path, old_path in untracked),
    ]
    records.sort(key=lambda item: (_LAYER_ORDER[item[0]], item[2], item[3] or ""))
    return head_sha, records


def _endpoint(role: str, decision: PathScopeDecision) -> ScopeEndpoint:
    return ScopeEndpoint(
        role=role,
        path=decision.path,
        admitted=decision.admitted,
        matched_include=decision.matched_include,
        matched_exclude=decision.matched_exclude,
        reason=decision.reason,
    )


def check_development_scope(
    task_path: Path,
    *,
    repository: Path,
) -> DevelopmentScopeReport:
    """Compare current Git working-tree changes with one admitted task."""

    root = _safe_root(repository)
    task_report = check_development_task(task_path, repository=root)
    if task_report.has_failures:
        messages = "; ".join(item.message for item in task_report.findings)
        raise ScopePolicyError(f"task contract is not eligible for scope checking: {messages}")
    document = load_development_task(task_report.path)
    decision = document["decision"]
    assert isinstance(decision, Mapping)
    if decision["state"] != "admitted":
        raise ScopePolicyError(
            f"task decision state is {decision['state']!r}; scope checking requires an admitted task"
        )

    scope = document["scope"]
    assert isinstance(scope, Mapping)
    includes = tuple(scope["include_paths"])
    excludes = tuple(scope["exclude_paths"])
    head_sha, records = _inventory_changes(root)
    changes: list[GitChange] = []
    findings: list[ScopeFinding] = []
    for layer, status, path, old_path in records:
        if status == "renamed" and old_path is not None:
            endpoints = (
                _endpoint(
                    "old",
                    evaluate_path_scope(old_path, includes=includes, excludes=excludes),
                ),
                _endpoint(
                    "new",
                    evaluate_path_scope(path, includes=includes, excludes=excludes),
                ),
            )
        else:
            role = "old" if status == "deleted" else "current"
            endpoints = (
                _endpoint(
                    role,
                    evaluate_path_scope(path, includes=includes, excludes=excludes),
                ),
            )
        change = GitChange(
            layer=layer,
            status=status,
            path=path,
            old_path=old_path,
            endpoints=endpoints,
        )
        changes.append(change)
        endpoint_summary = "; ".join(
            f"{item.role}={item.path!r}: {item.reason}" for item in endpoints
        )
        findings.append(
            ScopeFinding(
                ScopeFindingStatus.PASS if change.admitted else ScopeFindingStatus.FAIL,
                f"scope:{layer}:{status}:{path}",
                endpoint_summary,
            )
        )

    if not changes:
        findings.append(
            ScopeFinding(
                ScopeFindingStatus.PASS,
                "scope:working-tree:no-changes",
                "Git reports no staged, unstaged, or non-ignored untracked changes",
            )
        )
    if changes and document.get("architecture_refs"):
        findings.append(
            ScopeFinding(
                ScopeFindingStatus.ADVISORY,
                "architecture:candidate",
                "the task explicitly declares architecture references; an accountable human or coding agent should review the selected architecture context",
            )
        )

    task_relative = task_report.path.relative_to(root).as_posix()
    return DevelopmentScopeReport(
        contract=SCOPE_REPORT_CONTRACT,
        schema_version=SCOPE_REPORT_SCHEMA_VERSION,
        task_id=str(document["task_id"]),
        task_path=task_relative,
        task_digest=canonical_task_digest(document),
        head_sha=head_sha,
        changes=tuple(changes),
        findings=tuple(findings),
        known_limits=(
            "this phase inventories staged, unstaged, and non-ignored untracked working-tree changes; untracked .agentgov local tool state is canonically excluded",
            "committed-since-base changes require the later comparison-base evidence contract",
            "path admission does not prove requirement or architecture correctness",
            "architecture candidates are advisory",
        ),
        authority_boundary={
            "writes_repository": False,
            "modifies_worktree": False,
            "modifies_index": False,
            "modifies_branch": False,
            "modifies_history": False,
            "authorizes_exception": False,
            "authorizes_commit": False,
            "authorizes_merge": False,
        },
    )


def render_scope_report_json(report: DevelopmentScopeReport) -> str:
    payload = asdict(report)
    for finding in payload["findings"]:
        finding["status"] = finding["status"].value
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def render_scope_report_markdown(report: DevelopmentScopeReport) -> str:
    lines = [
        f"# Development scope report: {report.task_id}",
        "",
        f"- Task: `{report.task_path}`",
        f"- Task digest: `{report.task_digest}`",
        f"- Snapshot HEAD: `{report.head_sha}`",
        "",
        "## Findings",
        "",
        "| Status | Check | Message |",
        "|---|---|---|",
    ]
    for finding in report.findings:
        message = finding.message.replace("|", "\\|").replace("\n", " ")
        lines.append(f"| {finding.status.value} | `{finding.check_id}` | {message} |")
    lines.extend(["", "## Known limits", ""])
    lines.extend(f"- {item}" for item in report.known_limits)
    lines.extend(["", "## Authority boundary", ""])
    lines.extend(
        f"- `{key}`: `{str(value).lower()}`"
        for key, value in sorted(report.authority_boundary.items())
    )
    lines.append("")
    return "\n".join(lines)


def render_scope_report_terminal(report: DevelopmentScopeReport) -> str:
    lines = [
        f"SCOPE task={report.task_id} head={report.head_sha}",
        *(f"{item.status.value} {item.check_id}: {item.message}" for item in report.findings),
        "SUMMARY "
        + " ".join(
            f"{status.value}={report.count(status)}" for status in ScopeFindingStatus
        ),
        "NOTE scope inspection was read-only and did not authorize exceptions or Git transitions",
    ]
    return "\n".join(lines) + "\n"
