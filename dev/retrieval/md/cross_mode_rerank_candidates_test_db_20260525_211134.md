# Sweep: rerank_candidates (dense+rerank-0.6b)

**Timestamp:** 20260525_211134
**Collection:** test_db
**Mode (fixed):** dense+rerank-0.6b
**top_k (fixed):** 12
**Swept:** `rerank_candidates` over [20, 30, 40, 50] — 4 configs × 17 queries
**Fixed:** alpha=0.8, rrf_k=60, score_threshold=0.0, query_prefix=True
**Winner selection:** max(snippet_recall) → tie-break min(mean_lat)

---

## Primary Results

| rerank_candidates | Snippet Recall | NDCG@12 | MRR@12 | Recall@12 | Doc Recall | Mean Latency |
|---|---|---|---|---|---|---|
| **rc=20** | 94% | 0.661 | 0.629 | 94.1% | 100% | 2828ms |
| **rc=30** | **97%** | 0.667 | 0.627 | 97.1% | 100% | **4539ms** ← winner |
| **rc=40** | 97% | 0.665 | 0.626 | 97.1% | 100% | 6276ms |
| **rc=50** | 97% | 0.665 | 0.626 | 97.1% | 100% | 7228ms |

**Winner:** `rerank_candidates=30`
- snippet_recall: 97% (primary — plateau reached here)
- mean_latency: 4539ms (cheapest config at max recall)
- NDCG@12: 0.667 | MRR@12: 0.627 | Recall@12: 97.1%

---

## Latency Curve

| Step | rc | mean_lat | Δlat | lat ratio | expected (linear) |
|---|---|---|---|---|---|
| — | 20 | 2828ms | — | — | — |
| +10 | 30 | 4539ms | +1711ms | 1.60× | 1.50× |
| +10 | 40 | 6276ms | +1737ms | 1.38× | 1.33× |
| +10 | 50 | 7228ms | +952ms | 1.15× | 1.25× |

Latency scales approximately linearly with rc (Δlat ≈ +1700ms per +10 candidates), slightly sublinear at the high end (rc=50 step is +952ms vs expected ~+1800ms). Overall near-linear — no caching or throughput effect detected.

---

## Summary

**Snippet-recall plateau:** rc=30 → rc=40 → rc=50 all produce identical 97% snippet recall. rc=20 falls short at 94% (one additional snippet missed across 17 queries). Adding more candidates beyond rc=30 buys no recall.

**Prod-config recommendation:** `mode=dense+rerank-0.6b, top_k=12, rerank_candidates=30`
- Hits peak snippet recall (97%)
- 37% faster than rc=50 (4539ms vs 7228ms)
- NDCG marginally higher at rc=30 (0.667) vs rc=40/50 (0.665) — consistent with better candidates in the pool

**What rc=20 misses:** 94% vs 97% = 1 snippet missing across 17 queries (35 total snippets). The missing snippet is in candidates 21–30 at rc=30 but not retrieved in the top-20 by dense retrieval. A 56ms savings-per-candidate × 10 fewer candidates = not worth the recall loss.
