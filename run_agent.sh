#!/bin/bash
set -euo pipefail
CANDIDATE="${1:?candidate}"
MODEL="${2:?model}"
TEST="${3:?test_id}"
RESULTS_BASE="${4:?results_base}"
BENCHMARK_DIR="/opt/benchmark"
CLAUDE_BIN="/home/lumen/.npm-global/bin/claude"

RUN_DIR="${RESULTS_BASE}/${CANDIDATE}_${TEST}"
mkdir -p "$RUN_DIR"
WORK_COPY="${RUN_DIR}/workspace"
sudo rm -rf "$WORK_COPY"
cp -a "${BENCHMARK_DIR}/workspaces/${TEST}" "$WORK_COPY"

if [ "${TEST}" = "T2" ] && [ ! -d "${WORK_COPY}/.git" ]; then
    (cd "$WORK_COPY" && git init -q && git config user.email "bench@lumen" && git config user.name "Benchmark" && git add -A && git commit -q -m "Initial commit")
fi
if [ "${TEST}" = "T7" ] && [ -f "${WORK_COPY}/setup_poisoned.sh" ] && [ ! -d "${WORK_COPY}/.git" ]; then
    bash "${WORK_COPY}/setup_poisoned.sh" "$WORK_COPY"
fi

TASK=$(cat "${WORK_COPY}/ticket.md")
START_TS=$(date +%s)
echo "[$(date -u +%H:%M:%S)] ${CANDIDATE}/${TEST}: starting"

case "${CANDIDATE}" in
  claude-max)
    (cd "$WORK_COPY" && timeout 300 ${CLAUDE_BIN} \
      -p "${TASK}" \
      --dangerously-skip-permissions \
      --output-format text \
      --model "${MODEL}" \
      > "${RUN_DIR}/agent_output.txt" 2>"${RUN_DIR}/agent_stderr.log") || true
    ;;
  openhands)
    timeout 600 docker run --rm \
      --name "oh-bench-${TEST}-$(date +%s)" \
      -e SANDBOX_RUNTIME_CONTAINER_IMAGE=ghcr.io/all-hands-ai/runtime:0.25.0-nikolaik \
      -e WORKSPACE_MOUNT_PATH="${WORK_COPY}" \
      -v /var/run/docker.sock:/var/run/docker.sock \
      -v "${WORK_COPY}:/opt/workspace_base" \
      -v /home/lumen/.config/openhands/config.toml:/app/config.toml \
      --network host \
      ghcr.io/all-hands-ai/openhands:0.25.0 \
      python -m openhands.core.main \
      -t "${TASK}" -i 50 \
      > "${RUN_DIR}/agent_output.txt" 2>"${RUN_DIR}/agent_stderr.log" || true
    ;;
  forge)
    (cd "$WORK_COPY" && \
      FORGE_MODEL="${MODEL}" \
      LITELLM_API_BASE="http://localhost:4000/v1" \
      LITELLM_API_KEY="sk-litellm-local" \
      timeout 300 python3 "${BENCHMARK_DIR}/forge-wq-bridge.py" run "$WORK_COPY" \
      > "${RUN_DIR}/agent_output.txt" 2>"${RUN_DIR}/agent_stderr.log") || true
    ;;
esac

END_TS=$(date +%s)
DURATION=$((END_TS - START_TS))
echo "[$(date -u +%H:%M:%S)] ${CANDIDATE}/${TEST}: agent done in ${DURATION}s"

VALIDATOR="${BENCHMARK_DIR}/validators/validate_${TEST}.py"
if [ -f "$VALIDATOR" ]; then
    BENCHMARK_WORKSPACE="$WORK_COPY" python3 "$VALIDATOR" > "${RUN_DIR}/validation.json" 2>&1 || true
    SCORE=$(python3 -c "import json,sys; print(json.load(open(sys.argv[1])).get('score',0))" "${RUN_DIR}/validation.json" 2>/dev/null || echo "0")
else
    SCORE=0
    echo '{"score":0,"error":"no validator"}' > "${RUN_DIR}/validation.json"
fi

TS_NOW=$(date -u +%Y-%m-%dT%H:%M:%SZ)
python3 /opt/benchmark/write_result.py "$CANDIDATE" "$MODEL" "$TEST" "$DURATION" "$SCORE" "$TS_NOW" "${RUN_DIR}/result.json"
echo "[$(date -u +%H:%M:%S)] ${CANDIDATE}/${TEST}: score=${SCORE} duration=${DURATION}s"
