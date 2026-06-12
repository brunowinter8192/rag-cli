# INFRASTRUCTURE
"""Project doc indexing — manifest-driven sync with hash-based change detection.

Each project that wants its docs indexed places a `.rag-docs.json` at its root.

Single-collection format (legacy, still supported):

    {
      "collection": "Trading_internal",
      "include": [
        "decisions/*.md",
        "concepts/*.md",
        "strategies/**/*.md",
        "CLAUDE.md"
      ]
    }

Multi-collection format:

    {
      "collections": [
        {"name": "Trading_internal", "include": ["decisions/*.md", "CLAUDE.md"]},
        {"name": "Trading_archive",  "include": ["archive/**/*.md"]}
      ]
    }

Detection: presence of "collections" key → multi-collection. Else: single-collection.

`sync_docs_workflow(project_root)` reads the manifest, expands the globs,
hashes every matched file, diffs against the `indexed_files` table in
postgres, and performs only the necessary add/update/remove operations.
Unchanged files are skipped — no embedder calls.

Return value:
  Single-collection: flat dict with collection, added, updated, removed, unchanged, total_chunks_indexed.
  Multi-collection:  dict keyed by collection name, each value is the per-collection flat dict.
"""

import hashlib
import json
import logging
from pathlib import Path

from .chunker import chunk_workflow
from .db import get_connection
from .embedder import embed_workflow
from .indexer import (
    BATCH_SIZE,
    delete_chunks,
    ensure_schema,
    store_chunks,
)
from .lock import update_progress
from .server_manager import ensure_ready

LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    filename=LOG_DIR / "sync.log",
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

MANIFEST_NAME = ".rag-docs.json"

# Directories excluded from glob expansion — checked on path COMPONENTS, not substring
GLOB_EXCLUDE_DIRS = frozenset({".git", "venv", "node_modules", "__pycache__"})


# ORCHESTRATOR

def sync_docs_workflow(
    project_root: str | Path,
    chunk_size: int = 2000,
    overlap: int = 400,
) -> dict:
    """Sync project docs into RAG collection(s) per `.rag-docs.json` manifest.

    Single-collection manifest → returns flat result dict (backward-compatible):
        {"collection": str, "added": [...], "updated": [...],
         "removed": [...], "unchanged": [...], "total_chunks_indexed": int}

    Multi-collection manifest → returns dict keyed by collection name:
        {"col_a": {flat result dict}, "col_b": {flat result dict}, ...}
    """
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

    # Single-collection (legacy) path
    collection = manifest["collection"]
    includes = manifest["include"]
    result = _sync_one_collection(
        conn, project_root, collection, includes, chunk_size, overlap
    )
    conn.close()
    return result


# FUNCTIONS

# Sync a single collection — hash diff + embed new/updated + delete removed
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

    to_index = added + updated

    # Embedder + SPLADE only needed when we have new content to embed.
    # Removed-only runs are pure DB deletes — no GPU cost.
    if to_index:
        ensure_ready("index")

    total_chunks = 0
    for i, rel in enumerate(to_index):
        n = index_file(
            conn, files[rel],
            collection=collection,
            document=rel,
            chunk_size=chunk_size,
            overlap=overlap,
        )
        upsert_hash(conn, collection, rel, current_hashes[rel])
        update_progress(done=i + 1, total=len(to_index), current_document=rel, collection=collection)
        total_chunks += n

    for rel in removed:
        delete_chunks(conn, collection, rel)
        delete_indexed_file(conn, collection, rel)

    logging.info(
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


# Read and validate .rag-docs.json — accepts single-collection and multi-collection formats
def read_manifest(project_root: Path) -> dict:
    path = project_root / MANIFEST_NAME
    if not path.is_file():
        raise FileNotFoundError(
            f"No {MANIFEST_NAME} found in {project_root}. "
            f"Create one with: {{\"collection\": \"<name>\", \"include\": [\"<glob>\", ...]}}"
        )
    data = json.loads(path.read_text())

    if "collections" in data:
        # Multi-collection format
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

    # Single-collection format (legacy)
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


# Return True if path components include an excluded dir or the .claude/worktrees/ subtree
def _is_excluded_path(parts: tuple[str, ...]) -> bool:
    if any(part in GLOB_EXCLUDE_DIRS for part in parts):
        return True
    for i in range(len(parts) - 1):
        if parts[i] == ".claude" and parts[i + 1] == "worktrees":
            return True
    return False


# Expand glob patterns relative to project_root, excluding build/worktree dirs by component
def expand_globs(project_root: Path, includes: list[str]) -> dict[str, Path]:
    """Return {relative_path_str: absolute_Path} for every .md file matched.

    Files matched by multiple patterns are de-duplicated via the relative-path key.
    Only `.md` files are kept. Paths whose components include any entry from
    GLOB_EXCLUDE_DIRS, or that lie under `.claude/worktrees/`, are discarded.
    """
    seen: dict[str, Path] = {}
    for pattern in includes:
        for path in project_root.glob(pattern):
            if path.is_file() and path.suffix == ".md":
                rel = str(path.relative_to(project_root))
                if not _is_excluded_path(Path(rel).parts):
                    seen[rel] = path
    return seen


# Compute SHA256 of file content
def compute_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# Ensure the indexed_files tracking table exists
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


# Fetch stored hashes for a collection
def get_db_hashes(conn, collection: str) -> dict[str, str]:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT document, sha256 FROM indexed_files WHERE collection = %s",
            (collection,),
        )
        return {row[0]: row[1] for row in cur.fetchall()}


# Upsert (collection, document) → sha256 entry
def upsert_hash(conn, collection: str, document: str, sha256: str) -> None:
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO indexed_files (collection, document, sha256, last_indexed_at)
            VALUES (%s, %s, %s, NOW())
            ON CONFLICT (collection, document) DO UPDATE
            SET sha256 = EXCLUDED.sha256, last_indexed_at = NOW()
        """, (collection, document, sha256))
    conn.commit()


# Remove tracker row for a removed file
def delete_indexed_file(conn, collection: str, document: str) -> None:
    with conn.cursor() as cur:
        cur.execute(
            "DELETE FROM indexed_files WHERE collection = %s AND document = %s",
            (collection, document),
        )
    conn.commit()


# Chunk + embed + store a single file. Replaces existing chunks for that document.
def index_file(
    conn,
    file_path: Path,
    collection: str,
    document: str,
    chunk_size: int = 2000,
    overlap: int = 400,
) -> int:
    raw_chunks = chunk_workflow(str(file_path), chunk_size, overlap)

    # Always clear existing chunks first (handles updated AND empty-now cases)
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

    for i in range(0, total, BATCH_SIZE):
        batch = chunks[i:i + BATCH_SIZE]
        texts = [c["content"] for c in batch]
        embeddings = embed_workflow(texts, "search_document: ")
        store_chunks(conn, batch, embeddings)

    return total
