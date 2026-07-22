# INFRASTRUCTURE

from .db import add_document_filter, add_document_exclude
from .embedder import embed_workflow

DEFAULT_QUERY_PREFIX = "Instruct: Given a search query, retrieve relevant passages that answer the query\nQuery: "


# FUNCTIONS

# Embed search query with Qwen3 instruct prefix
def embed_query(query: str) -> list[float]:
    embeddings = embed_workflow(query, prefix=DEFAULT_QUERY_PREFIX)
    return embeddings[0]


# Search vectors in PostgreSQL using cosine distance
def search_vectors(
    conn,
    query_vector: list[float],
    top_k: int,
    collection: str | None = None,
    document: str | None = None,
    exclude: str | None = None
) -> list[dict]:
    where_clauses = []
    where_params = []

    if collection:
        where_clauses.append("collection = %s")
        where_params.append(collection)
    if document:
        where_clauses, where_params = add_document_filter(where_clauses, where_params, document)
    if exclude:
        where_clauses, where_params = add_document_exclude(where_clauses, where_params, exclude)

    where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
    params = [query_vector] + where_params + [query_vector, top_k]

    with conn.cursor() as cur:
        cur.execute(
            f"""
            SELECT content, collection, document, chunk_index,
                   1 - (embedding <=> %s::vector) as score
            FROM documents
            {where_sql}
            ORDER BY embedding <=> %s::vector
            LIMIT %s
            """,
            params
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

