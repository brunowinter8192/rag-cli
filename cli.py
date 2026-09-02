#!/usr/bin/env python3
# INFRASTRUCTURE
import json
import os
import signal
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import argparse

import httpx

from src.rag.retriever import (
    format_results,
    search_workflow,
    list_collections_workflow, format_collections,
    list_documents_workflow, format_documents,
    progress_workflow, format_progress,
    read_document_workflow
)

_READ_ONLY_CMDS = frozenset({
    "search", "list_collections", "list_documents", "progress", "read_document"
})

HELP_TEXT = (
    "You triggered the help function. Usage sits in your rules. "
    "Report to the user why you needed help and go idle immediately."
)


# Parser that redirects all help/usage/error output to the fixed rules pointer
class NoHelpParser(argparse.ArgumentParser):
    def error(self, message):
        self.exit(2, HELP_TEXT + "\n")

    def print_help(self, file=None):
        print(HELP_TEXT, file=file or sys.stderr)
        self.exit(2)


# ORCHESTRATOR
def main():
    signal.signal(signal.SIGTERM, _shutdown)
    signal.signal(signal.SIGINT, _shutdown)

    parser = _build_parser()
    args = parser.parse_args()

    if args.cmd == "status":
        from src.rag.status import gather, format_status
        print(format_status(gather()))
        return

    if args.cmd == "server":
        from src.rag.server_manager import cli_server
        cli_server(args.server_args)
        return

    if args.cmd in _READ_ONLY_CMDS:
        _run_dispatch(args)
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
        _run_dispatch(args)
    finally:
        _lock_ctx.__exit__(None, None, None)


# FUNCTIONS

# Handle SIGTERM/SIGINT by exiting with the conventional 128+signal code
def _shutdown(sig: int, _frame: object) -> None:
    sys.exit(128 + sig)


# Build the argparse surface for every subcommand
def _build_parser() -> argparse.ArgumentParser:
    parser = NoHelpParser(
        prog="cli.py",
        description="RAG CLI — hybrid search over indexed document collections."
    )
    sub = parser.add_subparsers(dest="cmd", required=True)
    _add_retrieval_parsers(sub)
    _add_pipeline_parsers(sub)
    _add_server_parser(sub)
    return parser


# Add the read-only retrieval subcommand parsers: search, list_collections, list_documents, progress, read_document
def _add_retrieval_parsers(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("search", help="Dense vector search with cross-encoder reranking; top_k=12 fixed.")
    p.add_argument("query", help="Natural language search query")
    p.add_argument("collection", help="Collection to search in")
    p.add_argument("--document", default=None,
                   help="Filter by document name. %% as wildcard")
    p.add_argument("--exclude", default=None,
                   help="Exclude documents matching pattern. %% as wildcard (NOT LIKE)")

    p = sub.add_parser("list_collections", help="List all indexed collections with chunk counts.")
    p.add_argument("--filter", default=None,
                   help="Substring filter on collection name (case-insensitive, e.g. 'RAG' matches RAG-meta, RAG-features)")
    p.add_argument("--json", action="store_true", dest="output_json",
                   help="Output as JSON array [{collection, chunks}] instead of human-readable text")

    p = sub.add_parser("list_documents", help="List documents in a collection.")
    p.add_argument("collection", help="Collection name")
    p.add_argument("--document", default=None,
                   help="Filter by document name. %% as wildcard")
    p.add_argument("--exclude", default=None,
                   help="Exclude documents matching pattern. %% as wildcard (NOT LIKE)")
    p.add_argument("--filter", default=None,
                   help="Substring filter on document name (case-insensitive)")

    p = sub.add_parser(
        "progress",
        help="Show indexing progress per document — done/total chunks plus percent. "
             "Pollable during a workflow.py index-dir run; documents with done < total are "
             "still being indexed."
    )
    p.add_argument("collection", help="Collection name")

    p = sub.add_parser("read_document", help="Read anchor chunk plus N before and M after.")
    p.add_argument("collection", help="Collection name")
    p.add_argument("document", help="Document name (e.g. 'chapter1.md')")
    p.add_argument("chunk_index", type=int, help="Anchor chunk index")
    p.add_argument("--before", type=int, default=0,
                   help="Chunks to read before the anchor (0–10, default 0)")
    p.add_argument("--after", type=int, default=0,
                   help="Chunks to read after the anchor (0–10, default 0)")


# Add the write/pipeline subcommand parsers: delete, index, status, update_docs
def _add_pipeline_parsers(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("delete", help="Delete chunks + manifest + source files for a collection (and optionally a document).")
    p.add_argument("--collection", required=True, help="Collection to delete from (required)")
    p.add_argument("--document", default=None, help="Delete only this document; omit to delete the entire collection")

    p = sub.add_parser("index", help="Chunk + index .md files from data/documents/<collection>/.")
    p.add_argument("--collection", required=True, help="Collection to index (required)")
    p.add_argument("--document", default=None, help="Index only this file; omit to index all .md in the collection directory")
    p.add_argument("--chunk-size", dest="chunk_size", type=int, default=2000, help="Target chunk size in chars (default 2000)")
    p.add_argument("--overlap", type=int, default=400, help="Overlap between chunks in chars (default 400)")
    p.add_argument("--force", action="store_true", help="Bypass skip-logic, re-embed every file")

    sub.add_parser(
        "status",
        help="Show lock state, GPU server health, and Postgres reachability. "
             "Always works regardless of lock state — no DB query."
    )

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


# Add the server subcommand parser
def _add_server_parser(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("server", help="Manage GPU servers (status/start/stop/restart/tail/errors/list)")
    p.add_argument("server_args", nargs=argparse.REMAINDER, default=["status"],
                   help="action [server_name] [flags] — start|stop|restart|status|list|tail|errors")


def _run_dispatch(args: argparse.Namespace) -> None:
    """Run _dispatch with GPU-server error handling (no lock)."""
    try:
        _dispatch(args)
    except httpx.HTTPStatusError as e:
        try:
            msg = e.response.json().get("error", {}).get("message", "") or e.response.text[:200]
        except Exception:
            msg = e.response.text[:200]
        print(f"Error: server returned HTTP {e.response.status_code} — {msg}", file=sys.stderr)
        sys.exit(1)
    except (httpx.RequestError, RuntimeError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def _dispatch(args: argparse.Namespace) -> None:
    handler = _COMMAND_HANDLERS.get(args.cmd)
    if handler is None:
        raise SystemExit(f"Unknown command: {args.cmd}")
    handler(args)


def _cmd_search(args: argparse.Namespace) -> None:
    results = search_workflow(
        args.query, args.collection, args.document, args.exclude
    )
    if not results:
        print("No results — 0 candidates. Check the collection name and --document filter "
              "(filters are SQL LIKE patterns: use %term%, not term).")
    else:
        print(format_results(results))


def _cmd_list_collections(args: argparse.Namespace) -> None:
    results = list_collections_workflow(args.filter)
    if getattr(args, 'output_json', False):
        print(json.dumps(results))
    else:
        print(format_collections(results))


def _cmd_list_documents(args: argparse.Namespace) -> None:
    results = list_documents_workflow(args.collection, args.document, args.filter, args.exclude)
    print(format_documents(results))


def _cmd_progress(args: argparse.Namespace) -> None:
    results = progress_workflow(args.collection)
    print(format_progress(results, args.collection))


def _cmd_read_document(args: argparse.Namespace) -> None:
    before = min(max(args.before, 0), 10)
    after = min(max(args.after, 0), 10)
    result = read_document_workflow(
        args.collection, args.document, args.chunk_index, before, after
    )
    print(_format_read_document(result))


# Assemble the read_document anchor-range header + content text
def _format_read_document(result: dict) -> str:
    start = result['chunk_index'] - result['before']
    end = result['chunk_index'] + result['after']
    return (
        f"Document: {result['document']} | "
        f"Chunks {start}-{end} (anchor: {result['chunk_index']})"
        f"\n\n{result['content']}"
    )


def _cmd_delete(args: argparse.Namespace) -> None:
    from src.rag.indexer import delete_workflow
    result = delete_workflow(
        collection=args.collection,
        document=args.document,
    )
    print(f"Deleted {result['chunks_deleted']} chunks")


def _cmd_index(args: argparse.Namespace) -> None:
    from src.rag.index_cmd import index_collection_workflow
    index_collection_workflow(
        collection=args.collection,
        document=args.document,
        chunk_size=args.chunk_size,
        overlap=args.overlap,
        force=args.force,
    )


def _cmd_update_docs(args: argparse.Namespace) -> None:
    from src.rag.sync import sync_docs_workflow
    result = sync_docs_workflow(
        args.project_root,
        chunk_size=args.chunk_size,
        overlap=args.overlap,
    )
    _print_sync_result(result)


# Print per-collection update_docs stats; result is a dict of collections or a single flat dict
def _print_sync_result(result: dict) -> None:
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


def _cmd_server(args: argparse.Namespace) -> None:
    from src.rag.server_manager import cli_server
    cli_server(args.server_args)


_COMMAND_HANDLERS = {
    "search": _cmd_search,
    "list_collections": _cmd_list_collections,
    "list_documents": _cmd_list_documents,
    "progress": _cmd_progress,
    "read_document": _cmd_read_document,
    "delete": _cmd_delete,
    "index": _cmd_index,
    "update_docs": _cmd_update_docs,
    "server": _cmd_server,
}


if __name__ == "__main__":
    main()
