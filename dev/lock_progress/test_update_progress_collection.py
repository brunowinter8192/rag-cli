# INFRASTRUCTURE
"""Test that update_progress writes the 'collection' field to the progress dict.

Inlines the lock logic (no src/ import — dev/ convention).
Run: python dev/lock_progress/test_update_progress_collection.py
No GPU, DB, or network required.
"""

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path


# --- inlined from src/rag/lock.py (the three functions under test) ---

def _write_atomic(data_file: Path, data: dict) -> None:
    tmp = data_file.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2))
    tmp.rename(data_file)


def read(data_file: Path) -> dict | None:
    try:
        return json.loads(data_file.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def update_progress(
    data_file: Path,
    done: int,
    total: int,
    current_document: str,
    collection: str | None = None,
) -> None:
    data = read(data_file)
    if data is None:
        return
    data["progress"] = {
        "done": done,
        "total": total,
        "current_document": current_document,
        "collection": collection,
    }
    data["heartbeat"] = datetime.now(timezone.utc).isoformat()
    _write_atomic(data_file, data)


# --- helpers ---

def _minimal_lock(path: Path) -> None:
    path.write_text(json.dumps({
        "pid": 1,
        "command": "update_docs",
        "kind": "index",
        "args": {},
        "started_at": "2026-01-01T00:00:00+00:00",
        "status": "running",
        "progress": {},
        "heartbeat": "2026-01-01T00:00:00+00:00",
    }))


# --- tests ---

def test_collection_field_written():
    with tempfile.TemporaryDirectory() as tmpdir:
        f = Path(tmpdir) / "rag.lock"
        _minimal_lock(f)
        update_progress(f, done=3, total=5, current_document="foo.md", collection="my-col")
        data = read(f)
        assert data is not None
        assert data["progress"]["collection"] == "my-col", data["progress"]
        assert data["progress"]["done"] == 3
        assert data["progress"]["total"] == 5
        assert data["progress"]["current_document"] == "foo.md"
    print("PASS: collection field written correctly")


def test_collection_defaults_to_none():
    with tempfile.TemporaryDirectory() as tmpdir:
        f = Path(tmpdir) / "rag.lock"
        _minimal_lock(f)
        update_progress(f, done=1, total=2, current_document="bar.md")
        data = read(f)
        assert data is not None
        assert data["progress"]["collection"] is None, data["progress"]
    print("PASS: collection defaults to None when omitted")


if __name__ == "__main__":
    test_collection_field_written()
    test_collection_defaults_to_none()
    print("All tests passed.")
