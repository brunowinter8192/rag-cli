# dev/server_management/

## Role
Measurement scripts for GPU server constellation performance profiling on M4 Pro — VRAM footprint, cold/warm query latency, timeout rate. Touch this when re-measuring constellation performance for exclusivity decisions; not for the production server lifecycle (`src/rag/server_lifecycle.py`, `server_utils.py`, `server_manager.py`).

## Public Interface
No `__init__.py` — scripts add their own directory to `sys.path` implicitly (same-directory sibling imports) and import `constellation_measure` directly.

## Flow
`A_constellation_profile.py` / `B_real_smell.py` ensure a server constellation is running (subprocess call into `src.rag.server_manager`) → `constellation_measure.py` samples VRAM from server logs and runs cold/warm synthetic (or real, for `B_real_smell.py`) queries → results are written to a Markdown report under `md/`.

## Modules

### constellation_measure.py (125 LOC)

**Purpose:** VRAM sampling (Metal log parsing, `system_profiler`) and synthetic embed/rerank query load generation with latency-percentile stats.
**Reads:** `~/.rag-locks/server-port-*.json` state files and their referenced llama-server logs; `system_profiler SPDisplaysDataType`.
**Writes:** nothing.
**Called by:** `A_constellation_profile.py`.
**Calls out:** httpx, subprocess.

---

### A_constellation_profile.py (287 LOC)

**Purpose:** Profile one or all 8 defined GPU server constellations end-to-end (VRAM, cold/warm latency, timeouts) and write a comparison report.
**Reads:** CLI args; `~/.rag-locks/server-port-*.json` state files (health/URL resolution).
**Writes:** `dev/server_management/md/profile_<timestamp>.md`.
**Called by:** run directly, no importers. **Not to be executed casually — profiling run, see module usage note.**
**Calls out:** `constellation_measure.py` (intra-dev); httpx, subprocess (`src.rag.server_manager.ensure_constellation`).

---

### B_real_smell.py (356 LOC)

**Purpose:** Real-data smell test across 6 server constellations using actual retrieved `test_db` chunks (not synthetic) for realistic rerank load.
**Reads:** `dev/retrieval/queries_test_db.json`; `~/.rag-locks/server-port-*.json` state files.
**Writes:** `dev/server_management/md/smell_<timestamp>.md`.
**Called by:** run directly, no importers.
**Calls out:** `dev/retrieval/p1_retriever.py`, `dev/indexing/p2_embedder.py`, `dev/indexing/p3_sparse_embedder.py` (intra-dev, URL-patched at runtime); httpx, subprocess.

---

## State
None owned. All three modules read `~/.rag-locks/server-port-*.json` (owned by `src/rag/server_utils.py`) and write only report files under `md/`.
