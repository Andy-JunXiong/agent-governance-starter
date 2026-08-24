from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agentgov.installed_schema_validation import (
    GenerationOutcome,
    _HostState,
    _default_temp_cleanup,
    _load_schema_documents,
    _verified_temp_directory,
    run_installed_schema_validation,
)
from agentgov.windows_process_observer import observe_windows_processes


def compatible_schema() -> dict[str, object]:
    return {
        "type": "object",
        "properties": {
            "method": {"const": "thread/start"},
            "params": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "approvalPolicy",
                    "cwd",
                    "ephemeral",
                    "sandbox",
                ],
                "properties": {
                    "approvalPolicy": {
                        "type": "string",
                        "enum": ["never"],
                    },
                    "cwd": {"type": "string"},
                    "ephemeral": {"type": "boolean"},
                    "sandbox": {
                        "type": "string",
                        "enum": ["workspace-write"],
                    },
                },
            },
        },
    }


def stable_state(marker: str = "same") -> _HostState:
    return _HostState("ready", 0, (), marker, marker)


def ready_snapshot():
    return observe_windows_processes(lambda: [])


class InstalledSchemaValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.command_directory = tempfile.TemporaryDirectory()
        self.entry = Path(self.command_directory.name) / "codex.cmd"
        self.entry.write_text("@echo off\n", encoding="utf-8")

    def tearDown(self) -> None:
        self.command_directory.cleanup()

    def run_driver(self, **overrides):
        options = {
            "command_entries": lambda: [self.entry],
            "help_probe": lambda _entry: None,
            "process_observer": ready_snapshot,
            "state_probe": lambda _repository: stable_state(),
        }
        options.update(overrides)
        return run_installed_schema_validation(Path("."), **options)

    def test_compatible_schema_completes_once_and_cleans_exact_directory(self) -> None:
        attempts: list[Path] = []

        def generate(_entry: Path, output: Path, _repository: Path):
            attempts.append(output)
            (output / "bundle.json").write_text(
                json.dumps(compatible_schema()), encoding="utf-8"
            )
            return GenerationOutcome("schema_generation_completed", 0, 900)

        result = self.run_driver(generation_runner=generate)

        self.assertEqual(result.status, "compatible")
        self.assertEqual(result.stage, "completed")
        self.assertEqual(result.generation_attempts, 1)
        self.assertEqual(result.help_queries, 1)
        self.assertEqual(result.document_count, 1)
        self.assertTrue(result.cleanup_verified)
        self.assertTrue(result.host_state_unchanged)
        self.assertEqual(len(attempts), 1)
        self.assertFalse(attempts[0].exists())
        self.assertIn("validation_completed", result.reason_codes)

    def test_incompatible_schema_is_a_bounded_completed_result(self) -> None:
        schema = compatible_schema()
        params = schema["properties"]["params"]  # type: ignore[index]
        params["properties"]["sandbox"]["enum"] = ["read-only"]  # type: ignore[index]

        def generate(_entry: Path, output: Path, _repository: Path):
            (output / "bundle.json").write_text(
                json.dumps(schema), encoding="utf-8"
            )
            return GenerationOutcome("schema_generation_completed", 0, 900)

        result = self.run_driver(generation_runner=generate)

        self.assertEqual(result.status, "incompatible")
        self.assertEqual(result.stage, "completed")
        self.assertIn("string_enum_incompatible", result.reason_codes)
        self.assertNotIn("workspace-write", repr(result))

    def test_invalid_json_stops_without_retry_and_cleans(self) -> None:
        attempts = 0
        created: list[Path] = []

        def generate(_entry: Path, output: Path, _repository: Path):
            nonlocal attempts
            attempts += 1
            created.append(output)
            (output / "bundle.json").write_text("{invalid", encoding="utf-8")
            return GenerationOutcome("schema_generation_completed", 0, 900)

        result = self.run_driver(generation_runner=generate)

        self.assertEqual(result.status, "indeterminate")
        self.assertEqual(result.stage, "schema_discovery")
        self.assertIn("schema_document_invalid", result.reason_codes)
        self.assertEqual(attempts, 1)
        self.assertFalse(created[0].exists())

    def test_non_json_generated_entry_is_rejected(self) -> None:
        def generate(_entry: Path, output: Path, _repository: Path):
            (output / "schema.txt").write_text("not retained", encoding="utf-8")
            return GenerationOutcome("schema_generation_completed", 0, 900)

        result = self.run_driver(generation_runner=generate)

        self.assertEqual(result.status, "indeterminate")
        self.assertIn("generated_non_json_entry_rejected", result.reason_codes)

    def test_generated_symbolic_link_is_rejected_without_following_it(self) -> None:
        directory = Path(tempfile.mkdtemp(prefix="agentgov-installed-schema-v2-"))
        self.addCleanup(lambda: _default_temp_cleanup(directory))
        target = directory / "target.json"
        target.write_text(json.dumps(compatible_schema()), encoding="utf-8")
        link = directory / "link.json"
        try:
            link.symlink_to(target)
        except OSError:
            self.skipTest("file symlinks are unavailable")

        loaded = _load_schema_documents(directory)

        self.assertEqual(loaded.status, "indeterminate")
        self.assertIn("generated_link_rejected", loaded.findings)

    def test_symbolic_link_temporary_root_is_rejected_before_resolution(self) -> None:
        with patch.object(Path, "is_symlink", return_value=True):
            verified = _verified_temp_directory(Path(tempfile.gettempdir()))

        self.assertIsNone(verified)

    def test_command_selection_rejects_script_wrapper_before_help(self) -> None:
        wrapper = Path(self.command_directory.name) / "codex.ps1"
        wrapper.write_text("Write-Output blocked\n", encoding="utf-8")
        help_calls = 0

        def help_probe(_entry: Path) -> str | None:
            nonlocal help_calls
            help_calls += 1
            return None

        result = self.run_driver(
            command_entries=lambda: [wrapper], help_probe=help_probe
        )

        self.assertEqual(result.stage, "command_discovery")
        self.assertIn("native_entry_not_found", result.reason_codes)
        self.assertEqual(help_calls, 0)
        self.assertEqual(result.generation_attempts, 0)

    def test_multiple_native_entries_are_rejected(self) -> None:
        second_directory = tempfile.TemporaryDirectory()
        self.addCleanup(second_directory.cleanup)
        second = Path(second_directory.name) / "codex.cmd"
        second.write_text("@echo off\n", encoding="utf-8")

        result = self.run_driver(command_entries=lambda: [self.entry, second])

        self.assertEqual(result.stage, "command_discovery")
        self.assertIn("native_entry_ambiguous", result.reason_codes)

    def test_unexpected_help_surface_stops_before_observation(self) -> None:
        observations = 0

        def observer():
            nonlocal observations
            observations += 1
            return ready_snapshot()

        result = self.run_driver(
            help_probe=lambda _entry: "schema_help_surface_unexpected",
            process_observer=observer,
        )

        self.assertEqual(result.stage, "command_help")
        self.assertEqual(result.help_queries, 1)
        self.assertEqual(observations, 0)

    def test_incomplete_process_observation_prevents_generation(self) -> None:
        incomplete = observe_windows_processes(
            lambda: [
                {
                    "ProcessId": 10,
                    "ParentProcessId": 4,
                    "Name": "python.exe",
                    "ExecutablePath": None,
                    "CommandLine": None,
                    "CreationDate": "created",
                }
            ]
        )
        attempts = 0

        def generate(_entry: Path, _output: Path, _repository: Path):
            nonlocal attempts
            attempts += 1
            return GenerationOutcome("schema_generation_completed", 0, 900)

        result = self.run_driver(
            process_observer=lambda: incomplete, generation_runner=generate
        )

        self.assertEqual(result.stage, "process_preflight")
        self.assertIn("relevant_classification_incomplete", result.reason_codes)
        self.assertEqual(attempts, 0)

    def test_nonzero_ambient_process_is_allowed(self) -> None:
        ambient = observe_windows_processes(
            lambda: [
                {
                    "ProcessId": 10,
                    "ParentProcessId": 4,
                    "Name": "codex.exe",
                    "ExecutablePath": None,
                    "CommandLine": None,
                    "CreationDate": "ambient",
                }
            ]
        )

        def generate(_entry: Path, output: Path, _repository: Path):
            (output / "bundle.json").write_text(
                json.dumps(compatible_schema()), encoding="utf-8"
            )
            return GenerationOutcome("schema_generation_completed", 0, 900)

        result = self.run_driver(
            process_observer=lambda: ambient, generation_runner=generate
        )

        self.assertEqual(result.status, "compatible")
        self.assertEqual(result.ambient_counts, (("codex_host", 1),))

    def test_task_descendant_remaining_blocks_analysis(self) -> None:
        preflight = ready_snapshot()
        postflight = observe_windows_processes(
            lambda: [
                {
                    "ProcessId": 901,
                    "ParentProcessId": 900,
                    "Name": "codex.exe",
                    "ExecutablePath": None,
                    "CommandLine": None,
                    "CreationDate": "task-child",
                }
            ]
        )
        snapshots = iter((preflight, postflight))

        def generate(_entry: Path, output: Path, _repository: Path):
            (output / "bundle.json").write_text(
                json.dumps(compatible_schema()), encoding="utf-8"
            )
            return GenerationOutcome("schema_generation_completed", 0, 900)

        result = self.run_driver(
            process_observer=lambda: next(snapshots),
            generation_runner=generate,
        )

        self.assertEqual(result.status, "indeterminate")
        self.assertEqual(result.stage, "process_postflight")
        self.assertIn("task_owned_process_remaining", result.reason_codes)
        self.assertEqual(result.document_count, 0)

    def test_generation_nonzero_is_not_retried(self) -> None:
        snapshots = iter((ready_snapshot(), ready_snapshot()))
        attempts = 0

        def generate(_entry: Path, _output: Path, _repository: Path):
            nonlocal attempts
            attempts += 1
            return GenerationOutcome("schema_generation_nonzero", 2, 900)

        result = self.run_driver(
            process_observer=lambda: next(snapshots),
            generation_runner=generate,
        )

        self.assertEqual(result.status, "indeterminate")
        self.assertIn("schema_generation_nonzero", result.reason_codes)
        self.assertEqual(attempts, 1)
        self.assertEqual(result.generation_attempts, 1)

    def test_cleanup_failure_is_reported_after_exact_directory_is_removed(self) -> None:
        created: list[Path] = []

        def generate(_entry: Path, output: Path, _repository: Path):
            created.append(output)
            (output / "bundle.json").write_text(
                json.dumps(compatible_schema()), encoding="utf-8"
            )
            return GenerationOutcome("schema_generation_completed", 0, 900)

        def cleanup_but_report_failure(path: Path) -> bool:
            self.assertTrue(_default_temp_cleanup(path))
            return False

        result = self.run_driver(
            generation_runner=generate,
            temp_cleanup=cleanup_but_report_failure,
        )

        self.assertEqual(result.stage, "cleanup")
        self.assertIn("temporary_cleanup_unverified", result.reason_codes)
        self.assertFalse(created[0].exists())

    def test_changed_host_state_is_reported_without_fingerprint_values(self) -> None:
        states = iter((stable_state("before"), stable_state("after")))

        def generate(_entry: Path, output: Path, _repository: Path):
            (output / "bundle.json").write_text(
                json.dumps(compatible_schema()), encoding="utf-8"
            )
            return GenerationOutcome("schema_generation_completed", 0, 900)

        result = self.run_driver(
            generation_runner=generate,
            state_probe=lambda _repository: next(states),
        )

        self.assertEqual(result.stage, "host_state_postflight")
        self.assertIn("host_state_changed_or_unavailable", result.reason_codes)
        self.assertNotIn("before", repr(result))
        self.assertNotIn("after", repr(result))

    def test_public_dictionary_contains_only_normalized_evidence(self) -> None:
        private_path = "C:/PRIVATE/HOST/PATH"

        def generate(_entry: Path, output: Path, _repository: Path):
            (output / "bundle.json").write_text(
                json.dumps(compatible_schema()), encoding="utf-8"
            )
            return GenerationOutcome("schema_generation_completed", 0, 987654)

        result = self.run_driver(generation_runner=generate)
        rendered = json.dumps(result.as_dict(), sort_keys=True)

        self.assertNotIn(private_path, rendered)
        self.assertNotIn("987654", rendered)
        self.assertNotIn(str(self.entry), rendered)


if __name__ == "__main__":
    unittest.main()
