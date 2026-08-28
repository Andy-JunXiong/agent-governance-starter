"""Fixed stdin worker for the bounded artifact replay harness."""

from __future__ import annotations

import base64
import binascii
from contextlib import redirect_stderr, redirect_stdout
import hashlib
import json
import re
import sys
from types import MappingProxyType
from typing import Any, Mapping

from .harness import (
    ENCODING_ALGORITHM,
    MAX_SOURCE_BYTES,
    SCHEMA_VERSION,
    SOURCE_IDENTITY_GLOBAL,
    SOURCE_IDENTITY_KEYS,
    WORKER_CONTRACT,
)


MAX_REQUEST_BYTES = 1_400_000
ENTRYPOINT = "artifact_replay_main"
_SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")


class _DiscardText:
    encoding = "utf-8"

    def write(self, value: object) -> int:
        return len(value) if isinstance(value, str) else 0

    def flush(self) -> None:
        return None


def _sha256(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _report(
    *,
    status: str,
    mode: str | None,
    phase: str,
    reason_code: str | None,
    source_length: int | None,
    source_sha256: str | None,
    encoded_length: int | None,
    encoded_sha256: str | None,
) -> Mapping[str, Any]:
    return {
        "contract": WORKER_CONTRACT,
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "mode": mode,
        "phase": phase,
        "reason_code": reason_code,
        "source_length": source_length,
        "source_sha256": source_sha256,
        "encoded_length": encoded_length,
        "encoded_sha256": encoded_sha256,
    }


def _write(report: Mapping[str, Any]) -> None:
    data = json.dumps(report, sort_keys=True, separators=(",", ":"))
    sys.__stdout__.write(data)
    sys.__stdout__.flush()


def _failure(
    reason_code: str,
    *,
    mode: str | None = None,
    phase: str = "transport",
    source_length: int | None = None,
    source_sha256: str | None = None,
    encoded_length: int | None = None,
    encoded_sha256: str | None = None,
) -> int:
    _write(
        _report(
            status="STOPPED_AT_FIRST_DEVIATION",
            mode=mode,
            phase=phase,
            reason_code=reason_code,
            source_length=source_length,
            source_sha256=source_sha256,
            encoded_length=encoded_length,
            encoded_sha256=encoded_sha256,
        )
    )
    return 1


def _exact_request(value: object) -> Mapping[str, Any] | None:
    expected = {
        "contract",
        "schema_version",
        "mode",
        "encoding_algorithm",
        "source_base64",
        "source_length",
        "source_sha256",
        "encoded_length",
        "encoded_sha256",
    }
    if not isinstance(value, Mapping) or set(value) != expected:
        return None
    mode = value.get("mode")
    source_length = value.get("source_length")
    encoded_length = value.get("encoded_length")
    if (
        value.get("contract") != WORKER_CONTRACT
        or value.get("schema_version") != SCHEMA_VERSION
        or mode not in {"dry", "actual"}
        or value.get("encoding_algorithm") != ENCODING_ALGORITHM
        or not isinstance(value.get("source_base64"), str)
        or not isinstance(source_length, int)
        or isinstance(source_length, bool)
        or source_length <= 0
        or source_length > MAX_SOURCE_BYTES
        or not isinstance(encoded_length, int)
        or isinstance(encoded_length, bool)
        or encoded_length <= 0
        or not isinstance(value.get("source_sha256"), str)
        or _SHA256_RE.fullmatch(value["source_sha256"]) is None
        or not isinstance(value.get("encoded_sha256"), str)
        or _SHA256_RE.fullmatch(value["encoded_sha256"]) is None
    ):
        return None
    return value


def _source_identity_context(
    *,
    source_length: int,
    source_sha256: str,
    encoded_length: int,
    encoded_sha256: str,
) -> Mapping[str, int | str]:
    """Return the exact worker-validated identity as a read-only mapping."""

    values: dict[str, int | str] = {
        "source_length": source_length,
        "source_sha256": source_sha256,
        "encoded_length": encoded_length,
        "encoded_sha256": encoded_sha256,
    }
    if tuple(values) != SOURCE_IDENTITY_KEYS:
        raise RuntimeError("source identity contract drift")
    return MappingProxyType(values)


def _main() -> int:
    raw = sys.stdin.buffer.read(MAX_REQUEST_BYTES + 1)
    if not raw or len(raw) > MAX_REQUEST_BYTES:
        return _failure("worker_request_invalid")
    try:
        value = json.loads(raw.decode("utf-8", errors="strict"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return _failure("worker_request_invalid")
    request = _exact_request(value)
    if request is None:
        return _failure("worker_request_invalid")

    mode = str(request["mode"])
    source_length = int(request["source_length"])
    source_sha256 = str(request["source_sha256"])
    encoded_length = int(request["encoded_length"])
    encoded_sha256 = str(request["encoded_sha256"])
    encoded_text = str(request["source_base64"])
    try:
        encoded = encoded_text.encode("ascii", errors="strict")
        source = base64.b64decode(encoded, validate=True)
    except (UnicodeEncodeError, binascii.Error, ValueError):
        return _failure(
            "source_encoding_invalid",
            mode=mode,
            phase="identity",
            source_length=source_length,
            source_sha256=source_sha256,
            encoded_length=encoded_length,
            encoded_sha256=encoded_sha256,
        )
    if (
        len(encoded) != encoded_length
        or _sha256(encoded) != encoded_sha256
        or len(source) != source_length
        or _sha256(source) != source_sha256
    ):
        return _failure(
            "source_identity_mismatch",
            mode=mode,
            phase="identity",
            source_length=source_length,
            source_sha256=source_sha256,
            encoded_length=encoded_length,
            encoded_sha256=encoded_sha256,
        )
    try:
        source_text = source.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        return _failure(
            "source_utf8_invalid",
            mode=mode,
            phase="identity",
            source_length=source_length,
            source_sha256=source_sha256,
            encoded_length=encoded_length,
            encoded_sha256=encoded_sha256,
        )
    try:
        code = compile(source_text, "<bounded-artifact-replay>", "exec")
    except BaseException:
        return _failure(
            "source_compile_failed",
            mode=mode,
            phase="compile",
            source_length=source_length,
            source_sha256=source_sha256,
            encoded_length=encoded_length,
            encoded_sha256=encoded_sha256,
        )

    namespace: dict[str, Any] = {
        "__name__": "__bounded_artifact_replay__",
        "ARTIFACT_REPLAY_MODE": mode,
    }
    identity_context = _source_identity_context(
        source_length=source_length,
        source_sha256=source_sha256,
        encoded_length=encoded_length,
        encoded_sha256=encoded_sha256,
    )
    namespace[SOURCE_IDENTITY_GLOBAL] = identity_context
    sink = _DiscardText()
    try:
        with redirect_stdout(sink), redirect_stderr(sink):
            exec(code, namespace, namespace)
    except (ImportError, ModuleNotFoundError):
        return _failure(
            "source_import_failed",
            mode=mode,
            phase="import",
            source_length=source_length,
            source_sha256=source_sha256,
            encoded_length=encoded_length,
            encoded_sha256=encoded_sha256,
        )
    except BaseException:
        return _failure(
            "source_initialization_failed",
            mode=mode,
            phase="initialize",
            source_length=source_length,
            source_sha256=source_sha256,
            encoded_length=encoded_length,
            encoded_sha256=encoded_sha256,
        )
    if namespace.get(SOURCE_IDENTITY_GLOBAL) is not identity_context:
        return _failure(
            "source_identity_context_drift",
            mode=mode,
            phase="initialize",
            source_length=source_length,
            source_sha256=source_sha256,
            encoded_length=encoded_length,
            encoded_sha256=encoded_sha256,
        )
    entrypoint = namespace.get(ENTRYPOINT)
    if not callable(entrypoint):
        return _failure(
            "source_entrypoint_invalid",
            mode=mode,
            phase="initialize",
            source_length=source_length,
            source_sha256=source_sha256,
            encoded_length=encoded_length,
            encoded_sha256=encoded_sha256,
        )
    try:
        with redirect_stdout(sink), redirect_stderr(sink):
            entrypoint()
    except BaseException:
        return _failure(
            "source_execution_failed",
            mode=mode,
            phase="execute",
            source_length=source_length,
            source_sha256=source_sha256,
            encoded_length=encoded_length,
            encoded_sha256=encoded_sha256,
        )
    if namespace.get(SOURCE_IDENTITY_GLOBAL) is not identity_context:
        return _failure(
            "source_identity_context_drift",
            mode=mode,
            phase="execute",
            source_length=source_length,
            source_sha256=source_sha256,
            encoded_length=encoded_length,
            encoded_sha256=encoded_sha256,
        )
    _write(
        _report(
            status="PASS",
            mode=mode,
            phase="complete",
            reason_code=None,
            source_length=source_length,
            source_sha256=source_sha256,
            encoded_length=encoded_length,
            encoded_sha256=encoded_sha256,
        )
    )
    return 0


def main() -> int:
    """Contain all worker failures behind one fixed, bounded response."""

    try:
        return _main()
    except BaseException:
        try:
            return _failure("worker_internal_failed")
        except BaseException:
            return 1


if __name__ == "__main__":
    raise SystemExit(main())
