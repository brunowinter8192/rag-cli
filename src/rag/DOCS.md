# src/rag/ — RAG Pipeline Modules

## Role

Core implementation of the RAG pipeline: dense (Qwen3) embedding, PostgreSQL/pgvector storage, dense retrieval with cross-encoder reranking (always-on), and GPU server lifecycle management. Touch this package when changing retrieval logic, embedding models, indexing behavior, or server startup. Do NOT touch for Skills/Commands (project root) or dev scripts (`dev/`).

## Public Interface

`__init__.py` is empty — import directly from sub-modules:
- `from src.rag.retriever import search_workflow, format_results` — primary entry point (cli.py)
- `from src.rag.db import get_connection` — direct DB access in scripts

## Flow

**Retrieval (per query):** `retriever.py` workflow → `db.py` opens connection + validates collection → `search_primitives.py` embeds query and runs vector search (RERANK_CANDIDATES=30) → `reranker.py` re-scores top 30 → `formatting.py` serializes output. Context expansion (neighboring chunks) via `read_document_workflow` using `--before`/`--after`.

**Indexing (per batch):** `chunker.py` splits document → `indexer.py` embeds chunks via `embedder.py` (dense only) and inserts into PostgreSQL. `server_manager.py` ensures GPU servers are running before embedding starts.

**Manifest-driven sync (per project, end of session):** `sync.py` reads `<project>/.rag-docs.json`, expands the include-globs, hashes each matched `.md` file, and diffs against the `indexed_files` tracking table. Only added/updated files are re-chunked + re-embedded; removed files are deleted from the index; unchanged files are skipped. Reuses chunker/indexer/server_manager primitives — no re-implementation of embedding or storage.

## Modules

### db.py (202 LOC)

**Purpose:** PostgreSQL connection factory, collection/document queries, and WHERE-clause filter builder shared across retrieval sub-modules. `get_connection` self-heals on connection failure: catches `OperationalError`, calls `ensure_postgres_up()` (boots OrbStack daemon via `open -a OrbStack` if down, then `docker start` the `PG_CONTAINER` container, polls reachability), and retries the connect once. Triggered only on actual failure — no latency on the normal path. macOS only.
**Reads:** `.env` (POSTGRES_* connection params, `RAG_PG_CONTAINER`); PostgreSQL `documents` table; `docker info` (daemon probe).
**Writes:** nothing to the DB (read-only queries); side effect: may launch OrbStack + start the Postgres container.
**Called by:** retriever.py, search_primitives.py, indexer.py, sync.py, index_cmd.py, status.py
**Calls out:** psycopg2, pgvector, python-dotenv, subprocess (`open`/`docker`)

---

### embedder.py (76 LOC)

**Purpose:** HTTP client for the llama-server dense embedding endpoint; auto-starts the embedding GPU server on first call via `server_manager.ensure_ready`.
**Reads:** `EMBEDDING_URL` env (override) or `server_manager.find_server_url('embedding')` for URL; llama-server `/v1/embeddings` response.
**Writes:** `src/rag/logs/embedder.log`; bumps `~/.rag-locks/server-port-{N}.json` mtime before each request (via `_touch_state_file`) so the watchdog idle timer reflects real inference activity.
**Called by:** search_primitives.py, indexer.py
**Calls out:** httpx

---

### sparse_embedder.py (60 LOC)

**Purpose:** HTTP client for the SPLADE server sparse embedding endpoint; mirrors `embedder.py` interface. Not called on the prod indexing path — `backfill_splade_workflow` removed.
**Reads:** `SPLADE_URL` env (override) or `server_manager.find_server_url('splade')` for URL; SPLADE server `/v1/sparse-embeddings` response.
**Writes:** `src/rag/logs/sparse_embedder.log`; bumps `~/.rag-locks/server-port-{N}.json` mtime before each request (via `_touch_state_file`).
**Called by:** [] (DEAD CODE — `backfill_splade_workflow` removed; verify before removing module)
**Calls out:** httpx

---

### reranker.py (68 LOC)

**Purpose:** HTTP client for the llama-server cross-encoder reranking endpoint; re-scores candidate result lists by query-document relevance.
**Reads:** `RERANKER_URL` env (override) or `server_manager.find_server_url('reranker')` for URL; llama-server `/v1/rerank` response.
**Writes:** `src/rag/logs/reranker.log`; bumps `~/.rag-locks/server-port-{N}.json` mtime before each request (via `_touch_state_file`).
**Called by:** retriever.py
**Calls out:** httpx

---

### search_primitives.py (129 LOC)

**Purpose:** Low-level search functions — `embed_query`, vector cosine search, BM25 full-text search against PostgreSQL. `splade_search` removed (2026-05-26).
**Reads:** PostgreSQL `documents` table (via `conn` parameter); embedding server (via embedder).
**Writes:** nothing.
**Called by:** retriever.py
**Calls out:** (none — all via internal modules: db, embedder)

---


### formatting.py (59 LOC)

**Purpose:** Serialize search results, collections, and document lists as human-readable strings for CLI stdout.
**Reads:** in-memory result lists.
**Writes:** nothing.
**Called by:** retriever.py (imported then re-exported — see Gotchas)
**Calls out:** (none — pure Python)

---

### retriever.py (115 LOC)

**Purpose:** Workflow orchestration for retrieval operations (search, search_hybrid, list_collections, list_documents, read_document). `search_hybrid_workflow` is unconditionally dense+rerank: `search_vectors(RERANK_CANDIDATES=30)` → `rerank_workflow(top_k=10)`. No cc-fusion path, no SPLADE call, no `rerank` parameter. Hosts `merge_chunks` + `find_overlap` helpers. Re-exports `format_*` functions for cli.py backward compatibility.
**Reads:** PostgreSQL via db; embedding/reranker servers via search_primitives/reranker.
**Writes:** `src/rag/logs/retriever.log` (via `logging.basicConfig`).
**Called by:** cli.py
**Calls out:** (none — all external calls delegated to sub-modules)

---

### chunker.py (116 LOC)

**Purpose:** Split markdown documents into semantic chunks using recursive character splitting at paragraph → sentence → word boundaries.
**Reads:** markdown file from disk.
**Writes:** nothing (returns chunk list; caller writes JSON).
**Called by:** index_cmd.py, sync.py
**Calls out:** (none — pure Python)

---

### index_cmd.py (162 LOC)

**Purpose:** Index-command workflow — orchestrates chunk + embed for `cli.py index`. Routes to `_index_single_file` (single `.md` via `--document`) or `_index_collection` (all `.md` in collection dir). Carries the skip/adopt/index bucket logic and `update_progress` calls. Heartbeat is provided by `lock.acquire`'s built-in daemon thread (active for the entire lock window). Hosts `_write_chunks_json` (chunks.json sidecar writer, moved here from cli.py).
**Reads:** `.md` files from `data/documents/<collection>/`; PostgreSQL `indexed_files` and `documents` tables (via sync/indexer helpers).
**Writes:** `chunks.json` sidecars next to source `.md` files; PostgreSQL `indexed_files` (upsert via sync helpers) and `documents` (via indexer).
**Called by:** cli.py (lazy import for `index` subcommand)
**Calls out:** chunker, db, indexer, lock, server_manager, sync (intra-package)

---

### indexer.py (250 LOC)

**Purpose:** Index chunks into PostgreSQL with dense embeddings (sparse_embedding stays NULL for new chunks); handles schema creation, batch insert, deletion by collection/document (chunks + manifest + source files), and per-document completeness check (`doc_is_complete`) used by index_cmd.py for adopt-on-complete skip logic.
**Reads:** `chunks.json` from disk; `.env` for connection params; PostgreSQL schema state.
**Writes:** PostgreSQL `documents` table (insert, delete, schema init); `indexed_files` table (delete via `delete_manifest_rows()`); on-disk source files removed by `delete_workflow()` — collection dir (`shutil.rmtree`) or per-document `.md` + `.json` sidecar (`md_path.with_suffix('.json')`).
**Called by:** sync.py, index_cmd.py, cli.py (lazy import for `delete` subcommand)
**Calls out:** psycopg2, pgvector, python-dotenv

---

### sync.py (341 LOC)

**Purpose:** Manifest-driven project doc indexing with hash-based change detection. Reads `<project>/.rag-docs.json` (single- or multi-collection format — `"collection"` key for legacy, `"collections"` array for multi), expands include-globs with component-based directory exclusions (`GLOB_EXCLUDE_DIRS`: `.git`, `venv`, `node_modules`, `__pycache__`) plus worktree copy exclusion via `_is_excluded_path()` consecutive-part check, hashes matched `.md` files, diffs against the `indexed_files` table, and only re-indexes the deltas. Multi-collection result is keyed by collection name; single-collection is the flat dict (backward-compatible). Composes existing chunker / indexer / server_manager primitives — no re-implementation of embedding or storage.
**Reads:** `<project>/.rag-docs.json` manifest; matched `.md` files from disk; PostgreSQL `indexed_files` table.
**Writes:** `src/rag/logs/sync.log`; PostgreSQL `indexed_files` (upsert/delete) and `documents` (via indexer primitives).
**Called by:** cli.py (`update_docs` subcommand), index_cmd.py (`ensure_indexed_files_table`, `get_db_hashes`, `upsert_hash`, `compute_hash`)
**Calls out:** hashlib, json, pathlib, logging (stdlib only — all RAG-specific calls are intra-package: chunker, indexer, db, server_manager)

---

### server_manager.py (120 LOC)

**Purpose:** Thin coordinator. Defines `ensure_ready` and `ensure_constellation` (API entry points), `_stop_exclusive` / `_get_running_presets` (exclusivity helpers), and re-exports the full public surface from the four sub-modules so all callers remain unchanged. All server logic lives in the sub-modules.
**Reads:** (via sub-modules)
**Writes:** (via sub-modules)
**Called by:** embedder.py, sparse_embedder.py, reranker.py, cli.py (lazy import for `server` subcommand), index_cmd.py (`ensure_ready`, `RAG_ROOT`), sync.py (`ensure_ready` before embed), indexer.py (lazy import of `RAG_ROOT`), status.py, watchdog_main.py (`_watchdog_loop`).
**Calls out:** server_utils, server_lifecycle, watchdog, server_cli (intra-package).

---

### server_utils.py (283 LOC)

**Purpose:** Shared constants + process utilities used by all server sub-modules. Contains the SERVERS preset dict (no `default_port` — ports are fully dynamic), all path constants, `_CLASS_MAP`, and the eight process primitives (`find_pid_on_port`, `find_all_pids_on_port`, `pgrep_llama_server`, `_check_health_port`, `_stop_by_state`, `_pid_alive`, `_allocate_port`, `_resolve_port`) plus state-file I/O helpers (`_write_state_file`, `_unlink_state_file`, `_touch_state_file`). Dependency root — no imports from other server sub-modules.
**Reads:** env vars (RAG_PROJECT_ROOT, LLAMA_SERVER_PATH, port overrides, IDLE_TIMEOUT); `lsof`/`pgrep` subprocess; httpx `/health` endpoints; `~/.rag-locks/server-port-{N}.json` (state file reads in `_stop_by_state`, `_unlink_state_file`).
**Writes:** `~/.rag-locks/server-port-{N}.json` (via `_write_state_file`, `_unlink_state_file`; mtime bump via `_touch_state_file`); kills processes (via `_stop_by_state`); `~/.rag-locks/logs/server_manager.log` (logging.basicConfig target). `LOG_DIR = ~/.rag-locks/logs/` — fixed worktree-independent path so server logs survive worktree cleanup (per-module Python loggers in chunker/embedder/etc. keep their own local `<project>/src/rag/logs/` paths).
**Called by:** server_lifecycle.py, watchdog.py, server_cli.py, server_manager.py.
**Calls out:** httpx, subprocess, error_log.

---

### server_lifecycle.py (358 LOC)

**Purpose:** Start/stop/restart logic for preset and arbitrary servers, plus state query functions. Manages single-instance enforcement, health polling on startup, port allocation (always dynamic via `_allocate_port` for presets; `_resolve_port` for arbitrary user-specified ports), and process command construction. `status()` and `check_health()` are state-file-only — no state file means not running. Provides `find_server_url` and `check_health` used by embedder/reranker/sparse_embedder callers.
**Reads:** `~/.rag-locks/server-port-{N}.json` state files (via `find_server_url`, `start` single-instance check); `/health` endpoints via `_check_health_port` (delegated to server_utils).
**Writes:** spawns server processes (via `start`, `start_arbitrary`); state files via server_utils helpers.
**Called by:** server_manager.py (re-exports), server_cli.py, watchdog.py (imports `_stop_by_state` indirectly via server_utils).
**Calls out:** httpx, subprocess, server_utils (constants + primitives), error_log.

---

### watchdog.py (112 LOC)

**Purpose:** Watchdog subprocess management and idle-timeout enforcement. `_ensure_watchdog_process` spawns a detached singleton process; `_watchdog_loop` runs inside it (via `watchdog_main.py`). Per-tick: purges unregistered llama-server orphans, idle-stops servers whose state-file mtime exceeds `IDLE_TIMEOUT`.
**Reads:** `~/.rag-locks/server-port-{N}.json` state files (content + mtime for idle calculation); `~/.rag-locks/watchdog.pid`.
**Writes:** kills orphan/idle server processes (via `_stop_by_state`); `~/.rag-locks/watchdog.pid`.
**Called by:** server_manager.py (re-exports `_ensure_watchdog_process`, `_watchdog_loop`); watchdog_main.py (runs `_watchdog_loop`).
**Calls out:** server_utils (constants + `_stop_by_state` + `_pid_alive` + `_check_health_port` + `pgrep_llama_server`), error_log.

---

### server_cli.py (314 LOC)

**Purpose:** CLI surface for `rag-cli server`. Dispatches status, start, stop, restart, list, tail, errors, and presets subcommands. Formats tabular output for terminal display.
**Reads:** `~/.rag-locks/server-port-{N}.json` state files (content + mtime for idle display in `list`); log files (for `tail`); error_log (for `errors` subcommand).
**Writes:** stdout only.
**Called by:** cli.py (lazy import).
**Calls out:** server_utils (SERVERS, TIMESTAMP_DIR, `_stop_by_state`, `_check_health_port`), server_lifecycle (start, stop, restart, start_all, stop_all, start_arbitrary, status), error_log.

---

### watchdog_main.py (7 LOC)

**Purpose:** Standalone watchdog entrypoint — invoked as `python -m src.rag.watchdog_main`. Imports server_manager and runs `_watchdog_loop()` directly. Spawned as detached process by `_ensure_watchdog_process()`; survives parent exit.
**Reads:** indirect (via `_watchdog_loop`).
**Writes:** indirect (via `stop`).
**Called by:** subprocess invocation only — no Python imports.
**Calls out:** server_manager (intra-package).

---

### splade_server.py (67 LOC)

**Purpose:** Standalone FastAPI server that loads the SPLADE model at startup and exposes `/v1/sparse-embeddings` and `/health` on port 8083.
**Reads:** HuggingFace model (`naver/splade-v3`, `MAX_ACTIVE_DIMS = 256`) from disk/HF cache at startup.
**Writes:** nothing.
**Called by:** (none — subprocess target launched by `server_manager.py`, never imported by Python code)
**Calls out:** fastapi, uvicorn, torch, transformers

---

### lock.py (162 LOC)

**Purpose:** Global RAG mutex via `fcntl.flock` + JSON lockfile; provides `acquire` context manager, `read`, `update_progress`, and `heartbeat` functions used by cli.py.
**Reads:** `~/.rag-locks/rag.flock` (fd hold); `~/.rag-locks/rag.lock` (JSON details).
**Writes:** `~/.rag-locks/rag.flock`; `~/.rag-locks/rag.lock` (atomic tmp+rename with pid, command, kind, started_at, heartbeat, progress). `kind="index"` for commands in `_INDEXING_COMMANDS = {"index", "update_docs"}`; `kind="query"` for all others. Consumers (e.g. Monitor_CC menubar) gate on `kind` to distinguish indexing runs from search/delete runs.
**Called by:** cli.py, index_cmd.py (`heartbeat`, `update_progress`), status.py (read-only via `read`)
**Calls out:** (none — stdlib only: fcntl, json, os, pathlib)

---

### status.py (151 LOC)

**Purpose:** Gather lock state, GPU server health, and Postgres reachability into a single dict for `rag-cli status`; formats the output for terminal display.
**Reads:** `lock.read()` for lock state; `server_manager.box_status()` for server state; `~/.rag-locks/server-port-{port}.json` mtime directly for idle display (state-file mtime, /health-immune); Postgres connect probe (2s timeout).
**Writes:** nothing.
**Called by:** cli.py (`status` subcommand)
**Calls out:** (none — all via lock, server_manager, db intra-package)

---

### error_log.py (60 LOC)

**Purpose:** Append structured error entries to `src/rag/logs/errors.jsonl`; O_APPEND write is POSIX-atomic for writes under PIPE_BUF, no locking needed. Defines `ERROR_CODES` (frozenset of 4 genuine anomaly codes) to separate lifecycle noise from real failures. `read_errors_today()` is the canonical anomaly filter query for display consumers (Monitor_CC, future callers).
**Reads:** `src/rag/logs/errors.jsonl` (via `read_all`, `read_today`, `read_errors_today`).
**Writes:** `src/rag/logs/errors.jsonl` (one JSON line per error event).
**Called by:** server_utils.py, server_lifecycle.py, watchdog.py, server_cli.py
**Calls out:** (none — stdlib only: json, pathlib)

---

### server_lock.py (76 LOC)

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
| PostgreSQL `indexed_files` table | Per-project (collection, document) → sha256 + last_indexed_at; sync.py's change-detection ledger | sync.py (diff against current file hashes) | sync.py (upsert/delete; auto-creates table on first run); indexer.py (delete via `delete_manifest_rows()` — keeps manifest honest after CLI delete) |
| `~/.rag-locks/server-port-{N}.json` | Per-process GPU server state (pid, port, model_path, model_name, mode, log_path, start_time, name); idle computed from state-file mtime (bumped by `_touch_state_file` on each inference request) | server_lifecycle.py (`find_server_url`, `start` single-instance check), watchdog.py (`_watchdog_tick`, `_purge_orphans`), status.py, server_cli.py | server_utils.py (`_write_state_file` — written after Popen; `_unlink_state_file` / `_stop_by_state` — unlinked on stop) |
| `~/.rag-locks/watchdog.pid` | Detached watchdog process PID for ensure-singleton spawn | watchdog.py (`_ensure_watchdog_process`) | watchdog.py (`_ensure_watchdog_process`) |
| `~/.rag-locks/rag.flock` + `rag.lock` | Global RAG mutex (flock fd) + JSON details (pid, command, kind, started_at, heartbeat, progress) | lock.py, status.py | lock.py (`acquire`, `heartbeat`, `update_progress`) |

## Gotchas

- **splade_server.py has no Python import callers** — appears as dead code in any import grep but is the subprocess target launched by `server_manager.py`. Do not delete.
- **server_lock.py has no Python import callers** — verify dead code status before removing; may be planned for future concurrent-request serialization.
- **retriever.py re-exports format_results / format_collections / format_documents** from `formatting.py`. `cli.py` imports these from `src.rag.retriever`, not `src.rag.formatting`. Keep the import in retriever.py's INFRASTRUCTURE or cli.py breaks.
- **DEFAULT_QUERY_PREFIX** lives in `search_primitives.py`, not retriever.py — it moved with `embed_query()` during the retriever split refactor.
- **error_log.py** is called by server_utils.py, server_lifecycle.py, watchdog.py, and server_cli.py (previously only server_manager.py — update any grepping for callers accordingly).
