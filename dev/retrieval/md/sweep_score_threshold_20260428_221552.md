# Retrieval Sweep: score_threshold

**Swept:** `score_threshold` over `[0.0, 0.3, 0.5]`
**Fixed (BASELINE):** mode=cc, top_k=10, alpha=0.8, rrf_k=60, query_prefix=True
**Timestamp:** 20260428_221552

| score_threshold | Mode | Doc Recall | Snippet Recall |
|----------------|------|-----------|----------------|
| 0.0 | cc | 80% | 78% |
| 0.3 | cc | 80% | 78% |
| 0.5 | cc | 80% | 78% |
