"""Deterministic historical case retrieval over synthetic local cases."""

from __future__ import annotations

import re

from eventflow.retrieval.types import HistoricalCaseRetrievalResult
from eventflow.schemas import HistoricalCase, RetrievalQuery

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def retrieve_historical_cases(
    query: RetrievalQuery,
    historical_cases: list[HistoricalCase],
) -> HistoricalCaseRetrievalResult:
    """Retrieve similar synthetic historical cases."""

    affected = {value.casefold() for value in query.affected_dependencies}
    keywords = set(query.keywords)
    scored: list[tuple[float, HistoricalCase, str]] = []

    for case in historical_cases:
        same_vendor = case.vendor.casefold() == query.vendor.casefold()
        same_event_type = case.event_type == query.event_type
        case_dependencies = {
            dependency.casefold() for dependency in case.affected_dependencies
        }
        dependency_overlap = bool(affected & case_dependencies)
        keyword_overlap = bool(keywords & _tokens(case.summary))

        if same_vendor and same_event_type and dependency_overlap:
            scored.append((1.0, case, "same vendor, event type, and dependency"))
        elif same_event_type and dependency_overlap:
            scored.append((0.8, case, "same event type and dependency"))
        elif same_vendor and same_event_type:
            scored.append((0.6, case, "same vendor and event type"))
        elif same_event_type:
            scored.append((0.4, case, "same event type"))
        elif dependency_overlap or keyword_overlap:
            scored.append((0.3, case, "weak dependency or keyword overlap"))

    scored.sort(key=lambda item: (-item[0], item[1].case_id))
    matched_cases = [item[1] for item in scored if item[0] >= 0.4]
    notes = [
        f"{case.case_id}: {reason} ({score:.1f})"
        for score, case, reason in scored
        if score >= 0.4
    ]
    return HistoricalCaseRetrievalResult(
        matched_historical_cases=matched_cases,
        historical_case_score=scored[0][0] if scored else 0.0,
        notes=notes,
    )


def _tokens(value: str) -> set[str]:
    return {token for token in _TOKEN_RE.findall(value.casefold()) if len(token) >= 3}
