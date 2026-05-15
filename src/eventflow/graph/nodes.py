"""LangGraph node wrappers around deterministic workflow logic."""

from __future__ import annotations

from eventflow.graph.state import EventFlowState, audit_entry, workflow_error
from eventflow.nodes.assess_risk_rule_based import assess_risk_rule_based
from eventflow.nodes.classify_rule_based import classify_rule_based
from eventflow.nodes.evaluate_evidence import evaluate_evidence
from eventflow.nodes.generate_brief import generate_brief
from eventflow.nodes.normalize import normalize_signal
from eventflow.nodes.retrieve_evidence import retrieve_evidence
from eventflow.schemas import (
    DependencyMap,
    EventCluster,
    ExpectedRoute,
    HistoricalCase,
    Playbook,
)


def normalize_signal_node(state: EventFlowState) -> EventFlowState:
    """Validate that the graph has a RawSignal and record normalization."""

    signal = state.get("raw_signal")
    if signal is None:
        return {
            "errors": [
                workflow_error(
                    node_name="normalize_signal",
                    error_code="missing_raw_signal",
                    message="Graph input did not include raw_signal.",
                )
            ],
            "audit_log": [
                audit_entry(
                    node_name="normalize_signal",
                    event="normalization_failed",
                    status="error",
                    message="Missing raw_signal.",
                    error_code="missing_raw_signal",
                )
            ],
        }

    normalized = normalize_signal(signal)
    return {
        "raw_signal": normalized,
        "audit_log": [
            audit_entry(
                node_name="normalize_signal",
                event="signal_normalized",
                status="success",
                message="Raw signal preserved as validated input.",
                input_refs=[signal.signal_id],
                output_refs=[normalized.signal_id],
            )
        ],
    }


def make_classify_event_node(dependency_map: DependencyMap):
    """Create a classify node bound to the dependency map."""

    def classify_event_node(state: EventFlowState) -> EventFlowState:
        signal = state.get("raw_signal")
        if signal is None:
            return _missing_state_update("classify_event", "raw_signal")

        candidate, errors = classify_rule_based(signal, dependency_map)
        if candidate is None:
            return {
                "errors": [
                    workflow_error(
                        node_name="classify_event",
                        error_code=error.error_code,
                        message=error.message,
                        input_refs=[signal.signal_id],
                    )
                    for error in errors
                ],
                "audit_log": [
                    audit_entry(
                        node_name="classify_event",
                        event="classification_failed",
                        status="error",
                        message="No supported event type matched.",
                        input_refs=[signal.signal_id],
                        error_code=errors[0].error_code if errors else None,
                    )
                ],
            }

        return {
            "event_candidate": candidate,
            "audit_log": [
                audit_entry(
                    node_name="classify_event",
                    event="event_classified",
                    status="success",
                    message=f"Classified event as {candidate.event_type.value}.",
                    input_refs=[signal.signal_id],
                    output_refs=[candidate.candidate_id],
                )
            ],
        }

    return classify_event_node


def deduplicate_event_node(state: EventFlowState) -> EventFlowState:
    """Create the M3 single-candidate event cluster."""

    candidate = state.get("event_candidate")
    if candidate is None:
        return _missing_state_update("deduplicate_event", "event_candidate")

    cluster = EventCluster(
        cluster_id=f"cluster_{candidate.source_signal_id}",
        candidate_ids=[candidate.candidate_id],
        canonical_title=f"{candidate.vendor}: {candidate.event_type.value}",
        canonical_summary=candidate.summary,
        event_type=candidate.event_type,
        vendor=candidate.vendor,
        affected_dependencies=candidate.affected_dependencies,
        confidence=candidate.confidence,
    )
    return {
        "event_cluster": cluster,
        "audit_log": [
            audit_entry(
                node_name="deduplicate_event",
                event="event_clustered",
                status="success",
                message="Created a single-candidate event cluster.",
                input_refs=[candidate.candidate_id],
                output_refs=[cluster.cluster_id],
            )
        ],
    }


def make_retrieve_evidence_node(
    dependency_map: DependencyMap,
    playbooks: list[Playbook],
    historical_cases: list[HistoricalCase] | None = None,
):
    """Create an evidence retrieval node bound to sample data."""

    def retrieve_evidence_node(state: EventFlowState) -> EventFlowState:
        signal = state.get("raw_signal")
        cluster = state.get("event_cluster")
        if signal is None:
            return _missing_state_update("retrieve_evidence", "raw_signal")
        if cluster is None:
            return _missing_state_update("retrieve_evidence", "event_cluster")

        try:
            output = retrieve_evidence(
                signal=signal,
                cluster=cluster,
                dependency_map=dependency_map,
                playbooks=playbooks,
                historical_cases=historical_cases or [],
            )
        except Exception as exc:  # pragma: no cover - defensive graph boundary
            return {
                "errors": [
                    workflow_error(
                        node_name="retrieve_evidence",
                        error_code="evidence_lookup_failed",
                        message=f"Evidence retrieval failed: {exc}",
                        input_refs=[cluster.cluster_id],
                    )
                ],
                "audit_log": [
                    audit_entry(
                        node_name="retrieve_evidence",
                        event="evidence_lookup_failed",
                        status="error",
                        message="Evidence retrieval failed.",
                        input_refs=[cluster.cluster_id],
                        error_code="evidence_lookup_failed",
                    )
                ],
            }

        update: EventFlowState = {
            "retrieval_query": output.retrieval_query,
            "evidence_pack": output.evidence_pack,
            "retrieval_scores": output.retrieval_scores,
            "audit_log": [
                audit_entry(
                    node_name="retrieve_evidence",
                    event="evidence_retrieved",
                    status="success",
                    message="Retrieved dependency, playbook, and historical evidence.",
                    input_refs=[cluster.cluster_id],
                    output_refs=[output.evidence_pack.evidence_id],
                )
            ],
        }
        if output.matched_playbook is not None:
            update["matched_playbook"] = output.matched_playbook
        return update

    return retrieve_evidence_node


def evaluate_evidence_node(state: EventFlowState) -> EventFlowState:
    """Evaluate evidence quality after retrieval."""

    evidence_pack = state.get("evidence_pack")
    retrieval_scores = state.get("retrieval_scores")
    if evidence_pack is None:
        return _missing_state_update("evaluate_evidence", "evidence_pack")
    if retrieval_scores is None:
        return _missing_state_update("evaluate_evidence", "retrieval_scores")

    output = evaluate_evidence(
        evidence_pack=evidence_pack,
        retrieval_scores=retrieval_scores,
    )
    evaluation = output.evidence_evaluation
    status = "success" if evaluation.evidence_sufficiency == "sufficient" else "warning"
    route_decision = (
        None
        if evaluation.evidence_sufficiency == "sufficient"
        else ExpectedRoute.REQUEST_MORE_EVIDENCE
    )
    return {
        "evidence_pack": output.evidence_pack,
        "evidence_evaluation": evaluation,
        "evidence_sufficiency": evaluation.evidence_sufficiency,
        "audit_log": [
            audit_entry(
                node_name="evaluate_evidence",
                event="evidence_evaluated",
                status=status,
                message=(
                    "Evidence is sufficient for risk assessment."
                    if evaluation.evidence_sufficiency == "sufficient"
                    else "Evidence is not sufficient for normal risk assessment."
                ),
                input_refs=[evidence_pack.evidence_id],
                output_refs=[output.evidence_pack.evidence_id],
                route_decision=route_decision,
            )
        ],
    }


def assess_risk_node(state: EventFlowState) -> EventFlowState:
    """Assess risk from graph state."""

    candidate = state.get("event_candidate")
    evidence_pack = state.get("evidence_pack")
    playbook = state.get("matched_playbook")
    if candidate is None:
        return _missing_state_update("assess_risk", "event_candidate")
    if evidence_pack is None:
        return _missing_state_update("assess_risk", "evidence_pack")
    if playbook is None:
        return _missing_state_update("assess_risk", "matched_playbook")

    risk_assessment = assess_risk_rule_based(
        candidate=candidate,
        evidence_pack=evidence_pack,
        playbook=playbook,
    )
    return {
        "risk_assessment": risk_assessment,
        "audit_log": [
            audit_entry(
                node_name="assess_risk",
                event="risk_assessed",
                status="success",
                message=f"Risk assessed as {risk_assessment.risk_level.value}.",
                input_refs=[candidate.candidate_id, evidence_pack.evidence_id],
            )
        ],
    }


def human_review_placeholder_node(state: EventFlowState) -> EventFlowState:
    """Record that human review is required without faking a review decision."""

    risk_assessment = state.get("risk_assessment")
    input_refs = []
    if risk_assessment is not None:
        input_refs.append(risk_assessment.risk_level.value)
    return {
        "route_decision": ExpectedRoute.HUMAN_REVIEW,
        "audit_log": [
            audit_entry(
                node_name="human_review_placeholder",
                event="human_review_required",
                status="success",
                message="Case requires human review; no reviewer decision created.",
                input_refs=input_refs,
                route_decision=ExpectedRoute.HUMAN_REVIEW,
            )
        ],
    }


def request_more_evidence_placeholder_node(state: EventFlowState) -> EventFlowState:
    """Record the insufficient-evidence terminal route."""

    evidence_pack = state.get("evidence_pack")
    return {
        "route_decision": ExpectedRoute.REQUEST_MORE_EVIDENCE,
        "audit_log": [
            audit_entry(
                node_name="request_more_evidence_placeholder",
                event="more_evidence_requested",
                status="warning",
                message="Evidence is insufficient for a normal risk brief.",
                output_refs=[evidence_pack.evidence_id] if evidence_pack else [],
                route_decision=ExpectedRoute.REQUEST_MORE_EVIDENCE,
            )
        ],
    }


def generate_event_risk_brief_node(state: EventFlowState) -> EventFlowState:
    """Generate the final Event Risk Brief for auto or review routes."""

    signal = state.get("raw_signal")
    candidate = state.get("event_candidate")
    evidence_pack = state.get("evidence_pack")
    risk_assessment = state.get("risk_assessment")
    if signal is None:
        return _missing_state_update("generate_event_risk_brief", "raw_signal")
    if candidate is None:
        return _missing_state_update("generate_event_risk_brief", "event_candidate")
    if evidence_pack is None:
        return _missing_state_update("generate_event_risk_brief", "evidence_pack")
    if risk_assessment is None:
        return _missing_state_update("generate_event_risk_brief", "risk_assessment")

    brief = generate_brief(
        signal=signal,
        candidate=candidate,
        evidence_pack=evidence_pack,
        risk_assessment=risk_assessment,
    )
    route_decision = (
        ExpectedRoute.HUMAN_REVIEW
        if risk_assessment.requires_human_review
        else ExpectedRoute.AUTO_BRIEF
    )
    return {
        "event_risk_brief": brief,
        "route_decision": route_decision,
        "audit_log": [
            audit_entry(
                node_name="generate_event_risk_brief",
                event="brief_generated",
                status="success",
                message="Generated Event Risk Brief.",
                input_refs=[candidate.candidate_id, evidence_pack.evidence_id],
                output_refs=[brief.brief_id],
                route_decision=route_decision,
            )
        ],
    }


def error_handler_node(state: EventFlowState) -> EventFlowState:
    """Record the terminal structured error route."""

    return {
        "route_decision": ExpectedRoute.ERROR,
        "audit_log": [
            audit_entry(
                node_name="error_handler",
                event="workflow_error",
                status="error",
                message="Workflow ended on the structured error route.",
                route_decision=ExpectedRoute.ERROR,
                error_code=(
                    state["errors"][0].error_code if state.get("errors") else None
                ),
            )
        ],
    }


def _missing_state_update(node_name: str, field_name: str) -> EventFlowState:
    error_code = "missing_required_state"
    return {
        "errors": [
            workflow_error(
                node_name=node_name,
                error_code=error_code,
                message=f"Required state field is missing: {field_name}.",
                input_refs=[field_name],
            )
        ],
        "audit_log": [
            audit_entry(
                node_name=node_name,
                event="precondition_failed",
                status="error",
                message=f"Required state field is missing: {field_name}.",
                input_refs=[field_name],
                error_code=error_code,
            )
        ],
    }
