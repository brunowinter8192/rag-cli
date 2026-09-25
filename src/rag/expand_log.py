# INFRASTRUCTURE
from datetime import datetime, timezone

from src.rag.log_setup import LOG_ROOT
from src.rag.retrieval_log import build_event_id, elapsed_ms, write_jsonl_lines

EXPAND_LOG_FILE = LOG_ROOT / "expand.jsonl"
EXPAND_CONTENT_FILE = LOG_ROOT / "expand_content.jsonl"


# ORCHESTRATOR

def log_expand(result: dict, started_at: float) -> None:
    expand_id = build_event_id()
    record = build_expand_record(expand_id, result, started_at)
    write_jsonl_lines(EXPAND_LOG_FILE, [record])
    content_line = build_expand_content_line(expand_id, result)
    write_jsonl_lines(EXPAND_CONTENT_FILE, [content_line])


# FUNCTIONS

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
