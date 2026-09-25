# dev/infra/

## Role
Tests for the logging and retrieval-configuration infrastructure of the RAG package. Touch this when logger setup, search-log records or configuration fingerprints change; not for the production modules in `src/rag/`.

## Public Interface
No `__init__.py` — run directly: `./venv/bin/python dev/infra/<test>.py`.

## Flow
Each test case runs as an isolated parallel strand via `dev/strand_runner.py`.
The strand loads the real `src/rag` module from a tmp copy of `src/`.
The strand asserts on the module's behaviour.
PASS/FAIL per strand goes to stdout, and the exit code is non-zero if any strand failed.

## Modules

### test_log_setup.py (49 LOC)

**Purpose:** Verify the logger factory writes to a name-derived file, is idempotent across repeated calls, and gives distinct names distinct files.
**Reads:** `src/rag/log_setup.py` (real module, loaded from a per-strand tmp copy of `src/`).
**Writes:** stdout only (PASS/FAIL per strand); exits non-zero on any failed strand.
**Called by:** run directly, no importers.
**Calls out:** `dev/strand_runner.py`.

---

### test_retrieval_log.py (115 LOC)

**Purpose:** Verify search-log record shape, sidecar linkage, reporting of write failures, and silent handling of a missing config registry versus traced read failures.
**Reads:** `src/rag/retrieval_log.py` (real module, loaded from a per-strand tmp copy of `src/`).
**Writes:** stdout only (PASS/FAIL per strand); exits non-zero on any failed strand.
**Called by:** run directly, no importers.
**Calls out:** `dev/strand_runner.py`.

---

### test_retrieval_config.py (104 LOC)

**Purpose:** Verify quantization extraction, context-size lookup, model-config building and the fingerprint's determinism, prefix sensitivity and insensitivity to redundant fields.
**Reads:** `src/rag/retrieval_config.py`, `src/rag/server_utils.py`, `src/rag/retrieval_log.py` (real modules, loaded from a per-strand tmp copy of `src/`).
**Writes:** stdout only (PASS/FAIL per strand); exits non-zero on any failed strand.
**Called by:** run directly, no importers.
**Calls out:** `dev/strand_runner.py`.

---

## State
None owned.
