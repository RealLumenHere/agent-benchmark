#!/usr/bin/env python3
"""Forge ↔ wq bridge daemon.

Polls wq for open tickets tagged with 'forge-bench', creates Forge tasks,
and syncs completed Forge tasks back to wq as done.

This is a benchmark-only bridge — it does not run as a persistent daemon.
Instead, it's called per-ticket by run_benchmark.sh.

Usage:
    forge-wq-bridge.py run <workspace_dir>
    forge-wq-bridge.py status
"""
import json
import os
import subprocess
import sys
import time


FORGE_API = os.environ.get("FORGE_API", "http://localhost:8420/api/v1")


def run_cmd(cmd, timeout=60):
    """Run a shell command and return stdout."""
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
    return r.stdout.strip(), r.stderr.strip(), r.returncode


def forge_api(method, endpoint, data=None):
    """Call Forge REST API."""
    import urllib.request
    import urllib.error

    url = f"{FORGE_API}/{endpoint}"
    req = urllib.request.Request(url, method=method)
    req.add_header("Content-Type", "application/json")

    if data:
        body = json.dumps(data).encode()
        req.data = body

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return {"error": str(e), "status": e.code, "body": e.read().decode()[:500]}
    except Exception as e:
        return {"error": str(e)}


def run_ticket(workspace_dir):
    """Run Forge against a single benchmark ticket workspace."""
    workspace = os.path.realpath(workspace_dir)
    ticket_path = os.path.join(workspace, "ticket.md")

    if not os.path.isfile(ticket_path):
        print(f"ERROR: No ticket.md in {workspace}")
        sys.exit(1)

    with open(ticket_path) as f:
        task = f.read()

    print(f"[forge-bridge] Workspace: {workspace}")
    print(f"[forge-bridge] Task: {task[:200]}...")

    # Check if Forge daemon is running
    status = forge_api("GET", "tasks")
    if "error" in status:
        print(f"[forge-bridge] Forge API not available: {status['error']}")
        print("[forge-bridge] Starting Forge daemon...")
        subprocess.Popen(
            ["forge", "--no-mcp", "--data-dir", os.path.expanduser("~/.forge")],
            stdout=open("/tmp/forge-bench.log", "a"),
            stderr=subprocess.STDOUT,
        )
        time.sleep(3)

    # Create task in Forge
    result = forge_api("POST", "tasks", {
        "description": task,
        "workspace": workspace,
        "model": os.environ.get("FORGE_MODEL", "openai/qwen3.6:35b-a3b"),
    })

    if "error" in result:
        print(f"[forge-bridge] Failed to create task: {result}")
        sys.exit(1)

    task_id = result.get("id", "unknown")
    print(f"[forge-bridge] Created task: {task_id}")

    # Poll for completion
    max_wait = 600  # 10 minutes
    poll_interval = 5
    elapsed = 0

    while elapsed < max_wait:
        status = forge_api("GET", f"tasks/{task_id}")
        state = status.get("status", "unknown")

        if state in ("completed", "failed", "error"):
            print(f"[forge-bridge] Task {task_id} finished: {state}")
            with open(os.path.join(workspace, ".forge_result.json"), "w") as f:
                json.dump(status, f, indent=2)
            break

        time.sleep(poll_interval)
        elapsed += poll_interval

    if elapsed >= max_wait:
        print(f"[forge-bridge] Task {task_id} timed out after {max_wait}s")

    return result


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "run" and len(sys.argv) >= 3:
        run_ticket(sys.argv[2])
    elif cmd == "status":
        result = forge_api("GET", "tasks")
        print(json.dumps(result, indent=2))
    else:
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
