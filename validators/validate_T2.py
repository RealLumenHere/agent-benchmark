#!/usr/bin/env python3
"""Validate T2: Git Hygiene — os.path to pathlib migration."""
import json
import os
import subprocess
import sys

WORKSPACE = os.environ.get("BENCHMARK_WORKSPACE", "/opt/benchmark/workspaces/T2")
RESULTS = {"test": "T2_git_hygiene", "passed": [], "failed": [], "score": 0.0}


def check(name, condition, detail=""):
    if condition:
        RESULTS["passed"].append(name)
    else:
        RESULTS["failed"].append({"name": name, "detail": detail})


def run(cmd, cwd=None):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd or WORKSPACE)
    return r.stdout.strip(), r.stderr.strip(), r.returncode


def main():
    # 1. Check it's a git repo
    _, _, rc = run("git rev-parse --is-inside-work-tree")
    check("is_git_repo", rc == 0, "Not a git repository")
    if rc != 0:
        RESULTS["score"] = 0.0
        print(json.dumps(RESULTS, indent=2))
        sys.exit(1)

    # 2. Check current branch is NOT main
    branch, _, _ = run("git branch --show-current")
    branches_out, _, _ = run("git branch --list")
    branches = [b.strip().lstrip("* ") for b in branches_out.split("\n") if b.strip()]

    # Check that work was done on a non-main branch
    has_feature_branch = any(b != "main" and b != "" for b in branches)
    check("feature_branch_exists", has_feature_branch,
          f"No feature branch found, branches: {branches}")

    # 3. Check main is untouched
    main_diff, _, rc = run("git diff main -- legacy_paths.py")
    # main should have the original file — check the feature branch has changes
    if has_feature_branch:
        feature = [b for b in branches if b != "main"][0]
        feat_diff, _, _ = run(f"git diff main..{feature} -- legacy_paths.py")
        check("main_untouched", len(feat_diff) > 0 or len(main_diff) == 0,
              "Changes should be on feature branch, not main")

    # 4. Read the modified file (from feature branch or working tree)
    if has_feature_branch:
        feature = [b for b in branches if b != "main"][0]
        content, _, rc = run(f"git show {feature}:legacy_paths.py")
        if rc != 0:
            content, _, _ = run("cat legacy_paths.py")
    else:
        with open(os.path.join(WORKSPACE, "legacy_paths.py")) as f:
            content = f.read()

    # 5. Check pathlib usage
    check("pathlib_imported", "from pathlib import" in content or "import pathlib" in content,
          "pathlib not imported")

    # 6. Check os.path removed
    check("os_path_removed", "os.path." not in content,
          "os.path still used in refactored file")

    # 7. Check commit message quality
    if has_feature_branch:
        feature = [b for b in branches if b != "main"][0]
        log, _, _ = run(f"git log main..{feature} --oneline")
        commits = [l.strip() for l in log.split("\n") if l.strip()]
        check("has_commits", len(commits) > 0, "No commits on feature branch")
        if commits:
            msg = commits[0].split(" ", 1)[1] if " " in commits[0] else ""
            bad_msgs = ["fix", "update", "changes", "wip", "asdf"]
            check("descriptive_commit", not any(msg.strip().lower() == b for b in bad_msgs),
                  f"Commit message too generic: '{msg}'")

    # Score
    total = len(RESULTS["passed"]) + len(RESULTS["failed"])
    RESULTS["score"] = round(len(RESULTS["passed"]) / total, 2) if total > 0 else 0.0
    print(json.dumps(RESULTS, indent=2))
    sys.exit(0 if not RESULTS["failed"] else 1)


if __name__ == "__main__":
    main()
