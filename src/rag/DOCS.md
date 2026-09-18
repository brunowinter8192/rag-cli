# src/rag/ — RAG Pipeline Modules

## Role

Core implementation of the RAG pipeline: dense (Qwen3) embedding, PostgreSQL/pgvector storage, dense retrieval with cross-encoder reranking (always-on), and GPU server lifecycle management. Touch this package when changing retrieval logic, embedding models, indexing behavior, or server startup. Do NOT touch for Skills/Commands (project root) or dev scripts (`dev/`).

## Public Interface

`__init__.py` is empty — import directly from sub-modules:
- `from src.rag.retriever import search_workflow, format_results` — primary entry point (cli.py)
- `from src.rag.db import get_connection` — direct DB access in scripts

## Flow

**Retrieval (per query):** `retriever.py` workflow → `db.py` opens connection + validates collection → `search_primitives.py` embeds query and runs vector search (RERANK_CANDIDATES=30) → `reranker.py` re-scores top 30 → `formatting.py` serializes output. Context expansion (neighboring chunks) via `expand_chunks_workflow` using `--before`/`--after`. Both `search_workflow` and `expand_chunks_workflow` hand their timing and result data to `retrieval_log.py`, which writes a lean JSONL record plus a content sidecar; `search_workflow` additionally hands `len(query_vector)` and `RERANK_CANDIDATES` through so `retrieval_log.py` can resolve a configuration fingerprint via `retrieval_config.py` (reads the live server state files, never the module constants) and attach it to the record.

**Indexing (per batch):** `chunker.py` splits document → `indexer.py` embeds chunks via `embedder.py` (dense only) and inserts into PostgreSQL. `server_manager.py` ensures GPU servers are running before embedding starts.

**Manifest-driven sync (per project, end of session):** `sync.py` reads `<project>/.rag-docs.json`, expands the include-globs, hashes each matched `.md` file, and diffs against the `indexed_files` tracking table. Only added/updated files are re-chunked + re-embedded; removed files are deleted from the index; unchanged files are skipped. Reuses chunker/indexer/server_manager primitives — no re-implementation of embedding or storage.

**Logging (cross-cutting):** every module that logs calls `log_setup.get_logger(name)` once at import time and gets back a `logging.Logger` with its own `FileHandler` attached directly (not via the root logger), writing to `src/rag/logs/<name>.log`. This is the single log root for all Python `logging` output in the package — no module calls `logging.basicConfig` anymore. `~/.rag-locks/logs/` remains in use only for subprocess stdout redirection (llama-server / uvicorn processes), a different concern entirely.

## Modules

### db.py (185 LOC)

**Purpose:** PostgreSQL connection factory, collection/document queries, and WHERE-clause filter builders shared across retrieval sub-modules.
**Reads:** `.env` (POSTGRES_* connection params, `RAG_PG_CONTAINER`); PostgreSQL `documents` table; `docker info` (daemon probe).
**Writes:** nothing to the DB (read-only queries); side effect: may launch OrbStack + start the Postgres container.
**Called by:** retriever.py, search_primitives.py, indexer.py, sync.py, index_cmd.py, status.py
**Calls out:** psycopg2, pgvector, python-dotenv, subprocess (`open`/`docker`)

---

### embedder.py (65 LOC)

**Purpose:** HTTP client for the llama-server dense embedding endpoint; auto-starts the embedding GPU server on first call via `server_manager.ensure_ready`.
**Reads:** `EMBEDDING_URL` env (override) or `server_manager.find_server_url('embedding')` for URL; llama-server `/v1/embeddings` response.
**Writes:** `src/rag/logs/embedder.log` (via `log_setup.get_logger`); bumps `~/.rag-locks/server-port-{N}.json` mtime before each request (via `_touch_state_file`) so the watchdog idle timer reflects real inference activity.
**Called by:** search_primitives.py, indexer.py
**Calls out:** httpx

---

### reranker.py (60 LOC)

**Purpose:** HTTP client for the llama-server cross-encoder reranking endpoint; re-scores candidate result lists by query-document relevance. Defines `RERANK_INSTRUCTION = None`, documenting that no reranker instruction is sent today.
**Reads:** `RERANKER_URL` env (override) or `server_manager.find_server_url('reranker')` for URL; llama-server `/v1/rerank` response.
**Writes:** `src/rag/logs/reranker.log` (via `log_setup.get_logger`); bumps `~/.rag-locks/server-port-{N}.json` mtime before each request (via `_touch_state_file`).
**Called by:** retriever.py; `RERANK_INSTRUCTION` read by retrieval_config.py
**Calls out:** httpx

---

### search_primitives.py (62 LOC)

**Purpose:** Low-level search functions — `embed_query`, vector cosine search against PostgreSQL.
**Reads:** PostgreSQL `documents` table (via `conn` parameter); embedding server (via embedder).
**Writes:** nothing.
**Called by:** retriever.py
**Calls out:** (none — all via internal modules: db, embedder)

---

### formatting.py (53 LOC)

**Purpose:** Serialize search results, collections, and document lists as human-readable strings for CLI stdout.
**Reads:** in-memory result lists.
**Writes:** nothing.
**Called by:** retriever.py (imported then re-exported)
**Calls out:** (none — pure Python)

---

### retriever.py (107 LOC)

**Purpose:** Workflow orchestration for retrieval operations (search, list_collections, list_documents, expand_chunks). Hosts `merge_chunks` + `find_overlap` helpers. Re-exports `format_*` functions for cli.py backward compatibility.
**Reads:** PostgreSQL via db; embedding/reranker servers via search_primitives/reranker.
**Writes:** nothing directly — hands query/filters/timing/results/`len(query_vector)`/`RERANK_CANDIDATES` to `retrieval_log.log_search` and `retrieval_log.log_expand` after every `search_workflow` / `expand_chunks_workflow` call. There is no plain-text `retriever.log`; its previous two `logging.info` lines (query truncated to 50 chars, no collection/filters/results recorded) are superseded entirely by the structured `search.jsonl` / `expand.jsonl` records — see retrieval_log.py.
**Called by:** cli.py
**Calls out:** retrieval_log (intra-package)

---

### log_setup.py (21 LOC)

**Purpose:** Owns the single Python-logging configuration point for the whole package — `get_logger(name)` returns a logger with its own `FileHandler` under `src/rag/logs/<name>.log`, never via the shared root logger.
**Reads:** nothing.
**Writes:** creates `src/rag/logs/` if missing; each returned logger writes to its own `<name>.log`.
**Called by:** chunker.py, embedder.py, reranker.py, indexer.py, sync.py, splade_server.py, server_utils.py, server_lifecycle.py, server_manager.py, watchdog.py, lock.py.
**Calls out:** (none — stdlib only: logging, pathlib)

---

### retrieval_config.py (66 LOC)

**Purpose:** Resolves the embedding/reranker configuration that actually answered a search from the running servers' own state, never from module constants. `resolve_search_config` is the single entry point; returns the full config snapshot later hashed and registered by retrieval_log.py.
**Reads:** `~/.rag-locks/server-port-{N}.json` (via `server_manager.find_server_state`, no network call); `SERVERS[preset]["extra_flags"]` (via `server_manager.context_size_for_preset`); `embedder.MAX_TOKENS`, `search_primitives.DEFAULT_QUERY_PREFIX`, `reranker.RERANK_INSTRUCTION`.
**Writes:** nothing.
**Called by:** retrieval_log.py
**Calls out:** embedder, reranker, search_primitives, server_manager (intra-package)

---

### retrieval_log.py (193 LOC)

**Purpose:** Structured, never-raising JSONL logging for retrieval entry points — `log_search` after every `search_workflow` call, `log_expand` after every `expand_chunks_workflow` call. Each writes a lean lookup record and a content-bearing sidecar, linked by a generated id. `log_search` also resolves and attaches a configuration fingerprint.
**Reads:** `src/rag/logs/config_registry.jsonl` (membership check before appending a new fingerprint's entry).
**Writes:** `src/rag/logs/search.jsonl`, `src/rag/logs/search_content.jsonl`, `src/rag/logs/expand.jsonl`, `src/rag/logs/expand_content.jsonl`, `src/rag/logs/config_registry.jsonl`. A write that raises for any reason never propagates — reported via `error_log.write(..., code="log_write_failed")`; a config-resolution failure is reported separately via `code="log_config_resolve_failed"`; both fall back to `stderr` only if the `error_log` write itself also fails.
**Called by:** retriever.py
**Calls out:** error_log, log_setup, retrieval_config (intra-package)

---

### chunker.py (102 LOC)

**Purpose:** Split markdown documents into semantic chunks using recursive character splitting at paragraph → sentence → word boundaries.
**Reads:** markdown file from disk.
**Writes:** `src/rag/logs/chunker.log` (via `log_setup.get_logger`); returns chunk list, caller writes the JSON sidecar.
**Called by:** index_cmd.py, sync.py
**Calls out:** log_setup (intra-package)

---

### index_cmd.py (180 LOC)

**Purpose:** Index-command workflow — orchestrates chunk + embed for `cli.py index`. Routes to `_index_single_file` (single `.md` via `--document`) or `_index_collection` (all `.md` in collection dir). Carries the skip/adopt/index bucket logic and `update_progress` calls.
**Reads:** `.md` files from `data/documents/<collection>/`; PostgreSQL `indexed_files` and `documents` tables (via sync/indexer helpers).
**Writes:** `chunks.json` sidecars next to source `.md` files; PostgreSQL `indexed_files` (upsert via sync helpers) and `documents` (via indexer).
**Called by:** cli.py (lazy import for `index` subcommand)
**Calls out:** chunker, db, indexer, lock, server_manager, sync (intra-package)

---

### indexer.py (267 LOC)

**Purpose:** Index chunks into PostgreSQL with dense embeddings (sparse_embedding stays NULL for new chunks); handles schema creation, batch insert, deletion by collection/document (chunks + manifest + source files), and per-document completeness check (`doc_is_complete`) used by index_cmd.py for adopt-on-complete skip logic.
**Reads:** `chunks.json` from disk; `.env` for connection params; PostgreSQL schema state.
**Writes:** `src/rag/logs/indexer.log` (via `log_setup.get_logger`); PostgreSQL `documents` table (insert, delete, schema init); `indexed_files` table (delete via `delete_manifest_rows()`); on-disk source files removed by `delete_workflow()`.
**Called by:** sync.py, index_cmd.py, cli.py (lazy import for `delete` subcommand)
**Calls out:** psycopg2, pgvector, python-dotenv; lock (update_progress)

---

### sync.py (282 LOC)

**Purpose:** Manifest-driven project doc indexing with hash-based change detection. Reads `<project>/.rag-docs.json` (single- or multi-collection format), expands include-globs with component-based directory exclusions, hashes matched `.md` files, diffs against the `indexed_files` table, and only re-indexes the deltas. Composes existing chunker / indexer / server_manager primitives — no re-implementation of embedding or storage.
**Reads:** `<project>/.rag-docs.json` manifest; matched `.md` files from disk; PostgreSQL `indexed_files` table.
**Writes:** `src/rag/logs/sync.log` (via `log_setup.get_logger`); PostgreSQL `indexed_files` (upsert/delete) and `documents` (via indexer primitives); `~/.rag-locks/rag.lock` (chunk-level progress via `update_progress`, only when doc context params are provided).
**Called by:** cli.py (`update_docs` subcommand), index_cmd.py (`ensure_indexed_files_table`, `get_db_hashes`, `upsert_hash`, `compute_hash`)
**Calls out:** hashlib, json, pathlib (stdlib only — all RAG-specific calls are intra-package: chunker, indexer, db, lock, server_manager, log_setup)

---

### server_manager.py (104 LOC)

**Purpose:** Thin coordinator. Defines `ensure_ready` and `ensure_constellation` (API entry points), `_stop_exclusive` / `_get_running_presets` (exclusivity helpers), and re-exports the full public surface from the four sub-modules (including `find_server_state` and `context_size_for_preset`) so all callers remain unchanged. All server logic lives in the sub-modules.
**Reads:** (via sub-modules)
**Writes:** `src/rag/logs/server_manager.log` (via `log_setup.get_logger`); other effects via sub-modules.
**Called by:** embedder.py, reranker.py, retrieval_config.py, cli.py (lazy import for `server` subcommand), index_cmd.py (`ensure_ready`, `RAG_ROOT`), sync.py (`ensure_ready` before embed), indexer.py (lazy import of `RAG_ROOT`), status.py, watchdog_main.py (`_watchdog_loop`).
**Calls out:** server_utils, server_lifecycle, watchdog, server_cli, log_setup (intra-package).

---

### server_utils.py (255 LOC)

**Purpose:** Shared constants + process utilities used by all server sub-modules. Contains the SERVERS preset dict (no `default_port` — ports are fully dynamic), all path constants, `_CLASS_MAP`, and the process primitives (`find_pid_on_port`, `find_all_pids_on_port`, `pgrep_llama_server`, `_check_health_port`, `_stop_by_state`, `_pid_alive`, `_allocate_port`, `_resolve_port`, `context_size_for_preset`) plus state-file I/O helpers. Dependency root — no imports from other server sub-modules. `LOG_DIR` here is `~/.rag-locks/logs/` — a *different* concern from `log_setup.LOG_ROOT`: it is the subprocess-stdout redirect target for llama-server/uvicorn processes (consumed by server_lifecycle.py), not Python `logging` output. `context_size_for_preset` reads `SERVERS[preset]["extra_flags"]` — the launch command, i.e. launch *intent*; it does not verify what context size the running process actually honors (no `/props` call, by design — see retrieval_config.py).
**Reads:** env vars (RAG_PROJECT_ROOT, LLAMA_SERVER_PATH, port overrides, IDLE_TIMEOUT); `lsof`/`pgrep` subprocess; httpx `/health` endpoints; `~/.rag-locks/server-port-{N}.json` (state file reads).
**Writes:** `src/rag/logs/server_utils.log` (via `log_setup.get_logger`); `~/.rag-locks/server-port-{N}.json` (via `_write_state_file`, `_unlink_state_file`; mtime bump via `_touch_state_file`); kills processes (via `_stop_by_state`).
**Called by:** server_lifecycle.py, watchdog.py, server_cli.py, server_manager.py.
**Calls out:** httpx, subprocess, error_log, log_setup.

---

### server_lifecycle.py (323 LOC)

**Purpose:** Start/stop/restart logic for preset and arbitrary servers, plus state query functions. Manages single-instance enforcement, health polling on startup, port allocation, and process command construction. `status()` and `check_health()` are state-file-only — no state file means not running. Provides `find_server_state`/`find_server_url` (the latter now a thin wrapper over the former) and `check_health` used by embedder/reranker/retrieval_config callers.
**Reads:** `~/.rag-locks/server-port-{N}.json` state files (via `find_server_url`, `start` single-instance check); `/health` endpoints via `_check_health_port` (delegated to server_utils).
**Writes:** `src/rag/logs/server_lifecycle.log` (via `log_setup.get_logger`); spawns server processes (via `start`, `start_arbitrary`) with their stdout redirected to `~/.rag-locks/logs/` (`server_utils.LOG_DIR`, out of scope for Python logging); state files via server_utils helpers.
**Called by:** server_manager.py (re-exports), server_cli.py, watchdog.py (imports `_stop_by_state` indirectly via server_utils).
**Calls out:** httpx, subprocess, server_utils (constants + primitives), error_log, log_setup.

---

### watchdog.py (110 LOC)

**Purpose:** Watchdog subprocess management and idle-timeout enforcement. `_ensure_watchdog_process` spawns a detached singleton process; `_watchdog_loop` runs inside it. Per-tick: purges unregistered llama-server orphans, idle-stops servers whose state exceeds `IDLE_TIMEOUT`.
**Reads:** `~/.rag-locks/server-port-{N}.json` state files; `~/.rag-locks/watchdog.pid`.
**Writes:** `src/rag/logs/watchdog.log` (via `log_setup.get_logger`); kills orphan/idle server processes (via `_stop_by_state`); `~/.rag-locks/watchdog.pid`.
**Called by:** server_manager.py (re-exports `_ensure_watchdog_process`, `_watchdog_loop`); watchdog_main.py (runs `_watchdog_loop`).
**Calls out:** server_utils (constants + `_stop_by_state` + `_pid_alive` + `_check_health_port` + `pgrep_llama_server`), error_log, log_setup.

---

### server_cli.py (309 LOC)

**Purpose:** CLI surface for `rag-cli server`. Dispatches status, start, stop, restart, list, tail, errors, and presets subcommands. Formats tabular output for terminal display.
**Reads:** `~/.rag-locks/server-port-{N}.json` state files (content + mtime for idle display in `list`); log files (for `tail`); error_log (for `errors` subcommand).
**Writes:** stdout for known actions; on an unrecognized action, the fixed help-redirect sentence to stderr and `exit(2)`.
**Called by:** cli.py (lazy import).
**Calls out:** server_utils (SERVERS, TIMESTAMP_DIR, `_stop_by_state`, `_check_health_port`), server_lifecycle (start, stop, restart, start_all, stop_all, start_arbitrary, status), error_log.

---

### watchdog_main.py (6 LOC)

**Purpose:** Standalone watchdog entrypoint — invoked as `python -m src.rag.watchdog_main`. Imports server_manager and runs `_watchdog_loop()` directly. Spawned as detached process by `_ensure_watchdog_process()`; survives parent exit.
**Reads:** indirect (via `_watchdog_loop`).
**Writes:** indirect (via `stop`).
**Called by:** subprocess invocation only — no Python imports.
**Calls out:** server_manager (intra-package).

---

### splade_server.py (59 LOC)

**Purpose:** Standalone FastAPI server that loads the SPLADE model at startup and exposes `/v1/sparse-embeddings` and `/health` on port 8083.
**Reads:** HuggingFace model (`naver/splade-v3`, `MAX_ACTIVE_DIMS = 256`) from disk/HF cache at startup.
**Writes:** `src/rag/logs/splade_server.log` (via `log_setup.get_logger`) — distinct from `~/.rag-locks/logs/splade_server.log`, which is this process's own stdout, redirected by the launching `server_lifecycle.py._launch`, not written by this module.
**Called by:** (none — subprocess target launched by `server_manager.py`, never imported by Python code)
**Calls out:** fastapi, uvicorn, torch, transformers, log_setup

---

### lock.py (155 LOC)

**Purpose:** Global RAG mutex via `fcntl.flock` + JSON lockfile; provides `acquire` context manager, `read`, `update_progress`, and `heartbeat` functions used by cli.py. `acquire` runs an auto-heartbeat daemon thread so long-running operations don't need to call `heartbeat()` explicitly.
**Reads:** `~/.rag-locks/rag.flock` (fd hold); `~/.rag-locks/rag.lock` (JSON details).
**Writes:** `src/rag/logs/lock.log` (via `log_setup.get_logger`, warnings only); `~/.rag-locks/rag.flock`; `~/.rag-locks/rag.lock` (atomic tmp+rename with pid, command, kind, started_at, heartbeat, progress).
**Lock scope (cli.py):** `acquire` is called **only** by write commands (`index`, `update_docs`, `delete`). Read commands (`search`, `list_collections`, `list_documents`, `progress`, `expand_chunks`) are fully lock-free.
**Called by:** cli.py (write path only), index_cmd.py (`heartbeat`, `update_progress`), indexer.py (`update_progress`), sync.py (`update_progress`), status.py (read-only via `read`)
**Calls out:** log_setup (intra-package); stdlib fcntl, json, os, pathlib, threading

---

### status.py (150 LOC)

**Purpose:** Gather lock state, GPU server health, and Postgres reachability into a single dict for `rag-cli status`; formats the output for terminal display.
**Reads:** `lock.read()` for lock state; `server_manager.box_status()` for server state; `~/.rag-locks/server-port-{port}.json` mtime directly for idle display; Postgres connect probe (2s timeout).
**Writes:** nothing.
**Called by:** cli.py (`status` subcommand)
**Calls out:** (none — all via lock, server_manager, db intra-package)

---

### error_log.py (58 LOC)

**Purpose:** Append structured error entries to `src/rag/logs/errors.jsonl`; O_APPEND write is POSIX-atomic for writes under PIPE_BUF, no locking needed. Defines `ERROR_CODES` (frozenset of 6 genuine anomaly codes) to separate lifecycle noise from real failures.
**Reads:** `src/rag/logs/errors.jsonl` (via `read_all`, `read_today`, `read_errors_today`).
**Writes:** `src/rag/logs/errors.jsonl` (one JSON line per error event).
**Called by:** server_utils.py, server_lifecycle.py, watchdog.py, server_cli.py, retrieval_log.py (failure-reporting path only)
**Calls out:** (none — stdlib only: json, pathlib)

---

### server_lock.py (64 LOC)

**Purpose:** Per-server flock context manager (`acquire`) with `ServerBusyError` — intended for serializing concurrent HTTP calls to a single GPU server instance.
**Reads:** `~/.rag-locks/rag-server-{name}.busy.flock`; `~/.rag-locks/rag-server-{name}.busy` (JSON).
**Writes:** `~/.rag-locks/rag-server-{name}.busy.flock`; `~/.rag-locks/rag-server-{name}.busy` (atomic).
**Called by:** [] (DEAD CODE — no import callers found; verify before removing)
**Calls out:** (none — stdlib only: fcntl, json, os, pathlib)

---

## State

| Owner | State | Reads | Writes |
|---|---|---|---|
| PostgreSQL `documents` table | All indexed chunks with dense + sparse embeddings | db.py, search_primitives.py | indexer.py (insert/delete/schema), sync.py (delete via indexer primitives) |
| PostgreSQL `indexed_files` table | Per-project (collection, document) → sha256 + last_indexed_at; sync.py's change-detection ledger | sync.py (diff against current file hashes) | sync.py (upsert/delete; auto-creates table on first run); indexer.py (delete via `delete_manifest_rows()`) |
| `~/.rag-locks/server-port-{N}.json` | Per-process GPU server state (pid, port, model_path, model_name, mode, log_path, start_time, name); idle computed from state-file mtime | server_lifecycle.py (`find_server_url`, `start` single-instance check), watchdog.py, status.py, server_cli.py | server_utils.py (`_write_state_file` after Popen; `_unlink_state_file` / `_stop_by_state` on stop) |
| `~/.rag-locks/watchdog.pid` | Detached watchdog process PID for ensure-singleton spawn | watchdog.py (`_ensure_watchdog_process`) | watchdog.py (`_ensure_watchdog_process`) |
| `~/.rag-locks/rag.flock` + `rag.lock` | Global RAG mutex (flock fd) + JSON details (pid, command, kind, started_at, heartbeat, progress) | lock.py, status.py | lock.py (`acquire`, `heartbeat`, `update_progress`) |
| `src/rag/logs/search.jsonl` + `search_content.jsonl` | One lean record per `search` call (query, collection, filters, candidate count, duration, per-hit rank/document/chunk_index/score, `config_fingerprint`) plus a content sidecar (full chunk text per hit), joined by `search_id` | (no readers in the codebase yet — append-only observability trail) | retrieval_log.py (`log_search`, called from retriever.py) |
| `src/rag/logs/expand.jsonl` + `expand_content.jsonl` | One lean record per `expand_chunks` call plus a content sidecar (merged expanded text), joined by `expand_id`. No `config_fingerprint` — `expand_chunks_workflow` touches no model. | (no readers in the codebase yet) | retrieval_log.py (`log_expand`, called from retriever.py) |
| `src/rag/logs/config_registry.jsonl` | One entry per distinct configuration fingerprint (embedding preset/model/path/quantization/context_size/vector_dimension, query prefix, truncation limit, reranker preset/model/path/quantization/context_size/instruction, candidate count requested), first-seen timestamp. Membership checked by reading the whole file — no lock; a fresh process per CLI call rules out an in-process cache, so two concurrent searches under a new config can each append an identical duplicate line. Harmless, not prevented — the read path stays lock-free. | retrieval_log.py (`known_fingerprints`, before appending) | retrieval_log.py (`ensure_registry_entry`) |
