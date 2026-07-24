import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CI_WORKFLOW = ROOT / ".github/workflows/ci.yml"


class CiWorkflowContractTests(unittest.TestCase):
    def test_ci_covers_supported_python_versions_on_linux_and_windows(self) -> None:
        workflow = CI_WORKFLOW.read_text(encoding="utf-8")

        self.assertIn("ubuntu-latest", workflow)
        self.assertIn("windows-latest", workflow)
        for version in ("3.11", "3.12", "3.13"):
            self.assertIn(f'- "{version}"', workflow)
        self.assertIn("python -m pip install --no-deps .", workflow)
        self.assertIn("python -m unittest discover -s tests -v", workflow)
        self.assertIn("agentgov check repository .", workflow)
        self.assertIn(
            "agentgov report repository . --format json --output governance-report.json",
            workflow,
        )
        self.assertIn(
            "actions/upload-artifact@b7c566a772e6b6bfb58ed0dc250532a479d7789f",
            workflow,
        )
        self.assertIn("if: always()", workflow)

    def test_ci_uses_pinned_official_actions_and_read_only_permissions(self) -> None:
        workflow = CI_WORKFLOW.read_text(encoding="utf-8")

        self.assertIn(
            "actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd",
            workflow,
        )
        self.assertIn(
            "actions/setup-python@a309ff8b426b58ec0e2a45f0f869d46889d02405",
            workflow,
        )
        self.assertIn("permissions:\n  contents: read\n", workflow)
        self.assertIn("persist-credentials: false", workflow)
        self.assertNotIn("pull_request_target", workflow)
        self.assertNotIn("secrets.", workflow)
        self.assertIsNone(
            re.search(r"(?m)^\s+[a-z-]+:\s*write\s*$", workflow)
        )


if __name__ == "__main__":
    unittest.main()
