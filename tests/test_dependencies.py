import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from agentgov.dependencies import (
    CAPABILITY_DEPENDENCIES_CONTRACT,
    CAPABILITY_DEPENDENCIES_SCHEMA_VERSION,
    READINESS_ORDER,
    DependencyStatus,
    check_dependency_declaration,
    find_dependency_cycles,
    readiness_meets,
    validate_dependency_document,
)
from agentgov.initializer import initialize_project
from agentgov.inventory import InventoryStatus, check_inventory
from agentgov.repository import FindingStatus, check_repository


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "governance/fixtures/dependencies"


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def finding(report, check_id: str):
    return next(item for item in report.findings if item.check_id == check_id)


def add_inventory_capability(
    root: Path,
    name: str,
    *,
    readiness: str = "needs_seed_cases",
) -> None:
    manifest = read_json(
        root / "governance/capabilities/example-capability.json"
    )
    manifest["name"] = name
    manifest["owner"] = f"{name} owner"
    manifest["evaluation"]["readiness"] = readiness
    manifest["evaluation"]["evidence_refs"] = (
        ["AGENTS.md"]
        if readiness in {"baseline_ready", "regression_ready"}
        else []
    )
    write_json(root / f"governance/capabilities/{name}.json", manifest)

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


def write_dependencies(
    root: Path,
    capability_name: str,
    depends_on: list[dict],
) -> Path:
    path = root / f"governance/dependencies/{capability_name}.json"
    write_json(
        path,
        {
            "contract": CAPABILITY_DEPENDENCIES_CONTRACT,
            "schema_version": CAPABILITY_DEPENDENCIES_SCHEMA_VERSION,
            "capability_name": capability_name,
            "depends_on": depends_on,
        },
    )
    return path


class CapabilityDependencyTests(unittest.TestCase):
    def test_schema_is_strict_and_matches_validator_constants(self) -> None:
        schema = read_json(
            ROOT / "governance/capability-dependencies.schema.json"
        )
        dependency = schema["$defs"]["dependency"]

        self.assertEqual(
            schema["properties"]["contract"]["const"],
            CAPABILITY_DEPENDENCIES_CONTRACT,
        )
        self.assertEqual(
            schema["properties"]["schema_version"]["const"],
            CAPABILITY_DEPENDENCIES_SCHEMA_VERSION,
        )
        self.assertFalse(schema["additionalProperties"])
        self.assertFalse(dependency["additionalProperties"])
        self.assertEqual(
            tuple(dependency["properties"]["minimum_readiness"]["enum"]),
            READINESS_ORDER,
        )

    def test_fixtures_cover_empty_explicit_and_implicit_minimum(self) -> None:
        for fixture in (
            "valid-empty.json",
            "valid-explicit-minimum.json",
            "valid-no-minimum.json",
        ):
            with self.subTest(fixture=fixture):
                self.assertEqual(
                    validate_dependency_document(read_json(FIXTURES / fixture)),
                    [],
                )

        errors = validate_dependency_document(
            read_json(FIXTURES / "invalid-self.json")
        )
        self.assertIn(
            "$.depends_on[0].capability must not depend on itself",
            errors,
        )

    def test_readiness_order_only_applies_to_explicit_thresholds(self) -> None:
        self.assertTrue(readiness_meets("baseline_ready", "baseline_ready"))
        self.assertTrue(readiness_meets("regression_ready", "baseline_ready"))
        self.assertFalse(readiness_meets("needs_seed_cases", "baseline_ready"))

    def test_cycle_detection_returns_precise_components(self) -> None:
        cycles = find_dependency_cycles(
            {
                "a": {"b"},
                "b": {"a"},
                "downstream": {"a"},
                "independent": set(),
            }
        )

        self.assertEqual(cycles, (("a", "b"),))

    def test_initialized_empty_declaration_passes_with_advisory(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "project"
            initialize_project(root, project_name="Dependency Project")
            declaration = (
                root / "governance/dependencies/example-capability.json"
            )

            result = check_dependency_declaration(root, declaration)
            repository = check_repository(root)
            inventory = check_inventory(root)

        self.assertIs(result.status, DependencyStatus.PASS)
        self.assertEqual(result.dependencies, ())
        self.assertIs(inventory.status, InventoryStatus.PASS)
        self.assertEqual(
            dict(inventory.capability_readiness),
            {"example-capability": "needs_seed_cases"},
        )
        advisory = finding(repository, "dependencies:completeness")
        self.assertIs(advisory.status, FindingStatus.ADVISORY)
        self.assertIn("cannot prove", advisory.message)

    def test_missing_directory_is_a_legacy_compatible_warning(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "project"
            initialize_project(root, project_name="Missing Dependencies")
            declaration = (
                root / "governance/dependencies/example-capability.json"
            )
            declaration.unlink()
            declaration.parent.rmdir()

            report = check_repository(root)

        result = finding(report, "dependencies:directory")
        self.assertIs(result.status, FindingStatus.WARN)
        self.assertFalse(report.has_failures)
        self.assertFalse(
            any(
                item.check_id == "dependencies:completeness"
                for item in report.findings
            )
        )

    def test_orphan_dependency_endpoint_fails_inventory_closure(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "project"
            initialize_project(root, project_name="Orphan Dependency")
            write_dependencies(
                root,
                "example-capability",
                [{"capability": "unlisted-capability"}],
            )

            report = check_repository(root)

        result = finding(
            report,
            "dependency:governance/dependencies/example-capability.json",
        )
        self.assertIs(result.status, FindingStatus.FAIL)
        self.assertIn("dependency endpoint", result.message)
        self.assertIn("not listed in governance/inventory.json", result.message)

    def test_self_dependency_fails_deterministically(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "project"
            initialize_project(root, project_name="Self Dependency")
            declaration = write_dependencies(
                root,
                "example-capability",
                [{"capability": "example-capability"}],
            )

            result = check_dependency_declaration(root, declaration)

        self.assertIs(result.status, DependencyStatus.FAIL)
        self.assertTrue(
            any("must not depend on itself" in item for item in result.messages)
        )

    def test_invalid_minimum_is_a_finding_not_an_operational_error(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "project"
            initialize_project(root, project_name="Invalid Readiness Floor")
            add_inventory_capability(root, "upstream-capability")
            write_dependencies(
                root,
                "example-capability",
                [
                    {
                        "capability": "upstream-capability",
                        "minimum_readiness": "production_ready",
                    }
                ],
            )

            report = check_repository(root)

        result = finding(
            report,
            "dependency:governance/dependencies/example-capability.json",
        )
        self.assertIs(result.status, FindingStatus.FAIL)
        self.assertIn("minimum_readiness must be one of", result.message)

    def test_cycle_fails_deterministically(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "project"
            initialize_project(root, project_name="Dependency Cycle")
            add_inventory_capability(root, "second-capability")
            write_dependencies(
                root,
                "example-capability",
                [{"capability": "second-capability"}],
            )
            write_dependencies(
                root,
                "second-capability",
                [{"capability": "example-capability"}],
            )

            report = check_repository(root)

        result = finding(
            report,
            "dependencies:cycle:example-capability,second-capability",
        )
        self.assertIs(result.status, FindingStatus.FAIL)
        self.assertIn("cycle detected", result.message)

    def test_explicit_minimum_readiness_is_enforced(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "project"
            initialize_project(root, project_name="Readiness Floor")
            add_inventory_capability(
                root,
                "upstream-capability",
                readiness="needs_seed_cases",
            )
            write_dependencies(
                root,
                "example-capability",
                [
                    {
                        "capability": "upstream-capability",
                        "minimum_readiness": "baseline_ready",
                    }
                ],
            )
            write_dependencies(root, "upstream-capability", [])

            report = check_repository(root)

        result = finding(
            report,
            "dependency:governance/dependencies/example-capability.json",
        )
        self.assertIs(result.status, FindingStatus.FAIL)
        self.assertIn("does not meet explicit minimum", result.message)

    def test_explicit_minimum_readiness_can_pass(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "project"
            initialize_project(root, project_name="Satisfied Floor")
            add_inventory_capability(
                root,
                "upstream-capability",
                readiness="baseline_ready",
            )
            write_dependencies(
                root,
                "example-capability",
                [
                    {
                        "capability": "upstream-capability",
                        "minimum_readiness": "baseline_ready",
                    }
                ],
            )
            write_dependencies(root, "upstream-capability", [])

            report = check_repository(root)

        result = finding(
            report,
            "dependency:governance/dependencies/example-capability.json",
        )
        self.assertIs(result.status, FindingStatus.PASS)
        self.assertIn("meets explicit minimum", result.message)
        self.assertFalse(report.has_failures)

    def test_readiness_difference_without_minimum_is_non_blocking(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "project"
            initialize_project(root, project_name="No Implicit Floor")
            add_inventory_capability(
                root,
                "upstream-capability",
                readiness="not_configured",
            )
            write_dependencies(
                root,
                "example-capability",
                [{"capability": "upstream-capability"}],
            )
            write_dependencies(root, "upstream-capability", [])

            report = check_repository(root)

        result = finding(
            report,
            "dependency:governance/dependencies/example-capability.json",
        )
        self.assertIs(result.status, FindingStatus.PASS)
        self.assertNotIn("minimum", result.message.split("; ")[-1])
        self.assertFalse(report.has_failures)

    def test_inventory_capability_without_declaration_is_a_warning(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "project"
            initialize_project(root, project_name="Partial Dependencies")
            add_inventory_capability(root, "second-capability")

            report = check_repository(root)

        result = finding(report, "dependencies:missing:second-capability")
        self.assertIs(result.status, FindingStatus.WARN)
        self.assertFalse(report.has_failures)

    def test_filename_must_match_declared_capability(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "project"
            initialize_project(root, project_name="Dependency Filename")
            source = root / "governance/dependencies/example-capability.json"
            renamed = source.with_name("misleading-name.json")
            source.rename(renamed)

            result = check_dependency_declaration(root, renamed)

        self.assertIs(result.status, DependencyStatus.FAIL)
        self.assertTrue(any("must match" in item for item in result.messages))

    def test_dependency_findings_never_emit_a_coverage_percentage(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "project"
            initialize_project(root, project_name="No Dependency Percentage")

            report = check_repository(root)

        rendered = " ".join(
            item.message
            for item in report.findings
            if item.check_id.startswith("dependenc")
        )
        self.assertNotIn("%", rendered)
        self.assertNotIn("coverage", rendered.lower())


if __name__ == "__main__":
    unittest.main()
