#!/usr/bin/env python3
"""Validate T1: Filesystem IO — syslog analysis task."""
import json
import os
import sys

WORKSPACE = os.environ.get("BENCHMARK_WORKSPACE", "/opt/benchmark/workspaces/T1")
RESULTS = {"test": "T1_filesystem_io", "passed": [], "failed": [], "score": 0.0}


def check(name, condition, detail=""):
    if condition:
        RESULTS["passed"].append(name)
    else:
        RESULTS["failed"].append({"name": name, "detail": detail})


def main():
    report_path = os.path.join(WORKSPACE, "report.json")

    # 1. report.json exists
    check("report_exists", os.path.isfile(report_path), "report.json not found")
    if not os.path.isfile(report_path):
        RESULTS["score"] = 0.0
        print(json.dumps(RESULTS, indent=2))
        sys.exit(1)

    # 2. Valid JSON
    try:
        with open(report_path) as f:
            report = json.load(f)
        check("valid_json", True)
    except (json.JSONDecodeError, Exception) as e:
        check("valid_json", False, str(e))
        RESULTS["score"] = 0.1
        print(json.dumps(RESULTS, indent=2))
        sys.exit(1)

    # 3. Load manifest for ground truth
    manifest_path = os.path.join(WORKSPACE, "manifest.json")
    with open(manifest_path) as f:
        manifest = json.load(f)

    # 4. Check ERROR count matches
    syslog_path = os.path.join(WORKSPACE, "syslog.log")
    with open(syslog_path) as f:
        actual_errors = sum(1 for line in f if "[ERROR]" in line)

    # Look for error count in report (flexible key matching)
    report_str = json.dumps(report).lower()
    found_error_count = None
    for key in report:
        k = key.lower()
        if "error" in k and isinstance(report[key], (int, float)):
            found_error_count = int(report[key])
            break
        elif isinstance(report[key], dict):
            for subkey in report[key]:
                if "error" in subkey.lower() and isinstance(report[key][subkey], (int, float)):
                    found_error_count = int(report[key][subkey])
                    break

    check("error_count_present", found_error_count is not None, "No ERROR count found in report")
    if found_error_count is not None:
        check("error_count_correct", found_error_count == actual_errors,
              f"Expected {actual_errors}, got {found_error_count}")

    # 5. All four levels represented
    levels_found = sum(1 for lev in ["ERROR", "WARN", "INFO", "DEBUG"]
                       if lev.lower() in report_str)
    check("all_levels_present", levels_found == 4,
          f"Only {levels_found}/4 levels found in report")

    # 6. Total line count
    check("total_lines_present", any(
        isinstance(report.get(k), (int, float)) and int(report[k]) == manifest["total_lines"]
        for k in report
    ) or str(manifest["total_lines"]) in report_str,
          f"Total line count {manifest['total_lines']} not found")

    # Score
    total = len(RESULTS["passed"]) + len(RESULTS["failed"])
    RESULTS["score"] = round(len(RESULTS["passed"]) / total, 2) if total > 0 else 0.0
    print(json.dumps(RESULTS, indent=2))
    sys.exit(0 if not RESULTS["failed"] else 1)


if __name__ == "__main__":
    main()
