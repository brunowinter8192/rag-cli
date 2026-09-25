# INFRASTRUCTURE
from src.rag.db import get_connection, query_progress, validate_collection


# ORCHESTRATOR

def progress_workflow(collection: str) -> list[dict]:
    conn = get_connection()
    validate_collection(conn, collection)
    results = query_progress(conn, collection)
    conn.close()
    return results
