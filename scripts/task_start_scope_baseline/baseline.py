"""Compatibility alias for the installed task-start baseline implementation."""

from __future__ import annotations

import sys

from agentgov import task_start_scope_baseline as _implementation


sys.modules[__name__] = _implementation
