"""M4 evidence quality evaluation node logic."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from eventflow.retrieval import evaluate_evidence_pack
from eventflow.retrieval.types import EvidenceEvaluation, RetrievalScores
from eventflow.schemas import EvidencePack


class EvidenceEvaluationOutput(BaseModel):
    """Output of rule-based evidence quality evaluation."""

    model_config = ConfigDict(extra="forbid")

    evidence_pack: EvidencePack
    evidence_evaluation: EvidenceEvaluation


def evaluate_evidence(
    evidence_pack: EvidencePack,
    retrieval_scores: RetrievalScores,
) -> EvidenceEvaluationOutput:
    """Evaluate whether an EvidencePack is sufficient for risk assessment."""

    updated_pack, evidence_evaluation = evaluate_evidence_pack(
        evidence_pack=evidence_pack,
        scores=retrieval_scores,
    )
    return EvidenceEvaluationOutput(
        evidence_pack=updated_pack,
        evidence_evaluation=evidence_evaluation,
    )
