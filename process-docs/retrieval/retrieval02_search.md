# Retrieval Step 2: Vector Search

## Status Quo (IST)

**Code:** `src/rag/search_primitives.py:search_vectors()`, `bm25_search()` (called via `retriever.py` imports)
**Dense Search:** pgvector cosine distance (`embedding <=> query::vector`) — active prod path via `search_hybrid_workflow`
**BM25 Search:** PostgreSQL tsvector full-text search (`ts_rank`) — available but not exposed in prod CLI
**Sparse (SPLADE) Search:** splade_search removed from `search_primitives.py` (2026-05-26, commit `f8f35c0`). `sparse_embedding` column retained in schema; existing values preserved; new chunks get NULL. `sparse_embed_workflow` still importable via `sparse_embedder.py` for `backfill_splade_workflow` (manual maintenance only).
**Index:** Sequential scan (no HNSW). GIN index on tsvector column.

**Candidates:** `RERANK_CANDIDATES = 30` dense candidates fetched for prod path (always-rerank)

### Why No HNSW Index

pgvector HNSW supports max 2000 dims for `vector` type, max 4000 dims for `halfvec`. Our embeddings are 4096d `vector` — exceeds both limits.

Options to enable HNSW:
1. MRL to 2000d or less → standard HNSW
2. MRL to 4000d or less → halfvec HNSW
3. pgvector future version raises limit

## Evidenz

No isolated search benchmark. Search performance is measured implicitly through eval suite.

At current scale (~7000 chunks across all collections), sequential scan is fast enough (<100ms per query). HNSW becomes critical at 100k+ chunks.

## Recommendation (SOLL)

Pending — HNSW evaluation blocked on MRL migration.

## Offene Fragen

- pgvector 0.8 iterative scans: 5.7x faster for filtered searches. Are we on 0.8? (Yes, 0.8.2)
- HNSW tuning (m, ef_construction, ef_search) — relevant only after MRL enables it
- At what collection size does sequential scan become unacceptable? Need to benchmark.

## Quellen

- AWS pgvector 0.8 blog (iterative scans, filtered search improvements)
- HNSW at scale (TDS — degradation patterns at scale)
- CrunchyData HNSW tuning guide (m, ef_construction, ef_search)
- ColBERT + pgvector (VectorChord — MaxSim in PostgreSQL)
