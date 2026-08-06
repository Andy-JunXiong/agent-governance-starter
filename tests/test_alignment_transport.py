from __future__ import annotations

import contextlib
import io
import json
import sys
import tomllib
import unittest
from dataclasses import asdict
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from agentgov.alignment_transport import (
    ALIGNMENT_RESPONSE_CONTRACT,
    AlignmentStreamSession,
    AlignmentTransportError,
    alignment_stream_response_from_payload,
    render_alignment_stream_response_json,
)
from agentgov.cli import EXIT_ERROR, EXIT_PASS, main
from agentgov.clarification_dialogue import clarification_update_from_payload
from agentgov.human_decision import record_human_decision
from agentgov.host_interaction import (
    REFERENCE_HOST_CAPABILITIES,
    host_interaction_capabilities_from_payload,
)
from tests.test_clarification_dialogue import context, question, resolutions, update
from tests.test_coding_agent_transport import create_repository, event_payload


ROOT = Path(__file__).resolve().parents[1]


def run_cli_with_stdin(stdin_text: str, *args: str) -> tuple[int, str, str]:
    stdout = io.StringIO()
    stderr = io.StringIO()
    with (
        patch.object(sys, "stdin", io.StringIO(stdin_text)),
        contextlib.redirect_stdout(stdout),
        contextlib.redirect_stderr(stderr),
    ):
        code = main(list(args))
    return code, stdout.getvalue(), stderr.getvalue()


class AlignmentStreamSessionTests(unittest.TestCase):
    def test_context_automatically_returns_one_clarification_question(self) -> None:
        session = AlignmentStreamSession()
        response = session.process_payload(context(), sequence=1)
        rendered = json.loads(render_alignment_stream_response_json(response))

        self.assertEqual(response.contract, ALIGNMENT_RESPONSE_CONTRACT)
        self.assertEqual(response.status, "exploring")
        self.assertEqual(response.input["actor_class"], "coding_agent")
        self.assertIsNotNone(response.clarification_prompt)
        self.assertIsNone(response.decision_prompt)
        self.assertEqual(
            response.clarification_prompt.question["response_mode"],
            "natural_language",
        )
        self.assertEqual(
            rendered["persistence"],
            {"mode": "foreground_memory", "survives_restart": False},
        )
        self.assertTrue(all(value is False for value in response.authority_boundary.values()))

    def test_human_update_automatically_returns_next_question_then_decision(self) -> None:
        session = AlignmentStreamSession()
        first = session.process_payload(context(), sequence=1)
        second_payload = update(
            first.dialogue,
            first.clarification_prompt,
            summary="The user wants another material boundary clarified.",
            new_questions=[question("b", "Should changed intent replace or split the work?")],
            digit="2",
        )
        second = session.process_payload(second_payload, sequence=2)
        final_payload = update(
            second.dialogue,
            second.clarification_prompt,
            summary="The user wants changed intent split into separate work.",
            candidates=resolutions(),
            recommendation="split_new_requirement",
            ready=True,
            digit="3",
        )
        ready = session.process_payload(final_payload, sequence=3)

        self.assertEqual(second.status, "exploring")
        self.assertEqual(
            second.clarification_prompt.question["text"],
            "Should changed intent replace or split the work?",
        )
        self.assertEqual(ready.status, "ready_for_decision")
        self.assertIsNone(ready.clarification_prompt)
        self.assertEqual(ready.decision_prompt.kind, "alignment_resolution")
        self.assertEqual(ready.decision_prompt.recommended_option_id, "split_new_requirement")

    def test_final_human_result_returns_resolved_state_only(self) -> None:
        session = AlignmentStreamSession()
        ready = session.process_payload(
            context(
                unknowns=[],
                candidates=resolutions(),
                recommendation="return_to_center",
            ),
            sequence=1,
        )
        result = record_human_decision(
            ready.decision_prompt,
            selected_option_id="return_to_center",
            adapter_id="agentgov.reference-adapter",
            recording_method="host_single_select",
            recorded_at="2026-08-06T00:00:05.000Z",
        )
        resolved = session.process_payload(asdict(result), sequence=2)

        self.assertEqual(resolved.status, "resolved")
        self.assertEqual(resolved.dialogue.resolution["option_id"], "return_to_center")
        self.assertIsNone(resolved.clarification_prompt)
        self.assertIsNone(resolved.decision_prompt)
        self.assertEqual(resolved.dialogue.metrics["governance_decision_episodes"], 1)
        self.assertTrue(all(value is False for value in resolved.authority_boundary.values()))

    def test_final_decision_binds_the_declared_host_not_a_core_vendor(self) -> None:
        capabilities = asdict(REFERENCE_HOST_CAPABILITIES)
        capabilities["adapter_id"] = "fixture.native-host"
        session = AlignmentStreamSession(
            host_capabilities=host_interaction_capabilities_from_payload(capabilities)
        )
        ready = session.process_payload(
            context(unknowns=[], candidates=resolutions(), recommendation="return_to_center"),
            sequence=1,
        )

        self.assertEqual(ready.decision_prompt.binding["adapter_id"], "fixture.native-host")

    def test_invalid_update_is_atomic_and_valid_retry_still_succeeds(self) -> None:
        session = AlignmentStreamSession()
        first = session.process_payload(context(), sequence=1)
        invalid = update(
            first.dialogue,
            first.clarification_prompt,
            summary="This stale answer must fail.",
            new_questions=[question("b", "What should be clarified next?")],
            digit="2",
        )
        invalid["dialogue"]["revision"] += 1
        with self.assertRaises(AlignmentTransportError):
            session.process_payload(invalid, sequence=2)

        valid = update(
            first.dialogue,
            first.clarification_prompt,
            summary="This exact answer advances the dialogue.",
            new_questions=[question("b", "What should be clarified next?")],
            digit="2",
        )
        advanced = session.process_payload(valid, sequence=2)

        self.assertEqual(advanced.dialogue.revision, 2)
        self.assertEqual(advanced.dialogue.metrics["clarification_turns"], 1)

    def test_duplicate_context_adapter_drift_and_missing_restart_state_fail(self) -> None:
        session = AlignmentStreamSession()
        first = session.process_payload(context(), sequence=1)
        with self.assertRaises(AlignmentTransportError):
            session.process_payload(context(), sequence=2)

        update_payload = update(
            first.dialogue,
            first.clarification_prompt,
            summary="A restarted process has no active state.",
            new_questions=[question("b", "Next question?")],
            digit="2",
        )
        with self.assertRaisesRegex(AlignmentTransportError, "active dialogue"):
            AlignmentStreamSession().process_payload(update_payload, sequence=1)

        resolved_session = AlignmentStreamSession()
        ready = resolved_session.process_payload(
            context(unknowns=[], candidates=resolutions(), recommendation="return_to_center"),
            sequence=1,
        )
        result = record_human_decision(
            ready.decision_prompt,
            selected_option_id="return_to_center",
            adapter_id="agentgov.reference-adapter",
            recording_method="host_single_select",
            recorded_at="2026-08-06T00:00:05.000Z",
        )
        resolved_session.process_payload(asdict(result), sequence=2)
        drifted = context()
        drifted["context_id"] = "acx-" + "2" * 32
        drifted["source"]["adapter_id"] = "different.coding-agent"
        with self.assertRaisesRegex(AlignmentTransportError, "adapter drifted"):
            resolved_session.process_payload(drifted, sequence=3)

    def test_response_parser_rejects_prompt_and_authority_drift(self) -> None:
        response = AlignmentStreamSession().process_payload(context(), sequence=1)
        prompt_drift = asdict(response)
        prompt_drift["clarification_prompt"]["question"]["text"] = "Substituted question?"
        authority = asdict(response)
        authority["authority_boundary"]["changes_center"] = True

        for payload in (prompt_drift, authority):
            with self.assertRaises(AlignmentTransportError):
                alignment_stream_response_from_payload(payload)

    def test_schema_is_strict_and_packaged(self) -> None:
        schema_path = ROOT / "schemas/coding-agent-alignment-response.schema.json"
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
        data_files = pyproject["tool"]["setuptools"]["data-files"]

        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(schema["properties"]["contract"]["const"], ALIGNMENT_RESPONSE_CONTRACT)
        self.assertIs(schema["properties"]["persistence"]["properties"]["survives_restart"]["const"], False)
        self.assertIn("schemas/*.schema.json", data_files["share/agent-governance-starter/schemas"])


class AlignmentLiveStreamTests(unittest.TestCase):
    def test_dev_stream_processes_context_update_and_final_result(self) -> None:
        builder = AlignmentStreamSession()
        context_payload = context(
            unknowns=[question("a", "Should this drift return to the current center?")]
        )
        first = builder.process_payload(context_payload, sequence=1)
        update_payload = update(
            first.dialogue,
            first.clarification_prompt,
            summary="The user confirmed returning to the current center.",
            candidates=resolutions(),
            recommendation="return_to_center",
            ready=True,
            digit="2",
        )
        ready = builder.process_payload(update_payload, sequence=2)
        result = record_human_decision(
            ready.decision_prompt,
            selected_option_id="return_to_center",
            adapter_id="agentgov.reference-adapter",
            recording_method="host_single_select",
            recorded_at="2026-08-06T00:00:05.000Z",
        )
        stream = "\n".join(
            json.dumps(item)
            for item in (context_payload, update_payload, asdict(result))
        ) + "\n"

        with TemporaryDirectory() as temp_dir:
            code, stdout, stderr = run_cli_with_stdin(
                stream,
                "dev",
                temp_dir,
                "--stream",
                "--format",
                "json",
            )
        responses = [json.loads(line) for line in stdout.splitlines()]

        self.assertEqual(code, EXIT_PASS)
        self.assertEqual(stderr, "")
        self.assertEqual([item["sequence"] for item in responses], [1, 2, 3])
        self.assertEqual(
            [item["status"] for item in responses],
            ["exploring", "ready_for_decision", "resolved"],
        )
        self.assertIsNotNone(responses[0]["clarification_prompt"])
        self.assertIsNotNone(responses[1]["decision_prompt"])
        self.assertIsNone(responses[2]["decision_prompt"])

    def test_lifecycle_and_alignment_records_share_one_adapter_connection(self) -> None:
        lifecycle = event_payload("task.requested")
        alignment = context()
        stream = json.dumps(lifecycle) + "\n" + json.dumps(alignment) + "\n"

        with TemporaryDirectory() as temp_dir:
            repository = create_repository(Path(temp_dir), active_task=False)
            code, stdout, stderr = run_cli_with_stdin(
                stream,
                "dev",
                str(repository),
                "--stream",
                "--format",
                "json",
            )
        responses = [json.loads(line) for line in stdout.splitlines()]

        self.assertEqual(code, EXIT_PASS)
        self.assertEqual(stderr, "")
        self.assertEqual(responses[0]["contract"], "agentgov.coding-agent-response")
        self.assertEqual(responses[1]["contract"], ALIGNMENT_RESPONSE_CONTRACT)

    def test_cross_adapter_or_unknown_contract_fails_on_exact_line(self) -> None:
        lifecycle = event_payload("task.requested")
        drifted = context()
        drifted["source"]["adapter_id"] = "different.coding-agent"
        stream = json.dumps(lifecycle) + "\n" + json.dumps(drifted) + "\n"

        with TemporaryDirectory() as temp_dir:
            repository = create_repository(Path(temp_dir), active_task=False)
            code, stdout, stderr = run_cli_with_stdin(
                stream,
                "dev",
                str(repository),
                "--stream",
                "--format",
                "json",
            )
            unknown_code, unknown_stdout, unknown_stderr = run_cli_with_stdin(
                json.dumps({"contract": "agentgov.unknown"}) + "\n",
                "dev",
                str(repository),
                "--stream",
                "--format",
                "json",
            )

        self.assertEqual(code, EXIT_ERROR)
        self.assertEqual(len(stdout.splitlines()), 1)
        self.assertIn("line 2", stderr)
        self.assertIn("same Coding Agent adapter", stderr)
        self.assertEqual(unknown_code, EXIT_ERROR)
        self.assertEqual(unknown_stdout, "")
        self.assertIn("line 1", unknown_stderr)
        self.assertIn("unsupported", unknown_stderr)


if __name__ == "__main__":
    unittest.main()
