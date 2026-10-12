#!/usr/bin/env python3
"""Long-running task that processes 300 iterations with checkpointing."""
import json
import os
import signal
import sys
import time

CHECKPOINT_FILE = os.path.join(os.path.dirname(__file__), "checkpoint.json")
RESULT_FILE = os.path.join(os.path.dirname(__file__), "result.json")
TOTAL_ITERATIONS = 300


def load_checkpoint():
    """Load the last checkpoint, if any."""
    if os.path.isfile(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE) as f:
            return json.load(f)
    return {"iteration": 0, "data": []}


def save_checkpoint(state):
    """Save current state to checkpoint."""
    with open(CHECKPOINT_FILE, "w") as f:
        json.dump(state, f)


def process_iteration(i):
    """Simulate work for one iteration."""
    time.sleep(0.1)  # 100ms per iteration = 30s for 300
    return {"iter": i, "value": i * i, "ts": time.time()}


def main():
    state = load_checkpoint()
    start_iter = state["iteration"]

    print(f"Starting from iteration {start_iter}/{TOTAL_ITERATIONS}")

    for i in range(start_iter, TOTAL_ITERATIONS):
        result = process_iteration(i)
        state["data"].append(result)
        state["iteration"] = i + 1

        # Checkpoint every 10 iterations
        if (i + 1) % 10 == 0:
            save_checkpoint(state)
            print(f"Checkpoint at {i + 1}/{TOTAL_ITERATIONS}")

    # Final save
    with open(RESULT_FILE, "w") as f:
        json.dump({
            "total_iterations": TOTAL_ITERATIONS,
            "completed": len(state["data"]),
            "final_value": state["data"][-1]["value"] if state["data"] else None,
        }, f, indent=2)

    # Clean up checkpoint
    if os.path.isfile(CHECKPOINT_FILE):
        os.remove(CHECKPOINT_FILE)

    print(f"Completed all {TOTAL_ITERATIONS} iterations")


if __name__ == "__main__":
    main()
