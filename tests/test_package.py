import contextlib
import io
import tomllib
import unittest
from pathlib import Path

from agentgov import __version__
from agentgov.cli import main


ROOT = Path(__file__).resolve().parents[1]


class PackageTests(unittest.TestCase):
    def test_package_exposes_stable_version(self) -> None:
        self.assertEqual(__version__, "0.2.0")

    def test_package_metadata_uses_the_runtime_version_as_its_single_source(
        self,
    ) -> None:
        pyproject = tomllib.loads(
            (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        )

        self.assertNotIn("version", pyproject["project"])
        self.assertIn("version", pyproject["project"]["dynamic"])
        self.assertEqual(
            pyproject["tool"]["setuptools"]["dynamic"]["version"],
            {"attr": "agentgov.__version__"},
        )

    def test_cli_reports_the_runtime_version(self) -> None:
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            with self.assertRaises(SystemExit) as raised:
                main(["--version"])

        self.assertEqual(raised.exception.code, 0)
        self.assertEqual(stdout.getvalue(), f"agentgov {__version__}\n")

    def test_package_uses_spdx_license_string(self) -> None:
        pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))

        self.assertEqual(pyproject["project"]["license"], "MIT")

    def test_mit_license_file_matches_package_metadata(self) -> None:
        pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
        license_text = (ROOT / "LICENSE").read_text(encoding="utf-8")

        self.assertEqual(pyproject["project"]["license"], "MIT")
        self.assertTrue(license_text.startswith("MIT License\n"))
        self.assertIn("Copyright (c) 2026 Andy", license_text)
        self.assertIn("Permission is hereby granted, free of charge", license_text)
        self.assertIn('THE SOFTWARE IS PROVIDED "AS IS"', license_text)


if __name__ == "__main__":
    unittest.main()
