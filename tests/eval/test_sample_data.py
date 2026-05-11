from collections import Counter
from pathlib import Path

from eventflow.datasets import (
    load_dependency_map,
    load_eval_cases,
    load_historical_cases,
    load_playbooks,
    load_raw_signals,
)
from eventflow.schemas import (
    EventType,
    ExpectedRoute,
    LabelStatus,
    RecommendedAction,
    RiskLevel,
)

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"


def test_sample_data_files_validate_against_schemas() -> None:
    raw_signals = load_raw_signals(DATA_DIR / "samples" / "raw_signals.jsonl")
    dependency_map = load_dependency_map(DATA_DIR / "samples" / "dependency_map.json")
    playbooks = load_playbooks(DATA_DIR / "samples" / "playbooks.jsonl")
    historical_cases = load_historical_cases(
        DATA_DIR / "samples" / "historical_cases.jsonl"
    )
    eval_cases = load_eval_cases(DATA_DIR / "eval" / "eval_cases.jsonl")

    assert len(raw_signals) == 24
    assert dependency_map.product_name == "EventFlow Demo SaaS"
    assert len(playbooks) == 16
    assert len(historical_cases) == 8
    assert len(eval_cases) == 24


def test_raw_signal_dataset_distribution_is_m1_balanced() -> None:
    eval_cases = load_eval_cases(DATA_DIR / "eval" / "eval_cases.jsonl")
    event_type_counts = Counter(case.expected_event_type for case in eval_cases)
    risk_counts = Counter(case.expected_risk_level for case in eval_cases)

    assert event_type_counts["service_incident"] == 7
    assert event_type_counts["security_advisory"] == 6
    assert event_type_counts["api_change"] == 6
    assert event_type_counts["product_release"] == 5

    assert risk_counts[RiskLevel.LOW] == 6
    assert risk_counts[RiskLevel.MEDIUM] == 7
    assert risk_counts[RiskLevel.HIGH] == 8
    assert risk_counts[RiskLevel.CRITICAL] == 3


def test_sample_records_are_synthetic_and_eval_cases_reference_raw_signals() -> None:
    raw_signals = load_raw_signals(DATA_DIR / "samples" / "raw_signals.jsonl")
    historical_cases = load_historical_cases(
        DATA_DIR / "samples" / "historical_cases.jsonl"
    )
    eval_cases = load_eval_cases(DATA_DIR / "eval" / "eval_cases.jsonl")

    signal_ids = {signal.signal_id for signal in raw_signals}

    assert all(signal.is_synthetic for signal in raw_signals)
    assert all(case.is_synthetic for case in historical_cases)
    assert {case.input_signal_id for case in eval_cases} == signal_ids


def test_dependency_references_are_known() -> None:
    dependency_map = load_dependency_map(DATA_DIR / "samples" / "dependency_map.json")
    eval_cases = load_eval_cases(DATA_DIR / "eval" / "eval_cases.jsonl")
    historical_cases = load_historical_cases(
        DATA_DIR / "samples" / "historical_cases.jsonl"
    )

    dependency_ids = {
        dependency.dependency_id
        for module in dependency_map.modules
        for dependency in module.dependencies
    }

    for case in eval_cases:
        assert set(case.expected_affected_dependencies) <= dependency_ids

    for case in historical_cases:
        assert set(case.affected_dependencies) <= dependency_ids


def test_playbooks_cover_m1_event_types_and_criticalities() -> None:
    playbooks = load_playbooks(DATA_DIR / "samples" / "playbooks.jsonl")

    coverage = {
        (playbook.event_type, playbook.dependency_criticality) for playbook in playbooks
    }

    expected_coverage = {
        (event_type, risk_level)
        for event_type in {
            EventType.SERVICE_INCIDENT,
            EventType.SECURITY_ADVISORY,
            EventType.API_CHANGE,
            EventType.PRODUCT_RELEASE,
        }
        for risk_level in {
            RiskLevel.LOW,
            RiskLevel.MEDIUM,
            RiskLevel.HIGH,
            RiskLevel.CRITICAL,
        }
    }

    assert coverage == expected_coverage
    assert all(
        playbook.recommended_action in set(RecommendedAction) for playbook in playbooks
    )


def test_high_risk_eval_labels_have_review_route_and_rationale() -> None:
    eval_cases = load_eval_cases(DATA_DIR / "eval" / "eval_cases.jsonl")

    for case in eval_cases:
        if case.expected_risk_level in {RiskLevel.HIGH, RiskLevel.CRITICAL}:
            assert case.expected_route == ExpectedRoute.HUMAN_REVIEW
            assert case.label_rationale


def test_eval_labels_are_draft_until_manually_reviewed() -> None:
    eval_cases = load_eval_cases(DATA_DIR / "eval" / "eval_cases.jsonl")

    assert {case.label_status for case in eval_cases} == {LabelStatus.DRAFT}
