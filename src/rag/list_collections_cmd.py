# INFRASTRUCTURE
from src.rag.db import get_connection, query_collections


# ORCHESTRATOR

def list_collections_workflow(filter: str | None = None) -> list[dict]:
    conn = get_connection()
    results = query_collections(conn, filter)
    conn.close()
    return results
