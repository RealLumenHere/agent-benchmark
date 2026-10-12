#!/usr/bin/env python3
"""Generate 10K synthetic syslog entries with ERROR/WARN/INFO/DEBUG levels."""
import random
import json
from datetime import datetime, timedelta

LEVELS = ["ERROR", "WARN", "INFO", "DEBUG"]
SERVICES = ["nginx", "postgres", "litellm", "docker", "sshd", "crond", "systemd", "vault", "cloudflared", "redis"]
ERROR_MSGS = [
    "Connection refused to upstream",
    "Out of memory: killed process",
    "Disk space critical: 98% used",
    "Authentication failure for user root",
    "SSL certificate expired",
]
WARN_MSGS = [
    "High memory usage detected: 85%",
    "Slow query detected: 2.3s",
    "Rate limit approaching threshold",
    "Deprecated API call detected",
    "Connection pool near capacity",
]
INFO_MSGS = [
    "Request processed successfully",
    "Service started on port 8080",
    "Backup completed: 2.3GB transferred",
    "Health check passed",
    "Configuration reloaded",
]
DEBUG_MSGS = [
    "Entering function process_request",
    "Cache hit for key user:1234",
    "SQL query plan: sequential scan",
    "Socket buffer size: 65536",
    "Thread pool size adjusted to 8",
]

MSG_MAP = {"ERROR": ERROR_MSGS, "WARN": WARN_MSGS, "INFO": INFO_MSGS, "DEBUG": DEBUG_MSGS}
WEIGHTS = [0.05, 0.10, 0.60, 0.25]

random.seed(42)
base = datetime(2026, 10, 1, 0, 0, 0)
entries = []

for i in range(10000):
    ts = base + timedelta(seconds=random.randint(0, 86400 * 7))
    level = random.choices(LEVELS, weights=WEIGHTS, k=1)[0]
    service = random.choice(SERVICES)
    msg = random.choice(MSG_MAP[level])
    pid = random.randint(1000, 65535)
    fmt = "%b %d %H:%M:%S"
    entry = f"{ts.strftime(fmt)} lumen {service}[{pid}]: [{level}] {msg}"
    entries.append(entry)

entries.sort()

with open("/opt/benchmark/workspaces/T1/syslog.log", "w") as f:
    f.write("\n".join(entries) + "\n")

manifest = {
    "total_lines": len(entries),
    "level_counts": {lev: sum(1 for e in entries if f"[{lev}]" in e) for lev in LEVELS},
    "services": SERVICES,
    "seed": 42
}
with open("/opt/benchmark/workspaces/T1/manifest.json", "w") as f:
    json.dump(manifest, f, indent=2)

print(f"Generated {len(entries)} entries")
print(json.dumps(manifest, indent=2))
