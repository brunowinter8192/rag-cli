# dev/indexing/

## Role
Self-contained indexing pipeline for dev experiments — chunking, dense/sparse embedding, PostgreSQL storage, and analysis scripts. No imports from `src/rag/`. Touch this when experimenting with indexing config (chunk size, overlap, batch size) outside production; not for the production indexer (`src/rag/indexer.py`).

## Public Interface
No `__init__.py` — scripts add `dev/indexing/` to `sys.path` and import the `pN_*.py` modules directly, e.g. `import p1_chunker as _chunker`.

## Flow
`A_chunking_stats.py` / `A_index_collection.py` read `.md` files from a source directory → `p1_chunker.py` splits into chunks → `p2_embedder.py`/`p3_sparse_embedder.py` embed (dense/sparse) → `p4_db.py` stores in `rag_test` Postgres → `p5_indexer.py` orchestrates chunk+embed+store per file/directory → analysis scripts write Markdown reports to `md/`.

## Modules

### p1_chunker.py (95 LOC)

**Purpose:** Recursive character-split chunker with word-aligned overlap, used by the dev indexing pipeline.
**Reads:** `.md` file content passed in by caller.
**Writes:** nothing (returns chunk dicts).
**Called by:** `A_chunking_stats.py`, `A_index_collection.py`, `p5_indexer.py`.
**Calls out:** (none — pure Python).

---

### p2_embedder.py (40 LOC)

**Purpose:** HTTP client for the dense embedding llama-server endpoint; also provides MRL truncation.
**Reads:** embedding URL env override; llama-server `/v1/embeddings` response.
**Writes:** nothing.
**Called by:** `p5_indexer.py`, `dev/retrieval/eval_constellation.py`, `dev/retrieval/A_mrl_sweep.py`, `dev/server_management/constellation_measure.py` (URL patched at runtime).
**Calls out:** httpx.

---

### p3_sparse_embedder.py (22 LOC)

**Purpose:** HTTP client for the SPLADE sparse embedding server.
**Reads:** SPLADE URL env override; SPLADE server `/v1/sparse-embeddings` response.
**Writes:** nothing.
**Called by:** `p5_indexer.py`, `dev/retrieval/eval_constellation.py` (URL patched at runtime).
**Calls out:** httpx.

---

### p4_db.py (255 LOC)

**Purpose:** PostgreSQL connection, schema, storage, and search primitives (dense/sparse/hybrid/CC fusion) plus the `collections` metadata table for the dev pipeline.
**Reads:** `rag_test` Postgres (documents, collections tables).
**Writes:** `rag_test` Postgres (schema DDL, chunk inserts/deletes, collection metadata upsert).
**Called by:** `p5_indexer.py`, `A_index_collection.py`, `dev/retrieval/p1_retriever.py`, `dev/retrieval/eval_runner.py`, `dev/chunker/A_quote_coverage.py`.
**Calls out:** psycopg2, pgvector.

---

### p5_indexer.py (83 LOC)

**Purpose:** Chunk + parallel-embed (dense+sparse) + store orchestration for a single file or a directory of `.md` files.
**Reads:** `.md` files from disk.
**Writes:** `rag_test` Postgres via `p4_db.py`.
**Called by:** `A_index_collection.py`.
**Calls out:** (none directly — delegates to `p1_chunker`, `p2_embedder`, `p3_sparse_embedder`, `p4_db`).

---

### A_chunking_stats.py (150 LOC)

**Purpose:** Analyze chunking output (size distribution, per-document stats) for a directory of `.md` files — no GPU, DB, or servers needed.
**Reads:** `.md` files from a source directory.
**Writes:** `dev/indexing/md/stats_<collection>_<timestamp>.md`.
**Called by:** run directly, no importers.
**Calls out:** `p1_chunker.py` (intra-dev).

---

### A_index_collection.py (156 LOC)

**Purpose:** Index a directory of `.md` files into the `rag_test` DB, upserting collection metadata on success.
**Reads:** `.md` files from a source directory; embedding (8081) and SPLADE (8083) server health.
**Writes:** `rag_test` Postgres (chunks + collection metadata); `dev/indexing/md/index_<collection>_<timestamp>.md`.
**Called by:** run directly, no importers.
**Calls out:** `p1_chunker.py`, `p4_db.py`, `p5_indexer.py` (intra-dev), httpx.

---

### test_null_embedding_skip.py (64 LOC)

**Purpose:** Verify a chunk with an all-NULL embedding is skipped, counted and logged while other chunks are stored.
**Reads:** `src/rag/indexer.py` (real module, loaded from a per-strand tmp copy of `src/`); in-memory stand-in for the DB connection.
**Writes:** stdout only (PASS/FAIL per strand); exits non-zero on any failed strand.
**Called by:** run directly, no importers.
**Calls out:** `dev/strand_runner.py`.

---

## State
`rag_test` Postgres `documents` and `collections` tables — written by `p4_db.py` (called from `p5_indexer.py`/`A_index_collection.py`), read by `p4_db.py`'s search functions and `dev/retrieval/p1_retriever.py`/`dev/retrieval/eval_runner.py`/`dev/chunker/A_quote_coverage.py`.
