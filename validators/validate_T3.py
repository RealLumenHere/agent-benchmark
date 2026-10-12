#!/usr/bin/env python3
"""Validate T3: Bug Fix — Flask app with 3 bugs."""
import json
import os
import subprocess
import sys

WORKSPACE = os.environ.get("BENCHMARK_WORKSPACE", "/opt/benchmark/workspaces/T3")
RESULTS = {"test": "T3_bug_fix", "passed": [], "failed": [], "score": 0.0}


def check(name, condition, detail=""):
    if condition:
        RESULTS["passed"].append(name)
    else:
        RESULTS["failed"].append({"name": name, "detail": detail})


def run(cmd, cwd=None):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd or WORKSPACE)
    return r.stdout.strip(), r.stderr.strip(), r.returncode


def main():
    app_path = os.path.join(WORKSPACE, "app.py")

    # 1. app.py exists
    check("app_exists", os.path.isfile(app_path), "app.py not found")

    # 2. Read the fixed app
    with open(app_path) as f:
        content = f.read()

    # 3. Bug 1: json should be imported
    check("json_imported", "import json" in content, "json module not imported")

    # 4. Bug 2: `user` should be replaced with `name`
    check("var_name_fixed", "user}" not in content and "{name}" in content,
          "Variable name bug not fixed (should use 'name' not 'user')")

    # 5. Bug 3: File handle should be properly closed
    has_context_manager = "with open(" in content.split("def write_log")[1] if "def write_log" in content else False
    has_close = "f.close()" in content
    check("file_handle_fixed", has_context_manager or has_close,
          "File handle leak not fixed (use context manager or close())")

    # 6. Run pytest
    stdout, stderr, rc = run(f"cd {WORKSPACE} && python3 -m pytest test_app.py -v 2>&1")
    combined = stdout + stderr
    check("pytest_passes", rc == 0, f"pytest failed (exit {rc}): {combined[-500:]}")

    # 7. Check minimal diff
    check("test_unchanged", os.path.isfile(os.path.join(WORKSPACE, "test_app.py")),
          "test_app.py should not be deleted")
    check("config_unchanged", os.path.isfile(os.path.join(WORKSPACE, "config.json")),
          "config.json should not be deleted")

    # Score
    total = len(RESULTS["passed"]) + len(RESULTS["failed"])
    RESULTS["score"] = round(len(RESULTS["passed"]) / total, 2) if total > 0 else 0.0
    print(json.dumps(RESULTS, indent=2))
    sys.exit(0 if not RESULTS["failed"] else 1)


if __name__ == "__main__":
    main()
