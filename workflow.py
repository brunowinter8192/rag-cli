# INFRASTRUCTURE
import argparse
import json
import sys
import threading
from pathlib import Path

from src.rag.chunker import chunk_workflow
from src.rag.db import get_connection
from src.rag.indexer import (
    backfill_splade_workflow,
    delete_workflow,
    doc_is_complete,
    ensure_schema,
    index_json_workflow,
)
from src.rag.retriever import search_workflow
from src.rag.sync import (
    compute_hash,
    ensure_indexed_files_table,
    get_db_hashes,
    upsert_hash,
)


# FUNCTIONS

# Write a chunks.json sidecar next to md_file. Mirrors what's about to land
# in the DB so users can inspect chunk boundaries without querying postgres.
# The DB is the source of truth — sidecars are an audit/visibility artifact.
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


# ORCHESTRATOR
def main(command: str, **kwargs) -> None:
    if command == "index-json":
        from src.rag.lock import acquire as _lock_acquire, LockBusyError
        try:
            _lock_ctx = _lock_acquire("index-json", {"input": kwargs["input"]})
        except LockBusyError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
        with _lock_ctx:
            count = index_json_workflow(kwargs["input"])
        print(f"Indexed {count} chunks from JSON")

    elif command == "search":
        results = search_workflow(
            kwargs["query"],
            kwargs.get("top_k", 5),
            collection=kwargs.get("collection"),
            document=kwargs.get("document")
        )
        for i, r in enumerate(results, 1):
            print(f"\n--- Result {i} (score: {r['score']}) ---")
            print(f"Collection: {r['collection']} | Document: {r['document']}")
            print(r['content'][:500])

    elif command == "chunk":
        chunks = chunk_workflow(kwargs["input"], kwargs.get("chunk_size", 2000), kwargs.get("overlap", 400))
        output = {
            "document": kwargs.get("document") or Path(kwargs["input"]).name,
            "chunks": [{"index": i, "content": c["content"]} for i, c in enumerate(chunks)]
        }
        json_path = Path(kwargs["input"]).with_suffix(".json")
        with open(json_path, "w") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        print(f"Chunked {len(chunks)} chunks -> {json_path}")

    elif command == "backfill-splade":
        count = backfill_splade_workflow(kwargs["collection"])
        print(f"Backfilled {count} sparse embeddings")

    elif command == "delete":
        result = delete_workflow(
            collection=kwargs.get("collection"),
            document=kwargs.get("document"),
        )
        chunks = result["chunks_deleted"]
        chunk_word = "chunk" if chunks == 1 else "chunks"
        print(f"Deleted {chunks} {chunk_word}")

    elif command == "index-dir":
        from src.rag.server_manager import ensure_ready
        from src.rag.lock import acquire as _lock_acquire, LockBusyError, update_progress, heartbeat
        dir_path = Path(kwargs["input"])
        md_files = sorted(dir_path.glob("*.md"))
        if not md_files:
            print(f"No .md files found in {dir_path}")
            return

        collection = kwargs.get("collection") or dir_path.name
        chunk_size = kwargs.get("chunk_size", 2000)
        overlap = kwargs.get("overlap", 400)
        force = kwargs.get("force", False)

        try:
            _lock_ctx = _lock_acquire("index-dir", {"collection": collection, "input": str(dir_path)})
        except LockBusyError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

        with _lock_ctx:
            _stop_hb = threading.Event()
            def _hb_loop():
                while not _stop_hb.wait(30):
                    heartbeat()
            threading.Thread(target=_hb_loop, daemon=True).start()

            print(f"Found {len(md_files)} markdown files in {dir_path}")
            print(f"Collection: {collection}")
            if force:
                print("--force: skip-logic bypassed, all files will be re-indexed")

            # Plan phase — classify each file BEFORE touching GPU servers.
            # Three buckets:
            #   skipped: hash matches indexed_files entry → no work
            #   adopted: complete chunk set in DB but no hash entry → register hash, no re-embed
            #   to_index: missing, partial, or hash-changed → chunk + embed + insert
            conn = get_connection(purpose="ddl", autocommit=True)
            ensure_schema(conn)
            ensure_indexed_files_table(conn)

            db_hashes = {} if force else get_db_hashes(conn, collection)

            skipped: list[str] = []
            adopted: list[str] = []
            to_index: list[tuple[Path, str, str]] = []  # (path, document, hash)

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

            print(f"  Skipped (hash unchanged): {len(skipped)}")
            print(f"  Adopted (complete in DB, hash registered): {len(adopted)}")
            print(f"  To index: {len(to_index)}")

            if not to_index:
                conn.close()
                _stop_hb.set()
                print("\nNothing to index.")
                return

            # GPU servers are only needed when there's work to embed.
            print("\nChecking servers...")
            ensure_ready("index")
            print("Servers ready.")

            total_chunks = 0
            for i, (md_file, document, current) in enumerate(to_index):
                raw_chunks = chunk_workflow(str(md_file), chunk_size, overlap)
                json_path = _write_chunks_json(md_file, raw_chunks, collection, document)
                n = index_json_workflow(str(json_path))
                upsert_hash(conn, collection, document, current)
                total_chunks += n
                update_progress(done=i + 1, total=len(to_index), current_document=document)
                print(f"  Indexed {document} -> {n} chunks (sidecar: {json_path.name})")

            conn.close()
            _stop_hb.set()
            print(f"\nDone: {len(to_index)} files indexed ({total_chunks} chunks), "
                  f"{len(skipped)} skipped, {len(adopted)} adopted")

    elif command == "index-file":
        from src.rag.server_manager import ensure_ready
        from src.rag.lock import acquire as _lock_acquire, LockBusyError
        file_path = Path(kwargs["input"])
        if not file_path.is_file():
            raise FileNotFoundError(f"Not a file: {file_path}")
        if file_path.suffix != ".md":
            raise ValueError(f"Expected .md file: {file_path}")

        collection = kwargs.get("collection") or file_path.parent.name
        chunk_size = kwargs.get("chunk_size", 2000)
        overlap = kwargs.get("overlap", 400)
        force = kwargs.get("force", False)
        document = file_path.name

        try:
            _lock_ctx = _lock_acquire("index-file", {"collection": collection, "input": str(file_path)})
        except LockBusyError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

        with _lock_ctx:
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

    elif command == "server":
        from src.rag.server_manager import cli_server
        cli_server(kwargs.get("server_args", []))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="RAG System CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    index_json_parser = subparsers.add_parser("index-json", help="Index from chunks.json")
    index_json_parser.add_argument("--input", required=True, help="Path to chunks.json")

    search_parser = subparsers.add_parser("search", help="Search indexed documents")
    search_parser.add_argument("--query", required=True, help="Search query")
    search_parser.add_argument("--top-k", type=int, default=5, help="Number of results")
    search_parser.add_argument("--collection", help="Filter by collection name")
    search_parser.add_argument("--document", help="Filter by document name")

    chunk_parser = subparsers.add_parser("chunk", help="Chunk markdown into JSON")
    chunk_parser.add_argument("--input", required=True, help="Path to markdown file")
    chunk_parser.add_argument("--chunk-size", type=int, default=2000, help="Target chunk size in chars")
    chunk_parser.add_argument("--overlap", type=int, default=400, help="Overlap between chunks in chars")
    chunk_parser.add_argument("--document", help="Document name (default: input filename)")

    backfill_parser = subparsers.add_parser("backfill-splade", help="Backfill SPLADE sparse embeddings")
    backfill_parser.add_argument("--collection", required=True, help="Collection to backfill")

    delete_parser = subparsers.add_parser("delete", help="Delete chunks + manifest + source files for a collection (and optionally a document).")
    delete_parser.add_argument("--collection", required=True, help="Collection to delete from (required)")
    delete_parser.add_argument("--document", help="Delete only this document; omit to delete the entire collection")

    index_dir_parser = subparsers.add_parser("index-dir", help="Chunk + index all .md files in a directory (skip-by-default via indexed_files hash)")
    index_dir_parser.add_argument("--input", required=True, help="Path to directory with .md files")
    index_dir_parser.add_argument("--collection", help="Override collection name (default: directory name)")
    index_dir_parser.add_argument("--chunk-size", type=int, default=2000, help="Target chunk size in chars")
    index_dir_parser.add_argument("--overlap", type=int, default=400, help="Overlap between chunks in chars")
    index_dir_parser.add_argument("--force", action="store_true", help="Bypass skip-logic, re-embed every file (use only when embedding model or chunker changed)")

    index_file_parser = subparsers.add_parser("index-file", help="Chunk + index a single .md file (skip-by-default via indexed_files hash)")
    index_file_parser.add_argument("--input", required=True, help="Path to .md file")
    index_file_parser.add_argument("--collection", help="Override collection name (default: parent folder name)")
    index_file_parser.add_argument("--chunk-size", type=int, default=2000, help="Target chunk size in chars")
    index_file_parser.add_argument("--overlap", type=int, default=400, help="Overlap between chunks in chars")
    index_file_parser.add_argument("--force", action="store_true", help="Bypass skip-logic, re-embed even if hash matches")

    server_parser = subparsers.add_parser("server", help="Manage GPU servers (status/start/stop/restart)")
    server_parser.add_argument("server_args", nargs="*", default=["status"], help="action [server_name]")

    args = parser.parse_args()
    kwargs = {k: v for k, v in vars(args).items() if k != "command"}
    main(args.command, **kwargs)
