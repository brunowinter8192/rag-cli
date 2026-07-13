# Infrastructure 3: Dynamic Port Allocation for GPU Servers

## Status Quo (IST)

**Code:** `src/rag/server_manager.py`
**Pattern:** Each GPU server (embedding/reranker/splade) gets a kernel-assigned free port at startup. Port + PID persisted to `~/.rag-locks/<server>.port` JSON. All HTTP clients read the port via `server_manager.get_port(name)` per call.

**Port discovery (in `start(name)`):**

```python
for attempt in range(1, 4):
    port = _get_free_port()                       # socket.bind(('', 0)) → kernel ephemeral
    cmd = cfg["cmd"] + ["--port", str(port)]
    proc = subprocess.Popen(cmd, ...)
    # Health-check loop with cfg["timeout"] (60-90s)
    if health_check_passes:
        _write_port_file(name, port, proc.pid)
        return True
    # Else: terminate, retry up to 3 attempts
```

**Port file format (`~/.rag-locks/<server>.port`):**

```json
{
  "port": 49445,
  "pid": 45387,
  "started_at": "2026-05-08T19:37:18+00:00"
}
```

**Stale detection (in `get_port(name)`):**

```python
def get_port(name: str) -> int:
    f = _port_file(name)
    data = json.loads(f.read_text())          # raises if missing
    pid = data.get("pid")
    if pid:
        os.kill(pid, 0)                        # raises ProcessLookupError if dead
    return data["port"]
# On stale: unlink port file, raise RuntimeError("server dead")
```

**Client URL construction:**

```python
# embedder.py
def _embedding_url() -> str:
    return f"http://localhost:{get_port('embedding')}/v1/embeddings"

# Called per-request inside generate_embeddings, NOT cached at module load.
# Server can restart with new port; clients always pick up current.
```

Same pattern in `sparse_embedder.py`, `reranker.py`. `status.py` reads ports the same way.

**SERVERS dict (in server_manager.py):** no `port` or `health_url` fields. Just `cmd` (without `--port`), `timeout`, `required_for`. Port appended dynamically in `start()`.

**Lazy activation:** `ensure_ready(target)` checks each needed server. If `check_health(name)` returns False (server stopped or stale), calls `start(name)`. Used by indexer and search workflows before HTTP calls.

**Idle shutdown:** `scripts/idle_watchdog.py` runs every 15 minutes via launchd LaunchAgent (`scripts/install_watchdog.sh` generates the plist with absolute paths). Reads each `<server>.last_used` timestamp; if >`IDLE_TIMEOUT` (3600s = 60min), calls `server_manager.stop(name)` which kills the PID and unlinks port file. Postgres is never auto-stopped.

## Evidenz

### Pre-fix conflict (see `OldThemes/connection_hang_cascade.md` § Layer 5)

`EMBEDDING_PORT = 8081` was a hardcoded constant. Monitor_CC dynamically allocated `:8081` for a worker proxy (mitmdump) when llama-server happened to be down. Restart attempts of llama-server failed silently (or were never tried) because the port was occupied. `rag-cli status` reported `RUNNING unhealthy` — there WAS something on the port responding to TCP, but mitmdump returned HTTP 502 to the /health probe.

The hardcoding was a false economy: it saved one config item but introduced an unresolvable conflict class.

### Why kernel-allocated ports

`socket.bind(('', 0))` returns an ephemeral port (32768-60999 range on Linux, 49152-65535 on macOS by default). The kernel guarantees the port is free at the moment of binding. After `getsockname()`, we close the discovery socket and pass the port number to the subprocess.

There is a small race window (~ms) between socket close and subprocess bind during which another process could grab the port. For a personal-use single-developer machine this is acceptable. The 3-attempt retry loop covers the rare collision: if subprocess bind fails (process exits early without serving /health), we discover a new port and retry. After 3 fails, raise — indicates a deeper environmental problem.

### Why per-request URL lookup (no caching)

If a client cached `http://localhost:8081/v1/embeddings` at module load, server restarts (manual `workflow.py server restart`, idle-shutdown + lazy-restart) would invalidate the cached URL. Per-request lookup is fast (one file read of the small port file, ~0.01ms) and always correct.

### Stale port file detection

A port file can be stale if the server was SIGKILLed or crashed without going through `stop(name)`. `get_port()` checks `os.kill(pid, 0)` — if the PID is dead, the port file is unlinked and `RuntimeError` raised. Caller (e.g., `ensure_ready`) sees the error, treats server as not running, calls `start(name)` to spawn fresh.

PID reuse risk: 32-bit PIDs aren't reused for hours/days on normal systems. Theoretical collision negligible. If matters in future, switch to PID + process-start-time check.

### Race-window retry rationale

The race between discovery-socket-close and subprocess-bind can fail in two ways:
1. Subprocess starts but `--port N` bind fails because another process grabbed N. Subprocess exits with error. `proc.poll() is not None` after a few seconds. Retry.
2. Subprocess starts but takes 60s+ to become healthy due to model load. Health check eventually succeeds. No retry needed.

3-attempt retry covers (1). Beyond 3 attempts, environmental issue is more likely (e.g., model file corrupted, GPU OOM). Caller surfaces as `RuntimeError`.

### Why launchd for idle watchdog (not in-process timer)

The in-process `_watchdog_loop()` thread (in `server_manager.py`) runs while a Python process is alive — useful during an active session. But for a system that may go idle overnight without any rag-cli activity, an in-process watchdog can't help (no process exists to run the watchdog). launchd LaunchAgent runs every 15 minutes regardless of whether any rag-cli is currently active, ensuring idle GPU servers actually get stopped.

`install_watchdog.sh` generates the plist with concrete absolute paths because launchd plists don't support `$HOME` substitution. Per-machine install is acceptable; the alternative (templating + runtime substitution) would just push complexity to install time.

## Recommendation (SOLL)

**Keep:** Kernel-assigned ephemeral ports via `socket.bind(0)`. Eliminates the hardcoded-port conflict class entirely.

**Keep:** Port file with PID for stale detection. File-based observability is debuggable with `cat`, recoverable from any state.

**Keep:** Per-request URL lookup in clients. Server restart resilience is more valuable than micro-optimization of cached URL.

**Keep:** 3-attempt retry on subprocess startup. Race-window mitigation without over-engineering.

**Keep:** launchd LaunchAgent for idle-watchdog. Out-of-process scheduling matches the use case (sporadic interactive work).

**Keep:** Postgres NOT auto-stopped. Lightweight, runs in Docker, idempotent on connect — no benefit to bouncing it.

## Offene Fragen

- **`--port 0` alternative** — llama-server and uvicorn both might support `--port 0` (kernel-assigned, no race). Would require parsing the server's stdout/log to discover the actual port. Significantly more complex and fragile across server versions. Current socket-discovery approach is clear and version-independent.
- **Linux vs macOS for idle-watchdog** — Current `install_watchdog.sh` is launchd (macOS). Linux equivalent would be a systemd timer or cron job. Not yet implemented; add when first Linux deployment happens.
- **Multi-instance per server** — current model assumes one llama-server, one SPLADE, one reranker per machine. If load increases, could run multiple embedders behind a load balancer. Adds significant complexity (registry, routing). Defer until measured.
- **Port range exhaustion** — ephemeral range has thousands of ports. Single-developer-machine never hits the limit. Theoretical concern, not actionable.

## Quellen

- POSIX `socket.bind(0)` ephemeral port semantics — [linux.die.net/man/7/ip](https://linux.die.net/man/7/ip)
- macOS launchd plist reference — [developer.apple.com/library/archive/documentation/MacOSX/Conceptual/BPSystemStartup/Chapters/CreatingLaunchdJobs.html](https://developer.apple.com/library/archive/documentation/MacOSX/Conceptual/BPSystemStartup/Chapters/CreatingLaunchdJobs.html)
- See `OldThemes/connection_hang_cascade.md` § Layer 5 + § Phase 3 for the bug-class history that drove this design.
