import contextlib
import hashlib
import io
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from agentgov.cli import EXIT_ERROR, EXIT_FAIL, EXIT_PASS, main
from agentgov.documentation_archive import (
    ARCHIVE_PLAN_CONTRACT,
    ARCHIVE_PLAN_SCHEMA_VERSION,
    ArchiveFindingStatus,
    ArchivePlanState,
    DocumentationArchiveApplyError,
    DEVELOPMENT_LOG_INDEX,
    apply_documentation_archive_plan,
    documentation_archive_plan_document,
    parse_through_date,
    plan_documentation_archive,
    render_documentation_archive_plan_json,
)


ROOT = Path(__file__).resolve().parents[1]
CASES = json.loads(
    (ROOT / "tests/fixtures/documentation-archive/cases.json").read_text(
        encoding="utf-8"
    )
)


def run_cli(*args: str) -> tuple[int, str, str]:
    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        exit_code = main(list(args))
    return exit_code, stdout.getvalue(), stderr.getvalue()


def materialize_case(root: Path, name: str) -> dict[str, object]:
    case = CASES[name]
    log_directory = root / "docs/development-log"
    log_directory.mkdir(parents=True)
    for filename, content in case["files"].items():
        (log_directory / filename).write_text(content, encoding="utf-8")
    return case


def snapshot(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def dated_log_snapshot(root: Path) -> dict[str, bytes]:
    return {
        path.name: path.read_bytes()
        for path in sorted((root / "docs/development-log").glob("20*.md"))
    }


class DocumentationArchivePlanTests(unittest.TestCase):
    def test_passing_plan_is_stable_read_only_and_same_day_safe(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            case = materialize_case(root, "passing")
            before = snapshot(root)

            plan = plan_documentation_archive(
                root, through_date=parse_through_date(case["through"])
            )
            after = snapshot(root)
            index_exists = (root / DEVELOPMENT_LOG_INDEX).exists()

        self.assertIs(plan.state, ArchivePlanState.PASS)
        self.assertEqual(before, after)
        self.assertEqual(
            [entry.path.name for entry in plan.entries],
            [
                "2026-08-14-historical-migration.md",
                "2026-08-14.md",
                "2026-08-13.md",
            ],
        )
        self.assertEqual(plan.change.action, "create")
        self.assertIsNone(plan.change.before_sha256)
        self.assertIn("(2026-08-14-historical-migration.md)", plan.change.content)
        self.assertIn("(2026-08-14.md)", plan.change.content)
        self.assertNotIn("sha256:", plan.change.content)
        self.assertNotIn("No repository file was written", plan.change.content)
        self.assertFalse(index_exists)
        self.assertEqual(
            hashlib.sha256(plan.change.content.encode("utf-8")).hexdigest(),
            plan.change.after_sha256,
        )

    def test_warning_uses_deterministic_title_fallback(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            case = materialize_case(root, "warning")

            plan = plan_documentation_archive(
                root, through_date=parse_through_date(case["through"])
            )

        self.assertIs(plan.state, ArchivePlanState.WARN)
        self.assertEqual(plan.entries[0].title, "2026 08 14")
        self.assertIn(
            "missing_primary_title",
            {finding.code for finding in plan.findings},
        )

    def test_invalid_calendar_filename_is_a_deterministic_failure(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            case = materialize_case(root, "failing")
            before = snapshot(root)

            plan = plan_documentation_archive(
                root, through_date=parse_through_date(case["through"])
            )
            after = snapshot(root)

        self.assertIs(plan.state, ArchivePlanState.FAIL)
        self.assertIsNone(plan.change)
        self.assertEqual(before, after)
        failure = next(item for item in plan.findings if item.code == "invalid_log_date")
        self.assertIs(failure.status, ArchiveFindingStatus.FAIL)
        self.assertEqual(failure.semantics, "deterministic")

    def test_future_and_non_dated_records_are_not_applicable(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            case = materialize_case(root, "not_applicable")

            plan = plan_documentation_archive(
                root, through_date=parse_through_date(case["through"])
            )

        self.assertIs(plan.state, ArchivePlanState.NOT_APPLICABLE)
        self.assertEqual(plan.entries, ())
        self.assertIn("_No eligible dated records._", plan.change.content)
        statuses = {finding.status for finding in plan.findings}
        self.assertIn(ArchiveFindingStatus.NOT_APPLICABLE, statuses)
        self.assertIn(ArchiveFindingStatus.ADVISORY, statuses)

    def test_existing_index_plans_update_then_none_without_writing(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            case = materialize_case(root, "passing")
            index = root / DEVELOPMENT_LOG_INDEX
            index.write_text("# Stale index\n", encoding="utf-8")

            update = plan_documentation_archive(
                root, through_date=parse_through_date(case["through"])
            )
            self.assertEqual(update.change.action, "update")
            self.assertEqual(index.read_text(encoding="utf-8"), "# Stale index\n")

            index.write_bytes(update.change.content.encode("utf-8"))
            before = snapshot(root)
            current = plan_documentation_archive(
                root, through_date=parse_through_date(case["through"])
            )
            after = snapshot(root)

        self.assertEqual(current.change.action, "none")
        self.assertEqual(current.change.before_sha256, current.change.after_sha256)
        self.assertEqual(before, after)

    def test_apply_exclusively_creates_then_noops_without_mutating_logs(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            case = materialize_case(root, "passing")
            before_logs = dated_log_snapshot(root)
            create = plan_documentation_archive(
                root, through_date=parse_through_date(case["through"])
            )

            created = apply_documentation_archive_plan(create)
            after_create_logs = dated_log_snapshot(root)
            current = plan_documentation_archive(
                root, through_date=parse_through_date(case["through"])
            )
            before_noop = snapshot(root)
            unchanged = apply_documentation_archive_plan(current)
            after_noop = snapshot(root)

        self.assertEqual(created.action, "create")
        self.assertEqual(unchanged.action, "none")
        self.assertEqual(before_logs, after_create_logs)
        self.assertEqual(before_noop, after_noop)
        self.assertEqual(current.change.before_sha256, current.change.after_sha256)

    def test_apply_atomically_updates_and_removes_temporary_file(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            case = materialize_case(root, "passing")
            index = root / DEVELOPMENT_LOG_INDEX
            index.write_text("# Stale index\n", encoding="utf-8")
            before_logs = dated_log_snapshot(root)
            update = plan_documentation_archive(
                root, through_date=parse_through_date(case["through"])
            )

            result = apply_documentation_archive_plan(update)

            self.assertEqual(result.action, "update")
            self.assertEqual(index.read_text(encoding="utf-8"), update.change.content)
            self.assertEqual(before_logs, dated_log_snapshot(root))
            self.assertEqual(list(index.parent.glob(".INDEX.md.agentgov-*.tmp")), [])

    def test_apply_rejects_stale_source_and_target_without_writing(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            case = materialize_case(root, "passing")
            create = plan_documentation_archive(
                root, through_date=parse_through_date(case["through"])
            )
            source = root / "docs/development-log/2026-08-13.md"
            source.write_text("# Changed after preview\n", encoding="utf-8")

            with self.assertRaisesRegex(DocumentationArchiveApplyError, "stale"):
                apply_documentation_archive_plan(create)
            self.assertFalse((root / DEVELOPMENT_LOG_INDEX).exists())

            index = root / DEVELOPMENT_LOG_INDEX
            index.write_text("# First stale index\n", encoding="utf-8")
            update = plan_documentation_archive(
                root, through_date=parse_through_date(case["through"])
            )
            index.write_text("# Competing index\n", encoding="utf-8")

            with self.assertRaisesRegex(DocumentationArchiveApplyError, "stale"):
                apply_documentation_archive_plan(update)
            self.assertEqual(index.read_text(encoding="utf-8"), "# Competing index\n")

    def test_update_failure_preserves_target_and_cleans_temporary_file(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            case = materialize_case(root, "passing")
            index = root / DEVELOPMENT_LOG_INDEX
            index.write_text("# Stale index\n", encoding="utf-8")
            update = plan_documentation_archive(
                root, through_date=parse_through_date(case["through"])
            )

            with patch("agentgov.documentation_archive.os.replace", side_effect=OSError("blocked")):
                with self.assertRaisesRegex(OSError, "blocked"):
                    apply_documentation_archive_plan(update)

            self.assertEqual(index.read_text(encoding="utf-8"), "# Stale index\n")
            self.assertEqual(list(index.parent.glob(".INDEX.md.agentgov-*.tmp")), [])

    def test_apply_rejects_unsafe_index_target_without_writing(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            case = materialize_case(root, "passing")
            index = root / DEVELOPMENT_LOG_INDEX
            index.mkdir()
            before = snapshot(root)
            failed = plan_documentation_archive(
                root, through_date=parse_through_date(case["through"])
            )

            with self.assertRaisesRegex(
                DocumentationArchiveApplyError, "failed.*cannot be applied"
            ):
                apply_documentation_archive_plan(failed)

            self.assertEqual(before, snapshot(root))
            self.assertTrue(index.is_dir())

    def test_cli_apply_requires_interactive_exact_confirmation(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            case = materialize_case(root, "passing")
            before = snapshot(root)

            json_apply = run_cli(
                "plan", "documentation-archive", str(root),
                "--through", case["through"], "--format", "json", "--apply",
            )
            with patch("sys.stdin.isatty", return_value=False):
                noninteractive = run_cli(
                    "plan", "documentation-archive", str(root),
                    "--through", case["through"], "--apply",
                )
            with patch("sys.stdin.isatty", return_value=True), patch(
                "builtins.input", return_value="NO"
            ):
                declined = run_cli(
                    "plan", "documentation-archive", str(root),
                    "--through", case["through"], "--apply",
                )
            with patch("sys.stdin.isatty", return_value=True), patch(
                "builtins.input", side_effect=EOFError
            ):
                interrupted = run_cli(
                    "plan", "documentation-archive", str(root),
                    "--through", case["through"], "--apply",
                )
            after_decline = snapshot(root)
            with patch("sys.stdin.isatty", return_value=True), patch(
                "builtins.input", return_value="APPLY INDEX"
            ):
                confirmed = run_cli(
                    "plan", "documentation-archive", str(root),
                    "--through", case["through"], "--apply",
                )

        self.assertEqual(json_apply[0], EXIT_ERROR)
        self.assertIn("requires text format", json_apply[2])
        self.assertEqual(noninteractive[0], EXIT_FAIL)
        self.assertIn("interactive terminal", noninteractive[2])
        self.assertEqual(declined[0], EXIT_FAIL)
        self.assertIn("CANCELLED", declined[2])
        self.assertEqual(interrupted[0], EXIT_FAIL)
        self.assertIn("CANCELLED", interrupted[2])
        self.assertEqual(before, after_decline)
        self.assertEqual(confirmed[0], EXIT_PASS)
        self.assertIn("APPLIED create docs/development-log/INDEX.md", confirmed[1])

    def test_contract_document_separates_findings_and_denies_authority(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            case = materialize_case(root, "passing")
            plan = plan_documentation_archive(
                root, through_date=parse_through_date(case["through"])
            )

        document = documentation_archive_plan_document(plan)
        self.assertEqual(document["contract"], ARCHIVE_PLAN_CONTRACT)
        self.assertEqual(document["schema_version"], ARCHIVE_PLAN_SCHEMA_VERSION)
        self.assertFalse(document["eligibility"]["uses_host_clock"])
        self.assertTrue(document["eligibility"]["preserves_source_paths"])
        self.assertIn(
            ("advisory", "advisory"),
            {(item["status"], item["semantics"]) for item in document["findings"]},
        )
        self.assertTrue(all(value is False for value in document["authority_boundary"].values()))
        self.assertIn("apply_authorized", document["authority_boundary"])
        self.assertIn("scheduling_authorized", document["authority_boundary"])
        self.assertTrue(all(len(entry["sha256"]) == 64 for entry in document["entries"]))
        self.assertNotIn("sha256:", document["change"]["content"])
        self.assertEqual(json.loads(render_documentation_archive_plan_json(plan)), document)

    def test_schema_is_strict_and_matches_runtime_authority(self) -> None:
        schema = json.loads(
            (ROOT / "schemas/documentation-archive-plan.schema.json").read_text(
                encoding="utf-8"
            )
        )

        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(schema["properties"]["contract"]["const"], ARCHIVE_PLAN_CONTRACT)
        self.assertEqual(
            schema["properties"]["schema_version"]["const"],
            ARCHIVE_PLAN_SCHEMA_VERSION,
        )
        self.assertEqual(
            set(schema["properties"]["state"]["enum"]),
            {item.value for item in ArchivePlanState},
        )
        authority = schema["properties"]["authority_boundary"]["properties"]
        self.assertTrue(all(item["const"] is False for item in authority.values()))

    def test_cli_renders_json_and_terminal_without_writing(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            case = materialize_case(root, "passing")
            before = snapshot(root)

            json_code, json_out, json_err = run_cli(
                "plan",
                "documentation-archive",
                str(root),
                "--through",
                case["through"],
                "--format",
                "json",
            )
            text_code, text_out, text_err = run_cli(
                "plan",
                "documentation-archive",
                str(root),
                "--through",
                case["through"],
            )
            after = snapshot(root)

        self.assertEqual((json_code, text_code), (EXIT_PASS, EXIT_PASS))
        self.assertEqual((json_err, text_err), ("", ""))
        self.assertEqual(json.loads(json_out)["state"], "pass")
        self.assertIn("STATE pass", text_out)
        self.assertIn("CONTENT-BEGIN", text_out)
        self.assertIn("no index, source log, apply, scheduling, Git", text_out)
        self.assertEqual(before, after)

    def test_cli_failure_and_invalid_through_date_are_bounded(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            case = materialize_case(root, "failing")
            before = snapshot(root)

            fail_code, fail_out, fail_err = run_cli(
                "plan",
                "documentation-archive",
                str(root),
                "--through",
                case["through"],
            )
            error_code, error_out, error_err = run_cli(
                "plan",
                "documentation-archive",
                str(root),
                "--through",
                "2026-02-30",
            )
            after = snapshot(root)

        self.assertEqual(fail_code, EXIT_FAIL)
        self.assertIn("STATE fail", fail_out)
        self.assertEqual(fail_err, "")
        self.assertEqual(error_code, EXIT_ERROR)
        self.assertEqual(error_out, "")
        self.assertIn("valid calendar date", error_err)
        self.assertEqual(before, after)

    def test_missing_log_directory_returns_fail_plan_not_a_write(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)

            plan = plan_documentation_archive(
                root, through_date=parse_through_date("2026-08-14")
            )

        self.assertIs(plan.state, ArchivePlanState.FAIL)
        self.assertEqual(plan.findings[0].code, "log_directory_missing")
        self.assertIsNone(plan.change)


if __name__ == "__main__":
    unittest.main()
