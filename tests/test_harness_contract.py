from __future__ import annotations

import json
import unittest
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory

from agentgov.harness_contract import (
    BLOCK_MODES,
    CHANNEL_NAMES,
    EVIDENCE_STRENGTHS,
    GOVERNANCE_EFFECTS,
    HARNESS_CONTRACT,
    HARNESS_SCHEMA_VERSION,
    derive_first_deviation,
    evaluate_harness_run,
    load_harness_run,
    validate_harness_run_document,
)


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas/harness-contract-v1.schema.json"
FIXTURES = ROOT / "governance/fixtures/harness-contract-v1"
MATCHING = FIXTURES / "matching-no-write.json"
AIRBNB = FIXTURES / "airbnb-uncoached-baseline.json"
AIRBNB_HEADING = FIXTURES / "airbnb-uncoached-heading-replay.json"
AIRBNB_OWNER_REGRESSION = (
    FIXTURES / "airbnb-adapter-1-5-owner-regression-replay.json"
)


class HarnessContractTests(unittest.TestCase):
    def fixture(self, path: Path = MATCHING) -> dict:
        return dict(load_harness_run(path))

    def test_schema_and_fixtures_have_no_duplicate_json_keys(self) -> None:
        def unique_object(pairs: list[tuple[str, object]]) -> dict:
            result = {}
            for key, value in pairs:
                if key in result:
                    raise ValueError(f"duplicate JSON key: {key}")
                result[key] = value
            return result

        for path in (
            SCHEMA,
            MATCHING,
            AIRBNB,
            AIRBNB_HEADING,
            AIRBNB_OWNER_REGRESSION,
        ):
            with self.subTest(path=path.name):
                json.loads(
                    path.read_text(encoding="utf-8"),
                    object_pairs_hook=unique_object,
                )

    def test_schema_and_validator_share_contract_identity_and_core_enums(self) -> None:
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))

        self.assertEqual(schema["properties"]["contract"]["const"], HARNESS_CONTRACT)
        self.assertEqual(
            schema["properties"]["schema_version"]["const"],
            HARNESS_SCHEMA_VERSION,
        )
        self.assertEqual(
            set(schema["properties"]["scenario"]["properties"]["evidence_strength"]["enum"]),
            EVIDENCE_STRENGTHS,
        )
        self.assertEqual(
            set(schema["$defs"]["transition"]["properties"]["effect"]["enum"]),
            GOVERNANCE_EFFECTS,
        )
        self.assertEqual(
            set(schema["$defs"]["capabilities"]["properties"]["block_mode"]["enum"]),
            BLOCK_MODES,
        )
        self.assertEqual(
            set(schema["properties"]["channels"]["required"]),
            set(CHANNEL_NAMES),
        )

    def test_current_source_of_truth_describes_the_same_bounded_slice(self) -> None:
        surfaces = (
            ROOT / "README.md",
            ROOT / "STATUS.md",
            ROOT / "DEVELOPMENT_PLAN.md",
            ROOT / "docs/harness-contract-v1.md",
            ROOT / "docs/development-log/2026-08-14.md",
        )

        for path in surfaces:
            normalized = " ".join(path.read_text(encoding="utf-8").split())
            with self.subTest(path=path.name):
                self.assertIn("Harness Contract v1", normalized)
                self.assertIn("First Deviation", normalized)
                self.assertIn("AIRBNB", normalized)

        guide = (ROOT / "docs/harness-contract-v1.md").read_text(encoding="utf-8")
        for phrase in (
            "Agent selection",
            "AgentGov",
            "transition outcome",
            "paired_counterfactual",
            "repeated_intervention",
            "cross_context_replication",
            "does not upgrade its evidence strength",
            "publishes no causal-effectiveness",
            "not yet a CLI",
        ):
            self.assertIn(phrase, guide)

    def test_matching_fixture_is_valid_and_has_no_deviation(self) -> None:
        document = self.fixture()

        self.assertEqual(validate_harness_run_document(document), [])
        self.assertEqual(
            derive_first_deviation(document),
            {
                "present": False,
                "sequence": None,
                "stage": None,
                "code": None,
                "expected_outcome": None,
                "observed_outcome": None,
            },
        )
        evaluation = evaluate_harness_run(document)
        self.assertTrue(evaluation.valid)
        self.assertEqual(
            evaluation.channel_statuses,
            {
                "agent_selection": "conforming",
                "governance_decision": "conforming",
                "intervention_outcome": "conforming",
            },
        )

    def test_airbnb_fixture_derives_materialization_as_first_deviation(self) -> None:
        document = self.fixture(AIRBNB)

        self.assertEqual(validate_harness_run_document(document), [])
        self.assertEqual(
            derive_first_deviation(document),
            {
                "present": True,
                "sequence": 3,
                "stage": "proposal_materialization",
                "code": "normalized_scope_path_rejected",
                "expected_outcome": "valid_input",
                "observed_outcome": "invalid_input",
            },
        )
        self.assertEqual(document["harness_result"]["effect"], "MEDIATE")
        self.assertIsNone(document["harness_result"]["prevented_transition"])
        self.assertFalse(document["terminal"]["repository_modified"])

    def test_later_form_gap_does_not_replace_earlier_materialization_deviation(self) -> None:
        document = self.fixture(AIRBNB)
        observed = document["observed_transitions"]

        self.assertEqual(observed[4]["outcome"], "form_absent")
        self.assertEqual(
            derive_first_deviation(document)["stage"],
            "proposal_materialization",
        )

    def test_airbnb_heading_replay_preserves_identity_first_deviation_and_later_gaps(self) -> None:
        document = self.fixture(AIRBNB_HEADING)
        observed = document["observed_transitions"]

        self.assertEqual(validate_harness_run_document(document), [])
        self.assertEqual(
            derive_first_deviation(document),
            {
                "present": True,
                "sequence": 3,
                "stage": "proposal_materialization",
                "code": "human_owner_misattributed",
                "expected_outcome": "human_accountable_owner",
                "observed_outcome": "agent_accountable_owner",
            },
        )
        self.assertEqual(
            evaluate_harness_run(document).channel_statuses,
            {
                "agent_selection": "conforming",
                "governance_decision": "deviating",
                "intervention_outcome": "deviating",
            },
        )
        self.assertEqual(observed[4]["reason_code"], "user_reported_native_accept")
        self.assertEqual(observed[10]["outcome"], "not_reached")
        self.assertEqual(observed[11]["outcome"], "not_reached")
        self.assertEqual(
            document["host"]["capabilities"]["human_origin_assurance"],
            "unavailable",
        )
        self.assertTrue(document["terminal"]["repository_modified"])
        self.assertTrue(document["terminal"]["external_side_effect_completed"])

    def test_airbnb_owner_regression_preserves_contaminated_precondition_first(self) -> None:
        document = self.fixture(AIRBNB_OWNER_REGRESSION)
        observed = document["observed_transitions"]

        self.assertEqual(validate_harness_run_document(document), [])
        self.assertEqual(
            derive_first_deviation(document),
            {
                "present": True,
                "sequence": 1,
                "stage": "session_start",
                "code": "preexisting_replay_state_not_cleared",
                "expected_outcome": "replay_preconditions_ready",
                "observed_outcome": "preexisting_target_change_present",
            },
        )
        self.assertEqual(
            evaluate_harness_run(document).channel_statuses,
            {
                "agent_selection": "unknown",
                "governance_decision": "not_reached",
                "intervention_outcome": "deviating",
            },
        )
        self.assertEqual(observed[5]["reason_code"], "user_reported_form_absent")
        self.assertEqual(document["harness_result"]["status"], "unavailable")
        self.assertEqual(
            document["harness_result"]["reason_code"],
            "replay_precondition_contaminated",
        )
        self.assertFalse(document["terminal"]["repository_modified"])
        self.assertFalse(document["terminal"]["external_side_effect_completed"])

    def test_declared_first_deviation_must_match_derived_result(self) -> None:
        document = self.fixture(AIRBNB)
        document["first_deviation"] = dict(document["first_deviation"])
        document["first_deviation"]["stage"] = "human_decision_mediation"

        errors = validate_harness_run_document(document)

        self.assertIn(
            "$.first_deviation must equal the deterministic earliest transition mismatch",
            errors,
        )

    def test_first_mismatched_field_gets_stable_fallback_code(self) -> None:
        document = self.fixture()
        observed = deepcopy(document["observed_transitions"])
        observed[1]["effect"] = "ADVISE"
        observed[1]["reason_code"] = None
        document["observed_transitions"] = observed
        document["first_deviation"] = {
            "present": True,
            "sequence": 2,
            "stage": "agent_selection",
            "code": "effect_mismatch",
            "expected_outcome": "selected_expected_tool",
            "observed_outcome": "selected_expected_tool",
        }

        self.assertEqual(validate_harness_run_document(document), [])
        self.assertEqual(derive_first_deviation(document)["code"], "effect_mismatch")

    def test_forbidden_raw_evidence_fields_are_rejected(self) -> None:
        for field in (
            "raw_prompt",
            "transcript",
            "model_output",
            "tool_input_output",
            "credentials",
            "absolute_paths",
            "unbounded_payload",
        ):
            with self.subTest(field=field):
                document = self.fixture()
                document[field] = "disallowed"

                errors = validate_harness_run_document(document)

                self.assertIn(f"$.{field} is not allowed", errors)

    def test_privacy_and_authority_claims_must_remain_false(self) -> None:
        document = self.fixture()
        document["privacy_boundary"] = dict(document["privacy_boundary"])
        document["privacy_boundary"]["contains_raw_prompt"] = True
        document["authority_boundary"] = dict(document["authority_boundary"])
        document["authority_boundary"]["authorizes_deployment"] = True

        errors = validate_harness_run_document(document)

        self.assertIn("$.privacy_boundary.contains_raw_prompt must be false", errors)
        self.assertIn("$.authority_boundary.authorizes_deployment must be false", errors)

    def test_absolute_and_parent_evidence_paths_are_rejected(self) -> None:
        for invalid in ("C:/private/evidence.json", "/private/evidence.json", "../outside.json"):
            with self.subTest(invalid=invalid):
                document = self.fixture()
                document["scenario"] = dict(document["scenario"])
                document["scenario"]["source_refs"] = [invalid]

                errors = validate_harness_run_document(document)

                self.assertTrue(any("$.scenario.source_refs[0]" in error for error in errors))

    def test_transition_sequence_and_stage_order_are_strict(self) -> None:
        document = self.fixture()
        observed = deepcopy(document["observed_transitions"])
        observed[1], observed[2] = observed[2], observed[1]
        document["observed_transitions"] = observed

        errors = validate_harness_run_document(document)

        self.assertIn(
            "$.observed_transitions sequence values must be contiguous and ordered from 1",
            errors,
        )
        self.assertIn(
            "$.observed_transitions stages must follow Harness lifecycle order",
            errors,
        )

    def test_duplicate_transition_identity_is_rejected(self) -> None:
        document = self.fixture()
        observed = deepcopy(document["observed_transitions"])
        observed[1]["transition_id"] = observed[0]["transition_id"]
        document["observed_transitions"] = observed

        errors = validate_harness_run_document(document)

        self.assertIn(
            "$.observed_transitions transition_id values must be unique",
            errors,
        )

    def test_malformed_transition_identity_and_stage_fail_without_crashing(self) -> None:
        document = self.fixture()
        observed = deepcopy(document["observed_transitions"])
        observed[1]["transition_id"] = ["not", "a", "string"]
        observed[2]["stage"] = ["not", "a", "stage"]
        document["observed_transitions"] = observed

        errors = validate_harness_run_document(document)

        self.assertTrue(any("transition_id must be a string" in error for error in errors))
        self.assertTrue(any("stage must be one of" in error for error in errors))

    def test_expected_and_observed_transition_identity_must_match(self) -> None:
        document = self.fixture()
        observed = deepcopy(document["observed_transitions"])
        observed[2]["transition_id"] = "trn-different-materialization"
        document["observed_transitions"] = observed

        errors = validate_harness_run_document(document)

        self.assertIn(
            "$.observed_transitions must use the same ordered transition identities and stages as $.expected_transitions",
            errors,
        )

    def test_unsupported_or_unknown_host_cannot_claim_block(self) -> None:
        for block_mode in ("unsupported", "unknown"):
            with self.subTest(block_mode=block_mode):
                document = self.fixture()
                document["host"] = deepcopy(document["host"])
                document["host"]["capabilities"]["block_mode"] = block_mode
                document["harness_result"] = dict(document["harness_result"])
                document["harness_result"].update(
                    {
                        "effect": "BLOCK",
                        "prevented_transition": "before_action",
                    }
                )

                errors = validate_harness_run_document(document)

                self.assertIn(
                    "$.harness_result.effect cannot be BLOCK unless host block_mode is supported and pre_action_hook/block_action are true",
                    errors,
                )

    def test_supported_pre_action_host_may_claim_exact_block(self) -> None:
        document = self.fixture()
        document["host"] = deepcopy(document["host"])
        document["host"]["capabilities"]["block_mode"] = "supported"
        document["host"]["capabilities"]["pre_action_hook"] = True
        document["host"]["capabilities"]["block_action"] = True
        document["harness_result"] = dict(document["harness_result"])
        document["harness_result"].update(
            {
                "effect": "BLOCK",
                "status": "denied",
                "reason_code": "missing_authority",
                "affected_transition": "before_action",
                "prevented_transition": "before_action",
                "already_completed_effect": False,
            }
        )

        self.assertEqual(validate_harness_run_document(document), [])

    def test_host_capability_declaration_rejects_internal_contradictions(self) -> None:
        block = self.fixture()
        block["host"] = deepcopy(block["host"])
        block["host"]["capabilities"]["block_mode"] = "supported"

        mediation = self.fixture()
        mediation["host"] = deepcopy(mediation["host"])
        mediation["host"]["capabilities"]["mediation_mode"] = "none"

        block_errors = validate_harness_run_document(block)
        mediation_errors = validate_harness_run_document(mediation)

        self.assertIn(
            "$.host.capabilities supported block_mode requires pre_action_hook and block_action",
            block_errors,
        )
        self.assertIn(
            "$.host.capabilities mediation_mode none cannot claim mediation or human decision UI",
            mediation_errors,
        )

    def test_post_action_result_cannot_claim_rollback_or_block(self) -> None:
        document = self.fixture()
        document["host"] = deepcopy(document["host"])
        document["host"]["capabilities"]["block_mode"] = "supported"
        document["host"]["capabilities"]["pre_action_hook"] = True
        document["host"]["capabilities"]["block_action"] = True
        document["harness_result"] = dict(document["harness_result"])
        document["harness_result"].update(
            {
                "effect": "BLOCK",
                "prevented_transition": "after_action",
                "already_completed_effect": True,
            }
        )

        errors = validate_harness_run_document(document)

        self.assertIn("$.harness_result cannot claim BLOCK after an effect completed", errors)
        self.assertIn(
            "$.harness_result cannot claim a prevented transition after an effect completed",
            errors,
        )

    def test_host_without_mediation_cannot_claim_mediate(self) -> None:
        document = self.fixture()
        document["host"] = deepcopy(document["host"])
        document["host"]["capabilities"]["mediate_action"] = False

        errors = validate_harness_run_document(document)

        self.assertIn(
            "$.harness_result.effect cannot be MEDIATE unless host mediate_action is true",
            errors,
        )

    def test_terminal_side_effect_facts_must_match_observed_trace(self) -> None:
        document = self.fixture()
        document["terminal"] = dict(document["terminal"])
        document["terminal"]["external_side_effect_completed"] = True
        document["terminal"]["repository_modified"] = True

        errors = validate_harness_run_document(document)

        self.assertIn(
            "$.terminal.external_side_effect_completed must match the observed transition facts",
            errors,
        )
        self.assertIn(
            "$.terminal.repository_modified must match repository_write_completed evidence",
            errors,
        )

    def test_evaluation_keeps_invalid_contract_errors_bounded(self) -> None:
        document = self.fixture()
        document["contract"] = "other.contract"

        evaluation = evaluate_harness_run(document)

        self.assertFalse(evaluation.valid)
        self.assertIsNone(evaluation.first_deviation)
        self.assertTrue(any("$.contract" in error for error in evaluation.errors))

    def test_loader_requires_an_object_root(self) -> None:
        with TemporaryDirectory(dir=ROOT) as temp_dir:
            path = Path(temp_dir) / "array.json"
            path.write_text("[]\n", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "root must be an object"):
                load_harness_run(path)


if __name__ == "__main__":
    unittest.main()
