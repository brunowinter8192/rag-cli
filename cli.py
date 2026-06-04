#!/usr/bin/env python3
import json
import os
import signal
import sys
import threading
from pathlib import Path

# Ensure src.rag.* imports resolve regardless of working directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import argparse

from src.rag.retriever import (
    format_results,
    search_hybrid_workflow,
    list_collections_workflow, format_collections,
    list_documents_workflow, format_documents,
    progress_workflow, format_progress,
    read_document_workflow
)


def _shutdown(sig: int, _frame: object) -> None:
    sys.exit(128 + sig)


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


def main():
    signal.signal(signal.SIGTERM, _shutdown)
    signal.signal(signal.SIGINT, _shutdown)

    parser = argparse.ArgumentParser(
        prog="cli.py",
        description="RAG CLI — hybrid search over indexed document collections."
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    # ── search_hybrid ─────────────────────────────────────────────────────────
    p = sub.add_parser("search_hybrid", help="Dense vector search with cross-encoder reranking; top_k=10 fixed.")
    p.add_argument("query", help="Natural language search query")
    p.add_argument("collection", help="Collection to search in")
    p.add_argument("--document", default=None,
                   help="Filter by document name. %% as wildcard")

    # ── list_collections ──────────────────────────────────────────────────────
    p = sub.add_parser("list_collections", help="List all indexed collections with chunk counts.")
    p.add_argument("--filter", default=None,
                   help="Substring filter on collection name (case-insensitive, e.g. 'RAG' matches RAG-meta, RAG-features)")

    # ── list_documents ────────────────────────────────────────────────────────
    p = sub.add_parser("list_documents", help="List documents in a collection.")
    p.add_argument("collection", help="Collection name")
    p.add_argument("--document", default=None,
                   help="Filter by document name. %% as wildcard")
    p.add_argument("--filter", default=None,
                   help="Substring filter on document name (case-insensitive)")

    # ── progress ──────────────────────────────────────────────────────────────
    p = sub.add_parser(
        "progress",
        help="Show indexing progress per document — done/total chunks plus percent. "
             "Pollable during a workflow.py index-dir run; documents with done < total are "
             "still being indexed."
    )
    p.add_argument("collection", help="Collection name")

    # ── read_document ─────────────────────────────────────────────────────────
    p = sub.add_parser("read_document", help="Read anchor chunk plus N before and M after.")
    p.add_argument("collection", help="Collection name")
    p.add_argument("document", help="Document name (e.g. 'chapter1.md')")
    p.add_argument("chunk_index", type=int, help="Anchor chunk index")
    p.add_argument("--before", type=int, default=0,
                   help="Chunks to read before the anchor (0–10, default 0)")
    p.add_argument("--after", type=int, default=0,
                   help="Chunks to read after the anchor (0–10, default 0)")

    # ── delete ────────────────────────────────────────────────────────────────
    p = sub.add_parser("delete", help="Delete chunks + manifest + source files for a collection (and optionally a document).")
    p.add_argument("--collection", required=True, help="Collection to delete from (required)")
    p.add_argument("--document", default=None, help="Delete only this document; omit to delete the entire collection")

    # ── index ─────────────────────────────────────────────────────────────────
    p = sub.add_parser("index", help="Chunk + index .md files from data/documents/<collection>/.")
    p.add_argument("--collection", required=True, help="Collection to index (required)")
    p.add_argument("--document", default=None, help="Index only this file; omit to index all .md in the collection directory")
    p.add_argument("--chunk-size", dest="chunk_size", type=int, default=2000, help="Target chunk size in chars (default 2000)")
    p.add_argument("--overlap", type=int, default=400, help="Overlap between chunks in chars (default 400)")
    p.add_argument("--force", action="store_true", help="Bypass skip-logic, re-embed every file")

    # ── status ────────────────────────────────────────────────────────────────
    sub.add_parser(
        "status",
        help="Show lock state, GPU server health, and Postgres reachability. "
             "Always works regardless of lock state — no DB query."
    )

    # ── update_docs ───────────────────────────────────────────────────────────
    p = sub.add_parser(
        "update_docs",
        help="Sync project docs into RAG collection per .rag-docs.json manifest. "
             "Hash-based change detection — unchanged files skipped, removed files cleaned up. "
             "Run at the end of every session to keep the project's docs collection current."
    )
    p.add_argument("project_root", help="Project root containing .rag-docs.json")
    p.add_argument("--chunk-size", dest="chunk_size", type=int, default=2000,
                   help="Target chunk size in chars (default 2000)")
    p.add_argument("--overlap", type=int, default=400,
                   help="Overlap between chunks in chars (default 400)")

    # ── server ────────────────────────────────────────────────────────────────
    p = sub.add_parser("server", help="Manage GPU servers (status/start/stop/restart/tail/errors/list)")
    p.add_argument("server_args", nargs=argparse.REMAINDER, default=["status"],
                   help="action [server_name] [flags] — start|stop|restart|status|list|tail|errors")

    # ── Dispatch ──────────────────────────────────────────────────────────────
    args = parser.parse_args()

    if args.cmd == "status":
        from src.rag.status import gather, format_status
        print(format_status(gather()))
        return

    if args.cmd == "server":
        from src.rag.server_manager import cli_server
        cli_server(args.server_args)
        return

    from src.rag.lock import acquire as _lock_acquire, LockBusyError as _LockBusyError
    _lock_args = {k: v for k, v in vars(args).items() if v is not None and k != "cmd"}
    try:
        _lock_ctx = _lock_acquire(args.cmd, _lock_args)
        _lock_ctx.__enter__()
    except _LockBusyError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        _dispatch(args)
    finally:
        _lock_ctx.__exit__(None, None, None)


def _dispatch(args: argparse.Namespace) -> None:
    if args.cmd == "search_hybrid":
        results = search_hybrid_workflow(
            args.query, args.collection, args.document
        )
        print(format_results(results))

    elif args.cmd == "list_collections":
        results = list_collections_workflow(args.filter)
        print(format_collections(results))

    elif args.cmd == "list_documents":
        results = list_documents_workflow(args.collection, args.document, args.filter)
        print(format_documents(results))

    elif args.cmd == "progress":
        results = progress_workflow(args.collection)
        print(format_progress(results, args.collection))

    elif args.cmd == "read_document":
        before = min(max(args.before, 0), 10)
        after = min(max(args.after, 0), 10)
        result = read_document_workflow(
            args.collection, args.document, args.chunk_index, before, after
        )
        start = result['chunk_index'] - result['before']
        end = result['chunk_index'] + result['after']
        text = (
            f"Document: {result['document']} | "
            f"Chunks {start}-{end} (anchor: {result['chunk_index']})"
            f"\n\n{result['content']}"
        )
        print(text)

    elif args.cmd == "delete":
        from src.rag.indexer import delete_workflow
        result = delete_workflow(
            collection=args.collection,
            document=args.document,
        )
        print(f"Deleted {result['chunks_deleted']} chunks")

    elif args.cmd == "index":
        from src.rag.server_manager import ensure_ready, RAG_ROOT
        from src.rag.lock import heartbeat, update_progress
        from src.rag.indexer import ensure_schema, doc_is_complete, index_json_workflow
        from src.rag.sync import ensure_indexed_files_table, get_db_hashes, upsert_hash, compute_hash
        from src.rag.chunker import chunk_workflow
        from src.rag.db import get_connection

        chunk_size = args.chunk_size
        overlap = args.overlap
        force = args.force
        coll_dir = RAG_ROOT / "data" / "documents" / args.collection

        if args.document:
            # Single-file path
            file_path = coll_dir / args.document
            if not file_path.is_file():
                raise FileNotFoundError(f"Not a file: {file_path}")
            if file_path.suffix != ".md":
                raise ValueError(f"Expected .md file: {file_path}")
            document = file_path.name
            print(f"File: {file_path.name}")
            print(f"Collection: {args.collection}")

            conn = get_connection(purpose="ddl", autocommit=True)
            ensure_schema(conn)
            ensure_indexed_files_table(conn)
            current = compute_hash(file_path)

            if not force:
                db_hashes = get_db_hashes(conn, args.collection)
                if document in db_hashes and db_hashes[document] == current:
                    conn.close()
                    print("  Skipped (hash unchanged)")
                    return
                if document not in db_hashes and doc_is_complete(conn, args.collection, document):
                    upsert_hash(conn, args.collection, document, current)
                    conn.close()
                    print("  Adopted (complete in DB, hash registered)")
                    return

            print("Checking servers...")
            ensure_ready("index")
            print("Servers ready.")

            raw_chunks = chunk_workflow(str(file_path), chunk_size, overlap)
            json_path = _write_chunks_json(file_path, raw_chunks, args.collection, document)
            n = index_json_workflow(str(json_path))
            upsert_hash(conn, args.collection, document, current)
            conn.close()
            print(f"  Indexed -> {n} chunks (sidecar: {json_path.name})")

        else:
            # Collection-wide path
            if not coll_dir.is_dir():
                raise FileNotFoundError(f"Collection directory not found: {coll_dir}")
            md_files = sorted(coll_dir.glob("*.md"))
            if not md_files:
                print(f"No .md files found in {coll_dir}")
                return

            print(f"Found {len(md_files)} markdown files in {coll_dir}")
            print(f"Collection: {args.collection}")
            if force:
                print("--force: skip-logic bypassed, all files will be re-indexed")

            conn = get_connection(purpose="ddl", autocommit=True)
            ensure_schema(conn)
            ensure_indexed_files_table(conn)

            db_hashes = {} if force else get_db_hashes(conn, args.collection)

            skipped: list[str] = []
            adopted: list[str] = []
            to_index: list[tuple[Path, str, str]] = []

            for md_file in md_files:
                document = md_file.name
                current = compute_hash(md_file)

                if not force and document in db_hashes and db_hashes[document] == current:
                    skipped.append(document)
                    continue

                if not force and document not in db_hashes and doc_is_complete(conn, args.collection, document):
                    upsert_hash(conn, args.collection, document, current)
                    adopted.append(document)
                    continue

                to_index.append((md_file, document, current))

            print(f"  Skipped (hash unchanged): {len(skipped)}")
            print(f"  Adopted (complete in DB, hash registered): {len(adopted)}")
            print(f"  To index: {len(to_index)}")

            if not to_index:
                conn.close()
                print("\nNothing to index.")
                return

            # Heartbeat thread — keeps lock JSON fresh during the long embed loop
            _stop_hb = threading.Event()
            def _hb_loop():
                while not _stop_hb.wait(30):
                    heartbeat()
            threading.Thread(target=_hb_loop, daemon=True).start()

            print("\nChecking servers...")
            ensure_ready("index")
            print("Servers ready.")

            total_chunks = 0
            for i, (md_file, document, current) in enumerate(to_index):
                raw_chunks = chunk_workflow(str(md_file), chunk_size, overlap)
                json_path = _write_chunks_json(md_file, raw_chunks, args.collection, document)
                n = index_json_workflow(str(json_path))
                upsert_hash(conn, args.collection, document, current)
                total_chunks += n
                update_progress(done=i + 1, total=len(to_index), current_document=document)
                print(f"  Indexed {document} -> {n} chunks (sidecar: {json_path.name})")

            conn.close()
            _stop_hb.set()
            print(f"\nDone: {len(to_index)} files indexed ({total_chunks} chunks), "
                  f"{len(skipped)} skipped, {len(adopted)} adopted")

    elif args.cmd == "update_docs":
        from src.rag.sync import sync_docs_workflow
        result = sync_docs_workflow(
            args.project_root,
            chunk_size=args.chunk_size,
            overlap=args.overlap,
        )
        # Multi-collection result: dict keyed by name, values are per-collection dicts.
        # Single-collection result: flat dict with "collection" key (backward-compat).
        per_collection = (
            result.values() if "collection" not in result
            else [result]
        )
        for r in per_collection:
            print(f"Collection: {r['collection']}")
            print(f"  added:     {len(r['added'])}")
            for f in r['added']:
                print(f"             + {f}")
            print(f"  updated:   {len(r['updated'])}")
            for f in r['updated']:
                print(f"             ~ {f}")
            print(f"  removed:   {len(r['removed'])}")
            for f in r['removed']:
                print(f"             - {f}")
            print(f"  unchanged: {len(r['unchanged'])}")
            print(f"  total chunks indexed this run: {r['total_chunks_indexed']}")

    elif args.cmd == "server":
        from src.rag.server_manager import cli_server
        cli_server(args.server_args)

    else:
        raise SystemExit(f"Unknown command: {args.cmd}")


if __name__ == "__main__":
    main()
