from __future__ import annotations

import json
import unittest

from tests.replay_event_normalizer import (
    normalize_replay_event,
    summarize_replay_events,
)


class ReplayEventNormalizerTests(unittest.TestCase):
    def test_tool_name_in_text_or_inventory_is_not_a_call(self) -> None:
        events = (
            {
                "method": "item/completed",
                "params": {
                    "item": {
                        "type": "agentMessage",
                        "id": "message-1",
                        "text": "agentgov_task_proposal_review",
                    }
                },
            },
            {
                "method": "mcpServer/startup/update",
                "params": {
                    "serverName": "agentgov_governance",
                    "tools": ["agentgov_task_proposal_review"],
                },
            },
        )
        self.assertEqual([normalize_replay_event(event) for event in events], [None, None])

    def test_exact_mcp_item_records_started_and_completed_phases(self) -> None:
        started = {
            "method": "item/started",
            "params": {
                "item": {
                    "type": "mcpToolCall",
                    "id": "call-1",
                    "server": "agentgov_governance",
                    "tool": "agentgov_task_proposal_review",
                    "status": "inProgress",
                    "arguments": {"raw_request": "must not survive"},
                }
            },
        }
        completed = {
            "method": "item/completed",
            "params": {
                "item": {
                    "type": "mcpToolCall",
                    "id": "call-1",
                    "server": "agentgov_governance",
                    "tool": "agentgov_task_proposal_review",
                    "status": "completed",
                    "arguments": {"raw_request": "must not survive"},
                    "result": {
                        "content": [{"type": "text", "text": "unbounded content"}],
                        "structuredContent": {
                            "contract": "agentgov.task-proposal-review-result",
                            "status": "request_changes",
                            "proposal": {
                                "proposal_id": "proposal-1",
                                "target": "governance/tasks/proposal-1.json",
                            },
                            "review": {
                                "action": "accept",
                                "decision": "request_changes",
                            },
                            "authority_boundary": {"repository_modified": False},
                            "private_extension": "must not survive",
                        },
                    },
                }
            },
        }

        self.assertEqual(
            normalize_replay_event(started),
            {
                "kind": "proposal_tool_call",
                "phase": "started",
                "item_id": "call-1",
                "status": "inProgress",
            },
        )
        normalized = normalize_replay_event(completed)
        self.assertEqual(normalized["phase"], "completed")
        self.assertEqual(normalized["result"]["review_decision"], "request_changes")
        self.assertIsNone(normalized["tool_error"])
        rendered = json.dumps(normalized)
        self.assertNotIn("must not survive", rendered)
        self.assertNotIn("unbounded content", rendered)
        self.assertNotIn("private_extension", rendered)

    def test_structured_agentgov_error_is_allowlisted_and_resolves_failure(self) -> None:
        call = {
            "method": "item/started",
            "params": {
                "item": {
                    "type": "mcpToolCall",
                    "id": "call-error",
                    "server": "agentgov_governance",
                    "tool": "agentgov_task_proposal_review",
                    "status": "inProgress",
                }
            },
        }
        completed = {
            "method": "item/completed",
            "params": {
                "item": {
                    **call["params"]["item"],
                    "status": "completed",
                    "error": {"message": "private app-server error"},
                    "result": {
                        "content": [{"type": "text", "text": "private tool text"}],
                        "structuredContent": {
                            "error": {
                                "contract": "agentgov.mcp-tool-error",
                                "schema_version": "1.0",
                                "error_code": "task_proposal_invalid_field",
                                "stage": "agentgov_task_proposal_review",
                                "field_path": "scope.include_paths[0]",
                                "rule": "repository_relative",
                                "retryable": True,
                                "private_extension": "must not survive",
                            }
                        },
                    },
                }
            },
        }

        normalized = normalize_replay_event(completed)
        self.assertIsNone(normalized["result"])
        self.assertEqual(
            normalized["tool_error"],
            {
                "contract": "agentgov.mcp-tool-error",
                "error_code": "task_proposal_invalid_field",
                "stage": "agentgov_task_proposal_review",
                "field_path": "scope.include_paths[0]",
                "rule": "repository_relative",
                "retryable": True,
            },
        )
        summary = summarize_replay_events([call, completed])
        self.assertEqual(summary["state"], "call_failed")
        self.assertEqual(summary["proposal_tool_completions"], 1)
        self.assertEqual(summary["proposal_tool_completion_statuses"], ["completed"])
        self.assertEqual(summary["agentgov_tool_errors"], [normalized["tool_error"]])
        rendered = json.dumps(summary)
        self.assertNotIn("private", rendered)
        self.assertNotIn("tool text", rendered)

    def test_completed_unknown_result_is_explicit_and_deduplicated(self) -> None:
        call = {
            "method": "item/started",
            "params": {
                "item": {
                    "type": "mcpToolCall",
                    "id": "call-unknown",
                    "server": "agentgov_governance",
                    "tool": "agentgov_task_proposal_review",
                    "status": "inProgress",
                }
            },
        }
        completed = {
            "method": "item/completed",
            "params": {
                "item": {
                    **call["params"]["item"],
                    "status": "completed",
                    "result": {
                        "content": [{"type": "text", "text": "must not survive"}],
                        "structuredContent": {"unknown": "private"},
                    },
                }
            },
        }

        summary = summarize_replay_events([call, completed, completed])
        self.assertEqual(summary["state"], "completion_unknown")
        self.assertEqual(summary["proposal_tool_calls"], 1)
        self.assertEqual(summary["proposal_tool_completions"], 1)
        self.assertEqual(summary["proposal_tool_completion_statuses"], ["completed"])
        self.assertEqual(summary["agentgov_tool_errors"], [])
        self.assertNotIn("private", json.dumps(summary))

    def test_invalid_or_excess_agentgov_errors_fail_closed_and_remain_bounded(self) -> None:
        events = []
        for index in range(10):
            item_id = f"call-{index}"
            events.extend(
                (
                    {
                        "method": "item/started",
                        "params": {
                            "item": {
                                "type": "mcpToolCall",
                                "id": item_id,
                                "server": "agentgov_governance",
                                "tool": "agentgov_task_proposal_review",
                                "status": "inProgress",
                            }
                        },
                    },
                    {
                        "method": "item/completed",
                        "params": {
                            "item": {
                                "type": "mcpToolCall",
                                "id": item_id,
                                "server": "agentgov_governance",
                                "tool": "agentgov_task_proposal_review",
                                "status": "completed",
                                "result": {
                                    "structuredContent": {
                                        "error": {
                                            "contract": "agentgov.mcp-tool-error",
                                            "error_code": f"bounded_error_{index}",
                                            "stage": "agentgov_task_proposal_review",
                                            "field_path": None,
                                            "rule": "fixture_rule",
                                            "retryable": False,
                                        }
                                    }
                                },
                            }
                        },
                    },
                )
            )

        summary = summarize_replay_events(events)
        self.assertEqual(summary["state"], "call_failed")
        self.assertEqual(summary["proposal_tool_completions"], 10)
        self.assertEqual(len(summary["agentgov_tool_errors"]), 8)
        self.assertTrue(summary["agentgov_tool_errors_truncated"])

        invalid = json.loads(json.dumps(events[1]))
        invalid_error = invalid["params"]["item"]["result"]["structuredContent"]["error"]
        invalid_error["stage"] = "agentgov_alignment_start"
        invalid_error["field_path"] = "C:\\private\\secret.txt"
        normalized = normalize_replay_event(invalid)
        self.assertIsNone(normalized["tool_error"])
        self.assertNotIn("private", json.dumps(normalized))

    def test_other_mcp_calls_are_ignored(self) -> None:
        base = {
            "method": "item/started",
            "params": {
                "item": {
                    "type": "mcpToolCall",
                    "id": "call-1",
                    "server": "agentgov_governance",
                    "tool": "agentgov_alignment_start",
                    "status": "inProgress",
                }
            },
        }
        self.assertIsNone(normalize_replay_event(base))
        base["params"]["item"]["tool"] = "agentgov_task_proposal_review"
        base["params"]["item"]["server"] = "different_server"
        self.assertIsNone(normalize_replay_event(base))

    def test_exact_form_preserves_only_reviewable_fields(self) -> None:
        event = {
            "id": 41,
            "method": "mcpServer/elicitation/request",
            "params": {
                "serverName": "agentgov_governance",
                "threadId": "thread-private",
                "turnId": "turn-private",
                "mode": "form",
                "message": "Exact normalized admission plan",
                "requestedSchema": {
                    "type": "object",
                    "properties": {
                        "decision": {
                            "type": "string",
                            "enum": ["admit", "request_changes", "reject"],
                        }
                    },
                    "required": ["decision"],
                },
                "_meta": {"secret": "must not survive"},
            },
        }
        self.assertEqual(
            normalize_replay_event(event),
            {
                "kind": "proposal_form",
                "request_id": 41,
                "message": "Exact normalized admission plan",
                "choices": ["admit", "request_changes", "reject"],
            },
        )

    def test_wrong_form_shape_fails_closed(self) -> None:
        event = {
            "id": 41,
            "method": "mcpServer/elicitation/request",
            "params": {
                "serverName": "agentgov_governance",
                "mode": "form",
                "message": "Plan",
                "requestedSchema": {
                    "type": "object",
                    "properties": {
                        "decision": {"type": "string", "enum": ["admit", "reject"]}
                    },
                    "required": ["decision"],
                },
            },
        }
        self.assertIsNone(normalize_replay_event(event))

    def test_turn_terminal_drops_messages_and_usage(self) -> None:
        event = {
            "method": "turn/completed",
            "params": {
                "threadId": "thread-private",
                "turn": {
                    "id": "turn-1",
                    "status": "completed",
                    "items": [{"type": "agentMessage", "text": "must not survive"}],
                    "usage": {"inputTokens": 123},
                },
            },
        }
        self.assertEqual(
            normalize_replay_event(event),
            {"kind": "terminal", "turn_id": "turn-1", "status": "completed"},
        )

    def test_malformed_events_are_ignored(self) -> None:
        for event in ({}, {"method": 1, "params": {}}, {"method": "item/started"}):
            self.assertIsNone(normalize_replay_event(event))

    def test_summary_distinguishes_absent_started_failed_form_and_completed(self) -> None:
        unrelated = {
            "method": "item/completed",
            "params": {
                "item": {
                    "type": "agentMessage",
                    "id": "message-1",
                    "text": "agentgov_task_proposal_review",
                }
            },
        }
        self.assertEqual(summarize_replay_events([unrelated])["state"], "not_called")

        call = {
            "method": "item/started",
            "params": {
                "item": {
                    "type": "mcpToolCall",
                    "id": "call-1",
                    "server": "agentgov_governance",
                    "tool": "agentgov_task_proposal_review",
                    "status": "inProgress",
                }
            },
        }
        self.assertEqual(summarize_replay_events([call])["state"], "call_started")

        failed = {
            "method": "item/completed",
            "params": {
                "item": {
                    **call["params"]["item"],
                    "status": "failed",
                    "error": {"message": "private failure detail"},
                    "result": None,
                }
            },
        }
        failed_summary = summarize_replay_events([call, failed])
        self.assertEqual(failed_summary["state"], "call_failed")
        self.assertEqual(failed_summary["proposal_tool_calls"], 1)
        self.assertNotIn("private", json.dumps(failed_summary))

        form = {
            "id": "form-1",
            "method": "mcpServer/elicitation/request",
            "params": {
                "serverName": "agentgov_governance",
                "mode": "form",
                "message": "Exact normalized admission plan",
                "requestedSchema": {
                    "type": "object",
                    "properties": {
                        "decision": {
                            "type": "string",
                            "enum": ["admit", "request_changes", "reject"],
                        }
                    },
                    "required": ["decision"],
                },
            },
        }
        self.assertEqual(
            summarize_replay_events([call, form])["state"], "form_presented"
        )

        completed = {
            "method": "item/completed",
            "params": {
                "item": {
                    **call["params"]["item"],
                    "status": "completed",
                    "result": {
                        "content": [],
                        "structuredContent": {
                            "contract": "agentgov.task-proposal-review-result",
                            "status": "rejected",
                            "proposal": {
                                "proposal_id": "proposal-1",
                                "target": "governance/tasks/proposal-1.json",
                            },
                            "review": {"action": "accept", "decision": "reject"},
                            "authority_boundary": {"repository_modified": False},
                        },
                    },
                }
            },
        }
        terminal = {
            "method": "turn/completed",
            "params": {
                "turn": {"id": "turn-1", "status": "completed", "items": []}
            },
        }
        summary = summarize_replay_events([call, form, completed, terminal])
        self.assertEqual(
            summary,
            {
                "state": "completed",
                "proposal_tool_calls": 1,
                "proposal_tool_completions": 1,
                "proposal_tool_completion_statuses": ["completed"],
                "agentgov_tool_errors": [],
                "agentgov_tool_errors_truncated": False,
                "forms_presented": 1,
                "terminal_status": "completed",
            },
        )


if __name__ == "__main__":
    unittest.main()
