# Cross-Product Sweep: mode x top_k

**Timestamp:** 20260525_2028
**Collection:** test_db
**Swept:** `mode` (8 values) x `top_k` (5 values) = 40 configs
**Fixed:** collection=test_db, alpha=0.8, rrf_k=60, score_threshold=0.0, query_prefix=True, rerank_candidates=50
**Source:** log preserved at `dev/retrieval/A_retrieval_eval_reports/cross_mode_top_k_test_db_20260525_2028.log`
**Note:** MRR@K, Recall@K, Doc Recall not in sweep stdout — see `cross_mode_top_k_test_db_20260525_004613.md` for 7-mode overlap. dense+rerank-0.6b is the new mode in this sweep.

---

## Primary: Snippet Recall  (format: `snippet% (NDCG) [mean_lat]`)

| mode \ top_k | top_k=3 | top_k=5 | top_k=7 | top_k=10 | top_k=12 |
|---|--- | --- | --- | --- | ---|
| dense | 63% (0.565) [137ms] | 69% (0.596) [131ms] | 75% (0.621) [131ms] | 80% (0.639) [131ms] | 86% (0.659) [131ms] |
| sparse | 70% (0.631) [81ms] | 75% (0.656) [39ms] | 75% (0.656) [39ms] | 80% (0.678) [38ms] | 85% (0.695) [36ms] |
| hybrid | 72% (0.665) [161ms] | 77% (0.696) [156ms] | 80% (0.708) [156ms] | 80% (0.708) [157ms] | 80% (0.708) [157ms] |
| cc | 69% (0.627) [157ms] | 77% (0.668) [155ms] | 80% (0.680) [155ms] | 83% (0.691) [155ms] | 83% (0.691) [156ms] |
| bm25 | 66% (0.616) [8ms] | 72% (0.647) [7ms] | 79% (0.676) [7ms] | 82% (0.686) [7ms] | 82% (0.686) [8ms] |
| cc+rerank | 55% (0.499) [7642ms] | 69% (0.564) [7492ms] | 79% (0.605) [7208ms] | 94% (0.655) [7181ms] | 97% (0.665) [7177ms] |
| hybrid+rerank | 55% (0.499) [7058ms] | 69% (0.564) [7051ms] | 79% (0.605) [7042ms] | 94% (0.655) [7025ms] | 97% (0.665) [7026ms] |
| dense+rerank-0.6b | 55% (0.499) [7158ms] | 69% (0.564) [7138ms] | 79% (0.605) [7133ms] | 94% (0.655) [7273ms] | 97% (0.665) [7448ms] |

**Best cell:** `mode=cc+rerank, top_k=12` — snippet_recall=97%, NDCG=0.665, mean_lat=7177ms

---

## Secondary: NDCG@K

| mode \ top_k | top_k=3 | top_k=5 | top_k=7 | top_k=10 | top_k=12 |
|---|--- | --- | --- | --- | ---|
| dense | 0.565 | 0.596 | 0.621 | 0.639 | 0.659 |
| sparse | 0.631 | 0.656 | 0.656 | 0.678 | 0.695 |
| hybrid | 0.665 | 0.696 | 0.708 | 0.708 | 0.708 |
| cc | 0.627 | 0.668 | 0.680 | 0.691 | 0.691 |
| bm25 | 0.616 | 0.647 | 0.676 | 0.686 | 0.686 |
| cc+rerank | 0.499 | 0.564 | 0.605 | 0.655 | 0.665 |
| hybrid+rerank | 0.499 | 0.564 | 0.605 | 0.655 | 0.665 |
| dense+rerank-0.6b | 0.499 | 0.564 | 0.605 | 0.655 | 0.665 |

## Secondary: Mean Latency (ms)

| mode \ top_k | top_k=3 | top_k=5 | top_k=7 | top_k=10 | top_k=12 |
|---|--- | --- | --- | --- | ---|
| dense | 137ms | 131ms | 131ms | 131ms | 131ms |
| sparse | 81ms | 39ms | 39ms | 38ms | 36ms |
| hybrid | 161ms | 156ms | 156ms | 157ms | 157ms |
| cc | 157ms | 155ms | 155ms | 155ms | 156ms |
| bm25 | 8ms | 7ms | 7ms | 7ms | 8ms |
| cc+rerank | 7642ms | 7492ms | 7208ms | 7181ms | 7177ms |
| hybrid+rerank | 7058ms | 7051ms | 7042ms | 7025ms | 7026ms |
| dense+rerank-0.6b | 7158ms | 7138ms | 7133ms | 7273ms | 7448ms |

---

## Summary

**Winner:** `mode=cc+rerank, top_k=12`
- snippet_recall: 97% (primary)
- NDCG@12: 0.665 (tie-breaker)
- mean_latency: 7177ms

**Notes:**
- `mode=dense`: snippet_recall spans 63%--86% (gain 23%); peaks at top_k=12
- `mode=sparse`: snippet_recall spans 70%--85% (gain 15%); peaks at top_k=12
- `mode=cc`: snippet_recall spans 69%--83% (gain 14%); peaks at top_k=10
- `mode=bm25`: snippet_recall spans 66%--82% (gain 16%); peaks at top_k=10
- `mode=cc+rerank`: snippet_recall spans 55%--97% (gain 42%); peaks at top_k=12
- `mode=hybrid+rerank`: snippet_recall spans 55%--97% (gain 42%); peaks at top_k=12
- `mode=dense+rerank-0.6b`: snippet_recall spans 55%--97% (gain 42%); peaks at top_k=12
