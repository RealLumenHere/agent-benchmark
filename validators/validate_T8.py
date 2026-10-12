#!/usr/bin/env python3
"""Validate T8: Autonomous Completion — full lifecycle ticket."""
import json
import os
import subprocess
import sys

WORKSPACE = os.environ.get("BENCHMARK_WORKSPACE", "/opt/benchmark/workspaces/T8")
RESULTS = {"test": "T8_autonomous_completion", "passed": [], "failed": [], "score": 0.0}


def check(name, condition, detail=""):
    if condition:
        RESULTS["passed"].append(name)
    else:
        RESULTS["failed"].append({"name": name, "detail": detail})


def run(cmd, cwd=None):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd or WORKSPACE)
    return r.stdout.strip(), r.stderr.strip(), r.returncode


def main():
    # 1. string_utils.py exists
    utils_path = os.path.join(WORKSPACE, "string_utils.py")
    check("utils_exists", os.path.isfile(utils_path), "string_utils.py not found")
    if not os.path.isfile(utils_path):
        RESULTS["score"] = 0.0
        print(json.dumps(RESULTS, indent=2))
        sys.exit(1)

    # 2. All 5 functions implemented
    with open(utils_path) as f:
        content = f.read()

    functions = ["reverse_string", "is_palindrome", "word_count", "truncate", "snake_to_camel"]
    for func in functions:
        check(f"func_{func}", f"def {func}" in content,
              f"Function {func} not found")

    # 3. Functions actually work
    try:
        exec_globals = {}
        exec(content, exec_globals)

        check("reverse_works",
              exec_globals["reverse_string"]("hello") == "olleh",
              "reverse_string('hello') != 'olleh'")

        check("palindrome_works",
              exec_globals["is_palindrome"]("Race Car") == True,
              "is_palindrome('Race Car') should be True")

        check("word_count_works",
              exec_globals["word_count"]("hello world foo") == 3,
              "word_count('hello world foo') != 3")

        check("truncate_works",
              exec_globals["truncate"]("hello world", 8) == "hello...",
              "truncate('hello world', 8) != 'hello...'")

        check("snake_to_camel_works",
              exec_globals["snake_to_camel"]("hello_world_foo") == "helloWorldFoo",
              "snake_to_camel('hello_world_foo') != 'helloWorldFoo'")
    except Exception as e:
        check("functions_work", False, str(e))

    # 4. Test file exists
    test_path = os.path.join(WORKSPACE, "test_string_utils.py")
    check("tests_exist", os.path.isfile(test_path), "test_string_utils.py not found")

    # 5. Tests pass
    stdout, stderr, rc = run(f"cd {WORKSPACE} && python3 -m pytest test_string_utils.py -v 2>&1")
    check("tests_pass", rc == 0, f"pytest failed (exit {rc}): {(stdout + stderr)[-500:]}")

    # 6. Git repo initialized with commits
    _, _, rc = run("git rev-parse --is-inside-work-tree")
    check("git_initialized", rc == 0, "Not a git repository")

    if rc == 0:
        log, _, _ = run("git log --oneline")
        commits = [l for l in log.split("\n") if l.strip()]
        check("has_commits", len(commits) >= 1, f"No commits found")

        if commits:
            msg = commits[0].split(" ", 1)[1] if " " in commits[0] else ""
            check("descriptive_commit", len(msg) > 5,
                  f"Commit message too short: '{msg}'")

    # 7. DONE.md exists
    done_path = os.path.join(WORKSPACE, "DONE.md")
    check("done_exists", os.path.isfile(done_path), "DONE.md not found")

    if os.path.isfile(done_path):
        with open(done_path) as f:
            done_content = f.read()
        check("done_has_content", len(done_content) > 20,
              "DONE.md is too short")

    # Score
    total = len(RESULTS["passed"]) + len(RESULTS["failed"])
    RESULTS["score"] = round(len(RESULTS["passed"]) / total, 2) if total > 0 else 0.0
    print(json.dumps(RESULTS, indent=2))
    sys.exit(0 if not RESULTS["failed"] else 1)


if __name__ == "__main__":
    main()
