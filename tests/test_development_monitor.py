import contextlib
import io
import json
import re
import shutil
import subprocess
import unittest
from dataclasses import replace
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
from agentgov.learning_review import build_learning_review, write_learning_review


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
                event_type="validation.completed",
                outcome="failed",
                occurred_at="2026-08-02T01:01:20.000Z",
                reasons=("validation_failed",),
            )
            add_event(
                repository,
                event_type="validation.completed",
                outcome="stale",
                occurred_at="2026-08-02T01:01:40.000Z",
                reasons=("validation_stale",),
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
            markdown_output = render_development_monitor_markdown(monitor)
            json_output = json.loads(render_development_monitor_json(monitor))

        self.assertEqual(monitor.schema_version, "1.9")
        self.assertEqual(monitor.overview["protection_events"], 4)
        self.assertEqual(monitor.overview["sessions_needing_attention"], 1)
        self.assertEqual(monitor.live_sessions[0]["state"], "needs_attention")
        self.assertEqual(
            [item["protection_type"] for item in monitor.protection_events],
            [
                "scope_boundary",
                "validation_failure",
                "stale_evidence",
                "incomplete_completion",
            ],
        )
        self.assertTrue(
            all(
                item["status"] == "observed_resolution_unknown"
                for item in monitor.protection_events
            )
        )
        self.assertEqual(
            [item["guidance"]["action_id"] for item in monitor.protection_events],
            [
                "review_scope_boundary",
                "review_validation_failure",
                "refresh_stale_evidence",
                "complete_missing_evidence",
            ],
        )
        self.assertTrue(
            all(
                item["guidance"]["availability"] == "available"
                and item["guidance"]["target"] == "task_detail"
                and item["guidance"]["semantics"] == "read_only_navigation"
                for item in monitor.protection_events
            )
        )
        self.assertEqual(
            json_output["protection_events"][0]["guidance"],
            monitor.protection_events[0]["guidance"],
        )
        self.assertIn("Protection Events", html_output)
        self.assertIn("Resolution", html_output)
        self.assertIn("Unknown", html_output)
        guidance_targets = re.findall(
            r'class="resolution-link" href="#(task-detail-[0-9a-f]{32})"',
            html_output,
        )
        self.assertEqual(len(guidance_targets), 4)
        self.assertEqual(len(set(guidance_targets)), 1)
        task_anchor = guidance_targets[0]
        self.assertIn(
            f'<details class="task task-attention" id="{task_anchor}" open>',
            html_output,
        )
        self.assertIn(
            f"[Review task scope and changed paths](#{task_anchor})",
            markdown_output,
        )
        self.assertIn("Needs attention", html_output)
        self.assertIn("incomplete completion", html_output)
        self.assertIn("fresh_evidence_missing", html_output)
        self.assertIn("Affected paths", html_output)
        self.assertIn(
            "current Monitor event contract records counts, not changed paths",
            html_output,
        )
        self.assertIn("Next human action", html_output)
        self.assertIn("Resolution remains unknown", html_output)
        self.assertIn("Technical audit data (optional)", html_output)
        self.assertNotIn('<details class="machine" open>', html_output)
        self.assertNotIn("http://", html_output)
        self.assertNotIn("https://", html_output)

    def test_protection_guidance_renderers_escape_labels_and_fail_closed_on_targets(self) -> None:
        with TemporaryDirectory() as temp_dir:
            repository = create_repository(Path(temp_dir))
            add_event(
                repository,
                event_type="scope.checked",
                outcome="failed",
                occurred_at=FIXED_TIME,
                reasons=("scope_failure",),
            )
            monitor = build_development_monitor(repository, generated_at=FIXED_TIME)

        protection = dict(monitor.protection_events[0])
        protection["guidance"] = {
            **protection["guidance"],
            "label": "Review [scope] <script>alert(1)</script>",
        }
        escaped = replace(monitor, protection_events=(protection,))
        html_output = render_development_monitor_html(escaped)
        markdown_output = render_development_monitor_markdown(escaped)
        self.assertNotIn("<script>alert", html_output)
        self.assertIn("&lt;script&gt;alert", html_output)
        self.assertRegex(
            markdown_output,
            r"\[Review \\\[scope\\\] <script>alert\(1\)</script>\]"
            r"\(#task-detail-[0-9a-f]{32}\)",
        )

        unavailable = dict(protection)
        unavailable["guidance"] = {
            "availability": "unavailable",
            "action_id": None,
            "label": "Resolution guidance unavailable",
            "target": None,
            "semantics": "read_only_navigation",
        }
        unavailable_monitor = replace(monitor, protection_events=(unavailable,))
        self.assertNotIn('class="resolution-link" href=', render_development_monitor_html(unavailable_monitor))
        self.assertIn("guidance unavailable", render_development_monitor_markdown(unavailable_monitor))

        unsafe = dict(protection)
        unsafe["guidance"] = {**protection["guidance"], "target": "https://example.invalid"}
        unsafe_output = render_development_monitor_html(
            replace(monitor, protection_events=(unsafe,))
        )
        self.assertNotIn('href="https://example.invalid"', unsafe_output)
        self.assertNotIn('class="resolution-link" href=', unsafe_output)
        self.assertIn("Unavailable", unsafe_output)

        malformed = dict(protection)
        malformed["guidance"] = None
        malformed_monitor = replace(monitor, protection_events=(malformed,))
        malformed_html = render_development_monitor_html(malformed_monitor)
        self.assertNotIn('class="resolution-link" href=', malformed_html)
        self.assertIn("Unavailable", malformed_html)
        self.assertIn("guidance unavailable", render_development_monitor_markdown(malformed_monitor))

    def test_guidance_targets_each_matching_task_and_leaves_healthy_tasks_compact(self) -> None:
        with TemporaryDirectory() as temp_dir:
            repository = create_repository(Path(temp_dir))
            add_event(
                repository,
                task_id="scope-task",
                event_type="scope.checked",
                outcome="failed",
                occurred_at="2026-08-02T01:01:00.000Z",
                reasons=("scope_failure",),
                metrics={"failures": 2},
            )
            add_event(
                repository,
                task_id="validation-task",
                event_type="validation.completed",
                outcome="failed",
                occurred_at="2026-08-02T01:01:20.000Z",
                reasons=("validation_failed",),
                metrics={"commands_run": 3, "commands_passed": 2},
            )
            add_event(
                repository,
                task_id="healthy-task",
                event_type="validation.completed",
                outcome="passed",
                occurred_at="2026-08-02T01:01:40.000Z",
                reasons=("validation_passed",),
                metrics={"commands_run": 1, "commands_passed": 1},
            )
            monitor = build_development_monitor(repository, generated_at=FIXED_TIME)
            html_output = render_development_monitor_html(monitor)
            markdown_output = render_development_monitor_markdown(monitor)
            json_before = render_development_monitor_json(monitor)

        protected_cards = dict(
            re.findall(
                r'<details class="task task-attention" id="(task-detail-[0-9a-f]{32})" open>'
                r'<summary><span>([^<]+)</span>',
                html_output,
            )
        )
        guidance_targets = set(
            re.findall(
                r'class="resolution-link" href="#(task-detail-[0-9a-f]{32})"',
                html_output,
            )
        )
        self.assertEqual(set(protected_cards.values()), {"scope-task", "validation-task"})
        self.assertEqual(guidance_targets, set(protected_cards))
        self.assertRegex(
            html_output,
            r'<details class="task" id="task-detail-[0-9a-f]{32}">'
            r'<summary><span>healthy-task</span>',
        )
        self.assertNotRegex(
            html_output,
            r'<details class="task" id="task-detail-[0-9a-f]{32}" open>'
            r'<summary><span>healthy-task</span>',
        )
        self.assertIn("scope_failure", html_output)
        self.assertIn("failures=2", html_output)
        self.assertIn("validation_failed", html_output)
        self.assertIn("commands passed=2", html_output)
        self.assertIn("commands run=3", html_output)
        self.assertTrue(
            all(f"(#{anchor})" in markdown_output for anchor in protected_cards)
        )
        self.assertEqual(render_development_monitor_json(monitor), json_before)

    def test_empty_store_is_honest_partial_history(self) -> None:
        with TemporaryDirectory() as temp_dir:
            repository = create_repository(Path(temp_dir))

            monitor = build_development_monitor(repository, generated_at=FIXED_TIME)
            html_output = render_development_monitor_html(monitor)

        self.assertEqual(monitor.overview["events"], 0)
        self.assertIsNone(monitor.observation["started_at"])
        self.assertEqual(monitor.benefit["comparison_mode"], "single_observation_only")
        self.assertEqual(
            monitor.benefit["observation_window"],
            {"started_at": None, "ended_at": None},
        )
        cards = {item["claim_class"]: item for item in monitor.benefit["cards"]}
        self.assertEqual(cards["observed_fact"]["metrics"]["events"], 0)
        self.assertEqual(cards["supported_inference"]["status"], "unavailable")
        self.assertEqual(cards["human_feedback"]["status"], "unavailable")
        self.assertEqual(cards["unknown"]["status"], "unknown")
        learning_cards = {
            item["learning_class"]: item for item in monitor.learning["cards"]
        }
        self.assertEqual(
            learning_cards["observed_signal"]["metrics"],
            {
                "scope_boundary": 0,
                "validation_failure": 0,
                "stale_evidence": 0,
                "incomplete_completion": 0,
            },
        )
        self.assertEqual(
            learning_cards["repeated_signal_candidate"]["status"],
            "none_observed",
        )
        self.assertEqual(
            learning_cards["human_judgment"]["status"], "unavailable"
        )
        self.assertEqual(learning_cards["unknown"]["status"], "unknown")
        self.assertIn("No governance events are visible", html_output)
        self.assertIn("Missing sources", html_output)

    def test_benefit_view_separates_single_observation_claim_classes(self) -> None:
        with TemporaryDirectory() as temp_dir:
            repository = create_repository(Path(temp_dir))
            add_event(
                repository,
                task_id="scope-task",
                event_type="scope.checked",
                outcome="failed",
                occurred_at="2026-08-02T01:01:00.000Z",
                reasons=("scope_failure",),
                metrics={"failures": 1},
            )
            add_event(
                repository,
                task_id="verified-task",
                event_type="completion.reconciled",
                outcome="verified",
                occurred_at=FIXED_TIME,
                reasons=("completion_reconciliation_requested",),
            )
            monitor = build_development_monitor(repository, generated_at=FIXED_TIME)
            html_output = render_development_monitor_html(monitor)
            markdown_output = render_development_monitor_markdown(monitor)
            json_output = json.loads(render_development_monitor_json(monitor))

        benefit = monitor.benefit
        self.assertEqual(benefit["comparison_mode"], "single_observation_only")
        self.assertEqual(benefit["scope"], "local_session")
        self.assertEqual(
            benefit["observation_window"],
            {
                "started_at": "2026-08-02T01:01:00.000Z",
                "ended_at": FIXED_TIME,
            },
        )
        self.assertEqual(
            [item["claim_class"] for item in benefit["cards"]],
            [
                "observed_fact",
                "reproduced_comparison",
                "supported_inference",
                "human_feedback",
                "unknown",
            ],
        )
        cards = {item["claim_class"]: item for item in benefit["cards"]}
        self.assertEqual(
            cards["observed_fact"]["metrics"],
            {
                "tasks": 2,
                "events": 2,
                "protection_events": 1,
                "verified_completions": 1,
                "handoffs": 0,
            },
        )
        self.assertEqual(cards["reproduced_comparison"]["status"], "unavailable")
        self.assertEqual(cards["reproduced_comparison"]["metrics"], {})
        self.assertIn(
            "denominator_unavailable",
            cards["reproduced_comparison"]["reason_codes"],
        )
        self.assertEqual(cards["supported_inference"]["status"], "supported")
        self.assertEqual(cards["supported_inference"]["semantics"], "advisory")
        self.assertEqual(
            cards["supported_inference"]["metrics"]["protection_events"],
            1,
        )
        self.assertEqual(cards["human_feedback"]["status"], "unavailable")
        self.assertEqual(cards["human_feedback"]["metrics"], {})
        self.assertEqual(cards["unknown"]["status"], "unknown")
        self.assertIn("return on investment", benefit["claim_limit"])
        self.assertEqual(json_output["benefit"], json.loads(json.dumps(benefit)))
        for text in (
            "Benefit",
            "Current-scope activity",
            "Cross-window comparison",
            "Review prioritization",
            "Attributed human feedback",
            "Causal benefit limits",
            "Single-observation cards do not prove causal benefit",
        ):
            self.assertIn(text, html_output)
            self.assertIn(text, markdown_output)
        self.assertLess(
            html_output.index('id="benefit"'),
            html_output.index("Technical audit data (optional)"),
        )
        self.assertNotIn('<details class="machine" open>', html_output)

        learning_cards = {
            item["learning_class"]: item for item in monitor.learning["cards"]
        }
        self.assertEqual(
            learning_cards["repeated_signal_candidate"]["status"],
            "none_observed",
        )

    def test_learning_view_separates_repetition_from_human_judgment(self) -> None:
        with TemporaryDirectory() as temp_dir:
            repository = create_repository(Path(temp_dir))
            add_event(
                repository,
                task_id="same-task",
                event_type="scope.checked",
                outcome="failed",
                occurred_at="2026-08-02T01:01:00.000Z",
                reasons=("scope_failure",),
            )
            add_event(
                repository,
                task_id="same-task",
                event_type="scope.checked",
                outcome="failed",
                occurred_at="2026-08-02T01:01:20.000Z",
                reasons=("scope_failure",),
            )
            add_event(
                repository,
                task_id="validation-one",
                event_type="validation.completed",
                outcome="failed",
                occurred_at="2026-08-02T01:01:40.000Z",
                reasons=("validation_failed",),
            )
            add_event(
                repository,
                task_id="validation-two",
                event_type="validation.completed",
                outcome="failed",
                occurred_at=FIXED_TIME,
                reasons=("validation_failed",),
            )
            monitor = build_development_monitor(repository, generated_at=FIXED_TIME)
            html_output = render_development_monitor_html(monitor)
            markdown_output = render_development_monitor_markdown(monitor)
            json_output = json.loads(render_development_monitor_json(monitor))

        learning = monitor.learning
        self.assertEqual(learning["mode"], "current_observation_candidates")
        self.assertEqual(learning["scope"], "local_session")
        self.assertEqual(
            learning["recurrence_rule"],
            {
                "signal_source": "protection_type",
                "minimum_occurrences": 2,
                "requires_distinct_tasks": False,
                "generalization_allowed": False,
            },
        )
        self.assertEqual(
            [item["learning_class"] for item in learning["cards"]],
            [
                "observed_signal",
                "repeated_signal_candidate",
                "human_judgment",
                "unknown",
            ],
        )
        cards = {item["learning_class"]: item for item in learning["cards"]}
        self.assertEqual(
            cards["observed_signal"]["metrics"],
            {
                "scope_boundary": 2,
                "validation_failure": 2,
                "stale_evidence": 0,
                "incomplete_completion": 0,
            },
        )
        self.assertEqual(cards["repeated_signal_candidate"]["status"], "candidates_observed")
        self.assertEqual(cards["repeated_signal_candidate"]["semantics"], "advisory")
        candidates = cards["repeated_signal_candidate"]["candidates"]
        self.assertEqual(
            [
                {
                    key: item[key]
                    for key in ("signal_id", "occurrences", "distinct_tasks", "cross_task")
                }
                for item in candidates
            ],
            [
                {
                    "signal_id": "scope_boundary",
                    "occurrences": 2,
                    "distinct_tasks": 1,
                    "cross_task": False,
                },
                {
                    "signal_id": "validation_failure",
                    "occurrences": 2,
                    "distinct_tasks": 2,
                    "cross_task": True,
                },
            ],
        )
        self.assertTrue(
            all(re.fullmatch(r"sha256:[0-9a-f]{64}", item["candidate_digest"]) for item in candidates)
        )
        self.assertNotIn("same-task", json.dumps(json_output["learning"]))
        self.assertEqual(cards["human_judgment"]["status"], "unavailable")
        self.assertIn(
            "false_positive_disposition",
            cards["human_judgment"]["topics"],
        )
        self.assertEqual(cards["unknown"]["status"], "unknown")
        self.assertIn("return_on_investment", cards["unknown"]["topics"])
        self.assertEqual(json_output["learning"], json.loads(json.dumps(learning)))
        for text in (
            "Learning",
            "Observed protection signals",
            "Repeated signal candidates",
            "Human learning judgments",
            "Learning limits",
            "Current-observation repetition does not prove shared root cause",
        ):
            self.assertIn(text, html_output)
            self.assertIn(text, markdown_output)
        self.assertLess(html_output.index('id="benefit"'), html_output.index('id="learning"'))
        self.assertLess(
            html_output.index('id="learning"'),
            html_output.index("Technical audit data (optional)"),
        )
        self.assertNotIn('<details class="machine" open>', html_output)

    def test_learning_view_projects_only_exact_current_human_reviews(self) -> None:
        with TemporaryDirectory() as temp_dir:
            repository = create_repository(Path(temp_dir))
            add_event(
                repository,
                task_id="first-task",
                event_type="scope.checked",
                outcome="failed",
                occurred_at="2026-08-02T01:01:00.000Z",
                reasons=("scope_failure",),
            )
            add_event(
                repository,
                task_id="second-task",
                event_type="scope.checked",
                outcome="failed",
                occurred_at="2026-08-02T01:02:00.000Z",
                reasons=("scope_failure",),
            )
            review = build_learning_review(
                repository,
                signal_class="scope_boundary",
                disposition="false_positive",
                reason_codes=("owner_confirmed",),
                recorded_at="2026-08-02T01:03:00.000Z",
                review_id="lrv-" + "1" * 32,
            )
            write_learning_review(repository, review)
            monitor = build_development_monitor(repository, generated_at=FIXED_TIME)
            html_output = render_development_monitor_html(monitor)
            markdown_output = render_development_monitor_markdown(monitor)
            json_output = json.loads(render_development_monitor_json(monitor))

            add_event(
                repository,
                task_id="third-task",
                event_type="scope.checked",
                outcome="failed",
                occurred_at="2026-08-02T01:04:00.000Z",
                reasons=("scope_failure",),
            )
            stale_monitor = build_development_monitor(repository, generated_at=FIXED_TIME)

        cards = {item["learning_class"]: item for item in monitor.learning["cards"]}
        judgment = cards["human_judgment"]
        self.assertEqual(judgment["status"], "recorded")
        self.assertEqual(judgment["metrics"]["matched_reviews"], 1)
        self.assertEqual(judgment["metrics"]["false_positive"], 1)
        self.assertEqual(
            judgment["judgments"],
            (
                {
                    "signal_id": "scope_boundary",
                    "disposition": "false_positive",
                    "recorded_at": "2026-08-02T01:03:00.000Z",
                    "actor_role": "human_product_owner",
                    "semantics": "human_judgment",
                    "resolution": "unknown",
                    "reason_codes": ("owner_confirmed",),
                },
            ),
        )
        projected = json.dumps(json_output["learning"])
        self.assertNotIn("first-task", projected)
        self.assertNotIn("evt-", projected)
        for text in ("false positive", "human product owner", "resolution=unknown"):
            self.assertIn(text, html_output)
        for text in ("false_positive", "human_product_owner", "resolution=unknown"):
            self.assertIn(text, markdown_output)
        stale_card = {
            item["learning_class"]: item for item in stale_monitor.learning["cards"]
        }["human_judgment"]
        self.assertEqual(stale_card["status"], "unavailable")
        self.assertEqual(stale_monitor.learning["human_review_source"]["stale_records"], 1)

    def test_learning_review_input_fails_closed_when_local_record_is_malformed(self) -> None:
        with TemporaryDirectory() as temp_dir:
            repository = create_repository(Path(temp_dir))
            directory = repository / ".agentgov" / "learning-reviews"
            directory.mkdir(parents=True)
            (directory / ("lrv-" + "1" * 32 + ".json")).write_text(
                "{}\n", encoding="utf-8"
            )

            with self.assertRaisesRegex(MonitorPolicyError, "unexpected fields"):
                build_development_monitor(repository, generated_at=FIXED_TIME)

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
        self.assertEqual(
            monitor.learning["human_review_source"],
            {
                "availability": "unavailable",
                "source_kind": "absent_from_selected_event_source",
                "records_read": 0,
                "matched_records": 0,
                "stale_records": 0,
            },
        )
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
        self.assertEqual(
            monitor.learning["human_review_source"]["availability"], "unavailable"
        )
        self.assertEqual(
            monitor.learning["human_review_source"]["source_kind"],
            "absent_from_selected_event_source",
        )

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
            "Benefit",
            "Learning",
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
        self.assertEqual(schema["properties"]["schema_version"]["const"], "1.9")
        self.assertIn("benefit", schema["required"])
        self.assertIn("learning", schema["required"])
        benefit_schema = schema["$defs"]["benefitView"]
        self.assertFalse(benefit_schema["additionalProperties"])
        self.assertEqual(benefit_schema["properties"]["comparison_mode"]["const"], "single_observation_only")
        self.assertEqual(benefit_schema["properties"]["cards"]["minItems"], 5)
        self.assertEqual(benefit_schema["properties"]["cards"]["maxItems"], 5)
        benefit_card_schema = schema["$defs"]["benefitCard"]
        self.assertFalse(benefit_card_schema["additionalProperties"])
        self.assertEqual(len(benefit_card_schema["oneOf"]), 5)
        self.assertEqual(
            benefit_card_schema["properties"]["claim_class"]["enum"],
            [
                "observed_fact",
                "reproduced_comparison",
                "supported_inference",
                "human_feedback",
                "unknown",
            ],
        )
        learning_schema = schema["$defs"]["learningView"]
        self.assertFalse(learning_schema["additionalProperties"])
        self.assertEqual(
            learning_schema["properties"]["mode"]["const"],
            "current_observation_candidates",
        )
        recurrence = learning_schema["properties"]["recurrence_rule"]
        self.assertFalse(recurrence["additionalProperties"])
        self.assertEqual(recurrence["properties"]["minimum_occurrences"]["const"], 2)
        self.assertFalse(
            recurrence["properties"]["generalization_allowed"]["const"]
        )
        self.assertEqual(learning_schema["properties"]["cards"]["minItems"], 4)
        self.assertEqual(learning_schema["properties"]["cards"]["maxItems"], 4)
        self.assertIn("human_review_source", learning_schema["required"])
        learning_card_schema = schema["$defs"]["learningCard"]
        self.assertFalse(learning_card_schema["additionalProperties"])
        self.assertEqual(len(learning_card_schema["oneOf"]), 4)
        self.assertFalse(schema["$defs"]["learningCandidate"]["additionalProperties"])
        self.assertFalse(schema["$defs"]["learningJudgment"]["additionalProperties"])
        protection_schema = schema["$defs"]["protectionEvent"]
        self.assertIn("guidance", protection_schema["required"])
        guidance_schema = schema["$defs"]["protectionGuidance"]
        self.assertFalse(guidance_schema["additionalProperties"])
        self.assertEqual(
            guidance_schema["properties"]["target"]["enum"],
            ["task_detail", None],
        )
        self.assertEqual(
            guidance_schema["properties"]["semantics"]["const"],
            "read_only_navigation",
        )
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
