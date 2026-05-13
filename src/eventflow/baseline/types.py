"""Structured results for the rule-based baseline workflow."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from eventflow.schemas import (
    EventCandidate,
    EventRiskBrief,
    EvidencePack,
    ExpectedRoute,
    RiskAssessment,
)


class BaselineError(BaseModel):
    """Structured baseline workflow error."""

    model_config = ConfigDict(extra="forbid")

    stage: str = Field(min_length=1)
    error_code: str = Field(min_length=1)
    message: str = Field(min_length=1)
    signal_id: str | None = None
    details: dict[str, object] = Field(default_factory=dict)


class BaselineResult(BaseModel):
    """Single-signal baseline workflow result."""

    model_config = ConfigDict(extra="forbid")

    signal_id: str = Field(min_length=1)
    candidate: EventCandidate | None = None
    evidence_pack: EvidencePack | None = None
    risk_assessment: RiskAssessment | None = None
    brief: EventRiskBrief | None = None
    route: ExpectedRoute
    errors: list[BaselineError] = Field(default_factory=list)

    @property
    def succeeded(self) -> bool:
        """Return whether the baseline produced a brief."""

        return self.brief is not None and not self.errors


class BaselineEvalMetrics(BaseModel):
    """Draft eval metrics for the deterministic baseline."""

    model_config = ConfigDict(extra="forbid")

    total_cases: int
    completed_cases: int
    event_type_match_rate: float
    dependency_exact_match_rate: float
    risk_level_match_rate: float
    route_match_rate: float
    recommended_action_match_rate: float
