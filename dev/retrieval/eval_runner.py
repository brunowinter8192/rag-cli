# INFRASTRUCTURE
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "indexing"))

import httpx

import p1_retriever as _retriever
from eval_config import THRESHOLD_IGNORED_MODES
from eval_constellation import _lookup_server_url


# FUNCTIONS

def _load_queries(queries_path: str) -> list[dict]:
    path = Path(queries_path)
    if not path.exists():
        print(f"ERROR: queries file not found: {queries_path}")
        sys.exit(1)
    with open(path) as f:
        data = json.load(f)
    if isinstance(data, dict) and "queries" in data:
        return data["queries"]
    if isinstance(data, list):
        return data
    print("ERROR: queries file must contain a JSON object with 'queries' key or a JSON array")
    sys.exit(1)


def _resolve_queries_path(collection: str, explicit_path: str | None) -> str:
    if explicit_path:
        return explicit_path
    derived = Path(__file__).parent / f"queries_{collection}.json"
    return str(derived)


def _verify_drift(queries: list[dict], collection: str) -> None:
    from p4_db import get_connection
    conn = get_connection()
    errors = []
    try:
        with conn.cursor() as cur:
            for qi, entry in enumerate(queries, 1):
                for ec in entry.get("expected_chunks", []):
                    cur.execute(
                        "SELECT 1 FROM documents WHERE collection=%s AND document=%s AND chunk_index=%s AND content LIKE %s",
                        (collection, ec["document"], ec["chunk_index"], f"%{ec['identifying_quote']}%"),
                    )
                    if not cur.fetchone():
                        errors.append(
                            f"Q{qi} {ec['document']}[{ec['chunk_index']}]: quote not in collection={collection}: '{ec['identifying_quote'][:60]}'"
                        )
    finally:
        conn.close()
    if errors:
        print("ERROR: Drift-detector — identifying_quotes do not match current index:")
        for e in errors:
            print(f"  {e}")
        sys.exit(1)


def _rerank_at(query: str, results: list[dict], top_k: int, url: str) -> list[dict]:
    contents = [r["content"] for r in results]
    response = httpx.post(
        url,
        json={"query": query, "documents": contents, "top_n": len(contents)},
        timeout=300.0,
    )
    response.raise_for_status()
    data = response.json()
    ranked = sorted(data.get("results", data), key=lambda x: x["relevance_score"], reverse=True)
    reranked = []
    for item in ranked[:top_k]:
        doc = results[item["index"]].copy()
        doc["score"] = round(item["relevance_score"], 6)
        reranked.append(doc)
    return reranked


def _dispatch_mode(mode: str, query: str, collection: str, config: dict) -> list[dict]:
    top_k = config["top_k"]
    alpha = config["alpha"]
    rrf_k = config["rrf_k"]
    query_prefix = config["query_prefix"]

    if mode == "dense":
        return _retriever.retrieve_dense(query, collection, top_k, query_prefix=query_prefix)
    if mode == "sparse":
        return _retriever.retrieve_sparse(query, collection, top_k)
    if mode == "bm25":
        return _retriever.retrieve_bm25(query, collection, top_k)
    if mode == "hybrid":
        return _retriever.retrieve_hybrid(query, collection, top_k, rrf_k=rrf_k, query_prefix=query_prefix)
    if mode == "cc":
        return _retriever.retrieve_cc(query, collection, top_k, alpha=alpha, query_prefix=query_prefix)
    if mode in ("cc+rerank", "hybrid+rerank", "cc+rerank-8b", "hybrid+rerank-8b", "dense+rerank-0.6b", "dense+rerank-8b"):
        return _dispatch_rerank_mode(mode, query, collection, config)
    return []


def _dispatch_rerank_mode(mode: str, query: str, collection: str, config: dict) -> list[dict]:
    top_k = config["top_k"]
    alpha = config["alpha"]
    rrf_k = config["rrf_k"]
    query_prefix = config["query_prefix"]
    candidates = config["rerank_candidates"]

    if mode == "cc+rerank":
        url = _lookup_server_url("reranker-0.6b")
        hits = _retriever.retrieve_cc(query, collection, candidates, alpha=alpha, query_prefix=query_prefix)
    elif mode == "hybrid+rerank":
        url = _lookup_server_url("reranker-0.6b")
        hits = _retriever.retrieve_hybrid(query, collection, candidates, rrf_k=rrf_k, query_prefix=query_prefix)
    elif mode == "cc+rerank-8b":
        url = _lookup_server_url("reranker-8b")
        hits = _retriever.retrieve_cc(query, collection, candidates, alpha=alpha, query_prefix=query_prefix)
    elif mode == "hybrid+rerank-8b":
        url = _lookup_server_url("reranker-8b")
        hits = _retriever.retrieve_hybrid(query, collection, candidates, rrf_k=rrf_k, query_prefix=query_prefix)
    elif mode == "dense+rerank-0.6b":
        url = _lookup_server_url("reranker-0.6b")
        hits = _retriever.retrieve_dense(query, collection, candidates, query_prefix=query_prefix)
    else:
        url = _lookup_server_url("reranker-8b")
        hits = _retriever.retrieve_dense(query, collection, candidates, query_prefix=query_prefix)
    return _rerank_at(query, hits, top_k, url)


def _run_query(query: str, collection: str, config: dict) -> tuple[list[dict], float]:
    mode = config["mode"]
    score_threshold = config["score_threshold"]

    t0 = time.perf_counter()
    try:
        hits = _dispatch_mode(mode, query, collection, config)
    except Exception as e:
        latency_ms = (time.perf_counter() - t0) * 1000
        print(f"WARNING: query failed ({e}): {query[:60]}")
        return [], latency_ms

    latency_ms = (time.perf_counter() - t0) * 1000

    if score_threshold > 0.0 and mode not in THRESHOLD_IGNORED_MODES:
        hits = [h for h in hits if h.get("score", 0) >= score_threshold]

    return hits, latency_ms
