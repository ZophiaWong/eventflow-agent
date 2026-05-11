"""Pydantic schemas for EventFlow Agent M1."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, model_validator

from eventflow.schemas.enums import (
    EventType,
    ExpectedRoute,
    LabelStatus,
    RecommendedAction,
    ReviewStatus,
    RiskLevel,
    SourceType,
)

_SYNTHETIC_BLOCKED_PATTERNS = (
    re.compile(r"\bCVE-\d{4}-\d{4,}\b", re.IGNORECASE),
)


class EventFlowModel(BaseModel):
    """Base schema with strict field names and stripped strings."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


def _has_blocked_synthetic_value(value: Any) -> bool:
    if isinstance(value, str):
        return any(pattern.search(value) for pattern in _SYNTHETIC_BLOCKED_PATTERNS)
    if isinstance(value, dict):
        return any(_has_blocked_synthetic_value(item) for item in value.values())
    if isinstance(value, list | tuple | set):
        return any(_has_blocked_synthetic_value(item) for item in value)
    return False


def _is_example_url(url: str) -> bool:
    parsed = urlparse(url)
    host = parsed.hostname or ""
    return parsed.scheme in {"http", "https"} and (
        host == "example.com" or host.endswith(".example.com")
    )


class RawSignal(EventFlowModel):
    """Unprocessed external signal."""

    signal_id: str = Field(min_length=1)
    source_type: SourceType
    vendor: str = Field(min_length=1)
    title: str = Field(min_length=1)
    content: str = Field(min_length=1)
    published_at: datetime | None = None
    source_url: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    is_synthetic: bool

    @model_validator(mode="after")
    def validate_synthetic_safety(self) -> RawSignal:
        if not self.is_synthetic:
            return self

        if self.source_url is not None and not _is_example_url(self.source_url):
            raise ValueError("synthetic source_url must be null or use example.com")

        values_to_check = {
            "signal_id": self.signal_id,
            "title": self.title,
            "content": self.content,
            "source_url": self.source_url,
            "metadata": self.metadata,
        }
        if _has_blocked_synthetic_value(values_to_check):
            raise ValueError("synthetic records must not use real CVE identifiers")

        return self


class EventCandidate(EventFlowModel):
    """First structured interpretation of a raw signal."""

    candidate_id: str = Field(min_length=1)
    source_signal_id: str = Field(min_length=1)
    event_type: EventType
    vendor: str = Field(min_length=1)
    affected_dependencies: list[str]
    summary: str = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)
    evidence_refs: list[str] = Field(default_factory=list)


class EventCluster(EventFlowModel):
    """Group of duplicate or related event candidates."""

    cluster_id: str = Field(min_length=1)
    candidate_ids: list[str] = Field(min_length=1)
    canonical_title: str = Field(min_length=1)
    canonical_summary: str = Field(min_length=1)
    event_type: EventType
    vendor: str = Field(min_length=1)
    affected_dependencies: list[str]
    first_seen_at: datetime | None = None
    last_seen_at: datetime | None = None
    confidence: float = Field(ge=0.0, le=1.0)

    @model_validator(mode="after")
    def validate_seen_window(self) -> EventCluster:
        if (
            self.first_seen_at is not None
            and self.last_seen_at is not None
            and self.last_seen_at < self.first_seen_at
        ):
            raise ValueError("last_seen_at cannot be earlier than first_seen_at")
        return self


class EvidencePack(EventFlowModel):
    """Retrieved context supporting risk assessment."""

    evidence_id: str = Field(min_length=1)
    source_signal_ids: list[str] = Field(min_length=1)
    matched_dependencies: list[str] = Field(default_factory=list)
    matched_playbooks: list[str] = Field(default_factory=list)
    matched_historical_cases: list[str] = Field(default_factory=list)
    evidence_notes: list[str] = Field(default_factory=list)
    retrieval_quality: float = Field(ge=0.0, le=1.0)


class RiskAssessment(EventFlowModel):
    """Internal risk judgment and route signal."""

    risk_level: RiskLevel
    confidence: float = Field(ge=0.0, le=1.0)
    risk_factors: list[str]
    uncertainty_factors: list[str] = Field(default_factory=list)
    recommended_action: RecommendedAction
    requires_human_review: bool
    rationale: str = Field(min_length=1)


class HumanReviewDecision(EventFlowModel):
    """Reviewer decision captured for human-in-the-loop cases."""

    review_id: str = Field(min_length=1)
    reviewer_id: str = Field(min_length=1)
    decision: ReviewStatus
    edited_risk_level: RiskLevel | None = None
    edited_recommended_action: RecommendedAction | None = None
    comments: str | None = None
    reviewed_at: datetime | None = None

    @model_validator(mode="after")
    def validate_decision_context(self) -> HumanReviewDecision:
        if (
            self.decision == ReviewStatus.EDITED
            and self.edited_risk_level is None
            and self.edited_recommended_action is None
        ):
            raise ValueError("edited decisions require at least one edited field")

        if (
            self.decision == ReviewStatus.REQUESTED_MORE_EVIDENCE
            and not self.comments
        ):
            raise ValueError("requested_more_evidence decisions require comments")

        return self


class EventRiskBrief(EventFlowModel):
    """Final structured decision-support output."""

    brief_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    event_type: EventType
    summary: str = Field(min_length=1)
    affected_dependencies: list[str]
    risk_level: RiskLevel
    confidence: float = Field(ge=0.0, le=1.0)
    evidence_refs: list[str]
    risk_rationale: str = Field(min_length=1)
    recommended_action: RecommendedAction
    review_status: ReviewStatus
    created_at: datetime | None = None


class Dependency(EventFlowModel):
    """External dependency used by a simulated product module."""

    dependency_id: str = Field(min_length=1)
    vendor: str = Field(min_length=1)
    dependency_name: str = Field(min_length=1)
    dependency_type: str = Field(min_length=1)
    criticality: RiskLevel
    used_for: str = Field(min_length=1)


class ProductModule(EventFlowModel):
    """Simulated product module and its dependencies."""

    module_id: str = Field(min_length=1)
    module_name: str = Field(min_length=1)
    business_criticality: RiskLevel
    dependencies: list[Dependency] = Field(min_length=1)


class DependencyMap(EventFlowModel):
    """Simulated SaaS product dependency map."""

    product_name: str = Field(min_length=1)
    modules: list[ProductModule] = Field(min_length=1)


class Playbook(EventFlowModel):
    """Rule guidance for event type and dependency criticality."""

    playbook_id: str = Field(min_length=1)
    event_type: EventType
    dependency_criticality: RiskLevel
    risk_level: RiskLevel
    recommended_action: RecommendedAction
    review_required: bool
    guidance: str = Field(min_length=1)


class HistoricalCase(EventFlowModel):
    """Synthetic past event case used for future retrieval."""

    case_id: str = Field(min_length=1)
    event_type: EventType
    vendor: str = Field(min_length=1)
    affected_dependencies: list[str]
    summary: str = Field(min_length=1)
    risk_level: RiskLevel
    action_taken: RecommendedAction
    outcome: str = Field(min_length=1)
    lessons_learned: str | None = None
    is_synthetic: bool

    @model_validator(mode="after")
    def validate_synthetic_case(self) -> HistoricalCase:
        if self.is_synthetic and _has_blocked_synthetic_value(self.model_dump()):
            raise ValueError("synthetic historical cases must not use real CVE IDs")
        return self


class EvalCase(EventFlowModel):
    """Labeled case for replay evaluation."""

    eval_id: str = Field(min_length=1)
    input_signal_id: str = Field(min_length=1)
    expected_event_type: EventType
    expected_affected_dependencies: list[str]
    expected_risk_level: RiskLevel
    expected_route: ExpectedRoute
    expected_recommended_action: RecommendedAction
    label_rationale: str = Field(min_length=1)
    label_status: LabelStatus
