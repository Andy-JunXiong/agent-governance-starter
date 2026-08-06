from __future__ import annotations

import json
import tomllib
import unittest
from dataclasses import asdict
from pathlib import Path

from agentgov.codex_hooks import CODEX_HOST_CAPABILITIES
from agentgov.coding_agent_transport import InteractionCard
from agentgov.host_interaction import (
    REFERENCE_HOST_CAPABILITIES,
    HostInteractionContractError,
    build_host_interaction_request,
    host_interaction_capabilities_from_payload,
    host_interaction_request_from_payload,
)


ROOT = Path(__file__).resolve().parents[1]


def card(*, kind: str, status: str) -> InteractionCard:
    return InteractionCard(
        contract="agentgov.interaction-card",
        schema_version="1.0",
        kind=kind,
        status=status,
        title=f"{kind} review",
        summary="A bounded human decision is required.",
        facts=({"label": "governance", "value": "human-owned"},),
        actions=("review", "decline"),
        authority_boundary={
            "authorizes_scope_expansion": False,
            "authorizes_exception": False,
            "authorizes_commit": False,
            "authorizes_merge": False,
            "authorizes_deployment": False,
        },
    )


class HostInteractionContractTests(unittest.TestCase):
    def test_schemas_are_strict_vendor_neutral_and_deny_authority(self) -> None:
        capabilities = json.loads(
            (ROOT / "schemas/host-interaction-capabilities.schema.json").read_text(
                encoding="utf-8"
            )
        )
        request = json.loads(
            (ROOT / "schemas/host-interaction-request.schema.json").read_text(
                encoding="utf-8"
            )
        )
        rendered = json.dumps((capabilities, request), sort_keys=True).lower()

        self.assertFalse(capabilities["additionalProperties"])
        self.assertFalse(request["additionalProperties"])
        self.assertNotIn("codex", rendered)
        for rule in capabilities["$defs"]["authority"]["properties"].values():
            self.assertIs(rule["const"], False)
        package = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
        packaged_schemas = package["tool"]["setuptools"]["data-files"][
            "share/agent-governance-starter/schemas"
        ]
        self.assertIn("schemas/*.schema.json", packaged_schemas)

    def test_capabilities_are_strict_complete_and_vendor_neutral(self) -> None:
        payload = asdict(REFERENCE_HOST_CAPABILITIES)
        parsed = host_interaction_capabilities_from_payload(payload)
        unknown = dict(payload)
        unknown["codex_hook"] = "PermissionRequest"
        authority = json.loads(json.dumps(payload))
        authority["authority_boundary"]["authorizes_commit"] = True

        self.assertEqual(parsed.surface_family, "foreground_stream")
        self.assertEqual(
            tuple(parsed.interactions),
            (
                "task_admission",
                "scope_resolution",
                "completion_review",
                "tool_permission",
            ),
        )
        for invalid in (unknown, authority):
            with self.assertRaises(HostInteractionContractError):
                host_interaction_capabilities_from_payload(invalid)

    def test_task_routing_request_is_deterministic_without_fake_core_event(self) -> None:
        first = build_host_interaction_request(
            event_id="evt-" + "a" * 32,
            card=card(kind="task", status="review_required"),
        )
        second = build_host_interaction_request(
            event_id="evt-" + "a" * 32,
            card=card(kind="task", status="review_required"),
        )

        self.assertEqual(first, second)
        self.assertEqual(first.kind, "task_admission")
        self.assertEqual(first.binding["delivery_mode"], "structured")
        self.assertEqual(first.binding["decision_recording"], "adapter_event")
        self.assertEqual(
            first.binding["reason_code"],
            "structured_single_selection_available",
        )
        self.assertEqual(first.options[0]["id"], "route_work_request")
        self.assertEqual(first.options[1]["id"], "prepare_task_proposal")
        self.assertTrue(all(option["next_event"] is None for option in first.options))
        self.assertTrue(all(value is False for value in first.authority_boundary.values()))

    def test_scope_and_completion_requests_map_only_to_existing_core_events(self) -> None:
        scope = build_host_interaction_request(
            event_id="evt-" + "b" * 32,
            card=card(kind="scope", status="blocked"),
        )
        completion = build_host_interaction_request(
            event_id="evt-" + "c" * 32,
            card=card(kind="completion", status="review_ready"),
        )

        self.assertEqual(scope.kind, "scope_resolution")
        self.assertEqual(
            {option["next_event"]["event_type"] for option in scope.options},
            {"scope.decision_recorded"},
        )
        self.assertEqual(completion.kind, "completion_review")
        self.assertEqual(
            {option["next_event"]["event_type"] for option in completion.options},
            {"session.reviewed"},
        )

    def test_non_decision_cards_do_not_invent_interaction_requests(self) -> None:
        active = build_host_interaction_request(
            event_id="evt-" + "d" * 32,
            card=card(kind="task", status="active"),
        )
        observed = build_host_interaction_request(
            event_id="evt-" + "e" * 32,
            card=card(kind="completion", status="observed"),
        )

        self.assertIsNone(active)
        self.assertIsNone(observed)

    def test_request_parser_rejects_vendor_fields_and_applied_decisions(self) -> None:
        request = build_host_interaction_request(
            event_id="evt-" + "f" * 32,
            card=card(kind="completion", status="review_ready"),
        )
        payload = asdict(request)
        vendor = dict(payload)
        vendor["codex_decision"] = "allow"
        applied = json.loads(json.dumps(payload))
        applied["authority_boundary"]["decision_applied"] = True

        self.assertEqual(host_interaction_request_from_payload(payload), request)
        for invalid in (vendor, applied):
            with self.assertRaises(HostInteractionContractError):
                host_interaction_request_from_payload(invalid)

    def test_codex_binding_reports_real_capability_drift(self) -> None:
        for kind in ("task_admission", "scope_resolution", "completion_review"):
            capability = CODEX_HOST_CAPABILITIES.interactions[kind]
            self.assertEqual(capability["delivery_mode"], "context_only")
            self.assertEqual(capability["decision_recording"], "unavailable")
            self.assertEqual(
                capability["reason_code"], "custom_decision_control_unsupported"
            )
        permission = CODEX_HOST_CAPABILITIES.interactions["tool_permission"]
        self.assertEqual(permission["delivery_mode"], "native")
        self.assertEqual(permission["decision_recording"], "host_managed")


if __name__ == "__main__":
    unittest.main()
