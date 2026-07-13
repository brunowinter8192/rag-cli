# Retrieval Step 3: Ranking & Fusion

## Status Quo (IST)

`cc_fusion` and `rrf_fusion` are **no longer in the production search path**. `fusion.py` deleted (2026-05-26, commit `f8f35c0`). `search_hybrid_workflow()` in `src/rag/retriever.py` is now unconditionally dense+rerank — no fusion step.

Both `cc_fusion` and `rrf_fusion` had zero callers in `src/` after the always-rerank migration. The cc-fusion path (`rerank=False` branch) was removed in full — no dev/ scaffold copies exist either. `search_workflow()` (pure dense, no fusion) is unchanged.

**Historical IST (superseded):** cc_fusion (CC α=0.8, HYBRID_CANDIDATES=50) was the default in `search_hybrid_workflow(rerank=False)`. Evidenz for that choice is preserved below. Superseded values and the code-drift closure are in `decisions/OldThemes/server_management/2026-05-25_phase_a_results.md`.

## Evidenz

### RAG_MCP Fusion Sweep (20 queries, 483 chunks — mixed academic+technical, 2026-04-08)

| Mode | Params | Doc Recall @10 | Snippet Recall @10 |
|---|---|---|---|
| Dense | - | 77% | 72% |
| Hybrid (RRF) | K=30 | 80% | 75% |
| Hybrid (RRF) | K=60 | 80% | 75% |
| Hybrid (RRF) | K=90 | 80% | 75% |
| CC | α=0.5 | 80% | 73% |
| CC | α=0.6 | 80% | 73% |
| CC | α=0.7 | 80% | 75% |
| **CC** | **α=0.8** | **80%** | **78%** |
| CC | α=0.9 | 80% | 72% |
| CC+Rerank | α=0.8 | 84% | 77% |
| Hybrid+Rerank | K=60 | 84% | 77% |

**CC α=0.8 is best without reranking** (highest Snippet Recall). RRF is K-insensitive on this collection. CC+Rerank and Hybrid+Rerank converge to same result (reranker normalizes input). Reranker adds +4pp Doc Recall but costs -1pp Snippet Recall and adds ~2s latency per query.

Script: pre-A_retrieval_eval.py eval harness (not committed to repo — non-reproducible; data preserved in report).
Report: `dev/retrieval/A_retrieval_eval_reports/sweep_comparison_20260408_190448.md`

## Recommendation (SOLL)

- **Keep:** No fusion in prod path — cc_fusion removed; always-rerank makes fusion redundant (Phase A confirmed all three rerank-0.6b modes converge identically, SPLADE adds zero signal when reranker active).
- **Keep:** `search_hybrid` as the prod search command (now always-rerank, no cc-fusion).
- Fusion implementations (`cc_fusion`, `rrf_fusion`) are permanently removed from src/. If a future architecture re-introduces hybrid-without-rerank, implement from scratch referencing the Evidenz tables below.

## Offene Fragen

- Should hybrid be the default search? Currently only via explicit `search_hybrid` tool call. Evidence says: only if Sparse component is fixed.
- Weighted RRF: Give Dense higher weight than Sparse? Not standard RRF but could compensate for weak Sparse.

## Quellen

- Anthropic contextual-retrieval (RRF for hybrid retrieval)
- RAG Collection: Pipeline_Optimization (two-stage retrieval findings)
- Bruch et al. 2023 "An Analysis of Fusion Functions for Hybrid Retrieval" (ACM TOIS, arXiv:2210.11934)
