import contextlib
import io
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from agentgov.cli import EXIT_ERROR, EXIT_FAIL, EXIT_PASS, main
from agentgov.consumer_ci import (
    UPGRADE_WORKFLOW_PATH,
    WORKFLOW_PATH,
    apply_integration_plan,
    plan_github_actions_integration,
    render_consumer_upgrade_workflow,
    render_consumer_workflow,
)
from agentgov.initializer import initialize_project
from agentgov.upgrade_pr import (
    UpgradePlanState,
    plan_upgrade_pull_request,
    render_upgrade_pull_request_plan_json,
)


ROOT = Path(__file__).resolve().parents[1]


def run_cli(*args: str) -> tuple[int, str, str]:
    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        exit_code = main(list(args))
    return exit_code, stdout.getvalue(), stderr.getvalue()


def write_manifest(
    root: Path,
    *,
    version: str = "0.2.0",
    supported_from: list[str] | None = None,
    repository_changes_declared: bool = False,
) -> Path:
    manifest = {
        "contract": "agentgov.release-manifest",
        "schema_version": "1.0",
        "distribution_name": "agent-governance-starter",
        "tool_version": version,
        "channel": "stable",
        "supported_from": supported_from or ["0.1.0"],
        "readable_layout_versions": ["1.0"],
        "target_layout_version": "1.0",
        "repository_changes_declared": repository_changes_declared,
        "declared_migrations": ["consumer-ci-v2"] if repository_changes_declared else [],
        "release_notes_url": (
            "https://github.com/Andy-JunXiong/agent-governance-starter/releases/"
            f"tag/v{version}"
        ),
        "artifact": {
            "filename": f"agent_governance_starter-{version}-py3-none-any.whl",
            "url": (
                "https://github.com/Andy-JunXiong/agent-governance-starter/"
                f"releases/download/v{version}/"
                f"agent_governance_starter-{version}-py3-none-any.whl"
            ),
            "sha256": "b" * 64,
            "install_method": "pipx",
        },
    }
    path = root / f"release-{version}.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    return path


def configured_repository(root: Path) -> None:
    initialize_project(root, project_name="Upgrade PR Fixture")
    apply_integration_plan(plan_github_actions_integration(root))


class UpgradePullRequestPlanTests(unittest.TestCase):
    def test_compatible_release_produces_one_exact_workflow_change(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            configured_repository(root)
            manifest = write_manifest(root)

            plan = plan_upgrade_pull_request(root, manifest_path=manifest)

        self.assertIs(plan.state, UpgradePlanState.CANDIDATE)
        self.assertEqual(plan.branch, "agentgov/update-0.2.0")
        self.assertEqual(len(plan.changes), 1)
        self.assertEqual(plan.changes[0].path, WORKFLOW_PATH)
        self.assertIn("pinned release 0.2.0", plan.changes[0].content)
        self.assertIn("b" * 64, plan.changes[0].content)
        self.assertNotEqual(
            plan.changes[0].before_sha256,
            plan.changes[0].after_sha256,
        )

    def test_current_release_has_no_change(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            configured_repository(root)
            manifest = write_manifest(root, version="0.1.0")

            plan = plan_upgrade_pull_request(root, manifest_path=manifest)

        self.assertIs(plan.state, UpgradePlanState.CURRENT)
        self.assertEqual(plan.changes, ())

    def test_already_upgraded_managed_workflow_can_plan_the_next_release(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            configured_repository(root)
            (root / WORKFLOW_PATH).write_text(
                render_consumer_workflow(
                    version="0.2.0",
                    wheel_sha256="d" * 64,
                ),
                encoding="utf-8",
            )
            manifest = write_manifest(
                root,
                version="0.2.1",
                supported_from=["0.2.0"],
            )

            plan = plan_upgrade_pull_request(root, manifest_path=manifest)

        self.assertIs(plan.state, UpgradePlanState.CANDIDATE)
        self.assertEqual(plan.current_version, "0.2.0")
        self.assertEqual(plan.available_version, "0.2.1")
        self.assertIn("from 0.2.0 to 0.2.1", plan.body)

    def test_custom_workflow_blocks_instead_of_overwriting(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            configured_repository(root)
            target = root / WORKFLOW_PATH
            target.write_text("custom\n", encoding="utf-8")
            manifest = write_manifest(root)

            plan = plan_upgrade_pull_request(root, manifest_path=manifest)

        self.assertIs(plan.state, UpgradePlanState.BLOCKED)
        self.assertIn("customized", plan.reasons[0])
        self.assertEqual(plan.changes, ())

    def test_declared_repository_migration_blocks_workflow_only_candidate(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            configured_repository(root)
            manifest = write_manifest(root, repository_changes_declared=True)

            plan = plan_upgrade_pull_request(root, manifest_path=manifest)

        self.assertIs(plan.state, UpgradePlanState.BLOCKED)
        self.assertIn("outside the bounded", plan.reasons[0])

    def test_declared_0_3_migration_plans_update_and_create(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            configured_repository(root)
            manifest = write_manifest(
                root,
                version="0.3.0",
                supported_from=["0.1.0"],
                repository_changes_declared=True,
            )

            plan = plan_upgrade_pull_request(root, manifest_path=manifest)

        self.assertIs(plan.state, UpgradePlanState.CANDIDATE)
        self.assertEqual(
            tuple((change.action, change.path) for change in plan.changes),
            (
                ("update", WORKFLOW_PATH),
                ("create", UPGRADE_WORKFLOW_PATH),
            ),
        )
        self.assertIsNone(plan.changes[1].before_sha256)
        self.assertIn("consumer-ci-v2", plan.reasons[0])

    def test_0_3_patch_upgrade_updates_both_exact_workflows(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            configured_repository(root)
            (root / WORKFLOW_PATH).write_text(
                render_consumer_workflow(version="0.3.0", wheel_sha256="d" * 64),
                encoding="utf-8",
            )
            (root / UPGRADE_WORKFLOW_PATH).write_text(
                render_consumer_upgrade_workflow(
                    version="0.3.0", wheel_sha256="d" * 64
                ),
                encoding="utf-8",
            )
            manifest = write_manifest(
                root,
                version="0.3.1",
                supported_from=["0.3.0"],
            )

            plan = plan_upgrade_pull_request(root, manifest_path=manifest)

        self.assertIs(plan.state, UpgradePlanState.CANDIDATE)
        self.assertEqual(
            tuple(change.path for change in plan.changes),
            (WORKFLOW_PATH, UPGRADE_WORKFLOW_PATH),
        )
        self.assertTrue(all(change.action == "update" for change in plan.changes))

    def test_0_3_current_state_requires_the_matching_upgrade_workflow(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            configured_repository(root)
            (root / WORKFLOW_PATH).write_text(
                render_consumer_workflow(version="0.3.0", wheel_sha256="d" * 64),
                encoding="utf-8",
            )
            manifest = write_manifest(
                root,
                version="0.3.0",
                supported_from=["0.3.0"],
            )

            plan = plan_upgrade_pull_request(root, manifest_path=manifest)

        self.assertIs(plan.state, UpgradePlanState.BLOCKED)
        self.assertIn("upgrade proposal workflow is missing", plan.reasons[0])

    def test_json_contract_is_read_only_and_denies_pr_authority(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            configured_repository(root)
            manifest = write_manifest(root)
            payload = json.loads(
                render_upgrade_pull_request_plan_json(
                    plan_upgrade_pull_request(root, manifest_path=manifest)
                )
            )

        self.assertEqual(payload["mode"], "read_only")
        self.assertEqual(payload["state"], "candidate")
        self.assertEqual(len(payload["pull_request"]["changes"]), 1)
        for value in payload["authority_boundary"].values():
            self.assertFalse(value)

    def test_schema_is_strict_and_denies_mutating_authority(self) -> None:
        schema = json.loads(
            (ROOT / "schemas/upgrade-pr-plan.schema.json").read_text(encoding="utf-8")
        )

        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(schema["properties"]["contract_version"]["const"], "1.1")
        self.assertEqual(
            schema["properties"]["pull_request"]["properties"]["changes"]["maxItems"],
            2,
        )
        authority = schema["properties"]["authority_boundary"]
        self.assertFalse(authority["additionalProperties"])
        for property_schema in authority["properties"].values():
            self.assertIs(property_schema["const"], False)


class UpgradePullRequestCliTests(unittest.TestCase):
    def test_cli_prints_candidate_without_writing(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            configured_repository(root)
            manifest = write_manifest(root)
            before = (root / WORKFLOW_PATH).read_bytes()

            exit_code, stdout, stderr = run_cli(
                "plan", "upgrade-pr", str(root), "--manifest", str(manifest)
            )
            after = (root / WORKFLOW_PATH).read_bytes()

        self.assertEqual(exit_code, EXIT_PASS)
        self.assertEqual(before, after)
        self.assertIn("STATE candidate", stdout)
        self.assertIn("BRANCH agentgov/update-0.2.0", stdout)
        self.assertIn("no repository file, Git branch, pull request", stdout)
        self.assertEqual(stderr, "")

    def test_cli_blocked_plan_returns_policy_failure(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            configured_repository(root)
            (root / WORKFLOW_PATH).write_text("custom\n", encoding="utf-8")
            manifest = write_manifest(root)

            exit_code, stdout, stderr = run_cli(
                "plan", "upgrade-pr", str(root), "--manifest", str(manifest)
            )

        self.assertEqual(exit_code, EXIT_FAIL)
        self.assertIn("STATE blocked", stdout)
        self.assertEqual(stderr, "")

    def test_cli_missing_manifest_is_operational_error(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            configured_repository(root)

            exit_code, stdout, stderr = run_cli(
                "plan",
                "upgrade-pr",
                str(root),
                "--manifest",
                str(root / "missing.json"),
            )

        self.assertEqual(exit_code, EXIT_ERROR)
        self.assertEqual(stdout, "")
        self.assertIn("path not found", stderr)


if __name__ == "__main__":
    unittest.main()
