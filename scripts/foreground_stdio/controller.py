"""Bounded, privacy-reducing controller for foreground JSONL subprocesses.

This is repository-internal validation infrastructure.  It deliberately has
no command-line entry point and is not part of the installed AgentGov package.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
import json
from pathlib import Path
from queue import Empty, Queue
import re
import subprocess
import threading
import time
from typing import Mapping, Sequence


class ExchangeOutcome(StrEnum):
    SUCCESS = "success"
    SPAWN_FAILURE = "spawn_failure"
    EARLY_EXIT = "early_exit"
    MALFORMED_JSONL = "malformed_jsonl"
    RESPONSE_MISMATCH = "response_mismatch"
    STEP_TIMEOUT = "step_timeout"
    OVERALL_TIMEOUT = "overall_timeout"
    OUTPUT_LIMIT = "output_limit"
    STDERR_POLICY_DEVIATION = "stderr_policy_deviation"
    NONZERO_EXIT = "nonzero_exit"
    TERMINATION_FAILURE = "termination_failure"


@dataclass(frozen=True)
class ControllerLimits:
    step_timeout_seconds: float = 5.0
    overall_timeout_seconds: float = 30.0
    shutdown_timeout_seconds: float = 1.0
    max_messages: int = 100
    max_stdout_bytes: int = 256_000
    max_stderr_bytes: int = 64_000
    max_notification_methods: int = 32

    def validate(self) -> None:
        numeric = (
            self.step_timeout_seconds,
            self.overall_timeout_seconds,
            self.shutdown_timeout_seconds,
        )
        counts = (
            self.max_messages,
            self.max_stdout_bytes,
            self.max_stderr_bytes,
            self.max_notification_methods,
        )
        if any(value <= 0 for value in numeric + counts):
            raise ValueError("all controller limits must be positive")
        if self.step_timeout_seconds > self.overall_timeout_seconds:
            raise ValueError("step timeout cannot exceed overall timeout")


@dataclass(frozen=True)
class ExchangeResult:
    outcome: ExchangeOutcome
    sent_count: int
    received_count: int
    matched_response_count: int
    notification_count: int
    notification_methods: tuple[str, ...]
    stdout_byte_count: int
    stderr_byte_count: int
    stderr_observed: bool
    stdin_closed: bool
    exit_nonzero: bool
    response_issue: str | None
    limit_kind: str | None
    termination_attempted: bool
    kill_attempted: bool
    termination_trigger: ExchangeOutcome | None
    timing_bucket: str


@dataclass(frozen=True)
class _StopResult:
    stopped: bool
    termination_attempted: bool
    kill_attempted: bool


@dataclass
class _State:
    sent_count: int = 0
    received_count: int = 0
    matched_response_count: int = 0
    notification_count: int = 0
    notification_methods: list[str] | None = None
    stdout_byte_count: int = 0
    stderr_byte_count: int = 0
    stderr_observed: bool = False
    stdin_closed: bool = False
    response_issue: str | None = None
    limit_kind: str | None = None

    def __post_init__(self) -> None:
        if self.notification_methods is None:
            self.notification_methods = []


_METHOD_RE = re.compile(r"^[A-Za-z0-9_.\-/]{1,64}$")


def _typed_id(value: object) -> tuple[str, object]:
    if value is None:
        return ("null", "null")
    if isinstance(value, bool):
        return ("bool", value)
    if isinstance(value, int):
        return ("int", value)
    if isinstance(value, str):
        return ("str", value)
    return ("invalid", type(value).__name__)


def _normalized_method(value: object) -> str:
    if isinstance(value, str) and _METHOD_RE.fullmatch(value):
        return value
    return "<invalid-method>"


def _timing_bucket(seconds: float) -> str:
    if seconds < 0.1:
        return "under_100ms"
    if seconds < 1.0:
        return "under_1s"
    if seconds < 5.0:
        return "under_5s"
    return "five_seconds_or_more"


def _read_stdout(
    stream: object,
    events: Queue[tuple[str, object]],
    state: _State,
    limit: int,
) -> None:
    buffered = b""
    try:
        while True:
            chunk = stream.read(4096)  # type: ignore[attr-defined]
            if not chunk:
                if buffered:
                    events.put(("stdout_line", buffered))
                break
            state.stdout_byte_count += len(chunk)
            if state.stdout_byte_count > limit:
                events.put(("stdout_limit", None))
                return
            buffered += chunk
            while b"\n" in buffered:
                line, buffered = buffered.split(b"\n", 1)
                events.put(("stdout_line", line.rstrip(b"\r")))
    except (OSError, ValueError):
        pass
    finally:
        events.put(("stdout_eof", None))


def _read_stderr(
    stream: object,
    events: Queue[tuple[str, object]],
    state: _State,
    limit: int,
) -> None:
    announced = False
    try:
        while True:
            chunk = stream.read(4096)  # type: ignore[attr-defined]
            if not chunk:
                break
            state.stderr_byte_count += len(chunk)
            if not announced:
                announced = True
                state.stderr_observed = True
                events.put(("stderr_observed", None))
            if state.stderr_byte_count > limit:
                events.put(("stderr_limit", None))
                return
    except (OSError, ValueError):
        pass
    finally:
        events.put(("stderr_eof", None))


def _stop_direct_child(
    process: subprocess.Popen[bytes], timeout_seconds: float
) -> _StopResult:
    """Stop only the exact Popen child; never scan or target a process tree."""
    if process.poll() is not None:
        return _StopResult(True, False, False)
    termination_attempted = True
    try:
        process.terminate()
        process.wait(timeout=timeout_seconds)
        return _StopResult(True, termination_attempted, False)
    except (OSError, subprocess.TimeoutExpired):
        if process.poll() is not None:
            return _StopResult(True, termination_attempted, False)
    kill_attempted = True
    try:
        process.kill()
        process.wait(timeout=timeout_seconds)
        return _StopResult(True, termination_attempted, kill_attempted)
    except (OSError, subprocess.TimeoutExpired):
        return _StopResult(
            process.poll() is not None, termination_attempted, kill_attempted
        )


def _build_result(
    *,
    outcome: ExchangeOutcome,
    state: _State,
    started_at: float,
    process: subprocess.Popen[bytes] | None,
    stop: _StopResult | None = None,
    termination_trigger: ExchangeOutcome | None = None,
) -> ExchangeResult:
    return ExchangeResult(
        outcome=outcome,
        sent_count=state.sent_count,
        received_count=state.received_count,
        matched_response_count=state.matched_response_count,
        notification_count=state.notification_count,
        notification_methods=tuple(state.notification_methods or ()),
        stdout_byte_count=state.stdout_byte_count,
        stderr_byte_count=state.stderr_byte_count,
        stderr_observed=state.stderr_observed,
        stdin_closed=state.stdin_closed,
        exit_nonzero=(process is not None and process.returncode not in (None, 0)),
        response_issue=state.response_issue,
        limit_kind=state.limit_kind,
        termination_attempted=bool(stop and stop.termination_attempted),
        kill_attempted=bool(stop and stop.kill_attempted),
        termination_trigger=termination_trigger,
        timing_bucket=_timing_bucket(time.monotonic() - started_at),
    )


def run_jsonl_exchange(
    *,
    argv: Sequence[str],
    cwd: str | Path,
    messages: Sequence[Mapping[str, object]],
    limits: ControllerLimits | None = None,
    allow_stderr: bool = False,
    env: Mapping[str, str] | None = None,
) -> ExchangeResult:
    """Run one bounded ordered JSONL exchange against one direct child.

    Inputs may contain private values, but the returned dataclass contains only
    normalized categories, counts, booleans, bounded method names, and a timing
    bucket.  Invalid controller inputs raise ``ValueError`` before launch.
    """
    active_limits = limits or ControllerLimits()
    active_limits.validate()
    if not argv or any(not isinstance(item, str) or not item or "\x00" in item for item in argv):
        raise ValueError("argv must contain non-empty strings without NUL bytes")
    working_directory = Path(cwd)
    if not working_directory.is_dir():
        raise ValueError("cwd must be an existing directory")
    if len(messages) > active_limits.max_messages:
        raise ValueError("outbound message count exceeds max_messages")

    prepared: list[tuple[bytes, bool, tuple[str, object] | None]] = []
    pending_ids: set[tuple[str, object]] = set()
    for message in messages:
        if not isinstance(message, Mapping):
            raise ValueError("every outbound message must be a mapping")
        try:
            encoded = json.dumps(
                dict(message), separators=(",", ":"), ensure_ascii=False
            ).encode("utf-8") + b"\n"
        except (TypeError, ValueError) as error:
            raise ValueError("outbound messages must be JSON serializable") from error
        has_id = "id" in message
        request_id = _typed_id(message.get("id")) if has_id else None
        if request_id is not None:
            if request_id[0] == "invalid" or request_id in pending_ids:
                raise ValueError("request IDs must be unique JSON scalar values")
            pending_ids.add(request_id)
        prepared.append((encoded, has_id, request_id))

    started_at = time.monotonic()
    state = _State()
    process: subprocess.Popen[bytes] | None = None
    try:
        process = subprocess.Popen(
            list(argv),
            cwd=working_directory,
            env=None if env is None else dict(env),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
            bufsize=0,
        )
    except (OSError, ValueError):
        return _build_result(
            outcome=ExchangeOutcome.SPAWN_FAILURE,
            state=state,
            started_at=started_at,
            process=None,
        )

    assert process.stdin is not None
    assert process.stdout is not None
    assert process.stderr is not None
    events: Queue[tuple[str, object]] = Queue()
    stdout_thread = threading.Thread(
        target=_read_stdout,
        args=(process.stdout, events, state, active_limits.max_stdout_bytes),
        daemon=True,
        name="foreground-stdio-stdout",
    )
    stderr_thread = threading.Thread(
        target=_read_stderr,
        args=(process.stderr, events, state, active_limits.max_stderr_bytes),
        daemon=True,
        name="foreground-stdio-stderr",
    )
    stdout_thread.start()
    stderr_thread.start()

    overall_deadline = started_at + active_limits.overall_timeout_seconds
    matched_ids: set[tuple[str, object]] = set()
    outcome: ExchangeOutcome | None = None
    stdout_eof = False
    stderr_eof = False

    def consume_event(
        event: tuple[str, object], expected_id: tuple[str, object] | None
    ) -> tuple[bool, ExchangeOutcome | None]:
        nonlocal stdout_eof, stderr_eof
        kind, payload = event
        if kind == "stdout_eof":
            stdout_eof = True
            if expected_id is not None:
                state.response_issue = "missing"
                return False, ExchangeOutcome.EARLY_EXIT
            return False, None
        if kind == "stderr_eof":
            stderr_eof = True
            return False, None
        if kind == "stdout_limit":
            state.limit_kind = "stdout_bytes"
            return False, ExchangeOutcome.OUTPUT_LIMIT
        if kind == "stderr_limit":
            state.limit_kind = "stderr_bytes"
            return False, ExchangeOutcome.OUTPUT_LIMIT
        if kind == "stderr_observed":
            if not allow_stderr:
                return False, ExchangeOutcome.STDERR_POLICY_DEVIATION
            return False, None
        if kind != "stdout_line":
            return False, None

        state.received_count += 1
        if state.received_count > active_limits.max_messages:
            state.limit_kind = "message_count"
            return False, ExchangeOutcome.OUTPUT_LIMIT
        try:
            document = json.loads(bytes(payload).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return False, ExchangeOutcome.MALFORMED_JSONL
        if not isinstance(document, dict):
            return False, ExchangeOutcome.MALFORMED_JSONL
        if "id" in document:
            response_id = _typed_id(document.get("id"))
            if response_id in matched_ids:
                state.response_issue = "duplicate"
                return False, ExchangeOutcome.RESPONSE_MISMATCH
            if expected_id is None:
                state.response_issue = "unexpected"
                return False, ExchangeOutcome.RESPONSE_MISMATCH
            if response_id != expected_id:
                state.response_issue = "mismatched"
                return False, ExchangeOutcome.RESPONSE_MISMATCH
            matched_ids.add(response_id)
            state.matched_response_count += 1
            return True, None

        state.notification_count += 1
        methods = state.notification_methods
        assert methods is not None
        if len(methods) < active_limits.max_notification_methods:
            methods.append(_normalized_method(document.get("method")))
        return False, None

    for encoded, has_id, request_id in prepared:
        if outcome is not None:
            break
        if time.monotonic() >= overall_deadline:
            outcome = ExchangeOutcome.OVERALL_TIMEOUT
            break
        try:
            process.stdin.write(encoded)
            process.stdin.flush()
            state.sent_count += 1
        except (BrokenPipeError, OSError, ValueError):
            state.response_issue = "missing" if has_id else None
            outcome = ExchangeOutcome.EARLY_EXIT
            break
        if not has_id:
            continue

        step_deadline = min(
            time.monotonic() + active_limits.step_timeout_seconds,
            overall_deadline,
        )
        matched = False
        while not matched and outcome is None:
            now = time.monotonic()
            if now >= overall_deadline:
                state.response_issue = "missing"
                outcome = ExchangeOutcome.OVERALL_TIMEOUT
                break
            if now >= step_deadline:
                state.response_issue = "missing"
                outcome = ExchangeOutcome.STEP_TIMEOUT
                break
            try:
                event = events.get(timeout=min(step_deadline, overall_deadline) - now)
            except Empty:
                continue
            matched, outcome = consume_event(event, request_id)

    if outcome is None:
        try:
            process.stdin.close()
            state.stdin_closed = True
        except OSError:
            outcome = ExchangeOutcome.EARLY_EXIT

    while outcome is None:
        now = time.monotonic()
        if now >= overall_deadline:
            outcome = ExchangeOutcome.OVERALL_TIMEOUT
            break
        if process.poll() is not None and stdout_eof and stderr_eof:
            break
        try:
            event = events.get(timeout=min(0.05, overall_deadline - now))
        except Empty:
            continue
        _, outcome = consume_event(event, None)

    if outcome is None:
        try:
            process.wait(timeout=max(0.0, overall_deadline - time.monotonic()))
        except subprocess.TimeoutExpired:
            outcome = ExchangeOutcome.OVERALL_TIMEOUT
    if outcome is None:
        outcome = (
            ExchangeOutcome.NONZERO_EXIT
            if process.returncode not in (None, 0)
            else ExchangeOutcome.SUCCESS
        )

    stop: _StopResult | None = None
    termination_trigger: ExchangeOutcome | None = None
    if process.poll() is None:
        termination_trigger = outcome
        stop = _stop_direct_child(process, active_limits.shutdown_timeout_seconds)
        if not stop.stopped:
            outcome = ExchangeOutcome.TERMINATION_FAILURE

    for stream in (process.stdin, process.stdout, process.stderr):
        try:
            stream.close()
        except (OSError, ValueError):
            pass
    stdout_thread.join(timeout=active_limits.shutdown_timeout_seconds)
    stderr_thread.join(timeout=active_limits.shutdown_timeout_seconds)

    return _build_result(
        outcome=outcome,
        state=state,
        started_at=started_at,
        process=process,
        stop=stop,
        termination_trigger=termination_trigger,
    )
