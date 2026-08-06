from __future__ import annotations

import json
import unittest
from dataclasses import asdict

from agentgov.reference_alignment_adapter import (
    AlignmentContextDraft,
    ClarificationUpdateDraft,
    ReferenceAlignmentAdapter,
    ReferenceAlignmentAdapterError,
)
from tests.test_clarification_dialogue import context, empty_patch, resolutions


class FixtureMaterializer:
    """Offline stand-in for semantic work performed by a real Coding Agent host."""

    def __init__(self) -> None:
        self.request_calls = 0
        self.answer_calls = 0
        self.invalid_answer = False

    def materialize_request(self, request_text: str) -> AlignmentContextDraft:
        self.request_calls += 1
        if "自然语言" not in request_text:
            raise ValueError("fixture expected an ordinary natural-language request")
        payload = context()
        return AlignmentContextDraft(
            subject_type=payload["source"]["subject_type"],
            subject_id=payload["source"]["subject_id"],
            center=payload["center"],
            drift=payload["drift"],
            assumptions=tuple(payload["assumptions"]),
            unknowns=tuple(payload["unknowns"]),
        )

    def materialize_answer(
        self,
        answer_text: str,
        *,
        dialogue,
        prompt,
    ) -> ClarificationUpdateDraft:
        self.answer_calls += 1
        if "先讨论" not in answer_text:
            raise ValueError("fixture expected an ordinary natural-language answer")
        patch = {"unexpected": None} if self.invalid_answer else empty_patch()
        return ClarificationUpdateDraft(
            answer_summary="The user wants natural discussion before the stable final choice.",
            center_patch=patch,
            candidate_resolutions=tuple(resolutions()),
            recommended_resolution_id="return_to_center",
            ready_requested=True,
        )


class ReferenceAlignmentAdapterTests(unittest.TestCase):
    def test_natural_language_journey_reaches_one_single_select_without_json(self) -> None:
        materializer = FixtureMaterializer()
        adapter = ReferenceAlignmentAdapter(materializer)

        first = adapter.start("我希望用户只用自然语言表达需求，不要手写治理 JSON。")
        ready = adapter.answer("是的，先讨论清楚，再给我稳定的单选决定。")
        resolved = adapter.select("return_to_center")
        journey = adapter.journey()

        self.assertIsNotNone(first.clarification_prompt)
        self.assertEqual(first.clarification_prompt.question["response_mode"], "natural_language")
        self.assertIsNotNone(ready.decision_prompt)
        self.assertEqual(ready.decision_prompt.input["mode"], "single_select")
        self.assertFalse(ready.decision_prompt.input["free_text_required"])
        self.assertEqual(resolved.status, "resolved")
        self.assertEqual(journey.status, "resolved")
        self.assertEqual(journey.sequence, 3)
        self.assertEqual(
            journey.interaction_burden,
            {
                "natural_language_requests": 1,
                "natural_language_answers": 1,
                "clarification_turns": 1,
                "single_select_decisions": 1,
                "governance_decision_episodes": 1,
                "user_authored_structured_records": 0,
                "user_authored_internal_commands": 0,
                "manual_confirmation_words": 0,
            },
        )
        self.assertEqual(materializer.request_calls, 1)
        self.assertEqual(materializer.answer_calls, 1)

    def test_privacy_safe_journey_contains_no_raw_conversation(self) -> None:
        raw_request = "RAW_REQUEST_7f95 自然语言"
        raw_answer = "RAW_ANSWER_4c21 先讨论"
        adapter = ReferenceAlignmentAdapter(FixtureMaterializer())

        adapter.start(raw_request)
        adapter.answer(raw_answer)
        rendered = json.dumps(asdict(adapter.journey()), ensure_ascii=False)

        self.assertNotIn(raw_request, rendered)
        self.assertNotIn(raw_answer, rendered)
        self.assertNotIn("request_text", rendered)
        self.assertNotIn("answer_text", rendered)
        self.assertTrue(
            all(value is False for value in adapter.journey().privacy_boundary.values())
        )

    def test_invalid_answer_draft_does_not_advance_core_or_metrics(self) -> None:
        materializer = FixtureMaterializer()
        adapter = ReferenceAlignmentAdapter(materializer)
        first = adapter.start("用自然语言驱动治理。")
        materializer.invalid_answer = True

        with self.assertRaisesRegex(ReferenceAlignmentAdapterError, "Core rejected"):
            adapter.answer("先讨论清楚。")

        after_failure = adapter.journey()
        self.assertEqual(after_failure.sequence, 1)
        self.assertEqual(after_failure.status, "exploring")
        self.assertEqual(after_failure.interaction_burden["natural_language_answers"], 0)
        self.assertEqual(after_failure.responses[-1], first)

        materializer.invalid_answer = False
        recovered = adapter.answer("先讨论清楚。")
        self.assertEqual(recovered.status, "ready_for_decision")
        self.assertEqual(adapter.journey().sequence, 2)

    def test_out_of_order_answer_or_decision_fails_before_materialization(self) -> None:
        materializer = FixtureMaterializer()
        adapter = ReferenceAlignmentAdapter(materializer)

        with self.assertRaisesRegex(ReferenceAlignmentAdapterError, "has not started"):
            adapter.answer("先讨论。")
        with self.assertRaisesRegex(ReferenceAlignmentAdapterError, "has not started"):
            adapter.select("return_to_center")

        adapter.start("用自然语言表达。")
        with self.assertRaisesRegex(ReferenceAlignmentAdapterError, "not waiting"):
            adapter.select("return_to_center")
        self.assertEqual(materializer.answer_calls, 0)
        self.assertEqual(adapter.journey().sequence, 1)

    def test_non_offered_selection_does_not_advance_journey(self) -> None:
        adapter = ReferenceAlignmentAdapter(FixtureMaterializer())
        adapter.start("自然语言开始。")
        adapter.answer("先讨论，再决定。")

        with self.assertRaisesRegex(ReferenceAlignmentAdapterError, "not offered"):
            adapter.select("invented_option")

        journey = adapter.journey()
        self.assertEqual(journey.sequence, 2)
        self.assertEqual(journey.status, "ready_for_decision")
        self.assertEqual(journey.interaction_burden["single_select_decisions"], 0)

    def test_materializer_must_return_small_normalized_draft_types(self) -> None:
        class WrongMaterializer:
            def materialize_request(self, request_text):
                return {"raw_prompt": request_text}

        adapter = ReferenceAlignmentAdapter(WrongMaterializer())
        with self.assertRaisesRegex(ReferenceAlignmentAdapterError, "AlignmentContextDraft"):
            adapter.start("自然语言请求。")

        self.assertEqual(adapter.journey().sequence, 0)
        self.assertEqual(adapter.journey().status, "not_started")


if __name__ == "__main__":
    unittest.main()
