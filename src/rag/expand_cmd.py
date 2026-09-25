# INFRASTRUCTURE
import time

from src.rag.config import DEFAULT_OVERLAP
from src.rag.db import fetch_chunk_range, get_connection, validate_collection
from src.rag.expand_log import log_expand


# ORCHESTRATOR

def expand_chunks_workflow(collection: str, document: str, chunk_index: int, before: int = 0, after: int = 0) -> dict:
    started = time.perf_counter()
    chunks = fetch_chunks(collection, document, chunk_index, before, after)
    result = build_expand_result(chunks, collection, document, chunk_index, before, after)
    log_expand(result, started)
    return result


# FUNCTIONS

def fetch_chunks(collection: str, document: str, chunk_index: int, before: int, after: int) -> list[dict]:
    conn = get_connection()
    validate_collection(conn, collection)
    chunks = fetch_chunk_range(conn, collection, document, chunk_index - before, chunk_index + after)
    conn.close()
    return chunks


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
