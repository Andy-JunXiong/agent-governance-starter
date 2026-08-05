import hashlib
import json
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from agentgov.release_metadata import validate_release_manifest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/build_release_manifest.py"
CURRENT = ROOT / "release/current.json"


class ReleaseManifestBuilderTests(unittest.TestCase):
    def _build(self, version: str, *, channel: str | None = None) -> dict[str, object]:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            wheel = root / f"agent_governance_starter-{version}-py3-none-any.whl"
            wheel.write_bytes(b"reviewed wheel fixture")
            output = root / "release-manifest.json"
            command = [
                sys.executable,
                str(SCRIPT),
                str(wheel),
                str(output),
                "--version",
                version,
            ]
            if channel is not None:
                command.extend(["--channel", channel])
            subprocess.run(command, check=True, capture_output=True, text=True)
            document = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(validate_release_manifest(document), [])
        self.assertEqual(document["supported_from"], ["0.1.0"])
        self.assertEqual(
            document["artifact"]["sha256"],
            hashlib.sha256(b"reviewed wheel fixture").hexdigest(),
        )
        return document

    def test_default_stable_manifest_matches_final_wheel(self) -> None:
        document = self._build("0.2.0")

        self.assertEqual(document["channel"], "stable")
        self.assertEqual(document["tool_version"], "0.2.0")
        self.assertIn("/releases/download/v0.2.0/", document["artifact"]["url"])

    def test_release_candidate_manifest_matches_rc_wheel(self) -> None:
        document = self._build("0.2.0rc1", channel="release-candidate")

        self.assertEqual(document["channel"], "release-candidate")
        self.assertEqual(document["tool_version"], "0.2.0rc1")
        self.assertIn(
            "/releases/download/v0.2.0rc1/",
            document["artifact"]["url"],
        )

    def test_release_candidate_uses_bundled_compatibility_metadata(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            wheel = root / "agent_governance_starter-0.3.0rc1-py3-none-any.whl"
            wheel.write_bytes(b"reviewed wheel fixture")
            output = root / "release-manifest.json"

            subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    str(wheel),
                    str(output),
                    "--version",
                    "0.3.0rc1",
                    "--channel",
                    "release-candidate",
                    "--metadata",
                    str(CURRENT),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            document = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(document["supported_from"], ["0.1.0", "0.2.0", "0.2.1"])
        self.assertEqual(validate_release_manifest(document), [])

    def test_bundled_metadata_preserves_patch_upgrade_sources(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            wheel = root / "agent_governance_starter-0.2.1-py3-none-any.whl"
            wheel.write_bytes(b"reviewed wheel fixture")
            output = root / "release-manifest.json"
            metadata = root / "current.json"
            metadata.write_text(
                json.dumps({
                    "tool_version": "0.2.1",
                    "channel": "stable",
                    "supported_from": ["0.1.0", "0.2.0"],
                }),
                encoding="utf-8",
            )

            subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    str(wheel),
                    str(output),
                    "--version",
                    "0.2.1",
                    "--metadata",
                    str(metadata),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            document = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(document["supported_from"], ["0.1.0", "0.2.0"])
        self.assertEqual(validate_release_manifest(document), [])

    def test_version_filename_mismatch_is_rejected_before_output(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            wheel = root / "agent_governance_starter-0.2.0-py3-none-any.whl"
            wheel.write_bytes(b"fixture")
            output = root / "release-manifest.json"

            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    str(wheel),
                    str(output),
                    "--version",
                    "0.2.1",
                ],
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 2)
            self.assertIn("wheel filename must match --version exactly", result.stderr)
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
