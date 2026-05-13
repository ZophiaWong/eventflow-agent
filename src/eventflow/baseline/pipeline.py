"""Single-signal orchestration for the M2 rule-based baseline."""

from __future__ import annotations

from pathlib import Path

from eventflow.baseline.types import BaselineError, BaselineEvalMetrics, BaselineResult
from eventflow.datasets import (
    load_dependency_map,
    load_eval_cases,
    load_playbooks,
    load_raw_signals,
)
from eventflow.nodes.assess_risk_rule_based import assess_risk_rule_based
from eventflow.nodes.classify_rule_based import classify_rule_based
from eventflow.nodes.generate_brief import generate_brief
from eventflow.nodes.normalize import normalize_signal
from eventflow.nodes.retrieve_playbook_rule_based import retrieve_playbook_rule_based
from eventflow.schemas import (
    DependencyMap,
    EvalCase,
    ExpectedRoute,
    Playbook,
    RawSignal,
    RecommendedAction,
)


def run_baseline_for_signal(
    raw_signal: RawSignal,
    dependency_map: DependencyMap,
    playbooks: list[Playbook],
) -> BaselineResult:
    """Run one RawSignal through the deterministic baseline."""

    errors: list[BaselineError] = []
    signal = normalize_signal(raw_signal)

    candidate, classification_errors = classify_rule_based(signal, dependency_map)
    errors.extend(classification_errors)
    if candidate is None:
        return BaselineResult(
            signal_id=signal.signal_id,
            route=ExpectedRoute.REQUEST_MORE_EVIDENCE,
            errors=errors,
        )

    evidence_pack, matched_playbook, retrieval_errors = retrieve_playbook_rule_based(
        signal=signal,
        candidate=candidate,
        dependency_map=dependency_map,
        playbooks=playbooks,
    )
    errors.extend(retrieval_errors)
    if matched_playbook is None or errors:
        return BaselineResult(
            signal_id=signal.signal_id,
            candidate=candidate,
            evidence_pack=evidence_pack,
            route=ExpectedRoute.REQUEST_MORE_EVIDENCE,
            errors=errors,
        )

    risk_assessment = assess_risk_rule_based(
        candidate=candidate,
        evidence_pack=evidence_pack,
        playbook=matched_playbook,
    )
    brief = generate_brief(
        signal=signal,
        candidate=candidate,
        evidence_pack=evidence_pack,
        risk_assessment=risk_assessment,
    )
    route = (
        ExpectedRoute.HUMAN_REVIEW
        if risk_assessment.requires_human_review
        else ExpectedRoute.AUTO_BRIEF
    )

    return BaselineResult(
        signal_id=signal.signal_id,
        candidate=candidate,
        evidence_pack=evidence_pack,
        risk_assessment=risk_assessment,
        brief=brief,
        route=route,
    )


def load_baseline_inputs(
    data_dir: Path | str,
) -> tuple[list[RawSignal], DependencyMap, list[Playbook]]:
    """Load the sample raw signals, dependency map, and playbooks."""

    root = Path(data_dir)
    return (
        load_raw_signals(root / "samples" / "raw_signals.jsonl"),
        load_dependency_map(root / "samples" / "dependency_map.json"),
        load_playbooks(root / "samples" / "playbooks.jsonl"),
    )


def run_baseline_for_signal_id(data_dir: Path | str, signal_id: str) -> BaselineResult:
    """Load sample data and run the baseline for one signal ID."""

    raw_signals, dependency_map, playbooks = load_baseline_inputs(data_dir)
    signal_by_id = {signal.signal_id: signal for signal in raw_signals}
    signal = signal_by_id.get(signal_id)
    if signal is None:
        return BaselineResult(
            signal_id=signal_id,
            route=ExpectedRoute.ERROR,
            errors=[
                BaselineError(
                    stage="load",
                    error_code="signal_not_found",
                    message=f"No raw signal found for signal_id={signal_id}",
                    signal_id=signal_id,
                )
            ],
        )
    return run_baseline_for_signal(signal, dependency_map, playbooks)


def run_baseline_for_all(data_dir: Path | str) -> list[BaselineResult]:
    """Run the baseline for every sample raw signal."""

    raw_signals, dependency_map, playbooks = load_baseline_inputs(data_dir)
    return [
        run_baseline_for_signal(signal, dependency_map, playbooks)
        for signal in raw_signals
    ]


def evaluate_baseline(data_dir: Path | str) -> BaselineEvalMetrics:
    """Compare baseline output to draft eval labels and return smoke metrics."""

    root = Path(data_dir)
    eval_cases = load_eval_cases(root / "eval" / "eval_cases.jsonl")
    results = {result.signal_id: result for result in run_baseline_for_all(root)}

    completed = 0
    event_type_matches = 0
    dependency_matches = 0
    risk_matches = 0
    route_matches = 0
    action_matches = 0

    for eval_case in eval_cases:
        result = results[eval_case.input_signal_id]
        if result.brief is not None:
            completed += 1
        if _event_type_matches(result, eval_case):
            event_type_matches += 1
        if _dependencies_match(result, eval_case):
            dependency_matches += 1
        if _risk_level_matches(result, eval_case):
            risk_matches += 1
        if result.route == eval_case.expected_route:
            route_matches += 1
        if _recommended_action_matches(result, eval_case):
            action_matches += 1

    total = len(eval_cases)
    return BaselineEvalMetrics(
        total_cases=total,
        completed_cases=completed,
        event_type_match_rate=event_type_matches / total,
        dependency_exact_match_rate=dependency_matches / total,
        risk_level_match_rate=risk_matches / total,
        route_match_rate=route_matches / total,
        recommended_action_match_rate=action_matches / total,
    )


def _event_type_matches(result: BaselineResult, eval_case: EvalCase) -> bool:
    if result.candidate is not None:
        return result.candidate.event_type == eval_case.expected_event_type
    return False


def _dependencies_match(result: BaselineResult, eval_case: EvalCase) -> bool:
    if result.candidate is not None:
        return (
            set(result.candidate.affected_dependencies)
            == set(eval_case.expected_affected_dependencies)
        )
    return False


def _risk_level_matches(result: BaselineResult, eval_case: EvalCase) -> bool:
    if result.risk_assessment is not None:
        return result.risk_assessment.risk_level == eval_case.expected_risk_level
    return False


def _recommended_action_matches(result: BaselineResult, eval_case: EvalCase) -> bool:
    if result.risk_assessment is not None:
        return (
            result.risk_assessment.recommended_action
            == eval_case.expected_recommended_action
        )
    return eval_case.expected_recommended_action == RecommendedAction.REQUEST_MORE_EVIDENCE
