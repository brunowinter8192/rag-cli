# `rag-cli server stop` Self-Kill via Port-Based PID Lookup

**Date:** 2026-05-25
**Commits:** c6f9269 (lsof LISTEN), d1a12c9 (stop() state-file-only)
**Scope:** `src/rag/server_lifecycle.py::stop()`, `src/rag/server_utils.py::find_all_pids_on_port`

## Symptom

Worker `eval-sweep` (Sonnet) died twice in a row after emitting a Bash tool_use for `rag-cli server stop`. Both deaths exactly **~10 seconds after the tool_use**, status 143 (SIGTERM), no `tool_result` in the JSONL.

Death 1: 2026-05-25 18:56:43
Death 2: 2026-05-25 19:31:14

Pattern reproducible. Ruled out as causes: OOM watchdog (threshold 26 GB never exceeded, last kill May 4), Monitor_CC menubar bg_timer abort (only kills sleep-PIDs, not workers), PreToolUse hooks (no signal-sending in any hook source), proxy_addon.py (no Bash/tool_use-specific reaction logic).

## Root Cause

`stop(name)` in `src/rag/server_lifecycle.py:118-126`:

```python
url = find_server_url(name)
port = int(url.split(":")[-1]) if url else cfg["default_port"]  # ← (1) fallback to hardcoded default_port
pids = find_all_pids_on_port(port)                              # ← (2) lsof returns all port touchers
for pid in pids:
    os.kill(pid, signal.SIGTERM)
```

Two components combined to cause the self-kill:

**(1) Default-port fallback for non-running servers.** `stop_all()` iterates all server presets (including non-running ones). For non-running servers `stop()` falls back to `cfg["default_port"]`. Example: reranker-0.6b not running → port = 8082.

**(2) `find_all_pids_on_port` via `lsof -ti :PORT` matched ALL processes touching the port** — both listeners and outbound TCP connectors. Without the `-sTCP:LISTEN` flag.

**Collision:** the worker-specific mitmproxy lived on port 8082 (because port 8081 was occupied by the trading-session mitmproxy at that time; `_worker_proxy_setup` picks `main_port + 1` and walks until a free port is found). 8082 = reranker-0.6b default_port = collision.

Worker's claude.exe had HTTPS_PROXY=http://localhost:8082 set — established an outbound connection on 8082. `lsof -ti :8082` returned both PIDs: mitmproxy (listener) AND claude.exe (connector).

`os.kill(claude.exe_PID, SIGTERM)` → worker kills itself.

## Smoking Gun

`~/.rag-locks/logs/server_manager.log`:

```
2026-05-25 19:31:05,389 - INFO - Stopping embedding-8b (PIDs [41662]) on port 8081...
2026-05-25 19:31:06,055 - INFO - Stopping reranker-0.6b (PIDs [2013, 2022]) on port 8082...
```

- PID 41662 = **trading-session's mitmproxy** (collateral damage from embedding-8b default_port 8081 collision)
- PID 2013 = worker mitmproxy (listener on 8082)
- **PID 2022 = worker claude.exe (HTTPS_PROXY connection on 8082)** ← self-kill

Confirmed by logger death-snapshot in `dev/server_management/md/` (via iterative-dev plugin's worker_logger.sh).

## Fix — two commits

### Commit c6f9269 — `find_all_pids_on_port` LISTEN-only

`src/rag/server_utils.py:154`:
```python
["lsof", "-ti", f":{port}", "-sTCP:LISTEN"]
```

Defensive. Also protects other callers (`status()`, `start_arbitrary()`, `_wait_for_health()`) from future connector collisions.

### Commit d1a12c9 — `stop()` state-file-only

`src/rag/server_lifecycle.py::stop()` completely rewritten. Iterates `~/.rag-locks/server-port-*.json`, matches on the `name` field, calls the existing `_stop_by_state(state, sf, ...)` (encapsulates SIGTERM→SIGKILL escalation + state-file cleanup). If no state file exists for the name: `return False` with a "not running" log.

**Completely eliminated:**
- `find_server_url(name)` → port lookup
- `cfg["default_port"]` fallback
- `find_all_pids_on_port(port)` call

Removed imports: `os`, `signal`, `find_all_pids_on_port`, `_allocate_port` (no longer needed).

Net change: −34/+15 lines.

## Architecture Decision — `default_port` stays for `start()`

Option B from the worker-phase-A discussion chosen: `default_port` field stays in the `SERVERS` dict for `start()` as "preferred start port" (start tries default first, falls back to a free port if busy). ONLY `stop()` was freed from the default_port fallback.

**Rationale:** consistent default ports make logs/status display easier ("embedding-8b on 8081" as a known mapping). Dynamic allocation from start would make every restart sequence unpredictable without bug-fix value (the bug only sat in the stop path).

## Open Follow-Up Work

- `status()` has the same default_port fallback logic but only for display (no kill). Less dangerous, but should be aligned for consistency later. Not part of this fix.
- The server-architecture state must be updated for the new `stop()` semantics (state-file-only, no port fallback). Follow-up recap task for the eval-sweep worker once it has completed the phase-1+2 sweep.

## Sources

- `~/.rag-locks/logs/server_manager.log` — the "Stopping reranker-0.6b (PIDs [2013, 2022])" line
- Logger snapshot `worker_logger.sh` (via iterative-dev plugin): `eval-sweep_20260525_192702_revive_DEATH.txt` with process tree, vm_stat, JSONL tail
- Cross-project: `decisions/OldThemes/worker_revive_proxy_and_logger.md (iterative-dev)` — diagnostic logger that produced the death captures
- Bead pointer: RAG-8r8 (server constellation profiling + eval sweep)
