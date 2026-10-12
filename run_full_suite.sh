#!/bin/bash
# Full OpenHands benchmark suite — robust version
# No set -e: we want to continue even if individual tests fail
set +e
CANDIDATE="openhands"
MODEL="openai/deepseek-v4-flash"
RUN_DIR="/opt/benchmark/results/run_20261012_full"
LOG="/tmp/bench-full-suite.log"
mkdir -p "$RUN_DIR"

exec > >(tee -a "$LOG") 2>&1

PASSED=0
FAILED=0
for TEST in T1 T2 T3 T4 T5 T6 T7 T8; do
  echo "======== ${TEST} $(date -u +%H:%M:%S) ========"

  # Clean up any leftover Docker containers
  docker ps -aq --filter "name=oh-bench-${TEST}" | xargs -r docker rm -f 2>/dev/null
  docker ps -aq --filter "name=openhands-runtime" --filter "status=exited" | xargs -r docker rm 2>/dev/null

  bash /opt/benchmark/run_agent.sh "$CANDIDATE" "$MODEL" "$TEST" "$RUN_DIR"
  RC=$?
  echo "  run_agent exit=$RC"

  # Clean up runtime containers after each test
  docker ps -aq --filter "name=openhands-runtime" | xargs -r docker rm -f 2>/dev/null
  sleep 5

  RESULT_FILE="${RUN_DIR}/${CANDIDATE}_${TEST}/result.json"
  if [ -f "$RESULT_FILE" ]; then
    SCORE=$(python3 -c "import json; print(json.load(open()).get(score,0))" 2>/dev/null || echo "0")
  else
    SCORE="0"
  fi

  if python3 -c "import sys; sys.exit(0 if float() > 0 else 1)" 2>/dev/null; then
    PASSED=$((PASSED+1))
    echo "  => PASS score=${SCORE}"
  else
    FAILED=$((FAILED+1))
    echo "  => FAIL score=${SCORE}"
  fi
done

echo ""
echo "=== FINAL: passed=$PASSED failed=$FAILED of 8 $(date -u +%H:%M:%S) ==="
