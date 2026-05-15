from pathlib import Path

from eventflow.datasets import load_dependency_map, load_playbooks
from eventflow.graph.nodes import (
    deduplicate_event_node,
    evaluate_evidence_node,
    make_retrieve_evidence_node,
)
from eventflow.schemas import EventCandidate, EventType, RawSignal, SourceType

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"


def test_deduplicate_event_node_creates_single_candidate_cluster() -> None:
    candidate = EventCandidate(
        candidate_id="cand_sig_test",
        source_signal_id="sig_test",
        event_type=EventType.PRODUCT_RELEASE,
        vendor="Vercel",
        affected_dependencies=["dep_vercel"],
        summary="Synthetic release note.",
        confidence=0.85,
        evidence_refs=["sig_test", "dep_vercel"],
    )

    update = deduplicate_event_node({"event_candidate": candidate})

    cluster = update["event_cluster"]
    assert cluster.cluster_id == "cluster_sig_test"
    assert cluster.candidate_ids == ["cand_sig_test"]
    assert cluster.affected_dependencies == ["dep_vercel"]
    assert update["audit_log"][0].node_name == "deduplicate_event"


def test_retrieve_evidence_node_treats_unknown_dependency_as_nonfatal() -> None:
    dependency_map = load_dependency_map(DATA_DIR / "samples" / "dependency_map.json")
    playbooks = load_playbooks(DATA_DIR / "samples" / "playbooks.jsonl")
    signal = RawSignal(
        signal_id="sig_unknown_vendor",
        source_type=SourceType.RELEASE_NOTE,
        vendor="Unknown Vendor",
        title="Synthetic product release announcement",
        content="Synthetic release announcement for an untracked dependency.",
        source_url="https://example.com/simulated/unknown-release",
        is_synthetic=True,
    )
    candidate = EventCandidate(
        candidate_id="cand_sig_unknown_vendor",
        source_signal_id=signal.signal_id,
        event_type=EventType.PRODUCT_RELEASE,
        vendor=signal.vendor,
        affected_dependencies=[],
        summary=signal.content,
        confidence=0.45,
        evidence_refs=[signal.signal_id],
    )
    cluster_update = deduplicate_event_node({"event_candidate": candidate})
    retrieve_evidence_node = make_retrieve_evidence_node(dependency_map, playbooks)

    update = retrieve_evidence_node(
        {
            "raw_signal": signal,
            "event_candidate": candidate,
            "event_cluster": cluster_update["event_cluster"],
        }
    )

    assert "errors" not in update
    assert update["retrieval_scores"].dependency_match_score == 0.0
    assert update["evidence_pack"].retrieval_quality == 0.0
    assert update["audit_log"][0].status == "success"

    evaluation_update = evaluate_evidence_node(update)

    assert evaluation_update["evidence_sufficiency"] == "insufficient"
    assert evaluation_update["evidence_pack"].retrieval_quality == 0.28
    assert evaluation_update["audit_log"][0].status == "warning"
