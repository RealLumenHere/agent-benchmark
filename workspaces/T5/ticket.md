# T5: Failure Recovery — Handle SIGKILL During Long Task

## Task
The script `long_task.py` processes 300 iterations. The test harness will SIGKILL
your process after 30 seconds.

Your job: Make the task recoverable. When killed and restarted, it should resume
from the last checkpoint and complete successfully.

## Requirements
1. Modify `long_task.py` to support graceful recovery after being killed
2. The script already has basic checkpointing — improve it if needed
3. After being killed and restarted, the script must complete all 300 iterations
4. `result.json` must exist at the end with correct totals

## Acceptance Criteria
- Process recovers cleanly after SIGKILL
- No crash/traceback on recovery
- `result.json` shows all 300 iterations completed
- `checkpoint.json` is cleaned up after successful completion
