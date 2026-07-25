import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/release.yml"


class ReleaseWorkflowTests(unittest.TestCase):
    def test_release_is_tag_only_and_uses_pinned_official_actions(self) -> None:
        text = WORKFLOW.read_text(encoding="utf-8")

        self.assertIn('tags:\n      - "v[0-9]+.[0-9]+.[0-9]+"', text)
        self.assertNotIn("pull_request:", text)
        self.assertIn(
            "actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd",
            text,
        )
        self.assertIn(
            "actions/setup-python@a309ff8b426b58ec0e2a45f0f869d46889d02405",
            text,
        )
        self.assertIn("persist-credentials: false", text)

    def test_release_builds_validates_and_publishes_both_assets(self) -> None:
        text = WORKFLOW.read_text(encoding="utf-8")

        self.assertIn("permissions:\n  contents: write", text)
        self.assertIn("python -m unittest discover -s tests -v", text)
        self.assertIn("python -m build --wheel", text)
        self.assertIn("scripts/build_release_manifest.py", text)
        self.assertIn("check release-manifest", text)
        self.assertIn("gh release create", text)
        self.assertIn("dist/agent_governance_starter-*.whl", text)
        self.assertIn("dist/release-manifest.json", text)
        self.assertIn("GH_TOKEN: ${{ github.token }}", text)


if __name__ == "__main__":
    unittest.main()
