"""M4 deterministic evidence retrieval node logic."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from eventflow.retrieval import (
    build_evidence_pack,
    build_retrieval_query,
    build_retrieval_scores,
    retrieve_dependencies,
    retrieve_historical_cases,
    retrieve_playbooks,
    score_source_support,
)
from eventflow.retrieval.types import RetrievalScores
from eventflow.schemas import (
    DependencyMap,
    EventCluster,
    EvidencePack,
    HistoricalCase,
    Playbook,
    RawSignal,
    RetrievalQuery,
)


class EvidenceRetrievalOutput(BaseModel):
    """Output of deterministic evidence retrieval before quality evaluation."""

    model_config = ConfigDict(extra="forbid")

    retrieval_query: RetrievalQuery
    evidence_pack: EvidencePack
    matched_playbook: Playbook | None
    retrieval_scores: RetrievalScores


def retrieve_evidence(
    signal: RawSignal,
    cluster: EventCluster,
    dependency_map: DependencyMap,
    playbooks: list[Playbook],
    historical_cases: list[HistoricalCase],
    attempt: int = 0,
) -> EvidenceRetrievalOutput:
    """Retrieve dependency, playbook, and historical evidence for a cluster."""

    query = build_retrieval_query(cluster, attempt=attempt)
    dependency_result = retrieve_dependencies(query, dependency_map)
    playbook_result = retrieve_playbooks(
        query=query,
        matched_dependencies=dependency_result.matched_dependencies,
        playbooks=playbooks,
    )
    historical_case_result = retrieve_historical_cases(query, historical_cases)
    evidence_pack = build_evidence_pack(
        query=query,
        source_signal=signal,
        dependency_result=dependency_result,
        playbook_result=playbook_result,
        historical_case_result=historical_case_result,
    )
    retrieval_scores = build_retrieval_scores(
        dependency_match_score=dependency_result.dependency_match_score,
        playbook_match_score=playbook_result.playbook_match_score,
        historical_case_score=historical_case_result.historical_case_score,
        source_support_score=score_source_support(signal),
    )
    return EvidenceRetrievalOutput(
        retrieval_query=query,
        evidence_pack=evidence_pack,
        matched_playbook=playbook_result.selected_playbook,
        retrieval_scores=retrieval_scores,
    )
