# dev/retrieval/

## Role
Self-contained retrieval evaluation suite — pipeline modules plus scripts for baseline/sweep/cross-sweep evaluation, ad-hoc mode comparison, and MRL dimension sweeps. Imports pipeline modules from `dev/indexing/`. Touch this when changing retrieval eval methodology or config; not for the production retriever (`src/rag/retriever.py`).

## Public Interface
No `__init__.py` — scripts add `dev/retrieval/` and `dev/indexing/` to `sys.path` and import modules directly, e.g. `import p1_retriever as _retriever`, `from eval_config import BASELINE, SWEEP_RANGES`.

## Flow
`A_retrieval_eval.py` (entry point) reads CLI args → `eval_runner.py` loads queries + runs each query through `p1_retriever.py` → `eval_metrics.py` scores hits against ground truth → `eval_report.py`/`eval_cross_report.py` write Markdown reports to `md/`. `eval_constellation.py` ensures the right GPU server preset is running per mode before queries run.

## Modules

### p1_retriever.py (132 LOC)

**Purpose:** Retrieval primitives (dense, sparse, BM25, hybrid RRF, CC fusion, CC+rerank) against `rag_test`, plus a standalone reranker client.
**Reads:** `rag_test` Postgres via `p4_db.py`; embedding/SPLADE/reranker servers via `p2_embedder.py`/`p3_sparse_embedder.py`/httpx.
**Writes:** nothing.
**Called by:** `A_retrieval_eval.py` (via `eval_runner.py`/`eval_constellation.py`), `A_retrieval_sandbox.py`, `dev/server_management/B_real_smell.py`.
**Calls out:** httpx (rerank endpoint); `p2_embedder.py`, `p3_sparse_embedder.py`, `p4_db.py` (intra-dev).

---

### eval_config.py (31 LOC)

**Purpose:** Config-only module for `A_retrieval_eval.py` — `BASELINE` defaults, `SWEEP_RANGES`, and mode-classification sets (`THRESHOLD_IGNORED_MODES`, `PREFIX_NOOP_MODES`).
**Reads:** nothing.
**Writes:** nothing.
**Called by:** `A_retrieval_eval.py`, `eval_constellation.py`, `eval_runner.py`, `eval_report.py`.
**Calls out:** (none — constants only).

---

### eval_constellation.py (118 LOC)

**Purpose:** Server health checks and GPU constellation lifecycle (start/patch dynamic URLs) for the eval pipeline, keyed by retrieval mode.
**Reads:** health endpoints (embedding/SPLADE/reranker/reranker-8b); `~/.rag-locks/server-port-*.json` state files.
**Writes:** patches `EMBEDDING_URL`/`SPLADE_URL`/`RERANKER_URL` module globals on `p1_retriever`/`p2_embedder`/`p3_sparse_embedder` at runtime.
**Called by:** `A_retrieval_eval.py`, `eval_runner.py`.
**Calls out:** httpx; subprocess (`src.rag.server_manager.ensure_constellation`).

---

### eval_runner.py (150 LOC)

**Purpose:** Load queries, verify no index drift, dispatch a query to the right retrieval mode, and apply score-threshold filtering.
**Reads:** queries JSON file; `rag_test` Postgres (drift check) via `p4_db.py`.
**Writes:** nothing.
**Called by:** `A_retrieval_eval.py`.
**Calls out:** `p1_retriever.py` (intra-dev); `eval_constellation.py` (`_lookup_server_url`); httpx (rerank).

---

### eval_metrics.py (85 LOC)

**Purpose:** Pure metric functions — document/snippet match checking, NDCG@K, MRR@K, Recall@K, and per-run averaging.
**Reads:** in-memory hit lists and ground-truth dicts.
**Writes:** nothing.
**Called by:** `A_retrieval_eval.py`.
**Calls out:** (none — pure Python, math only).

---

### eval_report.py (251 LOC)

**Purpose:** Markdown report writers for baseline and single-parameter sweep runs (per-query detail, aggregate summary, sweep comparison table).
**Reads:** in-memory query-result dicts.
**Writes:** `dev/retrieval/md/eval_<label>_<timestamp>.md`, `dev/retrieval/md/sweep_<param>_<timestamp>.md`.
**Called by:** `A_retrieval_eval.py`.
**Calls out:** (none — pure Python).

---

### eval_cross_report.py (117 LOC)

**Purpose:** Markdown report writer for two-parameter cross-sweep runs (primary + secondary metric matrices, winner summary).
**Reads:** in-memory cross-sweep results dict.
**Writes:** `dev/retrieval/md/cross_<param1>_<param2>_<collection>_<timestamp>.md`.
**Called by:** `A_retrieval_eval.py`.
**Calls out:** (none — pure Python).

---

### A_retrieval_eval.py (181 LOC)

**Purpose:** CLI entry point for baseline / single-sweep / cross-sweep retrieval evaluation against ground truth.
**Reads:** CLI args; queries JSON.
**Writes:** (via `eval_report.py`/`eval_cross_report.py`).
**Called by:** run directly, no importers.
**Calls out:** `eval_config.py`, `eval_constellation.py`, `eval_runner.py`, `eval_metrics.py`, `eval_report.py`, `eval_cross_report.py` (intra-dev).

---

### A_retrieval_sandbox.py (156 LOC)

**Purpose:** Ad-hoc, no-ground-truth retrieval exploration across modes for a list of queries.
**Reads:** CLI args; queries JSON (plain array).
**Writes:** `dev/retrieval/md/retrieval_<collection>_<timestamp>.md`.
**Called by:** run directly, no importers.
**Calls out:** `p1_retriever.py` (intra-dev); httpx (server health checks).

---

### A_mrl_sweep.py (365 LOC)

**Purpose:** Sweep MRL embedding-truncation dimensions to compare dense/hybrid retrieval quality against the full 4096d embedding.
**Reads:** `RAG_MCP_test` Postgres collection (hardcoded); embedding/SPLADE servers.
**Writes:** `dev/retrieval/md/mrl_sweep_<timestamp>.md`.
**Called by:** run directly, no importers.
**Calls out:** `p2_embedder.py`, `p1_retriever.py` (intra-dev); psycopg2, pgvector, numpy, httpx.

---

## State
`rag_test` Postgres `documents` table — read by all retrieval/eval modules via `p4_db.py`/`p1_retriever.py`, never written by this directory. `~/.rag-locks/server-port-*.json` — read by `eval_constellation.py` to resolve dynamic server URLs, never written here (owned by `src/rag/server_utils.py`).
