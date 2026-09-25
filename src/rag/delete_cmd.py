# INFRASTRUCTURE
import shutil

from src.rag.config import RAG_ROOT
from src.rag.db import get_connection
from src.rag.indexer import delete_chunks


# ORCHESTRATOR

def delete_workflow(
    collection: str,
    document: str | None = None,
) -> dict:
    require_collection(collection)
    conn = get_connection(purpose="write")
    deleted = delete_chunks(conn, collection, document)
    delete_manifest_rows(conn, collection, document)
    conn.close()
    remove_source_files(collection, document)
    return {"chunks_deleted": deleted}


# FUNCTIONS

def require_collection(collection: str) -> None:
    if not collection:
        raise ValueError("--collection is required")


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


def remove_source_files(collection: str, document: str | None) -> None:
    coll_dir = RAG_ROOT / "data" / "documents" / collection
    if document:
        md_path = coll_dir / document
        json_path = md_path.with_suffix(".json")
        for candidate in (md_path, json_path):
            if candidate.exists() and candidate.is_file():
                candidate.unlink()
    elif coll_dir.exists() and coll_dir.is_dir():
        shutil.rmtree(coll_dir)
