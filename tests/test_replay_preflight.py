from __future__ import annotations

import contextlib
import io
import json
import subprocess
import unittest
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from agentgov.cli import EXIT_ERROR, EXIT_FAIL, EXIT_PASS, main
from agentgov.replay_preflight import (
    AUTHORITY_BOUNDARY,
    REPLAY_ADAPTER_METADATA_CONTRACT,
    REPLAY_PREFLIGHT_PLAN_CONTRACT,
    REPLAY_PREFLIGHT_REPORT_CONTRACT,
    REPLAY_PREFLIGHT_SCHEMA_VERSION,
    ReplayPreflightPlanError,
    ReplayPreflightStatus,
    evaluate_replay_preflight,
    load_replay_preflight_plan,
    validate_replay_preflight_plan,
)


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas/replay-preflight-v1.schema.json"


class ReplayPreflightTests(unittest.TestCase):
    def git(self, repository: Path, *arguments: str) -> str:
        result = subprocess.run(
            ("git", "-C", str(repository), *arguments),
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return result.stdout.strip()

    def repository(self, *, readme: str = "# Demo\n\nOriginal text.\n") -> Path:
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        self.git(root, "init")
        self.git(root, "config", "user.email", "fixture@example.invalid")
        self.git(root, "config", "user.name", "Replay Fixture")
        (root / "README.md").write_text(readme, encoding="utf-8")
        metadata = root / ".agentgov" / "adapter.json"
        metadata.parent.mkdir()
        metadata.write_text(
            json.dumps(
                {
                    "contract": REPLAY_ADAPTER_METADATA_CONTRACT,
                    "schema_version": REPLAY_PREFLIGHT_SCHEMA_VERSION,
                    "adapter_id": "openai.codex-mcp",
                    "adapter_version": "1.5.0",
                    "protocol_version": "2026-07-28",
                }
            ),
            encoding="utf-8",
        )
        self.git(root, "add", "README.md", ".agentgov/adapter.json")
        self.git(root, "commit", "-m", "fixture")
        return root

    def plan(self, repository: Path) -> dict:
        return {
            "contract": REPLAY_PREFLIGHT_PLAN_CONTRACT,
            "schema_version": REPLAY_PREFLIGHT_SCHEMA_VERSION,
            "correlation": {
                "correlation_id": "rpf-0123456789abcdef",
                "registry_directory": ".agentgov/replay-correlations",
            },
            "repository": {"expected_head_sha": self.git(repository, "rev-parse", "HEAD")},
            "targets": [
                {
                    "path": "README.md",
                    "precondition": {
                        "kind": "text_absent",
                        "value": "### Two-terminal local demo",
                    },
                }
            ],
            "related_tasks": {
                "directory": "governance/tasks",
                "absent_task_ids": ["rename-readme-demo-heading"],
            },
            "adapter": {
                "metadata_path": ".agentgov/adapter.json",
                "expected_adapter_id": "openai.codex-mcp",
                "expected_adapter_version": "1.5.0",
                "expected_protocol_version": "2026-07-28",
            },
            "authority_boundary": dict(AUTHORITY_BOUNDARY),
        }

    def reason_codes(self, report) -> set[str]:
        return set(report.reason_codes)

    def test_schema_and_validator_share_contract_identity_and_boundaries(self) -> None:
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))

        self.assertEqual(
            schema["properties"]["contract"]["const"],
            REPLAY_PREFLIGHT_PLAN_CONTRACT,
        )
        self.assertEqual(
            schema["properties"]["schema_version"]["const"],
            REPLAY_PREFLIGHT_SCHEMA_VERSION,
        )
        self.assertEqual(
            set(schema["$defs"]["authorityBoundary"]["required"]),
            set(AUTHORITY_BOUNDARY),
        )
        self.assertTrue(
            all(
                item["const"] is False
                for item in schema["$defs"]["authorityBoundary"]["properties"].values()
            )
        )

    def test_clean_fixture_is_ready_but_grants_no_replay_authority(self) -> None:
        repository = self.repository()
        report = evaluate_replay_preflight(self.plan(repository), repository=repository)

        self.assertEqual(report.status, ReplayPreflightStatus.READY)
        self.assertTrue(report.preconditions_ready)
        self.assertEqual(report.reason_codes, ())
        self.assertEqual(report.contract, REPLAY_PREFLIGHT_REPORT_CONTRACT)
        self.assertTrue(all(value is False for value in report.authority_boundary.values()))

    def test_dirty_target_blocks_without_changing_the_repository(self) -> None:
        repository = self.repository()
        plan = self.plan(repository)
        target = repository / "README.md"
        target.write_text("# Demo\n\nLocal draft.\n", encoding="utf-8")
        before = target.read_bytes()

        report = evaluate_replay_preflight(plan, repository=repository)

        self.assertEqual(report.status, ReplayPreflightStatus.BLOCKED)
        self.assertIn("target_dirty", self.reason_codes(report))
        self.assertEqual(target.read_bytes(), before)

    def test_already_satisfied_target_prestate_blocks(self) -> None:
        repository = self.repository(
            readme="# Demo\n\n### Two-terminal local demo\n"
        )
        report = evaluate_replay_preflight(self.plan(repository), repository=repository)

        self.assertEqual(report.status, ReplayPreflightStatus.BLOCKED)
        self.assertIn("target_prestate_failed", self.reason_codes(report))

    def test_renamed_target_is_detected_as_dirty(self) -> None:
        repository = self.repository()
        plan = self.plan(repository)
        self.git(repository, "mv", "README.md", "README-old.md")

        report = evaluate_replay_preflight(plan, repository=repository)

        self.assertEqual(report.status, ReplayPreflightStatus.BLOCKED)
        self.assertIn("target_dirty", self.reason_codes(report))
        self.assertIn("target_missing", self.reason_codes(report))

    def test_related_task_collision_blocks(self) -> None:
        repository = self.repository()
        plan = self.plan(repository)
        task = repository / "governance" / "tasks" / "rename-readme-demo-heading.json"
        task.parent.mkdir(parents=True)
        task.write_text("{}\n", encoding="utf-8")

        report = evaluate_replay_preflight(plan, repository=repository)

        self.assertEqual(report.status, ReplayPreflightStatus.BLOCKED)
        self.assertIn("task_collision", self.reason_codes(report))

    def test_adapter_mismatch_blocks(self) -> None:
        repository = self.repository()
        plan = self.plan(repository)
        metadata_path = repository / ".agentgov" / "adapter.json"
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        metadata["adapter_version"] = "1.4.0"
        metadata_path.write_text(json.dumps(metadata), encoding="utf-8")

        report = evaluate_replay_preflight(plan, repository=repository)

        self.assertEqual(report.status, ReplayPreflightStatus.BLOCKED)
        self.assertIn("adapter_mismatch", self.reason_codes(report))

    def test_stale_revision_blocks(self) -> None:
        repository = self.repository()
        plan = self.plan(repository)
        plan["repository"]["expected_head_sha"] = "0" * 40

        report = evaluate_replay_preflight(plan, repository=repository)

        self.assertEqual(report.status, ReplayPreflightStatus.BLOCKED)
        self.assertIn("stale_repository_revision", self.reason_codes(report))

    def test_duplicate_correlation_marker_blocks(self) -> None:
        repository = self.repository()
        plan = self.plan(repository)
        registry = repository / ".agentgov" / "replay-correlations"
        registry.mkdir()
        (registry / "rpf-0123456789abcdef.json").write_text("{}\n", encoding="utf-8")

        report = evaluate_replay_preflight(plan, repository=repository)

        self.assertEqual(report.status, ReplayPreflightStatus.BLOCKED)
        self.assertIn("duplicate_correlation", self.reason_codes(report))

    def test_missing_adapter_facts_are_unknown(self) -> None:
        repository = self.repository()
        plan = self.plan(repository)
        (repository / ".agentgov" / "adapter.json").unlink()

        report = evaluate_replay_preflight(plan, repository=repository)

        self.assertEqual(report.status, ReplayPreflightStatus.UNKNOWN)
        self.assertIn("adapter_metadata_unavailable", self.reason_codes(report))

    def test_symbolic_link_boundary_is_unknown_and_not_followed(self) -> None:
        repository = self.repository()
        plan = self.plan(repository)

        with patch(
            "agentgov.replay_preflight._has_symlink_component", return_value=True
        ):
            report = evaluate_replay_preflight(plan, repository=repository)

        self.assertEqual(report.status, ReplayPreflightStatus.UNKNOWN)
        self.assertIn("target_unreadable", self.reason_codes(report))

    def test_unavailable_git_facts_are_unknown(self) -> None:
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        repository = Path(temporary.name)
        (repository / "README.md").write_text("# Demo\n", encoding="utf-8")
        metadata = repository / ".agentgov" / "adapter.json"
        metadata.parent.mkdir()
        metadata.write_text(
            json.dumps(
                {
                    "contract": REPLAY_ADAPTER_METADATA_CONTRACT,
                    "schema_version": "1.0",
                    "adapter_id": "openai.codex-mcp",
                    "adapter_version": "1.5.0",
                    "protocol_version": "2026-07-28",
                }
            ),
            encoding="utf-8",
        )
        plan = self.plan(self.repository())

        report = evaluate_replay_preflight(plan, repository=repository)

        self.assertEqual(report.status, ReplayPreflightStatus.UNKNOWN)
        self.assertIn("git_unavailable", self.reason_codes(report))

    def test_validator_rejects_ambiguous_or_authorizing_input(self) -> None:
        repository = self.repository()
        plan = self.plan(repository)
        invalid_cases = []
        duplicate_target = deepcopy(plan)
        duplicate_target["targets"].append(deepcopy(duplicate_target["targets"][0]))
        invalid_cases.append(duplicate_target)
        vague_prestate = deepcopy(plan)
        vague_prestate["targets"][0]["precondition"] = {
            "kind": "semantic_absence",
            "value": "similar heading",
        }
        invalid_cases.append(vague_prestate)
        authorizing = deepcopy(plan)
        authorizing["authority_boundary"]["authorizes_replay"] = True
        invalid_cases.append(authorizing)

        for document in invalid_cases:
            with self.subTest(document=document):
                self.assertTrue(validate_replay_preflight_plan(document))

    def test_loader_rejects_duplicate_json_keys(self) -> None:
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        path = Path(temporary.name) / "plan.json"
        path.write_text('{"contract":"a","contract":"b"}', encoding="utf-8")

        with self.assertRaisesRegex(ReplayPreflightPlanError, "duplicate JSON key"):
            load_replay_preflight_plan(path)

    def test_cli_returns_pass_fail_and_error_with_machine_readable_output(self) -> None:
        repository = self.repository()
        plan = self.plan(repository)
        plan_path = repository / "preflight.json"
        plan_path.write_text(json.dumps(plan), encoding="utf-8")
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            ready_code = main(
                [
                    "check",
                    "replay-preflight",
                    str(plan_path),
                    "--repository",
                    str(repository),
                    "--format",
                    "json",
                ]
            )
        payload = json.loads(stdout.getvalue())

        self.assertEqual(ready_code, EXIT_PASS)
        self.assertEqual(payload["status"], "READY")
        self.assertFalse(payload["authority_boundary"]["authorizes_replay"])

        (repository / "README.md").write_text("changed\n", encoding="utf-8")
        with contextlib.redirect_stdout(io.StringIO()):
            blocked_code = main(
                [
                    "check",
                    "replay-preflight",
                    str(plan_path),
                    "--repository",
                    str(repository),
                ]
            )
        self.assertEqual(blocked_code, EXIT_FAIL)

        plan_path.write_text("{}", encoding="utf-8")
        with contextlib.redirect_stderr(io.StringIO()):
            error_code = main(
                [
                    "check",
                    "replay-preflight",
                    str(plan_path),
                    "--repository",
                    str(repository),
                ]
            )
        self.assertEqual(error_code, EXIT_ERROR)


if __name__ == "__main__":
    unittest.main()
