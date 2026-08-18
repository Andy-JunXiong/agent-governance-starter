"""Run the deterministic AgentGov governed-refund demonstration.

The demonstration creates a disposable Git repository.  Agent edits and the
remediation step are scripted and labelled as such.  Scope classification,
foreground blocking, the human-decision contract, validation, and completion
reconciliation are executed by the current AgentGov development source.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Callable

from agentgov.change_scope import check_development_scope
from agentgov.coding_agent_transport import (
    coding_agent_event_from_human_decision,
    coding_agent_event_from_payload,
    run_coding_agent_event,
)
from agentgov.development_session import (
    apply_start_plan,
    build_start_plan,
    request_start_confirmation,
)
from agentgov.event_store import load_governance_events, utc_now
from agentgov.host_interaction import REFERENCE_HOST_CAPABILITIES
from agentgov.human_decision import request_reference_terminal_selection
from agentgov.initializer import initialize_project


HUMAN_REQUEST = (
    "Fix the refund calculation bug. Only change refund calculation logic. "
    "Do not change refund approval policy or payment authorization behavior."
)
ALLOWED_PATHS = ("refunds/calculation.py", "tests/test_refunds.py")
DENIED_PATHS = (
    "refunds/approval_policy.py",
    "refunds/payment_authorization.py",
)
CALCULATION_BEFORE = """from decimal import Decimal


def calculate_refund(paid: Decimal, restocking_fee: Decimal) -> Decimal:
    # Bug: the fee is not deducted.
    return paid
"""
CALCULATION_AFTER = """from decimal import Decimal


def calculate_refund(paid: Decimal, restocking_fee: Decimal) -> Decimal:
    return paid - restocking_fee
"""
APPROVAL_BEFORE = """from decimal import Decimal


def requires_human_approval(amount: Decimal) -> bool:
    return amount > Decimal("100.00")
"""
APPROVAL_OUTSIDE_SCOPE = """from decimal import Decimal


def requires_human_approval(amount: Decimal) -> bool:
    # Simulated agent change: this policy edit was not admitted.
    return amount >= Decimal("100.00")
"""
PAYMENT_AUTHORIZATION = """def payment_capture_authorized() -> bool:
    return False
"""
REFUND_TESTS = """from decimal import Decimal
import unittest

from refunds.approval_policy import requires_human_approval
from refunds.calculation import calculate_refund


class RefundTests(unittest.TestCase):
    def test_restocking_fee_is_deducted(self) -> None:
        self.assertEqual(
            calculate_refund(Decimal("120.00"), Decimal("20.00")),
            Decimal("100.00"),
        )

    def test_approval_policy_boundary_is_unchanged(self) -> None:
        self.assertFalse(requires_human_approval(Decimal("100.00")))
        self.assertTrue(requires_human_approval(Decimal("100.01")))


if __name__ == "__main__":
    unittest.main()
"""


class DemoError(RuntimeError):
    """The demo cannot continue without weakening its evidence boundary."""


@dataclass(frozen=True)
class DemoResult:
    initial_scope_status: str
    initial_observed_paths: tuple[str, ...]
    initial_failed_paths: tuple[str, ...]
    initial_cycle_status: str
    selected_option_id: str
    decision_evidence: str
    corrected_failed_paths: tuple[str, ...]
    completion_status: str
    validation_outcome: str
    reconciliation_outcome: str
    final_decision_recorded: bool
    event_types: tuple[str, ...]
    transcript: str


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def _git(repository: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ("git", "-C", str(repository), *arguments),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        message = completed.stderr.decode("utf-8", errors="replace").strip()
        raise DemoError(f"Git fixture setup failed: {message}")
    return completed.stdout.decode("utf-8", errors="replace").strip()


def _event(event_type: str, *, digit: str) -> object:
    return coding_agent_event_from_payload(
        {
            "contract": "agentgov.coding-agent-event",
            "schema_version": "1.0",
            "event_id": "evt-" + digit * 32,
            "occurred_at": utc_now(),
            "event_type": event_type,
            "source": {
                "adapter_id": REFERENCE_HOST_CAPABILITIES.adapter_id,
                "actor_class": "coding_agent",
            },
            "correlation_id": "governed-refund-demo",
            "facts": {
                "validation_outcome": None,
                "evidence_ref": None,
                "scope_decision": None,
                "review_outcome": None,
            },
        }
    )


def _business_paths(report: object) -> tuple[tuple[str, bool], ...]:
    paths: list[tuple[str, bool]] = []
    for change in report.changes:
        if change.path.startswith("refunds/"):
            paths.append((change.path, change.admitted))
    return tuple(sorted(paths))


def _prepare_repository(root: Path) -> None:
    initialize_project(root, project_name="Governed Refund Demo", dry_run=False)
    _write(root / ".gitignore", "__pycache__/\n*.py[cod]\n")
    _write(root / "refunds" / "__init__.py", "")
    _write(root / "refunds" / "calculation.py", CALCULATION_BEFORE)
    _write(root / "refunds" / "approval_policy.py", APPROVAL_BEFORE)
    _write(root / "refunds" / "payment_authorization.py", PAYMENT_AUTHORIZATION)
    _write(root / "tests" / "test_refunds.py", REFUND_TESTS)
    _write(
        root / "pyproject.toml",
        "[project]\nname = \"governed-refund-demo\"\nversion = \"0.0.0\"\n",
    )
    _git(root, "init", "--quiet")
    _git(root, "config", "user.email", "fixture@example.invalid")
    _git(root, "config", "user.name", "AgentGov Demo Fixture")
    _git(root, "add", ".")
    _git(root, "commit", "--quiet", "-m", "refund fixture baseline")


def run_demo(
    *,
    decision_reader: Callable[[str], str],
    interactive_terminal: bool,
    decision_evidence: str,
    temporary_parent: Path | None = None,
    output: Callable[[str], None] | None = None,
) -> DemoResult:
    """Run one disposable demo and return its stable semantic outcome."""

    if decision_evidence not in {"human-terminal", "test-harness"}:
        raise DemoError("decision evidence must be human-terminal or test-harness")
    emitted: list[str] = []

    def emit(line: str = "") -> None:
        emitted.append(line)
        if output is not None:
            output(line)

    with TemporaryDirectory(dir=temporary_parent) as temp_dir:
        repository = Path(temp_dir) / "refund-service"
        repository.mkdir()
        _prepare_repository(repository)

        plan = build_start_plan(
            repository,
            title="Fix the refund calculation bug",
            task_id="governed-refund-demo",
            requirement=HUMAN_REQUEST,
            include_paths=ALLOWED_PATHS,
            exclude_paths=DENIED_PATHS,
            validation_commands=("python -m unittest discover -s tests -v",),
            owner="Demo fixture operator",
            actor_label="Demo fixture operator",
        )

        emit("AGENTGOV GOVERNED REFUND DEMO · development source")
        emit("[HUMAN INTENT]")
        emit(HUMAN_REQUEST)
        emit("[RECORDED BOUNDARY]")
        emit("Allowed: " + ", ".join(ALLOWED_PATHS))
        emit("Not admitted: " + ", ".join(DENIED_PATHS))
        emit("AgentGov does not infer or widen this scope.")
        emit()

        confirmed = request_start_confirmation(
            plan,
            decision_reader=decision_reader,
            is_interactive_terminal=interactive_terminal,
        )
        if not confirmed:
            raise DemoError("demo task start was not confirmed in an interactive terminal")
        apply_start_plan(plan)
        if decision_evidence == "test-harness":
            emit("[TEST-HARNESS SETUP] Task start was injected for testing; this is not human evidence.")
        else:
            emit("[HUMAN DECISION] The operator confirmed the displayed task boundary.")
        emit()

        emit("[SIMULATED AGENT BEHAVIOR]")
        emit("The demo script now changes one admitted file and one non-admitted file.")
        _write(repository / "refunds" / "calculation.py", CALCULATION_AFTER)
        _write(repository / "refunds" / "approval_policy.py", APPROVAL_OUTSIDE_SCOPE)
        emit("Changed: refunds/calculation.py")
        emit("Changed: refunds/approval_policy.py")
        emit("These file writes simulate agent behavior; AgentGov did not write them.")
        emit()

        task_path = repository / plan.session.task_path
        initial_report = check_development_scope(task_path, repository=repository)
        business_paths = _business_paths(initial_report)
        observed_paths = tuple(path for path, _ in business_paths)
        failed_paths = tuple(path for path, admitted in business_paths if not admitted)
        initial_response = run_coding_agent_event(
            repository,
            event=_event("implementation.changed", digit="1"),
            sequence=1,
            dashboard_output=Path(".agentgov/dashboard.html"),
        )

        emit("[REAL AGENTGOV EVIDENCE]")
        emit("Allowed scope vs observed scope:")
        for path, admitted in business_paths:
            emit(f"{'PASS' if admitted else 'FAIL'} {path}")
        emit(f"Deterministic scope result: {'FAIL' if initial_report.has_failures else 'PASS'}")
        emit(f"AgentGov governance cycle: {initial_response.cycle.status.upper()}")
        emit("Completion validation is blocked until the working copy returns to admitted scope.")
        emit("This does not claim that AgentGov stopped or rolled back an external coding agent.")
        emit()

        prompt = initial_response.decision_prompt
        if prompt is None:
            raise DemoError("real scope failure did not produce the expected human decision prompt")
        emit("[HUMAN DECISION REQUIRED]")
        for option in prompt.options:
            recommended = " [recommended]" if option["id"] == prompt.recommended_option_id else ""
            emit(f"{option['index']}. {option['label']}{recommended}")
        decision = request_reference_terminal_selection(
            prompt,
            decision_reader=decision_reader,
            is_interactive_terminal=interactive_terminal,
        )
        selected_option_id = str(decision.selection["option_id"])
        if decision_evidence == "test-harness":
            emit(
                f"[TEST-HARNESS INPUT] Selected {selected_option_id}; "
                "this is contract-path coverage, not human evidence."
            )
        else:
            emit(f"[HUMAN DECISION RECORDED] Selected {selected_option_id}.")
        decision_event = coding_agent_event_from_human_decision(
            initial_response,
            decision,
            event_id="evt-" + "2" * 32,
            occurred_at=utc_now(),
        )
        run_coding_agent_event(
            repository,
            event=decision_event,
            sequence=2,
            dashboard_output=Path(".agentgov/dashboard.html"),
        )
        if selected_option_id != "narrow_changes":
            raise DemoError("this bounded first demo stops unless the human selects narrow changes")
        emit("Displaying and recording this choice did not itself edit code or expand scope.")
        emit()

        emit("[SCRIPTED REMEDIATION]")
        emit("The demo script restores only refunds/approval_policy.py to its baseline content.")
        _write(repository / "refunds" / "approval_policy.py", APPROVAL_BEFORE)
        emit("The admitted calculation fix remains. AgentGov did not perform this remediation.")
        emit()

        corrected_report = check_development_scope(task_path, repository=repository)
        corrected_failed = tuple(
            path for path, admitted in _business_paths(corrected_report) if not admitted
        )
        completion_response = run_coding_agent_event(
            repository,
            event=_event("completion.requested", digit="3"),
            sequence=3,
            dashboard_output=Path(".agentgov/dashboard.html"),
        )
        outcomes = {
            str(action["name"]): str(action["outcome"])
            for action in completion_response.cycle.actions
        }
        validation_outcome = outcomes.get("run_preapproved_validation", "not_run")
        reconciliation_outcome = outcomes.get("reconcile_completion", "not_run")

        if (
            corrected_report.has_failures
            or validation_outcome != "passed"
            or reconciliation_outcome != "verified"
            or completion_response.cycle.status != "review_ready"
        ):
            raise DemoError(
                "corrected state did not produce passing, fresh, review-ready AgentGov evidence"
            )

        emit("[REAL AGENTGOV FRESH EVIDENCE]")
        emit(f"Corrected scope result: {'FAIL' if corrected_report.has_failures else 'PASS'}")
        emit(f"Pre-approved validation: {validation_outcome.upper()}")
        emit(f"Fresh completion reconciliation: {reconciliation_outcome.upper()}")
        emit(f"Final AgentGov state: {completion_response.cycle.status.upper()}")
        emit()
        emit("[FINAL HUMAN AUTHORITY]")
        emit("The work is ready for human review; this demo deliberately records no final acceptance.")
        emit("Passing evidence does not authorize commit, merge, release, publication, or deployment.")

        event_types = tuple(
            event.event_type
            for event in load_governance_events(repository / ".agentgov" / "events").events
        )
        return DemoResult(
            initial_scope_status="FAIL" if initial_report.has_failures else "PASS",
            initial_observed_paths=observed_paths,
            initial_failed_paths=failed_paths,
            initial_cycle_status=initial_response.cycle.status,
            selected_option_id=selected_option_id,
            decision_evidence=decision_evidence,
            corrected_failed_paths=corrected_failed,
            completion_status=completion_response.cycle.status,
            validation_outcome=validation_outcome,
            reconciliation_outcome=reconciliation_outcome,
            final_decision_recorded="session.reviewed" in event_types,
            event_types=event_types,
            transcript="\n".join(emitted) + "\n",
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run a disposable, evidence-backed AgentGov refund-scope demo."
    )
    parser.parse_args(argv)
    try:
        run_demo(
            decision_reader=input,
            interactive_terminal=sys.stdin.isatty(),
            decision_evidence="human-terminal",
            output=print,
        )
    except (DemoError, EOFError) as exc:
        print(f"DEMO STOPPED: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
