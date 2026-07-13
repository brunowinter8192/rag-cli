# default_port Elimination — Dynamic Ports With No Fallback

## Problem

`status()` and `check_health()` (server_lifecycle.py) and `start()` carried a hardcoded `default_port` fallback: when a server had no state file, the code fell back to `cfg["default_port"]` (8081, 8082, …) instead of treating the server as not-running. A hardcoded port is exactly the thing dynamic allocation exists to avoid — and it collides with whatever else binds that number.

## Live Evidence (2026-06-12)

- Real running servers were on kernel-dynamic ports — state files: `reranker-0.6b` on 59078, `embedding-8b` on 59486 — and correctly reported healthy. `/health` on the live reranker answered HTTP 200 in 0.4ms.
- `lsof` showed `mitmdump` (the session's mitmproxy) bound to the default ports 8081/8082/8083/8084/8085/8086.
- `rag-cli server status` showed STOPPED servers as phantom `RUNNING / NO`: with no state file, `status()` fell back to `cfg["default_port"]` (e.g. 8085), `find_pid_on_port` found mitmdump's PID → "RUNNING", `_check_health_port` hit mitmdump → HTTP 502 → "NO". The phantom is not the server — it is the proxy sitting on the number the code assumed the server "should" be on.
- Contrast: Monitor_CC's GPU pane reads state files only — a server with no state file shows `stopped`, no phantom. The CLI differed solely by this one fallback branch.

## Lineage

Kernel-ephemeral ports (`socket.bind(('', 0))`) were established earlier to eliminate the hardcoded-port conflict class; that earlier evidence already described this exact symptom ("mitmdump returned HTTP 502 to the /health probe … RUNNING unhealthy"). A later iteration retained `default_port` as a "preferred start port" plus status-display mapping for log readability — that kept the hardcoded reference that reintroduces the collision in the display path. This iteration removes `default_port` as a concept: the display-readability rationale backfired into the phantom, and dynamic-means-dynamic leaves no hardcoded number for anything to masquerade on.

## Decision

Eliminate `default_port` everywhere:
- `status()` / `check_health()` — state-file-only. No state file → server is not running (`status`: running=False, port=None, healthy=False; `check_health`: return False). No port probe.
- `start()` — always `_allocate_port()` (kernel-dynamic). The `default_port` field dropped from the `error_log.write` start record.
- `SERVERS` presets — `default_port` field removed from all 6; the `*_PORT` constants (verified used nowhere else) removed.
- `server_cli` — `_action_status` renders `port=None` as `-`; `_action_presets` drops the port column/key.
- Retained: `_resolve_port` for `start_arbitrary` only — there the port comes from the user (`rag-cli server start --port N`), an explicit choice (try-then-dynamic), not a hardcoded default. Param renamed `default_port` → `port`.

Result: preset servers get kernel-dynamic ports exclusively, clients resolve them only via state files, stopped = stopped, and no hardcoded port exists that the proxy (or anything else) can impersonate.
