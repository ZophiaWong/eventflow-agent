"""Load and validate local sample datasets."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel

from eventflow.schemas import (
    DependencyMap,
    EvalCase,
    HistoricalCase,
    Playbook,
    RawSignal,
)

ModelT = TypeVar("ModelT", bound=BaseModel)


def load_json(path: Path | str) -> object:
    """Load a JSON file."""

    with Path(path).open(encoding="utf-8") as file:
        return json.load(file)


def load_jsonl(path: Path | str) -> list[dict[str, object]]:
    """Load a JSONL file, ignoring blank lines."""

    records: list[dict[str, object]] = []
    with Path(path).open(encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            value = json.loads(stripped)
            if not isinstance(value, dict):
                raise ValueError(f"{path}:{line_number} must contain a JSON object")
            records.append(value)
    return records


def _validate_jsonl(path: Path | str, model_type: type[ModelT]) -> list[ModelT]:
    return [model_type.model_validate(record) for record in load_jsonl(path)]


def load_raw_signals(path: Path | str) -> list[RawSignal]:
    """Load RawSignal records from JSONL."""

    return _validate_jsonl(path, RawSignal)


def load_dependency_map(path: Path | str) -> DependencyMap:
    """Load the dependency map from JSON."""

    return DependencyMap.model_validate(load_json(path))


def load_playbooks(path: Path | str) -> list[Playbook]:
    """Load Playbook records from JSONL."""

    return _validate_jsonl(path, Playbook)


def load_historical_cases(path: Path | str) -> list[HistoricalCase]:
    """Load HistoricalCase records from JSONL."""

    return _validate_jsonl(path, HistoricalCase)


def load_eval_cases(path: Path | str) -> list[EvalCase]:
    """Load EvalCase records from JSONL."""

    return _validate_jsonl(path, EvalCase)
