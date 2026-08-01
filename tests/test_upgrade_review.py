import contextlib
import io
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from agentgov.cli import EXIT_ERROR, EXIT_FAIL, EXIT_PASS, main
from agentgov.consumer_ci import (
    WORKFLOW_PATH,
    apply_integration_plan,
    plan_github_actions_integration,
)
from agentgov.initializer import initialize_project
from agentgov.upgrade_review import (
    UpgradeReviewConflictError,
    create_upgrade_review_bundle,
)


ROOT = Path(__file__).resolve().parents[1]


def run_cli(*args: str) -> tuple[int, str, str]:
    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        exit_code = main(list(args))
    return exit_code, stdout.getvalue(), stderr.getvalue()


def configured_repository(root: Path) -> None:
    initialize_project(root, project_name="Consumer Upgrade Review Fixture")
    apply_integration_plan(plan_github_actions_integration(root))


def write_manifest(
    root: Path,
    *,
    version: str = "0.2.0",
    channel: str = "stable",
) -> Path:
    document = {
        "contract": "agentgov.release-manifest",
        "schema_version": "1.0",
        "distribution_name": "agent-governance-starter",
        "tool_version": version,
        "channel": channel,
        "supported_from": ["0.1.0"],
        "readable_layout_versions": ["1.0"],
        "target_layout_version": "1.0",
        "repository_changes_declared": False,
        "declared_migrations": [],
        "release_notes_url": (
            "https://github.com/Andy-JunXiong/agent-governance-starter/"
            f"releases/tag/v{version}"
        ),
        "artifact": {
            "filename": f"agent_governance_starter-{version}-py3-none-any.whl",
            "url": (
                "https://github.com/Andy-JunXiong/agent-governance-starter/"
                f"releases/download/v{version}/"
                f"agent_governance_starter-{version}-py3-none-any.whl"
            ),
            "sha256": "c" * 64,
            "install_method": "pipx",
        },
    }
    path = root / "release-manifest.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    return path


class UpgradeReviewBundleTests(unittest.TestCase):
    def test_candidate_bundle_is_consumer_local_portable_and_non_mutating(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "consumer"
            root.mkdir()
            configured_repository(root)
            manifest = write_manifest(Path(temp_dir))
            output = root / "upgrade-review"
            workflow = root / WORKFLOW_PATH
            before = workflow.read_bytes()

            result = create_upgrade_review_bundle(
                root,
                manifest_path=manifest,
                output=output,
            )
            after = workflow.read_bytes()
            review = json.loads(
                (output / "upgrade-review.json").read_text(encoding="utf-8")
            )
            plan = json.loads(
                (output / "upgrade-plan.json").read_text(encoding="utf-8")
            )
            files = sorted(path.name for path in output.iterdir())

        self.assertEqual(result.state, "ready_for_human_review")
        self.assertEqual(before, after)
        self.assertEqual(review["consumer"], {"name": "consumer"})
        self.assertEqual(review["transition"]["plan_state"], "candidate")
        self.assertEqual(len(review["transition"]["changes"]), 1)
        self.assertEqual(review["human_decision"]["state"], "pending")
        self.assertFalse(review["authority_boundary"]["planned_change_applied"])
        self.assertEqual(plan["repository"], "consumer")
        self.assertEqual(plan["manifest_source"], "release-manifest.json")
        self.assertNotIn(str(Path(temp_dir)), json.dumps(review))
        self.assertNotIn(str(Path(temp_dir)), json.dumps(plan))
        self.assertEqual(
            files,
            [
                "UPGRADE_REVIEW.md",
                "current-status.md",
                "release-manifest.json",
                "upgrade-plan.json",
                "upgrade-review.json",
                "workflow.patch",
            ],
        )

    def test_release_candidate_is_visible_but_blocked(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "consumer"
            root.mkdir()
            configured_repository(root)
            manifest = write_manifest(Path(temp_dir), version="0.2.0rc1", channel="release-candidate")

            result = create_upgrade_review_bundle(
                root,
                manifest_path=manifest,
                output=root / "upgrade-review",
            )

        self.assertTrue(result.blocked)
        stable_gate = next(
            gate for gate in result.gates if gate["id"] == "stable-release-manifest"
        )
        self.assertEqual(stable_gate["status"], "FAIL")

    def test_existing_review_output_is_preserved(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "consumer"
            root.mkdir()
            configured_repository(root)
            manifest = write_manifest(Path(temp_dir))
            output = root / "upgrade-review"
            output.mkdir()
            marker = output / "human.txt"
            marker.write_text("keep\n", encoding="utf-8")

            with self.assertRaises(UpgradeReviewConflictError):
                create_upgrade_review_bundle(
                    root,
                    manifest_path=manifest,
                    output=output,
                )

            self.assertEqual(marker.read_text(encoding="utf-8"), "keep\n")

    def test_schema_is_strict_and_denies_upgrade_authority(self) -> None:
        schema = json.loads(
            (ROOT / "schemas/upgrade-review.schema.json").read_text(encoding="utf-8")
        )

        self.assertFalse(schema["additionalProperties"])
        authority = schema["properties"]["authority_boundary"]
        self.assertTrue(authority["properties"]["review_output_created"]["const"])
        for name, property_schema in authority["properties"].items():
            if name != "review_output_created":
                self.assertIs(property_schema["const"], False)


class UpgradeReviewCliTests(unittest.TestCase):
    def test_cli_creates_ready_consumer_review(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "consumer"
            root.mkdir()
            configured_repository(root)
            manifest = write_manifest(Path(temp_dir))
            output = root / "upgrade-review"

            exit_code, stdout, stderr = run_cli(
                "review",
                "upgrade",
                str(root),
                "--manifest",
                str(manifest),
                "--output",
                str(output),
            )

        self.assertEqual(exit_code, EXIT_PASS)
        self.assertIn("STATE ready_for_human_review", stdout)
        self.assertIn("DECISION pending", stdout)
        self.assertIn("planned consumer workflow change was not applied", stdout)
        self.assertEqual(stderr, "")

    def test_cli_returns_fail_for_blocked_release_candidate(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "consumer"
            root.mkdir()
            configured_repository(root)
            manifest = write_manifest(Path(temp_dir), version="0.2.0rc1", channel="release-candidate")

            exit_code, stdout, stderr = run_cli(
                "review",
                "upgrade",
                str(root),
                "--manifest",
                str(manifest),
                "--output",
                str(root / "upgrade-review"),
            )

        self.assertEqual(exit_code, EXIT_FAIL)
        self.assertIn("STATE blocked", stdout)
        self.assertEqual(stderr, "")

    def test_cli_missing_manifest_is_operational_error(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)

            exit_code, stdout, stderr = run_cli(
                "review",
                "upgrade",
                str(root),
                "--manifest",
                str(root / "missing.json"),
                "--output",
                str(root / "upgrade-review"),
            )

        self.assertEqual(exit_code, EXIT_ERROR)
        self.assertEqual(stdout, "")
        self.assertIn("release manifest must be a regular file", stderr)


if __name__ == "__main__":
    unittest.main()
