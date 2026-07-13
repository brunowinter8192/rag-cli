# Connection-Hang Cascade — Multi-Layer Bug Class (FIXED 2026-05-08)

## Symptom

`rag-cli` calls hung indefinitely against an idle-looking system. Specifically observed during a `cleanup-crypto-papers` worker indexing 8 crypto papers:

- Worker `tmux idle` from outside, but functionally stuck — its own `rag-cli progress` polling never returned
- Concurrent `rag-cli read_document` from a separate terminal: hung 1+ minutes, then routed to CC's "Output too large" persistence bucket with empty content
- `rag-cli list_collections` (lightweight, DB-only): also hung
- 8 ESTABLISHED Postgres connections accumulating from dead-but-not-cleaned-up Python processes
- Embedder reported `RUNNING unhealthy` because Monitor_CC mitmdump had grabbed `:8081` while the actual llama-server wasn't running

The hang was not random. Once the indexer started its embedding phase, every subsequent `rag-cli` call queued behind it indefinitely. A single in-flight indexing run made the entire RAG layer unresponsive to any other operation.

## Reproduction

During an active `workflow.py index-dir` run (after the embedding phase begins, when `index_json_workflow()` is iterating over chunks):

```bash
# Terminal 1 (running)
./venv/bin/python workflow.py index-dir --input data/documents/<col>/ --collection <col>

# Terminal 2 (any time during run)
rag-cli list_collections    # → hangs forever
rag-cli read_document ...   # → hangs forever
rag-cli progress <col>      # → hangs forever (the cleanup-and-index polling pattern)
```

Reproducible 100% with collections >100 chunks and concurrent calls during the embedding loop.

## Root Cause — Five-Layer Cascade

Five independent bugs combined to produce the symptom. Each was masking the next.

### Layer 1: `db.py:get_connection()` had NO timeouts

```python
# Before
conn = psycopg2.connect(host=..., port=..., user=..., password=..., dbname=...)
```

No `connect_timeout`, no `statement_timeout`, no `lock_timeout`. psycopg2 defaults all to unlimited. Any query waiting on a Postgres lock would wait forever.

### Layer 2: Three separate `get_connection()` implementations

```
src/rag/db.py:20         → used by retriever.py, sync.py
src/rag/indexer.py:169   → used by indexer.py internals
workflow.py:12           → imports get_connection from indexer.py (NOT db.py)
```

Three separate definitions, all with the same missing-timeout bug. Patching one had no effect on the others.

### Layer 3: `workflow.py` outer connection held read-locks across the entire indexing loop

```python
conn = get_connection(purpose="ddl")      # implicit transaction starts
db_hashes = get_db_hashes(conn, collection)  # SELECT → AccessShareLock on documents
                                             # transaction stays open
for md_file, document, current in to_index:
    ...
    n = index_json_workflow(str(json_path))  # opens NEW connection, calls ensure_schema
    upsert_hash(conn, ...)                    # outer conn still holds the read lock
```

Default psycopg2 mode is `autocommit=False`. The `SELECT` opened an implicit transaction, the transaction held `AccessShareLock` on `documents`, and the loop kept the connection alive through every iteration. Inside the loop, `index_json_workflow()` opened its own connection and called `ensure_schema()` → `ALTER TABLE documents ADD COLUMN IF NOT EXISTS sparse_embedding sparsevec(30522)`. That ALTER needs `AccessExclusiveLock`, which conflicts with the outer connection's `AccessShareLock`. With Layer 1 unlimited timeouts, the inner ALTER waited forever.

### Layer 4: `cleanup-and-index` Skill polled `rag-cli progress` during indexing runs

The skill orchestrating the indexing run had a polling loop that called `rag-cli progress <collection>` every few seconds to surface progress to the user. Each `progress` call ran `SELECT COUNT(*) ... FROM documents GROUP BY document` — which queued behind whatever the indexer was holding at that moment. Without `statement_timeout`, those `progress` calls hung. Each polling iteration left another zombie Python process holding another Postgres connection. Over minutes, the Postgres connection pool filled with dead-but-still-listed processes.

This was the visible symptom that triggered the investigation: the worker's own progress watcher killed itself with stale calls.

### Layer 5: GPU servers hardcoded on `:8081`/`:8082`/`:8083`

`server_manager.py` had `EMBEDDING_PORT = 8081`, `RERANKER_PORT = 8082`, `SPLADE_PORT = 8083` as constants. Module-level URLs in `embedder.py`/`sparse_embedder.py`/`reranker.py` likewise hardcoded `localhost:8081/v1/embeddings` etc. Monitor_CC's worker proxy (mitmdump on a Trading worker `pydoll-stealth-probe`) had grabbed `:8081` for itself. When `start.sh` later tried to start `llama-server`, the bind failed silently (or the previous `llama-server` had died and mitmdump took its socket). `rag-cli status` reported `RUNNING unhealthy` because something was on the port responding to TCP but returning HTTP 502 to /health probes (mitmdump speaks neither llama-server's nor the health endpoint's protocol).

This was orthogonal to the lock-cascade but blocked us from re-running indexing after the hang was resolved.

## Hypotheses Ruled Out

| Hypothesis | Test | Result |
|---|---|---|
| Watch project's OOM watchdog SIGKILLed processes mid-call | `ps` showed PIDs of hung rag-cli processes were ALIVE, not zombies. zsh wrappers still in tool-state | Ruled out — processes were waiting on syscall, not killed |
| Some Postgres-side lock from autovacuum | `pg_stat_activity` snapshot during hang showed only the diagnostic query, no active autovacuum | Partial — autovacuum DOES briefly take ACCESS SHARE, but that's not why the hang persists for minutes |
| `rag-cli progress` query is too expensive on large tables | Direct `SELECT COUNT(*) GROUP BY document` via psql ran in 0.04s on 6632 chunks | Ruled out — query is fast, the hang is lock-contention |
| ALTER TABLE itself is slow on large table | Direct `ALTER TABLE documents ADD COLUMN IF NOT EXISTS sparse_embedding ...` via psql ran in 0.04s | Ruled out — the DDL is a fast no-op since the column already exists; the hang is lock-acquisition wait |
| Connection pool exhaustion in psycopg2 | psycopg2 doesn't pool by default; each call opens a fresh connection | Ruled out as primary cause, but accumulation of dead-but-leaked connections did contribute to noise |

## Fix — Four Phases

The fix landed in four merged phases over a single session. Each phase exposed the next layer underneath.

### Phase 1 — Timeouts + Consolidation (commits `67c4a6b` … `c8df567`)

`db.py:get_connection(purpose="read"|"write"|"ddl")` with three timeout profiles:

| `purpose` | `connect_timeout` | `statement_timeout` | `lock_timeout` |
|-----------|-------------------|---------------------|----------------|
| `"read"`  | 5s | 10s | 5s |
| `"write"` | 5s | 120s | 10s |
| `"ddl"`   | 5s | 300s | 30s |

Eliminated duplicate `get_connection()` in `indexer.py` and `workflow.py`. Both now `from .db import get_connection`. SIGTERM/SIGINT handlers added in `cli.py` for clean shutdown.

### Phase 2 — Single-Instance Lock + Status (commits `33e5338` … `c8df567`)

New `src/rag/lock.py` — global mutex via `fcntl.flock(LOCK_EX | LOCK_NB)` on `~/.rag-locks/rag.flock`. JSON details in `~/.rag-locks/rag.lock` with `{pid, command, started_at, heartbeat, progress}`. Indexer writes heartbeat every 30s and per-document progress.

New `src/rag/status.py` and `rag-cli status` subcommand — lock-free, reads lockfile + probes GPU servers via HTTP /health + tries Postgres-connect with 2s timeout. Always works, even when lock is held by another operation.

`cleanup-and-index` skill (in `MCP/searxng/skills/cleanup-and-index/SKILL.md`) updated to read the lockfile directly instead of calling `rag-cli progress` — eliminates the polling-deadlock that triggered this whole investigation.

Idle-Watchdog: `scripts/idle_watchdog.py` + `scripts/install_watchdog.sh` (generates LaunchAgent plist with absolute paths). Idle GPU servers (>3600s last_used) get stopped automatically.

### Phase 3 — Dynamic Port Allocation (commits `6ce576f` … `7c938bb`)

`server_manager.py` discovers free ports at startup via `socket.bind(('', 0))` → `getsockname()[1]`, passes `--port` to subprocess. Port file at `~/.rag-locks/<server>.port` with `{port, pid, started_at}`. PID-based stale detection via `os.kill(pid, 0)`.

Clients (`embedder.py`, `sparse_embedder.py`, `reranker.py`) call `server_manager.get_port(name)` per request — no caching, since servers can restart with new ports. `status.py` likewise probes ports from port files, not from a hardcoded SERVERS dict.

3-attempt retry loop on subprocess startup to handle the small race window between `_get_free_port()` returning and the subprocess actually binding (acceptable for personal-use system, retry covers the edge case).

### Phase 4 — workflow.py Outer Connection Autocommit (commit `5bcb7bc`)

After Phase 1 fixed the silent hang, the indexer started failing with a loud `psycopg2.errors.LockNotAvailable: canceling statement due to lock timeout` after exactly 30 seconds. Root cause was Layer 3 of the original cascade — outer connection holding an open read transaction across the loop.

Fix: `db.py:get_connection()` gained an `autocommit: bool = False` parameter, set BEFORE `register_vector()` (which itself runs a query and would otherwise open an implicit transaction). `workflow.py` `index-dir` and `index-file` branches both call `get_connection(purpose="ddl", autocommit=True)`. Each query in the loop now auto-commits, releasing locks immediately, so the inner `ensure_schema()` `ALTER TABLE` doesn't block.

## Status After Fix

| Operation | Before | After |
|-----------|--------|-------|
| `rag-cli list_collections` | Infinite hang during concurrent indexing | 0.17s |
| `rag-cli status` | Did not exist | 0.31s, full visibility |
| `rag-cli read_document ...` | Infinite hang | <1s on small reads |
| Concurrent rag-cli call during indexer | Hang forever | Fail-fast in <1s with `Error: rag busy: index-dir running on Trading since Xm Ys ago, PID NNN, progress N/M` |
| Indexer on 16-doc Trading collection | Crashed mid-run (Layer 3) | 8/16 skipped, 8/16 indexed cleanly, 421 chunks added |
| Embedder on `:8081` with mitmdump conflict | Could not start | Picks dynamic port (e.g. `:49445`), starts successfully |

## Notes for Future Investigations

- **"Worker idle (tmux)" ≠ "task complete".** tmux idle just means no pane activity in last 10s. The worker can have its own background sleep / polling watcher running. Always read `worker-cli response <name>` before declaring completion.

- **Multi-layer root causes are common in lock-driven systems.** When Layer 1 was fixed (timeouts), the indexer started failing with timeout errors instead of hanging. That looked like a regression but was actually Layer 3 (autocommit) becoming visible. Pre-Phase-1, both bugs caused the same observable hang. Each fix exposed the next layer. Took 4 phases.

- **Symptom shift is the signal that you're peeling a cascade, not regressing.** Phase 1 turned hangs into timeout-errors. Phase 4 turned timeout-errors into clean completion. If a fix changes the FORM of the failure (silent-hang → loud-error → no-error), you're moving forward. If the failure form stays the same, you're not actually fixing anything.

- **Three duplicate implementations of `get_connection()` was a structural smell that masked the unit-fix illusion.** Patching one location appeared to work in isolation tests but did nothing for the indexer because the indexer used a different copy. Code-search for the pattern (`grep -rn 'def get_connection'`) before assuming a fix is total.

- **Hardcoded service ports are a recurring source of conflict on a multi-tenant developer machine.** Other tools (Monitor_CC mitmdump, dev servers, debug processes) compete for the same well-known ports. Dynamic allocation via `socket.bind(0)` + port-file persistence is cheap to implement and eliminates the entire conflict class.

- **Visibility tooling (`rag-cli status`) pays for itself the first time you need to debug a hang.** Without it, we spent significant time on `lsof`/`ps`/`docker exec psql` to reconstruct what was happening. The `status` command consolidates lock state, GPU server health, and Postgres reachability into a 0.3s call. Add it FIRST when designing a CLI that uses external resources, not last.

- **Polling against the very thing you're orchestrating is a deadlock factory.** The `cleanup-and-index` skill polled `rag-cli progress` to monitor an indexer it had just spawned. The poll calls had to acquire the same locks the indexer was using, so polling itself wedged. Fix: the indexer publishes progress to a sideband file (the lockfile JSON), watcher reads file, no DB call. General pattern: orchestration channels should be separate from work channels.

- **The bug had been triggered by — and only surfaced because of — using the system at all.** Phase 1+2 of the eventual fix were merged before the original symptom (cleanup-crypto-papers worker hanging) was even resolved. The fix process itself revealed the deeper layers (Phase 3 mitmdump conflict, Phase 4 autocommit). Don't trust "this looks fine" assessments of code that hasn't been exercised under load.
