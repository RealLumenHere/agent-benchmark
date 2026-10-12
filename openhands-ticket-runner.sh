#!/bin/bash
# openhands-ticket-runner.sh — Run OpenHands against a benchmark ticket
# Usage: openhands-ticket-runner.sh <workspace_dir> [--port PORT]
set -euo pipefail

WORKSPACE="${1:?Usage: openhands-ticket-runner.sh <workspace_dir>}"
OH_PORT="${2:-3100}"  # Avoid 3000 (used by vane)
WORKSPACE=$(realpath "$WORKSPACE")
TICKET="${WORKSPACE}/ticket.md"

if [ ! -f "$TICKET" ]; then
    echo "ERROR: No ticket.md found in ${WORKSPACE}"
    exit 1
fi

TASK=$(cat "$TICKET")

echo "[openhands-runner] Workspace: ${WORKSPACE}"
echo "[openhands-runner] Port: ${OH_PORT}"
echo "[openhands-runner] Task length: ${#TASK} chars"

# Run OpenHands in headless mode via Docker
docker run --rm \
    --name "openhands-bench-$(date +%s)" \
    -e SANDBOX_RUNTIME_CONTAINER_IMAGE=ghcr.io/all-hands-ai/runtime:0.25.0-nikolaik \
    -e WORKSPACE_MOUNT_PATH="${WORKSPACE}" \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -v "${WORKSPACE}:/opt/workspace_base" \
    -v /home/lumen/.config/openhands/config.toml:/app/config.toml \
    --add-host host.docker.internal:host-gateway \
    -p "${OH_PORT}:3000" \
    ghcr.io/all-hands-ai/openhands:0.25.0 \
    python -m openhands.core.main \
    -t "${TASK}" \
    2>&1 | tee "${WORKSPACE}/.openhands_log.txt"

EXIT_CODE=$?
echo "[openhands-runner] Exit code: ${EXIT_CODE}"
echo "[openhands-runner] Log: ${WORKSPACE}/.openhands_log.txt"
exit $EXIT_CODE
