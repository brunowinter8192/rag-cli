# dev/

## Role
Development, evaluation, and profiling scripts for the RAG indexing and retrieval pipelines, organized in pipeline-matching subdirectories plus a handful of standalone diagnostic/test scripts documented directly below. Touch this when adding a dev-only diagnostic; production code lives in `src/rag/`.

## Public Interface
No `__init__.py` — scripts run directly with the project venv: `./venv/bin/python dev/<path>/<script>.py`.

## Flow
Each subdirectory (`chunker/`, `indexing/`, `rag-chunking/`, `retrieval/`, `server_management/`) is self-contained with its own `DOCS.md`. The loose scripts documented here (`error_log/`, `lock_progress/`, `infra/`) read their respective state sources directly and print/write their own reports — no shared flow between them.

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

### infra/test_log_setup.py (58 LOC)

**Purpose:** Verify `log_setup.get_logger` writes to a name-derived file, is idempotent across repeated calls, and gives distinct names distinct files. Logic copied inline (not imported) per the sandbox rule that `dev/` scripts cannot import `src/`.
**Reads:** nothing (tempfile log root, no GPU/DB/network).
**Writes:** stdout only (PASS per check).
**Called by:** run directly, no importers.
**Calls out:** (none — stdlib only; `get_logger` logic inlined from `src/rag/log_setup.py`).

---

### infra/test_retrieval_log.py (130 LOC)

**Purpose:** Verify the search-log record shape (full query, filters, lean per-hit fields), the zero-hit shape, the content-sidecar linkage by id, and that a write failure is reported through a failure callback rather than raised or swallowed. Logic copied inline for the same reason as `test_log_setup.py`.
**Reads:** nothing (tempfile paths, no GPU/DB/network).
**Writes:** stdout only (PASS per check).
**Called by:** run directly, no importers.
**Calls out:** (none — stdlib only; record-building and write logic inlined from `src/rag/retrieval_log.py`).

---

## State
None owned by any of these modules. Full documentation for the five subdirectories lives in their own `DOCS.md`: `chunker/DOCS.md`, `indexing/DOCS.md`, `rag-chunking/DOCS.md`, `retrieval/DOCS.md`, `server_management/DOCS.md`.
