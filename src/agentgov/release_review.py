"""Create-new-only release review evidence without granting release authority."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import venv
import zipfile
from dataclasses import dataclass
from email.parser import Parser
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Callable, Mapping

from agentgov import __version__
from agentgov.evidence_freshness import (
    EvidenceFreshnessResult,
    check_evidence_freshness,
)
from agentgov.release_metadata import load_release_manifest, validate_release_manifest


RELEASE_REVIEW_CONTRACT_VERSION = "1.0"
FRESHNESS_PILOT_CONTRACT = "agentgov.release-review.evidence-freshness-pilot"
FRESHNESS_PILOT_SCHEMA_VERSION = "1.0"


class ReleaseReviewError(Exception):
    """Raised when trustworthy release review evidence cannot be collected."""


class ReleaseReviewConflictError(ReleaseReviewError):
    """Raised when review output would overwrite an existing path."""


@dataclass(frozen=True)
class CommandEvidence:
    exit_code: int
    stdout: str
    stderr: str

    def transcript(self) -> str:
        lines = [f"EXIT {self.exit_code}"]
        if self.stdout:
            lines.extend(["", "STDOUT", self.stdout.rstrip()])
        if self.stderr:
            lines.extend(["", "STDERR", self.stderr.rstrip()])
        return "\n".join(lines) + "\n"


@dataclass(frozen=True)
class ReleaseReviewEvidence:
    source_tests: CommandEvidence
    installed_version: CommandEvidence
    manifest_check: CommandEvidence
    consumer_check: CommandEvidence
    consumer_status: CommandEvidence
    upgrade_plan: CommandEvidence


@dataclass(frozen=True)
class ConsumerGovernanceSummary:
    adoption: str
    pass_count: int
    warn_count: int
    fail_count: int
    advisory_count: int


@dataclass(frozen=True)
class ReleaseReviewResult:
    output: Path
    state: str
    gates: tuple[Mapping[str, str], ...]
    freshness: Mapping[str, object] | None = None

    @property
    def blocked(self) -> bool:
        return self.state == "blocked"


EvidenceCollector = Callable[[Path, Path, Path, Path], ReleaseReviewEvidence]


def _regular_file(path: Path, label: str) -> Path:
    if path.is_symlink() or not path.is_file():
        raise ReleaseReviewError(f"{label} must be a regular file: {path}")
    return path.resolve()


def _directory(path: Path, label: str) -> Path:
    if path.is_symlink() or not path.is_dir():
        raise ReleaseReviewError(f"{label} must be a directory: {path}")
    return path.resolve()


def _source_relative_file(
    source: Path,
    path: Path,
    label: str,
) -> tuple[Path, str]:
    candidate = path if path.is_absolute() else source / path
    resolved = _regular_file(candidate, label)
    try:
        reference = resolved.relative_to(source)
    except ValueError as exc:
        raise ReleaseReviewError(f"{label} must stay inside the source repository") from exc
    return resolved, reference.as_posix()


def _freshness_pilot_document(
    *,
    record_ref: str,
    result: EvidenceFreshnessResult,
) -> dict[str, object]:
    return {
        "contract": FRESHNESS_PILOT_CONTRACT,
        "schema_version": FRESHNESS_PILOT_SCHEMA_VERSION,
        "mode": "advisory_non_blocking",
        "record_ref": record_ref,
        "result": {
            "evidence_id": result.evidence_id,
            "as_of": result.as_of,
            "status": result.status.value,
            "reason_codes": list(result.reason_codes),
            "messages": list(result.messages),
        },
        "effect": {
            "release_review_state_changed": False,
            "release_review_exit_changed": False,
        },
        "authority_boundary": {
            "record_modified": False,
            "automatic_event_discovery": False,
            "observed_events_modified": False,
            "release_authorized": False,
        },
    }


def _wheel_metadata_version(wheel: Path) -> str:
    try:
        with zipfile.ZipFile(wheel) as archive:
            metadata_names = sorted(
                name for name in archive.namelist() if name.endswith(".dist-info/METADATA")
            )
            if len(metadata_names) != 1:
                raise ReleaseReviewError(
                    "wheel must contain exactly one .dist-info/METADATA document"
                )
            metadata = Parser().parsestr(
                archive.read(metadata_names[0]).decode("utf-8")
            )
    except (OSError, UnicodeError, zipfile.BadZipFile, KeyError) as exc:
        raise ReleaseReviewError(f"cannot read wheel metadata: {exc}") from exc
    if metadata.get("Name") != "agent-governance-starter":
        raise ReleaseReviewError("wheel distribution name is not agent-governance-starter")
    version = metadata.get("Version")
    if not version:
        raise ReleaseReviewError("wheel metadata does not declare Version")
    return version


def _validate_artifacts(
    wheel: Path,
    manifest_path: Path,
) -> tuple[Mapping[str, object], str]:
    try:
        manifest = load_release_manifest(manifest_path)
    except (OSError, UnicodeError, TypeError, json.JSONDecodeError) as exc:
        raise ReleaseReviewError(f"cannot load release manifest: {exc}") from exc
    errors = validate_release_manifest(manifest)
    if errors:
        raise ReleaseReviewError("invalid release manifest: " + "; ".join(errors))
    artifact = manifest.get("artifact")
    if not isinstance(artifact, Mapping):
        raise ReleaseReviewError("review manifest must contain an immutable artifact")
    if artifact.get("filename") != wheel.name:
        raise ReleaseReviewError("manifest artifact filename does not match the wheel")
    digest = hashlib.sha256(wheel.read_bytes()).hexdigest()
    if artifact.get("sha256") != digest:
        raise ReleaseReviewError("manifest artifact SHA-256 does not match the wheel")
    wheel_version = _wheel_metadata_version(wheel)
    if manifest.get("tool_version") != wheel_version:
        raise ReleaseReviewError("manifest tool version does not match wheel metadata")
    return manifest, digest


def _run(
    command: list[str],
    *,
    cwd: Path | None = None,
    env: Mapping[str, str] | None = None,
) -> CommandEvidence:
    command_env = os.environ.copy()
    if env is not None:
        command_env.update(env)
    command_env["PYTHONUTF8"] = "1"
    command_env["PYTHONIOENCODING"] = "utf-8"
    completed = subprocess.run(
        command,
        cwd=cwd,
        env=command_env,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return CommandEvidence(completed.returncode, completed.stdout, completed.stderr)


def _installed_python(root: Path) -> Path:
    if os.name == "nt":
        return root / "Scripts/python.exe"
    return root / "bin/python"


def collect_release_review_evidence(
    source: Path,
    wheel: Path,
    manifest: Path,
    consumer: Path,
) -> ReleaseReviewEvidence:
    """Exercise source tests and the exact wheel in a temporary isolated runtime."""

    source_env = os.environ.copy()
    source_env["PYTHONPATH"] = str(source / "src")
    source_tests = _run(
        [
            sys.executable,
            "-m",
            "unittest",
            "discover",
            "-s",
            "tests",
            "-v",
        ],
        cwd=source,
        env=source_env,
    )
    with TemporaryDirectory(prefix="agentgov-release-review-runtime-") as temp_dir:
        runtime = Path(temp_dir) / "venv"
        venv.EnvBuilder(with_pip=True).create(runtime)
        python = _installed_python(runtime)
        install = _run(
            [str(python), "-m", "pip", "install", "--no-deps", str(wheel)]
        )
        if install.exit_code != 0:
            raise ReleaseReviewError(
                "candidate wheel installation failed:\n" + install.transcript()
            )
        candidate = [str(python), "-m", "agentgov"]
        installed_version = _run([*candidate, "--version"])
        manifest_check = _run(
            [*candidate, "check", "release-manifest", str(manifest)]
        )
        consumer_check = _run(
            [*candidate, "check", "repository", str(consumer)]
        )
        consumer_status = _run(
            [
                *candidate,
                "status",
                str(consumer),
                "--format",
                "markdown",
                "--non-interactive",
            ]
        )
        upgrade_plan = _run(
            [
                *candidate,
                "plan",
                "upgrade-pr",
                str(consumer),
                "--manifest",
                str(manifest),
                "--format",
                "json",
            ]
        )
    return ReleaseReviewEvidence(
        source_tests=source_tests,
        installed_version=installed_version,
        manifest_check=manifest_check,
        consumer_check=consumer_check,
        consumer_status=consumer_status,
        upgrade_plan=upgrade_plan,
    )


def _upgrade_gate(
    manifest: Mapping[str, object],
    evidence: CommandEvidence,
) -> tuple[dict[str, str], str]:
    try:
        plan = json.loads(evidence.stdout)
    except json.JSONDecodeError as exc:
        return (
            {
                "id": "consumer-upgrade-policy",
                "status": "FAIL",
                "detail": f"upgrade planner did not return JSON: {exc}",
            },
            "blocked",
        )
    state = plan.get("state") if isinstance(plan, Mapping) else None
    channel = manifest.get("channel")
    if channel == "release-candidate":
        reasons = plan.get("reasons") if isinstance(plan, Mapping) else None
        expected_reason = "only a validated stable release can produce an upgrade PR candidate"
        if state == "blocked" and isinstance(reasons, list) and expected_reason in reasons:
            return (
                {
                    "id": "consumer-upgrade-policy",
                    "status": "PASS",
                    "detail": "release candidate is blocked from consumer upgrade proposals",
                },
                "ready_for_human_review",
            )
    elif channel == "stable" and state in {"candidate", "current"}:
        return (
            {
                "id": "consumer-upgrade-policy",
                "status": "PASS",
                "detail": f"stable consumer upgrade plan state is {state}",
            },
            "ready_for_human_review",
        )
    return (
        {
            "id": "consumer-upgrade-policy",
            "status": "FAIL",
            "detail": f"unexpected {channel} upgrade plan state: {state}",
        },
        "blocked",
    )


def _gate(gate_id: str, evidence: CommandEvidence, detail: str) -> dict[str, str]:
    return {
        "id": gate_id,
        "status": "PASS" if evidence.exit_code == 0 else "FAIL",
        "detail": detail,
    }


def _consumer_governance_summary(markdown: str) -> ConsumerGovernanceSummary:
    lines = markdown.splitlines()
    adoption_rows = [line for line in lines if line.startswith("| Adoption |")]
    if len(adoption_rows) != 1:
        raise ReleaseReviewError(
            "consumer governance status must contain exactly one Adoption row"
        )
    adoption_cells = [
        cell.strip() for cell in adoption_rows[0].strip().strip("|").split("|")
    ]
    if len(adoption_cells) != 3 or adoption_cells[0] != "Adoption":
        raise ReleaseReviewError("consumer governance Adoption row is invalid")
    adoption = adoption_cells[1]
    if adoption not in {"configured", "incomplete"}:
        raise ReleaseReviewError(
            f"consumer governance adoption state is unsupported: {adoption}"
        )

    findings_header = "| PASS | WARN | FAIL | ADVISORY |"
    header_indexes = [
        index for index, line in enumerate(lines) if line == findings_header
    ]
    if len(header_indexes) != 1:
        raise ReleaseReviewError(
            "consumer governance status must contain exactly one Findings table"
        )
    header_index = header_indexes[0]
    if header_index + 2 >= len(lines):
        raise ReleaseReviewError("consumer governance Findings table is incomplete")
    alignment = lines[header_index + 1]
    if alignment != "|---:|---:|---:|---:|":
        raise ReleaseReviewError("consumer governance Findings table is unsupported")
    count_cells = [
        cell.strip()
        for cell in lines[header_index + 2].strip().strip("|").split("|")
    ]
    if len(count_cells) != 4 or any(not cell.isdecimal() for cell in count_cells):
        raise ReleaseReviewError("consumer governance finding counts are invalid")
    counts = [int(cell) for cell in count_cells]
    return ConsumerGovernanceSummary(adoption, *counts)


def _review_document(
    *,
    source: Path,
    consumer: Path,
    manifest: Mapping[str, object],
    wheel: Path,
    digest: str,
    evidence: ReleaseReviewEvidence,
) -> tuple[dict[str, object], tuple[Mapping[str, str], ...]]:
    expected_version_line = f"agentgov {manifest['tool_version']}"
    version_pass = (
        evidence.installed_version.exit_code == 0
        and evidence.installed_version.stdout.strip() == expected_version_line
    )
    gates: list[dict[str, str]] = [
        {
            "id": "artifact-integrity",
            "status": "PASS",
            "detail": "wheel filename, metadata version, and SHA-256 match the manifest",
        },
        _gate("source-tests", evidence.source_tests, "complete source test suite"),
        {
            "id": "installed-version",
            "status": "PASS" if version_pass else "FAIL",
            "detail": f"expected {expected_version_line}",
        },
        _gate(
            "manifest-contract",
            evidence.manifest_check,
            "installed candidate validates the immutable release manifest",
        ),
        _gate(
            "consumer-repository",
            evidence.consumer_check,
            "candidate checks the consumer repository without project dependencies",
        ),
        _gate(
            "consumer-status",
            evidence.consumer_status,
            "candidate renders the consumer governance status",
        ),
    ]
    upgrade_gate, upgrade_state = _upgrade_gate(manifest, evidence.upgrade_plan)
    gates.append(upgrade_gate)
    state = "ready_for_human_review"
    if upgrade_state == "blocked" or any(gate["status"] == "FAIL" for gate in gates):
        state = "blocked"
    document: dict[str, object] = {
        "contract_version": RELEASE_REVIEW_CONTRACT_VERSION,
        "tool": {"name": "agentgov", "version": __version__},
        "mode": "local_review",
        "release": {
            "version": manifest["tool_version"],
            "channel": manifest["channel"],
            "wheel_filename": wheel.name,
            "wheel_sha256": digest,
            "supported_from": manifest["supported_from"],
            "readable_layout_versions": manifest["readable_layout_versions"],
            "target_layout_version": manifest["target_layout_version"],
            "repository_changes_declared": manifest[
                "repository_changes_declared"
            ],
            "declared_migrations": manifest["declared_migrations"],
        },
        "source": {"name": source.name},
        "consumer": {"name": consumer.name},
        "review_state": state,
        "gates": gates,
        "human_decision": {
            "state": "pending",
            "allowed": ["approve", "request_changes", "reject"],
        },
        "authority_boundary": {
            "source_modified": False,
            "consumer_modified": False,
            "git_commit_created": False,
            "tag_created": False,
            "pushed": False,
            "published": False,
            "deployed": False,
        },
    }
    return document, tuple(gates)


def _render_review_markdown(
    document: Mapping[str, object],
    *,
    consumer_governance: ConsumerGovernanceSummary,
    freshness: Mapping[str, object] | None = None,
) -> str:
    release = document["release"]
    if not isinstance(release, Mapping):
        raise ReleaseReviewError("internal release review document is invalid")
    gates = document["gates"]
    if not isinstance(gates, list):
        raise ReleaseReviewError("internal release review gates are invalid")
    consumer = document["consumer"]
    if not isinstance(consumer, Mapping):
        raise ReleaseReviewError("internal release review consumer is invalid")
    escape = lambda value: str(value).replace("|", "\\|").replace("\n", "<br>")
    lines = [
        "# AgentGov Release Review",
        "",
        f"Release: `{escape(release['version'])}` ({escape(release['channel'])})",
        f"Consumer pilot: `{escape(consumer['name'])}`",
        f"Review state: **{document['review_state']}**",
        "",
        "## Automated gates",
        "",
        "| Gate | Status | Detail |",
        "|---|---|---|",
    ]
    lines.extend(
        f"| `{escape(gate['id'])}` | {escape(gate['status'])} | "
        f"{escape(gate['detail'])} |"
        for gate in gates
        if isinstance(gate, Mapping)
    )
    lines.extend(
        [
            "",
            "## Consumer governance summary",
            "",
            f"Adoption: **{consumer_governance.adoption}**",
            "",
            "| PASS | WARN | FAIL | ADVISORY |",
            "|---:|---:|---:|---:|",
            (
                f"| {consumer_governance.pass_count} | "
                f"{consumer_governance.warn_count} | "
                f"{consumer_governance.fail_count} | "
                f"{consumer_governance.advisory_count} |"
            ),
            "",
            (
                "A PASS `consumer-status` gate means the status command completed "
                "and rendered successfully. It does not mean consumer governance "
                "is complete. Review `consumer-status.md` for the findings."
            ),
            "",
        ]
    )
    if freshness is not None:
        freshness_result = freshness.get("result")
        if not isinstance(freshness_result, Mapping):
            raise ReleaseReviewError("internal freshness pilot result is invalid")
        reason_codes = freshness_result.get("reason_codes")
        messages = freshness_result.get("messages")
        if not isinstance(reason_codes, list) or not isinstance(messages, list):
            raise ReleaseReviewError("internal freshness pilot details are invalid")
        rendered_reasons = ", ".join(str(item) for item in reason_codes) or "none"
        lines.extend(
            [
                "## Evidence Freshness pilot (non-blocking)",
                "",
                f"Record: `{escape(freshness['record_ref'])}`",
                f"As of: `{escape(freshness_result['as_of'])}`",
                f"Status: **{escape(freshness_result['status'])}**",
                f"Reason codes: `{escape(rendered_reasons)}`",
                "",
                *[f"- {escape(message)}" for message in messages],
                "",
                "This pilot result does not change release-review gates, state, or exit behavior.",
                "Observed events remain producer-supplied; no event was discovered or added automatically.",
                "",
            ]
        )
    lines.extend(
        [
            "",
            "## Human decision",
            "",
            "Automated evidence is complete, but no release decision has been made.",
            "",
            "- [ ] Approve",
            "- [ ] Request changes",
            "- [ ] Reject",
            "",
            "## Authority boundary",
            "",
            "- Source and consumer repositories were not modified.",
            "- No commit, tag, push, publication, release, or deployment was performed.",
            "- A passing gate does not authorize a release.",
            "",
        ]
    )
    return "\n".join(lines)


def create_release_review_bundle(
    source: Path,
    *,
    wheel: Path,
    manifest_path: Path,
    consumer: Path,
    output: Path,
    freshness_record: Path | None = None,
    freshness_as_of: str | None = None,
    evidence_collector: EvidenceCollector = collect_release_review_evidence,
) -> ReleaseReviewResult:
    """Create one atomic review bundle from exact artifacts and consumer evidence."""

    resolved_source = _directory(source, "source repository")
    resolved_consumer = _directory(consumer, "consumer repository")
    resolved_wheel = _regular_file(wheel, "candidate wheel")
    resolved_manifest = _regular_file(manifest_path, "release manifest")
    if (freshness_record is None) != (freshness_as_of is None):
        raise ReleaseReviewError(
            "freshness_record and freshness_as_of must be supplied together"
        )
    if output.exists() or output.is_symlink():
        raise ReleaseReviewConflictError(f"review output already exists: {output}")
    parent = _directory(output.parent, "review output parent")
    resolved_output = parent / output.name
    manifest, digest = _validate_artifacts(resolved_wheel, resolved_manifest)
    freshness: Mapping[str, object] | None = None
    if freshness_record is not None:
        resolved_freshness, freshness_ref = _source_relative_file(
            resolved_source,
            freshness_record,
            "freshness record",
        )
        try:
            freshness_result = check_evidence_freshness(
                resolved_freshness,
                as_of=freshness_as_of,
            )
        except (OSError, UnicodeError, TypeError, ValueError) as exc:
            raise ReleaseReviewError(f"cannot evaluate freshness record: {exc}") from exc
        freshness = _freshness_pilot_document(
            record_ref=freshness_ref,
            result=freshness_result,
        )
    evidence = evidence_collector(
        resolved_source,
        resolved_wheel,
        resolved_manifest,
        resolved_consumer,
    )
    consumer_governance = _consumer_governance_summary(
        evidence.consumer_status.stdout
    )
    document, gates = _review_document(
        source=resolved_source,
        consumer=resolved_consumer,
        manifest=manifest,
        wheel=resolved_wheel,
        digest=digest,
        evidence=evidence,
    )
    with TemporaryDirectory(prefix=".agentgov-review-", dir=parent) as temp_dir:
        staging = Path(temp_dir)
        shutil.copyfile(resolved_wheel, staging / resolved_wheel.name)
        shutil.copyfile(resolved_manifest, staging / "release-manifest.json")
        (staging / "source-tests.txt").write_text(
            evidence.source_tests.transcript(), encoding="utf-8", newline="\n"
        )
        (staging / "consumer-check.txt").write_text(
            evidence.consumer_check.transcript(), encoding="utf-8", newline="\n"
        )
        (staging / "candidate-checks.txt").write_text(
            "INSTALLED VERSION\n"
            + evidence.installed_version.transcript()
            + "\nMANIFEST CONTRACT\n"
            + evidence.manifest_check.transcript(),
            encoding="utf-8",
            newline="\n",
        )
        (staging / "consumer-status.md").write_text(
            evidence.consumer_status.stdout, encoding="utf-8", newline="\n"
        )
        (staging / "upgrade-plan.json").write_text(
            evidence.upgrade_plan.stdout, encoding="utf-8", newline="\n"
        )
        if freshness is not None:
            (staging / "evidence-freshness.json").write_text(
                json.dumps(freshness, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
                newline="\n",
            )
        (staging / "review.json").write_text(
            json.dumps(document, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        (staging / "REVIEW.md").write_text(
            _render_review_markdown(
                document,
                consumer_governance=consumer_governance,
                freshness=freshness,
            ),
            encoding="utf-8",
            newline="\n",
        )
        staging.replace(resolved_output)
    return ReleaseReviewResult(
        resolved_output,
        str(document["review_state"]),
        gates,
        freshness,
    )
