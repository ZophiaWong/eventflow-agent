"""Build structured retrieval queries from event clusters."""

from __future__ import annotations

import re

from eventflow.schemas import EventCluster, RetrievalQuery

_TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9+/#.-]*")
_STOP_WORDS = {
    "and",
    "are",
    "but",
    "for",
    "from",
    "may",
    "new",
    "not",
    "the",
    "this",
    "with",
}


def build_retrieval_query(cluster: EventCluster, attempt: int = 0) -> RetrievalQuery:
    """Build a deterministic RetrievalQuery from an EventCluster."""

    text_parts = [
        cluster.vendor,
        cluster.canonical_title,
        cluster.canonical_summary,
        *cluster.affected_dependencies,
    ]
    keywords = _keywords_from_text(" ".join(text_parts))
    return RetrievalQuery(
        query_id=f"rq_{cluster.cluster_id}_attempt_{attempt}",
        event_type=cluster.event_type,
        vendor=cluster.vendor,
        affected_dependencies=cluster.affected_dependencies,
        keywords=keywords,
        summary=cluster.canonical_summary,
        attempt=attempt,
    )


def _keywords_from_text(text: str) -> list[str]:
    keywords: list[str] = []
    seen: set[str] = set()
    for match in _TOKEN_RE.finditer(text.casefold()):
        token = match.group(0).strip(".-/")
        if len(token) < 3 or token in _STOP_WORDS or token in seen:
            continue
        seen.add(token)
        keywords.append(token)
    return keywords
