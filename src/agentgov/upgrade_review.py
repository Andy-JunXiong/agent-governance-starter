"""Consumer-local review evidence for one stable AgentGov upgrade proposal."""

from __future__ import annotations

import difflib
import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Mapping

from agentgov import __version__
from agentgov.release_metadata import load_release_manifest
from agentgov.repository import FindingStatus
from agentgov.status import inspect_governance_status, render_status_markdown
from agentgov.upgrade_pr import (
    UpgradePlanState,
    plan_upgrade_pull_request,
    upgrade_pull_request_plan_document,
)


UPGRADE_REVIEW_CONTRACT_VERSION = "1.1"


class UpgradeReviewError(Exception):
    """Raised when trustworthy consumer upgrade evidence cannot be created."""


class UpgradeReviewConflictError(UpgradeReviewError):
    """Raised when review output would overwrite an existing path."""


@dataclass(frozen=True)
class UpgradeReviewResult:
    output: Path
    state: str
    gates: tuple[Mapping[str, str], ...]

    @property
    def blocked(self) -> bool:
        return self.state == "blocked"


def _regular_file(path: Path, label: str) -> Path:
    if path.is_symlink() or not path.is_file():
        raise UpgradeReviewError(f"{label} must be a regular file: {path}")
    return path.resolve()


def _repository(path: Path) -> Path:
    if path.is_symlink() or not path.is_dir():
        raise UpgradeReviewError(f"consumer repository must be a directory: {path}")
    return path.resolve()


def _output_parent(path: Path) -> Path:
    if path.is_symlink() or not path.is_dir():
        raise UpgradeReviewError(f"review output parent must be a directory: {path}")
    return path.resolve()


def _gate(gate_id: str, passed: bool, detail: str) -> dict[str, str]:
    return {
        "id": gate_id,
        "status": "PASS" if passed else "FAIL",
        "detail": detail,
    }


def _portable_plan(plan: object, repository_name: str, manifest_name: str) -> dict[str, object]:
    document = upgrade_pull_request_plan_document(plan)  # type: ignore[arg-type]
    document["repository"] = repository_name
    document["manifest_source"] = manifest_name
    return document


def _workflow_patch(root: Path, plan: object) -> str:
    changes = plan.changes  # type: ignore[attr-defined]
    if not changes:
        return ""
    patches: list[str] = []
    for change in changes:
        before = (
            []
            if change.action == "create"
            else (root / change.path)
            .read_text(encoding="utf-8")
            .splitlines(keepends=True)
        )
        after = change.content.splitlines(keepends=True)
        path = change.path.as_posix()
        patches.append(
            "".join(
                difflib.unified_diff(
                    before,
                    after,
                    fromfile=("/dev/null" if change.action == "create" else f"a/{path}"),
                    tofile=f"b/{path}",
                )
            )
        )
    return "".join(patches)


def _review_document(
    *,
    repository: Path,
    manifest: Mapping[str, object],
    plan: object,
    status: object,
) -> tuple[dict[str, object], tuple[Mapping[str, str], ...]]:
    report = status.repository_report  # type: ignore[attr-defined]
    plan_state = plan.state  # type: ignore[attr-defined]
    candidate = plan_state is UpgradePlanState.CANDIDATE
    current = plan_state is UpgradePlanState.CURRENT
    no_failures = not report.has_failures
    allowed_paths = {
        ".github/workflows/agentgov.yml",
        ".github/workflows/agentgov-upgrade.yml",
    }
    change_paths = [change.path.as_posix() for change in plan.changes]  # type: ignore[attr-defined]
    bounded_change = (
        candidate
        and 1 <= len(change_paths) <= 2
        and len(change_paths) == len(set(change_paths))
        and set(change_paths).issubset(allowed_paths)
    ) or (current and not change_paths)
    gates: tuple[Mapping[str, str], ...] = (
        _gate(
            "stable-release-manifest",
            manifest.get("channel") == "stable",
            (
                "release manifest is valid and declares the stable channel"
                if manifest.get("channel") == "stable"
                else f"manifest channel is {manifest.get('channel')}; stable is required"
            ),
        ),
        _gate(
            "compatible-upgrade-plan",
            candidate or current,
            (
                f"planner state is {plan_state.value}"
                if candidate or current
                else "; ".join(plan.reasons)  # type: ignore[attr-defined]
            ),
        ),
        _gate(
            "bounded-workflow-change",
            bounded_change,
            (
                f"proposal contains {len(change_paths)} exact managed workflow change(s)"
                if candidate
                else "no workflow change is required"
                if current
                else "no safe bounded workflow change is available"
            ),
        ),
        _gate(
            "consumer-governance-check",
            no_failures,
            "consumer repository has no deterministic FAIL findings",
        ),
    )
    state = (
        "no_upgrade_needed"
        if current and no_failures
        else "ready_for_human_review"
        if candidate and all(gate["status"] == "PASS" for gate in gates)
        else "blocked"
    )
    artifact = manifest.get("artifact")
    if not isinstance(artifact, Mapping):
        raise UpgradeReviewError("stable manifest does not contain an artifact")
    changes = [
        {
            "path": change.path.as_posix(),
            "action": change.action,
            "before_sha256": change.before_sha256,
            "after_sha256": change.after_sha256,
        }
        for change in plan.changes  # type: ignore[attr-defined]
    ]
    summary = {
        finding_status.value.lower(): report.count(finding_status)
        for finding_status in FindingStatus
    }
    document: dict[str, object] = {
        "contract_version": UPGRADE_REVIEW_CONTRACT_VERSION,
        "tool": {"name": "agentgov", "version": __version__},
        "mode": "consumer_local_review",
        "consumer": {"name": repository.name},
        "release": {
            "version": str(manifest["tool_version"]),
            "channel": str(manifest["channel"]),
            "artifact_filename": str(artifact["filename"]),
            "artifact_sha256": str(artifact["sha256"]),
        },
        "transition": {
            "current_version": plan.current_version,  # type: ignore[attr-defined]
            "available_version": plan.available_version,  # type: ignore[attr-defined]
            "plan_state": plan_state.value,
            "changes": changes,
        },
        "consumer_findings": summary,
        "review_state": state,
        "gates": list(gates),
        "human_decision": {
            "state": "pending",
            "allowed": ["approve", "request_changes", "reject"],
        },
        "limitations": [
            "The manifest contract was validated, but this command did not download or execute the release wheel.",
            "Consumer project tests and production workflows were not run.",
            "A workflow-only proposal does not prove governance effectiveness or upgrade benefit.",
        ],
        "authority_boundary": {
            "review_output_created": True,
            "governed_files_modified": False,
            "planned_change_applied": False,
            "git_branch_created": False,
            "pull_request_created": False,
            "merge_authorized": False,
            "release_or_deploy_authorized": False,
        },
    }
    return document, gates


def _escape(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", "<br>")


def _render_markdown(document: Mapping[str, object]) -> str:
    release = document["release"]
    transition = document["transition"]
    findings = document["consumer_findings"]
    gates = document["gates"]
    consumer = document["consumer"]
    if not all(isinstance(value, Mapping) for value in (release, transition, findings, consumer)):
        raise UpgradeReviewError("internal consumer upgrade review document is invalid")
    if not isinstance(gates, list):
        raise UpgradeReviewError("internal consumer upgrade gates are invalid")
    lines = [
        "# AgentGov Upgrade Review",
        "",
        f"Consumer: `{_escape(consumer['name'])}`",  # type: ignore[index]
        f"Upgrade: `{_escape(transition['current_version'])}` → `{_escape(transition['available_version'])}`",  # type: ignore[index]
        f"Review state: **{_escape(document['review_state'])}**",
        "",
        "> This page is generated for the consumer repository. It does not approve or apply the upgrade.",
        "",
        "## What would change",
        "",
    ]
    changes = transition["changes"]  # type: ignore[index]
    if isinstance(changes, list) and changes:
        for change in changes:
            if isinstance(change, Mapping):
                before = (
                    "absent"
                    if change["before_sha256"] is None
                    else str(change["before_sha256"])
                )
                lines.append(
                    f"- `{_escape(change['path'])}` ({_escape(change['action'])}): "
                    f"`{_escape(before)}` → "
                    f"`{_escape(change['after_sha256'])}`"
                )
    else:
        lines.append("- No managed workflow change is required.")
    lines.extend(
        [
            "",
            "## Automated gates",
            "",
            "| Gate | Status | Detail |",
            "|---|---|---|",
            *(
                f"| `{_escape(gate['id'])}` | {_escape(gate['status'])} | {_escape(gate['detail'])} |"
                for gate in gates
                if isinstance(gate, Mapping)
            ),
            "",
            "## Current consumer findings",
            "",
            "| PASS | WARN | FAIL | ADVISORY |",
            "|---:|---:|---:|---:|",
            f"| {findings['pass']} | {findings['warn']} | {findings['fail']} | {findings['advisory']} |",  # type: ignore[index]
            "",
            "## Human decision",
            "",
            "Automated evidence is complete, but no upgrade decision has been made.",
            "",
            "- [ ] Approve",
            "- [ ] Request changes",
            "- [ ] Reject",
            "",
            "## Important limitations",
            "",
            *(
                f"- {item}"
                for item in document["limitations"]  # type: ignore[union-attr]
            ),
            "",
            "## Authority boundary",
            "",
            "- The planned workflow change was not applied.",
            "- No branch, pull request, merge, release, or deployment was created or authorized.",
            "- The review output itself is evidence and may be uploaded as a CI artifact.",
            "",
        ]
    )
    return "\n".join(lines)


def create_upgrade_review_bundle(
    repository: Path,
    *,
    manifest_path: Path,
    output: Path,
) -> UpgradeReviewResult:
    """Create one atomic consumer-local review bundle without applying its plan."""

    resolved_repository = _repository(repository)
    resolved_manifest = _regular_file(manifest_path, "release manifest")
    if output.exists() or output.is_symlink():
        raise UpgradeReviewConflictError(f"review output already exists: {output}")
    parent = _output_parent(output.parent)
    resolved_output = parent / output.name
    try:
        manifest = load_release_manifest(resolved_manifest)
        plan = plan_upgrade_pull_request(
            resolved_repository,
            manifest_path=resolved_manifest,
        )
        status = inspect_governance_status(resolved_repository)
    except (OSError, UnicodeError, ValueError, TypeError, json.JSONDecodeError) as exc:
        raise UpgradeReviewError(str(exc)) from exc
    document, gates = _review_document(
        repository=resolved_repository,
        manifest=manifest,
        plan=plan,
        status=status,
    )
    portable_plan = _portable_plan(plan, resolved_repository.name, resolved_manifest.name)
    patch = _workflow_patch(resolved_repository, plan)
    with TemporaryDirectory(prefix=".agentgov-upgrade-review-", dir=parent) as temp_dir:
        staging = Path(temp_dir)
        shutil.copyfile(resolved_manifest, staging / "release-manifest.json")
        (staging / "upgrade-review.json").write_text(
            json.dumps(document, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        (staging / "UPGRADE_REVIEW.md").write_text(
            _render_markdown(document), encoding="utf-8", newline="\n"
        )
        (staging / "upgrade-plan.json").write_text(
            json.dumps(portable_plan, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        (staging / "workflow.patch").write_text(
            patch, encoding="utf-8", newline="\n"
        )
        (staging / "current-status.md").write_text(
            render_status_markdown(status), encoding="utf-8", newline="\n"
        )
        staging.replace(resolved_output)
    return UpgradeReviewResult(
        resolved_output,
        str(document["review_state"]),
        gates,
    )
