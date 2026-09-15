# dev/

## Role
Development, evaluation, and profiling scripts for the RAG indexing and retrieval pipelines, organized in pipeline-matching subdirectories plus two standalone diagnostic scripts. Touch this when adding a dev-only diagnostic; production code lives in `src/rag/`.

## Public Interface
No `__init__.py` — scripts run directly with the project venv: `./venv/bin/python dev/<path>/<script>.py`.

## Flow
Each subdirectory (`chunker/`, `indexing/`, `rag-chunking/`, `retrieval/`, `server_management/`) is self-contained with its own `DOCS.md`. The two loose scripts documented here read their respective state sources directly and print/write their own reports — no shared flow between them.

## Modules

### error_log/analyze_errors.py (106 LOC)

**Purpose:** Filter `src/rag/logs/errors.jsonl` to genuine anomaly codes and print a summary + detail view.
**Reads:** `src/rag/logs/errors.jsonl`.
**Writes:** stdout only.
**Called by:** run directly, no importers.
**Calls out:** (none — stdlib only).

---

### lock_progress/test_update_progress_collection.py (87 LOC)

**Purpose:** Verify that `update_progress` writes the `collection` field into the `progress` dict, and that omitting `collection` yields `None`.
**Reads:** nothing (tempfile lock path, no GPU/DB/network).
**Writes:** stdout only (PASS per check).
**Called by:** run directly, no importers.
**Calls out:** (none — stdlib only; lock logic inlined from `src/rag/lock.py`).

---

## State
None owned by either module. Full documentation for the five subdirectories lives in their own `DOCS.md`: `chunker/DOCS.md`, `indexing/DOCS.md`, `rag-chunking/DOCS.md`, `retrieval/DOCS.md`, `server_management/DOCS.md`.
