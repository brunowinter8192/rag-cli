# INFRASTRUCTURE
import json
import os
from pathlib import Path

from dotenv import load_dotenv

from src.rag.db import get_connection
from src.rag.embedder import embed_workflow
from src.rag.lock import update_progress
from src.rag.log_setup import get_logger

load_dotenv()

logger = get_logger("indexer")

VECTOR_DIMENSION = int(os.environ["VECTOR_DIMENSION"])
SPARSE_DIMENSION = 30522
BATCH_SIZE = 32


# ORCHESTRATOR

def index_json_workflow(
    json_path: str,
    doc_done: int | None = None,
    docs_total: int | None = None,
) -> int:
    prepare_schema()
    chunks = load_chunks_json(json_path)
    if not chunks:
        return 0
    conn = get_connection(purpose="write")
    replace_existing_chunks(conn, chunks)
    skipped_total = store_all_chunks(conn, chunks, doc_done, docs_total)
    conn.close()
    return record_indexed(json_path, chunks, skipped_total)


# FUNCTIONS

def prepare_schema() -> None:
    conn_ddl = get_connection(purpose="ddl")
    ensure_schema(conn_ddl)
    conn_ddl.close()


def ensure_schema(conn) -> None:
    with conn.cursor() as cur:
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
        cur.execute(f"""
            CREATE TABLE IF NOT EXISTS documents (
                id SERIAL PRIMARY KEY,
                content TEXT NOT NULL,
                collection TEXT NOT NULL,
                document TEXT NOT NULL,
                chunk_index INTEGER NOT NULL,
                total_chunks INTEGER NOT NULL,
                embedding vector({VECTOR_DIMENSION})
            )
        """)
        cur.execute(f"ALTER TABLE documents ADD COLUMN IF NOT EXISTS sparse_embedding sparsevec({SPARSE_DIMENSION})")
        cur.execute("""
            DO $$ BEGIN
                ALTER TABLE documents ADD COLUMN tsv tsvector
                    GENERATED ALWAYS AS (to_tsvector('english', content)) STORED;
            EXCEPTION WHEN duplicate_column THEN NULL;
            END $$
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_documents_tsv ON documents USING gin(tsv)")
        cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_documents_unique ON documents(collection, document, chunk_index)")
    conn.commit()
    logger.info("Schema ensured")


def load_chunks_json(json_path: str) -> list[dict]:
    path = Path(json_path)
    if not path.exists():
        raise FileNotFoundError(f"chunks.json not found: {json_path}")

    with open(path) as f:
        data = json.load(f)

    collection = data["collection"]
    document = data["document"]
    raw_chunks = data["chunks"]
    total = len(raw_chunks)

    return [
        {
            "content": c["content"],
            "collection": collection,
            "document": document,
            "chunk_index": c["index"],
            "total_chunks": total
        }
        for c in raw_chunks
    ]


def replace_existing_chunks(conn, chunks: list[dict]) -> None:
    collection = chunks[0]["collection"]
    for doc in sorted({c["document"] for c in chunks}):
        deleted = delete_chunks(conn, collection, doc)
        if deleted > 0:
            print(f"Deleted {deleted} existing chunks for {collection}/{doc}")


def delete_chunks(conn, collection: str | None, document: str | None) -> int:
    conditions = []
    params = []
    if collection:
        conditions.append("collection = %s")
        params.append(collection)
    if document:
        conditions.append("document = %s")
        params.append(document)

    where = " AND ".join(conditions)
    with conn.cursor() as cur:
        cur.execute(f"DELETE FROM documents WHERE {where}", params)
        deleted = cur.rowcount
    conn.commit()
    return deleted


def store_all_chunks(conn, chunks: list[dict], doc_done: int | None, docs_total: int | None) -> int:
    return embed_store_batches(
        conn, chunks, chunks[0]["document"], chunks[0]["collection"], doc_done, docs_total, verbose=True
    )


def embed_store_batches(
    conn,
    chunks: list[dict],
    document: str,
    collection: str,
    doc_done: int | None,
    docs_total: int | None,
    verbose: bool,
) -> int:
    total = len(chunks)
    _write_chunk_progress = doc_done is not None and docs_total is not None
    if _write_chunk_progress:
        update_progress(
            done=doc_done, total=docs_total,
            current_document=document, collection=collection,
            chunks_done=0, chunks_total=total,
        )

    skipped_total = 0
    for i in range(0, total, BATCH_SIZE):
        batch = chunks[i:i + BATCH_SIZE]
        texts = [c["content"] for c in batch]
        embeddings = embed_workflow(texts, "search_document: ")
        skipped = store_chunks(conn, batch, embeddings)
        skipped_total += skipped
        chunks_done = min(i + BATCH_SIZE, total)
        if verbose:
            suffix = f" ({skipped} NULL skipped)" if skipped else ""
            print(f"Indexed {chunks_done}/{total} chunks{suffix}")
        if _write_chunk_progress:
            update_progress(
                done=doc_done, total=docs_total,
                current_document=document, collection=collection,
                chunks_done=chunks_done, chunks_total=total,
            )

    return skipped_total


def store_chunks(conn, chunks: list[dict], embeddings: list[list[float]]) -> int:
    skipped = 0
    with conn.cursor() as cur:
        for chunk, embedding in zip(chunks, embeddings):
            if all(v is None for v in embedding):
                logger.warning(f"NULL embedding skipped: collection={chunk['collection']} document={chunk['document']} chunk_index={chunk['chunk_index']}")
                skipped += 1
                continue
            cur.execute(
                """
                INSERT INTO documents (content, collection, document, chunk_index, total_chunks, embedding)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    chunk["content"],
                    chunk["collection"],
                    chunk["document"],
                    chunk["chunk_index"],
                    chunk["total_chunks"],
                    embedding
                )
            )
    conn.commit()
    if skipped:
        logger.warning(f"Skipped {skipped} chunks with NULL embeddings")
    return skipped


def record_indexed(json_path: str, chunks: list[dict], skipped_total: int) -> int:
    total = len(chunks)
    indexed = total - skipped_total
    logger.info(f"Indexed {indexed}/{total} chunks from {json_path} ({skipped_total} skipped)")
    return indexed


def doc_is_complete(conn, collection: str, document: str) -> bool:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT COUNT(*), MAX(total_chunks)
            FROM documents
            WHERE collection = %s AND document = %s
            """,
            (collection, document),
        )
        actual, expected = cur.fetchone()
    return actual is not None and actual > 0 and actual == expected
