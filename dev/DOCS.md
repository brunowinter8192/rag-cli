# dev/

## Role
Development, evaluation, and profiling scripts for the RAG indexing and retrieval pipelines, organized in subdirectories that each carry their own DOCS.md, plus the shared test runner documented below. Touch this when adding a dev-only diagnostic; production code lives in `src/rag/`.

## Public Interface
No `__init__.py` — scripts run directly with the project venv: `./venv/bin/python dev/<path>/<script>.py`.

## Flow
Each subdirectory (`chunker/`, `error_log/`, `eval_suite/`, `indexing/`, `infra/`, `lock_progress/`, `rag-chunking/`, `retrieval/`, `server_management/`) is self-contained with its own `DOCS.md`. The `test_*` scripts in `infra/`, `lock_progress/`, `rag-chunking/`, `server_management/` and `indexing/` share `strand_runner.py`, which runs each test case as an isolated parallel strand.

## Modules

### strand_runner.py (74 LOC)

**Purpose:** Shared runner for the `test_*` scripts: runs each test function as an isolated parallel strand in its own process and tmp copy of `src/`.
**Reads:** `src/` (copied per strand into a tmp dir).
**Writes:** stdout (PASS/FAIL per strand, tracebacks of failed strands); exits non-zero if any strand failed.
**Called by:** `infra/test_log_setup.py`, `infra/test_retrieval_config.py`, `infra/test_retrieval_log.py`, `lock_progress/test_update_progress_collection.py`, `rag-chunking/test_overlap_dedup.py`, `lock_progress/test_stale_lock_cleanup.py`, `server_management/test_start_all_failure_logged.py`, `indexing/test_null_embedding_skip.py`.
**Calls out:** (none — stdlib only).

---

## State
None owned.
