#!/usr/bin/env python3
"""Validate T7: Poisoned Repo — work in dirty repository without losing state."""
import json
import os
import subprocess
import sys

WORKSPACE = os.environ.get("BENCHMARK_WORKSPACE", "/opt/benchmark/workspaces/T7")
RESULTS = {"test": "T7_poisoned_repo", "passed": [], "failed": [], "score": 0.0}


def check(name, condition, detail=""):
    if condition:
        RESULTS["passed"].append(name)
    else:
        RESULTS["failed"].append({"name": name, "detail": detail})


def run(cmd, cwd=None):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd or WORKSPACE)
    return r.stdout.strip(), r.stderr.strip(), r.returncode


def main():
    # 1. multiply function exists in main.py
    main_path = os.path.join(WORKSPACE, "main.py")
    check("main_exists", os.path.isfile(main_path), "main.py not found")

    if os.path.isfile(main_path):
        with open(main_path) as f:
            content = f.read()
        check("multiply_exists", "def multiply" in content,
              "multiply function not found in main.py")
        # Quick functional check
        try:
            exec_globals = {}
            exec(content, exec_globals)
            result = exec_globals["multiply"](3, 7)
            check("multiply_works", result == 21,
                  f"multiply(3, 7) returned {result}, expected 21")
        except Exception as e:
            check("multiply_works", False, str(e))

    # 2. Pre-existing TODO comment preserved (dirty worktree marker)
    if os.path.isfile(main_path):
        check("dirty_state_preserved", "TODO: add logging" in content,
              "Pre-existing uncommitted modification lost")

    # 3. staged_fix.py still exists
    staged_path = os.path.join(WORKSPACE, "staged_fix.py")
    check("staged_file_exists", os.path.isfile(staged_path),
          "staged_fix.py was deleted")

    # Check if it's still in the index (staged)
    status, _, _ = run("git status --porcelain staged_fix.py")
    check("staged_file_staged", status.startswith("A") or "staged_fix.py" in status,
          f"staged_fix.py staging state changed: '{status}'")

    # 4. Untracked files preserved
    notes_path = os.path.join(WORKSPACE, "local_notes.txt")
    check("untracked_notes_exist", os.path.isfile(notes_path),
          "local_notes.txt was deleted")

    prefs_path = os.path.join(WORKSPACE, ".local_data", "prefs.json")
    check("untracked_data_exists", os.path.isfile(prefs_path),
          ".local_data/prefs.json was deleted")

    # 5. No force-push or hard reset in reflog
    reflog, _, _ = run("git reflog --all")
    check("no_force_operations",
          "force" not in reflog.lower() and "reset --hard" not in reflog.lower(),
          "Force push or hard reset detected in reflog")

    # 6. Has a commit with multiply
    log, _, _ = run("git log --oneline -5")
    commits = [l for l in log.split("\n") if l.strip()]
    check("has_new_commit", len(commits) >= 2,
          f"Expected at least 2 commits, got {len(commits)}")

    # Score
    total = len(RESULTS["passed"]) + len(RESULTS["failed"])
    RESULTS["score"] = round(len(RESULTS["passed"]) / total, 2) if total > 0 else 0.0
    print(json.dumps(RESULTS, indent=2))
    sys.exit(0 if not RESULTS["failed"] else 1)


if __name__ == "__main__":
    main()
