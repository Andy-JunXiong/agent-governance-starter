from __future__ import annotations

import importlib.util
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "examples" / "governed-refund-demo" / "run_demo.py"


def load_runner():
    spec = importlib.util.spec_from_file_location("governed_refund_demo", RUNNER)
    if spec is None or spec.loader is None:
        raise AssertionError("demo runner could not be loaded")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    previous = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = previous
    return module


def git_status() -> str:
    completed = subprocess.run(
        ("git", "-C", str(ROOT), "status", "--porcelain=v1"),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        raise AssertionError(completed.stderr.decode("utf-8", errors="replace"))
    return completed.stdout.decode("utf-8", errors="replace")


class GovernedTaskDemoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.runner = load_runner()

    def run_scenario(self, parent: Path):
        decisions = iter(("START", "2"))
        return self.runner.run_demo(
            decision_reader=lambda _prompt: next(decisions),
            interactive_terminal=True,
            decision_evidence="test-harness",
            temporary_parent=parent,
        )

    def test_real_scope_failure_then_fresh_review_ready_completion(self) -> None:
        with TemporaryDirectory() as temp_dir:
            result = self.run_scenario(Path(temp_dir))

        self.assertEqual(result.initial_scope_status, "FAIL")
        self.assertEqual(
            result.initial_observed_paths,
            ("refunds/approval_policy.py", "refunds/calculation.py"),
        )
        self.assertEqual(result.initial_failed_paths, ("refunds/approval_policy.py",))
        self.assertEqual(result.initial_cycle_status, "blocked")
        self.assertEqual(result.selected_option_id, "narrow_changes")
        self.assertEqual(result.corrected_failed_paths, ())
        self.assertEqual(result.validation_outcome, "passed")
        self.assertEqual(result.reconciliation_outcome, "verified")
        self.assertEqual(result.completion_status, "review_ready")

    def test_simulation_human_and_authority_boundaries_remain_visible(self) -> None:
        with TemporaryDirectory() as temp_dir:
            result = self.run_scenario(Path(temp_dir))

        transcript = result.transcript
        self.assertIn("[SIMULATED AGENT BEHAVIOR]", transcript)
        self.assertIn("[REAL AGENTGOV EVIDENCE]", transcript)
        self.assertIn("[SCRIPTED REMEDIATION]", transcript)
        self.assertIn("[TEST-HARNESS INPUT]", transcript)
        self.assertIn("not human evidence", transcript)
        self.assertIn("did not perform this remediation", transcript)
        self.assertIn("does not claim that AgentGov stopped or rolled back", transcript)
        self.assertIn("records no final acceptance", transcript)
        self.assertIn(
            "Passing evidence does not authorize commit, merge, release, publication, or deployment.",
            transcript,
        )
        self.assertFalse(result.final_decision_recorded)
        self.assertNotIn("session.reviewed", result.event_types)

    def test_fixture_is_disposable_and_ignores_unrelated_parent_state(self) -> None:
        self.assertFalse((RUNNER.parent / "__pycache__").exists())
        before = git_status()
        with TemporaryDirectory() as temp_dir:
            parent = Path(temp_dir)
            unrelated = parent / "unrelated-user-file.txt"
            unrelated.write_text("preserve me\n", encoding="utf-8")

            result = self.run_scenario(parent)

            self.assertEqual(unrelated.read_text(encoding="utf-8"), "preserve me\n")
            self.assertEqual(
                sorted(path.name for path in parent.iterdir()),
                ["unrelated-user-file.txt"],
            )
            self.assertEqual(result.decision_evidence, "test-harness")
        self.assertEqual(git_status(), before)

    def test_semantic_transcript_is_stable_and_contains_no_temporary_path(self) -> None:
        with TemporaryDirectory() as first_dir, TemporaryDirectory() as second_dir:
            first = self.run_scenario(Path(first_dir))
            second = self.run_scenario(Path(second_dir))

        self.assertEqual(first.transcript, second.transcript)
        self.assertNotIn(str(Path(first_dir)), first.transcript)
        self.assertIn("FAIL refunds/approval_policy.py", first.transcript)
        self.assertIn("PASS refunds/calculation.py", first.transcript)
        self.assertIn("Final AgentGov state: REVIEW_READY", first.transcript)

    def test_noninteractive_execution_stops_before_task_or_agent_work(self) -> None:
        with TemporaryDirectory() as temp_dir:
            with self.assertRaisesRegex(
                self.runner.DemoError,
                "not confirmed in an interactive terminal",
            ):
                self.runner.run_demo(
                    decision_reader=lambda _prompt: "START",
                    interactive_terminal=False,
                    decision_evidence="human-terminal",
                    temporary_parent=Path(temp_dir),
                )


if __name__ == "__main__":
    unittest.main()
