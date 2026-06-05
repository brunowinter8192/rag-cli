# INFRASTRUCTURE
import logging
from pathlib import Path

from .db import get_connection, validate_collection, query_collections, query_documents, query_progress, fetch_chunk_range
from .search_primitives import embed_query, search_vectors
from .formatting import format_results, format_collections, format_documents, format_progress
from .reranker import rerank_workflow

LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    filename=LOG_DIR / "retriever.log",
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

RERANK_CANDIDATES = 30


# ORCHESTRATOR

def search_workflow(
    query: str,
    top_k: int = 12,
    collection: str | None = None,
    document: str | None = None
) -> list[dict]:
    top_k = min(top_k, 12)
    conn = get_connection()
    if collection:
        validate_collection(conn, collection)
    query_vector = embed_query(query)
    results = search_vectors(conn, query_vector, top_k, collection, document)
    conn.close()
    logging.info(f"Search '{query[:50]}...' returned {len(results)} results")
    return results


def list_collections_workflow(filter: str | None = None) -> list[dict]:
    conn = get_connection()
    results = query_collections(conn, filter)
    conn.close()
    return results


def list_documents_workflow(collection: str, document: str | None = None, filter: str | None = None) -> list[dict]:
    conn = get_connection()
    validate_collection(conn, collection)
    results = query_documents(conn, collection, document, filter)
    conn.close()
    return results


def progress_workflow(collection: str) -> list[dict]:
    conn = get_connection()
    validate_collection(conn, collection)
    results = query_progress(conn, collection)
    conn.close()
    return results


def read_document_workflow(collection: str, document: str, chunk_index: int, before: int = 0, after: int = 0) -> dict:
    conn = get_connection()
    validate_collection(conn, collection)
    chunks = fetch_chunk_range(conn, collection, document, chunk_index - before, chunk_index + after)
    conn.close()
    return {
        'content': merge_chunks(chunks),
        'collection': collection,
        'document': document,
        'chunk_index': chunk_index,
        'before': before,
        'after': after,
        'chunks_returned': len(chunks)
    }


def search_hybrid_workflow(
    query: str,
    collection: str | None = None,
    document: str | None = None
) -> list[dict]:
    conn = get_connection()
    if collection:
        validate_collection(conn, collection)
    query_vector = embed_query(query)
    vector_results = search_vectors(conn, query_vector, RERANK_CANDIDATES, collection, document)
    conn.close()
    if not vector_results:
        logging.info(f"Hybrid search '{query[:50]}...' returned 0 candidates (no match for collection/document filter)")
        return []
    results = rerank_workflow(query, vector_results, 10)
    results = [r for r in results if r['score'] > 0]
    logging.info(f"Hybrid search '{query[:50]}...' returned {len(results)} results (dense+rerank, candidates={RERANK_CANDIDATES})")
    return results


# FUNCTIONS

# Merge chunks into continuous text with overlap deduplication
def merge_chunks(chunks: list[dict]) -> str:
    if not chunks:
        return ""
    result = chunks[0]['content']
    for i in range(1, len(chunks)):
        overlap = find_overlap(result, chunks[i]['content'])
        result += "\n\n" + chunks[i]['content'][overlap:]
    return result


# Find longest suffix of text1 that is prefix of text2
def find_overlap(text1: str, text2: str, max_overlap: int = 300) -> int:
    for size in range(min(len(text1), len(text2), max_overlap), 0, -1):
        if text1[-size:] == text2[:size]:
            return size
    return 0
