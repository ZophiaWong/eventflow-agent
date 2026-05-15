"""Build EvidencePack objects from deterministic retrieval results."""

from __future__ import annotations

from eventflow.retrieval.types import (
    DependencyRetrievalResult,
    HistoricalCaseRetrievalResult,
    PlaybookRetrievalResult,
)
from eventflow.schemas import EvidencePack, RawSignal, RetrievalQuery


def build_evidence_pack(
    query: RetrievalQuery,
    source_signal: RawSignal,
    dependency_result: DependencyRetrievalResult,
    playbook_result: PlaybookRetrievalResult,
    historical_case_result: HistoricalCaseRetrievalResult,
) -> EvidencePack:
    """Combine retrieval results into the EvidencePack boundary object."""

    notes = [
        f"Raw signal {source_signal.signal_id} from {source_signal.source_type.value}.",
        *dependency_result.notes,
        *playbook_result.notes,
        *historical_case_result.notes,
    ]
    return EvidencePack(
        evidence_id=f"evidence_{source_signal.signal_id}_attempt_{query.attempt}",
        query=query,
        source_signal_ids=[source_signal.signal_id],
        matched_dependencies=[
            dependency.dependency_id
            for dependency in dependency_result.matched_dependencies
        ],
        matched_playbooks=[
            playbook.playbook_id for playbook in playbook_result.matched_playbooks
        ],
        matched_historical_cases=[
            case.case_id for case in historical_case_result.matched_historical_cases
        ],
        evidence_notes=notes,
        missing_evidence_reasons=[],
        retrieval_quality=0.0,
        attempt_count=query.attempt + 1,
    )
