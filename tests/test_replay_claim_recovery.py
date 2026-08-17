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
from agentgov.replay_claim_recovery import (
    MAX_CLAIM_EVIDENCE_BYTES,
    REPLAY_CLAIM_RECOVERY_INSPECTION_CONTRACT,
    REPLAY_CLAIM_RECOVERY_MARKER_CONTRACT,
    REPLAY_CLAIM_RECOVERY_PLAN_CONTRACT,
    REPLAY_CLAIM_RECOVERY_PREVIEW_CONTRACT,
    REPLAY_CLAIM_RECOVERY_RESULT_CONTRACT,
    REPLAY_CLAIM_RECOVERY_SCHEMA_VERSION,
    ClaimEvidenceClassification,
    RecoveryPreviewStatus,
    ReplayClaimOwnership,
    ReplayClaimRecoveryConflictError,
    ReplayClaimRecoveryStaleError,
    apply_replay_claim_recovery,
    classify_replay_claim_bytes,
    evaluate_replay_claim_ownership,
    prepare_replay_claim_recovery,
    replay_claim_recovery_digest,
    request_replay_claim_recovery_confirmation,
    validate_replay_claim_recovery,
    validate_replay_claim_recovery_marker,
    validate_replay_claim_recovery_plan,
)
from agentgov.replay_correlation_bridge import replay_reservation_marker_digest
from agentgov.replay_preflight import (
    AUTHORITY_BOUNDARY,
    REPLAY_ADAPTER_METADATA_CONTRACT,
    REPLAY_PREFLIGHT_SCHEMA_VERSION,
)


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas/replay-claim-recovery-v1.schema.json"
FIXTURES = ROOT / "governance/fixtures/replay-claim-recovery-v1"
CLAIM_FIXTURE = ROOT / "governance/fixtures/replay-correlation-claim-v1/claimed.json"


class InteractiveInput(io.StringIO):
    def isatty(self) -> bool:
        return True


def run_cli(*args: str) -> tuple[int, str, str]:
    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        exit_code = main(list(args))
    return exit_code, stdout.getvalue(), stderr.getvalue()


class ReplayClaimRecoveryTests(unittest.TestCase):
    def git(self, repository: Path, *arguments: str) -> str:
        result = subprocess.run(
            ("git", "-C", str(repository), *arguments),
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return result.stdout.strip()

    def repository(self) -> tuple[Path, dict, dict, bytes]:
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        self.git(root, "init")
        self.git(root, "config", "user.email", "fixture@example.invalid")
        self.git(root, "config", "user.name", "Recovery Fixture")
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
        reservation_path = root / marker["marker_path"]
        reservation_path.parent.mkdir()
        reservation_path.write_text(
            json.dumps(marker, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        claim = {
            "contract": "agentgov.replay-correlation-claim",
            "schema_version": "1.0",
            "claim_id": "rcl-0123456789abcdef",
            "correlation_id": marker["correlation_id"],
            "claim_path": ".agentgov/replay-claims/rpf-0123456789abcdef.json",
            "reservation": {
                "reservation_id": marker["reservation_id"],
                "marker_path": marker["marker_path"],
                "marker_digest": replay_reservation_marker_digest(marker),
            },
            "repository_head": head,
            "adapter": dict(marker["adapter"]),
            "claimant_id": "openai.codex-mcp",
            "status": "claimed",
            "authority_boundary": dict(AUTHORITY_BOUNDARY),
        }
        claim_bytes = (json.dumps(claim, indent=2, sort_keys=True) + "\n").encode()
        claim_path = root / claim["claim_path"]
        claim_path.parent.mkdir()
        claim_path.write_bytes(claim_bytes)
        (root / ".agentgov" / "replay-claim-recoveries").mkdir()
        plan = {
            "contract": REPLAY_CLAIM_RECOVERY_PLAN_CONTRACT,
            "schema_version": REPLAY_CLAIM_RECOVERY_SCHEMA_VERSION,
            "correlation_id": marker["correlation_id"],
            "reservation": {
                "marker_path": marker["marker_path"],
                "marker_digest": replay_reservation_marker_digest(marker),
            },
            "claim": {"marker_path": claim["claim_path"]},
            "recovery": {
                "registry_directory": ".agentgov/replay-claim-recoveries",
                "recovered_by": "human.product-owner",
                "reason_code": "claimant_abandoned",
            },
            "adapter": {"metadata_path": ".agentgov/adapter.json"},
            "authority_boundary": dict(AUTHORITY_BOUNDARY),
        }
        return root, marker, plan, claim_bytes

    def write_plan(self, plan: dict) -> Path:
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        path = Path(temporary.name) / "recovery-plan.json"
        path.write_text(json.dumps(plan), encoding="utf-8")
        return path

    def claim_path(self, root: Path) -> Path:
        return root / ".agentgov/replay-claims/rpf-0123456789abcdef.json"

    def recovery_path(self, root: Path) -> Path:
        return root / ".agentgov/replay-claim-recoveries/rpf-0123456789abcdef.json"

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
            {
                "#/$defs/plan",
                "#/$defs/inspection",
                "#/$defs/marker",
                "#/$defs/preview",
                "#/$defs/result",
            },
        )
        authority = schema["$defs"]["authorityBoundary"]["properties"]
        self.assertTrue(all(item["const"] is False for item in authority.values()))
        plan = json.loads((FIXTURES / "valid-plan.json").read_text(encoding="utf-8"))
        recovery = json.loads((FIXTURES / "recovered-valid.json").read_text(encoding="utf-8"))
        self.assertEqual(validate_replay_claim_recovery_plan(plan), [])
        self.assertEqual(validate_replay_claim_recovery_marker(recovery), [])
        self.assertEqual(recovery["contract"], REPLAY_CLAIM_RECOVERY_MARKER_CONTRACT)
        reservation = {
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
        self.assertEqual(
            validate_replay_claim_recovery(
                recovery,
                reservation_marker=reservation,
                claim_bytes=CLAIM_FIXTURE.read_bytes(),
            ),
            [],
        )

    def test_preview_is_read_only_exact_and_ready_for_valid_claim(self) -> None:
        root, marker, plan, claim_bytes = self.repository()
        reservation_before = (root / marker["marker_path"]).read_bytes()
        status_before = self.git(root, "status", "--porcelain")

        preview = prepare_replay_claim_recovery(plan, repository=root)

        self.assertEqual(preview.status, RecoveryPreviewStatus.READY)
        self.assertEqual(preview.contract, REPLAY_CLAIM_RECOVERY_PREVIEW_CONTRACT)
        self.assertEqual(preview.inspection.contract, REPLAY_CLAIM_RECOVERY_INSPECTION_CONTRACT)
        self.assertEqual(preview.inspection.classification, ClaimEvidenceClassification.VALID)
        self.assertEqual(
            validate_replay_claim_recovery(
                preview.recovery,
                reservation_marker=marker,
                claim_bytes=claim_bytes,
            ),
            [],
        )
        self.assertFalse(self.recovery_path(root).exists())
        self.assertEqual(self.claim_path(root).read_bytes(), claim_bytes)
        self.assertEqual((root / marker["marker_path"]).read_bytes(), reservation_before)
        self.assertEqual(self.git(root, "status", "--porcelain"), status_before)

    def test_valid_partial_and_malformed_claims_are_recovery_ready(self) -> None:
        cases = [
            (None, ClaimEvidenceClassification.VALID),
            (b'{"contract":', ClaimEvidenceClassification.PARTIAL),
            (b"not-json", ClaimEvidenceClassification.MALFORMED),
            (b'{"contract":"x","contract":"y"}', ClaimEvidenceClassification.MALFORMED),
            (b"", ClaimEvidenceClassification.PARTIAL),
        ]
        for replacement, expected in cases:
            with self.subTest(expected=expected):
                root, _marker, plan, _claim_bytes = self.repository()
                if replacement is not None:
                    self.claim_path(root).write_bytes(replacement)
                preview = prepare_replay_claim_recovery(plan, repository=root)
                self.assertEqual(preview.status, RecoveryPreviewStatus.READY)
                self.assertEqual(preview.inspection.classification, expected)
                self.assertEqual(preview.recovery["abandoned_claim"]["classification"], expected.value)

    def test_missing_and_inconsistent_claims_are_blocked(self) -> None:
        root, _marker, plan, _claim_bytes = self.repository()
        self.claim_path(root).unlink()
        missing = prepare_replay_claim_recovery(plan, repository=root)
        self.assertEqual(missing.status, RecoveryPreviewStatus.BLOCKED)
        self.assertEqual(missing.inspection.classification, ClaimEvidenceClassification.MISSING)
        self.assertIn("claim_missing", missing.inspection.reason_codes)

        root, _marker, plan, _claim_bytes = self.repository()
        value = json.loads(self.claim_path(root).read_text(encoding="utf-8"))
        value["correlation_id"] = "rpf-ffffffffffffffff"
        self.claim_path(root).write_text(json.dumps(value), encoding="utf-8")
        inconsistent = prepare_replay_claim_recovery(plan, repository=root)
        self.assertEqual(inconsistent.status, RecoveryPreviewStatus.BLOCKED)
        self.assertEqual(
            inconsistent.inspection.classification,
            ClaimEvidenceClassification.INCONSISTENT,
        )
        self.assertIn("claim_inconsistent", inconsistent.inspection.reason_codes)

    def test_unsafe_or_unbounded_claim_is_unknown(self) -> None:
        root, _marker, plan, _claim_bytes = self.repository()
        self.claim_path(root).write_bytes(b"x" * (MAX_CLAIM_EVIDENCE_BYTES + 1))
        preview = prepare_replay_claim_recovery(plan, repository=root)
        self.assertEqual(preview.status, RecoveryPreviewStatus.UNKNOWN)
        self.assertEqual(preview.inspection.classification, ClaimEvidenceClassification.UNKNOWN)
        self.assertIn("claim_evidence_unbounded", preview.inspection.reason_codes)

    def test_missing_registry_blocks_without_scaffolding(self) -> None:
        root, _marker, plan, _claim_bytes = self.repository()
        registry = root / ".agentgov/replay-claim-recoveries"
        registry.rmdir()
        preview = prepare_replay_claim_recovery(plan, repository=root)
        self.assertEqual(preview.status, RecoveryPreviewStatus.BLOCKED)
        self.assertIn("recovery_registry_missing", preview.inspection.reason_codes)
        self.assertFalse(registry.exists())

    def test_reservation_head_and_adapter_drift_fail_closed(self) -> None:
        root, _marker, plan, _claim_bytes = self.repository()
        wrong = deepcopy(plan)
        wrong["reservation"]["marker_digest"] = "sha256:" + "f" * 64
        preview = prepare_replay_claim_recovery(wrong, repository=root)
        self.assertEqual(preview.status, RecoveryPreviewStatus.BLOCKED)
        self.assertIn("reservation_marker_mismatch", preview.inspection.reason_codes)

        root, _marker, plan, _claim_bytes = self.repository()
        (root / "README.md").write_text("changed\n", encoding="utf-8")
        self.git(root, "add", "README.md")
        self.git(root, "commit", "-m", "head drift")
        preview = prepare_replay_claim_recovery(plan, repository=root)
        self.assertEqual(preview.status, RecoveryPreviewStatus.BLOCKED)
        self.assertIn("repository_head_mismatch", preview.inspection.reason_codes)

        root, _marker, plan, _claim_bytes = self.repository()
        metadata_path = root / ".agentgov/adapter.json"
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        metadata["adapter_version"] = "9.0.0"
        metadata_path.write_text(json.dumps(metadata), encoding="utf-8")
        preview = prepare_replay_claim_recovery(plan, repository=root)
        self.assertEqual(preview.status, RecoveryPreviewStatus.BLOCKED)
        self.assertIn("adapter_mismatch", preview.inspection.reason_codes)

    def test_confirmation_requires_exact_word_and_interactive_terminal(self) -> None:
        root, _marker, plan, _claim_bytes = self.repository()
        preview = prepare_replay_claim_recovery(plan, repository=root)
        self.assertFalse(request_replay_claim_recovery_confirmation(preview, decision_reader=lambda _: "RECOVER", is_interactive_terminal=False))
        self.assertFalse(request_replay_claim_recovery_confirmation(preview, decision_reader=lambda _: "recover", is_interactive_terminal=True))
        self.assertTrue(request_replay_claim_recovery_confirmation(preview, decision_reader=lambda _: "RECOVER", is_interactive_terminal=True))

    def test_apply_creates_once_and_preserves_claim_and_reservation(self) -> None:
        root, marker, plan, claim_bytes = self.repository()
        reservation_path = root / marker["marker_path"]
        reservation_before = reservation_path.read_bytes()
        preview = prepare_replay_claim_recovery(plan, repository=root)

        result = apply_replay_claim_recovery(preview, plan, repository=root)
        recovery = json.loads(self.recovery_path(root).read_text(encoding="utf-8"))

        self.assertEqual(result.contract, REPLAY_CLAIM_RECOVERY_RESULT_CONTRACT)
        self.assertEqual(result.status, "RECOVERED")
        self.assertEqual(result.recovery_digest, replay_claim_recovery_digest(recovery))
        self.assertEqual(recovery, preview.recovery)
        self.assertEqual(self.claim_path(root).read_bytes(), claim_bytes)
        self.assertEqual(reservation_path.read_bytes(), reservation_before)
        self.assertTrue(all(value is False for value in recovery["authority_boundary"].values()))
        with self.assertRaises(ReplayClaimRecoveryConflictError):
            apply_replay_claim_recovery(preview, plan, repository=root)

    def test_exact_recovery_marks_only_exact_claim_bytes_recovered(self) -> None:
        root, marker, plan, claim_bytes = self.repository()
        preview = prepare_replay_claim_recovery(plan, repository=root)
        apply_replay_claim_recovery(preview, plan, repository=root)
        recovery = json.loads(self.recovery_path(root).read_text(encoding="utf-8"))
        self.assertEqual(
            evaluate_replay_claim_ownership(
                claim_bytes,
                recovery_marker=recovery,
                reservation_marker=marker,
            ),
            ReplayClaimOwnership.RECOVERED,
        )
        self.assertEqual(
            evaluate_replay_claim_ownership(
                claim_bytes + b" ",
                recovery_marker=recovery,
                reservation_marker=marker,
            ),
            ReplayClaimOwnership.UNKNOWN,
        )
        inspected = prepare_replay_claim_recovery(plan, repository=root)
        self.assertEqual(inspected.status, RecoveryPreviewStatus.ALREADY_RECOVERED)
        self.assertEqual(inspected.inspection.classification, ClaimEvidenceClassification.RECOVERED)
        self.assertIsNone(inspected.recovery)

    def test_without_recovery_only_a_valid_claim_is_active(self) -> None:
        root, marker, plan, claim_bytes = self.repository()
        self.assertEqual(
            evaluate_replay_claim_ownership(
                claim_bytes,
                recovery_marker=None,
                reservation_marker=marker,
            ),
            ReplayClaimOwnership.ACTIVE,
        )
        custom = json.loads(claim_bytes)
        custom["claim_path"] = ".agentgov/custom-claims/rpf-0123456789abcdef.json"
        custom_bytes = (json.dumps(custom, indent=2, sort_keys=True) + "\n").encode()
        self.assertEqual(
            evaluate_replay_claim_ownership(
                custom_bytes,
                recovery_marker=None,
                reservation_marker=marker,
            ),
            ReplayClaimOwnership.ACTIVE,
        )
        self.assertEqual(
            classify_replay_claim_bytes(
                b"[]",
                claim_path=plan["claim"]["marker_path"],
                correlation_id=plan["correlation_id"],
                reservation_marker=marker,
            ),
            ClaimEvidenceClassification.MALFORMED,
        )

    def test_stale_claim_or_reservation_writes_no_recovery(self) -> None:
        root, marker, plan, _claim_bytes = self.repository()
        preview = prepare_replay_claim_recovery(plan, repository=root)
        self.claim_path(root).write_bytes(b'{"changed":')
        with self.assertRaises(ReplayClaimRecoveryStaleError):
            apply_replay_claim_recovery(preview, plan, repository=root)
        self.assertFalse(self.recovery_path(root).exists())

        root, marker, plan, _claim_bytes = self.repository()
        preview = prepare_replay_claim_recovery(plan, repository=root)
        reservation_path = root / marker["marker_path"]
        changed = json.loads(reservation_path.read_text(encoding="utf-8"))
        changed["reservation_id"] = "rrv-ffffffffffffffff"
        reservation_path.write_text(json.dumps(changed), encoding="utf-8")
        with self.assertRaises(ReplayClaimRecoveryStaleError):
            apply_replay_claim_recovery(preview, plan, repository=root)
        self.assertFalse(self.recovery_path(root).exists())

    def test_exclusive_create_race_preserves_competing_recovery(self) -> None:
        root, _marker, plan, claim_bytes = self.repository()
        preview = prepare_replay_claim_recovery(plan, repository=root)
        real_open = os.open

        def racing_open(path: os.PathLike[str] | str, flags: int, mode: int = 0o777) -> int:
            if Path(path) == self.recovery_path(root):
                self.recovery_path(root).write_text("winner\n", encoding="utf-8")
            return real_open(path, flags, mode)

        with patch("agentgov.replay_claim_recovery.os.open", side_effect=racing_open):
            with self.assertRaises(ReplayClaimRecoveryConflictError):
                apply_replay_claim_recovery(preview, plan, repository=root)
        self.assertEqual(self.recovery_path(root).read_text(encoding="utf-8"), "winner\n")
        self.assertEqual(self.claim_path(root).read_bytes(), claim_bytes)

    def test_write_failure_retains_ambiguous_recovery_and_original_claim(self) -> None:
        root, _marker, plan, claim_bytes = self.repository()
        preview = prepare_replay_claim_recovery(plan, repository=root)
        with patch("agentgov.replay_claim_recovery.os.write", side_effect=OSError("uncertain")):
            with self.assertRaises(OSError):
                apply_replay_claim_recovery(preview, plan, repository=root)
        self.assertTrue(self.recovery_path(root).exists())
        self.assertEqual(self.claim_path(root).read_bytes(), claim_bytes)
        retry = prepare_replay_claim_recovery(plan, repository=root)
        self.assertEqual(retry.status, RecoveryPreviewStatus.UNKNOWN)
        self.assertIn("recovery_marker_invalid", retry.inspection.reason_codes)

    def test_strict_validators_reject_extra_fields_unsafe_paths_and_drift(self) -> None:
        plan = json.loads((FIXTURES / "valid-plan.json").read_text(encoding="utf-8"))
        extra = deepcopy(plan)
        extra["delete_claim"] = True
        self.assertIn("$.delete_claim is not allowed", validate_replay_claim_recovery_plan(extra))
        unsafe = deepcopy(plan)
        unsafe["recovery"]["registry_directory"] = "../recoveries"
        self.assertTrue(any("registry_directory" in item for item in validate_replay_claim_recovery_plan(unsafe)))
        collision = deepcopy(plan)
        collision["recovery"]["registry_directory"] = ".agentgov/replay-claims"
        self.assertTrue(any("must be distinct" in item for item in validate_replay_claim_recovery_plan(collision)))
        recovery = json.loads((FIXTURES / "recovered-valid.json").read_text(encoding="utf-8"))
        recovery["status"] = "deleted"
        recovery["authority_boundary"]["authorizes_replay"] = True
        errors = validate_replay_claim_recovery_marker(recovery)
        self.assertIn("$.status must equal 'recovered'", errors)
        self.assertTrue(any("authority_boundary" in item for item in errors))
        unhashable = deepcopy(recovery)
        unhashable["abandoned_claim"]["classification"] = []
        self.assertTrue(validate_replay_claim_recovery_marker(unhashable))

    def test_cli_json_cancel_exact_apply_and_guards(self) -> None:
        root, _marker, plan, claim_bytes = self.repository()
        path = self.write_plan(plan)
        code, stdout, stderr = run_cli(
            "recover", "replay-claim", str(path), "--repository", str(root), "--format", "json"
        )
        self.assertEqual((code, stderr), (EXIT_PASS, ""))
        self.assertEqual(json.loads(stdout)["status"], "READY_TO_RECOVER")

        code, _stdout, stderr = run_cli(
            "recover", "replay-claim", str(path), "--repository", str(root), "--apply", "--format", "json"
        )
        self.assertEqual(code, EXIT_ERROR)
        self.assertIn("requires terminal format", stderr)

        with patch("sys.stdin", InteractiveInput("NO\n")):
            code, stdout, stderr = run_cli(
                "recover", "replay-claim", str(path), "--repository", str(root), "--apply"
            )
        self.assertEqual((code, stderr), (EXIT_PASS, ""))
        self.assertIn("CANCELLED", stdout)
        self.assertFalse(self.recovery_path(root).exists())
        self.assertEqual(self.claim_path(root).read_bytes(), claim_bytes)

        with patch("sys.stdin", InteractiveInput("RECOVER\n")):
            code, stdout, stderr = run_cli(
                "recover", "replay-claim", str(path), "--repository", str(root), "--apply"
            )
        self.assertEqual((code, stderr), (EXIT_PASS, ""))
        self.assertIn("RECOVERED", stdout)
        self.assertTrue(self.recovery_path(root).exists())

        code, _stdout, _stderr = run_cli(
            "recover", "replay-claim", str(path), "--repository", str(root), "--apply"
        )
        self.assertEqual(code, EXIT_FAIL)

    def test_cli_malformed_plan_is_operational_error(self) -> None:
        root, _marker, plan, _claim_bytes = self.repository()
        plan["authority_boundary"]["authorizes_replay"] = True
        code, _stdout, stderr = run_cli(
            "recover", "replay-claim", str(self.write_plan(plan)), "--repository", str(root)
        )
        self.assertEqual(code, EXIT_ERROR)
        self.assertIn("authority_boundary", stderr)

        duplicate = self.write_plan(plan)
        duplicate.write_text(
            '{"contract":"agentgov.replay-claim-recovery-plan","contract":"duplicate"}',
            encoding="utf-8",
        )
        code, _stdout, stderr = run_cli(
            "recover", "replay-claim", str(duplicate), "--repository", str(root)
        )
        self.assertEqual(code, EXIT_ERROR)
        self.assertIn("not readable JSON", stderr)


if __name__ == "__main__":
    unittest.main()
