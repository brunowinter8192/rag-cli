# INFRASTRUCTURE
import json
import logging
import os
from pathlib import Path

from dotenv import load_dotenv

from .db import get_connection
from .embedder import embed_workflow

load_dotenv()

LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    filename=LOG_DIR / "indexer.log",
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

VECTOR_DIMENSION = int(os.getenv("VECTOR_DIMENSION", "4096"))
BATCH_SIZE = 32


# ORCHESTRATOR


# Index from chunks.json (pre-chunked, LLM-cleaned)
def index_json_workflow(json_path: str) -> int:
    conn_ddl = get_connection(purpose="ddl")
    ensure_schema(conn_ddl)
    conn_ddl.close()
    conn = get_connection(purpose="write")

    chunks = load_chunks_json(json_path)
    if not chunks:
        conn.close()
        return 0

    collection = chunks[0]["collection"]
    documents = {c["document"] for c in chunks}
    for doc in sorted(documents):
        deleted = delete_chunks(conn, collection, doc)
        if deleted > 0:
            print(f"Deleted {deleted} existing chunks for {collection}/{doc}")

    total = len(chunks)
    skipped_total = 0
    for i in range(0, total, BATCH_SIZE):
        batch = chunks[i:i + BATCH_SIZE]
        texts = [c["content"] for c in batch]
        embeddings = embed_workflow(texts, "search_document: ")
        skipped = store_chunks(conn, batch, embeddings)
        skipped_total += skipped
        suffix = f" ({skipped} NULL skipped)" if skipped else ""
        print(f"Indexed {min(i + BATCH_SIZE, total)}/{total} chunks{suffix}")

    conn.close()
    indexed = total - skipped_total
    logging.info(f"Indexed {indexed}/{total} chunks from {json_path} ({skipped_total} skipped)")
    return indexed


# Delete chunks + manifest + source files for a collection (and optionally a document)
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

# Load chunks from JSON file
def load_chunks_json(json_path: str) -> list[dict]:
    path = Path(json_path)
    if not path.exists():
        raise FileNotFoundError(f"chunks.json not found: {json_path}")

    with open(path) as f:
        data = json.load(f)

    collection = data.get("collection", path.parent.name)
    document = data.get("document", path.stem + ".md")
    raw_chunks = data.get("chunks", [])
    total = len(raw_chunks)

    return [
        {
            "content": c["content"],
            "collection": collection,
            "document": c.get("document", document),
            "chunk_index": c["index"],
            "total_chunks": total
        }
        for c in raw_chunks
    ]


# Ensure pgvector extension and table exist
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
    logging.info("Schema ensured")


# Delete all chunks for a collection
def delete_collection(conn, collection: str) -> int:
    with conn.cursor() as cur:
        cur.execute("DELETE FROM documents WHERE collection = %s", (collection,))
        deleted = cur.rowcount
    conn.commit()
    return deleted


# Check if a document has a complete chunk set in the documents table.
# Complete means COUNT(*) > 0 AND COUNT(*) == MAX(total_chunks) — every
# expected chunk-row is present. Used by workflow.py index-dir / index-file
# to detect documents that were indexed before indexed_files tracking
# existed (adopt-on-complete pattern: register hash without re-embed).
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


# Delete chunks by collection and/or document
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


# Delete indexed_files manifest rows matching the same scope as delete_chunks
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


# Format sparse vector for pgvector sparsevec type: '{idx1:val1,idx2:val2}/dimensions'
def format_sparsevec(sparse: dict, dimensions: int = 30522) -> str:
    pairs = ",".join(f"{idx}:{val}" for idx, val in zip(sparse["indices"], sparse["values"]))
    return f"{{{pairs}}}/{dimensions}"


# Store chunks with dense embeddings in PostgreSQL; sparse_embedding stays NULL for new chunks.
# Returns count of chunks SKIPPED because the embedding model returned a NULL vector.
def store_chunks(conn, chunks: list[dict], embeddings: list[list[float]], sparse_embeddings: list[dict] | None = None) -> int:
    skipped = 0
    with conn.cursor() as cur:
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            if embedding is None or all(v is None for v in embedding):
                logging.warning(f"NULL embedding skipped: collection={chunk['collection']} document={chunk['document']} chunk_index={chunk['chunk_index']}")
                skipped += 1
                continue
            sparse_val = format_sparsevec(sparse_embeddings[i]) if sparse_embeddings else None
            cur.execute(
                """
                INSERT INTO documents (content, collection, document, chunk_index, total_chunks, embedding, sparse_embedding)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    chunk["content"],
                    chunk["collection"],
                    chunk["document"],
                    chunk["chunk_index"],
                    chunk["total_chunks"],
                    embedding,
                    sparse_val
                )
            )
    conn.commit()
    if skipped:
        logging.warning(f"Skipped {skipped} chunks with NULL embeddings")
    return skipped

