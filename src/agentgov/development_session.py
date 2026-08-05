"""Guided, explicitly confirmed working-copy development sessions."""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any, Callable, Mapping, Sequence

from agentgov.development_context import DevelopmentContext, select_development_context
from agentgov.event_store import (
    GovernanceEvent,
    append_governance_event,
    load_governance_events,
    utc_now,
)
from agentgov.git_snapshot import resolve_comparison_base
from agentgov.path_policy import is_segment_prefix, scope_path_error
from agentgov.task_contract import (
    canonical_task_digest,
    check_development_task,
    load_development_task,
    validate_development_task_document,
)


SESSION_CONTRACT = "agentgov.development-session"
SESSION_SCHEMA_VERSION = "1.0"
SESSION_RELATIVE_PATH = ".agentgov/current-task.json"

_TASK_ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_COMMIT_RE = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")
_SENSITIVE_RE = re.compile(
    r"(?i)(?:api[_-]?key|access[_-]?token|auth[_-]?token|password|passwd|secret)\s*[:=]"
)


class SessionPolicyError(ValueError):
    """A session action would be ambiguous, unsafe, or untruthful."""


@dataclass(frozen=True)
class DevelopmentSession:
    contract: str
    schema_version: str
    task_path: str
    task_id: str
    task_digest: str
    comparison_base_sha: str
    started_at: str
    actor: Mapping[str, str]


@dataclass(frozen=True)
class StartPlan:
    root: Path
    session: DevelopmentSession
    task_document: Mapping[str, Any]
    create_task: bool
    replace_active: bool
    already_active: bool
    prior_session: DevelopmentSession | None
    selected_governance: tuple[str, ...]
    event_id: str

    @property
    def targets(self) -> tuple[str, ...]:
        if self.already_active:
            return ()
        values: list[str] = []
        if self.create_task:
            values.append(self.session.task_path)
        values.extend(
            (
                SESSION_RELATIVE_PATH,
                f".agentgov/events/{self.event_id}.json",
            )
        )
        return tuple(values)


@dataclass(frozen=True)
class StartResult:
    session: DevelopmentSession
    context: DevelopmentContext
    created_task: bool
    event_ref: str | None


def _safe_root(repository: Path) -> Path:
    if repository.is_symlink():
        raise SessionPolicyError("repository root must not be a symbolic link")
    if not repository.exists():
        raise FileNotFoundError(repository)
    if not repository.is_dir():
        raise SessionPolicyError("repository root must be a directory")
    return repository.resolve()


def _safe_relative(root: Path, path: Path, *, label: str) -> tuple[Path, str]:
    candidate = path if path.is_absolute() else root / path
    resolved = candidate.resolve(strict=False)
    try:
        relative = resolved.relative_to(root).as_posix()
    except ValueError as exc:
        raise SessionPolicyError(f"{label} must stay within the repository") from exc
    if not relative or relative == "." or scope_path_error(relative):
        raise SessionPolicyError(f"{label} must be a safe repository-relative path")
    cursor = candidate
    while True:
        if cursor.is_symlink():
            raise SessionPolicyError(f"{label} must not use a symbolic link")
        if cursor.resolve(strict=False) == root or cursor.parent == cursor:
            break
        cursor = cursor.parent
    return resolved, relative


def _is_tracked(root: Path, relative: str) -> bool:
    completed = subprocess.run(
        ("git", "-C", str(root), "ls-files", "--error-unmatch", "--", relative),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
        timeout=30,
    )
    return completed.returncode == 0


def _validate_actor(actor: Any) -> Mapping[str, str]:
    if not isinstance(actor, Mapping) or set(actor) - {"class", "label"} or actor.get("class") != "human":
        raise SessionPolicyError("session actor must be an explicitly confirming human")
    label = actor.get("label")
    if label is not None and (
        not isinstance(label, str)
        or not label.strip()
        or len(label) > 100
        or "\n" in label
        or "\r" in label
        or label.startswith(("/", "\\"))
        or _SENSITIVE_RE.search(label)
        or re.search(r"(?i)(?:^|\s)[a-z]:[\\/]", label)
    ):
        raise SessionPolicyError("session actor label contains unsafe or sensitive text")
    return dict(actor)


def _session_from_payload(payload: Any) -> DevelopmentSession:
    fields = {
        "contract", "schema_version", "task_path", "task_id", "task_digest",
        "comparison_base_sha", "started_at", "actor",
    }
    if not isinstance(payload, Mapping) or set(payload) != fields:
        raise SessionPolicyError("current task session has unexpected fields")
    if payload.get("contract") != SESSION_CONTRACT or payload.get("schema_version") != SESSION_SCHEMA_VERSION:
        raise SessionPolicyError("current task session uses an unsupported contract")
    task_path = payload.get("task_path")
    if not isinstance(task_path, str) or "\\" in task_path:
        raise SessionPolicyError("session task_path must be repository-relative")
    pure = PurePosixPath(task_path)
    if pure.is_absolute() or task_path in {"", "."} or ".." in pure.parts:
        raise SessionPolicyError("session task_path must be repository-relative")
    task_id = payload.get("task_id")
    if not isinstance(task_id, str) or not _TASK_ID_RE.fullmatch(task_id):
        raise SessionPolicyError("session task_id is invalid")
    task_digest = payload.get("task_digest")
    if not isinstance(task_digest, str) or not _DIGEST_RE.fullmatch(task_digest):
        raise SessionPolicyError("session task_digest is invalid")
    base = payload.get("comparison_base_sha")
    if not isinstance(base, str) or not _COMMIT_RE.fullmatch(base):
        raise SessionPolicyError("session comparison_base_sha is invalid")
    started_at = payload.get("started_at")
    if not isinstance(started_at, str) or not started_at.endswith("Z"):
        raise SessionPolicyError("session started_at must be a UTC Z timestamp")
    try:
        datetime.fromisoformat(started_at.removesuffix("Z") + "+00:00")
    except ValueError as exc:
        raise SessionPolicyError("session started_at is invalid") from exc
    actor = _validate_actor(payload.get("actor"))
    return DevelopmentSession(
        contract=SESSION_CONTRACT,
        schema_version=SESSION_SCHEMA_VERSION,
        task_path=task_path,
        task_id=task_id,
        task_digest=task_digest,
        comparison_base_sha=base,
        started_at=started_at,
        actor=actor,
    )


def load_active_session(repository: Path) -> DevelopmentSession | None:
    """Load a strict untracked working-copy pointer, if one exists."""

    root = _safe_root(repository)
    path = root / SESSION_RELATIVE_PATH
    if path.is_symlink():
        raise SessionPolicyError("current task session must not be a symbolic link")
    if not path.exists():
        return None
    if not path.is_file():
        raise SessionPolicyError("current task session must be a regular file")
    if _is_tracked(root, SESSION_RELATIVE_PATH):
        raise SessionPolicyError("current task session is tracked; remove it from Git before continuing")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise SessionPolicyError(f"cannot read current task session: {exc}") from exc
    session = _session_from_payload(payload)
    _safe_relative(root, Path(*PurePosixPath(session.task_path).parts), label="session task path")
    return session


def resolve_active_task(repository: Path) -> tuple[Path, DevelopmentSession]:
    """Resolve the active task and fail closed if its admitted content drifted."""

    root = _safe_root(repository)
    session = load_active_session(root)
    if session is None:
        raise SessionPolicyError("no active task; run 'agentgov govern start' first")
    task_path, _ = _safe_relative(
        root,
        Path(*PurePosixPath(session.task_path).parts),
        label="session task path",
    )
    report = check_development_task(task_path, repository=root)
    if report.has_failures:
        raise SessionPolicyError("active task no longer satisfies the task contract; run govern start again")
    document = load_development_task(task_path)
    decision = document.get("decision")
    if not isinstance(decision, Mapping) or decision.get("state") != "admitted":
        raise SessionPolicyError("active task is no longer admitted; run govern start again")
    digest = canonical_task_digest(document)
    if digest != session.task_digest or document.get("task_id") != session.task_id:
        raise SessionPolicyError(
            "active task changed after govern start; review it and run govern start with --replace-active"
        )
    resolve_comparison_base(root, session.comparison_base_sha)
    return task_path, session


def current_session_events(
    repository: Path,
    session: DevelopmentSession,
) -> tuple[GovernanceEvent, ...]:
    """Load validated events belonging to one exact working-copy session."""

    root = _safe_root(repository)
    loaded = load_governance_events(root / ".agentgov" / "events")
    return tuple(
        event
        for event in loaded.events
        if event.task_id == session.task_id
        and event.task_digest == session.task_digest
        and event.occurred_at >= session.started_at
    )


def discover_admitted_tasks(
    repository: Path,
    *,
    excluded_task_digests: Sequence[str] = (),
) -> tuple[Path, ...]:
    """Return valid admitted direct task files without choosing among several."""

    root = _safe_root(repository)
    directory = root / "governance" / "tasks"
    if not directory.is_dir() or directory.is_symlink():
        return ()
    admitted: list[Path] = []
    for path in sorted(directory.glob("*.json"), key=lambda item: item.name):
        if path.is_symlink() or not path.is_file():
            continue
        try:
            report = check_development_task(path, repository=root)
            document = load_development_task(path)
        except (OSError, UnicodeError, ValueError, json.JSONDecodeError):
            continue
        decision = document.get("decision")
        digest = canonical_task_digest(document)
        if (
            not report.has_failures
            and isinstance(decision, Mapping)
            and decision.get("state") == "admitted"
            and digest not in excluded_task_digests
        ):
            admitted.append(path)
    return tuple(admitted)


def _slugify(value: str) -> str:
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", value.lower())).strip("-")


def detect_validation_commands(repository: Path) -> tuple[str, ...]:
    """Detect only conventional, deterministic validation entry points."""

    root = _safe_root(repository)
    if (root / "tests").is_dir() and any(
        (root / name).is_file()
        for name in ("pyproject.toml", "setup.py", "setup.cfg", "requirements.txt")
    ):
        return ("python -m unittest discover -s tests -v",)
    package_json = root / "package.json"
    if package_json.is_file() and not package_json.is_symlink():
        try:
            package = json.loads(package_json.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            package = None
        scripts = package.get("scripts") if isinstance(package, Mapping) else None
        test_script = scripts.get("test") if isinstance(scripts, Mapping) else None
        if isinstance(test_script, str) and test_script.strip() and "no test specified" not in test_script.lower():
            return ("npm test",)
    if (root / "Cargo.toml").is_file():
        return ("cargo test",)
    if (root / "go.mod").is_file():
        return ("go test ./...",)
    return ()


def build_compact_task(
    *,
    title: str,
    task_id: str | None,
    requirement: str | None,
    include_paths: Sequence[str],
    exclude_paths: Sequence[str],
    validation_commands: Sequence[str],
    owner: str,
) -> Mapping[str, Any]:
    identifier = task_id or _slugify(title)
    if not identifier:
        raise SessionPolicyError("title cannot form a portable task id; provide --task-id")
    if not include_paths:
        raise SessionPolicyError("a new compact task requires at least one --include path")
    own_path = f"governance/tasks/{identifier}.json"
    if any(is_segment_prefix(excluded, own_path) for excluded in exclude_paths):
        raise SessionPolicyError("the new task contract path cannot be excluded from its own scope")
    admitted_includes = list(include_paths)
    if not any(is_segment_prefix(included, own_path) for included in admitted_includes):
        admitted_includes.append(own_path)
    document: Mapping[str, Any] = {
        "contract": "agentgov.development-task",
        "schema_version": "1.1",
        "profile": "compact",
        "task_id": identifier,
        "title": title,
        "requirement": {
            "summary": requirement or f"Implement the admitted development task: {title}.",
            "source_refs": [],
        },
        "scope": {
            "include_paths": admitted_includes,
            "exclude_paths": list(exclude_paths),
        },
        "acceptance_signals": [
            "Declared validation commands pass and every governed changed path remains inside the admitted scope."
        ],
        "validation_commands": list(validation_commands),
        "owner": owner,
        "risk": {"level": "low", "items": []},
        "decision": {
            "state": "admitted",
            "decided_by": owner,
            "rationale": "The accountable human reviewed the govern start preview and confirmed this compact task.",
        },
    }
    errors = validate_development_task_document(document)
    if errors:
        raise SessionPolicyError("compact task is invalid: " + "; ".join(errors))
    return document


def build_start_plan(
    repository: Path,
    *,
    task: Path | None = None,
    title: str | None = None,
    task_id: str | None = None,
    requirement: str | None = None,
    include_paths: Sequence[str] = (),
    exclude_paths: Sequence[str] = (),
    validation_commands: Sequence[str] = (),
    owner: str = "Human product owner",
    comparison_base: str = "HEAD",
    actor_label: str | None = None,
    replace_active: bool = False,
) -> StartPlan:
    """Build a complete, read-only preview of one guided start action."""

    root = _safe_root(repository)
    prior = load_active_session(root)
    prior_events = current_session_events(root, prior) if prior is not None else ()
    prior_handed_off = bool(
        prior_events and prior_events[-1].event_type == "session.handed_off"
    )
    if task is not None and title is not None:
        raise SessionPolicyError("choose an existing task or --title, not both")
    creation_inputs = bool(
        task_id
        or requirement
        or include_paths
        or exclude_paths
        or validation_commands
        or owner != "Human product owner"
    )
    if title is None and creation_inputs:
        raise SessionPolicyError("--task-id, --requirement, --include, --exclude, --validate, and --owner require --title")
    create_task = title is not None
    if task is None and title is None:
        excluded = (prior.task_digest,) if prior is not None and prior_handed_off else ()
        candidates = discover_admitted_tasks(root, excluded_task_digests=excluded)
        if not candidates:
            raise SessionPolicyError("no admitted task was discovered; provide --title and at least one --include")
        if len(candidates) > 1:
            names = ", ".join(path.relative_to(root).as_posix() for path in candidates)
            raise SessionPolicyError(f"multiple admitted tasks were discovered; choose one explicitly: {names}")
        task = candidates[0]

    if create_task:
        assert title is not None
        commands = tuple(validation_commands) or detect_validation_commands(root)
        if not commands:
            raise SessionPolicyError("no validation command was detected; provide --validate")
        document = build_compact_task(
            title=title,
            task_id=task_id,
            requirement=requirement,
            include_paths=include_paths,
            exclude_paths=exclude_paths,
            validation_commands=commands,
            owner=owner,
        )
        relative = f"governance/tasks/{document['task_id']}.json"
        task_path, relative = _safe_relative(root, Path(*PurePosixPath(relative).parts), label="new task path")
        if task_path.exists() or task_path.is_symlink():
            raise SessionPolicyError(f"task target already exists and will not be overwritten: {relative}")
        selected_governance: tuple[str, ...] = ()
    else:
        assert task is not None
        task_path, relative = _safe_relative(root, task, label="task path")
        report = check_development_task(task_path, repository=root)
        if report.has_failures:
            raise SessionPolicyError("selected task does not satisfy the development task contract")
        document = load_development_task(task_path)
        decision = document.get("decision")
        if not isinstance(decision, Mapping) or decision.get("state") != "admitted":
            raise SessionPolicyError("selected task must be admitted before govern start")
        context = select_development_context(task_path, repository=root)
        selected_governance = tuple(item.path for item in context.selected_governance)

    base_sha = resolve_comparison_base(root, comparison_base)
    actor: dict[str, str] = {"class": "human"}
    if actor_label:
        actor["label"] = actor_label
    _validate_actor(actor)
    timestamp = utc_now()
    session = DevelopmentSession(
        contract=SESSION_CONTRACT,
        schema_version=SESSION_SCHEMA_VERSION,
        task_path=relative,
        task_id=str(document["task_id"]),
        task_digest=canonical_task_digest(document),
        comparison_base_sha=base_sha,
        started_at=timestamp,
        actor=actor,
    )
    same = prior is not None and all(
        (
            prior.task_path == session.task_path,
            prior.task_id == session.task_id,
            prior.task_digest == session.task_digest,
            prior.comparison_base_sha == session.comparison_base_sha,
        )
    )
    if same and prior_handed_off:
        raise SessionPolicyError(
            "the exact active task digest is already handed off and cannot be restarted; "
            "select a different admitted task or review a changed task version"
        )
    if prior is not None and not same and not replace_active:
        raise SessionPolicyError(
            f"active task {prior.task_id!r} would be replaced; review it and pass --replace-active"
        )
    if same:
        assert prior is not None
        session = prior
    return StartPlan(
        root=root,
        session=session,
        task_document=document,
        create_task=create_task,
        replace_active=prior is not None and not same,
        already_active=same,
        prior_session=prior,
        selected_governance=selected_governance,
        event_id=f"evt-{uuid.uuid4().hex}",
    )


def _plan_payload(plan: StartPlan) -> Mapping[str, Any]:
    return {
        "action": "already_active" if plan.already_active else ("replace" if plan.replace_active else "start"),
        "task": {
            "path": plan.session.task_path,
            "task_id": plan.session.task_id,
            "task_digest": plan.session.task_digest,
            "create": plan.create_task,
        },
        "comparison_base_sha": plan.session.comparison_base_sha,
        "selected_governance": list(plan.selected_governance),
        "targets": list(plan.targets),
        "authority_boundary": {
            "authorizes_code_change": False,
            "authorizes_exception": False,
            "authorizes_commit": False,
            "authorizes_merge": False,
            "authorizes_deployment": False,
        },
    }


def render_start_plan_json(plan: StartPlan) -> str:
    return json.dumps(_plan_payload(plan), ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def render_start_plan_terminal(plan: StartPlan) -> str:
    payload = _plan_payload(plan)
    lines = [
        "GOVERN START PREVIEW",
        f"ACTION {payload['action']}",
        f"TASK {plan.session.task_id} ({plan.session.task_path})",
        f"TASK_DIGEST {plan.session.task_digest}",
        f"COMPARISON_BASE {plan.session.comparison_base_sha}",
        f"SELECTED_GOVERNANCE {len(plan.selected_governance)}",
    ]
    lines.extend(f"  - {path}" for path in plan.selected_governance)
    lines.append(f"WRITE_TARGETS {len(plan.targets)}")
    lines.extend(f"  - {path}" for path in plan.targets)
    lines.append("AUTHORITY code_change=false exception=false commit=false merge=false deployment=false")
    if plan.create_task:
        lines.append("NOTE compact task content is part of this preview and is admitted only by exact confirmation")
        lines.append("NOTE governance selection will be derived after the confirmed task file is created")
        lines.append(json.dumps(plan.task_document, ensure_ascii=False, indent=2, sort_keys=True))
    return "\n".join(lines) + "\n"


def request_start_confirmation(
    plan: StartPlan,
    *,
    decision_reader: Callable[[str], str],
    is_interactive_terminal: bool,
) -> bool:
    """Accept write authority only from an exact decision on a real terminal."""

    if plan.already_active:
        return True
    if not is_interactive_terminal:
        return False
    word = "REPLACE" if plan.replace_active else "START"
    try:
        decision = decision_reader(
            f'Type {word} to write {len(plan.targets)} reviewed target(s) in "{plan.root}": '
        )
    except EOFError:
        return False
    return decision == word


def _encoded(value: Mapping[str, Any]) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _write_pointer(root: Path, session: DevelopmentSession) -> None:
    state_root = root / ".agentgov"
    pointer = root / SESSION_RELATIVE_PATH
    if state_root.is_symlink() or pointer.is_symlink():
        raise SessionPolicyError("local session path must not use a symbolic link")
    if _is_tracked(root, SESSION_RELATIVE_PATH):
        raise SessionPolicyError("current task session is tracked and will not be overwritten")
    state_root.mkdir(mode=0o700, exist_ok=True)
    temporary = state_root / f".current-task-{uuid.uuid4().hex}.tmp"
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(_encoded(asdict(session)))
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, pointer)
    finally:
        temporary.unlink(missing_ok=True)


def apply_start_plan(plan: StartPlan) -> StartResult:
    """Apply exactly one reviewed plan and append its bounded start observation."""

    if plan.already_active:
        task_path = plan.root / Path(*PurePosixPath(plan.session.task_path).parts)
        context = select_development_context(task_path, repository=plan.root)
        return StartResult(plan.session, context, False, None)

    current = load_active_session(plan.root)
    if current != plan.prior_session:
        raise SessionPolicyError("active task changed after preview; build and review a new start plan")
    task_path = plan.root / Path(*PurePosixPath(plan.session.task_path).parts)
    if canonical_task_digest(plan.task_document) != plan.session.task_digest:
        raise SessionPolicyError("task plan changed after preview; build and review a new start plan")
    parent = plan.root
    for part in PurePosixPath(plan.session.task_path).parts[:-1]:
        parent = parent / part
        if parent.is_symlink():
            raise SessionPolicyError("task parent became a symbolic link after preview")
        if parent.exists() and not parent.is_dir():
            raise SessionPolicyError("task parent became a non-directory after preview")
    if plan.create_task and (task_path.exists() or task_path.is_symlink()):
        raise SessionPolicyError("task target appeared after preview and was not overwritten")

    previous_pointer = None
    pointer = plan.root / SESSION_RELATIVE_PATH
    if pointer.exists():
        previous_pointer = pointer.read_bytes()
    planned_pointer = _encoded(asdict(plan.session))
    planned_task = _encoded(plan.task_document)
    created_task = False
    try:
        if plan.create_task:
            task_path.parent.mkdir(parents=True, exist_ok=True)
            with task_path.open("xb") as stream:
                stream.write(_encoded(plan.task_document))
            created_task = True
        context = select_development_context(task_path, repository=plan.root)
        if context.task_digest != plan.session.task_digest:
            raise SessionPolicyError("task content changed after preview; build and review a new start plan")
        selected = tuple(item.path for item in context.selected_governance)
        _write_pointer(plan.root, plan.session)
        _, event_ref = append_governance_event(
            plan.root,
            event_type="task.started",
            actor_class="human",
            actor_label=plan.session.actor.get("label"),
            task_id=plan.session.task_id,
            task_digest=plan.session.task_digest,
            outcome="started",
            evidence_ref=plan.session.task_path,
            governance_refs=selected,
            reason_codes=(
                "start_confirmed",
                "compact_task_created" if plan.create_task else "admitted_task_selected",
            ),
            metrics={"selected_governance": len(selected), "task_created": int(plan.create_task)},
            occurred_at=plan.session.started_at,
            event_id=plan.event_id,
        )
    except BaseException as exc:
        rollback_errors: list[str] = []
        try:
            if pointer.exists() and pointer.read_bytes() == planned_pointer:
                if plan.prior_session is None:
                    pointer.unlink()
                else:
                    _write_pointer(plan.root, plan.prior_session)
        except Exception as rollback_exc:
            rollback_errors.append(f"session pointer: {rollback_exc}")
        try:
            if created_task and task_path.exists():
                if task_path.read_bytes() == planned_task:
                    task_path.unlink()
                else:
                    rollback_errors.append("new task changed concurrently and was preserved")
        except Exception as rollback_exc:
            rollback_errors.append(f"new task: {rollback_exc}")
        if rollback_errors:
            raise SessionPolicyError(
                "govern start failed and rollback was incomplete: " + "; ".join(rollback_errors)
            ) from exc
        raise
    return StartResult(plan.session, context, created_task, event_ref)
