# SPLADE Server Scope — required_for fix (2026-05-30)

## Problem
`workflow.py index-dir` started the SPLADE server (port 8083) although indexing uses dense embeddings only. Observed via the GPU monitor during a `github_issues` index run.

## Root cause
`SERVERS["splade"]["required_for"] = ["search", "index"]` in `src/rag/server_utils.py`. `ensure_ready("index")` (called by `workflow.py index-dir`) starts every default-variant preset whose `required_for` contains the op → splade pulled in for both index and search.

## Evidence splade is used for NEITHER (index nor retrieval)
- Indexing: `index_json_workflow` (`indexer.py`) calls `embed_workflow` (dense) only; `store_chunks` inserts `sparse_embedding = NULL` for new chunks. Sparse embeddings are created ONLY by the separate `backfill_splade_workflow`.
- Retrieval: grep `sparse` across `src/rag` → matches only `indexer.py` / `sparse_embedder.py` / `splade_server.py` / `server_lifecycle.py`. NO search / fusion / retriever module references `sparse_embedding` or `sparse_embed_workflow`. `sparse_embed_workflow` is called only by backfill (`indexer.py:115`).
- So splade serves only the explicit `backfill-splade` command, which calls `ensure_ready("splade")` (direct preset path — independent of `required_for`).

## Fix
`server_utils.py`: splade `required_for: ["search","index"]` → `[]`. Verified: `ensure_ready("index")` and `ensure_ready("search")` now select only `embedding-8b`; `splade.required_for == []`. `backfill-splade` unaffected (direct path). Effective immediately (config is re-imported per CLI invocation).

## Server-by-op (post-fix)
- index → embedding-8b (dense only)
- search → embedding-8b (reranker only when rerank requested: reranker `required_for: ["rerank"]`)
- rerank → reranker
- splade → only explicit `server start splade` / `backfill-splade`

## If splade is ever wired into hybrid retrieval
Re-add the relevant op to `splade.required_for` at that point. Currently no search/fusion path uses it.
