"""Fresh validation evidence and completion reconciliation."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import uuid
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any, Mapping

from agentgov import __version__
from agentgov.event_store import append_governance_event, utc_now, write_local_record
from agentgov.git_snapshot import (
    CanonicalGitSnapshot,
    GitSnapshotError,
    capture_git_snapshot,
    explain_snapshot_difference,
    snapshot_from_payload,
    snapshot_to_payload,
)
from agentgov.path_policy import evaluate_path_scope
from agentgov.task_contract import (
    canonical_task_digest,
    check_development_task,
    load_development_task,
)


EVIDENCE_CONTRACT = "agentgov.development-evidence"
EVIDENCE_SCHEMA_VERSION = "1.0"
COMPLETION_CONTRACT = "agentgov.development-completion"
COMPLETION_SCHEMA_VERSION = "1.0"
_SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")


class EvidenceError(RuntimeError):
    """Validation evidence cannot be created or reconciled truthfully."""


@dataclass(frozen=True)
class CommandEvidence:
    command_index: int
    command_identity: str
    started_at: str
    completed_at: str
    exit_code: int
    stdout_digest: str
    stderr_digest: str


@dataclass(frozen=True)
class ValidationEvidence:
    contract: str
    schema_version: str
    evidence_id: str
    created_at: str
    agentgov_version: str
    task_id: str
    task_path: str
    task_digest: str
    comparison_base_sha: str
    snapshot_head_sha: str
    change_set_digest: str
    digest_format_version: str
    snapshot_before: CanonicalGitSnapshot
    snapshot_after: CanonicalGitSnapshot
    commands: tuple[CommandEvidence, ...]
    outcome: str
    mutation_reasons: tuple[str, ...]
    authority_boundary: Mapping[str, bool]


@dataclass(frozen=True)
class ValidationRun:
    evidence: ValidationEvidence
    evidence_ref: str
    event_ref: str
    transient_outputs: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class CompletionFinding:
    status: str
    check_id: str
    message: str


@dataclass(frozen=True)
class CompletionReport:
    contract: str
    schema_version: str
    task_id: str
    task_path: str
    task_digest: str
    state: str
    evidence_ref: str | None
    evidence_id: str | None
    comparison_base_sha: str | None
    snapshot_head_sha: str | None
    change_set_digest: str | None
    findings: tuple[CompletionFinding, ...]
    known_limits: tuple[str, ...]
    event_ref: str | None
    authority_boundary: Mapping[str, bool]


def _digest_bytes(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def _command_identity(command: str) -> str:
    return _digest_bytes(command.encode("utf-8"))


def _safe_repository(repository: Path) -> Path:
    if repository.is_symlink() or not repository.exists() or not repository.is_dir():
        raise EvidenceError("repository root must be an existing non-symbolic-link directory")
    return repository.resolve()


def _admitted_task(task_path: Path, root: Path) -> tuple[Path, Mapping[str, Any]]:
    report = check_development_task(task_path, repository=root)
    if report.has_failures:
        messages = "; ".join(item.message for item in report.findings)
        raise EvidenceError(f"task contract is not eligible: {messages}")
    document = load_development_task(report.path)
    decision = document.get("decision")
    if not isinstance(decision, Mapping) or decision.get("state") != "admitted":
        raise EvidenceError("fresh evidence requires an admitted task")
    return report.path, document


def _task_digest_if_valid(task_path: Path, root: Path) -> str | None:
    try:
        report = check_development_task(task_path, repository=root)
        if report.has_failures:
            return None
        return canonical_task_digest(load_development_task(report.path))
    except (OSError, ValueError, json.JSONDecodeError):
        return None


def _evidence_payload(evidence: ValidationEvidence) -> dict[str, Any]:
    payload = asdict(evidence)
    payload["snapshot_before"] = snapshot_to_payload(evidence.snapshot_before)
    payload["snapshot_after"] = snapshot_to_payload(evidence.snapshot_after)
    return payload


def run_task_validation(
    task_path: Path,
    *,
    repository: Path,
    comparison_base: str,
    actor_class: str = "coding_agent",
    actor_label: str | None = None,
    timeout_seconds: int = 1800,
) -> ValidationRun:
    """Run human-declared validation commands and persist privacy-bounded evidence."""

    root = _safe_repository(repository)
    resolved_task, task = _admitted_task(task_path, root)
    task_digest = canonical_task_digest(task)
    before = capture_git_snapshot(root, comparison_base=comparison_base)
    command_results: list[CommandEvidence] = []
    transient_outputs: list[tuple[str, str]] = []
    commands = task.get("validation_commands")
    if not isinstance(commands, list) or not commands:
        raise EvidenceError("admitted task has no validation commands")
    for index, command in enumerate(commands):
        if not isinstance(command, str):
            raise EvidenceError("validation command must be a string")
        started_at = utc_now()
        completed = subprocess.run(
            command,
            cwd=root,
            shell=True,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=timeout_seconds,
        )
        completed_at = utc_now()
        stdout = completed.stdout.decode("utf-8", errors="replace")
        stderr = completed.stderr.decode("utf-8", errors="replace")
        transient_outputs.append((stdout, stderr))
        command_results.append(
            CommandEvidence(
                command_index=index,
                command_identity=_command_identity(command),
                started_at=started_at,
                completed_at=completed_at,
                exit_code=completed.returncode,
                stdout_digest=_digest_bytes(completed.stdout),
                stderr_digest=_digest_bytes(completed.stderr),
            )
        )
        if completed.returncode != 0:
            break
    after = capture_git_snapshot(root, comparison_base=before.comparison_base_sha)
    mutation_reasons = list(explain_snapshot_difference(before, after))
    current_task_digest = _task_digest_if_valid(resolved_task, root)
    if current_task_digest != task_digest:
        mutation_reasons.insert(0, "task contract changed or became invalid during validation")
    all_commands_passed = (
        len(command_results) == len(commands)
        and all(item.exit_code == 0 for item in command_results)
    )
    if mutation_reasons:
        outcome = "stale"
    elif all_commands_passed:
        outcome = "passed"
    else:
        outcome = "failed"
    evidence_id = f"evd-{uuid.uuid4().hex}"
    evidence = ValidationEvidence(
        contract=EVIDENCE_CONTRACT,
        schema_version=EVIDENCE_SCHEMA_VERSION,
        evidence_id=evidence_id,
        created_at=utc_now(),
        agentgov_version=__version__,
        task_id=str(task["task_id"]),
        task_path=resolved_task.relative_to(root).as_posix(),
        task_digest=task_digest,
        comparison_base_sha=after.comparison_base_sha,
        snapshot_head_sha=after.snapshot_head_sha,
        change_set_digest=after.change_set_digest,
        digest_format_version=after.format_version,
        snapshot_before=before,
        snapshot_after=after,
        commands=tuple(command_results),
        outcome=outcome,
        mutation_reasons=tuple(mutation_reasons),
        authority_boundary={
            "authorizes_requirement_completion": False,
            "authorizes_architecture_correctness": False,
            "authorizes_exception": False,
            "authorizes_commit": False,
            "authorizes_merge": False,
            "authorizes_deployment": False,
        },
    )
    evidence_ref = write_local_record(
        root,
        area="evidence",
        record_id=evidence_id,
        payload=_evidence_payload(evidence),
    )
    reason_codes = ("declared_validation_requested",) + tuple(
        ["snapshot_mutated"] if mutation_reasons else []
    ) + tuple(["validation_failed"] if not all_commands_passed else [])
    _, event_ref = append_governance_event(
        root,
        event_type="validation.completed",
        actor_class=actor_class,
        actor_label=actor_label,
        task_id=evidence.task_id,
        task_digest=evidence.task_digest,
        outcome=evidence.outcome,
        evidence_ref=evidence_ref,
        reason_codes=reason_codes,
        metrics={
            "commands_declared": len(commands),
            "commands_run": len(command_results),
            "commands_passed": sum(item.exit_code == 0 for item in command_results),
        },
    )
    return ValidationRun(
        evidence=evidence,
        evidence_ref=evidence_ref,
        event_ref=event_ref,
        transient_outputs=tuple(transient_outputs),
    )


def _load_evidence_payload(path: Path) -> ValidationEvidence:
    if path.is_symlink():
        raise EvidenceError("evidence record must not be a symbolic link")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise EvidenceError(f"cannot read evidence record: {exc}") from exc
    required = {
        "contract", "schema_version", "evidence_id", "created_at", "agentgov_version",
        "task_id", "task_path", "task_digest", "comparison_base_sha",
        "snapshot_head_sha", "change_set_digest", "digest_format_version",
        "snapshot_before", "snapshot_after", "commands", "outcome",
        "mutation_reasons", "authority_boundary",
    }
    if not isinstance(payload, dict) or set(payload) != required:
        raise EvidenceError("evidence record has unexpected fields")
    if payload.get("contract") != EVIDENCE_CONTRACT or payload.get("schema_version") != EVIDENCE_SCHEMA_VERSION:
        raise EvidenceError("evidence record contract is unsupported")
    commands = payload.get("commands")
    if not isinstance(commands, list):
        raise EvidenceError("evidence commands must be an array")
    command_fields = {
        "command_index", "command_identity", "started_at", "completed_at",
        "exit_code", "stdout_digest", "stderr_digest",
    }
    for item in commands:
        if not isinstance(item, dict) or set(item) != command_fields:
            raise EvidenceError("command evidence has unexpected fields")
        if not isinstance(item.get("command_index"), int) or not isinstance(item.get("exit_code"), int):
            raise EvidenceError("command evidence indexes and exit codes must be integers")
        for key in ("command_identity", "stdout_digest", "stderr_digest"):
            if not isinstance(item.get(key), str) or not _SHA256_RE.fullmatch(item[key]):
                raise EvidenceError(f"command evidence {key} is invalid")
        for key in ("started_at", "completed_at"):
            if not isinstance(item.get(key), str) or not item[key]:
                raise EvidenceError(f"command evidence {key} is invalid")
    mutation_reasons = payload.get("mutation_reasons")
    if not isinstance(mutation_reasons, list) or any(not isinstance(item, str) or not item for item in mutation_reasons):
        raise EvidenceError("evidence mutation_reasons must be an array of strings")
    if not isinstance(payload.get("authority_boundary"), dict):
        raise EvidenceError("evidence authority_boundary must be an object")
    try:
        command_records = tuple(CommandEvidence(**item) for item in commands)
        before = snapshot_from_payload(payload["snapshot_before"])
        after = snapshot_from_payload(payload["snapshot_after"])
    except (TypeError, GitSnapshotError) as exc:
        raise EvidenceError(f"evidence record is invalid: {exc}") from exc
    return ValidationEvidence(
        contract=payload["contract"],
        schema_version=payload["schema_version"],
        evidence_id=payload["evidence_id"],
        created_at=payload["created_at"],
        agentgov_version=payload["agentgov_version"],
        task_id=payload["task_id"],
        task_path=payload["task_path"],
        task_digest=payload["task_digest"],
        comparison_base_sha=payload["comparison_base_sha"],
        snapshot_head_sha=payload["snapshot_head_sha"],
        change_set_digest=payload["change_set_digest"],
        digest_format_version=payload["digest_format_version"],
        snapshot_before=before,
        snapshot_after=after,
        commands=command_records,
        outcome=payload["outcome"],
        mutation_reasons=tuple(mutation_reasons),
        authority_boundary=payload["authority_boundary"],
    )


def _resolve_evidence_path(root: Path, task_id: str, evidence_path: Path | None) -> Path | None:
    evidence_root = root / ".agentgov" / "evidence"
    if evidence_path is not None:
        candidate = evidence_path if evidence_path.is_absolute() else root / evidence_path
        candidate = candidate.resolve()
        try:
            candidate.relative_to(evidence_root.resolve())
        except ValueError as exc:
            raise EvidenceError("evidence must be beneath .agentgov/evidence") from exc
        if candidate.is_symlink():
            raise EvidenceError("evidence record must not be a symbolic link")
        return candidate
    if not evidence_root.exists():
        return None
    candidates: list[tuple[str, str, Path]] = []
    for path in evidence_root.glob("evd-*.json"):
        try:
            evidence = _load_evidence_payload(path)
        except EvidenceError:
            continue
        if evidence.task_id == task_id:
            candidates.append((evidence.created_at, evidence.evidence_id, path))
    return max(candidates, default=("", "", None), key=lambda item: (item[0], item[1]))[2]


def _scope_findings(task: Mapping[str, Any], snapshot: CanonicalGitSnapshot) -> list[CompletionFinding]:
    scope = task.get("scope")
    assert isinstance(scope, Mapping)
    includes = tuple(scope["include_paths"])
    excludes = tuple(scope["exclude_paths"])
    findings: list[CompletionFinding] = []
    for layer in snapshot.layers:
        for change in layer.changes:
            endpoints = (
                tuple(path for path in (change.old_path, change.path) if path is not None)
                if change.status == "renamed"
                else (change.path,)
            )
            decisions = [evaluate_path_scope(path, includes=includes, excludes=excludes) for path in endpoints]
            if not all(item.admitted for item in decisions):
                failed = ", ".join(item.path for item in decisions if not item.admitted)
                findings.append(
                    CompletionFinding("FAIL", "scope.changed", f"{layer.name} change is outside admitted scope: {failed}")
                )
    if not findings:
        findings.append(CompletionFinding("PASS", "scope.changed", "all canonical changed paths are inside admitted scope"))
    return findings


def _evidence_integrity_errors(
    evidence: ValidationEvidence,
    task: Mapping[str, Any],
) -> tuple[str, ...]:
    errors: list[str] = []
    after = evidence.snapshot_after
    if evidence.comparison_base_sha != after.comparison_base_sha:
        errors.append("top-level comparison base does not match snapshot_after")
    if evidence.snapshot_head_sha != after.snapshot_head_sha:
        errors.append("top-level snapshot HEAD does not match snapshot_after")
    if evidence.change_set_digest != after.change_set_digest:
        errors.append("top-level change-set digest does not match snapshot_after")
    if evidence.digest_format_version != after.format_version:
        errors.append("top-level digest format does not match snapshot_after")
    if evidence.snapshot_before.comparison_base_sha != after.comparison_base_sha:
        errors.append("validation snapshots use different comparison bases")
    commands = task.get("validation_commands")
    if not isinstance(commands, list):
        errors.append("current task validation commands are invalid")
        commands = []
    if len(evidence.commands) != len(commands):
        errors.append("evidence does not cover every current task validation command")
    for index, command in enumerate(commands):
        if index >= len(evidence.commands):
            break
        recorded = evidence.commands[index]
        if recorded.command_index != index:
            errors.append(f"command evidence index {index} is not canonical")
        if not isinstance(command, str) or recorded.command_identity != _command_identity(command):
            errors.append(f"command evidence identity {index} does not match the task")
    snapshot_mutations = explain_snapshot_difference(evidence.snapshot_before, after)
    if evidence.outcome == "passed":
        if snapshot_mutations or evidence.mutation_reasons:
            errors.append("passed evidence contains validation-time snapshot mutations")
        if any(item.exit_code != 0 for item in evidence.commands):
            errors.append("passed evidence contains a failed validation command")
    elif evidence.outcome == "stale":
        if not evidence.mutation_reasons:
            errors.append("stale evidence does not explain its validation-time mutation")
    elif evidence.outcome == "failed":
        if not any(item.exit_code != 0 for item in evidence.commands):
            errors.append("failed evidence contains no failed validation command")
    else:
        errors.append("evidence outcome is unsupported")
    expected_authority = {
        "authorizes_requirement_completion": False,
        "authorizes_architecture_correctness": False,
        "authorizes_exception": False,
        "authorizes_commit": False,
        "authorizes_merge": False,
        "authorizes_deployment": False,
    }
    if dict(evidence.authority_boundary) != expected_authority:
        errors.append("evidence authority boundary is invalid")
    return tuple(errors)


def _assess_task_completion(
    task_path: Path,
    *,
    repository: Path,
    evidence_path: Path | None = None,
) -> tuple[CompletionReport, tuple[str, ...]]:
    root = _safe_repository(repository)
    resolved_task, task = _admitted_task(task_path, root)
    task_digest = canonical_task_digest(task)
    task_id = str(task["task_id"])
    selected_path = _resolve_evidence_path(root, task_id, evidence_path)
    findings: list[CompletionFinding] = []
    evidence: ValidationEvidence | None = None
    current: CanonicalGitSnapshot | None = None
    relative_evidence: str | None = None
    reason_codes: list[str] = []
    if selected_path is None:
        findings.append(CompletionFinding("FAIL", "evidence.missing", "no validation evidence exists for this task; run validation before finish"))
        reason_codes.append("evidence_missing")
    else:
        evidence = _load_evidence_payload(selected_path)
        relative_evidence = selected_path.relative_to(root).as_posix()
        if evidence.task_id != task_id:
            findings.append(CompletionFinding("FAIL", "evidence.task", "evidence belongs to a different task"))
            reason_codes.append("evidence_task_mismatch")
        if evidence.task_digest != task_digest:
            findings.append(CompletionFinding("FAIL", "evidence.task_digest", "task contract changed after validation; rerun validation"))
            reason_codes.append("task_changed")
        integrity_errors = _evidence_integrity_errors(evidence, task)
        if integrity_errors:
            findings.extend(
                CompletionFinding("FAIL", "evidence.integrity", message)
                for message in integrity_errors
            )
            reason_codes.append("evidence_integrity")
        if evidence.outcome != "passed":
            findings.append(CompletionFinding("FAIL", "evidence.outcome", f"validation evidence outcome is {evidence.outcome!r}; rerun validation"))
            reason_codes.append("evidence_not_passed")
            if evidence.outcome == "stale":
                findings.extend(
                    CompletionFinding(
                        "FAIL",
                        "evidence.validation_mutation",
                        reason
                        + "; inspect and retain task work, remove disposable output, "
                        "or add an intentional ignore rule, then rerun validation",
                    )
                    for reason in evidence.mutation_reasons
                )
        current = capture_git_snapshot(root, comparison_base=evidence.comparison_base_sha)
        differences = explain_snapshot_difference(evidence.snapshot_after, current)
        if differences:
            findings.extend(
                CompletionFinding("FAIL", "evidence.stale", reason + "; inspect and retain task work, remove disposable output, or add an intentional ignore rule, then rerun validation")
                for reason in differences
            )
            reason_codes.append("snapshot_changed")
        else:
            findings.append(CompletionFinding("PASS", "evidence.fresh", "task, HEAD, index, worktree, rename, and non-ignored untracked identities match validation evidence"))
        findings.extend(_scope_findings(task, current))
    architecture_refs = task.get("architecture_refs")
    if architecture_refs:
        findings.append(CompletionFinding("ADVISORY", "architecture.review", "passing evidence does not prove requirement or architecture correctness; review the selected architecture context"))
    verified = evidence is not None and not any(item.status == "FAIL" for item in findings)
    state = "verified" if verified else "needs_evidence"
    snapshot = current or (evidence.snapshot_after if evidence is not None else None)
    provisional = CompletionReport(
        contract=COMPLETION_CONTRACT,
        schema_version=COMPLETION_SCHEMA_VERSION,
        task_id=task_id,
        task_path=resolved_task.relative_to(root).as_posix(),
        task_digest=task_digest,
        state=state,
        evidence_ref=relative_evidence,
        evidence_id=evidence.evidence_id if evidence else None,
        comparison_base_sha=snapshot.comparison_base_sha if snapshot else None,
        snapshot_head_sha=snapshot.snapshot_head_sha if snapshot else None,
        change_set_digest=snapshot.change_set_digest if snapshot else None,
        findings=tuple(findings),
        known_limits=(
            "verified means declared commands passed against an unchanged governed snapshot",
            "verified does not prove requirement satisfaction, architecture correctness, or validation sufficiency",
            "local events are not visible to CI unless a later explicit redacted export is performed",
        ),
        event_ref=None,
        authority_boundary={
            "authorizes_requirement_completion": False,
            "authorizes_architecture_correctness": False,
            "authorizes_exception": False,
            "authorizes_commit": False,
            "authorizes_merge": False,
            "authorizes_deployment": False,
        },
    )
    return provisional, tuple(dict.fromkeys(["completion_reconciliation_requested", *reason_codes]))


def inspect_task_completion(
    task_path: Path,
    *,
    repository: Path,
    evidence_path: Path | None = None,
) -> CompletionReport:
    """Re-establish completion evidence freshness without appending an event."""

    report, _reason_codes = _assess_task_completion(
        task_path,
        repository=repository,
        evidence_path=evidence_path,
    )
    return report


def reconcile_task_completion(
    task_path: Path,
    *,
    repository: Path,
    evidence_path: Path | None = None,
    actor_class: str = "coding_agent",
    actor_label: str | None = None,
) -> CompletionReport:
    """Assess completion and append one immutable reconciliation observation."""

    root = _safe_repository(repository)
    provisional, reason_codes = _assess_task_completion(
        task_path,
        repository=root,
        evidence_path=evidence_path,
    )
    _, event_ref = append_governance_event(
        root,
        event_type="completion.reconciled",
        actor_class=actor_class,
        actor_label=actor_label,
        task_id=provisional.task_id,
        task_digest=provisional.task_digest,
        outcome=provisional.state,
        evidence_ref=provisional.evidence_ref,
        reason_codes=reason_codes,
        metrics={
            "failures": sum(item.status == "FAIL" for item in provisional.findings),
            "advisories": sum(item.status == "ADVISORY" for item in provisional.findings),
        },
    )
    return replace(provisional, event_ref=event_ref)


def render_validation_json(run: ValidationRun) -> str:
    return json.dumps(
        _evidence_payload(run.evidence),
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    ) + "\n"


def render_validation_terminal(run: ValidationRun) -> str:
    evidence = run.evidence
    lines = [
        f"VALIDATION task={evidence.task_id} outcome={evidence.outcome}",
        *(f"COMMAND index={item.command_index} exit={item.exit_code} identity={item.command_identity}" for item in evidence.commands),
        *(f"STALE {reason}" for reason in evidence.mutation_reasons),
        f"EVIDENCE {run.evidence_ref}",
        f"EVENT {run.event_ref}",
        "NOTE passing evidence proves only declared commands ran against an unchanged snapshot",
    ]
    return "\n".join(lines) + "\n"


def render_validation_markdown(run: ValidationRun) -> str:
    evidence = run.evidence
    lines = [
        f"# Validation evidence: {evidence.task_id}",
        "",
        f"- Outcome: `{evidence.outcome}`",
        f"- Evidence: `{run.evidence_ref}`",
        f"- Event: `{run.event_ref}`",
        f"- Comparison base: `{evidence.comparison_base_sha}`",
        f"- Snapshot HEAD: `{evidence.snapshot_head_sha}`",
        f"- Change-set digest: `{evidence.change_set_digest}`",
        "",
        "## Commands",
        "",
        "| Index | Identity | Exit |",
        "|---:|---|---:|",
        *(f"| {item.command_index} | `{item.command_identity}` | {item.exit_code} |" for item in evidence.commands),
    ]
    if evidence.mutation_reasons:
        lines.extend(["", "## Snapshot mutations", ""])
        lines.extend(f"- {reason}" for reason in evidence.mutation_reasons)
    lines.extend(["", "> Passing evidence proves only that declared commands ran against an unchanged governed snapshot.", ""])
    return "\n".join(lines)


def render_completion_json(report: CompletionReport) -> str:
    return json.dumps(asdict(report), ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def render_completion_terminal(report: CompletionReport) -> str:
    lines = [
        f"FINISH task={report.task_id} state={report.state}",
        *(f"{item.status} {item.check_id}: {item.message}" for item in report.findings),
        f"EVENT {report.event_ref}",
        "NOTE finish does not authorize commit, merge, deployment, or a semantic correctness claim",
    ]
    return "\n".join(lines) + "\n"


def render_completion_markdown(report: CompletionReport) -> str:
    lines = [
        f"# Development completion: {report.task_id}",
        "",
        f"- State: `{report.state}`",
        f"- Evidence: `{report.evidence_ref}`",
        f"- Event: `{report.event_ref}`",
        "",
        "## Findings",
        "",
        "| Status | Check | Message |",
        "|---|---|---|",
    ]
    for finding in report.findings:
        message = finding.message.replace("|", "\\|").replace("\n", " ")
        lines.append(f"| {finding.status} | `{finding.check_id}` | {message} |")
    lines.extend(["", "## Known limits", ""])
    lines.extend(f"- {item}" for item in report.known_limits)
    lines.append("")
    return "\n".join(lines)
