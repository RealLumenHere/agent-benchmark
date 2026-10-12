#!/usr/bin/env python3
import json, sys
candidate, model, test, duration, score, ts_now, outpath = sys.argv[1:8]
result = {
    "candidate": candidate,
    "model": model,
    "test": test,
    "duration_s": int(duration),
    "score": float(score),
    "passed": float(score) >= 0.8,
    "timestamp": ts_now
}
with open(outpath, "w") as f:
    json.dump(result, f, indent=2)
print(json.dumps(result))
