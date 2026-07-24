import contextlib
import io
import json
import re
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from agentgov.artifacts import export_capability_artifact
from agentgov.cli import EXIT_ERROR, EXIT_FAIL, EXIT_PASS, main
from agentgov.initializer import initialize_project
from agentgov.repository import FindingStatus, check_repository


_PLACEHOLDER_RE = re.compile(r"\{\{[A-Z][A-Z0-9_-]*\}\}")


def run_cli(*args: str) -> tuple[int, str, str]:
    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        exit_code = main(list(args))
    return exit_code, stdout.getvalue(), stderr.getvalue()


class RepositoryCheckTests(unittest.TestCase):
    def test_legacy_layout_is_supported_with_migration_warning(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "project"
            initialize_project(root, project_name="Legacy Layout")
            (root / "governance").rename(root / "prompt-governance")
            legacy = root / "prompt-governance"
            (legacy / "contracts").rename(legacy / "schemas")
            (legacy / "evidence").rename(legacy / "sources")
            manifest_path = legacy / "capabilities/example-capability.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["contracts"]["input_schema"] = (
                "prompt-governance/schemas/example-capability.input.schema.json"
            )
            manifest["contracts"]["output_schema"] = (
                "prompt-governance/schemas/example-capability.output.schema.json"
            )
            manifest["provenance"]["source_refs"] = [
                "prompt-governance/sources/example-capability.md"
            ]
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            report = check_repository(root)

        self.assertFalse(report.has_failures)
        self.assertTrue(
            any(
                finding.check_id == "governance:layout"
                and finding.status is FindingStatus.WARN
                for finding in report.findings
            )
        )

    def test_dual_layout_is_a_deterministic_conflict(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "project"
            initialize_project(root, project_name="Dual Layout")
            (root / "prompt-governance/capabilities").mkdir(parents=True)

            report = check_repository(root)

        self.assertTrue(report.has_failures)
        self.assertTrue(
            any(
                finding.check_id == "governance:layout"
                and finding.status is FindingStatus.FAIL
                for finding in report.findings
            )
        )

    def test_legacy_distribution_assets_do_not_create_a_dual_layout(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "project"
            initialize_project(root, project_name="Compatibility Assets")
            (root / "prompt-governance/fixtures").mkdir(parents=True)
            (root / "prompt-governance/capability.schema.json").write_text(
                "{}\n",
                encoding="utf-8",
            )

            report = check_repository(root)

        self.assertFalse(
            any(finding.check_id == "governance:layout" for finding in report.findings)
        )

    def test_evaluation_fixtures_are_not_treated_as_configured_bundles(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "project"
            initialize_project(root, project_name="Evaluation Fixtures")
            configured = root / "evaluation/example-capability"
            configured.rename(root / "evaluation/fixtures")

            report = check_repository(root)

        evaluation_finding = next(
            finding
            for finding in report.findings
            if finding.check_id == "evaluation:bundles"
        )
        self.assertIs(evaluation_finding.status, FindingStatus.WARN)
        self.assertIn("no evaluation bundles", evaluation_finding.message)

    def test_initialized_repository_has_warn_and_advisory_but_no_fail(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "project"
            initialize_project(root, project_name="Checked Project")

            report = check_repository(root)

        statuses = {finding.status for finding in report.findings}
        self.assertIn(FindingStatus.PASS, statuses)
        self.assertIn(FindingStatus.WARN, statuses)
        self.assertIn(FindingStatus.ADVISORY, statuses)
        self.assertNotIn(FindingStatus.FAIL, statuses)
        self.assertFalse(report.has_failures)
        self.assertEqual(
            {
                finding.check_id
                for finding in report.findings
                if finding.check_id.startswith("agent-skill:")
            },
            {
                "agent-skill:context-first-review",
                "agent-skill:development-slice",
                "agent-skill:incident-attribution",
                "agent-skill:incident-response",
            },
        )
        evaluation_finding = next(
            finding
            for finding in report.findings
            if finding.check_id == "evaluation:evaluation/example-capability"
        )
        self.assertIs(evaluation_finding.status, FindingStatus.WARN)
        self.assertIn("needs_seed_cases", evaluation_finding.message)
        artifact_finding = next(
            finding
            for finding in report.findings
            if finding.check_id == "artifacts:directory"
        )
        self.assertIs(artifact_finding.status, FindingStatus.WARN)

    def test_resolved_governance_files_pass_placeholder_check(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "project"
            initialize_project(root, project_name="Configured Project")
            for relative_path in (
                Path("AGENTS.md"),
                Path("docs/adr/TEMPLATE.md"),
                Path("docs/adr/INVARIANTS.md"),
            ):
                path = root / relative_path
                text = path.read_text(encoding="utf-8")
                path.write_text(_PLACEHOLDER_RE.sub("configured", text), encoding="utf-8")

            report = check_repository(root)

        placeholder_finding = next(
            finding
            for finding in report.findings
            if finding.check_id == "governance:placeholders"
        )
        self.assertIs(placeholder_finding.status, FindingStatus.PASS)

    def test_empty_repository_reports_missing_required_files(self) -> None:
        with TemporaryDirectory() as temp_dir:
            report = check_repository(Path(temp_dir))

        self.assertTrue(report.has_failures)
        self.assertEqual(report.count(FindingStatus.FAIL), 3)
        self.assertGreaterEqual(report.count(FindingStatus.WARN), 1)

    def test_invalid_capability_is_a_repository_failure(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "project"
            initialize_project(root, project_name="Invalid Capability Project")
            capability_path = (
                root / "governance/capabilities/example-capability.json"
            )
            capability = json.loads(capability_path.read_text(encoding="utf-8"))
            capability["risk_level"] = "critical"
            capability_path.write_text(json.dumps(capability), encoding="utf-8")

            report = check_repository(root)

        capability_finding = next(
            finding
            for finding in report.findings
            if finding.check_id.startswith("capability:")
        )
        self.assertIs(capability_finding.status, FindingStatus.FAIL)
        self.assertIn("must be true for high or critical risk", capability_finding.message)

    def test_broken_required_reference_is_a_repository_failure(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "project"
            initialize_project(root, project_name="Broken Reference Project")
            schema = root / "governance/contracts/example-capability.input.schema.json"
            schema.unlink()

            report = check_repository(root)

        reference_finding = next(
            finding
            for finding in report.findings
            if finding.check_id == "references:example-capability:contracts"
        )
        self.assertIs(reference_finding.status, FindingStatus.FAIL)
        self.assertIn("does not exist", reference_finding.message)

    def test_false_evaluation_readiness_is_a_repository_failure(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "project"
            initialize_project(root, project_name="False Readiness Project")
            manifest_path = root / "evaluation/example-capability/evaluation-manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["declared_readiness"] = "baseline_ready"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            report = check_repository(root)

        evaluation_finding = next(
            finding
            for finding in report.findings
            if finding.check_id == "evaluation:evaluation/example-capability"
        )
        self.assertIs(evaluation_finding.status, FindingStatus.FAIL)
        self.assertIn("human_approved must be true", evaluation_finding.message)

    def test_current_capability_artifact_is_a_repository_pass(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "project"
            initialize_project(root, project_name="Artifact Project")
            manifest = root / "governance/capabilities/example-capability.json"
            export_capability_artifact(manifest, repository=root)

            report = check_repository(root)

        artifact_finding = next(
            finding
            for finding in report.findings
            if finding.check_id == "artifact:example-capability"
        )
        self.assertIs(artifact_finding.status, FindingStatus.PASS)
        self.assertFalse(report.has_failures)
        self.assertFalse(
            any(finding.check_id == "artifacts:directory" for finding in report.findings)
        )

    def test_source_drift_is_a_repository_failure(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "project"
            initialize_project(root, project_name="Drift Project")
            source = root / "governance/evidence/example-capability.md"
            manifest = root / "governance/capabilities/example-capability.json"
            export_capability_artifact(manifest, repository=root)
            source.write_text("PROMPT = 'changed'\n", encoding="utf-8")

            report = check_repository(root)

        artifact_finding = next(
            finding
            for finding in report.findings
            if finding.check_id == "artifact:example-capability"
        )
        self.assertIs(artifact_finding.status, FindingStatus.FAIL)
        self.assertIn("source drift detected", artifact_finding.message)
        self.assertTrue(report.has_failures)

    def test_malformed_artifact_json_is_a_repository_failure(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "project"
            initialize_project(root, project_name="Malformed Artifact Project")
            artifact_dir = root / "governance/artifacts/example-capability"
            artifact_dir.mkdir(parents=True)
            (artifact_dir / "artifact.json").write_text("{broken", encoding="utf-8")

            report = check_repository(root)

        artifact_finding = next(
            finding
            for finding in report.findings
            if finding.check_id == "artifact:example-capability"
        )
        self.assertIs(artifact_finding.status, FindingStatus.FAIL)
        self.assertIn("invalid artifact JSON", artifact_finding.message)

    def test_partial_artifact_adoption_warns_for_each_missing_capability(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "project"
            initialize_project(root, project_name="Partial Artifact Project")
            first_manifest = (
                root / "governance/capabilities/example-capability.json"
            )
            export_capability_artifact(first_manifest, repository=root)
            second = json.loads(first_manifest.read_text(encoding="utf-8"))
            second["name"] = "second-capability"
            (root / "governance/capabilities/second-capability.json").write_text(
                json.dumps(second),
                encoding="utf-8",
            )

            report = check_repository(root)

        missing_finding = next(
            finding
            for finding in report.findings
            if finding.check_id == "artifact:second-capability"
        )
        self.assertIs(missing_finding.status, FindingStatus.WARN)
        self.assertIn("has no configured review artifact", missing_finding.message)


class RepositoryCliTests(unittest.TestCase):
    def test_warn_and_advisory_do_not_block_repository_check(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "project"
            initialize_project(root, project_name="CLI Project")

            exit_code, stdout, stderr = run_cli("check", "repository", str(root))

        self.assertEqual(exit_code, EXIT_PASS)
        self.assertIn("WARN governance:placeholders:", stdout)
        self.assertIn("WARN artifacts:directory:", stdout)
        self.assertIn("ADVISORY governance:human-review:", stdout)
        self.assertIn("SUMMARY PASS=11 WARN=4 FAIL=0 ADVISORY=1", stdout)
        self.assertEqual(stderr, "")

    def test_missing_required_files_return_fail(self) -> None:
        with TemporaryDirectory() as temp_dir:
            exit_code, stdout, stderr = run_cli(
                "check", "repository", str(Path(temp_dir))
            )

        self.assertEqual(exit_code, EXIT_FAIL)
        self.assertIn("FAIL required:constitution:", stdout)
        self.assertIn("FAIL=3", stdout)
        self.assertEqual(stderr, "")

    def test_missing_repository_path_returns_operational_error(self) -> None:
        with TemporaryDirectory() as temp_dir:
            missing = Path(temp_dir) / "missing"

            exit_code, stdout, stderr = run_cli(
                "check", "repository", str(missing)
            )

        self.assertEqual(exit_code, EXIT_ERROR)
        self.assertEqual(stdout, "")
        self.assertIn("ERROR repository: path not found:", stderr)


if __name__ == "__main__":
    unittest.main()
