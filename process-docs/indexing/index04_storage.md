# Storage (pgvector)

## Status Quo (IST)

- PostgreSQL 18 with pgvector extension (`vector` + `sparsevec` types)
- `documents` table schema:
  - `embedding vector(4096)` — Qwen3-Embedding-8B dense vectors
  - `sparse_embedding sparsevec(30522)` — SPLADE sparse vectors
- Sequential scan for both dense and sparse search (no index)
- HNSW index skipped: pgvector limits HNSW to 2000 dimensions, Qwen3 embeddings have 4096
- Sequential scan sufficient for current scale (<100k vectors)
- Code path: `src/rag/indexer.py` (schema creation, lines 155-172)
- Delete path: `delete_workflow()` clears `documents` (via `delete_chunks()`), `indexed_files` (via `delete_manifest_rows()`), and on-disk source files; `--collection` required; `--document` without `--collection` raises `ValueError`; collection-wide: `shutil.rmtree(coll_dir)`; per-document: removes `.md` + `.json` sidecar (`md_path.with_suffix('.json')`)

## Evidenz

No benchmarks run. Sequential scan latency acceptable at current corpus size.

## Recommendation (SOLL)

Pending — needs evaluation. Relevant when corpus exceeds ~50k vectors and query latency becomes noticeable.

## Offene Fragen

- At what corpus size does sequential scan become a bottleneck?
- Are there pgvector alternatives that support HNSW at 4096 dimensions?
- Would dimension reduction (e.g., Matryoshka) enable HNSW while preserving retrieval quality?

## Quellen

None yet.
