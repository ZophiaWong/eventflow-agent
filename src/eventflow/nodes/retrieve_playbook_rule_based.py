"""Rule-based evidence and playbook retrieval node."""

from __future__ import annotations

from eventflow.baseline.types import BaselineError
from eventflow.schemas import (
    Dependency,
    DependencyMap,
    EventCandidate,
    EvidencePack,
    Playbook,
    RawSignal,
    RiskLevel,
)

_RISK_RANK = {
    RiskLevel.LOW: 0,
    RiskLevel.MEDIUM: 1,
    RiskLevel.HIGH: 2,
    RiskLevel.CRITICAL: 3,
}


def retrieve_playbook_rule_based(
    signal: RawSignal,
    candidate: EventCandidate,
    dependency_map: DependencyMap,
    playbooks: list[Playbook],
) -> tuple[EvidencePack, Playbook | None, list[BaselineError]]:
    """Build an EvidencePack and retrieve the matching playbook."""

    errors: list[BaselineError] = []
    dependencies = _dependencies_by_id(dependency_map)
    matched_dependencies = [
        dependencies[dependency_id]
        for dependency_id in candidate.affected_dependencies
        if dependency_id in dependencies
    ]

    if not matched_dependencies:
        errors.append(
            BaselineError(
                stage="retrieve_playbook",
                error_code="dependency_not_matched",
                message="No dependency-map entry matched the candidate vendor.",
                signal_id=signal.signal_id,
                details={"vendor": candidate.vendor},
            )
        )

    criticality = _highest_criticality(matched_dependencies)
    matched_playbook = _find_playbook(candidate, criticality, playbooks)
    if matched_dependencies and matched_playbook is None:
        errors.append(
            BaselineError(
                stage="retrieve_playbook",
                error_code="playbook_not_found",
                message="No playbook matched the candidate event type and dependency criticality.",
                signal_id=signal.signal_id,
                details={
                    "event_type": candidate.event_type.value,
                    "dependency_criticality": criticality.value if criticality else None,
                },
            )
        )

    evidence_notes = [
        f"Raw signal {signal.signal_id} from {signal.source_type.value}.",
    ]
    for dependency in matched_dependencies:
        evidence_notes.append(
            f"Matched {dependency.dependency_id} with {dependency.criticality.value} criticality."
        )
    if matched_playbook is not None:
        evidence_notes.append(f"Matched playbook {matched_playbook.playbook_id}.")

    evidence_pack = EvidencePack(
        evidence_id=f"evidence_{signal.signal_id}",
        source_signal_ids=[signal.signal_id],
        matched_dependencies=[dependency.dependency_id for dependency in matched_dependencies],
        matched_playbooks=(
            [matched_playbook.playbook_id] if matched_playbook is not None else []
        ),
        matched_historical_cases=[],
        evidence_notes=evidence_notes,
        retrieval_quality=1.0 if matched_dependencies and matched_playbook else 0.4,
    )
    return evidence_pack, matched_playbook, errors


def _dependencies_by_id(dependency_map: DependencyMap) -> dict[str, Dependency]:
    return {
        dependency.dependency_id: dependency
        for module in dependency_map.modules
        for dependency in module.dependencies
    }


def _highest_criticality(dependencies: list[Dependency]) -> RiskLevel | None:
    if not dependencies:
        return None
    return max((dependency.criticality for dependency in dependencies), key=_RISK_RANK.get)


def _find_playbook(
    candidate: EventCandidate,
    criticality: RiskLevel | None,
    playbooks: list[Playbook],
) -> Playbook | None:
    if criticality is None:
        return None
    for playbook in playbooks:
        if (
            playbook.event_type == candidate.event_type
            and playbook.dependency_criticality == criticality
        ):
            return playbook
    return None
