# Box Architecture (RAG GPU Server Management)

## State (as of 2026-05-25)

As of 2026-05-25: all RAG GPU processes (llama-server presets embedding/reranker, uvicorn-based splade, arbitrary llama-server starts) are managed via `rag-cli server` as the sole sanctioned interface. Each box-managed process has a state file at `~/.rag-locks/server-port-{N}.json` containing pid, port, model_path, model_name, mode, start_time, log_path, name. stdout/stderr is redirected to per-process log files at `~/.rag-locks/logs/llama-port-{N}.log` for llama-server; splade writes its own `~/.rag-locks/logs/splade_server.log` via Python `logging`. `LOG_DIR` in `server_utils.py` is fixed to `~/.rag-locks/logs/` (NOT `<project>/src/rag/logs/`) so logs survive worktree cleanup — a server spawned from a worker-worktree keeps its log path stable after worktree removal for tail/inspection regardless of where it was started. (Idle-stop keys off the state-file mtime, not the log — see the next paragraph.)

The watchdog (`_watchdog_loop` in `watchdog.py`) iterates state files, computes idle from **state-file mtime** (`~/.rag-locks/server-port-{N}.json`), sends SIGTERM after IDLE_TIMEOUT (default 3600s). Client modules (embedder, sparse_embedder, reranker) call `_touch_state_file(port)` **before** the `httpx.post` call — semantics: "request received by client, about to be sent". This ensures the state file mtime is bumped even if the server is under memory pressure and the HTTP call times out or is cancelled; watchdog sees the server as active during stress without requiring a successful response. Watchdog /health probes are immune (they never touch the state file). On every tick watchdog also runs `_purge_orphans` which kills any `pgrep -x llama-server` PID not in the state-file registry — out-of-box processes die within ~30s.

**Exclusivity framework** (`SERVERS` dict in `server_utils.py`, enforced in `server_manager.py`): each preset carries an `exclusive_with: list[str]` field. Same-class exclusivity is set provisionally: `embedding-8b ↔ embedding-0.6b` and `reranker-0.6b ↔ reranker-8b`. Generator-4b and splade have empty lists. `ensure_ready(name)` calls `_stop_exclusive(name)` before any `start()` — `_stop_exclusive` reads live state files (alive-PID check, not health check) so unhealthy-but-alive servers are stopped to free GPU memory. Cross-class `exclusive_with` entries (e.g., `reranker-8b.exclusive_with: ["embedding-8b"]`) are NOT set yet — values depend on constellation profiling results.

**Reranker `-np 1`:** both `reranker-0.6b` and `reranker-8b` now launch with `extra_flags` including `-np 1`, reducing llama-server parallel slots from default 4 to 1. Rationale: eval workload issues sequential 50-pair batches; 4 slots × 32k context was pure memory waste with no throughput benefit. With `-np 1`, reranker-8b model-weights footprint drops from ~15 GB (4 slots) to estimated ~9 GB, making co-existence with embedding-8b (~9 GB) plausible under the 36 GB Metal VRAM budget.

**Health-Check:** Single 2s-Probe without retry (`_check_health_port` in `server_utils.py`). `/health` is decoupled from the inference slot — a timeout means genuinely not healthy (loading/wedged/dead), not busy.

**Port allocation:** All preset servers get kernel-assigned dynamic ports via `_allocate_port()` (socket bind to 0). No `default_port` concept — presets carry no hardcoded port. `status()` and `check_health()` are state-file-only: no state file means not running (port=None, healthy=False). `_resolve_port(port)` remains for `start_arbitrary` where the user may pass an explicit `--port N` or None.

**API:** two orchestration entry points in `server_manager.py`:
- `ensure_ready(target)` — ensure one server/class/operation is running; starts if needed, stops exclusives first
- `ensure_constellation(server_names)` — ensure EXACTLY the given set of preset servers is running; stops all running presets not in the list, then calls `ensure_ready` for each missing one. Intended for eval-orchestrator mode-switches.

CLI surface: `rag-cli server {status|list|start|stop|restart} [name]` for presets, `rag-cli server start --model PATH --port N --mode {embedding|rerank} [--name LABEL]` for arbitrary, `rag-cli server {stop|restart} --port N` for port-targeted control.

GPU pane (Monitor_CC) reads state files: 3 fixed preset rows always visible plus dynamic arbitrary rows below. Idle countdown derives from state-file mtime (`_state_file_idle`), consistent with the watchdog and with rag-cli's own `status` / `server list` displays (`_state_file_idle` in `status.py`, `sf.stat().st_mtime` in `server_cli.py`) — all idle consumers now key off the same state-file mtime, never the log. Anomalies (malformed JSON, dead PID, missing log, duplicates, legacy files) logged to `Monitor_CC/src/gpu_pane/logs/gpu_pane.log` and counted in pane footer.

Measurement script: `dev/server_management/A_constellation_profile.py` profiles 8 constellations (VRAM, cold/warm latency, timeout rate) to produce the empirical data for cross-class exclusivity decisions.

## Evidence

- Live-probe verified llama-server logs 8 lines per inference request to stdout (slot status + srv log), `/health` is silent. mtime updates per request, /health does NOT trigger updates. See `dev/watchdog_scope/proposal_phaseA_v2.md (Monitor_CC)` NQ3 for the probe.
- Splade `logging.info(f"Encoded {len(req.input)} texts")` in `splade_server.py:47` writes per-request line to `splade_server.log`. Same idle mechanism applies.
- pgrep `-x` (exact comm match) avoids false-positives from processes mentioning "llama-server" in argv (e.g. workers with prompt text containing the string). Tested via `pgrep -x llama-server` returning empty when no real llama-server runs.

## Recommendation

Pending — empirical constellation profiling next session via `dev/server_management/A_constellation_profile.py`. Cross-class exclusivity decisions (e.g., `reranker-8b.exclusive_with: ["embedding-8b"]`) depend on profile results. Dynamic-port future evolution deferred until after constellation decisions are settled.

## Sources

- `dev/watchdog_scope/proposal_phaseA_v2.md (Monitor_CC)` — full architecture spec, NQ1-NQ6.
- `~/.claude/shared-rules/global/tool-use.md` `#### RAG CLI` — operational rules in tool-use.
