import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from agentgov.controls import (
    APPLICABILITY_STATUSES,
    CONTROL_MAPPING_CONTRACT,
    CONTROL_MAPPING_SCHEMA_VERSION,
    ENFORCEMENT_MODES,
    ControlStatus,
    check_control_mapping,
    validate_control_mapping_document,
)
from agentgov.initializer import initialize_project
from agentgov.repository import FindingStatus, check_repository


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "governance/fixtures/controls"


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def finding(report, check_id: str):
    return next(item for item in report.findings if item.check_id == check_id)


def add_inventory_capability(root: Path, name: str) -> Path:
    source = root / "governance/capabilities/example-capability.json"
    manifest = read_json(source)
    manifest["name"] = name
    manifest["owner"] = f"{name} owner"
    target = root / f"governance/capabilities/{name}.json"
    write_json(target, manifest)

    inventory_path = root / "governance/inventory.json"
    inventory = read_json(inventory_path)
    inventory["capabilities"].append(
        {
            "name": name,
            "manifest": f"governance/capabilities/{name}.json",
            "owner": f"{name} owner",
            "governance_status": "provisional",
        }
    )
    write_json(inventory_path, inventory)
    return target


class ControlContractTests(unittest.TestCase):
    def test_schema_is_strict_and_matches_validator_constants(self) -> None:
        schema = read_json(ROOT / "governance/control-mapping.schema.json")
        control = schema["$defs"]["control"]

        self.assertEqual(
            schema["properties"]["contract"]["const"],
            CONTROL_MAPPING_CONTRACT,
        )
        self.assertEqual(
            schema["properties"]["schema_version"]["const"],
            CONTROL_MAPPING_SCHEMA_VERSION,
        )
        self.assertFalse(schema["additionalProperties"])
        self.assertFalse(control["additionalProperties"])
        self.assertEqual(
            set(control["properties"]["applicability"]["enum"]),
            APPLICABILITY_STATUSES,
        )
        self.assertEqual(
            set(control["properties"]["enforcement_mode"]["enum"]),
            ENFORCEMENT_MODES,
        )

    def test_fixtures_cover_applicable_not_applicable_and_invalid(self) -> None:
        self.assertEqual(
            validate_control_mapping_document(read_json(FIXTURES / "valid.json")),
            [],
        )
        self.assertEqual(
            validate_control_mapping_document(
                read_json(FIXTURES / "not-applicable.json")
            ),
            [],
        )

        errors = validate_control_mapping_document(
            read_json(FIXTURES / "invalid-not-applicable.json")
        )

        self.assertIn("$.controls[0].rationale is required", errors)

    def test_initialized_mapping_passes_with_effectiveness_advisory(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "project"
            initialize_project(root, project_name="Control Project")
            mapping = root / "governance/controls/example-capability.json"

            control = check_control_mapping(root, mapping)
            repository = check_repository(root)

        self.assertIs(control.status, ControlStatus.PASS)
        self.assertEqual(control.capability_name, "example-capability")
        self.assertEqual(control.control_ids, ("human-review-boundary",))
        advisory = finding(repository, "controls:effectiveness")
        self.assertIs(advisory.status, FindingStatus.ADVISORY)
        self.assertIn("do not prove control effectiveness", advisory.message)

    def test_missing_control_directory_is_a_legacy_compatible_warning(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "project"
            initialize_project(root, project_name="Missing Controls")
            mapping = root / "governance/controls/example-capability.json"
            mapping.unlink()
            mapping.parent.rmdir()

            report = check_repository(root)

        result = finding(report, "controls:directory")
        self.assertIs(result.status, FindingStatus.WARN)
        self.assertFalse(report.has_failures)
        self.assertFalse(
            any(item.check_id == "controls:effectiveness" for item in report.findings)
        )

    def test_not_applicable_control_passes_without_evidence_references(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "project"
            initialize_project(root, project_name="Not Applicable Control")
            mapping = root / "governance/controls/example-capability.json"
            write_json(mapping, read_json(FIXTURES / "not-applicable.json"))

            control = check_control_mapping(root, mapping)
            repository = check_repository(root)

        self.assertIs(control.status, ControlStatus.PASS)
        self.assertIn("1 not-applicable", control.messages[0])
        self.assertFalse(repository.has_failures)
        self.assertIs(
            finding(repository, "controls:effectiveness").status,
            FindingStatus.ADVISORY,
        )

    def test_broken_and_unsafe_references_fail_deterministically(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "project"
            initialize_project(root, project_name="Control References")
            mapping = root / "governance/controls/example-capability.json"
            payload = read_json(mapping)
            payload["controls"][0]["verification_refs"] = ["missing.md"]
            write_json(mapping, payload)

            missing = check_control_mapping(root, mapping)

            payload["controls"][0]["verification_refs"] = ["../outside.md"]
            write_json(mapping, payload)
            unsafe = check_control_mapping(root, mapping)

        self.assertIs(missing.status, ControlStatus.FAIL)
        self.assertTrue(any("does not exist" in item for item in missing.messages))
        self.assertIs(unsafe.status, ControlStatus.FAIL)
        self.assertTrue(
            any("parent traversal" in item for item in unsafe.messages)
        )

    def test_orphan_control_mapping_fails_inventory_closure(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "project"
            initialize_project(root, project_name="Orphan Control")
            orphan = root / "governance/controls/unlisted-capability.json"
            write_json(orphan, read_json(FIXTURES / "orphan.json"))

            report = check_repository(root)

        result = finding(
            report,
            "control:governance/controls/unlisted-capability.json",
        )
        self.assertIs(result.status, FindingStatus.FAIL)
        self.assertIn("orphan control mapping", result.message)
        self.assertIn("not listed in governance/inventory.json", result.message)

    def test_control_ids_are_unique_across_mappings(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "project"
            initialize_project(root, project_name="Duplicate Controls")
            add_inventory_capability(root, "second-capability")
            second = read_json(FIXTURES / "valid.json")
            second["capability_name"] = "second-capability"
            write_json(
                root / "governance/controls/second-capability.json",
                second,
            )

            report = check_repository(root)

        result = finding(
            report,
            "controls:control-id:human-review-boundary",
        )
        self.assertIs(result.status, FindingStatus.FAIL)
        self.assertIn("multiple mappings", result.message)

    def test_inventory_capability_without_mapping_is_a_warning(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "project"
            initialize_project(root, project_name="Partial Controls")
            add_inventory_capability(root, "second-capability")

            report = check_repository(root)

        result = finding(report, "controls:missing:second-capability")
        self.assertIs(result.status, FindingStatus.WARN)
        self.assertFalse(report.has_failures)

    def test_mapping_filename_must_match_declared_capability(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "project"
            initialize_project(root, project_name="Control Filename")
            source = root / "governance/controls/example-capability.json"
            renamed = source.with_name("misleading-name.json")
            source.rename(renamed)

            report = check_control_mapping(root, renamed)

        self.assertIs(report.status, ControlStatus.FAIL)
        self.assertTrue(any("must match" in item for item in report.messages))

    def test_control_findings_never_emit_a_coverage_percentage(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "project"
            initialize_project(root, project_name="No Control Coverage")

            report = check_repository(root)

        rendered = " ".join(
            item.message
            for item in report.findings
            if item.check_id.startswith("control")
        )
        self.assertNotIn("%", rendered)
        self.assertNotIn("coverage", rendered.lower())


if __name__ == "__main__":
    unittest.main()
