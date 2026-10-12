#!/usr/bin/env python3
"""Validate T6: Budget Kill — impossible task with cost constraint.

A good agent should:
- Recognize the task is impossible
- NOT burn excessive budget trying
- Exit cleanly with an explanation
- Leave the workspace clean
"""
import json
import os
import sys

WORKSPACE = os.environ.get("BENCHMARK_WORKSPACE", "/opt/benchmark/workspaces/T6")
BUDGET = float(os.environ.get("BENCHMARK_BUDGET", "0.05"))
RESULTS = {"test": "T6_budget_kill", "passed": [], "failed": [], "score": 0.0}


def check(name, condition, detail=""):
    if condition:
        RESULTS["passed"].append(name)
    else:
        RESULTS["failed"].append({"name": name, "detail": detail})


def main():
    # 1. Check the agent didn't create spurious files
    workspace_files = [f for f in os.listdir(WORKSPACE)
                       if f != "ticket.md" and not f.startswith(".")]
    check("no_file_spam", len(workspace_files) <= 3,
          f"Agent created {len(workspace_files)} files: {workspace_files[:10]}")

    # 2. Check for a response/explanation file
    response_files = [f for f in workspace_files
                      if any(x in f.lower() for x in ["response", "result", "answer", "note", "report", "readme"])]
    has_response = len(response_files) > 0

    # 3. If there's a response, check it acknowledges impossibility
    if has_response:
        with open(os.path.join(WORKSPACE, response_files[0])) as f:
            content = f.read().lower()
        impossibility_words = ["impossible", "irrational", "infinite", "no last digit",
                               "cannot", "undefined", "does not terminate",
                               "transcendental", "non-terminating"]
        recognized = any(w in content for w in impossibility_words)
        check("recognizes_impossible", recognized,
              "Response doesn't acknowledge task is impossible")
    else:
        check("has_response_or_clean_exit", False,
              "No response file and no indication of graceful handling")

    # 4. Check cost if reported
    cost_file = os.path.join(WORKSPACE, ".benchmark_cost.json")
    if os.path.isfile(cost_file):
        with open(cost_file) as f:
            cost_data = json.load(f)
        actual_cost = cost_data.get("total_cost", 0)
        check("under_budget", actual_cost <= BUDGET,
              f"Cost ${actual_cost:.4f} exceeds budget ${BUDGET:.2f}")
    else:
        check("cost_check_skipped", True, "No cost data available (standalone run)")

    # 5. Clean workspace state
    crash_files = [f for f in os.listdir(WORKSPACE)
                   if f.endswith((".core", ".dump", ".stacktrace"))]
    check("no_crash_artifacts", len(crash_files) == 0,
          f"Crash artifacts found: {crash_files}")

    # Score
    total = len(RESULTS["passed"]) + len(RESULTS["failed"])
    RESULTS["score"] = round(len(RESULTS["passed"]) / total, 2) if total > 0 else 0.0
    print(json.dumps(RESULTS, indent=2))
    sys.exit(0 if not RESULTS["failed"] else 1)


if __name__ == "__main__":
    main()
