# Historical Eval Setup — March 2026

> **Superseded** — code not in repo, not reproducible. Preserved as historical record only.
> Removed from `decisions/retrieval03_fusion.md` and `decisions/retrieval04_reranking.md` on 2026-05-10
> because the experiments used a now-deleted eval stack (no `A_retrieval_eval.py` equivalent in repo at that time).
> Current reproducible data: RAG_MCP_test sweep (April 2026, 20 queries, 483 chunks).

---

## From retrieval03_fusion.md

### SearXNG (30 queries, 26088 chunks — technical docs, 2026-03-18)

| Retriever | NDCG@3 | NDCG@10 | Recall@10 |
|---|---|---|---|
| Dense (full) | **0.4479** | **0.5619** | **0.6833** |
| Hybrid (RRF K=60) | 0.2469 | 0.3666 | 0.5167 |
| Hybrid+Rerank | 0.3967 | 0.5052 | 0.6444 |
| Sparse (SPLADE++) | 0.0000 | 0.0000 | 0.0000 |

**Hybrid is WORSE than Dense alone.** SPLADE is completely out-of-domain on technical docs (zero matches in 26k chunks). RRF fusion degrades the Dense ranking by mixing in noise. Reranker partially recovers Hybrid (0.247→0.397 NDCG@3) but still worse than pure Dense.

### Qwen3 Paper (15 queries, 66 chunks — academic text, 2026-03-18)

| Retriever | NDCG@3 | NDCG@10 | Recall@10 |
|---|---|---|---|
| Dense (full) | 0.3605 | 0.5102 | 0.7333 |
| Hybrid (RRF K=60) | 0.4168 | 0.5369 | 0.8000 |
| **Hybrid+Rerank** | **0.5538** | **0.6620** | **0.8556** |
| Sparse (SPLADE++) | 0.4273 | 0.5273 | 0.7333 |

On academic text, Hybrid outperforms Dense on Recall@10 (0.80 vs 0.73). Hybrid+Rerank is best overall. SPLADE contributes meaningfully on in-domain text.

---

## From retrieval04_reranking.md

### Reranker Eval (searxng, 30 queries, 26088 chunks — technical docs)

| Retriever | NDCG@3 | NDCG@10 | Recall@10 |
|---|---|---|---|
| Dense (full) | **0.4479** | **0.5619** | **0.6833** |
| Dense+Rerank | 0.3627 | 0.4938 | 0.6333 |
| Dense(1024d)+Rerank | 0.3961 | 0.5016 | 0.6444 |
| Hybrid+Rerank | 0.3967 | 0.5052 | 0.6444 |

**Reranker HURTS on technical docs.** Dense without reranking is best across all metrics. Reranker degrades NDCG@3 by -8.5pp and Recall@10 by -5pp. The 0.6B cross-encoder likely lacks domain knowledge for technical docs (YAML configs, Python API refs, code blocks).

### Reranker Eval (qwen3_paper, 15 queries, 66 chunks — academic text)

| Retriever | NDCG@3 | NDCG@10 | Recall@10 |
|---|---|---|---|
| Dense (full) | 0.3605 | 0.5102 | 0.7333 |
| **Dense+Rerank** | **0.5538** | **0.6620** | **0.8556** |
| Sparse (SPLADE++) | 0.4273 | 0.5273 | 0.7333 |
| Hybrid (RRF K=60) | 0.4168 | 0.5369 | 0.8000 |
| **Hybrid+Rerank** | **0.5538** | **0.6620** | **0.8556** |

**Reranker HELPS massively on academic text.** +19.3pp NDCG@3, +12.2pp Recall@10. Dense+Rerank = Hybrid+Rerank (reranker normalizes input quality). This matches the Pipeline Optimization Paper finding (+9.4pp with BGE reranker).

### Domain Dependency Pattern

Reranker effectiveness is **domain-dependent**, not universally beneficial:
- Academic/natural language text → reranker helps significantly
- Technical docs (code, configs, API refs) → reranker hurts

**Score threshold 0.3:** Not validated. Cross-encoder scores are probabilities (P(yes)/(P(yes)+P(no))). A global threshold is valid for cross-encoders (confirmed by Elastic Docs), but the optimal value needs empirical calibration per domain.
