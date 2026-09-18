# INFRASTRUCTURE
import json
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from . import error_log
from .log_setup import LOG_ROOT

SEARCH_LOG_FILE = LOG_ROOT / "search.jsonl"
SEARCH_CONTENT_FILE = LOG_ROOT / "search_content.jsonl"
EXPAND_LOG_FILE = LOG_ROOT / "expand.jsonl"
EXPAND_CONTENT_FILE = LOG_ROOT / "expand_content.jsonl"


# ORCHESTRATOR

def log_search(query: str, collection: str | None, document: str | None, exclude: str | None,
                candidates: int, hits: list[dict], started_at: float) -> None:
    search_id = build_event_id()
    record = build_search_record(search_id, query, collection, document, exclude, candidates, hits, started_at)
    write_jsonl_lines(SEARCH_LOG_FILE, [record])
    content_lines = build_search_content_lines(search_id, hits)
    write_jsonl_lines(SEARCH_CONTENT_FILE, content_lines)


def log_expand(result: dict, started_at: float) -> None:
    expand_id = build_event_id()
    record = build_expand_record(expand_id, result, started_at)
    write_jsonl_lines(EXPAND_LOG_FILE, [record])
    content_line = build_expand_content_line(expand_id, result)
    write_jsonl_lines(EXPAND_CONTENT_FILE, [content_line])


# FUNCTIONS

def build_event_id() -> str:
    return f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')}_{uuid.uuid4().hex[:6]}"


def elapsed_ms(started_at: float) -> int:
    return round((time.perf_counter() - started_at) * 1000)


def build_search_record(search_id: str, query: str, collection: str | None, document: str | None,
                         exclude: str | None, candidates: int, hits: list[dict], started_at: float) -> dict:
    return {
        "ts": datetime.now(timezone.utc).isoformat(),
        "search_id": search_id,
        "query": query,
        "collection": collection,
        "document": document,
        "exclude": exclude,
        "candidates": candidates,
        "duration_ms": elapsed_ms(started_at),
        "hit_count": len(hits),
        "hits": [
            {"rank": i + 1, "document": h["document"], "chunk_index": h["chunk_index"], "score": h["score"]}
            for i, h in enumerate(hits)
        ],
    }


def build_search_content_lines(search_id: str, hits: list[dict]) -> list[dict]:
    return [
        {
            "search_id": search_id,
            "rank": i + 1,
            "document": h["document"],
            "chunk_index": h["chunk_index"],
            "content": h["content"],
        }
        for i, h in enumerate(hits)
    ]


def build_expand_record(expand_id: str, result: dict, started_at: float) -> dict:
    return {
        "ts": datetime.now(timezone.utc).isoformat(),
        "expand_id": expand_id,
        "collection": result["collection"],
        "document": result["document"],
        "chunk_index": result["chunk_index"],
        "before": result["before"],
        "after": result["after"],
        "chunks_returned": result["chunks_returned"],
        "duration_ms": elapsed_ms(started_at),
    }


def build_expand_content_line(expand_id: str, result: dict) -> dict:
    return {
        "expand_id": expand_id,
        "collection": result["collection"],
        "document": result["document"],
        "chunk_index": result["chunk_index"],
        "content": result["content"],
    }


def write_jsonl_lines(path: Path, records: list[dict]) -> None:
    if not records:
        return
    try:
        with open(path, "a") as fh:
            for record in records:
                fh.write(json.dumps(record) + "\n")
    except Exception as exc:
        report_write_failure(path, exc)


def report_write_failure(path: Path, exc: Exception) -> None:
    try:
        error_log.write("retrieval_log", "log_write_failed", str(exc), path=str(path))
    except Exception:
        print(f"[retrieval_log] write to {path} failed: {exc}", file=sys.stderr)
