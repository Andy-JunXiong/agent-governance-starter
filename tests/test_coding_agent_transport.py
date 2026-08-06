from __future__ import annotations

import contextlib
import io
import json
import shutil
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from agentgov.cli import EXIT_ERROR, EXIT_PASS, main
from agentgov.coding_agent_transport import (
    CodingAgentTransportError,
    coding_agent_event_from_human_decision,
    coding_agent_event_from_payload,
    render_coding_agent_response_json,
    run_coding_agent_event,
)
from agentgov.human_decision import record_human_decision
from agentgov.development_session import apply_start_plan, build_start_plan
from agentgov.initializer import initialize_project


ROOT = Path(__file__).resolve().parents[1]


def run_git(repository: Path, *args: str) -> str:
    completed = subprocess.run(
        ("git", "-C", str(repository), *args),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        raise AssertionError(completed.stderr.decode("utf-8", errors="replace"))
    return completed.stdout.decode("utf-8", errors="replace").strip()


def create_repository(parent: Path, *, active_task: bool) -> Path:
    root = parent / "repository"
    root.mkdir()
    initialize_project(root, project_name="Coding Agent Stream Fixture", dry_run=False)
    run_git(root, "init", "--quiet")
    run_git(root, "config", "user.email", "fixture@example.invalid")
    run_git(root, "config", "user.name", "Fixture Author")
    (root / "README.md").write_text("# Fixture\n", encoding="utf-8")
    run_git(root, "add", ".")
    run_git(root, "commit", "--quiet", "-m", "baseline")
    if active_task:
        apply_start_plan(
            build_start_plan(
                root,
                title="Exercise the coding-agent stream",
                include_paths=("README.md",),
                validation_commands=("git --version",),
            )
        )
    return root


def event_payload(
    event_type: str,
    *,
    event_digit: str = "a",
    actor_class: str = "coding_agent",
    validation_outcome: str | None = None,
    evidence_ref: str | None = None,
    scope_decision: str | None = None,
    review_outcome: str | None = None,
) -> dict:
    return {
        "contract": "agentgov.coding-agent-event",
        "schema_version": "1.0",
        "event_id": "evt-" + event_digit * 32,
        "occurred_at": "2026-08-06T00:00:00.000Z",
        "event_type": event_type,
        "source": {"adapter_id": "fixture.coding-agent", "actor_class": actor_class},
        "correlation_id": "session-001",
        "facts": {
            "validation_outcome": validation_outcome,
            "evidence_ref": evidence_ref,
            "scope_decision": scope_decision,
            "review_outcome": review_outcome,
        },
    }


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


class CodingAgentEventContractTests(unittest.TestCase):
    def test_accepts_minimal_events_without_prompt_source_or_path_claims(self) -> None:
        event = coding_agent_event_from_payload(event_payload("implementation.changed"))

        self.assertEqual(event.event_type, "implementation.changed")
        self.assertEqual(event.source["adapter_id"], "fixture.coding-agent")
        self.assertNotIn("prompt", event.__dict__)
        self.assertNotIn("changed_paths", event.facts)

    def test_rejects_unknown_prompt_source_authority_and_unsafe_reference_fields(self) -> None:
        prompt = event_payload("task.requested")
        prompt["prompt"] = "private user request"
        source = event_payload("implementation.changed")
        source["source_code"] = "secret"
        authority = event_payload("repository.activated")
        authority["authority_boundary"] = {"authorizes_commit": True}
        absolute = event_payload(
            "validation.completed",
            validation_outcome="passed",
            evidence_ref="C:\\private\\evidence.json",
        )

        for payload in (prompt, source, authority, absolute):
            with self.subTest(fields=set(payload)), self.assertRaises(
                CodingAgentTransportError
            ):
                coding_agent_event_from_payload(payload)

    def test_rejects_agent_owned_scope_and_review_decisions(self) -> None:
        scope = event_payload("scope.decision_recorded", scope_decision="approved")
        review = event_payload("session.reviewed", review_outcome="accepted")

        for payload in (scope, review):
            with self.assertRaises(CodingAgentTransportError):
                coding_agent_event_from_payload(payload)

        human_review = coding_agent_event_from_payload(
            event_payload(
                "session.reviewed",
                actor_class="human",
                review_outcome="accepted",
            )
        )
        self.assertEqual(human_review.facts["review_outcome"], "accepted")

    def test_input_and_card_schemas_are_strict_and_deny_consequential_authority(self) -> None:
        event_schema = json.loads(
            (ROOT / "schemas/coding-agent-event.schema.json").read_text(encoding="utf-8")
        )
        card_schema = json.loads(
            (ROOT / "schemas/interaction-card.schema.json").read_text(encoding="utf-8")
        )
        response_schema = json.loads(
            (ROOT / "schemas/coding-agent-response.schema.json").read_text(
                encoding="utf-8"
            )
        )

        self.assertFalse(event_schema["additionalProperties"])
        self.assertNotIn("prompt", event_schema["properties"])
        self.assertNotIn("changed_paths", event_schema["properties"]["facts"]["properties"])
        self.assertEqual(response_schema["properties"]["schema_version"]["const"], "1.2")
        self.assertIn("interaction", response_schema["required"])
        self.assertIn("decision_prompt", response_schema["required"])
        for rule in card_schema["properties"]["authority_boundary"]["properties"].values():
            self.assertIs(rule["const"], False)


@unittest.skipUnless(shutil.which("git"), "Git is required for coding-agent stream fixtures")
class CodingAgentTransportTests(unittest.TestCase):
    def test_repository_activation_returns_bounded_task_card(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = create_repository(Path(temp_dir), active_task=True)
            event = coding_agent_event_from_payload(event_payload("repository.activated"))

            response = run_coding_agent_event(
                root,
                event=event,
                sequence=1,
                dashboard_output=Path(".agentgov/dashboard.html"),
            )
            payload = json.loads(render_coding_agent_response_json(response))

        self.assertEqual(payload["event"]["adapter_id"], "fixture.coding-agent")
        self.assertEqual(payload["card"]["kind"], "task")
        self.assertEqual(payload["card"]["status"], "active")
        self.assertEqual(payload["card"]["actions"], ["continue", "request_scope_decision"])
        self.assertIsNone(payload["interaction"])
        self.assertIsNone(payload["decision_prompt"])
        self.assertNotIn("git --version", json.dumps(payload["card"]))
        self.assertTrue(all(value is False for value in payload["card"]["authority_boundary"].values()))

    def test_missing_active_task_returns_admission_card_without_inferring_prompt_scope(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = create_repository(Path(temp_dir), active_task=False)
            event = coding_agent_event_from_payload(event_payload("task.requested"))

            response = run_coding_agent_event(
                root,
                event=event,
                sequence=1,
                dashboard_output=Path(".agentgov/dashboard.html"),
            )

        self.assertEqual(response.cycle.status, "needs_human")
        self.assertEqual(response.card.kind, "task")
        self.assertEqual(response.card.status, "review_required")
        self.assertIn("not inferred from prompts", response.card.facts[0]["value"])
        self.assertEqual(response.card.facts[1]["label"], "routing_contract")
        self.assertIn("agentgov.work-request 1.0", response.card.facts[1]["value"])
        self.assertEqual(response.card.facts[2]["label"], "proposal_contract")
        self.assertIn("agentgov.task-proposal 1.0", response.card.facts[2]["value"])
        self.assertIn("route_work_request", response.card.actions)
        self.assertIn("prepare_task_proposal", response.card.actions)
        self.assertEqual(response.interaction.kind, "task_admission")
        self.assertEqual(response.interaction.binding["decision_recording"], "adapter_event")
        self.assertEqual(response.decision_prompt.kind, "task_routing")
        self.assertEqual(response.decision_prompt.input["mode"], "single_select")

    def test_completion_request_returns_review_card_from_agentgov_evidence(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = create_repository(Path(temp_dir), active_task=True)
            (root / "README.md").write_text("# Fixture\n\nCompleted.\n", encoding="utf-8")
            event = coding_agent_event_from_payload(event_payload("completion.requested"))

            response = run_coding_agent_event(
                root,
                event=event,
                sequence=1,
                dashboard_output=Path(".agentgov/dashboard.html"),
            )

        self.assertEqual(response.cycle.status, "review_ready")
        self.assertEqual(response.card.kind, "completion")
        self.assertEqual(response.card.actions, ("accept", "request_changes"))
        self.assertEqual(response.card.facts[0], {"label": "scope", "value": "passed"})
        self.assertEqual(response.card.facts[1]["value"], "passed")
        self.assertEqual(response.card.facts[2]["value"], "verified")
        self.assertEqual(response.interaction.kind, "completion_review")
        self.assertEqual(response.decision_prompt.kind, "completion_review")
        self.assertEqual(
            response.interaction.options[0]["next_event"]["event_type"],
            "session.reviewed",
        )

        result = record_human_decision(
            response.decision_prompt,
            selected_option_id="accept",
            adapter_id="agentgov.reference-adapter",
            recording_method="host_single_select",
            recorded_at="2026-08-06T00:00:01.000Z",
        )
        next_event = coding_agent_event_from_human_decision(
            response,
            result,
            event_id="evt-" + "f" * 32,
            occurred_at="2026-08-06T00:00:02.000Z",
        )
        self.assertEqual(next_event.event_type, "session.reviewed")
        self.assertEqual(next_event.source["actor_class"], "human")
        self.assertEqual(next_event.facts["review_outcome"], "accepted")

    def test_implementation_change_derives_paths_and_blocks_out_of_scope_work(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = create_repository(Path(temp_dir), active_task=True)
            (root / "OUTSIDE.md").write_text("outside\n", encoding="utf-8")
            event = coding_agent_event_from_payload(event_payload("implementation.changed"))

            response = run_coding_agent_event(
                root,
                event=event,
                sequence=1,
                dashboard_output=Path(".agentgov/dashboard.html"),
            )

        self.assertEqual(response.cycle.status, "blocked")
        self.assertEqual(response.cycle.actions[0]["name"], "check_scope")
        self.assertEqual(response.cycle.actions[0]["outcome"], "blocked")
        self.assertEqual(response.card.kind, "scope")
        self.assertEqual(response.interaction.kind, "scope_resolution")
        self.assertFalse(response.interaction.authority_boundary["decision_applied"])

    def test_completion_scope_failure_returns_scope_resolution_not_fake_review(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = create_repository(Path(temp_dir), active_task=True)
            (root / "OUTSIDE.md").write_text("outside\n", encoding="utf-8")
            event = coding_agent_event_from_payload(event_payload("completion.requested"))

            response = run_coding_agent_event(
                root,
                event=event,
                sequence=1,
                dashboard_output=Path(".agentgov/dashboard.html"),
            )

        self.assertEqual(response.cycle.status, "blocked")
        self.assertEqual(response.card.kind, "scope")
        self.assertEqual(response.interaction.kind, "scope_resolution")
        self.assertNotIn("accept", response.card.actions)

    def test_stream_cli_processes_multiple_events_in_one_foreground_process(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = create_repository(Path(temp_dir), active_task=True)
            stream = "\n".join(
                json.dumps(payload)
                for payload in (
                    event_payload("repository.activated", event_digit="a"),
                    event_payload("task.requested", event_digit="b"),
                )
            ) + "\n"

            code, stdout, stderr = run_cli_with_stdin(
                stream,
                "dev",
                str(root),
                "--stream",
                "--format",
                "json",
            )
            responses = [json.loads(line) for line in stdout.splitlines()]

        self.assertEqual(code, EXIT_PASS)
        self.assertEqual(stderr, "")
        self.assertEqual([item["sequence"] for item in responses], [1, 2])
        self.assertEqual([item["card"]["kind"] for item in responses], ["task", "task"])

    def test_stream_stops_at_first_invalid_record_before_its_coordinator_action(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = create_repository(Path(temp_dir), active_task=False)
            invalid = event_payload("task.requested", event_digit="b")
            invalid["prompt"] = "must never be accepted"
            stream = (
                json.dumps(event_payload("repository.activated", event_digit="a"))
                + "\n"
                + json.dumps(invalid)
                + "\n"
                + json.dumps(event_payload("task.requested", event_digit="c"))
                + "\n"
            )

            code, stdout, stderr = run_cli_with_stdin(
                stream,
                "dev",
                str(root),
                "--stream",
                "--format",
                "json",
            )

        self.assertEqual(code, EXIT_ERROR)
        self.assertEqual(len(stdout.splitlines()), 1)
        self.assertIn("line 2", stderr)
        self.assertIn("unexpected fields", stderr)

    def test_stream_rejects_duplicate_ids_and_connection_identity_drift(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = create_repository(Path(temp_dir), active_task=False)
            first = event_payload("repository.activated", event_digit="a")
            duplicate = event_payload("task.requested", event_digit="a")
            code, stdout, stderr = run_cli_with_stdin(
                json.dumps(first) + "\n" + json.dumps(duplicate) + "\n",
                "dev",
                str(root),
                "--stream",
                "--format",
                "json",
            )

            drifted = event_payload("task.requested", event_digit="b")
            drifted["correlation_id"] = "session-002"
            drift_code, drift_stdout, drift_stderr = run_cli_with_stdin(
                json.dumps(first) + "\n" + json.dumps(drifted) + "\n",
                "dev",
                str(root),
                "--stream",
                "--format",
                "json",
            )

        self.assertEqual(code, EXIT_ERROR)
        self.assertEqual(len(stdout.splitlines()), 1)
        self.assertIn("duplicate event_id", stderr)
        self.assertEqual(drift_code, EXIT_ERROR)
        self.assertEqual(len(drift_stdout.splitlines()), 1)
        self.assertIn("must remain stable", drift_stderr)

    def test_empty_stream_is_an_explicit_error(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = create_repository(Path(temp_dir), active_task=False)
            code, stdout, stderr = run_cli_with_stdin(
                "", "dev", str(root), "--stream", "--format", "json"
            )

        self.assertEqual(code, EXIT_ERROR)
        self.assertEqual(stdout, "")
        self.assertIn("expected at least one JSONL event", stderr)

    def test_stream_rejects_single_cycle_event_options(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = create_repository(Path(temp_dir), active_task=False)
            stream = json.dumps(event_payload("repository.activated")) + "\n"
            code, stdout, stderr = run_cli_with_stdin(
                stream,
                "dev",
                str(root),
                "--stream",
                "--event",
                "completion.requested",
                "--format",
                "json",
            )

        self.assertEqual(code, EXIT_ERROR)
        self.assertEqual(stdout, "")
        self.assertIn("belong to single-cycle mode", stderr)


if __name__ == "__main__":
    unittest.main()
