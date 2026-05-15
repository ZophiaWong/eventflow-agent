"""Typed retrieval result objects for deterministic M4 retrieval."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from eventflow.schemas import Dependency, HistoricalCase, Playbook

EvidenceSufficiency = Literal["sufficient", "weak", "insufficient"]


class RetrievalScores(BaseModel):
    """Component scores used to calculate retrieval quality."""

    model_config = ConfigDict(extra="forbid")

    dependency_match_score: float = Field(ge=0.0, le=1.0)
    playbook_match_score: float = Field(ge=0.0, le=1.0)
    historical_case_score: float = Field(ge=0.0, le=1.0)
    source_support_score: float = Field(ge=0.0, le=1.0)


class DependencyRetrievalResult(BaseModel):
    """Dependency retrieval result."""

    model_config = ConfigDict(extra="forbid")

    matched_dependencies: list[Dependency] = Field(default_factory=list)
    dependency_match_score: float = Field(ge=0.0, le=1.0)
    notes: list[str] = Field(default_factory=list)


class PlaybookRetrievalResult(BaseModel):
    """Playbook retrieval result."""

    model_config = ConfigDict(extra="forbid")

    matched_playbooks: list[Playbook] = Field(default_factory=list)
    playbook_match_score: float = Field(ge=0.0, le=1.0)
    notes: list[str] = Field(default_factory=list)

    @property
    def selected_playbook(self) -> Playbook | None:
        """Return the best playbook match."""

        return self.matched_playbooks[0] if self.matched_playbooks else None


class HistoricalCaseRetrievalResult(BaseModel):
    """Historical case retrieval result."""

    model_config = ConfigDict(extra="forbid")

    matched_historical_cases: list[HistoricalCase] = Field(default_factory=list)
    historical_case_score: float = Field(ge=0.0, le=1.0)
    notes: list[str] = Field(default_factory=list)


class EvidenceEvaluation(BaseModel):
    """Evidence quality evaluation used by graph routing."""

    model_config = ConfigDict(extra="forbid")

    retrieval_quality: float = Field(ge=0.0, le=1.0)
    evidence_sufficiency: EvidenceSufficiency
    missing_evidence_reasons: list[str] = Field(default_factory=list)
