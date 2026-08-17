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
from agentgov.replay_claim import (
    REPLAY_CLAIM_MARKER_CONTRACT,
    REPLAY_CLAIM_PLAN_CONTRACT,
    REPLAY_CLAIM_PREVIEW_CONTRACT,
    REPLAY_CLAIM_RESULT_CONTRACT,
    REPLAY_CLAIM_SCHEMA_VERSION,
    ReplayClaimConflictError,
    ReplayClaimPreviewStatus,
    ReplayClaimStaleError,
    apply_replay_claim,
    prepare_replay_claim,
    replay_claim_digest,
    request_replay_claim_confirmation,
    validate_replay_claim,
    validate_replay_claim_marker,
    validate_replay_claim_plan,
)
from agentgov.replay_correlation_bridge import replay_reservation_marker_digest
from agentgov.replay_preflight import (
    AUTHORITY_BOUNDARY,
    REPLAY_ADAPTER_METADATA_CONTRACT,
    REPLAY_PREFLIGHT_SCHEMA_VERSION,
)


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas/replay-correlation-claim-v1.schema.json"
FIXTURES = ROOT / "governance/fixtures/replay-correlation-claim-v1"
BRIDGE_FIXTURE = ROOT / "governance/fixtures/replay-correlation-bridge-v1/reserved.json"


class InteractiveInput(io.StringIO):
    def isatty(self) -> bool:
        return True


def run_cli(*args: str) -> tuple[int, str, str]:
    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        exit_code = main(list(args))
    return exit_code, stdout.getvalue(), stderr.getvalue()


class ReplayClaimTests(unittest.TestCase):
    def git(self, repository: Path, *arguments: str) -> str:
        result = subprocess.run(
            ("git", "-C", str(repository), *arguments),
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return result.stdout.strip()

    def repository(self) -> tuple[Path, dict, dict]:
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        self.git(root, "init")
        self.git(root, "config", "user.email", "fixture@example.invalid")
        self.git(root, "config", "user.name", "Claim Fixture")
        (root / "README.md").write_text("# Demo\n", encoding="utf-8")
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
        head = self.git(root, "rev-parse", "HEAD")
        marker = {
            "contract": "agentgov.replay-correlation-reservation",
            "schema_version": "1.0",
            "reservation_id": "rrv-0123456789abcdef",
            "correlation_id": "rpf-0123456789abcdef",
            "marker_path": ".agentgov/replay-correlations/rpf-0123456789abcdef.json",
            "preflight": {
                "plan_digest": "sha256:" + "1" * 64,
                "expected_head_sha": head,
                "observed_head_sha": head,
            },
            "adapter": {
                "adapter_id": "openai.codex-mcp",
                "adapter_version": "1.5.0",
                "protocol_version": "2026-07-28",
            },
            "status": "reserved",
            "authority_boundary": dict(AUTHORITY_BOUNDARY),
        }
        marker_path = root / marker["marker_path"]
        marker_path.parent.mkdir()
        marker_path.write_text(json.dumps(marker, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        (root / ".agentgov" / "replay-claims").mkdir()
        plan = {
            "contract": REPLAY_CLAIM_PLAN_CONTRACT,
            "schema_version": REPLAY_CLAIM_SCHEMA_VERSION,
            "reservation": {
                "marker_path": marker["marker_path"],
                "marker_digest": replay_reservation_marker_digest(marker),
            },
            "claim": {
                "registry_directory": ".agentgov/replay-claims",
                "claimant_id": "openai.codex-mcp",
            },
            "adapter": {"metadata_path": ".agentgov/adapter.json"},
            "authority_boundary": dict(AUTHORITY_BOUNDARY),
        }
        return root, marker, plan

    def write_plan(self, plan: dict) -> Path:
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        path = Path(temporary.name) / "claim-plan.json"
        path.write_text(json.dumps(plan), encoding="utf-8")
        return path

    def claim_path(self, repository: Path) -> Path:
        return repository / ".agentgov/replay-claims/rpf-0123456789abcdef.json"

    def test_schema_and_fixtures_are_strict_non_authorizing_json(self) -> None:
        def unique_object(pairs: list[tuple[str, object]]) -> dict:
            result = {}
            for key, value in pairs:
                if key in result:
                    raise ValueError(f"duplicate JSON key: {key}")
                result[key] = value
            return result

        for path in (SCHEMA, *sorted(FIXTURES.glob("*.json"))):
            with self.subTest(path=path.name):
                json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique_object)
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        self.assertEqual(
            {item["$ref"] for item in schema["oneOf"]},
            {"#/$defs/plan", "#/$defs/marker", "#/$defs/preview", "#/$defs/result"},
        )
        authority = schema["$defs"]["authorityBoundary"]["properties"]
        self.assertTrue(all(item["const"] is False for item in authority.values()))
        plan = json.loads((FIXTURES / "valid-plan.json").read_text(encoding="utf-8"))
        marker = json.loads((FIXTURES / "claimed.json").read_text(encoding="utf-8"))
        self.assertEqual(validate_replay_claim_plan(plan), [])
        self.assertEqual(validate_replay_claim_marker(marker), [])

    def test_preview_is_read_only_exact_and_ready(self) -> None:
        repository, marker, plan = self.repository()
        reservation_before = (repository / marker["marker_path"]).read_bytes()
        status_before = self.git(repository, "status", "--porcelain")

        preview = prepare_replay_claim(plan, repository=repository)

        self.assertEqual(preview.status, ReplayClaimPreviewStatus.READY)
        self.assertEqual(preview.contract, REPLAY_CLAIM_PREVIEW_CONTRACT)
        self.assertEqual(preview.claim_path, ".agentgov/replay-claims/rpf-0123456789abcdef.json")
        self.assertEqual(validate_replay_claim(preview.claim, reservation_marker=marker), [])
        self.assertFalse(self.claim_path(repository).exists())
        self.assertEqual((repository / marker["marker_path"]).read_bytes(), reservation_before)
        self.assertEqual(self.git(repository, "status", "--porcelain"), status_before)

    def test_missing_registry_blocks_and_missing_marker_is_unknown(self) -> None:
        repository, marker, plan = self.repository()
        (repository / ".agentgov/replay-claims").rmdir()
        blocked = prepare_replay_claim(plan, repository=repository)
        self.assertEqual(blocked.status, ReplayClaimPreviewStatus.BLOCKED)
        self.assertIn("claim_registry_missing", blocked.reason_codes)
        self.assertIsNone(blocked.claim)

        (repository / marker["marker_path"]).unlink()
        unknown = prepare_replay_claim(plan, repository=repository)
        self.assertEqual(unknown.status, ReplayClaimPreviewStatus.UNKNOWN)
        self.assertIn("reservation_marker_unavailable", unknown.reason_codes)
        self.assertIsNone(unknown.claim)

    def test_digest_head_adapter_and_existing_claim_fail_closed(self) -> None:
        repository, _marker, plan = self.repository()
        wrong_digest = deepcopy(plan)
        wrong_digest["reservation"]["marker_digest"] = "sha256:" + "f" * 64
        digest_preview = prepare_replay_claim(wrong_digest, repository=repository)
        self.assertEqual(digest_preview.status, ReplayClaimPreviewStatus.BLOCKED)
        self.assertIn("reservation_marker_mismatch", digest_preview.reason_codes)

        (repository / "README.md").write_text("changed\n", encoding="utf-8")
        self.git(repository, "add", "README.md")
        self.git(repository, "commit", "-m", "head changes")
        head_preview = prepare_replay_claim(plan, repository=repository)
        self.assertEqual(head_preview.status, ReplayClaimPreviewStatus.BLOCKED)
        self.assertIn("repository_head_mismatch", head_preview.reason_codes)

        repository, _marker, plan = self.repository()
        metadata_path = repository / ".agentgov/adapter.json"
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        metadata["adapter_version"] = "9.0.0"
        metadata_path.write_text(json.dumps(metadata), encoding="utf-8")
        adapter_preview = prepare_replay_claim(plan, repository=repository)
        self.assertEqual(adapter_preview.status, ReplayClaimPreviewStatus.BLOCKED)
        self.assertIn("adapter_mismatch", adapter_preview.reason_codes)

        repository, _marker, plan = self.repository()
        self.claim_path(repository).write_text("owned elsewhere\n", encoding="utf-8")
        collision = prepare_replay_claim(plan, repository=repository)
        self.assertEqual(collision.status, ReplayClaimPreviewStatus.BLOCKED)
        self.assertIn("duplicate_claim", collision.reason_codes)
        self.assertEqual(self.claim_path(repository).read_text(encoding="utf-8"), "owned elsewhere\n")

    def test_unsafe_registry_and_invalid_adapter_are_unknown(self) -> None:
        repository, _marker, plan = self.repository()
        metadata_path = repository / ".agentgov/adapter.json"
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        metadata["adapter_version"] = []
        metadata_path.write_text(json.dumps(metadata), encoding="utf-8")
        invalid_adapter = prepare_replay_claim(plan, repository=repository)
        self.assertEqual(invalid_adapter.status, ReplayClaimPreviewStatus.UNKNOWN)
        self.assertIn("adapter_metadata_invalid", invalid_adapter.reason_codes)

        repository, _marker, plan = self.repository()
        registry = repository / ".agentgov/replay-claims"
        registry.rmdir()
        target = repository / "outside"
        target.mkdir()
        try:
            registry.symlink_to(target, target_is_directory=True)
        except OSError:
            self.skipTest("directory symlinks are unavailable")
        preview = prepare_replay_claim(plan, repository=repository)
        self.assertEqual(preview.status, ReplayClaimPreviewStatus.UNKNOWN)
        self.assertIn("claim_registry_unsafe", preview.reason_codes)

    def test_confirmation_requires_exact_word_and_interactive_terminal(self) -> None:
        repository, _marker, plan = self.repository()
        preview = prepare_replay_claim(plan, repository=repository)
        self.assertFalse(request_replay_claim_confirmation(preview, decision_reader=lambda _: "CLAIM", is_interactive_terminal=False))
        self.assertFalse(request_replay_claim_confirmation(preview, decision_reader=lambda _: "claim", is_interactive_terminal=True))
        self.assertTrue(request_replay_claim_confirmation(preview, decision_reader=lambda _: "CLAIM", is_interactive_terminal=True))

    def test_apply_revalidates_creates_once_and_preserves_reservation(self) -> None:
        repository, marker, plan = self.repository()
        marker_path = repository / marker["marker_path"]
        reservation_before = marker_path.read_bytes()
        preview = prepare_replay_claim(plan, repository=repository)

        result = apply_replay_claim(preview, plan, repository=repository)
        claim = json.loads(self.claim_path(repository).read_text(encoding="utf-8"))

        self.assertEqual(result.contract, REPLAY_CLAIM_RESULT_CONTRACT)
        self.assertEqual(result.status, "CLAIMED")
        self.assertEqual(result.claim_digest, replay_claim_digest(claim))
        self.assertEqual(claim, preview.claim)
        self.assertEqual(validate_replay_claim(claim, reservation_marker=marker), [])
        self.assertEqual(marker_path.read_bytes(), reservation_before)
        self.assertTrue(all(value is False for value in claim["authority_boundary"].values()))
        with self.assertRaises(ReplayClaimConflictError):
            apply_replay_claim(preview, plan, repository=repository)

    def test_stale_preview_after_head_change_writes_nothing(self) -> None:
        repository, _marker, plan = self.repository()
        preview = prepare_replay_claim(plan, repository=repository)
        (repository / "README.md").write_text("changed\n", encoding="utf-8")
        self.git(repository, "add", "README.md")
        self.git(repository, "commit", "-m", "stale")
        with self.assertRaises(ReplayClaimStaleError):
            apply_replay_claim(preview, plan, repository=repository)
        self.assertFalse(self.claim_path(repository).exists())

    def test_exclusive_create_race_never_overwrites_winner(self) -> None:
        repository, _marker, plan = self.repository()
        preview = prepare_replay_claim(plan, repository=repository)
        real_open = os.open

        def racing_open(path: os.PathLike[str] | str, flags: int, mode: int = 0o777) -> int:
            self.claim_path(repository).write_text("winner\n", encoding="utf-8")
            return real_open(path, flags, mode)

        with patch("agentgov.replay_claim.os.open", side_effect=racing_open):
            with self.assertRaises(ReplayClaimConflictError):
                apply_replay_claim(preview, plan, repository=repository)
        self.assertEqual(self.claim_path(repository).read_text(encoding="utf-8"), "winner\n")

    def test_write_failure_keeps_ambiguous_claim_and_blocks_reuse(self) -> None:
        repository, _marker, plan = self.repository()
        preview = prepare_replay_claim(plan, repository=repository)
        with patch("agentgov.replay_claim.os.write", side_effect=OSError("disk uncertain")):
            with self.assertRaises(OSError):
                apply_replay_claim(preview, plan, repository=repository)
        self.assertTrue(self.claim_path(repository).exists())
        blocked = prepare_replay_claim(plan, repository=repository)
        self.assertEqual(blocked.status, ReplayClaimPreviewStatus.BLOCKED)
        self.assertIn("duplicate_claim", blocked.reason_codes)

    def test_valid_reserved_bridge_binds_and_other_states_fail(self) -> None:
        marker = {
            "contract": "agentgov.replay-correlation-reservation",
            "schema_version": "1.0",
            "reservation_id": "rrv-0123456789abcdef",
            "correlation_id": "rpf-0123456789abcdef",
            "marker_path": ".agentgov/replay-correlations/rpf-0123456789abcdef.json",
            "preflight": {
                "plan_digest": "sha256:" + "1" * 64,
                "expected_head_sha": "2" * 40,
                "observed_head_sha": "2" * 40,
            },
            "adapter": {
                "adapter_id": "openai.codex-mcp",
                "adapter_version": "1.5.0",
                "protocol_version": "2026-07-28",
            },
            "status": "reserved",
            "authority_boundary": dict(AUTHORITY_BOUNDARY),
        }
        claim = json.loads((FIXTURES / "claimed.json").read_text(encoding="utf-8"))
        bridge = json.loads(BRIDGE_FIXTURE.read_text(encoding="utf-8"))
        self.assertEqual(validate_replay_claim(claim, reservation_marker=marker, reserved_bridge=bridge), [])
        changed = deepcopy(bridge)
        changed["state"] = "invalidated"
        errors = validate_replay_claim(claim, reservation_marker=marker, reserved_bridge=changed)
        self.assertTrue(any("reserved_bridge" in item for item in errors))

    def test_strict_validators_reject_malformed_and_authority_drift(self) -> None:
        plan = json.loads((FIXTURES / "valid-plan.json").read_text(encoding="utf-8"))
        extra = deepcopy(plan)
        extra["replay"] = True
        self.assertIn("$.replay is not allowed", validate_replay_claim_plan(extra))
        unsafe = deepcopy(plan)
        unsafe["claim"]["registry_directory"] = "../claims"
        self.assertTrue(any("registry_directory" in item for item in validate_replay_claim_plan(unsafe)))
        marker = json.loads((FIXTURES / "claimed.json").read_text(encoding="utf-8"))
        marker["status"] = "consumed"
        marker["authority_boundary"]["authorizes_replay"] = True
        errors = validate_replay_claim_marker(marker)
        self.assertIn("$.status must equal 'claimed'", errors)
        self.assertTrue(any("authority_boundary" in item for item in errors))

    def test_cli_preview_json_cancel_and_apply_format_guard(self) -> None:
        repository, _marker, plan = self.repository()
        path = self.write_plan(plan)
        code, stdout, stderr = run_cli(
            "claim", "replay-correlation", str(path), "--repository", str(repository), "--format", "json"
        )
        self.assertEqual((code, stderr), (EXIT_PASS, ""))
        self.assertEqual(json.loads(stdout)["status"], "READY_TO_CLAIM")

        code, _stdout, stderr = run_cli(
            "claim", "replay-correlation", str(path), "--repository", str(repository), "--apply", "--format", "json"
        )
        self.assertEqual(code, EXIT_ERROR)
        self.assertIn("requires terminal format", stderr)

        with patch("sys.stdin", InteractiveInput("NO\n")):
            code, stdout, stderr = run_cli(
                "claim", "replay-correlation", str(path), "--repository", str(repository), "--apply"
            )
        self.assertEqual((code, stderr), (EXIT_PASS, ""))
        self.assertIn("CANCELLED", stdout)
        self.assertFalse(self.claim_path(repository).exists())

    def test_cli_exact_claim_applies_and_blocked_or_malformed_fail(self) -> None:
        repository, _marker, plan = self.repository()
        path = self.write_plan(plan)
        with patch("sys.stdin", InteractiveInput("CLAIM\n")):
            code, stdout, stderr = run_cli(
                "claim", "replay-correlation", str(path), "--repository", str(repository), "--apply"
            )
        self.assertEqual((code, stderr), (EXIT_PASS, ""))
        self.assertIn("CLAIMED", stdout)
        self.assertTrue(self.claim_path(repository).exists())

        code, _stdout, _stderr = run_cli(
            "claim", "replay-correlation", str(path), "--repository", str(repository)
        )
        self.assertEqual(code, EXIT_FAIL)

        malformed = deepcopy(plan)
        malformed["authority_boundary"]["authorizes_replay"] = True
        code, _stdout, stderr = run_cli(
            "claim", "replay-correlation", str(self.write_plan(malformed)), "--repository", str(repository)
        )
        self.assertEqual(code, EXIT_ERROR)
        self.assertIn("authority_boundary", stderr)


if __name__ == "__main__":
    unittest.main()
