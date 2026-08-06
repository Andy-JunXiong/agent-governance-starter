"""Model-free semantic review Provider contracts and risk routing."""

from __future__ import annotations

import hashlib
import re
import unicodedata
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from agentgov.human_decision import canonical_document_digest
from agentgov.path_policy import scope_path_error


PROVIDER_CONTRACT = "agentgov.semantic-review-provider-capabilities"
PROVIDER_SCHEMA_VERSION = "1.0"
ROUTE_CONTRACT = "agentgov.semantic-review-route"
ROUTE_SCHEMA_VERSION = "1.0"
RESULT_CONTRACT = "agentgov.semantic-review-result"
RESULT_SCHEMA_VERSION = "1.0"

RISK_LEVELS = {"low", "medium", "high"}
REVIEW_MODES = {"self_review", "independent_review"}
INDEPENDENCE_LEVELS = (
    "same_turn",
    "separate_pass",
    "isolated_context",
    "different_model",
    "different_provider",
)
SOURCE_OWNERS = {"active_host", "user", "organization", "agentgov_hosted"}
ACCESS_MODES = {
    "current_agent_entitlement",
    "user_configured",
    "organization_gateway",
    "hosted_opt_in",
}
COST_OWNERS = {
    "existing_user_entitlement",
    "user",
    "organization",
    "hosted_service",
}
RETENTION_POLICIES = {"none", "host_policy", "provider_policy"}
ROUTES = {
    "no_semantic_review",
    "self_review",
    "independent_review",
    "requires_human_choice",
}
HIGH_RISK_OPTIONS = (
    "human_review",
    "accept_lower_assurance_self_review",
    "configure_provider",
)
OBSERVATION_KINDS = {
    "business",
    "requirement",
    "architecture",
    "scope",
    "implementation",
    "security",
    "data",
}

_ID_RE = re.compile(r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$")
_ROUTE_ID_RE = re.compile(r"^srr-[0-9a-f]{32}$")
_RESULT_ID_RE = re.compile(r"^srv-[0-9a-f]{32}$")
_OBSERVATION_ID_RE = re.compile(r"^obs-[0-9a-f]{16}$")
_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_SENSITIVE_RE = re.compile(
    r"(?i)(?:api[_-]?key|access[_-]?token|auth[_-]?token|password|passwd|secret)\s*[:=]"
)
_ABSOLUTE_PATH_RE = re.compile(
    r"(?i)(?:^|\s)(?:[a-z]:[\\/]|/(?:users|home|var|etc|tmp)/)"
)

_CONTENT_BOUNDARY = {
    "contains_raw_prompt": False,
    "contains_raw_answer": False,
    "contains_transcript": False,
    "contains_assistant_response": False,
    "contains_source_content": False,
    "contains_credentials": False,
    "contains_model_prompt": False,
    "contains_absolute_paths": False,
}
_AUTHORITY_BOUNDARY = {
    "changes_requirements": False,
    "changes_architecture": False,
    "admits_task": False,
    "starts_session": False,
    "authorizes_code_change": False,
    "authorizes_scope_expansion": False,
    "authorizes_exception": False,
    "authorizes_git_operations": False,
    "authorizes_publication": False,
    "authorizes_release": False,
    "authorizes_deployment": False,
    "authorizes_external_write": False,
}


class SemanticReviewContractError(ValueError):
    """Semantic review metadata, routing, or results are invalid or unsafe."""


@dataclass(frozen=True)
class SemanticReviewProviderCapabilities:
    contract: str
    schema_version: str
    provider_id: str
    adapter_id: str
    source: Mapping[str, str]
    availability: Mapping[str, str]
    review_mode: str
    independence_level: str
    cost_owner: str
    data_policy: Mapping[str, Any]
    content_boundary: Mapping[str, bool]
    authority_boundary: Mapping[str, bool]


@dataclass(frozen=True)
class SemanticReviewRoute:
    contract: str
    schema_version: str
    route_id: str
    risk: Mapping[str, Any]
    route: str
    provider: Mapping[str, str] | None
    assurance: Mapping[str, Any]
    options: tuple[str, ...]
    semantics: str
    authority_boundary: Mapping[str, bool]


@dataclass(frozen=True)
class SemanticReviewResult:
    contract: str
    schema_version: str
    result_id: str
    route: Mapping[str, str]
    provider: Mapping[str, str]
    status: str
    semantics: str
    assurance: Mapping[str, str]
    observations: tuple[Mapping[str, Any], ...]
    content_boundary: Mapping[str, bool]
    authority_boundary: Mapping[str, bool]


def semantic_content_boundary() -> Mapping[str, bool]:
    return dict(_CONTENT_BOUNDARY)


def semantic_authority_boundary() -> Mapping[str, bool]:
    return dict(_AUTHORITY_BOUNDARY)


def _identifier(value: Any, *, label: str) -> str:
    if not isinstance(value, str) or len(value) > 120 or not _ID_RE.fullmatch(value):
        raise SemanticReviewContractError(f"{label} is invalid")
    return value


def _safe_text(value: Any, *, label: str, maximum: int = 800) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        raise SemanticReviewContractError(
            f"{label} must be non-empty and at most {maximum} characters"
        )
    if any(unicodedata.category(character).startswith("C") for character in value):
        raise SemanticReviewContractError(f"{label} contains control characters")
    if _SENSITIVE_RE.search(value) or _ABSOLUTE_PATH_RE.search(value):
        raise SemanticReviewContractError(
            f"{label} contains sensitive or host-local content"
        )
    return value


def _false_boundary(value: Any, *, expected: Mapping[str, bool], label: str) -> Mapping[str, bool]:
    if (
        not isinstance(value, Mapping)
        or set(value) != set(expected)
        or any(item is not False for item in value.values())
    ):
        raise SemanticReviewContractError(f"{label} must deny every field")
    return dict(value)


def semantic_review_provider_capabilities_from_payload(
    payload: Any,
) -> SemanticReviewProviderCapabilities:
    fields = {
        "contract",
        "schema_version",
        "provider_id",
        "adapter_id",
        "source",
        "availability",
        "review_mode",
        "independence_level",
        "cost_owner",
        "data_policy",
        "content_boundary",
        "authority_boundary",
    }
    if not isinstance(payload, Mapping) or set(payload) != fields:
        raise SemanticReviewContractError("Provider capabilities have unexpected fields")
    if (
        payload.get("contract") != PROVIDER_CONTRACT
        or payload.get("schema_version") != PROVIDER_SCHEMA_VERSION
    ):
        raise SemanticReviewContractError("Provider capabilities contract is unsupported")
    provider_id = _identifier(payload.get("provider_id"), label="provider_id")
    adapter_id = _identifier(payload.get("adapter_id"), label="adapter_id")

    source = payload.get("source")
    if not isinstance(source, Mapping) or set(source) != {"owner", "access_mode"}:
        raise SemanticReviewContractError("Provider source is invalid")
    owner = source.get("owner")
    access_mode = source.get("access_mode")
    if owner not in SOURCE_OWNERS or access_mode not in ACCESS_MODES:
        raise SemanticReviewContractError("Provider source value is unsupported")
    expected_access = {
        "active_host": "current_agent_entitlement",
        "user": "user_configured",
        "organization": "organization_gateway",
        "agentgov_hosted": "hosted_opt_in",
    }[owner]
    if access_mode != expected_access:
        raise SemanticReviewContractError("Provider owner and access_mode disagree")

    availability = payload.get("availability")
    if not isinstance(availability, Mapping) or set(availability) != {
        "status",
        "reason_code",
    }:
        raise SemanticReviewContractError("Provider availability is invalid")
    if availability.get("status") not in {"available", "unavailable"}:
        raise SemanticReviewContractError("Provider availability status is unsupported")
    reason_code = _identifier(
        availability.get("reason_code"), label="availability reason_code"
    )

    review_mode = payload.get("review_mode")
    independence_level = payload.get("independence_level")
    if review_mode not in REVIEW_MODES or independence_level not in INDEPENDENCE_LEVELS:
        raise SemanticReviewContractError("Provider review assurance is unsupported")
    level_index = INDEPENDENCE_LEVELS.index(independence_level)
    if review_mode == "self_review" and level_index > 2:
        raise SemanticReviewContractError(
            "self-review cannot claim different-model or different-provider independence"
        )
    if review_mode == "independent_review" and level_index < 2:
        raise SemanticReviewContractError(
            "independent review requires at least isolated context"
        )
    if owner == "active_host" and review_mode != "self_review":
        raise SemanticReviewContractError(
            "the active host entitlement can declare only self-review"
        )

    cost_owner = payload.get("cost_owner")
    if cost_owner not in COST_OWNERS:
        raise SemanticReviewContractError("Provider cost_owner is unsupported")
    expected_cost = {
        "active_host": "existing_user_entitlement",
        "user": "user",
        "organization": "organization",
        "agentgov_hosted": "hosted_service",
    }[owner]
    if cost_owner != expected_cost:
        raise SemanticReviewContractError("Provider owner and cost_owner disagree")

    data_policy = payload.get("data_policy")
    if not isinstance(data_policy, Mapping) or set(data_policy) != {
        "retention",
        "external_transfer",
    }:
        raise SemanticReviewContractError("Provider data_policy is invalid")
    if data_policy.get("retention") not in RETENTION_POLICIES:
        raise SemanticReviewContractError("Provider retention policy is unsupported")
    if not isinstance(data_policy.get("external_transfer"), bool):
        raise SemanticReviewContractError("Provider external_transfer must be boolean")

    content = _false_boundary(
        payload.get("content_boundary"),
        expected=_CONTENT_BOUNDARY,
        label="Provider content boundary",
    )
    authority = _false_boundary(
        payload.get("authority_boundary"),
        expected=_AUTHORITY_BOUNDARY,
        label="Provider authority boundary",
    )
    return SemanticReviewProviderCapabilities(
        contract=PROVIDER_CONTRACT,
        schema_version=PROVIDER_SCHEMA_VERSION,
        provider_id=provider_id,
        adapter_id=adapter_id,
        source={"owner": owner, "access_mode": access_mode},
        availability={
            "status": availability["status"],
            "reason_code": reason_code,
        },
        review_mode=review_mode,
        independence_level=independence_level,
        cost_owner=cost_owner,
        data_policy={
            "retention": data_policy["retention"],
            "external_transfer": data_policy["external_transfer"],
        },
        content_boundary=content,
        authority_boundary=authority,
    )


def semantic_review_provider_digest(
    provider: SemanticReviewProviderCapabilities,
) -> str:
    parsed = semantic_review_provider_capabilities_from_payload(asdict(provider))
    return canonical_document_digest(asdict(parsed))


def _provider_binding(
    provider: SemanticReviewProviderCapabilities,
) -> Mapping[str, str]:
    return {
        "provider_id": provider.provider_id,
        "capability_digest": semantic_review_provider_digest(provider),
    }


def _route_identity(
    *,
    risk: Mapping[str, Any],
    route: str,
    provider: Mapping[str, str] | None,
    assurance: Mapping[str, Any],
    options: Sequence[str],
) -> str:
    digest = canonical_document_digest(
        {
            "risk": risk,
            "route": route,
            "provider": provider,
            "assurance": assurance,
            "options": tuple(options),
        }
    )
    return "srr-" + digest.removeprefix("sha256:")[:32]


def _require_active_self_review(
    provider: SemanticReviewProviderCapabilities | None,
) -> SemanticReviewProviderCapabilities:
    if provider is None:
        raise SemanticReviewContractError(
            "medium and high risk require the active Agent self-review capability"
        )
    parsed = semantic_review_provider_capabilities_from_payload(asdict(provider))
    if (
        parsed.source["owner"] != "active_host"
        or parsed.source["access_mode"] != "current_agent_entitlement"
        or parsed.review_mode != "self_review"
        or parsed.availability["status"] != "available"
    ):
        raise SemanticReviewContractError(
            "active Agent self-review capability is unavailable or invalid"
        )
    return parsed


def route_semantic_review(
    *,
    risk_level: str,
    reason_codes: Sequence[str],
    active_agent_provider: SemanticReviewProviderCapabilities | None = None,
    independent_provider: SemanticReviewProviderCapabilities | None = None,
) -> SemanticReviewRoute:
    """Select assurance without invoking a model or applying a human choice."""

    if risk_level not in RISK_LEVELS:
        raise SemanticReviewContractError("semantic review risk level is unsupported")
    normalized_reasons = tuple(
        sorted({_identifier(item, label="risk reason_code") for item in reason_codes})
    )
    if not normalized_reasons:
        raise SemanticReviewContractError("semantic review route requires a reason code")

    provider: SemanticReviewProviderCapabilities | None = None
    options: tuple[str, ...] = ()
    if risk_level == "low":
        route = "no_semantic_review"
        assurance = {
            "requested_review_mode": "none",
            "review_mode": "none",
            "independence_level": "none",
            "lower_than_requested": False,
        }
    elif risk_level == "medium":
        provider = _require_active_self_review(active_agent_provider)
        route = "self_review"
        assurance = {
            "requested_review_mode": "self_review",
            "review_mode": "self_review",
            "independence_level": provider.independence_level,
            "lower_than_requested": False,
        }
    else:
        _require_active_self_review(active_agent_provider)
        if independent_provider is not None:
            candidate = semantic_review_provider_capabilities_from_payload(
                asdict(independent_provider)
            )
        else:
            candidate = None
        if (
            candidate is not None
            and candidate.availability["status"] == "available"
            and candidate.review_mode == "independent_review"
            and INDEPENDENCE_LEVELS.index(candidate.independence_level) >= 2
            and candidate.source["owner"] != "active_host"
        ):
            provider = candidate
            route = "independent_review"
            assurance = {
                "requested_review_mode": "independent_review",
                "review_mode": "independent_review",
                "independence_level": provider.independence_level,
                "lower_than_requested": False,
            }
        else:
            route = "requires_human_choice"
            options = HIGH_RISK_OPTIONS
            assurance = {
                "requested_review_mode": "independent_review",
                "review_mode": "unresolved",
                "independence_level": "none",
                "lower_than_requested": True,
            }

    risk = {"level": risk_level, "reason_codes": normalized_reasons}
    binding = None if provider is None else _provider_binding(provider)
    payload = {
        "contract": ROUTE_CONTRACT,
        "schema_version": ROUTE_SCHEMA_VERSION,
        "route_id": _route_identity(
            risk=risk,
            route=route,
            provider=binding,
            assurance=assurance,
            options=options,
        ),
        "risk": risk,
        "route": route,
        "provider": binding,
        "assurance": assurance,
        "options": list(options),
        "semantics": "advisory",
        "authority_boundary": semantic_authority_boundary(),
    }
    return semantic_review_route_from_payload(payload)


def semantic_review_route_from_payload(payload: Any) -> SemanticReviewRoute:
    fields = {
        "contract",
        "schema_version",
        "route_id",
        "risk",
        "route",
        "provider",
        "assurance",
        "options",
        "semantics",
        "authority_boundary",
    }
    if not isinstance(payload, Mapping) or set(payload) != fields:
        raise SemanticReviewContractError("semantic review route has unexpected fields")
    if (
        payload.get("contract") != ROUTE_CONTRACT
        or payload.get("schema_version") != ROUTE_SCHEMA_VERSION
    ):
        raise SemanticReviewContractError("semantic review route contract is unsupported")
    route_id = payload.get("route_id")
    if not isinstance(route_id, str) or not _ROUTE_ID_RE.fullmatch(route_id):
        raise SemanticReviewContractError("semantic review route_id is invalid")
    risk = payload.get("risk")
    if not isinstance(risk, Mapping) or set(risk) != {"level", "reason_codes"}:
        raise SemanticReviewContractError("semantic review route risk is invalid")
    level = risk.get("level")
    reasons = risk.get("reason_codes")
    if level not in RISK_LEVELS or not isinstance(reasons, (list, tuple)) or not reasons:
        raise SemanticReviewContractError("semantic review route risk value is invalid")
    normalized_reasons = tuple(
        sorted({_identifier(item, label="risk reason_code") for item in reasons})
    )
    if len(normalized_reasons) != len(reasons):
        raise SemanticReviewContractError("semantic review reason_codes must be unique")
    route = payload.get("route")
    if route not in ROUTES or payload.get("semantics") != "advisory":
        raise SemanticReviewContractError("semantic review route semantics are invalid")
    provider_value = payload.get("provider")
    provider = None
    if provider_value is not None:
        if not isinstance(provider_value, Mapping) or set(provider_value) != {
            "provider_id",
            "capability_digest",
        }:
            raise SemanticReviewContractError("semantic review Provider binding is invalid")
        provider_id = _identifier(provider_value.get("provider_id"), label="provider_id")
        digest = provider_value.get("capability_digest")
        if not isinstance(digest, str) or not _DIGEST_RE.fullmatch(digest):
            raise SemanticReviewContractError("Provider capability digest is invalid")
        provider = {"provider_id": provider_id, "capability_digest": digest}
    assurance = payload.get("assurance")
    if not isinstance(assurance, Mapping) or set(assurance) != {
        "requested_review_mode",
        "review_mode",
        "independence_level",
        "lower_than_requested",
    }:
        raise SemanticReviewContractError("semantic review assurance is invalid")
    requested = assurance.get("requested_review_mode")
    actual = assurance.get("review_mode")
    independence = assurance.get("independence_level")
    lower = assurance.get("lower_than_requested")
    if requested not in {"none", *REVIEW_MODES}:
        raise SemanticReviewContractError("requested review mode is unsupported")
    if actual not in {"none", "unresolved", *REVIEW_MODES}:
        raise SemanticReviewContractError("actual review mode is unsupported")
    if independence not in {"none", *INDEPENDENCE_LEVELS} or not isinstance(lower, bool):
        raise SemanticReviewContractError("semantic review assurance value is invalid")
    options_value = payload.get("options")
    if not isinstance(options_value, (list, tuple)):
        raise SemanticReviewContractError("semantic review route options are invalid")
    options = tuple(options_value)

    expected = {
        "no_semantic_review": ("low", "none", "none", "none", False, False, ()),
        "self_review": ("medium", "self_review", "self_review", None, False, True, ()),
        "independent_review": (
            "high",
            "independent_review",
            "independent_review",
            None,
            False,
            True,
            (),
        ),
        "requires_human_choice": (
            "high",
            "independent_review",
            "unresolved",
            "none",
            True,
            False,
            HIGH_RISK_OPTIONS,
        ),
    }[route]
    (
        expected_level,
        expected_requested,
        expected_actual,
        expected_independence,
        expected_lower,
        provider_required,
        expected_options,
    ) = expected
    if (
        level != expected_level
        or requested != expected_requested
        or actual != expected_actual
        or lower is not expected_lower
        or (provider is not None) is not provider_required
        or options != expected_options
        or (expected_independence is not None and independence != expected_independence)
        or (expected_independence is None and independence not in INDEPENDENCE_LEVELS)
    ):
        raise SemanticReviewContractError("semantic review route combination is invalid")
    level_index = (
        None
        if independence == "none"
        else INDEPENDENCE_LEVELS.index(independence)
    )
    if route == "self_review" and (level_index is None or level_index > 2):
        raise SemanticReviewContractError("self-review route overstates independence")
    if route == "independent_review" and (level_index is None or level_index < 2):
        raise SemanticReviewContractError("independent route understates independence")
    normalized_risk = {"level": level, "reason_codes": normalized_reasons}
    normalized_assurance = {
        "requested_review_mode": requested,
        "review_mode": actual,
        "independence_level": independence,
        "lower_than_requested": lower,
    }
    expected_route_id = _route_identity(
        risk=normalized_risk,
        route=route,
        provider=provider,
        assurance=normalized_assurance,
        options=options,
    )
    if route_id != expected_route_id:
        raise SemanticReviewContractError("semantic review route identity drifted")
    authority = _false_boundary(
        payload.get("authority_boundary"),
        expected=_AUTHORITY_BOUNDARY,
        label="semantic review route authority",
    )
    return SemanticReviewRoute(
        contract=ROUTE_CONTRACT,
        schema_version=ROUTE_SCHEMA_VERSION,
        route_id=route_id,
        risk=normalized_risk,
        route=route,
        provider=provider,
        assurance=normalized_assurance,
        options=options,
        semantics="advisory",
        authority_boundary=authority,
    )


def _text_list(value: Any, *, label: str, maximum_items: int = 20) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)) or len(value) > maximum_items:
        raise SemanticReviewContractError(f"{label} must be a bounded list")
    items = tuple(_safe_text(item, label=label, maximum=400) for item in value)
    if len(set(items)) != len(items):
        raise SemanticReviewContractError(f"{label} must be unique")
    return items


def _observation(value: Any) -> Mapping[str, Any]:
    fields = {
        "observation_id",
        "kind",
        "summary",
        "evidence_refs",
        "assumptions",
        "unknowns",
        "recommended_question",
    }
    if not isinstance(value, Mapping) or set(value) != fields:
        raise SemanticReviewContractError("semantic review observation has unexpected fields")
    observation_id = value.get("observation_id")
    if not isinstance(observation_id, str) or not _OBSERVATION_ID_RE.fullmatch(observation_id):
        raise SemanticReviewContractError("semantic review observation_id is invalid")
    kind = value.get("kind")
    if kind not in OBSERVATION_KINDS:
        raise SemanticReviewContractError("semantic review observation kind is unsupported")
    summary = _safe_text(value.get("summary"), label="observation summary")
    refs_value = value.get("evidence_refs")
    if not isinstance(refs_value, (list, tuple)) or not 1 <= len(refs_value) <= 20:
        raise SemanticReviewContractError("evidence_refs must contain 1 to 20 paths")
    refs: list[str] = []
    for ref in refs_value:
        if not isinstance(ref, str) or len(ref) > 240:
            raise SemanticReviewContractError("evidence_refs must be safe repository paths")
        _safe_text(ref, label="evidence_ref", maximum=240)
        if scope_path_error(ref):
            raise SemanticReviewContractError("evidence_refs must be safe repository paths")
        refs.append(ref)
    if len(set(refs)) != len(refs):
        raise SemanticReviewContractError("evidence_refs must be unique")
    assumptions = _text_list(value.get("assumptions"), label="assumptions")
    unknowns = _text_list(value.get("unknowns"), label="unknowns")
    question_value = value.get("recommended_question")
    question = (
        None
        if question_value is None
        else _safe_text(question_value, label="recommended_question")
    )
    return {
        "observation_id": observation_id,
        "kind": kind,
        "summary": summary,
        "evidence_refs": tuple(refs),
        "assumptions": assumptions,
        "unknowns": unknowns,
        "recommended_question": question,
    }


def semantic_review_result_from_payload(payload: Any) -> SemanticReviewResult:
    fields = {
        "contract",
        "schema_version",
        "result_id",
        "route",
        "provider",
        "status",
        "semantics",
        "assurance",
        "observations",
        "content_boundary",
        "authority_boundary",
    }
    if not isinstance(payload, Mapping) or set(payload) != fields:
        raise SemanticReviewContractError("semantic review result has unexpected fields")
    if (
        payload.get("contract") != RESULT_CONTRACT
        or payload.get("schema_version") != RESULT_SCHEMA_VERSION
    ):
        raise SemanticReviewContractError("semantic review result contract is unsupported")
    result_id = payload.get("result_id")
    if not isinstance(result_id, str) or not _RESULT_ID_RE.fullmatch(result_id):
        raise SemanticReviewContractError("semantic review result_id is invalid")
    route = payload.get("route")
    if not isinstance(route, Mapping) or set(route) != {"route_id", "route_digest"}:
        raise SemanticReviewContractError("semantic review result route binding is invalid")
    if not isinstance(route.get("route_id"), str) or not _ROUTE_ID_RE.fullmatch(route["route_id"]):
        raise SemanticReviewContractError("semantic review result route_id is invalid")
    if not isinstance(route.get("route_digest"), str) or not _DIGEST_RE.fullmatch(route["route_digest"]):
        raise SemanticReviewContractError("semantic review result route digest is invalid")
    provider = payload.get("provider")
    if not isinstance(provider, Mapping) or set(provider) != {
        "provider_id",
        "capability_digest",
    }:
        raise SemanticReviewContractError("semantic review result Provider binding is invalid")
    provider_id = _identifier(provider.get("provider_id"), label="provider_id")
    capability_digest = provider.get("capability_digest")
    if not isinstance(capability_digest, str) or not _DIGEST_RE.fullmatch(capability_digest):
        raise SemanticReviewContractError("semantic review result Provider digest is invalid")
    if payload.get("status") != "completed" or payload.get("semantics") != "advisory":
        raise SemanticReviewContractError("semantic review result must be completed advisory")
    assurance = payload.get("assurance")
    if not isinstance(assurance, Mapping) or set(assurance) != {
        "review_mode",
        "independence_level",
    }:
        raise SemanticReviewContractError("semantic review result assurance is invalid")
    if (
        assurance.get("review_mode") not in REVIEW_MODES
        or assurance.get("independence_level") not in INDEPENDENCE_LEVELS
    ):
        raise SemanticReviewContractError("semantic review result assurance is unsupported")
    level_index = INDEPENDENCE_LEVELS.index(assurance["independence_level"])
    if assurance["review_mode"] == "self_review" and level_index > 2:
        raise SemanticReviewContractError("self-review result overstates independence")
    if assurance["review_mode"] == "independent_review" and level_index < 2:
        raise SemanticReviewContractError("independent result understates independence")
    observations_value = payload.get("observations")
    if not isinstance(observations_value, (list, tuple)) or not 1 <= len(observations_value) <= 50:
        raise SemanticReviewContractError("semantic review result requires observations")
    observations = tuple(_observation(item) for item in observations_value)
    if len({item["observation_id"] for item in observations}) != len(observations):
        raise SemanticReviewContractError("semantic review observation IDs must be unique")
    expected_result_id = "srv-" + canonical_document_digest(
        {
            "route_digest": route["route_digest"],
            "provider": {
                "provider_id": provider_id,
                "capability_digest": capability_digest,
            },
            "observations": observations,
        }
    ).removeprefix("sha256:")[:32]
    if result_id != expected_result_id:
        raise SemanticReviewContractError("semantic review result identity drifted")
    content = _false_boundary(
        payload.get("content_boundary"),
        expected=_CONTENT_BOUNDARY,
        label="semantic review result content boundary",
    )
    authority = _false_boundary(
        payload.get("authority_boundary"),
        expected=_AUTHORITY_BOUNDARY,
        label="semantic review result authority",
    )
    return SemanticReviewResult(
        contract=RESULT_CONTRACT,
        schema_version=RESULT_SCHEMA_VERSION,
        result_id=result_id,
        route={"route_id": route["route_id"], "route_digest": route["route_digest"]},
        provider={
            "provider_id": provider_id,
            "capability_digest": capability_digest,
        },
        status="completed",
        semantics="advisory",
        assurance={
            "review_mode": assurance["review_mode"],
            "independence_level": assurance["independence_level"],
        },
        observations=observations,
        content_boundary=content,
        authority_boundary=authority,
    )


def build_semantic_review_result(
    route: SemanticReviewRoute,
    provider: SemanticReviewProviderCapabilities,
    *,
    observations: Sequence[Mapping[str, Any]],
) -> SemanticReviewResult:
    """Bind normalized observations to one executable route without model I/O."""

    parsed_route = semantic_review_route_from_payload(asdict(route))
    parsed_provider = semantic_review_provider_capabilities_from_payload(asdict(provider))
    if parsed_route.route not in {"self_review", "independent_review"}:
        raise SemanticReviewContractError("this route cannot accept a semantic review result")
    binding = _provider_binding(parsed_provider)
    if parsed_provider.availability["status"] != "available" or parsed_route.provider != binding:
        raise SemanticReviewContractError("result Provider does not match the executable route")
    if (
        parsed_route.assurance["review_mode"] != parsed_provider.review_mode
        or parsed_route.assurance["independence_level"]
        != parsed_provider.independence_level
    ):
        raise SemanticReviewContractError("result Provider assurance does not match route")
    normalized = tuple(_observation(item) for item in observations)
    route_digest = canonical_document_digest(asdict(parsed_route))
    identity = canonical_document_digest(
        {
            "route_digest": route_digest,
            "provider": binding,
            "observations": normalized,
        }
    )
    return semantic_review_result_from_payload(
        {
            "contract": RESULT_CONTRACT,
            "schema_version": RESULT_SCHEMA_VERSION,
            "result_id": "srv-" + identity.removeprefix("sha256:")[:32],
            "route": {
                "route_id": parsed_route.route_id,
                "route_digest": route_digest,
            },
            "provider": binding,
            "status": "completed",
            "semantics": "advisory",
            "assurance": {
                "review_mode": parsed_provider.review_mode,
                "independence_level": parsed_provider.independence_level,
            },
            "observations": list(normalized),
            "content_boundary": semantic_content_boundary(),
            "authority_boundary": semantic_authority_boundary(),
        }
    )


def accept_semantic_review_result(
    route: SemanticReviewRoute,
    provider: SemanticReviewProviderCapabilities,
    result: SemanticReviewResult,
) -> SemanticReviewResult:
    """Fail closed on stale route/Provider bindings or assurance substitution."""

    parsed_route = semantic_review_route_from_payload(asdict(route))
    parsed_provider = semantic_review_provider_capabilities_from_payload(asdict(provider))
    parsed_result = semantic_review_result_from_payload(asdict(result))
    if parsed_route.route not in {"self_review", "independent_review"}:
        raise SemanticReviewContractError("route cannot accept a semantic review result")
    expected_provider = _provider_binding(parsed_provider)
    if parsed_provider.availability["status"] != "available":
        raise SemanticReviewContractError("unavailable Provider cannot produce a result")
    if parsed_route.provider != expected_provider or parsed_result.provider != expected_provider:
        raise SemanticReviewContractError("semantic review Provider binding drifted")
    expected_route = {
        "route_id": parsed_route.route_id,
        "route_digest": canonical_document_digest(asdict(parsed_route)),
    }
    if parsed_result.route != expected_route:
        raise SemanticReviewContractError("semantic review route binding is stale")
    expected_assurance = {
        "review_mode": parsed_route.assurance["review_mode"],
        "independence_level": parsed_route.assurance["independence_level"],
    }
    if parsed_result.assurance != expected_assurance:
        raise SemanticReviewContractError("semantic review result assurance drifted")
    return parsed_result
