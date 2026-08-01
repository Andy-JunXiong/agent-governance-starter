import contextlib
import io
import json
import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from agentgov.cli import EXIT_ERROR, main
from agentgov.consumer_ci import WORKFLOW_PATH, render_consumer_workflow
from agentgov.initializer import initialize_project
from agentgov.upgrade_writer import (
    PullRequest,
    RemoteFile,
    UpgradeWriteConflictError,
    UpgradeWriteState,
    create_upgrade_draft_pull_request as create_upgrade_write,
    render_upgrade_write_result_json,
)


class FakeGitHubClient:
    def __init__(self, *, base_content: str, base: str = "main") -> None:
        self.branches = {base: "base-sha"}
        self.files = {(base, WORKFLOW_PATH.as_posix()): RemoteFile(base_content, "blob-1")}
        self.changed_paths: dict[str, tuple[str, ...]] = {}
        self.pull_request: PullRequest | None = None
        self.last_pr_body: str | None = None
        self.calls: list[str] = []

    def get_branch_sha(self, branch: str) -> str | None:
        self.calls.append(f"get-branch:{branch}")
        return self.branches.get(branch)

    def get_file(self, path: str, *, ref: str) -> RemoteFile:
        self.calls.append(f"get-file:{ref}:{path}")
        return self.files[(ref, path)]

    def create_branch(self, branch: str, *, sha: str) -> None:
        self.calls.append(f"create-branch:{branch}")
        self.branches[branch] = sha
        self.files[(branch, WORKFLOW_PATH.as_posix())] = self.files[
            ("main", WORKFLOW_PATH.as_posix())
        ]

    def update_file(
        self,
        path: str,
        *,
        branch: str,
        current_sha: str,
        content: str,
        message: str,
    ) -> str:
        self.calls.append(f"update-file:{branch}:{path}")
        self.files[(branch, path)] = RemoteFile(content, "blob-2")
        self.branches[branch] = "upgrade-commit"
        self.changed_paths[branch] = (path,)
        return "upgrade-commit"

    def compare_changed_paths(self, *, base: str, head: str) -> tuple[str, ...]:
        self.calls.append(f"compare:{base}:{head}")
        return self.changed_paths.get(head, ())

    def find_open_pull_request(
        self,
        *,
        branch: str,
        base: str,
    ) -> PullRequest | None:
        self.calls.append(f"find-pr:{base}:{branch}")
        return self.pull_request

    def create_draft_pull_request(
        self,
        *,
        branch: str,
        base: str,
        title: str,
        body: str,
    ) -> PullRequest:
        self.calls.append(f"create-pr:{base}:{branch}")
        self.last_pr_body = body
        self.pull_request = PullRequest(
            17,
            "https://github.com/owner/repository/pull/17",
            True,
        )
        return self.pull_request


def write_consumer(root: Path, version: str = "0.3.0") -> str:
    initialize_project(root, project_name="Upgrade Writer Fixture")
    content = render_consumer_workflow(version=version, wheel_sha256="a" * 64)
    target = root / WORKFLOW_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return content


def write_manifest(root: Path, version: str = "0.3.1") -> Path:
    document = {
        "contract": "agentgov.release-manifest",
        "schema_version": "1.0",
        "distribution_name": "agent-governance-starter",
        "tool_version": version,
        "channel": "stable",
        "supported_from": ["0.3.0"],
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
            "sha256": "b" * 64,
            "install_method": "pipx",
        },
    }
    path = root / "release-manifest.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    return path


def write_validation_report(root: Path, *, name: str, version: str) -> Path:
    path = root / f"{name}.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "tool": {"name": "agentgov", "version": version},
                "repository": "upgrade-writer-fixture",
                "summary": {"pass": 1, "warn": 0, "fail": 0, "advisory": 0},
                "findings": [
                    {"check_id": "fixture:check", "status": "PASS", "message": "fixture"}
                ],
                "known_gaps": [],
                "recommended_actions": [],
                "scope_limitations": [],
            }
        ),
        encoding="utf-8",
    )
    return path


def create_upgrade_draft_pull_request(
    root: Path,
    *,
    manifest_path: Path,
    repository: str,
    base_branch: str,
    event_source: str,
    client: FakeGitHubClient,
):
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    current = write_validation_report(root, name="current-report", version="0.3.0")
    target = write_validation_report(
        root,
        name="target-report",
        version=str(manifest["tool_version"]),
    )
    return create_upgrade_write(
        root,
        manifest_path=manifest_path,
        repository=repository,
        base_branch=base_branch,
        event_source=event_source,
        client=client,
        current_report_path=current,
        target_report_path=target,
    )


class UpgradeWriterTests(unittest.TestCase):
    def test_creates_one_exact_workflow_commit_and_draft_pull_request(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            current = write_consumer(root)
            manifest = write_manifest(root)
            client = FakeGitHubClient(base_content=current)

            result = create_upgrade_draft_pull_request(
                root,
                manifest_path=manifest,
                repository="owner/repository",
                base_branch="main",
                event_source="schedule",
                client=client,
            )

        self.assertIs(result.state, UpgradeWriteState.CREATED)
        self.assertTrue(result.branch_created)
        self.assertTrue(result.workflow_commit_created)
        self.assertTrue(result.pull_request_created)
        self.assertTrue(result.pull_request.draft)
        self.assertEqual(result.validation.decision, "no_new_deterministic_failures")
        self.assertIn("Target-version dry run", client.last_pr_body)
        self.assertIn("no_new_deterministic_failures", client.last_pr_body)
        self.assertEqual(
            client.changed_paths["agentgov/update-0.3.1"],
            (WORKFLOW_PATH.as_posix(),),
        )

    def test_existing_exact_pull_request_is_idempotent(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            current = write_consumer(root)
            manifest = write_manifest(root)
            client = FakeGitHubClient(base_content=current)
            first = create_upgrade_draft_pull_request(
                root,
                manifest_path=manifest,
                repository="owner/repository",
                base_branch="main",
                event_source="schedule",
                client=client,
            )
            calls_before = len(client.calls)

            second = create_upgrade_draft_pull_request(
                root,
                manifest_path=manifest,
                repository="owner/repository",
                base_branch="main",
                event_source="schedule",
                client=client,
            )

        self.assertIs(first.state, UpgradeWriteState.CREATED)
        self.assertIs(second.state, UpgradeWriteState.EXISTING)
        self.assertFalse(second.workflow_commit_created)
        self.assertFalse(second.pull_request_created)
        self.assertNotIn("update-file", "\n".join(client.calls[calls_before:]))

    def test_remote_base_drift_blocks_before_branch_creation(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_consumer(root)
            manifest = write_manifest(root)
            client = FakeGitHubClient(base_content="changed remotely\n")

            with self.assertRaisesRegex(
                UpgradeWriteConflictError,
                "remote base workflow changed",
            ):
                create_upgrade_draft_pull_request(
                    root,
                    manifest_path=manifest,
                    repository="owner/repository",
                    base_branch="main",
                    event_source="schedule",
                    client=client,
                )

        self.assertFalse(any(call.startswith("create-branch") for call in client.calls))
        self.assertFalse(any(call.startswith("create-pr") for call in client.calls))

    def test_push_event_cannot_authorize_a_write(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            current = write_consumer(root)
            manifest = write_manifest(root)
            client = FakeGitHubClient(base_content=current)

            with self.assertRaisesRegex(UpgradeWriteConflictError, "schedule"):
                create_upgrade_draft_pull_request(
                    root,
                    manifest_path=manifest,
                    repository="owner/repository",
                    base_branch="main",
                    event_source="push",
                    client=client,
                )

        self.assertEqual(client.calls, [])

    def test_candidate_requires_reports_from_exact_current_and_target_versions(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            current_content = write_consumer(root)
            manifest = write_manifest(root)
            current = write_validation_report(root, name="current", version="0.3.0")
            wrong_target = write_validation_report(root, name="target", version="0.3.2")
            client = FakeGitHubClient(base_content=current_content)

            with self.assertRaisesRegex(
                UpgradeWriteConflictError,
                "proposed target version",
            ):
                create_upgrade_write(
                    root,
                    manifest_path=manifest,
                    repository="owner/repository",
                    base_branch="main",
                    event_source="schedule",
                    client=client,
                    current_report_path=current,
                    target_report_path=wrong_target,
                )

        self.assertFalse(any(call.startswith("create-branch") for call in client.calls))

    def test_recovers_exact_branch_left_before_pr_creation(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            current = write_consumer(root)
            manifest = write_manifest(root)
            client = FakeGitHubClient(base_content=current)
            first = create_upgrade_draft_pull_request(
                root,
                manifest_path=manifest,
                repository="owner/repository",
                base_branch="main",
                event_source="schedule",
                client=client,
            )
            client.pull_request = None

            recovered = create_upgrade_draft_pull_request(
                root,
                manifest_path=manifest,
                repository="owner/repository",
                base_branch="main",
                event_source="workflow_dispatch",
                client=client,
            )

        self.assertIs(first.state, UpgradeWriteState.CREATED)
        self.assertIs(recovered.state, UpgradeWriteState.RECOVERED)
        self.assertFalse(recovered.workflow_commit_created)
        self.assertTrue(recovered.pull_request_created)

    def test_existing_branch_with_unrelated_change_is_blocked(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            current = write_consumer(root)
            manifest = write_manifest(root)
            client = FakeGitHubClient(base_content=current)
            create_upgrade_draft_pull_request(
                root,
                manifest_path=manifest,
                repository="owner/repository",
                base_branch="main",
                event_source="schedule",
                client=client,
            )
            client.pull_request = None
            client.changed_paths["agentgov/update-0.3.1"] = (
                WORKFLOW_PATH.as_posix(),
                "README.md",
            )

            with self.assertRaisesRegex(UpgradeWriteConflictError, "outside"):
                create_upgrade_draft_pull_request(
                    root,
                    manifest_path=manifest,
                    repository="owner/repository",
                    base_branch="main",
                    event_source="schedule",
                    client=client,
                )

    def test_result_contract_never_grants_merge_or_deploy_authority(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            current = write_consumer(root)
            manifest = write_manifest(root)
            result = create_upgrade_draft_pull_request(
                root,
                manifest_path=manifest,
                repository="owner/repository",
                base_branch="main",
                event_source="schedule",
                client=FakeGitHubClient(base_content=current),
            )
            payload = json.loads(render_upgrade_write_result_json(result))

        self.assertEqual(payload["mode"], "github_draft_pull_request")
        self.assertEqual(payload["authority_boundary"]["changed_path"], WORKFLOW_PATH.as_posix())
        self.assertFalse(payload["authority_boundary"]["merge_authorized"])
        self.assertFalse(payload["authority_boundary"]["deploy_authorized"])

    def test_cli_requires_token_without_printing_a_secret(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with patch.dict(os.environ, {}, clear=True), contextlib.redirect_stdout(
            stdout
        ), contextlib.redirect_stderr(stderr):
            exit_code = main(
                [
                    "create",
                    "upgrade-pr",
                    ".",
                    "--manifest",
                    "release.json",
                    "--repository",
                    "owner/repository",
                    "--base",
                    "main",
                    "--event",
                    "schedule",
                ]
            )

        self.assertEqual(exit_code, EXIT_ERROR)
        self.assertEqual(stdout.getvalue(), "")
        self.assertIn("GH_TOKEN is not set", stderr.getvalue())

    def test_result_schema_is_strict_and_denies_downstream_authority(self) -> None:
        schema = json.loads(
            (Path(__file__).resolve().parents[1] / "schemas/upgrade-pr-write.schema.json")
            .read_text(encoding="utf-8")
        )

        self.assertFalse(schema["additionalProperties"])
        boundary = schema["properties"]["authority_boundary"]
        self.assertFalse(boundary["additionalProperties"])
        for key in (
            "merge_authorized",
            "release_authorized",
            "deploy_authorized",
            "production_execution_authorized",
        ):
            self.assertIs(boundary["properties"][key]["const"], False)


if __name__ == "__main__":
    unittest.main()
