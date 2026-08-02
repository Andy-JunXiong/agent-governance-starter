import contextlib
import io
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from agentgov.cli import EXIT_ERROR, EXIT_FAIL, EXIT_PASS, main
from agentgov.task_contract import (
    APPROVAL_STATUSES,
    DECISION_STATES,
    OBJECTIVE_ROLES,
    RISK_LEVELS,
    TASK_CONTRACT,
    TASK_PROFILES,
    TASK_SCHEMA_VERSION,
    TaskFindingStatus,
    check_development_task,
    load_development_task,
    validate_development_task_document,
)


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas/development-task.schema.json"
CURRENT_TASK = ROOT / "governance/tasks/p0-minimal-task-contract.json"
VALID_DRAFT = ROOT / "governance/fixtures/tasks/valid-supporting-draft.json"
INVALID_ADMISSION = (
    ROOT / "governance/fixtures/tasks/invalid-admitted-pending-approval.json"
)
VALID_COMPACT = ROOT / "governance/fixtures/tasks/valid-compact-admitted.json"


def run_cli(*args: str) -> tuple[int, str, str]:
    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        exit_code = main(list(args))
    return exit_code, stdout.getvalue(), stderr.getvalue()


class DevelopmentTaskContractTests(unittest.TestCase):
    def test_schema_is_strict_and_matches_validator_enums(self) -> None:
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

        self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(schema["properties"]["contract"]["const"], TASK_CONTRACT)
        self.assertEqual(
            schema["properties"]["schema_version"]["const"],
            TASK_SCHEMA_VERSION,
        )
        self.assertEqual(set(schema["properties"]["profile"]["enum"]), TASK_PROFILES)
        self.assertEqual(
            set(schema["properties"]["objective"]["properties"]["role"]["enum"]),
            OBJECTIVE_ROLES,
        )
        self.assertEqual(
            set(schema["properties"]["risk"]["properties"]["level"]["enum"]),
            RISK_LEVELS,
        )
        self.assertEqual(
            set(schema["properties"]["approval"]["properties"]["status"]["enum"]),
            APPROVAL_STATUSES,
        )
        self.assertEqual(
            set(schema["properties"]["decision"]["properties"]["state"]["enum"]),
            DECISION_STATES,
        )

    def test_current_p0_task_is_valid_and_admitted(self) -> None:
        document = load_development_task(CURRENT_TASK)

        self.assertEqual(validate_development_task_document(document), [])
        self.assertEqual(document["decision"]["state"], "admitted")
        self.assertEqual(document["profile"], "standard")
        self.assertEqual(document["objective"]["role"], "core")
        self.assertIn(
            "docs/case-studies/0001-pr-center-architecture-drift.md",
            document["requirement"]["source_refs"],
        )

    def test_admitted_task_reports_reproducible_facts_and_advisory_alignment(self) -> None:
        report = check_development_task(CURRENT_TASK, repository=ROOT)

        self.assertFalse(report.has_failures)
        self.assertEqual(report.count(TaskFindingStatus.PASS), 6)
        self.assertEqual(report.count(TaskFindingStatus.WARN), 0)
        self.assertEqual(report.count(TaskFindingStatus.FAIL), 0)
        self.assertEqual(report.count(TaskFindingStatus.ADVISORY), 1)
        alignment = next(
            finding
            for finding in report.findings
            if finding.check_id.endswith(":objective-alignment")
        )
        self.assertIn("accountable human must confirm", alignment.message)
        self.assertIn("declared core objective role", alignment.message)

    def test_draft_fixture_preserves_warning_and_advisory_states(self) -> None:
        report = check_development_task(VALID_DRAFT, repository=ROOT)

        self.assertFalse(report.has_failures)
        self.assertEqual(report.count(TaskFindingStatus.PASS), 2)
        self.assertEqual(report.count(TaskFindingStatus.WARN), 3)
        self.assertEqual(report.count(TaskFindingStatus.ADVISORY), 2)
        self.assertTrue(
            any("no architecture reference" in item.message for item in report.findings)
        )
        self.assertTrue(
            any("implementation is not admitted" in item.message for item in report.findings)
        )

    def test_compact_profile_is_low_friction_and_keeps_human_advisories(self) -> None:
        document = load_development_task(VALID_COMPACT)

        self.assertEqual(validate_development_task_document(document), [])
        self.assertEqual(document["profile"], "compact")
        for omitted in (
            "objective",
            "goal",
            "non_goals",
            "architecture_refs",
            "approval",
            "stop_conditions",
        ):
            self.assertNotIn(omitted, document)

        report = check_development_task(VALID_COMPACT, repository=ROOT)
        self.assertFalse(report.has_failures)
        self.assertTrue(
            any("compact task omits a parent objective" in item.message for item in report.findings)
        )
        self.assertTrue(
            any("compact task still advances" in item.message for item in report.findings)
        )

    def test_compact_profile_rejects_non_low_risk(self) -> None:
        document = dict(load_development_task(VALID_COMPACT))
        document["risk"] = {"level": "medium", "items": ["Needs standard profile"]}

        errors = validate_development_task_document(document)

        self.assertIn("$.risk.level must equal 'low' for compact tasks", errors)

    def test_inconsistent_admission_fails_deterministically(self) -> None:
        document = load_development_task(INVALID_ADMISSION)

        errors = validate_development_task_document(document)

        self.assertIn(
            "$.approval.status must be 'approved' before an approval-required task is admitted",
            errors,
        )

    def test_unsafe_scope_paths_fail_structural_validation(self) -> None:
        document = dict(load_development_task(CURRENT_TASK))
        document["scope"] = {
            "include_paths": ["../outside"],
            "exclude_paths": [],
        }

        errors = validate_development_task_document(document)

        self.assertTrue(any("parent traversal" in error for error in errors))

    def test_missing_declared_reference_is_a_deterministic_failure(self) -> None:
        with TemporaryDirectory(dir=ROOT) as temp_dir:
            repository = Path(temp_dir)
            task_path = repository / "task.json"
            document = dict(load_development_task(VALID_DRAFT))
            document["objective"] = {
                "role": "supporting",
                "parent_refs": ["docs/missing-parent.md"],
                "rationale": "This intentionally names a missing parent reference.",
            }
            task_path.write_text(
                json.dumps(document, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

            report = check_development_task(task_path, repository=repository)

        self.assertTrue(report.has_failures)
        finding = next(
            item for item in report.findings if item.check_id.endswith(":objective")
        )
        self.assertIs(finding.status, TaskFindingStatus.FAIL)
        self.assertIn("does not exist", finding.message)

    def test_check_is_read_only(self) -> None:
        before = CURRENT_TASK.read_bytes()
        report = check_development_task(CURRENT_TASK, repository=ROOT)
        after = CURRENT_TASK.read_bytes()

        self.assertFalse(report.has_failures)
        self.assertEqual(after, before)

    def test_cli_returns_pass_for_admitted_task_and_prints_advisory(self) -> None:
        exit_code, stdout, stderr = run_cli(
            "check",
            "task",
            str(CURRENT_TASK),
            "--repository",
            str(ROOT),
        )

        self.assertEqual(exit_code, EXIT_PASS)
        self.assertIn("PASS task:p0-minimal-task-contract:contract", stdout)
        self.assertIn(
            "ADVISORY task:p0-minimal-task-contract:objective-alignment",
            stdout,
        )
        self.assertIn("validation was read-only", stdout)
        self.assertEqual(stderr, "")

    def test_cli_returns_fail_for_contract_violation(self) -> None:
        exit_code, stdout, stderr = run_cli(
            "check",
            "task",
            str(INVALID_ADMISSION),
            "--repository",
            str(ROOT),
        )

        self.assertEqual(exit_code, EXIT_FAIL)
        self.assertIn("FAIL task:invalid-admission:contract", stdout)
        self.assertIn("before an approval-required task is admitted", stdout)
        self.assertEqual(stderr, "")

    def test_cli_returns_operational_error_for_missing_task(self) -> None:
        missing = ROOT / "governance/tasks/missing.json"

        exit_code, stdout, stderr = run_cli(
            "check",
            "task",
            str(missing),
            "--repository",
            str(ROOT),
        )

        self.assertEqual(exit_code, EXIT_ERROR)
        self.assertEqual(stdout, "")
        self.assertIn("ERROR task: file or repository not found", stderr)


if __name__ == "__main__":
    unittest.main()
