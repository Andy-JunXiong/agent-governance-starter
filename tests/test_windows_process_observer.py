from __future__ import annotations

import unittest

from agentgov.windows_process_observer import (
    _POWERSHELL_QUERY,
    assess_ambient_process_baseline,
    observe_windows_processes,
    reconcile_windows_processes,
)


def process_record(
    process_id: int,
    *,
    parent_process_id: int = 4,
    name: str = "unrelated.exe",
    command_line: str | None = None,
    creation_date: str | None = None,
    executable_path: str | None = None,
) -> dict[str, object]:
    return {
        "ProcessId": process_id,
        "ParentProcessId": parent_process_id,
        "Name": name,
        "ExecutablePath": executable_path,
        "CommandLine": command_line,
        "CreationDate": creation_date or f"created-{process_id}",
    }


class WindowsProcessObserverTests(unittest.TestCase):
    def test_host_query_does_not_request_executable_paths_or_usernames(self) -> None:
        self.assertNotIn("ExecutablePath", _POWERSHELL_QUERY)
        self.assertNotIn("UserName", _POWERSHELL_QUERY)

    def test_reduces_relevant_processes_to_normalized_counts(self) -> None:
        snapshot = observe_windows_processes(
            lambda: [
                process_record(10, name="Codex.exe"),
                process_record(11, name="agentgov.exe"),
                process_record(
                    12,
                    name="python.exe",
                    command_line="python -m agentgov.governance_mcp",
                ),
                process_record(13, name="notepad.exe"),
            ]
        )

        self.assertEqual(snapshot.status, "ready")
        self.assertEqual(
            snapshot.counts,
            (
                ("agentgov_service", 1),
                ("codex_host", 1),
                ("python_service", 1),
            ),
        )

    def test_snapshot_repr_excludes_raw_host_values_and_identifiers(self) -> None:
        private_command = "python PRIVATE_COMMAND_VALUE"
        private_path = "C:/PRIVATE/HOST/PATH/python.exe"
        snapshot = observe_windows_processes(
            lambda: [
                process_record(
                    987654,
                    name="python.exe",
                    command_line=private_command,
                    executable_path=private_path,
                )
            ]
        )

        rendered = repr(snapshot)
        self.assertNotIn("987654", rendered)
        self.assertNotIn(private_command, rendered)
        self.assertNotIn(private_path, rendered)

    def test_missing_candidate_command_line_fails_closed(self) -> None:
        snapshot = observe_windows_processes(
            lambda: [process_record(10, name="python.exe", command_line=None)]
        )

        self.assertEqual(snapshot.status, "indeterminate")
        self.assertIn("relevant_classification_incomplete", snapshot.reason_codes)

    def test_missing_relevant_creation_identity_fails_closed(self) -> None:
        value = process_record(10, name="codex.exe")
        value["CreationDate"] = None

        snapshot = observe_windows_processes(lambda: [value])

        self.assertEqual(snapshot.status, "indeterminate")
        self.assertIn("relevant_identity_incomplete", snapshot.reason_codes)

    def test_query_failure_is_normalized_without_exception_text(self) -> None:
        private_error = "PRIVATE QUERY ERROR"

        def fail() -> object:
            raise OSError(private_error)

        snapshot = observe_windows_processes(fail)

        self.assertEqual(snapshot.status, "indeterminate")
        self.assertEqual(snapshot.reason_codes, ("process_query_failed",))
        self.assertNotIn(private_error, repr(snapshot))

    def test_malformed_record_fails_closed(self) -> None:
        snapshot = observe_windows_processes(lambda: [{"ProcessId": 10}])

        self.assertEqual(snapshot.status, "indeterminate")
        self.assertEqual(snapshot.reason_codes, ("process_record_invalid",))

    def test_windows_idle_process_zero_identifier_is_a_valid_root_record(self) -> None:
        snapshot = observe_windows_processes(
            lambda: [
                process_record(
                    0,
                    parent_process_id=0,
                    name="System Idle Process",
                    creation_date="system-root",
                )
            ]
        )

        self.assertEqual(snapshot.status, "ready")
        self.assertEqual(snapshot.counts, ())

    def test_nonzero_ambient_baseline_is_ready(self) -> None:
        snapshot = observe_windows_processes(
            lambda: [
                process_record(10, name="codex.exe"),
                process_record(
                    11,
                    name="python.exe",
                    command_line="python -m agentgov.governance_mcp",
                ),
            ]
        )

        baseline = assess_ambient_process_baseline(snapshot)

        self.assertEqual(baseline.status, "ready")
        self.assertEqual(
            baseline.ambient_counts,
            (("codex_host", 1), ("python_service", 1)),
        )

    def test_unchanged_ambient_instances_reconcile_ready(self) -> None:
        records = [process_record(10, name="codex.exe")]
        preflight = observe_windows_processes(lambda: records)
        postflight = observe_windows_processes(lambda: records)

        boundary = reconcile_windows_processes(
            preflight, postflight, task_root_process_id=900
        )

        self.assertEqual(boundary.status, "ready")
        self.assertEqual(boundary.ambient_counts, (("codex_host", 1),))

    def test_task_descendant_remaining_is_blocked(self) -> None:
        preflight = observe_windows_processes(lambda: [])
        postflight = observe_windows_processes(
            lambda: [
                process_record(
                    901,
                    parent_process_id=900,
                    name="codex.exe",
                )
            ]
        )

        boundary = reconcile_windows_processes(
            preflight, postflight, task_root_process_id=900
        )

        self.assertEqual(boundary.status, "blocked")
        self.assertEqual(
            boundary.remaining_task_owned_counts, (("codex_host", 1),)
        )
        self.assertIn("task_owned_process_remaining", boundary.reason_codes)

    def test_same_class_replacement_cannot_hide_task_descendant(self) -> None:
        preflight = observe_windows_processes(
            lambda: [process_record(10, name="codex.exe", creation_date="old")]
        )
        postflight = observe_windows_processes(
            lambda: [
                process_record(
                    11,
                    parent_process_id=900,
                    name="codex.exe",
                    creation_date="new",
                )
            ]
        )

        boundary = reconcile_windows_processes(
            preflight, postflight, task_root_process_id=900
        )

        self.assertEqual(boundary.status, "blocked")
        self.assertEqual(boundary.preflight_counts, (("codex_host", 1),))
        self.assertEqual(boundary.postflight_counts, (("codex_host", 1),))

    def test_new_process_with_missing_ancestry_is_indeterminate(self) -> None:
        preflight = observe_windows_processes(lambda: [])
        postflight = observe_windows_processes(
            lambda: [
                process_record(
                    901,
                    parent_process_id=777,
                    name="codex.exe",
                )
            ]
        )

        boundary = reconcile_windows_processes(
            preflight, postflight, task_root_process_id=900
        )

        self.assertEqual(boundary.status, "indeterminate")
        self.assertIn("task_lineage_unknown", boundary.reason_codes)

    def test_new_non_task_relevant_process_is_indeterminate(self) -> None:
        preflight = observe_windows_processes(lambda: [])
        postflight = observe_windows_processes(
            lambda: [process_record(901, parent_process_id=4, name="codex.exe")]
        )

        boundary = reconcile_windows_processes(
            preflight, postflight, task_root_process_id=900
        )

        self.assertEqual(boundary.status, "indeterminate")
        self.assertIn("new_process_unattributed", boundary.reason_codes)

    def test_invalid_task_root_fails_closed_without_retaining_it(self) -> None:
        snapshot = observe_windows_processes(lambda: [])

        boundary = reconcile_windows_processes(
            snapshot, snapshot, task_root_process_id=-123456
        )

        self.assertEqual(boundary.status, "indeterminate")
        self.assertIn("task_root_identity_invalid", boundary.reason_codes)
        self.assertNotIn("123456", repr(boundary))

    def test_driver_python_process_is_not_misclassified_as_service(self) -> None:
        snapshot = observe_windows_processes(
            lambda: [
                process_record(
                    10,
                    name="python.exe",
                    command_line=(
                        "python -m agentgov.installed_schema_validation "
                        "--repository synthetic"
                    ),
                )
            ]
        )

        self.assertEqual(snapshot.status, "ready")
        self.assertEqual(snapshot.counts, ())


if __name__ == "__main__":
    unittest.main()
