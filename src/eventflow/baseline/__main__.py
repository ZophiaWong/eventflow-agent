"""Command-line runner for the rule-based baseline."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from eventflow.baseline import (
    evaluate_baseline,
    run_baseline_for_all,
    run_baseline_for_signal_id,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the EventFlow M2 baseline.")
    parser.add_argument("--data-dir", default="data", help="Path to the data directory.")
    parser.add_argument("--signal-id", help="Run one sample raw signal by ID.")
    parser.add_argument("--all", action="store_true", help="Run all sample raw signals.")
    parser.add_argument("--eval", action="store_true", help="Run draft eval smoke metrics.")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    selected_modes = sum(bool(value) for value in (args.signal_id, args.all, args.eval))
    if selected_modes != 1:
        parser.error("Select exactly one of --signal-id, --all, or --eval.")

    if args.signal_id:
        output: Any = run_baseline_for_signal_id(data_dir, args.signal_id).model_dump(
            mode="json"
        )
    elif args.all:
        output = [
            result.model_dump(mode="json")
            for result in run_baseline_for_all(data_dir)
        ]
    else:
        output = evaluate_baseline(data_dir).model_dump(mode="json")

    indent = 2 if args.pretty else None
    print(json.dumps(output, indent=indent, sort_keys=True))


if __name__ == "__main__":
    main()
