# INFRASTRUCTURE

COLLECTION = "test_db"

BASELINE = {
    "collection": "test_db",
    "mode": "cc",
    "top_k": 12,
    "alpha": 0.8,
    "rrf_k": 60,
    "score_threshold": 0.0,
    "query_prefix": True,
    "rerank_candidates": 50,
}

SWEEP_RANGES = {
    "mode":              ["dense", "sparse", "hybrid", "cc", "cc+rerank", "hybrid+rerank", "bm25",
                          "cc+rerank-8b", "hybrid+rerank-8b", "dense+rerank-0.6b", "dense+rerank-8b"],
    "top_k":             [3, 5, 7, 10, 12],
    "alpha":             [0.5, 0.6, 0.7, 0.8, 0.9],
    "rrf_k":             [30, 60, 90],
    "score_threshold":   [0.0, 0.3, 0.5],
    "query_prefix":      [True, False],
    "rerank_candidates": [20, 30, 40, 50],
}

# Modes where score_threshold is not meaningful (score scale not comparable to cosine)
THRESHOLD_IGNORED_MODES = {
    "hybrid", "hybrid+rerank", "bm25",
    "cc+rerank-8b", "hybrid+rerank-8b", "dense+rerank-0.6b", "dense+rerank-8b",
}
# Modes where query_prefix has no effect (no dense embedding step)
PREFIX_NOOP_MODES = {"sparse", "bm25"}
