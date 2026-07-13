# Sweep: rerank_candidates Up-Sweep (dense+rerank-0.6b, rc=20–80)

**Timestamp:** 20260525_2237
**Collection:** test_db
**Mode (fixed):** dense+rerank-0.6b
**top_k (fixed):** 12
**Swept:** `rerank_candidates` ∈ {20, 30, 40, 50} (Phase B) + {60, 70, 80} (Phase B Up)
**Source files:**
- rc=20–50: `sweep_rerank_candidates_20260525_211134.md`
- rc=60: `eval_baseline_20260525_223307.md`
- rc=70: `eval_baseline_20260525_223519.md`
- rc=80: `eval_baseline_20260525_223726.md`

---

## Primary Results (full rc=20–80 curve)

| rc | Snippet Recall | NDCG@12 | MRR@12 | Recall@12 | Mean Latency | Notes |
|---|---|---|---|---|---|---|
| 20 | 94% | 0.661 | 0.629 | 94.1% | 2828ms | — |
| **30** | **97%** | **0.667** | **0.627** | **97.1%** | **4539ms** | **plateau starts** |
| 40 | 97% | 0.665 | 0.626 | 97.1% | 6276ms | — |
| 50 | 97% | 0.665 | 0.626 | 97.1% | 7228ms | — |
| 60 | 97% | 0.665 | 0.626 | 97.1% | 7184ms | ← effectively rc=50 (see below) |
| 70 | 97% | 0.665 | 0.626 | 97.1% | 7557ms | ← effectively rc=50 |
| 80 | 97% | 0.665 | 0.626 | 97.1% | 7209ms | ← effectively rc=50 |

**Winner:** `rerank_candidates=30` — max snippet recall (97%), lowest latency at plateau (4539ms)

---

## Key Finding: CANDIDATES=50 Cap in p1_retriever.py

rc=60/70/80 produce **identical results to rc=50** — same recall, same NDCG, same latency (~7200ms). This is not a recall ceiling; it is a retriever implementation cap.

`retrieve_dense()` in `dev/retrieval/p1_retriever.py` always calls:
```python
CANDIDATES = 50   # line 19
results = search_dense(conn, emb, collection, CANDIDATES)   # hardcoded 50
return results[:top_k]   # top_k = rerank_candidates here
```

For rc > 50: `search_dense` returns 50 rows; `results[:60]` (or `[:70]`, `[:80]`) still returns 50. The reranker receives 50 candidates regardless. Identical latency, identical results.

**Implication:** the Phase B Up-Sweep did not measure rc=60–80 as intended — it re-measured rc=50 three times. To genuinely test rc>50, `CANDIDATES` in `p1_retriever.py` must be raised (e.g. to 100) and the database query can return more rows.

**Whether rc>50 is worth measuring** depends on whether there is recall budget left. Since rc=30–80 all reach 97% and the ceiling doesn't move, the remaining 3% gap is likely not in the candidate pool at any rc level — it may be a verbatim-match miss (quote text doesn't appear in any chunk) rather than a ranking miss.

---

## Latency Curve

| rc | mean_lat | Δlat from prev | ms/pair | status |
|---|---|---|---|---|
| 20 | 2828ms | — | 141ms | genuine |
| 30 | 4539ms | +1711ms | 151ms | genuine |
| 40 | 6276ms | +1737ms | 157ms | genuine |
| 50 | 7228ms | +952ms | 145ms | genuine |
| 60 | 7184ms | −44ms | 120ms | capped at 50 |
| 70 | 7557ms | +373ms | 108ms | capped at 50 |
| 80 | 7209ms | −348ms | 90ms | capped at 50 |

**Genuine range (rc=20–50):** latency is near-linear at ~145–157ms/pair, with a slight sublinear dip at rc=40→50 (+952ms vs expected ~+1700ms). This sublinear step was already present in Phase B — likely natural batch scheduling variation at the reranker.

**Capped range (rc=60–80):** latency clusters around 7200–7560ms (≈ rc=50 level) with run-to-run noise. No meaningful signal.

---

## Summary

**Snippet-recall plateau:** rc=30 is the minimum rc that achieves 97% (the collection-level ceiling). rc=20 misses one snippet (94%), which appears in positions 21–30 of the dense retrieval ranking. rc=31+ adds no recall.

**Hard ceiling at 97%:** One snippet is permanently missing regardless of rc (within the CANDIDATES=50 cap). Likely a verbatim-quote match failure (the exact quote text may span a chunk boundary or differ slightly from indexed content), not a ranking failure.

**Prod-config recommendation confirmed:** `mode=dense+rerank-0.6b, top_k=12, rerank_candidates=30`
- 97% snippet recall (ceiling for this collection)
- 4539ms mean latency (37% faster than rc=50)
- No SPLADE server needed (C3 constellation: embedding-8b + reranker-0.6b = 15.93 GB VRAM)

**Next open question:** To genuinely probe rc>50, raise `CANDIDATES` in `p1_retriever.py` (line 19). Whether this is worth pursuing depends on whether the 3% gap (1 missing snippet) is recoverable — that requires investigation into which query/snippet is failing at all rc levels.
