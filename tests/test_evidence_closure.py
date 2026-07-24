import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from agentgov.artifacts import export_capability_artifact
from agentgov.initializer import initialize_project
from agentgov.repository import FindingStatus, check_repository


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "governance/fixtures/orphan-evidence"


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def finding(report, check_id: str):
    return next(item for item in report.findings if item.check_id == check_id)


class EvidenceClosureTests(unittest.TestCase):
    def test_declared_evaluation_is_connected_by_manifest_claim(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "project"
            initialize_project(root, project_name="Declared Evaluation")

            report = check_repository(root)

        result = finding(report, "evaluation:evaluation/example-capability")
        self.assertIs(result.status, FindingStatus.WARN)
        self.assertIn(
            "capability 'example-capability' is declared in "
            "governance/inventory.json",
            result.message,
        )

    def test_orphan_evaluation_fails_deterministically(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "project"
            initialize_project(root, project_name="Orphan Evaluation")
            manifest_path = (
                root / "evaluation/example-capability/evaluation-manifest.json"
            )
            write_json(
                manifest_path,
                read_json(FIXTURES / "orphan-evaluation-manifest.json"),
            )

            report = check_repository(root)

        result = finding(report, "evaluation:evaluation/example-capability")
        self.assertIs(result.status, FindingStatus.FAIL)
        self.assertIn(
            "orphan evaluation declares capability 'unlisted-capability'",
            result.message,
        )
        self.assertIn("not listed in governance/inventory.json", result.message)

    def test_evaluation_directory_name_is_not_used_as_capability_identity(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "project"
            initialize_project(root, project_name="Claimed Evaluation Identity")
            source = root / "evaluation/example-capability"
            source.rename(root / "evaluation/misleading-directory")

            report = check_repository(root)

        result = finding(report, "evaluation:evaluation/misleading-directory")
        self.assertIs(result.status, FindingStatus.WARN)
        self.assertIn("capability 'example-capability' is declared", result.message)
        self.assertFalse(report.has_failures)

    def test_declared_artifact_is_connected_by_artifact_claim(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "project"
            initialize_project(root, project_name="Declared Artifact")
            manifest = root / "governance/capabilities/example-capability.json"
            export_capability_artifact(manifest, repository=root)

            report = check_repository(root)

        result = finding(report, "artifact:example-capability")
        self.assertIs(result.status, FindingStatus.PASS)
        self.assertIn(
            "capability 'example-capability' is declared in "
            "governance/inventory.json",
            result.message,
        )

    def test_orphan_artifact_fails_deterministically(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "project"
            initialize_project(root, project_name="Orphan Artifact")
            canonical = root / "governance/capabilities/example-capability.json"
            unlisted = root / "support/unlisted-capability.json"
            unlisted.parent.mkdir()
            manifest = read_json(canonical)
            manifest.update(
                read_json(FIXTURES / "orphan-artifact-capability.json")
            )
            write_json(unlisted, manifest)
            export_capability_artifact(unlisted, repository=root)

            report = check_repository(root)

        result = finding(report, "artifact:unlisted-capability")
        self.assertIs(result.status, FindingStatus.FAIL)
        self.assertIn(
            "orphan artifact declares capability 'unlisted-capability'",
            result.message,
        )
        self.assertIn("not listed in governance/inventory.json", result.message)
        self.assertIn(
            "manifest, source hash, and generated Markdown are current",
            result.message,
        )
        self.assertNotIn("drift detected", result.message)

    def test_artifact_directory_name_is_not_used_as_capability_identity(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "project"
            initialize_project(root, project_name="Claimed Artifact Identity")
            manifest = root / "governance/capabilities/example-capability.json"
            exported = export_capability_artifact(manifest, repository=root)
            renamed = exported.directory.with_name("misleading-directory")
            exported.directory.rename(renamed)

            report = check_repository(root)

        result = finding(report, "artifact:misleading-directory")
        self.assertIs(result.status, FindingStatus.PASS)
        self.assertIn("capability 'example-capability' is declared", result.message)
        self.assertFalse(report.has_failures)
        self.assertFalse(
            any(
                item.check_id == "artifact:example-capability"
                and item.status is FindingStatus.WARN
                for item in report.findings
            )
        )

    def test_missing_inventory_does_not_create_orphan_cascade(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "project"
            initialize_project(root, project_name="Legacy Evidence")
            manifest_path = (
                root / "evaluation/example-capability/evaluation-manifest.json"
            )
            write_json(
                manifest_path,
                read_json(FIXTURES / "orphan-evaluation-manifest.json"),
            )
            (root / "governance/inventory.json").unlink()

            report = check_repository(root)

        inventory = finding(report, "inventory:governance/inventory.json")
        evaluation = finding(
            report,
            "evaluation:evaluation/example-capability",
        )
        self.assertIs(inventory.status, FindingStatus.WARN)
        self.assertIs(evaluation.status, FindingStatus.WARN)
        self.assertNotIn("orphan evaluation", evaluation.message)
        self.assertFalse(report.has_failures)

    def test_invalid_inventory_does_not_create_orphan_cascade(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "project"
            initialize_project(root, project_name="Invalid Inventory Evidence")
            evaluation_path = (
                root / "evaluation/example-capability/evaluation-manifest.json"
            )
            write_json(
                evaluation_path,
                read_json(FIXTURES / "orphan-evaluation-manifest.json"),
            )
            inventory_path = root / "governance/inventory.json"
            inventory = read_json(inventory_path)
            inventory["capabilities"][0]["owner"] = "Mismatched owner"
            write_json(inventory_path, inventory)

            report = check_repository(root)

        inventory_finding = finding(
            report,
            "inventory:governance/inventory.json",
        )
        evaluation = finding(
            report,
            "evaluation:evaluation/example-capability",
        )
        self.assertIs(inventory_finding.status, FindingStatus.FAIL)
        self.assertIs(evaluation.status, FindingStatus.WARN)
        self.assertNotIn("orphan evaluation", evaluation.message)
        self.assertTrue(report.has_failures)


if __name__ == "__main__":
    unittest.main()
