from __future__ import annotations

import json
import subprocess
import tomllib
import unittest
from unittest import mock
from dataclasses import asdict
from pathlib import Path
from tempfile import TemporaryDirectory

from agentgov.admission_routing import build_admission_route
from agentgov.codex_hooks import CODEX_HOST_CAPABILITIES
from agentgov.coding_agent_transport import InteractionCard
from agentgov.cli import EXIT_FAIL, EXIT_PASS
from agentgov.host_interaction import build_host_interaction_request
from agentgov.human_decision import (
    DECISION_PROMPT_CONTRACT,
    DECISION_RESULT_CONTRACT,
    HumanDecisionError,
    apply_route_human_decision,
    build_host_decision_prompt,
    build_route_decision_prompt,
    human_decision_prompt_from_payload,
    human_decision_result_from_payload,
    record_human_decision,
    render_human_decision_prompt_terminal,
    request_reference_terminal_selection,
    validate_result_for_prompt,
)
from tests.test_admission_routing import create_repository, proposal, request, run_cli, write_json


ROOT = Path(__file__).resolve().parents[1]


def card(*, kind: str, status: str) -> InteractionCard:
    return InteractionCard(
        contract="agentgov.interaction-card",
        schema_version="1.0",
        kind=kind,
        status=status,
        title=f"{kind} decision",
        summary="One bounded human choice is required.",
        facts=({"label": "scope", "value": "bounded"},),
        actions=("review", "decline"),
        authority_boundary={
            "authorizes_scope_expansion": False,
            "authorizes_exception": False,
            "authorizes_commit": False,
            "authorizes_merge": False,
            "authorizes_deployment": False,
        },
    )


def interaction(kind: str):
    statuses = {
        "task": "review_required",
        "scope": "blocked",
        "completion": "review_ready",
    }
    return build_host_interaction_request(
        event_id="evt-" + "a" * 32,
        card=card(kind=kind, status=statuses[kind]),
    )


class HumanDecisionTests(unittest.TestCase):
    def test_schemas_are_strict_vendor_neutral_and_packaged(self) -> None:
        prompt_schema = json.loads(
            (ROOT / "schemas/human-decision-prompt.schema.json").read_text(encoding="utf-8")
        )
        result_schema = json.loads(
            (ROOT / "schemas/human-decision-result.schema.json").read_text(encoding="utf-8")
        )
        rendered = json.dumps((prompt_schema, result_schema), sort_keys=True).lower()
        package = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))

        self.assertFalse(prompt_schema["additionalProperties"])
        self.assertFalse(result_schema["additionalProperties"])
        self.assertEqual(prompt_schema["properties"]["contract"]["const"], DECISION_PROMPT_CONTRACT)
        self.assertEqual(result_schema["properties"]["contract"]["const"], DECISION_RESULT_CONTRACT)
        self.assertNotIn("codex", rendered)
        self.assertIn(
            "schemas/*.schema.json",
            package["tool"]["setuptools"]["data-files"][
                "share/agent-governance-starter/schemas"
            ],
        )

    def test_host_gate_becomes_proactive_single_select_without_free_text(self) -> None:
        prompt = build_host_decision_prompt(interaction("scope"))
        terminal = render_human_decision_prompt_terminal(prompt)

        self.assertEqual(prompt.kind, "scope_resolution")
        self.assertEqual(prompt.recommended_option_id, "narrow_changes")
        self.assertEqual(prompt.input["maximum_selections"], 1)
        self.assertFalse(prompt.input["free_text_required"])
        self.assertIn("HUMAN DECISION REQUIRED", terminal)
        self.assertIn("[recommended safe default]", terminal)
        self.assertIn("select one number", terminal)
        self.assertNotIn("ADMIT", terminal)
        self.assertTrue(all(value is False for value in prompt.authority_boundary.values()))

    def test_reference_terminal_records_one_numeric_selection_not_magic_words(self) -> None:
        prompt = build_host_decision_prompt(interaction("completion"))
        result = request_reference_terminal_selection(
            prompt,
            decision_reader=lambda _: "1",
            is_interactive_terminal=True,
        )

        self.assertEqual(result.selection["option_id"], "accept")
        self.assertEqual(result.selection["transition"]["event_type"], "session.reviewed")
        self.assertEqual(result.actor["actor_class"], "human")
        self.assertEqual(result.actor["recording_method"], "reference_terminal_single_select")
        self.assertTrue(result.authority_boundary["decision_recorded"])
        self.assertFalse(result.authority_boundary["decision_applied"])
        validate_result_for_prompt(prompt, result)
        self.assertNotIn("raw", json.dumps(asdict(result)).lower())

    def test_reference_terminal_rejects_noninteractive_invalid_and_magic_word_input(self) -> None:
        prompt = build_host_decision_prompt(interaction("scope"))
        for selection, interactive in (("1", False), ("ADMIT", True), ("0", True), ("9", True)):
            with self.subTest(selection=selection, interactive=interactive):
                with self.assertRaises(HumanDecisionError):
                    request_reference_terminal_selection(
                        prompt,
                        decision_reader=lambda _, value=selection: value,
                        is_interactive_terminal=interactive,
                    )

    def test_context_only_codex_prompt_is_displayable_but_not_recordable(self) -> None:
        request_value = build_host_interaction_request(
            event_id="evt-" + "b" * 32,
            card=card(kind="scope", status="blocked"),
            capabilities=CODEX_HOST_CAPABILITIES,
        )
        prompt = build_host_decision_prompt(request_value)

        self.assertEqual(prompt.binding["delivery_mode"], "context_only")
        self.assertEqual(prompt.binding["decision_recording"], "unavailable")
        with self.assertRaisesRegex(HumanDecisionError, "cannot record"):
            record_human_decision(
                prompt,
                selected_option_id="narrow_changes",
                adapter_id="openai.codex-hooks",
                recording_method="host_single_select",
            )

    def test_result_rejects_agent_actor_unknown_fields_and_transition_tampering(self) -> None:
        prompt = build_host_decision_prompt(interaction("completion"))
        result = record_human_decision(
            prompt,
            selected_option_id="request_changes",
            adapter_id="agentgov.reference-adapter",
            recording_method="host_single_select",
            recorded_at="2026-08-06T00:00:00.000Z",
        )
        agent = json.loads(json.dumps(asdict(result)))
        agent["actor"]["actor_class"] = "coding_agent"
        unknown = json.loads(json.dumps(asdict(result)))
        unknown["raw_input"] = "2"
        tampered = json.loads(json.dumps(asdict(result)))
        tampered["selection"]["transition"]["fact_value"] = "accepted"

        with self.assertRaises(HumanDecisionError):
            human_decision_result_from_payload(agent)
        with self.assertRaises(HumanDecisionError):
            human_decision_result_from_payload(unknown)
        with self.assertRaises(HumanDecisionError):
            validate_result_for_prompt(prompt, human_decision_result_from_payload(tampered))

    def test_task_route_prompt_exists_only_for_planned_low_risk_human_review(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root, policy_path = create_repository(Path(temp_dir))
            review = build_admission_route(
                root,
                policy_path=policy_path,
                request=request("repository_change", task_proposal=proposal(include="docs")),
            )
            fast = build_admission_route(
                root,
                policy_path=policy_path,
                request=request("repository_change", task_proposal=proposal()),
            )
            material = build_admission_route(
                root,
                policy_path=policy_path,
                request=request(
                    "repository_change",
                    task_proposal=proposal(),
                    architecture_change=True,
                ),
            )

            self.assertEqual(review.route, "human_review")
            self.assertIsNotNone(review.admission_plan)
            prompt = build_route_decision_prompt(review)
            self.assertEqual(prompt.kind, "task_admission")
            self.assertEqual(prompt.recommended_option_id, "request_changes")
            for invalid in (fast, material):
                with self.assertRaises(HumanDecisionError):
                    build_route_decision_prompt(invalid)

    def test_single_approve_selection_creates_only_exact_reviewed_task(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root, policy_path = create_repository(Path(temp_dir))
            route = build_admission_route(
                root,
                policy_path=policy_path,
                request=request("repository_change", task_proposal=proposal(include="docs")),
            )
            prompt = build_route_decision_prompt(route)
            result = request_reference_terminal_selection(
                prompt,
                decision_reader=lambda _: "1",
                is_interactive_terminal=True,
            )

            applied = apply_route_human_decision(route, prompt, result)

            self.assertEqual(applied.task_id, "small-health-check")
            self.assertTrue((root / "governance/tasks/small-health-check.json").is_file())
            self.assertFalse((root / ".agentgov").exists())
            self.assertFalse((root / ".codex").exists())

    def test_change_or_reject_selection_records_decision_without_writing(self) -> None:
        for selected in ("request_changes", "reject"):
            with self.subTest(selected=selected), TemporaryDirectory() as temp_dir:
                root, policy_path = create_repository(Path(temp_dir))
                route = build_admission_route(
                    root,
                    policy_path=policy_path,
                    request=request("repository_change", task_proposal=proposal(include="docs")),
                )
                prompt = build_route_decision_prompt(route)
                result = record_human_decision(
                    prompt,
                    selected_option_id=selected,
                    adapter_id="agentgov.reference-adapter",
                    recording_method="host_single_select",
                )
                before = subprocess.check_output(
                    ("git", "-C", str(root), "status", "--porcelain", "-uall")
                )

                self.assertIsNone(apply_route_human_decision(route, prompt, result))
                after = subprocess.check_output(
                    ("git", "-C", str(root), "status", "--porcelain", "-uall")
                )

                self.assertEqual(after, before)
                self.assertFalse((root / "governance/tasks/small-health-check.json").exists())

    def test_prompt_or_route_drift_fails_before_apply(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root, policy_path = create_repository(Path(temp_dir))
            route = build_admission_route(
                root,
                policy_path=policy_path,
                request=request("repository_change", task_proposal=proposal(include="docs")),
            )
            prompt = build_route_decision_prompt(route)
            result = record_human_decision(
                prompt,
                selected_option_id="approve_exact_task",
                adapter_id="agentgov.reference-adapter",
                recording_method="host_single_select",
            )
            policy_value = json.loads(policy_path.read_text(encoding="utf-8"))
            policy_value["decision"]["rationale"] += " Changed after display."
            policy_path.write_text(json.dumps(policy_value, indent=2) + "\n", encoding="utf-8")

            with self.assertRaisesRegex(HumanDecisionError, "drifted|changed"):
                apply_route_human_decision(route, prompt, result)
            self.assertFalse((root / "governance/tasks/small-health-check.json").exists())

    def test_target_race_fails_without_overwrite(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root, policy_path = create_repository(Path(temp_dir))
            route = build_admission_route(
                root,
                policy_path=policy_path,
                request=request("repository_change", task_proposal=proposal(include="docs")),
            )
            prompt = build_route_decision_prompt(route)
            result = record_human_decision(
                prompt,
                selected_option_id="approve_exact_task",
                adapter_id="agentgov.reference-adapter",
                recording_method="host_single_select",
            )
            target = root / "governance/tasks/small-health-check.json"
            target.write_text("someone else's task\n", encoding="utf-8")

            with self.assertRaises(HumanDecisionError):
                apply_route_human_decision(route, prompt, result)
            self.assertEqual(target.read_text(encoding="utf-8"), "someone else's task\n")

    def test_prompt_parser_rejects_authority_and_recommendation_drift(self) -> None:
        prompt = build_host_decision_prompt(interaction("scope"))
        authority = json.loads(json.dumps(asdict(prompt)))
        authority["authority_boundary"]["decision_recorded"] = True
        recommendation = json.loads(json.dumps(asdict(prompt)))
        recommendation["recommended_option_id"] = "approve_everything"

        for invalid in (authority, recommendation):
            with self.assertRaises(HumanDecisionError):
                human_decision_prompt_from_payload(invalid)

    def test_cli_proactively_prompts_once_and_applies_numeric_approval(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root, policy_path = create_repository(Path(temp_dir))
            request_path = write_json(
                root / "request.json",
                request("repository_change", task_proposal=proposal(include="docs")),
            )
            with mock.patch("agentgov.cli.sys.stdin.isatty", return_value=True), mock.patch(
                "builtins.input", return_value="1"
            ) as decision:
                code, stdout, stderr = run_cli(
                    "route", "request", str(request_path), "--policy", str(policy_path),
                    "--repository", str(root), "--prompt-human",
                )

            self.assertEqual(code, EXIT_PASS, stderr)
            self.assertEqual(decision.call_count, 1)
            self.assertIn("HUMAN DECISION REQUIRED", stdout)
            self.assertIn("DECISION_RECORDED approve_exact_task", stdout)
            self.assertIn("ADMITTED small-health-check", stdout)
            self.assertTrue((root / "governance/tasks/small-health-check.json").is_file())

    def test_cli_does_not_prompt_zero_interruption_route_and_fails_closed_headless(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root, policy_path = create_repository(Path(temp_dir))
            fast_path = write_json(
                root / "fast-request.json",
                request("repository_change", task_proposal=proposal()),
            )
            review_path = write_json(
                root / "review-request.json",
                request(
                    "repository_change",
                    task_proposal=proposal(task_id="docs-task", include="docs"),
                ),
            )
            with mock.patch("builtins.input") as decision:
                fast_code, fast_stdout, fast_stderr = run_cli(
                    "route", "request", str(fast_path), "--policy", str(policy_path),
                    "--repository", str(root), "--prompt-human",
                )
            with mock.patch("agentgov.cli.sys.stdin.isatty", return_value=False):
                review_code, _, review_stderr = run_cli(
                    "route", "request", str(review_path), "--policy", str(policy_path),
                    "--repository", str(root), "--prompt-human",
                )

            self.assertEqual(fast_code, EXIT_PASS, fast_stderr)
            self.assertIn("NO_HUMAN_PROMPT route fast_track", fast_stdout)
            decision.assert_not_called()
            self.assertEqual(review_code, EXIT_FAIL)
            self.assertIn("requires an interactive terminal", review_stderr)
            self.assertFalse((root / "governance/tasks/docs-task.json").exists())


if __name__ == "__main__":
    unittest.main()
