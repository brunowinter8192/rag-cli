# Indexing Step 3: Sparse Embedding

## Status Quo (IST)

**Code:** `src/rag/sparse_embedder.py` (client), `src/rag/splade_server.py` (server)
**Model:** naver/splade-v3 via sentence-transformers SparseEncoder v5.2.0
**Server:** FastAPI/uvicorn on port 8083 (single worker, synchronous), device auto-detected as MPS (Metal)
**Dimensions:** 30522 (BERT vocabulary size, sparse)
**Storage:** pgvector `sparsevec(30522)` column
**Safety-Net:** `max_active_dims=256` in `splade_server.py:21,55` — caps non-zero elements at 256 (normal output: 100-200 nnz). Uses sentence-transformers' official `select_max_active_dims()` truncation via the `encode()` parameter.

## Evidenz

### SearXNG Hybrid Sweep (30 queries, 2337 chunks)

| Retriever | NDCG@3 | NDCG@10 | Recall@10 |
|-----------|--------|---------|-----------|
| Dense (4096d) | 0.465 | 0.577 | 0.678 |
| Hybrid (RRF) | 0.298 | 0.474 | 0.656 |
| Sparse (SPLADE++) | 0.256 | 0.367 | 0.478 |

Sparse is 45% weaker than Dense. Hybrid is WORSE than Dense alone because SPLADE anti-correlates with correct relevance — its false positives displace Dense's correct results in RRF.

### Root Cause Analysis (ad-hoc investigation, notes preserved inline)

1. **Domain mismatch:** SPLADE++ trained on MS-MARCO (web search). SearXNG corpus is YAML configs, Python API docs, code blocks — completely out-of-domain.
2. **Low activation:** Queries produce only 35-51 non-zero SPLADE dimensions (expected 100-300 on in-domain text).
3. **Subword artifacts:** Technical terms tokenize into ambiguous subwords:
   - "Valkey" → `val`(2.74) + `##key`
   - "Redis" → `red`(2.85) + `##is`
   - "SearXNG" → `sea`(2.44) + `##r` + `##x` + `##ng`
4. **Code chunks:** Zero lexical overlap with query tokens → SPLADE scores near 0 on correct targets.

### Qwen3 Paper Small Dataset (15 queries, 53 chunks)

| Retriever | NDCG@3 |
|-----------|--------|
| Sparse | 0.416 |
| Dense | 0.397 |
| Hybrid | 0.421 |

Sparse performed better on the small academic paper dataset — in-domain for MS-MARCO style text.

## Recommendation (SOLL)

- **Keep:** naver/splade-v3 as sparse component — upgraded from SPLADE++ (naver/splade-cocondenser-ensembledistil); now active in production via sentence-transformers SparseEncoder (no separate `pip install splade` required)
- **Keep:** `max_active_dims=256` safety-net in splade_server.py
- **Pending:** Decision whether to drop Sparse entirely for technical docs (BM25 via tsvector as lightweight alternative)

## Offene Fragen

- **nnz-Corruption Bug:** SPLADE server produces 14k-30k nnz after 8h+ uptime (normal: 100-200). Restart fixes immediately. Root cause unknown — MPS numerical drift is strongest hypothesis. `max_active_dims=256` safety-net prevents pgvector crashes but doesn't explain the cause.
- SPLADE v3 (naver/splade-v3): Better out-of-domain performance? Requires separate library (`pip install splade`), not sentence-transformers compatible.
- Should we drop Sparse entirely for technical docs? BM25 (already in pgvector via tsvector) might be sufficient.
- Domain-specific SPLADE fine-tuning: Is it worth the effort?
- SPLADE server async: Single worker blocks concurrent requests. Not critical if Sparse is dropped.

## Quellen

- RAG Collection: SPLADE_v3_Paper (v3 training improvements, BEIR benchmarks)
- Anthropic contextual-retrieval (BM25 as sparse alternative)
- naver/splade GitHub repo (v3 model availability, custom model classes)
