"""Typed LangGraph state for the M3 workflow."""

from __future__ import annotations

from typing import Annotated, Any, Literal, TypedDict, TypeVar

from pydantic import BaseModel, ConfigDict, Field

from eventflow.schemas import (
    DependencyMap,
    EventCandidate,
    EventCluster,
    EventRiskBrief,
    EvidencePack,
    ExpectedRoute,
    HistoricalCase,
    HumanReviewDecision,
    Playbook,
    RawSignal,
    RetrievalQuery,
    RiskAssessment,
)
from eventflow.retrieval.types import (
    EvidenceEvaluation,
    EvidenceSufficiency,
    RetrievalScores,
)

ListItemT = TypeVar("ListItemT")


def _append_list(
    current: list[ListItemT] | None,
    update: list[ListItemT] | None,
) -> list[ListItemT]:
    return [*(current or []), *(update or [])]


class WorkflowError(BaseModel):
    """Structured fatal workflow error."""

    model_config = ConfigDict(extra="forbid")

    error_id: str = Field(min_length=1)
    node_name: str = Field(min_length=1)
    error_code: str = Field(min_length=1)
    message: str = Field(min_length=1)
    input_refs: list[str] = Field(default_factory=list)
    severity: Literal["error", "critical"] = "error"


class AuditLogEntry(BaseModel):
    """Lightweight workflow audit entry."""

    model_config = ConfigDict(extra="forbid")

    node_name: str = Field(min_length=1)
    event: str = Field(min_length=1)
    status: Literal["success", "warning", "error"]
    message: str = Field(min_length=1)
    input_refs: list[str] = Field(default_factory=list)
    output_refs: list[str] = Field(default_factory=list)
    route_decision: ExpectedRoute | None = None
    error_code: str | None = None


class EventFlowState(TypedDict, total=False):
    """Runtime state carried through one EventFlow graph run."""

    run_id: str

    raw_signal: RawSignal
    event_candidate: EventCandidate
    event_cluster: EventCluster
    retrieval_query: RetrievalQuery
    evidence_pack: EvidencePack
    evidence_evaluation: EvidenceEvaluation
    evidence_sufficiency: EvidenceSufficiency
    matched_playbook: Playbook
    risk_assessment: RiskAssessment
    human_review_decision: HumanReviewDecision
    event_risk_brief: EventRiskBrief

    route_decision: ExpectedRoute

    dependency_map: DependencyMap
    playbooks: list[Playbook]
    historical_cases: list[HistoricalCase]
    retrieval_scores: RetrievalScores
    errors: Annotated[list[WorkflowError], _append_list]
    audit_log: Annotated[list[AuditLogEntry], _append_list]
    metrics: dict[str, Any]


def workflow_error(
    node_name: str,
    error_code: str,
    message: str,
    input_refs: list[str] | None = None,
    severity: Literal["error", "critical"] = "error",
) -> WorkflowError:
    """Create a deterministic workflow error."""

    return WorkflowError(
        error_id=f"err_{node_name}_{error_code}",
        node_name=node_name,
        error_code=error_code,
        message=message,
        input_refs=input_refs or [],
        severity=severity,
    )


def audit_entry(
    node_name: str,
    event: str,
    status: Literal["success", "warning", "error"],
    message: str,
    input_refs: list[str] | None = None,
    output_refs: list[str] | None = None,
    route_decision: ExpectedRoute | None = None,
    error_code: str | None = None,
) -> AuditLogEntry:
    """Create a lightweight audit entry."""

    return AuditLogEntry(
        node_name=node_name,
        event=event,
        status=status,
        message=message,
        input_refs=input_refs or [],
        output_refs=output_refs or [],
        route_decision=route_decision,
        error_code=error_code,
    )
