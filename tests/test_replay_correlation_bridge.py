from __future__ import annotations

import json
import unittest
from copy import deepcopy
from pathlib import Path

from agentgov.harness_contract import HARNESS_CONTRACT, HARNESS_SCHEMA_VERSION
from agentgov.replay_correlation_bridge import (
    CLAIM_LIMITS,
    HARNESS_CORRELATION_FIELD,
    PRIVACY_BOUNDARY,
    REPLAY_CORRELATION_BRIDGE_CONTRACT,
    REPLAY_CORRELATION_BRIDGE_SCHEMA_VERSION,
    REPLAY_CORRELATION_BRIDGE_STATES,
    replay_reservation_marker_digest,
    validate_replay_correlation_bridge,
    validate_replay_correlation_bridge_document,
)
from agentgov.replay_preflight import AUTHORITY_BOUNDARY


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas/replay-correlation-bridge-v1.schema.json"
FIXTURES = ROOT / "governance/fixtures/replay-correlation-bridge-v1"
HARNESS_FIXTURE = ROOT / "governance/fixtures/harness-contract-v1/matching-no-write.json"


class ReplayCorrelationBridgeTests(unittest.TestCase):
    def bridge(self, state: str) -> dict:
        return json.loads((FIXTURES / f"{state}.json").read_text(encoding="utf-8"))

    def reservation_marker(self) -> dict:
        return {
            "contract": "agentgov.replay-correlation-reservation",
            "schema_version": "1.0",
            "reservation_id": "rrv-0123456789abcdef",
            "correlation_id": "rpf-0123456789abcdef",
            "marker_path": ".agentgov/replay-correlations/rpf-0123456789abcdef.json",
            "preflight": {
                "plan_digest": "sha256:" + "1" * 64,
                "expected_head_sha": "2" * 40,
                "observed_head_sha": "2" * 40,
            },
            "adapter": {
                "adapter_id": "openai.codex-mcp",
                "adapter_version": "1.5.0",
                "protocol_version": "2026-07-28",
            },
            "status": "reserved",
            "authority_boundary": dict(AUTHORITY_BOUNDARY),
        }

    def harness_run(self) -> dict:
        document = json.loads(HARNESS_FIXTURE.read_text(encoding="utf-8"))
        document["run_id"] = "hrn-2222222222222222"
        document["host"]["repository_correlation"] = "rpf-0123456789abcdef"
        return document

    def test_schema_and_fixtures_parse_without_duplicate_keys(self) -> None:
        def unique_object(pairs: list[tuple[str, object]]) -> dict:
            result = {}
            for key, value in pairs:
                if key in result:
                    raise ValueError(f"duplicate JSON key: {key}")
                result[key] = value
            return result

        for path in (SCHEMA, *sorted(FIXTURES.glob("*.json"))):
            with self.subTest(path=path.name):
                json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique_object)

    def test_schema_and_validator_share_contract_constants(self) -> None:
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))

        self.assertEqual(schema["properties"]["contract"]["const"], REPLAY_CORRELATION_BRIDGE_CONTRACT)
        self.assertEqual(schema["properties"]["schema_version"]["const"], REPLAY_CORRELATION_BRIDGE_SCHEMA_VERSION)
        self.assertEqual(set(schema["properties"]["state"]["enum"]), REPLAY_CORRELATION_BRIDGE_STATES)
        self.assertEqual(schema["$defs"]["harnessMapping"]["properties"]["contract"]["const"], HARNESS_CONTRACT)
        self.assertEqual(schema["$defs"]["harnessMapping"]["properties"]["schema_version"]["const"], HARNESS_SCHEMA_VERSION)
        self.assertEqual(schema["$defs"]["harnessMapping"]["properties"]["field"]["const"], HARNESS_CORRELATION_FIELD)

    def test_four_lifecycle_fixtures_are_strict_documents(self) -> None:
        for state in REPLAY_CORRELATION_BRIDGE_STATES:
            with self.subTest(state=state):
                self.assertEqual(validate_replay_correlation_bridge_document(self.bridge(state)), [])

    def test_reserved_and_consumed_require_and_accept_exact_evidence(self) -> None:
        marker = self.reservation_marker()
        self.assertEqual(replay_reservation_marker_digest(marker), self.bridge("reserved")["reservation"]["marker_digest"])
        self.assertEqual(validate_replay_correlation_bridge(self.bridge("reserved"), reservation_marker=marker), [])
        self.assertEqual(
            validate_replay_correlation_bridge(
                self.bridge("consumed"),
                reservation_marker=marker,
                harness_run=self.harness_run(),
            ),
            [],
        )

    def test_invalidated_and_unavailable_need_no_external_evidence(self) -> None:
        self.assertEqual(validate_replay_correlation_bridge(self.bridge("invalidated")), [])
        self.assertEqual(validate_replay_correlation_bridge(self.bridge("unavailable")), [])

    def test_extra_fields_and_malformed_identifiers_are_rejected(self) -> None:
        cases = []
        extra = self.bridge("reserved")
        extra["raw_prompt"] = "forbidden"
        cases.append((extra, "$.raw_prompt is not allowed"))
        bad_bridge = self.bridge("reserved")
        bad_bridge["bridge_id"] = "bridge-1"
        cases.append((bad_bridge, "$.bridge_id must match ^rcb-[0-9a-f]{16}$"))
        bad_correlation = self.bridge("reserved")
        bad_correlation["correlation_id"] = "other"
        cases.append((bad_correlation, "$.correlation_id must match ^rpf-[0-9a-f]{16}$"))

        for document, expected in cases:
            with self.subTest(expected=expected):
                self.assertIn(expected, validate_replay_correlation_bridge_document(document))

    def test_malformed_unhashable_state_returns_an_error(self) -> None:
        document = self.bridge("reserved")
        document["state"] = ["reserved"]

        self.assertIn(
            "$.state must be one of reserved, consumed, invalidated, unavailable",
            validate_replay_correlation_bridge_document(document),
        )

    def test_unsafe_paths_and_mapping_drift_are_rejected(self) -> None:
        unsafe = self.bridge("consumed")
        unsafe["harness_mapping"]["evidence_ref"] = "../run.json"
        self.assertTrue(any("evidence_ref" in item for item in validate_replay_correlation_bridge_document(unsafe)))

        wrong_field = self.bridge("consumed")
        wrong_field["harness_mapping"]["field"] = "scenario.scenario_id"
        self.assertIn(
            "$.harness_mapping.field must equal 'host.repository_correlation'",
            validate_replay_correlation_bridge_document(wrong_field),
        )

        wrong_value = self.bridge("consumed")
        wrong_value["harness_mapping"]["expected_value"] = "rpf-ffffffffffffffff"
        self.assertIn(
            "$.harness_mapping.expected_value must equal $.correlation_id",
            validate_replay_correlation_bridge_document(wrong_value),
        )

    def test_lifecycle_combinations_are_strict(self) -> None:
        reserved = self.bridge("reserved")
        reserved["reason_code"] = "not_allowed"
        self.assertIn(
            "$.reason_code must be null for reserved or consumed state",
            validate_replay_correlation_bridge_document(reserved),
        )

        invalidated = self.bridge("invalidated")
        invalidated["reason_code"] = None
        self.assertTrue(any("reason_code" in item for item in validate_replay_correlation_bridge_document(invalidated)))

        not_consumed = self.bridge("reserved")
        not_consumed["harness_mapping"]["run_id"] = "hrn-2222222222222222"
        not_consumed["harness_mapping"]["evidence_ref"] = "evidence/run.json"
        errors = validate_replay_correlation_bridge_document(not_consumed)
        self.assertTrue(any("run_id must be null" in item for item in errors))
        self.assertTrue(any("evidence_ref must be null" in item for item in errors))

    def test_consumed_rejects_missing_or_invalid_external_evidence(self) -> None:
        consumed = self.bridge("consumed")
        errors = validate_replay_correlation_bridge(consumed)
        self.assertIn("$ reservation_marker evidence is required for reserved or consumed state", errors)
        self.assertIn("$ harness_run evidence is required for consumed state", errors)

        invalid_marker = self.reservation_marker()
        invalid_marker["status"] = "consumed"
        errors = validate_replay_correlation_bridge(
            consumed,
            reservation_marker=invalid_marker,
            harness_run=self.harness_run(),
        )
        self.assertTrue(any("$reservation_marker" in item for item in errors))

        invalid_harness = self.harness_run()
        invalid_harness["contract"] = "other"
        errors = validate_replay_correlation_bridge(
            consumed,
            reservation_marker=self.reservation_marker(),
            harness_run=invalid_harness,
        )
        self.assertTrue(any("$harness_run" in item for item in errors))

    def test_binding_rejects_reservation_and_harness_mismatches(self) -> None:
        consumed = self.bridge("consumed")
        marker = self.reservation_marker()
        marker["reservation_id"] = "rrv-ffffffffffffffff"
        errors = validate_replay_correlation_bridge(
            consumed,
            reservation_marker=marker,
            harness_run=self.harness_run(),
        )
        self.assertTrue(any("reservation_id must match" in item for item in errors))
        self.assertTrue(any("marker_digest must match" in item for item in errors))

        wrong_run = self.harness_run()
        wrong_run["run_id"] = "hrn-ffffffffffffffff"
        errors = validate_replay_correlation_bridge(
            consumed,
            reservation_marker=self.reservation_marker(),
            harness_run=wrong_run,
        )
        self.assertTrue(any("run_id must match" in item for item in errors))

        wrong_correlation = self.harness_run()
        wrong_correlation["host"]["repository_correlation"] = "rpf-ffffffffffffffff"
        errors = validate_replay_correlation_bridge(
            consumed,
            reservation_marker=self.reservation_marker(),
            harness_run=wrong_correlation,
        )
        self.assertTrue(any("host.repository_correlation" in item for item in errors))

    def test_boundaries_are_exact_and_all_false(self) -> None:
        document = self.bridge("consumed")
        self.assertEqual(document["privacy_boundary"], PRIVACY_BOUNDARY)
        self.assertEqual(document["claim_limits"], CLAIM_LIMITS)
        self.assertEqual(document["authority_boundary"], AUTHORITY_BOUNDARY)
        self.assertFalse(any(document["privacy_boundary"].values()))
        self.assertFalse(any(document["claim_limits"].values()))
        self.assertFalse(any(document["authority_boundary"].values()))

    def test_harness_evidence_is_forbidden_for_non_consumed_state(self) -> None:
        errors = validate_replay_correlation_bridge(
            self.bridge("invalidated"), harness_run=self.harness_run()
        )
        self.assertIn("$ harness_run evidence is allowed only for consumed state", errors)


if __name__ == "__main__":
    unittest.main()
