# dev/rag-chunking/

## Role
Measurement and regression scripts for `expand_chunks`'s overlap deduplication (`merge_chunks` + `find_overlap` in `src/rag/retriever.py`). Touch this when investigating or re-verifying chunk-boundary overlap dedup; not for the chunker or retriever implementations themselves.

## Public Interface
No `__init__.py` — run directly: `./venv/bin/python dev/rag-chunking/A_overlap_match_probe.py`, `./venv/bin/python dev/rag-chunking/test_overlap_dedup.py`.

## Flow
`A_overlap_match_probe.py` reads real chunk pairs from the prod `rag` DB (read-only).
It measures the chunk-overlap match length under three variants and writes a distribution report to `md/`.
`test_overlap_dedup.py` builds chunk chains in memory via the real chunker.
It asserts the overlap-dedup behavior of the production retrieval code and prints PASS/FAIL per parallel strand.

## Modules

### A_overlap_match_probe.py (228 LOC)

**Purpose:** Measure chunk-overlap match length under three variants (pre-fix cap, raised cap, raised cap + whitespace-tolerant) across real adjacent chunk pairs, and report the distribution.
**Reads:** `src/rag/db.py` and `src/rag/retriever.py` (loaded dynamically via `importlib`); PostgreSQL `documents` table (prod `rag` DB, read-only).
**Writes:** `dev/rag-chunking/md/probe_output_<timestamp>.md`.
**Called by:** run directly, no importers.
**Calls out:** `src/rag/db.py`, `src/rag/retriever.py` (loaded dynamically, not a static import).

---

### test_overlap_dedup.py (83 LOC)

**Purpose:** Pins the overlap-dedup fix in `src/rag/retriever.py` (overlap bound, chunk-merge separator behavior) against the real chunker, in-memory.
**Reads:** `src/rag/chunker.py` and `src/rag/retriever.py` (real modules, loaded from a per-strand tmp copy of `src/`).
**Writes:** stdout only (PASS/FAIL per strand); exits non-zero on any failed strand.
**Called by:** run directly, no importers.
**Calls out:** `dev/strand_runner.py`.

---

## State
None owned. `A_overlap_match_probe.py` reads prod `rag` DB state but never writes to it. `test_overlap_dedup.py` is fully in-memory, no external state.
