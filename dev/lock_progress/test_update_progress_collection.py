# INFRASTRUCTURE

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from strand_runner import load_rag, run_strands


# ORCHESTRATOR

def run_all() -> None:
    run_strands([
        test_collection_field_written,
        test_collection_defaults_to_none,
    ])


# FUNCTIONS

def test_collection_field_written(workdir: Path) -> None:
    lock = _prepare_lock(workdir)
    lock.update_progress(done=3, total=5, current_document="foo.md", collection="my-col")
    data = lock.read()
    assert data is not None
    assert data["progress"]["collection"] == "my-col", data["progress"]
    assert data["progress"]["done"] == 3
    assert data["progress"]["total"] == 5
    assert data["progress"]["current_document"] == "foo.md"


def _prepare_lock(workdir: Path):
    lock = load_rag("lock")
    lock._DATA_FILE = workdir / "rag.lock"
    lock._DATA_FILE.write_text(json.dumps({
        "pid": 1,
        "command": "update_docs",
        "kind": "index",
        "args": {},
        "started_at": "2026-01-01T00:00:00+00:00",
        "status": "running",
        "progress": {},
        "heartbeat": "2026-01-01T00:00:00+00:00",
    }))
    return lock


def test_collection_defaults_to_none(workdir: Path) -> None:
    lock = _prepare_lock(workdir)
    lock.update_progress(done=1, total=2, current_document="bar.md")
    data = lock.read()
    assert data is not None
    assert data["progress"]["collection"] is None, data["progress"]


if __name__ == "__main__":
    run_all()
