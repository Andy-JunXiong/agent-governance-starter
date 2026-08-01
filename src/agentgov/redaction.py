"""Allowlisted portable-evidence redaction helpers."""

from __future__ import annotations

import re


_WINDOWS_USER_HOME_RE = re.compile(r"(?i)\b[A-Z]:\\Users\\[^\\\s]+")
_UNIX_USER_HOME_RE = re.compile(r"/(?:home|Users)/[^/\s]+")
_TOKEN_RE = re.compile(
    r"(?i)(?:github_pat_[A-Za-z0-9_]{8,}|gh[pousr]_[A-Za-z0-9]{8,}|"
    r"Bearer\s+[A-Za-z0-9._~+/=-]{8,})"
)
_SECRET_ASSIGNMENT_RE = re.compile(
    r"(?i)\b(?:GH_TOKEN|GITHUB_TOKEN|API_KEY|ACCESS_TOKEN|SECRET|PASSWORD)"
    r"\s*=\s*[^\s]+"
)


def redact_evidence_text(value: str) -> str:
    """Remove common local identity and credential shapes from portable output."""

    redacted = _WINDOWS_USER_HOME_RE.sub("<redacted-user-home>", value)
    redacted = _UNIX_USER_HOME_RE.sub("<redacted-user-home>", redacted)
    redacted = _SECRET_ASSIGNMENT_RE.sub("<redacted-secret-assignment>", redacted)
    return _TOKEN_RE.sub("<redacted-token>", redacted)
