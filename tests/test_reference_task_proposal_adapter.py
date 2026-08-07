from __future__ import annotations

import json
import traceback
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from agentgov.reference_task_proposal_adapter import (
    MAX_NATURAL_LANGUAGE_REQUEST_CHARACTERS,
    ReferenceTaskProposalAdapter,
    ReferenceTaskProposalAdapterError,
    TaskProposalDraft,
)
from agentgov.task_proposal import (
    apply_task_admission_plan,
    render_task_admission_plan_json,
    request_task_admission_confirmation,
    validate_task_proposal_document,
)


class FixtureTaskProposalMaterializer:
    """Offline stand-in for semantic work performed by a Coding Agent host."""

    def __init__(self) -> None:
        self.calls = 0
        self.invalid_scope = False
        self.fail_with_secret = False

    def materialize_task_proposal(self, request_text: str) -> TaskProposalDraft:
        self.calls += 1
        if self.fail_with_secret:
            raise RuntimeError("raw-secret-from-host")
        if "ordinary request" not in request_text:
            raise ValueError("fixture expected ordinary user language")
        include_paths = ("C:/Users/private/project",) if self.invalid_scope else ("src", "tests")
        return TaskProposalDraft(
            task_id="add-health-check",
            title="Add a bounded health check",
            requirement_summary=(
                "Expose one repository-local health check with deterministic tests."
            ),
            include_paths=include_paths,
            exclude_paths=("release",),
            acceptance_signals=("The health check and its focused tests pass.",),
            validation_commands=("python -m unittest tests.test_health -v",),
            owner="Human product owner",
            risk_items=("A route name may already exist.",),
            assumptions=("The project already has an HTTP application.",),
            unknowns=("The final route name still needs human review.",),
        )


def repository(path: Path) -> Path:
    (path / "governance/tasks").mkdir(parents=True)
    return path


class ReferenceTaskProposalAdapterTests(unittest.TestCase):
    def test_ordinary_request_becomes_existing_strict_read_only_preview(self) -> None:
        raw_request = "RAW_REQUEST_93c1 ordinary request from the product owner"
        materializer = FixtureTaskProposalMaterializer()
        with TemporaryDirectory() as temp_dir:
            root = repository(Path(temp_dir))
            prepared = ReferenceTaskProposalAdapter(materializer).prepare(root, raw_request)

            self.assertEqual(materializer.calls, 1)
            self.assertFalse((root / prepared.plan.target).exists())
            self.assertEqual(validate_task_proposal_document(prepared.plan.proposal), [])
            self.assertEqual(prepared.plan.proposal["source"]["actor_class"], "coding_agent")
            self.assertRegex(prepared.plan.proposal["proposal_id"], r"^prp-[0-9a-f]{32}$")
            self.assertEqual(prepared.plan.task_document["decision"]["state"], "admitted")
            self.assertFalse(prepared.repository_modified)
            self.assertFalse(prepared.task_admitted)
            self.assertFalse(prepared.session_started)

    def test_result_and_preview_do_not_retain_raw_request(self) -> None:
        raw_request = "RAW_REQUEST_61ad ordinary request with private conversational wording"
        with TemporaryDirectory() as temp_dir:
            prepared = ReferenceTaskProposalAdapter(
                FixtureTaskProposalMaterializer()
            ).prepare(repository(Path(temp_dir)), raw_request)
            rendered = render_task_admission_plan_json(prepared.plan)
            evidence = {
                "materializer_invocations": prepared.materializer_invocations,
                "agentgov_model_calls": prepared.agentgov_model_calls,
                "agentgov_network_calls": prepared.agentgov_network_calls,
                "result_contains_raw_request": prepared.result_contains_raw_request,
                "core_received_raw_request": prepared.core_received_raw_request,
            }

            self.assertNotIn(raw_request, rendered)
            self.assertNotIn("request_text", rendered)
            self.assertNotIn(raw_request, json.dumps(evidence))
            self.assertEqual(evidence["materializer_invocations"], 1)
            self.assertEqual(evidence["agentgov_model_calls"], 0)
            self.assertEqual(evidence["agentgov_network_calls"], 0)
            self.assertFalse(evidence["result_contains_raw_request"])
            self.assertFalse(evidence["core_received_raw_request"])
            self.assertTrue(
                all(value is False for value in prepared.plan.proposal["content_boundary"].values())
            )
            self.assertTrue(
                all(value is False for value in prepared.plan.proposal["authority_boundary"].values())
            )

    def test_existing_exact_human_admission_is_still_the_only_write_boundary(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = repository(Path(temp_dir))
            prepared = ReferenceTaskProposalAdapter(
                FixtureTaskProposalMaterializer()
            ).prepare(root, "an ordinary request")

            self.assertFalse(
                request_task_admission_confirmation(
                    prepared.plan,
                    decision_reader=lambda _: "ADMIT",
                    is_interactive_terminal=False,
                )
            )
            self.assertFalse((root / prepared.plan.target).exists())
            self.assertTrue(
                request_task_admission_confirmation(
                    prepared.plan,
                    decision_reader=lambda _: "ADMIT",
                    is_interactive_terminal=True,
                )
            )
            result = apply_task_admission_plan(prepared.plan)

            self.assertTrue((root / result.target).is_file())
            self.assertFalse((root / ".agentgov").exists())
            self.assertEqual(
                sorted(
                    path.relative_to(root).as_posix()
                    for path in root.rglob("*")
                    if path.is_file()
                ),
                [result.target],
            )

    def test_adapter_owns_identity_privacy_authority_and_low_risk_boundary(self) -> None:
        with TemporaryDirectory() as temp_dir:
            prepared = ReferenceTaskProposalAdapter(
                FixtureTaskProposalMaterializer(), adapter_id="fixture-host"
            ).prepare(repository(Path(temp_dir)), "one ordinary request")
            proposal = prepared.plan.proposal

            self.assertEqual(proposal["source"], {
                "adapter_id": "fixture-host",
                "actor_class": "coding_agent",
            })
            self.assertEqual(proposal["task"]["risk"]["level"], "low")
            self.assertFalse(prepared.authorizes_code_change)
            self.assertFalse(prepared.authorizes_scope_expansion)
            self.assertFalse(prepared.authorizes_exception)
            self.assertFalse(prepared.authorizes_git_operations)
            self.assertFalse(prepared.authorizes_deployment)
            self.assertFalse(prepared.authorizes_release)

    def test_invalid_normalized_draft_fails_before_write_and_fresh_retry_succeeds(self) -> None:
        materializer = FixtureTaskProposalMaterializer()
        materializer.invalid_scope = True
        with TemporaryDirectory() as temp_dir:
            root = repository(Path(temp_dir))
            with self.assertRaisesRegex(
                ReferenceTaskProposalAdapterError,
                "normalized task-proposal draft was rejected",
            ):
                ReferenceTaskProposalAdapter(materializer).prepare(
                    root, "an ordinary request"
                )
            self.assertEqual(list((root / "governance/tasks").iterdir()), [])

            materializer.invalid_scope = False
            recovered = ReferenceTaskProposalAdapter(materializer).prepare(
                root, "corrected ordinary request"
            )
            self.assertEqual(materializer.calls, 2)
            self.assertEqual(recovered.plan.target, "governance/tasks/add-health-check.json")

    def test_materializer_failure_is_bounded_and_does_not_echo_internal_text(self) -> None:
        materializer = FixtureTaskProposalMaterializer()
        materializer.fail_with_secret = True
        with TemporaryDirectory() as temp_dir:
            with self.assertRaises(ReferenceTaskProposalAdapterError) as raised:
                ReferenceTaskProposalAdapter(materializer).prepare(
                    repository(Path(temp_dir)), "an ordinary request"
                )

            self.assertNotIn("raw-secret-from-host", str(raised.exception))
            rendered = "".join(
                traceback.format_exception(
                    type(raised.exception), raised.exception, raised.exception.__traceback__
                )
            )
            self.assertNotIn("raw-secret-from-host", rendered)
            self.assertEqual(materializer.calls, 1)

    def test_direct_normalized_draft_reports_no_materializer_invocation(self) -> None:
        materializer = FixtureTaskProposalMaterializer()
        draft = materializer.materialize_task_proposal("one ordinary request")
        with TemporaryDirectory() as temp_dir:
            prepared = ReferenceTaskProposalAdapter(materializer).prepare_from_draft(
                repository(Path(temp_dir)), draft
            )

            self.assertEqual(prepared.materializer_invocations, 0)
            self.assertEqual(materializer.calls, 1)

    def test_blank_oversized_or_wrong_materializer_output_fails_closed(self) -> None:
        class WrongMaterializer:
            def materialize_task_proposal(self, request_text: str) -> object:
                return {"task_id": "not-a-draft"}

        with TemporaryDirectory() as temp_dir:
            root = repository(Path(temp_dir))
            adapter = ReferenceTaskProposalAdapter(FixtureTaskProposalMaterializer())
            with self.assertRaisesRegex(ReferenceTaskProposalAdapterError, "non-empty"):
                adapter.prepare(root, "  ")
            with self.assertRaisesRegex(ReferenceTaskProposalAdapterError, "input limit"):
                adapter.prepare(
                    root, "x" * (MAX_NATURAL_LANGUAGE_REQUEST_CHARACTERS + 1)
                )
            with self.assertRaisesRegex(ReferenceTaskProposalAdapterError, "must return"):
                ReferenceTaskProposalAdapter(WrongMaterializer()).prepare(
                    root, "an ordinary request"
                )


if __name__ == "__main__":
    unittest.main()
