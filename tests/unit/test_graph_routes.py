from eventflow.graph.routes import (
    AUTO_BRIEF,
    CONTINUE_TO_ASSESS,
    ERROR,
    HUMAN_REVIEW,
    REQUEST_MORE_EVIDENCE,
    route_after_evidence,
    route_after_risk,
)
from eventflow.graph.state import workflow_error
from eventflow.schemas import (
    EvidencePack,
    RecommendedAction,
    RiskAssessment,
    RiskLevel,
)


def test_route_after_evidence_returns_error_for_fatal_errors() -> None:
    route = route_after_evidence(
        {
            "errors": [
                workflow_error(
                    node_name="classify_event",
                    error_code="classification_failed",
                    message="Classification failed.",
                )
            ]
        }
    )

    assert route == ERROR


def test_route_after_evidence_requests_more_evidence_for_weak_retrieval() -> None:
    route = route_after_evidence(
        {
            "evidence_pack": EvidencePack(
                evidence_id="evidence_test",
                source_signal_ids=["sig_test"],
                retrieval_quality=0.4,
            )
        }
    )

    assert route == REQUEST_MORE_EVIDENCE


def test_route_after_evidence_continues_when_evidence_and_playbook_exist() -> None:
    route = route_after_evidence(
        {
            "evidence_pack": EvidencePack(
                evidence_id="evidence_test",
                source_signal_ids=["sig_test"],
                matched_dependencies=["dep_test"],
                matched_playbooks=["pb_test"],
                retrieval_quality=1.0,
            ),
            "matched_playbook": object(),  # route only needs presence
        }
    )

    assert route == CONTINUE_TO_ASSESS


def test_route_after_risk_routes_human_review_when_required() -> None:
    route = route_after_risk(
        {
            "risk_assessment": RiskAssessment(
                risk_level=RiskLevel.HIGH,
                confidence=0.9,
                risk_factors=["High-risk dependency."],
                recommended_action=RecommendedAction.CREATE_INTERNAL_ISSUE,
                requires_human_review=True,
                rationale="High-risk dependency requires review.",
            )
        }
    )

    assert route == HUMAN_REVIEW


def test_route_after_risk_routes_auto_brief_when_review_not_required() -> None:
    route = route_after_risk(
        {
            "risk_assessment": RiskAssessment(
                risk_level=RiskLevel.LOW,
                confidence=0.9,
                risk_factors=["Low-risk informational update."],
                recommended_action=RecommendedAction.IGNORE,
                requires_human_review=False,
                rationale="Low-risk event can be auto briefed.",
            )
        }
    )

    assert route == AUTO_BRIEF
