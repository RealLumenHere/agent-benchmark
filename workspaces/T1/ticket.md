# T1: Filesystem IO — Syslog Analysis

## Task
Parse the file `syslog.log` in this workspace and produce a JSON report at `report.json` containing:

1. Total number of lines
2. Count of each log level (ERROR, WARN, INFO, DEBUG)
3. Top 3 services by ERROR count
4. Time range (earliest and latest timestamp)

## Acceptance Criteria
- `report.json` must exist and be valid JSON
- ERROR count must match the actual count in the file
- All four log levels must be represented in the output
