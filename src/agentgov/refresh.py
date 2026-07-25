"""Deterministic, read-only repository refresh planning."""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Callable

from agentgov.update_check import (
    REPOSITORY_CONTRACT,
    REPOSITORY_CONTRACT_SCHEMA_VERSION,
    UpdateCheck,
    check_for_updates,
)


REFRESH_PLAN_CONTRACT_VERSION = "1.0"
CONTRACT_PATH = Path("governance/contract.json")


class RefreshAction(str, Enum):
    CREATE = "CREATE"
    PRESERVE = "PRESERVE"
    CONFLICT = "CONFLICT"


@dataclass(frozen=True)
class RefreshItem:
    action: RefreshAction
    path: Path
    reason: str
    content: str | None = None


@dataclass(frozen=True)
class RefreshPlan:
    update: UpdateCheck
    items: tuple[RefreshItem, ...]

    def count(self, action: RefreshAction) -> int:
        return sum(item.action is action for item in self.items)

    @property
    def has_conflicts(self) -> bool:
        return self.count(RefreshAction.CONFLICT) > 0


@dataclass(frozen=True)
class RefreshResult:
    root: Path
    created_files: tuple[Path, ...]


class RefreshConflictError(Exception):
    """Raised when a reviewed refresh plan is no longer safe to apply."""


def _contract_content(layout_version: str) -> str:
    return json.dumps(
        {
            "contract": REPOSITORY_CONTRACT,
            "schema_version": REPOSITORY_CONTRACT_SCHEMA_VERSION,
            "layout_version": layout_version,
        },
        indent=2,
    ) + "\n"


def plan_refresh(
    root: Path,
    *,
    manifest_path: Path | None = None,
) -> RefreshPlan:
    """Plan the bounded repository-contract refresh without writing."""

    update = check_for_updates(
        root,
        manifest_path=manifest_path,
        allow_contract_path_conflict=True,
    )
    target = update.repository / CONTRACT_PATH
    if target.is_symlink() or target.is_dir():
        item = RefreshItem(
            RefreshAction.CONFLICT,
            CONTRACT_PATH,
            "target must be a regular file and requires human resolution",
        )
    elif update.repository_layout is None:
        governance = update.repository / "governance"
        if governance.is_symlink() or (governance.exists() and not governance.is_dir()):
            item = RefreshItem(
                RefreshAction.CONFLICT,
                CONTRACT_PATH,
                "parent governance path is not a safe directory",
            )
        else:
            item = RefreshItem(
                RefreshAction.CREATE,
                CONTRACT_PATH,
                f"add repository layout anchor for {update.target_layout}",
                _contract_content(update.target_layout),
            )
    elif update.repository_layout == update.target_layout:
        item = RefreshItem(
            RefreshAction.PRESERVE,
            CONTRACT_PATH,
            f"repository layout already equals target {update.target_layout}",
        )
    else:
        item = RefreshItem(
            RefreshAction.CONFLICT,
            CONTRACT_PATH,
            f"layout migration {update.repository_layout} to {update.target_layout} "
            "is not implemented",
        )
    return RefreshPlan(update, (item,))


def render_refresh_plan_json(plan: RefreshPlan) -> str:
    payload = {
        "contract_version": REFRESH_PLAN_CONTRACT_VERSION,
        "mode": "dry_run",
        "repository": str(plan.update.repository),
        "target_layout_version": plan.update.target_layout,
        "summary": {
            action.value: plan.count(action) for action in RefreshAction
        },
        "items": [
            {
                "action": item.action.value,
                "path": item.path.as_posix(),
                "reason": item.reason,
                "content": item.content,
            }
            for item in plan.items
        ],
        "authority_boundary": {
            "repository_modified": False,
            "git_state_modified": False,
            "apply_authorized": False,
        },
    }
    return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"


def request_refresh_confirmation(
    plan: RefreshPlan,
    *,
    decision_reader: Callable[[str], str],
    is_interactive_terminal: bool,
) -> bool:
    """Grant write authority only for exact input from an interactive terminal."""

    if not is_interactive_terminal:
        return False
    create_count = plan.count(RefreshAction.CREATE)
    decision = decision_reader(
        f'Type REFRESH to create {create_count} file(s) in '
        f'"{plan.update.repository}": '
    )
    return decision == "REFRESH"


def apply_refresh_plan(plan: RefreshPlan) -> RefreshResult:
    """Create only reviewed deterministic files after revalidating the plan."""

    if plan.has_conflicts:
        raise RefreshConflictError("refresh plan contains unresolved conflicts")
    create_items = tuple(
        item for item in plan.items if item.action is RefreshAction.CREATE
    )
    for item in create_items:
        destination = plan.update.repository / item.path
        current = plan.update.repository
        for part in item.path.parts[:-1]:
            current = current / part
            if current.is_symlink():
                raise RefreshConflictError(
                    f"parent path became a symbolic link after preview: "
                    f"{current.relative_to(plan.update.repository).as_posix()}"
                )
            if current.exists() and not current.is_dir():
                raise RefreshConflictError(
                    f"parent path became a non-directory after preview: "
                    f"{current.relative_to(plan.update.repository).as_posix()}"
                )
        if destination.exists() or destination.is_symlink():
            raise RefreshConflictError(
                f"planned target appeared after preview and was not overwritten: "
                f"{item.path.as_posix()}"
            )

    created: list[Path] = []
    for item in create_items:
        if item.content is None:
            raise RefreshConflictError(
                f"planned create has no deterministic content: {item.path.as_posix()}"
            )
        destination = plan.update.repository / item.path
        destination.parent.mkdir(parents=True, exist_ok=True)
        try:
            with destination.open("x", encoding="utf-8", newline="") as handle:
                handle.write(item.content)
        except FileExistsError as exc:
            raise RefreshConflictError(
                f"planned target appeared during refresh and was not overwritten: "
                f"{item.path.as_posix()}"
            ) from exc
        created.append(item.path)
    return RefreshResult(plan.update.repository, tuple(created))
