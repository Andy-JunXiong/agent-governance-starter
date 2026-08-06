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

from agentgov.alignment_transport import AlignmentStreamSession
from agentgov.cli import EXIT_ERROR, EXIT_PASS, main
from agentgov.human_decision import canonical_document_digest, record_human_decision
from agentgov.semantic_review import semantic_authority_boundary, semantic_content_boundary
from agentgov.self_review_transport import (
    SELF_REVIEW_DRAFT_CONTRACT,
    SELF_REVIEW_RESPONSE_CONTRACT,
    SELF_REVIEW_START_CONTRACT,
    ActiveAgentSelfReviewStreamSession,
    SelfReviewTransportError,
    active_agent_self_review_stream_response_from_payload,
)
from tests.test_clarification_dialogue import context, resolutions


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "governance/fixtures/semantic-review"
EVIDENCE = "docs/product-requirements-automatic-governance.md"
ADAPTER_ID = "fixture.coding-agent"
DECISION_ADAPTER_ID = "agentgov.reference-adapter"


def provider_payload(name: str = "codex-self-review.json") -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def resolved_alignment():
    session = AlignmentStreamSession()
    context_payload = context(
        unknowns=[], candidates=resolutions(), recommendation="return_to_center"
    )
    ready = session.process_payload(context_payload, sequence=1)
    result = record_human_decision(
        ready.decision_prompt,
        selected_option_id="return_to_center",
        adapter_id=DECISION_ADAPTER_ID,
        recording_method="host_single_select",
        recorded_at="2026-08-06T00:00:05.000Z",
    )
    resolved = session.process_payload(asdict(result), sequence=2)
    return session, context_payload, result, resolved


def start_payload(resolved, provider_name: str = "codex-self-review.json") -> dict:
    return {
        "contract": SELF_REVIEW_START_CONTRACT,
        "schema_version": "1.0",
        "start_id": "asx-" + "1" * 32,
        "source": {"adapter_id": ADAPTER_ID, "actor_class": "coding_agent"},
        "alignment": {
            "dialogue_id": resolved.dialogue.dialogue_id,
            "revision": resolved.dialogue.revision,
            "digest": canonical_document_digest(asdict(resolved.dialogue)),
        },
        "risk": {"level": "medium", "reason_codes": ["requirement_ambiguity"]},
        "provider": provider_payload(provider_name),
        "allowed_evidence_refs": [EVIDENCE],
        "content_boundary": semantic_content_boundary(),
        "authority_boundary": semantic_authority_boundary(),
    }


def draft_payload(request: dict) -> dict:
    return {
        "contract": SELF_REVIEW_DRAFT_CONTRACT,
        "schema_version": "1.0",
        "draft_id": "asd-" + "2" * 32,
        "source": {"adapter_id": ADAPTER_ID, "actor_class": "coding_agent"},
        "request": {
            "request_id": request["request_id"],
            "request_digest": request["request_digest"],
        },
        "observations": [
            {
                "kind": "requirement",
                "summary": "The selected center is consistent; fallback ownership remains unknown.",
                "evidence_refs": [EVIDENCE],
                "assumptions": ["The resolved alignment remains active."],
                "unknowns": ["The production host integration owner is not named."],
                "recommended_question": "Who owns the production host integration?",
            }
        ],
        "content_boundary": semantic_content_boundary(),
        "authority_boundary": semantic_authority_boundary(),
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


class SelfReviewStreamSessionTests(unittest.TestCase):
    def test_start_returns_deterministic_ephemeral_materialization_request(self) -> None:
        alignment_session, _, _, resolved = resolved_alignment()
        payload = start_payload(resolved)
        first = ActiveAgentSelfReviewStreamSession().process_payload(
            payload,
            sequence=3,
            alignment_response=resolved,
            expected_adapter_id=alignment_session.coding_adapter_id,
        )
        second = ActiveAgentSelfReviewStreamSession().process_payload(
            payload,
            sequence=99,
            alignment_response=resolved,
            expected_adapter_id=alignment_session.coding_adapter_id,
        )

        self.assertEqual(first.contract, SELF_REVIEW_RESPONSE_CONTRACT)
        self.assertEqual(first.status, "materialization_required")
        self.assertEqual(first.materialization_request, second.materialization_request)
        self.assertIsNone(first.run)
        self.assertEqual(first.materialization_request["instruction"]["review_mode"], "self_review")
        self.assertEqual(first.materialization_request["context"]["allowed_evidence_refs"], (EVIDENCE,))
        self.assertTrue(all(value is False for value in first.authority_boundary.values()))

    def test_same_adapter_draft_completes_advisory_result_without_core_model_call(self) -> None:
        alignment_session, _, _, resolved = resolved_alignment()
        session = ActiveAgentSelfReviewStreamSession()
        requested = session.process_payload(
            start_payload(resolved), sequence=3, alignment_response=resolved,
            expected_adapter_id=alignment_session.coding_adapter_id,
        )
        completed = session.process_payload(
            draft_payload(requested.materialization_request), sequence=4,
            alignment_response=resolved,
            expected_adapter_id=alignment_session.coding_adapter_id,
        )

        self.assertEqual(completed.status, "completed")
        self.assertIsNone(completed.materialization_request)
        self.assertEqual(completed.run.result.semantics, "advisory")
        self.assertEqual(completed.run.result.assurance["review_mode"], "self_review")
        self.assertEqual(completed.run.execution["materializer_invocations"], 1)
        self.assertEqual(completed.run.execution["agentgov_model_calls"], 0)
        self.assertEqual(completed.run.execution["agentgov_network_calls"], 0)

    def test_codex_and_claude_provider_fixtures_follow_the_same_transport(self) -> None:
        for name in ("codex-self-review.json", "claude-code-self-review.json"):
            with self.subTest(name=name):
                alignment_session, _, _, resolved = resolved_alignment()
                session = ActiveAgentSelfReviewStreamSession()
                requested = session.process_payload(
                    start_payload(resolved, name), sequence=3, alignment_response=resolved,
                    expected_adapter_id=alignment_session.coding_adapter_id,
                )
                completed = session.process_payload(
                    draft_payload(requested.materialization_request), sequence=4,
                    alignment_response=resolved,
                    expected_adapter_id=alignment_session.coding_adapter_id,
                )
                self.assertEqual(
                    completed.run.result.provider["provider_id"],
                    provider_payload(name)["provider_id"],
                )

    def test_unresolved_stale_adapter_and_invalid_risk_fail_before_request(self) -> None:
        alignment_session, context_payload, _, resolved = resolved_alignment()
        unresolved = AlignmentStreamSession().process_payload(context_payload, sequence=1)
        mutations = []
        stale = start_payload(resolved)
        stale["alignment"]["revision"] += 1
        mutations.append((stale, resolved, alignment_session.coding_adapter_id))
        drifted = start_payload(resolved)
        drifted["source"]["adapter_id"] = "different.agent"
        mutations.append((drifted, resolved, alignment_session.coding_adapter_id))
        wrong_risk = start_payload(resolved)
        wrong_risk["risk"]["level"] = "high"
        mutations.append((wrong_risk, resolved, alignment_session.coding_adapter_id))
        mutations.append((start_payload(resolved), unresolved, ADAPTER_ID))
        for payload, response, adapter_id in mutations:
            with self.subTest(payload=payload):
                with self.assertRaises(SelfReviewTransportError):
                    ActiveAgentSelfReviewStreamSession().process_payload(
                        payload, sequence=3, alignment_response=response,
                        expected_adapter_id=adapter_id,
                    )

    def test_invalid_draft_is_atomic_and_valid_retry_succeeds(self) -> None:
        alignment_session, _, _, resolved = resolved_alignment()
        session = ActiveAgentSelfReviewStreamSession()
        requested = session.process_payload(
            start_payload(resolved), sequence=3, alignment_response=resolved,
            expected_adapter_id=alignment_session.coding_adapter_id,
        )
        invalid = draft_payload(requested.materialization_request)
        invalid["request"]["request_digest"] = "sha256:" + "0" * 64
        with self.assertRaisesRegex(SelfReviewTransportError, "stale"):
            session.process_payload(
                invalid, sequence=4, alignment_response=resolved,
                expected_adapter_id=alignment_session.coding_adapter_id,
            )
        completed = session.process_payload(
            draft_payload(requested.materialization_request), sequence=4,
            alignment_response=resolved,
            expected_adapter_id=alignment_session.coding_adapter_id,
        )
        self.assertEqual(completed.status, "completed")
        with self.assertRaisesRegex(SelfReviewTransportError, "duplicate|out of order"):
            session.process_payload(
                draft_payload(requested.materialization_request), sequence=5,
                alignment_response=resolved,
                expected_adapter_id=alignment_session.coding_adapter_id,
            )

    def test_draft_before_start_and_evidence_escape_fail_closed(self) -> None:
        alignment_session, _, _, resolved = resolved_alignment()
        fake_request = {"request_id": "asq-" + "3" * 32, "request_digest": "sha256:" + "4" * 64}
        with self.assertRaisesRegex(SelfReviewTransportError, "pending"):
            ActiveAgentSelfReviewStreamSession().process_payload(
                draft_payload(fake_request), sequence=3, alignment_response=resolved,
                expected_adapter_id=alignment_session.coding_adapter_id,
            )
        session = ActiveAgentSelfReviewStreamSession()
        requested = session.process_payload(
            start_payload(resolved), sequence=3, alignment_response=resolved,
            expected_adapter_id=alignment_session.coding_adapter_id,
        )
        invalid = draft_payload(requested.materialization_request)
        invalid["observations"][0]["evidence_refs"] = ["README.md"]
        with self.assertRaisesRegex(SelfReviewTransportError, "outside"):
            session.process_payload(
                invalid, sequence=4, alignment_response=resolved,
                expected_adapter_id=alignment_session.coding_adapter_id,
            )

    def test_contract_schemas_are_strict_packaged_and_vendor_neutral(self) -> None:
        pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
        for name in (
            "active-agent-self-review-start.schema.json",
            "active-agent-self-review-draft.schema.json",
            "active-agent-self-review-stream-response.schema.json",
        ):
            schema = json.loads((ROOT / "schemas" / name).read_text(encoding="utf-8"))
            self.assertFalse(schema["additionalProperties"])
            self.assertNotIn("codex", json.dumps(schema).lower())
            self.assertNotIn("claude", json.dumps(schema).lower())
        self.assertIn(
            "schemas/*.schema.json",
            pyproject["tool"]["setuptools"]["data-files"]["share/agent-governance-starter/schemas"],
        )

    def test_response_parser_rejects_impossible_status_and_authority_drift(self) -> None:
        alignment_session, _, _, resolved = resolved_alignment()
        response = ActiveAgentSelfReviewStreamSession().process_payload(
            start_payload(resolved), sequence=3, alignment_response=resolved,
            expected_adapter_id=alignment_session.coding_adapter_id,
        )
        impossible = asdict(response)
        impossible["status"] = "completed"
        authority = asdict(response)
        authority["authority_boundary"]["changes_requirements"] = True
        digest = asdict(response)
        digest["materialization_request"]["instruction"]["semantics"] = "binding"
        for payload in (impossible, authority, digest):
            with self.subTest(payload=payload):
                with self.assertRaises(SelfReviewTransportError):
                    active_agent_self_review_stream_response_from_payload(payload)


class SelfReviewLiveCliTests(unittest.TestCase):
    def test_dev_stream_runs_resolve_request_draft_complete_journey(self) -> None:
        alignment_session, context_payload, result, resolved = resolved_alignment()
        builder = ActiveAgentSelfReviewStreamSession()
        start = start_payload(resolved)
        requested = builder.process_payload(
            start, sequence=3, alignment_response=resolved,
            expected_adapter_id=alignment_session.coding_adapter_id,
        )
        draft = draft_payload(requested.materialization_request)
        stream = "\n".join(
            json.dumps(item) for item in (context_payload, asdict(result), start, draft)
        ) + "\n"

        with TemporaryDirectory() as temp_dir:
            code, stdout, stderr = run_cli_with_stdin(
                stream, "dev", temp_dir, "--stream", "--format", "json"
            )
        responses = [json.loads(line) for line in stdout.splitlines()]
        self.assertEqual(code, EXIT_PASS)
        self.assertEqual(stderr, "")
        self.assertEqual([item["sequence"] for item in responses], [1, 2, 3, 4])
        self.assertEqual(
            [item["status"] for item in responses],
            ["ready_for_decision", "resolved", "materialization_required", "completed"],
        )
        self.assertEqual(responses[3]["run"]["execution"]["agentgov_model_calls"], 0)

    def test_dev_stream_reports_exact_line_for_stale_self_review_start(self) -> None:
        _, context_payload, result, resolved = resolved_alignment()
        start = start_payload(resolved)
        start["alignment"]["revision"] += 1
        stream = "\n".join(json.dumps(item) for item in (context_payload, asdict(result), start)) + "\n"
        with TemporaryDirectory() as temp_dir:
            code, stdout, stderr = run_cli_with_stdin(
                stream, "dev", temp_dir, "--stream", "--format", "json"
            )
        self.assertEqual(code, EXIT_ERROR)
        self.assertEqual(len(stdout.splitlines()), 2)
        self.assertIn("line 3", stderr)
        self.assertIn("stale", stderr)


if __name__ == "__main__":
    unittest.main()
