"""Optional Codex lifecycle-hook adapter and create-missing-only integration."""

from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Mapping

from agentgov.change_scope import check_development_scope
from agentgov.coding_agent_transport import (
    CodingAgentEvent,
    CodingAgentResponse,
    coding_agent_event_from_payload,
    run_coding_agent_event,
)
from agentgov.development_session import load_active_session, resolve_active_task
from agentgov.event_store import utc_now
from agentgov.host_interaction import build_host_interaction_capabilities


CODEX_ADAPTER_ID = "openai.codex-hooks"
CODEX_HOOKS_PATH = Path(".codex/hooks.json")
CODEX_HOOK_EVENTS = {
    "SessionStart": "repository.activated",
    "PostToolUse": "implementation.changed",
    "Stop": "completion.requested",
}
CODEX_HOOK_NAMES = frozenset(
    (*CODEX_HOOK_EVENTS, "UserPromptSubmit", "PermissionRequest")
)
SENSITIVE_CODEX_FIELDS = {
    "prompt",
    "tool_input",
    "tool_response",
    "transcript_path",
    "last_assistant_message",
    "model",
}

CODEX_HOST_CAPABILITIES = build_host_interaction_capabilities(
    adapter_id=CODEX_ADAPTER_ID,
    surface_family="lifecycle_hooks",
    interactions={
        "task_admission": {
            "delivery_mode": "context_only",
            "decision_recording": "unavailable",
            "reason_code": "custom_decision_control_unsupported",
        },
        "scope_resolution": {
            "delivery_mode": "context_only",
            "decision_recording": "unavailable",
            "reason_code": "custom_decision_control_unsupported",
        },
        "completion_review": {
            "delivery_mode": "context_only",
            "decision_recording": "unavailable",
            "reason_code": "custom_decision_control_unsupported",
        },
        "tool_permission": {
            "delivery_mode": "native",
            "decision_recording": "host_managed",
            "reason_code": "normal_host_permission_prompt",
        },
    },
)


class CodexHookPolicyError(ValueError):
    """A Codex hook event or repository binding is unsafe or unsupported."""


class CodexHooksIntegrationError(RuntimeError):
    """A reviewed Codex hooks integration plan is no longer safe to apply."""


class CodexHooksAction(str, Enum):
    CREATE = "CREATE"
    PRESERVE = "PRESERVE"
    CONFLICT = "CONFLICT"


@dataclass(frozen=True)
class CodexHookEnvelope:
    hook_event_name: str
    event_id: str
    correlation_id: str
    actor_class: str
    source: str | None
    turn_present: bool
    stop_hook_active: bool
    discarded_fields: tuple[str, ...]


@dataclass(frozen=True)
class CodexHookResult:
    status: str
    envelope: CodexHookEnvelope
    output: Mapping[str, Any]
    response: CodingAgentResponse | None


@dataclass(frozen=True)
class CodexHooksIntegrationPlan:
    root: Path
    action: CodexHooksAction
    path: Path
    reason: str
    content: str | None

    @property
    def has_conflict(self) -> bool:
        return self.action is CodexHooksAction.CONFLICT


@dataclass(frozen=True)
class CodexHooksIntegrationResult:
    root: Path
    created_files: tuple[Path, ...]


def _git_root(path: Path) -> Path:
    if path.is_symlink():
        raise CodexHookPolicyError("repository path must not be a symbolic link")
    if not path.exists():
        raise FileNotFoundError(path)
    if not path.is_dir():
        raise CodexHookPolicyError("repository path must be a directory")
    completed = subprocess.run(
        ("git", "-C", str(path.resolve()), "rev-parse", "--show-toplevel"),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        raise CodexHookPolicyError("Codex hook cwd must belong to a Git worktree")
    try:
        reported = completed.stdout.decode("utf-8").strip()
    except UnicodeDecodeError as exc:
        raise CodexHookPolicyError("Git repository root is not valid UTF-8") from exc
    root = Path(reported).resolve(strict=True)
    if root.is_symlink() or not root.is_dir():
        raise CodexHookPolicyError("Git repository root must be a regular directory")
    return root


def _required_text(payload: Mapping[str, Any], field: str, *, maximum: int = 512) -> str:
    value = payload.get(field)
    if not isinstance(value, str) or not value or len(value) > maximum:
        raise CodexHookPolicyError(f"Codex hook {field} is invalid")
    return value


def _hashed_id(prefix: str, *parts: str) -> str:
    digest = hashlib.sha256("\x00".join(parts).encode("utf-8")).hexdigest()
    return prefix + digest[:32]


def codex_hook_from_payload(
    payload: Any,
    *,
    repository: Path,
) -> tuple[CodexHookEnvelope, Path]:
    """Validate stable Codex hook identity while discarding sensitive values."""

    if not isinstance(payload, Mapping):
        raise CodexHookPolicyError("Codex hook input must be one JSON object")
    hook_event_name = payload.get("hook_event_name")
    if hook_event_name not in CODEX_HOOK_NAMES:
        raise CodexHookPolicyError("Codex hook event is unsupported")
    session_id = _required_text(payload, "session_id")
    cwd_value = _required_text(payload, "cwd", maximum=4096)
    cwd = Path(cwd_value)
    if not cwd.is_absolute():
        raise CodexHookPolicyError("Codex hook cwd must be absolute")
    payload_root = _git_root(cwd)
    selected_root = _git_root(repository)
    if payload_root != selected_root:
        raise CodexHookPolicyError("Codex hook cwd does not match the selected repository")

    source: str | None = None
    turn_id: str | None = None
    stop_hook_active = False
    event_key = hook_event_name
    actor_class = "coding_agent"
    if hook_event_name == "SessionStart":
        source = _required_text(payload, "source", maximum=32)
        if source not in {"startup", "resume", "clear", "compact"}:
            raise CodexHookPolicyError("Codex SessionStart source is unsupported")
        event_key = source
    else:
        turn_id = _required_text(payload, "turn_id")
        event_key = turn_id

    if hook_event_name == "UserPromptSubmit":
        if not isinstance(payload.get("prompt"), str):
            raise CodexHookPolicyError("Codex UserPromptSubmit prompt shape is invalid")
        actor_class = "human"
    elif hook_event_name == "PostToolUse":
        tool_name = _required_text(payload, "tool_name", maximum=256)
        tool_use_id = _required_text(payload, "tool_use_id")
        if "tool_input" not in payload or "tool_response" not in payload:
            raise CodexHookPolicyError("Codex PostToolUse tool payload shape is invalid")
        event_key = f"{turn_id}:{tool_name}:{tool_use_id}"
    elif hook_event_name == "PermissionRequest":
        tool_name = _required_text(payload, "tool_name", maximum=256)
        if "tool_input" not in payload:
            raise CodexHookPolicyError(
                "Codex PermissionRequest tool payload shape is invalid"
            )
        event_key = f"{turn_id}:{tool_name}:permission"
    elif hook_event_name == "Stop":
        stop_hook_active = payload.get("stop_hook_active")
        if not isinstance(stop_hook_active, bool):
            raise CodexHookPolicyError("Codex Stop stop_hook_active must be boolean")
        last_message = payload.get("last_assistant_message")
        if last_message is not None and not isinstance(last_message, str):
            raise CodexHookPolicyError(
                "Codex Stop last_assistant_message shape is invalid"
            )

    discarded = tuple(sorted(field for field in SENSITIVE_CODEX_FIELDS if field in payload))
    envelope = CodexHookEnvelope(
        hook_event_name=hook_event_name,
        event_id=_hashed_id("evt-", session_id, hook_event_name, event_key),
        correlation_id=_hashed_id("codex-", session_id),
        actor_class=actor_class,
        source=source,
        turn_present=turn_id is not None,
        stop_hook_active=stop_hook_active,
        discarded_fields=discarded,
    )
    return envelope, selected_root


def _coding_agent_event(envelope: CodexHookEnvelope) -> CodingAgentEvent:
    payload = {
        "contract": "agentgov.coding-agent-event",
        "schema_version": "1.0",
        "event_id": envelope.event_id,
        "occurred_at": utc_now(),
        "event_type": CODEX_HOOK_EVENTS[envelope.hook_event_name],
        "source": {
            "adapter_id": CODEX_ADAPTER_ID,
            "actor_class": envelope.actor_class,
        },
        "correlation_id": envelope.correlation_id,
        "facts": {
            "validation_outcome": None,
            "evidence_ref": None,
            "scope_decision": None,
            "review_outcome": None,
        },
    }
    return coding_agent_event_from_payload(payload)


def _bounded_context(response: CodingAgentResponse, *, maximum: int = 1400) -> str:
    lines = [
        f"AgentGov status: {response.cycle.status}.",
        f"Dashboard: {response.cycle.dashboard_ref}.",
    ]
    if response.card is not None:
        lines.extend((response.card.title, response.card.summary))
        lines.append("Available actions: " + ", ".join(response.card.actions) + ".")
    if response.interaction is not None:
        binding = response.interaction.binding
        lines.append(
            "Host interaction: "
            f"delivery={binding['delivery_mode']}, "
            f"decision_recording={binding['decision_recording']}, "
            f"reason={binding['reason_code']}."
        )
        if binding["decision_recording"] == "unavailable":
            lines.append(
                "The listed actions are context only; this Codex Hook cannot record "
                "the human governance decision."
            )
    if response.decision_prompt is not None:
        prompt = response.decision_prompt
        lines.append(
            "Decision needed now: "
            f"{prompt.why_now} Recommended safe default: {prompt.recommended_option_id}."
        )
        lines.append(
            "Single-select options: "
            + "; ".join(
                f"{option['index']}={option['label']}" for option in prompt.options
            )
            + "."
        )
    for finding in response.cycle.findings:
        lines.append(
            f"{finding['semantics']} {finding['code']}: {finding['message']}"
        )
    lines.append(
        "No scope expansion, exception, commit, merge, release, or deployment was authorized."
    )
    text = "\n".join(lines)
    if len(text) > maximum:
        return text[: maximum - 1] + "…"
    return text


def _hook_output(
    envelope: CodexHookEnvelope,
    response: CodingAgentResponse,
) -> Mapping[str, Any]:
    context = _bounded_context(response)
    event_name = envelope.hook_event_name
    if event_name in {"SessionStart", "UserPromptSubmit"}:
        return {
            "systemMessage": f"AgentGov {response.cycle.status}",
            "hookSpecificOutput": {
                "hookEventName": event_name,
                "additionalContext": context,
            },
        }
    if event_name == "PostToolUse":
        output: dict[str, Any] = {
            "hookSpecificOutput": {
                "hookEventName": "PostToolUse",
                "additionalContext": context,
            }
        }
        if response.cycle.status == "blocked":
            output.update(
                {
                    "decision": "block",
                    "reason": (
                        "AgentGov observed a scope or evidence failure after the tool ran. "
                        "The completed side effect was not undone. Review the findings before continuing."
                    ),
                }
            )
        return output
    if event_name == "Stop":
        if response.cycle.status in {"blocked", "needs_human"}:
            return {
                "decision": "block",
                "reason": context,
            }
        return {
            "continue": True,
            "systemMessage": context,
        }
    raise CodexHookPolicyError("Codex hook output event is unsupported")


def process_codex_hook(
    payload: Any,
    *,
    repository: Path,
    dashboard_output: Path = Path(".agentgov/dashboard.html"),
) -> CodexHookResult:
    """Map one Codex hook to AgentGov without retaining sensitive host fields."""

    envelope, root = codex_hook_from_payload(payload, repository=repository)
    if envelope.hook_event_name == "PermissionRequest":
        return CodexHookResult(
            "delegated_native_permission",
            envelope,
            {
                "systemMessage": (
                    "AgentGov did not allow or deny this tool permission. Codex's "
                    "normal human approval flow remains in control. Tool permission "
                    "does not admit task scope, approve an exception, or accept completion."
                )
            },
            None,
        )
    if envelope.hook_event_name == "UserPromptSubmit":
        active = load_active_session(root)
        active_context = (
            f"A local active task exists: {active.task_id} ({active.task_digest}). "
            "Use active_task_continuation only if the requested work stays inside its admitted goal and scope."
            if active is not None
            else "No local active task exists."
        )
        policy_available = (root / "governance/admission-policy.json").is_file()
        context = (
            "AgentGov did not forward or interpret the user prompt. Classify it host-side with "
            "agentgov.work-request 1.0. Questions, explanations, status queries, and read-only "
            "diagnosis need no task and zero confirmation while no repository write occurs. "
            f"{active_context} Before a new repository change, route a normalized request under "
            f"the repository policy (conventional policy present={str(policy_available).lower()}); "
            "use fast_track only when AgentGov reports clean standing-policy authority. Otherwise "
            "use the existing task proposal review. No code, scope, exception, Git, deployment, "
            "or release authority was granted. If the AgentGov governance MCP tools are available, "
            "use them for normalized alignment and medium-risk active-Agent self-review; preserve "
            "the returned journey handle and exact pending bindings. Never send raw conversation "
            "or source content to those tools."
        )
        return CodexHookResult(
            "routing_context",
            envelope,
            {
                "systemMessage": "AgentGov work request routing",
                "hookSpecificOutput": {
                    "hookEventName": "UserPromptSubmit",
                    "additionalContext": context,
                },
            },
            None,
        )
    if envelope.hook_event_name == "Stop" and envelope.stop_hook_active:
        return CodexHookResult("ignored_repeat_stop", envelope, {"continue": True}, None)

    if envelope.hook_event_name == "PostToolUse":
        session = load_active_session(root)
        if session is not None:
            task_path, _ = resolve_active_task(root)
            report = check_development_scope(task_path, repository=root)
            if not report.changes:
                return CodexHookResult("ignored_no_change", envelope, {}, None)

    response = run_coding_agent_event(
        root,
        event=_coding_agent_event(envelope),
        sequence=1,
        dashboard_output=dashboard_output,
        host_capabilities=CODEX_HOST_CAPABILITIES,
    )
    return CodexHookResult(
        "processed",
        envelope,
        _hook_output(envelope, response),
        response,
    )


def render_codex_hook_output(result: CodexHookResult) -> str:
    return json.dumps(result.output, ensure_ascii=False, sort_keys=True) + "\n"


def render_codex_hooks_config() -> str:
    """Render the exact project hook config shipped by this AgentGov version."""

    command = "agentgov adapter codex-hook"
    config = {
        "description": (
            "Generated by AgentGov. Codex must separately review and trust this exact hook definition."
        ),
        "hooks": {
            "SessionStart": [
                {
                    "matcher": "startup|resume|clear|compact",
                    "hooks": [
                        {
                            "type": "command",
                            "command": command,
                            "commandWindows": command,
                            "timeout": 30,
                            "statusMessage": "Activating AgentGov",
                        }
                    ],
                }
            ],
            "UserPromptSubmit": [
                {
                    "hooks": [
                        {
                            "type": "command",
                            "command": command,
                            "commandWindows": command,
                            "timeout": 30,
                            "statusMessage": "Routing AgentGov task context",
                        }
                    ]
                }
            ],
            "PermissionRequest": [
                {
                    "hooks": [
                        {
                            "type": "command",
                            "command": command,
                            "commandWindows": command,
                            "timeout": 30,
                            "statusMessage": "Preserving human tool approval",
                        }
                    ]
                }
            ],
            "PostToolUse": [
                {
                    "matcher": "Bash|apply_patch|Edit|Write",
                    "hooks": [
                        {
                            "type": "command",
                            "command": command,
                            "commandWindows": command,
                            "timeout": 60,
                            "statusMessage": "Checking AgentGov scope",
                        }
                    ],
                }
            ],
            "Stop": [
                {
                    "hooks": [
                        {
                            "type": "command",
                            "command": command,
                            "commandWindows": command,
                            "timeout": 600,
                            "statusMessage": "Reconciling AgentGov completion",
                        }
                    ]
                }
            ],
        },
    }
    return json.dumps(config, ensure_ascii=False, indent=2) + "\n"


def plan_codex_hooks_integration(repository: Path) -> CodexHooksIntegrationPlan:
    root = _git_root(repository)
    target = root / CODEX_HOOKS_PATH
    expected = render_codex_hooks_config()
    if target.is_symlink() or target.is_dir():
        return CodexHooksIntegrationPlan(
            root,
            CodexHooksAction.CONFLICT,
            CODEX_HOOKS_PATH,
            "target must be a regular file and requires human resolution",
            None,
        )
    if target.is_file():
        try:
            current = target.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            raise CodexHookPolicyError(f"cannot read existing Codex hooks: {exc}") from exc
        if current == expected:
            return CodexHooksIntegrationPlan(
                root,
                CodexHooksAction.PRESERVE,
                CODEX_HOOKS_PATH,
                "the exact managed AgentGov Codex hooks are already configured",
                None,
            )
        return CodexHooksIntegrationPlan(
            root,
            CodexHooksAction.CONFLICT,
            CODEX_HOOKS_PATH,
            "existing Codex hooks differ and will not be overwritten or merged",
            None,
        )

    current = root
    for part in CODEX_HOOKS_PATH.parts[:-1]:
        current = current / part
        if current.is_symlink() or (current.exists() and not current.is_dir()):
            return CodexHooksIntegrationPlan(
                root,
                CodexHooksAction.CONFLICT,
                CODEX_HOOKS_PATH,
                f"parent path {current.relative_to(root).as_posix()} is not a safe directory",
                None,
            )
    return CodexHooksIntegrationPlan(
        root,
        CodexHooksAction.CREATE,
        CODEX_HOOKS_PATH,
        "create reviewed project hooks for the packaged AgentGov Codex Adapter",
        expected,
    )


def render_codex_hooks_plan_json(
    plan: CodexHooksIntegrationPlan,
    *,
    non_interactive: bool,
) -> str:
    payload = {
        "contract": "agentgov.codex-hooks-integration-plan",
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
            "hook_trust_authorized": False,
            "installs_plugin": False,
            "authorizes_git_or_release_operations": False,
        },
    }
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def request_codex_hooks_confirmation(
    plan: CodexHooksIntegrationPlan,
    *,
    decision_reader: Callable[[str], str],
    is_interactive_terminal: bool,
) -> bool:
    if not is_interactive_terminal:
        return False
    decision = decision_reader(
        f'Type INTEGRATE to create "{plan.path.as_posix()}" in "{plan.root}": '
    )
    return decision == "INTEGRATE"


def apply_codex_hooks_plan(
    plan: CodexHooksIntegrationPlan,
) -> CodexHooksIntegrationResult:
    if plan.has_conflict:
        raise CodexHooksIntegrationError("Codex hooks integration plan contains a conflict")
    if plan.action is CodexHooksAction.PRESERVE:
        return CodexHooksIntegrationResult(plan.root, ())
    if plan.content is None:
        raise CodexHooksIntegrationError("planned Codex hooks file has no content")

    target = plan.root / plan.path
    current = plan.root
    for part in plan.path.parts[:-1]:
        current = current / part
        if current.is_symlink():
            raise CodexHooksIntegrationError(
                f"parent path became a symbolic link: {current.relative_to(plan.root).as_posix()}"
            )
        if current.exists() and not current.is_dir():
            raise CodexHooksIntegrationError(
                f"parent path became a non-directory: {current.relative_to(plan.root).as_posix()}"
            )
    if target.exists() or target.is_symlink():
        raise CodexHooksIntegrationError(
            f"planned target appeared and was not overwritten: {plan.path.as_posix()}"
        )
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        with target.open("x", encoding="utf-8", newline="") as handle:
            handle.write(plan.content)
    except FileExistsError as exc:
        raise CodexHooksIntegrationError(
            f"planned target appeared and was not overwritten: {plan.path.as_posix()}"
        ) from exc
    return CodexHooksIntegrationResult(plan.root, (plan.path,))
