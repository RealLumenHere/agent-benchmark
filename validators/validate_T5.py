#!/usr/bin/env python3
"""Validate T5: Failure Recovery — SIGKILL during long task.

This validator:
1. Starts long_task.py
2. SIGKILLs it after 5 seconds (to keep benchmark fast)
3. Restarts it
4. Checks that it recovers and completes
"""
import json
import os
import signal
import subprocess
import sys
import time

WORKSPACE = os.environ.get("BENCHMARK_WORKSPACE", "/opt/benchmark/workspaces/T5")
RESULTS = {"test": "T5_failure_recovery", "passed": [], "failed": [], "score": 0.0}
KILL_AFTER = 5  # seconds


def check(name, condition, detail=""):
    if condition:
        RESULTS["passed"].append(name)
    else:
        RESULTS["failed"].append({"name": name, "detail": detail})


def main():
    script = os.path.join(WORKSPACE, "long_task.py")
    checkpoint = os.path.join(WORKSPACE, "checkpoint.json")
    result = os.path.join(WORKSPACE, "result.json")

    # Clean up any previous runs
    for f in [checkpoint, result]:
        if os.path.isfile(f):
            os.remove(f)

    # 1. Start the task
    proc = subprocess.Popen(
        [sys.executable, script],
        cwd=WORKSPACE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # 2. Wait then SIGKILL
    time.sleep(KILL_AFTER)
    proc.send_signal(signal.SIGKILL)
    proc.wait()

    check("process_killed", proc.returncode == -9 or proc.returncode == -signal.SIGKILL,
          f"Expected SIGKILL, got exit code {proc.returncode}")

    # 3. Check checkpoint exists
    check("checkpoint_saved", os.path.isfile(checkpoint),
          "No checkpoint.json after kill")

    if os.path.isfile(checkpoint):
        with open(checkpoint) as f:
            cp = json.load(f)
        check("checkpoint_has_progress", cp.get("iteration", 0) > 0,
              f"Checkpoint shows 0 progress: {cp}")

    # 4. Restart the task — should resume from checkpoint
    proc2 = subprocess.Popen(
        [sys.executable, script],
        cwd=WORKSPACE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    stdout, stderr = proc2.communicate(timeout=120)

    check("recovery_no_crash", proc2.returncode == 0,
          f"Recovery crashed (exit {proc2.returncode}): {stderr.decode()[-500:]}")

    # 5. Check result.json
    check("result_exists", os.path.isfile(result), "result.json not created after recovery")

    if os.path.isfile(result):
        with open(result) as f:
            res = json.load(f)
        check("all_iterations_done", res.get("completed") == 300,
              f"Only {res.get('completed')} iterations completed")

    # 6. Checkpoint cleaned up
    check("checkpoint_cleaned", not os.path.isfile(checkpoint),
          "checkpoint.json not cleaned up after completion")

    # Score
    total = len(RESULTS["passed"]) + len(RESULTS["failed"])
    RESULTS["score"] = round(len(RESULTS["passed"]) / total, 2) if total > 0 else 0.0
    print(json.dumps(RESULTS, indent=2))
    sys.exit(0 if not RESULTS["failed"] else 1)


if __name__ == "__main__":
    main()
