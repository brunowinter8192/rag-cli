# INFRASTRUCTURE
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from p1_chunker import chunk_file
from p2_embedder import embed
from p3_sparse_embedder import embed_sparse
from p4_db import store_chunks

logger = logging.getLogger(__name__)

BATCH_SIZE = 32


# ORCHESTRATOR

def index_file(md_path: str, collection: str, db_conn) -> int:
    chunks = chunk_file(md_path)
    if not chunks:
        return 0
    for chunk in chunks:
        chunk["collection"] = collection

    total = len(chunks)
    for i in range(0, total, BATCH_SIZE):
        batch = chunks[i:i + BATCH_SIZE]
        texts = [c["content"] for c in batch]
        embeddings, sparse_embeddings = _parallel_embed(texts)
        store_chunks(db_conn, batch, embeddings, sparse_embeddings)

    logger.info(f"Indexed {total} chunks from {md_path} into {collection}")
    return total


def index_directory(dir_path: str, collection: str, db_conn) -> dict:
    md_files = sorted(Path(dir_path).glob("*.md"))
    if not md_files:
        return {"files": 0, "chunks": 0, "errors": [], "per_file": [], "elapsed": 0.0}

    stats = {"files": 0, "chunks": 0, "errors": [], "per_file": []}
    start = time.time()

    for md_path in md_files:
        try:
            chunks = chunk_file(str(md_path))
            if not chunks:
                continue
            for chunk in chunks:
                chunk["collection"] = collection

            file_chunks = len(chunks)
            avg_size = sum(len(c["content"]) for c in chunks) // file_chunks

            for i in range(0, file_chunks, BATCH_SIZE):
                batch = chunks[i:i + BATCH_SIZE]
                texts = [c["content"] for c in batch]
                embeddings, sparse_embeddings = _parallel_embed(texts)
                store_chunks(db_conn, batch, embeddings, sparse_embeddings)

            stats["files"] += 1
            stats["chunks"] += file_chunks
            stats["per_file"].append({
                "filename": md_path.name,
                "chunks": file_chunks,
                "avg_chunk_size": avg_size,
            })
        except Exception as e:
            logger.error(f"Error indexing {md_path}: {e}")
            stats["errors"].append({"file": md_path.name, "error": str(e)})

    stats["elapsed"] = time.time() - start
    return stats


# FUNCTIONS

def _parallel_embed(texts: list[str]) -> tuple[list[list[float]], list[dict]]:
    with ThreadPoolExecutor(max_workers=2) as executor:
        dense_future = executor.submit(embed, texts)
        sparse_future = executor.submit(embed_sparse, texts)
        return dense_future.result(), sparse_future.result()
