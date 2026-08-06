from __future__ import annotations

import json
import hashlib
import tomllib
import unittest
from dataclasses import asdict
from pathlib import Path

from agentgov.clarification_dialogue import (
    ALIGNMENT_CONTEXT_CONTRACT,
    CLARIFICATION_DIALOGUE_CONTRACT,
    CLARIFICATION_PROMPT_CONTRACT,
    CLARIFICATION_UPDATE_CONTRACT,
    ClarificationDialogueError,
    alignment_context_from_payload,
    apply_clarification_update,
    build_alignment_resolution_prompt,
    build_next_clarification_prompt,
    clarification_dialogue_from_payload,
    clarification_update_from_payload,
    denied_authority,
    render_clarification_prompt_terminal,
    resolve_clarification_dialogue,
    start_clarification_dialogue,
)
from agentgov.human_decision import canonical_document_digest, record_human_decision


ROOT = Path(__file__).resolve().parents[1]


def empty_patch(**overrides):
    value = {
        "outcome": None,
        "why_now": None,
        "success_signals": None,
        "constraints": None,
        "non_goals": None,
    }
    value.update(overrides)
    return value


def question(digit: str, text: str, *, material: bool = True, priority: int = 5):
    return {
        "question_id": "qst-" + digit * 16,
        "question": text,
        "why_matters": "The answer changes the durable direction of this work.",
        "material": material,
        "priority": priority,
    }


def resolutions(*, include_continue: bool = False):
    items = [
        {
            "id": "return_to_center",
            "label": "Return to the original center",
            "effect": "Keep the original user outcome and revise the implementation direction.",
            "center_patch": empty_patch(),
        },
        {
            "id": "adopt_new_center",
            "label": "Adopt the clarified center",
            "effect": "Replace the working center with the newly confirmed business outcome.",
            "center_patch": empty_patch(
                outcome="Minimize manual input while preserving explicit human decisions."
            ),
        },
        {
            "id": "split_new_requirement",
            "label": "Split a separate requirement",
            "effect": "Keep the current center and route the new outcome as separate work.",
            "center_patch": empty_patch(),
        },
    ]
    if include_continue:
        items.append(
            {
                "id": "continue_exploration",
                "label": "Continue the discussion",
                "effect": "Keep exploring the remaining non-material question before changing direction.",
                "center_patch": empty_patch(),
            }
        )
    return items


def content_boundary():
    return {
        "contains_raw_prompt": False,
        "contains_raw_answer": False,
        "contains_transcript": False,
        "contains_assistant_response": False,
        "contains_source_content": False,
        "contains_credentials": False,
        "contains_absolute_paths": False,
    }


def context(*, unknowns=None, candidates=None, recommendation=None, semantics="advisory"):
    return {
        "contract": ALIGNMENT_CONTEXT_CONTRACT,
        "schema_version": "1.0",
        "context_id": "acx-" + "1" * 32,
        "source": {
            "adapter_id": "fixture.coding-agent",
            "actor_class": "coding_agent",
            "subject_type": "active_task",
            "subject_id": "minimal-input-decisions",
        },
        "center": {
            "outcome": "Keep human decisions while reducing mechanical input.",
            "why_now": "Repeated confirmation words are slowing ordinary development.",
            "success_signals": ["Users make real decisions without composing internal commands."],
            "constraints": ["Do not let the Coding Agent approve its own work."],
            "non_goals": ["Do not remove substantive architecture discussion."],
        },
        "drift": {
            "kind": "architecture",
            "semantics": semantics,
            "observation": "The single-select flow assumes stable options before discussion has converged.",
            "evidence_refs": ["docs/human-decision-prompts.md"],
            "impact": "Premature approval could optimize friction while losing user intent.",
        },
        "assumptions": ["Natural conversation remains available in the host."],
        "unknowns": list(unknowns if unknowns is not None else [
            question("a", "Should clarification stay conversational until the options are stable?")
        ]),
        "candidate_resolutions": list(candidates or []),
        "recommended_resolution_id": recommendation,
        "content_boundary": content_boundary(),
        "authority_boundary": denied_authority(),
    }


def update(dialogue, prompt, *, summary, new_questions=None, candidates=None, recommendation=None, ready=False, actor="human", patch=None, digit="1"):
    return {
        "contract": CLARIFICATION_UPDATE_CONTRACT,
        "schema_version": "1.0",
        "update_id": "cup-" + digit * 32,
        "dialogue": {
            "dialogue_id": dialogue.dialogue_id,
            "revision": dialogue.revision,
            "digest": canonical_document_digest(asdict(dialogue)),
        },
        "prompt": {
            "prompt_id": prompt.prompt_id,
            "prompt_digest": canonical_document_digest(asdict(prompt)),
        },
        "question_id": prompt.question["question_id"],
        "actor": {
            "adapter_id": "agentgov.reference-adapter",
            "actor_class": actor,
            "recording_method": "host_conversation",
        },
        "recorded_at": f"2026-08-06T00:00:0{digit}.000Z",
        "answer_summary": summary,
        "center_patch": patch or empty_patch(),
        "new_questions": list(new_questions or []),
        "candidate_resolutions": list(candidates or []),
        "recommended_resolution_id": recommendation,
        "ready_requested": ready,
        "content_boundary": content_boundary(),
        "authority_boundary": denied_authority(),
    }


class ClarificationDialogueTests(unittest.TestCase):
    def test_contracts_keep_center_drift_privacy_and_authority_separate(self) -> None:
        parsed = alignment_context_from_payload(context())
        invalid_semantics = context(semantics="deterministic")
        raw = context()
        raw["content_boundary"]["contains_raw_answer"] = True
        authority = context()
        authority["authority_boundary"]["changes_center"] = True

        self.assertEqual(parsed.drift["semantics"], "advisory")
        self.assertEqual(parsed.source["actor_class"], "coding_agent")
        for invalid in (invalid_semantics, raw, authority):
            with self.assertRaises(ClarificationDialogueError):
                alignment_context_from_payload(invalid)

    def test_start_and_prompt_keep_original_center_visible_and_ask_one_question(self) -> None:
        parsed = alignment_context_from_payload(
            context(
                unknowns=[
                    question("b", "Which secondary metric should be shown?", material=False, priority=5),
                    question("a", "Has the business outcome changed?", material=True, priority=4),
                ]
            )
        )
        dialogue = start_clarification_dialogue(parsed)
        prompt = build_next_clarification_prompt(dialogue)
        terminal = render_clarification_prompt_terminal(prompt)

        self.assertEqual(dialogue.status, "exploring")
        self.assertEqual(prompt.question["question_id"], "qst-" + "a" * 16)
        self.assertEqual(prompt.question["response_mode"], "natural_language")
        self.assertFalse(prompt.guidance["decision_episode"])
        self.assertIn("CENTER Keep human decisions", terminal)
        self.assertIn("OBSERVED_DRIFT", terminal)
        self.assertIn("QUESTION Has the business outcome changed?", terminal)
        self.assertTrue(all(value is False for value in prompt.authority_boundary.values()))

    def test_one_human_update_records_only_normalized_summary_and_not_a_decision(self) -> None:
        dialogue = start_clarification_dialogue(alignment_context_from_payload(context()))
        prompt = build_next_clarification_prompt(dialogue)
        next_dialogue = apply_clarification_update(
            dialogue,
            prompt,
            clarification_update_from_payload(
                update(
                    dialogue,
                    prompt,
                    summary="The user wants natural discussion before any bounded choice.",
                    new_questions=[question("b", "Should a changed goal replace or split the task?")],
                )
            ),
        )
        rendered = json.dumps(asdict(next_dialogue)).lower()

        self.assertEqual(next_dialogue.revision, 2)
        self.assertEqual(next_dialogue.metrics["clarification_turns"], 1)
        self.assertEqual(next_dialogue.metrics["governance_decision_episodes"], 0)
        self.assertEqual(next_dialogue.discussion_records[0]["recorded_by"], "human")
        self.assertNotIn("raw_answer", rendered)
        self.assertNotIn("transcript", rendered)

    def test_multiple_turns_are_not_capped_by_the_friction_decision_budget(self) -> None:
        dialogue = start_clarification_dialogue(
            alignment_context_from_payload(
                context(unknowns=[question("a", "First material clarification?")])
            )
        )
        for index, next_digit in enumerate(("b", "c", "d"), start=1):
            prompt = build_next_clarification_prompt(dialogue)
            dialogue = apply_clarification_update(
                dialogue,
                prompt,
                clarification_update_from_payload(
                    update(
                        dialogue,
                        prompt,
                        summary=f"Normalized human clarification {index}.",
                        new_questions=[question(next_digit, f"Clarification question {index + 1}?")],
                        digit=str(index),
                    )
                ),
            )

        self.assertEqual(dialogue.metrics["clarification_turns"], 3)
        self.assertEqual(dialogue.metrics["governance_decision_episodes"], 0)
        self.assertEqual(dialogue.status, "exploring")

    def test_operational_record_window_does_not_cap_clarification_turns(self) -> None:
        dialogue = start_clarification_dialogue(
            alignment_context_from_payload(
                context(unknowns=[question("a", "Initial clarification?")])
            )
        )
        for index in range(105):
            prompt = build_next_clarification_prompt(dialogue)
            next_question_id = "qst-" + hashlib.sha256(
                f"rolling-question-{index}".encode("utf-8")
            ).hexdigest()[:16]
            dialogue = apply_clarification_update(
                dialogue,
                prompt,
                clarification_update_from_payload(
                    {
                        **update(
                            dialogue,
                            prompt,
                            summary=f"Normalized rolling clarification {index}.",
                            digit=str((index % 9) + 1),
                        ),
                        "update_id": "cup-" + hashlib.sha256(
                            f"rolling-update-{index}".encode("utf-8")
                        ).hexdigest()[:32],
                        "recorded_at": f"2026-08-06T00:{index // 60:02d}:{index % 60:02d}.000Z",
                        "new_questions": [
                            {
                                **question("a", f"Rolling clarification {index + 1}?"),
                                "question_id": next_question_id,
                            }
                        ],
                    }
                ),
            )

        self.assertEqual(dialogue.metrics["clarification_turns"], 105)
        self.assertEqual(len(dialogue.discussion_records), 100)
        self.assertEqual(dialogue.metrics["governance_decision_episodes"], 0)

    def test_agent_answer_wrong_question_and_drifted_revision_fail_closed(self) -> None:
        dialogue = start_clarification_dialogue(alignment_context_from_payload(context()))
        prompt = build_next_clarification_prompt(dialogue)
        agent = update(dialogue, prompt, summary="Agent answer.", actor="coding_agent")
        wrong = update(dialogue, prompt, summary="Human answer.")
        wrong["question_id"] = "qst-" + "f" * 16
        drifted = update(dialogue, prompt, summary="Human answer.")
        drifted["dialogue"]["revision"] += 1

        with self.assertRaises(ClarificationDialogueError):
            clarification_update_from_payload(agent)
        for payload in (wrong, drifted):
            parsed = clarification_update_from_payload(payload)
            with self.assertRaises(ClarificationDialogueError):
                apply_clarification_update(dialogue, prompt, parsed)

    def test_material_unknown_prevents_premature_final_decision(self) -> None:
        dialogue = start_clarification_dialogue(alignment_context_from_payload(context()))
        prompt = build_next_clarification_prompt(dialogue)
        premature = update(
            dialogue,
            prompt,
            summary="One material answer created another material unknown.",
            new_questions=[question("b", "Which durable outcome is authoritative?")],
            candidates=resolutions(),
            recommendation="return_to_center",
            ready=True,
        )

        with self.assertRaisesRegex(ClarificationDialogueError, "material unknowns"):
            apply_clarification_update(
                dialogue,
                prompt,
                clarification_update_from_payload(premature),
            )

    def test_exploration_cannot_enter_a_no_question_dead_end(self) -> None:
        no_question_context = context(
            unknowns=[],
            candidates=resolutions(),
            recommendation=None,
        )
        with self.assertRaises(ClarificationDialogueError):
            alignment_context_from_payload(no_question_context)

        dialogue = start_clarification_dialogue(alignment_context_from_payload(context()))
        prompt = build_next_clarification_prompt(dialogue)
        dead_end = update(
            dialogue,
            prompt,
            summary="The answer is normalized but the options are not stable yet.",
        )
        with self.assertRaises(ClarificationDialogueError):
            apply_clarification_update(
                dialogue,
                prompt,
                clarification_update_from_payload(dead_end),
            )

    def test_resolved_unknowns_produce_existing_minimal_input_decision(self) -> None:
        dialogue = start_clarification_dialogue(alignment_context_from_payload(context()))
        clarification = build_next_clarification_prompt(dialogue)
        dialogue = apply_clarification_update(
            dialogue,
            clarification,
            clarification_update_from_payload(
                update(
                    dialogue,
                    clarification,
                    summary="The user confirmed discussion first, then one durable choice.",
                    candidates=resolutions(),
                    recommendation="return_to_center",
                    ready=True,
                )
            ),
        )
        decision = build_alignment_resolution_prompt(dialogue)

        self.assertEqual(dialogue.status, "ready_for_decision")
        self.assertEqual(decision.kind, "alignment_resolution")
        self.assertEqual(decision.recommended_option_id, "return_to_center")
        self.assertFalse(decision.input["free_text_required"])
        self.assertEqual(dialogue.metrics["governance_decision_episodes"], 0)

    def test_final_human_resolution_recenters_without_mutating_project_authority(self) -> None:
        dialogue = start_clarification_dialogue(
            alignment_context_from_payload(
                context(unknowns=[], candidates=resolutions(), recommendation="return_to_center")
            )
        )
        decision = build_alignment_resolution_prompt(dialogue)
        result = record_human_decision(
            decision,
            selected_option_id="return_to_center",
            adapter_id="agentgov.reference-adapter",
            recording_method="host_single_select",
            recorded_at="2026-08-06T00:00:05.000Z",
        )
        resolved = resolve_clarification_dialogue(dialogue, decision, result)

        self.assertEqual(resolved.status, "resolved")
        self.assertEqual(resolved.resolution["option_id"], "return_to_center")
        self.assertEqual(resolved.metrics["governance_decision_episodes"], 1)
        self.assertEqual(resolved.center, dialogue.center)
        self.assertTrue(all(value is False for value in resolved.authority_boundary.values()))

    def test_adopt_new_center_changes_only_structured_center(self) -> None:
        dialogue = start_clarification_dialogue(
            alignment_context_from_payload(
                context(unknowns=[], candidates=resolutions(), recommendation="adopt_new_center")
            )
        )
        decision = build_alignment_resolution_prompt(dialogue)
        result = record_human_decision(
            decision,
            selected_option_id="adopt_new_center",
            adapter_id="agentgov.reference-adapter",
            recording_method="host_single_select",
        )
        resolved = resolve_clarification_dialogue(dialogue, decision, result)

        self.assertEqual(
            resolved.center["outcome"],
            "Minimize manual input while preserving explicit human decisions.",
        )
        self.assertEqual(resolved.center["why_now"], dialogue.center["why_now"])

    def test_continue_exploration_returns_to_dialogue_without_new_project_authority(self) -> None:
        dialogue = start_clarification_dialogue(
            alignment_context_from_payload(
                context(
                    unknowns=[question("b", "Which wording is clearest?", material=False)],
                    candidates=resolutions(include_continue=True),
                    recommendation="continue_exploration",
                )
            )
        )
        self.assertEqual(dialogue.status, "ready_for_decision")
        decision = build_alignment_resolution_prompt(dialogue)
        result = record_human_decision(
            decision,
            selected_option_id="continue_exploration",
            adapter_id="agentgov.reference-adapter",
            recording_method="host_single_select",
        )
        exploring = resolve_clarification_dialogue(dialogue, decision, result)

        self.assertEqual(exploring.status, "exploring")
        self.assertIsNone(exploring.resolution)
        self.assertEqual(exploring.metrics["governance_decision_episodes"], 1)
        self.assertIsNotNone(build_next_clarification_prompt(exploring))

    def test_final_prompt_or_result_drift_is_rejected(self) -> None:
        dialogue = start_clarification_dialogue(
            alignment_context_from_payload(
                context(unknowns=[], candidates=resolutions(), recommendation="return_to_center")
            )
        )
        decision = build_alignment_resolution_prompt(dialogue)
        result = record_human_decision(
            decision,
            selected_option_id="return_to_center",
            adapter_id="agentgov.reference-adapter",
            recording_method="host_single_select",
        )
        changed = json.loads(json.dumps(asdict(dialogue)))
        changed["center"]["outcome"] += " Changed."

        with self.assertRaises(ClarificationDialogueError):
            resolve_clarification_dialogue(
                clarification_dialogue_from_payload(changed),
                decision,
                result,
            )

    def test_schemas_are_strict_vendor_neutral_and_packaged(self) -> None:
        expected = {
            "alignment-context.schema.json": ALIGNMENT_CONTEXT_CONTRACT,
            "clarification-dialogue.schema.json": CLARIFICATION_DIALOGUE_CONTRACT,
            "clarification-prompt.schema.json": CLARIFICATION_PROMPT_CONTRACT,
            "clarification-update.schema.json": CLARIFICATION_UPDATE_CONTRACT,
        }
        rendered = []
        for name, contract in expected.items():
            schema = json.loads((ROOT / "schemas" / name).read_text(encoding="utf-8"))
            self.assertFalse(schema["additionalProperties"])
            self.assertEqual(schema["properties"]["contract"]["const"], contract)
            rendered.append(json.dumps(schema, sort_keys=True).lower())
        self.assertNotIn("codex", "".join(rendered))
        package = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
        self.assertIn(
            "schemas/*.schema.json",
            package["tool"]["setuptools"]["data-files"][
                "share/agent-governance-starter/schemas"
            ],
        )


if __name__ == "__main__":
    unittest.main()
