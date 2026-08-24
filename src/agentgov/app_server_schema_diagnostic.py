"""Pure, bounded diagnostics for a normalized App Server thread/start schema.

This internal module intentionally performs no command, filesystem, network,
MCP, App Server, or model operation.  Callers provide already-loaded in-memory
objects and receive normalized findings that never include request values or
raw schema fragments.
"""

from __future__ import annotations

import re
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass
from typing import Any


COMPATIBILITY_STATUSES = {"compatible", "incompatible", "indeterminate"}

_FIELD_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_.-]{0,119}$")
_MAX_TRAVERSAL_NODES = 20_000
_MAX_REFERENCE_DEPTH = 64
_JSON_TYPES = {"array", "boolean", "integer", "null", "number", "object", "string"}


@dataclass(frozen=True, order=True)
class DiagnosticFinding:
    """One normalized diagnostic fact with no raw input value."""

    code: str
    field: str | None = None


@dataclass(frozen=True)
class AppServerSchemaDiagnostic:
    """Bounded static compatibility result for one normalized request."""

    status: str
    findings: tuple[DiagnosticFinding, ...]
    checked_fields: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.status not in COMPATIBILITY_STATUSES:
            raise ValueError("unsupported compatibility status")

    @property
    def reason_codes(self) -> tuple[str, ...]:
        return tuple(finding.code for finding in self.findings)


@dataclass(frozen=True)
class _Resolution:
    value: Mapping[str, Any] | None
    error_code: str | None = None


def _finding(code: str, field: str | None = None) -> DiagnosticFinding:
    return DiagnosticFinding(code=code, field=field)


def _ordered_findings(
    findings: Sequence[DiagnosticFinding],
) -> tuple[DiagnosticFinding, ...]:
    return tuple(
        sorted(set(findings), key=lambda item: (item.code, item.field or ""))
    )


def _safe_field(value: Any) -> str | None:
    if isinstance(value, str) and _FIELD_RE.fullmatch(value):
        return value
    return None


def _walk(value: Any) -> Iterator[tuple[str | None, Mapping[str, Any]]]:
    """Yield mapping nodes without following object cycles or unbounded input."""

    stack: list[tuple[str | None, Any]] = [(None, value)]
    seen: set[int] = set()
    visited = 0
    while stack and visited < _MAX_TRAVERSAL_NODES:
        name, item = stack.pop()
        if isinstance(item, Mapping):
            identity = id(item)
            if identity in seen:
                continue
            seen.add(identity)
            visited += 1
            yield name, item
            for key, child in reversed(list(item.items())):
                stack.append((key if isinstance(key, str) else None, child))
        elif isinstance(item, Sequence) and not isinstance(
            item, (str, bytes, bytearray)
        ):
            identity = id(item)
            if identity in seen:
                continue
            seen.add(identity)
            visited += 1
            for child in reversed(item):
                stack.append((None, child))


def _json_pointer(root: Mapping[str, Any], reference: str) -> _Resolution:
    if not reference.startswith("#/"):
        return _Resolution(None, "local_ref_unsupported")
    current: Any = root
    for raw_part in reference[2:].split("/"):
        part = raw_part.replace("~1", "/").replace("~0", "~")
        if isinstance(current, Mapping) and part in current:
            current = current[part]
            continue
        if (
            isinstance(current, Sequence)
            and not isinstance(current, (str, bytes, bytearray))
            and part.isdigit()
            and int(part) < len(current)
        ):
            current = current[int(part)]
            continue
        return _Resolution(None, "local_ref_unresolved")
    if not isinstance(current, Mapping):
        return _Resolution(None, "local_ref_target_not_object")
    return _Resolution(current)


def _resolve(
    root: Mapping[str, Any],
    value: Any,
    *,
    references: tuple[str, ...] = (),
) -> _Resolution:
    if not isinstance(value, Mapping):
        return _Resolution(None, "schema_node_not_object")
    current = value
    chain = references
    for _ in range(_MAX_REFERENCE_DEPTH):
        reference = current.get("$ref")
        if reference is None:
            return _Resolution(current)
        if not isinstance(reference, str):
            return _Resolution(None, "local_ref_invalid")
        if reference in chain:
            return _Resolution(None, "local_ref_cycle")
        target = _json_pointer(root, reference)
        if target.error_code is not None:
            return target
        assert target.value is not None
        siblings = {key: item for key, item in current.items() if key != "$ref"}
        current = {**target.value, **siblings} if siblings else target.value
        chain = (*chain, reference)
    return _Resolution(None, "local_ref_depth_exceeded")


def _literal_matches(
    root: Mapping[str, Any], schema: Any, expected: str
) -> bool:
    resolved = _resolve(root, schema)
    if resolved.error_code is not None or resolved.value is None:
        return False
    current = resolved.value
    if current.get("const") == expected:
        return True
    enum = current.get("enum")
    return (
        isinstance(enum, Sequence)
        and not isinstance(enum, (str, bytes, bytearray))
        and expected in enum
    )


def _method_params_candidates(
    root: Mapping[str, Any],
) -> tuple[list[Mapping[str, Any]], list[str], bool]:
    candidates: list[Mapping[str, Any]] = []
    errors: list[str] = []
    method_found = False
    seen_candidates: set[int] = set()

    for _, node in _walk(root):
        resolved_node = _resolve(root, node)
        if resolved_node.error_code is not None or resolved_node.value is None:
            continue
        current = resolved_node.value
        properties = current.get("properties")
        direct_method = current.get("method") == "thread/start"
        schema_method = (
            isinstance(properties, Mapping)
            and _literal_matches(root, properties.get("method"), "thread/start")
        )
        if not (direct_method or schema_method):
            continue
        method_found = True
        params = current.get("params") if direct_method else properties.get("params")
        if params is None:
            continue
        resolved_params = _resolve(root, params)
        if resolved_params.error_code is not None:
            errors.append(resolved_params.error_code)
            continue
        assert resolved_params.value is not None
        identity = id(resolved_params.value)
        if identity not in seen_candidates:
            seen_candidates.add(identity)
            candidates.append(resolved_params.value)

    if not method_found:
        return [], errors, False
    if candidates:
        return candidates, errors, True

    for name, node in _walk(root):
        normalized_name = "".join(
            character.lower() for character in (name or "") if character.isalnum()
        )
        title = node.get("title")
        normalized_title = "".join(
            character.lower() for character in title if character.isalnum()
        ) if isinstance(title, str) else ""
        if "threadstartparams" not in {normalized_name, normalized_title}:
            continue
        resolved_params = _resolve(root, node)
        if resolved_params.error_code is not None:
            errors.append(resolved_params.error_code)
            continue
        assert resolved_params.value is not None
        identity = id(resolved_params.value)
        if identity not in seen_candidates:
            seen_candidates.add(identity)
            candidates.append(resolved_params.value)
    return candidates, errors, True


def _json_type(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, Mapping):
        return "object"
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return "array"
    return "unsupported"


def _accepted_types(schema: Mapping[str, Any]) -> tuple[set[str] | None, str | None]:
    declared = schema.get("type")
    if isinstance(declared, str) and declared in _JSON_TYPES:
        return {declared}, None
    if (
        isinstance(declared, Sequence)
        and not isinstance(declared, (str, bytes, bytearray))
        and declared
        and all(isinstance(item, str) for item in declared)
        and set(declared) <= _JSON_TYPES
    ):
        return set(declared), None
    enum = schema.get("enum")
    if (
        declared is None
        and isinstance(enum, Sequence)
        and not isinstance(enum, (str, bytes, bytearray))
        and enum
        and all(isinstance(item, str) for item in enum)
    ):
        return {"string"}, None
    if declared is None:
        return None, "field_type_missing"
    return None, "field_type_invalid"


def _field_findings(
    root: Mapping[str, Any],
    field: str,
    field_schema: Any,
    value: Any,
) -> tuple[list[DiagnosticFinding], bool]:
    resolved = _resolve(root, field_schema)
    if resolved.error_code is not None or resolved.value is None:
        return [_finding(resolved.error_code or "field_schema_unresolved", field)], False
    schema = resolved.value
    findings: list[DiagnosticFinding] = []
    incompatible = False
    accepted_types, type_error = _accepted_types(schema)
    actual_type = _json_type(value)
    if type_error is not None:
        findings.append(_finding(type_error, field))
    elif accepted_types is not None:
        type_matches = actual_type in accepted_types or (
            actual_type == "integer" and "number" in accepted_types
        )
        if not type_matches:
            findings.append(_finding("field_type_incompatible", field))
            incompatible = True

    enum = schema.get("enum")
    if enum is not None:
        if not (
            isinstance(enum, Sequence)
            and not isinstance(enum, (str, bytes, bytearray))
            and enum
            and all(isinstance(item, str) for item in enum)
        ):
            findings.append(_finding("string_enum_invalid", field))
        elif not isinstance(value, str) or value not in enum:
            findings.append(_finding("string_enum_incompatible", field))
            incompatible = True
    return findings, incompatible


def diagnose_thread_start_schema(
    schema: Any,
    request: Any,
) -> AppServerSchemaDiagnostic:
    """Classify a normalized thread/start request against an in-memory schema.

    ``compatible`` means every supplied field and every declared required field
    was decisively checked within this module's bounded JSON Schema subset.
    ``incompatible`` means at least one definite conflict was found.
    ``indeterminate`` means decisive schema information was absent or unsupported.
    """

    if not isinstance(schema, Mapping):
        return AppServerSchemaDiagnostic(
            "indeterminate", (_finding("schema_not_object"),), ()
        )
    if not isinstance(request, Mapping):
        return AppServerSchemaDiagnostic(
            "indeterminate", (_finding("request_not_object"),), ()
        )

    safe_fields: list[str] = []
    for field in request:
        normalized = _safe_field(field)
        if normalized is None:
            return AppServerSchemaDiagnostic(
                "indeterminate", (_finding("request_field_name_invalid"),), ()
            )
        safe_fields.append(normalized)
    checked_fields = tuple(sorted(safe_fields))

    candidates, discovery_errors, method_found = _method_params_candidates(schema)
    if not method_found:
        return AppServerSchemaDiagnostic(
            "indeterminate", (_finding("thread_start_method_not_found"),), checked_fields
        )
    if not candidates:
        codes = discovery_errors or ["thread_start_params_not_found"]
        return AppServerSchemaDiagnostic(
            "indeterminate",
            _ordered_findings([_finding(code) for code in codes]),
            checked_fields,
        )
    if len(candidates) > 1:
        return AppServerSchemaDiagnostic(
            "indeterminate",
            (_finding("thread_start_params_ambiguous"),),
            checked_fields,
        )

    params = candidates[0]
    properties = params.get("properties")
    if not isinstance(properties, Mapping):
        return AppServerSchemaDiagnostic(
            "indeterminate",
            (_finding("params_properties_missing"),),
            checked_fields,
        )
    raw_required = params.get("required", [])
    if not (
        isinstance(raw_required, Sequence)
        and not isinstance(raw_required, (str, bytes, bytearray))
        and all(isinstance(item, str) for item in raw_required)
    ):
        return AppServerSchemaDiagnostic(
            "indeterminate",
            (_finding("params_required_invalid"),),
            checked_fields,
        )

    findings: list[DiagnosticFinding] = []
    incompatible = False
    for required_field in raw_required:
        safe_required = _safe_field(required_field)
        if safe_required is None:
            findings.append(_finding("required_field_name_invalid"))
        elif required_field not in request:
            findings.append(_finding("required_field_missing", safe_required))
            incompatible = True

    additional = params.get("additionalProperties")
    for field, value in request.items():
        assert isinstance(field, str)
        field_schema = properties.get(field)
        if field_schema is None:
            if additional is False:
                findings.append(_finding("request_field_not_allowed", field))
                incompatible = True
            elif additional is True:
                continue
            elif isinstance(additional, Mapping):
                item_findings, item_incompatible = _field_findings(
                    schema, field, additional, value
                )
                findings.extend(item_findings)
                incompatible = incompatible or item_incompatible
            else:
                findings.append(_finding("additional_properties_unspecified", field))
            continue
        item_findings, item_incompatible = _field_findings(
            schema, field, field_schema, value
        )
        findings.extend(item_findings)
        incompatible = incompatible or item_incompatible

    unique_findings = _ordered_findings(findings)
    if incompatible:
        status = "incompatible"
    elif unique_findings or discovery_errors:
        status = "indeterminate"
        unique_findings = _ordered_findings(
            [*unique_findings, *(_finding(code) for code in discovery_errors)]
        )
    else:
        status = "compatible"
    return AppServerSchemaDiagnostic(status, unique_findings, checked_fields)
