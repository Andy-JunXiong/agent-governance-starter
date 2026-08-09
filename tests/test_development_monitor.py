import contextlib
import io
import json
import shutil
import subprocess
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from agentgov.cli import EXIT_ERROR, EXIT_PASS, main
from agentgov.development_monitor import (
    MONITOR_CONTRACT,
    MonitorPolicyError,
    build_development_monitor,
    render_development_monitor_html,
    render_development_monitor_json,
    render_development_monitor_markdown,
    write_development_monitor,
)
from agentgov.development_event_export import (
    build_development_event_export,
    development_export_default_output,
    write_development_event_export,
)
from agentgov.event_store import (
    LocalStateError,
    append_governance_event,
    load_governance_events,
)


ROOT = Path(__file__).resolve().parents[1]
FIXED_TIME = "2026-08-02T01:02:03.000Z"


def run_cli(*args: str) -> tuple[int, str, str]:
    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        code = main(list(args))
    return code, stdout.getvalue(), stderr.getvalue()


def run_git(repository: Path, *args: str) -> str:
    completed = subprocess.run(
        ("git", "-C", str(repository), *args),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        raise AssertionError(completed.stderr.decode("utf-8", errors="replace"))
    return completed.stdout.decode("utf-8", errors="replace").strip()


def create_repository(parent: Path) -> Path:
    repository = parent / "repository"
    repository.mkdir()
    run_git(repository, "init", "--quiet")
    run_git(repository, "config", "user.email", "fixture@example.invalid")
    run_git(repository, "config", "user.name", "Fixture Author")
    (repository / "README.md").write_text("# Fixture\n", encoding="utf-8")
    run_git(repository, "add", "README.md")
    run_git(repository, "commit", "--quiet", "-m", "baseline")
    return repository


def add_event(
    repository: Path,
    *,
    event_type: str,
    outcome: str,
    occurred_at: str,
    actor: str = "coding_agent",
    label: str | None = "fixture-agent",
    reasons: tuple[str, ...] = ("explicit_check_requested",),
    metrics: dict[str, int] | None = None,
    task_id: str = "fixture-task",
) -> str:
    _, relative = append_governance_event(
        repository,
        event_type=event_type,
        actor_class=actor,
        actor_label=label,
        task_id=task_id,
        task_digest="sha256:" + "a" * 64,
        outcome=outcome,
        evidence_ref=(
            ".agentgov/evidence/evd-" + "b" * 32 + ".json"
            if event_type != "scope.checked"
            else None
        ),
        reason_codes=reasons,
        metrics=metrics or {},
        occurred_at=occurred_at,
    )
    return relative


@unittest.skipUnless(shutil.which("git"), "Git is required for Monitor fixtures")
class DevelopmentMonitorTests(unittest.TestCase):
    def test_monitor_builds_overview_timeline_and_task_detail_in_order(self) -> None:
        with TemporaryDirectory() as temp_dir:
            repository = create_repository(Path(temp_dir))
            add_event(
                repository,
                event_type="completion.reconciled",
                outcome="verified",
                occurred_at="2026-08-02T01:03:00.000Z",
                reasons=("completion_reconciliation_requested",),
                metrics={"failures": 0, "advisories": 1},
            )
            add_event(
                repository,
                event_type="scope.checked",
                outcome="passed",
                occurred_at="2026-08-02T01:01:00.000Z",
                metrics={"changes": 2, "failures": 0, "advisories": 1},
            )
            add_event(
                repository,
                event_type="validation.completed",
                outcome="passed",
                occurred_at="2026-08-02T01:02:00.000Z",
                reasons=("declared_validation_requested",),
                metrics={"commands_declared": 1, "commands_run": 1, "commands_passed": 1},
            )
            add_event(
                repository,
                event_type="session.handed_off",
                outcome="handed_off",
                occurred_at="2026-08-02T01:04:00.000Z",
                actor="human",
                label="fixture-owner",
                reasons=("handoff_confirmed", "verified_evidence_fresh"),
                metrics={"verified_evidence": 1},
            )

            monitor = build_development_monitor(
                repository,
                generated_at=FIXED_TIME,
            )

        self.assertEqual(monitor.observation["scope"], "local_session")
        self.assertEqual(monitor.observation["history_completeness"], "partial")
        self.assertFalse(monitor.observation["cross_stage_discovery_available"])
        self.assertEqual(monitor.overview["events"], 4)
        self.assertEqual(monitor.overview["verified_completions"], 1)
        self.assertEqual(monitor.overview["handoffs"], 1)
        self.assertEqual(monitor.drift_review["state"], "due")
        self.assertEqual(monitor.drift_review["review_request"]["semantics"], "advisory")
        self.assertEqual([item["event_type"] for item in monitor.timeline], [
            "scope.checked", "validation.completed", "completion.reconciled", "session.handed_off"
        ])
        self.assertEqual(monitor.tasks[0]["latest_completion_state"], "verified")
        self.assertEqual(monitor.tasks[0]["latest_routing_state"], "handed_off")
        self.assertEqual(monitor.tasks[0]["handoffs"], 1)
        self.assertEqual(monitor.live_sessions[0]["state"], "handed_off")
        self.assertFalse(monitor.live_sessions[0]["attention_required"])
        self.assertEqual(monitor.protection_events, ())
        self.assertEqual(set(monitor.claim_layers), {"observed", "inferred", "unknown"})

    def test_monitor_surfaces_protection_events_without_claiming_resolution(self) -> None:
        with TemporaryDirectory() as temp_dir:
            repository = create_repository(Path(temp_dir))
            add_event(
                repository,
                event_type="scope.checked",
                outcome="failed",
                occurred_at="2026-08-02T01:01:00.000Z",
                reasons=("scope_failure",),
                metrics={"failures": 1},
            )
            add_event(
                repository,
                event_type="completion.reconciled",
                outcome="needs_evidence",
                occurred_at="2026-08-02T01:02:00.000Z",
                reasons=("fresh_evidence_missing",),
            )

            monitor = build_development_monitor(repository, generated_at=FIXED_TIME)
            html_output = render_development_monitor_html(monitor)

        self.assertEqual(monitor.overview["protection_events"], 2)
        self.assertEqual(monitor.overview["sessions_needing_attention"], 1)
        self.assertEqual(monitor.live_sessions[0]["state"], "needs_attention")
        self.assertEqual(
            [item["protection_type"] for item in monitor.protection_events],
            ["scope_boundary", "incomplete_completion"],
        )
        self.assertTrue(
            all(
                item["status"] == "observed_resolution_unknown"
                for item in monitor.protection_events
            )
        )
        self.assertIn("Protection Events", html_output)
        self.assertIn("Resolution", html_output)
        self.assertIn("Unknown", html_output)

    def test_empty_store_is_honest_partial_history(self) -> None:
        with TemporaryDirectory() as temp_dir:
            repository = create_repository(Path(temp_dir))

            monitor = build_development_monitor(repository, generated_at=FIXED_TIME)
            html_output = render_development_monitor_html(monitor)

        self.assertEqual(monitor.overview["events"], 0)
        self.assertIsNone(monitor.observation["started_at"])
        self.assertIn("No governance events are visible", html_output)
        self.assertIn("Missing sources", html_output)

    def test_ci_only_requires_ci_actors_and_disables_cross_stage_comparison(self) -> None:
        with TemporaryDirectory() as temp_dir:
            repository = create_repository(Path(temp_dir))
            add_event(
                repository,
                event_type="scope.checked",
                outcome="passed",
                occurred_at=FIXED_TIME,
            )
            with self.assertRaises(MonitorPolicyError):
                build_development_monitor(repository, observation_scope="ci_only")

        with TemporaryDirectory() as temp_dir:
            repository = create_repository(Path(temp_dir))
            add_event(
                repository,
                event_type="scope.checked",
                outcome="passed",
                occurred_at=FIXED_TIME,
                actor="ci",
                label="github-actions",
            )
            monitor = build_development_monitor(
                repository,
                observation_scope="ci_only",
                generated_at=FIXED_TIME,
            )

        self.assertEqual(monitor.observation["scope"], "ci_only")
        self.assertFalse(monitor.observation["cross_stage_discovery_available"])
        self.assertTrue(any("pre-code" in item for item in monitor.observation["missing_sources"]))

    def test_exported_and_combined_scopes_fail_until_redacted_export_exists(self) -> None:
        with TemporaryDirectory() as temp_dir:
            repository = create_repository(Path(temp_dir))
            for scope in ("exported_development", "combined"):
                with self.subTest(scope=scope), self.assertRaises(MonitorPolicyError):
                    build_development_monitor(repository, observation_scope=scope)

    def test_exported_development_uses_only_redacted_bundle_and_labels_source(self) -> None:
        with TemporaryDirectory() as temp_dir:
            repository = create_repository(Path(temp_dir))
            add_event(
                repository,
                event_type="scope.checked",
                outcome="passed",
                occurred_at=FIXED_TIME,
            )
            bundle = build_development_event_export(repository, created_at=FIXED_TIME)
            export_path = development_export_default_output(bundle)
            write_development_event_export(repository, bundle=bundle, output=export_path)

            monitor = build_development_monitor(
                repository,
                observation_scope="exported_development",
                export_path=export_path,
                generated_at=FIXED_TIME,
            )

        self.assertEqual(monitor.observation["source_kind"], "redacted_development_export")
        self.assertEqual(monitor.observation["source_event_counts"], {
            "local_session": 0,
            "exported_development": 1,
            "ci_only": 0,
        })
        self.assertEqual(monitor.timeline[0]["source_scope"], "exported_development")
        self.assertIsNone(monitor.timeline[0]["actor_label"])
        self.assertIsNone(monitor.timeline[0]["evidence_ref"])
        self.assertFalse(monitor.observation["cross_stage_discovery_available"])

    def test_combined_merges_export_with_ci_only_replay_and_keeps_sources_distinct(self) -> None:
        with TemporaryDirectory() as temp_dir:
            repository = create_repository(Path(temp_dir))
            add_event(
                repository,
                event_type="scope.checked",
                outcome="passed",
                occurred_at="2026-08-02T01:01:00.000Z",
            )
            bundle = build_development_event_export(repository, created_at=FIXED_TIME)
            export_path = development_export_default_output(bundle)
            write_development_event_export(repository, bundle=bundle, output=export_path)
            shutil.rmtree(repository / ".agentgov/events")
            add_event(
                repository,
                event_type="validation.completed",
                outcome="passed",
                occurred_at="2026-08-02T01:02:00.000Z",
                actor="ci",
                label="github-actions",
            )

            monitor = build_development_monitor(
                repository,
                observation_scope="combined",
                export_path=export_path,
                generated_at=FIXED_TIME,
            )
            html_output = render_development_monitor_html(monitor)

        self.assertEqual(monitor.observation["source_kind"], "combined_sources")
        self.assertEqual(monitor.observation["source_event_counts"], {
            "local_session": 0,
            "exported_development": 1,
            "ci_only": 1,
        })
        self.assertEqual([item["source_scope"] for item in monitor.timeline], [
            "exported_development", "ci_only"
        ])
        self.assertFalse(monitor.observation["cross_stage_discovery_available"])
        self.assertIn("cross-stage finding identity", " ".join(monitor.observation["missing_sources"]))
        self.assertIn("Source: exported development", html_output)
        self.assertIn("Source: ci only", html_output)

    def test_combined_rejects_non_ci_or_empty_replay_input(self) -> None:
        with TemporaryDirectory() as temp_dir:
            repository = create_repository(Path(temp_dir))
            add_event(
                repository,
                event_type="scope.checked",
                outcome="passed",
                occurred_at=FIXED_TIME,
            )
            bundle = build_development_event_export(repository, created_at=FIXED_TIME)
            export_path = development_export_default_output(bundle)
            write_development_event_export(repository, bundle=bundle, output=export_path)
            with self.assertRaises(MonitorPolicyError):
                build_development_monitor(
                    repository,
                    observation_scope="combined",
                    export_path=export_path,
                )
            empty = repository / ".agentgov/empty-ci"
            empty.mkdir()
            with self.assertRaises(MonitorPolicyError):
                build_development_monitor(
                    repository,
                    observation_scope="combined",
                    export_path=export_path,
                    event_directory=empty,
                )

    def test_html_is_self_contained_escaped_and_has_no_authority_controls(self) -> None:
        with TemporaryDirectory() as temp_dir:
            repository = create_repository(Path(temp_dir))
            add_event(
                repository,
                event_type="scope.checked",
                outcome="passed",
                occurred_at=FIXED_TIME,
                label="<script>alert('x')</script>",
            )
            monitor = build_development_monitor(repository, generated_at=FIXED_TIME)
            output = render_development_monitor_html(monitor)

        for heading in (
            "Overview",
            "Live Sessions",
            "Protection Events",
            "Activity Timeline",
            "Task Detail",
            "Claim layers",
        ):
            self.assertIn(heading, output)
        self.assertNotIn("<script>alert", output)
        self.assertIn("&lt;script&gt;alert", output)
        self.assertNotIn("<script", output)
        self.assertNotIn("<button", output)
        self.assertNotIn("http://", output)
        self.assertNotIn("https://", output)
        self.assertIn("No approval, mutation, merge, or deployment authority", output)

    def test_renderers_are_stable_and_schema_is_strict(self) -> None:
        with TemporaryDirectory() as temp_dir:
            repository = create_repository(Path(temp_dir))
            add_event(
                repository,
                event_type="scope.checked",
                outcome="failed",
                occurred_at=FIXED_TIME,
                reasons=("explicit_check_requested", "scope_failure"),
                metrics={"failures": 1},
            )
            first = build_development_monitor(repository, generated_at=FIXED_TIME)
            second = build_development_monitor(repository, generated_at=FIXED_TIME)

        self.assertEqual(render_development_monitor_json(first), render_development_monitor_json(second))
        self.assertIn("# AgentGov development Monitor", render_development_monitor_markdown(first))
        schema = json.loads((ROOT / "schemas/development-monitor.schema.json").read_text(encoding="utf-8"))
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(schema["properties"]["contract"]["const"], MONITOR_CONTRACT)
        self.assertTrue(all(value["const"] is False for value in schema["properties"]["authority_boundary"]["properties"].values()))

    def test_loader_deduplicates_identical_events_and_rejects_conflicts_or_invalid_json(self) -> None:
        with TemporaryDirectory() as temp_dir:
            repository = create_repository(Path(temp_dir))
            relative = add_event(
                repository,
                event_type="scope.checked",
                outcome="passed",
                occurred_at=FIXED_TIME,
            )
            original = repository / relative
            duplicate_dir = original.parent / "duplicate"
            duplicate_dir.mkdir()
            duplicate = duplicate_dir / original.name
            shutil.copyfile(original, duplicate)

            loaded = load_governance_events(original.parent)
            payload = json.loads(duplicate.read_text(encoding="utf-8"))
            payload["outcome"] = "failed"
            duplicate.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
            with self.assertRaises(LocalStateError):
                load_governance_events(original.parent)
            duplicate.unlink()
            invalid = original.parent / ("evt-" + "c" * 32 + ".json")
            invalid.write_text("{broken", encoding="utf-8")
            with self.assertRaises(LocalStateError):
                load_governance_events(original.parent)

        self.assertEqual(len(loaded.events), 1)
        self.assertEqual(loaded.files_read, 2)
        self.assertEqual(loaded.duplicates_removed, 1)

    def test_writer_refreshes_only_untracked_agentgov_owned_output(self) -> None:
        with TemporaryDirectory() as temp_dir:
            repository = create_repository(Path(temp_dir))
            monitor = build_development_monitor(repository, generated_at=FIXED_TIME)

            output = write_development_monitor(
                repository,
                monitor=monitor,
                output=Path(".agentgov/dashboard.html"),
                output_format="html",
            )
            refreshed = write_development_monitor(
                repository,
                monitor=monitor,
                output=Path(".agentgov/dashboard.html"),
                output_format="html",
            )
            unowned = repository / "custom.html"
            unowned.write_text("user content", encoding="utf-8")
            with self.assertRaises(MonitorPolicyError):
                write_development_monitor(
                    repository,
                    monitor=monitor,
                    output=Path("custom.html"),
                    output_format="html",
                )
            run_git(repository, "add", "-f", ".agentgov/dashboard.html")
            with self.assertRaises(MonitorPolicyError):
                write_development_monitor(
                    repository,
                    monitor=monitor,
                    output=Path(".agentgov/dashboard.html"),
                    output_format="html",
                )
            owned_content = output.read_text(encoding="utf-8")

        self.assertEqual(output, refreshed)
        self.assertIn(MONITOR_CONTRACT, owned_content)

    def test_monitor_cli_writes_default_html_and_reports_scope(self) -> None:
        with TemporaryDirectory() as temp_dir:
            repository = create_repository(Path(temp_dir))
            add_event(
                repository,
                event_type="scope.checked",
                outcome="passed",
                occurred_at=FIXED_TIME,
            )

            code, stdout, stderr = run_cli("monitor", "development", str(repository))
            dashboard = repository / ".agentgov" / "dashboard.html"
            content = dashboard.read_text(encoding="utf-8")

        self.assertEqual(code, EXIT_PASS)
        self.assertIn("MONITOR scope=local_session events=1 tasks=1", stdout)
        self.assertEqual(stderr, "")
        self.assertIn("Activity Timeline", content)

    def test_monitor_cli_rejects_ci_only_with_non_ci_events(self) -> None:
        with TemporaryDirectory() as temp_dir:
            repository = create_repository(Path(temp_dir))
            add_event(
                repository,
                event_type="scope.checked",
                outcome="passed",
                occurred_at=FIXED_TIME,
            )

            code, stdout, stderr = run_cli(
                "monitor", "development", str(repository), "--scope", "ci_only"
            )

        self.assertEqual(code, EXIT_ERROR)
        self.assertEqual(stdout, "")
        self.assertIn("ci_only Monitor cannot include", stderr)

    def test_monitor_cli_accepts_explicit_redacted_development_export(self) -> None:
        with TemporaryDirectory() as temp_dir:
            repository = create_repository(Path(temp_dir))
            add_event(
                repository,
                event_type="scope.checked",
                outcome="passed",
                occurred_at=FIXED_TIME,
            )
            bundle = build_development_event_export(repository, created_at=FIXED_TIME)
            export_path = development_export_default_output(bundle)
            write_development_event_export(repository, bundle=bundle, output=export_path)

            code, stdout, stderr = run_cli(
                "monitor",
                "development",
                str(repository),
                "--scope",
                "exported_development",
                "--export",
                str(export_path),
                "--format",
                "json",
            )
            content = (repository / ".agentgov/dashboard.json").read_text(encoding="utf-8")

        self.assertEqual(code, EXIT_PASS)
        self.assertEqual(stderr, "")
        self.assertIn("MONITOR scope=exported_development events=1 tasks=1", stdout)
        self.assertIn('"source_scope": "exported_development"', content)


if __name__ == "__main__":
    unittest.main()
