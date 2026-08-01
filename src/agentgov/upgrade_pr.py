"""Read-only planning contract for a future automated AgentGov upgrade PR."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Mapping

from agentgov import __version__
from agentgov.consumer_ci import (
    WORKFLOW_PATH,
    inspect_managed_workflow_content,
    render_consumer_workflow,
)
from agentgov.release_metadata import load_release_manifest, validate_release_manifest
from agentgov.update_check import comparable_version_key, load_repository_layout


UPGRADE_PR_CONTRACT_VERSION = "1.0"


class UpgradePlanState(str, Enum):
    CURRENT = "current"
    CANDIDATE = "candidate"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class UpgradeChange:
    path: Path
    before_sha256: str
    after_sha256: str
    content: str


@dataclass(frozen=True)
class UpgradePullRequestPlan:
    root: Path
    manifest_source: Path
    state: UpgradePlanState
    current_version: str
    available_version: str
    branch: str | None
    title: str | None
    body: str | None
    changes: tuple[UpgradeChange, ...]
    reasons: tuple[str, ...]

    @property
    def has_candidate(self) -> bool:
        return self.state is UpgradePlanState.CANDIDATE


def _sha256_text(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _resolve_root(root: Path) -> Path:
    if root.is_symlink():
        raise ValueError(f"repository root must not be a symbolic link: {root}")
    if not root.exists():
        raise FileNotFoundError(root)
    if not root.is_dir():
        raise ValueError(f"repository root is not a directory: {root}")
    return root.resolve()


def _blocked(
    *,
    root: Path,
    manifest_source: Path,
    current_version: str,
    available_version: str,
    reason: str,
) -> UpgradePullRequestPlan:
    return UpgradePullRequestPlan(
        root=root,
        manifest_source=manifest_source,
        state=UpgradePlanState.BLOCKED,
        current_version=current_version,
        available_version=available_version,
        branch=None,
        title=None,
        body=None,
        changes=(),
        reasons=(reason,),
    )


def plan_upgrade_pull_request(
    root: Path,
    *,
    manifest_path: Path,
) -> UpgradePullRequestPlan:
    """Plan one exact managed-workflow change without writing or using Git."""

    resolved = _resolve_root(root)
    source = manifest_path.resolve()
    manifest = load_release_manifest(source)
    errors = validate_release_manifest(manifest)
    if errors:
        raise ValueError("invalid release manifest: " + "; ".join(errors))

    available = str(manifest["tool_version"])
    if manifest["channel"] != "stable":
        return _blocked(
            root=resolved,
            manifest_source=source,
            current_version="unknown",
            available_version=available,
            reason="only a validated stable release can produce an upgrade PR candidate",
        )

    target = resolved / WORKFLOW_PATH
    if target.is_symlink() or not target.is_file():
        return _blocked(
            root=resolved,
            manifest_source=source,
            current_version="unknown",
            available_version=available,
            reason="managed consumer CI workflow is missing or unsafe; integrate it first",
        )
    current_content = target.read_text(encoding="utf-8")
    managed_release = inspect_managed_workflow_content(current_content)
    if managed_release is None:
        return _blocked(
            root=resolved,
            manifest_source=source,
            current_version="unknown",
            available_version=available,
            reason="consumer workflow is customized or conflicted and cannot be rewritten automatically",
        )
    current_version = managed_release.version

    if comparable_version_key(available) <= comparable_version_key(current_version):
        return UpgradePullRequestPlan(
            root=resolved,
            manifest_source=source,
            state=UpgradePlanState.CURRENT,
            current_version=current_version,
            available_version=available,
            branch=None,
            title=None,
            body=None,
            changes=(),
            reasons=("managed consumer workflow already uses the latest stable release",),
        )

    supported_from = manifest.get("supported_from")
    if not isinstance(supported_from, list) or current_version not in supported_from:
        return _blocked(
            root=resolved,
            manifest_source=source,
            current_version=current_version,
            available_version=available,
            reason=(
                f"release {available} does not declare support from managed version "
                f"{current_version}"
            ),
        )

    layout = load_repository_layout(resolved)
    readable_layouts = manifest.get("readable_layout_versions")
    if layout is not None and (
        not isinstance(readable_layouts, list) or layout not in readable_layouts
    ):
        return _blocked(
            root=resolved,
            manifest_source=source,
            current_version=current_version,
            available_version=available,
            reason=f"repository layout {layout} is not readable by release {available}",
        )
    if manifest.get("repository_changes_declared") is True:
        return _blocked(
            root=resolved,
            manifest_source=source,
            current_version=current_version,
            available_version=available,
            reason=(
                "release declares repository migrations; a workflow-only upgrade PR "
                "cannot apply them safely"
            ),
        )

    artifact = manifest.get("artifact")
    if not isinstance(artifact, Mapping):
        raise ValueError("stable release manifest does not contain an artifact")
    next_content = render_consumer_workflow(
        version=available,
        wheel_url=str(artifact["url"]),
        wheel_sha256=str(artifact["sha256"]),
    )
    change = UpgradeChange(
        path=WORKFLOW_PATH,
        before_sha256=_sha256_text(current_content),
        after_sha256=_sha256_text(next_content),
        content=next_content,
    )
    title = f"chore: update AgentGov to {available}"
    body = (
        f"Updates the managed AgentGov consumer workflow from "
        f"{current_version} to {available}.\n\n"
        "The release manifest and wheel digest were validated before this plan was "
        "created. This pull request does not authorize merge, release, or deployment."
    )
    return UpgradePullRequestPlan(
        root=resolved,
        manifest_source=source,
        state=UpgradePlanState.CANDIDATE,
        current_version=current_version,
        available_version=available,
        branch=f"agentgov/update-{available}",
        title=title,
        body=body,
        changes=(change,),
        reasons=("a newer compatible stable release is available",),
    )


def upgrade_pull_request_plan_document(
    plan: UpgradePullRequestPlan,
) -> dict[str, Any]:
    return {
        "contract_version": UPGRADE_PR_CONTRACT_VERSION,
        "tool": {"name": "agentgov", "version": __version__},
        "repository": str(plan.root),
        "manifest_source": str(plan.manifest_source),
        "mode": "read_only",
        "state": plan.state.value,
        "current_version": plan.current_version,
        "available_version": plan.available_version,
        "pull_request": {
            "branch": plan.branch,
            "title": plan.title,
            "body": plan.body,
            "changes": [
                {
                    "path": change.path.as_posix(),
                    "before_sha256": change.before_sha256,
                    "after_sha256": change.after_sha256,
                    "content": change.content,
                }
                for change in plan.changes
            ],
        },
        "reasons": list(plan.reasons),
        "authority_boundary": {
            "repository_modified": False,
            "git_branch_created": False,
            "pull_request_created": False,
            "merge_authorized": False,
            "release_or_deploy_authorized": False,
        },
    }


def render_upgrade_pull_request_plan_json(plan: UpgradePullRequestPlan) -> str:
    return json.dumps(
        upgrade_pull_request_plan_document(plan),
        indent=2,
        ensure_ascii=False,
    ) + "\n"
