from pathlib import Path

from eventflow.baseline import (
    run_baseline_for_signal,
    run_baseline_for_signal_id,
)
from eventflow.datasets import load_dependency_map, load_playbooks
from eventflow.schemas import ExpectedRoute, RawSignal, ReviewStatus

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"


def test_baseline_processes_one_sample_signal_end_to_end() -> None:
    result = run_baseline_for_signal_id(DATA_DIR, "sig_001")

    assert result.errors == []
    assert result.candidate is not None
    assert result.evidence_pack is not None
    assert result.risk_assessment is not None
    assert result.brief is not None
    assert result.brief.brief_id == "brief_sig_001"
    assert result.brief.review_status == ReviewStatus.PENDING
    assert result.route == ExpectedRoute.HUMAN_REVIEW


def test_baseline_returns_structured_error_for_missing_signal_id() -> None:
    result = run_baseline_for_signal_id(DATA_DIR, "sig_missing")

    assert result.brief is None
    assert result.route == ExpectedRoute.ERROR
    assert result.errors[0].stage == "load"
    assert result.errors[0].error_code == "signal_not_found"


def test_baseline_returns_request_more_evidence_for_unknown_dependency() -> None:
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

    result = run_baseline_for_signal(signal, dependency_map, playbooks)

    assert result.brief is None
    assert result.route == ExpectedRoute.REQUEST_MORE_EVIDENCE
    assert result.errors[0].error_code == "dependency_not_matched"


def test_baseline_covers_multiple_event_types_end_to_end() -> None:
    expected_signal_ids = ["sig_001", "sig_008", "sig_014", "sig_020"]

    results = [
        run_baseline_for_signal_id(DATA_DIR, signal_id)
        for signal_id in expected_signal_ids
    ]

    assert all(result.brief is not None for result in results)
    assert {result.brief.event_type for result in results if result.brief} == {
        "service_incident",
        "security_advisory",
        "api_change",
        "product_release",
    }
