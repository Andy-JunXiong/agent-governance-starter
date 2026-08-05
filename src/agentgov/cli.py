"""Command-line interface for Agent Governance Starter Kit."""

from __future__ import annotations

import argparse
import json
import os
import secrets
import subprocess
import sys
from tempfile import TemporaryDirectory
from pathlib import Path
from typing import Sequence

from agentgov import __version__
from agentgov.adoption import (
    AdoptionConflictError,
    AdoptionState,
    adopt_existing_repository,
    inspect_adoption,
    render_adoption_report_json,
)
from agentgov.agent_skills import check_agent_skills
from agentgov.artifacts import (
    ArtifactConflictError,
    ArtifactPolicyError,
    check_capability_artifact,
    export_capability_artifact,
)
from agentgov.benefits import compare_repository_reports, render_benefit_comparison_json
from agentgov.benefit_monitor import (
    BenefitMonitorConflictError,
    build_benefit_monitor,
    build_upgrade_observation,
    render_github_annotations,
    write_benefit_monitor_bundle,
    write_upgrade_observation_bundle,
)
from agentgov.capability import load_capability_manifest, validate_capability_manifest
from agentgov.consumer_ci import (
    ConsumerCIState,
    IntegrationAction,
    IntegrationConflictError,
    apply_integration_plan,
    inspect_consumer_ci,
    plan_github_actions_integration,
    render_integration_plan_json,
    request_integration_confirmation,
)
from agentgov.change_scope import (
    GitInspectionError,
    ScopeFindingStatus,
    ScopePolicyError,
    check_development_scope,
    render_scope_report_json,
    render_scope_report_markdown,
    render_scope_report_terminal,
)
from agentgov.doctor import (
    DoctorStatus,
    diagnose_repository,
    render_doctor_report_json,
)
from agentgov.development_context import (
    ContextPolicyError,
    render_development_context_json,
    render_development_context_markdown,
    render_development_context_terminal,
    select_development_context,
)
from agentgov.development_evidence import (
    EvidenceError,
    reconcile_task_completion,
    render_completion_json,
    render_completion_markdown,
    render_completion_terminal,
    run_task_validation,
)
from agentgov.development_event_export import (
    DevelopmentExportPolicyError,
    build_development_event_export,
    development_export_default_output,
    render_development_event_export_preview,
    request_development_export_confirmation,
    write_development_event_export,
)
from agentgov.development_handoff import (
    HandoffPolicyError,
    apply_handoff_plan,
    build_handoff_plan,
    render_handoff_plan_json,
    render_handoff_plan_terminal,
    request_handoff_confirmation,
)
from agentgov.development_monitor import (
    MonitorPolicyError,
    build_development_monitor,
    write_development_monitor,
)
from agentgov.development_session import (
    SessionPolicyError,
    apply_start_plan,
    build_start_plan,
    render_start_plan_json,
    render_start_plan_terminal,
    request_start_confirmation,
    resolve_active_task,
)
from agentgov.event_store import LocalStateError, append_governance_event
from agentgov.foreground_coordinator import (
    CoordinatorPolicyError,
    render_foreground_cycle_json,
    render_foreground_cycle_terminal,
    run_foreground_cycle,
)
from agentgov.git_snapshot import GitSnapshotError
from agentgov.initializer import InitConflictError, initialize_project
from agentgov.onboarding import (
    OnboardingConflictError,
    apply_onboarding_plan,
    plan_onboarding,
    render_onboarding_plan_json,
    request_onboarding_confirmation,
)
from agentgov.next_action import render_next_action_json, select_next_action
from agentgov.html_reporting import render_repository_report_html
from agentgov.evaluation import EvaluationStatus, check_evaluation_bundle
from agentgov.repository import FindingStatus, check_repository
from agentgov.references import (
    ReferencePolicyError,
    ReferenceStatus,
    check_capability_references,
)
from agentgov.refresh import (
    RefreshAction,
    RefreshConflictError,
    apply_refresh_plan,
    plan_refresh,
    render_refresh_plan_json,
    request_refresh_confirmation,
)
from agentgov.reference_adapter import build_reference_trigger
from agentgov.release_metadata import (
    load_release_manifest,
    validate_release_manifest,
)
from agentgov.reporting import (
    ReportConflictError,
    render_repository_report,
    render_repository_report_json,
    write_report,
)
from agentgov.release_review import (
    ReleaseReviewConflictError,
    ReleaseReviewError,
    create_release_review_bundle,
)
from agentgov.software_update import (
    SoftwareUpdateError,
    download_release_manifest,
    download_verified_wheel,
    install_wheel_with_pipx,
    relaunch_updated_agentgov,
)
from agentgov.status import (
    inspect_governance_status,
    render_status_json,
    render_status_markdown,
)
from agentgov.task_contract import (
    TaskFindingStatus,
    check_development_task,
)
from agentgov.development_trigger import TRIGGER_TYPES, TriggerContractError
from agentgov.update_check import (
    check_for_updates,
    render_update_check_json,
    request_update_confirmation,
)
from agentgov.upgrade_pr import (
    UpgradePlanState,
    plan_upgrade_pull_request,
    render_upgrade_pull_request_plan_json,
)
from agentgov.upgrade_review import (
    UpgradeReviewConflictError,
    UpgradeReviewError,
    create_upgrade_review_bundle,
)
from agentgov.upgrade_writer import (
    GitHubApiClient,
    GitHubApiError,
    UpgradeWriteConflictError,
    create_upgrade_draft_pull_request,
    render_upgrade_write_result_json,
)


EXIT_PASS = 0
EXIT_FAIL = 1
EXIT_ERROR = 2


def _review_release(
    source: Path,
    *,
    wheel: Path,
    manifest: Path,
    consumer: Path,
    output: Path,
) -> int:
    try:
        result = create_release_review_bundle(
            source,
            wheel=wheel,
            manifest_path=manifest,
            consumer=consumer,
            output=output,
        )
    except ReleaseReviewConflictError as exc:
        print(f"FAIL review release: {exc}")
        return EXIT_FAIL
    except ReleaseReviewError as exc:
        print(f"ERROR review release: {exc}", file=sys.stderr)
        return EXIT_ERROR
    except (OSError, UnicodeError) as exc:
        print(f"ERROR review release: cannot create review bundle: {exc}", file=sys.stderr)
        return EXIT_ERROR

    print(f"CREATE review-bundle: {result.output}")
    print(f"STATE {result.state}")
    for gate in result.gates:
        print(f"GATE {gate['id']}: {gate['status']} - {gate['detail']}")
    print("DECISION pending: approve, request_changes, or reject")
    print("NOTE review release: source and consumer repositories were not modified")
    print("NOTE review release: no Git, tag, push, publish, release, or deploy action was run")
    return EXIT_FAIL if result.blocked else EXIT_PASS


def _review_upgrade(
    repository: Path,
    *,
    manifest: Path,
    output: Path,
) -> int:
    try:
        result = create_upgrade_review_bundle(
            repository,
            manifest_path=manifest,
            output=output,
        )
    except UpgradeReviewConflictError as exc:
        print(f"FAIL review upgrade: {exc}")
        return EXIT_FAIL
    except UpgradeReviewError as exc:
        print(f"ERROR review upgrade: {exc}", file=sys.stderr)
        return EXIT_ERROR
    except (OSError, UnicodeError) as exc:
        print(f"ERROR review upgrade: cannot create review bundle: {exc}", file=sys.stderr)
        return EXIT_ERROR

    print(f"CREATE upgrade-review: {result.output}")
    print(f"STATE {result.state}")
    for gate in result.gates:
        print(f"GATE {gate['id']}: {gate['status']} - {gate['detail']}")
    print("DECISION pending: approve, request_changes, or reject")
    print("NOTE review upgrade: the planned consumer workflow change was not applied")
    print("NOTE review upgrade: no branch, pull request, merge, release, or deploy action was run")
    return EXIT_FAIL if result.blocked else EXIT_PASS


def _compare_benefit_reports(
    before: Path,
    after: Path,
    *,
    output_format: str,
) -> int:
    try:
        comparison = compare_repository_reports(before, after)
    except FileNotFoundError as exc:
        print(f"ERROR benefits compare: report not found: {exc.filename or exc}", file=sys.stderr)
        return EXIT_ERROR
    except (OSError, UnicodeError, ValueError, TypeError, json.JSONDecodeError) as exc:
        print(f"ERROR benefits compare: {exc}", file=sys.stderr)
        return EXIT_ERROR

    if output_format == "json":
        print(render_benefit_comparison_json(comparison), end="")
    else:
        print(f"TARGET benefits: {comparison.repository}")
        print(
            "DENOMINATOR "
            f"before={comparison.before_finding_count} "
            f"after={comparison.after_finding_count} "
            f"matched={comparison.matched_check_count}"
        )
        print(
            "EVIDENCE "
            f"failures_resolved={len(comparison.deterministic_failures_resolved)} "
            f"failures_introduced={len(comparison.deterministic_failures_introduced)} "
            f"non_passing_cleared={len(comparison.non_passing_findings_cleared)} "
            f"added_checks={len(comparison.added_checks)} "
            f"removed_checks={len(comparison.removed_checks)}"
        )
        for transition in comparison.transitions:
            print(
                f"TRANSITION {transition.check_id}: "
                f"{transition.before}->{transition.after}"
            )
        print("LIMIT benefits: two snapshots do not prove causality or prevented incidents")
        print("LIMIT benefits: project tests and runtime outcomes were not observed")
        print("NOTE benefits: no repository, Git, merge, release, or deploy action was run")
    return EXIT_PASS


def _monitor_benefits(
    report: Path,
    *,
    baseline_report: Path | None,
    baseline_monitor: Path | None,
    repository: str,
    ref: str,
    commit_sha: str,
    run_id: int,
    run_attempt: int,
    event: str,
    observed_at: str,
    output: Path,
) -> int:
    try:
        monitor = build_benefit_monitor(
            report,
            repository=repository,
            ref=ref,
            commit_sha=commit_sha,
            run_id=run_id,
            run_attempt=run_attempt,
            event=event,
            observed_at=observed_at,
            baseline_report=baseline_report,
            baseline_monitor=baseline_monitor,
        )
        write_benefit_monitor_bundle(output, monitor)
    except BenefitMonitorConflictError as exc:
        print(f"FAIL benefits monitor: {exc}")
        return EXIT_FAIL
    except FileNotFoundError as exc:
        print(
            f"ERROR benefits monitor: path not found: {exc.filename or exc}",
            file=sys.stderr,
        )
        return EXIT_ERROR
    except (OSError, UnicodeError, ValueError, TypeError, json.JSONDecodeError) as exc:
        print(f"ERROR benefits monitor: {exc}", file=sys.stderr)
        return EXIT_ERROR

    print(f"CREATE benefit-monitor: {output.resolve()}")
    print(f"STATE {monitor.state.value}")
    print(f"HISTORY points={len(monitor.history)}")
    print(
        "BASELINE "
        + (f"run_id={monitor.baseline.run_id}" if monitor.baseline else "missing")
    )
    print("LIMIT benefits monitor: observed changes do not prove causality or ROI")
    print("NOTE benefits monitor: no governed repository, Git, merge, release, or deploy action was run")
    return EXIT_PASS


def _annotate_benefits(report: Path) -> int:
    try:
        print(render_github_annotations(report), end="")
    except FileNotFoundError as exc:
        print(
            f"ERROR benefits annotate: path not found: {exc.filename or exc}",
            file=sys.stderr,
        )
        return EXIT_ERROR
    except (OSError, UnicodeError, ValueError, TypeError, json.JSONDecodeError) as exc:
        print(f"ERROR benefits annotate: {exc}", file=sys.stderr)
        return EXIT_ERROR
    return EXIT_PASS


def _observe_upgrade_benefit(
    result: Path,
    *,
    repository: str,
    commit_sha: str,
    run_id: int,
    started_epoch: int,
    completed_epoch: int,
    output: Path,
) -> int:
    try:
        observation = build_upgrade_observation(
            result,
            repository=repository,
            commit_sha=commit_sha,
            run_id=run_id,
            started_epoch=started_epoch,
            completed_epoch=completed_epoch,
        )
        write_upgrade_observation_bundle(output, observation)
    except BenefitMonitorConflictError as exc:
        print(f"FAIL benefits observe-upgrade: {exc}")
        return EXIT_FAIL
    except FileNotFoundError as exc:
        print(
            f"ERROR benefits observe-upgrade: path not found: {exc.filename or exc}",
            file=sys.stderr,
        )
        return EXIT_ERROR
    except (OSError, UnicodeError, ValueError, TypeError, json.JSONDecodeError) as exc:
        print(f"ERROR benefits observe-upgrade: {exc}", file=sys.stderr)
        return EXIT_ERROR

    print(f"CREATE upgrade-observation: {output.resolve()}")
    print(f"STATE {observation.state}")
    print(
        "METRIC detection_to_draft_pr_seconds="
        f"{observation.detection_to_draft_pr_seconds}"
    )
    print(
        "METRIC mechanical_bridge_actions_observed="
        f"{observation.mechanical_bridge_actions_observed}"
    )
    print("LIMIT upgrade observation: workflow time is not labor saved or ROI")
    return EXIT_PASS


def _plan_upgrade_pr(
    path: Path,
    *,
    manifest: Path,
    output_format: str,
) -> int:
    try:
        plan = plan_upgrade_pull_request(path, manifest_path=manifest)
    except FileNotFoundError as exc:
        print(f"ERROR plan upgrade-pr: path not found: {exc.filename or exc}", file=sys.stderr)
        return EXIT_ERROR
    except (OSError, UnicodeError, ValueError, TypeError, json.JSONDecodeError) as exc:
        print(f"ERROR plan upgrade-pr: {exc}", file=sys.stderr)
        return EXIT_ERROR

    if output_format == "json":
        print(render_upgrade_pull_request_plan_json(plan), end="")
    else:
        print(f"TARGET upgrade-pr: {plan.root}")
        print(f"STATE {plan.state.value}")
        print(
            f"VERSION current={plan.current_version} available={plan.available_version}"
        )
        for reason in plan.reasons:
            print(f"REASON {reason}")
        if plan.branch:
            print(f"BRANCH {plan.branch}")
        if plan.title:
            print(f"TITLE {plan.title}")
        for change in plan.changes:
            before = change.before_sha256 or "absent"
            print(
                f"CHANGE {change.action} {change.path.as_posix()} "
                f"before={before} after={change.after_sha256}"
            )
        print(
            "NOTE upgrade-pr plan: no repository file, Git branch, pull request, "
            "merge, release, or deploy action was run"
        )
    return EXIT_FAIL if plan.state is UpgradePlanState.BLOCKED else EXIT_PASS


def _create_upgrade_pr(
    path: Path,
    *,
    manifest: Path,
    repository: str,
    base_branch: str,
    event_source: str,
    current_report: Path | None,
    target_report: Path | None,
    token_env: str,
    output_format: str,
) -> int:
    token = os.environ.get(token_env, "")
    if not token:
        print(
            f"ERROR create upgrade-pr: environment variable {token_env} is not set",
            file=sys.stderr,
        )
        return EXIT_ERROR
    try:
        client = GitHubApiClient(repository, token=token)
        result = create_upgrade_draft_pull_request(
            path,
            manifest_path=manifest,
            repository=repository,
            base_branch=base_branch,
            event_source=event_source,
            client=client,
            current_report_path=current_report,
            target_report_path=target_report,
        )
    except UpgradeWriteConflictError as exc:
        print(f"FAIL create upgrade-pr: {exc}")
        return EXIT_FAIL
    except FileNotFoundError as exc:
        print(
            f"ERROR create upgrade-pr: path not found: {exc.filename or exc}",
            file=sys.stderr,
        )
        return EXIT_ERROR
    except (
        GitHubApiError,
        OSError,
        UnicodeError,
        ValueError,
        TypeError,
        json.JSONDecodeError,
    ) as exc:
        print(f"ERROR create upgrade-pr: {exc}", file=sys.stderr)
        return EXIT_ERROR

    if output_format == "json":
        print(render_upgrade_write_result_json(result), end="")
    else:
        print(f"TARGET upgrade-pr: {result.repository}@{result.base_branch}")
        print(f"STATE {result.state.value}")
        print(
            f"VERSION current={result.current_version} "
            f"available={result.available_version}"
        )
        if result.branch:
            print(f"BRANCH {result.branch}")
        if result.pull_request:
            print(
                f"PULL_REQUEST #{result.pull_request.number} "
                f"draft={str(result.pull_request.draft).lower()} "
                f"url={result.pull_request.url}"
            )
        print(
            "ACTIONS "
            f"branch_created={str(result.branch_created).lower()} "
            f"workflow_commit_created={str(result.workflow_commit_created).lower()} "
            f"pull_request_created={str(result.pull_request_created).lower()}"
        )
        print(
            "NOTE create upgrade-pr: write scope is limited to "
            "the two declared AgentGov workflow paths on an AgentGov branch"
        )
        print(
            "NOTE create upgrade-pr: merge, release, deploy, and production execution "
            "remain unauthorized"
        )
    return EXIT_PASS


def _integrate_github_actions(
    path: Path,
    *,
    dry_run: bool,
    output_format: str,
    non_interactive: bool,
) -> int:
    if not dry_run and non_interactive:
        print(
            "ERROR integrate: --non-interactive never authorizes writes; add --dry-run",
            file=sys.stderr,
        )
        return EXIT_ERROR
    if not dry_run and output_format == "json":
        print(
            "ERROR integrate: interactive apply requires text output",
            file=sys.stderr,
        )
        return EXIT_ERROR
    try:
        plan = plan_github_actions_integration(path)
    except FileNotFoundError:
        print(f"ERROR integrate: repository path not found: {path}", file=sys.stderr)
        return EXIT_ERROR
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"ERROR integrate: cannot prepare GitHub Actions plan: {exc}", file=sys.stderr)
        return EXIT_ERROR

    if output_format == "json":
        print(
            render_integration_plan_json(
                plan,
                non_interactive=non_interactive,
            ),
            end="",
        )
    else:
        print(f"TARGET integrate: {plan.root}")
        print("INTEGRATION github-actions")
        print(
            f"{plan.item.action.value} {plan.item.path.as_posix()}: "
            f"{plan.item.reason}"
        )
        if plan.item.content is not None:
            print("CONTENT")
            print(plan.item.content, end="")
        print(
            "SUMMARY "
            + " ".join(
                f"{action.value}={int(plan.item.action is action)}"
                for action in IntegrationAction
            )
        )
        if dry_run:
            print("NOTE integrate dry-run: no repository files or Git state were modified")
            print("NOTE integrate dry-run: this preview does not authorize a later write")

    if plan.has_conflict:
        return EXIT_FAIL
    if dry_run or plan.item.action is IntegrationAction.PRESERVE:
        return EXIT_PASS
    try:
        confirmed = request_integration_confirmation(
            plan,
            decision_reader=input,
            is_interactive_terminal=sys.stdin.isatty(),
        )
    except EOFError:
        confirmed = False
    if not confirmed:
        print(
            "CANCELLED integrate: exact interactive INTEGRATE confirmation was not received"
        )
        print("NOTE integrate: no repository files or Git state were modified")
        return EXIT_PASS
    try:
        result = apply_integration_plan(plan)
    except IntegrationConflictError as exc:
        print(f"FAIL integrate: {exc}")
        return EXIT_FAIL
    except (OSError, UnicodeError) as exc:
        print(f"ERROR integrate: cannot create workflow: {exc}", file=sys.stderr)
        return EXIT_ERROR
    for created in result.created_files:
        print(f"CREATE {created.as_posix()}")
    status = inspect_consumer_ci(result.root)
    if status.state is not ConsumerCIState.MANAGED:
        print(f"FAIL integrate: post-write status is {status.state.value}")
        return EXIT_FAIL
    print(f"PASS integrate: created {len(result.created_files)} managed workflow file(s)")
    print("NOTE integrate: project dependencies and production workflows were not run")
    print("NOTE integrate: no Git, merge, publish, release, or deploy action is authorized")
    return EXIT_PASS


def _status_repository(
    path: Path,
    *,
    output_format: str,
    non_interactive: bool,
) -> int:
    try:
        status = inspect_governance_status(path)
    except FileNotFoundError:
        print(f"ERROR status: repository path not found: {path}", file=sys.stderr)
        return EXIT_ERROR
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR status: cannot inspect {path}: {exc}", file=sys.stderr)
        return EXIT_ERROR

    if output_format == "json":
        print(render_status_json(status, non_interactive=non_interactive), end="")
    elif output_format == "markdown":
        print(render_status_markdown(status), end="")
    else:
        print(f"TARGET status: {status.root}")
        layout = status.layout_version or ("invalid" if status.layout_error else "unversioned")
        print(
            f"ADOPTION configured={'yes' if status.adopted else 'no'} layout={layout}"
        )
        if status.layout_error:
            print(f"FAIL repository-contract: {status.layout_error}")
        paths = ",".join(path.as_posix() for path in status.ci.workflow_paths) or "none"
        print(f"CI state={status.ci.state.value} workflows={paths}")
        print(f"CI_DETAIL {status.ci.message}")
        for capability in status.capabilities:
            print(
                f"CAPABILITY {capability.name}: owner={capability.owner} "
                f"risk={capability.risk_level} readiness={capability.readiness}"
            )
            print(f"PURPOSE {capability.name}: {capability.purpose}")
            for caller in capability.called_by:
                print(f"USED_BY {capability.name}: {caller}")
        if not status.capabilities:
            print("CAPABILITY none: no readable capability manifest was discovered")
        for surface in status.surfaces:
            print(
                f"SURFACE {surface.name}: state={surface.state} "
                f"detail={surface.explanation}"
            )
        report = status.repository_report
        print(
            "SUMMARY "
            + " ".join(
                f"{finding_status.value}={report.count(finding_status)}"
                for finding_status in FindingStatus
            )
        )
        if status.ci.state is ConsumerCIState.MISSING:
            print(
                f'NEXT status: agentgov integrate github-actions "{status.root}" --dry-run'
            )
        else:
            print(f"NEXT status: {status.next_action.title}")
            if status.next_action.command:
                print(f"COMMAND {status.next_action.command}")
        print("NOTE status: visibility does not prove governance sufficiency")
        print("NOTE status: no repository, Git, release, deploy, or production action was run")
    return EXIT_FAIL if status.has_failures else EXIT_PASS


def _update_check(
    path: Path,
    *,
    manifest: Path | None,
    output_format: str,
) -> int:
    try:
        report = check_for_updates(path, manifest_path=manifest)
    except FileNotFoundError as exc:
        print(f"ERROR update: path not found: {exc.filename or exc}", file=sys.stderr)
        return EXIT_ERROR
    except json.JSONDecodeError as exc:
        print(
            f"ERROR update: invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}",
            file=sys.stderr,
        )
        return EXIT_ERROR
    except (TypeError, ValueError) as exc:
        print(f"ERROR update: {exc}", file=sys.stderr)
        return EXIT_ERROR
    except (OSError, UnicodeError) as exc:
        print(f"ERROR update: cannot inspect update state: {exc}", file=sys.stderr)
        return EXIT_ERROR

    if output_format == "json":
        print(render_update_check_json(report), end="")
    else:
        print(f"TARGET update: {report.repository}")
        print(
            f"TOOL installed={report.installed_version} "
            f"available={report.available_version} "
            f"update={'yes' if report.tool_update_available else 'no'}"
        )
        print(
            f"RUNTIME environment={report.environment} "
            f"executable={report.executable}"
        )
        print(
            "SHADOWING project-venv="
            f"{'yes' if report.shadowed_by_project_venv else 'no'}"
        )
        print(
            f"REPOSITORY contract={report.repository_layout or 'unversioned'} "
            f"target={report.target_layout} "
            f"readable={'yes' if report.readable else 'no'} "
            f"refresh={'yes' if report.repository_refresh_required else 'no'}"
        )
        print(
            f"RELEASE channel={report.channel} manifest={report.manifest_source}"
        )
        print("NOTE update check: no tool was installed or updated")
        print("NOTE update check: no repository files or Git state were modified")
    return EXIT_PASS if report.readable else EXIT_FAIL


def _update_repository(
    path: Path,
    *,
    check_only: bool,
    manifest: Path | None,
    output_format: str,
    non_interactive: bool,
    resume_after_tool_update: str | None,
) -> int:
    if resume_after_tool_update is not None and (
        not secrets.compare_digest(
            resume_after_tool_update,
            os.environ.get("AGENTGOV_UPDATE_RESUME_TOKEN", ""),
        )
    ):
        print("ERROR UPDATE_RESUME: invalid internal continuation token", file=sys.stderr)
        return EXIT_ERROR
    if manifest is None:
        if output_format == "text":
            print("[0/6] DISCOVER latest stable release")
        try:
            with TemporaryDirectory() as temp_dir:
                downloaded_manifest = Path(temp_dir) / "release-manifest.json"
                download_release_manifest(downloaded_manifest)
                return _update_repository(
                    path,
                    check_only=check_only,
                    manifest=downloaded_manifest,
                    output_format=output_format,
                    non_interactive=non_interactive,
                    resume_after_tool_update=resume_after_tool_update,
                )
        except SoftwareUpdateError as exc:
            print(f"ERROR UPDATE_NETWORK: {exc}", file=sys.stderr)
            print("RECOVERY agentgov update .")
            return EXIT_ERROR
    if not check_only and non_interactive:
        print(
            "ERROR update: --non-interactive never authorizes writes; add --check",
            file=sys.stderr,
        )
        return EXIT_ERROR
    if not check_only and output_format == "json":
        print(
            "ERROR update: interactive apply requires text output; add --check",
            file=sys.stderr,
        )
        return EXIT_ERROR
    if check_only:
        return _update_check(path, manifest=manifest, output_format=output_format)

    print("[1/4] CHECK tool and repository compatibility")
    try:
        update = check_for_updates(path, manifest_path=manifest)
        print("[2/4] PLAN exact repository changes")
        plan = plan_refresh(path, manifest_path=manifest)
    except KeyboardInterrupt:
        print("\nINTERRUPTED UPDATE_INTERRUPTED: stopped before repository writes")
        print("RECOVERY agentgov update .")
        return EXIT_ERROR
    except FileNotFoundError as exc:
        print(
            f"ERROR UPDATE_PATH: path not found: {exc.filename or exc}",
            file=sys.stderr,
        )
        return EXIT_ERROR
    except json.JSONDecodeError as exc:
        print(
            f"ERROR UPDATE_JSON: invalid JSON at line {exc.lineno}, "
            f"column {exc.colno}: {exc.msg}",
            file=sys.stderr,
        )
        return EXIT_ERROR
    except (TypeError, ValueError) as exc:
        print(f"ERROR UPDATE_CONTRACT: {exc}", file=sys.stderr)
        return EXIT_ERROR
    except (OSError, UnicodeError) as exc:
        print(f"ERROR UPDATE_IO: cannot prepare update: {exc}", file=sys.stderr)
        return EXIT_ERROR

    print(f"TARGET update: {update.repository}")
    print(
        f"TOOL installed={update.installed_version} "
        f"available={update.available_version} "
        f"update={'yes' if update.tool_update_available else 'no'}"
    )
    print(
        f"REPOSITORY contract={update.repository_layout or 'unversioned'} "
        f"target={update.target_layout} "
        f"refresh={'yes' if update.repository_refresh_required else 'no'}"
    )
    for item in plan.items:
        print(f"{item.action.value} {item.path.as_posix()}: {item.reason}")
        if item.content is not None:
            print("CONTENT")
            print(item.content, end="")
    print(
        "SUMMARY "
        + " ".join(
            f"{action.value}={plan.count(action)}"
            for action in RefreshAction
        )
    )

    if update.tool_update_available and update.artifact is None:
        print("BLOCKED UPDATE_INSTALL_SOURCE: stable artifact metadata is missing")
        print("NOTE update: no tool or repository files were modified")
        return EXIT_FAIL
    if not update.readable or plan.has_conflicts:
        print(
            "BLOCKED UPDATE_CONFLICT: resolve the reported repository "
            "compatibility conflict"
        )
        print("NOTE update: no repository files were modified")
        print("RECOVERY agentgov refresh . --dry-run")
        return EXIT_FAIL
    create_count = plan.count(RefreshAction.CREATE)
    change_count = create_count + int(update.tool_update_available)
    if change_count == 0:
        print("SUCCESS UPDATE_CURRENT: tool and repository contract are current")
        return EXIT_PASS

    if resume_after_tool_update is None:
        try:
            confirmed = request_update_confirmation(
                repository=update.repository,
                change_count=change_count,
                decision_reader=input,
                is_interactive_terminal=sys.stdin.isatty(),
            )
        except KeyboardInterrupt:
            print("\nINTERRUPTED UPDATE_INTERRUPTED: confirmation stopped before writes")
            print("NOTE update: no tool, repository files, or Git state were modified")
            print("RECOVERY agentgov update .")
            return EXIT_ERROR
        except EOFError:
            confirmed = False
        if not confirmed:
            print(
                "CANCELLED UPDATE_NOT_CONFIRMED: exact interactive UPDATE "
                "confirmation was not received"
            )
            print("NOTE update: no tool, repository files, or Git state were modified")
            print("RECOVERY agentgov update .")
            return EXIT_PASS

    if update.tool_update_available:
        assert update.artifact is not None
        print("[3/6] DOWNLOAD stable AgentGov wheel")
        try:
            with TemporaryDirectory() as temp_dir:
                wheel = Path(temp_dir) / update.artifact["filename"]
                download_verified_wheel(update.artifact, wheel)
                print("[4/6] VERIFY SHA-256 matched release manifest")
                print("[5/6] INSTALL verified wheel with pipx")
                executable = install_wheel_with_pipx(
                    wheel,
                    expected_version=update.available_version,
                )
                print("[6/6] RELAUNCH updated AgentGov")
                token = secrets.token_urlsafe(32)
                return relaunch_updated_agentgov(
                    executable,
                    repository=update.repository,
                    manifest=update.manifest_source,
                    resume_token=token,
                )
        except SoftwareUpdateError as exc:
            print(f"ERROR UPDATE_INSTALL: {exc}", file=sys.stderr)
            print("RECOVERY agentgov update .")
            return EXIT_ERROR

    print("[3/4] APPLY reviewed repository changes")
    try:
        result = apply_refresh_plan(plan)
    except KeyboardInterrupt:
        created = tuple(
            item.path
            for item in plan.items
            if item.action is RefreshAction.CREATE
            and (plan.update.repository / item.path).is_file()
        )
        if created:
            print("\nPARTIAL UPDATE_INTERRUPTED: interrupted after repository write")
            for created_path in created:
                print(f"CREATED {created_path.as_posix()}")
            print(f'RECOVERY agentgov check repository "{plan.update.repository}"')
        else:
            print("\nINTERRUPTED UPDATE_INTERRUPTED: stopped before repository writes")
            print("RECOVERY agentgov update .")
        return EXIT_ERROR
    except RefreshConflictError as exc:
        print(f"BLOCKED UPDATE_RACE: {exc}")
        print("RECOVERY agentgov update --check .")
        return EXIT_FAIL
    except (OSError, UnicodeError) as exc:
        print(
            f"ERROR UPDATE_WRITE: cannot apply repository refresh: {exc}",
            file=sys.stderr,
        )
        print(f'RECOVERY agentgov check repository "{plan.update.repository}"')
        return EXIT_ERROR

    for created in result.created_files:
        print(f"CREATE {created.as_posix()}")
    print(f"APPLIED update: {len(result.created_files)} repository change(s)")
    print("[4/4] VALIDATE final tool and repository state")
    try:
        update_exit = _update_check(
            result.root,
            manifest=manifest,
            output_format="text",
        )
        repository_exit = _check_repository(result.root)
    except KeyboardInterrupt:
        print("\nPARTIAL UPDATE_INTERRUPTED: repository changed; validation interrupted")
        for created in result.created_files:
            print(f"CREATED {created.as_posix()}")
        print(f'RECOVERY agentgov check repository "{result.root}"')
        return EXIT_ERROR
    print("NOTE update: no Git, merge, publish, release, or deploy action is authorized")
    final_exit = max(update_exit, repository_exit)
    if final_exit != EXIT_PASS:
        print("PARTIAL UPDATE_VALIDATION: repository changed; final validation did not pass")
        for created in result.created_files:
            print(f"CREATED {created.as_posix()}")
        print(f'RECOVERY agentgov check repository "{result.root}"')
        return final_exit
    print("SUCCESS UPDATE_COMPLETE: tool and repository contract are current")
    return EXIT_PASS


def _refresh_repository(
    path: Path,
    *,
    dry_run: bool,
    manifest: Path | None,
    output_format: str,
    non_interactive: bool,
) -> int:
    if not dry_run and non_interactive:
        print(
            "ERROR refresh: --non-interactive never authorizes writes; add --dry-run",
            file=sys.stderr,
        )
        return EXIT_ERROR
    if not dry_run and output_format == "json":
        print(
            "ERROR refresh: interactive apply requires text output",
            file=sys.stderr,
        )
        return EXIT_ERROR
    try:
        plan = plan_refresh(path, manifest_path=manifest)
    except FileNotFoundError as exc:
        print(f"ERROR refresh: path not found: {exc.filename or exc}", file=sys.stderr)
        return EXIT_ERROR
    except json.JSONDecodeError as exc:
        print(
            f"ERROR refresh: invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}",
            file=sys.stderr,
        )
        return EXIT_ERROR
    except (TypeError, ValueError) as exc:
        print(f"ERROR refresh: {exc}", file=sys.stderr)
        return EXIT_ERROR
    except (OSError, UnicodeError) as exc:
        print(f"ERROR refresh: cannot prepare plan: {exc}", file=sys.stderr)
        return EXIT_ERROR

    if output_format == "json":
        print(render_refresh_plan_json(plan), end="")
    else:
        print(f"TARGET refresh: {plan.update.repository}")
        print(f"LAYOUT current={plan.update.repository_layout or 'unversioned'} "
              f"target={plan.update.target_layout}")
        for item in plan.items:
            print(f"{item.action.value} {item.path.as_posix()}: {item.reason}")
            if item.content is not None:
                print("CONTENT")
                print(item.content, end="")
        print(
            "SUMMARY "
            + " ".join(
                f"{action.value}={plan.count(action)}"
                for action in RefreshAction
            )
        )
        if dry_run:
            print("NOTE refresh dry-run: no repository files or Git state were modified")
            print("NOTE refresh dry-run: this preview does not authorize a later write")
    if plan.has_conflicts:
        return EXIT_FAIL
    if dry_run:
        return EXIT_PASS
    if plan.count(RefreshAction.CREATE) == 0:
        print("PASS refresh: repository contract already matches the target layout")
        return EXIT_PASS

    try:
        confirmed = request_refresh_confirmation(
            plan,
            decision_reader=input,
            is_interactive_terminal=sys.stdin.isatty(),
        )
    except EOFError:
        confirmed = False
    if not confirmed:
        print("CANCELLED refresh: exact interactive REFRESH confirmation was not received")
        print("NOTE refresh: no repository files or Git state were modified")
        return EXIT_PASS

    try:
        result = apply_refresh_plan(plan)
    except RefreshConflictError as exc:
        print(f"FAIL refresh: {exc}")
        return EXIT_FAIL
    except (OSError, UnicodeError) as exc:
        print(f"ERROR refresh: cannot apply plan: {exc}", file=sys.stderr)
        return EXIT_ERROR

    for created in result.created_files:
        print(f"CREATE {created.as_posix()}")
    print(f"PASS refresh: created {len(result.created_files)} deterministic file(s)")
    print("CHECK refresh: verifying update and repository state")
    update_exit = _update_check(
        result.root,
        manifest=manifest,
        output_format="text",
    )
    repository_exit = _check_repository(result.root)
    print("NOTE refresh: no Git, merge, publish, release, or deploy action is authorized")
    return max(update_exit, repository_exit)


def _next_repository(
    path: Path,
    *,
    output_format: str,
    non_interactive: bool,
) -> int:
    try:
        action = select_next_action(path)
    except FileNotFoundError:
        print(f"ERROR next: repository path not found: {path}", file=sys.stderr)
        return EXIT_ERROR
    except ValueError as exc:
        print(f"ERROR next: {exc}", file=sys.stderr)
        return EXIT_ERROR
    except (OSError, UnicodeError) as exc:
        print(f"ERROR next: cannot inspect {path}: {exc}", file=sys.stderr)
        return EXIT_ERROR

    if output_format == "json":
        print(
            render_next_action_json(
                action,
                non_interactive=non_interactive,
            ),
            end="",
        )
    else:
        print(f"TARGET next: {action.root}")
        print(f"ACTION {action.kind.value}: {action.title}")
        if action.source_check_id is not None:
            print(f"SOURCE {action.source_check_id}")
        print(f"REASON {action.reason}")
        if action.command is not None:
            print(f"COMMAND {action.command}")
        print(f"BLOCKING {'yes' if action.blocking else 'no'}")
        print("NOTE next: this command selected but did not execute the action")
        print("NOTE next: no Git, merge, publish, release, or deploy action is authorized")
    return EXIT_FAIL if action.blocking else EXIT_PASS


def _onboard_repository(
    path: Path,
    *,
    project_name: str,
    dry_run: bool,
    output_format: str,
    non_interactive: bool,
) -> int:
    if not dry_run and non_interactive:
        print(
            "ERROR onboard: --non-interactive never authorizes writes; "
            "add --dry-run",
            file=sys.stderr,
        )
        return EXIT_ERROR
    if not dry_run and output_format == "json":
        print(
            "ERROR onboard: interactive adoption requires text output",
            file=sys.stderr,
        )
        return EXIT_ERROR

    try:
        plan = plan_onboarding(path, project_name=project_name)
    except FileNotFoundError:
        print(f"ERROR onboard: repository path not found: {path}", file=sys.stderr)
        return EXIT_ERROR
    except AdoptionConflictError as exc:
        print(f"FAIL onboard: {exc}")
        print("NOTE onboard dry-run: no repository files were created or modified")
        return EXIT_FAIL
    except ValueError as exc:
        print(f"ERROR onboard: {exc}", file=sys.stderr)
        return EXIT_ERROR
    except (OSError, UnicodeError) as exc:
        print(f"ERROR onboard: cannot prepare preview: {exc}", file=sys.stderr)
        return EXIT_ERROR

    if output_format == "json":
        print(
            render_onboarding_plan_json(
                plan,
                non_interactive=non_interactive,
            ),
            end="",
        )
    else:
        print(f"TARGET onboard: {plan.root}")
        for finding in plan.diagnosis.findings:
            print(f"{finding.status.value} {finding.check_id}: {finding.message}")
        for generated_file in plan.adoption.planned_files:
            print(f"PLAN {generated_file.relative_path.as_posix()}")
        for relative_path in plan.adoption.preserved_files:
            print(f"PRESERVE {relative_path.as_posix()}")
        print(
            f"SUMMARY CREATE={len(plan.adoption.planned_files)} "
            f"PRESERVE={len(plan.adoption.preserved_files)}"
        )
        if dry_run:
            print("NEXT onboard: review the exact target and every planned file")
            print(
                "NOTE onboard dry-run: no repository files, project environments, "
                "or Git state were modified"
            )
            print("NOTE onboard dry-run: this preview does not authorize a later write")

    if plan.diagnosis.has_failures:
        return EXIT_FAIL
    if dry_run:
        return EXIT_PASS
    if not plan.adoption.planned_files:
        print("PASS onboard: no missing scaffold files require creation")
        print("NEXT onboard: run `agentgov check repository`")
        return EXIT_PASS

    try:
        confirmed = request_onboarding_confirmation(
            plan,
            decision_reader=input,
            is_interactive_terminal=sys.stdin.isatty(),
        )
    except EOFError:
        confirmed = False
    if not confirmed:
        print("CANCELLED onboard: explicit terminal confirmation was not received")
        print("NOTE onboard: no repository files were created or modified")
        return EXIT_PASS

    try:
        result = apply_onboarding_plan(plan)
    except OnboardingConflictError as exc:
        print(f"FAIL onboard: {exc}")
        return EXIT_FAIL
    except (OSError, UnicodeError) as exc:
        print(f"ERROR onboard: cannot create reviewed files: {exc}", file=sys.stderr)
        return EXIT_ERROR

    for relative_path in result.created_files:
        print(f"CREATE {relative_path.as_posix()}")
    print(
        f"PASS onboard: created {len(result.created_files)} reviewed file(s); "
        f"preserved {len(result.preserved_files)} existing file(s)"
    )
    print("NOTE onboard: adoption does not authorize Git, merge, publish, release, or deploy")
    print("CHECK onboard: running the first read-only repository check")
    check_exit = _check_repository(result.root)
    print("NEXT onboard: run `agentgov next` to select one smallest useful action")
    return check_exit


def _doctor_repository(
    path: Path,
    *,
    output_format: str,
    non_interactive: bool,
) -> int:
    try:
        report = diagnose_repository(path)
    except FileNotFoundError:
        print(f"ERROR doctor: repository path not found: {path}", file=sys.stderr)
        return EXIT_ERROR
    except ValueError as exc:
        print(f"ERROR doctor: {exc}", file=sys.stderr)
        return EXIT_ERROR
    except OSError as exc:
        print(f"ERROR doctor: cannot diagnose {path}: {exc}", file=sys.stderr)
        return EXIT_ERROR

    if output_format == "json":
        print(
            render_doctor_report_json(
                report,
                non_interactive=non_interactive,
            ),
            end="",
        )
    else:
        print(f"TARGET doctor: {report.root}")
        print(
            f"RUNTIME doctor: Python {report.python_version} at "
            f"{report.python_executable}"
        )
        for finding in report.findings:
            print(f"{finding.status.value} {finding.check_id}: {finding.message}")
        summary = " ".join(
            f"{status.value}={report.count(status)}" for status in DoctorStatus
        )
        print(f"SUMMARY {summary}")
        print("NOTE doctor: no repository files or project environments were modified")
    return EXIT_FAIL if report.has_failures else EXIT_PASS


def _adopt_repository(
    path: Path,
    *,
    project_name: str,
    dry_run: bool,
) -> int:
    try:
        report = adopt_existing_repository(
            path,
            project_name=project_name,
            dry_run=dry_run,
        )
    except FileNotFoundError:
        print(f"ERROR adopt: repository path not found: {path}", file=sys.stderr)
        return EXIT_ERROR
    except AdoptionConflictError as exc:
        print(f"FAIL adopt: {exc}")
        return EXIT_FAIL
    except ValueError as exc:
        print(f"ERROR adopt: {exc}", file=sys.stderr)
        return EXIT_ERROR
    except (OSError, UnicodeError) as exc:
        print(f"ERROR adopt: cannot prepare scaffold: {exc}", file=sys.stderr)
        return EXIT_ERROR

    action = "PLAN" if dry_run else "CREATE"
    for generated_file in report.planned_files:
        print(f"{action} {generated_file.relative_path.as_posix()}")
    for relative_path in report.preserved_files:
        print(f"PRESERVE {relative_path.as_posix()}")
    print(
        f"SUMMARY CREATE={len(report.planned_files)} "
        f"PRESERVE={len(report.preserved_files)}"
    )
    if dry_run:
        print("NOTE adopt dry-run: no repository files were created or modified")
        print("NEXT adopt dry-run: review the plan, then rerun without --dry-run")
    else:
        print("NEXT adopt: review every created file and resolve governance placeholders")
        print(f"NEXT adopt: run `agentgov check repository \"{path}\"`")
    print("NOTE adopt: adoption does not authorize merge, publish, release, or deploy")
    return EXIT_PASS


def _inspect_repository(path: Path, *, output_format: str) -> int:
    try:
        report = inspect_adoption(path)
    except FileNotFoundError:
        print(f"ERROR inspect: repository path not found: {path}", file=sys.stderr)
        return EXIT_ERROR
    except ValueError as exc:
        print(f"ERROR inspect: {exc}", file=sys.stderr)
        return EXIT_ERROR
    except OSError as exc:
        print(f"ERROR inspect: cannot inspect {path}: {exc}", file=sys.stderr)
        return EXIT_ERROR

    if output_format == "json":
        print(render_adoption_report_json(report), end="")
    else:
        for item in report.items:
            print(f"{item.state.value} {item.check_id}: {item.message}")
        summary = " ".join(
            f"{state.value}={report.count(state)}" for state in AdoptionState
        )
        print(f"SUMMARY {summary}")
        for recommendation in report.recommendations:
            print(f"NEXT inspect: {recommendation}")
        print("NOTE inspect: no repository files were created or modified")
    return EXIT_FAIL if report.has_conflicts else EXIT_PASS


def _check_capability(path: Path) -> int:
    try:
        manifest = load_capability_manifest(path)
    except FileNotFoundError:
        print(f"ERROR capability: file not found: {path}", file=sys.stderr)
        return EXIT_ERROR
    except PermissionError:
        print(f"ERROR capability: permission denied: {path}", file=sys.stderr)
        return EXIT_ERROR
    except UnicodeError as exc:
        print(f"ERROR capability: file is not valid UTF-8: {path}: {exc}", file=sys.stderr)
        return EXIT_ERROR
    except json.JSONDecodeError as exc:
        print(
            f"ERROR capability: invalid JSON: {path}:{exc.lineno}:{exc.colno}: {exc.msg}",
            file=sys.stderr,
        )
        return EXIT_ERROR
    except ValueError as exc:
        print(f"ERROR capability: {path}: {exc}", file=sys.stderr)
        return EXIT_ERROR
    except OSError as exc:
        print(f"ERROR capability: cannot read {path}: {exc}", file=sys.stderr)
        return EXIT_ERROR

    errors = validate_capability_manifest(manifest)
    if errors:
        print(f"FAIL capability: {path}")
        for error in errors:
            print(f"  - {error}")
        return EXIT_FAIL

    print(f"PASS capability: {path}")
    return EXIT_PASS


def _check_task(path: Path, *, repository: Path) -> int:
    try:
        report = check_development_task(path, repository=repository)
    except FileNotFoundError as exc:
        print(
            f"ERROR task: file or repository not found: {exc.filename or exc}",
            file=sys.stderr,
        )
        return EXIT_ERROR
    except PermissionError as exc:
        print(f"ERROR task: permission denied: {exc.filename or exc}", file=sys.stderr)
        return EXIT_ERROR
    except json.JSONDecodeError as exc:
        print(
            f"ERROR task: invalid JSON: {path}:{exc.lineno}:{exc.colno}: {exc.msg}",
            file=sys.stderr,
        )
        return EXIT_ERROR
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"ERROR task: {exc}", file=sys.stderr)
        return EXIT_ERROR

    for finding in report.findings:
        print(f"{finding.status.value} {finding.check_id}: {finding.message}")
    summary = " ".join(
        f"{status.value}={report.count(status)}" for status in TaskFindingStatus
    )
    print(f"SUMMARY {summary}")
    print("NOTE task: validation was read-only and did not authorize implementation")
    return EXIT_FAIL if report.has_failures else EXIT_PASS


def _context_task(
    path: Path,
    *,
    repository: Path,
    context_format: str,
    include_content: bool,
) -> int:
    try:
        context = select_development_context(path, repository=repository)
    except ContextPolicyError as exc:
        print(f"FAIL context task: {exc}")
        return EXIT_FAIL
    except FileNotFoundError as exc:
        print(
            f"ERROR context task: file or repository not found: {exc.filename or exc}",
            file=sys.stderr,
        )
        return EXIT_ERROR
    except PermissionError as exc:
        print(
            f"ERROR context task: permission denied: {exc.filename or exc}",
            file=sys.stderr,
        )
        return EXIT_ERROR
    except json.JSONDecodeError as exc:
        print(
            f"ERROR context task: invalid JSON at line {exc.lineno}, "
            f"column {exc.colno}: {exc.msg}",
            file=sys.stderr,
        )
        return EXIT_ERROR
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"ERROR context task: {exc}", file=sys.stderr)
        return EXIT_ERROR

    if context_format == "terminal":
        rendered = render_development_context_terminal(context)
    elif context_format == "json":
        rendered = render_development_context_json(
            context,
            include_content=include_content,
        )
    else:
        rendered = render_development_context_markdown(
            context,
            include_content=include_content,
        )
    print(rendered, end="")
    return EXIT_PASS


def _check_scope(
    path: Path,
    *,
    repository: Path,
    scope_format: str,
) -> int:
    try:
        report = check_development_scope(path, repository=repository)
    except ScopePolicyError as exc:
        print(f"FAIL scope: {exc}")
        return EXIT_FAIL
    except FileNotFoundError as exc:
        print(
            f"ERROR scope: file, repository, or Git executable not found: {exc.filename or exc}",
            file=sys.stderr,
        )
        return EXIT_ERROR
    except PermissionError as exc:
        print(f"ERROR scope: permission denied: {exc.filename or exc}", file=sys.stderr)
        return EXIT_ERROR
    except json.JSONDecodeError as exc:
        print(
            f"ERROR scope: invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}",
            file=sys.stderr,
        )
        return EXIT_ERROR
    except (GitInspectionError, OSError, UnicodeError, ValueError) as exc:
        print(f"ERROR scope: {exc}", file=sys.stderr)
        return EXIT_ERROR

    renderer = {
        "terminal": render_scope_report_terminal,
        "json": render_scope_report_json,
        "markdown": render_scope_report_markdown,
    }[scope_format]
    print(renderer(report), end="")
    return EXIT_FAIL if report.has_failures else EXIT_PASS


def _dev_foreground(
    repository: Path,
    *,
    trigger_type: str,
    actor_class: str,
    correlation_id: str | None,
    validation_outcome: str | None,
    evidence_ref: Path | None,
    scope_decision: str | None,
    review_outcome: str | None,
    dashboard_output: Path,
    output_format: str,
) -> int:
    """Run one explicit foreground adapter/coordinator cycle."""

    try:
        trigger = build_reference_trigger(
            repository,
            trigger_type=trigger_type,
            actor_class=actor_class,
            correlation_id=correlation_id,
            validation_outcome=validation_outcome,
            evidence_ref=evidence_ref.as_posix() if evidence_ref is not None else None,
            scope_decision=scope_decision,
            review_outcome=review_outcome,
        )
        cycle = run_foreground_cycle(
            repository,
            trigger=trigger,
            dashboard_output=dashboard_output,
        )
    except FileNotFoundError as exc:
        print(f"ERROR dev: file or executable not found: {exc.filename or exc}", file=sys.stderr)
        return EXIT_ERROR
    except subprocess.TimeoutExpired as exc:
        print(f"ERROR dev: validation timed out after {exc.timeout} seconds", file=sys.stderr)
        return EXIT_ERROR
    except (
        CoordinatorPolicyError,
        TriggerContractError,
        ScopePolicyError,
        GitInspectionError,
        EvidenceError,
        GitSnapshotError,
        HandoffPolicyError,
        MonitorPolicyError,
        LocalStateError,
        SessionPolicyError,
        OSError,
        UnicodeError,
        ValueError,
    ) as exc:
        print(f"ERROR dev: {exc}", file=sys.stderr)
        return EXIT_ERROR
    renderer = {
        "terminal": render_foreground_cycle_terminal,
        "json": render_foreground_cycle_json,
    }[output_format]
    print(renderer(cycle), end="")
    return EXIT_FAIL if cycle.status == "blocked" else EXIT_PASS


def _govern_start(
    repository: Path,
    *,
    task: Path | None,
    title: str | None,
    task_id: str | None,
    requirement: str | None,
    include_paths: Sequence[str],
    exclude_paths: Sequence[str],
    validation_commands: Sequence[str],
    owner: str,
    comparison_base: str,
    actor_label: str | None,
    replace_active: bool,
    dry_run: bool,
    output_format: str,
) -> int:
    """Preview and explicitly confirm one bounded development session."""

    if output_format == "json" and not dry_run:
        print("ERROR govern start: --format json requires --dry-run", file=sys.stderr)
        return EXIT_ERROR
    try:
        plan = build_start_plan(
            repository,
            task=task,
            title=title,
            task_id=task_id,
            requirement=requirement,
            include_paths=include_paths,
            exclude_paths=exclude_paths,
            validation_commands=validation_commands,
            owner=owner,
            comparison_base=comparison_base,
            actor_label=actor_label,
            replace_active=replace_active,
        )
    except FileNotFoundError as exc:
        print(f"ERROR govern start: file or executable not found: {exc.filename or exc}", file=sys.stderr)
        return EXIT_ERROR
    except (
        ContextPolicyError,
        GitSnapshotError,
        LocalStateError,
        SessionPolicyError,
        OSError,
        UnicodeError,
        ValueError,
    ) as exc:
        print(f"ERROR govern start: {exc}", file=sys.stderr)
        return EXIT_ERROR

    renderer = render_start_plan_json if output_format == "json" else render_start_plan_terminal
    print(renderer(plan), end="")
    if dry_run:
        if output_format == "terminal":
            print("DRY_RUN no files were written")
        return EXIT_PASS
    if plan.already_active:
        print(f"ACTIVE {plan.session.task_id} ({plan.session.task_path})")
        print("NOTE no files were written because the exact task and comparison base are already active")
        return EXIT_PASS
    confirmed = request_start_confirmation(
        plan,
        decision_reader=input,
        is_interactive_terminal=sys.stdin.isatty(),
    )
    if not confirmed:
        print("CANCELLED govern start requires exact confirmation from an interactive terminal")
        return EXIT_FAIL
    try:
        result = apply_start_plan(plan)
    except FileNotFoundError as exc:
        print(f"ERROR govern start: file or executable not found: {exc.filename or exc}", file=sys.stderr)
        return EXIT_ERROR
    except (
        ContextPolicyError,
        GitSnapshotError,
        LocalStateError,
        SessionPolicyError,
        OSError,
        UnicodeError,
        ValueError,
    ) as exc:
        print(f"ERROR govern start: {exc}", file=sys.stderr)
        return EXIT_ERROR
    print(f"STARTED {result.session.task_id} ({result.session.task_path})")
    print(f"SELECTED_GOVERNANCE {len(result.context.selected_governance)}")
    for artifact in result.context.selected_governance:
        print(f"  - {artifact.path} [{artifact.selection_mode}]")
    if result.event_ref:
        print(f"EVENT {result.event_ref}")
    print("NEXT develop within the admitted scope, then run 'agentgov govern check' and 'agentgov govern finish'")
    print("NOTE start does not authorize code change, exception, commit, merge, deployment, or release")
    return EXIT_PASS


def _govern_check(
    path: Path | None,
    *,
    repository: Path,
    output_format: str,
    actor_class: str,
    actor_label: str | None,
) -> int:
    """Observe one development scope check and append a bounded local event."""

    try:
        active_session = None
        if path is None:
            path, active_session = resolve_active_task(repository)
        report = check_development_scope(path, repository=repository)
        _, event_ref = append_governance_event(
            repository,
            event_type="scope.checked",
            actor_class=actor_class,
            actor_label=actor_label,
            task_id=report.task_id,
            task_digest=report.task_digest,
            outcome="failed" if report.has_failures else "passed",
            evidence_ref=None,
            reason_codes=tuple(
                code
                for code in (
                    "active_session_used" if active_session is not None else "explicit_check_requested",
                    "scope_failure" if report.has_failures else None,
                )
                if code is not None
            ),
            metrics={
                "changes": len(report.changes),
                "failures": report.count(ScopeFindingStatus.FAIL),
                "advisories": report.count(ScopeFindingStatus.ADVISORY),
            },
        )
    except ScopePolicyError as exc:
        print(f"FAIL govern check: {exc}")
        return EXIT_FAIL
    except FileNotFoundError as exc:
        print(f"ERROR govern check: file or executable not found: {exc.filename or exc}", file=sys.stderr)
        return EXIT_ERROR
    except (GitInspectionError, LocalStateError, SessionPolicyError, OSError, UnicodeError, ValueError) as exc:
        print(f"ERROR govern check: {exc}", file=sys.stderr)
        return EXIT_ERROR
    renderer = {
        "terminal": render_scope_report_terminal,
        "json": render_scope_report_json,
        "markdown": render_scope_report_markdown,
    }[output_format]
    print(renderer(report), end="")
    if output_format == "terminal":
        print(f"EVENT {event_ref}")
    return EXIT_FAIL if report.has_failures else EXIT_PASS


def _govern_finish(
    path: Path | None,
    *,
    repository: Path,
    comparison_base: str | None,
    evidence: Path | None,
    output_format: str,
    actor_class: str,
    actor_label: str | None,
) -> int:
    """Optionally validate, then reconcile completion against exact evidence."""

    try:
        active_session = None
        if path is None:
            path, active_session = resolve_active_task(repository)
            if comparison_base is None and evidence is None:
                comparison_base = active_session.comparison_base_sha
        selected_evidence = evidence
        validation_run = None
        if comparison_base is not None:
            validation_run = run_task_validation(
                path,
                repository=repository,
                comparison_base=comparison_base,
                actor_class=actor_class,
                actor_label=actor_label,
            )
            selected_evidence = Path(validation_run.evidence_ref)
        report = reconcile_task_completion(
            path,
            repository=repository,
            evidence_path=selected_evidence,
            actor_class=actor_class,
            actor_label=actor_label,
        )
    except FileNotFoundError as exc:
        print(f"ERROR govern finish: file or executable not found: {exc.filename or exc}", file=sys.stderr)
        return EXIT_ERROR
    except subprocess.TimeoutExpired as exc:
        print(f"ERROR govern finish: validation timed out after {exc.timeout} seconds", file=sys.stderr)
        return EXIT_ERROR
    except (EvidenceError, GitSnapshotError, LocalStateError, SessionPolicyError, OSError, UnicodeError, ValueError) as exc:
        print(f"ERROR govern finish: {exc}", file=sys.stderr)
        return EXIT_ERROR
    if validation_run is not None:
        for command, (stdout, stderr) in zip(validation_run.evidence.commands, validation_run.transient_outputs):
            if command.exit_code != 0:
                if stdout:
                    print(stdout, end="" if stdout.endswith("\n") else "\n", file=sys.stderr)
                if stderr:
                    print(stderr, end="" if stderr.endswith("\n") else "\n", file=sys.stderr)
    renderer = {
        "terminal": render_completion_terminal,
        "json": render_completion_json,
        "markdown": render_completion_markdown,
    }[output_format]
    print(renderer(report), end="")
    return EXIT_PASS if report.state == "verified" else EXIT_FAIL


def _govern_handoff(
    repository: Path,
    *,
    actor_label: str | None,
    dry_run: bool,
    output_format: str,
) -> int:
    """Preview and explicitly confirm one append-only verified-session handoff."""

    if output_format == "json" and not dry_run:
        print("ERROR govern handoff: --format json requires --dry-run", file=sys.stderr)
        return EXIT_ERROR
    try:
        plan = build_handoff_plan(repository, actor_label=actor_label)
    except FileNotFoundError as exc:
        print(f"ERROR govern handoff: file or executable not found: {exc.filename or exc}", file=sys.stderr)
        return EXIT_ERROR
    except (
        EvidenceError,
        GitSnapshotError,
        HandoffPolicyError,
        LocalStateError,
        SessionPolicyError,
        OSError,
        UnicodeError,
        ValueError,
    ) as exc:
        print(f"ERROR govern handoff: {exc}", file=sys.stderr)
        return EXIT_ERROR

    renderer = render_handoff_plan_json if output_format == "json" else render_handoff_plan_terminal
    print(renderer(plan), end="")
    if dry_run:
        if output_format == "terminal":
            print("DRY_RUN no files were written")
        return EXIT_PASS
    if plan.already_handed_off:
        assert plan.existing_event_ref is not None
        print(f"HANDED_OFF {plan.session.task_id}")
        print(f"EVENT {plan.existing_event_ref}")
        print("NOTE no files were written because this exact session is already handed off")
        return EXIT_PASS
    confirmed = request_handoff_confirmation(
        plan,
        decision_reader=input,
        is_interactive_terminal=sys.stdin.isatty(),
    )
    if not confirmed:
        print("CANCELLED govern handoff requires exact HANDOFF from an interactive terminal")
        return EXIT_FAIL
    try:
        result = apply_handoff_plan(plan)
    except (HandoffPolicyError, LocalStateError, SessionPolicyError, OSError, UnicodeError, ValueError) as exc:
        print(f"ERROR govern handoff: {exc}", file=sys.stderr)
        return EXIT_ERROR
    print(f"HANDED_OFF {result.session.task_id}")
    print(f"EVENT {result.event_ref}")
    if result.already_handed_off:
        print("NOTE no new event was written because a matching handoff already exists")
    print("NEXT run 'agentgov next' to preview a separate governed task rollover")
    print("NOTE handoff ends routing responsibility only; it grants no approval or Git/release authority")
    return EXIT_PASS


def _monitor_development(
    repository: Path,
    *,
    observation_scope: str,
    event_directory: Path | None,
    export_path: Path | None,
    output_format: str,
    output: Path | None,
) -> int:
    try:
        monitor = build_development_monitor(
            repository,
            observation_scope=observation_scope,
            event_directory=event_directory,
            export_path=export_path,
        )
        if output is None:
            suffix = {"html": "html", "json": "json", "markdown": "md"}[output_format]
            output = Path(f".agentgov/dashboard.{suffix}")
        written = write_development_monitor(
            repository,
            monitor=monitor,
            output=output,
            output_format=output_format,
        )
        relative = written.relative_to(repository.resolve()).as_posix()
    except FileNotFoundError as exc:
        print(f"ERROR monitor development: file or executable not found: {exc.filename or exc}", file=sys.stderr)
        return EXIT_ERROR
    except (LocalStateError, MonitorPolicyError, OSError, UnicodeError, ValueError) as exc:
        print(f"ERROR monitor development: {exc}", file=sys.stderr)
        return EXIT_ERROR
    print(
        f"MONITOR scope={monitor.observation['scope']} "
        f"events={monitor.observation['event_count']} tasks={monitor.overview['tasks']}"
    )
    print(f"OUTPUT {relative}")
    print("NOTE observed counts are partial history, not approval, causality, ROI, or semantic correctness")
    if observation_scope == "local_session" and event_directory is None and export_path is None:
        try:
            handoff = build_handoff_plan(repository)
        except (
            EvidenceError,
            GitSnapshotError,
            HandoffPolicyError,
            LocalStateError,
            SessionPolicyError,
            OSError,
            UnicodeError,
            ValueError,
        ):
            handoff = None
        if handoff is not None and not handoff.already_handed_off:
            print(f'NEXT agentgov govern handoff --repository "{repository.resolve()}" --dry-run')
            print("NOTE Monitor generation does not prove review and does not append the handoff event")
    return EXIT_PASS


def _export_development_events(
    repository: Path,
    *,
    event_directory: Path | None,
    output: Path | None,
    dry_run: bool,
) -> int:
    try:
        bundle = build_development_event_export(
            repository,
            event_directory=event_directory,
        )
        selected_output = output or development_export_default_output(bundle)
        print(render_development_event_export_preview(bundle, output=selected_output), end="")
        if dry_run:
            print("DRY_RUN no export file was written")
            return EXIT_PASS
        try:
            confirmed = request_development_export_confirmation(
                decision_reader=input,
                is_interactive_terminal=sys.stdin.isatty(),
            )
        except EOFError:
            confirmed = False
        if not confirmed:
            print("CANCELLED export development requires exact EXPORT confirmation from an interactive terminal")
            print("NOTE no export file was written")
            return EXIT_PASS
        written = write_development_event_export(
            repository,
            bundle=bundle,
            output=selected_output,
        )
        relative = written.relative_to(repository.resolve()).as_posix()
    except FileNotFoundError as exc:
        print(f"ERROR export development: path not found: {exc.filename or exc}", file=sys.stderr)
        return EXIT_ERROR
    except (DevelopmentExportPolicyError, LocalStateError, OSError, UnicodeError, ValueError) as exc:
        print(f"ERROR export development: {exc}", file=sys.stderr)
        return EXIT_ERROR
    print(f"EXPORT {relative}")
    print(
        f"PASS export development: {bundle.source['event_count']} redacted events; "
        "history remains partial"
    )
    return EXIT_PASS


def _check_release_manifest(path: Path) -> int:
    try:
        document = load_release_manifest(path)
    except FileNotFoundError:
        print(f"ERROR release-manifest: file not found: {path}", file=sys.stderr)
        return EXIT_ERROR
    except json.JSONDecodeError as exc:
        print(
            "ERROR release-manifest: invalid JSON: "
            f"line {exc.lineno}, column {exc.colno}: {exc.msg}",
            file=sys.stderr,
        )
        return EXIT_ERROR
    except TypeError as exc:
        print(f"ERROR release-manifest: {exc}", file=sys.stderr)
        return EXIT_ERROR
    except (OSError, UnicodeError) as exc:
        print(
            f"ERROR release-manifest: cannot read {path}: {exc}",
            file=sys.stderr,
        )
        return EXIT_ERROR

    errors = validate_release_manifest(document)
    if errors:
        for error in errors:
            print(f"FAIL release-manifest: {error}")
        return EXIT_FAIL
    print(f"PASS release-manifest: {path} satisfies the release manifest contract")
    return EXIT_PASS


def _check_evaluation(path: Path) -> int:
    try:
        result = check_evaluation_bundle(path)
    except FileNotFoundError:
        print(f"ERROR evaluation: path not found: {path}", file=sys.stderr)
        return EXIT_ERROR
    except ValueError as exc:
        print(f"ERROR evaluation: {exc}", file=sys.stderr)
        return EXIT_ERROR
    except (OSError, UnicodeError) as exc:
        print(f"ERROR evaluation: cannot read {path}: {exc}", file=sys.stderr)
        return EXIT_ERROR

    print(f"{result.status.value} evaluation:{result.readiness}: {path}")
    for message in result.messages:
        print(f"  - {message}")
    return EXIT_FAIL if result.status is EvaluationStatus.FAIL else EXIT_PASS


def _check_agent_skills(path: Path) -> int:
    try:
        report = check_agent_skills(path)
    except FileNotFoundError:
        print(f"ERROR agent-skills: path not found: {path}", file=sys.stderr)
        return EXIT_ERROR
    except ValueError as exc:
        print(f"ERROR agent-skills: {exc}", file=sys.stderr)
        return EXIT_ERROR
    except (OSError, UnicodeError) as exc:
        print(f"ERROR agent-skills: cannot read {path}: {exc}", file=sys.stderr)
        return EXIT_ERROR

    for finding in report.findings:
        status = "PASS" if finding.passed else "FAIL"
        print(f"{status} {finding.check_id}: {finding.message}")
    pass_count = sum(finding.passed for finding in report.findings)
    fail_count = len(report.findings) - pass_count
    print(f"SUMMARY PASS={pass_count} FAIL={fail_count}")
    return EXIT_FAIL if report.has_failures else EXIT_PASS


def _export_capability(
    manifest: Path,
    *,
    repository: Path,
    output: Path,
    replace: bool,
) -> int:
    try:
        result = export_capability_artifact(
            manifest,
            repository=repository,
            output=output,
            replace=replace,
        )
    except FileNotFoundError as exc:
        print(f"ERROR export capability: path not found: {exc.filename or exc}", file=sys.stderr)
        return EXIT_ERROR
    except json.JSONDecodeError as exc:
        print(
            f"ERROR export capability: invalid JSON at line {exc.lineno}, "
            f"column {exc.colno}: {exc.msg}",
            file=sys.stderr,
        )
        return EXIT_ERROR
    except (ArtifactPolicyError, ArtifactConflictError) as exc:
        print(f"FAIL export capability: {exc}")
        return EXIT_FAIL
    except ValueError as exc:
        print(f"ERROR export capability: {exc}", file=sys.stderr)
        return EXIT_ERROR
    except (OSError, UnicodeError) as exc:
        print(f"ERROR export capability: cannot export artifact: {exc}", file=sys.stderr)
        return EXIT_ERROR

    for path in result.files:
        print(f"EXPORT {path}")
    print(f"SOURCE {result.source_hash}")
    print(f"PASS export capability: {result.capability_name}")
    return EXIT_PASS


def _check_artifact(path: Path, *, repository: Path) -> int:
    try:
        result = check_capability_artifact(path, repository=repository)
    except FileNotFoundError:
        print(f"ERROR artifact: path not found: {path}", file=sys.stderr)
        return EXIT_ERROR
    except json.JSONDecodeError as exc:
        print(
            f"ERROR artifact: invalid JSON at line {exc.lineno}, "
            f"column {exc.colno}: {exc.msg}",
            file=sys.stderr,
        )
        return EXIT_ERROR
    except ArtifactPolicyError as exc:
        print(f"FAIL artifact: {exc}")
        return EXIT_FAIL
    except ValueError as exc:
        print(f"ERROR artifact: {exc}", file=sys.stderr)
        return EXIT_ERROR
    except (OSError, UnicodeError) as exc:
        print(f"ERROR artifact: cannot check {path}: {exc}", file=sys.stderr)
        return EXIT_ERROR

    status = "PASS" if result.passed else "FAIL"
    print(f"{status} artifact: {result.directory}")
    for message in result.messages:
        print(f"  - {message}")
    return EXIT_PASS if result.passed else EXIT_FAIL


def _check_references(manifest: Path, *, repository: Path) -> int:
    try:
        report = check_capability_references(manifest, repository=repository)
    except FileNotFoundError:
        print(f"ERROR references: path not found: {manifest}", file=sys.stderr)
        return EXIT_ERROR
    except json.JSONDecodeError as exc:
        print(
            f"ERROR references: invalid JSON at line {exc.lineno}, "
            f"column {exc.colno}: {exc.msg}",
            file=sys.stderr,
        )
        return EXIT_ERROR
    except ReferencePolicyError as exc:
        print(f"FAIL references: {exc}")
        return EXIT_FAIL
    except ValueError as exc:
        print(f"ERROR references: {exc}", file=sys.stderr)
        return EXIT_ERROR
    except (OSError, UnicodeError) as exc:
        print(f"ERROR references: cannot check {manifest}: {exc}", file=sys.stderr)
        return EXIT_ERROR

    for finding in report.findings:
        print(f"{finding.status.value} {finding.check_id}: {finding.message}")
    summary = " ".join(
        f"{status.value}={report.count(status)}"
        for status in (
            ReferenceStatus.PASS,
            ReferenceStatus.WARN,
            ReferenceStatus.FAIL,
        )
    )
    print(f"SUMMARY {summary}")
    return EXIT_FAIL if report.has_failures else EXIT_PASS


def _init_project(target: Path, *, project_name: str, dry_run: bool) -> int:
    try:
        report = initialize_project(
            target,
            project_name=project_name,
            dry_run=dry_run,
        )
    except InitConflictError as exc:
        print(f"FAIL init: {exc}")
        return EXIT_FAIL
    except ValueError as exc:
        print(f"ERROR init: {exc}", file=sys.stderr)
        return EXIT_ERROR
    except (OSError, UnicodeError) as exc:
        print(f"ERROR init: cannot create governance scaffold: {exc}", file=sys.stderr)
        return EXIT_ERROR

    action = "PLAN" if report.dry_run else "CREATE"
    for generated_file in report.files:
        print(f"{action} {generated_file.relative_path.as_posix()}")

    if report.unresolved_placeholders:
        print(
            "WARN init: "
            f"{len(report.unresolved_placeholders)} unresolved governance placeholder(s) "
            "require human review"
        )

    if report.dry_run:
        print(f"PASS init dry-run: {report.target}")
        print(
            "NEXT init dry-run: rerun without --dry-run to create and review "
            "the scaffold"
        )
    else:
        print(f"PASS init: {report.target}")
        print(
            "NEXT init: review "
            f"{report.target / 'AGENTS.md'} and replace or explicitly defer "
            "governance placeholders"
        )
        print(
            "NEXT init: run "
            f"`agentgov check repository \"{report.target}\"` after adapting "
            "the scaffold"
        )
    if report.dry_run:
        print(
            "NOTE init dry-run: preview completion does not mean governance is "
            "complete and does not authorize merge, publish, release, or deploy"
        )
    else:
        print(
            "NOTE init: successful initialization does not mean governance is "
            "complete and does not authorize merge, publish, release, or deploy"
        )
    return EXIT_PASS


def _check_repository(path: Path) -> int:
    try:
        report = check_repository(path)
    except FileNotFoundError:
        print(f"ERROR repository: path not found: {path}", file=sys.stderr)
        return EXIT_ERROR
    except ValueError as exc:
        print(f"ERROR repository: {exc}", file=sys.stderr)
        return EXIT_ERROR
    except (OSError, UnicodeError) as exc:
        print(f"ERROR repository: cannot read {path}: {exc}", file=sys.stderr)
        return EXIT_ERROR

    for finding in report.findings:
        print(f"{finding.status.value} {finding.check_id}: {finding.message}")

    summary = " ".join(
        f"{status.value}={report.count(status)}"
        for status in (
            FindingStatus.PASS,
            FindingStatus.WARN,
            FindingStatus.FAIL,
            FindingStatus.ADVISORY,
        )
    )
    print(f"SUMMARY {summary}")
    return EXIT_FAIL if report.has_failures else EXIT_PASS


def _report_repository(
    path: Path,
    *,
    output: Path | None,
    report_format: str,
) -> int:
    try:
        report = check_repository(path)
        renderers = {
            "markdown": render_repository_report,
            "json": render_repository_report_json,
            "html": render_repository_report_html,
        }
        content = renderers[report_format](report)
    except FileNotFoundError:
        print(f"ERROR report: repository path not found: {path}", file=sys.stderr)
        return EXIT_ERROR
    except KeyError:
        print(f"ERROR report: unsupported format: {report_format}", file=sys.stderr)
        return EXIT_ERROR
    except ValueError as exc:
        print(f"ERROR report: {exc}", file=sys.stderr)
        return EXIT_ERROR
    except (OSError, UnicodeError) as exc:
        print(f"ERROR report: cannot read {path}: {exc}", file=sys.stderr)
        return EXIT_ERROR

    if output is None:
        print(content, end="")
    else:
        try:
            write_report(output, content)
        except ReportConflictError as exc:
            print(f"FAIL report: {exc}")
            return EXIT_FAIL
        except (OSError, UnicodeError) as exc:
            print(f"ERROR report: cannot write {output}: {exc}", file=sys.stderr)
            return EXIT_ERROR
        print(f"REPORT {output}")
        if report_format in {"markdown", "html"}:
            print(
                "NEXT report: open the report and review "
                "`Human decisions still required`"
            )
        else:
            print(
                "NEXT report: consume the versioned JSON contract and review "
                "its known gaps and recommended actions"
            )
        print(
            "NOTE report: report generation does not authorize merge, publish, "
            "release, or deploy"
        )

    return EXIT_FAIL if report.has_failures else EXIT_PASS


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="agentgov",
        description="Check repository-native AI governance contracts.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    review_parser = commands.add_parser(
        "review",
        help="Collect deterministic evidence while preserving human decision authority.",
    )
    review_targets = review_parser.add_subparsers(
        dest="review_target",
        required=True,
    )
    release_review_parser = review_targets.add_parser(
        "release",
        help="Create one local release review bundle from exact candidate artifacts.",
    )
    release_review_parser.add_argument(
        "source",
        nargs="?",
        type=Path,
        default=Path("."),
        help="AgentGov source repository (default: current directory).",
    )
    release_review_parser.add_argument(
        "--wheel",
        type=Path,
        required=True,
        help="Exact candidate wheel to install and review.",
    )
    release_review_parser.add_argument(
        "--manifest",
        type=Path,
        required=True,
        help="Immutable release manifest matching the candidate wheel.",
    )
    release_review_parser.add_argument(
        "--consumer",
        type=Path,
        required=True,
        help="Adopting repository used for compatibility evidence.",
    )
    release_review_parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="New review-bundle directory; existing paths are never overwritten.",
    )
    release_review_parser.set_defaults(
        handler=lambda args: _review_release(
            args.source,
            wheel=args.wheel,
            manifest=args.manifest,
            consumer=args.consumer,
            output=args.output,
        )
    )
    upgrade_review_parser = review_targets.add_parser(
        "upgrade",
        help="Create a consumer-local review bundle for one stable upgrade proposal.",
    )
    upgrade_review_parser.add_argument(
        "repository",
        nargs="?",
        type=Path,
        default=Path("."),
        help="Consumer repository directory (default: current directory).",
    )
    upgrade_review_parser.add_argument(
        "--manifest",
        type=Path,
        required=True,
        help="Downloaded and reviewed stable release manifest.",
    )
    upgrade_review_parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="New consumer review directory; existing paths are never overwritten.",
    )
    upgrade_review_parser.set_defaults(
        handler=lambda args: _review_upgrade(
            args.repository,
            manifest=args.manifest,
            output=args.output,
        )
    )

    benefits_parser = commands.add_parser(
        "benefits",
        help="Compare governance report evidence without claiming causality.",
    )
    benefits_targets = benefits_parser.add_subparsers(
        dest="benefits_target",
        required=True,
    )
    benefits_compare_parser = benefits_targets.add_parser(
        "compare",
        help="Compare two repository report snapshots with explicit denominators.",
    )
    benefits_compare_parser.add_argument(
        "before",
        type=Path,
        help="Earlier AgentGov repository report JSON.",
    )
    benefits_compare_parser.add_argument(
        "after",
        type=Path,
        help="Later AgentGov repository report JSON.",
    )
    benefits_compare_parser.add_argument(
        "--format",
        dest="benefits_format",
        choices=("text", "json"),
        default="text",
        help="Benefit-evidence serialization format (default: text).",
    )
    benefits_compare_parser.set_defaults(
        handler=lambda args: _compare_benefit_reports(
            args.before,
            args.after,
            output_format=args.benefits_format,
        )
    )
    benefits_monitor_parser = benefits_targets.add_parser(
        "monitor",
        help="Create a portable trend bundle from a current report and trusted baseline.",
    )
    benefits_monitor_parser.add_argument("report", type=Path)
    benefits_monitor_parser.add_argument("--baseline-report", type=Path)
    benefits_monitor_parser.add_argument("--baseline-monitor", type=Path)
    benefits_monitor_parser.add_argument("--repository", required=True)
    benefits_monitor_parser.add_argument("--ref", required=True)
    benefits_monitor_parser.add_argument("--commit", dest="commit_sha", required=True)
    benefits_monitor_parser.add_argument("--run-id", type=int, required=True)
    benefits_monitor_parser.add_argument("--run-attempt", type=int, required=True)
    benefits_monitor_parser.add_argument("--event", required=True)
    benefits_monitor_parser.add_argument("--observed-at", required=True)
    benefits_monitor_parser.add_argument("--output", type=Path, required=True)
    benefits_monitor_parser.set_defaults(
        handler=lambda args: _monitor_benefits(
            args.report,
            baseline_report=args.baseline_report,
            baseline_monitor=args.baseline_monitor,
            repository=args.repository,
            ref=args.ref,
            commit_sha=args.commit_sha,
            run_id=args.run_id,
            run_attempt=args.run_attempt,
            event=args.event,
            observed_at=args.observed_at,
            output=args.output,
        )
    )
    benefits_annotate_parser = benefits_targets.add_parser(
        "annotate",
        help="Render redacted non-passing findings as GitHub workflow annotations.",
    )
    benefits_annotate_parser.add_argument("report", type=Path)
    benefits_annotate_parser.set_defaults(
        handler=lambda args: _annotate_benefits(args.report)
    )
    benefits_observe_upgrade_parser = benefits_targets.add_parser(
        "observe-upgrade",
        help="Record bounded upgrade automation timing and bridge observations.",
    )
    benefits_observe_upgrade_parser.add_argument("result", type=Path)
    benefits_observe_upgrade_parser.add_argument("--repository", required=True)
    benefits_observe_upgrade_parser.add_argument(
        "--commit", dest="commit_sha", required=True
    )
    benefits_observe_upgrade_parser.add_argument("--run-id", type=int, required=True)
    benefits_observe_upgrade_parser.add_argument(
        "--started-epoch", type=int, required=True
    )
    benefits_observe_upgrade_parser.add_argument(
        "--completed-epoch", type=int, required=True
    )
    benefits_observe_upgrade_parser.add_argument("--output", type=Path, required=True)
    benefits_observe_upgrade_parser.set_defaults(
        handler=lambda args: _observe_upgrade_benefit(
            args.result,
            repository=args.repository,
            commit_sha=args.commit_sha,
            run_id=args.run_id,
            started_epoch=args.started_epoch,
            completed_epoch=args.completed_epoch,
            output=args.output,
        )
    )

    plan_parser = commands.add_parser(
        "plan",
        help="Build a read-only automation plan without applying it.",
    )
    plan_targets = plan_parser.add_subparsers(dest="plan_target", required=True)
    upgrade_pr_parser = plan_targets.add_parser(
        "upgrade-pr",
        help="Plan one bounded managed-workflow upgrade pull request.",
    )
    upgrade_pr_parser.add_argument(
        "path",
        nargs="?",
        type=Path,
        default=Path("."),
        help="Consumer repository directory (default: current directory).",
    )
    upgrade_pr_parser.add_argument(
        "--manifest",
        type=Path,
        required=True,
        help="Downloaded and reviewed stable release manifest.",
    )
    upgrade_pr_parser.add_argument(
        "--format",
        dest="upgrade_pr_format",
        choices=("text", "json"),
        default="text",
        help="Upgrade PR plan serialization format (default: text).",
    )
    upgrade_pr_parser.set_defaults(
        handler=lambda args: _plan_upgrade_pr(
            args.path,
            manifest=args.manifest,
            output_format=args.upgrade_pr_format,
        )
    )

    create_parser = commands.add_parser(
        "create",
        help="Perform one explicitly authorized bounded creation action.",
    )
    create_targets = create_parser.add_subparsers(dest="create_target", required=True)
    create_upgrade_pr_parser = create_targets.add_parser(
        "upgrade-pr",
        help="Create or recover one exact AgentGov upgrade Draft PR.",
    )
    create_upgrade_pr_parser.add_argument(
        "path",
        nargs="?",
        type=Path,
        default=Path("."),
        help="Consumer repository directory (default: current directory).",
    )
    create_upgrade_pr_parser.add_argument(
        "--manifest",
        type=Path,
        required=True,
        help="Downloaded stable release manifest used to revalidate the exact change.",
    )
    create_upgrade_pr_parser.add_argument(
        "--repository",
        required=True,
        help="GitHub repository in owner/name form.",
    )
    create_upgrade_pr_parser.add_argument(
        "--base",
        dest="base_branch",
        required=True,
        help="Reviewed base branch, normally the repository default branch.",
    )
    create_upgrade_pr_parser.add_argument(
        "--event",
        dest="event_source",
        choices=("schedule", "workflow_dispatch"),
        required=True,
        help="Authorized GitHub Actions event source.",
    )
    create_upgrade_pr_parser.add_argument(
        "--current-report",
        type=Path,
        help="Dry-run JSON report produced by the currently pinned AgentGov version.",
    )
    create_upgrade_pr_parser.add_argument(
        "--target-report",
        type=Path,
        help="Dry-run JSON report produced by the proposed AgentGov version.",
    )
    create_upgrade_pr_parser.add_argument(
        "--token-env",
        default="GH_TOKEN",
        help="Environment variable containing the GitHub token (default: GH_TOKEN).",
    )
    create_upgrade_pr_parser.add_argument(
        "--format",
        dest="create_upgrade_pr_format",
        choices=("text", "json"),
        default="text",
        help="Draft PR result serialization format (default: text).",
    )
    create_upgrade_pr_parser.set_defaults(
        handler=lambda args: _create_upgrade_pr(
            args.path,
            manifest=args.manifest,
            repository=args.repository,
            base_branch=args.base_branch,
            event_source=args.event_source,
            current_report=args.current_report,
            target_report=args.target_report,
            token_env=args.token_env,
            output_format=args.create_upgrade_pr_format,
        )
    )

    status_parser = commands.add_parser(
        "status",
        help="Explain where repository governance is used and which surfaces are active.",
    )
    status_parser.add_argument(
        "path",
        nargs="?",
        type=Path,
        default=Path("."),
        help="Repository directory to inspect (default: current directory).",
    )
    status_parser.add_argument(
        "--format",
        dest="status_format",
        choices=("text", "json", "markdown"),
        default="text",
        help="Status serialization format (default: text; markdown suits CI summaries).",
    )
    status_parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Declare automation mode; status remains read-only and never prompts.",
    )
    status_parser.set_defaults(
        handler=lambda args: _status_repository(
            args.path,
            output_format=args.status_format,
            non_interactive=args.non_interactive,
        )
    )

    integrate_parser = commands.add_parser(
        "integrate",
        help="Preview or explicitly create a bounded consumer integration.",
    )
    integrate_targets = integrate_parser.add_subparsers(
        dest="integration_target",
        required=True,
    )
    github_actions_parser = integrate_targets.add_parser(
        "github-actions",
        help="Create a pinned, read-only AgentGov consumer CI workflow.",
    )
    github_actions_parser.add_argument(
        "path",
        nargs="?",
        type=Path,
        default=Path("."),
        help="Repository directory to integrate (default: current directory).",
    )
    github_actions_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview exact workflow content without requesting confirmation.",
    )
    github_actions_parser.add_argument(
        "--format",
        dest="integration_format",
        choices=("text", "json"),
        default="text",
        help="Integration-plan serialization format (default: text).",
    )
    github_actions_parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Declare automation mode; it never grants write authority.",
    )
    github_actions_parser.set_defaults(
        handler=lambda args: _integrate_github_actions(
            args.path,
            dry_run=args.dry_run,
            output_format=args.integration_format,
            non_interactive=args.non_interactive,
        )
    )

    update_parser = commands.add_parser(
        "update",
        help="Check and explicitly apply the bounded tool/repository update workflow.",
    )
    update_parser.add_argument(
        "--check",
        action="store_true",
        help="Check update state without installing or modifying repository files.",
    )
    update_parser.add_argument(
        "path",
        nargs="?",
        type=Path,
        default=Path("."),
        help="Repository directory to inspect (default: current directory).",
    )
    update_parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Declare automation mode; it never grants write authority.",
    )
    update_parser.add_argument(
        "--manifest",
        type=Path,
        help="Reviewed release manifest to compare (default: bundled current manifest).",
    )
    update_parser.add_argument(
        "--format",
        dest="update_format",
        choices=("text", "json"),
        default="text",
        help="Update-check serialization format (default: text).",
    )
    update_parser.set_defaults(
        handler=lambda args: _update_repository(
            args.path,
            check_only=args.check,
            manifest=args.manifest,
            output_format=args.update_format,
            non_interactive=args.non_interactive,
            resume_after_tool_update=args.resume_after_tool_update,
        )
    )
    update_parser.add_argument(
        "--resume-after-tool-update",
        help=argparse.SUPPRESS,
    )

    refresh_parser = commands.add_parser(
        "refresh",
        help="Preview or explicitly apply a bounded repository contract refresh.",
    )
    refresh_parser.add_argument(
        "path",
        nargs="?",
        type=Path,
        default=Path("."),
        help="Repository directory to preview (default: current directory).",
    )
    refresh_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview exact repository changes without requesting confirmation.",
    )
    refresh_parser.add_argument(
        "--manifest",
        type=Path,
        help="Reviewed release manifest (default: bundled current manifest).",
    )
    refresh_parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Declare automation mode; it never grants write authority.",
    )
    refresh_parser.add_argument(
        "--format",
        dest="refresh_format",
        choices=("text", "json"),
        default="text",
        help="Refresh-plan serialization format (default: text).",
    )
    refresh_parser.set_defaults(
        handler=lambda args: _refresh_repository(
            args.path,
            dry_run=args.dry_run,
            manifest=args.manifest,
            output_format=args.refresh_format,
            non_interactive=args.non_interactive,
        )
    )

    doctor_parser = commands.add_parser(
        "doctor",
        help="Diagnose onboarding prerequisites without modifying the repository.",
    )
    doctor_parser.add_argument(
        "path",
        nargs="?",
        type=Path,
        default=Path("."),
        help="Repository directory to diagnose (default: current directory).",
    )
    doctor_parser.add_argument(
        "--format",
        dest="doctor_format",
        choices=("text", "json"),
        default="text",
        help="Diagnosis serialization format (default: text).",
    )
    doctor_parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Declare automation mode; doctor remains read-only and never prompts.",
    )
    doctor_parser.set_defaults(
        handler=lambda args: _doctor_repository(
            args.path,
            output_format=args.doctor_format,
            non_interactive=args.non_interactive,
        )
    )

    onboard_parser = commands.add_parser(
        "onboard",
        help=(
            "Guide create-missing-only onboarding; preview by default and write "
            "only after exact ADOPT confirmation in an interactive terminal."
        ),
    )
    onboard_parser.add_argument(
        "path",
        nargs="?",
        type=Path,
        default=Path("."),
        help="Repository directory to preview (default: current directory).",
    )
    onboard_parser.add_argument(
        "--project-name",
        required=True,
        help="Human-readable project name used only to build the preview.",
    )
    onboard_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview onboarding without requesting write confirmation.",
    )
    onboard_parser.add_argument(
        "--format",
        dest="onboard_format",
        choices=("text", "json"),
        default="text",
        help="Preview serialization format (default: text).",
    )
    onboard_parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Declare automation mode; it never grants write authority.",
    )
    onboard_parser.set_defaults(
        handler=lambda args: _onboard_repository(
            args.path,
            project_name=args.project_name,
            dry_run=args.dry_run,
            output_format=args.onboard_format,
            non_interactive=args.non_interactive,
        )
    )

    next_parser = commands.add_parser(
        "next",
        help="Select one smallest useful next action without executing it.",
    )
    next_parser.add_argument(
        "path",
        nargs="?",
        type=Path,
        default=Path("."),
        help="Repository directory to inspect (default: current directory).",
    )
    next_parser.add_argument(
        "--format",
        dest="next_format",
        choices=("text", "json"),
        default="text",
        help="Action serialization format (default: text).",
    )
    next_parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Declare automation mode; next remains read-only and never prompts.",
    )
    next_parser.set_defaults(
        handler=lambda args: _next_repository(
            args.path,
            output_format=args.next_format,
            non_interactive=args.non_interactive,
        )
    )

    inspect_parser = commands.add_parser(
        "inspect",
        help="Inspect an existing repository and print a read-only governance adoption plan.",
    )
    inspect_parser.add_argument(
        "path",
        nargs="?",
        type=Path,
        default=Path("."),
        help="Existing repository directory to inspect (default: current directory).",
    )
    inspect_parser.add_argument(
        "--format",
        dest="inspect_format",
        choices=("text", "json"),
        default="text",
        help="Inspection serialization format (default: text).",
    )
    inspect_parser.set_defaults(
        handler=lambda args: _inspect_repository(
            args.path,
            output_format=args.inspect_format,
        )
    )

    adopt_parser = commands.add_parser(
        "adopt",
        help="Create only missing governance scaffold files in an existing repository.",
    )
    adopt_parser.add_argument(
        "path",
        nargs="?",
        type=Path,
        default=Path("."),
        help="Existing repository directory to adopt into (default: current directory).",
    )
    adopt_parser.add_argument(
        "--project-name",
        required=True,
        help="Human-readable project name used in newly created documents.",
    )
    adopt_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show planned and preserved files without writing.",
    )
    adopt_parser.set_defaults(
        handler=lambda args: _adopt_repository(
            args.path,
            project_name=args.project_name,
            dry_run=args.dry_run,
        )
    )

    init_parser = commands.add_parser(
        "init",
        help="Create a governance scaffold in a new or empty directory.",
    )
    init_parser.add_argument(
        "target",
        nargs="?",
        type=Path,
        default=Path("."),
        help="New or empty target directory (default: current directory).",
    )
    init_parser.add_argument(
        "--project-name",
        required=True,
        help="Human-readable project name used in generated documents.",
    )
    init_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show planned files without creating the target directory.",
    )
    init_parser.set_defaults(
        handler=lambda args: _init_project(
            args.target,
            project_name=args.project_name,
            dry_run=args.dry_run,
        )
    )

    export_parser = commands.add_parser(
        "export",
        help="Generate repository-local governance artifacts.",
    )
    export_targets = export_parser.add_subparsers(dest="export_target", required=True)
    export_capability_parser = export_targets.add_parser(
        "capability",
        help="Export one AI capability as deterministic review artifacts.",
    )
    export_capability_parser.add_argument(
        "manifest",
        type=Path,
        help="Capability manifest located inside the repository root.",
    )
    export_capability_parser.add_argument(
        "--repository",
        type=Path,
        default=Path("."),
        help="Repository root used for path and source resolution (default: current directory).",
    )
    export_capability_parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help=(
            "Output root inside the repository. Defaults to governance/artifacts "
            "or the legacy prompt-governance/artifacts for a legacy manifest."
        ),
    )
    export_capability_parser.add_argument(
        "--replace",
        action="store_true",
        help="Replace only the generated CAPABILITY.md and artifact.json files.",
    )
    export_capability_parser.set_defaults(
        handler=lambda args: _export_capability(
            args.manifest,
            repository=args.repository,
            output=args.output,
            replace=args.replace,
        )
    )
    export_development_parser = export_targets.add_parser(
        "development",
        help="Preview and explicitly create a redacted local development-event bundle.",
    )
    export_development_parser.add_argument(
        "--repository",
        type=Path,
        default=Path("."),
        help="Git repository containing local AgentGov events (default: current directory).",
    )
    export_development_parser.add_argument(
        "--events",
        type=Path,
        help="Event directory inside the repository (default: .agentgov/events).",
    )
    export_development_parser.add_argument(
        "--output",
        type=Path,
        help="New JSON output inside the repository (default: .agentgov/exports/<export-id>.json).",
    )
    export_development_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview source counts, retained metadata, and redaction without writing.",
    )
    export_development_parser.set_defaults(
        handler=lambda args: _export_development_events(
            args.repository,
            event_directory=args.events,
            output=args.output,
            dry_run=args.dry_run,
        )
    )

    dev_parser = commands.add_parser(
        "dev",
        help="Run one explicit foreground automatic-governance cycle.",
    )
    dev_parser.add_argument(
        "repository",
        nargs="?",
        type=Path,
        default=Path("."),
        help="Git worktree root (default: current directory).",
    )
    dev_parser.add_argument(
        "--event",
        dest="trigger_type",
        choices=tuple(sorted(TRIGGER_TYPES)),
        default="repository.activated",
        help="Adapter event for this foreground cycle (default: repository.activated).",
    )
    dev_parser.add_argument(
        "--actor-class",
        choices=("human", "coding_agent", "ci"),
        default="coding_agent",
        help="Originating actor class; human is required for review or recorded scope decisions.",
    )
    dev_parser.add_argument("--correlation-id", help="Optional adapter correlation id.")
    dev_parser.add_argument(
        "--validation-outcome",
        choices=("passed", "failed"),
        help="Context-only adapter outcome; valid only with validation.completed.",
    )
    dev_parser.add_argument(
        "--evidence-ref",
        type=Path,
        help="Repository-relative adapter evidence pointer; valid only with validation.completed.",
    )
    dev_parser.add_argument(
        "--scope-decision",
        choices=("approved", "declined", "needs_human"),
        help="Human decision; valid only with scope.decision_recorded.",
    )
    dev_parser.add_argument(
        "--review-outcome",
        choices=("accepted", "changes_requested"),
        help="Human completion review; valid only with session.reviewed.",
    )
    dev_parser.add_argument(
        "--dashboard-output",
        type=Path,
        default=Path(".agentgov/dashboard.html"),
        help="Untracked AgentGov-owned Dashboard output inside the repository.",
    )
    dev_parser.add_argument(
        "--format",
        dest="dev_format",
        choices=("terminal", "json"),
        default="terminal",
    )
    dev_parser.set_defaults(
        handler=lambda args: _dev_foreground(
            args.repository,
            trigger_type=args.trigger_type,
            actor_class=args.actor_class,
            correlation_id=args.correlation_id,
            validation_outcome=args.validation_outcome,
            evidence_ref=args.evidence_ref,
            scope_decision=args.scope_decision,
            review_outcome=args.review_outcome,
            dashboard_output=args.dashboard_output,
            output_format=args.dev_format,
        )
    )

    govern_parser = commands.add_parser(
        "govern",
        help="Govern a coding-agent task during development and append local observations.",
    )
    govern_targets = govern_parser.add_subparsers(dest="govern_target", required=True)
    govern_start_parser = govern_targets.add_parser(
        "start",
        help="Preview and explicitly confirm one guided development governance session.",
    )
    govern_start_parser.add_argument(
        "task",
        nargs="?",
        type=Path,
        help="Existing admitted task; if omitted, exactly one admitted task may be auto-discovered.",
    )
    govern_start_parser.add_argument(
        "--repository",
        type=Path,
        default=Path("."),
        help="Git worktree root (default: current directory).",
    )
    govern_start_parser.add_argument(
        "--title",
        help="Create a low-risk compact task with this title instead of selecting an existing task.",
    )
    govern_start_parser.add_argument("--task-id", help="Optional kebab-case id for a new compact task.")
    govern_start_parser.add_argument(
        "--requirement",
        help="Human-readable requirement summary for a new compact task.",
    )
    govern_start_parser.add_argument(
        "--include",
        dest="include_paths",
        action="append",
        default=[],
        help="Machine-checkable included path or segment prefix; repeat as needed.",
    )
    govern_start_parser.add_argument(
        "--exclude",
        dest="exclude_paths",
        action="append",
        default=[],
        help="Excluded path or segment prefix; repeat as needed and always overrides include.",
    )
    govern_start_parser.add_argument(
        "--validate",
        dest="validation_commands",
        action="append",
        default=[],
        help="Validation command for a new compact task; repeat as needed. Conventional tests are detected when omitted.",
    )
    govern_start_parser.add_argument(
        "--owner",
        default="Human product owner",
        help="Accountable owner for a new compact task.",
    )
    govern_start_parser.add_argument(
        "--base",
        default="HEAD",
        help="Comparison-base revision recorded for later fresh validation (default: HEAD).",
    )
    govern_start_parser.add_argument(
        "--actor-label",
        help="Optional vendor-neutral label for the confirming human.",
    )
    govern_start_parser.add_argument(
        "--replace-active",
        action="store_true",
        help="Preview replacing a different active task; still requires exact REPLACE confirmation.",
    )
    govern_start_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Render the complete plan and write nothing.",
    )
    govern_start_parser.add_argument(
        "--format",
        dest="govern_format",
        choices=("terminal", "json"),
        default="terminal",
        help="Start preview format (default: terminal).",
    )
    govern_start_parser.set_defaults(
        handler=lambda args: _govern_start(
            args.repository,
            task=args.task,
            title=args.title,
            task_id=args.task_id,
            requirement=args.requirement,
            include_paths=args.include_paths,
            exclude_paths=args.exclude_paths,
            validation_commands=args.validation_commands,
            owner=args.owner,
            comparison_base=args.base,
            actor_label=args.actor_label,
            replace_active=args.replace_active,
            dry_run=args.dry_run,
            output_format=args.govern_format,
        )
    )
    govern_check_parser = govern_targets.add_parser(
        "check",
        help="Check the active or explicitly selected task scope and append one bounded event.",
    )
    govern_check_parser.add_argument(
        "task",
        nargs="?",
        type=Path,
        help="Optional admitted task; defaults to the task recorded by govern start.",
    )
    govern_check_parser.add_argument(
        "--repository",
        type=Path,
        default=Path("."),
        help="Git worktree root used for task and change inspection.",
    )
    govern_check_parser.add_argument(
        "--format",
        dest="govern_format",
        choices=("terminal", "json", "markdown"),
        default="terminal",
        help="Observed scope report format (default: terminal).",
    )
    govern_check_parser.add_argument(
        "--actor",
        choices=("human", "coding_agent", "ci"),
        default="coding_agent",
        help="Accountable actor class recorded in the local event.",
    )
    govern_check_parser.add_argument(
        "--actor-label",
        help="Optional vendor-neutral actor label; absolute paths and credential assignments are rejected.",
    )
    govern_check_parser.set_defaults(
        handler=lambda args: _govern_check(
            args.task,
            repository=args.repository,
            output_format=args.govern_format,
            actor_class=args.actor,
            actor_label=args.actor_label,
        )
    )

    govern_finish_parser = govern_targets.add_parser(
        "finish",
        help="Run declared validation or reuse evidence, then reconcile completion.",
    )
    govern_finish_parser.add_argument(
        "task",
        nargs="?",
        type=Path,
        help="Optional admitted task; defaults to the task and comparison base recorded by govern start.",
    )
    govern_finish_parser.add_argument(
        "--repository",
        type=Path,
        default=Path("."),
        help="Git worktree root used for validation and reconciliation.",
    )
    evidence_source = govern_finish_parser.add_mutually_exclusive_group()
    evidence_source.add_argument(
        "--base",
        help="Comparison-base revision; runs every task-declared validation command before finish.",
    )
    evidence_source.add_argument(
        "--evidence",
        type=Path,
        help="Specific prior record beneath .agentgov/evidence; otherwise the latest task evidence is used.",
    )
    govern_finish_parser.add_argument(
        "--format",
        dest="govern_format",
        choices=("terminal", "json", "markdown"),
        default="terminal",
        help="Completion report format (default: terminal).",
    )
    govern_finish_parser.add_argument(
        "--actor",
        choices=("human", "coding_agent", "ci"),
        default="coding_agent",
        help="Accountable actor class recorded in local events.",
    )
    govern_finish_parser.add_argument(
        "--actor-label",
        help="Optional vendor-neutral actor label; absolute paths and credential assignments are rejected.",
    )
    govern_finish_parser.set_defaults(
        handler=lambda args: _govern_finish(
            args.task,
            repository=args.repository,
            comparison_base=args.base,
            evidence=args.evidence,
            output_format=args.govern_format,
            actor_class=args.actor,
            actor_label=args.actor_label,
        )
    )
    govern_handoff_parser = govern_targets.add_parser(
        "handoff",
        help="Preview and explicitly confirm terminal routing handoff for one fresh verified session.",
    )
    govern_handoff_parser.add_argument(
        "--repository",
        type=Path,
        default=Path("."),
        help="Git worktree root containing the exact verified session.",
    )
    govern_handoff_parser.add_argument(
        "--actor-label",
        help="Optional vendor-neutral label for the confirming human.",
    )
    govern_handoff_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Re-establish freshness, render the complete one-event preview, and write nothing.",
    )
    govern_handoff_parser.add_argument(
        "--format",
        dest="govern_format",
        choices=("terminal", "json"),
        default="terminal",
        help="Handoff preview format (default: terminal).",
    )
    govern_handoff_parser.set_defaults(
        handler=lambda args: _govern_handoff(
            args.repository,
            actor_label=args.actor_label,
            dry_run=args.dry_run,
            output_format=args.govern_format,
        )
    )

    context_parser = commands.add_parser(
        "context",
        help="Select read-only task-specific governance context.",
    )
    context_targets = context_parser.add_subparsers(
        dest="context_target",
        required=True,
    )
    context_task_parser = context_targets.add_parser(
        "task",
        help="Select governance for one admitted development task.",
    )
    context_task_parser.add_argument(
        "task",
        type=Path,
        help="Admitted task contract JSON located inside the repository root.",
    )
    context_task_parser.add_argument(
        "--repository",
        type=Path,
        default=Path("."),
        help="Repository root used for discovery and reference resolution.",
    )
    context_task_parser.add_argument(
        "--format",
        dest="context_format",
        choices=("terminal", "json", "markdown"),
        default="terminal",
        help="Context serialization format (default: terminal).",
    )
    context_task_parser.add_argument(
        "--include-content",
        action="store_true",
        help="Embed selected file contents in JSON or Markdown instead of returning references only.",
    )
    context_task_parser.set_defaults(
        handler=lambda args: _context_task(
            args.task,
            repository=args.repository,
            context_format=args.context_format,
            include_content=args.include_content,
        )
    )

    check_parser = commands.add_parser("check", help="Run a deterministic governance check.")
    check_targets = check_parser.add_subparsers(dest="check_target", required=True)

    capability_parser = check_targets.add_parser(
        "capability",
        help="Validate one AI capability manifest.",
    )
    capability_parser.add_argument("manifest", type=Path, help="Path to a capability JSON file.")
    capability_parser.set_defaults(handler=lambda args: _check_capability(args.manifest))

    task_parser = check_targets.add_parser(
        "task",
        help="Validate one development-time coding-agent task contract.",
    )
    task_parser.add_argument(
        "task",
        type=Path,
        help="Task contract JSON located inside the repository root.",
    )
    task_parser.add_argument(
        "--repository",
        type=Path,
        default=Path("."),
        help="Repository root used for reference resolution (default: current directory).",
    )
    task_parser.set_defaults(
        handler=lambda args: _check_task(args.task, repository=args.repository)
    )

    scope_parser = check_targets.add_parser(
        "scope",
        help="Compare working-tree Git changes with one admitted task scope.",
    )
    scope_parser.add_argument(
        "task",
        type=Path,
        help="Admitted task contract JSON located inside the repository root.",
    )
    scope_parser.add_argument(
        "--repository",
        type=Path,
        default=Path("."),
        help="Git worktree root used for task and change inspection.",
    )
    scope_parser.add_argument(
        "--format",
        dest="scope_format",
        choices=("terminal", "json", "markdown"),
        default="terminal",
        help="Scope report serialization format (default: terminal).",
    )
    scope_parser.set_defaults(
        handler=lambda args: _check_scope(
            args.task,
            repository=args.repository,
            scope_format=args.scope_format,
        )
    )

    release_manifest_parser = check_targets.add_parser(
        "release-manifest",
        help="Validate machine-readable AgentGov release and compatibility metadata.",
    )
    release_manifest_parser.add_argument(
        "manifest",
        type=Path,
        help="Path to an AgentGov release manifest JSON file.",
    )
    release_manifest_parser.set_defaults(
        handler=lambda args: _check_release_manifest(args.manifest)
    )

    evaluation_parser = check_targets.add_parser(
        "evaluation",
        help="Validate an evaluation bundle and its declared readiness.",
    )
    evaluation_parser.add_argument(
        "bundle",
        type=Path,
        help="Directory containing evaluation-manifest.json and referenced cases.",
    )
    evaluation_parser.set_defaults(handler=lambda args: _check_evaluation(args.bundle))

    agent_skills_parser = check_targets.add_parser(
        "agent-skills",
        help="Validate repository-native agent operating protocols.",
    )
    agent_skills_parser.add_argument(
        "path",
        nargs="?",
        type=Path,
        default=Path("agent-skills"),
        help="Agent skills directory (default: agent-skills).",
    )
    agent_skills_parser.set_defaults(handler=lambda args: _check_agent_skills(args.path))

    artifact_parser = check_targets.add_parser(
        "artifact",
        help="Check a capability artifact for manifest, source, or generated-file drift.",
    )
    artifact_parser.add_argument(
        "path",
        type=Path,
        help="Capability artifact directory containing artifact.json.",
    )
    artifact_parser.add_argument(
        "--repository",
        type=Path,
        default=Path("."),
        help="Repository root used for path and source resolution (default: current directory).",
    )
    artifact_parser.set_defaults(
        handler=lambda args: _check_artifact(args.path, repository=args.repository)
    )

    references_parser = check_targets.add_parser(
        "references",
        help="Check repository-local capability schema, caller, source, and evidence paths.",
    )
    references_parser.add_argument(
        "manifest",
        type=Path,
        help="Capability manifest located inside the repository root.",
    )
    references_parser.add_argument(
        "--repository",
        type=Path,
        default=Path("."),
        help="Repository root used for reference resolution (default: current directory).",
    )
    references_parser.set_defaults(
        handler=lambda args: _check_references(
            args.manifest,
            repository=args.repository,
        )
    )

    repository_parser = check_targets.add_parser(
        "repository",
        help="Check required governance files, placeholders, and capability manifests.",
    )
    repository_parser.add_argument(
        "path",
        nargs="?",
        type=Path,
        default=Path("."),
        help="Repository directory to check (default: current directory).",
    )
    repository_parser.set_defaults(handler=lambda args: _check_repository(args.path))

    monitor_parser = commands.add_parser(
        "monitor",
        help="Generate an honest static view of observed development governance events.",
    )
    monitor_targets = monitor_parser.add_subparsers(dest="monitor_target", required=True)
    development_monitor_parser = monitor_targets.add_parser(
        "development",
        help="Build Overview, Activity Timeline, and Task Detail from local events.",
    )
    development_monitor_parser.add_argument(
        "repository",
        nargs="?",
        type=Path,
        default=Path("."),
        help="Repository containing .agentgov/events (default: current directory).",
    )
    development_monitor_parser.add_argument(
        "--scope",
        choices=("local_session", "exported_development", "ci_only", "combined"),
        default="local_session",
        help="Observation scope; exported and combined scopes require --export.",
    )
    development_monitor_parser.add_argument(
        "--events",
        type=Path,
        help="Local event directory inside the repository (default: .agentgov/events).",
    )
    development_monitor_parser.add_argument(
        "--export",
        dest="development_export",
        type=Path,
        help="Validated redacted development-event export inside the repository.",
    )
    development_monitor_parser.add_argument(
        "--format",
        dest="monitor_format",
        choices=("html", "json", "markdown"),
        default="html",
        help="Generated Monitor format (default: html).",
    )
    development_monitor_parser.add_argument(
        "--output",
        type=Path,
        help="Output inside the repository (default: .agentgov/dashboard.<format>).",
    )
    development_monitor_parser.set_defaults(
        handler=lambda args: _monitor_development(
            args.repository,
            observation_scope=args.scope,
            event_directory=args.events,
            export_path=args.development_export,
            output_format=args.monitor_format,
            output=args.output,
        )
    )

    report_parser = commands.add_parser(
        "report",
        help="Render governance findings as a Markdown, JSON, or HTML report.",
    )
    report_targets = report_parser.add_subparsers(dest="report_target", required=True)
    report_repository_parser = report_targets.add_parser(
        "repository",
        help="Render a repository governance report.",
    )
    report_repository_parser.add_argument(
        "path",
        nargs="?",
        type=Path,
        default=Path("."),
        help="Repository directory to report on (default: current directory).",
    )
    report_repository_parser.add_argument(
        "--output",
        type=Path,
        help="Write a new report file instead of printing to standard output.",
    )
    report_repository_parser.add_argument(
        "--format",
        dest="report_format",
        choices=("markdown", "json", "html"),
        default="markdown",
        help="Report serialization format (default: markdown).",
    )
    report_repository_parser.set_defaults(
        handler=lambda args: _report_repository(
            args.path,
            output=args.output,
            report_format=args.report_format,
        )
    )

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the CLI and return a stable process exit code."""

    args = build_parser().parse_args(argv)
    return int(args.handler(args))
