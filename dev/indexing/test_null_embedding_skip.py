# INFRASTRUCTURE

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from strand_runner import load_rag, run_strands


# ORCHESTRATOR

def run_all() -> None:
    run_strands([
        test_all_none_embedding_is_skipped_and_logged,
    ])


# FUNCTIONS

def test_all_none_embedding_is_skipped_and_logged(workdir: Path) -> None:
    indexer = load_rag("indexer")
    conn = _Connection()
    embeddings = [[None] * 4096, [0.1] * 4096]
    skipped = indexer.store_chunks(conn, [_chunk(0), _chunk(1)], embeddings)
    assert skipped == 1
    assert len(conn.inserted) == 1 and conn.inserted[0][3] == 1, conn.inserted
    for handler in indexer.logger.handlers:
        handler.flush()
    log_text = (workdir / "src" / "rag" / "logs" / "indexer.log").read_text()
    assert "NULL embedding skipped: collection=c document=d.md chunk_index=0" in log_text, log_text


class _Connection:
    def __init__(self):
        self.inserted = []

    def cursor(self):
        return _Cursor(self.inserted)

    def commit(self):
        pass


class _Cursor:
    def __init__(self, inserted: list):
        self._inserted = inserted

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def execute(self, sql, params):
        self._inserted.append(params)


def _chunk(index: int) -> dict:
    return {"content": f"text {index}", "collection": "c", "document": "d.md", "chunk_index": index, "total_chunks": 2}


if __name__ == "__main__":
    run_all()
