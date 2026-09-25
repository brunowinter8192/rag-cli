# src/rag/ — RAG Pipeline Modules

## Role

Core implementation of the RAG pipeline: dense (Qwen3) embedding, PostgreSQL/pgvector storage, dense retrieval with cross-encoder reranking (always-on), and GPU server lifecycle management. Every module holds one workflow at most; shared constants live in config.py. Touch this package when changing retrieval logic, embedding models, indexing behavior, or server startup. Do NOT touch for Skills/Commands (project root) or dev scripts (`dev/`).

## Public Interface

`__init__.py` is empty — import directly from sub-modules:
- `from src.rag.search_cmd import search_workflow` — primary entry point (cli.py); the other retrieval commands follow the same `<command>_cmd.py` pattern
- `from src.rag.db import get_connection` — direct DB access in scripts

## Flow

**Retrieval (per query):** `search_cmd.py` opens a connection via `db.py`, embeds the query and runs the vector search via `search_primitives.py`, re-scores the candidates via `reranker.py`, and hands timing and results to `retrieval_log.py`, which resolves a configuration fingerprint via `retrieval_config.py` (live server state files, never module constants). `expand_cmd.py` fetches neighboring chunks and logs via `expand_log.py`; `formatting.py` serializes output.

**Indexing (per batch):** `chunker.py` splits a document → `indexer.py` embeds chunks via `embedder.py` (dense only) and inserts into PostgreSQL. `server_manager.py` ensures GPU servers are running before embedding starts.

**Manifest-driven sync (per project, end of session):** `sync.py` reads `<project>/.rag-docs.json`, expands the include-globs, hashes each matched `.md` file, and diffs against the `indexed_files` tracking table. Only added/updated files are re-chunked and re-embedded; removed files are deleted from the index; unchanged files are skipped.

**Logging and server lifecycle (cross-cutting):** every module that logs obtains its own file logger from `log_setup.py`, writing to `src/rag/logs/<name>.log`; `~/.rag-locks/logs/` only holds subprocess stdout of the server processes. Server start, stop, status and state queries are separate modules (`server_start.py`, `server_stop.py`, `server_status.py`, `server_state.py`) sharing `server_utils.py` and `server_launch.py`.

## Modules

### chunker.py (100 LOC)

**Purpose:** Split markdown documents into semantic chunks using recursive splitting at paragraph, sentence and word boundaries.
**Reads:** markdown file from disk.
**Writes:** `src/rag/logs/chunker.log`; returns the chunk list, the caller writes the JSON sidecar.
**Called by:** index_cmd.py, sync.py
**Calls out:** (none — stdlib and intra-package only)

---

### config.py (19 LOC)

**Purpose:** Shared constants used by two or more modules: lock and server-log directories, project root, llama-server path, model name, chunk defaults, help text.
**Reads:** the project-root and llama-server path environment variables.
**Writes:** nothing.
**Called by:** chunker.py, cli.py, delete_cmd.py, expand_cmd.py, index_cmd.py, lock.py, server_cli.py, server_launch.py, server_start.py, server_start_arbitrary.py, server_state.py, server_utils.py, splade_server.py, status.py, sync.py, watchdog.py
**Calls out:** (none — stdlib and intra-package only)

---

### db.py (185 LOC)

**Purpose:** PostgreSQL connection factory with timeout profiles, Postgres auto-boot, collection and document queries, and WHERE-clause filter builders.
**Reads:** `.env` (POSTGRES_* connection params, container name); PostgreSQL `documents` table; `docker info`.
**Writes:** nothing to the DB (read-only queries); side effect: may launch OrbStack and start the Postgres container.
**Called by:** delete_cmd.py, expand_cmd.py, index_cmd.py, indexer.py, list_collections_cmd.py, list_documents_cmd.py, progress_cmd.py, search_cmd.py, search_primitives.py, status.py, sync.py
**Calls out:** dotenv, pgvector, psycopg2

---

### embedder.py (75 LOC)

**Purpose:** HTTP client for the llama-server dense embedding endpoint; auto-starts the embedding GPU server on first call.
**Reads:** embedding URL env override or the server state files; llama-server embeddings response.
**Writes:** `src/rag/logs/embedder.log`; bumps the server state file mtime before each request so the watchdog idle timer reflects real inference activity.
**Called by:** indexer.py, retrieval_config.py, search_primitives.py
**Calls out:** dotenv, httpx

---

### reranker.py (74 LOC)

**Purpose:** HTTP client for the llama-server cross-encoder reranking endpoint; re-scores candidate lists by query-document relevance.
**Reads:** reranker URL env override or the server state files; llama-server rerank response.
**Writes:** `src/rag/logs/reranker.log`; bumps the server state file mtime before each request.
**Called by:** retrieval_config.py, search_cmd.py
**Calls out:** dotenv, httpx

---

### search_primitives.py (62 LOC)

**Purpose:** Low-level search: query embedding and vector cosine search against PostgreSQL.
**Reads:** PostgreSQL `documents` table (via the connection argument); embedding server (via embedder).
**Writes:** nothing.
**Called by:** retrieval_config.py, search_cmd.py
**Calls out:** (none — stdlib and intra-package only)

---

### formatting.py (50 LOC)

**Purpose:** Serialize search results, collections, document lists and progress as human-readable strings for CLI stdout.
**Reads:** in-memory result lists.
**Writes:** nothing.
**Called by:** cli.py
**Calls out:** (none — stdlib and intra-package only)

---

### search_cmd.py (52 LOC)

**Purpose:** Workflow for the search command: candidate retrieval, reranking, positive-score filtering and search logging.
**Reads:** PostgreSQL via db; embedding and reranker servers via search_primitives and reranker.
**Writes:** nothing directly — hands query, filters, timing and results to retrieval_log.py after every search.
**Called by:** cli.py
**Calls out:** (none — stdlib and intra-package only)

---

### expand_cmd.py (58 LOC)

**Purpose:** Workflow for the expand_chunks command: fetches a chunk range and merges the chunks with overlap deduplication.
**Reads:** PostgreSQL via db.
**Writes:** nothing directly — hands the merged result to expand_log.py.
**Called by:** cli.py
**Calls out:** (none — stdlib and intra-package only)

---

### list_collections_cmd.py (11 LOC)

**Purpose:** Workflow for the list_collections command.
**Reads:** PostgreSQL via db.
**Writes:** nothing.
**Called by:** cli.py
**Calls out:** (none — stdlib and intra-package only)

---

### list_documents_cmd.py (12 LOC)

**Purpose:** Workflow for the list_documents command.
**Reads:** PostgreSQL via db.
**Writes:** nothing.
**Called by:** cli.py
**Calls out:** (none — stdlib and intra-package only)

---

### progress_cmd.py (12 LOC)

**Purpose:** Workflow for the progress command: per-document indexed-chunk counts of a collection.
**Reads:** PostgreSQL via db.
**Writes:** nothing.
**Called by:** cli.py
**Calls out:** (none — stdlib and intra-package only)

---

### log_setup.py (21 LOC)

**Purpose:** Single Python-logging configuration point: hands out per-name file loggers under `src/rag/logs/`, never via the root logger.
**Reads:** nothing.
**Writes:** creates `src/rag/logs/` if missing; each logger writes to its own `<name>.log`.
**Called by:** chunker.py, constellation.py, embedder.py, expand_log.py, indexer.py, lock.py, reranker.py, retrieval_log.py, server_cli.py, server_launch.py, server_manager.py, server_start.py, server_start_arbitrary.py, server_stop.py, server_utils.py, splade_server.py, sync.py, watchdog.py, watchdog_main.py
**Calls out:** (none — stdlib and intra-package only)

---

### retrieval_config.py (67 LOC)

**Purpose:** Resolves the embedding and reranker configuration that actually answered a search from the running servers' state, never from module constants.
**Reads:** `~/.rag-locks/server-port-{N}.json` (no network call); launch flags of the server presets; embedder, search_primitives and reranker settings.
**Writes:** nothing.
**Called by:** retrieval_log.py
**Calls out:** (none — stdlib and intra-package only)

---

### retrieval_log.py (152 LOC)

**Purpose:** Structured, never-raising JSONL logging for searches: lean lookup record plus content sidecar, configuration fingerprint and registry; shared helpers for expand_log.py.
**Reads:** `src/rag/logs/config_registry.jsonl`, to check whether a configuration fingerprint is already registered.
**Writes:** `src/rag/logs/search.jsonl`, `search_content.jsonl`, `config_registry.jsonl`; write failures are reported to error_log.py, never raised.
**Called by:** expand_log.py, search_cmd.py
**Calls out:** (none — stdlib and intra-package only)

---

### expand_log.py (44 LOC)

**Purpose:** Structured JSONL logging for expansions: lean lookup record plus content sidecar linked by a generated id.
**Reads:** nothing.
**Writes:** `src/rag/logs/expand.jsonl`, `expand_content.jsonl`; write failures are reported to error_log.py via retrieval_log.py.
**Called by:** expand_cmd.py
**Calls out:** (none — stdlib and intra-package only)

---

### index_cmd.py (210 LOC)

**Purpose:** Workflow for `cli.py index`: chunks and embeds a single document or a whole collection directory, with skip/adopt/index bucketing and progress updates.
**Reads:** `.md` files from `data/documents/<collection>/`; PostgreSQL `indexed_files` and `documents` tables (via sync and indexer helpers).
**Writes:** `chunks.json` sidecars next to source `.md` files; PostgreSQL `indexed_files` (upsert via sync) and `documents` (via indexer).
**Called by:** cli.py
**Calls out:** (none — stdlib and intra-package only)

---

### indexer.py (218 LOC)

**Purpose:** Indexes chunks into PostgreSQL with dense embeddings; owns schema creation, batch insert, chunk deletion and the per-document completeness check.
**Reads:** `chunks.json` from disk; `.env` for the vector dimension; PostgreSQL schema state.
**Writes:** `src/rag/logs/indexer.log`; PostgreSQL `documents` (insert, delete, schema init).
**Called by:** delete_cmd.py, index_cmd.py, sync.py
**Calls out:** dotenv

---

### delete_cmd.py (58 LOC)

**Purpose:** Workflow for the delete command: removes chunks, manifest rows and source files for a collection or a single document.
**Reads:** PostgreSQL `documents` and `indexed_files`; `data/documents/`.
**Writes:** PostgreSQL `documents` and `indexed_files` (delete); removes on-disk source files.
**Called by:** cli.py
**Calls out:** (none — stdlib and intra-package only)

---

### sync.py (287 LOC)

**Purpose:** Manifest-driven project doc indexing: hashes matched `.md` files, diffs against `indexed_files`, and re-indexes only the deltas.
**Reads:** `<project>/.rag-docs.json` manifest; matched `.md` files from disk; PostgreSQL `indexed_files`.
**Writes:** `src/rag/logs/sync.log`; PostgreSQL `indexed_files` (upsert/delete) and `documents` (via indexer); `~/.rag-locks/rag.lock` chunk-level progress when document context is provided.
**Called by:** cli.py, index_cmd.py
**Calls out:** (none — stdlib and intra-package only)

---

### lock.py (164 LOC)

**Purpose:** Global RAG mutex via `fcntl.flock` plus JSON lockfile, with progress tracking and an auto-heartbeat thread.
**Reads:** `~/.rag-locks/rag.flock` (fd hold); `~/.rag-locks/rag.lock` (JSON details).
**Writes:** `src/rag/logs/lock.log`; `~/.rag-locks/rag.flock`; `~/.rag-locks/rag.lock` (atomic tmp+rename).
**Called by:** cli.py, index_cmd.py, indexer.py, status.py, sync.py
**Calls out:** (none — stdlib and intra-package only)

---

### status.py (51 LOC)

**Purpose:** Gathers lock state, GPU server state and Postgres reachability into one dict for `rag-cli status`.
**Reads:** lock state; server state; `~/.rag-locks/server-port-{port}.json` mtime for idle display; Postgres connect probe.
**Writes:** nothing.
**Called by:** cli.py
**Calls out:** (none — stdlib and intra-package only)

---

### status_format.py (80 LOC)

**Purpose:** Formats the gathered status dict for terminal display, including durations.
**Reads:** in-memory status dict.
**Writes:** nothing.
**Called by:** cli.py
**Calls out:** (none — stdlib and intra-package only)

---

### error_log.py (51 LOC)

**Purpose:** Appends structured error entries to `src/rag/logs/errors.jsonl` and separates genuine anomaly codes from lifecycle noise.
**Reads:** `src/rag/logs/errors.jsonl`.
**Writes:** `src/rag/logs/errors.jsonl` (one JSON line per error event).
**Called by:** retrieval_log.py, server_cli.py, server_launch.py, server_start.py, server_start_arbitrary.py, server_utils.py, watchdog.py
**Calls out:** (none — stdlib and intra-package only)

---

### server_utils.py (232 LOC)

**Purpose:** Dependency root of the server modules: server preset table, process primitives and state-file I/O.
**Reads:** env vars (model paths); `lsof`/`pgrep`; httpx `/health` endpoints; `~/.rag-locks/server-port-{N}.json`.
**Writes:** `src/rag/logs/server_utils.log`; `~/.rag-locks/server-port-{N}.json` (write, unlink, mtime bump); kills processes on stop.
**Called by:** embedder.py, reranker.py, retrieval_config.py, server_cli.py, server_launch.py, server_manager.py, server_start.py, server_start_arbitrary.py, server_state.py, server_status.py, server_stop.py, watchdog.py
**Calls out:** httpx

---

### server_state.py (65 LOC)

**Purpose:** Read-only queries over the server state files: lookup by name, health, running presets, class-to-default resolution.
**Reads:** `~/.rag-locks/server-port-{N}.json` state files; `/health` endpoints.
**Writes:** nothing.
**Called by:** constellation.py, embedder.py, reranker.py, retrieval_config.py, server_manager.py, server_start.py, server_start_arbitrary.py, server_status.py, server_stop.py
**Calls out:** (none — stdlib and intra-package only)

---

### server_launch.py (83 LOC)

**Purpose:** Builds server launch commands and runs a launch with health wait and state-file bookkeeping.
**Reads:** `/health` endpoints of the launched server.
**Writes:** server log file under `~/.rag-locks/logs/`; spawns the server process; state files via server_utils.
**Called by:** server_start.py, server_start_arbitrary.py
**Calls out:** (none — stdlib and intra-package only)

---

### server_start.py (79 LOC)

**Purpose:** Workflow to start a preset server: replaces an unhealthy instance, allocates a port and launches.
**Reads:** `~/.rag-locks/server-port-{N}.json` state files.
**Writes:** `src/rag/logs/server_start.log`; spawns a server process via server_launch.
**Called by:** server_cli.py, server_manager.py
**Calls out:** (none — stdlib and intra-package only)

---

### server_start_arbitrary.py (95 LOC)

**Purpose:** Workflow to start a server from an arbitrary model path, with name collision and port checks.
**Reads:** `~/.rag-locks/server-port-{N}.json` state files.
**Writes:** `src/rag/logs/server_start_arbitrary.log`; spawns a server process via server_launch.
**Called by:** server_cli.py
**Calls out:** (none — stdlib and intra-package only)

---

### server_stop.py (34 LOC)

**Purpose:** Workflow to stop a preset server by its state file.
**Reads:** `~/.rag-locks/server-port-{N}.json` state files.
**Writes:** `src/rag/logs/server_stop.log`; kills the server process via server_utils.
**Called by:** constellation.py, server_cli.py, server_manager.py
**Calls out:** (none — stdlib and intra-package only)

---

### server_status.py (21 LOC)

**Purpose:** Workflow that reports running, pid, port and health for every preset server; state-file-only.
**Reads:** `~/.rag-locks/server-port-{N}.json` state files; `/health` endpoints.
**Writes:** nothing.
**Called by:** server_cli.py, status.py
**Calls out:** (none — stdlib and intra-package only)

---

### server_manager.py (66 LOC)

**Purpose:** Workflow that ensures the servers needed for a target are healthy, stopping exclusive competitors and starting missing ones.
**Reads:** (via server_state and server_start).
**Writes:** `src/rag/logs/server_manager.log`; other effects via server_start, server_stop and watchdog.
**Called by:** constellation.py, embedder.py, index_cmd.py, reranker.py, sync.py
**Calls out:** (none — stdlib and intra-package only)

---

### constellation.py (32 LOC)

**Purpose:** Workflow that ensures exactly the requested set of preset servers is running, stopping all others.
**Reads:** (via server_state and server_manager).
**Writes:** `src/rag/logs/constellation.log`; other effects via server_stop and server_manager.
**Called by:** dev scripts under `dev/server_management/` and `dev/retrieval/` (via subprocess)
**Calls out:** (none — stdlib and intra-package only)

---

### server_cli.py (322 LOC)

**Purpose:** CLI surface for `rag-cli server`: dispatches status, start, stop, restart, list, tail, errors and presets subcommands with tabular output.
**Reads:** `~/.rag-locks/server-port-{N}.json` state files (content and mtime for idle display); log files (for tail); error_log (for errors).
**Writes:** stdout for known actions; on an unrecognized action, the fixed help-redirect sentence to stderr and exit code 2; `src/rag/logs/server_cli.log`.
**Called by:** cli.py
**Calls out:** (none — stdlib and intra-package only)

---

### watchdog.py (100 LOC)

**Purpose:** Watchdog subprocess management and idle-timeout enforcement: purges unregistered llama-server orphans and idle-stops servers.
**Reads:** `~/.rag-locks/server-port-{N}.json` state files; `~/.rag-locks/watchdog.pid`.
**Writes:** `src/rag/logs/watchdog.log`; kills orphan/idle server processes; `~/.rag-locks/watchdog.pid`.
**Called by:** constellation.py, server_manager.py, watchdog_main.py
**Calls out:** (none — stdlib and intra-package only)

---

### watchdog_main.py (19 LOC)

**Purpose:** Standalone watchdog entrypoint (`python -m src.rag.watchdog_main`) running the watchdog loop in a detached process and logging an abort.
**Reads:** indirect (via the watchdog loop).
**Writes:** `src/rag/logs/watchdog_main.log` (traceback if the watchdog loop aborts); other effects via the watchdog loop.
**Called by:** none by import; spawned as a detached subprocess by watchdog.py
**Calls out:** (none — stdlib and intra-package only)

---

### splade_server.py (56 LOC)

**Purpose:** Standalone FastAPI server that loads the SPLADE model at startup and serves sparse embeddings and a health endpoint.
**Reads:** HuggingFace model from disk/HF cache at startup.
**Writes:** `src/rag/logs/splade_server.log`.
**Called by:** none by import; launched as a uvicorn subprocess by server_start.py
**Calls out:** fastapi, pydantic, sentence_transformers

---

## State

| Owner | State | Reads | Writes |
|---|---|---|---|
| PostgreSQL `documents` table | All indexed chunks with dense + sparse embeddings | db.py, search_primitives.py | indexer.py, sync.py and delete_cmd.py (delete via indexer) |
| PostgreSQL `indexed_files` table | Per-project (collection, document) to sha256 ledger for change detection | sync.py, index_cmd.py | sync.py (auto-creates on first run); delete_cmd.py (delete) |
| `~/.rag-locks/server-port-{N}.json` | Per-process GPU server state; idle computed from state-file mtime | server_state.py, watchdog.py, status.py, server_cli.py | server_utils.py |
| `~/.rag-locks/watchdog.pid` | Detached watchdog process PID | watchdog.py | watchdog.py |
| `~/.rag-locks/rag.flock` + `rag.lock` | Global RAG mutex (flock fd) plus JSON details | lock.py, status.py | lock.py |
| `src/rag/logs/search.jsonl` + `search_content.jsonl` | Lean record per search plus content sidecar, joined by search id | (no readers yet) | retrieval_log.py |
| `src/rag/logs/expand.jsonl` + `expand_content.jsonl` | Lean record per expansion plus content sidecar, joined by expand id | (no readers yet) | expand_log.py |
| `src/rag/logs/config_registry.jsonl` | One entry per distinct configuration fingerprint with first-seen timestamp | retrieval_log.py | retrieval_log.py |
