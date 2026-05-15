"""Rule-based baseline workflow."""

from eventflow.baseline.types import BaselineError, BaselineEvalMetrics, BaselineResult

__all__ = [
    "BaselineError",
    "BaselineEvalMetrics",
    "BaselineResult",
    "evaluate_baseline",
    "load_baseline_inputs",
    "run_baseline_for_all",
    "run_baseline_for_signal",
    "run_baseline_for_signal_id",
]


def __getattr__(name: str):
    if name in {
        "evaluate_baseline",
        "load_baseline_inputs",
        "run_baseline_for_all",
        "run_baseline_for_signal",
        "run_baseline_for_signal_id",
    }:
        from eventflow.baseline import pipeline

        return getattr(pipeline, name)
    raise AttributeError(f"module 'eventflow.baseline' has no attribute {name!r}")
