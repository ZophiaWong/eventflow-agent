"""Deterministic dependency retrieval over the local dependency map."""

from __future__ import annotations

import re
from dataclasses import dataclass

from eventflow.retrieval.types import DependencyRetrievalResult
from eventflow.schemas import Dependency, DependencyMap, ProductModule, RetrievalQuery

_TOKEN_RE = re.compile(r"[a-z0-9]+")


@dataclass(frozen=True)
class _DependencyContext:
    dependency: Dependency
    module: ProductModule


def retrieve_dependencies(
    query: RetrievalQuery,
    dependency_map: DependencyMap,
) -> DependencyRetrievalResult:
    """Retrieve dependency context for a structured query."""

    scored: list[tuple[float, Dependency, str]] = []
    query_vendor = query.vendor.casefold()
    normalized_vendor = _normalize(query.vendor)
    affected = {_normalize(value) for value in query.affected_dependencies}
    keyword_set = set(query.keywords)

    for context in _dependency_contexts(dependency_map):
        dependency = context.dependency
        exact_names = {
            dependency.vendor.casefold(),
            dependency.dependency_name.casefold(),
            dependency.dependency_id.casefold(),
        }
        normalized_names = {
            _normalize(dependency.vendor),
            _normalize(dependency.dependency_name),
            _normalize(dependency.dependency_id),
        }

        if query_vendor in exact_names or dependency.dependency_id.casefold() in {
            value.casefold() for value in query.affected_dependencies
        }:
            scored.append((1.0, dependency, "exact dependency match"))
            continue

        if normalized_vendor in normalized_names or normalized_names & affected:
            scored.append((0.8, dependency, "normalized dependency name match"))
            continue

        module_tokens = _tokens(context.module.module_name)
        if module_tokens and module_tokens & keyword_set:
            scored.append((0.6, dependency, "module keyword match"))
            continue

        dependency_tokens = (
            _tokens(dependency.dependency_type)
            | _tokens(dependency.used_for)
            | _tokens(dependency.vendor)
            | _tokens(dependency.dependency_name)
        )
        if dependency_tokens & keyword_set:
            scored.append((0.3, dependency, "weak dependency keyword match"))

    scored.sort(key=lambda item: (-item[0], item[1].dependency_id))
    matched_dependencies = [item[1] for item in scored]
    notes = [
        f"{dependency.dependency_id}: {reason} ({score:.1f})"
        for score, dependency, reason in scored
    ]
    return DependencyRetrievalResult(
        matched_dependencies=matched_dependencies,
        dependency_match_score=scored[0][0] if scored else 0.0,
        notes=notes,
    )


def _dependency_contexts(dependency_map: DependencyMap) -> list[_DependencyContext]:
    return [
        _DependencyContext(dependency=dependency, module=module)
        for module in dependency_map.modules
        for dependency in module.dependencies
    ]


def _normalize(value: str) -> str:
    return "".join(_TOKEN_RE.findall(value.casefold()))


def _tokens(value: str) -> set[str]:
    return {token for token in _TOKEN_RE.findall(value.casefold()) if len(token) >= 3}
