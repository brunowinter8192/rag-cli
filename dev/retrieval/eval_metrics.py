# INFRASTRUCTURE
import math


# FUNCTIONS

# Check which expected documents were found and at which ranks (diagnostic)
def _check_document_match(expected_docs: list[str], hits: list[dict]) -> list[dict]:
    results = []
    for doc in expected_docs:
        ranks = [rank for rank, h in enumerate(hits, 1) if h.get("document") == doc]
        results.append({"doc": doc, "found": bool(ranks), "ranks": ranks})
    return results


# Check which expected_chunks identifying_quotes appear as substrings in any hit's content
def _check_snippet_match(expected_chunks: list[dict], hits: list[dict]) -> list[dict]:
    results = []
    for ec in expected_chunks:
        quote = ec["identifying_quote"]
        found_rank = None
        for rank, h in enumerate(hits, 1):
            if quote.lower() in h.get("content", "").lower():
                found_rank = rank
                break
        results.append({"snippet": quote, "found": found_rank is not None, "rank": found_rank})
    return results


# Compute NDCG@K with binary relevance (rel=1 if (hit.document, hit.chunk_index) in expected_set)
# DCG@k = Σ (2^rel_i - 1) / log2(i+1), IDCG = DCG of perfect ranking using total_relevant
def _compute_ndcg_at_k(hits: list[dict], expected_set: set, total_relevant: int, k: int) -> float:
    rels = [1 if (h.get("document"), h.get("chunk_index")) in expected_set else 0 for h in hits[:k]]
    dcg = sum(r / math.log2(i + 2) for i, r in enumerate(rels))
    idcg = sum(1.0 / math.log2(i + 2) for i in range(min(total_relevant, k)))
    return min(1.0, dcg / idcg) if idcg > 0 else 0.0


# Compute MRR@K: 1/rank of first relevant hit in top K, 0 if none
def _compute_mrr_at_k(hits: list[dict], expected_set: set, k: int) -> float:
    for rank, h in enumerate(hits[:k], 1):
        if (h.get("document"), h.get("chunk_index")) in expected_set:
            return 1.0 / rank
    return 0.0


# Compute Recall@K: expected_chunks retrieved in top K / total expected_chunks
def _compute_recall_at_k(hits: list[dict], expected_set: set, total_relevant: int, k: int) -> float:
    if total_relevant == 0:
        return 0.0
    retrieved_relevant = sum(1 for h in hits[:k] if (h.get("document"), h.get("chunk_index")) in expected_set)
    return retrieved_relevant / total_relevant


# Bundle NDCG@K, MRR@K, Recall@K using expected_chunks as binary ground truth
def _compute_rank_metrics(hits: list[dict], expected_chunks: list[dict], k: int) -> dict:
    expected_set = {(ec["document"], ec["chunk_index"]) for ec in expected_chunks}
    total_relevant = len(expected_chunks)
    return {
        "ndcg_at_k": _compute_ndcg_at_k(hits, expected_set, total_relevant, k),
        "mrr_at_k": _compute_mrr_at_k(hits, expected_set, k),
        "recall_at_k": _compute_recall_at_k(hits, expected_set, total_relevant, k),
        "k": k,
    }


# Compute average doc recall, snippet recall, rank metrics, and latency across all query results
def _compute_avg_metrics(query_results: list[dict]) -> tuple[float, float, float, float, float, float]:
    doc_recalls = []
    snip_recalls = []
    ndcg_vals = []
    mrr_vals = []
    recall_k_vals = []
    lat_vals = []
    for qr in query_results:
        doc_match = qr["doc_match"]
        snippet_match = qr["snippet_match"]
        rm = qr.get("rank_metrics", {})
        doc_recalls.append(sum(1 for d in doc_match if d["found"]) / len(doc_match) if doc_match else 0)
        snip_recalls.append(sum(1 for s in snippet_match if s["found"]) / len(snippet_match) if snippet_match else 0)
        ndcg_vals.append(rm.get("ndcg_at_k", 0.0))
        mrr_vals.append(rm.get("mrr_at_k", 0.0))
        recall_k_vals.append(rm.get("recall_at_k", 0.0))
        lat_vals.append(qr.get("latency_ms", 0.0))
    total = len(query_results)
    return (
        sum(doc_recalls) / total if total else 0,
        sum(snip_recalls) / total if total else 0,
        sum(ndcg_vals) / total if total else 0,
        sum(mrr_vals) / total if total else 0,
        sum(recall_k_vals) / total if total else 0,
        sum(lat_vals) / total if total else 0,
    )
