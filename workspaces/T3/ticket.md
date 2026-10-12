# T3: Bug Fix — Fix Flask App

## Task
The Flask application in `app.py` has 3 bugs that prevent it from working correctly.
Fix all bugs so that `test_app.py` passes with pytest.

## Known Issues
1. The app crashes on startup
2. The `/api/greet` endpoint throws an error
3. The `/api/log` endpoint has a resource leak

## Requirements
- Fix all 3 bugs with minimal changes
- All tests in `test_app.py` must pass
- Do not change test_app.py or config.json
- Keep the fix as small as possible (minimal diff)

## Acceptance Criteria
- `pytest test_app.py` passes all 4 tests
- The diff is minimal (ideally < 10 lines changed)
