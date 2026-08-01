import contextlib
import io
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from agentgov import __version__
from agentgov.cli import EXIT_ERROR, EXIT_FAIL, EXIT_PASS, main
from agentgov.release_metadata import (
    RELEASE_MANIFEST_CONTRACT,
    RELEASE_MANIFEST_SCHEMA_VERSION,
    load_release_manifest,
    validate_release_manifest,
)


ROOT = Path(__file__).resolve().parents[1]
VALID = ROOT / "release/fixtures/valid-rc.json"
INVALID = ROOT / "release/fixtures/invalid-contract.json"
CURRENT = ROOT / "release/current.json"


def run_cli(*args: str) -> tuple[int, str, str]:
    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        exit_code = main(list(args))
    return exit_code, stdout.getvalue(), stderr.getvalue()


class ReleaseManifestTests(unittest.TestCase):
    def test_bundled_current_manifest_is_valid(self) -> None:
        self.assertEqual(validate_release_manifest(load_release_manifest(CURRENT)), [])

    def test_bundled_candidate_matches_runtime_and_stable_upgrade_source(self) -> None:
        document = load_release_manifest(CURRENT)

        self.assertEqual(document["tool_version"], __version__)
        self.assertEqual(document["channel"], "release-candidate")
        self.assertEqual(document["supported_from"], ["0.1.0"])
        self.assertEqual(document["target_layout_version"], "1.0")
        self.assertFalse(document["repository_changes_declared"])
        self.assertEqual(document["declared_migrations"], [])

    def test_valid_rc_manifest_declares_compatibility_without_authority(self) -> None:
        document = load_release_manifest(VALID)

        self.assertEqual(validate_release_manifest(document), [])
        self.assertTrue(document["repository_changes_declared"])
        self.assertEqual(
            document["declared_migrations"],
            ["inventory-1.0-to-1.1"],
        )
        self.assertNotIn("write_authorized", document)
        self.assertNotIn("authorized_by", document)

    def test_stable_manifest_requires_fixed_release_asset_and_digest(self) -> None:
        document = dict(load_release_manifest(VALID))
        document["tool_version"] = "0.1.0"
        document["channel"] = "stable"
        document["artifact"] = {
            "filename": "agent_governance_starter-0.1.0-py3-none-any.whl",
            "url": (
                "https://github.com/Andy-JunXiong/agent-governance-starter/"
                "releases/download/v0.1.0/"
                "agent_governance_starter-0.1.0-py3-none-any.whl"
            ),
            "sha256": "a" * 64,
            "install_method": "pipx",
        }

        self.assertEqual(validate_release_manifest(document), [])

    def test_invalid_manifest_rejects_channel_version_and_false_compatibility(
        self,
    ) -> None:
        errors = validate_release_manifest(load_release_manifest(INVALID))

        self.assertIn(
            "$.channel release-candidate requires an rc tool version",
            errors,
        )
        self.assertIn("$.supported_from contains an unsupported value", errors)
        self.assertIn(
            "$.target_layout_version must be listed in "
            "$.readable_layout_versions",
            errors,
        )
        self.assertIn(
            "$.repository_changes_declared must be true when migrations are declared",
            errors,
        )
        self.assertIn("$.release_notes_url must be an https URL", errors)

    def test_unknown_fields_and_duplicate_values_fail_strictly(self) -> None:
        document = dict(load_release_manifest(VALID))
        document["unsupported"] = True
        document["readable_layout_versions"] = ["1.0", "1.0"]

        errors = validate_release_manifest(document)

        self.assertIn("$.unsupported is not allowed", errors)
        self.assertIn(
            "$.readable_layout_versions must contain unique items",
            errors,
        )

    def test_schema_matches_validator_contract_constants(self) -> None:
        schema = json.loads(
            (ROOT / "schemas/release-manifest.schema.json").read_text(
                encoding="utf-8"
            )
        )

        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(
            schema["properties"]["contract"]["const"],
            RELEASE_MANIFEST_CONTRACT,
        )
        self.assertEqual(
            schema["properties"]["schema_version"]["const"],
            RELEASE_MANIFEST_SCHEMA_VERSION,
        )
        self.assertEqual(set(schema["required"]), set(schema["properties"]))


class ReleaseManifestCliTests(unittest.TestCase):
    def test_valid_manifest_returns_pass(self) -> None:
        exit_code, stdout, stderr = run_cli(
            "check",
            "release-manifest",
            str(VALID),
        )

        self.assertEqual(exit_code, EXIT_PASS)
        self.assertIn("PASS release-manifest:", stdout)
        self.assertEqual(stderr, "")

    def test_contract_violation_returns_fail(self) -> None:
        exit_code, stdout, stderr = run_cli(
            "check",
            "release-manifest",
            str(INVALID),
        )

        self.assertEqual(exit_code, EXIT_FAIL)
        self.assertIn("FAIL release-manifest:", stdout)
        self.assertEqual(stderr, "")

    def test_missing_and_malformed_documents_are_operational_errors(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            missing = root / "missing.json"
            malformed = root / "malformed.json"
            malformed.write_text('{"secret": "do-not-echo",', encoding="utf-8")

            missing_result = run_cli(
                "check",
                "release-manifest",
                str(missing),
            )
            malformed_result = run_cli(
                "check",
                "release-manifest",
                str(malformed),
            )

        self.assertEqual(missing_result[0], EXIT_ERROR)
        self.assertIn("file not found", missing_result[2])
        self.assertEqual(malformed_result[0], EXIT_ERROR)
        self.assertIn("invalid JSON", malformed_result[2])
        self.assertNotIn("do-not-echo", malformed_result[2])

    def test_non_object_document_is_an_operational_error(self) -> None:
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "array.json"
            path.write_text("[]\n", encoding="utf-8")

            exit_code, stdout, stderr = run_cli(
                "check",
                "release-manifest",
                str(path),
            )

        self.assertEqual(exit_code, EXIT_ERROR)
        self.assertEqual(stdout, "")
        self.assertIn("root must be an object", stderr)


if __name__ == "__main__":
    unittest.main()
