"""Fixed, privacy-bounded controller for one real artifact replay.

The external process receives configuration only as strict JSON stdin.  Replay
source is constructed internally and handed directly to the existing Harness;
it is never dynamic parent ``python -c`` program text.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import tomllib
import zipfile
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any, BinaryIO, TextIO

from scripts.artifact_invocation_caller.caller import (
    ArtifactInvocationCallerRequest,
    run_ready_artifact_replay,
)
from scripts.artifact_invocation_readiness.readiness import (
    ENCODING_ALGORITHM,
    InvocationTransportRequest,
    denied_authority_request,
)
from scripts.artifact_replay_driver.driver import ArtifactEvidence
from scripts.artifact_replay_harness.harness import (
    ArtifactReplayHarnessError,
    ArtifactReplayHarnessRequest,
    ArtifactReplayHarnessResult,
    run_bounded_artifact_replay,
)
from scripts.distribution_input_manifest.manifest import (
    canonical_content_digest,
    canonical_path_digest,
    check_manifest,
    derive_distribution_inputs,
)


REQUEST_CONTRACT = "agentgov.artifact-replay-controller-request"
RESULT_CONTRACT = "agentgov.artifact-replay-controller-result"
SCHEMA_VERSION = "1.0"
MAX_REQUEST_BYTES = 16_384
MANIFEST_RELATIVE = "governance/distribution-input-manifest.json"
EXPECTED_PATH_COUNT = 186
EXPECTED_PATH_DIGEST = (
    "sha256:cfea3a3632bd75d1f4db51168d257c465987d3fe620fda2449abcd86f42fcd03"
)
EXPECTED_CONTENT_DIGEST = (
    "sha256:b00be073afa541c3130cc620c84bd2bba2afa7b48ec4e70a4ff74998bc7fb8d9"
)
IDENTITY_KEYS = (
    "source_length",
    "source_sha256",
    "encoded_length",
    "encoded_sha256",
)
_SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_VERSION_RE = re.compile(r"^[0-9]+(?:\.[0-9]+)+(?:[A-Za-z0-9._+-]{0,24})$")
_SHORT_ROOT_RE = re.compile(r"^agv-(?:[0-9a-f]{8}|[0-9a-f]{16})$")
_REQUEST_KEYS = {
    "contract",
    "schema_version",
    "python_executable",
    "backend_wheel",
    "backend_wheel_sha256",
    "expected_python_version",
    "expected_pip_version",
    "expected_setuptools_version",
    "evidence_relative_path",
    "timeout_seconds",
}
_MANIFEST_FACT_KEYS = {
    "manifest_path_count",
    "manifest_path_digest",
    "manifest_content_digest",
}
_RUNTIME_KEYS = (
    _REQUEST_KEYS - {"contract", "schema_version", "timeout_seconds"}
) | _MANIFEST_FACT_KEYS


def _authority_boundary() -> Mapping[str, bool]:
    return {
        "authorizes_build": False,
        "retries_harness": False,
        "installs_dependencies": False,
        "uses_network": False,
        "starts_external_agent": False,
        "uses_model": False,
        "authorizes_git_operations": False,
        "authorizes_publication": False,
        "authorizes_release": False,
        "authorizes_deployment": False,
    }


@dataclass(frozen=True)
class ArtifactReplayControllerRequest:
    python_executable: Path = field(repr=False)
    backend_wheel: Path = field(repr=False)
    backend_wheel_sha256: str
    expected_python_version: str
    expected_pip_version: str
    expected_setuptools_version: str
    evidence_relative_path: str
    timeout_seconds: float = field(default=60.0, repr=False)


@dataclass(frozen=True)
class ArtifactReplayControllerResult:
    source_length: int
    source_sha256: str
    encoded_length: int
    encoded_sha256: str

    def normalized_report(self) -> Mapping[str, Any]:
        return {
            "contract": RESULT_CONTRACT,
            "schema_version": SCHEMA_VERSION,
            "status": "PASS",
            "transport": {
                "source_length": self.source_length,
                "source_sha256": self.source_sha256,
                "encoded_length": self.encoded_length,
                "encoded_sha256": self.encoded_sha256,
            },
            "controller_attempts": 1,
            "dry_attempts": 1,
            "actual_attempts": 1,
            "request_transport": "json_stdin",
            "reads_stdin": True,
            "depends_on_tty": False,
            "authority_boundary": _authority_boundary(),
        }


@dataclass(frozen=True)
class _ManifestFacts:
    path_count: int
    path_digest: str
    content_digest: str


class ArtifactReplayControllerError(RuntimeError):
    def __init__(
        self,
        reason_code: str,
        *,
        phase: str,
        controller_attempts: int,
        dry_attempts: int,
        actual_attempts: int,
    ) -> None:
        super().__init__(reason_code)
        self.reason_code = reason_code
        self.phase = phase
        self.controller_attempts = controller_attempts
        self.dry_attempts = dry_attempts
        self.actual_attempts = actual_attempts

    def normalized_report(self) -> Mapping[str, Any]:
        return {
            "contract": RESULT_CONTRACT,
            "schema_version": SCHEMA_VERSION,
            "status": "STOPPED_AT_FIRST_DEVIATION",
            "phase": self.phase,
            "reason_code": self.reason_code,
            "controller_attempts": self.controller_attempts,
            "dry_attempts": self.dry_attempts,
            "actual_attempts": self.actual_attempts,
            "request_transport": "json_stdin",
            "reads_stdin": True,
            "depends_on_tty": False,
            "authority_boundary": _authority_boundary(),
        }


def _stop(
    reason_code: str,
    *,
    phase: str,
    controller_attempts: int = 0,
    dry_attempts: int = 0,
    actual_attempts: int = 0,
) -> ArtifactReplayControllerError:
    return ArtifactReplayControllerError(
        reason_code,
        phase=phase,
        controller_attempts=controller_attempts,
        dry_attempts=dry_attempts,
        actual_attempts=actual_attempts,
    )


def _relative_path(value: object) -> str:
    if not isinstance(value, str) or not value or value != value.strip() or "\\" in value:
        raise _stop("request_invalid", phase="request")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise _stop("request_invalid", phase="request")
    return value


def _request_from_mapping(value: object) -> ArtifactReplayControllerRequest:
    if not isinstance(value, dict) or set(value) != _REQUEST_KEYS:
        raise _stop("request_invalid", phase="request")
    if value.get("contract") != REQUEST_CONTRACT or value.get("schema_version") != SCHEMA_VERSION:
        raise _stop("request_invalid", phase="request")
    for key in (
        "python_executable",
        "backend_wheel",
        "backend_wheel_sha256",
        "expected_python_version",
        "expected_pip_version",
        "expected_setuptools_version",
    ):
        if not isinstance(value.get(key), str) or not value[key]:
            raise _stop("request_invalid", phase="request")
    if not _SHA256_RE.fullmatch(value["backend_wheel_sha256"]):
        raise _stop("request_invalid", phase="request")
    for key in (
        "expected_python_version",
        "expected_pip_version",
        "expected_setuptools_version",
    ):
        if not _VERSION_RE.fullmatch(value[key]):
            raise _stop("request_invalid", phase="request")
    timeout = value.get("timeout_seconds")
    if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or not 0 < timeout <= 60:
        raise _stop("request_invalid", phase="request")
    return ArtifactReplayControllerRequest(
        python_executable=Path(value["python_executable"]),
        backend_wheel=Path(value["backend_wheel"]),
        backend_wheel_sha256=value["backend_wheel_sha256"],
        expected_python_version=value["expected_python_version"],
        expected_pip_version=value["expected_pip_version"],
        expected_setuptools_version=value["expected_setuptools_version"],
        evidence_relative_path=_relative_path(value["evidence_relative_path"]),
        timeout_seconds=float(timeout),
    )


def _runtime_mapping(
    request: ArtifactReplayControllerRequest, manifest: _ManifestFacts
) -> Mapping[str, Any]:
    return {
        "python_executable": str(request.python_executable),
        "backend_wheel": str(request.backend_wheel),
        "backend_wheel_sha256": request.backend_wheel_sha256,
        "expected_python_version": request.expected_python_version,
        "expected_pip_version": request.expected_pip_version,
        "expected_setuptools_version": request.expected_setuptools_version,
        "evidence_relative_path": request.evidence_relative_path,
        "manifest_path_count": manifest.path_count,
        "manifest_path_digest": manifest.path_digest,
        "manifest_content_digest": manifest.content_digest,
    }


def _replay_source(
    request: ArtifactReplayControllerRequest, manifest: _ManifestFacts
) -> str:
    configuration = json.dumps(
        _runtime_mapping(request, manifest),
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    )
    return (
        "from scripts.artifact_replay_controller.controller import execute_real_replay_source\n"
        f"_CONTROLLER_CONFIG = {configuration}\n"
        "def artifact_replay_main():\n"
        "    execute_real_replay_source(\n"
        "        mode=ARTIFACT_REPLAY_MODE,\n"
        "        identity=ARTIFACT_REPLAY_SOURCE_IDENTITY,\n"
        "        configuration=_CONTROLLER_CONFIG,\n"
        "    )\n"
    )


HarnessRunner = Callable[[ArtifactReplayHarnessRequest], ArtifactReplayHarnessResult]
ManifestChecker = Callable[[Path, Path], Mapping[str, Any]]


def _controller_manifest_preflight(
    repository: Path, manifest_checker: ManifestChecker
) -> _ManifestFacts:
    root = repository.resolve(strict=True)
    result = manifest_checker(root, root / MANIFEST_RELATIVE)
    if not isinstance(result, Mapping):
        raise RuntimeError("manifest_preflight_failed")
    facts = _ManifestFacts(
        path_count=result.get("path_count"),
        path_digest=result.get("path_digest"),
        content_digest=result.get("content_digest"),
    )
    if (
        result.get("status") != "PASS"
        or isinstance(facts.path_count, bool)
        or facts.path_count != EXPECTED_PATH_COUNT
        or facts.path_digest != EXPECTED_PATH_DIGEST
        or facts.content_digest != EXPECTED_CONTENT_DIGEST
    ):
        raise RuntimeError("manifest_preflight_failed")
    return facts


def run_artifact_replay_controller(
    request: ArtifactReplayControllerRequest,
    *,
    repository: Path | None = None,
    harness_runner: HarnessRunner = run_bounded_artifact_replay,
    manifest_checker: ManifestChecker = check_manifest,
) -> ArtifactReplayControllerResult:
    if not isinstance(request, ArtifactReplayControllerRequest):
        raise _stop("request_invalid", phase="request")
    root = Path.cwd() if repository is None else repository
    try:
        manifest = _controller_manifest_preflight(root, manifest_checker)
    except Exception:
        raise _stop(
            "manifest_preflight_failed",
            phase="preflight",
            controller_attempts=1,
        ) from None
    source = _replay_source(request, manifest)
    harness_request = ArtifactReplayHarnessRequest(
        source=source,
        repository=root,
        python_executable=request.python_executable,
        timeout_seconds=request.timeout_seconds,
    )
    try:
        result = harness_runner(harness_request)
    except ArtifactReplayHarnessError as error:
        raise _stop(
            "harness_" + error.reason_code,
            phase=error.phase,
            controller_attempts=1,
            dry_attempts=error.dry_attempts,
            actual_attempts=error.actual_attempts,
        ) from None
    except Exception:
        raise _stop(
            "harness_exception", phase="harness", controller_attempts=1
        ) from None
    if not isinstance(result, ArtifactReplayHarnessResult):
        raise _stop(
            "harness_result_invalid", phase="harness", controller_attempts=1
        )
    return ArtifactReplayControllerResult(
        source_length=result.source_length,
        source_sha256=result.source_sha256,
        encoded_length=result.encoded_length,
        encoded_sha256=result.encoded_sha256,
    )


def _sha256_bytes(payload: bytes) -> str:
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _regular_non_link(path: Path) -> Path:
    file_stat = path.lstat()
    if stat.S_ISLNK(file_stat.st_mode) or not stat.S_ISREG(file_stat.st_mode):
        raise RuntimeError("regular_file_required")
    resolved = path.resolve(strict=True)
    resolved_stat = resolved.lstat()
    if stat.S_ISLNK(resolved_stat.st_mode) or not stat.S_ISREG(resolved_stat.st_mode):
        raise RuntimeError("regular_file_required")
    return resolved


def _short_root_count() -> int:
    temporary_root = Path(tempfile.gettempdir())
    root_stat = temporary_root.lstat()
    if stat.S_ISLNK(root_stat.st_mode) or not stat.S_ISDIR(root_stat.st_mode):
        raise RuntimeError("temporary_root_invalid")
    return sum(
        1
        for child in temporary_root.iterdir()
        if _SHORT_ROOT_RE.fullmatch(child.name) and (child.exists() or child.is_symlink())
    )


@dataclass(frozen=True)
class _RuntimeConfig:
    python_executable: Path
    backend_wheel: Path
    backend_wheel_sha256: str
    expected_python_version: str
    expected_pip_version: str
    expected_setuptools_version: str
    evidence_relative_path: str
    manifest_path_count: int
    manifest_path_digest: str
    manifest_content_digest: str


def _runtime_config(value: object) -> _RuntimeConfig:
    if not isinstance(value, dict) or set(value) != _RUNTIME_KEYS:
        raise RuntimeError("runtime_config_invalid")
    config = _RuntimeConfig(
        python_executable=Path(value["python_executable"]),
        backend_wheel=Path(value["backend_wheel"]),
        backend_wheel_sha256=value["backend_wheel_sha256"],
        expected_python_version=value["expected_python_version"],
        expected_pip_version=value["expected_pip_version"],
        expected_setuptools_version=value["expected_setuptools_version"],
        evidence_relative_path=_relative_path(value["evidence_relative_path"]),
        manifest_path_count=value["manifest_path_count"],
        manifest_path_digest=value["manifest_path_digest"],
        manifest_content_digest=value["manifest_content_digest"],
    )
    if (
        isinstance(config.manifest_path_count, bool)
        or config.manifest_path_count != EXPECTED_PATH_COUNT
        or config.manifest_path_digest != EXPECTED_PATH_DIGEST
        or config.manifest_content_digest != EXPECTED_CONTENT_DIGEST
    ):
        raise RuntimeError("runtime_manifest_facts_invalid")
    return config


def _validated_identity(value: object) -> Mapping[str, Any]:
    if not isinstance(value, Mapping) or tuple(value.keys()) != IDENTITY_KEYS:
        raise RuntimeError("identity_context_invalid")
    if (
        not isinstance(value["source_length"], int)
        or isinstance(value["source_length"], bool)
        or value["source_length"] <= 0
        or not _SHA256_RE.fullmatch(value["source_sha256"])
        or not isinstance(value["encoded_length"], int)
        or isinstance(value["encoded_length"], bool)
        or value["encoded_length"] <= 0
        or value["encoded_length"] % 4
        or not _SHA256_RE.fullmatch(value["encoded_sha256"])
    ):
        raise RuntimeError("identity_context_invalid")
    return value


def _filesystem_manifest_preflight(
    repository: Path, config: _RuntimeConfig
) -> tuple[str, ...]:
    manifest_path = repository / MANIFEST_RELATIVE
    document = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(document, dict) or not isinstance(document.get("paths"), list):
        raise RuntimeError("manifest_filesystem_revalidation_failed")
    declared = document["paths"]
    derived = derive_distribution_inputs(repository)
    if (
        declared != derived
        or len(derived) != config.manifest_path_count
        or document.get("path_digest") != config.manifest_path_digest
        or document.get("content_digest") != config.manifest_content_digest
        or canonical_path_digest(derived) != config.manifest_path_digest
        or canonical_content_digest(repository, derived)
        != config.manifest_content_digest
    ):
        raise RuntimeError("manifest_filesystem_revalidation_failed")
    return tuple(derived)


def _build_environment() -> Mapping[str, str]:
    environment = {
        "PYTHONNOUSERSITE": "1",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PIP_DISABLE_PIP_VERSION_CHECK": "1",
        "PIP_NO_INPUT": "1",
        "PIP_NO_INDEX": "1",
        "NO_COLOR": "1",
    }
    for key in ("SYSTEMROOT", "WINDIR", "COMSPEC", "PATHEXT", "TEMP", "TMP"):
        if os.environ.get(key):
            environment[key] = os.environ[key]
    return environment


def _inventory_digest(names: Sequence[str]) -> str:
    return _sha256_bytes("".join(name + "\n" for name in sorted(names)).encode("utf-8"))


def _managed_members(stage: Path, paths: Sequence[str], wheel_base: str) -> tuple[dict[str, Path], int, int]:
    managed: dict[str, Path] = {}
    package_count = 0
    for relative in paths:
        if relative.startswith("src/"):
            managed[relative[4:]] = stage.joinpath(*PurePosixPath(relative).parts)
            package_count += 1
    configuration = tomllib.loads((stage / "pyproject.toml").read_text(encoding="utf-8"))
    data_count = 0
    for destination, patterns in configuration["tool"]["setuptools"]["data-files"].items():
        for pattern in patterns:
            matches = sorted(path for path in stage.glob(pattern) if path.is_file() and not path.is_symlink())
            if not matches:
                raise RuntimeError("data_pattern_empty")
            for path in matches:
                if path.relative_to(stage).as_posix() not in paths:
                    raise RuntimeError("data_source_not_manifested")
                member = wheel_base + ".data/data/" + destination + "/" + path.name
                if member in managed:
                    raise RuntimeError("managed_member_duplicate")
                managed[member] = path
                data_count += 1
    if package_count != 76 or data_count != 107 or len(managed) != 183:
        raise RuntimeError("managed_member_count_invalid")
    return managed, package_count, data_count


def _artifact_action(
    root: Any,
    *,
    repository: Path,
    config: _RuntimeConfig,
    paths: Sequence[str],
) -> ArtifactEvidence:
    stage = root.path / "stage"
    wheelhouse = root.path / "wheelhouse"
    stage.mkdir()
    wheelhouse.mkdir()
    copied = 0
    for relative in paths:
        parts = PurePosixPath(relative).parts
        source = _regular_non_link(repository.joinpath(*parts))
        target = stage.joinpath(*parts)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target, follow_symlinks=False)
        if source.read_bytes() != _regular_non_link(target).read_bytes():
            raise RuntimeError("staged_byte_mismatch")
        copied += 1
    if copied != EXPECTED_PATH_COUNT or canonical_content_digest(stage, list(paths)) != EXPECTED_CONTENT_DIGEST:
        raise RuntimeError("staged_manifest_mismatch")
    completed = subprocess.run(
        [
            str(config.python_executable), "-I", "-m", "pip", "wheel", ".",
            "--no-index", "--no-deps", "--no-build-isolation", "--no-cache-dir",
            "--wheel-dir", str(wheelhouse),
        ],
        cwd=stage,
        env=dict(_build_environment()),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=45,
        check=False,
    )
    if completed.returncode or len(completed.stdout) > 1024 * 1024 or len(completed.stderr) > 1024 * 1024:
        raise RuntimeError("offline_build_failed")
    wheels = sorted(wheelhouse.glob("*.whl"))
    if len(wheels) != 1:
        raise RuntimeError("wheel_count_invalid")
    wheel = _regular_non_link(wheels[0])
    suffix = "-py3-none-any.whl"
    if not wheel.name.endswith(suffix):
        raise RuntimeError("wheel_filename_invalid")
    wheel_base = wheel.name[:-len(suffix)]
    managed, package_count, data_count = _managed_members(stage, paths, wheel_base)
    with zipfile.ZipFile(wheel, "r") as archive:
        infos = [item for item in archive.infolist() if not item.is_dir()]
        names = [item.filename for item in infos]
        if len(names) != len(set(names)):
            raise RuntimeError("wheel_member_duplicate")
        for info in infos:
            parts = PurePosixPath(info.filename).parts
            mode = (info.external_attr >> 16) & 0xFFFF
            if (
                not info.filename
                or "\\" in info.filename
                or PurePosixPath(info.filename).is_absolute()
                or any(part in {"", ".", ".."} for part in parts)
                or (mode and stat.S_ISLNK(mode))
            ):
                raise RuntimeError("wheel_member_invalid")
        regular_names = set(names)
        if not set(managed).issubset(regular_names):
            raise RuntimeError("managed_member_missing")
        for member, source in managed.items():
            if archive.read(member) != source.read_bytes():
                raise RuntimeError("managed_payload_mismatch")
        generated = sorted(regular_names - set(managed))
        if (
            len(regular_names) != 189
            or len(generated) != 6
            or any(not name.startswith(wheel_base + ".dist-info/") for name in generated)
        ):
            raise RuntimeError("unmanaged_member_invalid")
    evidence = f"""# Interview-ready artifact replay close loop v1

Date: 2026-08-26

## Outcome before gated cleanup

INTERVIEW_READY_IDENTITY_BOUND_ARTIFACT_PASS_EVIDENCE_DURABLE_CLEANUP_PENDING

The fixed repository controller called the bounded Harness directly. One dry
attempt passed before this sole actual path. The caller constructed readiness
metadata from the exact immutable Harness source identity and invoked this
single offline action only after one fresh readiness check passed. This record
is returned before the unchanged driver performs its exclusive durable write,
receipt, and evidence-gated cleanup, so it makes no post-cleanup claim.

## Interview architecture chain

Fixed controller -> bounded Harness -> immutable identity bridge -> readiness
gate -> caller -> driver -> one offline action -> durable evidence receipt ->
evidence-gated cleanup.

## Observed facts

| Observation | Result |
| --- | --- |
| Manifest inputs | {EXPECTED_PATH_COUNT} |
| Manifest path identity | {EXPECTED_PATH_DIGEST} |
| Manifest content identity | {EXPECTED_CONTENT_DIGEST} |
| Backend | Python {config.expected_python_version} / pip {config.expected_pip_version} / setuptools {config.expected_setuptools_version} |
| Backend wheel identity | {config.backend_wheel_sha256} |
| Copied inputs / byte matches | {copied} / {copied} |
| Package payloads / data payloads | {package_count} / {data_count} |
| Build return code / wheels emitted | {completed.returncode} / {len(wheels)} |
| Wheel SHA-256 | {_sha256_bytes(wheel.read_bytes())} |
| Wheel regular members | {len(regular_names)} |
| Member-inventory SHA-256 | {_inventory_digest(tuple(regular_names))} |
| Managed byte matches / mismatches | {len(managed)} / 0 |
| Generated metadata members | {len(generated)} |
| Generated-member inventory SHA-256 | {_inventory_digest(tuple(generated))} |
| Unexpected unmanaged members | 0 |

## Boundaries and remaining unknowns

Controller attempts, Harness dry attempts, Harness actual attempts, callers,
readiness probes, drivers, actions, and builds are one each. Retry, repair,
alternate backend, dependency installation, network, external Agent, model,
Git, publication, release, and deployment are zero. No source text, host path,
raw output, traceback, environment, credential, process detail, or ephemeral
readiness receipt is retained.

This one local result does not prove cross-platform, adversarial, recovery,
future-toolchain, repeated-reliability, adoption, interview, time-saving,
causal-benefit, or return-on-investment outcomes.
"""
    return ArtifactEvidence(text=evidence)


def execute_real_replay_source(
    *, mode: str, identity: object, configuration: object
) -> None:
    config = _runtime_config(configuration)
    context = _validated_identity(identity)
    repository = Path.cwd().resolve(strict=True)
    paths = _filesystem_manifest_preflight(repository, config)
    launcher = _regular_non_link(config.python_executable)
    wheel = _regular_non_link(config.backend_wheel)
    if wheel.suffix.lower() != ".whl" or _sha256_bytes(wheel.read_bytes()) != config.backend_wheel_sha256:
        raise RuntimeError("backend_wheel_invalid")
    evidence = repository.joinpath(*PurePosixPath(config.evidence_relative_path).parts)
    if evidence.exists() or evidence.is_symlink() or _short_root_count():
        raise RuntimeError("execution_preflight_failed")
    if mode == "dry":
        return
    if mode != "actual":
        raise RuntimeError("mode_invalid")
    projected = tuple(
        ["stage/" + relative for relative in paths]
        + [
            "stage/build/lib/agentgov/reference_alignment_adapter.py",
            "stage/src/agent_governance_starter.egg-info/SOURCES.txt",
            "wheelhouse/agent_governance_starter-0.3.0rc1-py3-none-any.whl",
        ]
    )
    transport = InvocationTransportRequest(
        encoding_algorithm=ENCODING_ALGORITHM,
        encoded_length=context["encoded_length"],
        encoded_sha256=context["encoded_sha256"],
        launcher_path=launcher,
        backend_wheel_path=wheel,
        backend_wheel_sha256=config.backend_wheel_sha256,
        expected_python_version=config.expected_python_version,
        expected_pip_version=config.expected_pip_version,
        expected_setuptools_version=config.expected_setuptools_version,
        authority_request=denied_authority_request(),
    )
    request = ArtifactInvocationCallerRequest(
        transport=transport,
        repository=repository,
        manifest_relative_path=MANIFEST_RELATIVE,
        manifest_relative_paths=paths,
        manifest_path_count=config.manifest_path_count,
        manifest_path_digest=config.manifest_path_digest,
        manifest_content_digest=config.manifest_content_digest,
        projected_relative_paths=projected,
        evidence_relative_path=config.evidence_relative_path,
        action=lambda root: _artifact_action(
            root, repository=repository, config=config, paths=paths
        ),
    )
    report = run_ready_artifact_replay(request).normalized_report()
    if (
        report.get("status") != "PASS"
        or report.get("readiness_attempts") != 1
        or report.get("driver_attempts") != 1
        or report.get("readiness", {}).get("probe_attempts") != 1
        or report.get("driver", {}).get("action_attempts") != 1
        or report.get("driver", {}).get("cleanup_removed") is not True
        or report.get("driver", {}).get("root_absent") is not True
    ):
        raise RuntimeError("combined_result_invalid")


def _read_request(stream: BinaryIO) -> ArtifactReplayControllerRequest:
    payload = stream.read(MAX_REQUEST_BYTES + 1)
    if not isinstance(payload, bytes) or not payload or len(payload) > MAX_REQUEST_BYTES:
        raise _stop("request_invalid", phase="request")
    try:
        value = json.loads(payload.decode("utf-8", errors="strict"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise _stop("request_invalid", phase="request") from None
    return _request_from_mapping(value)


def main(
    stdin: BinaryIO | None = None,
    stdout: TextIO | None = None,
    *,
    runner: Callable[[ArtifactReplayControllerRequest], ArtifactReplayControllerResult] = run_artifact_replay_controller,
) -> int:
    input_stream = sys.stdin.buffer if stdin is None else stdin
    output_stream = sys.stdout if stdout is None else stdout
    try:
        request = _read_request(input_stream)
        result = runner(request)
        if not isinstance(result, ArtifactReplayControllerResult):
            raise _stop("controller_result_invalid", phase="controller", controller_attempts=1)
        report = result.normalized_report()
        code = 0
    except ArtifactReplayControllerError as error:
        report = error.normalized_report()
        code = 1
    except Exception:
        report = _stop("controller_exception", phase="controller", controller_attempts=1).normalized_report()
        code = 1
    output_stream.write(json.dumps(report, sort_keys=True, separators=(",", ":")) + "\n")
    output_stream.flush()
    return code
