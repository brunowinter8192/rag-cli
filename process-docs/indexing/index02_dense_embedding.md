# Indexing Step 2: Dense Embedding

## State (as of 2026-05-06)

**Code:** `src/rag/embedder.py`
**Model:** Qwen3-Embedding-8B Q8_0 (~9 GB GGUF)
**Server:** llama-server on port 8081
**Dimensions:** 4096d (full model output)
**MRL Support:** Yes (Matryoshka — truncate to first N dims + L2 normalize)
**Max Tokens:** 4000 (~12000 chars) per text, truncated before sending
**Query Prefix:** `Instruct: Given a search query, retrieve relevant passages that answer the query\nQuery: `

**Server Config (optimized 2026-03-15):**
```
-c 2048 -np 1 -b 4096 -ub 4096 -ngl 99
```

| Flag | Value | Why |
|------|-------|-----|
| `-c` | 2048 | Context per slot. Chunks max ~400 tokens. Saves ~30% RAM vs default 32768. |
| `-np` | 1 | Single slot. We embed sequentially, no concurrent queries during indexing. |
| `-b` | 4096 | Logical batch size. |
| `-ub` | 4096 | Physical batch size. `-ub 512` crashes llama-server v638 on Metal (Segfault after ~30 tasks). |
| `-ngl` | 99 | Full GPU offload. |

**Indexing Throughput:** ~20s per 32-chunk batch, ~1.2 chunks/sec.

**Indexing Prefix:** `parallel_embed` (in `indexer.py`) sends every chunk with the prefix `search_document: ` — required by Qwen3-Embedding-8B's task-aware tokenizer. Without the prefix, ~3-4% of code-heavy chunks silently produce all-None embeddings (tokenizer edge case at chunk boundaries that start with bare `import` etc.). Fix landed 2026-05-06 (NULL-embedding tokenizer bug).

**Indexing Visibility:** `cli.py index` prints `(N NULL skipped)` suffix per batch if any chunk's embedding fails to materialize. Operator-visible at run-time. Should be 0 with the prefix fix; non-zero indicates a new content pattern or model regression.

## Evidence

### MRL Dimension Sweep (Qwen3_Embedding_Paper, 15 queries, 53 chunks)

Script: `dev/retrieval/A_mrl_sweep.py`. Report: `dev/retrieval/md/mrl_sweep_20260407_215137.md`.

| Dims | NDCG@3 | NDCG@10 | Recall@10 |
|------|--------|---------|-----------|
| 256 | 0.4641 | 0.6152 | 0.8444 |
| 512 | 0.4207 | 0.5400 | 0.7778 |
| 1024 | 0.4387 | 0.5695 | 0.8111 |
| 2048 | 0.3810 | 0.5495 | 0.8111 |
| 4096 (full) | 0.3966 | 0.5277 | 0.7556 |

256d outperforms 4096d on this small dataset (66 chunks). Validated on larger collection below.

### MRL Dimension Sweep (searxng, 30 queries, 26088 chunks)

Script: `dev/retrieval/A_mrl_sweep.py`. Report: same `mrl_sweep_20260407_215137.md` (multi-collection run).

| Dims | NDCG@3 | NDCG@10 | Recall@10 |
|------|--------|---------|-----------|
| 256 | 0.3840 | 0.5040 | 0.6500 |
| 512 | 0.4098 | 0.5420 | 0.6944 |
| **1024** | **0.4439** | **0.5687** | **0.7278** |
| 2048 | 0.4432 | 0.5747 | 0.7278 |
| 4096 (full) | 0.4479 | 0.5619 | 0.6833 |

**1024d is the sweet spot on large collections.** Best Recall@10 (0.7278, tied with 2048d, better than full). NDCG@10 best at 1024d (0.5687 > full 0.5619). Full 4096d loses Recall — likely noise from unused dimensions hurting cosine similarity. 256d loses ~12% Recall vs 1024d — too much for production. 2048d ≈ 1024d — no gain from extra dims.

**HNSW now possible:** 1024d < 2000d pgvector HNSW limit for `vector` type.

Method: Corpus embeddings loaded from DB (no re-embedding), MRL truncation + L2 renormalization in numpy. Query embeddings via llama-server.

### Server Config Benchmark (historical benchmark, script no longer in repo)

| Config | 32 chunks | Notes |
|--------|-----------|-------|
| Original (-ub 4096, no -c, no -np) | 19.08s | 13+ GB RAM |
| Optimized (-c 2048, -np 1) | 20.37s | 9.2 GB RAM |
| With -ub 512 | CRASH | Segfault on Metal, llama.cpp v638 |

### -ub 512 Bug

llama.cpp v638 crashes on Metal/M4 Pro when `-ub 512` with Qwen3-Embedding-8B. Segfault without error log, server dies after ~30 tasks. Workaround: keep `-ub 4096`.

## Recommendation

- **Keep:** 4096d in storage permanently — MRL is one-way: truncation 4096→1024 is always available; promoting 1024→4096 requires full re-embedding. Storage format frozen at 4096d.
- **Keep:** MRL truncation available on-the-fly — `truncate_mrl(embeddings, dims=1024)` in `dev/indexing/p2_embedder.py`; `dev/retrieval/A_mrl_sweep.py` provides the sweep utility. Apply at query time or eval time without touching the index. The MRL Sweet Spot Evidence (1024d best Recall@10, see Evidence) justifies availability, not migration.
- **Keep:** Qwen3-Embedding-8B Q8_0 — still #1 MTEB Multilingual
- **Keep:** Server config `-c 2048 -np 1 -b 4096 -ub 4096 -ngl 99`
- **Pending:** Contextual Embeddings (Anthropic) — not evaluated
- **Pending:** ColBERT / latency-driven Query-Time MRL — if future ColBERT integration or latency requirements arise, revisit query-time dimension reduction.

## Open Questions

- Newer llama.cpp version: Does it fix the -ub 512 crash?
- Contextual Embeddings (Anthropic): Prepend document context to each chunk before embedding. 49-67% fewer retrieval failures claimed.

## Sources

- RAG Collection: Qwen3_Embedding_Paper (MRL support, model architecture)
- Anthropic contextual-retrieval (Contextual Embedding concept)
- Voyage context-3 (native contextual embedding model)
- Late Chunking (Weaviate — alternative to contextual embedding)
- llama-server README: github.com/ggml-org/llama.cpp/tree/master/tools/server
