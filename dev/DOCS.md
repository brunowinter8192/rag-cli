# dev/

## Role
Development, evaluation, and profiling scripts for the RAG indexing and retrieval pipelines, organized in pipeline-matching subdirectories plus a handful of standalone diagnostic/test scripts documented directly below. Touch this when adding a dev-only diagnostic; production code lives in `src/rag/`.

## Public Interface
No `__init__.py` — scripts run directly with the project venv: `./venv/bin/python dev/<path>/<script>.py`.

## Flow
Each subdirectory (`chunker/`, `eval_suite/`, `indexing/`, `rag-chunking/`, `retrieval/`, `server_management/`) is self-contained with its own `DOCS.md`. The loose scripts documented here (`error_log/`, `lock_progress/`, `infra/`) read their respective state sources directly and print/write their own reports — no shared flow between them.

## Modules

### error_log/analyze_errors.py (106 LOC)

**Purpose:** Filter `src/rag/logs/errors.jsonl` to genuine anomaly codes and print a summary + detail view.
**Reads:** `src/rag/logs/errors.jsonl`.
**Writes:** stdout only.
**Called by:** run directly, no importers.
**Calls out:** (none — stdlib only).

---

### lock_progress/test_update_progress_collection.py (59 LOC)

**Purpose:** Verify that `update_progress` writes the `collection` field into the `progress` dict, and that omitting `collection` yields `None`.
**Reads:** `src/rag/lock.py` (real module, loaded from a per-strand tmp copy of `src/`).
**Writes:** stdout only (PASS/FAIL per strand); exits non-zero on any failed strand.
**Called by:** run directly, no importers.
**Calls out:** `strand_runner.py`.

---

### infra/test_log_setup.py (49 LOC)

**Purpose:** Verify `log_setup.get_logger` writes to a name-derived file, is idempotent across repeated calls, and gives distinct names distinct files.
**Reads:** `src/rag/log_setup.py` (real module, loaded from a per-strand tmp copy of `src/`).
**Writes:** stdout only (PASS/FAIL per strand); exits non-zero on any failed strand.
**Called by:** run directly, no importers.
**Calls out:** `strand_runner.py`.

---

### infra/test_retrieval_log.py (115 LOC)

**Purpose:** Verify the search-log record shape (full query, filters, lean per-hit fields), the zero-hit shape, the content-sidecar linkage by id, that a write failure is reported through a failure callback rather than raised or swallowed, and that `known_fingerprints` treats a missing registry file as the silent normal case while any other read failure (corrupt, unreadable) is traced.
**Reads:** `src/rag/retrieval_log.py` (real module, loaded from a per-strand tmp copy of `src/`).
**Writes:** stdout only (PASS/FAIL per strand); exits non-zero on any failed strand.
**Called by:** run directly, no importers.
**Calls out:** `strand_runner.py`.

---

### infra/test_retrieval_config.py (104 LOC)

**Purpose:** Verify quantization extraction on both model-name casings, `context_size_for_preset`'s launch-intent flag reading, model-config building from an in-memory server state, fingerprint determinism, fingerprint sensitivity to the query prefix, and that a redundant field (preset label alone) does not change the fingerprint.
**Reads:** `src/rag/retrieval_config.py`, `src/rag/server_utils.py`, `src/rag/retrieval_log.py` (real modules, loaded from a per-strand tmp copy of `src/`).
**Writes:** stdout only (PASS/FAIL per strand); exits non-zero on any failed strand.
**Called by:** run directly, no importers.
**Calls out:** `strand_runner.py`.

---

### strand_runner.py (61 LOC)

**Purpose:** Shared runner for the `test_*` scripts: runs each test function as an isolated parallel strand in its own process and tmp copy of `src/`.
**Reads:** `src/` (copied per strand into a tmp dir).
**Writes:** stdout (PASS/FAIL per strand, tracebacks of failed strands); exits non-zero if any strand failed.
**Called by:** `infra/test_log_setup.py`, `infra/test_retrieval_config.py`, `infra/test_retrieval_log.py`, `lock_progress/test_update_progress_collection.py`, `rag-chunking/test_overlap_dedup.py`.
**Calls out:** (none — stdlib only).

---

## State
None owned by any of these modules. Full documentation for the six subdirectories lives in their own `DOCS.md`: `chunker/DOCS.md`, `eval_suite/DOCS.md`, `indexing/DOCS.md`, `rag-chunking/DOCS.md`, `retrieval/DOCS.md`, `server_management/DOCS.md`.
