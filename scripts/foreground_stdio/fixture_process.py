"""Inert local JSONL fixture for the foreground STDIO controller tests."""

from __future__ import annotations

import json
import sys
import time


def _emit(document: object) -> None:
    sys.stdout.write(json.dumps(document, separators=(",", ":")) + "\n")
    sys.stdout.flush()


def main() -> int:
    mode = sys.argv[1]
    if mode == "early_exit":
        return 0

    first = True
    for raw_line in sys.stdin:
        request = json.loads(raw_line)
        request_id = request.get("id")
        if mode == "malformed":
            sys.stdout.write("not-json\n")
            sys.stdout.flush()
            return 0
        if mode == "missing":
            return 0
        if mode == "overflow":
            sys.stdout.write("x" * 20_000 + "\n")
            sys.stdout.flush()
            return 0
        if mode == "many_notifications":
            for _ in range(20):
                _emit({"jsonrpc": "2.0", "method": "fixture/many"})
        if mode == "stderr":
            sys.stderr.write("fixture diagnostic\n")
            sys.stderr.flush()
            time.sleep(0.05)
        if mode in {"delay", "linger"}:
            time.sleep(2.0)
        if mode == "notify":
            _emit({"jsonrpc": "2.0", "method": "fixture/progress"})
        if mode == "invalid_method":
            _emit({"jsonrpc": "2.0", "method": "private value with spaces"})
        if mode == "mismatch":
            _emit({"jsonrpc": "2.0", "id": True, "result": {}})
            continue
        if mode == "unexpected":
            _emit({"jsonrpc": "2.0", "id": request_id, "result": {}})
            first = False
            continue
        if "id" in request:
            _emit({"jsonrpc": "2.0", "id": request_id, "result": {}})
            if mode == "duplicate" and first:
                _emit({"jsonrpc": "2.0", "id": request_id, "result": {}})
        first = False

    if mode in {"success", "notify", "invalid_method"}:
        _emit({"jsonrpc": "2.0", "method": "fixture/eof"})
    if mode == "unexpected":
        _emit({"jsonrpc": "2.0", "id": "outside", "result": {}})
    if mode == "nonzero":
        return 7
    if mode == "linger_after_eof":
        time.sleep(2.0)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
