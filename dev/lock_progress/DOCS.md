# dev/lock_progress/

## Role
Test for the progress tracking of the global RAG lock. Touch this when the lock progress record changes; not for the lock itself, which lives in `src/rag/lock.py`.

## Public Interface
No `__init__.py` — run directly: `./venv/bin/python dev/lock_progress/test_update_progress_collection.py`.

## Flow
Each test case runs as an isolated parallel strand via `dev/strand_runner.py` → loads the real lock module from a tmp copy of `src/` → asserts on a tmp lock file → PASS/FAIL per strand on stdout.

## Modules

### test_update_progress_collection.py (59 LOC)

**Purpose:** Verify that the progress update writes the `collection` field into the progress record, and that omitting it yields `None`.
**Reads:** `src/rag/lock.py` (real module, loaded from a per-strand tmp copy of `src/`).
**Writes:** stdout only (PASS/FAIL per strand); exits non-zero on any failed strand.
**Called by:** run directly, no importers.
**Calls out:** `dev/strand_runner.py`.

---

## State
None owned.
