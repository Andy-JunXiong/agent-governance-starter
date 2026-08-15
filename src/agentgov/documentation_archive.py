"""Planning and explicit safe apply for a development-log archive index."""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from dataclasses import dataclass
from datetime import date
from enum import Enum
from pathlib import Path
from typing import Any, Callable

from agentgov import __version__


ARCHIVE_PLAN_CONTRACT = "agentgov.documentation-archive-plan"
ARCHIVE_PLAN_SCHEMA_VERSION = "1.0"
DEVELOPMENT_LOG_DIRECTORY = Path("docs/development-log")
DEVELOPMENT_LOG_INDEX = DEVELOPMENT_LOG_DIRECTORY / "INDEX.md"
DATED_LOG_PATTERN = re.compile(
    r"^(?P<date>\d{4}-\d{2}-\d{2})(?:-[a-z0-9][a-z0-9-]*)?\.md$"
)


class ArchivePlanState(str, Enum):
    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"
    NOT_APPLICABLE = "not_applicable"


class ArchiveFindingStatus(str, Enum):
    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"
    ADVISORY = "advisory"
    NOT_APPLICABLE = "not_applicable"


class DocumentationArchiveApplyError(ValueError):
    """Raised when an archive-index plan is unsafe or stale at apply time."""


@dataclass(frozen=True)
class ArchiveFinding:
    status: ArchiveFindingStatus
    semantics: str
    code: str
    message: str
    path: Path | None = None


@dataclass(frozen=True)
class ArchiveEntry:
    path: Path
    record_date: date
    title: str
    sha256: str


@dataclass(frozen=True)
class ArchiveIndexChange:
    path: Path
    action: str
    before_sha256: str | None
    after_sha256: str
    content: str


@dataclass(frozen=True)
class DocumentationArchivePlan:
    root: Path
    through_date: date
    state: ArchivePlanState
    entries: tuple[ArchiveEntry, ...]
    change: ArchiveIndexChange | None
    findings: tuple[ArchiveFinding, ...]


@dataclass(frozen=True)
class DocumentationArchiveApplyResult:
    root: Path
    path: Path
    action: str
    sha256: str


def parse_through_date(value: str) -> date:
    """Parse one strict ISO calendar date without consulting the host clock."""

    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise ValueError("through date must use strict YYYY-MM-DD format")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError("through date must be a valid calendar date") from exc


def _sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _sha256_text(content: str) -> str:
    return _sha256_bytes(content.encode("utf-8"))


def _resolve_root(root: Path) -> Path:
    if root.is_symlink():
        raise ValueError("repository root must not be a symbolic link")
    if not root.exists():
        raise FileNotFoundError(root)
    if not root.is_dir():
        raise ValueError("repository root is not a directory")
    return root.resolve()


def _fallback_title(path: Path) -> str:
    return path.stem.replace("-", " ").strip().title()


def _first_level_titles(content: str) -> tuple[str, ...]:
    return tuple(
        line[2:].strip()
        for line in content.splitlines()
        if line.startswith("# ") and line[2:].strip()
    )


def _render_candidate_index(
    entries: tuple[ArchiveEntry, ...], *, through_date: date
) -> str:
    lines = [
        "# Development log index",
        "",
        f"Index eligibility through {through_date.isoformat()}.",
        "",
        "The dated records remain at their original stable paths. Inclusion in this",
        "index is logical archive eligibility only; it does not move, rename, delete,",
        "publish, commit, or authorize any record.",
        "",
        "## Records",
        "",
    ]
    if not entries:
        lines.append("_No eligible dated records._")
    else:
        for entry in entries:
            link = entry.path.name
            lines.append(
                f"- {entry.record_date.isoformat()} — [{entry.title}]({link})"
            )
    return "\n".join(lines) + "\n"


def _failed_plan(
    *,
    root: Path,
    through_date: date,
    entries: tuple[ArchiveEntry, ...],
    findings: list[ArchiveFinding],
) -> DocumentationArchivePlan:
    return DocumentationArchivePlan(
        root=root,
        through_date=through_date,
        state=ArchivePlanState.FAIL,
        entries=entries,
        change=None,
        findings=tuple(findings),
    )


def plan_documentation_archive(
    root: Path, *, through_date: date
) -> DocumentationArchivePlan:
    """Build an exact logical archive-index candidate without writing files."""

    resolved = _resolve_root(root)
    log_directory = resolved / DEVELOPMENT_LOG_DIRECTORY
    findings: list[ArchiveFinding] = []

    if log_directory.is_symlink():
        findings.append(
            ArchiveFinding(
                status=ArchiveFindingStatus.FAIL,
                semantics="deterministic",
                code="log_directory_symlink",
                message="development-log directory must not be a symbolic link",
                path=DEVELOPMENT_LOG_DIRECTORY,
            )
        )
        return _failed_plan(
            root=resolved,
            through_date=through_date,
            entries=(),
            findings=findings,
        )
    if not log_directory.exists() or not log_directory.is_dir():
        findings.append(
            ArchiveFinding(
                status=ArchiveFindingStatus.FAIL,
                semantics="deterministic",
                code="log_directory_missing",
                message="docs/development-log must be an existing directory",
                path=DEVELOPMENT_LOG_DIRECTORY,
            )
        )
        return _failed_plan(
            root=resolved,
            through_date=through_date,
            entries=(),
            findings=findings,
        )

    entries: list[ArchiveEntry] = []
    for candidate in sorted(log_directory.iterdir(), key=lambda item: item.name):
        relative = DEVELOPMENT_LOG_DIRECTORY / candidate.name
        if candidate.name == DEVELOPMENT_LOG_INDEX.name:
            continue
        if candidate.suffix != ".md":
            continue

        match = DATED_LOG_PATTERN.fullmatch(candidate.name)
        if match is None:
            findings.append(
                ArchiveFinding(
                    status=ArchiveFindingStatus.NOT_APPLICABLE,
                    semantics="deterministic",
                    code="non_dated_markdown",
                    message="Markdown file does not use the dated log filename contract",
                    path=relative,
                )
            )
            continue
        try:
            record_date = date.fromisoformat(match.group("date"))
        except ValueError:
            findings.append(
                ArchiveFinding(
                    status=ArchiveFindingStatus.FAIL,
                    semantics="deterministic",
                    code="invalid_log_date",
                    message="dated log filename contains an invalid calendar date",
                    path=relative,
                )
            )
            continue

        if candidate.is_symlink():
            findings.append(
                ArchiveFinding(
                    status=ArchiveFindingStatus.FAIL,
                    semantics="deterministic",
                    code="log_symlink",
                    message="dated log must not be a symbolic link",
                    path=relative,
                )
            )
            continue
        if not candidate.is_file():
            findings.append(
                ArchiveFinding(
                    status=ArchiveFindingStatus.FAIL,
                    semantics="deterministic",
                    code="log_not_file",
                    message="dated log path must be a regular file",
                    path=relative,
                )
            )
            continue
        if record_date > through_date:
            findings.append(
                ArchiveFinding(
                    status=ArchiveFindingStatus.NOT_APPLICABLE,
                    semantics="deterministic",
                    code="after_through_date",
                    message="dated log is later than the explicit through-date",
                    path=relative,
                )
            )
            continue

        raw = candidate.read_bytes()
        content = raw.decode("utf-8")
        titles = _first_level_titles(content)
        if not titles:
            title = _fallback_title(candidate)
            findings.append(
                ArchiveFinding(
                    status=ArchiveFindingStatus.WARN,
                    semantics="deterministic",
                    code="missing_primary_title",
                    message="dated log has no first-level title; filename fallback used",
                    path=relative,
                )
            )
        else:
            title = titles[0]
            if len(titles) > 1:
                findings.append(
                    ArchiveFinding(
                        status=ArchiveFindingStatus.WARN,
                        semantics="deterministic",
                        code="multiple_primary_titles",
                        message="dated log has multiple first-level titles; first title used",
                        path=relative,
                    )
                )
        entries.append(
            ArchiveEntry(
                path=relative,
                record_date=record_date,
                title=title,
                sha256=_sha256_bytes(raw),
            )
        )

    ordered_entries = tuple(
        sorted(
            entries,
            key=lambda entry: (-entry.record_date.toordinal(), entry.path.as_posix()),
        )
    )
    if any(finding.status is ArchiveFindingStatus.FAIL for finding in findings):
        return _failed_plan(
            root=resolved,
            through_date=through_date,
            entries=ordered_entries,
            findings=findings,
        )

    if ordered_entries:
        findings.append(
            ArchiveFinding(
                status=ArchiveFindingStatus.PASS,
                semantics="deterministic",
                code="eligible_records",
                message=f"{len(ordered_entries)} dated record(s) are index-eligible",
                path=DEVELOPMENT_LOG_DIRECTORY,
            )
        )
    else:
        findings.append(
            ArchiveFinding(
                status=ArchiveFindingStatus.NOT_APPLICABLE,
                semantics="deterministic",
                code="no_eligible_records",
                message="no dated records are on or before the explicit through-date",
                path=DEVELOPMENT_LOG_DIRECTORY,
            )
        )

    index_target = resolved / DEVELOPMENT_LOG_INDEX
    if index_target.is_symlink() or (index_target.exists() and not index_target.is_file()):
        findings.append(
            ArchiveFinding(
                status=ArchiveFindingStatus.FAIL,
                semantics="deterministic",
                code="index_target_unsafe",
                message="index target must be absent or a regular non-symlink file",
                path=DEVELOPMENT_LOG_INDEX,
            )
        )
        return _failed_plan(
            root=resolved,
            through_date=through_date,
            entries=ordered_entries,
            findings=findings,
        )

    content = _render_candidate_index(ordered_entries, through_date=through_date)
    before = index_target.read_bytes() if index_target.exists() else None
    before_sha256 = _sha256_bytes(before) if before is not None else None
    after_sha256 = _sha256_text(content)
    action = (
        "create"
        if before is None
        else "none"
        if before_sha256 == after_sha256
        else "update"
    )
    change = ArchiveIndexChange(
        path=DEVELOPMENT_LOG_INDEX,
        action=action,
        before_sha256=before_sha256,
        after_sha256=after_sha256,
        content=content,
    )
    findings.append(
        ArchiveFinding(
            status=ArchiveFindingStatus.ADVISORY,
            semantics="advisory",
            code="human_usefulness_review",
            message=(
                "an accountable human must decide whether the candidate index is "
                "useful; this plan cannot authorize applying it"
            ),
            path=DEVELOPMENT_LOG_INDEX,
        )
    )

    if any(finding.status is ArchiveFindingStatus.WARN for finding in findings):
        state = ArchivePlanState.WARN
    elif not ordered_entries:
        state = ArchivePlanState.NOT_APPLICABLE
    else:
        state = ArchivePlanState.PASS
    return DocumentationArchivePlan(
        root=resolved,
        through_date=through_date,
        state=state,
        entries=ordered_entries,
        change=change,
        findings=tuple(findings),
    )


def request_documentation_archive_confirmation(
    plan: DocumentationArchivePlan,
    *,
    decision_reader: Callable[[str], str],
    is_interactive_terminal: bool,
) -> bool:
    """Return write authority only for one exact interactive confirmation."""

    if not is_interactive_terminal or plan.change is None:
        return False
    decision = decision_reader(
        f'Type APPLY INDEX to {plan.change.action} '
        f'"{plan.change.path.as_posix()}" with candidate '
        f'sha256:{plan.change.after_sha256}: '
    )
    return decision == "APPLY INDEX"


def _require_current_plan(
    preview: DocumentationArchivePlan,
) -> DocumentationArchivePlan:
    current = plan_documentation_archive(
        preview.root,
        through_date=preview.through_date,
    )
    if current != preview:
        raise DocumentationArchiveApplyError(
            "documentation archive plan is stale; run the preview again"
        )
    return current


def _write_exclusive(target: Path, content: bytes) -> None:
    created = False
    try:
        with target.open("xb") as handle:
            created = True
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
    except FileExistsError as exc:
        raise DocumentationArchiveApplyError(
            "documentation archive plan is stale; index target appeared"
        ) from exc
    except BaseException:
        if created:
            try:
                target.unlink()
            except OSError:
                pass
        raise


def _replace_atomically(
    preview: DocumentationArchivePlan,
    *,
    target: Path,
    content: bytes,
) -> None:
    descriptor, temp_name = tempfile.mkstemp(
        prefix=".INDEX.md.agentgov-",
        suffix=".tmp",
        dir=target.parent,
    )
    temporary = Path(temp_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, target.stat().st_mode)
        _require_current_plan(preview)
        os.replace(temporary, target)
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def apply_documentation_archive_plan(
    preview: DocumentationArchivePlan,
) -> DocumentationArchiveApplyResult:
    """Apply one exact preview without opening any dated source log for write."""

    if preview.state is ArchivePlanState.FAIL or preview.change is None:
        raise DocumentationArchiveApplyError(
            "failed documentation archive plans cannot be applied"
        )
    current = _require_current_plan(preview)
    change = current.change
    if change is None:
        raise DocumentationArchiveApplyError(
            "documentation archive plan has no applicable index change"
        )
    if change.action == "none":
        return DocumentationArchiveApplyResult(
            root=current.root,
            path=change.path,
            action="none",
            sha256=change.after_sha256,
        )

    target = current.root / change.path
    content = change.content.encode("utf-8")
    if change.action == "create":
        _write_exclusive(target, content)
    elif change.action == "update":
        _replace_atomically(current, target=target, content=content)
    else:
        raise DocumentationArchiveApplyError(
            f"unsupported documentation archive action: {change.action}"
        )
    return DocumentationArchiveApplyResult(
        root=current.root,
        path=change.path,
        action=change.action,
        sha256=change.after_sha256,
    )


def documentation_archive_plan_document(
    plan: DocumentationArchivePlan,
) -> dict[str, Any]:
    return {
        "contract": ARCHIVE_PLAN_CONTRACT,
        "schema_version": ARCHIVE_PLAN_SCHEMA_VERSION,
        "tool": {"name": "agentgov", "version": __version__},
        "repository": str(plan.root),
        "through_date": plan.through_date.isoformat(),
        "mode": "read_only",
        "state": plan.state.value,
        "source_directory": DEVELOPMENT_LOG_DIRECTORY.as_posix(),
        "eligibility": {
            "kind": "logical_index_inclusion",
            "filename_pattern": DATED_LOG_PATTERN.pattern,
            "includes_on_or_before": plan.through_date.isoformat(),
            "preserves_source_paths": True,
            "uses_host_clock": False,
        },
        "entries": [
            {
                "path": entry.path.as_posix(),
                "date": entry.record_date.isoformat(),
                "title": entry.title,
                "sha256": entry.sha256,
            }
            for entry in plan.entries
        ],
        "change": (
            None
            if plan.change is None
            else {
                "path": plan.change.path.as_posix(),
                "action": plan.change.action,
                "before_sha256": plan.change.before_sha256,
                "after_sha256": plan.change.after_sha256,
                "content": plan.change.content,
            }
        ),
        "findings": [
            {
                "status": finding.status.value,
                "semantics": finding.semantics,
                "code": finding.code,
                "path": finding.path.as_posix() if finding.path else None,
                "message": finding.message,
            }
            for finding in plan.findings
        ],
        "authority_boundary": {
            "repository_modified": False,
            "index_written": False,
            "source_log_moved": False,
            "source_log_renamed": False,
            "source_log_deleted": False,
            "apply_authorized": False,
            "scheduling_authorized": False,
            "git_operation_authorized": False,
            "publication_authorized": False,
            "release_authorized": False,
            "deployment_authorized": False,
        },
    }


def render_documentation_archive_plan_json(
    plan: DocumentationArchivePlan,
) -> str:
    return json.dumps(
        documentation_archive_plan_document(plan),
        indent=2,
        ensure_ascii=False,
    ) + "\n"


def render_documentation_archive_plan_terminal(
    plan: DocumentationArchivePlan,
) -> str:
    lines = [
        f"TARGET documentation-archive: {plan.root / DEVELOPMENT_LOG_INDEX}",
        f"STATE {plan.state.value}",
        f"THROUGH {plan.through_date.isoformat()}",
    ]
    for entry in plan.entries:
        lines.append(
            f"ENTRY {entry.record_date.isoformat()} {entry.path.as_posix()} "
            f"sha256={entry.sha256} title={entry.title}"
        )
    if plan.change is not None:
        before = plan.change.before_sha256 or "absent"
        lines.append(
            f"CHANGE {plan.change.action} {plan.change.path.as_posix()} "
            f"before={before} after={plan.change.after_sha256}"
        )
        lines.append("CONTENT-BEGIN")
        lines.extend(plan.change.content.rstrip("\n").splitlines())
        lines.append("CONTENT-END")
    for finding in plan.findings:
        path = f" path={finding.path.as_posix()}" if finding.path else ""
        lines.append(
            f"{finding.status.value.upper()} {finding.code}{path}: {finding.message}"
        )
    lines.append(
        "NOTE documentation-archive plan: no index, source log, apply, scheduling, "
        "Git, publication, release, or deployment action was run"
    )
    return "\n".join(lines) + "\n"
