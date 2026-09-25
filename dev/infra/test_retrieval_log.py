# INFRASTRUCTURE

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from strand_runner import load_rag, run_strands


# ORCHESTRATOR

def run_all() -> None:
    run_strands([
        test_search_record_carries_full_query_and_filters,
        test_zero_hits_record_shape,
        test_sidecar_lines_carry_full_content_linked_by_search_id,
        test_write_failure_is_reported_not_swallowed,
        test_successful_write_reaches_disk,
        test_missing_registry_stays_silent,
        test_unreadable_registry_is_reported_not_swallowed,
    ])


# FUNCTIONS

def test_search_record_carries_full_query_and_filters(workdir: Path) -> None:
    retrieval_log = load_rag("retrieval_log")
    hits = [{"document": "a.md", "chunk_index": 3, "score": 0.0067, "content": "irrelevant text"}]
    record = retrieval_log.build_search_record(
        "id1", "a nine word query about logging of search results",
        "rag-cli-docs", None, "process-docs/%", 30, hits, time.perf_counter(), "fp",
    )
    assert record["query"] == "a nine word query about logging of search results"
    assert record["collection"] == "rag-cli-docs"
    assert record["exclude"] == "process-docs/%"
    assert record["candidates"] == 30
    assert record["hit_count"] == 1
    assert record["config_fingerprint"] == "fp"
    assert record["hits"][0] == {"rank": 1, "document": "a.md", "chunk_index": 3, "score": 0.0067}
    assert "content" not in record["hits"][0]


def test_zero_hits_record_shape(workdir: Path) -> None:
    retrieval_log = load_rag("retrieval_log")
    record = retrieval_log.build_search_record("id2", "off domain nonsense", "trading", None, None, 0, [], time.perf_counter(), None)
    assert record["hit_count"] == 0
    assert record["hits"] == []
    assert record["config_fingerprint"] is None


def test_sidecar_lines_carry_full_content_linked_by_search_id(workdir: Path) -> None:
    retrieval_log = load_rag("retrieval_log")
    hits = [
        {"document": "a.md", "chunk_index": 1, "score": 0.05, "content": "full chunk text one"},
        {"document": "b.md", "chunk_index": 2, "score": 0.03, "content": "full chunk text two"},
    ]
    lines = retrieval_log.build_search_content_lines("id3", hits)
    assert len(lines) == 2
    assert all(line["search_id"] == "id3" for line in lines)
    assert lines[0]["content"] == "full chunk text one"
    assert lines[1]["rank"] == 2


def test_write_failure_is_reported_not_swallowed(workdir: Path) -> None:
    retrieval_log = load_rag("retrieval_log")
    target = workdir / "bad.jsonl"
    retrieval_log.write_jsonl_lines(target, [{"value": object()}])
    entries = _error_entries(workdir)
    assert [e["code"] for e in entries] == ["log_write_failed"], entries
    assert entries[0]["path"] == str(target)


def _error_entries(workdir: Path) -> list[dict]:
    errors_file = workdir / "src" / "rag" / "logs" / "errors.jsonl"
    if not errors_file.exists():
        return []
    return [json.loads(line) for line in errors_file.read_text().splitlines() if line.strip()]


def test_successful_write_reaches_disk(workdir: Path) -> None:
    retrieval_log = load_rag("retrieval_log")
    target = workdir / "search.jsonl"
    retrieval_log.write_jsonl_lines(target, [{"a": 1}])
    lines = target.read_text().splitlines()
    assert len(lines) == 1
    assert json.loads(lines[0]) == {"a": 1}
    assert _error_entries(workdir) == []


def test_missing_registry_stays_silent(workdir: Path) -> None:
    retrieval_log = load_rag("retrieval_log")
    retrieval_log.CONFIG_REGISTRY_FILE = workdir / "does_not_exist.jsonl"
    assert retrieval_log.known_fingerprints() == set()
    assert _error_entries(workdir) == [], "a missing registry is the normal first-run case, must stay silent"


def test_unreadable_registry_is_reported_not_swallowed(workdir: Path) -> None:
    retrieval_log = load_rag("retrieval_log")
    registry = workdir / "config_registry.jsonl"
    registry.write_text('{"fingerprint": "abc"}\n')
    registry.chmod(0o000)
    retrieval_log.CONFIG_REGISTRY_FILE = registry
    try:
        result = retrieval_log.known_fingerprints()
    finally:
        registry.chmod(0o644)
    assert result == set(), "search must still proceed with an empty (safe) result"
    assert [e["code"] for e in _error_entries(workdir)] == ["log_config_resolve_failed"]


if __name__ == "__main__":
    run_all()
