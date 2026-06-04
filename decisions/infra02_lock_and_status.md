# Infrastructure 2: Single-Instance Lock + Status Visibility

## Status Quo (IST)

**Code:**
- `src/rag/lock.py` — global mutex + lockfile
- `src/rag/status.py` — observability
- `cli.py` — lock-acquire wrapper in `main()` around all subcommands except `status` and `server`

**Lock files (in `~/.rag-locks/`):**

| File | Purpose |
|------|---------|
| `rag.flock` | Held-open file descriptor for `fcntl.flock(LOCK_EX | LOCK_NB)`. Mutex. |
| `rag.lock` | JSON details — `{pid, command, args, started_at, status, progress, heartbeat}` |

GPU server state (ports, PIDs, idle tracking) → see `box_architecture.md` IST and `server_manager.py`.

**Acquire pattern (from `cli.py:main`):**

```python
try:
    _lock_ctx = lock.acquire(args.cmd, _lock_args)   # raises LockBusyError if held
    _lock_ctx.__enter__()
except LockBusyError as e:
    print(f"Error: {e}", file=sys.stderr)
    sys.exit(1)
try:
    _dispatch(args)
finally:
    _lock_ctx.__exit__(None, None, None)
```

`lock.acquire()` raises at construction (not at `__enter__`) — fail-fast semantics: error appears immediately if the lock is held, before the caller wraps anything in `with`.

**`status` subcommand bypasses the lock-acquire wrapper.** Always works regardless of lock state. Reads lockfile, probes GPU server `/health` endpoints, tries Postgres connect with 2s timeout. No DB query against `documents` (would acquire AccessShareLock).

**Heartbeat:** indexer writes `data["heartbeat"] = now` every 30s via background daemon thread. `status.py` reports `⚠ heartbeat stale` if heartbeat age >60s — caller can infer stuck indexer.

**Stale-lock cleanup:** `lock.cleanup_stale()` runs at start of every `acquire()`. Reads lockfile JSON, checks `os.kill(pid, 0)` — if PID is dead (`ProcessLookupError`), unlinks lockfile and proceeds. Recovery from SIGKILL'd indexer is automatic; next caller takes over.

**Progress writes:** `lock.update_progress(done, total, current_document)` updates the lockfile JSON via atomic tmp+rename. Called after each completed document in `cli.py index` (collection-wide path).

## Evidenz

### Why single-instance globally (not per-collection or per-operation-class)

GPU servers (llama-server, SPLADE, reranker) and Postgres are intrinsically single-instance per machine — they bind to fixed resources (GPU memory, ports). Concurrent operations would compete for those resources anyway. A single global lock makes the resource contention explicit and the system predictable: "is something running? yes/no" is a single boolean.

Read operations could theoretically run concurrently with each other (Postgres MVCC handles this), but the user explicitly chose uniform single-instance for predictability. Trade-off: search calls during indexing fail fast with `rag busy` instead of queueing. Acceptable for personal-use; operator retries when free.

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

**Keep:** Single-instance global lock. Predictable behavior > theoretical concurrent-read parallelism for personal-use.

**Keep:** Lockfile JSON with heartbeat. File-based observability is debuggable with `cat`, recoverable from any state, no dependencies.

**Keep:** `status` lock-free. Always-available visibility is non-negotiable; operator must be able to debug a stuck system.

**Keep:** Heartbeat 30s write / 60s stale-threshold. Tunable via constants if needed.

**Keep:** `acquire()` raises at construction. Forces caller to handle the busy case explicitly before entering the `with` block.

## Offene Fragen

- **Cross-machine locks** — irrelevant on personal-use single machine. If RAG ever runs distributed (multi-host indexing), the lockfile approach wouldn't work. Would need DB-backed advisory lock (`pg_advisory_lock`) or external service (Redis SETNX). Defer until distributed actually happens.
- **Sub-second progress updates** — current heartbeat is 30s, progress per-document. For large documents (>1000 chunks), per-chunk progress would be more responsive. Cost: lockfile write per chunk (~30 writes/sec at peak indexer rate). atomic tmp+rename can sustain this but adds noise to filesystem syslog. Defer until operators report wanting it.
- **`status` showing GPU server STARTED-AT** — currently shows idle time (derived from log file mtime). Adding started_at would let operators see "this server has been running 4 hours, healthy". Trivial addition if requested.

## Quellen

- POSIX `flock(2)` semantics, kernel-level atomicity — [man7.org/linux/man-pages/man2/flock.2.html](https://man7.org/linux/man-pages/man2/flock.2.html)
- Atomic file write via tmp+rename — POSIX rename(2) atomicity guarantee on the same filesystem
- `pg_advisory_lock` (deferred alternative for distributed case) — [postgresql.org/docs/current/explicit-locking.html](https://www.postgresql.org/docs/current/explicit-locking.html)
- See `OldThemes/connection_hang_cascade.md` § Phase 2 for the bug-class history.
