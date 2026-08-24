from __future__ import annotations

import builtins
import subprocess
import unittest
from copy import deepcopy
from unittest.mock import patch

from agentgov.app_server_schema_diagnostic import (
    AppServerSchemaDiagnostic,
    DiagnosticFinding,
    diagnose_thread_start_schema,
)


def protocol_schema() -> dict:
    return {
        "$defs": {
            "ApprovalPolicy": {
                "type": "string",
                "enum": ["never", "on-request"],
            },
            "ThreadStartParams": {
                "type": "object",
                "additionalProperties": False,
                "required": ["cwd", "ephemeral", "approvalPolicy", "sandbox"],
                "properties": {
                    "cwd": {"type": "string"},
                    "ephemeral": {"type": "boolean"},
                    "approvalPolicy": {"$ref": "#/$defs/ApprovalPolicy"},
                    "sandbox": {
                        "type": "string",
                        "enum": ["read-only", "workspace-write"],
                    },
                },
            },
        },
        "nested": {
            "requests": [
                {
                    "type": "object",
                    "required": ["method", "params"],
                    "properties": {
                        "method": {"const": "thread/start"},
                        "params": {"$ref": "#/$defs/ThreadStartParams"},
                    },
                }
            ]
        },
    }


def normalized_request() -> dict:
    return {
        "cwd": "workspace",
        "ephemeral": True,
        "approvalPolicy": "never",
        "sandbox": "workspace-write",
    }


class AppServerSchemaDiagnosticTests(unittest.TestCase):
    def assert_finding(
        self,
        result: AppServerSchemaDiagnostic,
        code: str,
        field: str | None = None,
    ) -> None:
        self.assertIn(DiagnosticFinding(code, field), result.findings)

    def test_nested_method_and_local_references_are_compatible(self) -> None:
        result = diagnose_thread_start_schema(protocol_schema(), normalized_request())

        self.assertEqual(result.status, "compatible")
        self.assertEqual(result.findings, ())
        self.assertEqual(
            result.checked_fields,
            ("approvalPolicy", "cwd", "ephemeral", "sandbox"),
        )

    def test_direct_method_descriptor_is_discovered(self) -> None:
        schema = {
            "method": "thread/start",
            "params": {
                "properties": {"ephemeral": {"type": "boolean"}},
                "required": ["ephemeral"],
                "additionalProperties": False,
            },
        }

        result = diagnose_thread_start_schema(schema, {"ephemeral": False})

        self.assertEqual(result.status, "compatible")

    def test_local_reference_to_method_literal_is_discovered(self) -> None:
        schema = protocol_schema()
        schema["$defs"]["ThreadStartMethod"] = {
            "type": "string",
            "const": "thread/start",
        }
        schema["nested"]["requests"][0]["properties"]["method"] = {
            "$ref": "#/$defs/ThreadStartMethod"
        }

        result = diagnose_thread_start_schema(schema, normalized_request())

        self.assertEqual(result.status, "compatible")

    def test_named_params_definition_is_a_bounded_fallback(self) -> None:
        schema = {
            "requests": [
                {"properties": {"method": {"enum": ["thread/start"]}}}
            ],
            "definitions": {
                "ThreadStartParams": {
                    "properties": {"cwd": {"type": "string"}},
                    "required": ["cwd"],
                    "additionalProperties": False,
                }
            },
        }

        result = diagnose_thread_start_schema(schema, {"cwd": "workspace"})

        self.assertEqual(result.status, "compatible")

    def test_missing_required_field_is_incompatible(self) -> None:
        request = normalized_request()
        del request["cwd"]

        result = diagnose_thread_start_schema(protocol_schema(), request)

        self.assertEqual(result.status, "incompatible")
        self.assert_finding(result, "required_field_missing", "cwd")

    def test_primitive_type_mismatch_is_incompatible(self) -> None:
        request = normalized_request()
        request["ephemeral"] = "true"

        result = diagnose_thread_start_schema(protocol_schema(), request)

        self.assertEqual(result.status, "incompatible")
        self.assert_finding(result, "field_type_incompatible", "ephemeral")

    def test_integer_satisfies_number_type(self) -> None:
        schema = {
            "method": "thread/start",
            "params": {
                "properties": {"timeout": {"type": "number"}},
                "required": ["timeout"],
                "additionalProperties": False,
            },
        }

        result = diagnose_thread_start_schema(schema, {"timeout": 30})

        self.assertEqual(result.status, "compatible")

    def test_string_enum_mismatch_is_incompatible(self) -> None:
        request = normalized_request()
        request["approvalPolicy"] = "always"

        result = diagnose_thread_start_schema(protocol_schema(), request)

        self.assertEqual(result.status, "incompatible")
        self.assert_finding(result, "string_enum_incompatible", "approvalPolicy")

    def test_unknown_field_is_incompatible_when_explicitly_denied(self) -> None:
        request = normalized_request()
        request["unexpected"] = True

        result = diagnose_thread_start_schema(protocol_schema(), request)

        self.assertEqual(result.status, "incompatible")
        self.assert_finding(result, "request_field_not_allowed", "unexpected")

    def test_unknown_field_is_indeterminate_without_additional_constraint(self) -> None:
        schema = protocol_schema()
        del schema["$defs"]["ThreadStartParams"]["additionalProperties"]
        request = normalized_request()
        request["unexpected"] = True

        result = diagnose_thread_start_schema(schema, request)

        self.assertEqual(result.status, "indeterminate")
        self.assert_finding(
            result, "additional_properties_unspecified", "unexpected"
        )

    def test_missing_field_type_is_indeterminate(self) -> None:
        schema = protocol_schema()
        schema["$defs"]["ThreadStartParams"]["properties"]["cwd"] = {}

        result = diagnose_thread_start_schema(schema, normalized_request())

        self.assertEqual(result.status, "indeterminate")
        self.assert_finding(result, "field_type_missing", "cwd")

    def test_malformed_top_level_inputs_are_normalized(self) -> None:
        schema_result = diagnose_thread_start_schema([], normalized_request())
        request_result = diagnose_thread_start_schema(protocol_schema(), [])

        self.assertEqual(schema_result.status, "indeterminate")
        self.assertEqual(schema_result.reason_codes, ("schema_not_object",))
        self.assertEqual(request_result.status, "indeterminate")
        self.assertEqual(request_result.reason_codes, ("request_not_object",))

    def test_missing_method_is_indeterminate(self) -> None:
        result = diagnose_thread_start_schema(
            {"$defs": {"ThreadStartParams": {"properties": {}}}},
            {},
        )

        self.assertEqual(result.status, "indeterminate")
        self.assertEqual(result.reason_codes, ("thread_start_method_not_found",))

    def test_unresolved_local_reference_is_indeterminate(self) -> None:
        schema = protocol_schema()
        schema["nested"]["requests"][0]["properties"]["params"] = {
            "$ref": "#/$defs/Missing"
        }

        result = diagnose_thread_start_schema(schema, normalized_request())

        self.assertEqual(result.status, "indeterminate")
        self.assertIn("local_ref_unresolved", result.reason_codes)

    def test_same_discovery_and_field_reference_error_is_stably_ordered(self) -> None:
        schema = protocol_schema()
        schema["$defs"]["ThreadStartParams"]["properties"]["cwd"] = {
            "$ref": "#/$defs/Missing"
        }
        schema["other"] = {
            "properties": {
                "method": {"const": "thread/start"},
                "params": {"$ref": "#/$defs/Missing"},
            }
        }

        result = diagnose_thread_start_schema(schema, normalized_request())

        self.assertEqual(result.status, "indeterminate")
        self.assertEqual(
            result.findings,
            (
                DiagnosticFinding("local_ref_unresolved"),
                DiagnosticFinding("local_ref_unresolved", "cwd"),
            ),
        )

    def test_reference_cycle_is_indeterminate(self) -> None:
        schema = protocol_schema()
        schema["nested"]["requests"][0]["properties"]["params"] = {
            "$ref": "#/$defs/A"
        }
        schema["$defs"]["A"] = {"$ref": "#/$defs/B"}
        schema["$defs"]["B"] = {"$ref": "#/$defs/A"}

        result = diagnose_thread_start_schema(schema, normalized_request())

        self.assertEqual(result.status, "indeterminate")
        self.assertIn("local_ref_cycle", result.reason_codes)

    def test_multiple_parameter_contracts_are_indeterminate(self) -> None:
        schema = protocol_schema()
        schema["other"] = {
            "properties": {
                "method": {"const": "thread/start"},
                "params": {
                    "properties": {"cwd": {"type": "string"}},
                    "required": ["cwd"],
                    "additionalProperties": False,
                },
            }
        }

        result = diagnose_thread_start_schema(schema, normalized_request())

        self.assertEqual(result.status, "indeterminate")
        self.assertEqual(result.reason_codes, ("thread_start_params_ambiguous",))

    def test_invalid_field_names_do_not_echo_raw_input(self) -> None:
        private_field = "private field value"

        result = diagnose_thread_start_schema(
            protocol_schema(), {private_field: "not retained"}
        )

        self.assertEqual(result.status, "indeterminate")
        self.assertEqual(result.reason_codes, ("request_field_name_invalid",))
        self.assertNotIn(private_field, repr(result))
        self.assertNotIn("not retained", repr(result))

    def test_result_never_retains_request_values_or_raw_schema(self) -> None:
        schema = protocol_schema()
        request = normalized_request()
        request["cwd"] = "private-workspace-value"

        result = diagnose_thread_start_schema(schema, request)

        rendered = repr(result)
        self.assertNotIn("private-workspace-value", rendered)
        self.assertNotIn("$defs", rendered)
        self.assertEqual(result.status, "compatible")

    def test_diagnostic_performs_no_external_or_filesystem_operations(self) -> None:
        schema = deepcopy(protocol_schema())
        request = normalized_request()

        with (
            patch.object(builtins, "open") as open_file,
            patch.object(subprocess, "run") as run_process,
            patch("socket.socket") as open_socket,
        ):
            result = diagnose_thread_start_schema(schema, request)

        self.assertEqual(result.status, "compatible")
        open_file.assert_not_called()
        run_process.assert_not_called()
        open_socket.assert_not_called()


if __name__ == "__main__":
    unittest.main()
