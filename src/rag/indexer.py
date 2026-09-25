# INFRASTRUCTURE
import json
import os
from pathlib import Path

from dotenv import load_dotenv

from .db import get_connection
from .embedder import embed_workflow
from .lock import update_progress
from .log_setup import get_logger

load_dotenv()

logger = get_logger("indexer")

VECTOR_DIMENSION = int(os.environ["VECTOR_DIMENSION"])
BATCH_SIZE = 32


# ORCHESTRATOR


def index_json_workflow(
    json_path: str,
    doc_done: int | None = None,
    docs_total: int | None = None,
) -> int:
    conn_ddl = get_connection(purpose="ddl")
    ensure_schema(conn_ddl)
    conn_ddl.close()
    conn = get_connection(purpose="write")

    chunks = load_chunks_json(json_path)
    if not chunks:
        conn.close()
        return 0

    collection = chunks[0]["collection"]
    current_document = chunks[0]["document"]
    documents = {c["document"] for c in chunks}
    for doc in sorted(documents):
        deleted = delete_chunks(conn, collection, doc)
        if deleted > 0:
            print(f"Deleted {deleted} existing chunks for {collection}/{doc}")

    total = len(chunks)
    skipped_total = _embed_store_batches(
        conn, chunks, current_document, collection, doc_done, docs_total, verbose=True
    )

    conn.close()
    indexed = total - skipped_total
    logger.info(f"Indexed {indexed}/{total} chunks from {json_path} ({skipped_total} skipped)")
    return indexed


def delete_workflow(
    collection: str,
    document: str | None = None,
) -> dict:
    if not collection:
        raise ValueError("--collection is required")
    conn = get_connection(purpose="write")
    deleted = delete_chunks(conn, collection, document)
    delete_manifest_rows(conn, collection, document)
    conn.close()
    import shutil
    from .server_manager import RAG_ROOT
    coll_dir = RAG_ROOT / "data" / "documents" / collection
    if document:
        md_path = coll_dir / document
        json_path = md_path.with_suffix(".json")
        for candidate in (md_path, json_path):
            if candidate.exists() and candidate.is_file():
                candidate.unlink()
    elif coll_dir.exists() and coll_dir.is_dir():
        shutil.rmtree(coll_dir)
    return {"chunks_deleted": deleted}


# FUNCTIONS

def _embed_store_batches(
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
        cur.execute("ALTER TABLE documents ADD COLUMN IF NOT EXISTS sparse_embedding sparsevec(30522)")
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


def delete_manifest_rows(conn, collection: str | None, document: str | None) -> int:
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
        cur.execute(f"DELETE FROM indexed_files WHERE {where}", params)
        deleted = cur.rowcount
    conn.commit()
    return deleted


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

