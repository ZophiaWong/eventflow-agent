from pathlib import Path

from eventflow.baseline import evaluate_baseline

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"


def test_baseline_eval_smoke_metrics_meet_m2_thresholds() -> None:
    metrics = evaluate_baseline(DATA_DIR)

    assert metrics.total_cases == 24
    assert metrics.completed_cases == 24
    assert metrics.event_type_match_rate >= 0.85
    assert metrics.dependency_exact_match_rate >= 0.85
    assert metrics.risk_level_match_rate >= 0.60
    assert metrics.route_match_rate >= 0.60
    assert metrics.recommended_action_match_rate >= 0.60
