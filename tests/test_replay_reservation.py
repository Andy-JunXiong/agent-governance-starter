from __future__ import annotations

import contextlib
import io
import json
import os
import subprocess
import sys
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
    REPLAY_PREFLIGHT_SCHEMA_VERSION,
)
from agentgov.replay_reservation import (
    REPLAY_RESERVATION_MARKER_CONTRACT,
    REPLAY_RESERVATION_PREVIEW_CONTRACT,
    REPLAY_RESERVATION_RESULT_CONTRACT,
    REPLAY_RESERVATION_SCHEMA_VERSION,
    ReplayReservationConflictError,
    ReplayReservationPreviewStatus,
    ReplayReservationStaleError,
    apply_replay_reservation,
    prepare_replay_reservation,
    render_replay_reservation_preview_json,
    request_replay_reservation_confirmation,
    validate_replay_reservation_marker,
)


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas/replay-correlation-reservation-v1.schema.json"


class InteractiveInput(io.StringIO):
    def isatty(self) -> bool:
        return True


def run_cli(*args: str) -> tuple[int, str, str]:
    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        exit_code = main(list(args))
    return exit_code, stdout.getvalue(), stderr.getvalue()


class ReplayReservationTests(unittest.TestCase):
    def git(self, repository: Path, *arguments: str) -> str:
        result = subprocess.run(
            ("git", "-C", str(repository), *arguments),
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return result.stdout.strip()

    def repository(self) -> Path:
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        self.git(root, "init")
        self.git(root, "config", "user.email", "fixture@example.invalid")
        self.git(root, "config", "user.name", "Reservation Fixture")
        (root / "README.md").write_text("# Demo\n\nOriginal text.\n", encoding="utf-8")
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
        (root / ".agentgov" / "replay-correlations").mkdir()
        return root

    def plan(self, repository: Path) -> dict:
        return {
            "contract": REPLAY_PREFLIGHT_PLAN_CONTRACT,
            "schema_version": REPLAY_PREFLIGHT_SCHEMA_VERSION,
            "correlation": {
                "correlation_id": "rpf-0123456789abcdef",
                "registry_directory": ".agentgov/replay-correlations",
            },
            "repository": {
                "expected_head_sha": self.git(repository, "rev-parse", "HEAD")
            },
            "targets": [
                {
                    "path": "README.md",
                    "precondition": {
                        "kind": "text_absent",
                        "value": "### Governed replay candidate",
                    },
                }
            ],
            "related_tasks": {
                "directory": "governance/tasks",
                "absent_task_ids": ["synthetic-readme-update"],
            },
            "adapter": {
                "metadata_path": ".agentgov/adapter.json",
                "expected_adapter_id": "openai.codex-mcp",
                "expected_adapter_version": "1.5.0",
                "expected_protocol_version": "2026-07-28",
            },
            "authority_boundary": dict(AUTHORITY_BOUNDARY),
        }

    def write_plan(self, repository: Path, plan: dict) -> Path:
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        path = Path(temporary.name) / "preflight-plan.json"
        path.write_text(json.dumps(plan), encoding="utf-8")
        return path

    def marker_path(self, repository: Path) -> Path:
        return repository / ".agentgov/replay-correlations/rpf-0123456789abcdef.json"

    def test_schema_and_runtime_contracts_are_strict_and_non_authorizing(self) -> None:
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        refs = {item["$ref"] for item in schema["oneOf"]}
        self.assertEqual(refs, {"#/$defs/marker", "#/$defs/preview", "#/$defs/result"})
        self.assertEqual(
            schema["$defs"]["marker"]["properties"]["contract"]["const"],
            REPLAY_RESERVATION_MARKER_CONTRACT,
        )
        self.assertEqual(
            schema["$defs"]["preview"]["properties"]["contract"]["const"],
            REPLAY_RESERVATION_PREVIEW_CONTRACT,
        )
        self.assertEqual(
            schema["$defs"]["result"]["properties"]["contract"]["const"],
            REPLAY_RESERVATION_RESULT_CONTRACT,
        )
        authority = schema["$defs"]["authorityBoundary"]["properties"]
        self.assertTrue(all(item["const"] is False for item in authority.values()))

    def test_preview_is_read_only_exact_and_ready(self) -> None:
        repository = self.repository()
        plan = self.plan(repository)
        before = self.git(repository, "status", "--porcelain")

        preview = prepare_replay_reservation(plan, repository=repository)

        self.assertEqual(preview.status, ReplayReservationPreviewStatus.READY)
        self.assertEqual(preview.contract, REPLAY_RESERVATION_PREVIEW_CONTRACT)
        self.assertEqual(preview.schema_version, REPLAY_RESERVATION_SCHEMA_VERSION)
        self.assertEqual(preview.marker_path, ".agentgov/replay-correlations/rpf-0123456789abcdef.json")
        self.assertIsNotNone(preview.marker)
        self.assertEqual(validate_replay_reservation_marker(preview.marker), [])
        self.assertEqual(self.git(repository, "status", "--porcelain"), before)
        self.assertFalse(self.marker_path(repository).exists())
        self.assertTrue(all(value is False for value in preview.authority_boundary.values()))

    def test_missing_registry_blocks_without_creating_scaffolding(self) -> None:
        repository = self.repository()
        registry = repository / ".agentgov/replay-correlations"
        registry.rmdir()

        preview = prepare_replay_reservation(self.plan(repository), repository=repository)

        self.assertEqual(preview.status, ReplayReservationPreviewStatus.BLOCKED)
        self.assertIn("reservation_registry_missing", preview.reason_codes)
        self.assertIsNone(preview.marker)
        self.assertFalse(registry.exists())

    def test_non_ready_preflight_never_prepares_a_marker(self) -> None:
        repository = self.repository()
        plan = self.plan(repository)
        metadata = repository / ".agentgov/adapter.json"
        value = json.loads(metadata.read_text(encoding="utf-8"))
        value["adapter_version"] = "1.4.0"
        metadata.write_text(json.dumps(value), encoding="utf-8")

        preview = prepare_replay_reservation(plan, repository=repository)

        self.assertEqual(preview.status, ReplayReservationPreviewStatus.BLOCKED)
        self.assertIn("adapter_mismatch", preview.reason_codes)
        self.assertIsNone(preview.marker)
        self.assertFalse(self.marker_path(repository).exists())

    def test_existing_marker_blocks_and_is_not_overwritten(self) -> None:
        repository = self.repository()
        marker = self.marker_path(repository)
        marker.write_text("owned elsewhere\n", encoding="utf-8")

        preview = prepare_replay_reservation(self.plan(repository), repository=repository)

        self.assertEqual(preview.status, ReplayReservationPreviewStatus.BLOCKED)
        self.assertIn("duplicate_correlation", preview.reason_codes)
        self.assertEqual(marker.read_text(encoding="utf-8"), "owned elsewhere\n")

    def test_confirmation_requires_exact_word_and_interactive_terminal(self) -> None:
        repository = self.repository()
        preview = prepare_replay_reservation(self.plan(repository), repository=repository)

        self.assertFalse(
            request_replay_reservation_confirmation(
                preview,
                decision_reader=lambda _: "RESERVE",
                is_interactive_terminal=False,
            )
        )
        self.assertFalse(
            request_replay_reservation_confirmation(
                preview,
                decision_reader=lambda _: "reserve",
                is_interactive_terminal=True,
            )
        )
        self.assertTrue(
            request_replay_reservation_confirmation(
                preview,
                decision_reader=lambda _: "RESERVE",
                is_interactive_terminal=True,
            )
        )

    def test_apply_revalidates_and_creates_exactly_one_marker(self) -> None:
        repository = self.repository()
        plan = self.plan(repository)
        preview = prepare_replay_reservation(plan, repository=repository)

        result = apply_replay_reservation(preview, plan, repository=repository)
        marker = self.marker_path(repository)
        content = json.loads(marker.read_text(encoding="utf-8"))

        self.assertEqual(result.status, "RESERVED")
        self.assertEqual(result.contract, REPLAY_RESERVATION_RESULT_CONTRACT)
        self.assertEqual(content, preview.marker)
        self.assertEqual(validate_replay_reservation_marker(content), [])
        self.assertEqual(result.effect, {"repository_modified": True, "reservation_created": True})
        self.assertTrue(all(value is False for value in result.authority_boundary.values()))
        with self.assertRaises(ReplayReservationConflictError):
            apply_replay_reservation(preview, plan, repository=repository)

    def test_stale_target_after_preview_blocks_apply_with_zero_marker_write(self) -> None:
        repository = self.repository()
        plan = self.plan(repository)
        preview = prepare_replay_reservation(plan, repository=repository)
        (repository / "README.md").write_text("changed after preview\n", encoding="utf-8")

        with self.assertRaises(ReplayReservationStaleError):
            apply_replay_reservation(preview, plan, repository=repository)

        self.assertFalse(self.marker_path(repository).exists())

    def test_exclusive_create_race_preserves_competing_marker(self) -> None:
        repository = self.repository()
        plan = self.plan(repository)
        preview = prepare_replay_reservation(plan, repository=repository)
        marker = self.marker_path(repository)
        original_open = os.open

        def race_open(path, flags, mode=0o777):
            marker.write_text("race winner\n", encoding="utf-8")
            return original_open(path, flags, mode)

        with patch("agentgov.replay_reservation.os.open", side_effect=race_open):
            with self.assertRaises(ReplayReservationConflictError):
                apply_replay_reservation(preview, plan, repository=repository)

        self.assertEqual(marker.read_text(encoding="utf-8"), "race winner\n")

    def test_json_preview_is_machine_readable_and_grants_no_authority(self) -> None:
        repository = self.repository()
        preview = prepare_replay_reservation(self.plan(repository), repository=repository)

        payload = json.loads(render_replay_reservation_preview_json(preview))

        self.assertEqual(payload["status"], "READY_TO_RESERVE")
        self.assertEqual(payload["marker"]["status"], "reserved")
        self.assertFalse(payload["authority_boundary"]["authorizes_replay"])

    def test_cli_preview_cancel_apply_and_success_have_distinct_write_semantics(self) -> None:
        repository = self.repository()
        plan_path = self.write_plan(repository, self.plan(repository))

        preview_code, preview_stdout, preview_stderr = run_cli(
            "reserve",
            "replay-correlation",
            str(plan_path),
            "--repository",
            str(repository),
            "--format",
            "json",
        )
        with patch.object(sys, "stdin", io.StringIO("RESERVE\n")):
            cancel_code, cancel_stdout, cancel_stderr = run_cli(
                "reserve",
                "replay-correlation",
                str(plan_path),
                "--repository",
                str(repository),
                "--apply",
            )
        self.assertFalse(self.marker_path(repository).exists())
        with patch.object(sys, "stdin", InteractiveInput("RESERVE\n")):
            apply_code, apply_stdout, apply_stderr = run_cli(
                "reserve",
                "replay-correlation",
                str(plan_path),
                "--repository",
                str(repository),
                "--apply",
            )

        self.assertEqual(preview_code, EXIT_PASS)
        self.assertEqual(json.loads(preview_stdout)["status"], "READY_TO_RESERVE")
        self.assertEqual(preview_stderr, "")
        self.assertEqual(cancel_code, EXIT_PASS)
        self.assertIn("CANCELLED", cancel_stdout)
        self.assertEqual(cancel_stderr, "")
        self.assertEqual(apply_code, EXIT_PASS)
        self.assertIn("RESERVED correlation=", apply_stdout)
        self.assertEqual(apply_stderr, "")
        self.assertTrue(self.marker_path(repository).exists())

    def test_cli_rejects_json_apply_before_prompt_or_write(self) -> None:
        repository = self.repository()
        plan_path = self.write_plan(repository, self.plan(repository))

        code, stdout, stderr = run_cli(
            "reserve",
            "replay-correlation",
            str(plan_path),
            "--repository",
            str(repository),
            "--apply",
            "--format",
            "json",
        )

        self.assertEqual(code, EXIT_ERROR)
        self.assertEqual(stdout, "")
        self.assertIn("requires terminal format", stderr)
        self.assertFalse(self.marker_path(repository).exists())

    def test_cli_malformed_plan_is_operational_error_without_marker_write(self) -> None:
        repository = self.repository()
        plan_path = self.write_plan(repository, {})

        code, stdout, stderr = run_cli(
            "reserve",
            "replay-correlation",
            str(plan_path),
            "--repository",
            str(repository),
        )

        self.assertEqual(code, EXIT_ERROR)
        self.assertEqual(stdout, "")
        self.assertIn("ERROR reserve replay-correlation", stderr)
        self.assertFalse(self.marker_path(repository).exists())

    def test_cli_blocked_preview_returns_policy_failure(self) -> None:
        repository = self.repository()
        plan = self.plan(repository)
        plan["repository"]["expected_head_sha"] = "0" * 40
        plan_path = self.write_plan(repository, plan)

        code, stdout, stderr = run_cli(
            "reserve",
            "replay-correlation",
            str(plan_path),
            "--repository",
            str(repository),
        )

        self.assertEqual(code, EXIT_FAIL)
        self.assertIn("status=BLOCKED", stdout)
        self.assertEqual(stderr, "")
        self.assertFalse(self.marker_path(repository).exists())

    def test_modified_plan_cannot_reuse_a_reviewed_preview(self) -> None:
        repository = self.repository()
        plan = self.plan(repository)
        preview = prepare_replay_reservation(plan, repository=repository)
        changed = deepcopy(plan)
        changed["targets"][0]["precondition"]["value"] = "different text"

        with self.assertRaises(ReplayReservationStaleError):
            apply_replay_reservation(preview, changed, repository=repository)

        self.assertFalse(self.marker_path(repository).exists())


if __name__ == "__main__":
    unittest.main()
