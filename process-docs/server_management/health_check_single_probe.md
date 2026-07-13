# Health-Check: Single Deterministic Probe (Retry Removal)

## Problem

The `/health` probe was implemented twice with divergent behavior:
- `_check_health_port(port, retries=2, backoff_s=0.3)` in `server_utils.py` — retrying: 3 attempts, 300ms backoff, ~6.6s worst case. Used by `status()`, `_wait_for_health`, `start()` single-instance check, `server_cli`, `watchdog`.
- `check_health(name)` in `server_lifecycle.py` — its own inline `httpx.get(/health)`, single attempt, no retry. Used by `ensure_ready` → embedder/reranker callers.

Same effect ("is the server healthy"), two implementations, different behavior under transient load. The retry's stated rationale: "a single httpx timeout (GPU busy, network hiccup) must not trigger a destructive stop+restart." That premise rested on the assumption that a busy GPU server might not answer `/health` within 2s.

## Investigation — Does /health block behind the inference slot?

The retry only makes sense if a busy server can fail a `/health` probe. That is a question about llama-server's behavior, answered definitively in its source. Source: the vendored copy at `llama.cpp/` (git checkout, commit `24d2ee0`, build `b8198`), `tools/server/`.

**Evidence — /health is decoupled from the inference slot:**

- `get_health` handler (`server-context.cpp:3196`) returns `{"status":"ok"}` immediately. It deliberately SHADOWS the real `ctx_server` member (`bool ctx_server; // do NOT delete this line` + `GGML_UNUSED(ctx_server)`) specifically to prevent the handler from touching the inference context. Comment: "this endpoint can be accessed during sleeping."
- By contrast, the `get_metrics` handler directly below explicitly does "request slots data using task queue" (`server_task task(SERVER_TASK_TYPE_METRICS)`). So queue-coupling is opt-in per endpoint — `get_metrics` is coupled, `get_health` is not.
- `server.cpp:241`: the HTTP server is started BEFORE the model loads — `// start the HTTP server before loading the model to be able to serve /health requests`. So `/health` answers even during model load.
- Loading and error states are handled by HTTP middleware (fast 503), not by the inference slot.

**Slot context:** all our presets run `-np 1` (single slot) — `SERVERS` in `server_utils.py`. The single slot serializes INFERENCE requests (`/v1/embeddings`, `/v1/rerank`), not `/health`. The Python-level per-server request serializer `server_lock.py` is dead code (no import callers) — the one-request-at-a-time property comes solely from the llama-server `-np 1` slot.

## Conclusion

`/health` is decoupled from the inference slot: a busy `-np 1` server still answers `/health` in milliseconds. A `/health` timeout therefore means genuinely not healthy (model still loading, process wedged, or dead) — never merely "busy". The retry guarded a scenario that does not occur for a correctly-functioning server, and it leaked up to 6.6s latency into pure display callers (`status`, `server list`) plus a nested double-loop inside `_wait_for_health` (which already polls per second).

**Decision:** one deterministic single probe, 2s timeout, no retry. `check_health` delegates to `_check_health_port(port)`; the inline duplicate (and `import httpx` in `server_lifecycle.py`) removed. A single `False` is now meaningful, not noise.

Consequence: the "alive but unhealthy → stop and restart on a fresh port" path in `start()` (single-instance enforcement) is sound — a merely-busy server reads healthy, so it is not killed mid-inference; it reads unhealthy only when genuinely wedged, which is exactly when recycling is wanted.
