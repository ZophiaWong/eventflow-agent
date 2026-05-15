from pathlib import Path

from eventflow.datasets import (
    load_dependency_map,
    load_historical_cases,
    load_playbooks,
)
from eventflow.retrieval import (
    build_evidence_pack,
    build_retrieval_query,
    build_retrieval_scores,
    evaluate_evidence_pack,
    retrieve_dependencies,
    retrieve_historical_cases,
    retrieve_playbooks,
)
from eventflow.schemas import EventCluster, EventType, RawSignal, SourceType

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"


def _cluster(
    vendor: str = "GitHub Actions",
    event_type: EventType = EventType.SERVICE_INCIDENT,
    dependencies: list[str] | None = None,
    summary: str = "Workflow job starts are delayed for hosted runners.",
) -> EventCluster:
    return EventCluster(
        cluster_id="cluster_sig_test",
        candidate_ids=["cand_sig_test"],
        canonical_title=f"{vendor}: {event_type.value}",
        canonical_summary=summary,
        event_type=event_type,
        vendor=vendor,
        affected_dependencies=(
            ["dep_github_actions"] if dependencies is None else dependencies
        ),
        confidence=0.9,
    )


def _signal(vendor: str = "GitHub Actions") -> RawSignal:
    return RawSignal(
        signal_id="sig_test",
        source_type=SourceType.STATUS_PAGE,
        vendor=vendor,
        title="Synthetic status update",
        content="Synthetic status content with enough retrieval support.",
        source_url="https://example.com/simulated/status",
        is_synthetic=True,
    )


def test_build_retrieval_query_from_event_cluster() -> None:
    query = build_retrieval_query(_cluster())

    assert query.query_id == "rq_cluster_sig_test_attempt_0"
    assert query.event_type == EventType.SERVICE_INCIDENT
    assert query.vendor == "GitHub Actions"
    assert "workflow" in query.keywords
    assert query.attempt == 0


def test_dependency_retriever_matches_exact_dependency() -> None:
    dependency_map = load_dependency_map(DATA_DIR / "samples" / "dependency_map.json")
    query = build_retrieval_query(_cluster())

    result = retrieve_dependencies(query, dependency_map)

    assert result.dependency_match_score == 1.0
    assert result.matched_dependencies[0].dependency_id == "dep_github_actions"


def test_dependency_retriever_returns_no_match_for_unknown_vendor() -> None:
    dependency_map = load_dependency_map(DATA_DIR / "samples" / "dependency_map.json")
    query = build_retrieval_query(
        _cluster(
            vendor="Unknown Vendor",
            event_type=EventType.PRODUCT_RELEASE,
            dependencies=[],
            summary="Synthetic release announcement for an untracked dependency.",
        )
    )

    result = retrieve_dependencies(query, dependency_map)

    assert result.dependency_match_score == 0.0
    assert result.matched_dependencies == []


def test_playbook_retriever_matches_event_type_and_criticality() -> None:
    dependency_map = load_dependency_map(DATA_DIR / "samples" / "dependency_map.json")
    playbooks = load_playbooks(DATA_DIR / "samples" / "playbooks.jsonl")
    query = build_retrieval_query(_cluster())
    dependency_result = retrieve_dependencies(query, dependency_map)

    result = retrieve_playbooks(
        query,
        dependency_result.matched_dependencies,
        playbooks,
    )

    assert result.playbook_match_score == 1.0
    assert result.selected_playbook is not None
    assert result.selected_playbook.playbook_id == "pb_service_incident_high"


def test_playbook_retriever_falls_back_to_event_type() -> None:
    playbooks = load_playbooks(DATA_DIR / "samples" / "playbooks.jsonl")
    query = build_retrieval_query(
        _cluster(
            vendor="Unknown Vendor",
            event_type=EventType.PRODUCT_RELEASE,
            dependencies=[],
        )
    )

    result = retrieve_playbooks(query, [], playbooks)

    assert result.playbook_match_score == 0.6
    assert result.selected_playbook is not None
    assert result.selected_playbook.event_type == EventType.PRODUCT_RELEASE


def test_historical_case_retriever_matches_vendor_event_and_dependency() -> None:
    historical_cases = load_historical_cases(
        DATA_DIR / "samples" / "historical_cases.jsonl"
    )
    query = build_retrieval_query(_cluster())

    result = retrieve_historical_cases(query, historical_cases)

    assert result.historical_case_score == 1.0
    assert result.matched_historical_cases[0].case_id == "hist_001"


def test_evidence_evaluator_marks_strong_evidence_sufficient() -> None:
    evidence_pack = _evidence_pack()
    scores = build_retrieval_scores(
        dependency_match_score=1.0,
        playbook_match_score=1.0,
        historical_case_score=1.0,
        source_support_score=1.0,
    )

    updated_pack, evaluation = evaluate_evidence_pack(evidence_pack, scores)

    assert updated_pack.retrieval_quality == 1.0
    assert evaluation.evidence_sufficiency == "sufficient"


def test_evidence_evaluator_marks_weak_evidence_weak() -> None:
    evidence_pack = _evidence_pack()
    scores = build_retrieval_scores(
        dependency_match_score=0.6,
        playbook_match_score=0.6,
        historical_case_score=0.0,
        source_support_score=1.0,
    )

    updated_pack, evaluation = evaluate_evidence_pack(evidence_pack, scores)

    assert updated_pack.retrieval_quality == 0.52
    assert evaluation.evidence_sufficiency == "weak"


def test_evidence_evaluator_hard_gates_missing_dependency() -> None:
    evidence_pack = _evidence_pack()
    scores = build_retrieval_scores(
        dependency_match_score=0.0,
        playbook_match_score=1.0,
        historical_case_score=1.0,
        source_support_score=1.0,
    )

    updated_pack, evaluation = evaluate_evidence_pack(evidence_pack, scores)

    assert updated_pack.retrieval_quality == 0.6
    assert evaluation.evidence_sufficiency == "insufficient"
    assert "No dependency-map match found." in evaluation.missing_evidence_reasons


def _evidence_pack():
    dependency_map = load_dependency_map(DATA_DIR / "samples" / "dependency_map.json")
    playbooks = load_playbooks(DATA_DIR / "samples" / "playbooks.jsonl")
    historical_cases = load_historical_cases(
        DATA_DIR / "samples" / "historical_cases.jsonl"
    )
    query = build_retrieval_query(_cluster())
    dependency_result = retrieve_dependencies(query, dependency_map)
    playbook_result = retrieve_playbooks(
        query,
        dependency_result.matched_dependencies,
        playbooks,
    )
    historical_result = retrieve_historical_cases(query, historical_cases)
    return build_evidence_pack(
        query=query,
        source_signal=_signal(),
        dependency_result=dependency_result,
        playbook_result=playbook_result,
        historical_case_result=historical_result,
    )
