from __future__ import annotations

import json
import tomllib
import unittest
from dataclasses import asdict
from pathlib import Path

from agentgov.semantic_review import (
    HIGH_RISK_OPTIONS,
    SemanticReviewContractError,
    accept_semantic_review_result,
    build_semantic_review_result,
    route_semantic_review,
    semantic_review_provider_capabilities_from_payload,
    semantic_review_result_from_payload,
    semantic_review_route_from_payload,
)


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "governance/fixtures/semantic-review"


def load_fixture(name: str):
    payload = json.loads((FIXTURES / name).read_text(encoding="utf-8"))
    return semantic_review_provider_capabilities_from_payload(payload)


def observation(**overrides: object) -> dict:
    value = {
        "observation_id": "obs-0123456789abcdef",
        "kind": "requirement",
        "summary": "The acceptance signal leaves one product choice unresolved.",
        "evidence_refs": ["docs/product-requirements-automatic-governance.md"],
        "assumptions": ["The current product requirement remains authoritative."],
        "unknowns": ["The desired fallback behavior is not yet selected."],
        "recommended_question": "Should the fallback stop or continue with lower assurance?",
    }
    value.update(overrides)
    return value


class SemanticReviewContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.codex = load_fixture("codex-self-review.json")
        self.claude = load_fixture("claude-code-self-review.json")
        self.independent = load_fixture("generic-ide-independent-review.json")
        self.unavailable = load_fixture("provider-unavailable.json")

    def test_schemas_are_strict_packaged_and_core_is_vendor_neutral(self) -> None:
        schema_names = (
            "semantic-review-provider-capabilities.schema.json",
            "semantic-review-route.schema.json",
            "semantic-review-result.schema.json",
        )
        schemas = [
            json.loads((ROOT / "schemas" / name).read_text(encoding="utf-8"))
            for name in schema_names
        ]
        for schema in schemas:
            self.assertFalse(schema["additionalProperties"])

        core = (ROOT / "src/agentgov/semantic_review.py").read_text(encoding="utf-8").lower()
        rendered_schemas = json.dumps(schemas, sort_keys=True).lower()
        for vendor in ("codex", "claude", "generic-ide"):
            self.assertNotIn(vendor, core)
            self.assertNotIn(vendor, rendered_schemas)
        for network_api in ("import requests", "import urllib", "import socket", "import subprocess"):
            self.assertNotIn(network_api, core)

        package = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
        packaged = package["tool"]["setuptools"]["data-files"][
            "share/agent-governance-starter/schemas"
        ]
        self.assertIn("schemas/*.schema.json", packaged)

    def test_all_provider_examples_use_one_contract_parser(self) -> None:
        self.assertEqual(self.codex.source["owner"], "active_host")
        self.assertEqual(self.claude.review_mode, "self_review")
        self.assertEqual(self.independent.review_mode, "independent_review")
        self.assertEqual(self.unavailable.availability["status"], "unavailable")

    def test_provider_contract_rejects_invalid_pairing_claims_and_authority(self) -> None:
        valid = asdict(self.codex)
        invalid_values = []

        wrong_access = json.loads(json.dumps(valid))
        wrong_access["source"]["access_mode"] = "user_configured"
        invalid_values.append(wrong_access)

        exaggerated = json.loads(json.dumps(valid))
        exaggerated["independence_level"] = "different_provider"
        invalid_values.append(exaggerated)

        active_independent = json.loads(json.dumps(valid))
        active_independent["review_mode"] = "independent_review"
        invalid_values.append(active_independent)

        authority = json.loads(json.dumps(valid))
        authority["authority_boundary"]["changes_architecture"] = True
        invalid_values.append(authority)

        raw_content = json.loads(json.dumps(valid))
        raw_content["content_boundary"]["contains_raw_prompt"] = True
        invalid_values.append(raw_content)

        unknown = json.loads(json.dumps(valid))
        unknown["model_name"] = "special-case"
        invalid_values.append(unknown)

        for invalid in invalid_values:
            with self.subTest(invalid=invalid):
                with self.assertRaises(SemanticReviewContractError):
                    semantic_review_provider_capabilities_from_payload(invalid)

    def test_low_risk_routes_without_a_provider_and_is_deterministic(self) -> None:
        first = route_semantic_review(
            risk_level="low",
            reason_codes=["bounded_change"],
            active_agent_provider=None,
            independent_provider=None,
        )
        second = route_semantic_review(
            risk_level="low",
            reason_codes=["bounded_change"],
            active_agent_provider=self.codex,
            independent_provider=self.independent,
        )

        self.assertEqual(first, second)
        self.assertEqual(first.route, "no_semantic_review")
        self.assertIsNone(first.provider)
        self.assertEqual(first.assurance["review_mode"], "none")

    def test_medium_risk_uses_only_the_active_agent_self_review(self) -> None:
        route = route_semantic_review(
            risk_level="medium",
            reason_codes=["requirement_ambiguity"],
            active_agent_provider=self.claude,
            independent_provider=self.independent,
        )

        self.assertEqual(route.route, "self_review")
        self.assertEqual(route.provider["provider_id"], self.claude.provider_id)
        self.assertEqual(route.assurance["independence_level"], "isolated_context")

        with self.assertRaises(SemanticReviewContractError):
            route_semantic_review(
                risk_level="medium",
                reason_codes=["requirement_ambiguity"],
                active_agent_provider=None,
            )

    def test_high_risk_uses_qualifying_independent_provider(self) -> None:
        route = route_semantic_review(
            risk_level="high",
            reason_codes=["architecture_change"],
            active_agent_provider=self.codex,
            independent_provider=self.independent,
        )

        self.assertEqual(route.route, "independent_review")
        self.assertEqual(route.provider["provider_id"], self.independent.provider_id)
        self.assertEqual(route.options, ())
        self.assertFalse(route.assurance["lower_than_requested"])

    def test_high_risk_without_independent_capacity_requires_exact_human_choice(self) -> None:
        for candidate in (None, self.unavailable, self.claude):
            with self.subTest(candidate=candidate):
                route = route_semantic_review(
                    risk_level="high",
                    reason_codes=["architecture_change"],
                    active_agent_provider=self.codex,
                    independent_provider=candidate,
                )
                self.assertEqual(route.route, "requires_human_choice")
                self.assertEqual(route.options, HIGH_RISK_OPTIONS)
                self.assertIsNone(route.provider)
                self.assertEqual(route.assurance["review_mode"], "unresolved")
                self.assertTrue(route.assurance["lower_than_requested"])

    def test_route_parser_rejects_tampering_silent_downgrade_and_false_authority(self) -> None:
        route = route_semantic_review(
            risk_level="medium",
            reason_codes=["scope_drift"],
            active_agent_provider=self.codex,
        )
        invalid_values = []

        stale_id = asdict(route)
        stale_id["route_id"] = "srr-" + "0" * 32
        invalid_values.append(stale_id)

        downgrade = asdict(route)
        downgrade["assurance"]["independence_level"] = "different_provider"
        invalid_values.append(downgrade)

        false_authority = asdict(route)
        false_authority["authority_boundary"]["admits_task"] = True
        invalid_values.append(false_authority)

        high = route_semantic_review(
            risk_level="high",
            reason_codes=["architecture_change"],
            active_agent_provider=self.codex,
            independent_provider=self.unavailable,
        )
        preselected = asdict(high)
        preselected["options"] = ["accept_lower_assurance_self_review"]
        invalid_values.append(preselected)

        for invalid in invalid_values:
            with self.assertRaises(SemanticReviewContractError):
                semantic_review_route_from_payload(invalid)

    def test_result_is_advisory_and_bound_to_exact_self_review_route(self) -> None:
        route = route_semantic_review(
            risk_level="medium",
            reason_codes=["requirement_ambiguity"],
            active_agent_provider=self.codex,
        )
        result = build_semantic_review_result(
            route,
            self.codex,
            observations=[observation()],
        )

        accepted = accept_semantic_review_result(route, self.codex, result)
        self.assertEqual(accepted.status, "completed")
        self.assertEqual(accepted.semantics, "advisory")
        self.assertTrue(all(value is False for value in accepted.authority_boundary.values()))
        self.assertTrue(all(value is False for value in accepted.content_boundary.values()))

    def test_independent_result_preserves_requested_assurance(self) -> None:
        route = route_semantic_review(
            risk_level="high",
            reason_codes=["architecture_change"],
            active_agent_provider=self.codex,
            independent_provider=self.independent,
        )
        result = build_semantic_review_result(
            route,
            self.independent,
            observations=[observation(kind="architecture")],
        )

        accepted = accept_semantic_review_result(route, self.independent, result)
        self.assertEqual(accepted.assurance["review_mode"], "independent_review")
        self.assertEqual(accepted.assurance["independence_level"], "different_provider")

    def test_non_executable_routes_cannot_accept_results(self) -> None:
        low = route_semantic_review(
            risk_level="low",
            reason_codes=["bounded_change"],
        )
        unresolved = route_semantic_review(
            risk_level="high",
            reason_codes=["architecture_change"],
            active_agent_provider=self.codex,
            independent_provider=self.unavailable,
        )
        for route in (low, unresolved):
            with self.assertRaises(SemanticReviewContractError):
                build_semantic_review_result(route, self.codex, observations=[observation()])

    def test_result_rejects_stale_binding_unavailable_provider_and_assurance_substitution(self) -> None:
        route = route_semantic_review(
            risk_level="medium",
            reason_codes=["requirement_ambiguity"],
            active_agent_provider=self.codex,
        )
        result = build_semantic_review_result(route, self.codex, observations=[observation()])

        with self.assertRaises(SemanticReviewContractError):
            accept_semantic_review_result(route, self.claude, result)
        with self.assertRaises(SemanticReviewContractError):
            accept_semantic_review_result(route, self.unavailable, result)

        tampered = asdict(result)
        tampered["assurance"]["independence_level"] = "different_provider"
        with self.assertRaises(SemanticReviewContractError):
            semantic_review_result_from_payload(tampered)

        stale_route = asdict(result)
        stale_route["route"]["route_digest"] = "sha256:" + "0" * 64
        with self.assertRaises(SemanticReviewContractError):
            semantic_review_result_from_payload(stale_route)

    def test_result_rejects_sensitive_content_host_paths_and_false_authority(self) -> None:
        route = route_semantic_review(
            risk_level="medium",
            reason_codes=["requirement_ambiguity"],
            active_agent_provider=self.codex,
        )
        invalid_observations = (
            observation(summary="password=do-not-store"),
            observation(evidence_refs=["C:\\Users\\person\\private.txt"]),
            observation(evidence_refs=["../outside.md"]),
            observation(evidence_refs=[]),
        )
        for item in invalid_observations:
            with self.assertRaises(SemanticReviewContractError):
                build_semantic_review_result(route, self.codex, observations=[item])

        result = build_semantic_review_result(route, self.codex, observations=[observation()])
        raw = asdict(result)
        raw["content_boundary"]["contains_transcript"] = True
        with self.assertRaises(SemanticReviewContractError):
            semantic_review_result_from_payload(raw)

        authority = asdict(result)
        authority["authority_boundary"]["changes_requirements"] = True
        with self.assertRaises(SemanticReviewContractError):
            semantic_review_result_from_payload(authority)


if __name__ == "__main__":
    unittest.main()
