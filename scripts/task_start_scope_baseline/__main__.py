"""Internal command surface for task-start baseline capture and comparison."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .baseline import (
    BaselineError,
    capture_task_start_baseline,
    check_task_start_baseline,
    comparison_to_payload,
    write_baseline,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="task-start-scope-baseline")
    subparsers = parser.add_subparsers(dest="command", required=True)
    capture = subparsers.add_parser("capture")
    capture.add_argument("--repository", default=".")
    capture.add_argument("--task", required=True)
    capture.add_argument("--output", required=True)
    capture.add_argument("--comparison-base", default="HEAD")
    check = subparsers.add_parser("check")
    check.add_argument("--repository", default=".")
    check.add_argument("--task", required=True)
    check.add_argument("--baseline", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    try:
        if arguments.command == "capture":
            baseline = capture_task_start_baseline(
                Path(arguments.repository),
                task_path=arguments.task,
                comparison_base=arguments.comparison_base,
            )
            write_baseline(
                baseline,
                repository=Path(arguments.repository),
                output_path=arguments.output,
            )
            result = {
                "contract": "agentgov.task-start-scope-baseline-capture-result",
                "schema_version": "1.0",
                "status": "captured",
                "task_id": baseline.task.task_id,
                "task_digest": baseline.task.digest,
                "baseline_digest": baseline.baseline_digest,
                "baseline_path": arguments.output,
                "capture_claim": baseline.capture_claim,
            }
            print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
            return 0
        report = check_task_start_baseline(
            Path(arguments.repository),
            task_path=arguments.task,
            baseline_path=arguments.baseline,
        )
        print(json.dumps(comparison_to_payload(report), ensure_ascii=False, indent=2, sort_keys=True))
        return 1 if report.has_failures else 0
    except BaselineError as exc:
        print(json.dumps({
            "contract": "agentgov.task-start-scope-baseline-error",
            "schema_version": "1.0",
            "status": "error",
            "message": str(exc),
        }, ensure_ascii=False, indent=2, sort_keys=True))
        return 2


if __name__ == "__main__":
    sys.exit(main())
