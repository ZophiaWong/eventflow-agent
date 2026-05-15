"""Rule-based evidence quality evaluation for M4 retrieval."""

from __future__ import annotations

from eventflow.retrieval.types import EvidenceEvaluation, RetrievalScores
from eventflow.schemas import EvidencePack, RawSignal

SUFFICIENT_RETRIEVAL_QUALITY = 0.70
WEAK_RETRIEVAL_QUALITY = 0.45


def evaluate_evidence_pack(
    evidence_pack: EvidencePack,
    scores: RetrievalScores,
) -> tuple[EvidencePack, EvidenceEvaluation]:
    """Evaluate retrieval quality and return an updated EvidencePack."""

    retrieval_quality = round(
        scores.dependency_match_score * 0.4
        + scores.playbook_match_score * 0.3
        + scores.historical_case_score * 0.2
        + scores.source_support_score * 0.1,
        2,
    )
    missing_reasons = _missing_reasons(evidence_pack, scores)
    if scores.dependency_match_score == 0:
        sufficiency = "insufficient"
        if "No dependency-map match found." not in missing_reasons:
            missing_reasons.append("No dependency-map match found.")
    elif retrieval_quality >= SUFFICIENT_RETRIEVAL_QUALITY:
        sufficiency = "sufficient"
    elif retrieval_quality >= WEAK_RETRIEVAL_QUALITY:
        sufficiency = "weak"
    else:
        sufficiency = "insufficient"

    updated_pack = evidence_pack.model_copy(
        update={
            "retrieval_quality": retrieval_quality,
            "missing_evidence_reasons": missing_reasons,
        }
    )
    return updated_pack, EvidenceEvaluation(
        retrieval_quality=retrieval_quality,
        evidence_sufficiency=sufficiency,
        missing_evidence_reasons=missing_reasons,
    )


def build_retrieval_scores(
    dependency_match_score: float,
    playbook_match_score: float,
    historical_case_score: float,
    source_support_score: float,
) -> RetrievalScores:
    """Create component scores for evidence quality calculation."""

    return RetrievalScores(
        dependency_match_score=dependency_match_score,
        playbook_match_score=playbook_match_score,
        historical_case_score=historical_case_score,
        source_support_score=source_support_score,
    )


def score_source_support(signal: RawSignal) -> float:
    """Score how much source content supports retrieval."""

    has_title = bool(signal.title.strip())
    has_content = bool(signal.content.strip())
    has_source_type = signal.source_type is not None
    if has_title and has_content and has_source_type and signal.is_synthetic:
        return 1.0
    if has_title and has_content:
        return 0.7
    if has_title:
        return 0.5
    return 0.0


def _missing_reasons(
    evidence_pack: EvidencePack,
    scores: RetrievalScores,
) -> list[str]:
    reasons: list[str] = []
    if scores.dependency_match_score == 0:
        reasons.append("No dependency-map match found.")
    if not evidence_pack.matched_playbooks:
        reasons.append("No matching playbook found.")
    if scores.source_support_score < 0.7:
        reasons.append("Source signal content is incomplete.")
    if scores.historical_case_score == 0:
        reasons.append("No similar historical case found.")
    return reasons
