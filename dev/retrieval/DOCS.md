# dev/retrieval/ — Retrieval Pipeline Dev Suite

Self-contained modules and scripts for retrieval experiments. Imports pipeline modules from `dev/indexing/` (added to `sys.path` automatically).

All scripts run from project root:
```bash
./venv/bin/python dev/retrieval/<script>.py [args]
```

---

## Pipeline Modules

### p1_retriever.py

Imports `p2_embedder`, `p3_sparse_embedder`, `p4_db` from `dev/indexing/` via `sys.path` insert.

| Function | Signature | Description |
|----------|-----------|-------------|
| `retrieve_dense` | `(query, collection, top_k=10, query_prefix=True) -> list[dict]` | Embed query (instruct prefix optional), cosine search |
| `retrieve_sparse` | `(query, collection, top_k=10) -> list[dict]` | SPLADE-embed query, sparse cosine search |
| `retrieve_bm25` | `(query, collection, top_k=10) -> list[dict]` | BM25 full-text search via PostgreSQL tsquery |
| `retrieve_hybrid` | `(query, collection, top_k=10, rrf_k=60, query_prefix=True) -> list[dict]` | Dense + sparse search, RRF fusion |
| `retrieve_cc` | `(query, collection, top_k=10, alpha=0.8, query_prefix=True) -> list[dict]` | Dense + sparse search, Convex Combination fusion |
| `retrieve_cc_rerank` | `(query, collection, top_k=10, alpha=0.8, rerank_candidates=50, query_prefix=True) -> list[dict]` | CC fusion then cross-encoder rerank |
| `rerank` | `(query, results, top_k=10) -> list[dict]` | Cross-encoder rerank via llama-server port 8082 |

**Dense query prefix:** `Instruct: Given a search query, retrieve relevant passages that answer the query\nQuery: `

**query_prefix=False:** passes bare query string to embedder (no instruct prefix). No-op for sparse/bm25 modes.

**Candidates fetched before top_k cutoff:** 50

---

### eval_config.py

Config module for `A_retrieval_eval.py`. Defines `BASELINE` (single-run defaults) and `SWEEP_RANGES` (valid value arrays per sweepable parameter). Import directly — no CLI, no side effects. See `A_retrieval_eval.py` section for full config reference.

---

## Analysis Scripts

### A_retrieval_eval.py

**Purpose:** Evaluate retrieval quality against ground truth documents and snippets. Config-driven via `eval_config.py` — all parameters have BASELINE defaults and SWEEP_RANGES for systematic sweeps. Produces per-run reports with config header, per-query results, and aggregate summary. Sweep mode produces an additional comparison table across all swept values.

**Metrics computed per query + aggregated:**
- `doc_recall` (binary): expected_documents in top-K hits or not
- `snippet_recall` (binary): expected_snippets as substring in any hit's content
- `NDCG@K`: rank-aware, binary relevance (rel=1 if chunk.document ∈ expected_documents)
- `MRR@K`: 1/rank of first relevant hit, 0 if none in top-K
- `Recall@K` (chunk-level): retrieved_relevant / total_relevant_in_collection (via DB query for chunk-counts-per-document)

**Prerequisites:** Embedding server (8081) always. SPLADE (8083) for sparse, hybrid, cc, cc+rerank, hybrid+rerank modes. Reranker (8082) for any mode containing "rerank".

**Config file: `eval_config.py`**

```python
BASELINE = {
    "mode": "cc",         # retrieval mode
    "top_k": 10,          # results returned per query
    "alpha": 0.8,         # CC fusion weight for dense (0–1)
    "rrf_k": 60,          # RRF K constant for hybrid modes
    "score_threshold": 0.0,   # min score filter (0.0 = off); cosine-based modes only
    "query_prefix": True,     # apply instruct prefix to dense embedding; dense-using modes only
}

SWEEP_RANGES = {
    "mode":            ["dense", "sparse", "hybrid", "cc", "cc+rerank", "hybrid+rerank", "bm25"],
    "top_k":           [5, 10, 20],
    "alpha":           [0.5, 0.6, 0.7, 0.8, 0.9],
    "rrf_k":           [30, 60, 90],
    "score_threshold": [0.0, 0.3, 0.5],
    "query_prefix":    [True, False],
}
```

**score_threshold** is applied only for cosine-based modes (dense, sparse, cc, cc+rerank). For rrf/bm25/rerank modes, score scales are not comparable — the threshold is silently ignored and the report header carries a ⚠ note.

**query_prefix** is a no-op for pure sparse/bm25 modes (no dense embedding step). The report header carries a ℹ note when swept over these modes.

**CLI flags:**

| Flag | Default | Description |
|------|---------|-------------|
| `--collection` | `test_db` | Collection name to query |
| `--queries` | `dev/retrieval/queries_test_db.json` | Queries JSON path |
| `--baseline` | — | Single run at BASELINE config (+ any `--override`) |
| `--sweep PARAM` | — | Sweep `PARAM` over `SWEEP_RANGES[PARAM]`; others fixed at BASELINE |
| `--override key=val` | — | Override one BASELINE key; repeatable |

Exactly one of `--baseline` or `--sweep PARAM` is required.

**Queries JSON format:**
```json
{
  "queries": [
    {
      "query": "What embedding dimensions does Qwen3 support?",
      "type": "factual",
      "expected_documents": ["Qwen3_Embedding_Paper"],
      "expected_snippets": ["Matryoshka Representation Learning"]
    }
  ]
}
```

**Output:**
- `A_retrieval_eval_reports/eval_<label>_<timestamp>.md` — per-run report with config table, per-query results, and summary
- `A_retrieval_eval_reports/sweep_<param>_<timestamp>.md` — comparison table across all swept values (only with `--sweep`)

**Usage:**
```bash
# Single run at BASELINE
./venv/bin/python dev/retrieval/A_retrieval_eval.py --baseline

# BASELINE with ad-hoc overrides
./venv/bin/python dev/retrieval/A_retrieval_eval.py --baseline --override mode=dense --override top_k=20

# Sweep a single parameter (others fixed at BASELINE)
./venv/bin/python dev/retrieval/A_retrieval_eval.py --sweep alpha
./venv/bin/python dev/retrieval/A_retrieval_eval.py --sweep mode
./venv/bin/python dev/retrieval/A_retrieval_eval.py --sweep score_threshold

# Sweep with non-default fixed params
./venv/bin/python dev/retrieval/A_retrieval_eval.py --sweep alpha --override top_k=20 --override mode=cc+rerank
```

---

### A_retrieval_sandbox.py

**Purpose:** Explore retrieval results interactively across modes for a set of ad-hoc queries. No ground truth — outputs raw ranked results per query per mode for manual inspection.

**Prerequisites:** Embedding server (8081) always. SPLADE (8083) for sparse, hybrid, cc, cc+rerank, hybrid+rerank modes. Reranker (8082) for any mode containing "rerank".

**CLI flags:**

| Flag | Default | Description |
|------|---------|-------------|
| `--collection` | required | Collection name to query |
| `--queries` | required | Path to JSON file with queries list |
| `--top-k` | `5` | Results per query per mode |
| `--modes` | `dense,sparse,hybrid,cc` | Comma-separated modes |

**Valid modes:** `dense`, `sparse`, `hybrid`, `hybrid+rerank`, `cc`, `cc+rerank`

**Queries JSON format:**
```json
["What embedding dimensions does Qwen3 support?", "How does SPLADE work?"]
```

**Output:** `A_retrieval_sandbox_reports/retrieval_<collection>_<timestamp>.md`
- Per query, per mode: rank/score/document/chunk index with content snippet

**Usage:**
```bash
./venv/bin/python dev/retrieval/A_retrieval_sandbox.py \
    --collection RAG_MCP_test \
    --queries dev/retrieval/queries.json \
    --top-k 5

./venv/bin/python dev/retrieval/A_retrieval_sandbox.py \
    --collection RAG_MCP_test \
    --queries dev/retrieval/queries.json \
    --modes dense,hybrid,cc

./venv/bin/python dev/retrieval/A_retrieval_sandbox.py \
    --collection RAG_MCP_test \
    --queries dev/retrieval/queries.json \
    --modes cc+rerank \
    --top-k 10
```

---

### A_mrl_sweep.py

**Purpose:** Sweep embedding dimensions [256, 512, 768, 1024, 2048, 4096] to evaluate dense and hybrid retrieval quality across MRL truncation levels. Collection and dimensions are hardcoded (`COLLECTION = "RAG_MCP_test"`, `DIMENSIONS = [256, 512, 768, 1024, 2048, 4096]`). Requires full 4096d embeddings already indexed.

**Prerequisites:** Embedding server (8081), SPLADE (8083).

**Output:** `A_mrl_sweep_reports/mrl_sweep_<timestamp>.md`

**Usage:**
```bash
./venv/bin/python dev/retrieval/A_mrl_sweep.py
```

---

## Data Files

### queries_test_db.json (active)

17 queries with ground truth for the `test_db` collection. Default queries-path for `A_retrieval_eval.py`. Format: JSON object with `"queries"` array, each entry has `query`, `type`, `expected_documents`, `expected_snippets`. All snippets grep-verified in source MDs. Query-Mix ist faktual-lastig; conceptual/cross-document Coverage offen (worker-generated baseline, User-Inspection vor authoritative Eval-Execution empfohlen).

### queries_rag_mcp_test.json (historical, retained for reference)

20 queries (8 factual, 7 conceptual, 5 cross-document) for the deprecated `RAG_MCP_test` collection. Collection no longer indexed (April 30 data clean-slate). Nicht in current eval flow.

---

### Current Test Database State

`rag_test` (Postgres) enthält die Collection `test_db` (250 Chunks aus 7 Reference Papers: RAGAS_Evaluation_Framework, RAG_Evaluation_Survey_2025, Pipeline_Optimization, Fusion_Functions_Hybrid_Retrieval, Qwen3_Embedding, SPLADE_v3, Rethinking_Chunk_Size_Long_Document — kopiert aus `data/documents/rag-cli-reference/` und neu indexiert für isolierte Eval). Production-DB `rag` enthält die Live-Collections (RAG-features, RAG-meta, RAG_reference, searxng_reference, Trading, Trading_internal). Strikte Trennung: Eval läuft gegen `rag_test`, prod-rag-cli läuft gegen `rag`.

### Query Coverage

17 Queries in `queries_test_db.json` decken die 7 Reference Papers ab. Alle `expected_snippets` sind grep-verified gegen die Source-MDs. Query-Typen-Verteilung ist faktual-lastig (sehr spezifische Substring-Hits) — möglicher Bias der worker-generierten Baseline-Queries Richtung exact-match.

### Pipeline Coverage / Friction Boundary

Was die Eval heute prüft: alle Retrieval-Knöpfe ohne Re-Indexing-Bedarf — Modi (dense/sparse/hybrid/cc/cc+rerank/hybrid+rerank), Fusion-Parameter (RRF K, CC α), MRL-Dimension via separates Script, plus rank-aware Metriken (NDCG@K, MRR@K, Recall@K).

Was die Eval nicht prüft trotz No-Re-Index-Möglichkeit: BM25/keyword (Code in src/rag/search_primitives.py vorhanden, nicht in p1_retriever.py exposed — wait, BM25 IS jetzt in p1_retriever exposed via `retrieve_bm25`), top_k-Variation reduziert (Production-Clamp auf [12,12]), statistische Signifikanz-Tests, Latency-Tracking.

Was die Eval nicht prüft weil Re-Index nötig: Chunking-Config, Dense-Embedding-Modell, Sparse-Embedding-Modell, Schema-Änderungen.

Wichtig: Eval läuft auf `test_db` (7 reference papers, RAG-internes Methodologie-Material), Production läuft auf live-Collections in `rag`. Eval-Aussagen müssen durch DB-Erweiterung re-validiert werden — siehe `decisions/OldThemes/eval_suite/in_progress.md` für den Erweiterungspfad.
