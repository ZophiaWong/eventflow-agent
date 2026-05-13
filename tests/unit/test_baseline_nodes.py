from pathlib import Path

from eventflow.datasets import load_dependency_map, load_playbooks, load_raw_signals
from eventflow.nodes.assess_risk_rule_based import assess_risk_rule_based
from eventflow.nodes.classify_rule_based import classify_rule_based
from eventflow.nodes.generate_brief import generate_brief
from eventflow.nodes.normalize import normalize_signal
from eventflow.nodes.retrieve_playbook_rule_based import retrieve_playbook_rule_based
from eventflow.schemas import (
    EventType,
    ExpectedRoute,
    RawSignal,
    RecommendedAction,
    ReviewStatus,
    RiskLevel,
)

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"


def _sample_signal(signal_id: str) -> RawSignal:
    signals = load_raw_signals(DATA_DIR / "samples" / "raw_signals.jsonl")
    return next(signal for signal in signals if signal.signal_id == signal_id)


def test_normalize_preserves_valid_raw_signal() -> None:
    signal = _sample_signal("sig_001")

    assert normalize_signal(signal) == signal


def test_classification_covers_supported_event_types() -> None:
    dependency_map = load_dependency_map(DATA_DIR / "samples" / "dependency_map.json")

    expected_types = {
        "sig_001": EventType.SERVICE_INCIDENT,
        "sig_008": EventType.SECURITY_ADVISORY,
        "sig_014": EventType.API_CHANGE,
        "sig_020": EventType.PRODUCT_RELEASE,
    }

    for signal_id, expected_type in expected_types.items():
        candidate, errors = classify_rule_based(_sample_signal(signal_id), dependency_map)
        assert errors == []
        assert candidate is not None
        assert candidate.event_type == expected_type


def test_classification_matches_dependency_ids() -> None:
    dependency_map = load_dependency_map(DATA_DIR / "samples" / "dependency_map.json")

    candidate, errors = classify_rule_based(_sample_signal("sig_003"), dependency_map)

    assert errors == []
    assert candidate is not None
    assert candidate.affected_dependencies == ["dep_stripe_api"]


def test_classification_returns_structured_error_for_unknown_event_type() -> None:
    dependency_map = load_dependency_map(DATA_DIR / "samples" / "dependency_map.json")
    signal = RawSignal(
        signal_id="sig_unknown",
        source_type="manual",
        vendor="Stripe API",
        title="Synthetic provider note",
        content="Synthetic content with no supported M2 classification keywords.",
        source_url="https://example.com/simulated/unknown-note",
        is_synthetic=True,
    )

    candidate, errors = classify_rule_based(signal, dependency_map)

    assert candidate is None
    assert errors[0].stage == "classify"
    assert errors[0].error_code == "unclassified_event_type"


def test_playbook_retrieval_matches_event_type_and_dependency_criticality() -> None:
    dependency_map = load_dependency_map(DATA_DIR / "samples" / "dependency_map.json")
    playbooks = load_playbooks(DATA_DIR / "samples" / "playbooks.jsonl")
    signal = _sample_signal("sig_014")
    candidate, _ = classify_rule_based(signal, dependency_map)
    assert candidate is not None

    evidence_pack, playbook, errors = retrieve_playbook_rule_based(
        signal=signal,
        candidate=candidate,
        dependency_map=dependency_map,
        playbooks=playbooks,
    )

    assert errors == []
    assert playbook is not None
    assert playbook.playbook_id == "pb_api_change_critical"
    assert evidence_pack.matched_dependencies == ["dep_stripe_api"]
    assert evidence_pack.matched_playbooks == ["pb_api_change_critical"]


def test_playbook_retrieval_returns_error_for_missing_dependency() -> None:
    dependency_map = load_dependency_map(DATA_DIR / "samples" / "dependency_map.json")
    playbooks = load_playbooks(DATA_DIR / "samples" / "playbooks.jsonl")
    signal = RawSignal(
        signal_id="sig_unknown_vendor",
        source_type="release_note",
        vendor="Unknown Vendor",
        title="Synthetic product release announcement",
        content="Synthetic release announcement for an untracked dependency.",
        source_url="https://example.com/simulated/unknown-release",
        is_synthetic=True,
    )
    candidate, _ = classify_rule_based(signal, dependency_map)
    assert candidate is not None

    evidence_pack, playbook, errors = retrieve_playbook_rule_based(
        signal=signal,
        candidate=candidate,
        dependency_map=dependency_map,
        playbooks=playbooks,
    )

    assert playbook is None
    assert evidence_pack.retrieval_quality == 0.4
    assert errors[0].error_code == "dependency_not_matched"


def test_risk_assessment_uses_playbook_and_review_rules() -> None:
    dependency_map = load_dependency_map(DATA_DIR / "samples" / "dependency_map.json")
    playbooks = load_playbooks(DATA_DIR / "samples" / "playbooks.jsonl")
    signal = _sample_signal("sig_003")
    candidate, _ = classify_rule_based(signal, dependency_map)
    assert candidate is not None
    evidence_pack, playbook, _ = retrieve_playbook_rule_based(
        signal=signal,
        candidate=candidate,
        dependency_map=dependency_map,
        playbooks=playbooks,
    )
    assert playbook is not None

    risk_assessment = assess_risk_rule_based(candidate, evidence_pack, playbook)

    assert risk_assessment.risk_level == RiskLevel.CRITICAL
    assert risk_assessment.recommended_action == RecommendedAction.ESCALATE_TO_ENGINEERING
    assert risk_assessment.requires_human_review is True


def test_generate_brief_creates_valid_review_pending_brief() -> None:
    dependency_map = load_dependency_map(DATA_DIR / "samples" / "dependency_map.json")
    playbooks = load_playbooks(DATA_DIR / "samples" / "playbooks.jsonl")
    signal = _sample_signal("sig_003")
    candidate, _ = classify_rule_based(signal, dependency_map)
    assert candidate is not None
    evidence_pack, playbook, _ = retrieve_playbook_rule_based(
        signal=signal,
        candidate=candidate,
        dependency_map=dependency_map,
        playbooks=playbooks,
    )
    assert playbook is not None
    risk_assessment = assess_risk_rule_based(candidate, evidence_pack, playbook)

    brief = generate_brief(signal, candidate, evidence_pack, risk_assessment)

    assert brief.brief_id == "brief_sig_003"
    assert brief.review_status == ReviewStatus.PENDING
    assert "sig_003" in brief.evidence_refs
    assert "dep_stripe_api" in brief.evidence_refs


def test_low_risk_brief_does_not_require_review() -> None:
    dependency_map = load_dependency_map(DATA_DIR / "samples" / "dependency_map.json")
    playbooks = load_playbooks(DATA_DIR / "samples" / "playbooks.jsonl")
    signal = _sample_signal("sig_024")
    candidate, _ = classify_rule_based(signal, dependency_map)
    assert candidate is not None
    evidence_pack, playbook, _ = retrieve_playbook_rule_based(
        signal=signal,
        candidate=candidate,
        dependency_map=dependency_map,
        playbooks=playbooks,
    )
    assert playbook is not None
    risk_assessment = assess_risk_rule_based(candidate, evidence_pack, playbook)
    brief = generate_brief(signal, candidate, evidence_pack, risk_assessment)

    assert risk_assessment.risk_level == RiskLevel.LOW
    assert brief.review_status == ReviewStatus.NOT_REQUIRED


def test_expected_route_import_is_available_for_m2_tests() -> None:
    assert ExpectedRoute.REQUEST_MORE_EVIDENCE.value == "request_more_evidence"
