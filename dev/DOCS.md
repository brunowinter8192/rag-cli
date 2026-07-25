# dev/ — Development & Evaluation Scripts

Pipeline-oriented layout matching the RAG system architecture. Scripts for evaluating, profiling, and validating the indexing and retrieval pipelines.

All scripts run from project root with the project venv:

```bash
./venv/bin/python dev/<path>/<script>.py [args]
```

## Test Database

Dev scripts that write to PostgreSQL use `rag_test` (never `rag` prod DB).

```bash
# One-time setup
docker exec rag-postgres psql -U rag -d postgres -c "CREATE DATABASE rag_test;"
```

Schema is created automatically by `p4_db.py:ensure_schema()` on first use.

## Documentation Tree

- [chunker/DOCS.md](chunker/DOCS.md) — Chunker output quality audit scripts
- [indexing/DOCS.md](indexing/DOCS.md) — Indexing pipeline modules and scripts
- [retrieval/DOCS.md](retrieval/DOCS.md) — Retrieval pipeline modules and scripts
- [server_management/DOCS.md](server_management/DOCS.md) — GPU server constellation profiling scripts

## error_log/

`analyze_errors.py` — filter `src/rag/logs/errors.jsonl` to genuine anomaly codes (mirrors `ERROR_CODES` from `src/rag/error_log.py`) and print a summary + detail view. Lifecycle events (`start_*`, `stop_*`, `state_unlinked`) are excluded; only the four anomaly classes are shown.

Flags: `--all` (full history; default: today only), `--tail N` (detail rows shown; default 10), `--raw` (JSONL dump to stdout for piping).

```bash
./venv/bin/python dev/error_log/analyze_errors.py --all
./venv/bin/python dev/error_log/analyze_errors.py --all --raw | grep watchdog
```

**Note:** `ERROR_CODES` is inlined in this script (dev/ cannot import from src/); keep in sync with `src/rag/error_log.py` when adding new anomaly codes.

---

## lock_progress/

`test_update_progress_collection.py` — verifies that `update_progress` writes the `collection` field into the `progress` dict in `rag.lock`, and that omitting `collection` yields `None`. Uses a tempfile lock path — no GPU, DB, or network required. Lock logic is inlined (dev/ cannot import from src/).

```bash
python3 dev/lock_progress/test_update_progress_collection.py
```
