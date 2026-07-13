# Retrieval Sweep: query_prefix

**Swept:** `query_prefix` over `[True, False]`
**Fixed (BASELINE):** mode=cc, top_k=10, alpha=0.8, rrf_k=60, score_threshold=0.0
**Timestamp:** 20260428_221609

| query_prefix | Mode | Doc Recall | Snippet Recall |
|-------------|------|-----------|----------------|
| True | cc | 80% | 78% |
| False | cc | 79% | 72% |
