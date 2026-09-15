# INFRASTRUCTURE
import logging
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "indexing"))

import httpx

from p2_embedder import embed
from p3_sparse_embedder import embed_sparse
from p4_db import get_connection, search_dense, search_sparse, search_hybrid, search_cc

logger = logging.getLogger(__name__)

INSTRUCT_PREFIX = "Instruct: Given a search query, retrieve relevant passages that answer the query\nQuery: "
RERANKER_URL = os.getenv("RERANKER_URL", "http://localhost:8082/v1/rerank")
CANDIDATES = 50


# FUNCTIONS

def retrieve_dense(query: str, collection: str, top_k: int = 10, query_prefix: bool = True) -> list[dict]:
    conn = get_connection()
    prefix = INSTRUCT_PREFIX if query_prefix else ""
    emb = embed([query], prefix=prefix)[0]
    results = search_dense(conn, emb, collection, CANDIDATES)
    conn.close()
    return results[:top_k]


def retrieve_sparse(query: str, collection: str, top_k: int = 10) -> list[dict]:
    conn = get_connection()
    sparse = embed_sparse([query])[0]
    results = search_sparse(conn, sparse, collection, CANDIDATES)
    conn.close()
    return results[:top_k]


def retrieve_bm25(query: str, collection: str, top_k: int = 10) -> list[dict]:
    words = [w for w in query.split() if w]
    if not words:
        return []
    conn = get_connection()
    tsquery_and = " & ".join(words)
    results = _bm25_query(conn, tsquery_and, top_k, collection)
    if not results and len(words) > 1:
        tsquery_or = " | ".join(words)
        results = _bm25_query(conn, tsquery_or, top_k, collection)
    conn.close()
    return results


def _bm25_query(conn, tsquery: str, top_k: int, collection: str) -> list[dict]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT content, collection, document, chunk_index,
                   ts_rank(tsv, to_tsquery('english', %s)) as score
            FROM documents
            WHERE tsv @@ to_tsquery('english', %s) AND collection = %s
            ORDER BY score DESC
            LIMIT %s
            """,
            [tsquery, tsquery, collection, top_k]
        )
        rows = cur.fetchall()
    return [
        {
            "content": row[0],
            "collection": row[1],
            "document": row[2],
            "chunk_index": row[3],
            "score": round(float(row[4]), 4)
        }
        for row in rows
    ]


def retrieve_hybrid(query: str, collection: str, top_k: int = 10, rrf_k: int = 60, query_prefix: bool = True) -> list[dict]:
    conn = get_connection()
    prefix = INSTRUCT_PREFIX if query_prefix else ""
    emb = embed([query], prefix=prefix)[0]
    sparse = embed_sparse([query])[0]
    dense_results = search_dense(conn, emb, collection, CANDIDATES)
    sparse_results = search_sparse(conn, sparse, collection, CANDIDATES)
    results = search_hybrid(conn, dense_results, sparse_results, rrf_k)
    conn.close()
    return results[:top_k]


def retrieve_cc(query: str, collection: str, top_k: int = 10, alpha: float = 0.8, query_prefix: bool = True) -> list[dict]:
    conn = get_connection()
    prefix = INSTRUCT_PREFIX if query_prefix else ""
    emb = embed([query], prefix=prefix)[0]
    sparse = embed_sparse([query])[0]
    dense_results = search_dense(conn, emb, collection, CANDIDATES)
    sparse_results = search_sparse(conn, sparse, collection, CANDIDATES)
    results = search_cc(conn, dense_results, sparse_results, alpha)
    conn.close()
    return results[:top_k]


def retrieve_cc_rerank(query: str, collection: str, top_k: int = 10, alpha: float = 0.8, rerank_candidates: int = 50, query_prefix: bool = True) -> list[dict]:
    conn = get_connection()
    prefix = INSTRUCT_PREFIX if query_prefix else ""
    emb = embed([query], prefix=prefix)[0]
    sparse = embed_sparse([query])[0]
    dense_results = search_dense(conn, emb, collection, CANDIDATES)
    sparse_results = search_sparse(conn, sparse, collection, CANDIDATES)
    results = search_cc(conn, dense_results, sparse_results, alpha)
    conn.close()
    return rerank(query, results[:rerank_candidates], top_k)


def rerank(query: str, results: list[dict], top_k: int = 10) -> list[dict]:
    contents = [r["content"] for r in results]
    response = httpx.post(
        RERANKER_URL,
        json={"query": query, "documents": contents, "top_n": len(contents)},
        timeout=60.0,
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
