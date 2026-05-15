from pathlib import Path

from eventflow.datasets import load_dependency_map, load_playbooks, load_raw_signals
from eventflow.graph import build_eventflow_graph, run_graph_for_signal
from eventflow.schemas import ExpectedRoute, RawSignal, ReviewStatus, SourceType

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"


def _sample_signal(signal_id: str):
    signals = load_raw_signals(DATA_DIR / "samples" / "raw_signals.jsonl")
    return next(signal for signal in signals if signal.signal_id == signal_id)


def _graph_inputs():
    return (
        load_dependency_map(DATA_DIR / "samples" / "dependency_map.json"),
        load_playbooks(DATA_DIR / "samples" / "playbooks.jsonl"),
    )


def test_graph_routes_low_risk_event_to_auto_brief() -> None:
    dependency_map, playbooks = _graph_inputs()

    result = run_graph_for_signal(
        raw_signal=_sample_signal("sig_024"),
        dependency_map=dependency_map,
        playbooks=playbooks,
    )

    assert result["route_decision"] == ExpectedRoute.AUTO_BRIEF
    assert result["event_risk_brief"].review_status == ReviewStatus.NOT_REQUIRED
    assert result.get("errors", []) == []


def test_graph_routes_high_risk_event_to_review_placeholder() -> None:
    dependency_map, playbooks = _graph_inputs()

    result = run_graph_for_signal(
        raw_signal=_sample_signal("sig_003"),
        dependency_map=dependency_map,
        playbooks=playbooks,
    )

    assert result["route_decision"] == ExpectedRoute.HUMAN_REVIEW
    assert result["event_risk_brief"].review_status == ReviewStatus.PENDING
    assert "human_review_decision" not in result
    assert result.get("errors", []) == []


def test_graph_routes_unknown_vendor_to_request_more_evidence() -> None:
    dependency_map, playbooks = _graph_inputs()
    signal = RawSignal(
        signal_id="sig_unknown_vendor",
        source_type=SourceType.RELEASE_NOTE,
        vendor="Unknown Vendor",
        title="Synthetic product release announcement",
        content="Synthetic release announcement for an untracked dependency.",
        source_url="https://example.com/simulated/unknown-release",
        is_synthetic=True,
    )

    result = run_graph_for_signal(
        raw_signal=signal,
        dependency_map=dependency_map,
        playbooks=playbooks,
    )

    assert result["route_decision"] == ExpectedRoute.REQUEST_MORE_EVIDENCE
    assert "event_risk_brief" not in result
    assert result.get("errors", []) == []
    assert any(entry.status == "warning" for entry in result["audit_log"])


def test_graph_routes_missing_raw_signal_to_structured_error() -> None:
    dependency_map, playbooks = _graph_inputs()
    graph = build_eventflow_graph(dependency_map, playbooks)

    result = graph.invoke({"run_id": "run_missing_raw_signal"})

    assert result["route_decision"] == ExpectedRoute.ERROR
    assert "event_risk_brief" not in result
    assert result["errors"][0].error_code == "missing_raw_signal"


def test_graph_audit_log_records_expected_successful_path_nodes() -> None:
    dependency_map, playbooks = _graph_inputs()

    result = run_graph_for_signal(
        raw_signal=_sample_signal("sig_024"),
        dependency_map=dependency_map,
        playbooks=playbooks,
    )

    node_names = [entry.node_name for entry in result["audit_log"]]
    assert node_names == [
        "normalize_signal",
        "classify_event",
        "deduplicate_event",
        "retrieve_evidence",
        "assess_risk",
        "generate_event_risk_brief",
    ]
