#!/bin/bash
# run_benchmark.sh — Master benchmark runner for agent comparison
# Usage: run_benchmark.sh <candidate> <model> [test_ids...]
# Example: run_benchmark.sh openhands qwen3.6:35b-a3b T1 T3 T5
# Example: run_benchmark.sh forge deepseek-v4 (runs all 8)
set -euo pipefail

BENCHMARK_DIR="/opt/benchmark"
RESULTS_DIR="${BENCHMARK_DIR}/results"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
CANDIDATE="${1:?Usage: run_benchmark.sh <candidate> <model> [test_ids...]}"
MODEL="${2:?Usage: run_benchmark.sh <candidate> <model> [test_ids...]}"
shift 2

# Default to all tests if none specified
if [ $# -eq 0 ]; then
    TESTS=(T1 T2 T3 T4 T5 T6 T7 T8)
else
    TESTS=("$@")
fi

RUN_DIR="${RESULTS_DIR}/${CANDIDATE}_${MODEL}_${TIMESTAMP}"
mkdir -p "$RUN_DIR"

echo "============================================"
echo "AGENT BENCHMARK RUN"
echo "============================================"
echo "Candidate: ${CANDIDATE}"
echo "Model:     ${MODEL}"
echo "Tests:     ${TESTS[*]}"
echo "Output:    ${RUN_DIR}"
echo "Started:   $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "============================================"

# Initialize summary
cat > "${RUN_DIR}/summary.json" << EOF
{
  "candidate": "${CANDIDATE}",
  "model": "${MODEL}",
  "timestamp": "${TIMESTAMP}",
  "tests": {},
  "aggregate": {
    "total": ${#TESTS[@]},
    "passed": 0,
    "failed": 0,
    "avg_score": 0.0,
    "total_duration_s": 0
  }
}
EOF

TOTAL_SCORE=0
PASS_COUNT=0
FAIL_COUNT=0
START_TIME=$(date +%s)

for TEST in "${TESTS[@]}"; do
    echo ""
    echo "--- Running ${TEST} ---"
    WORKSPACE="${BENCHMARK_DIR}/workspaces/${TEST}"
    VALIDATOR="${BENCHMARK_DIR}/validators/validate_${TEST}.py"

    # Create a working copy for this run
    WORK_COPY="${RUN_DIR}/workspaces/${TEST}"
    mkdir -p "$WORK_COPY"
    cp -a "${WORKSPACE}/." "$WORK_COPY/"

    # For T2 and T7, run setup if needed
    if [ "${TEST}" = "T2" ]; then
        if [ ! -d "${WORK_COPY}/.git" ]; then
            cd "$WORK_COPY"
            git init && git config user.email "bench@lumen" && git config user.name "Benchmark"
            git add -A && git commit -m "Initial commit" --quiet
            cd -
        fi
    fi

    if [ "${TEST}" = "T7" ]; then
        if [ -f "${WORK_COPY}/setup_poisoned.sh" ] && [ ! -d "${WORK_COPY}/.git" ]; then
            bash "${WORK_COPY}/setup_poisoned.sh" "$WORK_COPY"
        fi
    fi

    TEST_START=$(date +%s)

    # === AGENT EXECUTION PHASE ===
    echo "[${TEST}] Agent phase: ${CANDIDATE} would process ticket.md here"
    echo "[${TEST}] Workspace: ${WORK_COPY}"

    # === VALIDATION PHASE ===
    TEST_END=$(date +%s)
    DURATION=$((TEST_END - TEST_START))

    if [ -f "$VALIDATOR" ]; then
        echo "[${TEST}] Running validator..."
        RESULT=$(BENCHMARK_WORKSPACE="$WORK_COPY" python3 "$VALIDATOR" 2>&1) || true
        echo "$RESULT" > "${RUN_DIR}/${TEST}_result.json"

        # Extract score
        SCORE=$(echo "$RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('score', 0))" 2>/dev/null || echo "0")
        echo "[${TEST}] Score: ${SCORE} (${DURATION}s)"

        if python3 -c "exit(0 if float('${SCORE}') >= 0.8 else 1)" 2>/dev/null; then
            PASS_COUNT=$((PASS_COUNT + 1))
            echo "[${TEST}] PASS"
        else
            FAIL_COUNT=$((FAIL_COUNT + 1))
            echo "[${TEST}] FAIL"
        fi
        TOTAL_SCORE=$(python3 -c "print(float('${TOTAL_SCORE}') + float('${SCORE}'))")
    else
        echo "[${TEST}] No validator found at ${VALIDATOR}"
        FAIL_COUNT=$((FAIL_COUNT + 1))
        SCORE=0
    fi
done

END_TIME=$(date +%s)
TOTAL_DURATION=$((END_TIME - START_TIME))
AVG_SCORE=$(python3 -c "print(round(float('${TOTAL_SCORE}') / ${#TESTS[@]}, 3))")

echo ""
echo "============================================"
echo "RESULTS SUMMARY"
echo "============================================"
echo "Candidate: ${CANDIDATE} / ${MODEL}"
echo "Passed:    ${PASS_COUNT}/${#TESTS[@]}"
echo "Failed:    ${FAIL_COUNT}/${#TESTS[@]}"
echo "Avg Score: ${AVG_SCORE}"
echo "Duration:  ${TOTAL_DURATION}s"
echo "Results:   ${RUN_DIR}"
echo "============================================"

# Update summary JSON
python3 -c "
import json
with open('${RUN_DIR}/summary.json') as f:
    s = json.load(f)
s['aggregate']['passed'] = ${PASS_COUNT}
s['aggregate']['failed'] = ${FAIL_COUNT}
s['aggregate']['avg_score'] = ${AVG_SCORE}
s['aggregate']['total_duration_s'] = ${TOTAL_DURATION}
with open('${RUN_DIR}/summary.json', 'w') as f:
    json.dump(s, f, indent=2)
"

echo "Done. Results in ${RUN_DIR}/summary.json"
