from __future__ import annotations

import builtins
import socket
import subprocess
import unittest
import urllib.request
from unittest.mock import patch

from agentgov.process_attribution_gate import (
    ProcessAttributionFinding,
    ProcessAttributionGateResult,
    assess_process_attribution_gate,
    classify_process_observation,
)


def observation(
    process_class: str = "codex_host",
    *,
    preflight: bool,
    postflight: bool,
    lineage: str,
    complete: bool = True,
) -> dict[str, object]:
    return {
        "process_class": process_class,
        "present_at_preflight": preflight,
        "present_at_postflight": postflight,
        "task_lineage": lineage,
        "identity_complete": complete,
    }


class ProcessAttributionGateTests(unittest.TestCase):
    def assert_finding(
        self,
        result: ProcessAttributionGateResult,
        code: str,
        process_class: str | None = None,
    ) -> None:
        self.assertIn(
            ProcessAttributionFinding(code, process_class), result.findings
        )

    def test_zero_process_boundary_is_ready(self) -> None:
        result = assess_process_attribution_gate({}, {}, [])

        self.assertEqual(result.status, "ready")
        self.assertEqual(result.findings, ())

    def test_nonzero_complete_ambient_baseline_is_ready(self) -> None:
        observations = [
            observation(
                "codex_host",
                preflight=True,
                postflight=True,
                lineage="not_task_tree",
            ),
            observation(
                "agentgov_service",
                preflight=True,
                postflight=True,
                lineage="not_task_tree",
            ),
        ]

        result = assess_process_attribution_gate(
            {"codex_host": 1, "agentgov_service": 1},
            {"codex_host": 1, "agentgov_service": 1},
            observations,
        )

        self.assertEqual(result.status, "ready")
        self.assertEqual(
            result.ambient_counts,
            (("agentgov_service", 1), ("codex_host", 1)),
        )

    def test_task_descendant_that_exits_is_ready(self) -> None:
        observations = [
            observation(
                preflight=False,
                postflight=False,
                lineage="task_root_or_descendant",
            )
        ]

        result = assess_process_attribution_gate({}, {}, observations)

        self.assertEqual(result.status, "ready")
        self.assertEqual(result.task_owned_counts, (("codex_host", 1),))
        self.assertEqual(result.remaining_task_owned_counts, ())

    def test_remaining_task_descendant_blocks(self) -> None:
        observations = [
            observation(
                preflight=False,
                postflight=True,
                lineage="task_root_or_descendant",
            )
        ]

        result = assess_process_attribution_gate(
            {}, {"codex_host": 1}, observations
        )

        self.assertEqual(result.status, "blocked")
        self.assert_finding(
            result, "task_owned_process_remaining", "codex_host"
        )
        self.assertEqual(result.new_remaining_counts, (("codex_host", 1),))

    def test_same_class_replacement_cannot_hide_task_process(self) -> None:
        observations = [
            observation(
                preflight=True,
                postflight=False,
                lineage="not_task_tree",
            ),
            observation(
                preflight=False,
                postflight=True,
                lineage="task_root_or_descendant",
            ),
        ]

        result = assess_process_attribution_gate(
            {"codex_host": 1}, {"codex_host": 1}, observations
        )

        self.assertEqual(result.status, "blocked")
        self.assertEqual(result.new_remaining_counts, ())
        self.assertEqual(
            result.remaining_task_owned_counts, (("codex_host", 1),)
        )

    def test_duplicate_normalized_classes_are_counted_as_a_multiset(self) -> None:
        observations = [
            observation(
                "python_service",
                preflight=True,
                postflight=True,
                lineage="not_task_tree",
            ),
            observation(
                "python_service",
                preflight=True,
                postflight=True,
                lineage="not_task_tree",
            ),
        ]

        result = assess_process_attribution_gate(
            {"python_service": 2}, {"python_service": 2}, observations
        )

        self.assertEqual(result.status, "ready")
        self.assertEqual(result.ambient_counts, (("python_service", 2),))

    def test_new_non_task_process_is_indeterminate(self) -> None:
        value = observation(
            preflight=False,
            postflight=True,
            lineage="not_task_tree",
        )

        attribution = classify_process_observation(value)
        result = assess_process_attribution_gate({}, {"codex_host": 1}, [value])

        self.assertEqual(attribution.status, "indeterminate")
        self.assertIn("new_process_unattributed", attribution.reason_codes)
        self.assertEqual(result.status, "indeterminate")

    def test_incomplete_identity_is_indeterminate(self) -> None:
        value = observation(
            preflight=True,
            postflight=True,
            lineage="not_task_tree",
            complete=False,
        )

        result = assess_process_attribution_gate(
            {"codex_host": 1}, {"codex_host": 1}, [value]
        )

        self.assertEqual(result.status, "indeterminate")
        self.assert_finding(result, "identity_incomplete", "codex_host")

    def test_unknown_lineage_is_indeterminate(self) -> None:
        value = observation(
            preflight=True,
            postflight=True,
            lineage="unknown",
        )

        result = assess_process_attribution_gate(
            {"codex_host": 1}, {"codex_host": 1}, [value]
        )

        self.assertEqual(result.status, "indeterminate")
        self.assert_finding(result, "task_lineage_unknown", "codex_host")

    def test_preflight_task_lineage_conflict_is_indeterminate(self) -> None:
        value = observation(
            preflight=True,
            postflight=True,
            lineage="task_root_or_descendant",
        )

        result = assess_process_attribution_gate(
            {"codex_host": 1}, {"codex_host": 1}, [value]
        )

        self.assertEqual(result.status, "indeterminate")
        self.assert_finding(
            result, "preflight_task_lineage_conflict", "codex_host"
        )

    def test_preflight_snapshot_must_reconcile_exactly(self) -> None:
        result = assess_process_attribution_gate(
            {"codex_host": 2},
            {"codex_host": 1},
            [
                observation(
                    preflight=True,
                    postflight=True,
                    lineage="not_task_tree",
                )
            ],
        )

        self.assertEqual(result.status, "indeterminate")
        self.assert_finding(result, "preflight_snapshot_unreconciled")

    def test_postflight_snapshot_must_reconcile_exactly(self) -> None:
        result = assess_process_attribution_gate(
            {"codex_host": 1},
            {"codex_host": 2},
            [
                observation(
                    preflight=True,
                    postflight=True,
                    lineage="not_task_tree",
                )
            ],
        )

        self.assertEqual(result.status, "indeterminate")
        self.assert_finding(result, "postflight_snapshot_unreconciled")

    def test_malformed_observation_fails_closed(self) -> None:
        result = assess_process_attribution_gate({}, {}, ["not-a-record"])

        self.assertEqual(result.status, "indeterminate")
        self.assert_finding(result, "observation_not_mapping")

    def test_unknown_observation_fields_are_rejected_without_leaking_values(self) -> None:
        value = observation(
            preflight=True,
            postflight=True,
            lineage="not_task_tree",
        )
        value["raw_command_line"] = "PRIVATE HOST VALUE"

        result = assess_process_attribution_gate({}, {}, [value])

        self.assertEqual(result.status, "indeterminate")
        self.assert_finding(
            result, "observation_fields_invalid", "codex_host"
        )
        self.assertNotIn("PRIVATE HOST VALUE", repr(result))
        self.assertNotIn("raw_command_line", repr(result))

    def test_unsafe_process_class_is_not_retained(self) -> None:
        private_class = "C:/Users/private/process.exe"
        value = observation(
            private_class,
            preflight=True,
            postflight=True,
            lineage="not_task_tree",
        )

        result = assess_process_attribution_gate(
            {private_class: 1}, {private_class: 1}, [value]
        )

        self.assertEqual(result.status, "indeterminate")
        self.assertNotIn(private_class, repr(result))
        self.assertIn("process_class_invalid", result.reason_codes)

    def test_snapshot_counts_reject_boolean_negative_and_excessive_values(self) -> None:
        for count in (True, -1, 10_001):
            with self.subTest(count=count):
                result = assess_process_attribution_gate(
                    {"codex_host": count}, {}, []
                )
                self.assertEqual(result.status, "indeterminate")
                self.assert_finding(
                    result, "preflight_process_count_invalid", "codex_host"
                )

    def test_observations_must_be_a_bounded_sequence(self) -> None:
        result = assess_process_attribution_gate({}, {}, {"not": "a list"})

        self.assertEqual(result.status, "indeterminate")
        self.assert_finding(result, "observations_not_sequence")

    def test_findings_have_stable_code_then_class_order(self) -> None:
        observations = [
            observation(
                "z_service",
                preflight=True,
                postflight=True,
                lineage="unknown",
                complete=False,
            ),
            observation(
                "a_service",
                preflight=True,
                postflight=True,
                lineage="unknown",
                complete=False,
            ),
        ]

        result = assess_process_attribution_gate(
            {"a_service": 1, "z_service": 1},
            {"a_service": 1, "z_service": 1},
            observations,
        )

        self.assertEqual(
            result.findings,
            (
                ProcessAttributionFinding("identity_incomplete", "a_service"),
                ProcessAttributionFinding("identity_incomplete", "z_service"),
                ProcessAttributionFinding("task_lineage_unknown", "a_service"),
                ProcessAttributionFinding("task_lineage_unknown", "z_service"),
            ),
        )

    def test_assessment_performs_no_external_or_filesystem_operation(self) -> None:
        observations = [
            observation(
                preflight=True,
                postflight=True,
                lineage="not_task_tree",
            )
        ]

        with (
            patch.object(builtins, "open", side_effect=AssertionError("open")),
            patch.object(
                subprocess, "run", side_effect=AssertionError("subprocess")
            ),
            patch.object(
                socket, "create_connection", side_effect=AssertionError("network")
            ),
            patch.object(
                urllib.request, "urlopen", side_effect=AssertionError("network")
            ),
        ):
            result = assess_process_attribution_gate(
                {"codex_host": 1}, {"codex_host": 1}, observations
            )

        self.assertEqual(result.status, "ready")


if __name__ == "__main__":
    unittest.main()
