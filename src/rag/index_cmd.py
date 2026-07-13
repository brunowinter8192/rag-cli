# INFRASTRUCTURE
import json
from pathlib import Path

from .chunker import chunk_workflow
from .db import get_connection
from .indexer import ensure_schema, doc_is_complete, index_json_workflow
from .lock import update_progress
from .server_manager import ensure_ready, RAG_ROOT
from .sync import ensure_indexed_files_table, get_db_hashes, upsert_hash, compute_hash


# ORCHESTRATOR

# Chunk + index .md files for a collection; routes to single-file or collection-wide path
def index_collection_workflow(
    collection: str,
    document: str | None,
    chunk_size: int,
    overlap: int,
    force: bool,
) -> None:
    coll_dir = RAG_ROOT / "data" / "documents" / collection
    if document:
        _index_single_file(collection, coll_dir, document, chunk_size, overlap, force)
    else:
        _index_collection(collection, coll_dir, chunk_size, overlap, force)


# FUNCTIONS

# Write a chunks.json sidecar next to md_file for audit/visibility
def _write_chunks_json(md_file: Path, chunks: list[dict], collection: str, document: str) -> Path:
    output = {
        "collection": collection,
        "document": document,
        "chunks": [{"index": i, "content": c["content"]} for i, c in enumerate(chunks)],
    }
    json_path = md_file.with_suffix(".json")
    with open(json_path, "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    return json_path


# Index a single .md file into the collection; skip/adopt logic applied before embedding
def _index_single_file(
    collection: str,
    coll_dir: Path,
    document_name: str,
    chunk_size: int,
    overlap: int,
    force: bool,
) -> None:
    file_path = coll_dir / document_name
    if not file_path.is_file():
        raise FileNotFoundError(f"Not a file: {file_path}")
    if file_path.suffix != ".md":
        raise ValueError(f"Expected .md file: {file_path}")
    document = file_path.name
    print(f"File: {file_path.name}")
    print(f"Collection: {collection}")

    conn = get_connection(purpose="ddl", autocommit=True)
    ensure_schema(conn)
    ensure_indexed_files_table(conn)
    current = compute_hash(file_path)

    if not force:
        db_hashes = get_db_hashes(conn, collection)
        if document in db_hashes and db_hashes[document] == current:
            conn.close()
            print("  Skipped (hash unchanged)")
            return
        if document not in db_hashes and doc_is_complete(conn, collection, document):
            upsert_hash(conn, collection, document, current)
            conn.close()
            print("  Adopted (complete in DB, hash registered)")
            return

    print("Checking servers...")
    ensure_ready("index")
    print("Servers ready.")

    raw_chunks = chunk_workflow(str(file_path), chunk_size, overlap)
    json_path = _write_chunks_json(file_path, raw_chunks, collection, document)
    n = index_json_workflow(str(json_path))
    upsert_hash(conn, collection, document, current)
    conn.close()
    print(f"  Indexed -> {n} chunks (sidecar: {json_path.name})")


# Bucket md_files into skipped (hash unchanged) / adopted (complete in DB, hash registered) / to_index
def _classify_md_files(
    conn,
    collection: str,
    md_files: list[Path],
    db_hashes: dict[str, str],
    force: bool,
) -> tuple[list[str], list[str], list[tuple[Path, str, str]]]:
    skipped: list[str] = []
    adopted: list[str] = []
    to_index: list[tuple[Path, str, str]] = []

    for md_file in md_files:
        document = md_file.name
        current = compute_hash(md_file)

        if not force and document in db_hashes and db_hashes[document] == current:
            skipped.append(document)
            continue

        if not force and document not in db_hashes and doc_is_complete(conn, collection, document):
            upsert_hash(conn, collection, document, current)
            adopted.append(document)
            continue

        to_index.append((md_file, document, current))

    return skipped, adopted, to_index


# Chunk + index each queued file, registering its hash; returns total chunks indexed
def _index_queued_files(
    conn,
    collection: str,
    to_index: list[tuple[Path, str, str]],
    chunk_size: int,
    overlap: int,
) -> int:
    total_chunks = 0
    for i, (md_file, document, current) in enumerate(to_index):
        raw_chunks = chunk_workflow(str(md_file), chunk_size, overlap)
        json_path = _write_chunks_json(md_file, raw_chunks, collection, document)
        n = index_json_workflow(str(json_path), doc_done=i, docs_total=len(to_index))
        upsert_hash(conn, collection, document, current)
        total_chunks += n
        update_progress(done=i + 1, total=len(to_index), current_document=document, collection=collection)
        print(f"  Indexed {document} -> {n} chunks (sidecar: {json_path.name})")
    return total_chunks


# Index all .md files in a collection directory; skip/adopt/index bucketing
def _index_collection(
    collection: str,
    coll_dir: Path,
    chunk_size: int,
    overlap: int,
    force: bool,
) -> None:
    if not coll_dir.is_dir():
        raise FileNotFoundError(f"Collection directory not found: {coll_dir}")
    md_files = sorted(coll_dir.glob("*.md"))
    if not md_files:
        print(f"No .md files found in {coll_dir}")
        return

    print(f"Found {len(md_files)} markdown files in {coll_dir}")
    print(f"Collection: {collection}")
    if force:
        print("--force: skip-logic bypassed, all files will be re-indexed")

    conn = get_connection(purpose="ddl", autocommit=True)
    ensure_schema(conn)
    ensure_indexed_files_table(conn)

    db_hashes = {} if force else get_db_hashes(conn, collection)
    skipped, adopted, to_index = _classify_md_files(conn, collection, md_files, db_hashes, force)

    print(f"  Skipped (hash unchanged): {len(skipped)}")
    print(f"  Adopted (complete in DB, hash registered): {len(adopted)}")
    print(f"  To index: {len(to_index)}")

    if not to_index:
        conn.close()
        print("\nNothing to index.")
        return

    print("\nChecking servers...")
    ensure_ready("index")
    print("Servers ready.")

    total_chunks = _index_queued_files(conn, collection, to_index, chunk_size, overlap)

    conn.close()
    print(f"\nDone: {len(to_index)} files indexed ({total_chunks} chunks), "
          f"{len(skipped)} skipped, {len(adopted)} adopted")
