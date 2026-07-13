# Retrieval Sweep: rerank_candidates

**Swept:** `rerank_candidates` over `[20, 30, 40, 50]`
**Fixed (BASELINE):** collection=test_db, mode=dense+rerank-0.6b, top_k=12, alpha=0.8, rrf_k=60, score_threshold=0.0, query_prefix=True
**Timestamp:** 20260525_211134

| rerank_candidates | Mode | Doc Recall | Snippet Recall | NDCG@K | MRR@K | Recall@K | Latency (mean_ms) |
|------------------|------|-----------|----------------|--------|-------|---------|-----------------|
| 20 | dense+rerank-0.6b | 100% | 94% | 0.661 | 0.629 | 94.1% | 2828ms |
| 30 | dense+rerank-0.6b | 100% | 97% | 0.667 | 0.627 | 97.1% | 4539ms |
| 40 | dense+rerank-0.6b | 100% | 97% | 0.665 | 0.626 | 97.1% | 6276ms |
| 50 | dense+rerank-0.6b | 100% | 97% | 0.665 | 0.626 | 97.1% | 7228ms |
