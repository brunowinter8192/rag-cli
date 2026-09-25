# INFRASTRUCTURE
from src.rag.db import get_connection, query_documents, validate_collection


# ORCHESTRATOR

def list_documents_workflow(collection: str, document: str | None = None, filter: str | None = None, exclude: str | None = None) -> list[dict]:
    conn = get_connection()
    validate_collection(conn, collection)
    results = query_documents(conn, collection, document, filter, exclude)
    conn.close()
    return results
