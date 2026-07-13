import contextlib
import io
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from agentgov.artifacts import (
    ArtifactConflictError,
    ArtifactPolicyError,
    check_capability_artifact,
    export_capability_artifact,
)
from agentgov.cli import EXIT_ERROR, EXIT_FAIL, EXIT_PASS, main


ROOT = Path(__file__).resolve().parents[1]
BASE_MANIFEST = json.loads(
    (
        ROOT
        / "prompt-governance"
        / "fixtures"
        / "valid"
        / "runtime-low-risk.json"
    ).read_text(encoding="utf-8")
)


def run_cli(*args: str) -> tuple[int, str, str]:
    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        exit_code = main(list(args))
    return exit_code, stdout.getvalue(), stderr.getvalue()


def make_repository(root: Path, *, source_ref: str = "src/prompt.py") -> Path:
    source_path = root / source_ref
    source_path.parent.mkdir(parents=True, exist_ok=True)
    source_path.write_text("PROMPT = 'Summarize approved notes.'\n", encoding="utf-8")

    manifest = json.loads(json.dumps(BASE_MANIFEST))
    manifest["provenance"]["source_refs"] = [source_ref]
    manifest_path = root / "prompt-governance/capabilities/release-summary.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest_path


class CapabilityArtifactTests(unittest.TestCase):
    def test_export_creates_reviewable_deterministic_artifact(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            manifest_path = make_repository(root)

            exported = export_capability_artifact(manifest_path, repository=root)
            state = json.loads((exported.directory / "artifact.json").read_text("utf-8"))
            markdown = (exported.directory / "CAPABILITY.md").read_text("utf-8")
            check = check_capability_artifact(exported.directory, repository=root)

        self.assertEqual(exported.capability_name, "summarize-release-notes")
        self.assertEqual(state["artifact_version"], "1.0")
        self.assertEqual(state["source_refs"], ["src/prompt.py"])
        self.assertRegex(state["source_hash"], r"^sha256:[0-9a-f]{64}$")
        self.assertIn("# Capability artifact: summarize-release-notes", markdown)
        self.assertNotIn("Summarize approved notes.", markdown)
        self.assertNotIn("last_updated", markdown)
        self.assertTrue(check.passed)

    def test_reexport_requires_explicit_replace_and_preserves_manual_files(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            manifest_path = make_repository(root)
            first = export_capability_artifact(manifest_path, repository=root)
            markdown_before = (first.directory / "CAPABILITY.md").read_bytes()
            state_before = (first.directory / "artifact.json").read_bytes()
            manual = first.directory / "review-notes.md"
            manual.write_text("human notes\n", encoding="utf-8")

            with self.assertRaises(ArtifactConflictError):
                export_capability_artifact(manifest_path, repository=root)

            second = export_capability_artifact(
                manifest_path,
                repository=root,
                replace=True,
            )

            self.assertEqual(
                (second.directory / "CAPABILITY.md").read_bytes(),
                markdown_before,
            )
            self.assertEqual(
                (second.directory / "artifact.json").read_bytes(),
                state_before,
            )
            self.assertEqual(manual.read_text(encoding="utf-8"), "human notes\n")

    def test_source_change_is_reported_as_drift(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            manifest_path = make_repository(root)
            exported = export_capability_artifact(manifest_path, repository=root)
            (root / "src/prompt.py").write_text("PROMPT = 'Changed.'\n", encoding="utf-8")

            check = check_capability_artifact(exported.directory, repository=root)

        self.assertFalse(check.passed)
        self.assertIn("source drift detected", check.messages)

    def test_manifest_change_is_reported_as_drift(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            manifest_path = make_repository(root)
            exported = export_capability_artifact(manifest_path, repository=root)
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["purpose"] = "Summarize approved release notes for another audience."
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            check = check_capability_artifact(exported.directory, repository=root)

        self.assertFalse(check.passed)
        self.assertIn("manifest drift detected", check.messages)

    def test_generated_markdown_change_is_reported_as_drift(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            manifest_path = make_repository(root)
            exported = export_capability_artifact(manifest_path, repository=root)
            (exported.directory / "CAPABILITY.md").write_text(
                "manual generated-file edit\n",
                encoding="utf-8",
            )

            check = check_capability_artifact(exported.directory, repository=root)

        self.assertFalse(check.passed)
        self.assertIn("generated Markdown drift detected", check.messages)

    def test_source_reference_cannot_escape_repository(self) -> None:
        with TemporaryDirectory() as temp_dir:
            parent = Path(temp_dir)
            root = parent / "repo"
            root.mkdir()
            outside = parent / "outside.py"
            outside.write_text("SECRET = 'not read'\n", encoding="utf-8")
            manifest_path = make_repository(root)
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["provenance"]["source_refs"] = ["../outside.py"]
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            with self.assertRaises(ArtifactPolicyError) as raised:
                export_capability_artifact(manifest_path, repository=root)

        self.assertIn("must stay within repository root", str(raised.exception))

    def test_output_cannot_escape_repository(self) -> None:
        with TemporaryDirectory() as temp_dir:
            parent = Path(temp_dir)
            root = parent / "repo"
            root.mkdir()
            manifest_path = make_repository(root)

            with self.assertRaises(ArtifactPolicyError):
                export_capability_artifact(
                    manifest_path,
                    repository=root,
                    output=Path("../outside"),
                )

        self.assertFalse((parent / "outside").exists())

    def test_stale_declared_source_hash_blocks_export(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            manifest_path = make_repository(root)
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["provenance"]["source_hash"] = "sha256:" + "0" * 64
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            with self.assertRaises(ArtifactPolicyError) as raised:
                export_capability_artifact(manifest_path, repository=root)

        self.assertIn("does not match current repository sources", str(raised.exception))


class CapabilityArtifactCliTests(unittest.TestCase):
    def test_export_and_check_commands_pass(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            manifest_path = make_repository(root)

            export_code, export_stdout, export_stderr = run_cli(
                "export",
                "capability",
                str(manifest_path),
                "--repository",
                str(root),
            )
            artifact_dir = root / "prompt-governance/artifacts/summarize-release-notes"
            check_code, check_stdout, check_stderr = run_cli(
                "check",
                "artifact",
                str(artifact_dir),
                "--repository",
                str(root),
            )

        self.assertEqual(export_code, EXIT_PASS)
        self.assertIn("PASS export capability: summarize-release-notes", export_stdout)
        self.assertEqual(export_stderr, "")
        self.assertEqual(check_code, EXIT_PASS)
        self.assertIn("PASS artifact:", check_stdout)
        self.assertEqual(check_stderr, "")

    def test_export_conflict_returns_policy_failure(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            manifest_path = make_repository(root)
            export_capability_artifact(manifest_path, repository=root)

            exit_code, stdout, stderr = run_cli(
                "export",
                "capability",
                str(manifest_path),
                "--repository",
                str(root),
            )

        self.assertEqual(exit_code, EXIT_FAIL)
        self.assertIn("FAIL export capability:", stdout)
        self.assertEqual(stderr, "")

    def test_source_drift_returns_policy_failure(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            manifest_path = make_repository(root)
            exported = export_capability_artifact(manifest_path, repository=root)
            (root / "src/prompt.py").write_text("changed\n", encoding="utf-8")

            exit_code, stdout, stderr = run_cli(
                "check",
                "artifact",
                str(exported.directory),
                "--repository",
                str(root),
            )

        self.assertEqual(exit_code, EXIT_FAIL)
        self.assertIn("source drift detected", stdout)
        self.assertEqual(stderr, "")

    def test_malformed_artifact_json_returns_operational_error(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            artifact_dir = root / "artifact"
            artifact_dir.mkdir()
            (artifact_dir / "artifact.json").write_text("{broken", encoding="utf-8")

            exit_code, stdout, stderr = run_cli(
                "check",
                "artifact",
                str(artifact_dir),
                "--repository",
                str(root),
            )

        self.assertEqual(exit_code, EXIT_ERROR)
        self.assertEqual(stdout, "")
        self.assertIn("ERROR artifact: invalid JSON", stderr)


if __name__ == "__main__":
    unittest.main()
