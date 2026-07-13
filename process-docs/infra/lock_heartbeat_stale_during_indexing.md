# Lock heartbeat goes stale during long indexing — process is alive, just not updating heartbeat

**Scope:** Session 2026-05-23. Triggered during RAG-CLI collection-migration (Monitor_CC/RAG/searxng `-meta` + `-features` → `-docs`).
**Symptom resolved by:** `lock.py` auto-heartbeat thread (commit pending).
**Companion theme:** `connection_hang_cascade.md` (different issue — polling-deadlock from `rag-cli progress` — but same architectural surface).

---

## Problem (symptom)

`rag-cli update_docs <project>` for a project with ~80-100 documents / 500+ chunks runs for several minutes. During the run, `rag-cli status` reports:

```
Lock: HELD by PID <pid> (update_docs) since 3m02s ago [heartbeat: 3m02s ⚠ heartbeat stale]
```

Heartbeat-age == lock-age for the entire duration of the run. The "⚠ heartbeat stale" warning makes it look like the process is hung. Three sessions in a row (2026-05-23) we treated the warning as truth, killed the PID, and retried — wasting cycles on a non-bug.

**Critical observation:** PID was alive (`ps -p <pid>` showed the python process) with very low CPU time (~1.7s over 3-7 minutes). Looked exactly like a stuck process. But after `kill -9`, the next `rag-cli list_collections` revealed that the "stuck" run had actually been indexing the whole time — chunks were committed incrementally; the killed process had populated most of the target collection before death.

So: stuck-looking, actually working.

## Investigation

### Code Analysis

`src/rag/lock.py` defines:
- `class acquire` (context manager) — writes lock-file once in `__init__` with `"heartbeat": now()`, then never updates it.
- `def heartbeat()` — standalone function that updates the heartbeat timestamp. Available, just nobody calls it.
- `def update_progress(done, total, current_document)` — updates both progress AND heartbeat. Available, just nobody calls it.

`src/rag/sync.py` (the `update_docs` workflow) — searched for `heartbeat` and `update_progress` calls: **zero**. The indexing loop runs through `_index_one_file()` for every input file, but never touches the lock-state once acquired.

### Architectural mismatch

The original lock design (commit chain from `decisions/OldThemes/connection_hang_cascade.md` Phase 2) assumes callers periodically call `update_progress()` so the heartbeat doubles as a freshness signal. That's a fine design — but it requires every long-running workflow to remember the call. `sync.py` doesn't, and neither do other workflows (verified via grep: no caller of `update_progress` or `heartbeat` exists in src/rag/).

The result: every long-running operation under the lock has the same false-stale-heartbeat behavior. This is a class-of-bug, not a single missed call.

### Hypotheses ruled out

| Hypothesis | Why ruled out |
|---|---|
| embedding-server (`embedding-8b`) hung | `rag-cli server status` reports healthy; restart didn't change behavior on first attempt; later runs without restart also indexed successfully |
| postgres connection-pool exhausted | postgres reachable throughout (`rag-cli status` shows `REACHABLE`); past connection-hang-cascade fix should already prevent this |
| splade-server hung | splade reports healthy and is not on the critical path for update_docs |
| update_docs in transaction-deadlock with old `<Project>-meta`/`-features` `indexed_files` entries | tested: deleted old collections first, retry hung exactly the same way → not the cause |

## Root Cause

`lock.acquire` stamps heartbeat at acquisition time and never updates it. No caller in `src/rag/` calls `lock.heartbeat()` or `lock.update_progress()` during long-running operations. The "stale heartbeat" warning fires after ~60s and stays as the lock-age grows — independent of actual process activity.

## Fix

**Auto-heartbeat daemon thread in `lock.py:acquire.__init__`.**

```python
# new constant
_HEARTBEAT_INTERVAL = 30   # seconds

# in __init__, after _write_atomic(data):
self._stop_heartbeat = threading.Event()
self._heartbeat_thread = threading.Thread(
    target=self._heartbeat_loop, daemon=True
)
self._heartbeat_thread.start()

def _heartbeat_loop(self) -> None:
    while not self._stop_heartbeat.wait(_HEARTBEAT_INTERVAL):
        heartbeat()

# in __exit__, before existing cleanup:
self._stop_heartbeat.set()
```

Daemon thread → dies with the process if `__exit__` is skipped (no zombie threads). `_stop_heartbeat.wait(N)` returns True if set (clean stop) or False after N seconds (then call `heartbeat()`). No race with explicit `update_progress` calls (both write atomically).

Plus side-cleanup: replaced existing `except Exception: pass` in `__exit__` with `except OSError as e: logger.warning(...)` per project code-standard (no silent exception swallow).

## Why this approach over alternatives

| Alternative | Rejected because |
|---|---|
| Add `lock.heartbeat()` calls inside `sync.py` indexing loop | Caller-side fix: every new long-running workflow has to remember. Same class-of-bug will recur. |
| Spawn separate watchdog process to ping heartbeat | Heavier (extra process, IPC); auto-thread inside `acquire` is fully contained in the lock module. |
| Lower the stale-threshold in `status.py` so 30s+ no longer warns | Would lose the actual stale-detection use-case (process really hung). Threshold is fine — it's the heartbeat-update side that was missing. |
| Change `sync.py` to call `update_progress(done, total, current_doc)` per chunk | Better as future-enhancement (gives accurate progress display) but orthogonal to the bug. The auto-heartbeat fixes the false-stale issue regardless of whether `update_progress` is ever wired in. |

## Verification (pending)

Will be confirmed on the next `update_docs` run AFTER the lock.py change is loaded into a fresh process. Current runs use the old code already in-memory. Expected behavior: `rag-cli status` shows `[heartbeat: <some seconds <30>]` that resets every ~30s, never crossing 60s while the lock is held by an actively-working process.

## Files Touched

- `src/rag/lock.py` (+15 lines: `threading` + `logging` imports, `_HEARTBEAT_INTERVAL` constant, `_stop_heartbeat` Event + thread, `_heartbeat_loop` method, `__exit__` adjustment, logging replacement for silent except)

## Related

- `decisions/OldThemes/connection_hang_cascade.md` — original lock + heartbeat introduction (Phase 2). The fix here completes that design: heartbeat is now both a freshness signal AND auto-maintained, not relying on caller discipline.
