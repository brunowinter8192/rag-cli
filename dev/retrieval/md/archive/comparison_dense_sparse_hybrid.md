# Retrieval Mode Comparison: RAG_MCP

**Collection:** RAG_MCP | **Top-k:** 10 | **Queries:** 20

| Mode | Doc Recall @10 | Snippet Recall @10 | 100% Doc Match | 100% Snippet Match | 0 Snippet Match |
|------|---------------|-------------------|----------------|-------------------|-----------------|
| dense | 77% | 75% | 11/20 | 10/20 | 0/20 |
| sparse | 79% | 63% | 11/20 | 7/20 | 1/20 |
| hybrid | 80% | 66% | 12/20 | 7/20 | 1/20 |

## By Query Type

| Type | Count | Dense Doc | Dense Snip | Sparse Doc | Sparse Snip | Hybrid Doc | Hybrid Snip |
|------|-------|-----------|-----------|------------|-------------|------------|-------------|
| factual | 8 | 94% | 81% | 100% | 81% | 100% | 75% |
| conceptual | 7 | 70% | 74% | 63% | 48% | 70% | 67% |
| cross-document | 5 | 58% | 67% | 69% | 57% | 62% | 50% |

## Observations

- **Document Recall:** hybrid > sparse > dense (80% > 79% > 77%) — marginal gains from adding sparse signal
- **Snippet Recall:** dense wins clearly (75% > 66% hybrid > 63% sparse) — dense embeddings better capture semantic similarity for exact phrase recovery
- **Factual queries:** sparse and hybrid achieve 100% doc recall vs. 94% dense; snippet recall comparable
- **Conceptual queries:** dense dominates snippet recall (74% vs. 48% sparse, 67% hybrid) — keyword-based sparse retrieval struggles with paraphrase
- **Cross-document queries:** no mode clearly wins; hybrid achieves best doc recall (62%) but lowest snippet recall (50%)

## Source Reports

- `eval_dense_20260407_190609.md`
- `eval_sparse_20260407_193841.md`
- `eval_hybrid_20260407_193852.md`
