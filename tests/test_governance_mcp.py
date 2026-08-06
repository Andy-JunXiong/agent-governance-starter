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
    MCP_PROTOCOL_VERSION,
    MCP_SERVER_INSTRUCTIONS,
    MCP_TOOL_NAMES,
    GovernanceMcpAdapter,
    GovernanceMcpServer,
    build_active_host_self_review_provider,
    governance_mcp_tools,
)
from agentgov.human_decision import canonical_document_digest
from tests.test_clarification_dialogue import empty_patch, question, resolutions


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = "docs/product-requirements-automatic-governance.md"


def adapter(host: str = "fixture.codex-mcp") -> GovernanceMcpAdapter:
    provider = build_active_host_self_review_provider(
        adapter_id=host,
        provider_id=host + "-current-agent",
    )
    return GovernanceMcpAdapter(adapter_id=host, provider=provider)


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
            rpc(2, "initialize", {"protocolVersion": "2025-11-25", "capabilities": {}, "clientInfo": {"name": "fixture", "version": "1"}})
        )
        listed = server.dispatch(rpc(3, "tools/list", {}))

        self.assertEqual(discovered["result"]["supportedVersions"][0], MCP_PROTOCOL_VERSION)
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
        self.assertIn("After implementing and validating", MCP_SERVER_INSTRUCTIONS)
        self.assertIn("do not silently continue", MCP_SERVER_INSTRUCTIONS)
        descriptions = {tool["name"]: tool["description"] for tool in listed["result"]["tools"]}
        self.assertIn("multiple reasonable directions", descriptions[MCP_TOOL_NAMES[0]])
        self.assertIn("human must select", descriptions[MCP_TOOL_NAMES[0]])
        self.assertIn("before completion handoff", descriptions[MCP_TOOL_NAMES[3]])
        self.assertIn("distinct advisory", descriptions[MCP_TOOL_NAMES[3]])
        for tool in listed["result"]["tools"]:
            self.assertFalse(tool["inputSchema"]["additionalProperties"])
            self.assertTrue(tool["annotations"]["readOnlyHint"])
            self.assertFalse(tool["annotations"]["destructiveHint"])
        start_question = listed["result"]["tools"][0]["inputSchema"]["properties"]["unknowns"]["items"]
        update_question = listed["result"]["tools"][1]["inputSchema"]["properties"]["new_questions"]["items"]
        self.assertNotIn("question_id", start_question["properties"])
        self.assertNotIn("question_id", update_question["properties"])

    def test_repository_guidance_matches_mcp_selection_boundaries(self) -> None:
        guidance = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("the human does not need to name the tools", guidance)
        self.assertIn("asks the Agent to choose what to build", guidance)
        self.assertIn("Do not choose that direction for them", guidance)
        self.assertIn("fully specified low-risk change", guidance)
        self.assertIn("agentgov_self_review_start", guidance)
        self.assertIn("agentgov_self_review_complete", guidance)
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
        self.assertEqual(error["field_path"], "$")
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
