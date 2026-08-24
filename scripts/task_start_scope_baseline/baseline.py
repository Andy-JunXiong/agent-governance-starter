"""Deterministic, privacy-bounded task-start scope baselines.

This is deliberately an internal bridge rather than a public ``agentgov`` API.
It captures the already-dirty Git state at an explicit future task boundary and
later distinguishes preserved predecessor work from changes made after that
boundary.  It never claims to know what happened before its capture point.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
from dataclasses import asdict, dataclass, replace
from enum import Enum
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Sequence

from agentgov.git_snapshot import (
    CanonicalGitSnapshot,
    GitSnapshotError,
    SnapshotChange,
    capture_git_snapshot,
)
from agentgov.path_policy import evaluate_path_scope, is_segment_prefix, scope_path_error
from agentgov.task_contract import (
    canonical_task_digest,
    load_development_task,
    validate_development_task_document,
)


BASELINE_CONTRACT = "agentgov.task-start-scope-baseline"
BASELINE_SCHEMA_VERSION = "1.0"
COMPARISON_CONTRACT = "agentgov.task-start-scope-comparison"
COMPARISON_SCHEMA_VERSION = "1.0"
CAPTURE_CLAIM = "boundary_begins_at_this_capture; earlier state is not proven"
LOCAL_BASELINE_PREFIX = ".agentgov/scope-baselines"
_LAYERS = ("committed", "staged", "unstaged", "untracked")
_TRACKED_STATUSES = {
    "added",
    "copied",
    "deleted",
    "modified",
    "renamed",
    "type_changed",
    "unmerged",
    "unknown",
}
_SNAPSHOT_EXCLUSIONS = (
    "ignored untracked paths are omitted by git ls-files --exclude-standard",
    "untracked paths beneath .agentgov are local tool state and are excluded",
    "tracked .agentgov paths and tracked .gitignore changes remain included",
)
_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_GIT_SHA_RE = re.compile(r"^[0-9a-f]{40,64}$")


class BaselineError(RuntimeError):
    """The requested boundary could not be captured or trusted."""


class FindingStatus(str, Enum):
    PASS = "PASS"
    PRESERVED = "PRESERVED"
    FAIL = "FAIL"


@dataclass(frozen=True)
class PathIdentity:
    layer: str
    status: str
    path: str
    old_path: str | None
    identity_digest: str
    identity_kind: str

    @property
    def endpoints(self) -> tuple[str, ...]:
        if self.status in {"copied", "renamed"} and self.old_path is not None:
            return (self.old_path, self.path)
        return (self.path,)


@dataclass(frozen=True)
class IdentityLayer:
    name: str
    changes: tuple[PathIdentity, ...]


@dataclass(frozen=True)
class CapturedState:
    comparison_base_sha: str
    snapshot_head_sha: str
    snapshot_change_set_digest: str
    layers: tuple[IdentityLayer, ...]
    exclusions: tuple[str, ...]


@dataclass(frozen=True)
class TaskBinding:
    path: str
    task_id: str
    digest: str


@dataclass(frozen=True)
class ScopeBinding:
    include_paths: tuple[str, ...]
    exclude_paths: tuple[str, ...]


@dataclass(frozen=True)
class TaskStartBaseline:
    contract: str
    schema_version: str
    task: TaskBinding
    comparison_base_sha: str
    snapshot_head_sha: str
    snapshot_change_set_digest: str
    scope: ScopeBinding
    layers: tuple[IdentityLayer, ...]
    exclusions: tuple[str, ...]
    capture_claim: str
    baseline_digest: str


@dataclass(frozen=True)
class BaselineFinding:
    status: FindingStatus
    check_id: str
    layer: str | None
    path: str | None
    old_path: str | None
    message: str


@dataclass(frozen=True)
class BaselineComparison:
    contract: str
    schema_version: str
    task_id: str
    task_path: str
    task_digest: str
    baseline_digest: str
    comparison_base_sha: str
    baseline_head_sha: str
    current_head_sha: str
    findings: tuple[BaselineFinding, ...]
    known_limits: tuple[str, ...]
    authority_boundary: Mapping[str, bool]

    @property
    def has_failures(self) -> bool:
        return any(item.status is FindingStatus.FAIL for item in self.findings)


def _canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _sha256(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def _safe_root(repository: Path) -> Path:
    if repository.is_symlink():
        raise BaselineError("repository root must not be a symbolic link")
    if not repository.exists() or not repository.is_dir():
        raise BaselineError("repository root must be an existing directory")
    return repository.resolve()


def _safe_relative_path(value: str, *, label: str) -> str:
    error = scope_path_error(value)
    if error:
        raise BaselineError(f"{label} {error}")
    return PurePosixPath(value).as_posix()


def _resolve_inside(root: Path, relative: str, *, label: str) -> Path:
    normalized = _safe_relative_path(relative, label=label)
    candidate = root.joinpath(*PurePosixPath(normalized).parts)
    resolved = candidate.resolve(strict=False)
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise BaselineError(f"{label} must stay within the repository") from exc
    cursor = candidate
    while True:
        if cursor.is_symlink():
            raise BaselineError(f"{label} must not use a symbolic link")
        if cursor.resolve(strict=False) == root or cursor.parent == cursor:
            break
        cursor = cursor.parent
    return resolved


def _load_task_binding(
    root: Path,
    task_path: str,
) -> tuple[TaskBinding, ScopeBinding, Mapping[str, Any]]:
    normalized = _safe_relative_path(task_path, label="task path")
    resolved = _resolve_inside(root, normalized, label="task path")
    if not resolved.exists() or not resolved.is_file():
        raise BaselineError("task path must name an existing regular file")
    try:
        document = load_development_task(resolved)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        raise BaselineError("task record is not readable valid JSON") from exc
    errors = validate_development_task_document(document)
    if errors:
        raise BaselineError("task record does not satisfy the development-task contract")
    decision = document.get("decision")
    if not isinstance(decision, Mapping) or decision.get("state") != "admitted":
        raise BaselineError("task record must have an admitted decision")
    scope = document.get("scope")
    if not isinstance(scope, Mapping):
        raise BaselineError("task scope is missing")
    includes = tuple(sorted(str(item) for item in scope.get("include_paths", ())))
    excludes = tuple(sorted(str(item) for item in scope.get("exclude_paths", ())))
    binding = TaskBinding(
        path=normalized,
        task_id=str(document["task_id"]),
        digest=canonical_task_digest(document),
    )
    return binding, ScopeBinding(includes, excludes), document


def _run_git_identity(root: Path, arguments: Sequence[str]) -> bytes:
    try:
        completed = subprocess.run(
            ("git", "-c", "core.quotepath=false", "-C", str(root), *arguments),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise BaselineError("read-only Git identity command could not complete") from exc
    if completed.returncode != 0:
        raise BaselineError("read-only Git identity command failed")
    return completed.stdout


def _tracked_patch_arguments(
    snapshot: CanonicalGitSnapshot,
    change: SnapshotChange,
) -> tuple[str, ...]:
    common = (
        "--binary",
        "--full-index",
        "--no-ext-diff",
        "--no-textconv",
        "--no-color",
        "--find-renames",
    )
    paths = (change.path,) if change.old_path is None else (change.old_path, change.path)
    if change.layer == "committed":
        return (
            "diff",
            *common,
            snapshot.comparison_base_sha,
            snapshot.snapshot_head_sha,
            "--",
            *paths,
        )
    if change.layer == "staged":
        return (
            "diff",
            "--cached",
            *common,
            snapshot.snapshot_head_sha,
            "--",
            *paths,
        )
    if change.layer == "unstaged":
        return ("diff", *common, "--", *paths)
    raise BaselineError("tracked identity requested for an unsupported Git layer")


def _path_identity(
    root: Path,
    snapshot: CanonicalGitSnapshot,
    change: SnapshotChange,
) -> PathIdentity:
    if change.layer == "untracked":
        if change.content_digest is None or change.content_kind not in {"file", "symlink"}:
            raise BaselineError("untracked Git identity is incomplete")
        digest = change.content_digest
        kind = change.content_kind
    else:
        patch = _run_git_identity(root, _tracked_patch_arguments(snapshot, change))
        digest = _sha256(
            _canonical_json(
                {
                    "layer": change.layer,
                    "status": change.status,
                    "path": change.path,
                    "old_path": change.old_path,
                    "patch_digest": _sha256(patch),
                }
            )
        )
        kind = "patch"
    return PathIdentity(
        layer=change.layer,
        status=change.status,
        path=change.path,
        old_path=change.old_path,
        identity_digest=digest,
        identity_kind=kind,
    )


def _capture_state(root: Path, *, comparison_base: str) -> CapturedState:
    try:
        before = capture_git_snapshot(root, comparison_base=comparison_base)
    except GitSnapshotError as exc:
        raise BaselineError("canonical Git snapshot capture failed") from exc
    layers = tuple(
        IdentityLayer(
            name=layer.name,
            changes=tuple(_path_identity(root, before, change) for change in layer.changes),
        )
        for layer in before.layers
    )
    try:
        after = capture_git_snapshot(root, comparison_base=before.comparison_base_sha)
    except GitSnapshotError as exc:
        raise BaselineError("canonical Git stability check failed") from exc
    if before.change_set_digest != after.change_set_digest:
        raise BaselineError("Git state changed during capture; no baseline was created")
    return CapturedState(
        comparison_base_sha=before.comparison_base_sha,
        snapshot_head_sha=before.snapshot_head_sha,
        snapshot_change_set_digest=before.change_set_digest,
        layers=layers,
        exclusions=before.exclusions,
    )


def _all_identities(layers: Sequence[IdentityLayer]) -> tuple[PathIdentity, ...]:
    return tuple(change for layer in layers for change in layer.changes)


def _identity_sort_key(item: PathIdentity) -> tuple[str, str, str, str, str]:
    return (item.layer, item.path, item.old_path or "", item.status, item.identity_digest)


def _baseline_digest(baseline: TaskStartBaseline) -> str:
    payload = asdict(baseline)
    payload.pop("baseline_digest", None)
    return _sha256(_canonical_json(payload))


def capture_task_start_baseline(
    repository: Path,
    *,
    task_path: str,
    comparison_base: str = "HEAD",
) -> TaskStartBaseline:
    """Capture one boundary in memory without changing Git or the worktree."""

    root = _safe_root(repository)
    binding, scope, _document = _load_task_binding(root, task_path)
    state = _capture_state(root, comparison_base=comparison_base)
    binding_after, scope_after, _document_after = _load_task_binding(root, task_path)
    if binding != binding_after or scope != scope_after:
        raise BaselineError("task record changed during capture; no baseline was created")
    for identity in _all_identities(state.layers):
        for endpoint in identity.endpoints:
            decision = evaluate_path_scope(
                endpoint,
                includes=scope.include_paths,
                excludes=scope.exclude_paths,
            )
            if decision.matched_include is None and decision.matched_exclude is None:
                raise BaselineError("current Git state contains an unclassified task path")
    baseline = TaskStartBaseline(
        contract=BASELINE_CONTRACT,
        schema_version=BASELINE_SCHEMA_VERSION,
        task=binding,
        comparison_base_sha=state.comparison_base_sha,
        snapshot_head_sha=state.snapshot_head_sha,
        snapshot_change_set_digest=state.snapshot_change_set_digest,
        scope=scope,
        layers=state.layers,
        exclusions=state.exclusions,
        capture_claim=CAPTURE_CLAIM,
        baseline_digest="",
    )
    return replace(baseline, baseline_digest=_baseline_digest(baseline))


def _local_baseline_path(root: Path, value: str, *, must_exist: bool) -> Path:
    normalized = _safe_relative_path(value, label="baseline path")
    if not is_segment_prefix(LOCAL_BASELINE_PREFIX, normalized):
        raise BaselineError("baseline path must be beneath .agentgov/scope-baselines")
    resolved = _resolve_inside(root, normalized, label="baseline path")
    if must_exist:
        if not resolved.exists() or not resolved.is_file() or resolved.is_symlink():
            raise BaselineError("baseline path must name an existing regular file")
    return resolved


def write_baseline(
    baseline: TaskStartBaseline,
    *,
    repository: Path,
    output_path: str,
) -> None:
    """Persist one baseline with exclusive creation and no overwrite path."""

    root = _safe_root(repository)
    target = _local_baseline_path(root, output_path, must_exist=False)
    parent = target.parent
    try:
        parent.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise BaselineError("baseline directory could not be created safely") from exc
    _resolve_inside(root, target.relative_to(root).as_posix(), label="baseline path")
    payload = baseline_to_payload(baseline)
    baseline_from_payload(payload)
    encoded = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8") + b"\n"
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    descriptor: int | None = None
    created = False
    try:
        descriptor = os.open(target, flags, 0o600)
        created = True
        with os.fdopen(descriptor, "wb") as stream:
            descriptor = None
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
    except FileExistsError as exc:
        raise BaselineError("baseline path already exists; overwrite is forbidden") from exc
    except OSError as exc:
        if descriptor is not None:
            os.close(descriptor)
        try:
            if created and target.exists():
                target.unlink()
        except OSError:
            pass
        raise BaselineError("baseline file could not be written safely") from exc


def baseline_to_payload(baseline: TaskStartBaseline) -> dict[str, Any]:
    # Round-trip through canonical JSON so immutable tuples become the arrays
    # required by the persisted contract rather than leaking Python shapes.
    return json.loads(_canonical_json(asdict(baseline)).decode("utf-8"))


def _require_fields(value: Any, expected: set[str], *, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping) or set(value) != expected:
        raise BaselineError(f"{label} has unexpected fields")
    return value


def _require_digest(value: Any, *, label: str) -> str:
    if not isinstance(value, str) or not _DIGEST_RE.fullmatch(value):
        raise BaselineError(f"{label} is not a SHA-256 digest")
    return value


def _parse_scope(value: Any) -> ScopeBinding:
    mapping = _require_fields(value, {"include_paths", "exclude_paths"}, label="baseline scope")
    parsed: list[tuple[str, ...]] = []
    for name in ("include_paths", "exclude_paths"):
        items = mapping[name]
        if not isinstance(items, list) or any(not isinstance(item, str) for item in items):
            raise BaselineError(f"baseline scope {name} must be an array of paths")
        values = tuple(items)
        if values != tuple(sorted(set(values))):
            raise BaselineError(f"baseline scope {name} is not canonical")
        for item in values:
            _safe_relative_path(item, label=f"baseline scope {name} item")
        parsed.append(values)
    return ScopeBinding(parsed[0], parsed[1])


def _parse_identity(value: Any, *, layer_name: str) -> PathIdentity:
    mapping = _require_fields(
        value,
        {"layer", "status", "path", "old_path", "identity_digest", "identity_kind"},
        label="baseline change",
    )
    if mapping["layer"] != layer_name:
        raise BaselineError("baseline change layer does not match its container")
    status = mapping["status"]
    allowed_statuses = {"untracked"} if layer_name == "untracked" else _TRACKED_STATUSES
    if status not in allowed_statuses:
        raise BaselineError("baseline change status is invalid")
    path = mapping["path"]
    old_path = mapping["old_path"]
    if not isinstance(path, str):
        raise BaselineError("baseline change path is invalid")
    _safe_relative_path(path, label="baseline change path")
    if old_path is not None:
        if not isinstance(old_path, str):
            raise BaselineError("baseline old path is invalid")
        _safe_relative_path(old_path, label="baseline old path")
    if status in {"copied", "renamed"} and old_path is None:
        raise BaselineError("baseline rename or copy is missing its old path")
    if status not in {"copied", "renamed"} and old_path is not None:
        raise BaselineError("baseline non-rename change must not have an old path")
    identity_kind = mapping["identity_kind"]
    allowed_kinds = {"file", "symlink"} if layer_name == "untracked" else {"patch"}
    if identity_kind not in allowed_kinds:
        raise BaselineError("baseline change identity kind is invalid")
    return PathIdentity(
        layer=layer_name,
        status=str(status),
        path=path,
        old_path=old_path,
        identity_digest=_require_digest(mapping["identity_digest"], label="baseline change identity"),
        identity_kind=str(identity_kind),
    )


def baseline_from_payload(value: Any) -> TaskStartBaseline:
    mapping = _require_fields(
        value,
        {
            "contract",
            "schema_version",
            "task",
            "comparison_base_sha",
            "snapshot_head_sha",
            "snapshot_change_set_digest",
            "scope",
            "layers",
            "exclusions",
            "capture_claim",
            "baseline_digest",
        },
        label="baseline",
    )
    if mapping["contract"] != BASELINE_CONTRACT or mapping["schema_version"] != BASELINE_SCHEMA_VERSION:
        raise BaselineError("baseline contract or schema version is unsupported")
    task = _require_fields(mapping["task"], {"path", "task_id", "digest"}, label="baseline task")
    if not isinstance(task["path"], str) or not isinstance(task["task_id"], str) or not task["task_id"]:
        raise BaselineError("baseline task binding is invalid")
    _safe_relative_path(task["path"], label="baseline task path")
    task_binding = TaskBinding(
        path=task["path"],
        task_id=task["task_id"],
        digest=_require_digest(task["digest"], label="baseline task digest"),
    )
    for name in ("comparison_base_sha", "snapshot_head_sha"):
        if not isinstance(mapping[name], str) or not _GIT_SHA_RE.fullmatch(mapping[name]):
            raise BaselineError(f"baseline {name} is invalid")
    layers_value = mapping["layers"]
    if not isinstance(layers_value, list):
        raise BaselineError("baseline layers must be an array")
    layers: list[IdentityLayer] = []
    for layer_value in layers_value:
        layer = _require_fields(layer_value, {"name", "changes"}, label="baseline layer")
        name = layer["name"]
        if name not in _LAYERS or not isinstance(layer["changes"], list):
            raise BaselineError("baseline layer is invalid")
        changes = tuple(_parse_identity(item, layer_name=name) for item in layer["changes"])
        if changes != tuple(sorted(changes, key=_identity_sort_key)):
            raise BaselineError("baseline changes are not canonically ordered")
        layers.append(IdentityLayer(name=name, changes=changes))
    if tuple(layer.name for layer in layers) != _LAYERS:
        raise BaselineError("baseline layers are not canonical")
    exclusions = mapping["exclusions"]
    if not isinstance(exclusions, list) or tuple(exclusions) != _SNAPSHOT_EXCLUSIONS:
        raise BaselineError("baseline snapshot exclusions are not canonical")
    if mapping["capture_claim"] != CAPTURE_CLAIM:
        raise BaselineError("baseline capture claim is not canonical")
    baseline = TaskStartBaseline(
        contract=BASELINE_CONTRACT,
        schema_version=BASELINE_SCHEMA_VERSION,
        task=task_binding,
        comparison_base_sha=mapping["comparison_base_sha"],
        snapshot_head_sha=mapping["snapshot_head_sha"],
        snapshot_change_set_digest=_require_digest(
            mapping["snapshot_change_set_digest"], label="baseline snapshot identity"
        ),
        scope=_parse_scope(mapping["scope"]),
        layers=tuple(layers),
        exclusions=tuple(exclusions),
        capture_claim=CAPTURE_CLAIM,
        baseline_digest=_require_digest(mapping["baseline_digest"], label="baseline identity"),
    )
    if _baseline_digest(baseline) != baseline.baseline_digest:
        raise BaselineError("baseline digest does not match its canonical fields")
    return baseline


def load_baseline(*, repository: Path, baseline_path: str) -> TaskStartBaseline:
    root = _safe_root(repository)
    path = _local_baseline_path(root, baseline_path, must_exist=True)
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise BaselineError("baseline file is not readable valid JSON") from exc
    return baseline_from_payload(value)


def _record_is_admitted(record: PathIdentity, scope: ScopeBinding) -> bool:
    return all(
        evaluate_path_scope(
            endpoint,
            includes=scope.include_paths,
            excludes=scope.exclude_paths,
        ).admitted
        for endpoint in record.endpoints
    )


def _record_is_classified(record: PathIdentity, scope: ScopeBinding) -> bool:
    return all(
        (decision := evaluate_path_scope(
            endpoint,
            includes=scope.include_paths,
            excludes=scope.exclude_paths,
        )).matched_include is not None
        or decision.matched_exclude is not None
        for endpoint in record.endpoints
    )


def _finding(
    status: FindingStatus,
    prefix: str,
    record: PathIdentity,
    message: str,
) -> BaselineFinding:
    return BaselineFinding(
        status=status,
        check_id=f"{prefix}:{record.layer}:{record.status}:{record.path}",
        layer=record.layer,
        path=record.path,
        old_path=record.old_path,
        message=message,
    )


def compare_task_start_baseline(
    baseline: TaskStartBaseline,
    current: CapturedState,
    *,
    current_task: TaskBinding,
) -> BaselineComparison:
    findings: list[BaselineFinding] = []
    if current_task.path != baseline.task.path or current_task.task_id != baseline.task.task_id:
        findings.append(BaselineFinding(
            FindingStatus.FAIL,
            "binding:task",
            None,
            None,
            None,
            "current task identity does not match the captured task",
        ))
    if current_task.digest != baseline.task.digest:
        findings.append(BaselineFinding(
            FindingStatus.FAIL,
            "binding:task-digest",
            None,
            None,
            None,
            "task contract changed after baseline capture",
        ))
    if current.comparison_base_sha != baseline.comparison_base_sha:
        findings.append(BaselineFinding(
            FindingStatus.FAIL,
            "binding:comparison-base",
            None,
            None,
            None,
            "comparison base changed after baseline capture",
        ))
    if current.snapshot_head_sha != baseline.snapshot_head_sha:
        findings.append(BaselineFinding(
            FindingStatus.FAIL,
            "binding:head",
            None,
            None,
            None,
            "Git HEAD changed after baseline capture",
        ))
    if current.exclusions != baseline.exclusions:
        findings.append(BaselineFinding(
            FindingStatus.FAIL,
            "binding:exclusions",
            None,
            None,
            None,
            "Git snapshot exclusions changed after baseline capture",
        ))

    before = set(_all_identities(baseline.layers))
    after = set(_all_identities(current.layers))
    for record in sorted(before, key=_identity_sort_key):
        if record in after:
            if _record_is_admitted(record, baseline.scope):
                findings.append(_finding(
                    FindingStatus.PASS,
                    "baseline-unchanged-included",
                    record,
                    "pre-existing included change is unchanged",
                ))
            elif _record_is_classified(record, baseline.scope):
                findings.append(_finding(
                    FindingStatus.PRESERVED,
                    "baseline-preserved-excluded",
                    record,
                    "pre-existing excluded change is byte-identical at its Git layer",
                ))
            else:
                findings.append(_finding(
                    FindingStatus.FAIL,
                    "baseline-unclassified",
                    record,
                    "pre-existing change is not classified by the captured task scope",
                ))
            continue
        status = FindingStatus.PASS if _record_is_admitted(record, baseline.scope) else FindingStatus.FAIL
        message = (
            "pre-existing included change may evolve within admitted scope"
            if status is FindingStatus.PASS
            else "pre-existing excluded change changed layer, identity, endpoint, or presence"
        )
        findings.append(_finding(status, "baseline-changed", record, message))

    for record in sorted(after - before, key=_identity_sort_key):
        admitted = _record_is_admitted(record, baseline.scope)
        findings.append(_finding(
            FindingStatus.PASS if admitted else FindingStatus.FAIL,
            "current-delta",
            record,
            (
                "post-start change is inside the captured include scope"
                if admitted
                else "post-start change has an excluded or unclassified endpoint"
            ),
        ))
    if not findings:
        findings.append(BaselineFinding(
            FindingStatus.PASS,
            "scope:no-changes",
            None,
            None,
            None,
            "baseline and current Git state contain no changed paths",
        ))
    return BaselineComparison(
        contract=COMPARISON_CONTRACT,
        schema_version=COMPARISON_SCHEMA_VERSION,
        task_id=baseline.task.task_id,
        task_path=baseline.task.path,
        task_digest=baseline.task.digest,
        baseline_digest=baseline.baseline_digest,
        comparison_base_sha=baseline.comparison_base_sha,
        baseline_head_sha=baseline.snapshot_head_sha,
        current_head_sha=current.snapshot_head_sha,
        findings=tuple(findings),
        known_limits=(
            "the boundary begins at capture and cannot prove or authorize earlier work",
            "hash identities show change or preservation, not requirement correctness",
            "public CLI and development-session integration are deferred",
        ),
        authority_boundary={
            "writes_repository": False,
            "modifies_worktree": False,
            "modifies_index": False,
            "modifies_branch": False,
            "modifies_history": False,
            "authorizes_exception": False,
            "authorizes_commit": False,
        },
    )


def check_task_start_baseline(
    repository: Path,
    *,
    task_path: str,
    baseline_path: str,
) -> BaselineComparison:
    root = _safe_root(repository)
    baseline = load_baseline(repository=root, baseline_path=baseline_path)
    binding, _scope, _document = _load_task_binding(root, task_path)
    current = _capture_state(root, comparison_base=baseline.comparison_base_sha)
    return compare_task_start_baseline(baseline, current, current_task=binding)


def comparison_to_payload(report: BaselineComparison) -> dict[str, Any]:
    payload = asdict(report)
    for finding in payload["findings"]:
        finding["status"] = finding["status"].value
    return payload
