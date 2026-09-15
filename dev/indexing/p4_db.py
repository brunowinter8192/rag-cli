# INFRASTRUCTURE
import logging

import psycopg2
from pgvector.psycopg2 import register_vector

logger = logging.getLogger(__name__)

DB_HOST = "localhost"
DB_PORT = 5433
DB_USER = "rag"
DB_PASSWORD = "rag"
SPARSE_DIMS = 30522
RRF_K = 60


# FUNCTIONS

def get_connection(db_name: str = "rag_test"):
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        dbname=db_name,
    )
    with conn.cursor() as cur:
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
    conn.commit()
    register_vector(conn)
    return conn


def ensure_schema(conn, vector_dim: int = 4096) -> None:
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
                embedding vector({vector_dim}),
                sparse_embedding sparsevec({SPARSE_DIMS})
            )
        """)
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
    logger.info(f"Schema ensured (vector_dim={vector_dim})")


def clear_collection(conn, collection: str) -> int:
    with conn.cursor() as cur:
        cur.execute("DELETE FROM documents WHERE collection = %s", (collection,))
        deleted = cur.rowcount
    conn.commit()
    return deleted


def format_sparsevec(sparse: dict, dimensions: int = SPARSE_DIMS) -> str:
    pairs = ",".join(f"{idx}:{val}" for idx, val in zip(sparse["indices"], sparse["values"]))
    return f"{{{pairs}}}/{dimensions}"


def store_chunks(conn, chunks: list[dict], embeddings: list[list[float]], sparse_embeddings: list[dict]) -> None:
    with conn.cursor() as cur:
        for chunk, embedding, sparse in zip(chunks, embeddings, sparse_embeddings):
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
                    format_sparsevec(sparse),
                ),
            )
    conn.commit()


def search_dense(conn, query_embedding: list[float], collection: str, top_k: int) -> list[dict]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT content, collection, document, chunk_index,
                   1 - (embedding <=> %s::vector) as score
            FROM documents
            WHERE collection = %s
            ORDER BY embedding <=> %s::vector
            LIMIT %s
            """,
            (query_embedding, collection, query_embedding, top_k),
        )
        rows = cur.fetchall()
    return [
        {
            "content": row[0],
            "collection": row[1],
            "document": row[2],
            "chunk_index": row[3],
            "score": round(float(row[4]), 4),
        }
        for row in rows
    ]


def search_sparse(conn, query_sparse: dict, collection: str, top_k: int) -> list[dict]:
    sparsevec = format_sparsevec(query_sparse)
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT content, collection, document, chunk_index,
                   1 - (sparse_embedding <=> %s::sparsevec) as score
            FROM documents
            WHERE collection = %s
            ORDER BY sparse_embedding <=> %s::sparsevec
            LIMIT %s
            """,
            (sparsevec, collection, sparsevec, top_k),
        )
        rows = cur.fetchall()
    return [
        {
            "content": row[0],
            "collection": row[1],
            "document": row[2],
            "chunk_index": row[3],
            "score": round(float(row[4]), 4),
        }
        for row in rows
    ]


def search_hybrid(conn, dense_results: list[dict], sparse_results: list[dict], rrf_k: int = RRF_K) -> list[dict]:
    scores = {}
    chunks = {}

    for rank, r in enumerate(dense_results, start=1):
        key = (r["collection"], r["document"], r["chunk_index"])
        scores[key] = scores.get(key, 0.0) + 1.0 / (rrf_k + rank)
        chunks[key] = r

    for rank, r in enumerate(sparse_results, start=1):
        key = (r["collection"], r["document"], r["chunk_index"])
        scores[key] = scores.get(key, 0.0) + 1.0 / (rrf_k + rank)
        if key not in chunks:
            chunks[key] = r

    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [{**chunks[key], "score": round(score, 6)} for key, score in ranked]


def search_cc(conn, dense_results: list[dict], sparse_results: list[dict], alpha: float = 0.8) -> list[dict]:
    max_dense = max((r["score"] for r in dense_results), default=0.0)
    max_sparse = max((r["score"] for r in sparse_results), default=0.0)

    scores = {}
    chunks = {}

    if max_dense > 0:
        for r in dense_results:
            key = (r["collection"], r["document"], r["chunk_index"])
            scores[key] = alpha * (r["score"] / max_dense)
            chunks[key] = r

    if max_sparse > 0:
        for r in sparse_results:
            key = (r["collection"], r["document"], r["chunk_index"])
            sparse_contrib = (1 - alpha) * (r["score"] / max_sparse)
            scores[key] = scores.get(key, 0.0) + sparse_contrib
            if key not in chunks:
                chunks[key] = r

    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [{**chunks[key], "score": round(score, 6)} for key, score in ranked]


def ensure_collections_schema(conn) -> None:
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS collections (
                name TEXT PRIMARY KEY,
                embedding_model TEXT,
                embedding_dims INTEGER,
                sparse_model TEXT,
                chunk_size INTEGER,
                overlap INTEGER,
                db_name TEXT,
                indexed_at TIMESTAMPTZ,
                doc_count INTEGER,
                chunk_count INTEGER,
                notes TEXT
            )
        """)
    conn.commit()
    logger.info("Collections schema ensured")


def upsert_collection_metadata(
    conn,
    name: str,
    embedding_model: str,
    embedding_dims: int,
    sparse_model: str | None,
    chunk_size: int,
    overlap: int,
    db_name: str,
    indexed_at,
    doc_count: int,
    chunk_count: int,
    notes: str | None = None,
) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO collections (
                name, embedding_model, embedding_dims, sparse_model,
                chunk_size, overlap, db_name, indexed_at,
                doc_count, chunk_count, notes
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (name) DO UPDATE SET
                embedding_model = EXCLUDED.embedding_model,
                embedding_dims  = EXCLUDED.embedding_dims,
                sparse_model    = EXCLUDED.sparse_model,
                chunk_size      = EXCLUDED.chunk_size,
                overlap         = EXCLUDED.overlap,
                db_name         = EXCLUDED.db_name,
                indexed_at      = EXCLUDED.indexed_at,
                doc_count       = EXCLUDED.doc_count,
                chunk_count     = EXCLUDED.chunk_count,
                notes           = EXCLUDED.notes
            """,
            (
                name, embedding_model, embedding_dims, sparse_model,
                chunk_size, overlap, db_name, indexed_at,
                doc_count, chunk_count, notes,
            ),
        )
    conn.commit()
    logger.info(f"Collection metadata upserted: {name} ({chunk_count} chunks, {doc_count} docs)")
