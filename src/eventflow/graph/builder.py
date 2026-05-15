"""Build and run the M3 LangGraph workflow."""

from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from eventflow.graph.nodes import (
    assess_risk_node,
    deduplicate_event_node,
    error_handler_node,
    evaluate_evidence_node,
    generate_event_risk_brief_node,
    human_review_placeholder_node,
    make_classify_event_node,
    make_retrieve_evidence_node,
    normalize_signal_node,
    request_more_evidence_placeholder_node,
)
from eventflow.graph.routes import (
    AUTO_BRIEF,
    CONTINUE_TO_ASSESS,
    ERROR,
    HUMAN_REVIEW,
    REQUEST_MORE_EVIDENCE,
    route_after_evidence,
    route_after_risk,
)
from eventflow.graph.state import EventFlowState
from eventflow.schemas import DependencyMap, HistoricalCase, Playbook, RawSignal


def build_eventflow_graph(
    dependency_map: DependencyMap,
    playbooks: list[Playbook],
    historical_cases: list[HistoricalCase] | None = None,
):
    """Compile the EventFlow StateGraph."""

    graph = StateGraph(EventFlowState)
    graph.add_node("normalize_signal", normalize_signal_node)
    graph.add_node("classify_event", make_classify_event_node(dependency_map))
    graph.add_node("deduplicate_event", deduplicate_event_node)
    graph.add_node(
        "retrieve_evidence",
        make_retrieve_evidence_node(dependency_map, playbooks, historical_cases),
    )
    graph.add_node("evaluate_evidence", evaluate_evidence_node)
    graph.add_node("assess_risk", assess_risk_node)
    graph.add_node("human_review_placeholder", human_review_placeholder_node)
    graph.add_node(
        "request_more_evidence_placeholder",
        request_more_evidence_placeholder_node,
    )
    graph.add_node("generate_event_risk_brief", generate_event_risk_brief_node)
    graph.add_node("error_handler", error_handler_node)

    graph.add_edge(START, "normalize_signal")
    graph.add_edge("normalize_signal", "classify_event")
    graph.add_edge("classify_event", "deduplicate_event")
    graph.add_edge("deduplicate_event", "retrieve_evidence")
    graph.add_edge("retrieve_evidence", "evaluate_evidence")
    graph.add_conditional_edges(
        "evaluate_evidence",
        route_after_evidence,
        {
            CONTINUE_TO_ASSESS: "assess_risk",
            REQUEST_MORE_EVIDENCE: "request_more_evidence_placeholder",
            ERROR: "error_handler",
        },
    )
    graph.add_conditional_edges(
        "assess_risk",
        route_after_risk,
        {
            AUTO_BRIEF: "generate_event_risk_brief",
            HUMAN_REVIEW: "human_review_placeholder",
            ERROR: "error_handler",
        },
    )
    graph.add_edge("human_review_placeholder", "generate_event_risk_brief")
    graph.add_edge("request_more_evidence_placeholder", END)
    graph.add_edge("generate_event_risk_brief", END)
    graph.add_edge("error_handler", END)

    return graph.compile()


def run_graph_for_signal(
    raw_signal: RawSignal,
    dependency_map: DependencyMap,
    playbooks: list[Playbook],
    historical_cases: list[HistoricalCase] | None = None,
    run_id: str | None = None,
) -> EventFlowState:
    """Run one RawSignal through the compiled graph."""

    graph = build_eventflow_graph(dependency_map, playbooks, historical_cases)
    initial_state: EventFlowState = {
        "run_id": run_id or f"run_{raw_signal.signal_id}",
        "raw_signal": raw_signal,
    }
    return graph.invoke(initial_state)
