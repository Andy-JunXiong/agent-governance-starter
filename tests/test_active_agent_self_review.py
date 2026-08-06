from __future__ import annotations

import json
import unittest
from dataclasses import asdict, replace
from pathlib import Path

from agentgov.active_agent_self_review import (
    ActiveAgentSelfReviewContext,
    SelfReviewObservationDraft,
)
from agentgov.reference_alignment_adapter import (
    ReferenceAlignmentAdapter,
    ReferenceAlignmentAdapterError,
)
from agentgov.semantic_review import semantic_review_provider_capabilities_from_payload
from tests.test_reference_alignment_adapter import FixtureMaterializer


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "governance/fixtures/semantic-review"
EVIDENCE = "docs/product-requirements-automatic-governance.md"


def provider(name: str):
    payload = json.loads((FIXTURES / name).read_text(encoding="utf-8"))
    return semantic_review_provider_capabilities_from_payload(payload)


def resolved_adapter(*, raw_marker: str = "RAW_MARKER") -> ReferenceAlignmentAdapter:
    adapter = ReferenceAlignmentAdapter(FixtureMaterializer())
    adapter.start(f"{raw_marker} 请用自然语言对齐需求。")
    adapter.answer("先讨论清楚，再进行最终选择。")
    adapter.select("return_to_center")
    return adapter


class FixtureSelfReviewer:
    """Offline stand-in for a review pass supplied by the active Agent host."""

    def __init__(self) -> None:
        self.calls = 0
        self.contexts: list[ActiveAgentSelfReviewContext] = []
        self.output: object = (
            SelfReviewObservationDraft(
                kind="requirement",
                summary="The selected center is consistent, but fallback ownership remains unknown.",
                evidence_refs=(EVIDENCE,),
                assumptions=("The resolved alignment remains the active product direction.",),
                unknowns=("The production host callback is not yet installed.",),
                recommended_question="Who owns the production host integration?",
            ),
        )
        self.failure: Exception | None = None

    def materialize_self_review(self, context: ActiveAgentSelfReviewContext):
        self.calls += 1
        self.contexts.append(context)
        if self.failure is not None:
            raise self.failure
        return self.output


class ActiveAgentSelfReviewTests(unittest.TestCase):
    def test_codex_and_claude_fixtures_use_one_end_to_end_adapter_path(self) -> None:
        for fixture_name in (
            "codex-self-review.json",
            "claude-code-self-review.json",
        ):
            with self.subTest(fixture_name=fixture_name):
                adapter = resolved_adapter()
                reviewer = FixtureSelfReviewer()
                active_provider = provider(fixture_name)

                run = adapter.self_review(
                    reviewer,
                    provider=active_provider,
                    reason_codes=("requirement_ambiguity",),
                    allowed_evidence_refs=(EVIDENCE,),
                )

                self.assertEqual(reviewer.calls, 1)
                self.assertEqual(run.route.route, "self_review")
                self.assertEqual(
                    run.route.provider["provider_id"], active_provider.provider_id
                )
                self.assertEqual(run.result.semantics, "advisory")
                self.assertEqual(run.result.assurance["review_mode"], "self_review")
                self.assertEqual(run.execution["materializer_invocations"], 1)
                self.assertEqual(run.execution["agentgov_model_calls"], 0)
                self.assertEqual(run.execution["agentgov_network_calls"], 0)
                self.assertTrue(
                    all(value is False for value in run.authority_boundary.values())
                )
                self.assertTrue(
                    all(value is False for value in run.privacy_boundary.values())
                )

    def test_materializer_receives_only_resolved_normalized_ephemeral_context(self) -> None:
        raw_marker = "RAW_REQUEST_63d9"
        adapter = resolved_adapter(raw_marker=raw_marker)
        reviewer = FixtureSelfReviewer()

        run = adapter.self_review(
            reviewer,
            provider=provider("codex-self-review.json"),
            reason_codes=("scope_drift",),
            allowed_evidence_refs=(EVIDENCE,),
        )
        context = reviewer.contexts[0]
        rendered = json.dumps(
            {"context": asdict(context), "run": asdict(run)},
            ensure_ascii=False,
            sort_keys=True,
        )

        self.assertEqual(context.dialogue["resolution_option_id"], "return_to_center")
        self.assertEqual(context.route.route, "self_review")
        self.assertEqual(context.provider.source["owner"], "active_host")
        self.assertEqual(context.allowed_evidence_refs, (EVIDENCE,))
        self.assertNotIn(raw_marker, rendered)
        self.assertNotIn("request_text", rendered)
        self.assertNotIn("answer_text", rendered)
        self.assertFalse(context.content_boundary["contains_transcript"])
        self.assertFalse(run.execution["context_retained_by_adapter"])

    def test_self_review_requires_final_human_resolution_before_host_call(self) -> None:
        reviewer = FixtureSelfReviewer()
        active_provider = provider("codex-self-review.json")

        not_started = ReferenceAlignmentAdapter(FixtureMaterializer())
        with self.assertRaisesRegex(ReferenceAlignmentAdapterError, "has not started"):
            not_started.self_review(
                reviewer,
                provider=active_provider,
                reason_codes=("requirement_ambiguity",),
                allowed_evidence_refs=(EVIDENCE,),
            )

        exploring = ReferenceAlignmentAdapter(FixtureMaterializer())
        exploring.start("自然语言对齐。")
        ready = ReferenceAlignmentAdapter(FixtureMaterializer())
        ready.start("自然语言对齐。")
        ready.answer("先讨论后再决定。")

        for adapter in (exploring, ready):
            with self.assertRaisesRegex(
                ReferenceAlignmentAdapterError, "accepted advisory result"
            ):
                adapter.self_review(
                    reviewer,
                    provider=active_provider,
                    reason_codes=("requirement_ambiguity",),
                    allowed_evidence_refs=(EVIDENCE,),
                )
        self.assertEqual(reviewer.calls, 0)

    def test_only_medium_risk_available_active_host_self_review_can_execute(self) -> None:
        invalid_providers = (
            provider("generic-ide-independent-review.json"),
            provider("provider-unavailable.json"),
        )
        for risk_level, active_provider in (
            ("low", provider("codex-self-review.json")),
            ("high", provider("codex-self-review.json")),
            ("medium", invalid_providers[0]),
            ("medium", invalid_providers[1]),
        ):
            with self.subTest(risk_level=risk_level, provider=active_provider.provider_id):
                reviewer = FixtureSelfReviewer()
                with self.assertRaisesRegex(
                    ReferenceAlignmentAdapterError, "accepted advisory result"
                ):
                    resolved_adapter().self_review(
                        reviewer,
                        provider=active_provider,
                        risk_level=risk_level,
                        reason_codes=("requirement_ambiguity",),
                        allowed_evidence_refs=(EVIDENCE,),
                    )
                self.assertEqual(reviewer.calls, 0)

    def test_materializer_failure_or_malformed_output_fails_without_result(self) -> None:
        invalid_outputs = (
            (),
            ({"kind": "requirement", "raw_prompt": "not allowed"},),
            ("not a draft",),
            tuple(
                SelfReviewObservationDraft(
                    kind="requirement",
                    summary="Repeated observation.",
                    evidence_refs=(EVIDENCE,),
                )
                for _ in range(2)
            ),
        )
        for output in invalid_outputs:
            with self.subTest(output=output):
                reviewer = FixtureSelfReviewer()
                reviewer.output = output
                with self.assertRaisesRegex(
                    ReferenceAlignmentAdapterError, "accepted advisory result"
                ):
                    resolved_adapter().self_review(
                        reviewer,
                        provider=provider("codex-self-review.json"),
                        reason_codes=("requirement_ambiguity",),
                        allowed_evidence_refs=(EVIDENCE,),
                    )
                self.assertEqual(reviewer.calls, 1)

        reviewer = FixtureSelfReviewer()
        reviewer.failure = RuntimeError("host unavailable")
        with self.assertRaisesRegex(
            ReferenceAlignmentAdapterError, "accepted advisory result"
        ):
            resolved_adapter().self_review(
                reviewer,
                provider=provider("codex-self-review.json"),
                reason_codes=("requirement_ambiguity",),
                allowed_evidence_refs=(EVIDENCE,),
            )
        self.assertEqual(reviewer.calls, 1)

    def test_materializer_cannot_mutate_the_bound_context(self) -> None:
        class MutatingReviewer(FixtureSelfReviewer):
            def materialize_self_review(self, context):
                output = super().materialize_self_review(context)
                context.center["outcome"] = "Mutated by host callback."
                return output

        reviewer = MutatingReviewer()
        with self.assertRaisesRegex(
            ReferenceAlignmentAdapterError, "accepted advisory result"
        ):
            resolved_adapter().self_review(
                reviewer,
                provider=provider("codex-self-review.json"),
                reason_codes=("requirement_ambiguity",),
                allowed_evidence_refs=(EVIDENCE,),
            )
        self.assertEqual(reviewer.calls, 1)

    def test_evidence_privacy_and_authority_drift_fail_closed(self) -> None:
        invalid_drafts = (
            SelfReviewObservationDraft(
                kind="requirement",
                summary="Evidence is outside the allowed set.",
                evidence_refs=("README.md",),
            ),
            SelfReviewObservationDraft(
                kind="requirement",
                summary="password=must-not-enter-result",
                evidence_refs=(EVIDENCE,),
            ),
            {
                "kind": "requirement",
                "summary": "Advisory observation.",
                "evidence_refs": (EVIDENCE,),
                "assumptions": (),
                "unknowns": (),
                "recommended_question": None,
                "authority": {"changes_requirements": True},
            },
        )
        for draft in invalid_drafts:
            with self.subTest(draft=draft):
                reviewer = FixtureSelfReviewer()
                reviewer.output = (draft,)
                with self.assertRaisesRegex(
                    ReferenceAlignmentAdapterError, "accepted advisory result"
                ):
                    resolved_adapter().self_review(
                        reviewer,
                        provider=provider("codex-self-review.json"),
                        reason_codes=("requirement_ambiguity",),
                        allowed_evidence_refs=(EVIDENCE,),
                    )

        with self.assertRaisesRegex(
            ReferenceAlignmentAdapterError, "accepted advisory result"
        ):
            resolved_adapter().self_review(
                FixtureSelfReviewer(),
                provider=provider("codex-self-review.json"),
                reason_codes=("requirement_ambiguity",),
                allowed_evidence_refs=("C:\\Users\\person\\private.md",),
            )

    def test_observation_ids_and_result_are_deterministic_for_exact_context(self) -> None:
        adapter = resolved_adapter()
        reviewer = FixtureSelfReviewer()
        active_provider = provider("codex-self-review.json")
        kwargs = {
            "provider": active_provider,
            "reason_codes": ("requirement_ambiguity",),
            "allowed_evidence_refs": (EVIDENCE,),
        }

        first = adapter.self_review(reviewer, **kwargs)
        second = adapter.self_review(reviewer, **kwargs)

        self.assertEqual(first, second)
        self.assertEqual(reviewer.calls, 2)
        self.assertEqual(
            first.result.observations[0]["observation_id"],
            second.result.observations[0]["observation_id"],
        )

    def test_tampered_alignment_response_fails_before_materializer(self) -> None:
        adapter = resolved_adapter()
        reviewer = FixtureSelfReviewer()
        active = adapter._active_response()
        adapter._responses[-1] = replace(active, status="exploring")

        with self.assertRaisesRegex(
            ReferenceAlignmentAdapterError, "accepted advisory result"
        ):
            adapter.self_review(
                reviewer,
                provider=provider("codex-self-review.json"),
                reason_codes=("requirement_ambiguity",),
                allowed_evidence_refs=(EVIDENCE,),
            )
        self.assertEqual(reviewer.calls, 0)

    def test_core_implementation_has_no_vendor_or_network_special_case(self) -> None:
        source = (ROOT / "src/agentgov/active_agent_self_review.py").read_text(
            encoding="utf-8"
        ).lower()
        for vendor in ("codex", "claude", "generic-ide"):
            self.assertNotIn(vendor, source)
        for network_api in (
            "import requests",
            "import urllib",
            "import socket",
            "import subprocess",
        ):
            self.assertNotIn(network_api, source)


if __name__ == "__main__":
    unittest.main()
