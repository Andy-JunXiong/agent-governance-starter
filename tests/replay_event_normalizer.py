"""Privacy-bounded normalization for Codex proposal-review replay events.

This module is test support, not a product App Server client.  It accepts only
the exact structured App Server events needed by the installed-runtime replay
and deliberately drops model messages, tool arguments, raw MCP content, error
messages, and unrelated event payloads.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from typing import Any


PROPOSAL_SERVER = "agentgov_governance"
PROPOSAL_TOOL = "agentgov_task_proposal_review"
PROPOSAL_RESULT_CONTRACT = "agentgov.task-proposal-review-result"
PROPOSAL_ERROR_CONTRACT = "agentgov.mcp-tool-error"
MAX_NORMALIZED_TOOL_ERRORS = 8
_NORMALIZED_IDENTIFIER = re.compile(r"^[a-z][a-z0-9_]{0,79}$")
_BOUNDED_FIELD_PATH = re.compile(r"^[A-Za-z0-9_.\[\]-]{1,160}$")


def normalize_replay_event(event: Mapping[str, Any]) -> dict[str, Any] | None:
    """Return one allow-listed replay record or ``None`` for unrelated input."""

    method = event.get("method")
    params = event.get("params")
    if not isinstance(method, str) or not isinstance(params, Mapping):
        return None

    if method in {"item/started", "item/completed"}:
        return _normalize_tool_call(method, params)
    if method == "mcpServer/elicitation/request":
        return _normalize_form(event.get("id"), params)
    if method == "turn/completed":
        return _normalize_terminal(params)
    return None


def summarize_replay_events(events: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Reduce exact normalized events to one bounded replay outcome."""

    state = "not_called"
    call_ids: set[str] = set()
    completion_ids: set[str] = set()
    completion_statuses: set[str] = set()
    tool_errors: list[dict[str, Any]] = []
    tool_error_keys: set[tuple[Any, ...]] = set()
    tool_errors_truncated = False
    form_count = 0
    terminal_status: str | None = None

    for event in events:
        record = normalize_replay_event(event)
        if record is None:
            continue
        if record["kind"] == "proposal_tool_call":
            call_ids.add(record["item_id"])
            if record["phase"] == "started":
                state = "call_started"
            else:
                completion_ids.add(record["item_id"])
                completion_statuses.add(record["status"])
                tool_error = record["tool_error"]
                if tool_error is not None:
                    key = (
                        tool_error["error_code"],
                        tool_error["stage"],
                        tool_error["field_path"],
                        tool_error["rule"],
                        tool_error["retryable"],
                    )
                    if key not in tool_error_keys:
                        tool_error_keys.add(key)
                        if len(tool_errors) < MAX_NORMALIZED_TOOL_ERRORS:
                            tool_errors.append(tool_error)
                        else:
                            tool_errors_truncated = True
                    state = "call_failed"
                elif record["status"] == "failed":
                    state = "call_failed"
                elif record["result"] is not None:
                    state = "completed"
                else:
                    state = "completion_unknown"
        elif record["kind"] == "proposal_form":
            form_count += 1
            if state != "completed":
                state = "form_presented"
        elif record["kind"] == "terminal":
            terminal_status = record["status"]

    return {
        "state": state,
        "proposal_tool_calls": len(call_ids),
        "proposal_tool_completions": len(completion_ids),
        "proposal_tool_completion_statuses": sorted(completion_statuses),
        "agentgov_tool_errors": tool_errors,
        "agentgov_tool_errors_truncated": tool_errors_truncated,
        "forms_presented": form_count,
        "terminal_status": terminal_status,
    }


def _normalize_tool_call(
    method: str, params: Mapping[str, Any]
) -> dict[str, Any] | None:
    item = params.get("item")
    if not isinstance(item, Mapping):
        return None
    if (
        item.get("type") != "mcpToolCall"
        or item.get("server") != PROPOSAL_SERVER
        or item.get("tool") != PROPOSAL_TOOL
    ):
        return None

    item_id = item.get("id")
    status = item.get("status")
    if not isinstance(item_id, str) or not isinstance(status, str):
        return None
    if method == "item/started" and status != "inProgress":
        return None
    if method == "item/completed" and status not in {"completed", "failed"}:
        return None

    record: dict[str, Any] = {
        "kind": "proposal_tool_call",
        "phase": "started" if method == "item/started" else "completed",
        "item_id": item_id,
        "status": status,
    }
    if method == "item/completed":
        record["result"] = _normalize_tool_result(item.get("result"))
        record["tool_error"] = _normalize_tool_error(item.get("result"))
    return record


def _normalize_tool_result(value: Any) -> dict[str, Any] | None:
    if not isinstance(value, Mapping):
        return None
    structured = value.get("structuredContent")
    if not isinstance(structured, Mapping):
        return None
    if structured.get("contract") != PROPOSAL_RESULT_CONTRACT:
        return None

    review = structured.get("review")
    boundary = structured.get("authority_boundary")
    proposal = structured.get("proposal")
    if not all(isinstance(part, Mapping) for part in (review, boundary, proposal)):
        return None

    return {
        "contract": PROPOSAL_RESULT_CONTRACT,
        "status": structured.get("status"),
        "proposal_id": proposal.get("proposal_id"),
        "target": proposal.get("target"),
        "review_action": review.get("action"),
        "review_decision": review.get("decision"),
        "repository_modified": boundary.get("repository_modified"),
    }


def _normalize_tool_error(value: Any) -> dict[str, Any] | None:
    if not isinstance(value, Mapping):
        return None
    structured = value.get("structuredContent")
    if not isinstance(structured, Mapping):
        return None
    error = structured.get("error")
    if not isinstance(error, Mapping):
        return None

    if error.get("contract") != PROPOSAL_ERROR_CONTRACT:
        return None
    error_code = error.get("error_code")
    stage = error.get("stage")
    field_path = error.get("field_path")
    rule = error.get("rule")
    retryable = error.get("retryable")
    if (
        not isinstance(error_code, str)
        or _NORMALIZED_IDENTIFIER.fullmatch(error_code) is None
        or stage != PROPOSAL_TOOL
        or not isinstance(rule, str)
        or _NORMALIZED_IDENTIFIER.fullmatch(rule) is None
        or not isinstance(retryable, bool)
    ):
        return None
    if field_path is not None and (
        not isinstance(field_path, str)
        or _BOUNDED_FIELD_PATH.fullmatch(field_path) is None
    ):
        return None

    return {
        "contract": PROPOSAL_ERROR_CONTRACT,
        "error_code": error_code,
        "stage": stage,
        "field_path": field_path,
        "rule": rule,
        "retryable": retryable,
    }


def _normalize_form(request_id: Any, params: Mapping[str, Any]) -> dict[str, Any] | None:
    if params.get("serverName") != PROPOSAL_SERVER:
        return None
    if params.get("mode") not in {"form", "openai/form"}:
        return None
    message = params.get("message")
    schema = params.get("requestedSchema")
    if not isinstance(message, str) or not isinstance(schema, Mapping):
        return None
    if schema.get("type") != "object" or schema.get("required") != ["decision"]:
        return None

    properties = schema.get("properties")
    if not isinstance(properties, Mapping):
        return None
    decision = properties.get("decision")
    if not isinstance(decision, Mapping):
        return None

    choices = decision.get("enum")
    if not isinstance(choices, list):
        one_of = decision.get("oneOf")
        if not isinstance(one_of, list):
            return None
        choices = [
            option.get("const")
            for option in one_of
            if isinstance(option, Mapping) and isinstance(option.get("const"), str)
        ]
    if choices != ["admit", "request_changes", "reject"]:
        return None
    if not isinstance(request_id, (int, str)) or isinstance(request_id, bool):
        return None

    return {
        "kind": "proposal_form",
        "request_id": request_id,
        "message": message,
        "choices": choices,
    }


def _normalize_terminal(params: Mapping[str, Any]) -> dict[str, Any] | None:
    turn = params.get("turn")
    if not isinstance(turn, Mapping):
        return None
    turn_id = turn.get("id")
    status = turn.get("status")
    if not isinstance(turn_id, str) or not isinstance(status, str):
        return None
    return {"kind": "terminal", "turn_id": turn_id, "status": status}
