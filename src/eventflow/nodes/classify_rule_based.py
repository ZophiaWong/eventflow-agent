"""Rule-based event classification node."""

from __future__ import annotations

from eventflow.baseline.types import BaselineError
from eventflow.schemas import (
    DependencyMap,
    EventCandidate,
    EventType,
    RawSignal,
    SourceType,
)

_API_CHANGE_KEYWORDS = (
    "deprecation",
    "deprecated",
    "webhook",
    "field",
    "header",
    "pagination",
    "rate limit",
    "lifecycle",
    "validation update",
    "contract",
    "removed",
)
_PRODUCT_RELEASE_KEYWORDS = (
    "release",
    "availability",
    "performance",
    "dashboard",
    "stable",
    "improves",
    "expanded",
    "announcement",
    "refresh",
)


def classify_rule_based(
    signal: RawSignal,
    dependency_map: DependencyMap,
) -> tuple[EventCandidate | None, list[BaselineError]]:
    """Classify a RawSignal into an EventCandidate using deterministic rules."""

    event_type, confidence = _classify_event_type(signal)
    if event_type is None:
        return None, [
            BaselineError(
                stage="classify",
                error_code="unclassified_event_type",
                message="No rule matched the signal source type or text.",
                signal_id=signal.signal_id,
                details={"source_type": signal.source_type.value},
            )
        ]

    dependencies = _match_dependencies(signal, dependency_map)
    if not dependencies:
        confidence = min(confidence, 0.45)

    evidence_refs = [signal.signal_id, *dependencies]
    candidate = EventCandidate(
        candidate_id=f"cand_{signal.signal_id}",
        source_signal_id=signal.signal_id,
        event_type=event_type,
        vendor=signal.vendor,
        affected_dependencies=dependencies,
        summary=_summarize(signal),
        confidence=confidence,
        evidence_refs=evidence_refs,
    )
    return candidate, []


def _classify_event_type(signal: RawSignal) -> tuple[EventType | None, float]:
    if signal.source_type == SourceType.STATUS_PAGE:
        return EventType.SERVICE_INCIDENT, 0.95
    if signal.source_type == SourceType.SECURITY_ADVISORY:
        return EventType.SECURITY_ADVISORY, 0.95

    text = f"{signal.title} {signal.content}".lower()
    if any(keyword in text for keyword in _API_CHANGE_KEYWORDS):
        return EventType.API_CHANGE, 0.85
    if any(keyword in text for keyword in _PRODUCT_RELEASE_KEYWORDS):
        return EventType.PRODUCT_RELEASE, 0.85

    return None, 0.0


def _match_dependencies(signal: RawSignal, dependency_map: DependencyMap) -> list[str]:
    vendor = signal.vendor.casefold()
    matches: list[str] = []
    for module in dependency_map.modules:
        for dependency in module.dependencies:
            names = {
                dependency.vendor.casefold(),
                dependency.dependency_name.casefold(),
            }
            if vendor in names:
                matches.append(dependency.dependency_id)
    return matches


def _summarize(signal: RawSignal) -> str:
    content = signal.content.strip()
    if len(content) <= 220:
        return content
    return f"{content[:217].rstrip()}..."
