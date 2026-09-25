# INFRASTRUCTURE
import time

from src.rag.db import get_connection, validate_collection
from src.rag.reranker import rerank_workflow
from src.rag.retrieval_log import log_search
from src.rag.search_primitives import embed_query, search_vectors

RERANK_CANDIDATES = 30
RERANK_TOP_K = 12


# ORCHESTRATOR

def search_workflow(
    query: str,
    collection: str | None = None,
    document: str | None = None,
    exclude: str | None = None
) -> list[dict]:
    started = time.perf_counter()
    query_vector, candidates = retrieve_candidates(query, collection, document, exclude)
    results = rerank_candidates(query, candidates)
    record_search(query, collection, document, exclude, candidates, results, started, query_vector)
    return results


# FUNCTIONS

def retrieve_candidates(query: str, collection: str | None, document: str | None, exclude: str | None) -> tuple[list[float], list[dict]]:
    conn = get_connection()
    if collection:
        validate_collection(conn, collection)
    query_vector = embed_query(query)
    candidates = search_vectors(conn, query_vector, RERANK_CANDIDATES, collection, document, exclude)
    conn.close()
    return query_vector, candidates


def rerank_candidates(query: str, candidates: list[dict]) -> list[dict]:
    if not candidates:
        return []
    return filter_positive_score(rerank_workflow(query, candidates, RERANK_TOP_K))


def filter_positive_score(results: list[dict]) -> list[dict]:
    return [r for r in results if r['score'] > 0]


def record_search(query: str, collection: str | None, document: str | None, exclude: str | None,
                  candidates: list[dict], results: list[dict], started: float, query_vector: list[float]) -> None:
    log_search(query, collection, document, exclude, len(candidates), results, started, len(query_vector), RERANK_CANDIDATES)
