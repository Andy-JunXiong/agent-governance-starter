import contextlib
import io
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from agentgov.benefit_monitor import (
    BenefitMonitorConflictError,
    BenefitMonitorState,
    build_benefit_monitor,
    build_upgrade_observation,
    render_github_annotations,
    render_benefit_monitor_json,
    render_pull_request_review_markdown,
    render_upgrade_observation_json,
    write_benefit_monitor_bundle,
)
from agentgov.cli import EXIT_PASS, main


ROOT = Path(__file__).resolve().parents[1]
COMMIT_A = "a" * 40
COMMIT_B = "b" * 40


def finding(check_id: str, status: str) -> dict[str, str]:
    return {"check_id": check_id, "status": status, "message": "fixture"}


def report_document(findings: list[dict[str, str]]) -> dict[str, object]:
    summary = {"pass": 0, "warn": 0, "fail": 0, "advisory": 0}
    for item in findings:
        summary[item["status"].lower()] += 1
    gaps = [item for item in findings if item["status"] != "PASS"]
    return {
        "schema_version": "1.0",
        "tool": {"name": "agentgov", "version": "0.3.0"},
        "repository": "/home/runner/work/repository/repository",
        "summary": summary,
        "findings": findings,
        "known_gaps": gaps,
        "recommended_actions": [
            {"check_id": item["check_id"], "status": item["status"], "action": "review"}
            for item in gaps
        ],
        "scope_limitations": ["fixture"],
    }


def write_report(path: Path, findings: list[dict[str, str]]) -> None:
    path.write_text(json.dumps(report_document(findings)), encoding="utf-8")


def build_monitor(
    report: Path,
    *,
    commit: str = COMMIT_A,
    run_id: int = 10,
    baseline_report: Path | None = None,
    baseline_monitor: Path | None = None,
):
    return build_benefit_monitor(
        report,
        repository="owner/repository",
        ref="refs/heads/main",
        commit_sha=commit,
        run_id=run_id,
        run_attempt=1,
        event="push",
        observed_at="2026-08-02T01:02:03Z",
        baseline_report=baseline_report,
        baseline_monitor=baseline_monitor,
    )


class BenefitMonitorTests(unittest.TestCase):
    def test_first_snapshot_is_visible_without_making_a_trend_claim(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            report = root / "report.json"
            output = root / "monitor"
            write_report(report, [finding("one", "PASS"), finding("two", "WARN")])

            monitor = build_monitor(report)
            write_benefit_monitor_bundle(output, monitor)
            payload = json.loads((output / "benefit-monitor.json").read_text())
            markdown = (output / "BENEFIT_MONITOR.md").read_text()
            html = (output / "benefit-monitor.html").read_text()
            pr_markdown = (output / "PR_REVIEW.md").read_text()

        self.assertIs(monitor.state, BenefitMonitorState.BASELINE_MISSING)
        self.assertFalse(payload["baseline"]["available"])
        self.assertEqual(payload["user_state"], "missing")
        self.assertIsNone(payload["comparison"])
        self.assertEqual(len(payload["history"]), 1)
        self.assertIn("makes no trend or benefit claim", markdown)
        self.assertIn("Recent observed trend", html)
        self.assertIn("AgentGov Pull Request Review", pr_markdown)
        self.assertNotIn("coverage_percentage", json.dumps(payload))

    def test_trusted_baseline_builds_history_and_observed_improvement(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            before = root / "before.json"
            after = root / "after.json"
            baseline_output = root / "baseline-monitor"
            write_report(before, [finding("fixed", "FAIL"), finding("stable", "PASS")])
            baseline = build_monitor(before)
            write_benefit_monitor_bundle(baseline_output, baseline)
            write_report(after, [finding("fixed", "PASS"), finding("stable", "PASS")])

            monitor = build_monitor(
                after,
                commit=COMMIT_B,
                run_id=11,
                baseline_report=before,
                baseline_monitor=baseline_output / "benefit-monitor.json",
            )
            payload = json.loads(render_benefit_monitor_json(monitor))

        self.assertIs(monitor.state, BenefitMonitorState.IMPROVEMENT_OBSERVED)
        self.assertTrue(payload["baseline"]["available"])
        self.assertEqual(
            payload["comparison"]["deterministic_failures_resolved"],
            ["fixed"],
        )
        self.assertEqual([point["run_id"] for point in payload["history"]], [10, 11])
        self.assertTrue(any("caus" in item.lower() for item in payload["scope_limitations"]))
        self.assertTrue(any("ROI" in item for item in payload["scope_limitations"]))
        self.assertEqual(payload["user_state"], "improved")

    def test_pr_surface_contains_delta_and_actions_but_not_trend_or_upgrade_noise(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            before = root / "before.json"
            after = root / "after.json"
            baseline_output = root / "baseline"
            write_report(before, [finding("changed", "PASS")])
            write_benefit_monitor_bundle(baseline_output, build_monitor(before))
            write_report(after, [finding("changed", "FAIL")])
            monitor = build_monitor(
                after,
                commit=COMMIT_B,
                run_id=11,
                baseline_report=before,
                baseline_monitor=baseline_output / "benefit-monitor.json",
            )
            markdown = render_pull_request_review_markdown(monitor)

        self.assertIn("Merge signal", markdown)
        self.assertIn("New deterministic failures: `1`", markdown)
        self.assertIn("changed", markdown)
        self.assertNotIn("Recent observed trend", markdown)
        self.assertNotIn("upgrade", markdown.lower())

    def test_annotations_are_non_blocking_for_warn_and_redact_local_identity_and_token(self) -> None:
        with TemporaryDirectory() as temp_dir:
            report = Path(temp_dir) / "report.json"
            document = report_document(
                [
                    {
                        "check_id": "warn:fixture",
                        "status": "WARN",
                        "message": "C:\\Users\\alice\\project GH_TOKEN=secret-value ghp_1234567890abcdef",
                    },
                    finding("fail:fixture", "FAIL"),
                ]
            )
            report.write_text(json.dumps(document), encoding="utf-8")
            annotations = render_github_annotations(report)

        self.assertIn("::warning title=AgentGov WARN::", annotations)
        self.assertIn("::error title=AgentGov FAIL::", annotations)
        self.assertIn("<redacted-user-home>", annotations)
        self.assertIn("<redacted-secret-assignment>", annotations)
        self.assertNotIn("alice", annotations)
        self.assertNotIn("secret-value", annotations)
        self.assertNotIn("ghp_1234567890abcdef", annotations)

    def test_tampered_baseline_report_is_rejected(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            before = root / "before.json"
            after = root / "after.json"
            output = root / "baseline"
            write_report(before, [finding("x", "PASS")])
            write_benefit_monitor_bundle(output, build_monitor(before))
            write_report(before, [finding("x", "FAIL")])
            write_report(after, [finding("x", "PASS")])

            with self.assertRaisesRegex(ValueError, "digest"):
                build_monitor(
                    after,
                    baseline_report=before,
                    baseline_monitor=output / "benefit-monitor.json",
                )

    def test_malformed_inherited_history_is_rejected(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            before = root / "before.json"
            after = root / "after.json"
            output = root / "baseline"
            write_report(before, [finding("x", "PASS")])
            write_benefit_monitor_bundle(output, build_monitor(before))
            monitor_path = output / "benefit-monitor.json"
            payload = json.loads(monitor_path.read_text())
            payload["history"][0]["summary"]["pass"] = "forged"
            monitor_path.write_text(json.dumps(payload), encoding="utf-8")
            write_report(after, [finding("x", "PASS")])

            with self.assertRaisesRegex(ValueError, "history.*non-negative"):
                build_monitor(
                    after,
                    baseline_report=before,
                    baseline_monitor=monitor_path,
                )

    def test_baseline_cannot_claim_mutating_authority(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            before = root / "before.json"
            after = root / "after.json"
            output = root / "baseline"
            write_report(before, [finding("x", "PASS")])
            write_benefit_monitor_bundle(output, build_monitor(before))
            monitor_path = output / "benefit-monitor.json"
            payload = json.loads(monitor_path.read_text())
            payload["authority_boundary"]["governed_repository_modified"] = True
            monitor_path.write_text(json.dumps(payload), encoding="utf-8")
            write_report(after, [finding("x", "PASS")])

            with self.assertRaisesRegex(ValueError, "authority boundary"):
                build_monitor(
                    after,
                    baseline_report=before,
                    baseline_monitor=monitor_path,
                )

    def test_baseline_inputs_must_be_paired(self) -> None:
        with TemporaryDirectory() as temp_dir:
            report = Path(temp_dir) / "report.json"
            write_report(report, [finding("x", "PASS")])

            with self.assertRaisesRegex(ValueError, "supplied together"):
                build_benefit_monitor(
                    report,
                    repository="owner/repository",
                    ref="refs/heads/main",
                    commit_sha=COMMIT_A,
                    run_id=1,
                    run_attempt=1,
                    event="push",
                    observed_at="2026-08-02T01:02:03Z",
                    baseline_report=report,
                )

    def test_bundle_refuses_to_overwrite_existing_output(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            report = root / "report.json"
            output = root / "monitor"
            output.mkdir()
            write_report(report, [finding("x", "PASS")])

            with self.assertRaises(BenefitMonitorConflictError):
                write_benefit_monitor_bundle(output, build_monitor(report))

    def test_upgrade_observation_records_automation_without_counterfactual_claim(self) -> None:
        with TemporaryDirectory() as temp_dir:
            result = Path(temp_dir) / "upgrade.json"
            result.write_text(
                json.dumps(
                    {
                        "contract_version": "1.0",
                        "mode": "github_draft_pull_request",
                        "repository": "owner/repository",
                        "state": "created",
                        "branch": "agentgov/update-0.3.1",
                        "pull_request": {
                            "number": 3,
                            "url": "https://github.com/owner/repository/pull/3",
                            "draft": True,
                        },
                        "actions": {"draft_pull_request_created": True},
                    }
                ),
                encoding="utf-8",
            )

            observation = build_upgrade_observation(
                result,
                repository="owner/repository",
                commit_sha=COMMIT_A,
                run_id=12,
                started_epoch=100,
                completed_epoch=107,
            )
            payload = json.loads(render_upgrade_observation_json(observation))

        self.assertEqual(payload["metrics"]["detection_to_draft_pr_seconds"], 7)
        self.assertEqual(payload["metrics"]["mechanical_bridge_actions_observed"], 0)
        self.assertNotIn("actions_avoided", json.dumps(payload))
        self.assertTrue(any("counterfactual" in item for item in payload["scope_limitations"]))
        self.assertFalse(payload["authority_boundary"]["merge_authorized"])

    def test_cli_creates_monitor_bundle_for_ci(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            report = root / "report.json"
            output = root / "monitor"
            write_report(report, [finding("x", "PASS")])
            stdout = io.StringIO()
            stderr = io.StringIO()
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                exit_code = main(
                    [
                        "benefits",
                        "monitor",
                        str(report),
                        "--repository",
                        "owner/repository",
                        "--ref",
                        "refs/heads/main",
                        "--commit",
                        COMMIT_A,
                        "--run-id",
                        "10",
                        "--run-attempt",
                        "1",
                        "--event",
                        "push",
                        "--observed-at",
                        "2026-08-02T01:02:03Z",
                        "--output",
                        str(output),
                    ]
                )

        self.assertEqual(exit_code, EXIT_PASS)
        self.assertIn("STATE baseline_missing", stdout.getvalue())
        self.assertEqual(stderr.getvalue(), "")

    def test_schemas_are_strict_and_preserve_evidence_limits(self) -> None:
        monitor_schema = json.loads(
            (ROOT / "schemas/benefit-monitor.schema.json").read_text(encoding="utf-8")
        )
        upgrade_schema = json.loads(
            (ROOT / "schemas/upgrade-observation.schema.json").read_text(encoding="utf-8")
        )

        self.assertFalse(monitor_schema["additionalProperties"])
        self.assertIn("scope_limitations", monitor_schema["required"])
        self.assertIn("user_state", monitor_schema["required"])
        for value in monitor_schema["properties"]["authority_boundary"]["properties"].values():
            self.assertIs(value["const"], False)
        self.assertFalse(upgrade_schema["additionalProperties"])
        self.assertEqual(
            upgrade_schema["properties"]["metrics"]["properties"]["mechanical_bridge_actions_observed"]["enum"],
            [0, None],
        )


if __name__ == "__main__":
    unittest.main()
