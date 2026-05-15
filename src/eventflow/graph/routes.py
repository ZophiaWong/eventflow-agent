"""Conditional route functions for the M3 LangGraph workflow."""

from __future__ import annotations

from typing import Literal

from eventflow.graph.state import EventFlowState

AUTO_BRIEF = "auto_brief"
CONTINUE_TO_ASSESS = "continue_to_assess"
ERROR = "error"
HUMAN_REVIEW = "human_review"
REQUEST_MORE_EVIDENCE = "request_more_evidence"

MIN_RETRIEVAL_QUALITY = 0.70

EvidenceRoute = Literal["continue_to_assess", "request_more_evidence", "error"]
RiskRoute = Literal["auto_brief", "human_review", "error"]


def route_after_evidence(state: EventFlowState) -> EvidenceRoute:
    """Route after evidence retrieval."""

    if state.get("errors"):
        return ERROR

    evidence_pack = state.get("evidence_pack")
    if evidence_pack is None:
        return REQUEST_MORE_EVIDENCE

    evidence_sufficiency = state.get("evidence_sufficiency")
    if evidence_sufficiency is not None and evidence_sufficiency != "sufficient":
        return REQUEST_MORE_EVIDENCE

    if evidence_pack.retrieval_quality < MIN_RETRIEVAL_QUALITY:
        return REQUEST_MORE_EVIDENCE

    if state.get("matched_playbook") is None:
        return REQUEST_MORE_EVIDENCE

    return CONTINUE_TO_ASSESS


def route_after_risk(state: EventFlowState) -> RiskRoute:
    """Route after risk assessment."""

    if state.get("errors"):
        return ERROR

    risk_assessment = state.get("risk_assessment")
    if risk_assessment is None:
        return ERROR

    if risk_assessment.requires_human_review:
        return HUMAN_REVIEW

    return AUTO_BRIEF
