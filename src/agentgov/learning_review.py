"""Immutable human Learning reviews bound to current Protection Event candidates."""

from __future__ import annotations

import hashlib
import json
import re
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

from agentgov.event_store import (
    GovernanceEvent,
    load_governance_events,
    utc_now,
    write_local_record,
)


LEARNING_REVIEW_CONTRACT = "agentgov.learning-review"
LEARNING_REVIEW_SCHEMA_VERSION = "1.0"
LEARNING_REVIEW_DIRECTORY = Path(".agentgov/learning-reviews")
LEARNING_SIGNAL_CLASSES = (
    "scope_boundary",
    "validation_failure",
    "stale_evidence",
    "incomplete_completion",
)
LEARNING_DISPOSITIONS = (
    "confirmed_constraint_gap",
    "false_positive",
    "intentional_override",
    "consumer_configuration_needed",
    "improvement_candidate",
    "no_change_needed",
)
HUMAN_PRODUCT_OWNER_ROLE = "human_product_owner"

_REVIEW_ID_RE = re.compile(r"^lrv-[0-9a-f]{32}$")
_EVENT_ID_RE = re.compile(r"^evt-[0-9a-f]{32}$")
_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_REASON_RE = re.compile(r"^[a-z][a-z0-9_]*$")


class LearningReviewPolicyError(RuntimeError):
    """A Learning review is unsafe, stale, or cannot be supported."""


@dataclass(frozen=True)
class LearningReview:
    contract: str
    schema_version: str
    review_id: str
    recorded_at: str
    actor: Mapping[str, str]
    signal_class: str
    source_event_ids: tuple[str, ...]
    candidate_digest: str
    disposition: str
    reason_codes: tuple[str, ...]
    semantics: str
    authority_boundary: Mapping[str, bool]


def learning_review_authority_boundary() -> Mapping[str, bool]:
    return {
        "authorizes_resolution": False,
        "authorizes_code_change": False,
        "authorizes_scope_expansion": False,
        "authorizes_exception": False,
        "authorizes_commit": False,
        "authorizes_merge": False,
        "authorizes_deployment": False,
        "authorizes_release": False,
    }


def _parse_utc(value: Any) -> str:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise LearningReviewPolicyError("recorded_at must be a UTC Z timestamp")
    try:
        datetime.fromisoformat(value.removesuffix("Z") + "+00:00").astimezone(
            timezone.utc
        )
    except ValueError as exc:
        raise LearningReviewPolicyError("recorded_at must be a valid UTC Z timestamp") from exc
    return value


def _safe_root(repository: Path) -> Path:
    if repository.is_symlink() or not repository.exists() or not repository.is_dir():
        raise LearningReviewPolicyError(
            "repository root must be an existing non-symbolic-link directory"
        )
    return repository.resolve()


def protection_signal_class(event: GovernanceEvent) -> str | None:
    """Return the fixed Learning signal class for one lifecycle event."""

    if event.event_type == "scope.checked" and event.outcome == "failed":
        return "scope_boundary"
    if event.event_type == "validation.completed" and event.outcome == "failed":
        return "validation_failure"
    if event.event_type == "validation.completed" and event.outcome == "stale":
        return "stale_evidence"
    if event.event_type == "completion.reconciled" and event.outcome == "needs_evidence":
        return "incomplete_completion"
    return None


def learning_candidate_event_ids(
    events: Iterable[GovernanceEvent], signal_class: str
) -> tuple[str, ...]:
    if signal_class not in LEARNING_SIGNAL_CLASSES:
        raise LearningReviewPolicyError("signal_class is unsupported")
    identities = sorted(
        {
            event.event_id
            for event in events
            if protection_signal_class(event) == signal_class
        }
    )
    if len(identities) < 2:
        raise LearningReviewPolicyError(
            "Learning review requires at least two current Protection Events of one class"
        )
    return tuple(identities)


def learning_candidate_digest(
    signal_class: str, source_event_ids: Iterable[str]
) -> str:
    if signal_class not in LEARNING_SIGNAL_CLASSES:
        raise LearningReviewPolicyError("signal_class is unsupported")
    identities = tuple(source_event_ids)
    if (
        len(identities) < 2
        or len(identities) > 10000
        or identities != tuple(sorted(set(identities)))
        or any(not isinstance(item, str) or not _EVENT_ID_RE.fullmatch(item) for item in identities)
    ):
        raise LearningReviewPolicyError(
            "source_event_ids must contain at least two sorted unique event identities"
        )
    document = {
        "contract": "agentgov.learning-candidate",
        "schema_version": "1.0",
        "signal_class": signal_class,
        "source_event_ids": list(identities),
    }
    encoded = json.dumps(
        document, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def learning_review_from_payload(
    payload: Any, *, source_name: str = "embedded-learning-review.json"
) -> LearningReview:
    fields = {
        "contract",
        "schema_version",
        "review_id",
        "recorded_at",
        "actor",
        "signal_class",
        "source_event_ids",
        "candidate_digest",
        "disposition",
        "reason_codes",
        "semantics",
        "authority_boundary",
    }
    if not isinstance(payload, Mapping) or set(payload) != fields:
        raise LearningReviewPolicyError(
            f"Learning review {source_name!r} has unexpected fields"
        )
    if (
        payload.get("contract") != LEARNING_REVIEW_CONTRACT
        or payload.get("schema_version") != LEARNING_REVIEW_SCHEMA_VERSION
    ):
        raise LearningReviewPolicyError(
            f"Learning review {source_name!r} uses an unsupported contract"
        )
    review_id = payload.get("review_id")
    if not isinstance(review_id, str) or not _REVIEW_ID_RE.fullmatch(review_id):
        raise LearningReviewPolicyError(f"Learning review {source_name!r} has an invalid id")
    recorded_at = _parse_utc(payload.get("recorded_at"))
    actor = payload.get("actor")
    expected_actor = {"class": "human", "role": HUMAN_PRODUCT_OWNER_ROLE}
    if actor != expected_actor:
        raise LearningReviewPolicyError(
            "Learning review attribution must use the canonical human product-owner role"
        )
    signal_class = payload.get("signal_class")
    if signal_class not in LEARNING_SIGNAL_CLASSES:
        raise LearningReviewPolicyError("Learning review signal_class is unsupported")
    identities_value = payload.get("source_event_ids")
    if not isinstance(identities_value, (list, tuple)):
        raise LearningReviewPolicyError("Learning review source_event_ids must be an array")
    identities = tuple(identities_value)
    expected_digest = learning_candidate_digest(signal_class, identities)
    digest = payload.get("candidate_digest")
    if not isinstance(digest, str) or not _DIGEST_RE.fullmatch(digest) or digest != expected_digest:
        raise LearningReviewPolicyError("Learning review candidate_digest is invalid")
    disposition = payload.get("disposition")
    if disposition not in LEARNING_DISPOSITIONS:
        raise LearningReviewPolicyError("Learning review disposition is unsupported")
    reason_value = payload.get("reason_codes")
    if (
        not isinstance(reason_value, (list, tuple))
        or len(reason_value) > 10
        or len(reason_value) != len(set(reason_value))
        or any(not isinstance(code, str) or not _REASON_RE.fullmatch(code) for code in reason_value)
    ):
        raise LearningReviewPolicyError(
            "Learning review reason_codes must be at most ten unique snake_case values"
        )
    if payload.get("semantics") != "human_judgment":
        raise LearningReviewPolicyError("Learning review semantics must remain human_judgment")
    if payload.get("authority_boundary") != learning_review_authority_boundary():
        raise LearningReviewPolicyError("Learning review grants unsupported authority")
    return LearningReview(
        contract=LEARNING_REVIEW_CONTRACT,
        schema_version=LEARNING_REVIEW_SCHEMA_VERSION,
        review_id=review_id,
        recorded_at=recorded_at,
        actor=expected_actor,
        signal_class=signal_class,
        source_event_ids=identities,
        candidate_digest=digest,
        disposition=disposition,
        reason_codes=tuple(reason_value),
        semantics="human_judgment",
        authority_boundary=learning_review_authority_boundary(),
    )


def build_learning_review(
    repository: Path,
    *,
    signal_class: str,
    disposition: str,
    reason_codes: Iterable[str] = (),
    events: Iterable[GovernanceEvent] | None = None,
    recorded_at: str | None = None,
    review_id: str | None = None,
) -> LearningReview:
    root = _safe_root(repository)
    visible_events = tuple(events) if events is not None else load_governance_events(
        root / ".agentgov" / "events"
    ).events
    identities = learning_candidate_event_ids(visible_events, signal_class)
    payload = {
        "contract": LEARNING_REVIEW_CONTRACT,
        "schema_version": LEARNING_REVIEW_SCHEMA_VERSION,
        "review_id": review_id or f"lrv-{uuid.uuid4().hex}",
        "recorded_at": recorded_at or utc_now(),
        "actor": {"class": "human", "role": HUMAN_PRODUCT_OWNER_ROLE},
        "signal_class": signal_class,
        "source_event_ids": list(identities),
        "candidate_digest": learning_candidate_digest(signal_class, identities),
        "disposition": disposition,
        "reason_codes": list(reason_codes),
        "semantics": "human_judgment",
        "authority_boundary": learning_review_authority_boundary(),
    }
    return learning_review_from_payload(payload, source_name="planned-learning-review.json")


def revalidate_learning_review(repository: Path, review: LearningReview) -> None:
    root = _safe_root(repository)
    events = load_governance_events(root / ".agentgov" / "events").events
    identities = learning_candidate_event_ids(events, review.signal_class)
    digest = learning_candidate_digest(review.signal_class, identities)
    if identities != review.source_event_ids or digest != review.candidate_digest:
        raise LearningReviewPolicyError(
            "Learning review preview is stale because the current candidate changed"
        )


def write_learning_review(repository: Path, review: LearningReview) -> str:
    validated = learning_review_from_payload(
        asdict(review), source_name=f"{review.review_id}.json"
    )
    return write_local_record(
        repository,
        area="learning-reviews",
        record_id=validated.review_id,
        payload=asdict(validated),
    )


def load_learning_reviews(repository: Path) -> tuple[LearningReview, ...]:
    root = _safe_root(repository)
    directory = root / LEARNING_REVIEW_DIRECTORY
    if not directory.exists():
        return ()
    if directory.is_symlink() or not directory.is_dir():
        raise LearningReviewPolicyError(
            "Learning review path must be a non-symbolic-link directory"
        )
    reviews: list[LearningReview] = []
    seen: set[str] = set()
    for path in sorted(directory.glob("*.json"), key=lambda item: item.name):
        if path.is_symlink() or not path.is_file() or not _REVIEW_ID_RE.fullmatch(path.stem):
            raise LearningReviewPolicyError(
                "Learning review files must be regular files with matching identities"
            )
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise LearningReviewPolicyError(
                f"cannot read Learning review {path.name!r}: {exc}"
            ) from exc
        review = learning_review_from_payload(payload, source_name=path.name)
        if path.stem != review.review_id or review.review_id in seen:
            raise LearningReviewPolicyError(
                "Learning review identity is duplicated or mismatched"
            )
        seen.add(review.review_id)
        reviews.append(review)
    return tuple(sorted(reviews, key=lambda item: (item.recorded_at, item.review_id)))
