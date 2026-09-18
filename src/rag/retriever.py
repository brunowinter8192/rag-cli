# INFRASTRUCTURE
import time

from .db import get_connection, validate_collection, query_collections, query_documents, query_progress, fetch_chunk_range
from .search_primitives import embed_query, search_vectors
from .formatting import format_results, format_collections, format_documents, format_progress
from .reranker import rerank_workflow
from .chunker import DEFAULT_OVERLAP
from .retrieval_log import log_search, log_expand

RERANK_CANDIDATES = 30


# ORCHESTRATOR

def list_collections_workflow(filter: str | None = None) -> list[dict]:
    conn = get_connection()
    results = query_collections(conn, filter)
    conn.close()
    return results


def list_documents_workflow(collection: str, document: str | None = None, filter: str | None = None, exclude: str | None = None) -> list[dict]:
    conn = get_connection()
    validate_collection(conn, collection)
    results = query_documents(conn, collection, document, filter, exclude)
    conn.close()
    return results


def progress_workflow(collection: str) -> list[dict]:
    conn = get_connection()
    validate_collection(conn, collection)
    results = query_progress(conn, collection)
    conn.close()
    return results


def expand_chunks_workflow(collection: str, document: str, chunk_index: int, before: int = 0, after: int = 0) -> dict:
    started = time.perf_counter()
    conn = get_connection()
    validate_collection(conn, collection)
    chunks = fetch_chunk_range(conn, collection, document, chunk_index - before, chunk_index + after)
    conn.close()
    result = build_expand_result(chunks, collection, document, chunk_index, before, after)
    log_expand(result, started)
    return result


def search_workflow(
    query: str,
    collection: str | None = None,
    document: str | None = None,
    exclude: str | None = None
) -> list[dict]:
    started = time.perf_counter()
    conn = get_connection()
    if collection:
        validate_collection(conn, collection)
    query_vector = embed_query(query)
    vector_results = search_vectors(conn, query_vector, RERANK_CANDIDATES, collection, document, exclude)
    conn.close()
    if not vector_results:
        log_search(query, collection, document, exclude, len(vector_results), [], started)
        return []
    reranked = rerank_workflow(query, vector_results, 12)
    results = filter_positive_score(reranked)
    log_search(query, collection, document, exclude, len(vector_results), results, started)
    return results


# FUNCTIONS

def build_expand_result(chunks: list[dict], collection: str, document: str, chunk_index: int, before: int, after: int) -> dict:
    return {
        'content': merge_chunks(chunks),
        'collection': collection,
        'document': document,
        'chunk_index': chunk_index,
        'before': before,
        'after': after,
        'chunks_returned': len(chunks)
    }


def filter_positive_score(results: list[dict]) -> list[dict]:
    return [r for r in results if r['score'] > 0]


def merge_chunks(chunks: list[dict]) -> str:
    if not chunks:
        return ""
    result = chunks[0]['content']
    for i in range(1, len(chunks)):
        overlap = find_overlap(result, chunks[i]['content'])
        if overlap > 0:
            result += chunks[i]['content'][overlap:]
        else:
            result += "\n\n" + chunks[i]['content']
    return result


def find_overlap(text1: str, text2: str, max_overlap: int = DEFAULT_OVERLAP) -> int:
    for size in range(min(len(text1), len(text2), max_overlap), 0, -1):
        if text1[-size:] == text2[:size]:
            return size
    return 0
