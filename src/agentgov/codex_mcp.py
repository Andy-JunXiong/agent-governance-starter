"""Reviewed create-missing-only Codex project configuration for AgentGov MCP."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from agentgov.codex_hooks import (
    CodexHookPolicyError,
    CodexHooksAction,
    _git_root,
)
from agentgov.governance_mcp import MCP_TOOL_NAMES


CODEX_MCP_CONFIG_PATH = Path(".codex/config.toml")
CODEX_MCP_ADAPTER_ID = "openai.codex-mcp"
CODEX_MCP_PROVIDER_ID = "openai.codex-current-agent"


class CodexMcpIntegrationError(RuntimeError):
    """A reviewed Codex MCP integration plan is no longer safe to apply."""


@dataclass(frozen=True)
class CodexMcpIntegrationPlan:
    root: Path
    action: CodexHooksAction
    path: Path
    reason: str
    content: str | None

    @property
    def has_conflict(self) -> bool:
        return self.action is CodexHooksAction.CONFLICT


@dataclass(frozen=True)
class CodexMcpIntegrationResult:
    root: Path
    created_files: tuple[Path, ...]


def render_codex_mcp_config() -> str:
    tools = ", ".join(json.dumps(item) for item in MCP_TOOL_NAMES)
    return (
        "[mcp_servers.agentgov_governance]\n"
        'command = "agentgov"\n'
        'args = ["adapter", "governance-mcp", "--host-profile", "codex"]\n'
        "enabled = true\n"
        "required = true\n"
        f"enabled_tools = [{tools}]\n"
        'default_tools_approval_mode = "auto"\n'
        "startup_timeout_sec = 10\n"
        "tool_timeout_sec = 1800\n"
    )


def plan_codex_mcp_integration(repository: Path) -> CodexMcpIntegrationPlan:
    root = _git_root(repository)
    target = root / CODEX_MCP_CONFIG_PATH
    expected = render_codex_mcp_config()
    if target.is_symlink() or target.is_dir():
        return CodexMcpIntegrationPlan(
            root, CodexHooksAction.CONFLICT, CODEX_MCP_CONFIG_PATH,
            "target must be a regular file and requires human resolution", None,
        )
    if target.is_file():
        try:
            current = target.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            raise CodexHookPolicyError(f"cannot read existing Codex config: {exc}") from exc
        if current == expected:
            return CodexMcpIntegrationPlan(
                root, CodexHooksAction.PRESERVE, CODEX_MCP_CONFIG_PATH,
                "the exact AgentGov Codex MCP server is already configured", None,
            )
        return CodexMcpIntegrationPlan(
            root, CodexHooksAction.CONFLICT, CODEX_MCP_CONFIG_PATH,
            "existing Codex config differs and will not be overwritten or merged", None,
        )
    current = root
    for part in CODEX_MCP_CONFIG_PATH.parts[:-1]:
        current = current / part
        if current.is_symlink() or (current.exists() and not current.is_dir()):
            return CodexMcpIntegrationPlan(
                root, CodexHooksAction.CONFLICT, CODEX_MCP_CONFIG_PATH,
                f"parent path {current.relative_to(root).as_posix()} is not a safe directory", None,
            )
    return CodexMcpIntegrationPlan(
        root, CodexHooksAction.CREATE, CODEX_MCP_CONFIG_PATH,
        "create reviewed project configuration for the packaged AgentGov MCP Adapter",
        expected,
    )


def render_codex_mcp_plan_json(
    plan: CodexMcpIntegrationPlan,
    *,
    non_interactive: bool,
) -> str:
    payload = {
        "contract": "agentgov.codex-mcp-integration-plan",
        "schema_version": "1.0",
        "repository": str(plan.root),
        "mode": "dry_run",
        "interaction": "non_interactive" if non_interactive else "no_prompt",
        "item": {
            "action": plan.action.value,
            "path": plan.path.as_posix(),
            "reason": plan.reason,
            "content": plan.content,
        },
        "authority_boundary": {
            "repository_modified": False,
            "write_authorized": False,
            "config_trust_authorized": False,
            "starts_mcp_server": False,
            "authorizes_git_or_release_operations": False,
        },
    }
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def request_codex_mcp_confirmation(
    plan: CodexMcpIntegrationPlan,
    *,
    decision_reader: Callable[[str], str],
    is_interactive_terminal: bool,
) -> bool:
    if not is_interactive_terminal:
        return False
    return decision_reader(
        f'Type INTEGRATE to create "{plan.path.as_posix()}" in "{plan.root}": '
    ) == "INTEGRATE"


def apply_codex_mcp_plan(plan: CodexMcpIntegrationPlan) -> CodexMcpIntegrationResult:
    if plan.has_conflict:
        raise CodexMcpIntegrationError("Codex MCP integration plan contains a conflict")
    if plan.action is CodexHooksAction.PRESERVE:
        return CodexMcpIntegrationResult(plan.root, ())
    if plan.content is None:
        raise CodexMcpIntegrationError("planned Codex MCP config has no content")
    target = plan.root / plan.path
    current = plan.root
    for part in plan.path.parts[:-1]:
        current = current / part
        if current.is_symlink() or (current.exists() and not current.is_dir()):
            raise CodexMcpIntegrationError("Codex MCP config parent path became unsafe")
    if target.exists() or target.is_symlink():
        raise CodexMcpIntegrationError(
            f"planned target appeared and was not overwritten: {plan.path.as_posix()}"
        )
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        with target.open("x", encoding="utf-8", newline="") as handle:
            handle.write(plan.content)
    except FileExistsError as exc:
        raise CodexMcpIntegrationError(
            f"planned target appeared and was not overwritten: {plan.path.as_posix()}"
        ) from exc
    return CodexMcpIntegrationResult(plan.root, (plan.path,))
