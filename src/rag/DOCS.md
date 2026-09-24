# src/rag/ — RAG Pipeline Modules

## Role

Core implementation of the RAG pipeline: dense (Qwen3) embedding, PostgreSQL/pgvector storage, dense retrieval with cross-encoder reranking (always-on), and GPU server lifecycle management. Touch this package when changing retrieval logic, embedding models, indexing behavior, or server startup. Do NOT touch for Skills/Commands (project root) or dev scripts (`dev/`).

## Public Interface

`__init__.py` is empty — import directly from sub-modules:
- `from src.rag.retriever import search_workflow, format_results` — primary entry point (cli.py)
- `from src.rag.db import get_connection` — direct DB access in scripts

## Flow

**Retrieval (per query):** `retriever.py` workflow → `db.py` opens connection + validates collection → `search_primitives.py` embeds query and runs vector search → `reranker.py` re-scores the candidates → `formatting.py` serializes output. Context expansion (neighboring chunks) via `expand_chunks_workflow` using `--before`/`--after`. Search and expansion hand their timing and result data to `retrieval_log.py`, which writes a lean JSONL record plus a content sidecar; for searches it also resolves a configuration fingerprint via `retrieval_config.py` (live server state files, never module constants).

**Indexing (per batch):** `chunker.py` splits document → `indexer.py` embeds chunks via `embedder.py` (dense only) and inserts into PostgreSQL. `server_manager.py` ensures GPU servers are running before embedding starts.

**Manifest-driven sync (per project, end of session):** `sync.py` reads `<project>/.rag-docs.json`, expands the include-globs, hashes each matched `.md` file, and diffs against the `indexed_files` tracking table. Only added/updated files are re-chunked + re-embedded; removed files are deleted from the index; unchanged files are skipped. Reuses chunker/indexer/server_manager primitives — no re-implementation of embedding or storage.

**Logging (cross-cutting):** every module that logs obtains its own file logger from `log_setup.py`, writing to `src/rag/logs/<name>.log`. This is the single log root for Python `logging` output; `~/.rag-locks/logs/` only holds subprocess stdout of the server processes.

## Modules

### db.py (185 LOC)

**Purpose:** PostgreSQL connection factory, collection/document queries, and WHERE-clause filter builders shared across retrieval sub-modules.
**Reads:** `.env` (POSTGRES_* connection params, `RAG_PG_CONTAINER`); PostgreSQL `documents` table; `docker info` (daemon probe).
**Writes:** nothing to the DB (read-only queries); side effect: may launch OrbStack + start the Postgres container.
**Called by:** retriever.py, search_primitives.py, indexer.py, sync.py, index_cmd.py, status.py
**Calls out:** psycopg2, pgvector, python-dotenv, subprocess (`open`/`docker`)

---

### embedder.py (65 LOC)

**Purpose:** HTTP client for the llama-server dense embedding endpoint; auto-starts the embedding GPU server on first call.
**Reads:** embedding URL env override or the server state files; llama-server embeddings response.
**Writes:** `src/rag/logs/embedder.log`; bumps the server state file mtime before each request so the watchdog idle timer reflects real inference activity.
**Called by:** search_primitives.py, indexer.py
**Calls out:** httpx

---

### reranker.py (60 LOC)

**Purpose:** HTTP client for the llama-server cross-encoder reranking endpoint; re-scores candidate lists by query-document relevance.
**Reads:** reranker URL env override or the server state files; llama-server rerank response.
**Writes:** `src/rag/logs/reranker.log`; bumps the server state file mtime before each request.
**Called by:** retriever.py, retrieval_config.py
**Calls out:** httpx

---

### search_primitives.py (62 LOC)

**Purpose:** Low-level search: query embedding and vector cosine search against PostgreSQL.
**Reads:** PostgreSQL `documents` table (via `conn` parameter); embedding server (via embedder).
**Writes:** nothing.
**Called by:** retriever.py
**Calls out:** (none — all via internal modules: db, embedder)

---

### formatting.py (53 LOC)

**Purpose:** Serialize search results, collections, and document lists as human-readable strings for CLI stdout.
**Reads:** in-memory result lists.
**Writes:** nothing.
**Called by:** retriever.py
**Calls out:** (none — pure Python)

---

### retriever.py (107 LOC)

**Purpose:** Workflow orchestration for retrieval operations (search, list collections, list documents, expand chunks) plus chunk merge helpers.
**Reads:** PostgreSQL via db; embedding/reranker servers via search_primitives/reranker.
**Writes:** nothing directly — hands query, filters, timing and results to `retrieval_log.py` after every search and expansion.
**Called by:** cli.py
**Calls out:** retrieval_log (intra-package)

---

### log_setup.py (21 LOC)

**Purpose:** Single Python-logging configuration point: hands out per-name file loggers under `src/rag/logs/`, never via the root logger.
**Reads:** nothing.
**Writes:** creates `src/rag/logs/` if missing; each logger writes to its own `<name>.log`.
**Called by:** chunker.py, embedder.py, reranker.py, indexer.py, sync.py, splade_server.py, server_utils.py, server_lifecycle.py, server_manager.py, watchdog.py, lock.py.
**Calls out:** (none — stdlib only: logging, pathlib)

---

### retrieval_config.py (66 LOC)

**Purpose:** Resolves the embedding and reranker configuration that actually answered a search from the running servers' state, never from module constants.
**Reads:** `~/.rag-locks/server-port-{N}.json` (no network call); launch flags of the server presets; embedder, search_primitives and reranker settings.
**Writes:** nothing.
**Called by:** retrieval_log.py
**Calls out:** embedder, reranker, search_primitives, server_manager (intra-package)

---

### retrieval_log.py (186 LOC)

**Purpose:** Structured, never-raising JSONL logging for search and expansion: lean lookup record plus content sidecar, linked by a generated id.
**Reads:** `src/rag/logs/config_registry.jsonl`, to check whether a configuration fingerprint is already registered.
**Writes:** `src/rag/logs/search.jsonl`, `search_content.jsonl`, `expand.jsonl`, `expand_content.jsonl`, `config_registry.jsonl`; write failures are reported to `error_log.py`, never raised.
**Called by:** retriever.py
**Calls out:** error_log, log_setup, retrieval_config (intra-package)

---

### chunker.py (102 LOC)

**Purpose:** Split markdown documents into semantic chunks using recursive character splitting at paragraph → sentence → word boundaries.
**Reads:** markdown file from disk.
**Writes:** `src/rag/logs/chunker.log`; returns the chunk list, the caller writes the JSON sidecar.
**Called by:** index_cmd.py, sync.py
**Calls out:** log_setup (intra-package)

---

### index_cmd.py (180 LOC)

**Purpose:** Workflow for `cli.py index`: chunks and embeds a single document or a whole collection directory, with skip/adopt/index bucketing and progress updates.
**Reads:** `.md` files from `data/documents/<collection>/`; PostgreSQL `indexed_files` and `documents` tables (via sync/indexer helpers).
**Writes:** `chunks.json` sidecars next to source `.md` files; PostgreSQL `indexed_files` (upsert via sync helpers) and `documents` (via indexer).
**Called by:** cli.py (lazy import)
**Calls out:** chunker, db, indexer, lock, server_manager, sync (intra-package)

---

### indexer.py (267 LOC)

**Purpose:** Indexes chunks into PostgreSQL with dense embeddings; owns schema creation, batch insert, deletion and the per-document completeness check.
**Reads:** `chunks.json` from disk; `.env` for connection params; PostgreSQL schema state.
**Writes:** `src/rag/logs/indexer.log`; PostgreSQL `documents` (insert, delete, schema init) and `indexed_files` (delete); removes on-disk source files on document deletion.
**Called by:** sync.py, index_cmd.py, cli.py (lazy import)
**Calls out:** psycopg2, pgvector, python-dotenv; lock (update_progress)

---

### sync.py (282 LOC)

**Purpose:** Manifest-driven project doc indexing: hashes matched `.md` files, diffs against `indexed_files`, and re-indexes only the deltas.
**Reads:** `<project>/.rag-docs.json` manifest; matched `.md` files from disk; PostgreSQL `indexed_files` table.
**Writes:** `src/rag/logs/sync.log`; PostgreSQL `indexed_files` (upsert/delete) and `documents` (via indexer); `~/.rag-locks/rag.lock` chunk-level progress when document context is provided.
**Called by:** cli.py, index_cmd.py
**Calls out:** hashlib, json, pathlib (stdlib only — all RAG-specific calls are intra-package: chunker, indexer, db, lock, server_manager, log_setup)

---

### server_manager.py (101 LOC)

**Purpose:** Thin coordinator: ensures GPU servers are ready and re-exports the public surface of the four server sub-modules.
**Reads:** (via sub-modules)
**Writes:** `src/rag/logs/server_manager.log`; other effects via sub-modules.
**Called by:** embedder.py, reranker.py, retrieval_config.py, cli.py (lazy), index_cmd.py, sync.py, indexer.py (lazy), status.py, watchdog_main.py.
**Calls out:** server_utils, server_lifecycle, watchdog, server_cli, log_setup (intra-package).

---

### server_utils.py (239 LOC)

**Purpose:** Dependency root of the server sub-modules: server preset table, path constants, process primitives and state-file I/O.
**Reads:** env vars (project root, llama-server path, port overrides, idle timeout); `lsof`/`pgrep`; httpx `/health` endpoints; `~/.rag-locks/server-port-{N}.json`.
**Writes:** `src/rag/logs/server_utils.log`; `~/.rag-locks/server-port-{N}.json` (write, unlink, mtime bump); kills processes on stop.
**Called by:** server_lifecycle.py, watchdog.py, server_cli.py, server_manager.py.
**Calls out:** httpx, subprocess, error_log, log_setup.

---

### server_lifecycle.py (314 LOC)

**Purpose:** Start, stop and restart logic for preset and arbitrary servers, plus state queries; state-file-only, no state file means not running.
**Reads:** `~/.rag-locks/server-port-{N}.json` state files; `/health` endpoints (delegated to server_utils).
**Writes:** `src/rag/logs/server_lifecycle.log`; spawns server processes with stdout redirected to `~/.rag-locks/logs/`; state files via server_utils.
**Called by:** server_manager.py (re-exports), server_cli.py, watchdog.py.
**Calls out:** httpx, subprocess, server_utils, error_log, log_setup.

---

### watchdog.py (98 LOC)

**Purpose:** Watchdog subprocess management and idle-timeout enforcement: purges unregistered llama-server orphans and idle-stops servers.
**Reads:** `~/.rag-locks/server-port-{N}.json` state files; `~/.rag-locks/watchdog.pid`.
**Writes:** `src/rag/logs/watchdog.log`; kills orphan/idle server processes; `~/.rag-locks/watchdog.pid`.
**Called by:** server_manager.py (re-exports); watchdog_main.py.
**Calls out:** server_utils, error_log, log_setup.

---

### server_cli.py (287 LOC)

**Purpose:** CLI surface for `rag-cli server`: dispatches status, start, stop, restart, list, tail, errors and presets subcommands with tabular output.
**Reads:** `~/.rag-locks/server-port-{N}.json` state files (content + mtime for idle display in `list`); log files (for `tail`); error_log (for `errors` subcommand).
**Writes:** stdout for known actions; on an unrecognized action, the fixed help-redirect sentence to stderr and `exit(2)`.
**Called by:** cli.py (lazy import).
**Calls out:** server_utils, server_lifecycle, error_log.

---

### watchdog_main.py (14 LOC)

**Purpose:** Standalone watchdog entrypoint (`python -m src.rag.watchdog_main`) running the watchdog loop in a detached process.
**Reads:** indirect (via the watchdog loop).
**Writes:** `src/rag/logs/watchdog_main.log` (traceback if the watchdog loop aborts); other effects via the watchdog loop.
**Called by:** subprocess invocation only — no Python imports.
**Calls out:** server_manager (intra-package).

---

### splade_server.py (59 LOC)

**Purpose:** Standalone FastAPI server that loads the SPLADE model at startup and serves sparse embeddings and a health endpoint.
**Reads:** HuggingFace model `naver/splade-v3` from disk/HF cache at startup.
**Writes:** `src/rag/logs/splade_server.log`.
**Called by:** (none — subprocess target launched by `server_manager.py`, never imported by Python code)
**Calls out:** fastapi, uvicorn, torch, transformers, log_setup

---

### lock.py (151 LOC)

**Purpose:** Global RAG mutex via `fcntl.flock` plus JSON lockfile, with progress tracking and an auto-heartbeat thread.
**Reads:** `~/.rag-locks/rag.flock` (fd hold); `~/.rag-locks/rag.lock` (JSON details).
**Writes:** `src/rag/logs/lock.log` (warnings only); `~/.rag-locks/rag.flock`; `~/.rag-locks/rag.lock` (atomic tmp+rename).
**Called by:** cli.py (write path only), index_cmd.py, indexer.py, sync.py, status.py (read-only)
**Calls out:** log_setup (intra-package); stdlib fcntl, json, os, pathlib, threading

---

### status.py (139 LOC)

**Purpose:** Gathers lock state, GPU server health and Postgres reachability into one dict for `rag-cli status` and formats it for the terminal.
**Reads:** lock state; server state; `~/.rag-locks/server-port-{port}.json` mtime for idle display; Postgres connect probe.
**Writes:** nothing.
**Called by:** cli.py
**Calls out:** (none — all via lock, server_manager, db intra-package)

---

### error_log.py (55 LOC)

**Purpose:** Appends structured error entries to `src/rag/logs/errors.jsonl` and separates genuine anomaly codes from lifecycle noise.
**Reads:** `src/rag/logs/errors.jsonl`.
**Writes:** `src/rag/logs/errors.jsonl` (one JSON line per error event).
**Called by:** server_utils.py, server_lifecycle.py, watchdog.py, server_cli.py, retrieval_log.py
**Calls out:** (none — stdlib only: json, pathlib)

---

## State

| Owner | State | Reads | Writes |
|---|---|---|---|
| PostgreSQL `documents` table | All indexed chunks with dense + sparse embeddings | db.py, search_primitives.py | indexer.py, sync.py (delete via indexer) |
| PostgreSQL `indexed_files` table | Per-project (collection, document) to sha256 ledger for change detection | sync.py | sync.py (auto-creates on first run); indexer.py (delete) |
| `~/.rag-locks/server-port-{N}.json` | Per-process GPU server state; idle computed from state-file mtime | server_lifecycle.py, watchdog.py, status.py, server_cli.py | server_utils.py |
| `~/.rag-locks/watchdog.pid` | Detached watchdog process PID | watchdog.py | watchdog.py |
| `~/.rag-locks/rag.flock` + `rag.lock` | Global RAG mutex (flock fd) plus JSON details | lock.py, status.py | lock.py |
| `src/rag/logs/search.jsonl` + `search_content.jsonl` | Lean record per search plus content sidecar, joined by search id | (no readers yet) | retrieval_log.py |
| `src/rag/logs/expand.jsonl` + `expand_content.jsonl` | Lean record per expansion plus content sidecar, joined by expand id | (no readers yet) | retrieval_log.py |
| `src/rag/logs/config_registry.jsonl` | One entry per distinct configuration fingerprint with first-seen timestamp | retrieval_log.py | retrieval_log.py |
