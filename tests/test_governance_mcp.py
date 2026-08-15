from __future__ import annotations

import contextlib
import io
import json
import subprocess
import sys
import tomllib
import unittest
from dataclasses import asdict
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from agentgov.cli import EXIT_PASS, main
from agentgov.codex_hooks import CodexHooksAction
from agentgov.codex_mcp import (
    CODEX_MCP_ADAPTER_ID,
    CODEX_MCP_CONFIG_PATH,
    CODEX_MCP_PROVIDER_ID,
    apply_codex_mcp_plan,
    plan_codex_mcp_integration,
    render_codex_mcp_config,
)
from agentgov.governance_mcp import (
    MCP_BASE_TOOL_NAMES,
    MCP_DRIFT_REVIEW_TOOL_NAME,
    MCP_NATIVE_ACCOUNTABLE_OWNER,
    MCP_PROTOCOL_VERSION,
    MCP_SERVER_VERSION,
    MCP_SERVER_INSTRUCTIONS,
    MCP_TASK_PROPOSAL_TOOL_NAME,
    MCP_TOOL_NAMES,
    GovernanceMcpAdapter,
    GovernanceMcpError,
    GovernanceMcpServer,
    build_active_host_self_review_provider,
    governance_mcp_tools,
)
from agentgov.development_monitor import MonitorPolicyError
from agentgov.drift_review import build_drift_review_status
from agentgov.human_decision import canonical_document_digest
from agentgov.reference_alignment_adapter import (
    ReferenceAlignmentAdapter,
    ReferenceAlignmentAdapterError,
)
from tests.test_clarification_dialogue import empty_patch, question, resolutions


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = "docs/product-requirements-automatic-governance.md"


def adapter(
    host: str = "fixture.codex-mcp",
    repository: Path | None = None,
) -> GovernanceMcpAdapter:
    provider = build_active_host_self_review_provider(
        adapter_id=host,
        provider_id=host + "-current-agent",
    )
    return GovernanceMcpAdapter(
        adapter_id=host,
        provider=provider,
        repository=repository,
    )


def task_proposal_arguments(task_id: str = "native-review-fixture") -> dict:
    return {
        "task_id": task_id,
        "title": "Review one native Codex task proposal",
        "requirement_summary": (
            "Prove that Codex can review and explicitly admit one exact bounded task."
        ),
        "scope": {
            "include_paths": ["src/agentgov"],
            "exclude_paths": ["release"],
        },
        "acceptance_signals": ["Only exact native admission creates the task."],
        "validation_commands": ["python -m unittest discover -s tests -v"],
        "risk_items": ["Native form support depends on negotiated client capability."],
        "assumptions": ["The current Codex client supports form elicitation."],
        "unknowns": [],
    }


def drift_review_arguments() -> dict:
    return {
        "candidate_outcome": "no_drift_evidence",
        "observations": [
            {
                "dimension": "requirement",
                "finding": "The implemented reminder matches the admitted development-time journey.",
            },
            {
                "dimension": "architecture",
                "finding": "The foreground and native-form boundaries remain explicit and model-free in Core.",
            },
            {
                "dimension": "functionality",
                "finding": "The shared cadence, Monitor state, and create-only records agree.",
            },
        ],
        "evidence_refs": [
            "docs/product-requirements-automatic-governance.md",
            "docs/adr/0013-make-automatic-governance-and-dashboard-primary.md",
        ],
    }


def start_arguments() -> dict:
    return {
        "subject_type": "active_task",
        "subject_id": "native-mcp-self-review",
        "center": {
            "outcome": "Use the current Coding Agent for governed self-review.",
            "why_now": "The transport exists but native hosts do not own its records.",
            "success_signals": ["The user writes no protocol JSON."],
            "constraints": ["Core must remain model-free."],
            "non_goals": ["Do not add an independent Reviewer."],
        },
        "drift": {
            "kind": "architecture",
            "semantics": "advisory",
            "observation": "Command hooks cannot directly perform semantic inference.",
            "evidence_refs": ["docs/codex-hooks-adapter.md"],
            "impact": "Pretending a command hook is an Agent would overstate the integration.",
        },
        "assumptions": ["The host supports model-controlled MCP tools."],
        "unknowns": [mcp_question("Should the foreground MCP Adapter own the normalized journey?")],
        "candidate_resolutions": [],
        "recommended_resolution_id": None,
    }


def mcp_question(text: str) -> dict:
    value = question("a", text)
    value.pop("question_id")
    return value


def prompt_binding(response: dict, key: str) -> dict:
    prompt = response["response"][key]
    return {"prompt_id": prompt["prompt_id"], "digest": canonical_document_digest(prompt)}


def ready_journey(active: GovernanceMcpAdapter) -> dict:
    started = active.call_tool(MCP_TOOL_NAMES[0], start_arguments())
    return active.call_tool(
        MCP_TOOL_NAMES[1],
        {
            "journey_handle": started["journey_handle"],
            "prompt": prompt_binding(started, "clarification_prompt"),
            "answer_summary": "The human kept the normalized center.",
            "center_patch": empty_patch(),
            "new_questions": [],
            "candidate_resolutions": resolutions(),
            "recommended_resolution_id": "return_to_center",
            "ready_requested": True,
        },
    )


def review_observation() -> dict:
    return {
        "kind": "architecture",
        "summary": "The Adapter validates normalized post-selection input before Core state advances.",
        "evidence_refs": [EVIDENCE],
        "assumptions": ["The foreground journey remains in one process."],
        "unknowns": ["Live host behavior remains unproven."],
        "recommended_question": "Should a later requirement run a fresh host replay?",
    }


def full_journey(active: GovernanceMcpAdapter) -> tuple[dict, dict]:
    started = active.call_tool(MCP_TOOL_NAMES[0], start_arguments())
    handle = started["journey_handle"]
    ready = active.call_tool(
        MCP_TOOL_NAMES[1],
        {
            "journey_handle": handle,
            "prompt": prompt_binding(started, "clarification_prompt"),
            "answer_summary": "The user confirmed that MCP should own only normalized foreground state.",
            "center_patch": empty_patch(),
            "new_questions": [],
            "candidate_resolutions": resolutions(),
            "recommended_resolution_id": "return_to_center",
            "ready_requested": True,
        },
    )
    resolved = active.call_tool(
        MCP_TOOL_NAMES[2],
        {
            "journey_handle": handle,
            "decision_prompt": prompt_binding(ready, "decision_prompt"),
            "selected_option_id": "return_to_center",
        },
    )
    requested = active.call_tool(
        MCP_TOOL_NAMES[3],
        {
            "journey_handle": handle,
            "reason_codes": ["architecture_drift"],
            "allowed_evidence_refs": [EVIDENCE],
        },
    )
    request = requested["response"]["materialization_request"]
    completed = active.call_tool(
        MCP_TOOL_NAMES[4],
        {
            "journey_handle": handle,
            "request": {"request_id": request["request_id"], "digest": request["request_digest"]},
            "observations": [
                {
                    "kind": "architecture",
                    "summary": "The MCP boundary reuses the current Agent without moving inference into Core.",
                    "evidence_refs": [EVIDENCE],
                    "assumptions": ["The MCP host preserves the journey handle."],
                    "unknowns": ["Native tool selection still requires a host rehearsal."],
                    "recommended_question": "Should the next host rehearsal use this exact config?",
                }
            ],
        },
    )
    return resolved, completed


def rpc(request_id: int, method: str, params: dict | None = None) -> dict:
    value = {"jsonrpc": "2.0", "id": request_id, "method": method}
    if params is not None:
        value["params"] = params
    return value


def create_git_repository(root: Path) -> None:
    subprocess.run(("git", "init", "-q", str(root)), check=True)


def create_drift_review_repository(root: Path) -> None:
    create_git_repository(root)
    (root / "docs" / "adr").mkdir(parents=True)
    (root / "docs" / "product-requirements-automatic-governance.md").write_text(
        "# Requirements\n\nPeriodic drift review remains advisory.\n",
        encoding="utf-8",
    )
    (root / "docs" / "adr" / "0013-make-automatic-governance-and-dashboard-primary.md").write_text(
        "# ADR-0013\n\nUse an explicit foreground host interaction.\n",
        encoding="utf-8",
    )


def run_cli(stdin_text: str, *args: str) -> tuple[int, str, str]:
    stdout = io.StringIO()
    stderr = io.StringIO()
    with (
        patch.object(sys, "stdin", io.StringIO(stdin_text)),
        contextlib.redirect_stdout(stdout),
        contextlib.redirect_stderr(stderr),
    ):
        code = main(list(args))
    return code, stdout.getvalue(), stderr.getvalue()


class GovernanceMcpProtocolTests(unittest.TestCase):
    def test_current_discovery_legacy_initialize_and_tool_list_are_deterministic(self) -> None:
        server = GovernanceMcpServer(adapter())
        discovered = server.dispatch(rpc(1, "server/discover", {"_meta": {}}))
        initialized = server.dispatch(
            rpc(2, "initialize", {"protocolVersion": "2025-11-25", "capabilities": {"elicitation": {"form": {}}}, "clientInfo": {"name": "fixture", "version": "1"}})
        )
        listed = server.dispatch(rpc(3, "tools/list", {}))

        self.assertEqual(discovered["result"]["supportedVersions"][0], MCP_PROTOCOL_VERSION)
        self.assertEqual(MCP_SERVER_VERSION, "1.5.0")
        self.assertEqual(initialized["result"]["serverInfo"]["version"], MCP_SERVER_VERSION)
        self.assertEqual(initialized["result"]["protocolVersion"], "2025-11-25")
        self.assertEqual(
            tuple(item["name"] for item in listed["result"]["tools"]),
            MCP_TOOL_NAMES,
        )
        self.assertEqual(governance_mcp_tools(), governance_mcp_tools())
        self.assertIn("Never send raw prompts", MCP_SERVER_INSTRUCTIONS)
        self.assertIn("without waiting for the user to name them", MCP_SERVER_INSTRUCTIONS)
        self.assertIn("when asked to choose what to build", MCP_SERVER_INSTRUCTIONS)
        self.assertIn("never select it for them", MCP_SERVER_INSTRUCTIONS)
        self.assertIn(
            "After implementing and validating any repository-changing task, run a distinct advisory review",
            MCP_SERVER_INSTRUCTIONS,
        )
        self.assertIn("do not fabricate a journey handle", MCP_SERVER_INSTRUCTIONS)
        self.assertIn("do not silently continue", MCP_SERVER_INSTRUCTIONS)
        self.assertIn("governance/tasks/*.json record", MCP_SERVER_INSTRUCTIONS)
        self.assertIn("A direct chat request, approval, authorization", MCP_SERVER_INSTRUCTIONS)
        self.assertIn(
            "unrelated, measurement-only, or differently scoped",
            MCP_SERVER_INSTRUCTIONS,
        )
        self.assertIn("Do not use proposal review for read-only work", MCP_SERVER_INSTRUCTIONS)
        self.assertIn("human alone", MCP_SERVER_INSTRUCTIONS)
        descriptions = {tool["name"]: tool["description"] for tool in listed["result"]["tools"]}
        self.assertIn("multiple reasonable directions", descriptions[MCP_TOOL_NAMES[0]])
        self.assertIn("human must select", descriptions[MCP_TOOL_NAMES[0]])
        self.assertIn("before completion handoff", descriptions[MCP_TOOL_NAMES[3]])
        self.assertIn("distinct advisory", descriptions[MCP_TOOL_NAMES[3]])
        self.assertIn(
            "no readable, validated governance/tasks/*.json record",
            descriptions[MCP_TASK_PROPOSAL_TOOL_NAME],
        )
        self.assertIn(
            "read-only work does not need proposal review",
            descriptions[MCP_TASK_PROPOSAL_TOOL_NAME],
        )
        self.assertIn(
            "Never supply or infer the human decision",
            descriptions[MCP_DRIFT_REVIEW_TOOL_NAME],
        )
        for index, tool in enumerate(listed["result"]["tools"]):
            self.assertFalse(tool["inputSchema"]["additionalProperties"])
            self.assertEqual(tool["annotations"]["readOnlyHint"], index < 5)
            self.assertFalse(tool["annotations"]["destructiveHint"])
        start_question = listed["result"]["tools"][0]["inputSchema"]["properties"]["unknowns"]["items"]
        update_question = listed["result"]["tools"][1]["inputSchema"]["properties"]["new_questions"]["items"]
        self.assertNotIn("question_id", start_question["properties"])
        self.assertNotIn("question_id", update_question["properties"])
        review_start = listed["result"]["tools"][3]["inputSchema"]["properties"]
        self.assertEqual(review_start["reason_codes"]["maxItems"], 50)
        self.assertEqual(review_start["reason_codes"]["items"]["maxLength"], 120)
        self.assertEqual(
            review_start["reason_codes"]["items"]["pattern"],
            "^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$",
        )
        self.assertEqual(review_start["allowed_evidence_refs"]["maxItems"], 20)
        self.assertEqual(review_start["allowed_evidence_refs"]["items"]["maxLength"], 240)
        review_complete = listed["result"]["tools"][4]["inputSchema"]["properties"]
        observation = review_complete["observations"]["items"]["properties"]
        self.assertTrue(review_complete["observations"]["uniqueItems"])
        self.assertEqual(observation["assumptions"]["maxItems"], 20)
        self.assertEqual(observation["unknowns"]["maxItems"], 20)
        proposal = listed["result"]["tools"][5]["inputSchema"]
        self.assertNotIn("raw_prompt", proposal["properties"])
        self.assertNotIn("decision", proposal["properties"])
        self.assertNotIn("repository", proposal["properties"])
        self.assertNotIn("owner", proposal["properties"])
        self.assertNotIn("owner", proposal["required"])
        self.assertIn(
            "canonical human owner role",
            descriptions[MCP_TASK_PROPOSAL_TOOL_NAME],
        )
        self.assertEqual(
            proposal["properties"]["scope"]["properties"]["include_paths"]["items"]["maxLength"],
            400,
        )
        drift = listed["result"]["tools"][6]["inputSchema"]
        self.assertNotIn("decision", drift["properties"])
        self.assertNotIn("repository", drift["properties"])
        self.assertEqual(drift["properties"]["observations"]["minItems"], 3)
        self.assertEqual(drift["properties"]["observations"]["maxItems"], 3)

    def test_legacy_client_cannot_discover_or_call_native_proposal_review(self) -> None:
        server = GovernanceMcpServer(adapter())
        server.dispatch(
            rpc(
                1,
                "initialize",
                {
                    "protocolVersion": "2025-11-25",
                    "capabilities": {},
                    "clientInfo": {"name": "legacy", "version": "1"},
                },
            )
        )
        listed = server.dispatch(rpc(2, "tools/list", {}))
        self.assertEqual(
            tuple(item["name"] for item in listed["result"]["tools"]),
            MCP_BASE_TOOL_NAMES,
        )
        called = server.dispatch(
            rpc(
                3,
                "tools/call",
                {"name": MCP_TOOL_NAMES[5], "arguments": task_proposal_arguments()},
            )
        )["result"]
        self.assertTrue(called["isError"])
        self.assertEqual(
            called["structuredContent"]["error"]["error_code"],
            "task_proposal_elicitation_unsupported",
        )
        drift_called = server.dispatch(
            rpc(
                4,
                "tools/call",
                {"name": MCP_DRIFT_REVIEW_TOOL_NAME, "arguments": drift_review_arguments()},
            )
        )["result"]
        self.assertTrue(drift_called["isError"])
        self.assertEqual(
            drift_called["structuredContent"]["error"]["error_code"],
            "drift_review_elicitation_unsupported",
        )

    def test_native_proposal_review_admits_only_exact_accept_decision(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "governance" / "tasks").mkdir(parents=True)
            server = GovernanceMcpServer(
                adapter(repository=root), request_id_factory=lambda: "elc-fixture"
            )
            stream = "\n".join(
                (
                    json.dumps(
                        rpc(
                            1,
                            "initialize",
                            {
                                "protocolVersion": "2025-11-25",
                                "capabilities": {"elicitation": {"form": {}}},
                                "clientInfo": {"name": "codex", "version": "fixture"},
                            },
                        )
                    ),
                    json.dumps(
                        rpc(
                            2,
                            "tools/call",
                            {
                                "name": MCP_TOOL_NAMES[5],
                                "arguments": task_proposal_arguments(),
                            },
                        )
                    ),
                    json.dumps(
                        {
                            "jsonrpc": "2.0",
                            "id": "elc-fixture",
                            "result": {
                                "action": "accept",
                                "content": {"decision": "admit"},
                                "clientExtension": {"private": "ignored"},
                            },
                        }
                    ),
                )
            ) + "\n"
            output = io.StringIO()
            self.assertEqual(server.serve(io.StringIO(stream), output), 0)
            messages = [json.loads(line) for line in output.getvalue().splitlines()]

            self.assertEqual(messages[1]["method"], "elicitation/create")
            self.assertEqual(messages[1]["params"]["mode"], "form")
            self.assertIn("task_document", messages[1]["params"]["message"])
            requested_schema = messages[1]["params"]["requestedSchema"]
            self.assertEqual(set(requested_schema), {"type", "properties", "required"})
            self.assertEqual(requested_schema["required"], ["decision"])
            result = messages[2]["result"]["structuredContent"]
            self.assertEqual(
                result["contract"], "agentgov.task-proposal-review-result"
            )
            self.assertEqual(result["status"], "admitted")
            self.assertTrue(result["authority_boundary"]["repository_modified"])
            self.assertNotIn("clientExtension", json.dumps(result))
            self.assertNotIn("private", json.dumps(result))
            target = root / "governance" / "tasks" / "native-review-fixture.json"
            self.assertTrue(target.is_file())
            document = json.loads(target.read_text(encoding="utf-8"))
            self.assertEqual(document["decision"]["state"], "admitted")
            self.assertEqual(document["owner"], MCP_NATIVE_ACCOUNTABLE_OWNER)
            self.assertEqual(
                document["decision"]["decided_by"], MCP_NATIVE_ACCOUNTABLE_OWNER
            )

    def test_native_proposal_rejects_agent_supplied_owner_before_elicitation(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "governance" / "tasks").mkdir(parents=True)
            server = GovernanceMcpServer(
                adapter(repository=root), request_id_factory=lambda: "elc-unused"
            )
            arguments = task_proposal_arguments("native-agent-owner")
            arguments["owner"] = "current-agent"
            stream = "\n".join(
                (
                    json.dumps(
                        rpc(
                            1,
                            "initialize",
                            {
                                "protocolVersion": "2025-11-25",
                                "capabilities": {"elicitation": {"form": {}}},
                                "clientInfo": {"name": "codex", "version": "fixture"},
                            },
                        )
                    ),
                    json.dumps(
                        rpc(
                            2,
                            "tools/call",
                            {
                                "name": MCP_TASK_PROPOSAL_TOOL_NAME,
                                "arguments": arguments,
                            },
                        )
                    ),
                )
            ) + "\n"
            output = io.StringIO()

            self.assertEqual(server.serve(io.StringIO(stream), output), 0)
            messages = [json.loads(line) for line in output.getvalue().splitlines()]
            self.assertEqual(len(messages), 2)
            result = messages[1]["result"]
            self.assertTrue(result["isError"])
            error = result["structuredContent"]["error"]
            self.assertEqual(error["error_code"], "tool_arguments_invalid")
            self.assertEqual(error["stage"], MCP_TASK_PROPOSAL_TOOL_NAME)
            self.assertEqual(error["field_path"], "$")
            self.assertEqual(error["rule"], "exact_fields")
            self.assertTrue(error["retryable"])
            self.assertFalse(
                (root / "governance" / "tasks" / "native-agent-owner.json").exists()
            )

    def test_native_proposal_non_admission_and_stale_plan_are_zero_write(self) -> None:
        outcomes = (
            {"action": "accept", "content": {"decision": "request_changes"}},
            {"action": "accept", "content": {"decision": "reject"}},
            {"action": "decline"},
            {"action": "cancel"},
        )
        for index, elicitation_result in enumerate(outcomes):
            with self.subTest(elicitation_result=elicitation_result), TemporaryDirectory() as temp_dir:
                root = Path(temp_dir)
                (root / "governance" / "tasks").mkdir(parents=True)
                task_id = f"native-no-write-{index}"
                active = adapter(repository=root)
                preparation = active.prepare_task_proposal(task_proposal_arguments(task_id))
                result = active.complete_task_proposal_review(
                    preparation, elicitation_result
                )
                self.assertFalse(result["authority_boundary"]["repository_modified"])
                self.assertFalse((root / preparation.plan.target).exists())

        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "governance" / "tasks").mkdir(parents=True)
            active = adapter(repository=root)
            preparation = active.prepare_task_proposal(
                task_proposal_arguments("native-race-fixture")
            )
            target = root / preparation.plan.target
            target.write_text("existing\n", encoding="utf-8")
            with self.assertRaises(GovernanceMcpError) as caught:
                active.complete_task_proposal_review(
                    preparation,
                    {"action": "accept", "content": {"decision": "admit"}},
                )
            self.assertEqual(caught.exception.code, "task_proposal_plan_stale")
            self.assertEqual(target.read_text(encoding="utf-8"), "existing\n")

        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "governance" / "tasks").mkdir(parents=True)
            active = adapter(repository=root)
            preparation = active.prepare_task_proposal(
                task_proposal_arguments("native-malformed-fixture")
            )
            with self.assertRaises(GovernanceMcpError) as caught:
                active.complete_task_proposal_review(
                    preparation,
                    {
                        "action": "accept",
                        "content": {"decision": "admit", "extra": True},
                    },
                )
            self.assertEqual(caught.exception.code, "task_proposal_review_invalid")
            self.assertFalse((root / preparation.plan.target).exists())

            with patch(
                "agentgov.governance_mcp.apply_task_admission_plan",
                side_effect=OSError(r"C:\private-host\task.json"),
            ):
                with self.assertRaises(GovernanceMcpError) as os_error:
                    active.complete_task_proposal_review(
                        preparation,
                        {"action": "accept", "content": {"decision": "admit"}},
                    )
            self.assertEqual(os_error.exception.code, "task_proposal_plan_stale")
            self.assertNotIn("private-host", str(os_error.exception))
            self.assertFalse((root / preparation.plan.target).exists())

    def test_native_proposal_interruption_and_private_invalid_input_are_zero_write(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "governance" / "tasks").mkdir(parents=True)
            server = GovernanceMcpServer(
                adapter(repository=root), request_id_factory=lambda: "elc-interrupted"
            )
            initialize = rpc(
                1,
                "initialize",
                {
                    "protocolVersion": "2025-11-25",
                    "capabilities": {"elicitation": {}},
                    "clientInfo": {"name": "codex", "version": "fixture"},
                },
            )
            call = rpc(
                2,
                "tools/call",
                {
                    "name": MCP_TOOL_NAMES[5],
                    "arguments": task_proposal_arguments("native-interrupted"),
                },
            )
            output = io.StringIO()
            server.serve(
                io.StringIO(json.dumps(initialize) + "\n" + json.dumps(call) + "\n"),
                output,
            )
            messages = [json.loads(line) for line in output.getvalue().splitlines()]
            self.assertEqual(messages[1]["method"], "elicitation/create")
            self.assertTrue(messages[2]["result"]["isError"])
            self.assertEqual(
                messages[2]["result"]["structuredContent"]["error"]["error_code"],
                "task_proposal_elicitation_interrupted",
            )
            self.assertFalse((root / "governance" / "tasks" / "native-interrupted.json").exists())

            private_value = "password=do-not-echo"
            invalid_arguments = task_proposal_arguments("native-private")
            invalid_arguments["requirement_summary"] = private_value
            second_server = GovernanceMcpServer(
                adapter(repository=root), request_id_factory=lambda: "elc-unused"
            )
            invalid_stream = "\n".join(
                (
                    json.dumps(initialize),
                    json.dumps(
                        rpc(
                            3,
                            "tools/call",
                            {
                                "name": MCP_TOOL_NAMES[5],
                                "arguments": invalid_arguments,
                            },
                        )
                    ),
                )
            ) + "\n"
            invalid_output = io.StringIO()
            second_server.serve(io.StringIO(invalid_stream), invalid_output)
            serialized = invalid_output.getvalue()
            self.assertNotIn(private_value, serialized)
            self.assertNotIn("elicitation/create", serialized)
            invalid_messages = [json.loads(line) for line in serialized.splitlines()]
            diagnostic = invalid_messages[-1]["result"]["structuredContent"]["error"]
            self.assertEqual(diagnostic["rule"], "privacy_boundary")

    def test_native_drift_review_records_exact_candidate_and_refreshes_monitor(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            create_drift_review_repository(root)
            server = GovernanceMcpServer(
                adapter(repository=root), request_id_factory=lambda: "elc-drift-fixture"
            )
            stream = "\n".join(
                (
                    json.dumps(
                        rpc(
                            1,
                            "initialize",
                            {
                                "protocolVersion": "2025-11-25",
                                "capabilities": {"elicitation": {"form": {}}},
                                "clientInfo": {"name": "codex", "version": "fixture"},
                            },
                        )
                    ),
                    json.dumps(
                        rpc(
                            2,
                            "tools/call",
                            {
                                "name": MCP_DRIFT_REVIEW_TOOL_NAME,
                                "arguments": drift_review_arguments(),
                            },
                        )
                    ),
                    json.dumps(
                        {
                            "jsonrpc": "2.0",
                            "id": "elc-drift-fixture",
                            "result": {
                                "action": "accept",
                                "content": {"decision": "record_candidate"},
                                "clientExtension": {"private": "ignored"},
                            },
                        }
                    ),
                )
            ) + "\n"
            output = io.StringIO()

            self.assertEqual(server.serve(io.StringIO(stream), output), 0)
            messages = [json.loads(line) for line in output.getvalue().splitlines()]

            self.assertEqual(messages[1]["method"], "elicitation/create")
            self.assertEqual(messages[1]["params"]["mode"], "form")
            self.assertIn("Candidate outcome: no_drift_evidence", messages[1]["params"]["message"])
            self.assertIn("Snooze interval: 7 days", messages[1]["params"]["message"])
            self.assertIn("requirement:", messages[1]["params"]["message"])
            choices = messages[1]["params"]["requestedSchema"]["properties"]["decision"]["oneOf"]
            self.assertEqual(
                [item["const"] for item in choices],
                ["record_candidate", "snooze", "no_record"],
            )
            result = messages[2]["result"]["structuredContent"]
            self.assertEqual(result["contract"], "agentgov.drift-review-form-result")
            self.assertEqual(result["status"], "recorded")
            self.assertEqual(result["candidate"]["outcome"], "no_drift_evidence")
            self.assertEqual(result["drift_review"]["state"], "not_due")
            self.assertEqual(result["monitor"]["status"], "refreshed")
            self.assertTrue(result["authority_boundary"]["review_record_created"])
            self.assertFalse(result["authority_boundary"]["decides_semantic_drift"])
            self.assertNotIn("clientExtension", json.dumps(result))
            records = list((root / "governance" / "drift-reviews").glob("*.json"))
            self.assertEqual(len(records), 1)
            record = json.loads(records[0].read_text(encoding="utf-8"))
            self.assertEqual(record["outcome"], "no_drift_evidence")
            self.assertTrue((root / ".agentgov" / "dashboard.html").is_file())

    def test_native_drift_review_no_write_snooze_and_stale_retry_are_bounded(self) -> None:
        for response, expected in (
            ({"action": "accept", "content": {"decision": "no_record"}}, "not_recorded"),
            ({"action": "decline"}, "declined"),
            ({"action": "cancel"}, "cancelled"),
        ):
            with self.subTest(response=response), TemporaryDirectory() as temp_dir:
                root = Path(temp_dir)
                create_drift_review_repository(root)
                active = adapter(repository=root)
                preparation = active.prepare_drift_review(drift_review_arguments())
                result = active.complete_drift_review(preparation, response)
                self.assertEqual(result["status"], expected)
                self.assertFalse(result["authority_boundary"]["repository_modified"])
                self.assertFalse((root / "governance" / "drift-reviews").exists())

        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            create_drift_review_repository(root)
            active = adapter(repository=root)
            preparation = active.prepare_drift_review(drift_review_arguments())
            snoozed = active.complete_drift_review(
                preparation,
                {"action": "accept", "content": {"decision": "snooze"}},
            )
            self.assertEqual(snoozed["status"], "snoozed")
            self.assertEqual(snoozed["drift_review"]["state"], "not_due")
            record_count = len(list((root / "governance" / "drift-reviews").glob("*.json")))
            with self.assertRaises(GovernanceMcpError) as stale:
                active.complete_drift_review(
                    preparation,
                    {"action": "accept", "content": {"decision": "record_candidate"}},
                )
            self.assertEqual(stale.exception.code, "drift_review_state_stale")
            self.assertEqual(
                len(list((root / "governance" / "drift-reviews").glob("*.json"))),
                record_count,
            )

    def test_native_drift_review_invalid_agent_input_is_zero_write(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            create_drift_review_repository(root)
            active = adapter(repository=root)
            invalid_values = []
            duplicate = drift_review_arguments()
            duplicate["observations"][2]["dimension"] = "architecture"
            invalid_values.append(duplicate)
            missing = drift_review_arguments()
            missing["evidence_refs"] = ["docs/missing.md"]
            invalid_values.append(missing)
            private = drift_review_arguments()
            private["observations"][0]["finding"] = "password=do-not-echo"
            invalid_values.append(private)

            for value in invalid_values:
                with self.subTest(value=value), self.assertRaises(GovernanceMcpError):
                    active.prepare_drift_review(value)
            self.assertFalse((root / "governance" / "drift-reviews").exists())

    def test_native_drift_review_monitor_failure_preserves_recorded_success(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            create_drift_review_repository(root)
            active = adapter(repository=root)
            preparation = active.prepare_drift_review(drift_review_arguments())
            with patch(
                "agentgov.governance_mcp.write_development_monitor",
                side_effect=MonitorPolicyError("private path detail"),
            ):
                result = active.complete_drift_review(
                    preparation,
                    {"action": "accept", "content": {"decision": "record_candidate"}},
                )

            self.assertEqual(result["status"], "recorded")
            self.assertEqual(result["monitor"]["status"], "refresh_failed")
            self.assertEqual(
                result["monitor"]["reason_code"], "local_monitor_refresh_failed"
            )
            self.assertNotIn("private path detail", json.dumps(result))
            self.assertEqual(build_drift_review_status(root).state, "not_due")
            self.assertEqual(
                len(list((root / "governance" / "drift-reviews").glob("*.json"))),
                1,
            )

    def test_repository_guidance_matches_mcp_selection_boundaries(self) -> None:
        guidance = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("the human does not need to name the tools", guidance)
        self.assertIn("asks the Agent to choose what to build", guidance)
        self.assertIn("Do not choose that direction for them", guidance)
        self.assertIn("fully specified low-risk change", guidance)
        self.assertIn("A direct\n  chat request, approval, authorization", guidance)
        self.assertIn("any repository-changing task", guidance)
        self.assertIn("do not fabricate a journey handle", guidance)
        self.assertIn("agentgov_self_review_start", guidance)
        self.assertIn("agentgov_self_review_complete", guidance)
        self.assertIn("agentgov_drift_review_record", guidance)
        self.assertIn("never supply or infer that choice", guidance)
        self.assertIn("remain fail-closed", guidance)

    def test_codex_and_claude_hosts_complete_the_same_normalized_tool_journey(self) -> None:
        for host in ("fixture.codex-mcp", "fixture.claude-code-mcp"):
            with self.subTest(host=host):
                host_adapter = adapter(host)
                resolved, completed = full_journey(host_adapter)
                self.assertEqual(resolved["response"]["status"], "resolved")
                run = completed["response"]["run"]
                self.assertEqual(completed["response"]["status"], "completed")
                self.assertEqual(run["result"]["semantics"], "advisory")
                self.assertEqual(run["execution"]["agentgov_model_calls"], 0)
                self.assertEqual(run["execution"]["agentgov_network_calls"], 0)
                self.assertTrue(all(value is False for value in completed["authority_boundary"].values()))
                with self.assertRaisesRegex(ValueError, "already started"):
                    host_adapter.call_tool(
                        MCP_TOOL_NAMES[3],
                        {
                            "journey_handle": resolved["journey_handle"],
                            "reason_codes": ["architecture_drift"],
                            "allowed_evidence_refs": [EVIDENCE],
                        },
                    )

    def test_stale_prompt_is_atomic_and_valid_retry_succeeds(self) -> None:
        active = adapter()
        started = active.call_tool(MCP_TOOL_NAMES[0], start_arguments())
        other = active.call_tool(MCP_TOOL_NAMES[0], start_arguments())
        invalid = {
            "journey_handle": other["journey_handle"],
            "prompt": prompt_binding(started, "clarification_prompt"),
            "answer_summary": "A stale prompt must not advance state.",
            "center_patch": empty_patch(),
            "new_questions": [],
            "candidate_resolutions": resolutions(),
            "recommended_resolution_id": "return_to_center",
            "ready_requested": True,
        }
        invalid["prompt"]["digest"] = "sha256:" + "0" * 64
        with self.assertRaisesRegex(ValueError, "stale"):
            active.call_tool(MCP_TOOL_NAMES[1], invalid)
        valid = dict(invalid)
        valid["prompt"] = prompt_binding(other, "clarification_prompt")
        ready = active.call_tool(MCP_TOOL_NAMES[1], valid)
        self.assertEqual(ready["response"]["status"], "ready_for_decision")

    def test_resolve_repairable_failures_are_structured_atomic_and_retryable(self) -> None:
        active = adapter()
        ready = ready_journey(active)
        valid = {
            "journey_handle": ready["journey_handle"],
            "decision_prompt": prompt_binding(ready, "decision_prompt"),
            "selected_option_id": "return_to_center",
        }
        cases = (
            ("binding shape", {**valid, "decision_prompt": {"prompt_id": "invalid"}}, "decision_prompt", "exact_fields"),
            ("binding digest", {**valid, "decision_prompt": {**valid["decision_prompt"], "digest": "sha256:" + "0" * 64}}, "decision_prompt", "stale_binding"),
            ("offered option", {**valid, "selected_option_id": "stop"}, "selected_option_id", "offered_option"),
            ("option type", {**valid, "selected_option_id": ["return_to_center"]}, "selected_option_id", "offered_option"),
        )
        for name, arguments, field_path, rule in cases:
            with self.subTest(name=name):
                with self.assertRaises(GovernanceMcpError) as caught:
                    active.call_tool(MCP_TOOL_NAMES[2], arguments)
                diagnostic = caught.exception.diagnostic()
                self.assertEqual(diagnostic["error_code"], "post_selection_invalid_field")
                self.assertEqual(diagnostic["stage"], MCP_TOOL_NAMES[2])
                self.assertEqual(diagnostic["field_path"], field_path)
                self.assertEqual(diagnostic["rule"], rule)
                self.assertTrue(diagnostic["retryable"])
                self.assertEqual(active._journeys[ready["journey_handle"]].adapter.journey().responses[-1].status, "ready_for_decision")
        resolved = active.call_tool(MCP_TOOL_NAMES[2], valid)
        self.assertEqual(resolved["response"]["status"], "resolved")

    def test_self_review_repairable_failures_are_structured_atomic_and_retryable(self) -> None:
        active = adapter()
        ready = ready_journey(active)
        resolved = active.call_tool(
            MCP_TOOL_NAMES[2],
            {"journey_handle": ready["journey_handle"], "decision_prompt": prompt_binding(ready, "decision_prompt"), "selected_option_id": "return_to_center"},
        )
        start = {
            "journey_handle": resolved["journey_handle"],
            "reason_codes": ["requirement_drift"],
            "allowed_evidence_refs": [EVIDENCE],
        }
        for field, value, rule in (
            ("reason_codes", [], "min_items"),
            ("reason_codes", ["Needs review"], "normalized_identifier"),
            ("allowed_evidence_refs", ["../outside.md"], "repository_relative"),
            ("allowed_evidence_refs", ["docs/" + "a" * 236], "normalized_text"),
        ):
            with self.subTest(field=field):
                invalid = {**start, field: value}
                with self.assertRaises(GovernanceMcpError) as caught:
                    active.call_tool(MCP_TOOL_NAMES[3], invalid)
                diagnostic = caught.exception.diagnostic()
                self.assertEqual(diagnostic["error_code"], "post_selection_invalid_field")
                expected_path = (
                    field
                    if value == [] or value == ["../outside.md"]
                    else f"{field}[0]"
                )
                self.assertEqual(diagnostic["field_path"], expected_path)
                self.assertEqual(diagnostic["rule"], rule)
                self.assertTrue(diagnostic["retryable"])
                self.assertFalse(active._journeys[resolved["journey_handle"]].review_requested)
        requested = active.call_tool(MCP_TOOL_NAMES[3], start)
        request = requested["response"]["materialization_request"]
        complete = {
            "journey_handle": resolved["journey_handle"],
            "request": {"request_id": request["request_id"], "digest": request["request_digest"]},
            "observations": [review_observation()],
        }
        invalid = {**complete, "request": {**complete["request"], "digest": "sha256:" + "0" * 64}}
        with self.assertRaises(GovernanceMcpError) as caught:
            active.call_tool(MCP_TOOL_NAMES[4], invalid)
        self.assertEqual(caught.exception.diagnostic()["rule"], "stale_binding")
        self.assertFalse(active._journeys[resolved["journey_handle"]].review_completed)
        invalid = {**complete, "observations": [{**review_observation(), "evidence_refs": ["../outside.md"]}]}
        with self.assertRaises(GovernanceMcpError) as caught:
            active.call_tool(MCP_TOOL_NAMES[4], invalid)
        self.assertEqual(caught.exception.diagnostic()["field_path"], "observations[0].evidence_refs")
        self.assertFalse(active._journeys[resolved["journey_handle"]].review_completed)
        invalid = {**complete, "observations": [{**review_observation(), "kind": ["architecture"]}]}
        with self.assertRaises(GovernanceMcpError) as caught:
            active.call_tool(MCP_TOOL_NAMES[4], invalid)
        self.assertEqual(caught.exception.diagnostic()["rule"], "enum")
        self.assertFalse(active._journeys[resolved["journey_handle"]].review_completed)
        invalid = {
            **complete,
            "observations": [
                {**review_observation(), "evidence_refs": ["README.md"]}
            ],
        }
        with self.assertRaises(GovernanceMcpError) as caught:
            active.call_tool(MCP_TOOL_NAMES[4], invalid)
        diagnostic = caught.exception.diagnostic()
        self.assertEqual(diagnostic["field_path"], "observations[0].evidence_refs")
        self.assertEqual(diagnostic["rule"], "allowed_evidence")
        self.assertTrue(diagnostic["retryable"])
        self.assertFalse(active._journeys[resolved["journey_handle"]].review_completed)
        invalid = {
            **complete,
            "observations": [review_observation(), review_observation()],
        }
        with self.assertRaises(GovernanceMcpError) as caught:
            active.call_tool(MCP_TOOL_NAMES[4], invalid)
        diagnostic = caught.exception.diagnostic()
        self.assertEqual(diagnostic["field_path"], "observations")
        self.assertEqual(diagnostic["rule"], "unique_items")
        self.assertTrue(diagnostic["retryable"])
        self.assertFalse(active._journeys[resolved["journey_handle"]].review_completed)
        invalid_observation = review_observation()
        invalid_observation["assumptions"] = [f"assumption {index}" for index in range(21)]
        invalid = {**complete, "observations": [invalid_observation]}
        with self.assertRaises(GovernanceMcpError) as caught:
            active.call_tool(MCP_TOOL_NAMES[4], invalid)
        diagnostic = caught.exception.diagnostic()
        self.assertEqual(diagnostic["field_path"], "observations[0].assumptions")
        self.assertEqual(diagnostic["rule"], "max_items")
        self.assertTrue(diagnostic["retryable"])
        self.assertFalse(active._journeys[resolved["journey_handle"]].review_completed)
        completed = active.call_tool(MCP_TOOL_NAMES[4], complete)
        self.assertEqual(completed["response"]["status"], "completed")

    def test_restart_unknown_handle_raw_fields_and_authority_drift_fail_closed(self) -> None:
        first = adapter()
        started = first.call_tool(MCP_TOOL_NAMES[0], start_arguments())
        update = {
            "journey_handle": started["journey_handle"],
            "prompt": prompt_binding(started, "clarification_prompt"),
            "answer_summary": "Normalized answer.",
            "center_patch": empty_patch(),
            "new_questions": [],
            "candidate_resolutions": resolutions(),
            "recommended_resolution_id": "return_to_center",
            "ready_requested": True,
        }
        with self.assertRaisesRegex(ValueError, "restarted"):
            adapter().call_tool(MCP_TOOL_NAMES[1], update)

        raw = start_arguments()
        raw["raw_prompt"] = "private conversation"
        authority = start_arguments()
        authority["center"]["authorizes_code_change"] = True
        for payload in (raw, authority):
            with self.subTest(payload=payload):
                with self.assertRaises(ValueError):
                    adapter().call_tool(MCP_TOOL_NAMES[0], payload)

    def test_json_rpc_errors_and_tool_errors_remain_protocol_responses(self) -> None:
        server = GovernanceMcpServer(adapter())
        unknown_method = server.dispatch(rpc(1, "unknown", {}))
        unknown_tool = server.dispatch(rpc(2, "tools/call", {"name": "unknown", "arguments": {}}))
        tool_error = server.dispatch(rpc(3, "tools/call", {"name": MCP_TOOL_NAMES[1], "arguments": {}}))
        notification = server.dispatch({"jsonrpc": "2.0", "method": "notifications/initialized"})

        self.assertEqual(unknown_method["error"]["code"], -32601)
        self.assertEqual(unknown_tool["error"]["code"], -32602)
        self.assertTrue(tool_error["result"]["isError"])
        self.assertEqual(
            tool_error["result"]["structuredContent"]["error"]["contract"],
            "agentgov.mcp-tool-error",
        )
        self.assertIsNone(notification)

    def test_alignment_error_is_structured_private_and_corrected_start_retries(self) -> None:
        server = GovernanceMcpServer(adapter())
        invalid = start_arguments()
        private_value = "C:\\private\\draft.txt"
        invalid["center"]["outcome"] = private_value
        failed = server.dispatch(
            rpc(1, "tools/call", {"name": MCP_TOOL_NAMES[0], "arguments": invalid})
        )["result"]

        self.assertTrue(failed["isError"])
        error = failed["structuredContent"]["error"]
        self.assertEqual(error["error_code"], "alignment_invalid_field")
        self.assertEqual(error["stage"], MCP_TOOL_NAMES[0])
        self.assertEqual(error["field_path"], "center.outcome")
        self.assertEqual(error["rule"], "privacy_boundary")
        self.assertTrue(error["retryable"])
        self.assertNotIn(private_value, json.dumps(failed))

        corrected = server.dispatch(
            rpc(2, "tools/call", {"name": MCP_TOOL_NAMES[0], "arguments": start_arguments()})
        )["result"]
        self.assertFalse(corrected["isError"])
        generated = corrected["structuredContent"]["response"]["dialogue"]["open_questions"][0]["question_id"]
        self.assertRegex(generated, r"^qst-[0-9a-f]{16}$")

    def test_invalid_question_shape_reports_path_and_does_not_start_journey(self) -> None:
        server = GovernanceMcpServer(adapter())
        invalid = start_arguments()
        invalid["unknowns"][0]["question_id"] = "model-owned-id"
        failed = server.dispatch(
            rpc(1, "tools/call", {"name": MCP_TOOL_NAMES[0], "arguments": invalid})
        )["result"]
        error = failed["structuredContent"]["error"]
        self.assertEqual(error["field_path"], "unknowns[0]")
        self.assertEqual(error["rule"], "exact_fields")
        self.assertTrue(error["retryable"])

        corrected = server.dispatch(
            rpc(2, "tools/call", {"name": MCP_TOOL_NAMES[0], "arguments": start_arguments()})
        )["result"]
        self.assertFalse(corrected["isError"])

    def test_subject_and_recommendation_errors_are_bounded_and_retryable(self) -> None:
        server = GovernanceMcpServer(adapter())
        invalid_subject = start_arguments()
        invalid_subject["subject_id"] = "Invalid Subject"
        subject_error = server.dispatch(
            rpc(1, "tools/call", {"name": MCP_TOOL_NAMES[0], "arguments": invalid_subject})
        )["result"]["structuredContent"]["error"]
        self.assertEqual(subject_error["field_path"], "subject_id")
        self.assertEqual(subject_error["rule"], "normalized_identifier")

        invalid_recommendation = start_arguments()
        invalid_recommendation["unknowns"] = []
        invalid_recommendation["candidate_resolutions"] = resolutions()
        invalid_recommendation["recommended_resolution_id"] = "stop"
        recommendation_error = server.dispatch(
            rpc(2, "tools/call", {"name": MCP_TOOL_NAMES[0], "arguments": invalid_recommendation})
        )["result"]["structuredContent"]["error"]
        self.assertEqual(recommendation_error["field_path"], "recommended_resolution_id")
        self.assertEqual(recommendation_error["rule"], "candidate_binding")
        self.assertTrue(recommendation_error["retryable"])

    def test_advisory_drift_kinds_match_core_and_failed_start_is_atomic(self) -> None:
        tools = {item["name"]: item for item in governance_mcp_tools()}
        drift_schema = tools[MCP_TOOL_NAMES[0]]["inputSchema"]["properties"]["drift"]
        conditional = drift_schema["allOf"][0]
        self.assertEqual(
            conditional["if"]["properties"]["kind"]["enum"],
            ["business", "requirement", "architecture"],
        )
        self.assertEqual(
            conditional["then"]["properties"]["semantics"]["const"],
            "advisory",
        )

        for request_id, kind in enumerate(
            ("business", "requirement", "architecture"), start=1
        ):
            with self.subTest(kind=kind):
                server = GovernanceMcpServer(adapter())
                invalid = start_arguments()
                invalid["drift"]["kind"] = kind
                invalid["drift"]["semantics"] = "deterministic"
                failed = server.dispatch(
                    rpc(
                        request_id,
                        "tools/call",
                        {"name": MCP_TOOL_NAMES[0], "arguments": invalid},
                    )
                )["result"]

                self.assertTrue(failed["isError"])
                error = failed["structuredContent"]["error"]
                self.assertEqual(error["error_code"], "alignment_invalid_field")
                self.assertEqual(error["field_path"], "drift.semantics")
                self.assertEqual(error["rule"], "advisory_required")
                self.assertTrue(error["retryable"])

                corrected = start_arguments()
                corrected["drift"]["kind"] = kind
                accepted = server.dispatch(
                    rpc(
                        request_id + 10,
                        "tools/call",
                        {"name": MCP_TOOL_NAMES[0], "arguments": corrected},
                    )
                )["result"]
                self.assertFalse(accepted["isError"])

        for request_id, kind in enumerate(("scope", "implementation"), start=21):
            with self.subTest(kind=kind, semantics="deterministic"):
                server = GovernanceMcpServer(adapter())
                valid = start_arguments()
                valid["drift"]["kind"] = kind
                valid["drift"]["semantics"] = "deterministic"
                accepted = server.dispatch(
                    rpc(
                        request_id,
                        "tools/call",
                        {"name": MCP_TOOL_NAMES[0], "arguments": valid},
                    )
                )["result"]
                self.assertFalse(accepted["isError"])

    def test_no_unknowns_require_stable_options_and_recommendation(self) -> None:
        tools = {item["name"]: item for item in governance_mcp_tools()}
        start_schema = tools[MCP_TOOL_NAMES[0]]["inputSchema"]
        conditional = start_schema["allOf"][0]
        self.assertEqual(
            conditional["if"]["properties"]["unknowns"]["maxItems"], 0
        )
        self.assertEqual(
            conditional["then"]["properties"]["candidate_resolutions"]["minItems"],
            2,
        )
        self.assertEqual(
            conditional["then"]["properties"]["recommended_resolution_id"]["type"],
            "string",
        )

        server = GovernanceMcpServer(adapter())
        insufficient = start_arguments()
        insufficient["unknowns"] = []
        candidate_error = server.dispatch(
            rpc(
                1,
                "tools/call",
                {"name": MCP_TOOL_NAMES[0], "arguments": insufficient},
            )
        )["result"]
        self.assertTrue(candidate_error["isError"])
        candidate_diagnostic = candidate_error["structuredContent"]["error"]
        self.assertEqual(candidate_diagnostic["field_path"], "candidate_resolutions")
        self.assertEqual(candidate_diagnostic["rule"], "stable_options_required")
        self.assertTrue(candidate_diagnostic["retryable"])

        missing_recommendation = start_arguments()
        missing_recommendation["unknowns"] = []
        missing_recommendation["candidate_resolutions"] = resolutions()
        recommendation_error = server.dispatch(
            rpc(
                2,
                "tools/call",
                {"name": MCP_TOOL_NAMES[0], "arguments": missing_recommendation},
            )
        )["result"]
        self.assertTrue(recommendation_error["isError"])
        recommendation_diagnostic = recommendation_error["structuredContent"]["error"]
        self.assertEqual(
            recommendation_diagnostic["field_path"], "recommended_resolution_id"
        )
        self.assertEqual(recommendation_diagnostic["rule"], "recommendation_required")
        self.assertTrue(recommendation_diagnostic["retryable"])

        corrected = start_arguments()
        corrected["unknowns"] = []
        corrected["candidate_resolutions"] = resolutions()
        corrected["recommended_resolution_id"] = "return_to_center"
        accepted = server.dispatch(
            rpc(
                3,
                "tools/call",
                {"name": MCP_TOOL_NAMES[0], "arguments": corrected},
            )
        )["result"]
        self.assertFalse(accepted["isError"])
        self.assertEqual(
            accepted["structuredContent"]["response"]["status"],
            "ready_for_decision",
        )

    def test_alignment_start_repairable_input_matrix_has_no_unclassified_path(self) -> None:
        def add_non_adopt_patch(payload: dict) -> None:
            payload["candidate_resolutions"] = resolutions()
            payload["candidate_resolutions"][0]["center_patch"]["outcome"] = "Changed"

        def duplicate_candidate(payload: dict) -> None:
            payload["candidate_resolutions"] = resolutions()
            payload["candidate_resolutions"][1]["id"] = "return_to_center"

        cases = (
            ("envelope fields", lambda p: p.__setitem__("unexpected", True), "$", "exact_fields"),
            ("subject type", lambda p: p.__setitem__("subject_type", "other"), "subject_type", "enum"),
            ("subject id", lambda p: p.__setitem__("subject_id", "Invalid Subject"), "subject_id", "normalized_identifier"),
            ("center shape", lambda p: p["center"].pop("why_now"), "center", "exact_fields"),
            ("center text", lambda p: p["center"].__setitem__("outcome", ""), "center.outcome", "normalized_text"),
            ("success minimum", lambda p: p["center"].__setitem__("success_signals", []), "center.success_signals", "min_items"),
            ("center unique", lambda p: p["center"].__setitem__("constraints", ["same", "same"]), "center.constraints", "unique_items"),
            ("drift shape", lambda p: p["drift"].pop("impact"), "drift", "exact_fields"),
            ("drift kind", lambda p: p["drift"].__setitem__("kind", "other"), "drift.kind", "enum"),
            ("drift text", lambda p: p["drift"].__setitem__("observation", ""), "drift.observation", "normalized_text"),
            ("evidence relative", lambda p: p["drift"].__setitem__("evidence_refs", ["../outside.md"]), "drift.evidence_refs", "repository_relative"),
            ("assumption maximum", lambda p: p.__setitem__("assumptions", [f"item-{i}" for i in range(51)]), "assumptions", "max_items"),
            ("assumption unique", lambda p: p.__setitem__("assumptions", ["same", "same"]), "assumptions", "unique_items"),
            ("unknown maximum", lambda p: p.__setitem__("unknowns", [mcp_question(f"Question {i}?") for i in range(101)]), "unknowns", "max_items"),
            ("question text", lambda p: p["unknowns"][0].__setitem__("question", ""), "unknowns[0].question", "normalized_text"),
            ("question reason", lambda p: p["unknowns"][0].__setitem__("why_matters", ""), "unknowns[0].why_matters", "normalized_text"),
            ("question material", lambda p: p["unknowns"][0].__setitem__("material", "yes"), "unknowns[0].material", "boolean_required"),
            ("question priority", lambda p: p["unknowns"][0].__setitem__("priority", 6), "unknowns[0].priority", "range"),
            ("candidate type", lambda p: p.__setitem__("candidate_resolutions", {}), "candidate_resolutions", "array_required"),
            ("candidate maximum", lambda p: p.__setitem__("candidate_resolutions", [resolutions()[0] for _ in range(6)]), "candidate_resolutions", "max_items"),
            ("candidate shape", lambda p: p.__setitem__("candidate_resolutions", [{"id": "stop"}]), "candidate_resolutions[0]", "exact_fields"),
            ("candidate id", lambda p: p.__setitem__("candidate_resolutions", [{**resolutions()[0], "id": "other"}]), "candidate_resolutions[0].id", "enum"),
            ("candidate duplicate", duplicate_candidate, "candidate_resolutions[1].id", "unique_items"),
            ("candidate label", lambda p: p.__setitem__("candidate_resolutions", [{**resolutions()[0], "label": ""}]), "candidate_resolutions[0].label", "normalized_text"),
            ("candidate effect", lambda p: p.__setitem__("candidate_resolutions", [{**resolutions()[0], "effect": ""}]), "candidate_resolutions[0].effect", "normalized_text"),
            ("candidate patch shape", lambda p: p.__setitem__("candidate_resolutions", [{**resolutions()[0], "center_patch": {}}]), "candidate_resolutions[0].center_patch", "exact_fields"),
            ("adopt patch", lambda p: p.__setitem__("candidate_resolutions", [{**resolutions()[1], "center_patch": empty_patch()}]), "candidate_resolutions[0].center_patch", "adopt_patch_required"),
            ("non-adopt patch", add_non_adopt_patch, "candidate_resolutions[0].center_patch", "patch_forbidden"),
            ("recommendation binding", lambda p: p.__setitem__("recommended_resolution_id", "stop"), "recommended_resolution_id", "candidate_binding"),
            ("privacy", lambda p: p["center"].__setitem__("why_now", "password=private-value"), "center.why_now", "privacy_boundary"),
        )
        self.assertEqual(len(cases), 30)

        for name, mutate, expected_path, expected_rule in cases:
            with self.subTest(name=name):
                payload = start_arguments()
                mutate(payload)
                result = GovernanceMcpServer(adapter()).dispatch(
                    rpc(
                        1,
                        "tools/call",
                        {"name": MCP_TOOL_NAMES[0], "arguments": payload},
                    )
                )["result"]
                self.assertTrue(result["isError"])
                diagnostic = result["structuredContent"]["error"]
                self.assertEqual(diagnostic["field_path"], expected_path)
                self.assertEqual(diagnostic["rule"], expected_rule)
                self.assertTrue(diagnostic["retryable"])
                self.assertNotEqual(diagnostic["rule"], "unclassified")
                self.assertNotIn("private-value", json.dumps(result))

    def test_alignment_start_schema_matches_core_input_cardinality_and_patch_rules(self) -> None:
        start_schema = governance_mcp_tools()[0]["inputSchema"]
        self.assertEqual(
            start_schema["properties"]["center"]["properties"]["success_signals"]["minItems"],
            1,
        )
        assumptions = start_schema["properties"]["assumptions"]
        self.assertEqual(assumptions["maxItems"], 50)
        self.assertTrue(assumptions["uniqueItems"])
        self.assertEqual(assumptions["items"]["minLength"], 1)
        self.assertEqual(assumptions["items"]["maxLength"], 400)
        resolution_schema = start_schema["properties"]["candidate_resolutions"]["items"]
        patch_rule = resolution_schema["allOf"][0]
        self.assertEqual(
            patch_rule["if"]["properties"]["id"]["const"], "adopt_new_center"
        )
        self.assertEqual(len(patch_rule["then"]["anyOf"]), 5)
        null_properties = patch_rule["else"]["properties"]["center_patch"]["properties"]
        self.assertTrue(all(item["const"] is None for item in null_properties.values()))

    def test_unknown_core_start_failure_remains_private_and_nonretryable(self) -> None:
        def reject_unknown(*_: object, **__: object) -> None:
            try:
                raise ValueError("synthetic future internal invariant")
            except ValueError as cause:
                raise ReferenceAlignmentAdapterError(
                    "Core rejected the host's normalized alignment draft"
                ) from cause

        active = adapter()
        with patch.object(
            ReferenceAlignmentAdapter,
            "start_from_draft",
            side_effect=reject_unknown,
        ):
            with self.assertRaises(GovernanceMcpError) as caught:
                active.call_tool(MCP_TOOL_NAMES[0], start_arguments())
        diagnostic = caught.exception.diagnostic()
        self.assertEqual(diagnostic["error_code"], "alignment_rejected_internal")
        self.assertIsNone(diagnostic["field_path"])
        self.assertEqual(diagnostic["rule"], "unclassified")
        self.assertFalse(diagnostic["retryable"])
        self.assertNotIn("synthetic future internal invariant", json.dumps(diagnostic))

    def test_failed_update_is_atomic_and_adapter_assigns_new_question_identity(self) -> None:
        server = GovernanceMcpServer(adapter())
        started = server.dispatch(
            rpc(1, "tools/call", {"name": MCP_TOOL_NAMES[0], "arguments": start_arguments()})
        )["result"]["structuredContent"]
        update = {
            "journey_handle": started["journey_handle"],
            "prompt": prompt_binding(started, "clarification_prompt"),
            "answer_summary": "The user kept the current center and identified one follow-up.",
            "center_patch": empty_patch(),
            "new_questions": [mcp_question("Should the result record include retry evidence?")],
            "candidate_resolutions": [],
            "recommended_resolution_id": None,
            "ready_requested": False,
        }
        invalid = json.loads(json.dumps(update))
        invalid["new_questions"][0]["question_id"] = "model-owned-id"
        failed = server.dispatch(
            rpc(2, "tools/call", {"name": MCP_TOOL_NAMES[1], "arguments": invalid})
        )["result"]
        self.assertTrue(failed["isError"])
        self.assertEqual(failed["structuredContent"]["error"]["field_path"], "new_questions[0]")

        corrected = server.dispatch(
            rpc(3, "tools/call", {"name": MCP_TOOL_NAMES[1], "arguments": update})
        )["result"]
        self.assertFalse(corrected["isError"])
        open_questions = corrected["structuredContent"]["response"]["dialogue"]["open_questions"]
        self.assertEqual(len(open_questions), 1)
        self.assertRegex(open_questions[0]["question_id"], r"^qst-[0-9a-f]{16}$")

    def test_cli_stdio_emits_only_json_rpc_lines(self) -> None:
        stream = "\n".join(
            (
                json.dumps(rpc(1, "server/discover", {"_meta": {}})),
                json.dumps(rpc(2, "tools/list", {})),
                "not json",
            )
        ) + "\n"
        code, stdout, stderr = run_cli(
            stream, "adapter", "governance-mcp", "--host-profile", "codex"
        )
        output = [json.loads(line) for line in stdout.splitlines()]
        self.assertEqual(code, EXIT_PASS)
        self.assertEqual(stderr, "")
        self.assertEqual(len(output), 3)
        self.assertEqual(output[-1]["error"]["code"], -32700)


class CodexMcpIntegrationTests(unittest.TestCase):
    def test_config_is_valid_exact_and_uses_packaged_foreground_command(self) -> None:
        rendered = render_codex_mcp_config()
        config = tomllib.loads(rendered)
        server = config["mcp_servers"]["agentgov_governance"]
        self.assertEqual(server["command"], "agentgov")
        self.assertEqual(server["args"], ["adapter", "governance-mcp", "--host-profile", "codex"])
        self.assertEqual(tuple(server["enabled_tools"]), MCP_TOOL_NAMES)
        self.assertTrue(server["required"])
        self.assertEqual(server["default_tools_approval_mode"], "auto")
        self.assertEqual(
            rendered,
            (ROOT / "templates/codex-mcp.template.toml").read_text(encoding="utf-8"),
        )

    def test_create_preserve_conflict_and_apply_are_create_only(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            create_git_repository(root)
            create = plan_codex_mcp_integration(root)
            self.assertEqual(create.action, CodexHooksAction.CREATE)
            result = apply_codex_mcp_plan(create)
            self.assertEqual(result.created_files, (CODEX_MCP_CONFIG_PATH,))
            self.assertEqual(plan_codex_mcp_integration(root).action, CodexHooksAction.PRESERVE)

        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            create_git_repository(root)
            (root / ".codex").mkdir()
            (root / CODEX_MCP_CONFIG_PATH).write_text("model = 'custom'\n", encoding="utf-8")
            conflict = plan_codex_mcp_integration(root)
            self.assertEqual(conflict.action, CodexHooksAction.CONFLICT)
            with self.assertRaises(RuntimeError):
                apply_codex_mcp_plan(conflict)

    def test_cli_dry_run_is_read_only_and_denies_config_trust(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            create_git_repository(root)
            code, stdout, stderr = run_cli(
                "", "integrate", "codex-mcp", str(root), "--dry-run", "--format", "json", "--non-interactive"
            )
            payload = json.loads(stdout)
            self.assertEqual(code, EXIT_PASS)
            self.assertEqual(stderr, "")
            self.assertEqual(payload["item"]["action"], "CREATE")
            self.assertFalse(payload["authority_boundary"]["config_trust_authorized"])
            self.assertFalse((root / CODEX_MCP_CONFIG_PATH).exists())

    def test_schema_is_strict_packaged_and_codex_specificity_stays_out_of_core(self) -> None:
        schema = json.loads((ROOT / "schemas/codex-mcp-integration-plan.schema.json").read_text(encoding="utf-8"))
        pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
        core = (ROOT / "src/agentgov/governance_mcp.py").read_text(encoding="utf-8").lower()
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(schema["properties"]["item"]["properties"]["path"]["const"], ".codex/config.toml")
        self.assertNotIn("openai.codex", core)
        self.assertNotIn("claude", core)
        self.assertIn("schemas/*.schema.json", pyproject["tool"]["setuptools"]["data-files"]["share/agent-governance-starter/schemas"])


if __name__ == "__main__":
    unittest.main()
