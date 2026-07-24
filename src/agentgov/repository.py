"""Scoped repository-level governance checks."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from agentgov.agent_skills import check_agent_skills
from agentgov.artifacts import ArtifactPolicyError, check_capability_artifact
from agentgov.capability import load_capability_manifest, validate_capability_manifest
from agentgov.controls import ControlStatus, check_control_mapping
from agentgov.evaluation import EvaluationStatus, check_evaluation_bundle
from agentgov.inventory import InventoryReport, InventoryStatus, check_inventory
from agentgov.references import (
    ReferencePolicyError,
    ReferenceStatus,
    check_capability_references,
)


class FindingStatus(str, Enum):
    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"
    ADVISORY = "ADVISORY"


@dataclass(frozen=True)
class Finding:
    status: FindingStatus
    check_id: str
    message: str


@dataclass(frozen=True)
class RepositoryReport:
    root: Path
    findings: tuple[Finding, ...]

    @property
    def has_failures(self) -> bool:
        return any(finding.status is FindingStatus.FAIL for finding in self.findings)

    def count(self, status: FindingStatus) -> int:
        return sum(finding.status is status for finding in self.findings)


_REQUIRED_FILES = {
    "required:constitution": Path("AGENTS.md"),
    "required:adr-template": Path("docs/adr/TEMPLATE.md"),
    "required:invariants": Path("docs/adr/INVARIANTS.md"),
}
_PLACEHOLDER_RE = re.compile(r"\{\{[A-Z][A-Z0-9_-]*\}\}")
_CAPABILITY_DIRECTORY = Path("governance/capabilities")
_LEGACY_CAPABILITY_DIRECTORY = Path("prompt-governance/capabilities")
_CONTROL_DIRECTORY = Path("governance/controls")
_EVALUATION_DIRECTORY = Path("evaluation")
_AGENT_SKILLS_DIRECTORY = Path("agent-skills")
_ARTIFACT_DIRECTORY = Path("governance/artifacts")
_LEGACY_ARTIFACT_DIRECTORY = Path("prompt-governance/artifacts")


def _configured_path(root: Path, canonical: Path, legacy: Path) -> Path:
    """Prefer the canonical layout while retaining read-only legacy support."""

    return canonical if (root / canonical).exists() else legacy


def _check_layout(root: Path) -> Finding | None:
    canonical = root / "governance"
    legacy = root / "prompt-governance"
    canonical_configured = any(
        (canonical / child).exists() for child in ("capabilities", "artifacts")
    )
    legacy_configured = any(
        (legacy / child).exists() for child in ("capabilities", "artifacts")
    )
    if canonical_configured and legacy_configured:
        return Finding(
            FindingStatus.FAIL,
            "governance:layout",
            "governance/ and prompt-governance/ must not both be configured; "
            "complete an explicit migration to one layout",
        )
    if legacy_configured:
        return Finding(
            FindingStatus.WARN,
            "governance:layout",
            "prompt-governance/ is a supported legacy layout; migrate explicitly "
            "to canonical governance/",
        )
    return None


def _check_required_files(root: Path) -> tuple[list[Finding], list[Path]]:
    findings: list[Finding] = []
    readable_files: list[Path] = []
    for check_id, relative_path in _REQUIRED_FILES.items():
        path = root / relative_path
        if path.is_symlink():
            findings.append(
                Finding(
                    FindingStatus.FAIL,
                    check_id,
                    f"{relative_path.as_posix()} must not be a symbolic link",
                )
            )
        elif path.is_file():
            findings.append(
                Finding(
                    FindingStatus.PASS,
                    check_id,
                    f"{relative_path.as_posix()} exists",
                )
            )
            readable_files.append(path)
        else:
            findings.append(
                Finding(
                    FindingStatus.FAIL,
                    check_id,
                    f"{relative_path.as_posix()} is missing",
                )
            )
    return findings, readable_files


def _check_placeholders(root: Path, files: list[Path]) -> Finding:
    occurrences: list[str] = []
    for path in files:
        text = path.read_text(encoding="utf-8")
        relative_path = path.relative_to(root).as_posix()
        occurrences.extend(
            f"{relative_path}:{placeholder}"
            for placeholder in _PLACEHOLDER_RE.findall(text)
        )

    if occurrences:
        unique_placeholders = {item.split(":", 1)[1] for item in occurrences}
        return Finding(
            FindingStatus.WARN,
            "governance:placeholders",
            f"{len(unique_placeholders)} unresolved governance placeholder(s) remain",
        )
    return Finding(
        FindingStatus.PASS,
        "governance:placeholders",
        "no unresolved governance placeholders found in required files",
    )


def _check_capabilities(root: Path) -> list[Finding]:
    capability_directory = _configured_path(
        root, _CAPABILITY_DIRECTORY, _LEGACY_CAPABILITY_DIRECTORY
    )
    capability_root = root / capability_directory
    if capability_root.is_symlink():
        return [
            Finding(
                FindingStatus.FAIL,
                "capabilities:directory",
                f"{capability_directory.as_posix()} must not be a symbolic link",
            )
        ]
    if not capability_root.exists():
        return [
            Finding(
                FindingStatus.WARN,
                "capabilities:directory",
                f"{_CAPABILITY_DIRECTORY.as_posix()} is not configured",
            )
        ]
    if not capability_root.is_dir():
        return [
            Finding(
                FindingStatus.FAIL,
                "capabilities:directory",
                f"{capability_directory.as_posix()} is not a directory",
            )
        ]

    capability_paths = sorted(capability_root.rglob("*.json"))
    if not capability_paths:
        return [
            Finding(
                FindingStatus.WARN,
                "capabilities:manifests",
                "no AI capability manifests found",
            )
        ]

    findings: list[Finding] = []
    for path in capability_paths:
        relative_path = path.relative_to(root).as_posix()
        check_id = f"capability:{relative_path}"
        if path.is_symlink():
            findings.append(
                Finding(
                    FindingStatus.FAIL,
                    check_id,
                    f"{relative_path} must not be a symbolic link",
                )
            )
            continue
        try:
            manifest = load_capability_manifest(path)
        except json.JSONDecodeError as exc:
            findings.append(
                Finding(
                    FindingStatus.FAIL,
                    check_id,
                    f"invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}",
                )
            )
            continue
        except ValueError as exc:
            findings.append(Finding(FindingStatus.FAIL, check_id, str(exc)))
            continue

        errors = validate_capability_manifest(manifest)
        if errors:
            findings.append(
                Finding(
                    FindingStatus.FAIL,
                    check_id,
                    "; ".join(errors),
                )
            )
        else:
            findings.append(
                Finding(
                    FindingStatus.PASS,
                    check_id,
                    f"{relative_path} satisfies the capability contract",
                )
            )
    return findings


def _check_evaluations(
    root: Path,
    inventory: InventoryReport,
) -> list[Finding]:
    evaluation_root = root / _EVALUATION_DIRECTORY
    if evaluation_root.is_symlink():
        return [
            Finding(
                FindingStatus.FAIL,
                "evaluation:directory",
                "evaluation must not be a symbolic link",
            )
        ]
    if not evaluation_root.exists():
        return [
            Finding(
                FindingStatus.WARN,
                "evaluation:directory",
                "evaluation readiness is not configured",
            )
        ]
    if not evaluation_root.is_dir():
        return [
            Finding(
                FindingStatus.FAIL,
                "evaluation:directory",
                "evaluation is not a directory",
            )
        ]

    manifest_paths = sorted(
        path
        for path in evaluation_root.rglob("evaluation-manifest.json")
        if "fixtures" not in path.relative_to(evaluation_root).parts
    )
    if not manifest_paths:
        return [
            Finding(
                FindingStatus.WARN,
                "evaluation:bundles",
                "no evaluation bundles are configured",
            )
        ]

    status_map = {
        EvaluationStatus.PASS: FindingStatus.PASS,
        EvaluationStatus.WARN: FindingStatus.WARN,
        EvaluationStatus.FAIL: FindingStatus.FAIL,
    }
    inventory_names = (
        set(inventory.capability_names)
        if inventory.configured and inventory.status is InventoryStatus.PASS
        else None
    )
    findings: list[Finding] = []
    for manifest_path in manifest_paths:
        bundle = manifest_path.parent
        relative_bundle = bundle.relative_to(root).as_posix()
        result = check_evaluation_bundle(bundle)
        status = status_map[result.status]
        messages = list(result.messages)
        if inventory_names is not None and result.capability_name is not None:
            if result.capability_name in inventory_names:
                messages.append(
                    f"capability {result.capability_name!r} is declared in "
                    "governance/inventory.json"
                )
            else:
                status = FindingStatus.FAIL
                messages.append(
                    f"orphan evaluation declares capability "
                    f"{result.capability_name!r}, which is not listed in "
                    "governance/inventory.json"
                )
        findings.append(
            Finding(
                status,
                f"evaluation:{relative_bundle}",
                f"{result.readiness}: {'; '.join(messages)}",
            )
        )
    return findings


def _check_governance_inventory(report: InventoryReport) -> list[Finding]:
    status_map = {
        InventoryStatus.PASS: FindingStatus.PASS,
        InventoryStatus.WARN: FindingStatus.WARN,
        InventoryStatus.FAIL: FindingStatus.FAIL,
    }
    findings = [
        Finding(
            status_map[report.status],
            "inventory:governance/inventory.json",
            "; ".join(report.messages),
        )
    ]
    if report.configured and report.status is InventoryStatus.PASS:
        findings.append(
            Finding(
                FindingStatus.ADVISORY,
                "inventory:completeness",
                "inventory closure validates owner declarations; it cannot prove "
                "that every real AI capability was discovered or declared",
            )
        )
    return findings


def _check_control_mappings(
    root: Path,
    inventory: InventoryReport,
) -> list[Finding]:
    controls_root = root / _CONTROL_DIRECTORY
    if controls_root.is_symlink():
        return [
            Finding(
                FindingStatus.FAIL,
                "controls:directory",
                "governance/controls must not be a symbolic link",
            )
        ]
    if not controls_root.exists():
        return [
            Finding(
                FindingStatus.WARN,
                "controls:directory",
                "capability control mappings are not configured",
            )
        ]
    if not controls_root.is_dir():
        return [
            Finding(
                FindingStatus.FAIL,
                "controls:directory",
                "governance/controls is not a directory",
            )
        ]

    mapping_paths = sorted(controls_root.rglob("*.json"))
    if not mapping_paths:
        return [
            Finding(
                FindingStatus.WARN,
                "controls:directory",
                "no capability control mappings are configured",
            )
        ]

    inventory_names = (
        set(inventory.capability_names)
        if inventory.configured and inventory.status is InventoryStatus.PASS
        else None
    )
    findings: list[Finding] = []
    claimed_names: set[str] = set()
    control_locations: dict[str, list[str]] = {}
    claims_complete = True
    for mapping_path in mapping_paths:
        relative_path = mapping_path.relative_to(root).as_posix()
        report = check_control_mapping(root, mapping_path)
        status = (
            FindingStatus.PASS
            if report.status is ControlStatus.PASS
            else FindingStatus.FAIL
        )
        messages = list(report.messages)
        if report.capability_name is None:
            claims_complete = False
        else:
            claimed_names.add(report.capability_name)
            if inventory_names is not None:
                if report.capability_name in inventory_names:
                    messages.append(
                        f"capability {report.capability_name!r} is declared in "
                        "governance/inventory.json"
                    )
                else:
                    status = FindingStatus.FAIL
                    claims_complete = False
                    messages.append(
                        f"orphan control mapping declares capability "
                        f"{report.capability_name!r}, which is not listed in "
                        "governance/inventory.json"
                    )
        if report.status is ControlStatus.PASS:
            for control_id in report.control_ids:
                control_locations.setdefault(control_id, []).append(relative_path)
        findings.append(
            Finding(
                status,
                f"control:{relative_path}",
                "; ".join(messages),
            )
        )

    for control_id, locations in sorted(control_locations.items()):
        if len(locations) > 1:
            findings.append(
                Finding(
                    FindingStatus.FAIL,
                    f"controls:control-id:{control_id}",
                    f"control ID {control_id!r} is declared in multiple mappings: "
                    + ", ".join(locations),
                )
            )

    if inventory_names is not None and claims_complete:
        for capability_name in sorted(inventory_names - claimed_names):
            findings.append(
                Finding(
                    FindingStatus.WARN,
                    f"controls:missing:{capability_name}",
                    f"Inventory capability {capability_name!r} has no configured "
                    "control mapping",
                )
            )

    if not any(
        finding.status is FindingStatus.FAIL for finding in findings
    ):
        findings.append(
            Finding(
                FindingStatus.ADVISORY,
                "controls:effectiveness",
                "control declarations and readable references do not prove "
                "control effectiveness, applicability, or exception quality",
            )
        )
    return findings


def _check_agent_skill_protocols(root: Path) -> list[Finding]:
    skills_root = root / _AGENT_SKILLS_DIRECTORY
    if not skills_root.exists():
        return [
            Finding(
                FindingStatus.WARN,
                "agent-skills:directory",
                "agent operating protocols are not configured",
            )
        ]

    try:
        report = check_agent_skills(skills_root)
    except ValueError as exc:
        return [Finding(FindingStatus.FAIL, "agent-skills:directory", str(exc))]

    return [
        Finding(
            FindingStatus.PASS if finding.passed else FindingStatus.FAIL,
            finding.check_id,
            finding.message,
        )
        for finding in report.findings
    ]


def _valid_capability_names(root: Path) -> set[str]:
    capability_root = root / _configured_path(
        root, _CAPABILITY_DIRECTORY, _LEGACY_CAPABILITY_DIRECTORY
    )
    if not capability_root.is_dir() or capability_root.is_symlink():
        return set()

    names: set[str] = set()
    for path in sorted(capability_root.rglob("*.json")):
        if path.is_symlink():
            continue
        try:
            manifest = load_capability_manifest(path)
        except (json.JSONDecodeError, ValueError, OSError, UnicodeError):
            continue
        if not validate_capability_manifest(manifest):
            names.add(str(manifest["name"]))
    return names


def _check_capability_artifacts(
    root: Path,
    inventory: InventoryReport,
) -> list[Finding]:
    artifact_directory = _configured_path(
        root, _ARTIFACT_DIRECTORY, _LEGACY_ARTIFACT_DIRECTORY
    )
    artifacts_root = root / artifact_directory
    capability_names = _valid_capability_names(root)
    inventory_names = (
        set(inventory.capability_names)
        if inventory.configured and inventory.status is InventoryStatus.PASS
        else None
    )
    if artifacts_root.is_symlink():
        return [
            Finding(
                FindingStatus.FAIL,
                "artifacts:directory",
                f"{artifact_directory.as_posix()} must not be a symbolic link",
            )
        ]
    if not artifacts_root.exists():
        return [
            Finding(
                FindingStatus.WARN,
                "artifacts:directory",
                "capability artifacts are not configured",
            )
        ]
    if not artifacts_root.is_dir():
        return [
            Finding(
                FindingStatus.FAIL,
                "artifacts:directory",
                f"{artifact_directory.as_posix()} is not a directory",
            )
        ]

    artifact_directories = sorted(
        (path for path in artifacts_root.iterdir() if path.is_dir()),
        key=lambda path: path.name,
    )
    if not artifact_directories:
        return [
            Finding(
                FindingStatus.WARN,
                "artifacts:directory",
                "no capability artifacts are configured",
            )
        ]

    findings: list[Finding] = []
    configured_names: set[str] = set()
    artifact_claims_complete = True
    for artifact_dir in artifact_directories:
        relative_dir = artifact_dir.relative_to(root).as_posix()
        check_id = f"artifact:{artifact_dir.name}"
        try:
            result = check_capability_artifact(artifact_dir, repository=root)
        except json.JSONDecodeError as exc:
            findings.append(
                Finding(
                    FindingStatus.FAIL,
                    check_id,
                    f"invalid artifact JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}",
                )
            )
            artifact_claims_complete = False
            continue
        except (ArtifactPolicyError, ValueError, OSError, UnicodeError) as exc:
            findings.append(Finding(FindingStatus.FAIL, check_id, str(exc)))
            artifact_claims_complete = False
            continue

        status = FindingStatus.PASS if result.passed else FindingStatus.FAIL
        messages = list(result.messages)
        if result.capability_name is None:
            artifact_claims_complete = False
        else:
            configured_names.add(result.capability_name)
            if result.capability_name not in capability_names:
                artifact_claims_complete = False
            if inventory_names is not None:
                if result.capability_name in inventory_names:
                    messages.append(
                        f"capability {result.capability_name!r} is declared in "
                        "governance/inventory.json"
                    )
                else:
                    status = FindingStatus.FAIL
                    artifact_claims_complete = False
                    messages.append(
                        f"orphan artifact declares capability "
                        f"{result.capability_name!r}, which is not listed in "
                        "governance/inventory.json"
                    )
        findings.append(
            Finding(
                status,
                check_id,
                f"{relative_dir}: {'; '.join(messages)}",
            )
        )

    if artifact_claims_complete:
        for name in sorted(capability_names - configured_names):
            findings.append(
                Finding(
                    FindingStatus.WARN,
                    f"artifact:{name}",
                    f"valid capability {name!r} has no configured review artifact",
                )
            )
    return findings


def _check_reference_integrity(root: Path) -> list[Finding]:
    capability_root = root / _configured_path(
        root, _CAPABILITY_DIRECTORY, _LEGACY_CAPABILITY_DIRECTORY
    )
    if not capability_root.is_dir() or capability_root.is_symlink():
        return []

    status_map = {
        ReferenceStatus.PASS: FindingStatus.PASS,
        ReferenceStatus.WARN: FindingStatus.WARN,
        ReferenceStatus.FAIL: FindingStatus.FAIL,
    }
    findings: list[Finding] = []
    for manifest_path in sorted(capability_root.rglob("*.json")):
        if manifest_path.is_symlink():
            continue
        try:
            manifest = load_capability_manifest(manifest_path)
        except (json.JSONDecodeError, ValueError, OSError, UnicodeError):
            continue
        if validate_capability_manifest(manifest):
            continue

        try:
            report = check_capability_references(manifest_path, repository=root)
        except ReferencePolicyError as exc:
            relative_path = manifest_path.relative_to(root).as_posix()
            findings.append(
                Finding(
                    FindingStatus.FAIL,
                    f"references:{relative_path}",
                    str(exc),
                )
            )
            continue
        for finding in report.findings:
            findings.append(
                Finding(
                    status_map[finding.status],
                    finding.check_id,
                    finding.message,
                )
            )
    return findings


def check_repository(root: Path) -> RepositoryReport:
    """Check the v0.1 repository contract without making any changes."""

    if root.is_symlink():
        raise ValueError(f"repository path must not be a symbolic link: {root}")
    if not root.exists():
        raise FileNotFoundError(root)
    if not root.is_dir():
        raise ValueError(f"repository path is not a directory: {root}")

    findings, readable_files = _check_required_files(root)
    inventory_report = check_inventory(root)
    layout_finding = _check_layout(root)
    if layout_finding is not None:
        findings.append(layout_finding)
    findings.append(_check_placeholders(root, readable_files))
    findings.extend(_check_capabilities(root))
    findings.extend(_check_governance_inventory(inventory_report))
    findings.extend(_check_control_mappings(root, inventory_report))
    findings.extend(_check_reference_integrity(root))
    findings.extend(_check_evaluations(root, inventory_report))
    findings.extend(_check_agent_skill_protocols(root))
    findings.extend(_check_capability_artifacts(root, inventory_report))
    findings.append(
        Finding(
            FindingStatus.ADVISORY,
            "governance:human-review",
            "confirm that approval and escalation boundaries match the repository's real risks",
        )
    )
    return RepositoryReport(root=root, findings=tuple(findings))
