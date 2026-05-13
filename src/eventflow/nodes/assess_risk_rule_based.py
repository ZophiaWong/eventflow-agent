"""Rule-based risk assessment node."""

from eventflow.schemas import (
    EventCandidate,
    EvidencePack,
    Playbook,
    RiskAssessment,
    RiskLevel,
)


def assess_risk_rule_based(
    candidate: EventCandidate,
    evidence_pack: EvidencePack,
    playbook: Playbook,
) -> RiskAssessment:
    """Assess risk from the candidate and retrieved playbook evidence."""

    confidence = round(min(candidate.confidence, evidence_pack.retrieval_quality), 2)
    requires_review = (
        playbook.review_required
        or playbook.risk_level in {RiskLevel.HIGH, RiskLevel.CRITICAL}
        or confidence < 0.60
    )
    uncertainty_factors: list[str] = []
    if confidence < 0.60:
        uncertainty_factors.append("Baseline confidence is below review threshold.")

    return RiskAssessment(
        risk_level=playbook.risk_level,
        confidence=confidence,
        risk_factors=[
            f"Event classified as {candidate.event_type.value}.",
            f"Matched playbook {playbook.playbook_id}.",
            f"Matched dependencies: {', '.join(evidence_pack.matched_dependencies)}.",
        ],
        uncertainty_factors=uncertainty_factors,
        recommended_action=playbook.recommended_action,
        requires_human_review=requires_review,
        rationale=(
            f"{playbook.guidance} Baseline confidence is {confidence:.2f} based on "
            "classification and evidence retrieval quality."
        ),
    )
