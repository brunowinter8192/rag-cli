# Phase 5: fallbacks and tripwires in src/ (2026-09-24)

## Correction of an earlier claim
The Phase 3 process-docs entry (file `2026-09-24_phase3_test_structure.md`, section "Production finding, not fixed") states that `server_utils.context_size_for_preset("splade")` raises `TypeError`. That is wrong. `SERVERS["splade"]` has no `extra_flags` key at all, so `.get("extra_flags", [])` returns `[]`, the `"-c" not in flags` check fires and the function returns `None`. Re-run on 2026-09-24: `context_size_for_preset("splade")` is `None`, no exception. I had printed `SERVERS[k].get("extra_flags")` (no default) and mistook the missing key for a stored `None`. There is no bug and no issue to file. That default stays: uvicorn presets legitimately have no launch flags.

## Rule applied
Default or swallow for an OBSERVED condition = fallback, must be traceable. Never observed = removed so it fails loudly. Structural (a valid empty answer, an optional override whose default is the normal path) = kept. Evidence sources searched: process-docs, dev/**/md reports, git history (`d832562`, `74d4cd8`), the production `.env` key set (`RAG_PROJECT_ROOT`, `POSTGRES_*`, `EMBEDDING_MODEL`, `VECTOR_DIMENSION`).

## What was removed (never observed)
- Env defaults for the keys the production `.env` always sets: `POSTGRES_*`, `EMBEDDING_MODEL`, `VECTOR_DIMENSION` now `os.environ[...]`. Optional overrides not in `.env` (`RAG_PG_CONTAINER`, `LLAMA_SERVER_PATH`, model paths, idle timeout, `SPLADE_PORT`, `RAG_PROJECT_ROOT` derivation) keep their default: firing every time is the normal path.
- db `get_connection` unknown purpose fell back to the read profile; now `KeyError`.
- error_log `read_all` skipped corrupt lines; lock `read` swallowed `JSONDecodeError`; `cleanup_stale` swallowed `PermissionError`; lock `__exit__` swallowed unlink `OSError`.
- lock `_raise_busy` and status formatting: `.get(k, 0)`, `or {}`, `"?"` on progress and heartbeat fields. The lock file always carries them. Kept: `prog.get("chunks_total")` (optional key by design) and the `?` for `collection` (observed: `update_docs` lock args carry no collection).
- indexer `load_chunks_json` defaults (the only writer, `index_cmd._write_chunks_json`, always writes `collection`, `document`, `chunks`; per-chunk `document` is never written, so it is just the file-level document).
- reranker `data.get("results", data)`.
- retrieval_log: per-line JSON skip in `known_fingerprints`; the stderr fallbacks in `report_write_failure` and `report_resolve_failure` (a failing `error_log.write` now raises).
- server_cli: broad `except Exception` that printed and exited 0 (start, start arbitrary, stop --port, restart --port); missing-flag guards now `stderr` plus `sys.exit(2)`; JSON/OSError skips in tail and list; `"?"` for mode and model; `_parse_flag` no longer swallows `IndexError` (flag without value).
- server_lifecycle `_iter_state_files`, `find_server_state`, `_reclaim_or_clear_port_state`; server_manager `_get_running_presets`; `.get("default")`, `.get("exclusive_with", [])`, `_CLASS_MAP.get(cls, [name])`, `state.get("pid", -1)`.
- server_utils: `lsof` and `pgrep` blanket excepts (an `[]` would have meant "no listener"), invalid `-c` value, SIGKILL `ProcessLookupError`, `_unlink_state_file` JSON/OSError.
- status: `_state_file_idle`, `_elapsed` blanket except, negative-seconds clamps.
- watchdog: pid-file `ValueError`/`OSError`, JSON skips, SIGTERM/SIGKILL `ProcessLookupError` on orphans.
- `server_lock.py` deleted (no callers, its unlink swallow was part of the finding).

## What was kept, and why
- OBS: db.py OperationalError then OrbStack/container boot (git `d832562`, stderr traces); indexer all-`None` embedding skip (`null_embedding_qwen3_prefix`, warning log; narrowed to `all(...)`, the unobserved `embedding is None` was dropped); lock `cleanup_stale` `ProcessLookupError` (`infra02`; now logs `stale lock removed: pid N is not running`); `start_all` aggregation (now logs a warning per failed server); `_resolve_port` dynamic-port switch (logged); `_stop_by_state` "already dead at SIGTERM" (written to error_log as `not_required`).
- Kept by decision of Main: retrieval_log lines around `resolve_fingerprint`, `known_fingerprints` read failure and `write_jsonl_lines` (traced via `error_log`, deliberate 2026-09-18 design, covered by `dev/infra/test_retrieval_log.py`).
- STRUCT: predicates that return `False` (`_postgres_reachable`, `_docker_daemon_up`, `_check_health_port`, `_pid_alive`; `_check_health_port` now catches only `httpx.RequestError`); `FileNotFoundError` for "no lock" / "no errors file" / "no registry"; `_touch_state_file` for env-URL servers without a state file; `find_server_state` `_CLASS_MAP.get(name, [])` (called with preset and class names); `cli.py` abort handlers (exit 1 plus message).
- `status._postgres_status` narrowed to `psycopg2.OperationalError`: reporting an unreachable Postgres is the purpose of `status`.
- watchdog: the abort must be visible although the process runs with stdout/stderr on `/dev/null`. `watchdog_main.py` now wraps the loop in `logger.exception(...)` plus re-raise (`watchdog_main.log` under `src/rag/logs/`).

## Test infrastructure
- `dev/strand_runner.py` now sets `HOME` to a per-strand tmp dir (so `~/.rag-locks` is isolated) and sets explicit values for `POSTGRES_*`, `EMBEDDING_MODEL`, `VECTOR_DIMENSION` before any import. Without this, importing `db` or `embedder` in the tmp copy (no `.env`) raises `KeyError`.
- New tests, one strand each, asserting the log line appears when the observed condition occurs: `dev/lock_progress/test_stale_lock_cleanup.py` (dead pid), `dev/server_management/test_start_all_failure_logged.py` (real `start` fails because no llama-server binary exists in the tmp copy), `dev/indexing/test_null_embedding_skip.py` (all-`None` vector; the DB connection is an in-memory stand-in because no Postgres is available in a test).
- Existing tests unchanged and green.

## End-to-end run in the production setup (2026-09-24)
Wrapper `/tmp/rag-cli-p5` = production venv + production `.env` exported, running the worktree `cli.py`. (`~/.local/bin/rag-cli` targets the main checkout, so it cannot exercise worktree code.)
- `status`, `server status`, `server list`, `server errors`, `server presets`, `list_collections`: OK with all servers stopped.
- `search "how to authenticate api requests" gh-cli-docs`: started `embedding-8b` (5 s) and `reranker-0.6b` (2 s), returned results, wrote `search.jsonl`. Afterwards `status`, `server status`, `server list`, `server errors [--verbose --today]`, `server tail`, `expand_chunks`, `progress`, `list_documents` all OK. No strict access raised anywhere.
- `_watchdog_tick()` from the worktree code against a live `embedding-8b`: ran without exception. `server stop` stopped both servers; `status` shows all STOPPED again.
- Side effect: the search spawned the singleton watchdog (`python -m src.rag.watchdog_main`, cwd = main checkout, so it runs main-checkout code, not this branch); it was still running afterwards, normal for a healthy system.
- Shell note: the zsh in this environment does not word-split unquoted `$c` in a for-loop, so an early loop attempt showed the CLI help text for every subcommand. Direct invocations were correct.
