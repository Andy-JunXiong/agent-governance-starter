from __future__ import annotations

import copy
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.distribution_input_manifest.manifest import (
    ManifestError,
    canonical_content_digest,
    canonical_path_digest,
    check_manifest,
    derive_distribution_inputs,
)


PYPROJECT = """\
[build-system]
requires = ["setuptools>=69"]
build-backend = "setuptools.build_meta"

[project]
name = "fixture"
version = "1.0"
readme = "README.md"
license = "MIT"

[tool.setuptools.packages.find]
where = ["src"]

[tool.setuptools.data-files]
"share/fixture" = ["data/*.txt"]
"""


class DistributionInputManifestTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self._write("pyproject.toml", PYPROJECT)
        self._write("LICENSE", "MIT fixture\n")
        self._write("README.md", "fixture readme\n")
        self._write("src/fixture/__init__.py", "VALUE = 1\n")
        self._write("data/top.txt", "top\n")
        self._write("data/nested/deep.txt", "deep\n")
        self._git("init", "-q")
        self._git("config", "user.email", "fixture@example.invalid")
        self._git("config", "user.name", "Fixture")
        self._git("add", ".")
        self._git("commit", "-qm", "fixture")
        self.manifest_path = self.root / "manifest.json"
        self._write_manifest(self._manifest())

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _write(self, relative: str, content: str) -> None:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def _git(self, *args: str) -> str:
        result = subprocess.run(
            ["git", *args], cwd=self.root, text=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
        )
        return result.stdout

    def _manifest(self) -> dict[str, object]:
        paths = derive_distribution_inputs(self.root)
        return {
            "contract": "agentgov.distribution-input-manifest",
            "schema_version": "1.0",
            "authority": {
                "authorizes_build": False,
                "authorizes_git_write": False,
                "authorizes_journey": False,
                "authorizes_publication": False,
                "authorizes_release": False,
                "authorizes_deployment": False,
            },
            "derivation": {
                "pyproject": "pyproject.toml",
                "fixed_metadata_inputs": ["LICENSE", "pyproject.toml"],
                "package_inputs": "regular .py files below each tool.setuptools.packages.find.where root",
                "data_file_inputs": "regular files matched by tool.setuptools.data-files source patterns",
                "glob_semantics": "python-glob-nonrecursive-unless-double-star",
            },
            "supersession": {
                "supersedes": "exact-distribution-pathspec-replay-v1 omitted path list",
                "historical_observed_count": 199,
                "recovered_historical_paths": False,
                "reason": "A current contract, not historical recovery.",
            },
            "paths": paths,
            "path_digest": canonical_path_digest(paths),
            "content_digest": canonical_content_digest(self.root, paths),
        }

    def _write_manifest(self, manifest: dict[str, object]) -> None:
        self.manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    def test_pass_and_nonrecursive_glob(self) -> None:
        result = check_manifest(self.root, self.manifest_path)
        self.assertEqual("PASS", result["status"])
        self.assertNotIn("data/nested/deep.txt", result.get("paths", []))
        self.assertNotIn("data/nested/deep.txt", derive_distribution_inputs(self.root))

    def test_manifest_missing_derived_path_fails(self) -> None:
        manifest = self._manifest()
        manifest["paths"].remove("data/top.txt")  # type: ignore[union-attr]
        self._write_manifest(manifest)
        result = check_manifest(self.root, self.manifest_path)
        self.assertEqual("FAIL", result["status"])
        self.assertEqual(["data/top.txt"], result["differences"]["extra"])

    def test_manifest_extra_path_fails(self) -> None:
        self._write("notes.txt", "not distributed\n")
        manifest = self._manifest()
        manifest["paths"].append("notes.txt")  # type: ignore[union-attr]
        manifest["paths"].sort()  # type: ignore[union-attr]
        self._write_manifest(manifest)
        result = check_manifest(self.root, self.manifest_path)
        self.assertEqual("FAIL", result["status"])
        self.assertEqual(["notes.txt"], result["differences"]["missing"])

    def test_unsafe_duplicate_and_unsorted_paths_fail_closed(self) -> None:
        for replacement, expected in (
            (["../secret"], "safe relative"),
            (["LICENSE", "LICENSE"], "unique"),
            (["pyproject.toml", "LICENSE"], "sorted"),
        ):
            with self.subTest(expected=expected):
                manifest = self._manifest()
                manifest["paths"] = replacement
                self._write_manifest(manifest)
                with self.assertRaisesRegex(ManifestError, expected):
                    check_manifest(self.root, self.manifest_path)

    def test_unsupported_package_configuration_fails_closed(self) -> None:
        candidates = (
            (PYPROJECT.replace('where = ["src"]', 'where = ["src"]\ninclude = ["fixture*"]'), "unsupported package-find keys"),
            (PYPROJECT + '\n[tool.setuptools.dynamic]\nreadme = {file = ["OTHER.md"]}\n', "dynamic.*supported"),
            (PYPROJECT.replace('"share/fixture"', '"../outside"'), "safe relative"),
        )
        for content, expected in candidates:
            with self.subTest(expected=expected):
                self._write("pyproject.toml", content)
                with self.assertRaisesRegex(ManifestError, expected):
                    check_manifest(self.root, self.manifest_path)

    def test_untracked_overlay_is_classified(self) -> None:
        self._write("src/fixture/overlay.py", "OVERLAY = True\n")
        self._write_manifest(self._manifest())
        result = check_manifest(self.root, self.manifest_path)
        self.assertEqual("PASS", result["status"])
        self.assertEqual(1, result["classifications"]["untracked_overlay"])

    def test_tracked_deletion_is_classified_and_fails(self) -> None:
        (self.root / "src/fixture/__init__.py").unlink()
        result = check_manifest(self.root, self.manifest_path)
        self.assertEqual("FAIL", result["status"])
        self.assertEqual(1, result["classifications"]["deletion"])
        self.assertEqual(["src/fixture/__init__.py"], result["differences"]["missing"])

    def test_content_change_is_tracked_and_digest_fails(self) -> None:
        self._write("src/fixture/__init__.py", "VALUE = 2\n")
        result = check_manifest(self.root, self.manifest_path)
        self.assertEqual("FAIL", result["status"])
        self.assertIn("manifest digest mismatch: content_digest", result["errors"])
        self.assertEqual(1, result["classifications"]["tracked_delta"])

    def test_symbolic_link_fails_closed(self) -> None:
        target = self.root / "src/fixture/linked.py"
        try:
            os.symlink(self.root / "src/fixture/__init__.py", target)
        except (OSError, NotImplementedError) as exc:
            self.skipTest(f"symbolic links unavailable: {exc}")
        with self.assertRaisesRegex(ManifestError, "symbolic links"):
            check_manifest(self.root, self.manifest_path)

    def test_result_is_privacy_bounded_and_checker_is_read_only(self) -> None:
        before_status = self._git("status", "--porcelain=v1", "-z")
        before_manifest = self.manifest_path.read_bytes()
        result = check_manifest(self.root, self.manifest_path)
        after_status = self._git("status", "--porcelain=v1", "-z")
        rendered = json.dumps(result, sort_keys=True)
        self.assertEqual(before_status, after_status)
        self.assertEqual(before_manifest, self.manifest_path.read_bytes())
        self.assertNotIn(str(self.root), rendered)
        self.assertNotIn("VALUE = 1", rendered)
        self.assertFalse(result["claims"]["artifact_built"])
        self.assertFalse(result["claims"]["historical_199_paths_recovered"])

    def test_root_contract_and_digests_are_strict(self) -> None:
        manifest = self._manifest()
        for mutation, expected in (
            (("unexpected", True), "manifest keys"),
            (("path_digest", "sha256:" + "0" * 64), None),
        ):
            candidate = copy.deepcopy(manifest)
            candidate[mutation[0]] = mutation[1]
            self._write_manifest(candidate)
            if expected:
                with self.assertRaisesRegex(ManifestError, expected):
                    check_manifest(self.root, self.manifest_path)
            else:
                result = check_manifest(self.root, self.manifest_path)
                self.assertEqual("FAIL", result["status"])
                self.assertIn("path_digest", result["errors"][0])


if __name__ == "__main__":
    unittest.main()
