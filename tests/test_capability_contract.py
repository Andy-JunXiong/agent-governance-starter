import json
import unittest
from pathlib import Path

from agentgov.capability import (
    CANONICAL_CONTRACT,
    LEGACY_CONTRACT,
    CAPABILITY_KINDS,
    CAPABILITY_TYPES,
    IMPLEMENTATION_MODES,
    DECISION_AUTHORITIES,
    AUTONOMY_LEVELS,
    EVALUATION_READINESS,
    MODEL_ROUTE_MODES,
    PROVENANCE_ORIGINS,
    RISK_LEVELS,
    SCHEMA_VERSION,
    load_capability_manifest,
    validate_capability_manifest,
)


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "governance" / "capability.schema.json"
VALID_FIXTURES = ROOT / "prompt-governance" / "fixtures" / "valid"
INVALID_FIXTURES = ROOT / "prompt-governance" / "fixtures" / "invalid"


class CapabilityContractTests(unittest.TestCase):
    def test_schema_uses_supported_draft_and_strict_objects(self) -> None:
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

        self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(schema["properties"]["contract"]["const"], CANONICAL_CONTRACT)
        self.assertIn("contract", schema["required"])
        self.assertEqual(schema["properties"]["schema_version"]["const"], SCHEMA_VERSION)
        self.assertEqual(set(schema["properties"]["capability_type"]["enum"]), CAPABILITY_TYPES)
        self.assertEqual(
            set(schema["properties"]["implementation_mode"]["enum"]),
            IMPLEMENTATION_MODES,
        )
        self.assertEqual(
            set(schema["properties"]["decision_authority"]["enum"]),
            DECISION_AUTHORITIES,
        )
        self.assertEqual(
            set(schema["properties"]["autonomy_level"]["enum"]),
            AUTONOMY_LEVELS,
        )
        self.assertEqual(set(schema["properties"]["risk_level"]["enum"]), RISK_LEVELS)
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

    def test_canonical_template_uses_orthogonal_ai_capability_fields(self) -> None:
        manifest = load_capability_manifest(
            ROOT / "templates/prompt-capability.template.json"
        )

        errors = validate_capability_manifest(manifest)

        self.assertEqual(errors, [])
        self.assertNotIn("capability_kind", manifest)
        self.assertNotIn("model_route", manifest)
        self.assertEqual(manifest["implementation_mode"], "hybrid")
        self.assertEqual(manifest["contract"], CANONICAL_CONTRACT)

    def test_legacy_and_canonical_field_families_cannot_be_mixed(self) -> None:
        manifest = dict(
            load_capability_manifest(VALID_FIXTURES / "runtime-low-risk.json")
        )
        manifest.update(
            {
                "capability_type": "decision_support",
                "implementation_mode": "hybrid",
                "decision_authority": "recommend",
                "autonomy_level": "human_approval_required",
            }
        )

        errors = validate_capability_manifest(manifest)

        self.assertTrue(any("not both" in error for error in errors))

    def test_canonical_manifest_requires_explicit_contract_identity(self) -> None:
        manifest = dict(
            load_capability_manifest(ROOT / "templates/prompt-capability.template.json")
        )
        del manifest["contract"]

        errors = validate_capability_manifest(manifest)

        self.assertIn("$.contract is required", errors)

    def test_contract_identity_must_match_the_field_family(self) -> None:
        canonical = dict(
            load_capability_manifest(ROOT / "templates/prompt-capability.template.json")
        )
        canonical["contract"] = LEGACY_CONTRACT
        legacy = dict(
            load_capability_manifest(VALID_FIXTURES / "runtime-low-risk.json")
        )
        legacy["contract"] = CANONICAL_CONTRACT

        canonical_errors = validate_capability_manifest(canonical)
        legacy_errors = validate_capability_manifest(legacy)

        self.assertTrue(any("incompatible with canonical" in item for item in canonical_errors))
        self.assertTrue(any("incompatible with legacy" in item for item in legacy_errors))

    def test_legacy_manifest_without_contract_remains_readable(self) -> None:
        manifest = load_capability_manifest(VALID_FIXTURES / "runtime-low-risk.json")

        self.assertNotIn("contract", manifest)
        self.assertEqual(validate_capability_manifest(manifest), [])


if __name__ == "__main__":
    unittest.main()
