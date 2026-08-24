from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

try:
    from . import controller
except ImportError:
    import controller  # type: ignore[no-redef]


FIXTURE = Path(__file__).with_name("fixture_process.py")


class ForegroundStdioControllerTests(unittest.TestCase):
    def run_fixture(
        self,
        mode: str,
        *,
        messages: list[dict[str, object]] | None = None,
        limits: controller.ControllerLimits | None = None,
        allow_stderr: bool = False,
    ) -> controller.ExchangeResult:
        return controller.run_jsonl_exchange(
            argv=[sys.executable, str(FIXTURE), mode],
            cwd=FIXTURE.parent,
            messages=messages
            or [{"jsonrpc": "2.0", "id": 1, "method": "fixture/request"}],
            limits=limits,
            allow_stderr=allow_stderr,
        )

    def test_success_correlates_ordered_responses_and_observes_stdin_close(self) -> None:
        result = self.run_fixture(
            "success",
            messages=[
                {"jsonrpc": "2.0", "id": 1, "method": "fixture/one"},
                {"jsonrpc": "2.0", "method": "fixture/initialized"},
                {"jsonrpc": "2.0", "id": "2", "method": "fixture/two"},
            ],
        )
        self.assertEqual(controller.ExchangeOutcome.SUCCESS, result.outcome)
        self.assertEqual(3, result.sent_count)
        self.assertEqual(2, result.matched_response_count)
        self.assertTrue(result.stdin_closed)
        self.assertIn("fixture/eof", result.notification_methods)

    def test_notifications_are_retained_only_as_bounded_methods(self) -> None:
        result = self.run_fixture("notify")
        self.assertEqual(controller.ExchangeOutcome.SUCCESS, result.outcome)
        self.assertEqual(
            ("fixture/progress", "fixture/eof"), result.notification_methods
        )

        invalid = self.run_fixture("invalid_method")
        self.assertEqual("<invalid-method>", invalid.notification_methods[0])

    def test_spawn_failure_is_normalized_and_shell_is_disabled(self) -> None:
        with mock.patch.object(
            controller.subprocess, "Popen", side_effect=OSError("private path")
        ) as popen:
            result = controller.run_jsonl_exchange(
                argv=["private-executable"],
                cwd=FIXTURE.parent,
                messages=[],
            )
        self.assertEqual(controller.ExchangeOutcome.SPAWN_FAILURE, result.outcome)
        self.assertFalse(popen.call_args.kwargs["shell"])
        self.assertNotIn("private", json.dumps(asdict(result), default=str))

    def test_early_exit_and_missing_response_are_classified(self) -> None:
        for mode in ("early_exit", "missing"):
            with self.subTest(mode=mode):
                result = self.run_fixture(mode)
                self.assertEqual(controller.ExchangeOutcome.EARLY_EXIT, result.outcome)
                self.assertEqual("missing", result.response_issue)

    def test_malformed_jsonl_is_classified(self) -> None:
        result = self.run_fixture("malformed")
        self.assertEqual(controller.ExchangeOutcome.MALFORMED_JSONL, result.outcome)

    def test_typed_mismatch_and_unexpected_ids_are_classified(self) -> None:
        mismatch = self.run_fixture("mismatch")
        self.assertEqual(
            controller.ExchangeOutcome.RESPONSE_MISMATCH, mismatch.outcome
        )
        self.assertEqual("mismatched", mismatch.response_issue)

        unexpected = self.run_fixture("unexpected")
        self.assertEqual(
            controller.ExchangeOutcome.RESPONSE_MISMATCH, unexpected.outcome
        )
        self.assertEqual("unexpected", unexpected.response_issue)

    def test_notification_method_retention_is_capped(self) -> None:
        result = self.run_fixture(
            "many_notifications",
            limits=controller.ControllerLimits(max_notification_methods=2),
        )
        self.assertEqual(controller.ExchangeOutcome.SUCCESS, result.outcome)
        self.assertEqual(20, result.notification_count)
        self.assertEqual(2, len(result.notification_methods))

    def test_duplicate_response_is_classified(self) -> None:
        result = self.run_fixture(
            "duplicate",
            messages=[
                {"jsonrpc": "2.0", "id": 1, "method": "fixture/one"},
                {"jsonrpc": "2.0", "id": 2, "method": "fixture/two"},
            ],
        )
        self.assertEqual(controller.ExchangeOutcome.RESPONSE_MISMATCH, result.outcome)
        self.assertEqual("duplicate", result.response_issue)

    def test_step_timeout_terminates_only_direct_child(self) -> None:
        result = self.run_fixture(
            "delay",
            limits=controller.ControllerLimits(
                step_timeout_seconds=0.2,
                overall_timeout_seconds=2.0,
                shutdown_timeout_seconds=1.0,
            ),
        )
        self.assertEqual(controller.ExchangeOutcome.STEP_TIMEOUT, result.outcome)
        self.assertTrue(result.termination_attempted)
        self.assertEqual(
            controller.ExchangeOutcome.STEP_TIMEOUT, result.termination_trigger
        )

    def test_overall_timeout_is_distinct(self) -> None:
        result = self.run_fixture(
            "linger_after_eof",
            limits=controller.ControllerLimits(
                step_timeout_seconds=0.5,
                overall_timeout_seconds=0.6,
                shutdown_timeout_seconds=1.0,
            ),
        )
        self.assertEqual(controller.ExchangeOutcome.OVERALL_TIMEOUT, result.outcome)

    def test_stdout_and_message_limits_are_classified(self) -> None:
        stdout = self.run_fixture(
            "overflow",
            limits=controller.ControllerLimits(max_stdout_bytes=100),
        )
        self.assertEqual(controller.ExchangeOutcome.OUTPUT_LIMIT, stdout.outcome)
        self.assertEqual("stdout_bytes", stdout.limit_kind)

        messages = self.run_fixture(
            "many_notifications",
            limits=controller.ControllerLimits(max_messages=3),
        )
        self.assertEqual(controller.ExchangeOutcome.OUTPUT_LIMIT, messages.outcome)
        self.assertEqual("message_count", messages.limit_kind)

    def test_stderr_policy_and_stderr_limit_are_distinct(self) -> None:
        policy = self.run_fixture("stderr")
        self.assertEqual(
            controller.ExchangeOutcome.STDERR_POLICY_DEVIATION, policy.outcome
        )
        self.assertTrue(policy.stderr_observed)

        limit = self.run_fixture(
            "stderr",
            allow_stderr=True,
            limits=controller.ControllerLimits(max_stderr_bytes=3),
        )
        self.assertEqual(controller.ExchangeOutcome.OUTPUT_LIMIT, limit.outcome)
        self.assertEqual("stderr_bytes", limit.limit_kind)

    def test_nonzero_exit_after_valid_exchange_is_classified(self) -> None:
        result = self.run_fixture("nonzero")
        self.assertEqual(controller.ExchangeOutcome.NONZERO_EXIT, result.outcome)
        self.assertTrue(result.exit_nonzero)

    def test_termination_failure_retains_timeout_trigger(self) -> None:
        real_stop = controller._stop_direct_child

        def stop_but_report_failure(
            process: subprocess.Popen[bytes], timeout_seconds: float
        ) -> controller._StopResult:
            stopped = real_stop(process, timeout_seconds)
            return controller._StopResult(
                False, stopped.termination_attempted, stopped.kill_attempted
            )

        with mock.patch.object(
            controller, "_stop_direct_child", side_effect=stop_but_report_failure
        ):
            result = self.run_fixture(
                "delay",
                limits=controller.ControllerLimits(
                    step_timeout_seconds=0.2,
                    overall_timeout_seconds=2.0,
                    shutdown_timeout_seconds=1.0,
                ),
            )
        self.assertEqual(
            controller.ExchangeOutcome.TERMINATION_FAILURE, result.outcome
        )
        self.assertEqual(
            controller.ExchangeOutcome.STEP_TIMEOUT, result.termination_trigger
        )

    def test_result_does_not_retain_private_inputs(self) -> None:
        private_value = "do-not-retain-7d391"
        with tempfile.TemporaryDirectory(prefix="stdio-private-") as directory:
            result = controller.run_jsonl_exchange(
                argv=[sys.executable, str(FIXTURE), "success", private_value],
                cwd=directory,
                env={"PRIVATE_VALUE": private_value},
                messages=[
                    {
                        "jsonrpc": "2.0",
                        "id": private_value,
                        "method": "fixture/request",
                        "params": {"value": private_value},
                    }
                ],
            )
        rendered = json.dumps(asdict(result), default=str)
        self.assertNotIn(private_value, rendered)
        self.assertNotIn(directory, rendered)

    def test_invalid_inputs_stop_before_spawn(self) -> None:
        with mock.patch.object(controller.subprocess, "Popen") as popen:
            with self.assertRaises(ValueError):
                controller.run_jsonl_exchange(
                    argv=[sys.executable], cwd="missing-directory", messages=[]
                )
            with self.assertRaises(ValueError):
                controller.run_jsonl_exchange(
                    argv=[sys.executable],
                    cwd=FIXTURE.parent,
                    messages=[{}, {}],
                    limits=controller.ControllerLimits(max_messages=1),
                )
        popen.assert_not_called()


if __name__ == "__main__":
    unittest.main()
