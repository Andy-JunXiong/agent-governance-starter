import contextlib
import io
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from agentgov.cli import EXIT_ERROR, EXIT_FAIL, EXIT_PASS, main
from agentgov.initializer import initialize_project
from agentgov.references import (
    ReferenceStatus,
    check_capability_references,
)


def run_cli(*args: str) -> tuple[int, str, str]:
    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        exit_code = main(list(args))
    return exit_code, stdout.getvalue(), stderr.getvalue()


def initialized_repository(parent: Path) -> tuple[Path, Path]:
    root = parent / "project"
    initialize_project(root, project_name="Reference Project")
    manifest = root / "governance/capabilities/example-capability.json"
    return root, manifest


def update_manifest(path: Path, update) -> None:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    update(manifest)
    path.write_text(json.dumps(manifest), encoding="utf-8")


class CapabilityReferenceTests(unittest.TestCase):
    def test_initialized_capability_has_required_refs_and_optional_evidence_warn(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root, manifest = initialized_repository(Path(temp_dir))

            report = check_capability_references(manifest, repository=root)

        self.assertFalse(report.has_failures)
        self.assertEqual(report.count(ReferenceStatus.PASS), 3)
        self.assertEqual(report.count(ReferenceStatus.WARN), 1)
        evaluation = next(
            finding
            for finding in report.findings
            if finding.check_id.endswith(":evaluation")
        )
        self.assertIn("no evaluation evidence is declared", evaluation.message)

    def test_missing_required_schema_fails(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root, manifest = initialized_repository(Path(temp_dir))
            (root / "governance/contracts/example-capability.input.schema.json").unlink()

            report = check_capability_references(manifest, repository=root)

        contracts = next(
            finding
            for finding in report.findings
            if finding.check_id.endswith(":contracts")
        )
        self.assertIs(contracts.status, ReferenceStatus.FAIL)
        self.assertIn("does not exist", contracts.message)

    def test_invalid_schema_json_fails(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root, manifest = initialized_repository(Path(temp_dir))
            schema = root / "governance/contracts/example-capability.output.schema.json"
            schema.write_text("{broken", encoding="utf-8")

            report = check_capability_references(manifest, repository=root)

        contracts = next(
            finding
            for finding in report.findings
            if finding.check_id.endswith(":contracts")
        )
        self.assertIs(contracts.status, ReferenceStatus.FAIL)
        self.assertIn("invalid JSON", contracts.message)

    def test_non_utf8_schema_fails_as_reference_integrity(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root, manifest = initialized_repository(Path(temp_dir))
            schema = root / "governance/contracts/example-capability.output.schema.json"
            schema.write_bytes(b"\xff\xfe")

            report = check_capability_references(manifest, repository=root)

        contracts = next(
            finding
            for finding in report.findings
            if finding.check_id.endswith(":contracts")
        )
        self.assertIs(contracts.status, ReferenceStatus.FAIL)
        self.assertIn("not valid UTF-8", contracts.message)

    def test_declared_missing_caller_fails(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root, manifest = initialized_repository(Path(temp_dir))
            update_manifest(
                manifest,
                lambda payload: payload.__setitem__("called_by", ["src/missing-caller.py"]),
            )

            report = check_capability_references(manifest, repository=root)

        callers = next(
            finding
            for finding in report.findings
            if finding.check_id.endswith(":callers")
        )
        self.assertIs(callers.status, ReferenceStatus.FAIL)
        self.assertIn("declared caller does not exist", callers.message)

    def test_source_path_cannot_escape_repository(self) -> None:
        with TemporaryDirectory() as temp_dir:
            parent = Path(temp_dir)
            root, manifest = initialized_repository(parent)
            (parent / "outside.md").write_text("outside\n", encoding="utf-8")
            update_manifest(
                manifest,
                lambda payload: payload["provenance"].__setitem__(
                    "source_refs", ["../outside.md"]
                ),
            )

            report = check_capability_references(manifest, repository=root)

        sources = next(
            finding
            for finding in report.findings
            if finding.check_id.endswith(":sources")
        )
        self.assertIs(sources.status, ReferenceStatus.FAIL)
        self.assertIn("must stay within repository root", sources.message)

    def test_symbolic_link_source_is_rejected_when_supported(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root, manifest = initialized_repository(Path(temp_dir))
            link = root / "governance/evidence/linked-source.md"
            target = root / "governance/evidence/example-capability.md"
            try:
                link.symlink_to(target)
            except OSError as exc:
                self.skipTest(f"symbolic links are unavailable: {exc}")
            update_manifest(
                manifest,
                lambda payload: payload["provenance"].__setitem__(
                    "source_refs", ["governance/evidence/linked-source.md"]
                ),
            )

            report = check_capability_references(manifest, repository=root)

        sources = next(
            finding
            for finding in report.findings
            if finding.check_id.endswith(":sources")
        )
        self.assertIs(sources.status, ReferenceStatus.FAIL)
        self.assertTrue(
            "symbolic link" in sources.message
            or "must stay within repository root" in sources.message
        )

    def test_declared_missing_evaluation_evidence_fails(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root, manifest = initialized_repository(Path(temp_dir))
            update_manifest(
                manifest,
                lambda payload: payload["evaluation"].__setitem__(
                    "evidence_refs", ["evaluation/missing-evidence.json"]
                ),
            )

            report = check_capability_references(manifest, repository=root)

        evaluation = next(
            finding
            for finding in report.findings
            if finding.check_id.endswith(":evaluation")
        )
        self.assertIs(evaluation.status, ReferenceStatus.FAIL)
        self.assertIn("does not exist", evaluation.message)

    def test_existing_evaluation_evidence_directory_passes(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root, manifest = initialized_repository(Path(temp_dir))
            update_manifest(
                manifest,
                lambda payload: payload["evaluation"].__setitem__(
                    "evidence_refs", ["evaluation/example-capability"]
                ),
            )

            report = check_capability_references(manifest, repository=root)

        evaluation = next(
            finding
            for finding in report.findings
            if finding.check_id.endswith(":evaluation")
        )
        self.assertIs(evaluation.status, ReferenceStatus.PASS)

    def test_schema_json_pointer_fragment_resolves_file(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root, manifest = initialized_repository(Path(temp_dir))
            update_manifest(
                manifest,
                lambda payload: payload["contracts"].__setitem__(
                    "input_schema",
                    "governance/contracts/example-capability.input.schema.json#/$defs/input",
                ),
            )

            report = check_capability_references(manifest, repository=root)

        contracts = next(
            finding
            for finding in report.findings
            if finding.check_id.endswith(":contracts")
        )
        self.assertIs(contracts.status, ReferenceStatus.PASS)


class CapabilityReferenceCliTests(unittest.TestCase):
    def test_optional_evidence_warning_does_not_block(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root, manifest = initialized_repository(Path(temp_dir))

            exit_code, stdout, stderr = run_cli(
                "check",
                "references",
                str(manifest),
                "--repository",
                str(root),
            )

        self.assertEqual(exit_code, EXIT_PASS)
        self.assertIn("WARN references:example-capability:evaluation:", stdout)
        self.assertIn("SUMMARY PASS=3 WARN=1 FAIL=0", stdout)
        self.assertEqual(stderr, "")

    def test_broken_required_reference_returns_fail(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root, manifest = initialized_repository(Path(temp_dir))
            (root / "governance/evidence/example-capability.md").unlink()

            exit_code, stdout, stderr = run_cli(
                "check",
                "references",
                str(manifest),
                "--repository",
                str(root),
            )

        self.assertEqual(exit_code, EXIT_FAIL)
        self.assertIn("FAIL references:example-capability:sources:", stdout)
        self.assertEqual(stderr, "")

    def test_missing_manifest_returns_operational_error(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            missing = root / "missing.json"

            exit_code, stdout, stderr = run_cli(
                "check",
                "references",
                str(missing),
                "--repository",
                str(root),
            )

        self.assertEqual(exit_code, EXIT_ERROR)
        self.assertEqual(stdout, "")
        self.assertIn("ERROR references: path not found:", stderr)


if __name__ == "__main__":
    unittest.main()
