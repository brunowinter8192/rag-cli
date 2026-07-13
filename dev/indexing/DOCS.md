# dev/indexing/ — Indexing Pipeline Dev Suite

Self-contained modules and scripts for indexing experiments. No imports from `src/rag/`. DB: `rag_test` (never `rag`). Vector dim: 4096 in DB; MRL truncation only on-the-fly via `A_mrl_sweep.py` or the `truncate_mrl` helper in `p2_embedder.py`.

All scripts run from project root:
```bash
./venv/bin/python dev/indexing/<script>.py [args]
```

**Note:** If `rag_test` already has a `documents` table with `vector(4096)` from other tools, drop it first:
```bash
docker exec rag-postgres psql -U rag -d rag_test -c "DROP TABLE IF EXISTS documents;"
```

---

## Pipeline Modules

Prefixed `pN_` to indicate pipe position. Scripts add `dev/indexing/` to `sys.path` and import these directly.

### p1_chunker.py

| Function | Signature | Description |
|----------|-----------|-------------|
| `chunk_file` | `(path, chunk_size=None, overlap=None) -> list[dict]` | Load file, chunk, return dicts with `content`, `document`, `chunk_index`, `total_chunks` |
| `chunk_text` | `(text, chunk_size=None, overlap=None) -> list[str]` | Recursive character split with overlap |

### p2_embedder.py

| Function | Signature | Description |
|----------|-----------|-------------|
| `embed` | `(texts, prefix=None) -> list[list[float]]` | HTTP POST to llama-server port 8081, returns full 4096d vectors |
| `truncate_mrl` | `(embeddings, dims=1024) -> list[list[float]]` | Truncate to first N dims + L2 renormalize |

### p3_sparse_embedder.py

| Function | Signature | Description |
|----------|-----------|-------------|
| `embed_sparse` | `(texts) -> list[dict]` | HTTP POST to SPLADE server port 8083, returns `{indices, values}` dicts |

### p4_db.py

| Function | Signature | Description |
|----------|-----------|-------------|
| `get_connection` | `(db_name="rag_test") -> conn` | psycopg2 connection, creates pgvector extension before registering |
| `ensure_schema` | `(conn, vector_dim=4096)` | Creates `documents` table with `vector(4096)` + `sparsevec(30522)` if not exists |
| `ensure_collections_schema` | `(conn)` | Creates `collections` metadata table if not exists (idempotent) |
| `upsert_collection_metadata` | `(conn, name, embedding_model, embedding_dims, sparse_model, chunk_size, overlap, db_name, indexed_at, doc_count, chunk_count, notes=None)` | INSERT … ON CONFLICT DO UPDATE for collection indexing config; called by `A_index_collection.py` after each full index run |
| `clear_collection` | `(conn, collection) -> int` | DELETE all chunks for collection, returns count |
| `store_chunks` | `(conn, chunks, embeddings, sparse_embeddings)` | Bulk INSERT chunks with both embedding types |
| `search_dense` | `(conn, query_embedding, collection, top_k) -> list[dict]` | Cosine distance on `vector` column |
| `search_sparse` | `(conn, query_sparse, collection, top_k) -> list[dict]` | Cosine distance on `sparsevec` column |
| `search_hybrid` | `(conn, dense_results, sparse_results, rrf_k=60) -> list[dict]` | Reciprocal Rank Fusion of two result lists |
| `search_cc` | `(conn, dense_results, sparse_results, alpha=0.7) -> list[dict]` | Convex Combination fusion with min-max normalization |

### p5_indexer.py

| Function | Signature | Description |
|----------|-----------|-------------|
| `index_file` | `(md_path, collection, db_conn) -> int` | Chunk + parallel embed (dense+sparse) + store (full 4096d); no MRL truncation in index path |
| `index_directory` | `(dir_path, collection, db_conn) -> dict` | Index all `.md` files; returns `{files, chunks, errors, per_file, elapsed}` |

### Config Defaults

| Parameter | Value |
|-----------|-------|
| CHUNK_SIZE | 2000 chars |
| OVERLAP | 400 chars |
| MRL dims | Not applied at index time; `truncate_mrl` available on-the-fly (`p2_embedder.py`) |
| Batch size | 32 |
| DB | rag_test, port 5433, user rag |

---

## A_chunking_stats.py

**Purpose:** Analyze chunking output — no GPU, no DB, no servers needed.

**CLI flags:**

| Flag | Default | Description |
|------|---------|-------------|
| `--source-dir` | required | Directory with `.md` files |
| `--chunk-size` | 2000 | Chunk size in chars |
| `--overlap` | 400 | Overlap in chars |

**Output:** `md/stats_<collection>_<timestamp>.md`
- Config (chunk_size, overlap, separators)
- Per-document table: filename, file_size_chars, num_chunks, avg/min/max chunk size
- Summary: total docs, total chunks, overall avg/min/max
- Distribution: chunk counts per size bucket (0-500, 500-1000, 1000-1500, 1500-2000, 2000+)

**Usage:**
```bash
./venv/bin/python dev/indexing/A_chunking_stats.py \
    --source-dir data/documents/RAG_MCP_test

./venv/bin/python dev/indexing/A_chunking_stats.py \
    --source-dir data/documents/RAG_MCP_test \
    --chunk-size 1000 --overlap 200
```

---

## A_index_collection.py

**Purpose:** Index a directory of `.md` files into `rag_test` DB.

**Prerequisites:** Embedding server (port 8081) + SPLADE server (port 8083) running (`./start.sh`).

**CLI flags:**

| Flag | Default | Description |
|------|---------|-------------|
| `--source-dir` | required | Directory with `.md` files |
| `--collection` | source-dir basename | Collection name in DB |
| `--chunk-size` | 2000 | Chunk size in chars |
| `--overlap` | 400 | Overlap in chars |

**Output:** `md/index_<collection>_<timestamp>.md`
- Config (chunk_size, overlap, MRL dims, batch_size)
- Per-document table: filename, chunks, avg chunk size
- Summary: total docs, total chunks, total time, throughput (chunks/sec), error count

After each successful index run the script upserts a row into the `collections` table in `rag_test` via `p4_db.upsert_collection_metadata`. Model/dims/sparse constants (`EMBEDDING_MODEL`, `EMBEDDING_DIMS`, `SPARSE_MODEL`) are defined in INFRASTRUCTURE; `doc_count`/`chunk_count` come from the `stats` dict returned by `index_directory()`.

**Usage:**
```bash
./venv/bin/python dev/indexing/A_index_collection.py \
    --source-dir data/documents/RAG_MCP_test \
    --collection RAG_MCP_test

./venv/bin/python dev/indexing/A_index_collection.py \
    --source-dir data/documents/RAG_MCP_test \
    --collection RAG_MCP_small \
    --chunk-size 500 --overlap 100
```
