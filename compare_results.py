#!/usr/bin/env python3
"""Compare benchmark results across multiple runs/candidates."""
import json
import os
import sys
from pathlib import Path

RESULTS_DIR = Path("/opt/benchmark/results")
SCORING = Path("/opt/benchmark/scoring_template.json")


def load_run(run_dir):
    """Load a single run's results."""
    summary_path = run_dir / "summary.json"
    if not summary_path.exists():
        return None

    with open(summary_path) as f:
        summary = json.load(f)

    # Load individual test results
    for test_file in run_dir.glob("T*_result.json"):
        test_id = test_file.stem.replace("_result", "")
        try:
            with open(test_file) as f:
                summary["tests"][test_id] = json.load(f)
        except (json.JSONDecodeError, KeyError):
            pass

    return summary


def weighted_score(results, scoring):
    """Calculate weighted score based on scoring template."""
    total_weight = 0
    weighted_sum = 0

    for test_id, test_meta in scoring["tests"].items():
        weight = test_meta["weight"]
        total_weight += weight

        test_result = results.get("tests", {}).get(test_id, {})
        score = test_result.get("score", 0.0) if isinstance(test_result, dict) else 0.0
        weighted_sum += score * weight

    return round(weighted_sum / total_weight, 4) if total_weight > 0 else 0.0


def main():
    if not RESULTS_DIR.exists():
        print("No results found.")
        sys.exit(1)

    with open(SCORING) as f:
        scoring = json.load(f)

    runs = []
    for run_dir in sorted(RESULTS_DIR.iterdir()):
        if run_dir.is_dir():
            result = load_run(run_dir)
            if result:
                result["_dir"] = str(run_dir)
                result["weighted_score"] = weighted_score(result, scoring)
                runs.append(result)

    if not runs:
        print("No completed runs found.")
        sys.exit(1)

    # Print comparison table
    print(f"\n{'Candidate':<20} {'Model':<25} {'Score':>8} {'W.Score':>8} {'Pass':>5} {'Fail':>5} {'Time':>6}")
    print("-" * 80)

    for run in sorted(runs, key=lambda r: r.get("weighted_score", 0), reverse=True):
        agg = run.get("aggregate", {})
        print(f"{run.get('candidate', '?'):<20} "
              f"{run.get('model', '?'):<25} "
              f"{agg.get('avg_score', 0):>8.3f} "
              f"{run.get('weighted_score', 0):>8.4f} "
              f"{agg.get('passed', 0):>5} "
              f"{agg.get('failed', 0):>5} "
              f"{agg.get('total_duration_s', 0):>5}s")

    # Per-test breakdown
    print(f"\n{'Test':<8}", end="")
    for run in runs:
        label = f"{run.get('candidate', '?')[:10]}"
        print(f" {label:>12}", end="")
    print()
    print("-" * (8 + 13 * len(runs)))

    for test_id in ["T1", "T2", "T3", "T4", "T5", "T6", "T7", "T8"]:
        meta = scoring["tests"].get(test_id, {})
        print(f"{test_id:<8}", end="")
        for run in runs:
            test_result = run.get("tests", {}).get(test_id, {})
            score = test_result.get("score", "-") if isinstance(test_result, dict) else "-"
            if isinstance(score, (int, float)):
                print(f" {score:>12.2f}", end="")
            else:
                print(f" {str(score):>12}", end="")
        print(f"  (w={meta.get('weight', 1.0):.1f})")


if __name__ == "__main__":
    main()
