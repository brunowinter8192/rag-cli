# Cross-Product Sweep: mode × top_k

**Timestamp:** 20260525_004613
**Collection:** test_db
**Swept:** `mode` (7 values) × `top_k` (5 values) = 35 configs
**Fixed:** collection=test_db, alpha=0.8, rrf_k=60, score_threshold=0.0, query_prefix=True

---

## Primary: Snippet Recall  (format: `snippet% (NDCG)`)

| mode \ top_k | top_k=3 | top_k=5 | top_k=7 | top_k=10 | top_k=12 |
|---|--- | --- | --- | --- | ---|
| dense | 63% (0.565) | 69% (0.596) | 75% (0.621) | 80% (0.639) | 86% (0.659) |
| sparse | 70% (0.631) | 75% (0.656) | 75% (0.656) | 80% (0.678) | 85% (0.695) |
| hybrid | 72% (0.665) | 77% (0.696) | 80% (0.708) | 80% (0.708) | 80% (0.708) |
| cc | 69% (0.627) | 77% (0.668) | 80% (0.680) | 83% (0.691) | 83% (0.691) |
| cc+rerank | 55% (0.499) | 69% (0.564) | 79% (0.605) | 94% (0.655) | 97% (0.665) |
| hybrid+rerank | 55% (0.499) | 69% (0.564) | 82% (0.617) | 94% (0.655) | 97% (0.665) |
| bm25 | 66% (0.616) | 72% (0.647) | 79% (0.676) | 82% (0.686) | 82% (0.686) |

**Best cell:** `mode=cc+rerank, top_k=12` — snippet_recall=97%, NDCG=0.665, MRR=0.626

---

## Secondary: NDCG@K

| mode \ top_k | top_k=3 | top_k=5 | top_k=7 | top_k=10 | top_k=12 |
|---|--- | --- | --- | --- | ---|
| dense | 0.565 | 0.596 | 0.621 | 0.639 | 0.659 |
| sparse | 0.631 | 0.656 | 0.656 | 0.678 | 0.695 |
| hybrid | 0.665 | 0.696 | 0.708 | 0.708 | 0.708 |
| cc | 0.627 | 0.668 | 0.680 | 0.691 | 0.691 |
| cc+rerank | 0.499 | 0.564 | 0.605 | 0.655 | 0.665 |
| hybrid+rerank | 0.499 | 0.564 | 0.617 | 0.655 | 0.665 |
| bm25 | 0.616 | 0.647 | 0.676 | 0.686 | 0.686 |

## Secondary: MRR@K

| mode \ top_k | top_k=3 | top_k=5 | top_k=7 | top_k=10 | top_k=12 |
|---|--- | --- | --- | --- | ---|
| dense | 0.686 | 0.686 | 0.686 | 0.693 | 0.693 |
| sparse | 0.657 | 0.669 | 0.669 | 0.669 | 0.674 |
| hybrid | 0.755 | 0.770 | 0.770 | 0.770 | 0.770 |
| cc | 0.706 | 0.735 | 0.735 | 0.735 | 0.735 |
| cc+rerank | 0.578 | 0.605 | 0.613 | 0.626 | 0.626 |
| hybrid+rerank | 0.578 | 0.605 | 0.613 | 0.626 | 0.626 |
| bm25 | 0.676 | 0.676 | 0.685 | 0.685 | 0.685 |

## Secondary: Recall@K (chunk-level)

| mode \ top_k | top_k=3 | top_k=5 | top_k=7 | top_k=10 | top_k=12 |
|---|--- | --- | --- | --- | ---|
| dense | 62.7% | 68.6% | 74.5% | 80.4% | 86.3% |
| sparse | 69.6% | 74.5% | 74.5% | 80.4% | 85.3% |
| hybrid | 71.6% | 77.5% | 80.4% | 80.4% | 80.4% |
| cc | 68.6% | 77.5% | 80.4% | 83.3% | 83.3% |
| cc+rerank | 54.9% | 68.6% | 79.4% | 94.1% | 97.1% |
| hybrid+rerank | 54.9% | 68.6% | 82.4% | 94.1% | 97.1% |
| bm25 | 65.7% | 71.6% | 79.4% | 82.4% | 82.4% |

## Secondary: Doc Recall (diagnostic)

| mode \ top_k | top_k=3 | top_k=5 | top_k=7 | top_k=10 | top_k=12 |
|---|--- | --- | --- | --- | ---|
| dense | 100% | 100% | 100% | 100% | 100% |
| sparse | 94% | 100% | 100% | 100% | 100% |
| hybrid | 97% | 100% | 100% | 100% | 100% |
| cc | 97% | 97% | 100% | 100% | 100% |
| cc+rerank | 94% | 97% | 100% | 100% | 100% |
| hybrid+rerank | 94% | 100% | 100% | 100% | 100% |
| bm25 | 94% | 100% | 100% | 100% | 100% |

---

## Summary

**Winner:** `mode=cc+rerank, top_k=12`
- snippet_recall: 97% (primary)
- NDCG@12: 0.665 (tie-breaker)
- MRR@12: 0.626
- Recall@12: 97.1%
- doc_recall: 100%

**Notes:**
- `mode=dense`: snippet_recall spans 63%–86% (gain 24%); peaks at top_k=12
- `mode=sparse`: snippet_recall spans 70%–85% (gain 16%); peaks at top_k=12
- `mode=cc`: snippet_recall spans 69%–83% (gain 15%); peaks at top_k=10
- `mode=cc+rerank`: snippet_recall spans 55%–97% (gain 42%); peaks at top_k=12
- `mode=hybrid+rerank`: snippet_recall spans 55%–97% (gain 42%); peaks at top_k=12
- `mode=bm25`: snippet_recall spans 66%–82% (gain 17%); peaks at top_k=10

