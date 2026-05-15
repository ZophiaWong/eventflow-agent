from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from eventflow.schemas import (
    EventCluster,
    EvidencePack,
    HumanReviewDecision,
    RawSignal,
    RetrievalQuery,
    ReviewStatus,
)


def test_raw_signal_rejects_empty_required_fields() -> None:
    with pytest.raises(ValidationError):
        RawSignal.model_validate(
            {
                "signal_id": "",
                "source_type": "status_page",
                "vendor": "GitHub Actions",
                "title": "Synthetic status update",
                "content": "Synthetic content.",
                "is_synthetic": True,
            }
        )


def test_raw_signal_rejects_unknown_enum_value() -> None:
    with pytest.raises(ValidationError):
        RawSignal.model_validate(
            {
                "signal_id": "sig_test",
                "source_type": "forum_post",
                "vendor": "GitHub Actions",
                "title": "Synthetic status update",
                "content": "Synthetic content.",
                "is_synthetic": True,
            }
        )


def test_raw_signal_rejects_non_example_url_for_synthetic_data() -> None:
    with pytest.raises(ValidationError):
        RawSignal.model_validate(
            {
                "signal_id": "sig_test",
                "source_type": "status_page",
                "vendor": "GitHub Actions",
                "title": "Synthetic status update",
                "content": "Synthetic content.",
                "source_url": "https://status.example-vendor.test/incidents/real-looking",
                "is_synthetic": True,
            }
        )


def test_raw_signal_rejects_real_cve_pattern_for_synthetic_data() -> None:
    with pytest.raises(ValidationError):
        RawSignal.model_validate(
            {
                "signal_id": "sig_test",
                "source_type": "security_advisory",
                "vendor": "Pydantic",
                "title": "Synthetic advisory CVE-2026-12345",
                "content": "Synthetic content.",
                "source_url": "https://example.com/simulated/advisory",
                "is_synthetic": True,
            }
        )


def test_event_candidate_rejects_confidence_out_of_range() -> None:
    from eventflow.schemas import EventCandidate

    with pytest.raises(ValidationError):
        EventCandidate.model_validate(
            {
                "candidate_id": "cand_test",
                "source_signal_id": "sig_test",
                "event_type": "service_incident",
                "vendor": "GitHub Actions",
                "affected_dependencies": ["dep_github_actions"],
                "summary": "Synthetic candidate.",
                "confidence": 1.2,
            }
        )


def test_event_cluster_rejects_reversed_seen_window() -> None:
    with pytest.raises(ValidationError):
        EventCluster.model_validate(
            {
                "cluster_id": "cluster_test",
                "candidate_ids": ["cand_test"],
                "canonical_title": "Synthetic cluster",
                "canonical_summary": "Synthetic summary.",
                "event_type": "service_incident",
                "vendor": "GitHub Actions",
                "affected_dependencies": ["dep_github_actions"],
                "first_seen_at": datetime(2026, 4, 2, tzinfo=timezone.utc),
                "last_seen_at": datetime(2026, 4, 1, tzinfo=timezone.utc),
                "confidence": 0.8,
            }
        )


def test_edited_human_review_requires_edited_field() -> None:
    with pytest.raises(ValidationError):
        HumanReviewDecision.model_validate(
            {
                "review_id": "review_test",
                "reviewer_id": "reviewer_001",
                "decision": ReviewStatus.EDITED,
            }
        )


def test_requested_more_evidence_review_requires_comments() -> None:
    with pytest.raises(ValidationError):
        HumanReviewDecision.model_validate(
            {
                "review_id": "review_test",
                "reviewer_id": "reviewer_001",
                "decision": "requested_more_evidence",
            }
        )


def test_retrieval_query_requires_non_empty_summary() -> None:
    with pytest.raises(ValidationError):
        RetrievalQuery.model_validate(
            {
                "query_id": "rq_test",
                "event_type": "service_incident",
                "vendor": "GitHub Actions",
                "summary": "",
            }
        )


def test_evidence_pack_supports_m4_retrieval_metadata() -> None:
    query = RetrievalQuery(
        query_id="rq_test",
        event_type="service_incident",
        vendor="GitHub Actions",
        affected_dependencies=["dep_github_actions"],
        keywords=["workflow", "jobs"],
        summary="Workflow job starts are delayed.",
    )

    evidence_pack = EvidencePack(
        evidence_id="evidence_test",
        query=query,
        source_signal_ids=["sig_test"],
        missing_evidence_reasons=["No similar historical case found."],
        retrieval_quality=0.8,
        attempt_count=1,
    )

    assert evidence_pack.query == query
    assert evidence_pack.missing_evidence_reasons == [
        "No similar historical case found."
    ]
    assert evidence_pack.attempt_count == 1
