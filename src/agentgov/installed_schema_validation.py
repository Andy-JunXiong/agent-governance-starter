"""One-shot, no-model validation of an installed App Server schema.

This internal driver is intentionally not part of the public ``agentgov`` CLI.
It composes the privacy-bounded Windows process observer, the deterministic
process-attribution gate, and the pure schema diagnostic.  Public results use
only stable codes, normalized fields, bounded counts, and booleans.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from agentgov.app_server_schema_diagnostic import (
    AppServerSchemaDiagnostic,
    diagnose_thread_start_schema,
)
from agentgov.windows_process_observer import (
    ObservedProcessBoundary,
    WindowsProcessSnapshot,
    assess_ambient_process_baseline,
    observe_windows_processes,
    reconcile_windows_processes,
)


VALIDATION_STATUSES = frozenset({"compatible", "incompatible", "indeterminate"})

_TEMP_PREFIX = "agentgov-installed-schema-v2-"
_HELP_TIMEOUT_SECONDS = 20
_MAX_HELP_BYTES = 128 * 1024
_MAX_SCHEMA_DOCUMENTS = 64
_MAX_SCHEMA_DOCUMENT_BYTES = 4 * 1024 * 1024
_MAX_SCHEMA_TOTAL_BYTES = 16 * 1024 * 1024
_MAX_CONFIG_BYTES = 4 * 1024 * 1024

_NORMALIZED_REQUEST = {
    "approvalPolicy": "never",
    "cwd": "C:/synthetic",
    "ephemeral": True,
    "sandbox": "workspace-write",
}


@dataclass(frozen=True, order=True)
class InstalledSchemaValidationFinding:
    """One normalized validation fact with no host-local value."""

    code: str
    field: str | None = None


@dataclass(frozen=True)
class InstalledSchemaValidationResult:
    """Privacy-safe retained result for one controlled attempt."""

    status: str
    stage: str
    findings: tuple[InstalledSchemaValidationFinding, ...]
    document_count: int
    checked_fields: tuple[str, ...]
    preflight_counts: tuple[tuple[str, int], ...]
    postflight_counts: tuple[tuple[str, int], ...]
    ambient_counts: tuple[tuple[str, int], ...]
    remaining_task_owned_counts: tuple[tuple[str, int], ...]
    help_queries: int
    generation_attempts: int
    cleanup_verified: bool
    host_state_unchanged: bool

    def __post_init__(self) -> None:
        if self.status not in VALIDATION_STATUSES:
            raise ValueError("unsupported installed-schema validation status")

    @property
    def reason_codes(self) -> tuple[str, ...]:
        return tuple(finding.code for finding in self.findings)

    def as_dict(self) -> dict[str, Any]:
        return {
            "ambient_counts": dict(self.ambient_counts),
            "checked_fields": list(self.checked_fields),
            "cleanup_verified": self.cleanup_verified,
            "contract": "agentgov.installed-schema-validation-result",
            "document_count": self.document_count,
            "generation_attempts": self.generation_attempts,
            "help_queries": self.help_queries,
            "host_state_unchanged": self.host_state_unchanged,
            "postflight_counts": dict(self.postflight_counts),
            "preflight_counts": dict(self.preflight_counts),
            "reason_codes": list(self.reason_codes),
            "remaining_task_owned_counts": dict(
                self.remaining_task_owned_counts
            ),
            "schema_version": "1.0",
            "stage": self.stage,
            "status": self.status,
        }


@dataclass(frozen=True)
class _HostState:
    status: str
    trust_match_count: int
    findings: tuple[str, ...]
    _config_fingerprint: str = field(repr=False, compare=True)
    _repository_fingerprint: str = field(repr=False, compare=True)


@dataclass(frozen=True)
class _CommandSelection:
    status: str
    code: str
    _entry: Path | None = field(default=None, repr=False, compare=False)


@dataclass(frozen=True)
class GenerationOutcome:
    """Private launch result; the process identifier is never retained publicly."""

    code: str
    return_code: int | None
    _task_root_process_id: int | None = field(
        default=None, repr=False, compare=False
    )


@dataclass(frozen=True)
class _LoadedDocuments:
    status: str
    count: int
    findings: tuple[str, ...]
    _documents: tuple[Any, ...] = field(default=(), repr=False, compare=False)


@dataclass(frozen=True)
class _AggregatedDiagnostic:
    status: str
    findings: tuple[InstalledSchemaValidationFinding, ...]
    checked_fields: tuple[str, ...]


CommandEntries = Callable[[], Sequence[Path]]
HelpProbe = Callable[[Path], str | None]
ProcessObserver = Callable[[], WindowsProcessSnapshot]
GenerationRunner = Callable[[Path, Path, Path], GenerationOutcome]
StateProbe = Callable[[Path], _HostState]
TempFactory = Callable[[], Path]
TempCleanup = Callable[[Path], bool]


def _finding(
    code: str, field: str | None = None
) -> InstalledSchemaValidationFinding:
    return InstalledSchemaValidationFinding(code=code, field=field)


def _ordered_findings(
    findings: Sequence[InstalledSchemaValidationFinding],
) -> tuple[InstalledSchemaValidationFinding, ...]:
    return tuple(sorted(set(findings), key=lambda item: (item.code, item.field or "")))


def _discover_codex_entries() -> tuple[Path, ...]:
    if os.name != "nt":
        return ()
    entries: set[Path] = set()
    for raw_directory in os.environ.get("PATH", "").split(os.pathsep):
        if not raw_directory:
            continue
        try:
            candidate = Path(raw_directory) / "codex.cmd"
            if candidate.is_file() and not candidate.is_symlink():
                entries.add(candidate.resolve())
        except OSError:
            continue
    return tuple(sorted(entries, key=lambda item: str(item).casefold()))


def _select_codex_entry(entries: Sequence[Path]) -> _CommandSelection:
    candidates: list[Path] = []
    try:
        for value in entries:
            path = Path(value)
            if (
                path.name.casefold() == "codex.cmd"
                and path.is_file()
                and not path.is_symlink()
            ):
                candidates.append(path.resolve())
    except (OSError, TypeError, ValueError):
        return _CommandSelection("indeterminate", "native_entry_invalid")
    unique = tuple(sorted(set(candidates), key=lambda item: str(item).casefold()))
    if not unique:
        return _CommandSelection("indeterminate", "native_entry_not_found")
    if len(unique) != 1:
        return _CommandSelection("indeterminate", "native_entry_ambiguous")
    return _CommandSelection("ready", "native_entry_ready", unique[0])


def _default_help_probe(entry: Path) -> str | None:
    try:
        completed = subprocess.run(
            (str(entry), "app-server", "generate-json-schema", "--help"),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=False,
            timeout=_HELP_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.SubprocessError):
        return "schema_help_query_failed"
    if completed.returncode != 0 or len(completed.stdout) > _MAX_HELP_BYTES:
        return "schema_help_query_failed"
    try:
        help_text = completed.stdout.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        return "schema_help_output_invalid"
    required_markers = (
        "app-server generate-json-schema",
        "--out <DIR>",
        "--experimental",
    )
    if not all(marker in help_text for marker in required_markers):
        return "schema_help_surface_unexpected"
    return None


def _run_git_bytes(repository: Path, *arguments: str) -> bytes | None:
    try:
        completed = subprocess.run(
            (
                "git",
                "-c",
                "core.quotepath=false",
                "-C",
                str(repository),
                *arguments,
            ),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=False,
            timeout=30,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return completed.stdout if completed.returncode == 0 else None


def _default_state_probe(repository: Path) -> _HostState:
    findings: list[str] = []
    try:
        root = repository.resolve(strict=True)
    except (OSError, RuntimeError):
        return _HostState(
            "indeterminate", 0, ("repository_state_unavailable",), "", ""
        )
    if not root.is_dir() or root.is_symlink():
        return _HostState(
            "indeterminate", 0, ("repository_state_unavailable",), "", ""
        )

    config_path = Path.home() / ".codex" / "config.toml"
    try:
        if config_path.exists():
            config_bytes = config_path.read_bytes()
            if len(config_bytes) > _MAX_CONFIG_BYTES:
                findings.append("configuration_state_unavailable")
                config_bytes = b""
        else:
            config_bytes = b"<absent>"
    except OSError:
        findings.append("configuration_state_unavailable")
        config_bytes = b""

    status = _run_git_bytes(root, "status", "--porcelain=v1", "-z", "--untracked-files=all")
    head = _run_git_bytes(root, "rev-parse", "HEAD")
    remotes = _run_git_bytes(root, "remote", "-v")
    if status is None or head is None or remotes is None:
        findings.append("repository_state_unavailable")
        repository_bytes = b""
    else:
        repository_bytes = b"\0".join((status, head, remotes))

    config_text = config_bytes.decode("utf-8", errors="ignore").casefold()
    path_variants = {
        str(root).casefold(),
        str(root).replace("\\", "/").casefold(),
        str(root).replace("\\", "\\\\").casefold(),
    }
    trust_match_count = sum(config_text.count(value) for value in path_variants)
    return _HostState(
        "indeterminate" if findings else "ready",
        trust_match_count,
        tuple(sorted(set(findings))),
        hashlib.sha256(config_bytes).hexdigest(),
        hashlib.sha256(repository_bytes).hexdigest(),
    )


def _host_state_matches(before: _HostState, after: _HostState) -> bool:
    return before.status == after.status == "ready" and before == after


def _verified_temp_directory(path: Path) -> Path | None:
    try:
        if path.is_symlink():
            return None
        resolved = path.resolve(strict=True)
        temp_root = Path(tempfile.gettempdir()).resolve(strict=True)
    except (OSError, RuntimeError):
        return None
    if (
        not resolved.is_dir()
        or resolved.is_symlink()
        or resolved.parent != temp_root
        or not resolved.name.startswith(_TEMP_PREFIX)
    ):
        return None
    return resolved


def _default_temp_factory() -> Path:
    return Path(tempfile.mkdtemp(prefix=_TEMP_PREFIX))


def _default_temp_cleanup(path: Path) -> bool:
    verified = _verified_temp_directory(path)
    if verified is None:
        return False
    try:
        shutil.rmtree(verified)
    except OSError:
        return False
    return not verified.exists()


def _default_generation_runner(
    entry: Path, output_directory: Path, repository: Path
) -> GenerationOutcome:
    command = (
        str(entry),
        "app-server",
        "generate-json-schema",
        "--out",
        str(output_directory),
        "--experimental",
    )
    try:
        process = subprocess.Popen(
            command,
            cwd=repository,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except OSError:
        return GenerationOutcome("schema_generation_launch_failed", None)
    task_root_process_id = process.pid
    return_code = process.wait()
    if return_code != 0:
        return GenerationOutcome(
            "schema_generation_nonzero", return_code, task_root_process_id
        )
    return GenerationOutcome(
        "schema_generation_completed", return_code, task_root_process_id
    )


def _load_schema_documents(root: Path) -> _LoadedDocuments:
    verified = _verified_temp_directory(root)
    if verified is None:
        return _LoadedDocuments("indeterminate", 0, ("temporary_path_invalid",))
    documents: list[Any] = []
    total_bytes = 0
    try:
        entries = sorted(verified.rglob("*"), key=lambda item: item.as_posix())
    except OSError:
        return _LoadedDocuments("indeterminate", 0, ("schema_discovery_failed",))
    for entry in entries:
        try:
            if entry.is_symlink():
                return _LoadedDocuments(
                    "indeterminate", len(documents), ("generated_link_rejected",)
                )
            if entry.is_dir():
                continue
            if not entry.is_file() or entry.suffix.casefold() != ".json":
                return _LoadedDocuments(
                    "indeterminate",
                    len(documents),
                    ("generated_non_json_entry_rejected",),
                )
            if not entry.resolve(strict=True).is_relative_to(verified):
                return _LoadedDocuments(
                    "indeterminate", len(documents), ("generated_path_escape",)
                )
            size = entry.stat().st_size
            if size > _MAX_SCHEMA_DOCUMENT_BYTES:
                return _LoadedDocuments(
                    "indeterminate", len(documents), ("schema_document_too_large",)
                )
            total_bytes += size
            if total_bytes > _MAX_SCHEMA_TOTAL_BYTES:
                return _LoadedDocuments(
                    "indeterminate", len(documents), ("schema_bundle_too_large",)
                )
            if len(documents) >= _MAX_SCHEMA_DOCUMENTS:
                return _LoadedDocuments(
                    "indeterminate", len(documents), ("schema_document_limit_exceeded",)
                )
            data = entry.read_bytes()
            documents.append(json.loads(data.decode("utf-8-sig")))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            return _LoadedDocuments(
                "indeterminate", len(documents), ("schema_document_invalid",)
            )
    if not documents:
        return _LoadedDocuments(
            "indeterminate", 0, ("schema_document_not_found",)
        )
    return _LoadedDocuments("ready", len(documents), (), tuple(documents))


def _aggregate_diagnostics(
    documents: Sequence[Any], request: Mapping[str, Any]
) -> _AggregatedDiagnostic:
    diagnostics = [
        diagnose_thread_start_schema(document, request) for document in documents
    ]
    relevant = [
        item
        for item in diagnostics
        if item.reason_codes != ("thread_start_method_not_found",)
    ]
    if not relevant:
        return _AggregatedDiagnostic(
            "indeterminate", (_finding("thread_start_method_not_found"),), ()
        )
    statuses = {item.status for item in relevant}
    if len(statuses) != 1:
        return _AggregatedDiagnostic(
            "indeterminate", (_finding("schema_contracts_conflict"),), ()
        )
    status = statuses.pop()
    if len(relevant) > 1:
        signatures = {
            (item.status, item.findings, item.checked_fields) for item in relevant
        }
        if len(signatures) != 1:
            return _AggregatedDiagnostic(
                "indeterminate", (_finding("schema_contracts_ambiguous"),), ()
            )
    representative: AppServerSchemaDiagnostic = relevant[0]
    findings = _ordered_findings(
        [_finding(item.code, item.field) for item in representative.findings]
    )
    return _AggregatedDiagnostic(status, findings, representative.checked_fields)


def _result(
    *,
    status: str = "indeterminate",
    stage: str,
    findings: Sequence[InstalledSchemaValidationFinding],
    document_count: int = 0,
    checked_fields: tuple[str, ...] = (),
    boundary: ObservedProcessBoundary | None = None,
    help_queries: int = 0,
    generation_attempts: int = 0,
    cleanup_verified: bool = False,
    host_state_unchanged: bool = False,
) -> InstalledSchemaValidationResult:
    return InstalledSchemaValidationResult(
        status=status,
        stage=stage,
        findings=_ordered_findings(findings),
        document_count=document_count,
        checked_fields=checked_fields,
        preflight_counts=boundary.preflight_counts if boundary else (),
        postflight_counts=boundary.postflight_counts if boundary else (),
        ambient_counts=boundary.ambient_counts if boundary else (),
        remaining_task_owned_counts=(
            boundary.remaining_task_owned_counts if boundary else ()
        ),
        help_queries=help_queries,
        generation_attempts=generation_attempts,
        cleanup_verified=cleanup_verified,
        host_state_unchanged=host_state_unchanged,
    )


def run_installed_schema_validation(
    repository: Path,
    *,
    command_entries: CommandEntries | None = None,
    help_probe: HelpProbe | None = None,
    process_observer: ProcessObserver | None = None,
    generation_runner: GenerationRunner | None = None,
    state_probe: StateProbe | None = None,
    temp_factory: TempFactory | None = None,
    temp_cleanup: TempCleanup | None = None,
    request: Mapping[str, Any] | None = None,
) -> InstalledSchemaValidationResult:
    """Run one bounded attempt; callers must not automatically retry it."""

    entries_provider = command_entries or _discover_codex_entries
    help_provider = help_probe or _default_help_probe
    observe = process_observer or observe_windows_processes
    generate = generation_runner or _default_generation_runner
    probe_state = state_probe or _default_state_probe
    create_temp = temp_factory or _default_temp_factory
    cleanup_temp = temp_cleanup or _default_temp_cleanup
    normalized_request = dict(request or _NORMALIZED_REQUEST)

    before_state = probe_state(repository)
    if before_state.status != "ready":
        return _result(
            stage="host_state_preflight",
            findings=[_finding(code) for code in before_state.findings],
        )

    def stop_before_temporary_directory(
        *,
        stage: str,
        findings: Sequence[InstalledSchemaValidationFinding],
        boundary: ObservedProcessBoundary | None = None,
        help_queries: int = 0,
    ) -> InstalledSchemaValidationResult:
        retained_findings = list(findings)
        try:
            after_state = probe_state(repository)
            state_unchanged = _host_state_matches(before_state, after_state)
        except (OSError, subprocess.SubprocessError, TypeError, ValueError):
            state_unchanged = False
        if not state_unchanged:
            retained_findings.append(_finding("host_state_changed_or_unavailable"))
        return _result(
            stage=stage,
            findings=retained_findings,
            boundary=boundary,
            help_queries=help_queries,
            cleanup_verified=True,
            host_state_unchanged=state_unchanged,
        )

    selection = _select_codex_entry(entries_provider())
    if selection.status != "ready" or selection._entry is None:
        return stop_before_temporary_directory(
            stage="command_discovery", findings=[_finding(selection.code)]
        )
    entry = selection._entry

    help_error = help_provider(entry)
    if help_error is not None:
        return stop_before_temporary_directory(
            stage="command_help",
            findings=[_finding(help_error)],
            help_queries=1,
        )

    preflight = observe()
    baseline = assess_ambient_process_baseline(preflight)
    if baseline.status != "ready":
        return stop_before_temporary_directory(
            stage="process_preflight",
            findings=[_finding(code) for code in baseline.reason_codes],
            boundary=baseline,
            help_queries=1,
        )

    task_directory: Path | None = None
    generation: GenerationOutcome | None = None
    boundary: ObservedProcessBoundary = baseline
    documents = _LoadedDocuments("indeterminate", 0, ())
    diagnostic = _AggregatedDiagnostic("indeterminate", (), ())
    primary_stage = "temporary_directory"
    primary_findings: list[InstalledSchemaValidationFinding] = []
    cleanup_verified = False

    try:
        task_directory = create_temp()
        verified_directory = _verified_temp_directory(task_directory)
        if verified_directory is None:
            primary_findings.append(_finding("temporary_path_invalid"))
        else:
            generation = generate(entry, verified_directory, repository)
            primary_stage = "schema_generation"
            if generation.code != "schema_generation_completed":
                primary_findings.append(_finding(generation.code))

            postflight = observe()
            root_process_id = generation._task_root_process_id
            boundary = reconcile_windows_processes(
                preflight,
                postflight,
                task_root_process_id=root_process_id or 0,
            )
            if boundary.status != "ready":
                primary_stage = "process_postflight"
                primary_findings.extend(
                    _finding(code) for code in boundary.reason_codes
                )

            if not primary_findings:
                documents = _load_schema_documents(verified_directory)
                primary_stage = "schema_discovery"
                if documents.status != "ready":
                    primary_findings.extend(
                        _finding(code) for code in documents.findings
                    )
                else:
                    diagnostic = _aggregate_diagnostics(
                        documents._documents, normalized_request
                    )
                    primary_stage = "schema_diagnostic"
    except (OSError, subprocess.SubprocessError, TypeError, ValueError):
        primary_findings.append(_finding("validation_driver_failed"))
        primary_stage = "driver"
    finally:
        if task_directory is not None:
            cleanup_verified = cleanup_temp(task_directory)

    if not cleanup_verified:
        primary_findings.append(_finding("temporary_cleanup_unverified"))
        primary_stage = "cleanup"

    after_state = probe_state(repository)
    host_state_unchanged = _host_state_matches(before_state, after_state)
    if not host_state_unchanged:
        primary_findings.append(_finding("host_state_changed_or_unavailable"))
        primary_stage = "host_state_postflight"

    attempts = 1 if generation is not None else 0
    if primary_findings:
        return _result(
            stage=primary_stage,
            findings=primary_findings,
            document_count=documents.count,
            checked_fields=diagnostic.checked_fields,
            boundary=boundary,
            help_queries=1,
            generation_attempts=attempts,
            cleanup_verified=cleanup_verified,
            host_state_unchanged=host_state_unchanged,
        )
    return _result(
        status=diagnostic.status,
        stage="completed",
        findings=diagnostic.findings or (_finding("validation_completed"),),
        document_count=documents.count,
        checked_fields=diagnostic.checked_fields,
        boundary=boundary,
        help_queries=1,
        generation_attempts=attempts,
        cleanup_verified=cleanup_verified,
        host_state_unchanged=host_state_unchanged,
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run one internal no-model installed-schema validation."
    )
    parser.add_argument("--repository", type=Path, default=Path.cwd())
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        result = run_installed_schema_validation(args.repository)
    except Exception:  # pragma: no cover - final privacy boundary
        result = _result(
            stage="driver", findings=[_finding("validation_driver_failed")]
        )
    print(json.dumps(result.as_dict(), sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
