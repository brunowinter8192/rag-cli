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

def index_collection_workflow(
    collection: str,
    document: str | None,
    chunk_size: int,
    overlap: int,
    force: bool,
) -> None:
    coll_dir = resolve_collection_dir(collection)
    if document:
        _index_single_file(collection, coll_dir, document, chunk_size, overlap, force)
    else:
        _index_collection(collection, coll_dir, chunk_size, overlap, force)


# FUNCTIONS

def resolve_collection_dir(collection: str) -> Path:
    return RAG_ROOT / "data" / "documents" / collection


def _index_single_file(
    collection: str,
    coll_dir: Path,
    document_name: str,
    chunk_size: int,
    overlap: int,
    force: bool,
) -> None:
    file_path = _validate_md_file(coll_dir, document_name)
    print(f"File: {file_path.name}")
    print(f"Collection: {collection}")

    conn = _open_index_connection()
    skipped, adopted, to_index = _classify_md_files(
        conn, collection, [file_path], _load_db_hashes(conn, collection, force), force
    )
    if skipped:
        conn.close()
        print("  Skipped (hash unchanged)")
        return
    if adopted:
        conn.close()
        print("  Adopted (complete in DB, hash registered)")
        return

    _ensure_servers_ready("")
    md_file, document, current = to_index[0]
    n, json_path = _index_one_file(conn, collection, md_file, document, current, chunk_size, overlap)
    conn.close()
    print(f"  Indexed -> {n} chunks (sidecar: {json_path.name})")


def _validate_md_file(coll_dir: Path, document_name: str) -> Path:
    file_path = coll_dir / document_name
    if not file_path.is_file():
        raise FileNotFoundError(f"Not a file: {file_path}")
    if file_path.suffix != ".md":
        raise ValueError(f"Expected .md file: {file_path}")
    return file_path


def _open_index_connection():
    conn = get_connection(purpose="ddl", autocommit=True)
    ensure_schema(conn)
    ensure_indexed_files_table(conn)
    return conn


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


def _ensure_servers_ready(lead: str) -> None:
    print(f"{lead}Checking servers...")
    ensure_ready("index")
    print("Servers ready.")


def _index_one_file(
    conn,
    collection: str,
    md_file: Path,
    document: str,
    current: str,
    chunk_size: int,
    overlap: int,
    doc_done: int | None = None,
    docs_total: int | None = None,
) -> tuple[int, Path]:
    raw_chunks = chunk_workflow(str(md_file), chunk_size, overlap)
    json_path = _write_chunks_json(md_file, raw_chunks, collection, document)
    n = index_json_workflow(str(json_path), doc_done=doc_done, docs_total=docs_total)
    upsert_hash(conn, collection, document, current)
    return n, json_path


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


def _load_db_hashes(conn, collection: str, force: bool) -> dict[str, str]:
    return {} if force else get_db_hashes(conn, collection)


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

    conn = _open_index_connection()
    skipped, adopted, to_index = _classify_md_files(
        conn, collection, md_files, _load_db_hashes(conn, collection, force), force
    )

    print(f"  Skipped (hash unchanged): {len(skipped)}")
    print(f"  Adopted (complete in DB, hash registered): {len(adopted)}")
    print(f"  To index: {len(to_index)}")

    if not to_index:
        conn.close()
        print("\nNothing to index.")
        return

    _ensure_servers_ready("\n")
    total_chunks = _index_queued_files(conn, collection, to_index, chunk_size, overlap)

    conn.close()
    print(f"\nDone: {len(to_index)} files indexed ({total_chunks} chunks), "
          f"{len(skipped)} skipped, {len(adopted)} adopted")


def _index_queued_files(
    conn,
    collection: str,
    to_index: list[tuple[Path, str, str]],
    chunk_size: int,
    overlap: int,
) -> int:
    total_chunks = 0
    for i, (md_file, document, current) in enumerate(to_index):
        n, json_path = _index_one_file(
            conn, collection, md_file, document, current, chunk_size, overlap,
            doc_done=i, docs_total=len(to_index),
        )
        total_chunks += n
        update_progress(done=i + 1, total=len(to_index), current_document=document, collection=collection)
        print(f"  Indexed {document} -> {n} chunks (sidecar: {json_path.name})")
    return total_chunks
