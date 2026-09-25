# dev/error_log/

## Role
Diagnostic script over the server error log. Touch this when the anomaly-code set or the error-log format changes; not for writing error entries, which lives in `src/rag/error_log.py`.

## Public Interface
No `__init__.py` — run directly: `./venv/bin/python dev/error_log/analyze_errors.py`.

## Flow
Reads `src/rag/logs/errors.jsonl`.
Filters the entries to the genuine anomaly codes defined in `src/rag/error_log.py`.
Prints a summary and a detail view to stdout.

## Modules

### analyze_errors.py (107 LOC)

**Purpose:** Filter `src/rag/logs/errors.jsonl` to genuine anomaly codes and print a summary and detail view.
**Reads:** `src/rag/logs/errors.jsonl`.
**Writes:** stdout only.
**Called by:** run directly, no importers.
**Calls out:** `src/rag/error_log.py` (anomaly code set and log path, loaded via `importlib`).

---

## State
None owned.
