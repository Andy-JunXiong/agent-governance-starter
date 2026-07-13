import json
import unittest
from pathlib import Path

from agentgov.capability import (
    CAPABILITY_KINDS,
    EVALUATION_READINESS,
    MODEL_ROUTE_MODES,
    PROVENANCE_ORIGINS,
    RISK_LEVELS,
    SCHEMA_VERSION,
    load_capability_manifest,
    validate_capability_manifest,
)


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "prompt-governance" / "capability.schema.json"
VALID_FIXTURES = ROOT / "prompt-governance" / "fixtures" / "valid"
INVALID_FIXTURES = ROOT / "prompt-governance" / "fixtures" / "invalid"


class CapabilityContractTests(unittest.TestCase):
    def test_schema_uses_supported_draft_and_strict_objects(self) -> None:
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

        self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(schema["properties"]["schema_version"]["const"], SCHEMA_VERSION)
        self.assertEqual(set(schema["properties"]["capability_kind"]["enum"]), CAPABILITY_KINDS)
        self.assertEqual(set(schema["properties"]["risk_level"]["enum"]), RISK_LEVELS)
        self.assertEqual(
            set(schema["properties"]["model_route"]["properties"]["mode"]["enum"]),
            MODEL_ROUTE_MODES,
        )
        self.assertEqual(
            set(schema["properties"]["evaluation"]["properties"]["readiness"]["enum"]),
            EVALUATION_READINESS,
        )
        self.assertEqual(
            set(schema["properties"]["provenance"]["properties"]["origin"]["enum"]),
            PROVENANCE_ORIGINS,
        )

    def test_all_valid_fixtures_pass(self) -> None:
        fixture_paths = sorted(VALID_FIXTURES.glob("*.json"))
        self.assertGreaterEqual(len(fixture_paths), 2)

        for path in fixture_paths:
            with self.subTest(fixture=path.name):
                errors = validate_capability_manifest(load_capability_manifest(path))
                self.assertEqual(errors, [])

    def test_all_invalid_fixtures_fail_for_expected_policy(self) -> None:
        expected_error_fragments = {
            "agent-protocol-kind.json": "$.capability_kind must be one of",
            "high-risk-without-review.json": "must be true for high or critical risk",
            "missing-owner.json": "$.owner is required",
            "ready-without-evidence.json": "evidence_refs must not be empty",
        }
        self.assertEqual(
            {path.name for path in INVALID_FIXTURES.glob("*.json")},
            set(expected_error_fragments),
        )

        for filename, expected_fragment in expected_error_fragments.items():
            with self.subTest(fixture=filename):
                manifest = load_capability_manifest(INVALID_FIXTURES / filename)
                errors = validate_capability_manifest(manifest)
                self.assertTrue(errors)
                self.assertTrue(
                    any(expected_fragment in error for error in errors),
                    msg=f"Expected {expected_fragment!r} in {errors!r}",
                )

    def test_unknown_top_level_fields_are_rejected(self) -> None:
        manifest = dict(load_capability_manifest(VALID_FIXTURES / "runtime-low-risk.json"))
        manifest["undocumented_policy"] = True

        errors = validate_capability_manifest(manifest)

        self.assertIn("$.undocumented_policy is not allowed", errors)

    def test_wrong_enum_type_returns_an_error_instead_of_crashing(self) -> None:
        manifest = dict(load_capability_manifest(VALID_FIXTURES / "runtime-low-risk.json"))
        manifest["risk_level"] = ["low"]

        errors = validate_capability_manifest(manifest)

        self.assertTrue(any("$.risk_level must be one of" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
