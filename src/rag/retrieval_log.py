# INFRASTRUCTURE
import hashlib
import json
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from . import error_log
from .log_setup import LOG_ROOT
from .retrieval_config import resolve_search_config

SEARCH_LOG_FILE = LOG_ROOT / "search.jsonl"
SEARCH_CONTENT_FILE = LOG_ROOT / "search_content.jsonl"
EXPAND_LOG_FILE = LOG_ROOT / "expand.jsonl"
EXPAND_CONTENT_FILE = LOG_ROOT / "expand_content.jsonl"
CONFIG_REGISTRY_FILE = LOG_ROOT / "config_registry.jsonl"


# ORCHESTRATOR

def log_search(query: str, collection: str | None, document: str | None, exclude: str | None,
                candidates: int, hits: list[dict], started_at: float,
                vector_dimension: int, candidates_requested: int) -> None:
    search_id = build_event_id()
    fingerprint = resolve_fingerprint(vector_dimension, candidates_requested)
    record = build_search_record(search_id, query, collection, document, exclude, candidates, hits, started_at, fingerprint)
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


def resolve_fingerprint(vector_dimension: int, candidates_requested: int) -> str | None:
    try:
        snapshot = resolve_search_config(vector_dimension, candidates_requested)
        fingerprint = compute_fingerprint(snapshot)
        ensure_registry_entry(fingerprint, snapshot)
        return fingerprint
    except Exception as exc:
        report_resolve_failure(exc)
        return None


def compute_fingerprint(snapshot: dict) -> str:
    hash_input = build_hash_input(snapshot)
    canonical = json.dumps(hash_input, sort_keys=True)
    return hashlib.sha256(canonical.encode()).hexdigest()[:16]


def build_hash_input(snapshot: dict) -> dict:
    embedding = snapshot["embedding"]
    reranker = snapshot["reranker"]
    return {
        "embedding_model_name": embedding["model_name"],
        "embedding_context_size": embedding["context_size"],
        "embedding_vector_dimension": embedding["vector_dimension"],
        "query_prefix": snapshot["query_prefix"],
        "truncation_limit_tokens": snapshot["truncation_limit_tokens"],
        "reranker_model_name": reranker["model_name"],
        "reranker_context_size": reranker["context_size"],
        "reranker_instruction": reranker["instruction"],
        "candidate_count_requested": snapshot["candidate_count_requested"],
    }


def ensure_registry_entry(fingerprint: str, snapshot: dict) -> None:
    if fingerprint in known_fingerprints():
        return
    entry = {
        "fingerprint": fingerprint,
        "first_seen": datetime.now(timezone.utc).isoformat(),
        **snapshot,
    }
    write_jsonl_lines(CONFIG_REGISTRY_FILE, [entry])


def known_fingerprints() -> set[str]:
    try:
        lines = CONFIG_REGISTRY_FILE.read_text().splitlines()
    except FileNotFoundError:
        return set()
    except Exception as exc:
        report_resolve_failure(exc)
        return set()
    result = set()
    for line in lines:
        line = line.strip()
        if not line:
            continue
        result.add(json.loads(line)["fingerprint"])
    return result


def build_search_record(search_id: str, query: str, collection: str | None, document: str | None,
                         exclude: str | None, candidates: int, hits: list[dict], started_at: float,
                         config_fingerprint: str | None) -> dict:
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
        "config_fingerprint": config_fingerprint,
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
    error_log.write("retrieval_log", "log_write_failed", str(exc), path=str(path))


def report_resolve_failure(exc: Exception) -> None:
    error_log.write("retrieval_log", "log_config_resolve_failed", str(exc))
