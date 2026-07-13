# Infrastructure 1: PostgreSQL Connection Management

## State (as of 2026-05-08)

As of 2026-05-08: `get_connection(purpose, autocommit)` in `src/rag/db.py` is the sole Postgres connection factory.

**Code:** `src/rag/db.py:get_connection(purpose, autocommit)`
**Sole connection factory** — `indexer.py`, `cli.py`, `retriever.py`, `sync.py` all import from here. No duplicates.

**Signature:**
```python
def get_connection(purpose: str = "read", autocommit: bool = False)
```

**Three timeout profiles:**

| `purpose` | `connect_timeout` | `statement_timeout` | `lock_timeout` |
|-----------|-------------------|---------------------|----------------|
| `"read"`  | 5s | 10s | 5s |
| `"write"` | 5s | 120s | 10s |
| `"ddl"`   | 5s | 300s | 30s |

Implemented via psycopg2 `options="-c statement_timeout=NN -c lock_timeout=NN"`. `connect_timeout` is a connect-kwarg.

**Autocommit:** opt-in. `autocommit=True` is set BEFORE `register_vector(conn)` because `register_vector` itself runs a query that would otherwise open an implicit transaction.

**Used by:**
- `retriever.py` workflows (`search_workflow`, `list_collections_workflow`, etc.) → `purpose="read"`
- `indexer.py` `index_json_workflow` → `purpose="ddl"` for `ensure_schema`, then `purpose="write"` for batch inserts; both close before next call
- `cli.py` `index` outer connection → `purpose="ddl", autocommit=True` (held across loop, autocommit prevents lock-hold)
- `sync.py` `sync_docs_workflow` → `purpose="ddl"` for schema + ensure_indexed_files_table

**SIGTERM/SIGINT:** `cli.py:main()` registers handlers that `sys.exit(128 + sig)`. With `statement_timeout` active, blocking queries unblock as exceptions, allowing clean shutdown. No connection-close-on-signal needed because Python GC closes connections on exit anyway.

## Evidence

### Pre-fix bug

Without timeouts, concurrent reads against an indexer holding `AccessShareLock` on `documents` waited indefinitely. `rag-cli list_collections` hung 1+ minute, accumulated dead Python processes holding postgres connections.

### Why three timeout profiles

- **Read (10s):** `SELECT COUNT(*) GROUP BY document` on a 6632-row table runs in 0.04s under no-contention. 10s gives 250× headroom for unexpected slow paths (cold cache, autovacuum interleaving). Beyond 10s indicates real lock contention worth surfacing.
- **Write (120s):** Batch inserts of 32 chunks (default `BATCH_SIZE`) with vector + sparsevec serialization take 1-3s. 120s gives 60× headroom for large embedding payloads or transient I/O slowdowns.
- **DDL (300s):** `ensure_schema` runs `CREATE TABLE IF NOT EXISTS`, `CREATE INDEX IF NOT EXISTS` (GIN on tsv), `ALTER TABLE ADD COLUMN IF NOT EXISTS`. On an existing table these are <100ms no-ops. On a fresh table the GIN index build can take seconds-to-minutes proportional to row count. 300s covers 100k-row indexes.

### Why autocommit is explicit (opt-in)

Default psycopg2 `autocommit=False` is correct for transactional write patterns. The `index_json_workflow` write path benefits from transaction grouping (insert batch + commit). Only the `cli.py index` outer connection needs autocommit because it's read+write across a long loop. Making autocommit the default would break the batch-insert atomicity semantics in `index_json_workflow`.

### Race scenarios that would still fail (acceptable)

- DDL `lock_timeout=30s` with a long-running concurrent read transaction holding `AccessShareLock` for >30s: ALTER TABLE fails. Diagnosis: read transaction shouldn't be that long; check for unclosed connections in client code.
- Network partition between client and Postgres lasting >5s: `connect_timeout` fires. Same recovery as any DB outage.
- Embedder/SPLADE HTTP timeout (separate from DB) leaves connection in transaction state: psycopg2's `with conn:` block handles via rollback on exception. Verified clean shutdown via test of forced HTTP-timeout in embed workflow.

## Recommendation

**Keep:** Current implementation. Three-purpose timeout profile model is the right abstraction — covers read/write/ddl latency expectations distinctly without requiring per-call timeout tuning.

**Keep:** SOLE `get_connection()` in `db.py`. Any new code that needs Postgres MUST `from .db import get_connection` — never re-implement. Periodic `grep -rn 'def get_connection'` to catch reintroduced duplicates.

**Keep:** Autocommit as explicit opt-in. Document in API comment which call sites need it.

**Keep:** `register_vector()` after autocommit assignment. The ordering matters; comment in code explains why.

## Open Questions

- Connection pooling — currently each call opens a fresh connection. For high-frequency search workloads (many `search_hybrid` calls in burst), pooling would cut connect-overhead. psycopg2's `psycopg2.pool.SimpleConnectionPool` works but adds lifecycle complexity. Defer until measured to be a bottleneck.
- DDL lock_timeout=30s vs 60s — Phase 1 used 30s and Phase 4 revealed it was too short under the autocommit bug. With autocommit fixed, 30s should be enough. If future concurrent workloads (e.g., parallel sync runs from different projects) introduce DDL contention, raise to 60s.

## Sources

- PostgreSQL `statement_timeout`, `lock_timeout`, `connect_timeout` semantics — [postgresql.org/docs/current/runtime-config-client.html](https://www.postgresql.org/docs/current/runtime-config-client.html)
- pgvector `register_vector()` — registers `vector` and `sparsevec` types per-connection, requires query execution
- psycopg2 connection lifecycle and autocommit — [psycopg.org/docs/connection.html](https://www.psycopg.org/docs/connection.html#connection.autocommit)
