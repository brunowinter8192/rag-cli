# INFRASTRUCTURE

import hashlib
import json
from pathlib import Path

from .chunker import chunk_workflow
from .db import get_connection
from .indexer import (
    _embed_store_batches,
    delete_chunks,
    ensure_schema,
)
from .lock import update_progress
from .server_manager import ensure_ready
from .log_setup import get_logger

logger = get_logger("sync")

MANIFEST_NAME = ".rag-docs.json"

GLOB_EXCLUDE_DIRS = frozenset({".git", "venv", "node_modules", "__pycache__"})


# ORCHESTRATOR

def sync_docs_workflow(
    project_root: str | Path,
    chunk_size: int = 2000,
    overlap: int = 400,
) -> dict:
    project_root = Path(project_root).expanduser().resolve()

    if not project_root.is_dir():
        raise FileNotFoundError(f"Project root not found: {project_root}")

    manifest = read_manifest(project_root)

    conn = get_connection(purpose="ddl")
    ensure_schema(conn)
    ensure_indexed_files_table(conn)

    if "collections" in manifest:
        results = {}
        for entry in manifest["collections"]:
            name = entry["name"]
            includes = entry["include"]
            results[name] = _sync_one_collection(
                conn, project_root, name, includes, chunk_size, overlap
            )
        conn.close()
        return results

    collection = manifest["collection"]
    includes = manifest["include"]
    result = _sync_one_collection(
        conn, project_root, collection, includes, chunk_size, overlap
    )
    conn.close()
    return result


# FUNCTIONS

def _sync_one_collection(
    conn,
    project_root: Path,
    collection: str,
    includes: list[str],
    chunk_size: int,
    overlap: int,
) -> dict:
    files = expand_globs(project_root, includes)

    db_hashes = get_db_hashes(conn, collection)
    current_hashes = {rel: compute_hash(path) for rel, path in files.items()}
    added, removed, updated, unchanged = _diff_hashes(current_hashes, db_hashes)

    to_index = added + updated

    if to_index:
        ensure_ready("index")

    total_chunks = _index_to_index_files(conn, collection, files, to_index, current_hashes, chunk_size, overlap)

    for rel in removed:
        delete_chunks(conn, collection, rel)
        delete_indexed_file(conn, collection, rel)

    logger.info(
        f"sync_docs {collection}: +{len(added)} ~{len(updated)} -{len(removed)} ={len(unchanged)} "
        f"({total_chunks} chunks indexed)"
    )

    return {
        "collection": collection,
        "added": added,
        "updated": updated,
        "removed": removed,
        "unchanged": unchanged,
        "total_chunks_indexed": total_chunks,
    }


def _diff_hashes(
    current_hashes: dict[str, str], db_hashes: dict[str, str]
) -> tuple[list[str], list[str], list[str], list[str]]:
    added = sorted(r for r in current_hashes if r not in db_hashes)
    removed = sorted(r for r in db_hashes if r not in current_hashes)
    updated = sorted(
        r for r in current_hashes
        if r in db_hashes and current_hashes[r] != db_hashes[r]
    )
    unchanged = sorted(
        r for r in current_hashes
        if r in db_hashes and current_hashes[r] == db_hashes[r]
    )
    return added, removed, updated, unchanged


def _index_to_index_files(
    conn,
    collection: str,
    files: dict[str, Path],
    to_index: list[str],
    current_hashes: dict[str, str],
    chunk_size: int,
    overlap: int,
) -> int:
    total_chunks = 0
    for i, rel in enumerate(to_index):
        n = index_file(
            conn, files[rel],
            collection=collection,
            document=rel,
            chunk_size=chunk_size,
            overlap=overlap,
            doc_done=i,
            docs_total=len(to_index),
        )
        upsert_hash(conn, collection, rel, current_hashes[rel])
        update_progress(done=i + 1, total=len(to_index), current_document=rel, collection=collection)
        total_chunks += n
    return total_chunks


def read_manifest(project_root: Path) -> dict:
    path = project_root / MANIFEST_NAME
    if not path.is_file():
        raise FileNotFoundError(
            f"No {MANIFEST_NAME} found in {project_root}. "
            f"Create one with: {{\"collection\": \"<name>\", \"include\": [\"<glob>\", ...]}}"
        )
    data = json.loads(path.read_text())

    if "collections" in data:
        if not isinstance(data["collections"], list) or not data["collections"]:
            raise ValueError(
                f"Manifest 'collections' must be a non-empty list: {path}"
            )
        for i, entry in enumerate(data["collections"]):
            if not isinstance(entry.get("name"), str) or not entry["name"]:
                raise ValueError(
                    f"Manifest collections[{i}] must have a non-empty 'name': {path}"
                )
            if not isinstance(entry.get("include"), list) or not entry["include"]:
                raise ValueError(
                    f"Manifest collections[{i}] must have a non-empty 'include' list: {path}"
                )
        return data

    if "collection" not in data or "include" not in data:
        raise ValueError(
            f"Manifest must have 'collection' and 'include' keys (or 'collections' for multi): {path}"
        )
    if not isinstance(data["collection"], str) or not data["collection"]:
        raise ValueError(f"Manifest 'collection' must be a non-empty string: {path}")
    if not isinstance(data["include"], list) or not data["include"]:
        raise ValueError(
            f"Manifest 'include' must be a non-empty list of glob patterns: {path}"
        )
    return data


def _is_excluded_path(parts: tuple[str, ...]) -> bool:
    if any(part in GLOB_EXCLUDE_DIRS for part in parts):
        return True
    for i in range(len(parts) - 1):
        if parts[i] == ".claude" and parts[i + 1] == "worktrees":
            return True
    return False


def expand_globs(project_root: Path, includes: list[str]) -> dict[str, Path]:
    seen: dict[str, Path] = {}
    for pattern in includes:
        for path in project_root.glob(pattern):
            if path.is_file() and path.suffix == ".md":
                rel = str(path.relative_to(project_root))
                if not _is_excluded_path(Path(rel).parts):
                    seen[rel] = path
    return seen


def compute_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ensure_indexed_files_table(conn) -> None:
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS indexed_files (
                collection TEXT NOT NULL,
                document TEXT NOT NULL,
                sha256 TEXT NOT NULL,
                last_indexed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                PRIMARY KEY (collection, document)
            )
        """)
    conn.commit()


def get_db_hashes(conn, collection: str) -> dict[str, str]:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT document, sha256 FROM indexed_files WHERE collection = %s",
            (collection,),
        )
        return {row[0]: row[1] for row in cur.fetchall()}


def upsert_hash(conn, collection: str, document: str, sha256: str) -> None:
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO indexed_files (collection, document, sha256, last_indexed_at)
            VALUES (%s, %s, %s, NOW())
            ON CONFLICT (collection, document) DO UPDATE
            SET sha256 = EXCLUDED.sha256, last_indexed_at = NOW()
        """, (collection, document, sha256))
    conn.commit()


def delete_indexed_file(conn, collection: str, document: str) -> None:
    with conn.cursor() as cur:
        cur.execute(
            "DELETE FROM indexed_files WHERE collection = %s AND document = %s",
            (collection, document),
        )
    conn.commit()


def index_file(
    conn,
    file_path: Path,
    collection: str,
    document: str,
    chunk_size: int = 2000,
    overlap: int = 400,
    doc_done: int | None = None,
    docs_total: int | None = None,
) -> int:
    raw_chunks = chunk_workflow(str(file_path), chunk_size, overlap)

    delete_chunks(conn, collection, document)

    if not raw_chunks:
        return 0

    total = len(raw_chunks)
    chunks = [
        {
            "content": c["content"],
            "collection": collection,
            "document": document,
            "chunk_index": i,
            "total_chunks": total,
        }
        for i, c in enumerate(raw_chunks)
    ]

    _embed_store_batches(conn, chunks, document, collection, doc_done, docs_total, verbose=False)
    return total
