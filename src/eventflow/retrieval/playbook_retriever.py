"""Deterministic playbook retrieval for M4 evidence retrieval."""

from __future__ import annotations

from eventflow.retrieval.types import PlaybookRetrievalResult
from eventflow.schemas import Dependency, Playbook, RetrievalQuery, RiskLevel

_RISK_RANK = {
    RiskLevel.LOW: 0,
    RiskLevel.MEDIUM: 1,
    RiskLevel.HIGH: 2,
    RiskLevel.CRITICAL: 3,
}


def retrieve_playbooks(
    query: RetrievalQuery,
    matched_dependencies: list[Dependency],
    playbooks: list[Playbook],
) -> PlaybookRetrievalResult:
    """Retrieve playbooks by event type and dependency criticality."""

    criticality = _highest_criticality(matched_dependencies)
    scored: list[tuple[float, Playbook, str]] = []

    for playbook in playbooks:
        event_matches = playbook.event_type == query.event_type
        criticality_matches = criticality is not None and (
            playbook.dependency_criticality == criticality
        )
        criticality_adjacent = criticality is not None and (
            abs(_RISK_RANK[playbook.dependency_criticality] - _RISK_RANK[criticality])
            == 1
        )

        if event_matches and criticality_matches:
            scored.append((1.0, playbook, "event type and criticality match"))
        elif event_matches and criticality_adjacent:
            scored.append((0.8, playbook, "event type and adjacent criticality match"))
        elif event_matches:
            scored.append((0.6, playbook, "event type fallback match"))
        elif criticality_matches:
            scored.append((0.4, playbook, "criticality-only match"))

    scored.sort(
        key=lambda item: (
            -item[0],
            abs(
                _RISK_RANK[item[1].dependency_criticality] - _RISK_RANK[criticality]
                if criticality is not None
                else 0
            ),
            item[1].playbook_id,
        )
    )
    matched_playbooks = [item[1] for item in scored]
    notes = [
        f"{playbook.playbook_id}: {reason} ({score:.1f})"
        for score, playbook, reason in scored
    ]
    return PlaybookRetrievalResult(
        matched_playbooks=matched_playbooks,
        playbook_match_score=scored[0][0] if scored else 0.0,
        notes=notes,
    )


def _highest_criticality(dependencies: list[Dependency]) -> RiskLevel | None:
    if not dependencies:
        return None
    return max(
        (dependency.criticality for dependency in dependencies),
        key=_RISK_RANK.get,
    )
