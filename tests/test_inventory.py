import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from agentgov.initializer import initialize_project
from agentgov.inventory import (
    GOVERNANCE_STATUSES,
    INVENTORY_CONTRACT,
    INVENTORY_SCHEMA_VERSION,
    InventoryStatus,
    check_inventory,
    validate_inventory_document,
)
from agentgov.repository import FindingStatus, check_repository


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "governance/fixtures/inventory"


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


class InventorySchemaTests(unittest.TestCase):
    def test_schema_is_strict_and_matches_validator_constants(self) -> None:
        schema = read_json(ROOT / "governance/inventory.schema.json")

        self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(schema["properties"]["contract"]["const"], INVENTORY_CONTRACT)
        self.assertEqual(
            schema["properties"]["schema_version"]["const"],
            INVENTORY_SCHEMA_VERSION,
        )
        self.assertEqual(
            set(
                schema["$defs"]["capability"]["properties"][
                    "governance_status"
                ]["enum"]
            ),
            GOVERNANCE_STATUSES,
        )

    def test_fixture_contracts_cover_valid_and_invalid_exclusion(self) -> None:
        self.assertEqual(validate_inventory_document(read_json(FIXTURES / "valid.json")), [])

        errors = validate_inventory_document(
            read_json(FIXTURES / "invalid-exclusion.json")
        )

        self.assertIn("$.exclusions[0].reason is required", errors)

    def test_initializer_template_is_structurally_valid(self) -> None:
        document = read_json(ROOT / "templates/governance-inventory.template.json")

        self.assertEqual(validate_inventory_document(document), [])
        self.assertEqual(document["capabilities"][0]["governance_status"], "provisional")


class InventoryRepositoryTests(unittest.TestCase):
    def test_missing_inventory_is_an_honest_warning(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)

            report = check_inventory(root)

        self.assertIs(report.status, InventoryStatus.WARN)
        self.assertFalse(report.configured)
        self.assertIn("not configured", report.messages[0])

    def test_initialized_inventory_passes_and_adds_completeness_advisory(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "project"
            initialize_project(root, project_name="Inventory Project")

            inventory = check_inventory(root)
            repository = check_repository(root)

        self.assertIs(inventory.status, InventoryStatus.PASS)
        self.assertTrue(inventory.configured)
        finding = next(
            item
            for item in repository.findings
            if item.check_id == "inventory:completeness"
        )
        self.assertIs(finding.status, FindingStatus.ADVISORY)
        self.assertIn("cannot prove", finding.message)

    def test_owner_mismatch_fails(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "project"
            initialize_project(root, project_name="Owner Mismatch")
            inventory_path = root / "governance/inventory.json"
            payload = read_json(inventory_path)
            payload["capabilities"][0]["owner"] = "Different owner"
            write_json(inventory_path, payload)

            report = check_inventory(root)

        self.assertIs(report.status, InventoryStatus.FAIL)
        self.assertTrue(any("does not match manifest owner" in item for item in report.messages))

    def test_unlisted_canonical_manifest_fails(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "project"
            initialize_project(root, project_name="Unlisted Manifest")
            source = root / "governance/capabilities/example-capability.json"
            payload = read_json(source)
            payload["name"] = "second-capability"
            payload["owner"] = "Second owner"
            write_json(
                root / "governance/capabilities/second-capability.json",
                payload,
            )

            report = check_inventory(root)

        self.assertIs(report.status, InventoryStatus.FAIL)
        self.assertTrue(
            any("second-capability.json" in item and "not listed" in item for item in report.messages)
        )

    def test_missing_and_unsafe_manifest_references_fail(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "project"
            initialize_project(root, project_name="Bad References")
            inventory_path = root / "governance/inventory.json"
            payload = read_json(inventory_path)
            payload["capabilities"][0]["manifest"] = "../outside.json"
            write_json(inventory_path, payload)

            unsafe = check_inventory(root)

            payload["capabilities"][0]["manifest"] = (
                "governance/../governance/capabilities/example-capability.json"
            )
            write_json(inventory_path, payload)
            traversing = check_inventory(root)

            payload["capabilities"][0]["manifest"] = (
                "governance\\capabilities\\example-capability.json"
            )
            write_json(inventory_path, payload)
            backslash = check_inventory(root)

            payload["capabilities"][0]["manifest"] = (
                "governance/capabilities/missing.json"
            )
            write_json(inventory_path, payload)
            missing = check_inventory(root)

        self.assertIs(unsafe.status, InventoryStatus.FAIL)
        self.assertTrue(any("parent traversal" in item for item in unsafe.messages))
        self.assertIs(traversing.status, InventoryStatus.FAIL)
        self.assertTrue(any("parent traversal" in item for item in traversing.messages))
        self.assertIs(backslash.status, InventoryStatus.FAIL)
        self.assertTrue(any("forward slashes" in item for item in backslash.messages))
        self.assertIs(missing.status, InventoryStatus.FAIL)
        self.assertTrue(any("does not exist" in item for item in missing.messages))

    def test_exclusion_requires_an_existing_safe_path(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "project"
            initialize_project(root, project_name="Exclusion Project")
            inventory_path = root / "governance/inventory.json"
            payload = read_json(inventory_path)
            payload["exclusions"] = [
                {
                    "path": "docs/examples",
                    "reason": "Examples are documentation and do not execute as capabilities.",
                }
            ]
            write_json(inventory_path, payload)

            missing = check_inventory(root)
            (root / "docs/examples").mkdir()
            passing = check_inventory(root)

        self.assertIs(missing.status, InventoryStatus.FAIL)
        self.assertTrue(any("exclusion does not exist" in item for item in missing.messages))
        self.assertIs(passing.status, InventoryStatus.PASS)

    def test_inventory_never_emits_a_coverage_percentage(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "project"
            initialize_project(root, project_name="No Coverage")

            report = check_inventory(root)

        rendered = " ".join(report.messages)
        self.assertNotIn("%", rendered)
        self.assertNotIn("coverage", rendered.lower())


if __name__ == "__main__":
    unittest.main()
