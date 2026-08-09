import contextlib
import hashlib
import io
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from agentgov.cli import EXIT_ERROR, EXIT_FAIL, EXIT_PASS, main
from agentgov.consumer_ci import (
    ConsumerCIState,
    IntegrationAction,
    IntegrationConflictError,
    STABLE_CONSUMER_VERSION,
    STABLE_CONSUMER_WHEEL_SHA256,
    WORKFLOW_PATH,
    apply_integration_plan,
    inspect_consumer_ci,
    inspect_managed_upgrade_workflow_content,
    inspect_managed_workflow_content,
    plan_github_actions_integration,
    render_consumer_workflow,
    render_consumer_upgrade_workflow,
    render_integration_plan_json,
    request_integration_confirmation,
)


ROOT = Path(__file__).resolve().parents[1]


class FakeTerminal(io.StringIO):
    def isatty(self) -> bool:
        return True


def run_cli(*args: str) -> tuple[int, str, str]:
    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        exit_code = main(list(args))
    return exit_code, stdout.getvalue(), stderr.getvalue()


class ConsumerWorkflowTests(unittest.TestCase):
    def test_workflow_is_pinned_read_only_and_project_runtime_independent(self) -> None:
        workflow = render_consumer_workflow()

        self.assertIn(f"pinned release {STABLE_CONSUMER_VERSION}", workflow)
        self.assertIn(f"releases/download/v{STABLE_CONSUMER_VERSION}/", workflow)
        self.assertIn(STABLE_CONSUMER_WHEEL_SHA256, workflow)
        self.assertIn("permissions:\n  contents: read", workflow)
        self.assertIn("persist-credentials: false", workflow)
        self.assertIn("sha256sum --check -", workflow)
        self.assertIn("python -m pip install --no-deps", workflow)
        self.assertIn("agentgov update --check . --non-interactive --format json", workflow)
        self.assertIn(
            "agentgov report repository . --format json --output agentgov-report.json",
            workflow,
        )
        self.assertIn(
            "agentgov report repository . --format markdown --output "
            "agentgov-report.md || true",
            workflow,
        )
        self.assertIn('cat agentgov-report.md >> "$GITHUB_STEP_SUMMARY"', workflow)
        self.assertNotIn("agentgov status . --format markdown", workflow)
        self.assertNotIn("agentgov-status.md", workflow)
        self.assertNotIn("agentgov review upgrade", workflow)
        self.assertNotIn("agentgov-latest-manifest.json", workflow)
        self.assertNotIn("schedule:", workflow)
        self.assertIn("if: always()", workflow)
        self.assertIn("actions/upload-artifact@b7c566a772e6b6bfb58ed0dc250532a479d7789f", workflow)
        self.assertNotIn("requirements.txt", workflow)
        self.assertNotIn("pull_request_target", workflow)
        self.assertNotIn("contents: write", workflow)
        self.assertNotIn("secrets.", workflow)
        self.assertEqual(
            hashlib.sha256(workflow.encode("utf-8")).hexdigest(),
            "9fa83b71b498b058afb2f5bdf777b23ed27933995faedc546faf4321f3974be8",
        )

    def test_workflow_rejects_untrusted_release_coordinates(self) -> None:
        with self.assertRaises(ValueError):
            render_consumer_workflow(version="not-a-version")
        with self.assertRaises(ValueError):
            render_consumer_workflow(
                version="0.2.0",
                wheel_url="https://example.invalid/agentgov.whl",
                wheel_sha256="a" * 64,
            )
        with self.assertRaises(ValueError):
            render_consumer_workflow(version="0.2.0", wheel_sha256="invalid")

    def test_missing_workflow_plans_one_create_without_writing(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            before = tuple(root.rglob("*"))
            plan = plan_github_actions_integration(root)
            after = tuple(root.rglob("*"))

        self.assertEqual(before, after)
        self.assertIs(plan.item.action, IntegrationAction.CREATE)
        self.assertEqual(plan.item.path, WORKFLOW_PATH)
        self.assertEqual(plan.item.content, render_consumer_workflow())

    def test_exact_managed_workflow_is_preserved(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            target = root / WORKFLOW_PATH
            target.parent.mkdir(parents=True)
            target.write_text(render_consumer_workflow(), encoding="utf-8")

            plan = plan_github_actions_integration(root)
            status = inspect_consumer_ci(root)

        self.assertIs(plan.item.action, IntegrationAction.PRESERVE)
        self.assertIs(status.state, ConsumerCIState.MANAGED)

    def test_newer_exact_managed_workflow_remains_managed(self) -> None:
        workflow = render_consumer_workflow(
            version="0.2.0",
            wheel_sha256="d" * 64,
        )
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            target = root / WORKFLOW_PATH
            target.parent.mkdir(parents=True)
            target.write_text(workflow, encoding="utf-8")

            plan = plan_github_actions_integration(root)
            status = inspect_consumer_ci(root)
            managed_release = inspect_managed_workflow_content(workflow)

        self.assertIs(plan.item.action, IntegrationAction.PRESERVE)
        self.assertIn("0.2.0", plan.item.reason)
        self.assertIs(status.state, ConsumerCIState.MANAGED)
        self.assertIn("0.2.0", status.message)
        self.assertIsNotNone(managed_release)
        self.assertEqual(managed_release.version, "0.2.0")

    def test_version_0_2_workflow_adds_visible_status_without_write_authority(self) -> None:
        workflow = render_consumer_workflow(
            version="0.2.1",
            wheel_sha256="d" * 64,
        )

        self.assertIn(
            "agentgov status . --format markdown --non-interactive > "
            "agentgov-status.md || true",
            workflow,
        )
        self.assertIn('cat agentgov-status.md >> "$GITHUB_STEP_SUMMARY"', workflow)
        self.assertIn("            agentgov-status.md", workflow)
        self.assertIn(
            "releases/latest/download/release-manifest.json",
            workflow,
        )
        self.assertIn(
            "agentgov update --check . --manifest agentgov-latest-manifest.json",
            workflow,
        )
        self.assertIn("agentgov review upgrade .", workflow)
        self.assertIn('schedule:\n    - cron: "0 13 * * 1-5"', workflow)
        self.assertIn(
            'wheel_path="$RUNNER_TEMP/agent_governance_starter-0.2.1-py3-none-any.whl"',
            workflow,
        )
        self.assertIn('python -m pip install --no-deps "$wheel_path"', workflow)
        self.assertNotIn("$RUNNER_TEMP/agentgov.whl", workflow)
        self.assertIn("--output agentgov-upgrade-review", workflow)
        self.assertIn(
            'cat agentgov-upgrade-review/UPGRADE_REVIEW.md >> "$GITHUB_STEP_SUMMARY"',
            workflow,
        )
        self.assertIn("            agentgov-upgrade-review", workflow)
        self.assertNotIn("contents: write", workflow)
        self.assertNotIn("actions: read", workflow)
        self.assertNotIn("agentgov benefits monitor", workflow)
        self.assertNotIn("agentgov-main-baseline", workflow)
        self.assertNotIn("publish_development_monitor", workflow)
        self.assertNotIn("agentgov-development-monitor", workflow)
        self.assertNotIn("pull_request_target", workflow)
        self.assertNotIn("gh pr", workflow)

    def test_future_version_schedule_surfaces_advisory_drift_reminder_without_failure(self) -> None:
        workflow = render_consumer_workflow(
            version="0.4.0",
            wheel_sha256="f" * 64,
        )
        published_candidate = render_consumer_workflow(
            version="0.3.0rc1",
            wheel_sha256="e" * 64,
        )

        self.assertIn("Surface scheduled AgentGov drift review reminder", workflow)
        self.assertIn("if: github.event_name == 'schedule'", workflow)
        self.assertIn("agentgov review drift . --format github", workflow)
        self.assertIn("intentionally leaves this job green", workflow)
        self.assertIn("agentgov-drift-review.md", workflow)
        self.assertNotIn("issues: write", workflow)
        self.assertNotIn("Surface scheduled AgentGov drift review reminder", published_candidate)
        self.assertNotIn("agentgov review drift", published_candidate)

    def test_version_0_3_monitor_artifact_is_explicit_source_limited_and_read_only(self) -> None:
        workflow = render_consumer_workflow(
            version="0.3.0",
            wheel_sha256="e" * 64,
        )

        self.assertIn("publish_development_monitor:", workflow)
        self.assertIn(
            'description: "Build and upload the source-limited Development Monitor"',
            workflow,
        )
        self.assertIn("type: boolean\n        default: false", workflow)
        self.assertIn("development_export:", workflow)
        self.assertIn(
            "if: github.event_name == 'workflow_dispatch' && "
            "inputs.publish_development_monitor",
            workflow,
        )
        self.assertIn("monitor_args=(--scope ci_only)", workflow)
        self.assertIn(
            'monitor_args=(--scope exported_development --export '
            '"$AGENTGOV_DEVELOPMENT_EXPORT")',
            workflow,
        )
        self.assertIn(
            'monitor_args=(--scope combined --export '
            '"$AGENTGOV_DEVELOPMENT_EXPORT")',
            workflow,
        )
        self.assertIn("find .agentgov/events", workflow)
        self.assertIn('"${monitor_args[@]}"', workflow)
        self.assertIn("--output agentgov-development-monitor.html", workflow)
        self.assertIn("name: agentgov-development-monitor", workflow)
        self.assertIn("path: agentgov-development-monitor.html", workflow)
        self.assertIn("if-no-files-found: error", workflow)
        self.assertIn(
            "if: always() && github.event_name == 'workflow_dispatch' && "
            "inputs.publish_development_monitor",
            workflow,
        )

        upload_block = workflow.split("- name: Upload opt-in Development Monitor", 1)[1]
        upload_block = upload_block.split("- name: Preserve trusted main benefit baseline", 1)[0]
        self.assertNotIn(".agentgov", upload_block)
        self.assertNotIn("development_export", upload_block)
        self.assertNotIn("events", upload_block)
        self.assertIn("permissions:\n  contents: read\n  actions: read", workflow)
        self.assertNotIn("contents: write", workflow)
        self.assertNotIn("pull-requests: write", workflow)
        self.assertNotIn("secrets.", workflow)
        self.assertNotIn("pull_request_target", workflow)

    def test_version_0_3_limits_draft_pr_writes_to_schedule_or_opt_in_dispatch(self) -> None:
        governance_workflow = render_consumer_workflow(
            version="0.3.0",
            wheel_sha256="e" * 64,
        )
        upgrade_workflow = render_consumer_upgrade_workflow(
            version="0.3.0",
            wheel_sha256="e" * 64,
        )
        workflow = governance_workflow + "\n" + upgrade_workflow

        self.assertIn("create_upgrade_pr:", workflow)
        self.assertIn("default: false", workflow)
        self.assertIn("propose-agentgov-upgrade:", workflow)
        self.assertIn(
            "if: always() && (github.event_name == 'schedule' || "
            "(github.event_name == 'workflow_dispatch' && inputs.create_upgrade_pr))",
            workflow,
        )
        self.assertIn("needs: governance", workflow)
        self.assertIn("contents: write", workflow)
        self.assertIn("pull-requests: write", workflow)
        self.assertIn("actions: read", workflow)
        self.assertIn("persist-credentials: false", workflow)
        self.assertIn("agentgov create upgrade-pr .", workflow)
        self.assertIn('--event "$GITHUB_EVENT_NAME"', workflow)
        self.assertIn("GH_TOKEN: ${{ github.token }}", workflow)
        self.assertIn("Restore previous trusted AgentGov main baseline", workflow)
        self.assertIn("actions/workflows/agentgov.yml/runs?branch=", workflow)
        self.assertIn('select(.event == "push" or .event == "schedule"', workflow)
        self.assertIn('select(.name == "agentgov-main-baseline")', workflow)
        self.assertIn("agentgov benefits monitor agentgov-report.json \\", workflow)
        self.assertIn('"${baseline_args[@]}" \\', workflow)
        self.assertIn("agentgov-benefit-monitor/BENEFIT_MONITOR.md", workflow)
        self.assertIn("agentgov-benefit-monitor/benefit-monitor.json", workflow)
        self.assertIn("retention-days: 90", workflow)
        self.assertIn("agentgov benefits observe-upgrade", workflow)
        self.assertIn('started_epoch="$(date +%s)"', workflow)
        self.assertIn("agentgov-upgrade-observation", workflow)
        self.assertIn("agentgov-benefit-monitor/PR_REVIEW.md", workflow)
        self.assertIn("agentgov benefits annotate agentgov-report.json", workflow)
        self.assertIn("Enforce deterministic governance failures", workflow)
        self.assertIn("surface-governance-regression:", workflow)
        self.assertIn("Push regression through the workflow conclusion", workflow)
        self.assertIn("github.event_name != 'pull_request'", workflow)
        self.assertIn("GitHub can deliver its normal Actions failure notification", workflow)
        self.assertIn("Run current and proposed versions before writing a Draft PR", workflow)
        self.assertIn("agentgov check release-manifest", workflow)
        self.assertIn('--current-report "$RUNNER_TEMP/agentgov-current-report.json"', workflow)
        self.assertIn('--target-report "$RUNNER_TEMP/agentgov-target-report.json"', workflow)
        self.assertIn('github.event_name != \'pull_request\'', workflow)
        self.assertIn("retention-days: 90", workflow)
        self.assertNotIn("contents: write", governance_workflow)
        self.assertNotIn("pull-requests: write", governance_workflow)
        self.assertNotIn("propose-agentgov-upgrade:", governance_workflow)
        self.assertNotIn("pull_request:", upgrade_workflow)
        self.assertNotIn("push:", upgrade_workflow)
        self.assertIn("contents: write", upgrade_workflow)
        self.assertIn("pull-requests: write", upgrade_workflow)
        self.assertNotIn("issues: write", workflow)
        self.assertIsNotNone(inspect_managed_upgrade_workflow_content(upgrade_workflow))
        self.assertIsNone(
            inspect_managed_upgrade_workflow_content(
                upgrade_workflow.replace("default: false", "default: true")
            )
        )
        self.assertNotIn("pull_request_target", workflow)
        self.assertNotIn("gh pr merge", workflow)

    def test_modified_generated_workflow_is_not_managed(self) -> None:
        workflow = render_consumer_workflow().replace(
            "permissions:\n  contents: read",
            "permissions:\n  contents: write",
        )

        self.assertIsNone(inspect_managed_workflow_content(workflow))

    def test_existing_different_target_is_conflict_and_not_overwritten(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            target = root / WORKFLOW_PATH
            target.parent.mkdir(parents=True)
            target.write_text("human workflow\n", encoding="utf-8")

            plan = plan_github_actions_integration(root)
            with self.assertRaises(IntegrationConflictError):
                apply_integration_plan(plan)
            content = target.read_text(encoding="utf-8")

        self.assertTrue(plan.has_conflict)
        self.assertEqual(content, "human workflow\n")

    def test_custom_workflow_invocation_is_visible_without_claiming_managed(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            target = root / ".github/workflows/custom.yml"
            target.parent.mkdir(parents=True)
            target.write_text(
                "name: custom\njobs:\n  check:\n    steps:\n"
                "      - run: agentgov check repository .\n",
                encoding="utf-8",
            )

            status = inspect_consumer_ci(root)

        self.assertIs(status.state, ConsumerCIState.CUSTOM)
        self.assertEqual(status.workflow_paths, (Path(".github/workflows/custom.yml"),))

    def test_json_preview_denies_write_and_runtime_authority(self) -> None:
        with TemporaryDirectory() as temp_dir:
            plan = plan_github_actions_integration(Path(temp_dir))
            payload = json.loads(
                render_integration_plan_json(plan, non_interactive=True)
            )

        self.assertEqual(payload["mode"], "dry_run")
        self.assertEqual(payload["interaction"], "non_interactive")
        self.assertFalse(payload["authority_boundary"]["write_authorized"])
        self.assertFalse(
            payload["authority_boundary"]["runs_project_or_production_workflows"]
        )

    def test_confirmation_requires_exact_interactive_integrate(self) -> None:
        with TemporaryDirectory() as temp_dir:
            plan = plan_github_actions_integration(Path(temp_dir))

        self.assertTrue(
            request_integration_confirmation(
                plan,
                decision_reader=lambda _: "INTEGRATE",
                is_interactive_terminal=True,
            )
        )
        self.assertFalse(
            request_integration_confirmation(
                plan,
                decision_reader=lambda _: "integrate",
                is_interactive_terminal=True,
            )
        )
        self.assertFalse(
            request_integration_confirmation(
                plan,
                decision_reader=lambda _: "INTEGRATE",
                is_interactive_terminal=False,
            )
        )

    def test_apply_revalidates_target_before_exclusive_create(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            plan = plan_github_actions_integration(root)
            target = root / WORKFLOW_PATH
            target.parent.mkdir(parents=True)
            target.write_text("appeared\n", encoding="utf-8")

            with self.assertRaises(IntegrationConflictError):
                apply_integration_plan(plan)

            self.assertEqual(target.read_text(encoding="utf-8"), "appeared\n")


class ConsumerCICommandTests(unittest.TestCase):
    def test_dry_run_shows_exact_workflow_without_writing(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            exit_code, stdout, stderr = run_cli(
                "integrate", "github-actions", temp_dir, "--dry-run"
            )

        self.assertEqual(exit_code, EXIT_PASS)
        self.assertIn("CREATE .github/workflows/agentgov.yml", stdout)
        self.assertIn("SUMMARY CREATE=1 PRESERVE=0 CONFLICT=0", stdout)
        self.assertIn("does not authorize a later write", stdout)
        self.assertEqual(stderr, "")
        self.assertFalse((root / WORKFLOW_PATH).exists())

    def test_non_interactive_apply_is_rejected(self) -> None:
        with TemporaryDirectory() as temp_dir:
            exit_code, stdout, stderr = run_cli(
                "integrate",
                "github-actions",
                temp_dir,
                "--non-interactive",
            )

        self.assertEqual(exit_code, EXIT_ERROR)
        self.assertEqual(stdout, "")
        self.assertIn("never authorizes writes", stderr)

    def test_redirected_confirmation_cancels_without_writing(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            with patch("sys.stdin", io.StringIO("INTEGRATE\n")):
                exit_code, stdout, stderr = run_cli(
                    "integrate", "github-actions", temp_dir
                )

        self.assertEqual(exit_code, EXIT_PASS)
        self.assertIn("CANCELLED integrate", stdout)
        self.assertEqual(stderr, "")
        self.assertFalse((root / WORKFLOW_PATH).exists())

    def test_exact_confirmation_creates_only_managed_workflow(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            with patch("sys.stdin", FakeTerminal("INTEGRATE\n")):
                exit_code, stdout, stderr = run_cli(
                    "integrate", "github-actions", temp_dir
                )
            files = tuple(path.relative_to(root) for path in root.rglob("*") if path.is_file())

        self.assertEqual(exit_code, EXIT_PASS)
        self.assertEqual(files, (WORKFLOW_PATH,))
        self.assertIn("PASS integrate: created 1 managed workflow file(s)", stdout)
        self.assertIn("production workflows were not run", stdout)
        self.assertEqual(stderr, "")

    def test_conflict_returns_policy_failure(self) -> None:
        with TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / WORKFLOW_PATH
            target.parent.mkdir(parents=True)
            target.write_text("human workflow\n", encoding="utf-8")
            exit_code, stdout, stderr = run_cli(
                "integrate", "github-actions", temp_dir, "--dry-run"
            )

        self.assertEqual(exit_code, EXIT_FAIL)
        self.assertIn("CONFLICT .github/workflows/agentgov.yml", stdout)
        self.assertEqual(stderr, "")

    def test_schema_is_strict_and_denies_authority(self) -> None:
        schema = json.loads(
            (ROOT / "schemas/ci-integration-plan.schema.json").read_text(
                encoding="utf-8"
            )
        )

        self.assertFalse(schema["additionalProperties"])
        authority = schema["properties"]["authority_boundary"]
        self.assertFalse(authority["additionalProperties"])
        for property_schema in authority["properties"].values():
            self.assertIs(property_schema["const"], False)


if __name__ == "__main__":
    unittest.main()
