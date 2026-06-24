# Infrastructure 2: Single-Instance Lock + Status Visibility

## Status Quo (IST)

**Code:**
- `src/rag/lock.py` — global mutex + lockfile
- `src/rag/status.py` — observability
- `cli.py` — `main()` dispatch with a read/write split: read-only commands (`search_hybrid`, `list_collections`, `list_documents`, `progress`, `read_document`) run **lock-free** via `_run_dispatch()`; only write commands (`index`, `update_docs`, `delete`) take the exclusive lock. `status`/`server` bypass entirely.

**Lock files (in `~/.rag-locks/`):**

| File | Purpose |
|------|---------|
| `rag.flock` | Held-open file descriptor for `fcntl.flock(LOCK_EX | LOCK_NB)`. Mutex. |
| `rag.lock` | JSON details — `{pid, command, args, started_at, status, progress, heartbeat}` |

GPU server state (ports, PIDs, idle tracking) → see `box_architecture.md` IST and `server_manager.py`.

**Dispatch pattern (from `cli.py:main`):**

```python
_READ_ONLY_CMDS = frozenset({"search_hybrid", "list_collections",
                             "list_documents", "progress", "read_document"})
if args.cmd in _READ_ONLY_CMDS:
    _run_dispatch(args)          # NO lock — MVCC reads + -np 1 GPU serialize
    return
# write commands: index / update_docs / delete
try:
    _lock_ctx = lock.acquire(args.cmd, _lock_args)   # raises LockBusyError if held
    _lock_ctx.__enter__()
except LockBusyError as e:
    print(f"Error: {e}", file=sys.stderr); sys.exit(1)
try:
    _run_dispatch(args)
finally:
    _lock_ctx.__exit__(None, None, None)
```

`_run_dispatch()` wraps `_dispatch` with the httpx/RuntimeError GPU-server error handling — factored out so reads get error handling WITHOUT the lock. `lock.acquire()` raises at construction (fail-fast). On a write-command error `_run_dispatch` calls `sys.exit(1)` → the `SystemExit` propagates through the `finally` → the lock is always released.

**`status` subcommand bypasses the lock-acquire wrapper.** Always works regardless of lock state. Reads lockfile, probes GPU server `/health` endpoints, tries Postgres connect with 2s timeout. No DB query against `documents` (would acquire AccessShareLock).

**Heartbeat:** indexer writes `data["heartbeat"] = now` every 30s via background daemon thread. `status.py` reports `⚠ heartbeat stale` if heartbeat age >60s — caller can infer stuck indexer.

**Stale-lock cleanup:** `lock.cleanup_stale()` runs at start of every `acquire()`. Reads lockfile JSON, checks `os.kill(pid, 0)` — if PID is dead (`ProcessLookupError`), unlinks lockfile and proceeds. Recovery from SIGKILL'd indexer is automatic; next caller takes over.

**Progress writes:** `lock.update_progress(done, total, current_document, collection=None, chunks_done=None, chunks_total=None)` updates the lockfile JSON via atomic tmp+rename. `chunks_done`/`chunks_total` are optional — omitted when not supplied (backward-compat callers unchanged). The `progress` dict carries:

```json
{
  "done": 2,
  "total": 5,
  "current_document": "large_doc.md",
  "collection": "trading-reference",
  "chunks_done": 30,
  "chunks_total": 1772
}
```

`chunks_done`/`chunks_total` are absent when the call omits them (e.g. the per-document END marker written by `_index_collection` and `_sync_one_collection` after each file). During a document's embedding loop they are present.

**Two-level progress write pattern** (`index_cmd._index_collection`, `sync._sync_one_collection`):
1. Pre-embed: the file loop passes `doc_done=i, docs_total=len(to_index)` into `index_json_workflow` / `index_file`.
2. Inside those functions: immediately before the batch loop, writes `chunks_done=0, chunks_total=M`; after each batch: writes `chunks_done=min(i+BATCH_SIZE, M), chunks_total=M`.
3. After each file finishes: the outer loop writes `done=i+1, total=N` (no chunk fields) as the definitive doc-complete marker.

In multi-collection manifests the counter and label reset naturally per collection as `sync_docs_workflow` iterates.

**`rag-cli status` and `_raise_busy` label:** both now render `{done}/{total} docs [· {chunks_done}/{chunks_total} chunks]`, falling back to doc-level only when `chunks_total` is absent.

## Evidenz

### Why single-instance globally (not per-collection or per-operation-class)

GPU servers (llama-server, SPLADE, reranker) and Postgres are intrinsically single-instance per machine — they bind to fixed resources (GPU memory, ports). Concurrent operations would compete for those resources anyway. A single global lock makes the resource contention explicit and the system predictable: "is something running? yes/no" is a single boolean.

Read operations could theoretically run concurrently with each other (Postgres MVCC handles this), but the user initially chose uniform single-instance for predictability. Trade-off: search calls during indexing fail fast with `rag busy` instead of queueing. Acceptable for personal-use; operator retries when free.

**Reversal (2026-06-14) — reads made lock-free.** The uniform-single-instance choice broke down once TWO rag-heavy CC sessions ran in parallel (a trading session + a searxng session): every overlapping pair — even two read-only searches — collided, one dying with `rag busy`. Empirically reproduced: two concurrent `rag-cli search_hybrid` → one OK, one `rag busy` (sequential `;` chaining is fine; only time-overlap collides). Reads are MVCC-safe and the GPU servers serialize at `-np 1`, so concurrent reads (with each other AND with a running index — slight GPU-queue latency, no corruption) are safe. Reads now bypass the exclusive lock; only `index`/`update_docs`/`delete` keep it. Smoke-verified post-merge: two parallel `python cli.py search_hybrid` both exit 0, 12 results each, no `rag busy`.

### Why lockfile JSON instead of pure flock or external service

- `flock` alone gives mutex but no visibility: holder PID isn't stored, no progress, no command name. Blind locking.
- A daemon process (Redis, systemd-machined, custom server) gives full features but adds dependency and lifecycle.
- Lockfile JSON sits between: file is the source of truth, atomic write via tmp+rename, readable by any tool with `cat` or `jq`. Zero external services. Recoverable by hand.

### Why heartbeat in lockfile vs DB

Heartbeat must be writable WHILE the work is running. If it went through Postgres, it would compete for the same locks the indexer holds → potential deadlock. File-based heartbeat is independent of the DB's state. Atomic tmp+rename ensures readers never see a partially-written state.

### Race conditions

- **Two processes call `acquire()` simultaneously:** `flock(LOCK_EX | LOCK_NB)` is atomic at the kernel level. Exactly one succeeds; others get `BlockingIOError` and raise `LockBusyError`. No race.
- **Lockfile JSON is being read while indexer writes it:** atomic `tmp.rename(_DATA_FILE)` is atomic on POSIX. Reader either sees old or new, never partial. JSON parse failure (rare, only if rename was interrupted mid-flight) → `read()` returns `None`, treated as no-info.
- **Stale PID briefly reused by OS:** `os.kill(pid, 0)` returns `True` for a different process with the same PID number. Theoretical collision but PIDs are 32-bit and not reused for hours/days on a normal system. Accept the risk; alternative (PID + start_time matching) adds complexity for negligible gain.

### `rag-cli status` design rationale

`status.gather()` returns `{lock, servers, postgres}` dict. Three independent layers, each can fail independently. Output format prioritizes "what's running, what's free, what's broken":

```
Lock:    HELD by PID 12345 (index-dir) since 4m12s ago [heartbeat: 8s]
         Progress: 87/250 chunks — Paper3.md

Servers:
  embedding    :49445 RUNNING  healthy  last_used: 3m46s ago
  reranker     :49425 RUNNING  healthy  last_used: 3m46s ago
  splade       :49302 RUNNING  healthy  last_used: 3m46s ago

Postgres:  REACHABLE (:5433)
```

Server-side: HTTP /health probe with 2s `httpx` timeout per server. If response is HTTP 200, healthy. If port has TCP listener but /health fails, `unhealthy` (could be a non-RAG process on the port — happened with mitmdump on `:8081`). If no TCP listener, `STOPPED`.

Postgres-side: `psycopg2.connect(connect_timeout=2)` independent of `db.get_connection()` (avoids triggering its options-string handling for a probe).

## Recommendation (SOLL)

**Changed (2026-06-14):** the lock is no longer uniform single-instance. Read-only commands (`search_hybrid`/`list_collections`/`list_documents`/`progress`/`read_document`) run lock-free; only writes (`index`/`update_docs`/`delete`) take the exclusive lock. The prior "predictability > concurrent-read parallelism" trade-off was reversed because parallel rag-heavy sessions made overlapping reads fail with `rag busy`. Reads are MVCC-safe + GPU serializes at `-np 1` → no correctness cost. Evidence: smoke test (two parallel searches both succeed, 12 results each). Related same-session change: hybrid prod `top_k` restored 10 → 12 (`retriever.py search_hybrid_workflow`).

**Keep:** Lockfile JSON with heartbeat. File-based observability is debuggable with `cat`, recoverable from any state, no dependencies.

**Keep:** `status` lock-free. Always-available visibility is non-negotiable; operator must be able to debug a stuck system.

**Keep:** Heartbeat 30s write / 60s stale-threshold. Tunable via constants if needed.

**Keep:** `acquire()` raises at construction. Forces caller to handle the busy case explicitly before entering the `with` block.

## Offene Fragen

- **Cross-machine locks** — irrelevant on personal-use single machine. If RAG ever runs distributed (multi-host indexing), the lockfile approach wouldn't work. Would need DB-backed advisory lock (`pg_advisory_lock`) or external service (Redis SETNX). Defer until distributed actually happens.
- **Sub-second progress updates** — resolved: per-batch (BATCH_SIZE=32 chunks) writes now land in the lock during a document's embedding loop. Lock write rate ≈ 1 per batch (~1-3s apart at typical GPU throughput), not per-individual-chunk. Filesystem noise is negligible at this rate.
- **`status` showing GPU server STARTED-AT** — currently shows idle time (derived from log file mtime). Adding started_at would let operators see "this server has been running 4 hours, healthy". Trivial addition if requested.

## Quellen

- POSIX `flock(2)` semantics, kernel-level atomicity — [man7.org/linux/man-pages/man2/flock.2.html](https://man7.org/linux/man-pages/man2/flock.2.html)
- Atomic file write via tmp+rename — POSIX rename(2) atomicity guarantee on the same filesystem
- `pg_advisory_lock` (deferred alternative for distributed case) — [postgresql.org/docs/current/explicit-locking.html](https://www.postgresql.org/docs/current/explicit-locking.html)
- See `OldThemes/connection_hang_cascade.md` § Phase 2 for the bug-class history.
