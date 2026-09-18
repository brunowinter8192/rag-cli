# INFRASTRUCTURE

import json
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path


# FUNCTIONS

def build_event_id() -> str:
    return f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')}_probe"


def elapsed_ms(started_at: float) -> int:
    return round((time.perf_counter() - started_at) * 1000)


def build_search_record(search_id, query, collection, document, exclude, candidates, hits, started_at):
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


def build_search_content_lines(search_id, hits):
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


def write_jsonl_lines(path: Path, records: list, on_failure) -> None:
    if not records:
        return
    try:
        with open(path, "a") as fh:
            for record in records:
                fh.write(json.dumps(record) + "\n")
    except Exception as exc:
        on_failure(path, exc)


def known_fingerprints(path: Path, on_resolve_failure) -> set:
    try:
        lines = path.read_text().splitlines()
    except FileNotFoundError:
        return set()
    except Exception as exc:
        on_resolve_failure(exc)
        return set()
    result = set()
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            result.add(json.loads(line)["fingerprint"])
        except (json.JSONDecodeError, KeyError):
            continue
    return result


def test_search_record_carries_full_query_and_filters():
    started = time.perf_counter()
    hits = [{"document": "a.md", "chunk_index": 3, "score": 0.0067, "content": "irrelevant text"}]
    record = build_search_record(
        "id1", "a nine word query about logging of search results",
        "rag-cli-docs", None, "process-docs/%", 30, hits, started,
    )
    assert record["query"] == "a nine word query about logging of search results"
    assert record["collection"] == "rag-cli-docs"
    assert record["exclude"] == "process-docs/%"
    assert record["candidates"] == 30
    assert record["hit_count"] == 1
    assert record["hits"][0] == {"rank": 1, "document": "a.md", "chunk_index": 3, "score": 0.0067}
    assert "content" not in record["hits"][0]
    print("PASS: search record carries full query, filters, and lean per-hit fields")


def test_zero_hits_record_shape():
    started = time.perf_counter()
    record = build_search_record("id2", "off domain nonsense", "trading", None, None, 0, [], started)
    assert record["hit_count"] == 0
    assert record["hits"] == []
    print("PASS: zero-hit search still produces a well-formed record")


def test_sidecar_lines_carry_full_content_linked_by_search_id():
    hits = [
        {"document": "a.md", "chunk_index": 1, "score": 0.05, "content": "full chunk text one"},
        {"document": "b.md", "chunk_index": 2, "score": 0.03, "content": "full chunk text two"},
    ]
    lines = build_search_content_lines("id3", hits)
    assert len(lines) == 2
    assert all(line["search_id"] == "id3" for line in lines)
    assert lines[0]["content"] == "full chunk text one"
    assert lines[1]["rank"] == 2
    print("PASS: sidecar lines carry full content, each linked to the search_id")


def test_write_failure_is_reported_not_swallowed():
    reported = []

    def on_failure(path, exc):
        reported.append((path, exc))

    bad_record = {"value": object()}
    write_jsonl_lines(Path("/tmp/does_not_matter.jsonl"), [bad_record], on_failure)
    assert len(reported) == 1, "a non-serializable record must trigger the failure path, not raise"
    print("PASS: a write failure is reported through the failure channel, never silently dropped")


def test_successful_write_reaches_disk():
    reported = []
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "search.jsonl"
        write_jsonl_lines(path, [{"a": 1}], lambda p, e: reported.append(e))
        lines = path.read_text().splitlines()
    assert len(lines) == 1
    assert json.loads(lines[0]) == {"a": 1}
    assert reported == []
    print("PASS: a normal write reaches disk with no failure reported")


def test_missing_registry_stays_silent():
    reported = []
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "does_not_exist.jsonl"
        result = known_fingerprints(path, lambda exc: reported.append(exc))
    assert result == set()
    assert reported == [], "a missing registry is the normal first-run case, must stay silent"
    print("PASS: a missing config_registry.jsonl produces no traced failure")


def test_unreadable_registry_is_reported_not_swallowed():
    reported = []
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "config_registry.jsonl"
        path.write_text('{"fingerprint": "abc"}\n')
        path.chmod(0o000)
        try:
            result = known_fingerprints(path, lambda exc: reported.append(exc))
        finally:
            path.chmod(0o644)
    assert result == set(), "search must still proceed with an empty (safe) result"
    assert len(reported) == 1, "any failure other than FileNotFoundError must be traced, not swallowed"
    print("PASS: an unreadable config_registry.jsonl is reported through the failure channel, never silently dropped")


if __name__ == "__main__":
    test_search_record_carries_full_query_and_filters()
    test_zero_hits_record_shape()
    test_sidecar_lines_carry_full_content_linked_by_search_id()
    test_write_failure_is_reported_not_swallowed()
    test_successful_write_reaches_disk()
    test_missing_registry_stays_silent()
    test_unreadable_registry_is_reported_not_swallowed()
    print("All tests passed.")
