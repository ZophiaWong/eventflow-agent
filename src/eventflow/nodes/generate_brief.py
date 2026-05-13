"""Event Risk Brief generation node."""

from eventflow.schemas import (
    EventCandidate,
    EventRiskBrief,
    EvidencePack,
    RawSignal,
    ReviewStatus,
    RiskAssessment,
)


def generate_brief(
    signal: RawSignal,
    candidate: EventCandidate,
    evidence_pack: EvidencePack,
    risk_assessment: RiskAssessment,
) -> EventRiskBrief:
    """Generate a structured EventRiskBrief from baseline artifacts."""

    review_status = (
        ReviewStatus.PENDING
        if risk_assessment.requires_human_review
        else ReviewStatus.NOT_REQUIRED
    )
    evidence_refs = [
        *evidence_pack.source_signal_ids,
        *evidence_pack.matched_dependencies,
        *evidence_pack.matched_playbooks,
        *evidence_pack.matched_historical_cases,
    ]
    return EventRiskBrief(
        brief_id=f"brief_{signal.signal_id}",
        title=f"{candidate.vendor}: {signal.title}",
        event_type=candidate.event_type,
        summary=candidate.summary,
        affected_dependencies=candidate.affected_dependencies,
        risk_level=risk_assessment.risk_level,
        confidence=risk_assessment.confidence,
        evidence_refs=evidence_refs,
        risk_rationale=risk_assessment.rationale,
        recommended_action=risk_assessment.recommended_action,
        review_status=review_status,
        created_at=None,
    )
